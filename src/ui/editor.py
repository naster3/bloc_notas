from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


class Editor:
    def __init__(self, app, parent) -> None:
        self.app = app
        self.frame = ttk.Frame(parent, style="Panel.TFrame")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self._activity_job: str | None = None
        self._selection_job: str | None = None
        self._readonly = False
        self.tab_size = int(getattr(app, "tab_size", 4))
        self._build()

    def _build(self) -> None:
        self.app.text = tk.Text(
            self.frame,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=2000,
        )
        self.app.text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.app.text.bind("<<Modified>>", self.app.on_text_modified)
        self.app.text.bind("<<Modified>>", self._on_activity, add="+")
        self.app.text.bind("<KeyRelease>", self._on_activity, add="+")
        self.app.text.bind("<ButtonRelease-1>", self._on_selection, add="+")
        self.app.text.bind("<<Selection>>", self._on_selection, add="+")
        self.app.text.bind("<Key>", self._block_edit, add="+")
        self.app.text.bind("<<Paste>>", self._block_edit, add="+")
        self.app.text.bind("<<Cut>>", self._block_edit, add="+")

        text_scroll = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.app.text.yview
        )
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.app.text.config(yscrollcommand=text_scroll.set)
        self.set_tabsize(self.tab_size)

    def set_readonly(self, readonly: bool) -> None:
        self._readonly = bool(readonly)

    def is_readonly(self) -> bool:
        return self._readonly

    def set_tabsize(self, spaces: int) -> None:
        spaces = max(1, int(spaces))
        self.tab_size = spaces
        try:
            font = tkfont.nametofont(self.app.text.cget("font"))
        except tk.TclError:
            return
        tab_width = font.measure(" " * spaces)
        self.app.text.config(tabs=(tab_width,))
        if hasattr(self.app, "set_tab_size"):
            if getattr(self.app, "tab_size", None) != spaces:
                self.app.set_tab_size(spaces)

    def _block_edit(self, event=None):
        if not self._readonly:
            return None
        state = getattr(event, "state", 0)
        keysym = getattr(event, "keysym", "")
        if state & 0x4:
            if keysym.lower() in {"a", "c", "insert"}:
                return None
        if keysym in {
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
        }:
            return None
        if getattr(event, "char", ""):
            return "break"
        if keysym in {"BackSpace", "Delete", "Return", "Tab"}:
            return "break"
        return "break"

    def _on_activity(self, event=None) -> None:
        if self._activity_job is not None:
            try:
                self.app.root.after_cancel(self._activity_job)
            except tk.TclError:
                pass
        self._activity_job = self.app.root.after(150, self._apply_activity_updates)

    def _apply_activity_updates(self) -> None:
        self._activity_job = None
        if hasattr(self.app, "_schedule_highlight_update"):
            self.app._schedule_highlight_update()
        if getattr(self.app, "status_var", None) is not None:
            try:
                if self.app.status_var.get() and hasattr(self.app, "_render_statusbar"):
                    self.app._render_statusbar()
            except tk.TclError:
                pass
        if hasattr(self.app, "menubar") and self.app.menubar:
            if hasattr(self.app.menubar, "refresh_states"):
                self.app.menubar.refresh_states()
        if hasattr(self.app, "toolbar") and self.app.toolbar:
            if hasattr(self.app.toolbar, "refresh_states"):
                self.app.toolbar.refresh_states()

    def _on_selection(self, event=None) -> None:
        if self._selection_job is not None:
            try:
                self.app.root.after_cancel(self._selection_job)
            except tk.TclError:
                pass
        self._selection_job = self.app.root.after(80, self._apply_selection_updates)

    def _apply_selection_updates(self) -> None:
        self._selection_job = None
        if getattr(self.app, "status_var", None) is not None:
            try:
                if self.app.status_var.get() and hasattr(self.app, "_render_statusbar"):
                    self.app._render_statusbar()
            except tk.TclError:
                pass
        if hasattr(self.app, "menubar") and self.app.menubar:
            if hasattr(self.app.menubar, "refresh_states"):
                self.app.menubar.refresh_states()
        if hasattr(self.app, "toolbar") and self.app.toolbar:
            if hasattr(self.app.toolbar, "refresh_states"):
                self.app.toolbar.refresh_states()
