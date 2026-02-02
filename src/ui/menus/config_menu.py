from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from ..texts import get_dialog_texts, get_menu_texts


class ConfigMenu:
    LABEL = "Configuracion"

    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._theme_menu: tk.Menu | None = None
        self._language_menu: tk.Menu | None = None
        self._theme_indices: dict[str, int] = {}
        self._language_indices: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        self._theme_menu = None
        self._language_menu = None
        self._theme_indices = {}
        self._language_indices = {}
        texts = self._get_texts()
        tema = tk.Menu(self.menu, tearoff=0)
        self._theme_menu = tema
        self._theme_indices = {}
        for label, value in (
            (texts["warm"], "warm"),
            (texts["dark"], "dark"),
            (texts["minimal"], "minimal"),
            (texts["retro"], "retro"),
        ):
            tema.add_radiobutton(
                label=label,
                value=value,
                variable=self.app.theme_var,
                command=lambda v=value: self._set_theme(v),
            )
            theme_index = tema.index("end")
            if theme_index is not None:
                self._theme_indices[value] = int(theme_index)
        self.menu.add_cascade(label=texts["theme"], menu=tema)

        idioma = tk.Menu(self.menu, tearoff=0)
        self._language_menu = idioma
        self._language_indices = {}
        for label, value in (
            (texts["lang_es"], "es"),
            (texts["lang_en"], "en"),
            (texts["lang_pt"], "pt"),
            (texts["lang_fr"], "fr"),
        ):
            idioma.add_radiobutton(
                label=label,
                value=value,
                variable=self.app.language_var,
                command=lambda v=value: self._set_language(v),
            )
            lang_index = idioma.index("end")
            if lang_index is not None:
                self._language_indices[value] = int(lang_index)
        self.menu.add_cascade(label=texts["language"], menu=idioma)

        plantillas = tk.Menu(self.menu, tearoff=0)
        plantillas.add_command(
            label=texts["templates_preview"],
            command=self.app.show_templates_preview,
        )
        plantillas.add_command(
            label=texts["templates_validate"],
            command=self.app.validate_templates,
        )
        self.menu.add_cascade(label=texts["templates"], menu=plantillas)

        formatos = tk.Menu(self.menu, tearoff=0)
        formatos.add_command(
            label=texts["date_format"],
            command=self.app.configure_date_format,
        )
        formatos.add_command(
            label=texts["datetime_format"],
            command=self.app.configure_datetime_format,
        )
        formats_texts = get_dialog_texts("config", getattr(self.app, "language_name", "es"))
        self.menu.add_cascade(label=formats_texts["formats_label"], menu=formatos)
        self.menu.add_command(
            label=texts["open_settings"],
            command=self._open_settings,
        )
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["reset_settings"],
            command=self._confirm_reset,
        )
        self._refresh_disabled_items()

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("config", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._build()

    def _set_theme(self, value: str) -> None:
        self.app.set_theme(value)
        self._refresh_disabled_items()

    def _set_language(self, value: str) -> None:
        self.app.set_language(value)

    def _refresh_disabled_items(self) -> None:
        if not self._theme_menu or not self._language_menu:
            return
        current_theme = self.app.theme_var.get()
        for value, index in self._theme_indices.items():
            state = "disabled" if value == current_theme else "normal"
            self._theme_menu.entryconfigure(index, state=state)
        current_language = self.app.language_var.get()
        for value, index in self._language_indices.items():
            state = "disabled" if value == current_language else "normal"
            self._language_menu.entryconfigure(index, state=state)

    def _confirm_reset(self) -> None:
        texts = get_dialog_texts("config", getattr(self.app, "language_name", "es"))
        if not messagebox.askyesno(
            texts["reset_title"],
            texts["reset_confirm"],
            parent=self.app.root,
        ):
            return
        if hasattr(self.app, "reset_settings"):
            self.app.reset_settings()
        messagebox.showinfo(
            texts["reset_title"],
            texts["reset_done"],
            parent=self.app.root,
        )

    def _open_settings(self) -> None:
        texts = get_dialog_texts("config", getattr(self.app, "language_name", "es"))
        if not hasattr(self.app, "open_settings_file"):
            return
        try:
            ok, error = self.app.open_settings_file()
        except Exception as exc:
            ok, error = False, str(exc)
        if ok:
            return
        if error == "missing":
            messagebox.showwarning(
                texts["open_settings_title"],
                texts["open_settings_missing"],
                parent=self.app.root,
            )
            return
        messagebox.showerror(
            texts["open_settings_title"],
            texts["open_settings_error"].format(error=error),
            parent=self.app.root,
        )
