from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts


class ViewMenu:
    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._indices: dict[str, int] = {}
        self._zoom_label_index: int | None = None
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        zoom = tk.Menu(self.menu, tearoff=0)
        zoom.add_command(label=self._zoom_label(), state="disabled")
        zoom_index = zoom.index("end")
        self._zoom_label_index = int(zoom_index) if zoom_index is not None else None
        zoom.add_separator()
        zoom.add_command(
            label=texts["zoom_in"],
            command=self.app.zoom_in,
            accelerator="Ctrl+Alt+Plus",
        )
        zoom.add_command(
            label=texts["zoom_out"],
            command=self.app.zoom_out,
            accelerator="Ctrl+Alt+-",
        )
        zoom.add_command(
            label=texts["zoom_reset"],
            command=self.app.zoom_reset,
            accelerator="Ctrl+Alt+0",
        )
        self.menu.add_cascade(label=texts["zoom"], menu=zoom)
        zoom_menu_index = self.menu.index("end")
        if zoom_menu_index is not None:
            self._indices["zoom"] = int(zoom_menu_index)
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["reset_view"],
            command=self.app.reset_view,
            accelerator="Ctrl+Alt+R",
        )
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label=texts["wrap"],
            variable=self.app.wrap_var,
            command=self.app.toggle_wrap,
        )
        wrap_index = self.menu.index("end")
        if wrap_index is not None:
            self._indices["wrap"] = int(wrap_index)
        self.menu.add_checkbutton(
            label=texts["status"],
            variable=self.app.status_var,
            command=self.app.toggle_statusbar,
        )
        status_index = self.menu.index("end")
        if status_index is not None:
            self._indices["status"] = int(status_index)
        self.menu.add_checkbutton(
            label=texts["focus"],
            variable=self.app.focus_var,
            command=self.app.toggle_focus_mode,
            accelerator="Ctrl+Shift+F",
        )
        focus_index = self.menu.index("end")
        if focus_index is not None:
            self._indices["focus"] = int(focus_index)

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("view", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._indices = {}
        self._zoom_label_index = None
        self._build()

    def _refresh_states(self) -> None:
        has_editor = hasattr(self.app, "text")
        self._set_state("wrap", has_editor)
        if self._zoom_label_index is not None:
            try:
                zoom_menu = self.menu.nametowidget(
                    self.menu.entrycget(self._indices["zoom"], "menu")
                )
            except Exception:
                zoom_menu = None
            if zoom_menu is not None:
                zoom_menu.entryconfigure(self._zoom_label_index, label=self._zoom_label())

    def _set_state(self, key: str, enabled: bool) -> None:
        index = self._indices.get(key)
        if index is None:
            return
        state = "normal" if enabled else "disabled"
        self.menu.entryconfigure(index, state=state)

    def _zoom_label(self) -> str:
        texts = self._get_texts()
        zoom = int(getattr(self.app, "view_zoom", 100))
        return texts.get("zoom_label", "Zoom: {percent}%").format(percent=zoom)
