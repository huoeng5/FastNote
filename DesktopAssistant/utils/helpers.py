"""Shared utility helpers."""

from __future__ import annotations

from typing import Iterable, Mapping


def parse_tags(raw: str | Iterable[str]) -> list[str]:
    """Normalize tags while preserving input order."""
    if isinstance(raw, str):
        parts = raw.split()
    else:
        parts = [str(item).strip() for item in raw]

    seen: set[str] = set()
    normalized: list[str] = []
    for part in parts:
        if not part:
            continue
        if part in seen:
            continue
        seen.add(part)
        normalized.append(part)
    return normalized


def normalize_tags(raw: str | Iterable[str], alias_map: Mapping[str, str] | None = None) -> list[str]:
    """Normalize tags and expand aliases while preserving order."""
    parts = parse_tags(raw)
    aliases: dict[str, str] = {}
    if alias_map:
        aliases = {str(k).strip(): str(v).strip() for k, v in alias_map.items() if str(k).strip()}

    expanded: list[str] = []
    for token in parts:
        mapped = aliases.get(token, token)
        expanded.extend(mapped.split())
    return parse_tags(expanded)


def infer_content_type(text: str, image_path: str) -> str:
    """Infer content type from text/image combination."""
    has_text = bool(text.strip())
    has_image = bool(image_path.strip())
    if has_text and has_image:
        return "mixed"
    if has_image:
        return "screenshot"
    return "text"
