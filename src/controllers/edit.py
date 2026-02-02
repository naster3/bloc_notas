from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class EditController:
    def __init__(self, app) -> None:
        self.app = app

    def _edit_event(self, sequence: str):
        widget = self._resolve_focus_widget()
        if widget is None:
            return "break"
        self._try_event(widget, sequence)
        return "break"

    @staticmethod
    def _try_event(widget, sequence: str) -> None:
        try:
            widget.event_generate(sequence)
        except tk.TclError:
            return

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
        return None

    def _copy_entry(self, widget) -> None:
        try:
            if widget.selection_present():
                text = widget.selection_get()
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(text)
        except tk.TclError:
            return

    def _cut_entry(self, widget) -> None:
        try:
            if widget.selection_present():
                start = widget.index("sel.first")
                end = widget.index("sel.last")
                text = widget.selection_get()
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append(text)
                widget.delete(start, end)
        except tk.TclError:
            return

    def _paste_entry(self, widget) -> None:
        try:
            text = self.app.root.clipboard_get()
        except tk.TclError:
            return
        try:
            if widget.selection_present():
                start = widget.index("sel.first")
                end = widget.index("sel.last")
                widget.delete(start, end)
            widget.insert(tk.INSERT, text)
        except tk.TclError:
            return

    def cut(self):
        widget = self._resolve_focus_widget()
        if widget is None:
            return "break"
        if isinstance(widget, tk.Text):
            self._try_event(widget, "<<Cut>>")
            return "break"
        self._cut_entry(widget)
        return "break"

    def copy(self):
        widget = self._resolve_focus_widget()
        if widget is None:
            return "break"
        if isinstance(widget, tk.Text):
            self._try_event(widget, "<<Copy>>")
            return "break"
        self._copy_entry(widget)
        return "break"

    def paste(self):
        widget = self._resolve_focus_widget()
        if widget is None:
            return "break"
        if isinstance(widget, tk.Text):
            self._try_event(widget, "<<Paste>>")
            return "break"
        self._paste_entry(widget)
        return "break"

    def delete_selection(self):
        widget = self._resolve_focus_widget()
        if widget is None:
            return "break"
        if isinstance(widget, tk.Text):
            try:
                widget.delete("sel.first", "sel.last")
            except tk.TclError:
                return "break"
            return "break"
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            try:
                if widget.selection_present():
                    start = widget.index("sel.first")
                    end = widget.index("sel.last")
                    widget.delete(start, end)
            except tk.TclError:
                return "break"
        return "break"

    def edit_undo(self):
        try:
            self.app.text.edit_undo()
        except tk.TclError:
            return "break"
        return "break"

    def edit_redo(self):
        try:
            self.app.text.edit_redo()
        except tk.TclError:
            return "break"
        return "break"

    def select_all(self):
        widget = self.app.root.focus_get()
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "1.0")
            widget.see("insert")
            return "break"
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.selection_range(0, tk.END)
            widget.icursor(0)
            return "break"
        return "break"

    def select_line(self):
        widget = self._resolve_focus_widget()
        if isinstance(widget, tk.Text):
            start = widget.index("insert linestart")
            end = widget.index("insert lineend")
            widget.tag_add("sel", start, end)
            widget.mark_set("insert", end)
            widget.see("insert")
            return "break"
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            try:
                widget.selection_range(0, tk.END)
                widget.icursor(0)
            except tk.TclError:
                return "break"
        return "break"

    def select_word(self):
        widget = self._resolve_focus_widget()
        if isinstance(widget, tk.Text):
            start = widget.index("insert wordstart")
            end = widget.index("insert wordend")
            widget.tag_add("sel", start, end)
            widget.mark_set("insert", end)
            widget.see("insert")
            return "break"
        if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            try:
                widget.selection_range(0, tk.END)
                widget.icursor(0)
            except tk.TclError:
                return "break"
        return "break"
