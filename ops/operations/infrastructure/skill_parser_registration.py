"""Register the lossless skill parser on import.

Domain audits call the registered parser. This module is the composition root.
"""

from __future__ import annotations

from typing import Any

from operations.domain.packaging.skill_frontmatter_audit import (
    SkillParseFailure,
    register_skill_parser,
)
from operads.infrastructure.lossless_skill_parser import (
    LosslessParseError,
    parse_bytes,
)


class _ParsedSkill:
    def __init__(self, document: Any) -> None:
        self._document = document

    def render(self) -> bytes:
        return self._document.render()

    def frontmatter_mapping(self) -> Any:
        try:
            return self._document.frontmatter_mapping()
        except LosslessParseError as exc:
            raise SkillParseFailure(str(exc)) from exc


def _parse(raw: bytes) -> _ParsedSkill:
    try:
        return _ParsedSkill(parse_bytes(raw))
    except LosslessParseError as exc:
        raise SkillParseFailure(str(exc)) from exc


register_skill_parser(_parse)
