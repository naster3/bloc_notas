from __future__ import annotations

from pathlib import Path
import logging
import os
import sys

from src.app import main


MIN_PYTHON = (3, 10)


def _check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"Se requiere Python {required}+ (actual: {current}).",
            file=sys.stderr,
        )


def _parse_args(argv: list[str]) -> tuple[bool, bool]:
    reset_settings = False
    debug = False
    for arg in argv:
        if arg == "--reset-settings":
            reset_settings = True
        elif arg == "--debug":
            debug = True
    return reset_settings, debug


def _reset_settings_file() -> None:
    config_path = Path(__file__).resolve().parent / "settings.json"
    try:
        if config_path.exists():
            config_path.unlink()
            print("settings.json restablecido.")
    except OSError as exc:
        print(f"No se pudo borrar settings.json: {exc}", file=sys.stderr)


def _enable_debug() -> None:
    logging.basicConfig(level=logging.DEBUG)
    os.environ["BLOC_NOTAS_DEBUG"] = "1"


if __name__ == "__main__":
    _check_python_version()
    reset_settings, debug = _parse_args(sys.argv[1:])
    if debug:
        _enable_debug()
    if reset_settings:
        _reset_settings_file()
    try:
        main()
    except Exception as exc:  # pragma: no cover - top-level guard
        print(f"Ocurrio un error inesperado: {exc}", file=sys.stderr)
        raise
