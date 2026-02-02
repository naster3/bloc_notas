from __future__ import annotations

import tkinter as tk

from ..texts import get_menu_texts


class InsertMenu:
    def __init__(self, app, menubar: tk.Menu) -> None:
        self.app = app
        self.menubar = menubar
        self.menu = tk.Menu(self.menubar, tearoff=0)
        self._root_entries: list[int] = []
        self._build()
        self.menu.config(postcommand=self._refresh_states)

    def _build(self) -> None:
        texts = self._get_texts()
        self._add_root_command(
            label=texts["separator"],
            command=self.app.insert_separator,
            accelerator="Ctrl+Shift+S",
        )

        headers = tk.Menu(self.menu, tearoff=0)
        headers.add_command(
            label=texts["heading"],
            command=self.app.insert_heading,
            accelerator="Ctrl+Shift+H",
        )
        headers.add_command(
            label=texts["h1"],
            command=self.app.insert_h1,
            accelerator="Ctrl+Alt+1",
        )
        headers.add_command(
            label=texts["h2"],
            command=self.app.insert_h2,
            accelerator="Ctrl+Alt+2",
        )
        headers.add_command(
            label=texts["h3"],
            command=self.app.insert_h3,
            accelerator="Ctrl+Alt+3",
        )
        self.menu.add_cascade(label=texts["heading"], menu=headers)

        lists = tk.Menu(self.menu, tearoff=0)
        lists.add_command(
            label=texts["list"],
            command=self.app.insert_list,
            accelerator="Ctrl+Shift+L",
        )
        lists.add_command(
            label=texts["bullets"],
            command=self.app.insert_bullets,
            accelerator="Ctrl+Shift+B",
        )
        lists.add_command(
            label=texts["numbered"],
            command=self.app.insert_numbered,
            accelerator="Ctrl+Shift+N",
        )
        lists.add_command(
            label=texts["checklist"],
            command=self.app.insert_checklist,
            accelerator="Ctrl+Shift+C",
        )
        self.menu.add_cascade(label=texts["list"], menu=lists)

        templates = tk.Menu(self.menu, tearoff=0)
        templates.add_command(
            label=texts["quick_note"],
            command=self.app.insert_quick_note,
            accelerator="Ctrl+Alt+Q",
        )
        templates.add_command(
            label=texts["meeting"],
            command=self.app.insert_meeting,
            accelerator="Ctrl+Alt+M",
        )
        templates.add_command(
            label=texts["todo"],
            command=self.app.insert_todo,
            accelerator="Ctrl+Alt+O",
        )
        templates.add_command(
            label=texts["journal"],
            command=self.app.insert_journal,
            accelerator="Ctrl+Alt+J",
        )
        self.menu.add_cascade(label=texts["templates"], menu=templates)

        link_code = tk.Menu(self.menu, tearoff=0)
        link_code.add_command(
            label=texts["link"],
            command=self.app.insert_link_template,
            accelerator="Ctrl+Alt+L",
        )
        link_code.add_command(
            label=texts["insert_link"],
            command=self.app.insert_link_prompt,
            accelerator="Ctrl+Alt+U",
        )
        link_code.add_command(
            label=texts["code"],
            command=self.app.insert_inline_code,
            accelerator="Ctrl+Alt+I",
        )
        link_code.add_command(
            label=texts["code_block"],
            command=self.app.insert_code_block,
            accelerator="Ctrl+Alt+G",
        )
        self.menu.add_cascade(label=texts["link_code"], menu=link_code)

        dates = tk.Menu(self.menu, tearoff=0)
        dates.add_command(
            label=texts["date"],
            command=self.app.insert_date,
            accelerator="Ctrl+Shift+D",
        )
        dates.add_command(
            label=texts["datetime"],
            command=self.app.insert_datetime,
            accelerator="Ctrl+Alt+T",
        )
        self.menu.add_cascade(label=texts["date"], menu=dates)

    def attach(self) -> int:
        self.menubar.add_cascade(label=self.get_label(), menu=self.menu)
        index = self.menubar.index("end")
        if index is None:
            return 0
        return int(index)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_menu_texts("insert", language)

    def get_label(self) -> str:
        return self._get_texts()["label"]

    def refresh(self) -> None:
        self.menu.delete(0, "end")
        self._root_entries = []
        self._build()

    def _add_root_command(
        self, *, label: str, command, accelerator: str | None = None
    ) -> None:
        if accelerator:
            self.menu.add_command(
                label=label, command=command, accelerator=accelerator
            )
        else:
            self.menu.add_command(label=label, command=command)
        index = self.menu.index("end")
        if index is not None:
            self._root_entries.append(int(index))

    def _refresh_states(self) -> None:
        has_focus = self._focus_in_editor()
        state = "normal" if has_focus else "disabled"
        for index in self._root_entries:
            self.menu.entryconfigure(index, state=state)
        end_index = self.menu.index("end")
        if end_index is None:
            return
        for i in range(int(end_index) + 1):
            try:
                if self.menu.type(i) == "cascade":
                    self.menu.entryconfigure(i, state=state)
            except tk.TclError:
                continue

    def _focus_in_editor(self) -> bool:
        widget = self.app.root.focus_get()
        if widget is None:
            return False
        if widget is getattr(self.app, "text", None):
            return True
        parent = getattr(widget, "master", None)
        while parent is not None:
            if parent is getattr(self.app, "text", None):
                return True
            parent = getattr(parent, "master", None)
        return False
