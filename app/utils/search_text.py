"""
Shared helper that produces the flat string indexed by the poems_fts FTS5
trigram virtual table. Single source of truth used by both the bulk importer
(scripts/import_json.py) and the live PUT /api/poems/{id} handler.

Keeping this in one place ensures admin edits land in the search index the same
way fresh imports do.
"""
from __future__ import annotations

import json
from typing import Any, Iterable


def build_search_text(
    title: str | None,
    text: str | None,
    bhavam: str | None,
    prathipadartham: Iterable[dict[str, Any]] | str | None,
) -> str | None:
    """Flatten the searchable surface of a poem into one newline-joined blob."""
    parts: list[str] = []
    if title:
        parts.append(title)
    if text:
        parts.append(text)
    if bhavam:
        parts.append(bhavam)

    entries = _coerce_prathipadartham(prathipadartham)
    for entry in entries:
        w = entry.get("word")
        m = entry.get("meaning")
        if w:
            parts.append(str(w))
        if m:
            parts.append(str(m))

    return "\n".join(p for p in parts if p) or None


def _coerce_prathipadartham(
    value: Iterable[dict[str, Any]] | str | None,
) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []
    if isinstance(value, list):
        return value
    return []
