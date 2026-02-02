from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts


class FileMenu:
    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._indices: dict[str, int] = {}
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        self.menu.add_command(
            label=texts["new"],
            command=self.app.new_note,
            accelerator="Ctrl+N",
        )
        self.menu.add_command(
            label=texts["save"],
            command=self.app.save_current,
            accelerator="Ctrl+S",
        )
        save_index = self.menu.index("end")
        if save_index is not None:
            self._indices["save"] = int(save_index)
        self.menu.add_command(
            label=texts["delete"],
            command=self.app.delete_note,
            accelerator="Ctrl+Shift+Del",
        )
        delete_index = self.menu.index("end")
        if delete_index is not None:
            self._indices["delete"] = int(delete_index)
        template_menu = tk.Menu(self.menu, tearoff=0)
        template_menu.add_command(
            label=texts["new_quick_note"],
            command=lambda: self._new_from_template(self.app.insert_quick_note),
        )
        template_menu.add_command(
            label=texts["new_meeting"],
            command=lambda: self._new_from_template(self.app.insert_meeting),
        )
        template_menu.add_command(
            label=texts["new_todo"],
            command=lambda: self._new_from_template(self.app.insert_todo),
        )
        template_menu.add_command(
            label=texts["new_journal"],
            command=lambda: self._new_from_template(self.app.insert_journal),
        )
        self.menu.add_cascade(label=texts["new_from_template"], menu=template_menu)
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["export_txt"],
            command=self.app.export_txt,
            accelerator="Ctrl+Shift+T",
        )
        export_txt_index = self.menu.index("end")
        if export_txt_index is not None:
            self._indices["export_txt"] = int(export_txt_index)
        self.menu.add_command(
            label=texts["export_md"],
            command=self.app.export_md,
            accelerator="Ctrl+Shift+M",
        )
        export_md_index = self.menu.index("end")
        if export_md_index is not None:
            self._indices["export_md"] = int(export_md_index)
        self.menu.add_command(
            label=texts["import_md"],
            command=self.app.import_md,
            accelerator="Ctrl+O",
        )
        self.menu.add_separator()
        self.menu.add_command(
            label=texts["exit"],
            command=self.app.on_close,
            accelerator="Ctrl+Q",
        )

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("file", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._indices = {}
        self._build()

    def _refresh_states(self) -> None:
        has_note = bool(getattr(self.app, "current_note_id", None))
        has_changes = bool(getattr(self.app, "dirty", False))
        has_content = False
        if hasattr(self.app, "get_editor_content"):
            try:
                has_content = bool(self.app.get_editor_content().strip())
            except Exception:
                has_content = False
        self._set_state("save", has_changes)
        self._set_state("delete", has_note)
        self._set_state("export_txt", has_note or has_content)
        self._set_state("export_md", has_note or has_content)

    def _set_state(self, key: str, enabled: bool) -> None:
        index = self._indices.get(key)
        if index is None:
            return
        state = "normal" if enabled else "disabled"
        self.menu.entryconfigure(index, state=state)

    def _new_from_template(self, insert_func) -> None:
        self.app.new_note()
        if hasattr(self.app, "_hide_placeholder"):
            try:
                self.app._hide_placeholder()
            except Exception:
                pass
        insert_func()
        if hasattr(self.app, "text"):
            try:
                self.app.text.focus_set()
            except tk.TclError:
                pass
