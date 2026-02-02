from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts


class SearchMenu:
    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._indices: dict[str, int] = {}
        self._last_search_index: int | None = None
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        self.menu.add_command(
            label=texts["list"],
            command=self.app.focus_search,
            accelerator="Ctrl+F2",
        )
        list_index = self.menu.index("end")
        if list_index is not None:
            self._indices["list"] = int(list_index)
        self.menu.add_command(
            label=texts["note"],
            command=self.app.find_in_note,
            accelerator="Ctrl+F",
        )
        note_index = self.menu.index("end")
        if note_index is not None:
            self._indices["note"] = int(note_index)
        self.menu.add_command(
            label=texts["replace_menu"],
            command=self.app.find_in_note,
            accelerator="Ctrl+H",
        )
        replace_index = self.menu.index("end")
        if replace_index is not None:
            self._indices["replace"] = int(replace_index)
        self.menu.add_command(
            label=texts["next"], command=self.app.find_next, accelerator="F3"
        )
        next_index = self.menu.index("end")
        if next_index is not None:
            self._indices["next"] = int(next_index)
        self.menu.add_command(
            label=texts["prev"], command=self.app.find_prev, accelerator="Shift+F3"
        )
        prev_index = self.menu.index("end")
        if prev_index is not None:
            self._indices["prev"] = int(prev_index)
        self.menu.add_separator()
        self.menu.add_command(label=self._last_search_label(), state="disabled")
        last_index = self.menu.index("end")
        self._last_search_index = int(last_index) if last_index is not None else None
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label=texts["match_case"],
            variable=self.app.match_case_var,
            command=self.app.update_search_highlights,
        )
        match_index = self.menu.index("end")
        if match_index is not None:
            self._indices["match_case"] = int(match_index)
        self.menu.add_checkbutton(
            label=texts["whole_word"],
            variable=self.app.whole_word_var,
            command=self.app.update_search_highlights,
        )
        whole_index = self.menu.index("end")
        if whole_index is not None:
            self._indices["whole_word"] = int(whole_index)
        self.menu.add_checkbutton(
            label=texts["regex"],
            variable=self.app.regex_var,
            command=self.app.update_search_highlights,
        )
        regex_index = self.menu.index("end")
        if regex_index is not None:
            self._indices["regex"] = int(regex_index)

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("search", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._indices = {}
        self._last_search_index = None
        self._build()

    def _refresh_states(self) -> None:
        has_content = False
        if hasattr(self.app, "get_editor_content"):
            try:
                has_content = bool(self.app.get_editor_content().strip())
            except Exception:
                has_content = False
        has_matches = False
        if hasattr(self.app, "text"):
            try:
                has_matches = bool(self.app.text.tag_ranges("search_match"))
            except tk.TclError:
                has_matches = False

        for key in ("note", "replace", "match_case", "whole_word", "regex"):
            self._set_state(key, has_content)

        for key in ("next", "prev"):
            self._set_state(key, has_content and has_matches)

        if self._last_search_index is not None:
            self.menu.entryconfigure(
                self._last_search_index, label=self._last_search_label()
            )

    def _set_state(self, key: str, enabled: bool) -> None:
        index = self._indices.get(key)
        if index is None:
            return
        state = "normal" if enabled else "disabled"
        self.menu.entryconfigure(index, state=state)

    def _last_search_label(self) -> str:
        texts = self._get_texts()
        term = getattr(self.app, "last_search", "")
        if not term:
            term = texts.get("last_search_empty", "-")
        return texts["last_search"].format(term=term)
