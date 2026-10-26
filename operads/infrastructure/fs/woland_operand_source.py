"""Read exact, small OEWAS operand sources without following catalogue aliases.

This is a candidate-source reader, not an admission authority. AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path

from ...application.woland_candidate_plan import PlanRefusal
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.value_objects.identifier import SkillId
from ..parser.markdown_parser_adapter import LosslessMarkdownParserAdapter

_SOURCE_RELATIVE = Path("omega_engine_operads/catalog/operands/v1")
_NAME = re.compile(r"[a-z][a-z0-9_-]*\Z")
_MAX_SOURCE_BYTES = 16384


def read_woland_operand_sources(
    repo_root: Path, relative_paths: tuple[str, ...]
) -> tuple[SkillDocumentV3, ...]:
    """Read explicitly selected `<domain>/<id>.md` files in caller order.

    File contents are hashed by the lossless parser. No directory crawl, glob,
    fallback to `.agents`, or self-declared admission occurs.
    """
    if type(relative_paths) is not tuple or not relative_paths:
        raise PlanRefusal("SOURCE_SELECTION_INVALID", "nonempty tuple required")
    if len(relative_paths) != len(set(relative_paths)):
        raise PlanRefusal("DUPLICATE_SOURCE_PATH", "each source is selected once")
    root = repo_root.resolve()
    source_root = root / _SOURCE_RELATIVE
    cursor = root
    for part in _SOURCE_RELATIVE.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PlanRefusal("SOURCE_ALIAS_REFUSED", str(cursor))
    if not source_root.is_dir():
        raise PlanRefusal("SOURCE_ROOT_UNAVAILABLE", str(source_root))
    parser = LosslessMarkdownParserAdapter()
    documents: list[SkillDocumentV3] = []
    for selected in relative_paths:
        if type(selected) is not str or "\\" in selected:
            raise PlanRefusal("SOURCE_PATH_INVALID", repr(selected))
        parts = selected.split("/")
        if (
            len(parts) != 2
            or _NAME.fullmatch(parts[0]) is None
            or not parts[1].endswith(".md")
            or _NAME.fullmatch(parts[1][:-3]) is None
        ):
            raise PlanRefusal("SOURCE_PATH_INVALID", selected)
        path = source_root.joinpath(*parts)
        if path.parent.is_symlink() or path.is_symlink():
            raise PlanRefusal("SOURCE_ALIAS_REFUSED", selected)
        if not path.is_file() or not path.resolve().is_relative_to(source_root.resolve()):
            raise PlanRefusal("SOURCE_UNAVAILABLE", selected)
        raw = path.read_bytes()
        if not raw or len(raw) > _MAX_SOURCE_BYTES:
            raise PlanRefusal("SOURCE_SIZE_INVALID", selected)
        operation_id = f"{parts[0]}.{parts[1][:-3]}"
        source_relative_path = (_SOURCE_RELATIVE / selected).as_posix()
        parsed = parser.parse_document(SkillId(operation_id), source_relative_path, raw)
        if parsed.is_err:
            raise PlanRefusal(parsed.unwrap_err().code, source_relative_path)
        document = parsed.unwrap()
        if len(document.operations) != 1 or str(document.operations[0].operation_id) != operation_id:
            raise PlanRefusal("SOURCE_OPERATION_ID_MISMATCH", selected)
        documents.append(document)
    return tuple(documents)


__all__ = ["read_woland_operand_sources"]
