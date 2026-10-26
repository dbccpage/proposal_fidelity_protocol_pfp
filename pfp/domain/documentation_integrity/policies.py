"""Pure path and content classification policies."""

from __future__ import annotations

from pathlib import Path

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}


def extension_kind(path: str) -> str:
    suffix = Path(path).suffix.lower()
    kinds = {
        ".ipynb": "notebook",
        ".py": "source_code",
        ".rs": "source_code",
        ".svg": "asset",
        ".png": "asset",
        ".jpg": "asset",
        ".jpeg": "asset",
        ".gif": "asset",
        ".webp": "asset",
        ".mp4": "asset",
        ".mov": "asset",
        ".csv": "tabular_data",
        ".tsv": "tabular_data",
        ".mermaid": "diagram_source",
        ".gitkeep": "placeholder",
        ".txt": "text_record",
        ".source": "text_record",
    }
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".toml"}:
        return "structured_data"
    return kinds.get(suffix, "other")


def is_document_relative_path(value: str) -> bool:
    return bool(
        value
        and not value.startswith(("/", "\\\\"))
        and "\\" not in value
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )
