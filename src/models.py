from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


DEFAULT_TITLE = "Sin titulo"
MAX_TITLE_LEN = 120
TAG_SEPARATOR = ","

IsoTimestamp = str
TagList = list[str]


@dataclass(frozen=True, slots=True)
class Note:
    id: str
    title: str
    content: str
    tags: TagList
    pinned: bool
    created_at: IsoTimestamp
    updated_at: IsoTimestamp

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", list(self.tags))

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Note":
        return cls(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            tags=split_tags(row["tags"]),
            pinned=bool(row["pinned"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_tags(tags: Iterable[str]) -> TagList:
    return [tag.strip() for tag in tags if tag.strip()]


def join_tags(tags: Iterable[str]) -> str:
    return TAG_SEPARATOR.join(normalize_tags(tags))


def split_tags(tags: str) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(TAG_SEPARATOR) if tag.strip()]


def normalize_title(
    title: str,
    *,
    max_len: int = MAX_TITLE_LEN,
    fallback: str = DEFAULT_TITLE,
) -> str:
    cleaned = title.replace("\r", " ").replace("\n", " ").strip()
    if not cleaned:
        return fallback
    if max_len > 0:
        return cleaned[:max_len]
    return cleaned


def title_from_content(content: str, fallback: str = DEFAULT_TITLE) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line:
            return normalize_title(line, fallback=fallback)
    return fallback


def parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_local(value: str, fmt: str = "%Y-%m-%d %H:%M") -> str:
    parsed = parse_iso(value)
    if not parsed:
        return value
    return parsed.astimezone().strftime(fmt)
