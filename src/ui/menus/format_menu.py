from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts


class FormatMenu:
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
            label=texts["bold"], command=self.app.toggle_bold, accelerator="Ctrl+B"
        )
        bold_index = self.menu.index("end")
        if bold_index is not None:
            self._indices["bold"] = int(bold_index)
        self.menu.add_command(
            label=texts["italic"],
            command=self.app.toggle_italic,
            accelerator="Ctrl+I",
        )
        italic_index = self.menu.index("end")
        if italic_index is not None:
            self._indices["italic"] = int(italic_index)
        self.menu.add_command(
            label=texts["underline"],
            command=self.app.toggle_underline,
            accelerator="Ctrl+U",
        )
        underline_index = self.menu.index("end")
        if underline_index is not None:
            self._indices["underline"] = int(underline_index)
        self.menu.add_command(
            label=texts["strike"],
            command=self.app.toggle_strike,
            accelerator="Ctrl+Shift+X",
        )
        strike_index = self.menu.index("end")
        if strike_index is not None:
            self._indices["strike"] = int(strike_index)
        self.menu.add_separator()
        font_menu = tk.Menu(self.menu, tearoff=0)
        font_menu.add_command(
            label=texts["font"],
            command=self.app.open_font_dialog,
            accelerator="Ctrl+Alt+F",
        )
        font_menu.add_separator()
        font_menu.add_command(
            label=texts["size_plus"],
            command=self.app.increase_font_size,
            accelerator="Ctrl+Plus",
        )
        font_menu.add_command(
            label=texts["size_minus"],
            command=self.app.decrease_font_size,
            accelerator="Ctrl+-",
        )
        font_menu.add_command(
            label=texts["size_reset"],
            command=self.app.reset_font_size,
            accelerator="Ctrl+0",
        )
        self.menu.add_cascade(label=texts["font_menu"], menu=font_menu)

        color_menu = tk.Menu(self.menu, tearoff=0)
        color_menu.add_command(
            label=texts["text_color"],
            command=self.app.choose_text_color,
            accelerator="Ctrl+Alt+C",
        )
        color_menu.add_command(
            label=texts["bg_color"],
            command=self.app.choose_bg_color,
            accelerator="Ctrl+Alt+B",
        )
        self.menu.add_cascade(label=texts["color_menu"], menu=color_menu)
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["clear_sel"],
            command=self.app.clear_selection_formatting,
            accelerator="Ctrl+Shift+K",
        )
        clear_index = self.menu.index("end")
        if clear_index is not None:
            self._indices["clear_sel"] = int(clear_index)
        self.menu.add_command(
            label=texts["reset"],
            command=self.app.reset_format,
            accelerator="Ctrl+Shift+R",
        )
        reset_index = self.menu.index("end")
        if reset_index is not None:
            self._indices["reset"] = int(reset_index)

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("format", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._indices = {}
        self._build()

    def _refresh_states(self) -> None:
        has_selection = False
        if hasattr(self.app, "text"):
            try:
                has_selection = bool(self.app.text.tag_ranges("sel"))
            except tk.TclError:
                has_selection = False
        for key in ("bold", "italic", "underline", "strike", "clear_sel"):
            self._set_state(key, has_selection)

    def _set_state(self, key: str, enabled: bool) -> None:
        index = self._indices.get(key)
        if index is None:
            return
        state = "normal" if enabled else "disabled"
        self.menu.entryconfigure(index, state=state)
