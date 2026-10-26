"""A compact strict/fast research loop for papers and research programs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

try:
    from omega_discrete_deformation_algebra import FiniteCochainComplex
except ImportError:
    class FiniteCochainComplex:
        pass

try:
    from omega_solvers.finite_cochain_obstruction_solver import (
        Verdict,
        analyze_finite_cochain,
    )
except ImportError:
    from enum import Enum
    class Verdict(str, Enum):
        SUCCESS = "SUCCESS"
        FAIL = "FAIL"
    def analyze_finite_cochain(*args: Any, **kwargs: Any) -> Any:
        return None

from omega_engine_research_papers.domain.models.paper_iteration.evaluation import (
    GateReceipt,
    GateVerdict,
    ResearchEvaluation,
    ResearchGate,
)

try:
    from omega_symbol_game.research_packets import (
        ClaimKind,
        EvidenceCeiling,
        FrozenCorpus,
        ResearchMode,
        ResearchProposal,
        ResearchSeedPacket,
        canonical_bytes,
    )
except ImportError:
    from enum import Enum
    class ClaimKind(str, Enum):
        LEAN = "LEAN"
    class EvidenceCeiling(str, Enum):
        FORMAL = "FORMAL"
    class ResearchMode(str, Enum):
        FAST = "fast"
        FULL = "full"
        SYMBOL = "symbol"
    class ResearchProposal:
        pass
    class ResearchSeedPacket:
        pass
    class FrozenCorpus:
        pass
    def canonical_bytes(data: Any) -> bytes:
        return b""



HOST_EVALUATOR_ID = "omega-python-host"
_CORPUS_REPLAY_REQUIRED = object()
EXTERNAL_GATES = {
    ResearchGate.MECHANICAL,
    ResearchGate.ADVERSARIAL,
    ResearchGate.CITATION_PROVENANCE,
}
_AUTHORITY_LANGUAGE = re.compile(
    r"\b(mints? authority|authority granted|authorized transition|human approved|self[- ]certif(?:y|ied))\b",
    re.IGNORECASE,
)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def external_gate_receipt(
    gate: ResearchGate,
    evaluator_id: str,
    evidence: bytes | str,
    reason_code: str = "EXTERNALLY_CHECKED",
    verdict: GateVerdict = GateVerdict.PASS,
) -> GateReceipt:
    if gate not in EXTERNAL_GATES:
        raise ValueError(f"{gate.value} is host-owned and cannot be supplied externally")
    raw = evidence if isinstance(evidence, bytes) else evidence.encode("utf-8")
    return GateReceipt(
        gate=gate,
        verdict=verdict,
        reason_code=reason_code,
        evaluator_id=evaluator_id,
        evidence_sha256=hashlib.sha256(raw).hexdigest(),
    )


class OmegaResearchEngine:
    """Evaluate frozen research carriers through DDA objects and math solvers.

    Proposal generation remains outside the engine. Codex, Claude, Antigravity,
    or another source receives a seed packet and returns ``ResearchProposal``.
    No method applies a proposed patch or performs human promotion.
    """

    def start(
        self,
        corpus: FrozenCorpus,
        objective: str,
        proposer_id: str,
        mode: ResearchMode = ResearchMode.FAST,
        proposal_budget: int = 8,
        protected_paths: Iterable[str] = (),
    ) -> ResearchSeedPacket:
        ceiling = (
            EvidenceCeiling.BOUNDARY_CHECKED
            if mode is ResearchMode.STRICT
            else EvidenceCeiling.EXPLORATORY_ONLY
        )
        return ResearchSeedPacket(
            corpus=corpus,
            objective=objective,
            proposer_id=proposer_id,
            mode=mode,
            proposal_budget=proposal_budget,
            protected_paths=tuple(sorted(set(protected_paths))),
            evidence_ceiling=ceiling,
        )

    @staticmethod
    def render_model_packet(packet: ResearchSeedPacket) -> str:
        payload = {
            "packet": packet.canonical_payload(),
            "packet_id": packet.packet_id,
            "packet_sha256": packet.packet_sha256,
            "required_output": "omega.research_proposal.v1 JSON",
            "hard_rules": [
                "propose only; do not apply changes",
                "declare every claim type and falsifier",
                "preserve the frozen corpus hash",
                "request human_review only",
                "authority_effect must remain none",
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    @staticmethod
    def _cochain_receipt(proposal: ResearchProposal) -> GateReceipt | None:
        if proposal.cochain_problem is None:
            return None
        problem = dict(proposal.cochain_problem)
        try:
            dimensions = tuple(problem["dimensions"])
            complex_ = FiniteCochainComplex.from_rows(
                dimensions=dimensions,
                d0=problem["d0"],
                d1=problem["d1"],
            )
            analysis = analyze_finite_cochain(complex_, problem["beta"])
        except (KeyError, TypeError, ValueError) as error:
            return GateReceipt(
                gate=ResearchGate.MECHANICAL,
                verdict=GateVerdict.REFUSE,
                reason_code=f"INVALID_COHCHAIN_PACKET:{type(error).__name__}",
                evaluator_id=HOST_EVALUATOR_ID,
            )
        if proposal.declared_cochain_verdict != analysis.verdict.value:
            return GateReceipt(
                gate=ResearchGate.MECHANICAL,
                verdict=GateVerdict.FAIL,
                reason_code="DECLARED_COHCHAIN_VERDICT_MISMATCH",
                evaluator_id=HOST_EVALUATOR_ID,
                evidence_sha256=analysis.evidence_sha256,
            )
        reason = {
            Verdict.INVALID_COMPLEX: "INVALID_COMPLEX_REPRODUCED",
            Verdict.CURVATURE: "CURVATURE_REPRODUCED",
            Verdict.EXACT_REPAIR: "EXACT_REPAIR_WITNESSED",
            Verdict.CLOSED_RESIDUAL: "CLOSED_RESIDUAL_WITNESSED",
        }[analysis.verdict]
        return GateReceipt(
            gate=ResearchGate.MECHANICAL,
            verdict=GateVerdict.PASS,
            reason_code=reason,
            evaluator_id=HOST_EVALUATOR_ID,
            evidence_sha256=analysis.evidence_sha256,
        )

    @staticmethod
    def _claim_hygiene(proposal: ResearchProposal) -> GateReceipt:
        problems: list[str] = []
        for claim in proposal.claims:
            if claim.kind in {ClaimKind.CONDITIONAL, ClaimKind.THEOREM_CANDIDATE}:
                if not claim.hypotheses:
                    problems.append(f"{claim.claim_id}:MISSING_HYPOTHESES")
            if claim.kind in {ClaimKind.EMPIRICAL, ClaimKind.THEOREM_CANDIDATE}:
                if not claim.evidence_refs:
                    problems.append(f"{claim.claim_id}:MISSING_EVIDENCE_REF")
            if re.search(r"\b(proves?|guarantees?)\b", claim.text, re.IGNORECASE):
                if claim.kind is not ClaimKind.THEOREM_CANDIDATE or not claim.evidence_refs:
                    problems.append(f"{claim.claim_id}:UNSCOPED_PROOF_LANGUAGE")
        if problems:
            return GateReceipt(
                gate=ResearchGate.CLAIM_HYGIENE,
                verdict=GateVerdict.FAIL,
                reason_code=";".join(problems),
                evaluator_id=HOST_EVALUATOR_ID,
            )
        return GateReceipt(
            gate=ResearchGate.CLAIM_HYGIENE,
            verdict=GateVerdict.PASS,
            reason_code="TYPED_CLAIMS_AND_HEDGES_PRESENT",
            evaluator_id=HOST_EVALUATOR_ID,
            evidence_sha256=proposal.proposal_sha256,
        )

    def evaluate(
        self,
        packet: ResearchSeedPacket,
        proposal: ResearchProposal,
        evaluator_id: str,
        external_receipts: Iterable[GateReceipt] = (),
        *,
        corpus_replay_error: str | None | object = _CORPUS_REPLAY_REQUIRED,
    ) -> ResearchEvaluation:
        by_gate: dict[ResearchGate, GateReceipt] = {}
        for receipt in external_receipts:
            if receipt.gate not in EXTERNAL_GATES:
                raise ValueError(f"external receipt attempted to override {receipt.gate.value}")
            if receipt.gate in by_gate:
                raise ValueError(f"duplicate external receipt for {receipt.gate.value}")
            if receipt.evaluator_id != evaluator_id:
                raise ValueError("external gate evaluator does not match evaluation identity")
            by_gate[receipt.gate] = receipt

        gates: dict[ResearchGate, GateReceipt] = {
            ResearchGate.PACKET_SHAPE: GateReceipt(
                gate=ResearchGate.PACKET_SHAPE,
                verdict=GateVerdict.PASS,
                reason_code="TYPED_PACKET_PARSED",
                evaluator_id=HOST_EVALUATOR_ID,
                evidence_sha256=proposal.proposal_sha256,
            )
        }

        if corpus_replay_error is _CORPUS_REPLAY_REQUIRED:
            gates[ResearchGate.CORPUS_REPLAY] = GateReceipt(
                gate=ResearchGate.CORPUS_REPLAY,
                verdict=GateVerdict.REFUSE,
                reason_code="PIPELINE_CORPUS_REPLAY_REQUIRED",
                evaluator_id=HOST_EVALUATOR_ID,
            )
        elif corpus_replay_error is not None:
            gates[ResearchGate.CORPUS_REPLAY] = GateReceipt(
                gate=ResearchGate.CORPUS_REPLAY,
                verdict=GateVerdict.REFUSE,
                reason_code=str(corpus_replay_error),
                evaluator_id=HOST_EVALUATOR_ID,
            )
        else:
            gates[ResearchGate.CORPUS_REPLAY] = GateReceipt(
                gate=ResearchGate.CORPUS_REPLAY,
                verdict=GateVerdict.PASS,
                reason_code="FROZEN_CORPUS_REPLAYED",
                evaluator_id=HOST_EVALUATOR_ID,
                evidence_sha256=packet.corpus.corpus_sha256,
            )

        fidelity_errors: list[str] = []
        if proposal.seed_sha256 != packet.packet_sha256:
            fidelity_errors.append("SEED_HASH_MISMATCH")
        if proposal.model_id != packet.proposer_id:
            fidelity_errors.append("PROPOSER_ID_MISMATCH")
        if proposal.target_path not in packet.corpus.paths:
            fidelity_errors.append("TARGET_OUTSIDE_FROZEN_CORPUS")
        if proposal.target_path in packet.protected_paths:
            fidelity_errors.append("PROTECTED_TARGET")
        gates[ResearchGate.FIDELITY] = GateReceipt(
            gate=ResearchGate.FIDELITY,
            verdict=GateVerdict.FAIL if fidelity_errors else GateVerdict.PASS,
            reason_code=";".join(fidelity_errors) if fidelity_errors else "SEED_AND_TARGET_BOUND",
            evaluator_id=HOST_EVALUATOR_ID,
            evidence_sha256=None if fidelity_errors else packet.packet_sha256,
        )

        gates[ResearchGate.CLAIM_HYGIENE] = self._claim_hygiene(proposal)
        gates[ResearchGate.MECHANICAL] = self._cochain_receipt(proposal) or by_gate.get(
            ResearchGate.MECHANICAL,
            GateReceipt(
                gate=ResearchGate.MECHANICAL,
                verdict=GateVerdict.OPEN,
                reason_code="MECHANICAL_EVALUATOR_REQUIRED",
                evaluator_id=evaluator_id,
            ),
        )
        gates[ResearchGate.ADVERSARIAL] = by_gate.get(
            ResearchGate.ADVERSARIAL,
            GateReceipt(
                gate=ResearchGate.ADVERSARIAL,
                verdict=GateVerdict.OPEN,
                reason_code="ADVERSARIAL_REVIEW_REQUIRED",
                evaluator_id=evaluator_id,
            ),
        )

        external_refs = tuple(
            reference
            for claim in proposal.claims
            for reference in claim.evidence_refs
            if reference.startswith(("http://", "https://", "doi:", "arxiv:"))
        )
        citation = by_gate.get(ResearchGate.CITATION_PROVENANCE)
        if citation is not None:
            gates[ResearchGate.CITATION_PROVENANCE] = citation
        elif external_refs:
            gates[ResearchGate.CITATION_PROVENANCE] = GateReceipt(
                gate=ResearchGate.CITATION_PROVENANCE,
                verdict=GateVerdict.OPEN,
                reason_code="EXTERNAL_REFERENCES_REQUIRE_VERIFICATION",
                evaluator_id=evaluator_id,
            )
        else:
            local_refs = [reference for claim in proposal.claims for reference in claim.evidence_refs]
            gates[ResearchGate.CITATION_PROVENANCE] = GateReceipt(
                gate=ResearchGate.CITATION_PROVENANCE,
                verdict=GateVerdict.PASS,
                reason_code="NO_UNVERIFIED_EXTERNAL_REFERENCE",
                evaluator_id=HOST_EVALUATOR_ID,
                evidence_sha256=hashlib.sha256(
                    canonical_bytes({"local_refs": local_refs})
                ).hexdigest(),
            )

        authority_text = "\n".join(
            [proposal.summary, proposal.proposed_change]
            + [claim.text for claim in proposal.claims]
        )
        authority_attempt = _AUTHORITY_LANGUAGE.search(authority_text)
        gates[ResearchGate.AUTHORITY_FIREWALL] = GateReceipt(
            gate=ResearchGate.AUTHORITY_FIREWALL,
            verdict=GateVerdict.REFUSE if authority_attempt else GateVerdict.PASS,
            reason_code=(
                "MODEL_AUTHORITY_CLAIM_DETECTED"
                if authority_attempt
                else "AUTHORITY_EFFECT_NONE"
            ),
            evaluator_id=HOST_EVALUATOR_ID,
            evidence_sha256=None if authority_attempt else _hash_text(authority_text),
        )

        return ResearchEvaluation(
            packet_sha256=packet.packet_sha256,
            proposal_sha256=proposal.proposal_sha256,
            proposer_id=proposal.model_id,
            evaluator_id=evaluator_id,
            mode=packet.mode,
            gates=tuple(gates[gate] for gate in ResearchGate),
            refutation_candidate=proposal.is_refutation_candidate,
        )


    def next_round(
        self,
        packet: ResearchSeedPacket,
        evaluation: ResearchEvaluation,
        proposer_id: str,
        parent_ledger_sha256: str | None = None,
    ) -> ResearchSeedPacket:
        # A round advances against the exact frozen corpus. If a human edits the
        # sources, the edit starts a new seed rather than silently rebinding this
        # packet to a different research object.
        return ResearchSeedPacket(
            corpus=packet.corpus,
            objective=packet.objective,
            proposer_id=proposer_id,
            mode=packet.mode,
            round_index=packet.round_index + 1,
            proposal_budget=packet.proposal_budget,
            protected_paths=packet.protected_paths,
            focus_codes=evaluation.focus_codes,
            parent_ledger_sha256=parent_ledger_sha256,
            evidence_ceiling=packet.evidence_ceiling,
        )


__all__ = ["HOST_EVALUATOR_ID", "OmegaResearchEngine", "external_gate_receipt"]
