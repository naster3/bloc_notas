from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..texts import get_menu_texts


class EditMenu:
    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._indices: dict[str, int] = {}
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        self.menu.add_command(
            label=texts["undo"], command=self.app.edit_undo, accelerator="Ctrl+Z"
        )
        undo_index = self.menu.index("end")
        if undo_index is not None:
            self._indices["undo"] = int(undo_index)
        self.menu.add_command(
            label=texts["redo"],
            command=self.app.edit_redo,
            accelerator="Ctrl+Y / Ctrl+Shift+Z",
        )
        redo_index = self.menu.index("end")
        if redo_index is not None:
            self._indices["redo"] = int(redo_index)
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["cut"],
            command=self.app.cut,
            accelerator="Ctrl+X",
        )
        cut_index = self.menu.index("end")
        if cut_index is not None:
            self._indices["cut"] = int(cut_index)
        self.menu.add_command(
            label=texts["copy"],
            command=self.app.copy,
            accelerator="Ctrl+C",
        )
        copy_index = self.menu.index("end")
        if copy_index is not None:
            self._indices["copy"] = int(copy_index)
        self.menu.add_command(
            label=texts["paste"],
            command=self.app.paste,
            accelerator="Ctrl+V",
        )
        paste_index = self.menu.index("end")
        if paste_index is not None:
            self._indices["paste"] = int(paste_index)
        self.menu.add_command(
            label=texts["delete"],
            command=self.app.delete_selection,
            accelerator="Del",
        )
        delete_index = self.menu.index("end")
        if delete_index is not None:
            self._indices["delete"] = int(delete_index)
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["select_all"],
            command=self.app.select_all,
            accelerator="Ctrl+A",
        )
        self.menu.add_command(
            label=texts["select_line"],
            command=self.app.select_line,
            accelerator="Ctrl+L",
        )
        self.menu.add_command(
            label=texts["select_word"],
            command=self.app.select_word,
            accelerator="Ctrl+D",
        )

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("edit", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._indices = {}
        self._build()

    def _refresh_states(self) -> None:
        widget = self._resolve_focus_widget()
        has_selection = self._has_selection(widget)
        self._set_state("cut", has_selection)
        self._set_state("copy", has_selection)
        self._set_state("delete", has_selection)
        self._set_state("undo", self._can_undo(widget))
        self._set_state("redo", self._can_redo(widget))

    def _set_state(self, key: str, enabled: bool) -> None:
        index = self._indices.get(key)
        if index is None:
            return
        state = "normal" if enabled else "disabled"
        self.menu.entryconfigure(index, state=state)

    def _resolve_focus_widget(self):
        widget = self.app.root.focus_get()
        if widget is None:
            return getattr(self.app, "text", None)
        if isinstance(widget, (tk.Text, tk.Entry, ttk.Entry, ttk.Combobox)):
            return widget
        parent = getattr(widget, "master", None)
        while parent is not None:
            if isinstance(parent, (tk.Text, tk.Entry, ttk.Entry, ttk.Combobox)):
                return parent
            parent = getattr(parent, "master", None)
        return getattr(self.app, "text", None)

    def _has_selection(self, widget) -> bool:
        if widget is None:
            return False
        if isinstance(widget, tk.Text):
            return bool(widget.tag_ranges("sel"))
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            try:
                return bool(widget.selection_present())
            except tk.TclError:
                return False
        return False

    def _can_undo(self, widget) -> bool:
        if not isinstance(widget, tk.Text):
            return False
        try:
            return bool(widget.edit("canundo"))
        except tk.TclError:
            return True

    def _can_redo(self, widget) -> bool:
        if not isinstance(widget, tk.Text):
            return False
        try:
            return bool(widget.edit("canredo"))
        except tk.TclError:
            return True
