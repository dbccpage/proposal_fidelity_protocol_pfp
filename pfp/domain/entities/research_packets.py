"""Typed, evidence-only packets for rapid Core research iteration.

These packets carry frozen inputs and model proposals. They never authorize a
patch, certify a theorem, or promote an evidence level.
"""

from __future__ import annotations


from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Dict, Mapping

from governance.contracts import AuthorityEffect
from ..shared_kernel.research_digest import canonical_bytes, digest_payload


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


def _require_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _require_relative_path(value: str, label: str) -> None:
    parts = value.split("/") if isinstance(value, str) else ()
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or ".." in parts
    ):
        raise ValueError(f"{label} must be a normalized relative POSIX path")


class ResearchMode(str, Enum):
    STRICT = "strict"
    FAST = "fast"


class EvidenceCeiling(str, Enum):
    SHAPE_ONLY = "shape_only"
    LOCAL_REPLAY = "local_replay"
    BOUNDARY_CHECKED = "boundary_checked"
    EXPLORATORY_ONLY = "exploratory_only"
    EXTERNAL_ORACLE_REQUIRED = "external_oracle_required"


class ClaimKind(str, Enum):
    DEFINITION = "definition"
    CONJECTURE = "conjecture"
    CONDITIONAL = "conditional"
    EMPIRICAL = "empirical"
    THEOREM_CANDIDATE = "theorem_candidate"
    REFUTATION_CANDIDATE = "refutation_candidate"


class StepRealization(str, Enum):
    STRUCTURAL = "structural"
    MECHANICAL = "mechanical"


@dataclass
class CorpusFileRef:
    path: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        _require_relative_path(self.path, "corpus file path")
        _require_sha256(self.sha256, "corpus file hash")
        if self.byte_count < 0:
            raise ValueError("corpus file byte_count must be nonnegative")

    def canonical_payload(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "byte_count": self.byte_count}


@dataclass
class FrozenCorpus:
    source_root: str
    files: tuple[CorpusFileRef, ...]
    corpus_sha256: str
    schema_version: str = "core.frozen_research_corpus.v1"

    def __post_init__(self) -> None:
        if not self.source_root or not self.files:
            raise ValueError(
                "a frozen corpus needs a source root and at least one file"
            )
        paths = [item.path for item in self.files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("corpus files must be unique and sorted by path")
        _require_sha256(self.corpus_sha256, "corpus_sha256")
        if self.corpus_sha256 != digest_payload(self.hash_payload()):
            raise ValueError("corpus_sha256 does not bind the file manifest")

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "files": [item.canonical_payload() for item in self.files],
        }

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.files)


@dataclass
class ResearchClaim:
    claim_id: str
    text: str
    kind: ClaimKind
    hypotheses: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    falsifier: str = ""

    def __post_init__(self) -> None:
        if _SAFE_ID.fullmatch(self.claim_id) is None or not self.text.strip():
            raise ValueError("claim_id and claim text must be nonempty and stable")
        if not isinstance(self.kind, ClaimKind):
            raise TypeError("claim kind must be a ClaimKind")
        if self.kind is not ClaimKind.DEFINITION and not self.falsifier.strip():
            raise ValueError("every non-definition claim needs a falsifier")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "kind": self.kind.value,
            "hypotheses": list(self.hypotheses),
            "evidence_refs": list(self.evidence_refs),
            "falsifier": self.falsifier,
        }


@dataclass
class ResearchSeedPacket:
    corpus: FrozenCorpus
    objective: str
    proposer_id: str
    mode: ResearchMode
    round_index: int = 1
    proposal_budget: int = 8
    protected_paths: tuple[str, ...] = ()
    focus_codes: tuple[str, ...] = ()
    parent_ledger_sha256: str | None = None
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.EXPLORATORY_ONLY
    authority_effect: AuthorityEffect = AuthorityEffect.None_
    schema_version: str = "core.research_seed_packet.v1"

    def __post_init__(self) -> None:
        if not self.objective.strip() or not self.proposer_id.strip():
            raise ValueError("objective and proposer_id must be nonempty")
        if not isinstance(self.mode, ResearchMode):
            raise TypeError("mode must be a ResearchMode")
        if self.round_index < 1 or self.proposal_budget < 1:
            raise ValueError("round_index and proposal_budget must be positive")
        for path in self.protected_paths:
            _require_relative_path(path, "protected path")
        if self.parent_ledger_sha256 is not None:
            _require_sha256(self.parent_ledger_sha256, "parent_ledger_sha256")
        expected = (
            EvidenceCeiling.BOUNDARY_CHECKED
            if self.mode is ResearchMode.STRICT
            else EvidenceCeiling.EXPLORATORY_ONLY
        )
        if self.evidence_ceiling is not expected:
            raise ValueError("evidence ceiling does not match the research mode")
        if self.authority_effect is not AuthorityEffect.None_:
            raise ValueError("research seed packets must carry AuthorityEffect::None")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "corpus": self.corpus.hash_payload(),
            "corpus_sha256": self.corpus.corpus_sha256,
            "objective": self.objective,
            "proposer_id": self.proposer_id,
            "mode": self.mode.value,
            "round_index": self.round_index,
            "proposal_budget": self.proposal_budget,
            "protected_paths": list(self.protected_paths),
            "focus_codes": list(self.focus_codes),
            "parent_ledger_sha256": self.parent_ledger_sha256,
            "evidence_ceiling": self.evidence_ceiling.value,
            "authority_effect": self.authority_effect.value,
        }

    @property
    def packet_sha256(self) -> str:
        return digest_payload(self.canonical_payload())

    @property
    def packet_id(self) -> str:
        return f"research:{self.packet_sha256[:20]}"


@dataclass
class ResearchProposal:
    proposal_id: str
    seed_sha256: str
    model_id: str
    target_path: str
    summary: str
    proposed_change: str
    claims: tuple[ResearchClaim, ...]
    proof_obligations: tuple[str, ...] = ()
    cochain_problem: Mapping[str, Any] | None = None
    declared_cochain_verdict: str | None = None
    requested_terminal: str = "human_review"
    authority_effect: AuthorityEffect = AuthorityEffect.None_
    schema_version: str = "core.research_proposal.v1"

    def __post_init__(self) -> None:
        if _SAFE_ID.fullmatch(self.proposal_id) is None:
            raise ValueError("proposal_id must be a stable identifier")
        _require_sha256(self.seed_sha256, "seed_sha256")
        _require_relative_path(self.target_path, "target_path")
        if (
            not self.model_id.strip()
            or not self.summary.strip()
            or not self.proposed_change.strip()
        ):
            raise ValueError("model_id, summary, and proposed_change must be nonempty")
        if not self.claims:
            raise ValueError(
                "a research proposal must declare at least one typed claim"
            )
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claim IDs must be unique within a proposal")
        if self.cochain_problem is None and self.declared_cochain_verdict is not None:
            raise ValueError("a cochain verdict requires a cochain problem")
        if self.cochain_problem is not None and not self.declared_cochain_verdict:
            raise ValueError("a cochain problem requires a declared verdict")
        if self.requested_terminal != "human_review":
            raise ValueError("models may request human_review only")
        if self.authority_effect is not AuthorityEffect.None_:
            raise ValueError("research proposals must carry AuthorityEffect::None")
        if self.cochain_problem is not None:
            canonical_bytes(dict(self.cochain_problem))

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "seed_sha256": self.seed_sha256,
            "model_id": self.model_id,
            "target_path": self.target_path,
            "summary": self.summary,
            "proposed_change": self.proposed_change,
            "claims": [claim.canonical_payload() for claim in self.claims],
            "proof_obligations": list(self.proof_obligations),
            "cochain_problem": self.cochain_problem,
            "declared_cochain_verdict": self.declared_cochain_verdict,
            "requested_terminal": self.requested_terminal,
            "authority_effect": self.authority_effect.value,
        }

    @property
    def proposal_sha256(self) -> str:
        return digest_payload(self.canonical_payload())

    @property
    def is_refutation_candidate(self) -> bool:
        return any(
            claim.kind is ClaimKind.REFUTATION_CANDIDATE for claim in self.claims
        )


@dataclass(frozen=True)
class ReplayTracePacket:
    """Canonical replay carrier for one proposed sweep step."""

    paper_sha256: str
    proposal_sha256: str
    gate_receipt_sha256: str
    loop_pass: int
    step_index: int
    status: str
    authority_effect: str = "none"
    schema_version: str = "core.replay_trace.v1"

    def __post_init__(self) -> None:
        _require_sha256(self.paper_sha256, "paper_sha256")
        _require_sha256(self.proposal_sha256, "proposal_sha256")
        _require_sha256(self.gate_receipt_sha256, "gate_receipt_sha256")
        if self.loop_pass < 1 or self.step_index < 1:
            raise ValueError("loop_pass and step_index must be positive")
        if not self.status:
            raise ValueError("status must be non-empty")
        if self.authority_effect != "none":
            raise ValueError("replay trace packets must carry AuthorityEffect::None")

    def canonical_payload(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @property
    def replay_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.paper_sha256 == other.paper_sha256
            and self.proposal_sha256 == other.proposal_sha256
            and self.gate_receipt_sha256 == other.gate_receipt_sha256
            and self.loop_pass == other.loop_pass
            and self.step_index == other.step_index
            and self.status == other.status
            and self.authority_effect == other.authority_effect
            and self.schema_version == other.schema_version
        )


@dataclass
class ResearchStepPacket:
    """Replay carrier used by paper sweeps without pretending to be a DDA proof."""

    carrier_sha256: str
    proposal_sha256: str
    round_index: int
    step_index: int
    realization: StepRealization = StepRealization.STRUCTURAL
    verifier_id: str | None = None
    mechanical_evidence_sha256: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.None_

    def __post_init__(self) -> None:
        _require_sha256(self.carrier_sha256, "carrier_sha256")
        _require_sha256(self.proposal_sha256, "proposal_sha256")
        if self.round_index < 1 or self.step_index < 1:
            raise ValueError("round_index and step_index must be positive")
        if self.authority_effect is not AuthorityEffect.None_:
            raise ValueError("research step packets must carry AuthorityEffect::None")
        if self.realization is StepRealization.MECHANICAL:
            if not self.verifier_id or self.mechanical_evidence_sha256 is None:
                raise ValueError(
                    "mechanical realization requires verifier and evidence"
                )
            _require_sha256(self.mechanical_evidence_sha256, "mechanical evidence")

    def to_replay_trace(
        self, gate_receipt_sha256: str, status: str
    ) -> ReplayTracePacket:
        # This carrier is mutable: revalidate at the actual conversion boundary.
        # The replay-v1 wire identity is lowercase `none`, not a display label.
        self.__post_init__()
        return ReplayTracePacket(
            paper_sha256=self.carrier_sha256,
            proposal_sha256=self.proposal_sha256,
            gate_receipt_sha256=gate_receipt_sha256,
            loop_pass=self.round_index,
            step_index=self.step_index,
            status=status,
            authority_effect=self.authority_effect.value,
        )


__all__ = [
    "ClaimKind",
    "CorpusFileRef",
    "EvidenceCeiling",
    "FrozenCorpus",
    "ReplayTracePacket",
    "ResearchClaim",
    "ResearchMode",
    "ResearchProposal",
    "ResearchSeedPacket",
    "ResearchStepPacket",
    "StepRealization",
    "canonical_bytes",
    "digest_payload",
]


@dataclass
class SymbolGameResearchPacket:
    """Placeholder carried over from the pre-port universe module; no rail
    counterpart exists. Kept only for the package export contract."""

    packet_id: str = "packet_001"
    authority_effect: str = "None"


