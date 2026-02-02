from __future__ import annotations

from collections.abc import Callable
import tkinter as tk


class ShortcutManager:
    def __init__(self, app) -> None:
        self.app = app
        self.root = app.root
        self._root_bindings: list[tuple[str, Callable[..., object]]] = []
        self._text_bindings: list[tuple[str, Callable[..., object]]] = []
        self._register_defaults()

    def bind_root(self) -> None:
        for sequence, handler in self._root_bindings:
            self.root.bind_all(sequence, handler)

    def bind_text(self, text: tk.Text) -> None:
        for sequence, handler in self._text_bindings:
            text.bind(sequence, handler)

    def _register_defaults(self) -> None:
        self._add_root("<Control-z>", "edit_undo")
        self._add_root("<Control-y>", "edit_redo")
        self._add_root("<Control-Shift-Z>", "edit_redo")
        self._add_root("<Control-x>", "cut")
        self._add_root("<Control-c>", "copy")
        self._add_root("<Control-v>", "paste")
        self._add_root("<Control-a>", "select_all")
        self._add_root("<Control-l>", "select_line")
        self._add_root("<Control-d>", "select_word")
        self._add_root("<Control-n>", "new_note")
        self._add_root("<Control-s>", "save_current")
        self._add_root("<Control-o>", "import_md")
        self._add_root("<Control-Shift-T>", "export_txt")
        self._add_root("<Control-Shift-M>", "export_md")
        self._add_root("<Control-Shift-Delete>", "delete_note")
        self._add_root("<Control-q>", "on_close")
        self._add_root("<Control-b>", "toggle_bold")
        self._add_root("<Control-i>", "toggle_italic")
        self._add_root("<Control-u>", "toggle_underline")
        self._add_root("<Control-Shift-X>", "toggle_strike")
        self._add_root("<Control-Shift-R>", "reset_format")
        self._add_root("<Control-Alt-F>", "open_font_dialog")
        self._add_root("<Control-Alt-C>", "choose_text_color")
        self._add_root("<Control-Alt-B>", "choose_bg_color")
        self._add_root("<Control-plus>", "increase_font_size")
        self._add_root("<Control-equal>", "increase_font_size")
        self._add_root("<Control-minus>", "decrease_font_size")
        self._add_root("<Control-0>", "reset_font_size")
        self._add_root("<Control-Shift-H>", "insert_heading")
        self._add_root("<Control-Shift-L>", "insert_list")
        self._add_root("<Control-Shift-S>", "insert_separator")
        self._add_root("<Control-Alt-1>", "insert_h1")
        self._add_root("<Control-Alt-2>", "insert_h2")
        self._add_root("<Control-Alt-3>", "insert_h3")
        self._add_root("<Control-Shift-B>", "insert_bullets")
        self._add_root("<Control-Shift-N>", "insert_numbered")
        self._add_root("<Control-Shift-C>", "insert_checklist")
        self._add_root("<Control-Alt-L>", "insert_link_template")
        self._add_root("<Control-Alt-U>", "insert_link_prompt")
        self._add_root("<Control-Alt-I>", "insert_inline_code")
        self._add_root("<Control-Alt-G>", "insert_code_block")
        self._add_root("<Control-Alt-T>", "insert_datetime")
        self._add_root("<Control-Alt-Q>", "insert_quick_note")
        self._add_root("<Control-Alt-M>", "insert_meeting")
        self._add_root("<Control-Alt-O>", "insert_todo")
        self._add_root("<Control-Alt-J>", "insert_journal")
        self._add_root("<Control-F2>", "focus_search")
        self._add_root("<Control-f>", "find_in_note")
        self._add_root("<Control-h>", "find_in_note")
        self._add_root("<F3>", "find_next")
        self._add_root("<Shift-F3>", "find_prev")
        self._add_root("<Control-Shift-K>", "clear_selection_formatting")
        self._add_root("<Control-Alt-plus>", "zoom_in")
        self._add_root("<Control-Alt-equal>", "zoom_in")
        self._add_root("<Control-Alt-minus>", "zoom_out")
        self._add_root("<Control-Alt-0>", "zoom_reset")
        self._add_root("<Control-Alt-R>", "reset_view")
        self._add_root("<Control-Shift-F>", "toggle_focus_mode")
        self._add_root("<Control-Shift-D>", "insert_date")

        self._add_text("<Return>", "handle_list_continue")

    def _add_root(self, sequence: str, method_name: str) -> None:
        self._root_bindings.append((sequence, self._call(method_name)))

    def _add_text(self, sequence: str, method_name: str) -> None:
        self._text_bindings.append((sequence, self._call_event(method_name)))

    def _call(self, method_name: str):
        def handler(event=None):
            func = getattr(self.app, method_name, None)
            if callable(func):
                return func()
            return None

        return handler

    def _call_event(self, method_name: str):
        def handler(event):
            func = getattr(self.app, method_name, None)
            if callable(func):
                return func(event)
            return None

        return handler
