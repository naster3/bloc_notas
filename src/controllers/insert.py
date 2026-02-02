from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import webbrowser

from ..ui.texts import INSERT_TEMPLATES, get_dialog_texts, pick_texts


class InsertController:
    def __init__(self, app) -> None:
        self.app = app
        self._preview_dialog: tk.Toplevel | None = None

    def insert_datetime(self) -> None:
        stamp = datetime.now().strftime(self._datetime_format())
        self._insert_inline(stamp)

    def insert_date(self) -> None:
        stamp = datetime.now().strftime(self._date_format())
        self._insert_inline(stamp)

    def insert_separator(self) -> None:
        self._insert_block(self._get_templates()["separator"])

    def insert_heading(self) -> None:
        self._insert_block(self._get_templates()["heading"])

    def insert_h1(self) -> None:
        self._insert_block(self._get_templates()["h1"])

    def insert_h2(self) -> None:
        self._insert_block(self._get_templates()["h2"])

    def insert_h3(self) -> None:
        self._insert_block(self._get_templates()["h3"])

    def insert_list(self) -> None:
        self._insert_block(self._get_templates()["list"])

    def insert_bullets(self) -> None:
        self._insert_block(self._get_templates()["bullets"])

    def insert_numbered(self) -> None:
        self._insert_block(self._get_templates()["numbered"])

    def insert_checklist(self) -> None:
        widget = self._get_text_widget()
        if self._apply_checklist_to_selection(widget):
            return
        self._insert_block(self._get_templates()["checklist"])

    def insert_quick_note(self) -> None:
        self._insert_block(self._get_templates()["quick_note"])

    def insert_meeting(self) -> None:
        self._insert_block(self._get_templates()["meeting"])

    def insert_todo(self) -> None:
        self._insert_block(self._get_templates()["todo"])

    def insert_journal(self) -> None:
        self._insert_block(self._get_templates()["journal"])

    def insert_link_template(self) -> None:
        widget = self._get_target_widget()
        if self._wrap_selection(widget, "[", "](https://)"):
            return
        self._insert_inline(self._get_templates()["link_template"])

    def insert_link_prompt(self) -> None:
        texts = self._get_texts()
        widget = self._get_target_widget()
        selected = self._get_selection_text(widget)
        if selected:
            selected = selected.strip()
            if self._looks_like_url(selected):
                url = self._normalize_url(selected)
                texto = simpledialog.askstring(
                    texts["dialog_title"],
                    texts["text"],
                    parent=self.app.root,
                )
                if not texto:
                    texto = selected
                self._replace_selection(widget, f"[{texto}]({url})")
                return
            url = simpledialog.askstring(
                texts["dialog_title"],
                texts["url"],
                parent=self.app.root,
            )
            if not url:
                return
            url = self._normalize_url(url.strip())
            self._replace_selection(widget, f"[{selected}]({url})")
            return

        url = simpledialog.askstring(
            texts["dialog_title"],
            texts["url"],
            parent=self.app.root,
        )
        if not url:
            return
        url = self._normalize_url(url.strip())
        texto = simpledialog.askstring(
            texts["dialog_title"],
            texts["text"],
            parent=self.app.root,
        )
        if not texto:
            texto = texts["default_text"]
        self._insert_inline(f"[{texto}]({url})")

    def insert_inline_code(self) -> None:
        widget = self._get_target_widget()
        if self._wrap_selection(widget, "`", "`"):
            return
        self._insert_inline(self._get_templates()["inline_code"])

    def insert_code_block(self) -> None:
        self._insert_block(self._get_templates()["code_block"])

    def validate_templates(self) -> None:
        texts = get_dialog_texts("templates", self._language())
        issues = self._collect_template_issues()
        if not issues:
            messagebox.showinfo(
                texts["validation_title"],
                texts["validation_ok"],
                parent=self.app.root,
            )
            return
        body = "\n".join([texts["validation_errors"]] + [f"- {item}" for item in issues])
        messagebox.showwarning(
            texts["validation_title"],
            body,
            parent=self.app.root,
        )

    def show_templates_preview(self) -> None:
        texts = get_dialog_texts("templates", self._language())
        if self._preview_dialog and self._preview_dialog.winfo_exists():
            self._preview_dialog.lift()
            return

        dialog = tk.Toplevel(self.app.root)
        dialog.title(texts["preview_title"])
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)
        self._preview_dialog = dialog

        frame = ttk.Frame(dialog, padding=(12, 10))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        list_frame = ttk.Frame(frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        listbox = tk.Listbox(list_frame, width=28, exportselection=False)
        listbox.grid(row=0, column=0, sticky="nsew")
        list_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=listbox.yview
        )
        list_scroll.grid(row=0, column=1, sticky="ns")
        listbox.config(yscrollcommand=list_scroll.set)

        preview_frame = ttk.Frame(frame)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        origin_label = ttk.Label(preview_frame, style="Muted.TLabel")
        origin_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        text = tk.Text(preview_frame, wrap="word", width=60, height=18)
        text.grid(row=1, column=0, sticky="nsew")
        text_scroll = ttk.Scrollbar(
            preview_frame, orient="vertical", command=text.yview
        )
        text_scroll.grid(row=1, column=1, sticky="ns")
        text.config(yscrollcommand=text_scroll.set)

        items = self._build_preview_items(texts)
        for item in items:
            listbox.insert("end", item["label"])

        def refresh_items(select_index: int | None = None) -> None:
            nonlocal items
            items = self._build_preview_items(texts)
            listbox.delete(0, "end")
            for item in items:
                listbox.insert("end", item["label"])
            if items:
                index = 0 if select_index is None else min(select_index, len(items) - 1)
                listbox.selection_set(index)
                on_select()

        def on_select(event=None) -> None:
            selection = listbox.curselection()
            if not selection:
                return
            item = items[selection[0]]
            origin_label.config(
                text=f"{texts['origin_label']}: {item['origin']}"
            )
            text.config(state="normal")
            text.delete("1.0", "end")
            text.insert("1.0", item["content"])
            text.config(state="disabled")

        def on_copy() -> None:
            selection = listbox.curselection()
            if not selection:
                return
            item = items[selection[0]]
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(item["content"])
            messagebox.showinfo(
                texts["preview_title"],
                texts["copy_done"],
                parent=self.app.root,
            )

        def on_reset() -> None:
            selection = listbox.curselection()
            if not selection:
                return
            item = items[selection[0]]
            overrides = getattr(self.app, "template_overrides", {})
            if isinstance(overrides, dict):
                overrides.pop(item["key"], None)
                self.app.template_overrides = overrides
                if hasattr(self.app, "_save_config"):
                    self.app._save_config()
            messagebox.showinfo(
                texts["preview_title"],
                texts["reset_done"],
                parent=self.app.root,
            )
            refresh_items(selection[0])

        listbox.bind("<<ListboxSelect>>", on_select)
        if items:
            listbox.selection_set(0)
            on_select()

        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(
            buttons,
            text=texts["copy_template"],
            command=on_copy,
        ).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(
            buttons,
            text=texts["reset_template"],
            command=on_reset,
        ).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(
            buttons,
            text=texts["open_settings"],
            command=self._open_settings,
        ).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(buttons, text=texts["close"], command=dialog.destroy).grid(
            row=0, column=3
        )

        dialog.bind("<Escape>", lambda event: dialog.destroy())

    def _insert_inline(self, text: str) -> None:
        widget = self._get_target_widget()
        widget.insert(tk.INSERT, text)

    def _insert_block(self, text: str) -> None:
        widget = self._get_text_widget()
        core = text.strip("\n")
        if not core:
            return
        insert_index = widget.index(tk.INSERT)
        prefix = ""
        suffix = ""
        line, column = map(int, insert_index.split("."))
        if column != 0:
            prefix = "\n"
        elif insert_index != "1.0":
            prev_char = widget.get(f"{insert_index}-1c", insert_index)
            if prev_char != "\n":
                prefix = "\n"
        try:
            next_char = widget.get(insert_index, f"{insert_index}+1c")
        except tk.TclError:
            next_char = ""
        if next_char != "\n":
            suffix = "\n"
        widget.insert(tk.INSERT, f"{prefix}{core}{suffix}")

    def _get_target_widget(self):
        widget = self.app.root.focus_get()
        if isinstance(widget, (tk.Text, tk.Entry, ttk.Entry)):
            return widget
        return self.app.text

    def _get_text_widget(self) -> tk.Text:
        widget = self.app.root.focus_get()
        if isinstance(widget, tk.Text):
            return widget
        return self.app.text

    def _get_selection_range(self, widget) -> tuple[str, str] | None:
        try:
            start = widget.index("sel.first")
            end = widget.index("sel.last")
            return start, end
        except tk.TclError:
            return None

    def _get_selection_text(self, widget) -> str | None:
        selection = self._get_selection_range(widget)
        if not selection:
            return None
        start, end = selection
        try:
            return widget.get(start, end)
        except tk.TclError:
            return None

    def _replace_selection(self, widget, text: str) -> bool:
        selection = self._get_selection_range(widget)
        if not selection:
            return False
        start, end = selection
        try:
            widget.delete(start, end)
            widget.insert(start, text)
        except tk.TclError:
            return False
        return True

    def _wrap_selection(self, widget, prefix: str, suffix: str) -> bool:
        selection = self._get_selection_range(widget)
        if not selection:
            return False
        start, end = selection
        try:
            selected = widget.get(start, end)
            widget.delete(start, end)
            widget.insert(start, f"{prefix}{selected}{suffix}")
        except tk.TclError:
            return False
        return True

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        if not value:
            return False
        value = value.strip()
        if not value or " " in value:
            return False
        if re.match(r"(?i)^(https?://|ftp://|mailto:|www\.)", value):
            return True
        return bool(re.match(r"(?i)^[\w.-]+\.[a-z]{2,}(/.*)?$", value))

    @staticmethod
    def _normalize_url(value: str) -> str:
        if not value:
            return value
        value = value.strip()
        if re.match(r"(?i)^(https?://|ftp://|mailto:)", value):
            return value
        if value.startswith("www."):
            return f"https://{value}"
        if re.match(r"(?i)^[\w.-]+\.[a-z]{2,}(/.*)?$", value):
            return f"https://{value}"
        return value

    def _apply_checklist_to_selection(self, widget: tk.Text) -> bool:
        selection = self._get_selection_range(widget)
        if not selection:
            return False
        start, end = selection
        try:
            selected = widget.get(start, end)
        except tk.TclError:
            return False
        lines = selected.splitlines(keepends=True)
        updated_lines = []
        for line in lines:
            if not line.strip():
                updated_lines.append(line)
                continue
            line_break = "\n" if line.endswith("\n") else ""
            body = line.rstrip("\n")
            indent_len = len(body) - len(body.lstrip(" \t"))
            indent = body[:indent_len]
            content = body[indent_len:]
            stripped = content.lstrip()
            if self._is_checklist_line(stripped):
                updated_lines.append(line)
            else:
                updated_lines.append(f"{indent}\u2610 {content}{line_break}")
        return self._replace_selection(widget, "".join(updated_lines))

    @staticmethod
    def _is_checklist_line(text: str) -> bool:
        check = ("\u2610", "\u2611", "[ ]", "[x]", "[X]")
        if text.startswith(check):
            return True
        for marker in ("- ", "* ", "+ "):
            if text.startswith(marker):
                rest = text[len(marker) :]
                if rest.startswith(check):
                    return True
        i = 0
        while i < len(text) and text[i].isdigit():
            i += 1
        if i > 0 and text[i : i + 2] in (". ", ") "):
            rest = text[i + 2 :]
            if rest.startswith(check):
                return True
        return False

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_dialog_texts("insert", language)

    def _get_templates(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        base = dict(pick_texts(INSERT_TEMPLATES, language))
        overrides = getattr(self.app, "template_overrides", {})
        if isinstance(overrides, dict):
            for key, value in overrides.items():
                if not isinstance(key, str):
                    continue
                resolved = self._resolve_template_override(value, language)
                if resolved is not None:
                    base[key] = resolved
        return base

    @staticmethod
    def _resolve_template_override(value: object, language: str) -> str | None:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            lang_value = value.get(language)
            if isinstance(lang_value, str):
                return lang_value
            default_value = value.get("default")
            if isinstance(default_value, str):
                return default_value
            es_value = value.get("es")
            if isinstance(es_value, str):
                return es_value
        return None

    def _language(self) -> str:
        return getattr(self.app, "language_name", "es")

    def _datetime_format(self) -> str:
        return getattr(self.app, "datetime_format", "%Y-%m-%d %H:%M")

    def _date_format(self) -> str:
        return getattr(self.app, "date_format", "%Y-%m-%d")

    def _collect_template_issues(self) -> list[str]:
        texts = get_dialog_texts("templates", self._language())
        overrides = getattr(self.app, "template_overrides", {})
        if not isinstance(overrides, dict):
            return [texts["invalid_value"]]
        issues: list[str] = []
        base_keys = set(INSERT_TEMPLATES.get("es", {}).keys())
        for key, value in overrides.items():
            if not isinstance(key, str):
                continue
            if key not in base_keys:
                issues.append(f"{texts['unknown_key']}: {key}")
            if isinstance(value, str):
                if not value.strip():
                    issues.append(f"{texts['empty_value']}: {key}")
                continue
            if isinstance(value, dict):
                if not value:
                    issues.append(f"{texts['empty_value']}: {key}")
                for lang, text in value.items():
                    if not isinstance(text, str):
                        issues.append(f"{texts['invalid_value']}: {key}")
                    elif not text.strip():
                        issues.append(f"{texts['empty_value']}: {key}")
                if self._resolve_template_override(value, self._language()) is None:
                    issues.append(f"{texts['missing_lang']}: {key}")
                continue
            issues.append(f"{texts['invalid_value']}: {key}")
        return issues

    def _build_preview_items(self, texts: dict[str, str]) -> list[dict[str, str]]:
        language = self._language()
        base = pick_texts(INSERT_TEMPLATES, language)
        overrides = getattr(self.app, "template_overrides", {})
        items: list[dict[str, str]] = []
        if not isinstance(overrides, dict):
            overrides = {}

        for key in sorted(base.keys()):
            override_value = overrides.get(key)
            resolved = (
                self._resolve_template_override(override_value, language)
                if override_value is not None
                else None
            )
            if resolved is not None:
                label = f"{key} *"
                origin = texts["origin_override"]
                content = resolved
            else:
                label = key
                origin = texts["origin_base"]
                content = base[key]
            items.append(
                {"key": key, "label": label, "origin": origin, "content": content}
            )

        unknown_keys = sorted(
            key for key in overrides.keys() if key not in base and isinstance(key, str)
        )
        for key in unknown_keys:
            resolved = self._resolve_template_override(overrides.get(key), language)
            items.append(
                {
                    "key": key,
                    "label": f"{key} ?",
                    "origin": texts["origin_override"],
                    "content": resolved or "",
                }
            )
        return items

    def configure_date_format(self) -> None:
        texts = get_dialog_texts("config", self._language())
        current = self._date_format()
        value = simpledialog.askstring(
            texts["date_prompt"],
            texts["date_prompt"],
            initialvalue=current,
            parent=self.app.root,
        )
        if value is None:
            return
        value = value.strip()
        if not value:
            return
        try:
            datetime.now().strftime(value)
        except ValueError:
            messagebox.showwarning(
                texts["date_prompt"],
                texts["format_invalid"],
                parent=self.app.root,
            )
            return
        if hasattr(self.app, "set_date_format"):
            self.app.set_date_format(value)
        messagebox.showinfo(
            texts["date_prompt"],
            texts["format_saved"],
            parent=self.app.root,
        )

    def configure_datetime_format(self) -> None:
        texts = get_dialog_texts("config", self._language())
        current = self._datetime_format()
        value = simpledialog.askstring(
            texts["datetime_prompt"],
            texts["datetime_prompt"],
            initialvalue=current,
            parent=self.app.root,
        )
        if value is None:
            return
        value = value.strip()
        if not value:
            return
        try:
            datetime.now().strftime(value)
        except ValueError:
            messagebox.showwarning(
                texts["datetime_prompt"],
                texts["format_invalid"],
                parent=self.app.root,
            )
            return
        if hasattr(self.app, "set_datetime_format"):
            self.app.set_datetime_format(value)
        messagebox.showinfo(
            texts["datetime_prompt"],
            texts["format_saved"],
            parent=self.app.root,
        )

    def handle_list_continue(self, event=None):
        widget = self._get_text_widget()
        if widget is not getattr(self.app, "text", None):
            return None
        if widget.tag_ranges("sel"):
            return None
        line_start = widget.index("insert linestart")
        line_end = widget.index("insert lineend")
        line = widget.get(line_start, line_end)
        continuation = self._get_list_continuation(line)
        if continuation is None:
            return None
        prefix, should_clear = continuation
        if should_clear:
            widget.delete(line_start, line_end)
            if prefix:
                widget.insert(line_start, prefix)
            return "break"
        widget.insert(tk.INSERT, f"\n{prefix}")
        return "break"

    def _get_list_continuation(self, line: str) -> tuple[str, bool] | None:
        if not line.strip():
            return None
        numbered = re.match(r"^(\s*)(\d+)([.)])\s+(.*)$", line)
        if numbered:
            indent, num, sep, rest = numbered.groups()
            if not rest.strip():
                return (indent, True)
            return (f"{indent}{int(num) + 1}{sep} ", False)

        checklist = re.match(r"^(\s*)([-*+])\s+\[( |x|X)\]\s+(.*)$", line)
        if checklist:
            indent, marker, _, rest = checklist.groups()
            if not rest.strip():
                return (indent, True)
            return (f"{indent}{marker} [ ] ", False)

        checkbox = re.match(r"^(\s*)([\u2610\u2611])\s+(.*)$", line)
        if checkbox:
            indent, _, rest = checkbox.groups()
            if not rest.strip():
                return (indent, True)
            return (f"{indent}\u2610 ", False)

        bullet = re.match(r"^(\s*)([-*+]|•)\s+(.*)$", line)
        if bullet:
            indent, marker, rest = bullet.groups()
            if not rest.strip():
                return (indent, True)
            return (f"{indent}{marker} ", False)

        return None

    def _open_settings(self) -> None:
        texts = get_dialog_texts("templates", self._language())
        path = self._settings_path()
        if not path.exists():
            messagebox.showinfo(
                texts["validation_title"],
                texts["settings_missing"],
                parent=self.app.root,
            )
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                webbrowser.open(path.as_uri())
        except OSError:
            messagebox.showinfo(
                texts["validation_title"],
                texts["settings_open_error"],
                parent=self.app.root,
            )

    def _settings_path(self) -> Path:
        path = getattr(self.app, "config_path", None)
        if isinstance(path, Path):
            return path
        return Path(__file__).resolve().parents[2] / "settings.json"
