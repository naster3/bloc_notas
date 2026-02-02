import types

import pytest

import src.controllers.formatting as formatting_module


class DummyText:
    def __init__(self):
        self._selection = None
        self._tags = {}

    def set_selection(self, start, end):
        self._selection = (start, end)

    def index(self, index):
        if index == "sel.first":
            if not self._selection:
                raise formatting_module.tk.TclError()
            return self._selection[0]
        if index == "sel.last":
            if not self._selection:
                raise formatting_module.tk.TclError()
            return self._selection[1]
        return index

    def tag_names(self, index):
        return list(self._tags.get(index, set()))

    def tag_add(self, tag, start, end):
        self._tags.setdefault(start, set()).add(tag)

    def tag_remove(self, tag, start, end):
        if start in self._tags and tag in self._tags[start]:
            self._tags[start].remove(tag)


class DummyFont:
    def __init__(self, family="Arial", size=12):
        self._family = family
        self._size = size

    def cget(self, option):
        if option == "family":
            return self._family
        if option == "size":
            return self._size
        raise KeyError(option)


class DummyTagManager:
    def __init__(self, text):
        self.text = text
        self.calls = []
        self.last_persistent = None

    def apply_persistent_style(self, bold, italic):
        self.last_persistent = (bold, italic)
        self.calls.append(("persistent", bold, italic))

    def apply_font_override(self, family, size, start, end):
        self.calls.append(("font_override", family, size, start, end))

    def clear_basic_formatting(self, start, end):
        self.calls.append(("clear", start, end))


def _controller_with_selection(tags=None):
    text = DummyText()
    text.set_selection("1.0", "1.4")
    if tags:
        text._tags["1.0"] = set(tags)
    app = types.SimpleNamespace(text=text)
    return formatting_module.FormattingController(app), text


def _controller_without_selection():
    text = DummyText()
    app = types.SimpleNamespace(text=text)
    return formatting_module.FormattingController(app), text


def test_toggle_bold_adds_bold():
    controller, text = _controller_with_selection()
    controller.toggle_bold()
    assert "bold" in text._tags["1.0"]


def test_toggle_bold_with_italic_creates_bold_italic():
    controller, text = _controller_with_selection(tags={"italic"})
    controller.toggle_bold()
    assert "italic" not in text._tags["1.0"]
    assert "bold_italic" in text._tags["1.0"]


def test_toggle_italic_with_bold_creates_bold_italic():
    controller, text = _controller_with_selection(tags={"bold"})
    controller.toggle_italic()
    assert "bold" not in text._tags["1.0"]
    assert "bold_italic" in text._tags["1.0"]


def test_toggle_underline_adds_and_removes():
    controller, text = _controller_with_selection()
    controller.toggle_underline()
    assert "underline" in text._tags["1.0"]
    controller.toggle_underline()
    assert "underline" not in text._tags["1.0"]


def test_toggle_strike_adds_and_removes():
    controller, text = _controller_with_selection()
    controller.toggle_strike()
    assert "strike" in text._tags["1.0"]
    controller.toggle_strike()
    assert "strike" not in text._tags["1.0"]


def test_toggle_bold_without_selection_sets_persistent(monkeypatch):
    controller, _ = _controller_without_selection()
    monkeypatch.setattr(formatting_module, "TagManager", DummyTagManager)
    controller.toggle_bold()
    assert controller.persistent_bold is True
    assert controller._tag_manager.last_persistent == (True, False)


def test_toggle_italic_without_selection_sets_persistent(monkeypatch):
    controller, _ = _controller_without_selection()
    monkeypatch.setattr(formatting_module, "TagManager", DummyTagManager)
    controller.toggle_italic()
    assert controller.persistent_italic is True
    assert controller._tag_manager.last_persistent == (False, True)


def test_clear_selection_formatting_calls_tag_manager(monkeypatch):
    controller, _ = _controller_with_selection()
    monkeypatch.setattr(formatting_module, "TagManager", DummyTagManager)
    controller.clear_selection_formatting()
    assert controller._tag_manager.calls == [("clear", "1.0", "1.4")]


def test_set_selection_font_family_uses_tag_manager(monkeypatch):
    controller, _ = _controller_with_selection()
    controller.app.text_font = DummyFont(family="Arial", size=14)
    monkeypatch.setattr(formatting_module, "TagManager", DummyTagManager)
    controller.set_selection_font_family("Courier")
    assert controller._tag_manager.calls == [
        ("font_override", "Courier", 14, "1.0", "1.4")
    ]


def test_set_selection_font_size_uses_tag_manager(monkeypatch):
    controller, _ = _controller_with_selection()
    controller.app.text_font = DummyFont(family="Verdana", size=14)
    monkeypatch.setattr(formatting_module, "TagManager", DummyTagManager)
    controller.set_selection_font_size(18)
    assert controller._tag_manager.calls == [
        ("font_override", "Verdana", 18, "1.0", "1.4")
    ]
