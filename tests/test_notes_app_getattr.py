from src.notes_app import NotesApp


class DummyController:
    def new_note(self):
        return "ok"


def test_notes_app_getattr_allows_forwarded_method():
    app = NotesApp.__new__(NotesApp)
    app._controllers = [DummyController()]

    method = NotesApp.__getattr__(app, "new_note")
    assert callable(method)
    assert method() == "ok"


def test_notes_app_getattr_rejects_unknown_method():
    app = NotesApp.__new__(NotesApp)
    app._controllers = [DummyController()]

    try:
        NotesApp.__getattr__(app, "not_allowed")
    except AttributeError:
        assert True
    else:
        assert False


def test_notes_app_getattr_requires_forwarded_method_present():
    app = NotesApp.__new__(NotesApp)
    app._controllers = [DummyController()]

    try:
        NotesApp.__getattr__(app, "save_current")
    except AttributeError:
        assert True
    else:
        assert False
