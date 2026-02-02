from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .texts import get_sidebar_texts


class Sidebar:
    def __init__(self, app, parent) -> None:
        self.app = app
        self.frame = ttk.Frame(parent, style="Panel.TFrame")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(4, weight=1)
        self.title_label: ttk.Label | None = None
        self.new_button: ttk.Button | None = None
        self.delete_button: ttk.Button | None = None
        self.sort_label: ttk.Label | None = None
        self.sort_combo: ttk.Combobox | None = None
        self.tags_label: ttk.Label | None = None
        self.tag_container: ttk.Frame | None = None
        self._sort_map: dict[str, str] = {}
        self._tags: list[str] = []
        self._build()

    def _build(self) -> None:
        texts = self._get_texts()
        header = ttk.Frame(self.frame, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        header.columnconfigure(3, weight=1)
        self.title_label = ttk.Label(
            header, text=texts["notes"], style="Section.TLabel"
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.new_button = ttk.Button(
            header,
            text=texts["new"],
            style="Ghost.TButton",
            command=self.app.new_note,
        )
        self.new_button.grid(row=0, column=1, padx=(6, 4))
        self.delete_button = ttk.Button(
            header,
            text=texts["delete"],
            style="Ghost.TButton",
            command=self.app.delete_note,
        )
        self.delete_button.grid(row=0, column=2, padx=(0, 6))
        self.app.notes_count = ttk.Label(header, text="0", style="Muted.TLabel")
        self.app.notes_count.grid(row=0, column=4, sticky="e")

        self.app.search_entry = ttk.Entry(
            self.frame, textvariable=self.app.search_var, style="Search.TEntry"
        )
        self.app.search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        sort_frame = ttk.Frame(self.frame, style="Panel.TFrame")
        sort_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
        sort_frame.columnconfigure(1, weight=1)
        self.sort_label = ttk.Label(sort_frame, text=texts["sort"], style="Muted.TLabel")
        self.sort_label.grid(row=0, column=0, sticky="w")
        self.sort_combo = ttk.Combobox(sort_frame, state="readonly", width=14)
        self.sort_combo.grid(row=0, column=1, sticky="e")
        self.sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        self._update_sort_options()

        tags_frame = ttk.Frame(self.frame, style="Panel.TFrame")
        tags_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        tags_frame.columnconfigure(0, weight=1)
        self.tags_label = ttk.Label(tags_frame, text=texts["tags"], style="Muted.TLabel")
        self.tags_label.grid(row=0, column=0, sticky="w")
        self.tag_container = ttk.Frame(tags_frame, style="Panel.TFrame")
        self.tag_container.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        list_frame = ttk.Frame(self.frame, style="Panel.TFrame")
        list_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.app.listbox = tk.Listbox(list_frame, exportselection=False)
        self.app.listbox.grid(row=0, column=0, sticky="nsew")
        self.app.listbox.bind("<<ListboxSelect>>", self.app.on_select)

        list_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.app.listbox.yview
        )
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.app.listbox.config(yscrollcommand=list_scroll.set)

    def update_texts(self) -> None:
        texts = self._get_texts()
        if self.title_label:
            self.title_label.config(text=texts["notes"])
        if self.new_button:
            self.new_button.config(text=texts["new"])
        if self.delete_button:
            self.delete_button.config(text=texts["delete"])
        if self.sort_label:
            self.sort_label.config(text=texts["sort"])
        if self.tags_label:
            self.tags_label.config(text=texts["tags"])
        self._update_sort_options()
        self.update_tags(self._tags)

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_sidebar_texts(language)

    def update_tags(self, tags: list[str]) -> None:
        self._tags = list(tags)
        if not self.tag_container:
            return
        for child in self.tag_container.winfo_children():
            child.destroy()
        if not tags:
            return
        selected = set(getattr(self.app, "tag_filters", set()))
        row = 0
        col = 0
        for tag in tags:
            style = "Accent.TButton" if tag in selected else "Ghost.TButton"
            btn = ttk.Button(
                self.tag_container,
                text=tag,
                style=style,
                command=lambda t=tag: self._toggle_tag(t),
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="w")
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def _toggle_tag(self, tag: str) -> None:
        selected = set(getattr(self.app, "tag_filters", set()))
        if tag in selected:
            selected.remove(tag)
        else:
            selected.add(tag)
        if hasattr(self.app, "set_tag_filters"):
            self.app.set_tag_filters(selected)
        else:
            self.app.tag_filters = selected
        self.update_tags(self._tags)
        self.app.refresh_list(select_id=self.app.current_note_id)

    def _update_sort_options(self) -> None:
        if not self.sort_combo:
            return
        texts = self._get_texts()
        options = [
            (texts["sort_recent"], "recent"),
            (texts["sort_alpha"], "alpha"),
            (texts["sort_pinned"], "pinned"),
        ]
        self._sort_map = {label: key for label, key in options}
        values = [label for label, _ in options]
        self.sort_combo["values"] = values
        current = getattr(self.app, "sort_mode", "pinned")
        for label, key in options:
            if key == current:
                self.sort_combo.set(label)
                return
        if values:
            self.sort_combo.set(values[0])

    def _on_sort_change(self, event=None) -> None:
        if not self.sort_combo:
            return
        label = self.sort_combo.get()
        mode = self._sort_map.get(label, "pinned")
        if hasattr(self.app, "set_sort_mode"):
            self.app.set_sort_mode(mode)
        else:
            self.app.sort_mode = mode
        self.app.refresh_list(select_id=self.app.current_note_id)
