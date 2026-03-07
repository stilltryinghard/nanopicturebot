from __future__ import annotations
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
TG_MAX_LEN = 4096


def _load(filename: str) -> str:
    path = DOCS_DIR / filename
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"[Файл {filename} не найден]"


def _split(text: str) -> list[str]:
    """Разбивает текст на страницы по TG_MAX_LEN символов, разрезая по абзацам."""
    if len(text) <= TG_MAX_LEN:
        return [text]

    pages: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in text.split("\n\n"):
        chunk = paragraph + "\n\n"
        if current_len + len(chunk) > TG_MAX_LEN and current:
            pages.append("".join(current).rstrip())
            current = []
            current_len = 0
        current.append(chunk)
        current_len += len(chunk)

    if current:
        pages.append("".join(current).rstrip())

    return pages


def get_privacy_policy() -> list[str]:
    return _split(_load("privacy_policy.txt"))


def get_terms_of_service() -> list[str]:
    return _split(_load("terms_of_service.txt"))
