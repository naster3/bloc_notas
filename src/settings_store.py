from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Iterable, Mapping, cast


THEME_CHOICES = {"warm", "dark", "minimal", "retro"}
LANGUAGE_CHOICES = {"es", "en", "pt", "fr"}
SORT_CHOICES = {"recent", "alpha", "pinned"}
SETTINGS_VERSION = 1

DEFAULT_THEME = "warm"
DEFAULT_LANGUAGE = "es"
DEFAULT_SORT_MODE = "pinned"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_ZOOM = 100
ZOOM_MIN = 50
ZOOM_MAX = 200
TAB_SIZE_DEFAULT = 4
TAB_SIZE_MIN = 1
TAB_SIZE_MAX = 16


@dataclass
class SearchSettings:
    term: str = ""
    match_case: bool = False
    regex: bool = False
    whole_word: bool = False


@dataclass
class ViewSettings:
    status_bar: bool = False
    zoom: int = DEFAULT_ZOOM
    focus: bool = False


@dataclass
class SidebarSettings:
    sort_mode: str = DEFAULT_SORT_MODE
    tags: list[str] = field(default_factory=list)


@dataclass
class Settings:
    settings_version: int = SETTINGS_VERSION
    theme: str = DEFAULT_THEME
    language: str = DEFAULT_LANGUAGE
    templates: dict[str, object] = field(default_factory=dict)
    datetime_format: str = DEFAULT_DATETIME_FORMAT
    date_format: str = DEFAULT_DATE_FORMAT
    search: SearchSettings = field(default_factory=SearchSettings)
    view: ViewSettings = field(default_factory=ViewSettings)
    last_import_dir: str = ""
    tab_size: int = TAB_SIZE_DEFAULT
    sidebar: SidebarSettings = field(default_factory=SidebarSettings)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "settings_version": self.settings_version,
            "theme": self.theme,
            "language": self.language,
            "datetime_format": self.datetime_format,
            "date_format": self.date_format,
            "search": {
                "term": self.search.term,
                "match_case": self.search.match_case,
                "regex": self.search.regex,
                "whole_word": self.search.whole_word,
            },
            "view": {
                "status_bar": self.view.status_bar,
                "zoom": self.view.zoom,
                "focus": self.view.focus,
            },
            "tab_size": self.tab_size,
            "sidebar": {
                "sort_mode": self.sidebar.sort_mode,
                "tags": list(self.sidebar.tags),
            },
        }
        if self.templates:
            data["templates"] = self.templates
        if self.last_import_dir:
            data["last_import_dir"] = self.last_import_dir
        return data


class SettingsStore:
    KNOWN_KEYS = {
        "settings_version",
        "theme",
        "language",
        "templates",
        "datetime_format",
        "date_format",
        "search",
        "view",
        "last_import_dir",
        "tab_size",
        "sidebar",
    }

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, *, raise_errors: bool = False) -> tuple[Settings, list[str], dict[str, object]]:
        warnings: list[str] = []
        extras: dict[str, object] = {}
        if not self.path.exists():
            return Settings(), warnings, extras
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            if raise_errors:
                raise SettingsStoreError(str(exc)) from exc
            warnings.append(f"No se pudo leer settings.json: {exc}")
            return Settings(), warnings, extras
        if not isinstance(raw, dict):
            warnings.append("settings.json no tiene un formato valido.")
            return Settings(), warnings, extras
        raw_dict = cast(dict[str, object], raw)
        migrated = self._migrate(raw_dict, warnings)
        extras = self._extract_extras(migrated)
        settings = self._parse(migrated, warnings)
        return settings, warnings, extras

    def save(self, settings: Settings, extras: Mapping[str, object] | None = None) -> None:
        data = settings.to_dict()
        if extras:
            data = self._merge_extras(data, extras)
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )

    def _parse(self, raw: dict[str, object], warnings: list[str]) -> Settings:
        settings_version = self._int(
            raw.get("settings_version"), SETTINGS_VERSION, min_value=0
        )
        theme = self._choice(raw.get("theme"), THEME_CHOICES, DEFAULT_THEME)
        language = self._choice(raw.get("language"), LANGUAGE_CHOICES, DEFAULT_LANGUAGE)
        templates = self._sanitize_templates(raw.get("templates"))
        datetime_format = self._strftime_format(
            raw.get("datetime_format"),
            DEFAULT_DATETIME_FORMAT,
            warnings,
            "datetime_format",
        )
        date_format = self._strftime_format(
            raw.get("date_format"),
            DEFAULT_DATE_FORMAT,
            warnings,
            "date_format",
        )
        last_import_dir = self._path(raw.get("last_import_dir"), "")
        tab_size = self._int(
            raw.get("tab_size"),
            TAB_SIZE_DEFAULT,
            min_value=TAB_SIZE_MIN,
            max_value=TAB_SIZE_MAX,
        )

        raw_search = raw.get("search")
        search_raw = raw_search if isinstance(raw_search, dict) else {}
        search = SearchSettings(
            term=self._string(search_raw.get("term"), ""),
            match_case=self._bool(search_raw.get("match_case"), False),
            regex=self._bool(search_raw.get("regex"), False),
            whole_word=self._bool(search_raw.get("whole_word"), False),
        )

        raw_view = raw.get("view")
        view_raw = raw_view if isinstance(raw_view, dict) else {}
        view = ViewSettings(
            status_bar=self._bool(view_raw.get("status_bar"), False),
            zoom=self._int(
                view_raw.get("zoom"),
                DEFAULT_ZOOM,
                min_value=ZOOM_MIN,
                max_value=ZOOM_MAX,
            ),
            focus=self._bool(view_raw.get("focus"), False),
        )

        raw_sidebar = raw.get("sidebar")
        sidebar_raw = raw_sidebar if isinstance(raw_sidebar, dict) else {}
        sort_mode = self._choice(
            sidebar_raw.get("sort_mode"), SORT_CHOICES, DEFAULT_SORT_MODE
        )
        tags = self._string_list(sidebar_raw.get("tags"))
        sidebar = SidebarSettings(sort_mode=sort_mode, tags=tags)

        return Settings(
            settings_version=settings_version,
            theme=theme,
            language=language,
            templates=templates,
            datetime_format=datetime_format,
            date_format=date_format,
            search=search,
            view=view,
            last_import_dir=last_import_dir,
            tab_size=tab_size,
            sidebar=sidebar,
        )

    @staticmethod
    def _string(value: object, default: str) -> str:
        return value if isinstance(value, str) else default

    @staticmethod
    def _bool(value: object, default: bool) -> bool:
        return value if isinstance(value, bool) else default

    @staticmethod
    def _int(
        value: object,
        default: int,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        if not isinstance(value, int):
            return default
        if min_value is not None and value < min_value:
            return default
        if max_value is not None and value > max_value:
            return default
        return value

    @staticmethod
    def _choice(value: object, options: Iterable[str], default: str) -> str:
        if isinstance(value, str) and value in options:
            return value
        return default

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return sorted(set(items))

    @staticmethod
    def _sanitize_templates(value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            return {}
        sanitized: dict[str, object] = {}
        for key, template in value.items():
            if not isinstance(key, str):
                continue
            if isinstance(template, str):
                sanitized[key] = template
                continue
            if isinstance(template, dict):
                nested: dict[str, str] = {}
                for lang, text in template.items():
                    if isinstance(lang, str) and isinstance(text, str):
                        nested[lang] = text
                if nested:
                    sanitized[key] = nested
        return sanitized

    @staticmethod
    def _path(value: object, default: str) -> str:
        if not isinstance(value, str) or not value.strip():
            return default
        try:
            return str(Path(value).expanduser().resolve())
        except OSError:
            return str(Path(value).expanduser())

    @staticmethod
    def _strftime_format(
        value: object,
        default: str,
        warnings: list[str],
        field: str,
    ) -> str:
        if not isinstance(value, str):
            return default
        try:
            datetime.now().strftime(value)
        except Exception:
            warnings.append(f"{field} invalido, se usa el valor por defecto.")
            return default
        return value

    def _migrate(self, raw: dict[str, object], warnings: list[str]) -> dict[str, object]:
        migrated = dict(raw)
        version = migrated.get("settings_version")
        version_int = version if isinstance(version, int) else 0
        if version_int > SETTINGS_VERSION:
            warnings.append("settings.json es de una version mas nueva.")
        if version_int < SETTINGS_VERSION:
            version_int = SETTINGS_VERSION
        migrated["settings_version"] = version_int
        return migrated

    def _extract_extras(self, raw: dict[str, object]) -> dict[str, object]:
        extras: dict[str, object] = {
            key: value for key, value in raw.items() if key not in self.KNOWN_KEYS
        }
        nested_keys = {
            "search": {"term", "match_case", "regex", "whole_word"},
            "view": {"status_bar", "zoom", "focus"},
            "sidebar": {"sort_mode", "tags"},
        }
        for section, known in nested_keys.items():
            raw_section = raw.get(section)
            if not isinstance(raw_section, dict):
                continue
            nested = {k: v for k, v in raw_section.items() if k not in known}
            if nested:
                extras[section] = nested
        return extras

    def _merge_extras(
        self, base: Mapping[str, object], extras: Mapping[str, object]
    ) -> dict[str, object]:
        merged: dict[str, object] = dict(base)
        for key, value in extras.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_extras(
                    cast(Mapping[str, object], merged[key]),
                    cast(Mapping[str, object], value),
                )
                continue
            if key not in merged:
                merged[key] = value
        return merged


class SettingsStoreError(RuntimeError):
    pass
