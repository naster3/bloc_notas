from __future__ import annotations

import re
import tkinter as tk
from tkinter import messagebox, ttk

from ..ui.texts import get_dialog_texts


class SearchController:
    def __init__(self, app) -> None:
        self.app = app
        self._search_dialog: tk.Toplevel | None = None
        self._find_var: tk.StringVar | None = None
        self._replace_var: tk.StringVar | None = None
        self._last_regex_state = self.app.regex_var.get()
        self._last_whole_word_state = self.app.whole_word_var.get()
        self._regex_warning_job: str | None = None
        self._last_invalid_pattern: str | None = None

    def focus_search(self) -> None:
        self.app.search_entry.focus_set()
        self.app.search_entry.selection_range(0, tk.END)
        self.app.search_entry.icursor(0)

    def find_in_note(self) -> None:
        texts = self._get_texts()
        if self._search_dialog and self._search_dialog.winfo_exists():
            self._search_dialog.lift()
            return

        dialog = tk.Toplevel(self.app.root)
        dialog.title(texts["find_title"])
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)
        self._search_dialog = dialog

        self._find_var = tk.StringVar(value=self.app.last_search or "")
        self._replace_var = tk.StringVar()

        ttk.Label(dialog, text=texts["find_label"]).grid(
            row=0, column=0, padx=8, pady=6, sticky="w"
        )
        find_entry = ttk.Entry(dialog, textvariable=self._find_var)
        find_entry.grid(row=0, column=1, padx=8, pady=6, sticky="ew")

        ttk.Label(dialog, text=texts["replace_label"]).grid(
            row=1, column=0, padx=8, pady=6, sticky="w"
        )
        replace_entry = ttk.Entry(dialog, textvariable=self._replace_var)
        replace_entry.grid(row=1, column=1, padx=8, pady=6, sticky="ew")

        options = ttk.Frame(dialog)
        options.grid(row=2, column=0, columnspan=2, pady=(0, 6), sticky="w")
        ttk.Checkbutton(
            options,
            text=texts["match_case"],
            variable=self.app.match_case_var,
        ).grid(row=0, column=0, padx=(8, 12))
        ttk.Checkbutton(
            options,
            text=texts["whole_word"],
            variable=self.app.whole_word_var,
        ).grid(row=0, column=1, padx=(0, 12))
        ttk.Checkbutton(
            options,
            text=texts["regex"],
            variable=self.app.regex_var,
        ).grid(row=0, column=2, padx=(0, 12))

        buttons = ttk.Frame(dialog)
        buttons.grid(row=3, column=0, columnspan=2, pady=(0, 8), sticky="e")
        ttk.Button(buttons, text=texts["next"], command=self.find_next).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(buttons, text=texts["prev"], command=self.find_prev).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(buttons, text=texts["replace_one"], command=self.replace_one).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(buttons, text=texts["replace_all"], command=self.replace_all).grid(
            row=0, column=3, padx=(0, 6)
        )

        self._find_var.trace_add("write", self._on_find_change)

        find_entry.focus_set()
        find_entry.selection_range(0, tk.END)

        dialog.bind("<Escape>", lambda event: dialog.destroy())

    def find_next(self) -> None:
        term = self._get_current_term()
        if not term:
            return
        if not self._validate_regex(term):
            return
        self.app.last_search = term
        self.app.last_search_index = self.app.last_search_index or "1.0"
        start = self.app.text.index(self.app.last_search_index)
        pattern, regexp = self._build_search_pattern(term)
        nocase = not self.app.match_case_var.get()
        count_var = tk.IntVar()
        try:
            match = self.app.text.search(
                pattern,
                start,
                stopindex="end",
                nocase=nocase,
                regexp=regexp,
                count=count_var,
            )
        except tk.TclError:
            return
        if not match:
            try:
                match = self.app.text.search(
                    pattern,
                    "1.0",
                    stopindex="end",
                    nocase=nocase,
                    regexp=regexp,
                    count=count_var,
                )
            except tk.TclError:
                return
            if not match:
                texts = self._get_texts()
                messagebox.showinfo(
                    texts["find_title"],
                    texts["not_found"],
                    parent=self.app.root,
                )
                return
        match_len = count_var.get() or len(term) or 1
        end = f"{match}+{match_len}c"
        self._select_match(match, end, insert_at=end)
        self.app.last_search_index = end

    def find_prev(self) -> None:
        term = self._get_current_term()
        if not term:
            return
        if not self._validate_regex(term):
            return
        self.app.last_search = term
        self.app.last_search_index = self.app.last_search_index or "end"
        start = self.app.text.index(self.app.last_search_index)
        pattern, regexp = self._build_search_pattern(term)
        nocase = not self.app.match_case_var.get()
        count_var = tk.IntVar()
        try:
            match = self.app.text.search(
                pattern,
                start,
                stopindex="1.0",
                nocase=nocase,
                backwards=True,
                regexp=regexp,
                count=count_var,
            )
        except tk.TclError:
            return
        if not match:
            try:
                match = self.app.text.search(
                    pattern,
                    "end",
                    stopindex="1.0",
                    nocase=nocase,
                    backwards=True,
                    regexp=regexp,
                    count=count_var,
                )
            except tk.TclError:
                return
            if not match:
                texts = self._get_texts()
                messagebox.showinfo(
                    texts["find_title"],
                    texts["not_found"],
                    parent=self.app.root,
                )
                return
        match_len = count_var.get() or len(term) or 1
        end = f"{match}+{match_len}c"
        self._select_match(match, end, insert_at=match)
        self.app.last_search_index = match

    def replace_one(self) -> None:
        term = self._get_current_term()
        if not term:
            return
        if not self._validate_regex(term):
            return
        replacement = self._get_replace_text()
        if not self._selection_matches_term(term):
            self.find_next()
        if not self._selection_matches_term(term):
            return
        try:
            sel_start = self.app.text.index("sel.first")
            sel_end = self.app.text.index("sel.last")
            self.app.text.delete(sel_start, sel_end)
            self.app.text.insert(sel_start, replacement)
            self.app.text.tag_remove("sel", "1.0", "end")
            self.app.text.mark_set("insert", sel_start)
        except tk.TclError:
            return
        self.app.last_search_index = self.app.text.index("insert")
        self.app.update_search_highlights()
        self.find_next()

    def replace_all(self) -> None:
        term = self._get_current_term()
        if not term:
            return
        if not self._validate_regex(term):
            return
        texts = self._get_texts()
        if not messagebox.askyesno(
            texts["find_title"],
            texts["replace_confirm"],
            parent=self.app.root,
        ):
            return
        replacement = self._get_replace_text()
        pattern, regexp = self._build_search_pattern(term)
        nocase = not self.app.match_case_var.get()
        start = "1.0"
        count = 0
        self.app.text.tag_remove("sel", "1.0", "end")
        while True:
            count_var = tk.IntVar()
            try:
                match = self.app.text.search(
                    pattern,
                    start,
                    stopindex="end",
                    nocase=nocase,
                    regexp=regexp,
                    count=count_var,
                )
            except tk.TclError:
                break
            if not match:
                break
            match_len = count_var.get()
            if match_len == 0:
                start = f"{match}+1c"
                continue
            end = f"{match}+{match_len}c"
            self.app.text.delete(match, end)
            self.app.text.insert(match, replacement)
            start = f"{match}+{len(replacement)}c"
            count += 1
        self.app.update_search_highlights()
        messagebox.showinfo(
            texts["find_title"],
            texts["replace_done"].format(count=count),
            parent=self.app.root,
        )

    def _get_texts(self) -> dict[str, str]:
        language = getattr(self.app, "language_name", "es")
        return get_dialog_texts("search", language)

    def _on_find_change(self, *_):
        term = self._get_current_term()
        self.app.last_search = term
        self.app.last_search_index = "1.0"
        self.app.update_search_highlights()
        if hasattr(self.app, "set_search_prefs"):
            self.app.set_search_prefs(term=term)
        if term:
            if self._validate_regex(term):
                self.find_next()
        self._schedule_regex_warning(term)

    def _get_current_term(self) -> str:
        if self._find_var is not None:
            return self._find_var.get().strip()
        return (self.app.last_search or "").strip()

    def _get_replace_text(self) -> str:
        if self._replace_var is not None:
            return self._replace_var.get()
        return ""

    def _build_search_pattern(self, term: str) -> tuple[str, bool]:
        regex = self.app.regex_var.get()
        whole_word = self.app.whole_word_var.get()
        pattern = term
        regexp = regex or whole_word
        if not regex:
            pattern = re.escape(term)
        if whole_word:
            pattern = rf"\y(?:{pattern})\y"
        return pattern, regexp

    def _validate_regex(self, term: str) -> bool:
        if not term:
            return True
        if not self.app.regex_var.get():
            return True
        try:
            re.compile(term)
        except re.error:
            texts = self._get_texts()
            messagebox.showwarning(
                texts["find_title"],
                texts["regex_invalid"],
                parent=self.app.root,
            )
            return False
        return True

    def validate_regex_toggle(self) -> None:
        regex_state = bool(self.app.regex_var.get())
        whole_word_state = bool(self.app.whole_word_var.get())
        if regex_state and not self._last_regex_state:
            self._validate_regex(self._get_current_term())
        if whole_word_state and not self._last_whole_word_state and regex_state:
            self._validate_regex(self._get_current_term())
        self._last_regex_state = regex_state
        self._last_whole_word_state = whole_word_state
        self._schedule_regex_warning(self._get_current_term())

    def _schedule_regex_warning(self, term: str) -> None:
        if self._regex_warning_job is not None:
            try:
                self.app.root.after_cancel(self._regex_warning_job)
            except tk.TclError:
                pass
            self._regex_warning_job = None
        if not self.app.regex_var.get():
            self._last_invalid_pattern = None
            return
        if not term:
            return
        self._regex_warning_job = self.app.root.after(
            300, lambda: self._show_regex_warning(term)
        )

    def _show_regex_warning(self, term: str) -> None:
        self._regex_warning_job = None
        if not self.app.regex_var.get() or not term:
            return
        try:
            re.compile(term)
        except re.error:
            if term == self._last_invalid_pattern:
                return
            texts = self._get_texts()
            messagebox.showwarning(
                texts["find_title"],
                texts["regex_invalid"],
                parent=self.app.root,
            )
            self._last_invalid_pattern = term
            return
        self._last_invalid_pattern = None

    def _selection_matches_term(self, term: str) -> bool:
        try:
            sel_start = self.app.text.index("sel.first")
            sel_end = self.app.text.index("sel.last")
            selected = self.app.text.get(sel_start, sel_end)
        except tk.TclError:
            return False
        if not selected:
            return False
        regex = self.app.regex_var.get() or self.app.whole_word_var.get()
        if not regex:
            if self.app.match_case_var.get():
                return selected == term
            return selected.lower() == term.lower()
        pattern, _ = self._build_search_pattern(term)
        flags = 0 if self.app.match_case_var.get() else re.IGNORECASE
        try:
            py_pattern = pattern.replace(r"\y", r"\b")
            return re.fullmatch(py_pattern, selected, flags) is not None
        except re.error:
            return False

    def _select_match(self, start: str, end: str, insert_at: str) -> None:
        self.app.text.tag_remove("sel", "1.0", "end")
        self.app.text.tag_add("sel", start, end)
        self.app.text.mark_set("insert", insert_at)
        self._ensure_visible(start)

    def _ensure_visible(self, index: str) -> None:
        try:
            top = self.app.text.index("@0,0")
            bottom = self.app.text.index(f"@0,{self.app.text.winfo_height()}")
        except tk.TclError:
            self.app.text.see(index)
            return
        if not (
            self.app.text.compare(index, ">=", top)
            and self.app.text.compare(index, "<=", bottom)
        ):
            self.app.text.see(index)
