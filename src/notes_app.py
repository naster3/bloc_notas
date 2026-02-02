from __future__ import annotations

from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from .app import App, APP_TITLE
from .settings_store import SettingsStore
from .storage_sqlite import NoteStore
from .controllers.edit import EditController
from .controllers.formatting import FormattingController
from .controllers.help import HelpController
from .controllers.insert import InsertController
from .controllers.notes import NotesController
from .controllers.search import SearchController
from .controllers.view import ViewController
from .ui.menus.menu_bar import MenuBar
from .ui.shortcut_manager import ShortcutManager
from .ui.toolbar import Toolbar
from .ui.sidebar import Sidebar
from .ui.editor import Editor
from .ui.statusbar import StatusBar


AUTOSAVE_MS = 3000


class NotesApp(App):
    _FORWARDED_METHODS = {
        "new_note",
        "save_current",
        "delete_note",
        "export_txt",
        "export_md",
        "import_md",
        "on_close",
        "refresh_list",
        "on_select",
        "on_text_modified",
        "on_search_change",
        "get_editor_content",
        "edit_undo",
        "edit_redo",
        "cut",
        "copy",
        "paste",
        "delete_selection",
        "select_all",
        "select_line",
        "select_word",
        "toggle_bold",
        "toggle_italic",
        "toggle_underline",
        "toggle_strike",
        "reset_format",
        "open_font_dialog",
        "choose_text_color",
        "choose_bg_color",
        "increase_font_size",
        "decrease_font_size",
        "reset_font_size",
        "clear_selection_formatting",
        "insert_separator",
        "insert_heading",
        "insert_h1",
        "insert_h2",
        "insert_h3",
        "insert_list",
        "insert_bullets",
        "insert_numbered",
        "insert_checklist",
        "insert_link_template",
        "insert_link_prompt",
        "insert_inline_code",
        "insert_code_block",
        "insert_quick_note",
        "insert_meeting",
        "insert_todo",
        "insert_journal",
        "insert_date",
        "insert_datetime",
        "show_help",
        "show_shortcuts",
        "show_changes",
        "open_readme",
        "show_about",
        "has_readme",
        "show_templates_preview",
        "validate_templates",
        "configure_date_format",
        "configure_datetime_format",
        "handle_list_continue",
        "focus_search",
        "find_in_note",
        "find_next",
        "find_prev",
        "replace_one",
        "replace_all",
        "validate_regex_toggle",
        "update_search_highlights",
        "toggle_wrap",
        "toggle_statusbar",
        "toggle_focus_mode",
        "zoom_in",
        "zoom_out",
        "zoom_reset",
        "reset_view",
        "apply_view_settings",
        "garbage_collect_tags",
        "_update_format_tags",
        "_normalize_weight",
        "_normalize_slant",
        "_apply_text_theme",
        "_hide_placeholder",
        "_render_statusbar",
        "_schedule_highlight_update",
    }

    def __init__(
        self,
        root: tk.Tk,
        db_path: str | Path | None = None,
        *,
        store: NoteStore | None = None,
        settings_store: SettingsStore | None = None,
    ) -> None:
        super().__init__(root, app_title=APP_TITLE, settings_store=settings_store)
        self.root.geometry("900x600")

        db_path = db_path or Path(__file__).resolve().parent.parent / "notes.db"
        self.store = store or NoteStore(db_path)

        self._init_state()
        self._init_controllers()
        self._bind_state_traces()
        self._build_ui()
        self._init_shortcuts()
        self._restore_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def __getattr__(self, name: str):
        if name not in self._FORWARDED_METHODS:
            raise AttributeError(f"{type(self).__name__} has no attribute {name}")
        for controller in self._controllers:
            value = getattr(controller, name, None)
            if callable(value):
                return value
        raise AttributeError(f"{type(self).__name__} has no attribute {name}")

    def _init_state(self) -> None:
        self.current_note_id = None
        self.note_ids = []
        self.dirty = False
        self.loading_note = False
        self.loading_list = False
        self.search_var = tk.StringVar()
        self.match_case_var = tk.BooleanVar(value=self.search_match_case)
        self.regex_var = tk.BooleanVar(value=self.search_regex)
        self.whole_word_var = tk.BooleanVar(value=self.search_whole_word)
        self.wrap_var = tk.BooleanVar(value=True)
        self.status_var = tk.BooleanVar(value=self.view_statusbar)
        self.focus_var = tk.BooleanVar(value=self.view_focus)
        self.text_font: tkfont.Font | None = None
        self.bold_font: tkfont.Font | None = None
        self.italic_font: tkfont.Font | None = None
        self.bold_italic_font: tkfont.Font | None = None
        self.autosave_delay = AUTOSAVE_MS
        self.autosave_job: str | None = None
        self.base_font_size = 0
        self.base_font_family = ""
        self.base_font_weight = "normal"
        self.base_font_slant = "roman"
        self.base_text_fg = ""
        self.base_text_bg = ""
        self.status_job: str | None = None
        self.last_search = self.search_term
        self.last_search_index = "1.0"
        self.menubar: MenuBar | None = None
        self.toolbar: Toolbar | None = None
        self.sidebar: Sidebar | None = None
        self.editor: Editor | None = None
        self.statusbar: StatusBar | None = None
        self.main_frame: ttk.Frame | None = None
        self.shortcuts: ShortcutManager | None = None
        self.text: tk.Text | None = None
        self.sort_mode = getattr(self, "sort_mode", "pinned")
        raw_tags = getattr(self, "tag_filters", [])
        if isinstance(raw_tags, (set, list, tuple)):
            self.tag_filters = [tag for tag in raw_tags if isinstance(tag, str) and tag]
        else:
            self.tag_filters = []

    def _init_controllers(self) -> None:
        self._controllers = [
            EditController(self),
            FormattingController(self),
            HelpController(self),
            InsertController(self),
            SearchController(self),
            ViewController(self),
            NotesController(self),
        ]

    def _bind_state_traces(self) -> None:
        self.search_var.trace_add("write", self.on_search_change)
        self.match_case_var.trace_add("write", self._on_search_option_change)
        self.regex_var.trace_add("write", self._on_search_option_change)
        self.whole_word_var.trace_add("write", self._on_search_option_change)

    def _restore_state(self) -> None:
        self.apply_view_settings()
        self.last_search = self.search_term
        if self.search_var.get():
            self.search_var.set("")
        else:
            self.refresh_list()
        self.sync_ui_state()

    def _init_shortcuts(self) -> None:
        self.shortcuts = ShortcutManager(self)
        self.shortcuts.bind_root()
        if isinstance(self.text, tk.Text):
            self.shortcuts.bind_text(self.text)

    def _build_ui(self) -> None:
        self._refresh_menus()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_main_frame()
        self._build_sidebar()
        self._build_editor()
        self._build_statusbar()
        self._apply_text_theme()

    def _build_toolbar(self) -> None:
        if self.toolbar is not None:
            return
        self.toolbar = Toolbar(self, self.root)
        self.toolbar.frame.grid(row=0, column=0, sticky="ew")

    def _build_main_frame(self) -> None:
        if self.main_frame is None:
            main = ttk.Frame(self.root, padding=(14, 10), style="App.TFrame")
            main.grid(row=1, column=0, sticky="nsew")
            main.columnconfigure(1, weight=1)
            main.rowconfigure(0, weight=1)
            self.main_frame = main

    def _build_sidebar(self) -> None:
        if self.sidebar is not None:
            return
        if self.main_frame is None:
            self._build_main_frame()
        if self.main_frame is None:
            return
        self.sidebar = Sidebar(self, self.main_frame)
        self.sidebar.frame.grid(row=0, column=0, sticky="nsew")

    def _build_editor(self) -> None:
        if self.editor is not None:
            return
        if self.main_frame is None:
            self._build_main_frame()
        if self.main_frame is None:
            return
        right = Editor(self, self.main_frame)
        self.editor = right
        right.frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self._init_editor_fonts()
        if self.shortcuts and isinstance(self.text, tk.Text):
            self.shortcuts.bind_text(self.text)

    def _build_statusbar(self) -> None:
        if self.statusbar is not None:
            return
        self.statusbar = StatusBar(self, self.root)
        self.statusbar.frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.statusbar.frame.grid_remove()

    def _init_editor_fonts(self) -> None:
        if not isinstance(self.text, tk.Text):
            return
        text_widget = self.text
        self.text_font = tkfont.nametofont(text_widget.cget("font")).copy()
        self.text_font.configure(family=self.editor_font_family, size=12)
        self.base_font_size = int(self.text_font.cget("size"))
        self.base_font_family = str(self.text_font.cget("family"))
        self.base_font_weight = self._normalize_weight(
            str(self.text_font.cget("weight"))
        )
        self.base_font_slant = self._normalize_slant(str(self.text_font.cget("slant")))
        text_widget.configure(font=self.text_font)
        self.base_text_fg = str(text_widget.cget("fg"))
        self.base_text_bg = str(text_widget.cget("bg"))
        self._update_format_tags()

    def _schedule_autosave(self) -> None:
        self.root.after(AUTOSAVE_MS, self.autosave_tick)

    def autosave_tick(self) -> None:
        if self.dirty:
            self.save_current()
        self._schedule_autosave()

    def set_theme(self, name: str) -> None:
        super().set_theme(name)
        if self.text_font:
            self.text_font.configure(family=self.editor_font_family)
            self.base_font_family = str(self.text_font.cget("family"))
            self._update_format_tags()
        if hasattr(self, "text"):
            self._apply_text_theme()
        self.sync_ui_state()

    def set_language(self, code: str) -> None:
        super().set_language(code)
        self._refresh_menus()
        self._refresh_ui_texts()
        if self.statusbar is not None:
            self.statusbar.render()
        self.sync_ui_state()

    def _refresh_menus(self) -> None:
        if self.menubar is None:
            self.menubar = MenuBar(self)
            self.root.config(menu=self.menubar.menu)
            return
        self.menubar.refresh()

    def _refresh_ui_texts(self) -> None:
        if hasattr(self, "toolbar") and self.toolbar:
            self.toolbar.update_texts()
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.update_texts()

    def sync_ui_state(self, *, refresh_texts: bool = False) -> None:
        if refresh_texts:
            if self.menubar:
                self.menubar.refresh()
            if self.toolbar:
                self.toolbar.update_texts()
            if self.sidebar:
                self.sidebar.update_texts()
        if self.menubar:
            self.menubar.refresh_states()
        if self.toolbar:
            self.toolbar.refresh_states()
        if self.statusbar and self.status_var.get():
            self.statusbar.render()

    def _on_search_option_change(self, *_) -> None:
        self.set_search_prefs(
            term=self.last_search,
            match_case=self.match_case_var.get(),
            regex=self.regex_var.get(),
            whole_word=self.whole_word_var.get(),
        )
        self.validate_regex_toggle()
        self.update_search_highlights()

    def reset_settings(self) -> None:
        config_path = getattr(self, "config_path", None)
        if isinstance(config_path, Path):
            try:
                config_path.unlink()
            except OSError:
                pass
        self._suspend_save = True
        try:
            self._config_extras = {}
            self.template_overrides = {}
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
            self.tag_filters = []
            self.theme_var.set("warm")
            self.language_var.set("es")
            self.set_theme("warm")
            self.set_language("es")
            self.search_var.set("")
            self.match_case_var.set(False)
            self.regex_var.set(False)
            self.whole_word_var.set(False)
            self.status_var.set(False)
            self.toggle_statusbar()
            self.focus_var.set(False)
            self.toggle_focus_mode()
            self.zoom_reset()
            if self.editor is not None:
                try:
                    self.editor.set_tabsize(self.tab_size)
                except Exception:
                    pass
        finally:
            self._suspend_save = False
