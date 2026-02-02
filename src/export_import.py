from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import title_from_content


class ExportImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class MarkdownNote:
    title: str
    content: str
    source_path: Path


class ExportImport:
    def __init__(
        self,
        *,
        encoding: str = "utf-8",
        ensure_newline: bool = False,
        title_max_len: int = 120,
    ) -> None:
        self.default_encoding = encoding
        self.ensure_newline = ensure_newline
        self.title_max_len = title_max_len

    def export_note_txt(
        self,
        content: str,
        path: str | Path,
        *,
        encoding: str | None = None,
        ensure_newline: bool | None = None,
    ) -> None:
        final_content = self._normalize_content(
            content, ensure_newline=ensure_newline
        )
        self._write_text(path, final_content, encoding=encoding)

    def export_note_md(
        self,
        title: str,
        content: str,
        path: str | Path,
        *,
        encoding: str | None = None,
        ensure_newline: bool | None = None,
        title_max_len: int | None = None,
    ) -> None:
        clean_title = self.sanitize_title(title, max_len=title_max_len)
        md_content = self._ensure_md_title(clean_title, content)
        md_content = self._normalize_content(md_content, ensure_newline=ensure_newline)
        self._write_text(path, md_content, encoding=encoding)

    def import_markdown(
        self,
        path: str | Path,
        *,
        encoding: str | None = None,
        title_max_len: int | None = None,
    ) -> tuple[str, str]:
        note = self.read_markdown(
            path, encoding=encoding, title_max_len=title_max_len
        )
        return note.title, note.content

    def read_markdown(
        self,
        path: str | Path,
        *,
        encoding: str | None = None,
        title_max_len: int | None = None,
    ) -> MarkdownNote:
        source = Path(path)
        content = self._read_text(source, encoding=encoding)
        title = self.markdown_title(content, max_len=title_max_len)
        if not title:
            title = title_from_content(content, source.stem)
        return MarkdownNote(title=title, content=content, source_path=source)

    def markdown_title(self, content: str, *, max_len: int | None = None) -> str | None:
        trimmed = self._strip_front_matter(content)
        max_len = self._resolve_title_max_len(max_len)
        for line in trimmed.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title:
                    return self.sanitize_title(title, max_len=max_len)
        return None

    def sanitize_title(self, title: str, *, max_len: int | None = None) -> str:
        max_len = self._resolve_title_max_len(max_len)
        cleaned = title.replace("\r", " ").replace("\n", " ").strip()
        cleaned = cleaned.lstrip("#").strip()
        cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32)
        if not cleaned:
            return ""
        if max_len > 0:
            return cleaned[:max_len]
        return cleaned

    @staticmethod
    def ensure_txt_path(path: str | Path) -> str:
        return ExportImport._ensure_extension(path, ".txt")

    @staticmethod
    def ensure_md_path(path: str | Path) -> str:
        return ExportImport._ensure_extension(path, ".md")

    def _resolve_title_max_len(self, value: int | None) -> int:
        if isinstance(value, int):
            return value
        return self.title_max_len

    def _normalize_content(
        self, content: str, *, ensure_newline: bool | None = None
    ) -> str:
        if ensure_newline is None:
            ensure_newline = self.ensure_newline
        if ensure_newline and content and not content.endswith("\n"):
            return f"{content}\n"
        return content

    def _read_text(self, path: Path, *, encoding: str | None = None) -> str:
        resolved_encoding = encoding or self.default_encoding
        try:
            return path.read_text(encoding=resolved_encoding)
        except OSError as exc:
            raise ExportImportError(str(exc)) from exc

    def _write_text(
        self, path: str | Path, content: str, *, encoding: str | None = None
    ) -> None:
        resolved_encoding = encoding or self.default_encoding
        try:
            Path(path).write_text(content, encoding=resolved_encoding)
        except OSError as exc:
            raise ExportImportError(str(exc)) from exc

    @staticmethod
    def _strip_front_matter(content: str) -> str:
        lines = content.splitlines()
        if not lines:
            return content
        idx = 0
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx >= len(lines) or lines[idx].strip() != "---":
            return content
        idx += 1
        while idx < len(lines):
            if lines[idx].strip() == "---":
                idx += 1
                return "\n".join(lines[idx:])
            idx += 1
        return content

    @staticmethod
    def _ensure_md_title(title: str, content: str) -> str:
        stripped = content.lstrip()
        if stripped.startswith("#"):
            return content
        return f"# {title}\n\n{content}"

    @staticmethod
    def _ensure_extension(path: str | Path, extension: str) -> str:
        if not extension.startswith("."):
            extension = f".{extension}"
        path_obj = Path(path)
        if path_obj.suffix.lower() == extension.lower():
            return str(path_obj)
        return str(path_obj.with_suffix(extension))
