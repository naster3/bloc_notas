import types

import src.controllers.edit as edit_module


class DummyRoot:
    def __init__(self, focus=None):
        self._focus = focus
        self.clipboard = ""

    def focus_get(self):
        return self._focus

    def clipboard_clear(self):
        self.clipboard = ""

    def clipboard_append(self, text):
        self.clipboard = text

    def clipboard_get(self):
        if self.clipboard == "":
            raise edit_module.tk.TclError()
        return self.clipboard


class DummyText:
    def __init__(self):
        self.events = []
        self.tags = []
        self.marked = None
        self.seen = None
        self.deleted = None

    def event_generate(self, sequence):
        self.events.append(sequence)

    def tag_add(self, tag, start, end):
        self.tags.append((tag, start, end))

    def mark_set(self, mark, index):
        self.marked = (mark, index)

    def see(self, index):
        self.seen = index

    def index(self, index):
        return index

    def delete(self, start, end):
        self.deleted = (start, end)


class DummyEntry:
    def __init__(self, value=""):
        self.value = value
        self.selection = None
        self.cursor = 0

    def selection_present(self):
        return self.selection is not None and self.selection[0] != self.selection[1]

    def selection_get(self):
        if not self.selection_present():
            raise edit_module.tk.TclError()
        start, end = self.selection
        return self.value[start:end]

    def selection_range(self, start, end):
        if end == edit_module.tk.END:
            end = len(self.value)
        self.selection = (int(start), int(end))

    def icursor(self, pos):
        if pos == edit_module.tk.END:
            pos = len(self.value)
        self.cursor = int(pos)

    def index(self, what):
        if what == "sel.first":
            return self.selection[0]
        if what == "sel.last":
            return self.selection[1]
        if what == edit_module.tk.INSERT:
            return self.cursor
        return 0

    def delete(self, start, end):
        start = int(start)
        end = int(end)
        self.value = self.value[:start] + self.value[end:]
        self.selection = None

    def insert(self, index, text):
        if index == edit_module.tk.INSERT:
            index = self.cursor
        if isinstance(index, str) and index.isdigit():
            index = int(index)
        if not isinstance(index, int):
            index = len(self.value)
        self.value = self.value[:index] + text + self.value[index:]


class DummyCombobox(DummyEntry):
    pass


def _build_controller(monkeypatch, focus):
    monkeypatch.setattr(edit_module.tk, "Text", DummyText)
    monkeypatch.setattr(edit_module.tk, "Entry", DummyEntry)
    monkeypatch.setattr(edit_module.ttk, "Entry", DummyEntry)
    monkeypatch.setattr(edit_module.ttk, "Combobox", DummyCombobox)

    root = DummyRoot(focus)
    app = types.SimpleNamespace(root=root, text=DummyText())
    return edit_module.EditController(app), app, root


def test_cut_copy_paste_text(monkeypatch):
    text = DummyText()
    controller, app, root = _build_controller(monkeypatch, text)
    root._focus = text

    assert controller.cut() == "break"
    assert "<<Cut>>" in text.events

    assert controller.copy() == "break"
    assert "<<Copy>>" in text.events

    assert controller.paste() == "break"
    assert "<<Paste>>" in text.events


def test_cut_copy_paste_entry(monkeypatch):
    entry = DummyEntry("hello world")
    entry.selection_range(0, 5)
    controller, app, root = _build_controller(monkeypatch, entry)
    root._focus = entry

    controller.cut()
    assert root.clipboard == "hello"
    assert entry.value == " world"

    entry2 = DummyEntry("alpha")
    entry2.selection_range(0, 5)
    root._focus = entry2
    controller.copy()
    assert root.clipboard == "alpha"
    assert entry2.value == "alpha"

    entry3 = DummyEntry("x")
    entry3.icursor(1)
    root._focus = entry3
    root.clipboard = "y"
    controller.paste()
    assert entry3.value == "xy"


def test_select_line_and_word_text(monkeypatch):
    text = DummyText()
    controller, app, root = _build_controller(monkeypatch, text)
    root._focus = text

    controller.select_line()
    assert ("sel", "insert linestart", "insert lineend") in text.tags

    controller.select_word()
    assert ("sel", "insert wordstart", "insert wordend") in text.tags


def test_delete_selection_text(monkeypatch):
    text = DummyText()
    controller, app, root = _build_controller(monkeypatch, text)
    root._focus = text

    assert controller.delete_selection() == "break"
    assert text.deleted == ("sel.first", "sel.last")


def test_delete_selection_entry(monkeypatch):
    entry = DummyEntry("hello world")
    entry.selection_range(0, 5)
    controller, app, root = _build_controller(monkeypatch, entry)
    root._focus = entry

    assert controller.delete_selection() == "break"
    assert entry.value == " world"
