from __future__ import annotations

from typing import Literal
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, colorchooser

from .tag_manager import TagManager


class FormattingController:
    def __init__(self, app) -> None:
        self.app = app
        self.persistent_bold = False
        self.persistent_italic = False
        self.min_font_size = 8
        self.max_font_size = 48
        self._tag_manager: TagManager | None = None

    def open_font_dialog(self) -> None:
        text_font = self.app.text_font
        if text_font is None:
            return
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Fuente")
        dialog.resizable(False, False)
        dialog.transient(self.app.root)
        dialog.grab_set()

        families = sorted(set(tkfont.families()))
        sizes = [str(size) for size in range(8, 49)]

        family_var = tk.StringVar(value=text_font.cget("family"))
        size_var = tk.StringVar(value=str(text_font.cget("size")))

        ttk.Label(dialog, text="Fuente:").grid(row=0, column=0, padx=8, pady=6)
        family_box = ttk.Combobox(
            dialog, textvariable=family_var, values=families, width=24
        )
        family_box.grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(dialog, text="Tamano:").grid(row=1, column=0, padx=8, pady=6)
        size_box = ttk.Combobox(dialog, textvariable=size_var, values=sizes, width=8)
        size_box.grid(row=1, column=1, padx=8, pady=6, sticky="w")

        def apply_font() -> None:
            family = family_var.get().strip() or text_font.cget("family")
            try:
                size = int(size_var.get())
            except ValueError:
                size = int(text_font.cget("size"))
            text_font.configure(family=family, size=size)
            self.app.base_font_family = str(text_font.cget("family"))
            self.app.base_font_size = int(text_font.cget("size"))
            self._update_format_tags()

        ttk.Button(dialog, text="Aplicar", command=apply_font).grid(
            row=2, column=0, padx=8, pady=10
        )
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).grid(
            row=2, column=1, padx=8, pady=10, sticky="e"
        )

        dialog.bind("<Return>", lambda event: apply_font())

    def increase_font_size(self, step: int = 1) -> None:
        self._adjust_font_size(step)

    def decrease_font_size(self, step: int = 1) -> None:
        self._adjust_font_size(-step)

    def reset_font_size(self) -> None:
        if not self.app.text_font:
            return
        self.app.text_font.configure(size=self.app.base_font_size)
        self._update_format_tags()

    def _adjust_font_size(self, delta: int) -> None:
        if not self.app.text_font:
            return
        size = int(self.app.text_font.cget("size"))
        size = max(self.min_font_size, min(self.max_font_size, size + delta))
        self.app.text_font.configure(size=size)
        self._update_format_tags()

    def choose_text_color(self) -> None:
        color = colorchooser.askcolor(initialcolor=self.app.text.cget("fg"))[1]
        if not color:
            return
        self.app.text.config(fg=color, insertbackground=color)

    def choose_bg_color(self) -> None:
        color = colorchooser.askcolor(initialcolor=self.app.text.cget("bg"))[1]
        if not color:
            return
        self.app.text.config(bg=color)

    def reset_format(self) -> None:
        if self.app.text_font:
            self.app.text_font.configure(
                family=self.app.base_font_family,
                size=self.app.base_font_size,
                weight=self.app.base_font_weight,
                slant=self.app.base_font_slant,
            )
            self._update_format_tags()
        self.app.text.config(
            fg=self.app.base_text_fg,
            bg=self.app.base_text_bg,
            insertbackground=self.app.base_text_fg,
        )

    @staticmethod
    def _normalize_weight(value: str) -> Literal["normal", "bold"]:
        return "bold" if value == "bold" else "normal"

    @staticmethod
    def _normalize_slant(value: str) -> Literal["roman", "italic"]:
        return "italic" if value == "italic" else "roman"

    def _update_format_tags(self) -> None:
        if not self.app.text_font:
            return
        manager = self._ensure_tag_manager()
        if not manager:
            return
        manager.set_base_font(self.app.text_font)
        manager.apply_persistent_style(self.persistent_bold, self.persistent_italic)

    def set_selection_font_family(self, family: str) -> None:
        selection = self._get_selection_range()
        if not selection:
            return
        if not self.app.text_font:
            return
        manager = self._ensure_tag_manager()
        if not manager:
            return
        manager.merge_font_override(*selection, family=family)

    def set_selection_font_size(self, size: int) -> None:
        selection = self._get_selection_range()
        if not selection:
            return
        if not self.app.text_font:
            return
        manager = self._ensure_tag_manager()
        if not manager:
            return
        manager.merge_font_override(*selection, size=int(size))

    def garbage_collect_tags(self) -> None:
        manager = self._ensure_tag_manager()
        if not manager:
            return
        manager.garbage_collect_overrides()

    def clear_selection_formatting(self) -> None:
        selection = self._get_selection_range()
        if not selection:
            return
        manager = self._ensure_tag_manager()
        if not manager:
            return
        start, end = selection
        manager.clear_basic_formatting(start, end)

    def _ensure_tag_manager(self) -> TagManager | None:
        if not hasattr(self.app, "text"):
            return None
        if self._tag_manager is None:
            self._tag_manager = TagManager(self.app.text)
        return self._tag_manager

    def _get_selection_range(self) -> tuple[str, str] | None:
        try:
            start = self.app.text.index("sel.first")
            end = self.app.text.index("sel.last")
            return start, end
        except tk.TclError:
            return None

    def _get_target_range(self) -> tuple[str, str] | None:
        try:
            start = self.app.text.index("sel.first")
            end = self.app.text.index("sel.last")
            return start, end
        except tk.TclError:
            start = self.app.text.index("insert wordstart")
            end = self.app.text.index("insert wordend")
            if start == end:
                return None
            return start, end

    def _apply_persistent_style(self) -> None:
        manager = self._ensure_tag_manager()
        if not manager:
            return
        manager.apply_persistent_style(self.persistent_bold, self.persistent_italic)

    def _toggle_persistent_bold(self) -> None:
        self.persistent_bold = not self.persistent_bold
        self._apply_persistent_style()

    def _toggle_persistent_italic(self) -> None:
        self.persistent_italic = not self.persistent_italic
        self._apply_persistent_style()

    def toggle_bold(self) -> None:
        target = self._get_selection_range()
        if not target:
            self._toggle_persistent_bold()
            return
        start, end = target
        manager = self._ensure_tag_manager()
        if not manager:
            return
        tags = set(self.app.text.tag_names(start))
        has_bold = "bold" in tags or "bold_italic" in tags
        manager.apply_composite_style(start, end, bold=not has_bold)

    def toggle_italic(self) -> None:
        target = self._get_selection_range()
        if not target:
            self._toggle_persistent_italic()
            return
        start, end = target
        manager = self._ensure_tag_manager()
        if not manager:
            return
        tags = set(self.app.text.tag_names(start))
        has_italic = "italic" in tags or "bold_italic" in tags
        manager.apply_composite_style(start, end, italic=not has_italic)

    def toggle_underline(self) -> None:
        target = self._get_target_range()
        if not target:
            return
        start, end = target
        manager = self._ensure_tag_manager()
        if not manager:
            return
        tags = set(self.app.text.tag_names(start))
        manager.apply_composite_style(start, end, underline="underline" not in tags)

    def toggle_strike(self) -> None:
        target = self._get_target_range()
        if not target:
            return
        start, end = target
        manager = self._ensure_tag_manager()
        if not manager:
            return
        tags = set(self.app.text.tag_names(start))
        manager.apply_composite_style(start, end, strike="strike" not in tags)
