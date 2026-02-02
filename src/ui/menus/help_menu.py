from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts
from ...app import APP_VERSION


class HelpMenu:
    LABEL = "Ayuda"

    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._readme_index: int | None = None
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        self.menu.add_command(label=texts["help"], command=self.app.show_help)
        self.menu.add_command(label=texts["shortcuts"], command=self.app.show_shortcuts)
        self.menu.add_command(label=texts["changes"], command=self.app.show_changes)
        self.menu.add_command(label=texts["open_readme"], command=self.app.open_readme)
        readme_index = self.menu.index("end")
        self._readme_index = int(readme_index) if readme_index is not None else None
        self.menu.add_separator()
        about_label = texts.get("about_with_version", texts["about"]).format(
            version=APP_VERSION
        )
        self.menu.add_command(label=about_label, command=self.app.show_about)

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("help", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._readme_index = None
        self._build()

    def _refresh_states(self) -> None:
        if self._readme_index is None:
            return
        has_readme = True
        if hasattr(self.app, "has_readme"):
            try:
                has_readme = bool(self.app.has_readme())
            except Exception:
                has_readme = True
        state = "normal" if has_readme else "disabled"
        self.menu.entryconfigure(self._readme_index, state=state)
