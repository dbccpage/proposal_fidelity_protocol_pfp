"""Process-local disk ports. The domain does not open paths."""

from __future__ import annotations

from omega_engine_operations.domain.cicd.text_io import ByteReader, TextReader, TextWriter

_reader: TextReader | None = None
_writer: TextWriter | None = None
_byte_reader: ByteReader | None = None


def install_disk_ports(
    *,
    reader: TextReader | None = None,
    writer: TextWriter | None = None,
    byte_reader: ByteReader | None = None,
) -> None:
    """Record ports supplied by infrastructure. None leaves that port unbound."""
    global _reader, _writer, _byte_reader
    if reader is not None:
        _reader = reader
    if writer is not None:
        _writer = writer
    if byte_reader is not None:
        _byte_reader = byte_reader


def require_text_reader() -> TextReader:
    if _reader is None:
        raise RuntimeError("DOMAIN_DISK_READER_UNBOUND")
    return _reader


def require_text_writer() -> TextWriter:
    if _writer is None:
        raise RuntimeError("DOMAIN_DISK_WRITER_UNBOUND")
    return _writer


def require_byte_reader() -> ByteReader:
    if _byte_reader is None:
        raise RuntimeError("DOMAIN_DISK_READER_UNBOUND")
    return _byte_reader
