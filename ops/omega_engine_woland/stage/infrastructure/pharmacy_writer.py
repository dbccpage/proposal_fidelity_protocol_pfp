"""Filesystem writer for the stage pharmacy. The domain does not call Path.write."""

from __future__ import annotations

from pathlib import Path


def filesystem_text_writer(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class FilesystemCatalogText:
    """Open catalog paths. The domain receives the text."""

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def exists(self, path: str) -> bool:
        return Path(path).exists()


filesystem_catalog_text = FilesystemCatalogText()
