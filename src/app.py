from __future__ import annotations

from pathlib import Path
import logging
import os
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from .settings_store import Settings, SettingsStore


APP_TITLE = "Bloc de notas"
APP_VERSION = "1.4.0"


class App:
    def __init__(
        self,
        root: tk.Tk,
        app_title: str = APP_TITLE,
        settings_store: SettingsStore | None = None,
    ) -> None:
        self.root = root
        self.app_title = app_title
        self.colors: dict[str, str] = {}
        self.ui_font_family = ""
        self.editor_font_family = ""
        self.config_path = Path(__file__).resolve().parent.parent / "settings.json"
        self._settings_store = settings_store or SettingsStore(self.config_path)
        if settings_store is not None:
            self.config_path = settings_store.path
        self._config_extras: dict[str, object] = {}
        self._config_warnings: list[str] = []
        self._save_job: str | None = None
        self._save_delay_ms = 350
        self.theme_name = "warm"
        self.language_name = "es"
        self.theme_var = tk.StringVar(value=self.theme_name)
        self.language_var = tk.StringVar(value=self.language_name)
        self.current_note_title: str | None = None
        self.template_overrides: dict[str, object] = {}
        self._suspend_save = False
        self.datetime_format = "%Y-%m-%d %H:%M"
        self.date_format = "%Y-%m-%d"
        self.search_term = ""
        self.search_match_case = False
        self.search_regex = False
        self.search_whole_word = False
        self.view_statusbar = False
        self.view_zoom = 100
        self.view_focus = False
        self.last_import_dir = ""
        self.tab_size = 4
        self.sort_mode = "pinned"
        self.tag_filters: list[str] = []
        self.saving = False

        self._load_config()
        self.apply_settings()

    def _load_config(self) -> None:
        settings, warnings, extras = self._settings_store.load()
        self._config_extras = extras
        if warnings:
            self._config_warnings.extend(warnings)
            for warning in warnings:
                logging.warning(warning)
            self._notify_config_warning()
        self._apply_loaded_settings(settings)

    def _save_config(self) -> None:
        self._schedule_save_config()

    def _apply_loaded_settings(self, settings: Settings) -> None:
        self.theme_name = settings.theme
        self.language_name = settings.language
        self.template_overrides = settings.templates
        self.datetime_format = settings.datetime_format
        self.date_format = settings.date_format
        self.search_term = settings.search.term
        self.search_match_case = settings.search.match_case
        self.search_regex = settings.search.regex
        self.search_whole_word = settings.search.whole_word
        self.view_statusbar = settings.view.status_bar
        self.view_zoom = settings.view.zoom
        self.view_focus = settings.view.focus
        self.last_import_dir = settings.last_import_dir
        self.tab_size = settings.tab_size
        self.sort_mode = settings.sidebar.sort_mode
        self.tag_filters = list(settings.sidebar.tags)

    def apply_settings(self) -> None:
        self.theme_var.set(self.theme_name)
        self.language_var.set(self.language_name)
        self._apply_theme()
        self._set_title(self.current_note_title)

    def _schedule_save_config(self) -> None:
        if self._suspend_save:
            return
        if self._save_job is not None:
            try:
                self.root.after_cancel(self._save_job)
            except tk.TclError:
                pass
        self._save_job = self.root.after(self._save_delay_ms, self._save_config_now)

    def _save_config_now(self) -> None:
        if self._suspend_save:
            return
        self._save_job = None
        settings = self._collect_settings()
        try:
            self._settings_store.save(settings, self._config_extras)
        except OSError as exc:
            message = f"No se pudo guardar settings.json: {exc}"
            self._config_warnings.append(message)
            logging.warning(message)
            self._notify_config_warning()

    def flush_settings(self) -> None:
        if self._save_job is not None:
            try:
                self.root.after_cancel(self._save_job)
            except tk.TclError:
                pass
            self._save_job = None
        self._save_config_now()

    def _collect_settings(self) -> Settings:
        return Settings(
            theme=self.theme_name,
            language=self.language_name,
            templates=self.template_overrides,
            datetime_format=self.datetime_format,
            date_format=self.date_format,
            search=self._collect_search(),
            view=self._collect_view(),
            last_import_dir=self.last_import_dir,
            tab_size=int(self.tab_size),
            sidebar=self._collect_sidebar(),
        )

    def _collect_search(self):
        from .settings_store import SearchSettings

        return SearchSettings(
            term=self.search_term,
            match_case=self.search_match_case,
            regex=self.search_regex,
            whole_word=self.search_whole_word,
        )

    def _collect_view(self):
        from .settings_store import ViewSettings

        return ViewSettings(
            status_bar=self.view_statusbar,
            zoom=self.view_zoom,
            focus=self.view_focus,
        )

    def _collect_sidebar(self):
        from .settings_store import SidebarSettings

        return SidebarSettings(
            sort_mode=self.sort_mode,
            tags=list({tag for tag in self.tag_filters if isinstance(tag, str) and tag}),
        )

    def _apply_theme(self) -> None:
        themes = {
            "warm": {
                "colors": {
                    "bg": "#F4F1EA",
                    "panel": "#FDFBF7",
                    "accent": "#2F6B66",
                    "accent_dark": "#24524E",
                    "text": "#1F1F1F",
                    "muted": "#6B6B6B",
                    "list_bg": "#FFFDF8",
                    "editor_bg": "#FFFEFA",
                    "selection": "#CDE7E5",
                },
                "ui_fonts": ["Trebuchet MS", "Candara", "Segoe UI", "Arial"],
                "editor_fonts": ["Georgia", "Cambria", "Times New Roman", "Arial"],
            },
            "dark": {
                "colors": {
                    "bg": "#1B1E22",
                    "panel": "#23272B",
                    "accent": "#5CBDB0",
                    "accent_dark": "#449589",
                    "text": "#E9EEF2",
                    "muted": "#A7B0BA",
                    "list_bg": "#1F2327",
                    "editor_bg": "#1E2226",
                    "selection": "#3A5E5B",
                },
                "ui_fonts": ["Segoe UI", "Candara", "Arial"],
                "editor_fonts": ["Consolas", "Cascadia Mono", "Courier New", "Arial"],
            },
            "minimal": {
                "colors": {
                    "bg": "#F8F9FB",
                    "panel": "#FFFFFF",
                    "accent": "#1E2A3A",
                    "accent_dark": "#141C27",
                    "text": "#111827",
                    "muted": "#6B7280",
                    "list_bg": "#FFFFFF",
                    "editor_bg": "#FFFFFF",
                    "selection": "#D7E3F4",
                },
                "ui_fonts": ["Arial", "Segoe UI", "Candara"],
                "editor_fonts": ["Cambria", "Georgia", "Times New Roman", "Arial"],
            },
            "retro": {
                "colors": {
                    "bg": "#EFE7D3",
                    "panel": "#F7F0DC",
                    "accent": "#B14A2B",
                    "accent_dark": "#8E3A21",
                    "text": "#2C2418",
                    "muted": "#6A5B4A",
                    "list_bg": "#F7F0DC",
                    "editor_bg": "#FBF6E8",
                    "selection": "#E4CDA7",
                },
                "ui_fonts": ["Trebuchet MS", "Verdana", "Arial"],
                "editor_fonts": ["Georgia", "Times New Roman", "Cambria", "Arial"],
            },
        }

        theme = themes.get(self.theme_name, themes["warm"])
        self.colors = theme["colors"]
        self.ui_font_family = self._pick_font(theme["ui_fonts"])
        self.editor_font_family = self._pick_font(theme["editor_fonts"])

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg=self.colors["bg"])
        style.configure("App.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("Toolbar.TFrame", background=self.colors["bg"])

        style.configure(
            "Title.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=(self.ui_font_family, 14, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=(self.ui_font_family, 11, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["muted"],
            font=(self.ui_font_family, 10),
        )
        style.configure(
            "Status.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=(self.ui_font_family, 9),
        )

        style.configure(
            "Ghost.TButton",
            padding=(10, 6),
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=(self.ui_font_family, 10),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", self.colors["selection"])],
        )
        style.configure(
            "Accent.TButton",
            padding=(10, 6),
            background=self.colors["accent"],
            foreground="white",
            font=(self.ui_font_family, 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent_dark"])],
        )
        style.configure(
            "Search.TEntry",
            fieldbackground=self.colors["list_bg"],
            foreground=self.colors["text"],
            insertcolor=self.colors["accent"],
            font=(self.ui_font_family, 10),
        )

    def _pick_font(self, preferred: list[str]) -> str:
        available = set(tkfont.families())
        for name in preferred:
            if name in available:
                return name
        return tkfont.nametofont("TkDefaultFont").cget("family")

    def _base_title(self) -> str:
        titles = {
            "es": "Bloc de notas",
            "en": "Notepad",
            "pt": "Bloco de notas",
            "fr": "Bloc-notes",
        }
        return titles.get(self.language_name, self.app_title)

    def _set_title(self, note_title: str | None = None) -> None:
        self.current_note_title = note_title
        base = self._base_title()
        if note_title:
            self.root.title(f"{base} - {note_title}")
        else:
            self.root.title(base)

    def set_theme(self, name: str) -> None:
        self.theme_name = name
        self.theme_var.set(name)
        self._apply_theme()
        self._save_config()

    def set_language(self, code: str) -> None:
        self.language_name = code
        self.language_var.set(code)
        self._set_title(self.current_note_title)
        self._save_config()

    def set_datetime_format(self, fmt: str) -> None:
        if not isinstance(fmt, str) or not fmt.strip():
            return
        self.datetime_format = fmt
        self._save_config()

    def set_date_format(self, fmt: str) -> None:
        if not isinstance(fmt, str) or not fmt.strip():
            return
        self.date_format = fmt
        self._save_config()

    def set_search_prefs(
        self,
        term: str | None = None,
        match_case: bool | None = None,
        regex: bool | None = None,
        whole_word: bool | None = None,
    ) -> None:
        if term is not None:
            self.search_term = term
        if match_case is not None:
            self.search_match_case = bool(match_case)
        if regex is not None:
            self.search_regex = bool(regex)
        if whole_word is not None:
            self.search_whole_word = bool(whole_word)
        self._save_config()

    def set_view_prefs(
        self,
        *,
        status_bar: bool | None = None,
        zoom: int | None = None,
        focus: bool | None = None,
    ) -> None:
        if status_bar is not None:
            self.view_statusbar = bool(status_bar)
        if zoom is not None:
            self.view_zoom = int(zoom)
        if focus is not None:
            self.view_focus = bool(focus)
        self._save_config()

    def set_last_import_dir(self, path: str) -> None:
        if not isinstance(path, str):
            return
        self.last_import_dir = path
        self._save_config()

    def set_tab_size(self, size: int) -> None:
        try:
            size = int(size)
        except (TypeError, ValueError):
            return
        if size <= 0:
            return
        if size == self.tab_size:
            return
        self.tab_size = size
        self._save_config()

    def set_sort_mode(self, mode: str) -> None:
        if not isinstance(mode, str):
            return
        if mode not in {"recent", "alpha", "pinned"}:
            return
        if mode == self.sort_mode:
            return
        self.sort_mode = mode
        self._save_config()

    def set_tag_filters(self, tags: list[str] | set[str] | tuple[str, ...]) -> None:
        if not isinstance(tags, (set, list, tuple)):
            return
        normalized = sorted({tag for tag in tags if isinstance(tag, str) and tag})
        if normalized == sorted(self.tag_filters):
            return
        self.tag_filters = normalized
        self._save_config()

    def get_config_path(self) -> str:
        return str(self.config_path)

    def get_config_warnings(self) -> list[str]:
        return list(self._config_warnings)

    def config_warning_count(self) -> int:
        return len(self._config_warnings)

    def _notify_config_warning(self) -> None:
        renderer = getattr(self, "_render_statusbar", None)
        if callable(renderer):
            try:
                renderer()
            except tk.TclError:
                pass

    def open_settings_file(self) -> tuple[bool, str]:
        path = self.config_path
        if not path.exists():
            return False, "missing"
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
                return True, ""
            if sys.platform == "darwin":
                result = subprocess.run(["open", str(path)], check=False)
            else:
                result = subprocess.run(["xdg-open", str(path)], check=False)
            if result.returncode != 0:
                return False, f"open failed ({result.returncode})"
        except Exception as exc:
            return False, str(exc)
        return True, ""


def main() -> None:
    root = tk.Tk()
    from .notes_app import NotesApp

    NotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
