from src.storage_sqlite import NoteStore


def test_crud(tmp_path):
    store = NoteStore(tmp_path / "notes.db")

    note = store.create_note("Titulo", "Contenido", tags=["a", "b"], pinned=True)
    assert note.id
    assert note.title == "Titulo"
    assert note.content == "Contenido"
    assert note.tags == ["a", "b"]
    assert note.pinned is True

    fetched = store.get_note(note.id)
    assert fetched is not None
    assert fetched.title == "Titulo"

    updated = store.update_note(note.id, "Nuevo", "Actualizado", tags=["x"])
    assert updated is not None
    assert updated.title == "Nuevo"
    assert updated.content == "Actualizado"
    assert updated.tags == ["x"]

    notes = store.list_notes()
    assert len(notes) == 1

    assert store.delete_note(note.id) is True
    assert store.get_note(note.id) is None


def test_search(tmp_path):
    store = NoteStore(tmp_path / "notes.db")
    store.create_note("Alpha", "Hola mundo")
    store.create_note("Beta", "Otra cosa")

    results = store.list_notes(query="hola")
    assert len(results) == 1
    assert results[0].title == "Alpha"
