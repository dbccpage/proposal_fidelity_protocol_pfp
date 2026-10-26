"""Relational Prompt Representation Model.

Characteristics:
- Encodes prompt spans under Relational Normal Form (profile: sqlite_strict_text_set_v1).
- Emits SQL header comments and strict relational row insertions into `prompt_spans`.
- Evaluated on benchmark tasks in results.md (16 trials, 75.0% validation rate, avg 218.5 input tokens, +132.4 tok overhead).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Dict, List, Literal

from pydantic import Field, StrictStr, model_validator

from .common import (
    MAX_SEGMENTS,
    BaseRepresentationRecord,
    Digest,
    Role,
    sha256_digest,
)

SQLITE_STRICT_DDL = """CREATE TABLE IF NOT EXISTS prompt_spans (
    slot TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('task', 'constraint', 'context', 'output', 'unresolved')),
    text TEXT NOT NULL
) STRICT;"""


class RelationalSpanRow(BaseRepresentationRecord):
    """Represents a single row tuple for the prompt_spans relation."""

    slot: Annotated[StrictStr, Field(pattern=r"^s[0-9]+$")]
    role: Role
    text: StrictStr

    def to_sql_insert(self, table_name: str = "prompt_spans") -> str:
        """Emits the insert statement exactly as sent in the recorded pilot dispatches.

        The `::text` cast and the JSON-escaped (double-quoted) text are PostgreSQL-style and are
        not executable against the SQLite STRICT DDL. They are kept byte-for-byte so the rendered
        prompt digests match the 64 recorded dispatches; this is a recorded wire format, not a
        runnable SQLite script.
        """
        escaped_json_text = json.dumps(self.text)
        return f"INSERT INTO {table_name} (slot, role, text) VALUES ('{self.slot}', '{self.role}', {escaped_json_text}::text);"


class RelationalPromptRepresentation(BaseRepresentationRecord):
    """Encapsulates the SQL DDL and relational span table prompt representation."""

    source_id: StrictStr = Field(..., min_length=1)
    source_sha256: Digest
    proposal_sha256: Digest
    profile: Literal["sqlite_strict_text_set_v1"] = "sqlite_strict_text_set_v1"
    table_name: StrictStr = "prompt_spans"
    spans: Annotated[List[RelationalSpanRow], Field(min_length=1, max_length=MAX_SEGMENTS)]
    representation_kind: Literal["relational"] = "relational"
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def validate_relational_invariants(self) -> RelationalPromptRepresentation:
        # Verify slot sequence monotonicity s0, s1, ...
        for idx, span in enumerate(self.spans):
            expected_slot = f"s{idx}"
            if span.slot != expected_slot:
                raise ValueError(
                    f"SLOT_ORDER_MISMATCH: span {idx} has slot '{span.slot}', expected '{expected_slot}'"
                )

        # Verify mandatory task span
        if not any(span.role == "task" for span in self.spans):
            raise ValueError("TASK_SPAN_REQUIRED: at least one span must have role='task'")

        return self

    def render(self) -> str:
        """Renders the canonical SQL prompt wire representation."""
        lines = [
            f"-- Prompt Relational Normal Form (profile: {self.profile})",
            f"-- Source ID: {self.source_id} | Hash: {self.source_sha256[:16]}",
            "-- Occurrences and role bindings:",
        ]
        for span in self.spans:
            lines.append(span.to_sql_insert(self.table_name))
        return "\n".join(lines)

    def prompt_sha256(self) -> str:
        """Returns the SHA-256 digest of the rendered relational SQL wire prompt."""
        return sha256_digest(self.render())

    @staticmethod
    def ddl() -> str:
        """Returns the sovereign SQLite STRICT schema definition for prompt_spans."""
        return SQLITE_STRICT_DDL

    def to_envelope(self) -> Dict[str, Any]:
        """Serializes the prompt representation metadata envelope."""
        return {
            "source_id": self.source_id,
            "representation_kind": self.representation_kind,
            "profile": self.profile,
            "table_name": self.table_name,
            "source_sha256": self.source_sha256,
            "proposal_sha256": self.proposal_sha256,
            "prompt_sha256": self.prompt_sha256(),
            "authority_effect": self.authority_effect,
            "span_count": len(self.spans),
            "rendered_prompt": self.render(),
        }

    @classmethod
    def from_spans(
        cls,
        source_id: str,
        source_sha256: str,
        proposal_sha256: str,
        spans: List[RelationalSpanRow],
    ) -> RelationalPromptRepresentation:
        """Convenience factory constructor."""
        return cls(
            source_id=source_id,
            source_sha256=source_sha256,
            proposal_sha256=proposal_sha256,
            spans=spans,
            representation_kind="relational",
            authority_effect="None",
        )


class SqlitePromptRepresentation(RelationalPromptRepresentation):
    """Executable, lossless SQL profile; historical v1 wire bytes stay unchanged.

    Only host-rendered DDL and inserts are executable. Text is encoded as a UTF-8
    blob cast to TEXT, so quotes, comments and NUL bytes remain data. This does
    not authorize execution of SQL supplied by a model.
    """

    profile: Literal["sqlite_strict_utf8_v2"] = "sqlite_strict_utf8_v2"
    table_name: Literal["prompt_spans"] = "prompt_spans"

    def render(self) -> str:
        from .common import MAX_PROMPT_BYTES

        lines = [SQLITE_STRICT_DDL]
        for span in self.spans:
            encoded = span.text.encode("utf-8").hex()
            lines.append(
                "INSERT INTO prompt_spans (slot, role, text) VALUES "
                f"('{span.slot}', '{span.role}', CAST(X'{encoded}' AS TEXT));"
            )
        rendered = "\n".join(lines)
        if len(rendered.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("SQL_PROMPT_BYTE_LIMIT")
        return rendered
