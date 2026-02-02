from __future__ import annotations

from pathlib import Path
import os
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from ..ui.shortcuts import SECTION_ORDER, SECTION_TITLES, SHORTCUTS
from ..ui.texts import HELP_TEXTS, get_help_changes, pick_texts
from ..app import APP_TITLE, APP_VERSION


class HelpController:
    def __init__(self, app) -> None:
        self.app = app

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return pick_texts(HELP_TEXTS, language)

    def _build_help_body(self) -> str:
        texts = self._get_texts()
        language = getattr(self.app, "language_name", "es")
        lines = [f"{texts['quick_title']}:"]
        for section in SECTION_ORDER:
            section_titles = SECTION_TITLES.get(section, {})
            section_title = section_titles.get(language, section_titles.get("es", ""))
            if section_title:
                lines.append(f"{section_title}:")
            for item in SHORTCUTS.get(section, []):
                label = item["label"].get(language, item["label"]["es"])
                keys = item.get("keys")
                if keys:
                    lines.append(f"{keys} {label}")
                else:
                    lines.append(label)
            lines.append("")
        return "\n".join(lines).strip()

    def show_help(self) -> None:
        texts = self._get_texts()
        self._show_text_dialog(
            texts["help_title"],
            self._build_help_body(),
            include_readme=True,
        )

    def show_about(self) -> None:
        texts = self._get_texts()
        changes = get_help_changes(getattr(self.app, "language_name", "es"))
        lines = [
            f"{APP_TITLE}",
            texts["about_body"],
            f"{texts['version_label']}: {APP_VERSION}",
            "",
            f"{texts['changes_title']}:",
        ]
        for change in changes:
            lines.append(f"- {change}")
        body = "\n".join(lines).strip()
        self._show_text_dialog(
            texts["about_title"],
            body,
            include_readme=True,
        )

    def show_shortcuts(self) -> None:
        texts = self._get_texts()
        self._show_text_dialog(
            texts["quick_title"],
            self._build_help_body(),
            include_readme=False,
        )

    def show_changes(self) -> None:
        texts = self._get_texts()
        changes = get_help_changes(getattr(self.app, "language_name", "es"))
        lines = [f"{texts['changes_title']}:"] + [f"- {item}" for item in changes]
        body = "\n".join(lines).strip()
        self._show_text_dialog(
            texts["changes_title"],
            body,
            include_readme=False,
        )

    def open_readme(self) -> None:
        self._open_readme()

    def _show_text_dialog(self, title: str, body: str, include_readme: bool) -> None:
        dialog = tk.Toplevel(self.app.root)
        dialog.title(title)
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        frame = ttk.Frame(dialog, padding=(12, 10))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = tk.Text(frame, wrap="word", width=68, height=20)
        text.insert("1.0", body)
        text.config(state="disabled")
        text.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.config(yscrollcommand=scroll.set)

        texts = self._get_texts()
        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        if include_readme:
            ttk.Button(
                buttons, text=texts["open_readme"], command=self._open_readme
            ).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text=texts["close"], command=dialog.destroy).grid(
            row=0, column=1
        )

        dialog.bind("<Escape>", lambda event: dialog.destroy())

    def _open_readme(self) -> None:
        texts = self._get_texts()
        path = self._readme_path()
        if not path.exists():
            messagebox.showinfo(
                texts["help_title"],
                texts["readme_missing"],
                parent=self.app.root,
            )
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                webbrowser.open(path.as_uri())
        except OSError:
            messagebox.showinfo(
                texts["help_title"],
                texts["readme_open_error"],
                parent=self.app.root,
            )

    def _readme_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "README.md"

    def has_readme(self) -> bool:
        return self._readme_path().exists()
