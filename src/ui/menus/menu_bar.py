from __future__ import annotations

import tkinter as tk
from typing import Any

from .config_menu import ConfigMenu
from .edit_menu import EditMenu
from .file_menu import FileMenu
from .format_menu import FormatMenu
from .help_menu import HelpMenu
from .insert_menu import InsertMenu
from .search_menu import SearchMenu
from .view_menu import ViewMenu


class MenuBar:
    MENU_CLASSES = {
        "file": FileMenu,
        "edit": EditMenu,
        "search": SearchMenu,
        "config": ConfigMenu,
        "format": FormatMenu,
        "view": ViewMenu,
        "insert": InsertMenu,
        "help": HelpMenu,
    }
    ORDER = (
        "file",
        "edit",
        "search",
        "config",
        "format",
        "view",
        "insert",
        "help",
    )
    FOCUS_DISABLED = {"insert", "format", "search", "config", "help"}

    def __init__(self, app) -> None:
        self.app = app
        self.menu = tk.Menu(app.root)
        self._sections: dict[str, Any] = {}
        self._menu_indices: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        for name in self.ORDER:
            section = self._sections.get(name)
            if section is None:
                section_class = self.MENU_CLASSES[name]
                section = section_class(self.app, self.menu)
                self._sections[name] = section
            if not hasattr(section, "attach"):
                continue
            index = section.attach()
            self._menu_indices[name] = index
        self._apply_focus_state()

    def refresh(self) -> None:
        for name in self.ORDER:
            section = self._sections.get(name)
            if section is None:
                continue
            if hasattr(section, "refresh"):
                section.refresh()
            if name in self._menu_indices:
                index = self._menu_indices[name]
                if hasattr(section, "get_label"):
                    self.menu.entryconfigure(index, label=section.get_label())
        self._apply_focus_state()

    def refresh_states(self) -> None:
        for section in self._sections.values():
            if hasattr(section, "_refresh_states"):
                section._refresh_states()

    def set_focus_mode(self, enabled: bool) -> None:
        for name, index in self._menu_indices.items():
            if name in self.FOCUS_DISABLED:
                state = "disabled" if enabled else "normal"
                self.menu.entryconfigure(index, state=state)

    def _apply_focus_state(self) -> None:
        enabled = bool(getattr(self.app, "focus_var", None) and self.app.focus_var.get())
        self.set_focus_mode(enabled)
