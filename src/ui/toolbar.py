from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .texts import get_toolbar_texts


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str = "") -> None:
        self.widget = widget
        self.text = text
        self._tip: tk.Toplevel | None = None
        self.widget.bind("<Enter>", self._show, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<ButtonPress>", self._hide, add="+")

    def update(self, text: str) -> None:
        self.text = text

    def _show(self, event=None) -> None:
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 6
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except tk.TclError:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            bg="#2A2A2A",
            fg="white",
            padx=8,
            pady=4,
            relief="solid",
            borderwidth=1,
            justify="left",
        )
        label.pack()

    def _hide(self, event=None) -> None:
        if not self._tip:
            return
        try:
            self._tip.destroy()
        except tk.TclError:
            pass
        self._tip = None


class Toolbar:
    COMPACT_WIDTH = 820
    COMPACT_PADDING = (6, 4)
    NORMAL_PADDING = (10, 6)

    def __init__(self, app, parent) -> None:
        self.app = app
        self.frame = ttk.Frame(parent, padding=(14, 10), style="Toolbar.TFrame")
        self._compact = False
        self._buttons: dict[str, ttk.Button] = {}
        self._tooltips: dict[str, Tooltip] = {}
        self._all_buttons: list[ttk.Widget] = []
        self._separators: list[ttk.Separator] = []
        self._separator_map: dict[str, ttk.Separator] = {}
        self._groups: dict[str, ttk.Frame] = {}
        self.more_button: ttk.Menubutton | None = None
        self._more_menu: tk.Menu | None = None
        self._more_menu_items: dict[str, int] = {}
        self.readonly_label: ttk.Label | None = None
        self.new_button: ttk.Button | None = None
        self.save_button: ttk.Button | None = None
        self.delete_button: ttk.Button | None = None
        self.undo_button: ttk.Button | None = None
        self.redo_button: ttk.Button | None = None
        self.cut_button: ttk.Button | None = None
        self.copy_button: ttk.Button | None = None
        self.paste_button: ttk.Button | None = None
        self.bold_button: ttk.Button | None = None
        self.italic_button: ttk.Button | None = None
        self.underline_button: ttk.Button | None = None
        self.heading_button: ttk.Button | None = None
        self.list_button: ttk.Button | None = None
        self.link_button: ttk.Button | None = None
        self.date_button: ttk.Button | None = None
        self.wrap_button: ttk.Button | None = None
        self.status_button: ttk.Button | None = None
        self.focus_button: ttk.Button | None = None
        self.zoom_in_button: ttk.Button | None = None
        self.zoom_out_button: ttk.Button | None = None
        self.zoom_reset_button: ttk.Button | None = None
        self._build()

    def _build(self) -> None:
        file_group = self._add_group("file")
        self.new_button = self._add_button(
            file_group, "new", self.app.new_note, style="Ghost.TButton"
        )
        self.save_button = self._add_button(
            file_group, "save", self.app.save_current, style="Accent.TButton"
        )
        self.delete_button = self._add_button(
            file_group, "delete", self.app.delete_note, style="Ghost.TButton"
        )

        self._add_separator("file")

        edit_group = self._add_group("edit")
        self.undo_button = self._add_button(
            edit_group, "undo", self.app.edit_undo, style="Ghost.TButton"
        )
        self.redo_button = self._add_button(
            edit_group, "redo", self.app.edit_redo, style="Ghost.TButton"
        )
        self.cut_button = self._add_button(
            edit_group, "cut", self.app.cut, style="Ghost.TButton"
        )
        self.copy_button = self._add_button(
            edit_group, "copy", self.app.copy, style="Ghost.TButton"
        )
        self.paste_button = self._add_button(
            edit_group, "paste", self.app.paste, style="Ghost.TButton"
        )

        self._add_separator("edit")

        format_group = self._add_group("format")
        self.bold_button = self._add_button(
            format_group, "bold", self.app.toggle_bold, style="Ghost.TButton"
        )
        self.italic_button = self._add_button(
            format_group, "italic", self.app.toggle_italic, style="Ghost.TButton"
        )
        self.underline_button = self._add_button(
            format_group, "underline", self.app.toggle_underline, style="Ghost.TButton"
        )

        self._add_separator("format")

        insert_group = self._add_group("insert")
        self.heading_button = self._add_button(
            insert_group, "heading", self.app.insert_heading, style="Ghost.TButton"
        )
        self.list_button = self._add_button(
            insert_group, "list", self.app.insert_list, style="Ghost.TButton"
        )
        self.link_button = self._add_button(
            insert_group, "link", self.app.insert_link_prompt, style="Ghost.TButton"
        )
        self.date_button = self._add_button(
            insert_group, "date", self.app.insert_date, style="Ghost.TButton"
        )

        self._add_separator("insert")

        view_group = self._add_group("view")
        self.wrap_button = self._add_button(
            view_group, "wrap", self._toggle_wrap, style="Ghost.TButton"
        )
        self.status_button = self._add_button(
            view_group, "status", self._toggle_statusbar, style="Ghost.TButton"
        )
        self.focus_button = self._add_button(
            view_group, "focus", self._toggle_focus, style="Ghost.TButton"
        )
        self.zoom_in_button = self._add_button(
            view_group, "zoom_in", self.app.zoom_in, style="Ghost.TButton"
        )
        self.zoom_out_button = self._add_button(
            view_group, "zoom_out", self.app.zoom_out, style="Ghost.TButton"
        )
        self.zoom_reset_button = self._add_button(
            view_group, "zoom_reset", self.app.zoom_reset, style="Ghost.TButton"
        )

        self._build_more_menu()
        self.readonly_label = ttk.Label(self.frame, style="Status.TLabel")

        self.frame.bind("<Configure>", self._on_resize, add="+")
        self.update_texts()
        self._layout(self._compact)
        self.refresh_states()

    def update_texts(self) -> None:
        texts = self._get_texts()
        tips_raw = texts.get("tips")
        tips: dict[str, str] = tips_raw if isinstance(tips_raw, dict) else {}
        if self.new_button:
            self.new_button.config(text=self._text(texts, "new"))
            self._set_tooltip("new", tips.get("new", ""))
        if self.save_button:
            self.save_button.config(text=self._text(texts, "save"))
            self._set_tooltip("save", tips.get("save", ""))
        if self.delete_button:
            self.delete_button.config(text=self._text(texts, "delete"))
            self._set_tooltip("delete", tips.get("delete", ""))
        if self.undo_button:
            self.undo_button.config(text=self._text(texts, "undo"))
            self._set_tooltip("undo", tips.get("undo", ""))
        if self.redo_button:
            self.redo_button.config(text=self._text(texts, "redo"))
            self._set_tooltip("redo", tips.get("redo", ""))
        if self.cut_button:
            self.cut_button.config(text=self._text(texts, "cut"))
            self._set_tooltip("cut", tips.get("cut", ""))
        if self.copy_button:
            self.copy_button.config(text=self._text(texts, "copy"))
            self._set_tooltip("copy", tips.get("copy", ""))
        if self.paste_button:
            self.paste_button.config(text=self._text(texts, "paste"))
            self._set_tooltip("paste", tips.get("paste", ""))
        if self.bold_button:
            self.bold_button.config(text=self._text(texts, "bold"))
            self._set_tooltip("bold", tips.get("bold", ""))
        if self.italic_button:
            self.italic_button.config(text=self._text(texts, "italic"))
            self._set_tooltip("italic", tips.get("italic", ""))
        if self.underline_button:
            self.underline_button.config(text=self._text(texts, "underline"))
            self._set_tooltip("underline", tips.get("underline", ""))
        if self.heading_button:
            self.heading_button.config(text=self._text(texts, "heading"))
            self._set_tooltip("heading", tips.get("heading", ""))
        if self.list_button:
            self.list_button.config(text=self._text(texts, "list"))
            self._set_tooltip("list", tips.get("list", ""))
        if self.link_button:
            self.link_button.config(text=self._text(texts, "link"))
            self._set_tooltip("link", tips.get("link", ""))
        if self.date_button:
            self.date_button.config(text=self._text(texts, "date"))
            self._set_tooltip("date", tips.get("date", ""))
        if self.wrap_button:
            self.wrap_button.config(text=self._text(texts, "wrap"))
            self._set_tooltip("wrap", tips.get("wrap", ""))
        if self.status_button:
            self.status_button.config(text=self._text(texts, "status"))
            self._set_tooltip("status", tips.get("status", ""))
        if self.focus_button:
            self.focus_button.config(text=self._text(texts, "focus"))
            self._set_tooltip("focus", tips.get("focus", ""))
        if self.zoom_in_button:
            self.zoom_in_button.config(text=self._text(texts, "zoom_in"))
            self._set_tooltip("zoom_in", tips.get("zoom_in", ""))
        if self.zoom_out_button:
            self.zoom_out_button.config(text=self._text(texts, "zoom_out"))
            self._set_tooltip("zoom_out", tips.get("zoom_out", ""))
        if self.zoom_reset_button:
            self.zoom_reset_button.config(text=self._text(texts, "zoom_reset"))
            self._set_tooltip("zoom_reset", tips.get("zoom_reset", ""))
        if self.readonly_label is not None:
            self.readonly_label.config(text="")
        self._update_more_menu_labels(texts)
        self.refresh_states()

    def refresh_states(self) -> None:
        texts = self._get_texts()
        editor_ready = self._editor_ready()
        has_selection = self._has_selection()
        has_note = self._has_note()
        self._set_button_state(self.save_button, editor_ready and (has_note or self.app.dirty))
        self._set_button_state(self.delete_button, bool(self.app.current_note_id))
        self._set_button_state(self.undo_button, editor_ready)
        self._set_button_state(self.redo_button, editor_ready)
        self._set_button_state(self.cut_button, editor_ready and has_selection)
        self._set_button_state(self.copy_button, has_selection)
        self._set_button_state(self.paste_button, editor_ready)
        self._set_button_state(self.bold_button, editor_ready)
        self._set_button_state(self.italic_button, editor_ready)
        self._set_button_state(self.underline_button, editor_ready)
        self._set_button_state(self.heading_button, editor_ready)
        self._set_button_state(self.list_button, editor_ready)
        self._set_button_state(self.link_button, editor_ready)
        self._set_button_state(self.date_button, editor_ready)

        if self.save_button:
            if getattr(self.app, "saving", False):
                self.save_button.config(
                    text=self._text(texts, "saving"), state="disabled"
                )
            else:
                self.save_button.config(text=self._text(texts, "save"))

        tags = self._current_tags()
        self._set_toggle_style(
            self.bold_button, "bold" in tags or "bold_italic" in tags
        )
        self._set_toggle_style(
            self.italic_button, "italic" in tags or "bold_italic" in tags
        )
        self._set_toggle_style(self.underline_button, "underline" in tags)

        self._set_toggle_style(self.wrap_button, self._var_enabled("wrap_var"))
        self._set_toggle_style(self.status_button, self._var_enabled("status_var"))
        self._set_toggle_style(self.focus_button, self._var_enabled("focus_var"))

        if self.readonly_label is not None:
            if editor_ready:
                self.readonly_label.config(text="")
            else:
                self.readonly_label.config(text=self._text(texts, "readonly"))
        self._refresh_more_menu(editor_ready, has_selection)

    def _set_tooltip(self, key: str, text: str) -> None:
        widget = self._buttons.get(key)
        if not widget:
            return
        tip = self._tooltips.get(key)
        if tip is None:
            self._tooltips[key] = Tooltip(widget, text)
        else:
            tip.update(text)

    def _add_group(self, name: str) -> ttk.Frame:
        group = ttk.Frame(self.frame, style="Toolbar.TFrame")
        self._groups[name] = group
        return group

    def _add_separator(self, name: str) -> None:
        sep = ttk.Separator(self.frame, orient="vertical")
        self._separators.append(sep)
        self._separator_map[name] = sep

    def _add_button(
        self, parent: ttk.Frame, key: str, command, *, style: str
    ) -> ttk.Button:
        texts = self._get_texts()
        btn = ttk.Button(
            parent, text=self._text(texts, key, key), command=command, style=style
        )
        btn.pack(side="left", padx=(0, 6))
        self._buttons[key] = btn
        self._all_buttons.append(btn)
        return btn

    def _get_texts(self) -> dict[str, object]:
        language = getattr(self.app, "language_name", "es")
        return dict(get_toolbar_texts(language))

    @staticmethod
    def _text(texts: dict[str, object], key: str, fallback: str = "") -> str:
        value = texts.get(key, fallback)
        return value if isinstance(value, str) else fallback

    def _editor_ready(self) -> bool:
        editor = getattr(self.app, "editor", None)
        if editor and hasattr(editor, "is_readonly"):
            return not bool(editor.is_readonly())
        return True

    def _has_selection(self) -> bool:
        if not hasattr(self.app, "text"):
            return False
        try:
            ranges = self.app.text.tag_ranges("sel")
        except tk.TclError:
            return False
        return len(ranges) >= 2

    def _has_note(self) -> bool:
        if getattr(self.app, "current_note_id", None):
            return True
        try:
            content = self.app.get_editor_content()
        except Exception:
            content = ""
        return bool(content.strip())

    def _current_tags(self) -> set[str]:
        if not hasattr(self.app, "text"):
            return set()
        try:
            index = "sel.first" if self._has_selection() else "insert"
            return set(self.app.text.tag_names(index))
        except tk.TclError:
            return set()

    def _set_button_state(self, button: ttk.Button | None, enabled: bool) -> None:
        if not button:
            return
        button.config(state="normal" if enabled else "disabled")

    def _set_toggle_style(self, button: ttk.Button | None, active: bool) -> None:
        if not button:
            return
        style = "Accent.TButton" if active else "Ghost.TButton"
        button.config(style=style)

    def _var_enabled(self, name: str) -> bool:
        var = getattr(self.app, name, None)
        if var is None:
            return False
        try:
            return bool(var.get())
        except tk.TclError:
            return False

    def _toggle_wrap(self) -> None:
        self._toggle_var("wrap_var", self.app.toggle_wrap)

    def _toggle_statusbar(self) -> None:
        self._toggle_var("status_var", self.app.toggle_statusbar)

    def _toggle_focus(self) -> None:
        self._toggle_var("focus_var", self.app.toggle_focus_mode)

    def _toggle_var(self, name: str, callback) -> None:
        var = getattr(self.app, name, None)
        if var is None:
            return
        try:
            var.set(not bool(var.get()))
        except tk.TclError:
            return
        callback()
        self.refresh_states()

    def _build_more_menu(self) -> None:
        self.more_button = ttk.Menubutton(self.frame, style="Ghost.TButton")
        self._more_menu = tk.Menu(self.more_button, tearoff=0)
        self.more_button.config(menu=self._more_menu)

        self._add_more_command("heading", self.app.insert_heading)
        self._add_more_command("list", self.app.insert_list)
        self._add_more_command("link", self.app.insert_link_prompt)
        self._add_more_command("date", self.app.insert_date)
        self._more_menu.add_separator()
        self._add_more_check("wrap", "wrap_var", self.app.toggle_wrap)
        self._add_more_check("status", "status_var", self.app.toggle_statusbar)
        self._add_more_check("focus", "focus_var", self.app.toggle_focus_mode)
        self._more_menu.add_separator()
        self._add_more_command("zoom_in", self.app.zoom_in)
        self._add_more_command("zoom_out", self.app.zoom_out)
        self._add_more_command("zoom_reset", self.app.zoom_reset)

        self._all_buttons.append(self.more_button)

    def _add_more_command(self, key: str, command) -> None:
        if not self._more_menu:
            return
        self._more_menu.add_command(label=key, command=command)
        index = self._more_menu.index("end")
        if index is None:
            return
        self._more_menu_items[key] = int(index)

    def _add_more_check(self, key: str, var_name: str, command) -> None:
        if not self._more_menu:
            return
        var = getattr(self.app, var_name, None)
        if not isinstance(var, tk.Variable):
            return
        self._more_menu.add_checkbutton(label=key, variable=var, command=command)
        index = self._more_menu.index("end")
        if index is None:
            return
        self._more_menu_items[key] = int(index)

    def _update_more_menu_labels(self, texts: dict[str, object]) -> None:
        if not self.more_button or not self._more_menu:
            return
        self.more_button.config(text=self._text(texts, "more", "..."))
        for key, index in self._more_menu_items.items():
            label = self._text(texts, key, key)
            self._more_menu.entryconfigure(index, label=label)

    def _refresh_more_menu(self, editor_ready: bool, has_selection: bool) -> None:
        if not self._more_menu:
            return
        insert_enabled = editor_ready
        view_enabled = True
        for key in ("heading", "list", "link", "date"):
            self._set_menu_state(key, insert_enabled)
        for key in ("wrap", "status", "focus", "zoom_in", "zoom_out", "zoom_reset"):
            self._set_menu_state(key, view_enabled)

    def _set_menu_state(self, key: str, enabled: bool) -> None:
        if not self._more_menu:
            return
        index = self._more_menu_items.get(key)
        if index is None:
            return
        self._more_menu.entryconfigure(index, state="normal" if enabled else "disabled")

    def _on_resize(self, event=None) -> None:
        width = int(getattr(event, "width", 0))
        if not width:
            return
        compact = width < self.COMPACT_WIDTH
        if compact == self._compact:
            return
        self._compact = compact
        self._apply_compact(compact)

    def _apply_compact(self, compact: bool) -> None:
        self._layout(compact)
        padding = self.COMPACT_PADDING if compact else self.NORMAL_PADDING
        padx = (0, 4) if compact else (0, 6)
        for button in self._all_buttons:
            try:
                button.configure({"padding": padding})
            except tk.TclError:
                pass
            try:
                button.pack_configure(padx=padx)
            except tk.TclError:
                pass
        for sep in self._separators:
            try:
                sep.pack_configure(padx=4 if compact else 8)
            except tk.TclError:
                pass

    def _layout(self, compact: bool) -> None:
        widgets: list[ttk.Widget] = []
        widgets.extend(self._groups.values())
        widgets.extend(self._separators)
        if self.more_button:
            widgets.append(self.more_button)
        if self.readonly_label:
            widgets.append(self.readonly_label)
        for widget in widgets:
            try:
                widget.pack_forget()
            except tk.TclError:
                pass

        self._groups["file"].pack(side="left")
        self._separator_map["file"].pack(side="left", fill="y", padx=8, pady=4)
        self._groups["edit"].pack(side="left")
        self._separator_map["edit"].pack(side="left", fill="y", padx=8, pady=4)
        self._groups["format"].pack(side="left")

        if compact:
            self._separator_map["format"].pack(side="left", fill="y", padx=8, pady=4)
            if self.more_button:
                self.more_button.pack(side="left", padx=(0, 6))
        else:
            self._separator_map["format"].pack(side="left", fill="y", padx=8, pady=4)
            self._groups["insert"].pack(side="left")
            self._separator_map["insert"].pack(side="left", fill="y", padx=8, pady=4)
            self._groups["view"].pack(side="left")

        if self.readonly_label is not None:
            self.readonly_label.pack(side="right", padx=(8, 0))
