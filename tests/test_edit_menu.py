import types

import src.ui.menus.edit_menu as menu_module


class DummyMenu:
    def __init__(self, *args, **kwargs):
        self.entries = []
        self.postcommand = None

    def add_command(self, label, command=None, accelerator=None):
        self.entries.append(
            {
                "label": label,
                "command": command,
                "accelerator": accelerator,
                "state": "normal",
            }
        )

    def add_separator(self):
        self.entries.append({"separator": True})

    def index(self, what):
        if what == "end":
            return len(self.entries) - 1
        return int(what)

    def entryconfigure(self, index, **kwargs):
        if "state" in kwargs:
            self.entries[index]["state"] = kwargs["state"]

    def config(self, **kwargs):
        self.postcommand = kwargs.get("postcommand", self.postcommand)


class DummyRoot:
    def __init__(self, focus=None):
        self._focus = focus

    def focus_get(self):
        return self._focus


class DummyTk:
    def __init__(self, can_undo=False, can_redo=False):
        self.can_undo = can_undo
        self.can_redo = can_redo

    def call(self, _w, _edit, action):
        if action == "canundo":
            return 1 if self.can_undo else 0
        if action == "canredo":
            return 1 if self.can_redo else 0
        return 0


class DummyText:
    def __init__(self, *, has_selection=False, can_undo=False, can_redo=False):
        self._has_selection = has_selection
        self.tk = DummyTk(can_undo=can_undo, can_redo=can_redo)
        self._w = "text"

    def tag_ranges(self, tag):
        if tag == "sel" and self._has_selection:
            return ("1.0", "1.1")
        return ()


class DummyEntry:
    def __init__(self, *, has_selection=False):
        self._has_selection = has_selection

    def selection_present(self):
        return self._has_selection


class DummyCombobox(DummyEntry):
    pass


def _build_menu(monkeypatch, focus_widget):
    monkeypatch.setattr(menu_module.tk, "Menu", DummyMenu)
    monkeypatch.setattr(menu_module.tk, "Text", DummyText)
    monkeypatch.setattr(menu_module.tk, "Entry", DummyEntry)
    monkeypatch.setattr(menu_module.ttk, "Entry", DummyEntry)
    monkeypatch.setattr(menu_module.ttk, "Combobox", DummyCombobox)

    root = DummyRoot(focus_widget)
    app = types.SimpleNamespace(
        root=root,
        text=focus_widget,
        edit_undo=lambda: None,
        edit_redo=lambda: None,
        cut=lambda: None,
        copy=lambda: None,
        paste=lambda: None,
        delete_selection=lambda: None,
        select_all=lambda: None,
        select_line=lambda: None,
        select_word=lambda: None,
        language_name="es",
    )
    return menu_module.EditMenu(app, DummyMenu()), app


def test_refresh_states_with_selection(monkeypatch):
    text = DummyText(has_selection=True, can_undo=True, can_redo=False)
    menu, _ = _build_menu(monkeypatch, text)

    menu._refresh_states()

    assert menu.menu.entries[menu._indices["cut"]]["state"] == "normal"
    assert menu.menu.entries[menu._indices["copy"]]["state"] == "normal"
    assert menu.menu.entries[menu._indices["delete"]]["state"] == "normal"
    assert menu.menu.entries[menu._indices["undo"]]["state"] == "normal"
    assert menu.menu.entries[menu._indices["redo"]]["state"] == "disabled"


def test_refresh_states_without_selection(monkeypatch):
    text = DummyText(has_selection=False, can_undo=False, can_redo=False)
    menu, _ = _build_menu(monkeypatch, text)

    menu._refresh_states()

    assert menu.menu.entries[menu._indices["cut"]]["state"] == "disabled"
    assert menu.menu.entries[menu._indices["copy"]]["state"] == "disabled"
    assert menu.menu.entries[menu._indices["delete"]]["state"] == "disabled"
    assert menu.menu.entries[menu._indices["undo"]]["state"] == "disabled"
    assert menu.menu.entries[menu._indices["redo"]]["state"] == "disabled"
