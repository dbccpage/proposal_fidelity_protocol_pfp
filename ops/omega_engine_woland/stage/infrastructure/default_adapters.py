"""Production default adapters for the Woland stage connecting to canonical runtime crates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnReplyV1, SeatTurnRequestV1

from ..application.emission import (
    DdaSink,
    IntelligenceEventV1,
    SymbolGamePacketSink,
    UnsSink,
    UtsSink,
)
from ..application.ports import (
    AntibodyStorePort,
    CemeterySink,
    ContinuationPortV1,
    ContinueDecisionKindV1,
    ContinueDecisionV1,
    SeatPortV1,
    ValuatorPortV1,
)
from ..domain import (
    AUTHORITY_EFFECT_NONE,
    AntibodyEntryV1,
    CandidateProposalV1,
    CemeteryHeadstoneV1,
    DdaLetter,
    DdaStepReceipt,
    DdaStepV1,
    EvaluatorEpochV1,
    SwarmRunStateV1,
    ValuationReceiptV1,
    canonical_json_bytes,
    strict_json_loads,
    validate_dda_purity,
)
from .genealogy_store import FileGenealogyAdapter as FileGenealogyAdapter
from .runtime_stores import UniversalNarrativeStore, UniversalTraceStore


def _atomic_write_json(
    path: Path,
    payload: dict[str, Any],
    *,
    replace_existing: bool,
) -> None:
    """Write one canonical JSON record without exposing partial bytes."""
    body = canonical_json_bytes(payload) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace_existing:
        if path.read_bytes() != body:
            raise ValueError(f"content-addressed record collision at {path}")
        return
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() and not replace_existing:
            if path.read_bytes() != body:
                raise ValueError(f"content-addressed record collision at {path}")
            return
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


_EXPECTED_DDC_ALPHABET: tuple[str, ...] = ("E", "R", "C", "I", "Λ", "D", "M", "T")


def _require_matching_dda_alphabet() -> None:
    """Verify the bound DdcLetter alphabet against the 8-character DDC alphabet in omega_wdp."""
    from ..domain import ddc as ddc_module

    ddc_letter = getattr(ddc_module, "DdcLetter", None)
    canonical = getattr(ddc_letter, "CANONICAL_ALPHABET", ()) if ddc_letter is not None else ()
    if tuple(canonical) != _EXPECTED_DDC_ALPHABET:
        raise ValueError(
            f"DdcLetter.CANONICAL_ALPHABET {canonical!r} does not match expected "
            f"8-letter DDC alphabet {_EXPECTED_DDC_ALPHABET!r}"
        )


class UniversalTraceUtsSink(UtsSink):
    """UTS adapter wrapping the canonical store at an explicit repository root or in-memory."""

    def __init__(
        self, repo_root: Path | str | None = None, *, persist_to_disk: bool = False
    ) -> None:
        self.persist_to_disk = persist_to_disk
        self.store = (
            UniversalTraceStore(repo_root=repo_root or ".") if persist_to_disk else None
        )
        self.recorded_events: list[dict[str, Any]] = []

    def record_event(
        self, event: IntelligenceEventV1, payload: bytes | str
    ) -> Result[str, Refusal]:
        if self.store is not None:
            res = self.store.record_event(event, payload)
            if res.is_err:
                return res
        event_dict = event.to_dict() if hasattr(event, "to_dict") else dict(event)
        self.recorded_events.append({"event": event_dict, "payload": payload})
        return Ok(event.ie_id)


class UniversalNarrativeUnsSink(UnsSink):
    """UNS adapter wrapping the canonical store at an explicit repository root or in-memory."""

    def __init__(
        self, repo_root: Path | str | None = None, *, persist_to_disk: bool = False
    ) -> None:
        self.persist_to_disk = persist_to_disk
        self.store = (
            UniversalNarrativeStore(repo_root=repo_root or ".")
            if persist_to_disk
            else None
        )
        self.recorded_narratives: list[tuple[str, str]] = []

    def record_narrative(self, session_id: str, turn_md: str) -> Result[str, Refusal]:
        if self.store is not None:
            res = self.store.record_narrative(session_id, turn_md)
            if res.is_err:
                return res
        self.recorded_narratives.append((session_id, turn_md))
        return Ok(f"narrative:{session_id}")


class DiscreteDeformationAlgebraDdaSink(DdaSink):
    """DDA sink materializing canonical runtime DDA receipt types and optional file persistence."""

    def __init__(self, trace_id: str | Path | None = None) -> None:
        _require_matching_dda_alphabet()
        self.trace_id = str(trace_id or "dda_trace")
        self.recorded_steps: list[DdaStepV1] = []
        self.receipts: list[DdaStepReceipt] = []
        self.rolled_back_steps: list[dict[str, Any]] = []
        self.compensation_branches: dict[str, list[DdaStepV1]] = {}
        self._checkpoints: list[int] = []
        self._terminalized = False
        self._head_sha256: str | None = None
        self._next_sequence: int = 0
        self.output_file = (
            Path(trace_id)
            if trace_id
            and ("." in str(trace_id) or "/" in str(trace_id) or "\\" in str(trace_id))
            else None
        )

    @property
    def head_sha256(self) -> str | None:
        """Cryptographic head digest of the persisted DDA/DDC hash chain."""
        return self._head_sha256

    @property
    def next_sequence(self) -> int:
        """Next ordinal sequence index in the append-only audit hash chain."""
        return self._next_sequence

    def record_step(self, step: DdaStepV1) -> Result[str, Refusal]:
        purity_check = validate_dda_purity(step)
        if purity_check.is_err:
            return Err(purity_check.unwrap_err())
        if self._terminalized:
            return Err(
                Refusal(
                    code="DDA_TERMINALIZED",
                    message="Cannot append a DDA step after terminalization",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters",
                )
            )

        try:
            crate_letter = step.letter
            witness = step.witness_hash or step.receipt_sha256
            receipt = DdaStepReceipt(
                step_id=f"{self.trace_id}:DDA_STEP_{len(self.receipts) + 1:03d}",
                letter=crate_letter,
                input_state_hash=hashlib.sha256(
                    step.before_class.encode("utf-8")
                ).hexdigest(),
                output_state_hash=hashlib.sha256(
                    step.after_class.encode("utf-8")
                ).hexdigest(),
                carrier_hash=hashlib.sha256(
                    step.carrier_hash.encode("utf-8")
                ).hexdigest(),
                diagnostic_before=step.before_class,
                diagnostic_after=step.after_class,
                required_witness=witness,
                witness_hash=hashlib.sha256(witness.encode("utf-8")).hexdigest(),
                authority_effect=AUTHORITY_EFFECT_NONE,
            )
        except (TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="DDA_SINK_ERROR",
                    message=f"Canonical DDA trace emission failed: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters",
                )
            )

        self.recorded_steps.append(step)
        self.receipts.append(receipt)
        if self.output_file:
            step_dict = step.to_dict()
            record_payload: dict[str, Any] = {
                "sequence": self._next_sequence,
                "parent_sha256": self._head_sha256,
                "record_type": "step",
                **step_dict,
            }
            material = canonical_json_bytes({
                k: v for k, v in record_payload.items() if k != "record_sha256"
            })
            digest = hashlib.sha256(material).hexdigest()
            record_payload["record_sha256"] = digest
            self._head_sha256 = digest
            self._next_sequence += 1
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, "a", encoding="utf-8") as fp:
                    fp.write(json.dumps(record_payload, ensure_ascii=False) + "\n")
            except (OSError, TypeError, ValueError) as exc:
                return Err(
                    Refusal(
                        code="DDA_PERSIST_FAILED",
                        message=f"Failed to persist DDA step: {exc}",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.DiscreteDeformationAlgebraDdaSink",
                    )
                )
        self._terminalized = crate_letter == DdaLetter.T
        return Ok(receipt.step_id)

    def checkpoint(self) -> int:
        """Record a tape checkpoint at current step count."""
        cp = len(self.recorded_steps)
        self._checkpoints.append(cp)
        return cp

    def rollback(
        self, checkpoint_index: int | None = None, *, reason: str = ""
    ) -> Result[tuple[DdaStepV1, ...], Refusal]:
        """Roll back recorded steps to a checkpoint, archiving uncommitted steps with receipts."""
        target_idx = (
            checkpoint_index
            if checkpoint_index is not None
            else (self._checkpoints.pop() if self._checkpoints else 0)
        )
        if type(target_idx) is not int or target_idx < 0 or target_idx > len(self.recorded_steps):
            return Err(
                Refusal(
                    code="INVALID_CHECKPOINT",
                    message=f"Checkpoint index {target_idx} is out of bounds [0, {len(self.recorded_steps)}]",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.DiscreteDeformationAlgebraDdaSink.rollback",
                )
            )

        rolled_steps = self.recorded_steps[target_idx:]
        rolled_receipts = self.receipts[target_idx:]
        self.recorded_steps = self.recorded_steps[:target_idx]
        self.receipts = self.receipts[:target_idx]

        for s, r in zip(rolled_steps, rolled_receipts, strict=True):
            self.rolled_back_steps.append(
                {
                    "step": s,
                    "receipt": r,
                    "reason": reason,
                    "rolled_back_from_index": target_idx,
                    "authority_effect": AUTHORITY_EFFECT_NONE,
                }
            )

        if self.output_file and rolled_steps:
            rollback_payload: dict[str, Any] = {
                "sequence": self._next_sequence,
                "parent_sha256": self._head_sha256,
                "record_type": "rollback",
                "checkpoint_index": target_idx,
                "reason": reason,
                "rolled_back_steps": [s.to_dict() for s in rolled_steps],
                "authority_effect": AUTHORITY_EFFECT_NONE,
            }
            material = canonical_json_bytes({
                k: v for k, v in rollback_payload.items() if k != "record_sha256"
            })
            digest = hashlib.sha256(material).hexdigest()
            rollback_payload["record_sha256"] = digest
            self._head_sha256 = digest
            self._next_sequence += 1
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, "a", encoding="utf-8") as fp:
                    fp.write(json.dumps(rollback_payload, ensure_ascii=False) + "\n")
            except (OSError, TypeError, ValueError) as exc:
                return Err(
                    Refusal(
                        code="DDA_PERSIST_FAILED",
                        message=f"Failed to persist DDA rollback: {exc}",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.DiscreteDeformationAlgebraDdaSink.rollback",
                    )
                )

        self._terminalized = any(s.letter == DdaLetter.T for s in self.recorded_steps)
        return Ok(tuple(rolled_steps))

    def record_compensation_branch(
        self, branch_id: str, steps: Sequence[DdaStepV1]
    ) -> Result[str, Refusal]:
        """Record an explicit compensation or refusal branch tape."""
        from ..domain.canonical import identifier
        try:
            identifier(branch_id, "branch_id")
        except (TypeError, ValueError) as exc:
            return Err(Refusal(
                code="INVALID_COMPENSATION_BRANCH",
                message=str(exc),
                locus="omega_engine_woland.stage.infrastructure.default_adapters",
            ))
        if branch_id in self.compensation_branches:
            return Err(Refusal(
                code="INVALID_COMPENSATION_BRANCH",
                message="Compensation branch ID must be nonempty, normalized and unique",
                locus="omega_engine_woland.stage.infrastructure.default_adapters",
            ))
        for s in steps:
            purity = validate_dda_purity(s)
            if purity.is_err:
                return Err(purity.unwrap_err())
        self.compensation_branches[branch_id] = list(steps)
        if self.output_file:
            branch_payload: dict[str, Any] = {
                "sequence": self._next_sequence,
                "parent_sha256": self._head_sha256,
                "record_type": "compensation_branch",
                "branch_id": branch_id,
                "steps": [s.to_dict() for s in steps],
                "authority_effect": AUTHORITY_EFFECT_NONE,
            }
            material = canonical_json_bytes({
                k: v for k, v in branch_payload.items() if k != "record_sha256"
            })
            digest = hashlib.sha256(material).hexdigest()
            branch_payload["record_sha256"] = digest
            self._head_sha256 = digest
            self._next_sequence += 1
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, "a", encoding="utf-8") as fp:
                    fp.write(json.dumps(branch_payload, ensure_ascii=False) + "\n")
            except (OSError, TypeError, ValueError) as exc:
                return Err(
                    Refusal(
                        code="DDA_PERSIST_FAILED",
                        message=f"Failed to persist compensation branch: {exc}",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.DiscreteDeformationAlgebraDdaSink.record_compensation_branch",
                    )
                )
        return Ok(branch_id)

    def as_tape(self, separator: str = " · ") -> str:
        """Format the recorded step sequence as a DDC execution tape string."""
        return separator.join(step.letter.value for step in self.recorded_steps)

    def as_branch_tapes(self, separator: str = " · ") -> dict[str, str]:
        """Format all recorded branches into DDC execution tape strings."""
        result = {"main": self.as_tape(separator=separator)}
        for b_id, steps in self.compensation_branches.items():
            result[b_id] = separator.join(s.letter.value for s in steps)
        return result



class InMemorySymbolGamePacketSink(SymbolGamePacketSink):
    """In-memory symbol-game packet projection sink."""

    def __init__(self, output_file: str | Path | None = None) -> None:
        self.output_file = Path(output_file) if output_file else None
        self.recorded_packets: list[bytes] = []

    def record_packet(self, packet_bytes: bytes) -> Result[str, Refusal]:
        self.recorded_packets.append(packet_bytes)
        if self.output_file:
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, "ab") as fp:
                    fp.write(packet_bytes + b"\n")
            except (OSError, TypeError, ValueError) as exc:
                return Err(
                    Refusal(
                        code="SGT_PERSIST_FAILED",
                        message=f"Failed to persist symbol-game packet: {exc}",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.InMemorySymbolGamePacketSink",
                    )
                )
        packet_id = hashlib.sha256(packet_bytes).hexdigest()[:16]
        return Ok(packet_id)


DiscreteDeformationCalculusDdcSink = DiscreteDeformationAlgebraDdaSink
SymbolGameSgtSink = InMemorySymbolGamePacketSink


class PermissiveContinuationAdapter(ContinuationPortV1):
    """Bounded continuation adapter for Woland stage profiles."""

    def __init__(self, max_circuits: int = 64) -> None:
        self.max_circuits = max_circuits

    def can_continue(
        self, state: SwarmRunStateV1
    ) -> Result[ContinueDecisionV1, Refusal]:
        circuit_count = state.circuit_count if hasattr(state, "circuit_count") else 0
        if circuit_count >= self.max_circuits:
            return Ok(
                ContinueDecisionV1(
                    kind=ContinueDecisionKindV1.HALT,
                    reason=f"Circuit count reached maximum allowed limit ({self.max_circuits})",
                    remaining_budget=0,
                )
            )
        return Ok(
            ContinueDecisionV1(
                kind=ContinueDecisionKindV1.CONTINUE,
                reason="Budget available",
                remaining_budget=self.max_circuits - circuit_count,
            )
        )


class TrivialValuatorAdapter(ValuatorPortV1):
    """Deterministic test adapter over caller-measured residual vectors.

    The adapter never looks at the candidate. It can only recompute the
    weighted potential from residual vectors that were measured elsewhere and
    handed to it. With no vectors it refuses: it used to invent a pre-residual
    of all ones and a post-residual of all zeros and report that invented
    improvement as ``independently_recomputed=True``.
    """

    def __init__(
        self,
        *,
        pre_residual: Sequence[int] | None = None,
        post_residual: Sequence[int] | None = None,
    ) -> None:
        self.pre_residual = tuple(pre_residual) if pre_residual is not None else None
        self.post_residual = tuple(post_residual) if post_residual is not None else None

    @property
    def independently_recomputed(self) -> bool:
        """True only when both residual vectors were measured outside the candidate."""
        return self.pre_residual is not None and self.post_residual is not None

    def evaluate(
        self, epoch: EvaluatorEpochV1, candidate: CandidateProposalV1
    ) -> Result[ValuationReceiptV1, Refusal]:
        pre = self.pre_residual
        post = self.post_residual
        if pre is None or post is None:
            return Err(
                Refusal(
                    code="VALUATION_NOT_MEASURED",
                    message=(
                        "No measured residual vectors were supplied; the trivial "
                        "valuator does not measure candidates and will not invent a valuation"
                    ),
                    locus="omega_engine_woland.stage.infrastructure.default_adapters",
                )
            )

        if len(pre) != len(epoch.weights) or len(post) != len(epoch.weights):
            return Err(
                Refusal(
                    code="VALUATION_INPUT_ARITY_MISMATCH",
                    message="Explicit residual vectors must match the evaluator epoch arity",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters",
                )
            )
        if any(type(value) is not int or value < 0 for value in pre + post):
            return Err(
                Refusal(
                    code="VALUATION_INPUT_INVALID",
                    message="Explicit residual vectors must contain non-negative integers",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters",
                )
            )

        phi_pre = sum(
            weight * value for weight, value in zip(epoch.weights, pre, strict=True)
        )
        phi_post = sum(
            weight * value for weight, value in zip(epoch.weights, post, strict=True)
        )
        delta_phi = phi_post - phi_pre
        disposition = "NON_INCREASING" if delta_phi <= 0 else "INCREASING"

        cand_id = getattr(candidate, "candidate_id", "candidate_1")
        cand_digest = (
            cand_id
            if ":" in cand_id
            else f"sha256:{hashlib.sha256(cand_id.encode('utf-8')).hexdigest()}"
        )

        return Ok(
            ValuationReceiptV1(
                evaluator_epoch_id=epoch.epoch_id,
                candidate_id=cand_digest,
                probe_ids=epoch.probe_ids,
                weights=epoch.weights,
                pre_residual=pre,
                post_residual=post,
                phi_pre=phi_pre,
                phi_post=phi_post,
                delta_phi=delta_phi,
                disposition=disposition,
                independently_recomputed=self.independently_recomputed,
                authority_effect=AUTHORITY_EFFECT_NONE,
            )
        )


class FileCemeteryAdapter(CemeterySink):
    """Lossless storage for dead findings and killed candidates under _ic/darpa/stage/cemetery/."""

    def __init__(self, cemetery_dir: str | Path | None = None) -> None:
        self.cemetery_dir = Path(cemetery_dir or canonical_intelligence_route("_intelligence/_stage/cemetery"))
        self.headstones: list[CemeteryHeadstoneV1] = []
        self._lock = threading.RLock()
        self._load_state()

    def _load_state(self) -> None:
        loaded: list[CemeteryHeadstoneV1] = []
        if self.cemetery_dir.exists():
            for filepath in sorted(self.cemetery_dir.glob("*.headstone.json")):
                try:
                    payload = strict_json_loads(filepath.read_bytes())
                    headstone = CemeteryHeadstoneV1.from_dict(payload)
                except (OSError, TypeError, ValueError) as exc:
                    raise ValueError(
                        f"CEMETERY_HEADSTONE_UNREADABLE:{filepath.name}:{exc}"
                    ) from exc
                if headstone not in loaded:
                    loaded.append(headstone)
        self.headstones = loaded

    def load_headstones(self) -> Result[tuple[CemeteryHeadstoneV1, ...], Refusal]:
        try:
            with self._lock:
                self._load_state()
                return Ok(tuple(self.headstones))
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="CEMETERY_LOAD_FAILED",
                    message=f"Failed to load cemetery headstones: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.FileCemeteryAdapter.load_headstones",
                )
            )

    def record_headstone(self, headstone: CemeteryHeadstoneV1) -> Result[None, Refusal]:
        try:
            if type(headstone) is not CemeteryHeadstoneV1:
                raise TypeError("headstone must be an exact CemeteryHeadstoneV1")
            record_digest = headstone.headstone_id.removeprefix("sha256:")
            filepath = self.cemetery_dir / f"{record_digest}.headstone.json"
            with self._lock:
                self._load_state()
                _atomic_write_json(
                    filepath,
                    headstone.to_dict(),
                    replace_existing=False,
                )
                if headstone not in self.headstones:
                    self.headstones.append(headstone)
            return Ok(None)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="CEMETERY_RECORD_FAILED",
                    message=f"Failed to record headstone: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.FileCemeteryAdapter",
                )
            )


class FileAntibodyAdapter(AntibodyStorePort):
    """Immune antibody store: loads antibodies from compost history and accumulates failures."""

    def __init__(self, antibody_dir: str | Path | None = None) -> None:
        self.antibody_dir = Path(antibody_dir or canonical_intelligence_route("_intelligence/_stage/antibodies"))
        self.failure_counts: dict[str, int] = {}
        self.antibodies: dict[str, AntibodyEntryV1] = {}
        self._records: dict[str, AntibodyEntryV1] = {}
        self._loaded = False
        self._lock = threading.RLock()

    def _load_state(self) -> None:
        if self._loaded:
            return
        if self.antibody_dir.exists():
            for path in sorted(self.antibody_dir.glob("ab_*.json")):
                wire = strict_json_loads(path.read_bytes())
                entry = AntibodyEntryV1.from_dict(wire)
                expected_name = f"{entry.antibody_id}.json"
                if path.name != expected_name:
                    raise ValueError(
                        f"antibody filename does not match payload: {path}"
                    )
                prior = self._records.get(entry.antibody_id)
                if prior is not None and prior != entry:
                    raise ValueError(
                        f"conflicting antibody identity: {entry.antibody_id}"
                    )
                self._records[entry.antibody_id] = entry
                self.failure_counts[entry.failure_pattern] = entry.occurrences
                if entry.status == "ACTIVE":
                    self.antibodies[entry.antibody_id] = entry
        self._loaded = True

    def load_antibodies(
        self, objective: str
    ) -> Result[tuple[AntibodyEntryV1, ...], Refusal]:
        try:
            if type(objective) is not str:
                raise TypeError("objective must be an exact string")
            with self._lock:
                self._load_state()
                return Ok(
                    tuple(self.antibodies[key] for key in sorted(self.antibodies))
                )
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="ANTIBODY_LOAD_FAILED",
                    message=f"Failed to load antibodies: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.FileAntibodyAdapter",
                )
            )

    def record_failure(
        self, failure_pattern: str, constraint_rule: str
    ) -> Result[AntibodyEntryV1 | None, Refusal]:
        try:
            if (
                type(failure_pattern) is not str
                or not failure_pattern
                or failure_pattern.strip() != failure_pattern
            ):
                raise ValueError("failure_pattern must be a normalized nonempty string")
            if (
                type(constraint_rule) is not str
                or not constraint_rule
                or constraint_rule.strip() != constraint_rule
            ):
                raise ValueError("constraint_rule must be a normalized nonempty string")
            with self._lock:
                self._load_state()
                ab_id = f"ab_{hashlib.sha256(failure_pattern.encode('utf-8')).hexdigest()[:16]}"
                prior = self._records.get(ab_id)
                if prior is not None and (
                    prior.failure_pattern != failure_pattern
                    or prior.constraint_rule != constraint_rule
                ):
                    raise ValueError(
                        "antibody identity collides with different failure data"
                    )
                count = 1 if prior is None else prior.occurrences + 1
                # A sighting count never activates an antibody: activation is an
                # admission act recorded outside this store. A judged record (ACTIVE,
                # or any status other than PENDING) keeps its status when seen again.
                status = (
                    prior.status if prior is not None and prior.status != "PENDING" else "PENDING"
                )
                entry = AntibodyEntryV1(
                    antibody_id=ab_id,
                    failure_pattern=failure_pattern,
                    occurrences=count,
                    constraint_rule=constraint_rule,
                    status=status,
                )
                _atomic_write_json(
                    self.antibody_dir / f"{ab_id}.json",
                    entry.to_dict(),
                    replace_existing=True,
                )
                self._records[ab_id] = entry
                self.failure_counts[failure_pattern] = count
                if entry.status == "ACTIVE":
                    self.antibodies[ab_id] = entry
                    return Ok(entry)
                return Ok(None)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="ANTIBODY_RECORD_FAILED",
                    message=f"Failed to record failure pattern: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.FileAntibodyAdapter",
                )
            )


class FixtureAgentTurnAdapter(SeatPortV1):
    """Deterministic fixture-based seat turn adapter for unit tests and CI."""

    def __init__(
        self,
        canned_replies: dict[tuple[str, str], SeatTurnReplyV1] | None = None,
        default_reply: SeatTurnReplyV1 | None = None,
    ) -> None:
        self.canned_replies = canned_replies or {}
        self.default_reply = default_reply or SeatTurnReplyV1(
            reply_text="```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Open\nDISPOSITION=PASS\n```\nDeterministic fixture turn completed.",
            machine_fields={
                "AUTHORITY_EFFECT": "None",
                "RESIDUAL_COLOUR": "Open",
                "DISPOSITION": "PASS",
            },
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"deterministic_fixture",
        )
        self.invocation_log: list[SeatTurnRequestV1] = []

    def execute_turn(
        self, request: SeatTurnRequestV1
    ) -> Result[SeatTurnReplyV1, Refusal]:
        self.invocation_log.append(request)
        key = (request.scene_id, request.seat_id)
        reply = self.canned_replies.get(key, self.default_reply)
        if reply.request_digest is None:
            # Binding a canned reply to the request it answered is a fact about
            # this call, not a claim about any model; model and usage stay None.
            reply = replace(reply, request_digest=request.request_digest())
        return Ok(reply)


class AntigravityAgentTurnAdapter(SeatPortV1):
    """Agent-turn adapter executing turns through an injected executor.

    The executor may return the raw reply text, or a ``SeatTurnReplyV1`` when
    it can also report model, provider, parameters and usage. Either way the
    reply is bound to the digest of the request it answers.
    """

    def __init__(
        self,
        turn_executor: Callable[[SeatTurnRequestV1], str | SeatTurnReplyV1]
        | None = None,
    ) -> None:
        self.turn_executor = turn_executor

    def execute_turn(
        self, request: SeatTurnRequestV1
    ) -> Result[SeatTurnReplyV1, Refusal]:
        if self.turn_executor is None:
            return Err(
                Refusal(
                    code="AGENT_TURN_EXECUTOR_MISSING",
                    message="No turn executor was configured; no agent turn ran.",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.AntigravityAgentTurnAdapter",
                )
            )
        try:
            executed = self.turn_executor(request)
            request_digest = request.request_digest()
            if type(executed) is SeatTurnReplyV1:
                return self._bind_structured_reply(executed, request_digest)
            if type(executed) is not str:
                return Err(
                    Refusal(
                        code="AGENT_TURN_FAILED",
                        message="Turn executor must return reply text or a SeatTurnReplyV1",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.AntigravityAgentTurnAdapter",
                    )
                )
            raw_text = executed

            match = re.search(r"```machine\s*\n(.*?)```", raw_text, re.DOTALL)
            fields: dict[str, str] = {}
            if match:
                for line in match.group(1).strip().split("\n"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        fields[k.strip()] = v.strip()

            auth = fields.get("AUTHORITY_EFFECT", "None")
            if auth != "None":
                return Err(
                    Refusal(
                        code="REFUSAL_AUTHORITY_NON_NONE",
                        message=f"Model reply minted non-None authority: '{auth}'",
                        locus="omega_engine_woland.stage.infrastructure.default_adapters.AntigravityAgentTurnAdapter",
                    )
                )

            res_colour = fields.get("RESIDUAL_COLOUR", "Open")

            reply = SeatTurnReplyV1(
                reply_text=raw_text,
                machine_fields=fields,
                residual_colour=res_colour,
                authority_effect=auth,
                raw_bytes=raw_text.encode("utf-8"),
                request_digest=request_digest,
            )
            return Ok(reply)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="AGENT_TURN_FAILED",
                    message=f"Failed to execute seat turn: {exc}",
                    locus="omega_engine_woland.stage.infrastructure.default_adapters.AntigravityAgentTurnAdapter",
                )
            )

    @staticmethod
    def _bind_structured_reply(
        reply: SeatTurnReplyV1, request_digest: str
    ) -> Result[SeatTurnReplyV1, Refusal]:
        locus = "omega_engine_woland.stage.infrastructure.default_adapters.AntigravityAgentTurnAdapter"
        declared = reply.machine_fields.get("AUTHORITY_EFFECT", "None")
        if reply.authority_effect != "None" or declared != "None":
            return Err(
                Refusal(
                    code="REFUSAL_AUTHORITY_NON_NONE",
                    message="Model reply minted non-None authority",
                    locus=locus,
                )
            )
        if reply.request_digest is not None and reply.request_digest != request_digest:
            return Err(
                Refusal(
                    code="AGENT_TURN_REQUEST_DIGEST_MISMATCH",
                    message="The reply names a different request than the one executed",
                    locus=locus,
                )
            )
        return Ok(replace(reply, request_digest=request_digest))


class OearsApiTurnAdapter(SeatPortV1):
    """Scaffold for live API transport (OpenRouter / Gemini API) — disabled by default in Sprint 2."""

    def __init__(self, api_key: str = "", endpoint_url: str = "") -> None:
        self.api_key = api_key
        self.endpoint_url = endpoint_url

    def execute_turn(
        self, request: SeatTurnRequestV1
    ) -> Result[SeatTurnReplyV1, Refusal]:
        return Err(
            Refusal(
                code="API_TRANSPORT_DISABLED",
                message="Live API transport is scheduled for Sprint 3+. Use AntigravityAgentTurnAdapter.",
                locus="omega_engine_woland.stage.infrastructure.default_adapters.OearsApiTurnAdapter",
            )
        )


__all__ = [
    "AntigravityAgentTurnAdapter",
    "DiscreteDeformationAlgebraDdaSink",
    "DiscreteDeformationCalculusDdcSink",
    "FileAntibodyAdapter",
    "FileCemeteryAdapter",
    "FixtureAgentTurnAdapter",
    "InMemorySymbolGamePacketSink",
    "OearsApiTurnAdapter",
    "PermissiveContinuationAdapter",
    "SymbolGameSgtSink",
    "TrivialValuatorAdapter",
    "UniversalNarrativeUnsSink",
    "UniversalTraceUtsSink",
]
