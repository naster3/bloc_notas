from __future__ import annotations

import re
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, filedialog, simpledialog

from ..export_import import ExportImport, ExportImportError
from ..models import Note, title_from_content
from ..storage_sqlite import NoteStoreError
from ..ui.texts import get_dialog_texts


class NotesController:
    def __init__(self, app) -> None:
        self.app = app
        self._export_import = ExportImport()
        self._highlight_job: str | None = None
        self._placeholder_active = False
        self._placeholder_bound = False

    def on_text_modified(self, event=None) -> None:
        if self.app.loading_note:
            self.app.text.edit_modified(False)
            return
        if self.app.text.edit_modified():
            self.app.dirty = True
            self.app.text.edit_modified(False)
            self._schedule_autosave()
            self._schedule_highlight_update()
            if self._placeholder_active:
                self._clear_placeholder_after_modification()

    def on_search_change(self, *_) -> None:
        self.refresh_list(select_id=self.app.current_note_id)
        self.update_search_highlights()

    def refresh_list(self, select_id: str | None = None) -> None:
        query_text, tags = self._parse_search_query(self.app.search_var.get())
        extra_tags = getattr(self.app, "tag_filters", set())
        if extra_tags:
            tags = list({*tags, *extra_tags})
        try:
            notes = self.app.store.list_notes(query=query_text)
            total_notes = notes if not query_text and not tags else self.app.store.list_notes()
        except (sqlite3.Error, NoteStoreError) as exc:
            self._show_error(self._get_texts()["list_failed"], exc)
            return
        if tags:
            notes = self._filter_notes_by_tags(notes, tags)
        notes = self._sort_notes(notes)
        self.app.loading_list = True
        self.app.listbox.delete(0, "end")
        self.app.note_ids = []
        for note in notes:
            label = note.title or title_from_content(note.content)
            if note.pinned:
                label = f"* {label}"
            self.app.listbox.insert("end", label)
            self.app.note_ids.append(note.id)
        self.app.loading_list = False
        filtered_count = len(self.app.note_ids)
        total_count = len(total_notes) if total_notes is not None else filtered_count
        self.app.notes_count.config(text=f"{filtered_count} / {total_count}")
        self._highlight_active_note()
        if hasattr(self.app, "sidebar"):
            try:
                tags_list = self._collect_tags(total_notes)
                self.app.sidebar.update_tags(tags_list)
            except Exception:
                pass

        if select_id and select_id in self.app.note_ids:
            index = self.app.note_ids.index(select_id)
            self.app.listbox.selection_set(index)
            self.app.listbox.see(index)
        elif notes and self.app.current_note_id is None:
            self.app.listbox.selection_set(0)
            self.app.listbox.see(0)
            self.on_select()
        elif not notes and not self.app.dirty:
            self._show_placeholder()

    def on_select(self, event=None) -> None:
        if self.app.loading_list:
            return
        selection = self.app.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        note_id = self.app.note_ids[index]
        if note_id == self.app.current_note_id:
            return
        if not self._confirm_save_if_dirty():
            self._restore_current_selection()
            return
        try:
            note = self.app.store.get_note(note_id)
        except (sqlite3.Error, NoteStoreError) as exc:
            self._show_error(self._get_texts()["load_failed"], exc)
            return
        if not note:
            self._show_error(self._get_texts()["load_failed"], None)
            return
        self.load_note(note)
        self._highlight_active_note()

    def load_note(self, note: Note) -> None:
        self._cancel_autosave()
        self.app.loading_note = True
        self._set_readonly(False)
        self.app.text.delete("1.0", "end")
        self.app.text.insert("1.0", note.content)
        self.app.text.edit_modified(False)
        self.app.loading_note = False
        self.app.current_note_id = note.id
        self.app.dirty = False
        self.app._set_title(note.title)
        self._apply_text_theme()
        self.update_search_highlights()
        self._hide_placeholder()
        self._reset_undo()
        self._render_statusbar()
        if hasattr(self.app, "garbage_collect_tags"):
            self.app.garbage_collect_tags()

    def get_editor_content(self) -> str:
        if self._placeholder_active:
            return ""
        return self.app.text.get("1.0", "end-1c")

    def new_note(self) -> None:
        if not self._confirm_save_if_dirty():
            return
        self._cancel_autosave()
        self.app.current_note_id = None
        self.app.dirty = False
        self.app.loading_note = True
        self._set_readonly(False)
        self.app.text.delete("1.0", "end")
        self.app.text.edit_modified(False)
        self.app.loading_note = False
        self.app._set_title()
        self.app.listbox.selection_clear(0, "end")
        self._apply_text_theme()
        self._show_placeholder(readonly=False)
        self._reset_undo()

    def save_current(self) -> Note | None:
        content = self.get_editor_content()
        self._set_saving_state(True)
        try:
            note = self.app.store.upsert_from_content(self.app.current_note_id, content)
        except (sqlite3.Error, NoteStoreError) as exc:
            self._set_saving_state(False)
            self._show_error(self._get_texts()["save_failed"], exc)
            return None
        self._set_saving_state(False)
        if note is None:
            self.app.dirty = False
            self._render_statusbar()
            return None
        self.app.current_note_id = note.id
        self.app.dirty = False
        self._render_statusbar()
        self.app._set_title(note.title)
        self.refresh_list(select_id=note.id)
        return note

    def delete_note(self) -> None:
        if not self.app.current_note_id:
            self._set_readonly(False)
            self.app.text.delete("1.0", "end")
            self.app.text.edit_modified(False)
            self.app.dirty = False
            self._render_statusbar()
            return
        texts = self._get_texts()
        if not messagebox.askyesno(
            texts["delete_title"],
            texts["delete_confirm"],
            parent=self.app.root,
        ):
            return
        try:
            deleted = self.app.store.delete_note(self.app.current_note_id)
        except (sqlite3.Error, NoteStoreError) as exc:
            self._show_error(texts["delete_failed"], exc)
            return
        if not deleted:
            self._show_error(texts["delete_failed"], None)
            return
        self.app.current_note_id = None
        self.app.dirty = False
        self._set_readonly(False)
        self.app.text.delete("1.0", "end")
        self.app.text.edit_modified(False)
        self.app._set_title()
        self.refresh_list()
        self._apply_text_theme()

    def export_txt(self) -> None:
        note = self.save_current()
        if note is None:
            texts = self._get_texts()
            messagebox.showinfo(
                texts["export_title"],
                texts["export_empty"],
                parent=self.app.root,
            )
            return
        texts = self._get_texts()
        path = filedialog.asksaveasfilename(
            parent=self.app.root,
            defaultextension=".txt",
            filetypes=[(texts["file_text"], "*.txt")],
        )
        if path:
            path = self._ensure_extension(path, ".txt")
            if not path:
                return
            try:
                self._export_import.export_note_txt(note.content, path)
            except (ExportImportError, OSError) as exc:
                self._show_error(texts["export_failed"], exc)

    def export_md(self) -> None:
        note = self.save_current()
        if note is None:
            texts = self._get_texts()
            messagebox.showinfo(
                texts["export_title"],
                texts["export_empty"],
                parent=self.app.root,
            )
            return
        texts = self._get_texts()
        title = simpledialog.askstring(
            texts["title_prompt"],
            texts["title_prompt"],
            initialvalue=note.title,
            parent=self.app.root,
        )
        if title is None:
            return
        title = title.strip() or note.title
        path = filedialog.asksaveasfilename(
            parent=self.app.root,
            defaultextension=".md",
            filetypes=[(texts["file_markdown"], "*.md")],
        )
        if path:
            path = self._ensure_extension(path, ".md")
            if not path:
                return
            try:
                self._export_import.export_note_md(title, note.content, path)
            except (ExportImportError, OSError) as exc:
                self._show_error(texts["export_failed"], exc)

    def import_md(self) -> None:
        texts = self._get_texts()
        initial_dir = None
        last_dir = getattr(self.app, "last_import_dir", "")
        if isinstance(last_dir, str) and last_dir:
            initial_dir = last_dir
        path = filedialog.askopenfilename(
            parent=self.app.root,
            filetypes=[(texts["file_markdown"], "*.md")],
            initialdir=initial_dir,
        )
        if not path:
            return
        try:
            base_dir = str(Path(path).parent)
        except OSError:
            base_dir = ""
        if base_dir and hasattr(self.app, "set_last_import_dir"):
            self.app.set_last_import_dir(base_dir)
        path = self._ensure_extension(path, ".md")
        if not path:
            return
        try:
            title, content = self._export_import.import_markdown(path)
        except (ExportImportError, OSError) as exc:
            self._show_error(texts["import_failed"], exc)
            return
        new_title = simpledialog.askstring(
            texts["title_prompt"],
            texts["title_prompt"],
            initialvalue=title,
            parent=self.app.root,
        )
        if new_title is None:
            return
        if new_title.strip():
            title = new_title.strip()
        try:
            note = self.app.store.create_note(title=title, content=content)
        except (sqlite3.Error, NoteStoreError) as exc:
            self._show_error(texts["import_failed"], exc)
            return
        self.load_note(note)
        self.refresh_list(select_id=note.id)

    def on_close(self) -> None:
        if not self._confirm_save_if_dirty():
            return
        self._cancel_autosave()
        if hasattr(self.app, "flush_settings"):
            try:
                self.app.flush_settings()
            except Exception:
                pass
        self.app.root.destroy()

    def _apply_text_theme(self) -> None:
        editor_bg = self.app.colors.get("editor_bg", "white")
        editor_fg = self.app.colors.get("text", "black")
        self.app.text.config(
            bg=editor_bg,
            fg=editor_fg,
            insertbackground=self.app.colors.get("accent", "black"),
            selectbackground=self.app.colors.get("selection", "#CCE0FF"),
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            padx=12,
            pady=12,
        )
        self.app.listbox.config(
            bg=self.app.colors.get("list_bg", "white"),
            fg=self.app.colors.get("text", "black"),
            selectbackground=self.app.colors.get("selection", "#CCE0FF"),
            selectforeground=self.app.colors.get("text", "black"),
            highlightthickness=0,
            borderwidth=0,
            activestyle="none",
            font=(self.app.ui_font_family, 10),
        )
        self.app.base_text_fg = editor_fg
        self.app.base_text_bg = editor_bg
        self._configure_search_tag()
        self._configure_placeholder_tag()
        self._highlight_active_note()

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_dialog_texts("notes", language)

    def update_search_highlights(self, *_) -> None:
        term = self.app.last_search
        if not term:
            self._clear_search_highlights()
            self._render_statusbar()
            return
        if self._placeholder_active:
            self._clear_search_highlights()
            self._render_statusbar()
            return
        self._highlight_matches(term)
        self._render_statusbar()

    def _show_error(self, message: str, exc: Exception | None) -> None:
        texts = self._get_texts()
        detail = f"\n{exc}" if exc else ""
        messagebox.showerror(
            texts["error_title"],
            f"{message}{detail}",
            parent=self.app.root,
        )

    def _confirm_save_if_dirty(self) -> bool:
        if not self.app.dirty:
            return True
        texts = self._get_texts()
        result = messagebox.askyesnocancel(
            texts["unsaved_title"],
            texts["unsaved_message"],
            parent=self.app.root,
        )
        if result is None:
            return False
        if result is False:
            self._discard_changes()
            return True
        self.save_current()
        return not self.app.dirty

    def _discard_changes(self) -> None:
        self.app.dirty = False
        try:
            self.app.text.edit_modified(False)
        except tk.TclError:
            pass
        self._render_statusbar()

    def _restore_current_selection(self) -> None:
        current = self.app.current_note_id
        if not current:
            self.app.listbox.selection_clear(0, "end")
            return
        if current in self.app.note_ids:
            index = self.app.note_ids.index(current)
            self.app.listbox.selection_clear(0, "end")
            self.app.listbox.selection_set(index)
            self.app.listbox.see(index)

    def _schedule_autosave(self) -> None:
        self._cancel_autosave()
        delay = getattr(self.app, "autosave_delay", 3000)
        self.app.autosave_job = self.app.root.after(delay, self._autosave_if_dirty)

    def _cancel_autosave(self) -> None:
        if self.app.autosave_job is not None:
            try:
                self.app.root.after_cancel(self.app.autosave_job)
            except tk.TclError:
                pass
            self.app.autosave_job = None

    def _autosave_if_dirty(self) -> None:
        self.app.autosave_job = None
        if self.app.dirty:
            self.save_current()

    def _schedule_highlight_update(self) -> None:
        if not self.app.last_search:
            return
        if self._highlight_job is not None:
            try:
                self.app.root.after_cancel(self._highlight_job)
            except tk.TclError:
                pass
            self._highlight_job = None
        self._highlight_job = self.app.root.after(150, self._run_highlight_update)

    def _run_highlight_update(self) -> None:
        self._highlight_job = None
        self.update_search_highlights()

    def _configure_search_tag(self) -> None:
        try:
            self.app.text.tag_configure(
                "search_match",
                background=self.app.colors.get("selection", "#FFE59A"),
                foreground=self.app.colors.get("text", "black"),
            )
        except tk.TclError:
            pass

    def _clear_search_highlights(self) -> None:
        try:
            self.app.text.tag_remove("search_match", "1.0", "end")
        except tk.TclError:
            pass

    def _highlight_matches(self, term: str) -> None:
        self._configure_search_tag()
        self._clear_search_highlights()
        if not term:
            return
        if self.app.regex_var.get():
            try:
                re.compile(term)
            except re.error:
                return
        pattern, regexp = self._build_search_pattern(term)
        start = "1.0"
        nocase = not self.app.match_case_var.get()
        while True:
            count_var = tk.IntVar()
            try:
                match = self.app.text.search(
                    pattern,
                    start,
                    stopindex="end",
                    nocase=nocase,
                    regexp=regexp,
                    count=count_var,
                )
            except tk.TclError:
                break
            if not match:
                break
            match_len = count_var.get() or len(term) or 1
            end = f"{match}+{match_len}c"
            try:
                self.app.text.tag_add("search_match", match, end)
            except tk.TclError:
                break
            start = end

    def _parse_search_query(self, query: str) -> tuple[str, list[str]]:
        tokens = (query or "").strip().split()
        tags: list[str] = []
        text_tokens: list[str] = []
        for token in tokens:
            lowered = token.lower()
            if lowered.startswith("tag:") or lowered.startswith("tags:"):
                raw = token.split(":", 1)[1]
                tags.extend(self._split_tags_token(raw))
                continue
            if token.startswith("#"):
                tags.extend(self._split_tags_token(token[1:]))
                continue
            text_tokens.append(token)
        return " ".join(text_tokens), [tag.lower() for tag in tags if tag]

    @staticmethod
    def _split_tags_token(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _filter_notes_by_tags(notes: list[Note], tags: list[str]) -> list[Note]:
        tag_set = {tag.lower() for tag in tags}
        filtered: list[Note] = []
        for note in notes:
            note_tags = {tag.lower() for tag in note.tags}
            if tag_set.issubset(note_tags):
                filtered.append(note)
        return filtered

    def _sort_notes(self, notes: list[Note]) -> list[Note]:
        mode = getattr(self.app, "sort_mode", "pinned")
        if mode == "recent":
            return sorted(notes, key=lambda note: note.updated_at, reverse=True)
        if mode == "alpha":
            return sorted(
                notes,
                key=lambda note: (
                    (note.title or title_from_content(note.content)).lower()
                ),
            )
        notes_sorted = sorted(notes, key=lambda note: note.updated_at, reverse=True)
        return sorted(notes_sorted, key=lambda note: not note.pinned)

    @staticmethod
    def _collect_tags(notes: list[Note]) -> list[str]:
        tags: set[str] = set()
        for note in notes:
            for tag in note.tags:
                if tag:
                    tags.add(tag)
        return sorted(tags)

    def _highlight_active_note(self) -> None:
        if not hasattr(self.app, "listbox"):
            return
        listbox = self.app.listbox
        default_bg = self.app.colors.get("list_bg", "white")
        default_fg = self.app.colors.get("text", "black")
        active_bg = self.app.colors.get("selection", "#CCE0FF")
        active_fg = self.app.colors.get("text", "black")
        try:
            for i in range(listbox.size()):
                listbox.itemconfig(i, background=default_bg, foreground=default_fg)
        except tk.TclError:
            return
        current = self.app.current_note_id
        if current and current in self.app.note_ids:
            index = self.app.note_ids.index(current)
            try:
                listbox.itemconfig(index, background=active_bg, foreground=active_fg)
            except tk.TclError:
                return

    def _build_search_pattern(self, term: str) -> tuple[str, bool]:
        regex = self.app.regex_var.get()
        whole_word = self.app.whole_word_var.get()
        pattern = term
        regexp = regex or whole_word
        if not regex:
            pattern = re.escape(term)
        if whole_word:
            pattern = rf"\y(?:{pattern})\y"
        return pattern, regexp

    def _reset_undo(self) -> None:
        try:
            self.app.text.edit_reset()
        except tk.TclError:
            pass

    def _configure_placeholder_tag(self) -> None:
        try:
            self.app.text.tag_configure(
                "placeholder",
                foreground=self.app.colors.get("muted", "#7A7A7A"),
            )
        except tk.TclError:
            pass

    def _ensure_placeholder_bindings(self) -> None:
        if self._placeholder_bound or not hasattr(self.app, "text"):
            return
        self._placeholder_bound = True
        self.app.text.bind("<FocusIn>", self._on_editor_focus, add="+")
        self.app.text.bind("<Key>", self._on_editor_key, add="+")

    def _on_editor_focus(self, event=None) -> None:
        if self._placeholder_active and not self._editor_readonly():
            self._hide_placeholder()

    def _on_editor_key(self, event=None) -> None:
        if self._placeholder_active and not self._editor_readonly():
            self._hide_placeholder()

    def _show_placeholder(self, readonly: bool = True) -> None:
        self._ensure_placeholder_bindings()
        if self._placeholder_active or not hasattr(self.app, "text"):
            return
        text = self.app.text
        placeholder = self._get_texts().get("placeholder", "")
        if not placeholder:
            return
        self._set_readonly(False)
        text.delete("1.0", "end")
        text.insert("1.0", placeholder)
        text.tag_add("placeholder", "1.0", "end")
        self._placeholder_active = True
        self._clear_search_highlights()
        try:
            text.edit_modified(False)
        except tk.TclError:
            pass
        self._set_readonly(readonly)
        self._render_statusbar()

    def _hide_placeholder(self) -> None:
        if not self._placeholder_active or not hasattr(self.app, "text"):
            return
        text = self.app.text
        self._set_readonly(False)
        text.delete("1.0", "end")
        text.tag_remove("placeholder", "1.0", "end")
        self._placeholder_active = False
        try:
            text.edit_modified(False)
        except tk.TclError:
            pass
        self._render_statusbar()

    def _clear_placeholder_after_modification(self) -> None:
        if not self._placeholder_active or not hasattr(self.app, "text"):
            return
        text = self.app.text
        placeholder = self._get_texts().get("placeholder", "")
        content = text.get("1.0", "end-1c")
        if content == placeholder:
            return
        if placeholder and content.startswith(placeholder):
            new_content = content[len(placeholder) :]
            text.delete("1.0", "end")
            text.insert("1.0", new_content.lstrip("\n"))
        text.tag_remove("placeholder", "1.0", "end")
        self._placeholder_active = False
        self._set_readonly(False)
        self._render_statusbar()

    def _set_readonly(self, readonly: bool) -> None:
        editor = getattr(self.app, "editor", None)
        if editor and hasattr(editor, "set_readonly"):
            editor.set_readonly(readonly)

    def _editor_readonly(self) -> bool:
        editor = getattr(self.app, "editor", None)
        if editor and hasattr(editor, "is_readonly"):
            return bool(editor.is_readonly())
        return False

    def _set_saving_state(self, saving: bool) -> None:
        setattr(self.app, "saving", bool(saving))
        self._render_statusbar()

    def _render_statusbar(self) -> None:
        if getattr(self.app, "status_var", None) is None:
            return
        try:
            if self.app.status_var.get() and hasattr(self.app, "_render_statusbar"):
                self.app._render_statusbar()
        except tk.TclError:
            pass
        self._refresh_toolbar()

    def _refresh_toolbar(self) -> None:
        toolbar = getattr(self.app, "toolbar", None)
        if toolbar and hasattr(toolbar, "refresh_states"):
            try:
                toolbar.refresh_states()
            except tk.TclError:
                pass

    def _ensure_extension(self, path: str, expected: str) -> str | None:
        expected_lower = expected.lower()
        path_lower = path.lower()
        if path_lower.endswith(expected_lower):
            return path
        helper = None
        if expected_lower == ".md":
            helper = ExportImport.ensure_md_path
        elif expected_lower == ".txt":
            helper = ExportImport.ensure_txt_path
        if "." not in Path(path).name:
            if helper:
                return helper(path)
            return f"{path}{expected}"
        texts = self._get_texts()
        if messagebox.askyesno(
            texts["export_title"],
            texts["change_extension"].format(ext=expected),
            parent=self.app.root,
        ):
            if helper:
                return helper(path)
            return f"{path}{expected}"
        messagebox.showwarning(
            texts["export_title"],
            texts["invalid_extension"].format(ext=expected),
            parent=self.app.root,
        )
        return None
