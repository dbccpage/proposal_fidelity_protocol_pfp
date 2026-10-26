"""Packetization witness for the Paper Sweep pilot (parse-normalize-render)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from omega_engine_pfp.domain.shared_kernel.research_digest import (
    canonical_bytes,
    digest_payload,
)

GRAMMAR_ID = "omega.markdown.paper_sweep.v1"
SCHEMA_ID = "omega.paper_sweep.packetization.v1"


@dataclass(frozen=True)
class PacketizationWitness:
    grammar_id: str
    schema_id: str
    raw_sha256: str
    normalized_sha256: str
    ast_sha256: str
    reparse_ok: bool
    budgets: Mapping[str, int]
    evidence_class: str = "EvidenceOnly"
    authority_effect: str = "None"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "ast_sha256": self.ast_sha256,
            "authority_effect": self.authority_effect,
            "budgets": dict(self.budgets),
            "evidence_class": self.evidence_class,
            "grammar_id": self.grammar_id,
            "normalized_sha256": self.normalized_sha256,
            "raw_sha256": self.raw_sha256,
            "reparse_ok": self.reparse_ok,
            "schema_id": self.schema_id,
        }

    @property
    def witness_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


@dataclass(frozen=True)
class PacketizationOutput:
    witness: PacketizationWitness
    normalized_text: str
    stage_projections: tuple[dict[str, Any], ...]

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "stage_projections": list(self.stage_projections),
            "witness": self.witness.canonical_payload(),
            "witness_sha256": self.witness.witness_sha256,
        }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_markdown(raw: bytes) -> tuple[str, bytes]:
    """Deterministic normalize: decode UTF-8, unify newlines to LF for AST only.

    The source carrier bytes themselves are never rewritten on disk.
    """
    text = raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized, normalized.encode("utf-8")


def _ast_payload(normalized: str) -> dict[str, Any]:
    """Minimal deterministic AST-like structure (headings + line count)."""
    lines = normalized.split("\n")
    headings = [
        {"line": index + 1, "text": line.strip()}
        for index, line in enumerate(lines)
        if line.startswith("#")
    ]
    return {
        "heading_count": len(headings),
        "headings": headings[:64],  # bounded
        "line_count": len(lines),
        "schema": "omega.paper_ast.minimal.v1",
    }


def packetize_paper(raw: bytes) -> PacketizationOutput:
    """Parse → normalize → render AST → reparse check."""
    raw_hash = _sha256(raw)
    normalized_text, normalized_bytes = _normalize_markdown(raw)
    # Reparse: normalize again from normalized bytes must be stable.
    again_text, again_bytes = _normalize_markdown(normalized_bytes)
    reparse_ok = again_text == normalized_text and again_bytes == normalized_bytes
    if not reparse_ok:
        raise ValueError("packetization reparse failed (normalize not idempotent)")

    ast = _ast_payload(normalized_text)
    ast_hash = digest_payload(ast)
    witness = PacketizationWitness(
        grammar_id=GRAMMAR_ID,
        schema_id=SCHEMA_ID,
        raw_sha256=raw_hash,
        normalized_sha256=_sha256(normalized_bytes),
        ast_sha256=ast_hash,
        reparse_ok=reparse_ok,
        budgets={
            "max_bytes": max(len(raw), 1),
            "max_headings": 64,
            "max_lines": max(len(normalized_text.split("\n")), 1),
        },
    )
    projections = (
        {
            "stage": "parse",
            "status": "OBSERVED",
            "evidence_eligible": False,
            "raw_sha256": raw_hash,
        },
        {
            "stage": "normalize",
            "status": "OBSERVED",
            "evidence_eligible": False,
            "normalized_sha256": witness.normalized_sha256,
        },
        {
            "stage": "ast",
            "status": "OBSERVED",
            "evidence_eligible": False,
            "ast_sha256": ast_hash,
        },
        {
            "stage": "reparse",
            "status": "OBSERVED" if reparse_ok else "REFUSED",
            "evidence_eligible": False,
            "reparse_ok": reparse_ok,
        },
    )
    return PacketizationOutput(
        witness=witness,
        normalized_text=normalized_text,
        stage_projections=projections,
    )


def write_json(path_payload: Mapping[str, Any]) -> bytes:
    return canonical_bytes(path_payload)


__all__ = [
    "GRAMMAR_ID",
    "SCHEMA_ID",
    "PacketizationOutput",
    "PacketizationWitness",
    "packetize_paper",
    "write_json",
]
