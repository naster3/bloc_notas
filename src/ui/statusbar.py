from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from .texts import STATUS_TEXTS, pick_texts


class StatusBar:
    def __init__(self, app, parent) -> None:
        self.app = app
        self.frame = ttk.Frame(parent, style="App.TFrame")
        self.frame.columnconfigure(0, weight=1)
        self.left_label = ttk.Label(self.frame, anchor="w", style="Status.TLabel")
        self.left_label.grid(row=0, column=0, sticky="w")
        self.right_frame = ttk.Frame(self.frame, style="App.TFrame")
        self.right_frame.grid(row=0, column=1, sticky="e")
        self._segment_labels: list[ttk.Label] = []
        self._segment_separators: list[ttk.Label] = []
        self._segments: dict[str, ttk.Label] = {}
        self._build_segments()

    def _build_segments(self) -> None:
        order = ["state", "readonly", "search", "focus", "zoom", "config"]
        for idx, key in enumerate(order):
            label = ttk.Label(self.right_frame, anchor="e", style="Status.TLabel")
            if key == "zoom":
                label.configure(cursor="hand2")
                label.bind("<Button-1>", self._on_zoom_click)
            if key == "focus":
                label.configure(cursor="hand2")
                label.bind("<Button-1>", self._on_focus_click)
            label.grid(row=0, column=idx * 2, sticky="e")
            self._segment_labels.append(label)
            self._segments[key] = label
            if idx < len(order) - 1:
                sep = ttk.Label(self.right_frame, text=" | ", style="Status.TLabel")
                sep.grid(row=0, column=idx * 2 + 1, sticky="e")
                self._segment_separators.append(sep)

    def show(self) -> None:
        self.frame.grid()
        self.schedule_render()

    def hide(self) -> None:
        self.frame.grid_remove()
        self.cancel_render()

    def schedule_render(self, delay: int = 200) -> None:
        if not self._is_visible():
            return
        self.cancel_render()
        self.app.status_job = self.app.root.after(delay, self.render)

    def cancel_render(self) -> None:
        job = getattr(self.app, "status_job", None)
        if job is None:
            return
        try:
            self.app.root.after_cancel(job)
        except tk.TclError:
            pass
        self.app.status_job = None

    def render(self) -> None:
        if not self._is_visible():
            return
        self.app.status_job = None
        texts = self._get_texts()
        line, col = self._cursor_position()
        selection = self._selection_length()
        content = self._content()
        lines = self._line_count()
        chars = len(content)
        words = self._word_count(content)
        left_parts = [
            f"{texts['line']}: {line}",
            f"{texts['col']}: {col}",
        ]
        if selection:
            left_parts.append(f"{texts['sel']}: {selection}")
        left_parts.extend(
            [
                f"{texts['lines']}: {lines}",
                f"{texts['words']}: {words}",
                f"{texts['chars']}: {chars}",
            ]
        )
        self.left_label.config(text=" | ".join(left_parts))
        self._update_segments(texts)

    def _update_segments(self, texts: dict[str, str]) -> None:
        state_text = self._save_state_text(texts)
        readonly_text = texts["readonly"] if self._is_readonly() else ""
        matches = self._search_matches()
        search_text = f"{texts['matches']}: {matches}" if matches else ""
        focus_text = texts["focus"] if self._focus_enabled() else ""
        zoom_value = getattr(self.app, "view_zoom", 100)
        if isinstance(zoom_value, (int, float, str)):
            try:
                zoom = int(zoom_value)
            except (TypeError, ValueError):
                zoom = 100
        else:
            zoom = 100
        zoom_text = f"{texts['zoom']}: {zoom}%"
        config_count = self._config_warning_count()
        config_text = f"{texts['config']}: {config_count}" if config_count else ""
        values = {
            "state": state_text,
            "readonly": readonly_text,
            "search": search_text,
            "focus": focus_text,
            "zoom": zoom_text,
            "config": config_text,
        }
        visible_flags: list[bool] = []
        order = ["state", "readonly", "search", "focus", "zoom", "config"]
        for key in order:
            label = self._segments[key]
            text = values.get(key, "")
            if text:
                label.config(text=text)
                label.grid()
                visible_flags.append(True)
            else:
                label.config(text="")
                label.grid_remove()
                visible_flags.append(False)
        for idx, sep in enumerate(self._segment_separators):
            if visible_flags[idx] and visible_flags[idx + 1]:
                sep.grid()
            else:
                sep.grid_remove()

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return pick_texts(STATUS_TEXTS, language)

    def _cursor_position(self) -> tuple[int, int]:
        try:
            index = self.app.text.index("insert")
        except tk.TclError:
            return (1, 1)
        if not isinstance(index, str):
            return (1, 1)
        line_str, col_str = index.split(".")
        line = self._safe_int(line_str, 1)
        col = self._safe_int(col_str, 0) + 1
        if line <= 0:
            return (1, 1)
        return (line, col)

    def _selection_length(self) -> int:
        try:
            ranges = self.app.text.tag_ranges("sel")
        except tk.TclError:
            return 0
        if len(ranges) < 2:
            return 0
        start, end = ranges[0], ranges[1]
        try:
            count = self.app.text.count(start, end, "chars")
            if count:
                return self._safe_int(count[0], 0)
        except tk.TclError:
            pass
        try:
            return len(self.app.text.get(start, end))
        except tk.TclError:
            return 0

    def _content(self) -> str:
        if hasattr(self.app, "get_editor_content"):
            return self.app.get_editor_content()
        try:
            return self.app.text.get("1.0", "end-1c")
        except tk.TclError:
            return ""

    def _line_count(self) -> int:
        try:
            index = self.app.text.index("end-1c")
            if not isinstance(index, str):
                return 0
            return self._safe_int(index.split(".")[0], 0)
        except (AttributeError, tk.TclError, ValueError):
            return 0

    @staticmethod
    def _word_count(content: str) -> int:
        if not content:
            return 0
        return len(re.findall(r"\S+", content))

    def _save_state_text(self, texts: dict[str, str]) -> str:
        if getattr(self.app, "saving", False):
            return texts["saving"]
        if getattr(self.app, "dirty", False):
            return texts["unsaved"]
        return texts["saved"]

    def _is_readonly(self) -> bool:
        editor = getattr(self.app, "editor", None)
        if editor and hasattr(editor, "is_readonly"):
            return bool(editor.is_readonly())
        return False

    def _focus_enabled(self) -> bool:
        focus_var = getattr(self.app, "focus_var", None)
        if focus_var is None:
            return False
        try:
            return bool(focus_var.get())
        except tk.TclError:
            return False

    def _search_matches(self) -> int:
        try:
            ranges = self.app.text.tag_ranges("search_match")
        except tk.TclError:
            return 0
        if not ranges:
            return 0
        return len(ranges) // 2

    def _is_visible(self) -> bool:
        try:
            return bool(self.frame.winfo_ismapped())
        except tk.TclError:
            return False

    def _config_warning_count(self) -> int:
        getter = getattr(self.app, "config_warning_count", None)
        if callable(getter):
            try:
                return self._safe_int(getter(), 0)
            except Exception:
                return 0
        warnings = getattr(self.app, "_config_warnings", None)
        if isinstance(warnings, list):
            return len(warnings)
        return 0

    @staticmethod
    def _safe_int(value: object, default: int) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    def _on_zoom_click(self, event=None) -> None:
        if hasattr(self.app, "zoom_reset"):
            self.app.zoom_reset()

    def _on_focus_click(self, event=None) -> None:
        if hasattr(self.app, "toggle_focus_mode"):
            self.app.focus_var.set(not self._focus_enabled())
            self.app.toggle_focus_mode()
