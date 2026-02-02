from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont


class TagManager:
    MAX_OVERRIDE_TAGS = 48

    def __init__(self, text: tk.Text) -> None:
        self.text = text
        self.base_font: tkfont.Font | None = None
        self.bold_font: tkfont.Font | None = None
        self.italic_font: tkfont.Font | None = None
        self.bold_italic_font: tkfont.Font | None = None
        self._font_override_tags: dict[tuple[str, int], str] = {}
        self._tag_to_override: dict[str, tuple[str, int]] = {}
        self._override_order: list[tuple[str, int]] = []

    def set_base_font(self, base_font: tkfont.Font) -> None:
        self.base_font = base_font
        self.bold_font = base_font.copy()
        self.bold_font.configure(weight="bold")
        self.italic_font = base_font.copy()
        self.italic_font.configure(slant="italic")
        self.bold_italic_font = base_font.copy()
        self.bold_italic_font.configure(weight="bold", slant="italic")

        self.text.tag_configure("bold", font=self.bold_font)
        self.text.tag_configure("italic", font=self.italic_font)
        self.text.tag_configure("bold_italic", font=self.bold_italic_font)
        self.text.tag_configure("underline", underline=True)
        self.text.tag_configure("strike", overstrike=True)

        self.text.tag_raise("bold_italic")
        self.text.tag_raise("bold")
        self.text.tag_raise("italic")
        self.text.tag_raise("underline")
        self.text.tag_raise("strike")

    def apply_persistent_style(self, bold: bool, italic: bool) -> None:
        try:
            self.text.tag_remove("bold", "insert")
            self.text.tag_remove("italic", "insert")
            self.text.tag_remove("bold_italic", "insert")
        except tk.TclError:
            return

        if bold and italic:
            self.text.tag_add("bold_italic", "insert")
        elif bold:
            self.text.tag_add("bold", "insert")
        elif italic:
            self.text.tag_add("italic", "insert")

    def apply_font_override(self, family: str, size: int, start: str, end: str) -> None:
        if not self._ensure_base_font():
            return
        self.remove_font_overrides(start, end)
        tag = self._get_font_override_tag(family, size)
        self.text.tag_add(tag, start, end)

    def merge_font_override(
        self,
        start: str,
        end: str,
        *,
        family: str | None = None,
        size: int | None = None,
    ) -> None:
        if not self._ensure_base_font():
            return
        base_font = self.base_font
        if base_font is None:
            return
        current = self._get_override_key_at(start)
        base_family = str(base_font.cget("family"))
        base_size = int(base_font.cget("size"))
        resolved_family = family or (current[0] if current else base_family)
        resolved_size = size if size is not None else (current[1] if current else base_size)
        self.apply_font_override(resolved_family, int(resolved_size), start, end)

    def remove_font_overrides(self, start: str, end: str) -> None:
        for tag in self._font_override_tags.values():
            self.text.tag_remove(tag, start, end)

    def clear_basic_formatting(self, start: str, end: str) -> None:
        self.text.tag_remove("bold", start, end)
        self.text.tag_remove("italic", start, end)
        self.text.tag_remove("bold_italic", start, end)
        self.text.tag_remove("underline", start, end)
        self.text.tag_remove("strike", start, end)
        self.remove_font_overrides(start, end)

    def _get_font_override_tag(self, family: str, size: int) -> str:
        key = (family, size)
        tag = self._font_override_tags.get(key)
        if tag:
            self._mark_override_used(key)
            return tag
        safe = "".join(ch if ch.isalnum() else "_" for ch in f"{family}_{size}")
        tag = f"font_override_{safe}"
        if not self._ensure_base_font():
            return tag
        base_font = self.base_font
        if base_font is None:
            return tag
        font = base_font.copy()
        font.configure(family=family, size=size)
        self.text.tag_configure(tag, font=font)
        self._font_override_tags[key] = tag
        self._tag_to_override[tag] = key
        self._override_order.append(key)
        self._evict_overrides()
        return tag

    def _get_override_key_at(self, index: str) -> tuple[str, int] | None:
        for tag in self.text.tag_names(index):
            key = self._tag_to_override.get(tag)
            if key:
                return key
        return None

    def get_tags_at(self, index: str) -> set[str]:
        try:
            return set(self.text.tag_names(index))
        except tk.TclError:
            return set()

    def get_tags_in_range(self, start: str, end: str) -> set[str]:
        try:
            all_tags = self.text.tag_names()
        except tk.TclError:
            return set()
        tags: set[str] = set()
        for tag in all_tags:
            try:
                ranges = self.text.tag_ranges(tag)
            except tk.TclError:
                continue
            for i in range(0, len(ranges), 2):
                if self.text.compare(ranges[i + 1], ">", start) and self.text.compare(
                    ranges[i], "<", end
                ):
                    tags.add(tag)
                    break
        return tags

    def _ensure_base_font(self) -> bool:
        if self.base_font is not None:
            return True
        font_name = None
        try:
            font_name = self.text.cget("font")
        except tk.TclError:
            font_name = None
        base_font = None
        if font_name:
            try:
                base_font = tkfont.nametofont(font_name).copy()
            except (tk.TclError, ValueError):
                try:
                    base_font = tkfont.Font(font=font_name)
                except tk.TclError:
                    base_font = None
        if base_font is None:
            try:
                base_font = tkfont.nametofont("TkDefaultFont").copy()
            except tk.TclError:
                base_font = None
        if base_font is None:
            return False
        self.set_base_font(base_font)
        return True

    def apply_composite_style(
        self,
        start: str,
        end: str,
        *,
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        strike: bool | None = None,
    ) -> None:
        if bold is not None:
            self._toggle_tag("bold", "bold_italic", start, end, bold)
        if italic is not None:
            self._toggle_tag("italic", "bold_italic", start, end, italic)
        if underline is not None:
            self._set_tag("underline", start, end, underline)
        if strike is not None:
            self._set_tag("strike", start, end, strike)

    def _toggle_tag(
        self, primary: str, combined: str, start: str, end: str, enable: bool
    ) -> None:
        tags = set(self.text.tag_names(start))
        has_primary = primary in tags or combined in tags
        if enable and not has_primary:
            if combined in tags:
                return
            if primary == "bold":
                if "italic" in tags:
                    self.text.tag_remove("italic", start, end)
                    self.text.tag_add(combined, start, end)
                else:
                    self.text.tag_add(primary, start, end)
            elif primary == "italic":
                if "bold" in tags:
                    self.text.tag_remove("bold", start, end)
                    self.text.tag_add(combined, start, end)
                else:
                    self.text.tag_add(primary, start, end)
        if not enable and has_primary:
            self.text.tag_remove(primary, start, end)
            self.text.tag_remove(combined, start, end)
            if combined in tags:
                if primary == "bold":
                    self.text.tag_add("italic", start, end)
                elif primary == "italic":
                    self.text.tag_add("bold", start, end)

    def _set_tag(self, name: str, start: str, end: str, enable: bool) -> None:
        if enable:
            self.text.tag_add(name, start, end)
        else:
            self.text.tag_remove(name, start, end)

    def _mark_override_used(self, key: tuple[str, int]) -> None:
        if key in self._override_order:
            self._override_order.remove(key)
        self._override_order.append(key)

    def _evict_overrides(self) -> None:
        remaining: list[tuple[str, int]] = []
        for key in self._override_order:
            tag = self._font_override_tags.get(key)
            if not tag:
                continue
            try:
                if self.text.tag_ranges(tag):
                    remaining.append(key)
                    continue
                self.text.tag_delete(tag)
                self._font_override_tags.pop(key, None)
                self._tag_to_override.pop(tag, None)
            except tk.TclError:
                continue
        self._override_order = remaining

    def garbage_collect_overrides(self) -> None:
        for key, tag in list(self._font_override_tags.items()):
            try:
                if not self.text.tag_ranges(tag):
                    self.text.tag_delete(tag)
                    self._font_override_tags.pop(key, None)
                    self._tag_to_override.pop(tag, None)
            except tk.TclError:
                continue
        self._override_order = [
            key for key in self._override_order if key in self._font_override_tags
        ]
