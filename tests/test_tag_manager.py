import src.controllers.tag_manager as tag_manager_module


class DummyFont:
    def __init__(self, family="Arial", size=12):
        self._family = family
        self._size = size
        self._weight = "normal"
        self._slant = "roman"

    def copy(self):
        clone = DummyFont(self._family, self._size)
        clone._weight = self._weight
        clone._slant = self._slant
        return clone

    def configure(self, **kwargs):
        if "family" in kwargs:
            self._family = kwargs["family"]
        if "size" in kwargs:
            self._size = kwargs["size"]
        if "weight" in kwargs:
            self._weight = kwargs["weight"]
        if "slant" in kwargs:
            self._slant = kwargs["slant"]

    def cget(self, option):
        if option == "family":
            return self._family
        if option == "size":
            return self._size
        raise KeyError(option)


class DummyText:
    def __init__(self, *, raise_on_cget=False, font_name="DummyFont"):
        self._raise_on_cget = raise_on_cget
        self._font_name = font_name
        self._tags = {}

    def cget(self, option):
        if option == "font":
            if self._raise_on_cget:
                raise tag_manager_module.tk.TclError()
            return self._font_name
        raise tag_manager_module.tk.TclError()

    def tag_configure(self, *args, **kwargs):
        return None

    def tag_raise(self, *args, **kwargs):
        return None

    def tag_add(self, tag, start, end):
        self._tags.setdefault(tag, []).append((start, end))

    def tag_remove(self, tag, start, end):
        if tag in self._tags:
            self._tags[tag] = [
                (s, e)
                for (s, e) in self._tags[tag]
                if not (self._in_range(start, s, e) or self._in_range(end, s, e))
            ]

    def tag_delete(self, tag):
        self._tags.pop(tag, None)

    def tag_ranges(self, tag):
        ranges = []
        for start, end in self._tags.get(tag, []):
            ranges.extend([start, end])
        return ranges

    def tag_names(self, index=None):
        if index is None:
            return list(self._tags.keys())
        tags = []
        for tag, ranges in self._tags.items():
            for start, end in ranges:
                if self._compare(index, ">=", start) and self._compare(index, "<", end):
                    tags.append(tag)
                    break
        return tags

    def compare(self, left, op, right):
        return self._compare(left, op, right)

    @staticmethod
    def _parse_index(index):
        if isinstance(index, str) and "." in index:
            line, col = index.split(".", 1)
            return int(line), int(col)
        return 0, 0

    def _compare(self, left, op, right):
        l_val = self._parse_index(left)
        r_val = self._parse_index(right)
        if op == ">":
            return l_val > r_val
        if op == "<":
            return l_val < r_val
        if op == ">=":
            return l_val >= r_val
        if op == "<=":
            return l_val <= r_val
        if op == "==":
            return l_val == r_val
        raise ValueError(op)

    def _in_range(self, index, start, end):
        return self._compare(index, ">=", start) and self._compare(index, "<", end)


def test_get_tags_in_range_returns_intersections():
    text = DummyText()
    text.tag_add("bold", "1.0", "1.4")
    text.tag_add("underline", "1.3", "1.6")
    text.tag_add("italic", "2.0", "2.5")
    manager = tag_manager_module.TagManager(text)

    tags = manager.get_tags_in_range("1.2", "1.5")

    assert tags == {"bold", "underline"}


def test_get_tags_at_returns_tags_for_index():
    text = DummyText()
    text.tag_add("bold", "1.0", "1.4")
    text.tag_add("underline", "1.3", "1.6")
    manager = tag_manager_module.TagManager(text)

    tags = manager.get_tags_at("1.3")

    assert tags == {"bold", "underline"}


def test_ensure_base_font_uses_widget_font(monkeypatch):
    text = DummyText(font_name="WidgetFont")
    manager = tag_manager_module.TagManager(text)

    def fake_nametofont(name):
        assert name == "WidgetFont"
        return DummyFont(family="Verdana", size=11)

    monkeypatch.setattr(tag_manager_module.tkfont, "nametofont", fake_nametofont)

    assert manager._ensure_base_font() is True
    assert manager.base_font is not None
    assert manager.base_font.cget("family") == "Verdana"


def test_ensure_base_font_falls_back_to_default(monkeypatch):
    text = DummyText(raise_on_cget=True)
    manager = tag_manager_module.TagManager(text)

    def fake_nametofont(name):
        assert name == "TkDefaultFont"
        return DummyFont(family="TkDefault", size=10)

    monkeypatch.setattr(tag_manager_module.tkfont, "nametofont", fake_nametofont)
    monkeypatch.setattr(tag_manager_module.tkfont, "Font", lambda **kwargs: DummyFont())

    assert manager._ensure_base_font() is True
    assert manager.base_font is not None
    assert manager.base_font.cget("family") == "TkDefault"
