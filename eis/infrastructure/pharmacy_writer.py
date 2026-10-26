"""Filesystem writer for the epistemic pharmacy. The domain does not call Path.write."""

from __future__ import annotations

from pathlib import Path


def filesystem_byte_writer(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


class FilesystemCatalogBytes:
    """Open catalog paths. The domain receives the bytes."""

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def read_bytes(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def exists(self, path: str) -> bool:
        return Path(path).exists()


filesystem_catalog_bytes = FilesystemCatalogBytes()


def release_publication_marker(marker_path: str | None) -> None:
    """Delete a publication marker after a successful domain commit."""
    if not marker_path:
        return
    path = Path(marker_path)
    if path.is_file():
        path.unlink()
