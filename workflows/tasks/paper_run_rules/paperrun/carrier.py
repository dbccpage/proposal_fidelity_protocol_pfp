"""Local paper carrier: content-address a paper folder and read its declared claims.

Trimmed port of the internal carrier adapter: only the tree hash and claim reading
that the planning use case needs. AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path

from paperrun.claim_ir import ClaimIRDocument
from paperrun.claim_node import ClaimNode
from paperrun.enums import ClaimKind
from paperrun.errors import PaperRunGraphError
from paperrun.tree_hash import SnapshotError, tree_sha256


def parse_claim_ir(root: Path) -> list[ClaimNode]:
    ir = root / "docs" / "claim_ir.yaml"
    if not ir.is_file():
        return []
    doc = ClaimIRDocument.from_yaml(ir.read_text(encoding="utf-8"))
    return doc.to_claim_nodes()


def parse_ledger_ids(root: Path) -> list[ClaimNode]:
    """Fallback: rough claim IDs from a claim ledger markdown file."""
    hits = list(root.glob("*_claim_ledger.md")) + list(root.glob("*claim_ledger*.md"))
    if not hits:
        return []
    text = hits[0].read_text(encoding="utf-8", errors="replace")
    ids = sorted(set(re.findall(r"\b([A-Z]\d{1,3}|[A-Z]{1,3}-\d{2,4})\b", text)))
    return [ClaimNode(claim_id=i, kind="unknown", claim_ceiling="UNKNOWN") for i in ids[:80]]


def parse_claims(paper_root: Path | str) -> list[ClaimNode]:
    root = Path(paper_root).resolve()
    claims = parse_claim_ir(root)
    if not claims:
        claims = parse_ledger_ids(root)
    if not claims:
        claims = [
            ClaimNode(
                claim_id="PKG",
                kind=ClaimKind.RELEASE.value,
                claim_ceiling="DECLARED",
            )
        ]
    return claims


def compute_carrier_hash(paper_root: Path | str) -> str:
    root = Path(paper_root).resolve()
    if not root.is_dir():
        raise PaperRunGraphError(f"not a directory: {root}")
    try:
        return tree_sha256(root)
    except SnapshotError as exc:
        raise PaperRunGraphError(str(exc)) from exc


class LocalPaperCarrier:
    """Filesystem carrier port used by ``paper_plan`` when no port is supplied."""

    def compute_tree_hash(self, paper_root: Path | str) -> str:
        return compute_carrier_hash(paper_root)

    def parse_claims(self, paper_root: Path | str) -> list[ClaimNode]:
        return parse_claims(paper_root)


__all__ = [
    "LocalPaperCarrier",
    "compute_carrier_hash",
    "parse_claim_ir",
    "parse_claims",
    "parse_ledger_ids",
]
