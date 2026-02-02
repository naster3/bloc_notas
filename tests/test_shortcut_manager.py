import src.ui.shortcut_manager as shortcut_module


class DummyRoot:
    def __init__(self):
        self.bindings = {}

    def bind_all(self, sequence, handler):
        self.bindings[sequence] = handler


class DummyText:
    def __init__(self):
        self.bindings = {}

    def bind(self, sequence, handler):
        self.bindings[sequence] = handler


class DummyApp:
    def __init__(self):
        self.root = DummyRoot()
        self.called = []

    def save_current(self):
        self.called.append("save")

    def edit_undo(self):
        self.called.append("undo")

    def handle_list_continue(self, event=None):
        self.called.append("list")


def test_shortcut_manager_binds_root_and_calls():
    app = DummyApp()
    manager = shortcut_module.ShortcutManager(app)
    manager.bind_root()

    assert "<Control-s>" in app.root.bindings
    handler = app.root.bindings["<Control-s>"]
    handler(None)
    assert "save" in app.called


def test_shortcut_manager_binds_text():
    app = DummyApp()
    text = DummyText()
    manager = shortcut_module.ShortcutManager(app)
    manager.bind_text(text)

    assert "<Return>" in text.bindings
    text.bindings["<Return>"](None)
    assert "list" in app.called
