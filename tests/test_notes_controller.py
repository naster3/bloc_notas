import types

import src.controllers.notes as notes_module


class DummyText:
    def __init__(self):
        self._modified = False

    def edit_modified(self, value=None):
        if value is None:
            return self._modified
        self._modified = bool(value)


class DummyRoot:
    def __init__(self):
        self.after_calls = []
        self.after_cancel_calls = []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))
        return f"job-{len(self.after_calls)}"

    def after_cancel(self, job):
        self.after_cancel_calls.append(job)

    def destroy(self):
        self.destroyed = True


class DummyListbox:
    def __init__(self):
        self._selection = []

    def selection_clear(self, start, end):
        self._selection = []

    def selection_set(self, index):
        self._selection = [index]

    def see(self, index):
        self.seen = index


class DummyStore:
    def __init__(self):
        self.upsert_calls = []

    def upsert_from_content(self, note_id, content):
        self.upsert_calls.append((note_id, content))
        return types.SimpleNamespace(id="id-1", title="Title")


class DummyApp:
    def __init__(self):
        self.root = DummyRoot()
        self.text = DummyText()
        self.listbox = DummyListbox()
        self.store = DummyStore()
        self.dirty = False
        self.loading_note = False
        self.autosave_delay = 100
        self.autosave_job = None
        self.current_note_id = "id-1"
        self.note_ids = ["id-1"]
        self.search_var = types.SimpleNamespace(get=lambda: "")

    def _set_title(self, *_):
        pass


def test_confirm_save_cancel_blocks_action(monkeypatch):
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.dirty = True

    monkeypatch.setattr(
        notes_module.messagebox, "askyesnocancel", lambda *args, **kwargs: None
    )

    assert controller._confirm_save_if_dirty() is False


def test_confirm_save_no_discards(monkeypatch):
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.dirty = True

    monkeypatch.setattr(
        notes_module.messagebox, "askyesnocancel", lambda *args, **kwargs: False
    )

    assert controller._confirm_save_if_dirty() is True
    assert app.dirty is False
    assert app.text.edit_modified() is False


def test_confirm_save_yes_calls_save(monkeypatch):
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.dirty = True

    monkeypatch.setattr(
        notes_module.messagebox, "askyesnocancel", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(controller, "save_current", lambda: app.store.upsert_from_content("id-1", ""))

    assert controller._confirm_save_if_dirty() is True


def test_autosave_schedules_on_modified(monkeypatch):
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.text.edit_modified(True)
    controller.on_text_modified()
    assert app.autosave_job == "job-1"
    assert app.root.after_calls[0][0] == app.autosave_delay


def test_autosave_cancels_previous_job():
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.autosave_job = "job-0"
    controller._schedule_autosave()
    assert app.root.after_cancel_calls == ["job-0"]


def test_autosave_if_dirty_calls_save():
    app = DummyApp()
    controller = notes_module.NotesController(app)
    app.dirty = True
    controller._autosave_if_dirty()
    assert app.store.upsert_calls
