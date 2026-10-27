"""Intelligence Spine emission layer: one event source, four typed sinks.

Integrates directly with canonical linear_algebra_theory/density.py and
engine/eng_qm_quantum_density.py for Quantum Density Matrix (SBE) metrics.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    canonical_json_bytes,
    identifier,
    text,
)
from ..domain.ddc import (
    DdaStepV1,
    DdcStepV1,
    validate_dda_purity,
)
from ..domain.genealogy import AntibodyEntryV1, CemeteryHeadstoneV1, GenealogyEntryV1


@dataclass(frozen=True)
class IntelligenceEventV1:
    """Canonical Intelligence Event (IE) under Intelligence Spine doctrine."""

    ie_id: str
    ts_utc: str
    actor_id: str
    actor_kind: str
    event_kind: str
    source_system: str
    payload_uri: str
    payload_sha256: str
    session_id: str
    parent_ie_id: tuple[str, ...] = ()
    object_ids: tuple[str, ...] = ()
    terminal: bool = False
    authority_effect: str = AUTHORITY_EFFECT_NONE
    privacy_class: str = "PUBLIC"

    def __post_init__(self) -> None:
        object.__setattr__(self, "ie_id", identifier(self.ie_id, "ie_id"))
        object.__setattr__(self, "ts_utc", text(self.ts_utc, "ts_utc"))
        object.__setattr__(self, "actor_id", identifier(self.actor_id, "actor_id"))
        object.__setattr__(
            self, "actor_kind", identifier(self.actor_kind, "actor_kind")
        )
        object.__setattr__(
            self, "event_kind", identifier(self.event_kind, "event_kind")
        )
        object.__setattr__(
            self, "source_system", identifier(self.source_system, "source_system")
        )
        object.__setattr__(
            self, "payload_uri", text(self.payload_uri, "payload_uri", allow_empty=True)
        )
        object.__setattr__(
            self, "payload_sha256", text(self.payload_sha256, "payload_sha256")
        )
        object.__setattr__(
            self, "session_id", identifier(self.session_id, "session_id")
        )
        object.__setattr__(
            self,
            "parent_ie_id",
            tuple(identifier(p, "parent_ie_id") for p in self.parent_ie_id),
        )
        object.__setattr__(
            self, "object_ids", tuple(text(o, "object_ids") for o in self.object_ids)
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError(f"authority_effect must be '{AUTHORITY_EFFECT_NONE}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ie_id": self.ie_id,
            "ts_utc": self.ts_utc,
            "actor_id": self.actor_id,
            "actor_kind": self.actor_kind,
            "event_kind": self.event_kind,
            "source_system": self.source_system,
            "payload_uri": self.payload_uri,
            "payload_sha256": self.payload_sha256,
            "session_id": self.session_id,
            "parent_ie_id": list(self.parent_ie_id),
            "object_ids": list(self.object_ids),
            "terminal": self.terminal,
            "authority_effect": self.authority_effect,
            "privacy_class": self.privacy_class,
        }


@runtime_checkable
class UtsSink(Protocol):
    """Universal Trace Stream (UTS): per-event superset source of truth."""

    def record_event(
        self, event: IntelligenceEventV1, payload: bytes | str
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class DdcSink(Protocol):
    """Discrete Deformation Calculus (DDC) sink: strict-purity actions only."""

    def record_step(self, step: DdcStepV1 | DdaStepV1) -> Result[str, Refusal]: ...


DdaSink = DdcSink


@runtime_checkable
class UnsSink(Protocol):
    """Universal Narrative Stream (UNS): derived novella for humans."""

    def record_narrative(
        self, session_id: str, turn_md: str
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class SgtSink(Protocol):
    """Symbol Game Trace (SGT) sink: typed turn packets."""

    def record_turn(
        self, session_id: str, turn_payload: dict[str, Any]
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class CemeterySink(Protocol):
    """Cemetery sink: records killed candidates with cryptographic headstones."""

    def record_headstone(
        self, headstone: CemeteryHeadstoneV1
    ) -> Result[str, Refusal]: ...


@runtime_checkable
class AntibodySink(Protocol):
    """Antibody sink: mines failure patterns into active immune constraints."""

    def record_failure(
        self, failure_pattern: str, constraint_rule: str
    ) -> Result[str, Refusal]: ...

    def load_antibodies(
        self, context_key: str
    ) -> Result[tuple[AntibodyEntryV1, ...], Refusal]: ...


@runtime_checkable
class GenealogySink(Protocol):
    """Genealogy sink: records parent-child lineage DAG for compost re-entry."""

    def record_lineage(self, entry: GenealogyEntryV1) -> Result[str, Refusal]: ...


@dataclass(frozen=True)
class EmitterSuiteV1:
    """Four-stream typed sink suite with Cemetery, Antibody, and Lineage extensions."""

    uts: UtsSink | None = None
    dda: DdaSink | None = None
    uns: UnsSink | None = None
    sgt: SgtSink | None = None
    cemetery: CemeterySink | None = None
    antibodies: AntibodySink | None = None
    genealogy: GenealogySink | None = None
    ddc: DdaSink | None = None

    def __post_init__(self) -> None:
        if self.ddc is not None and self.dda is None:
            object.__setattr__(self, "dda", self.ddc)
        elif self.dda is not None and self.ddc is None:
            object.__setattr__(self, "ddc", self.dda)


# The synthetic diagnostic materializes dense matrices and computes their
# spectrum. Keep its public allocation budget bounded for HTTP and direct use.
MAX_SBE_DIMENSION = 128


def compute_sbe_metrics(text: str, dim: int = 28) -> dict[str, Any]:
    """Compute a deterministic synthetic SBE diagnostic, never a verification receipt."""
    import numpy as np

    from ..domain.quantum import (
        DensityMatrixConfig,
        NumericalDensityMatrix,
        QuantumDensityEngine,
    )

    try:
        if type(dim) is not int or not 1 <= dim <= MAX_SBE_DIMENSION:
            raise ValueError("SBE dimension must be an integer in the admitted range")
        text_bytes = text.encode("utf-8")
        prompt_hash = hashlib.sha256(text_bytes).hexdigest()
        seed = int(prompt_hash[:8], 16)
        rng = np.random.default_rng(seed)

        num_states = max(4, dim // 7)
        states = []
        for k in range(num_states):
            vec = rng.standard_normal(dim)
            char_factor = (len(text) + sum(text_bytes[:: k + 1])) % 100 / 100.0
            vec += char_factor * rng.standard_normal(dim)
            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vec = vec / norm
            states.append(vec.tolist())

        dm = QuantumDensityEngine.from_states(states)
        if dm is None:
            dm = NumericalDensityMatrix.from_diagonal_probs(
                [1.0 / dim] * dim, DensityMatrixConfig.default()
            )

        purity = float(dm.purity())
        entropy_bits = float(dm.entropy_bits())
        l1_coherence = float(dm.l1_coherence())
        evals = dm.approximate_eigenvalues()
        nonzero_evals = sum(1 for v in evals if v > 1e-5)

        return {
            "measurement_status": "DETERMINISTIC_SYNTHETIC_DIAGNOSTIC",
            "total_eigenvalues": dim,
            "nonzero_eigenvalues": f"{nonzero_evals} entries",
            "purity": f"{purity:.6f}",
            "entropy_bits": f"{entropy_bits:.6f}",
            "l1_coherence": f"{l1_coherence:.6f}",
        }
    except (
        ArithmeticError,
        np.linalg.LinAlgError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        return {
            "measurement_status": "UNAVAILABLE",
            "measurement_error": type(exc).__name__,
            "total_eigenvalues": dim,
            "nonzero_eigenvalues": "UNAVAILABLE",
            "purity": "UNAVAILABLE",
            "entropy_bits": "UNAVAILABLE",
            "l1_coherence": "UNAVAILABLE",
        }


def build_intelligence_event(
    ie_id: str,
    actor_id: str,
    actor_kind: str,
    event_kind: str,
    source_system: str,
    session_id: str,
    payload: Any,
    parent_ie_id: tuple[str, ...] = (),
    object_ids: tuple[str, ...] = (),
    terminal: bool = False,
) -> tuple[IntelligenceEventV1, bytes]:
    """Helper to build an IntelligenceEventV1 and its canonical JSON bytes."""
    if isinstance(payload, bytes):
        payload_bytes = payload
    elif isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    elif isinstance(payload, dict):
        payload_bytes = canonical_json_bytes(payload)
    else:
        payload_bytes = str(payload).encode("utf-8")

    payload_sha256 = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()
    ts_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    event = IntelligenceEventV1(
        ie_id=ie_id,
        ts_utc=ts_utc,
        actor_id=actor_id,
        actor_kind=actor_kind,
        event_kind=event_kind,
        source_system=source_system,
        payload_uri=f"memory://{session_id}/{ie_id}",
        payload_sha256=payload_sha256,
        session_id=session_id,
        parent_ie_id=parent_ie_id,
        object_ids=object_ids,
        terminal=terminal,
        authority_effect=AUTHORITY_EFFECT_NONE,
        privacy_class="PUBLIC",
    )
    return event, payload_bytes


def emit_event(
    event: IntelligenceEventV1,
    payload: bytes | str,
    emitters: EmitterSuiteV1,
    *,
    dda_step: DdaStepV1 | None = None,
    sgt_payload: dict[str, Any] | None = None,
) -> Result[str, Refusal]:
    """Emit an intelligence event across all active typed sinks."""
    # Strict fail-closed DDA validation before UTS
    if event.event_kind == "DDA" and emitters.dda:
        if dda_step is None:
            return Err(
                Refusal(
                    code="DDA_IMPURE_RECORD",
                    message="Event of kind DDA requires dda_step parameter",
                    locus="adversary.stage.application.emission.emit_event",
                )
            )
        purity_check = validate_dda_purity(dda_step)
        if purity_check.is_err:
            return Err(purity_check.unwrap_err())

    if emitters.uts:
        uts_res = emitters.uts.record_event(event, payload)
        if uts_res.is_err:
            return Err(uts_res.unwrap_err())

    if dda_step and emitters.dda:
        dda_res = emitters.dda.record_step(dda_step)
        if dda_res.is_err:
            return Err(dda_res.unwrap_err())

    if emitters.sgt and (sgt_payload or event.event_kind == "PACKET"):
        try:
            if isinstance(payload, bytes):
                packet_bytes = payload
            elif isinstance(payload, str):
                packet_bytes = payload.encode("utf-8")
            elif isinstance(payload, dict):
                packet_bytes = canonical_json_bytes(payload)
            else:
                packet_bytes = str(payload).encode("utf-8")

            if hasattr(emitters.sgt, "record_packet"):
                sgt_res = emitters.sgt.record_packet(packet_bytes)
            elif hasattr(emitters.sgt, "record_turn"):
                p_dict = sgt_payload or (
                    json.loads(packet_bytes.decode("utf-8"))
                    if packet_bytes.startswith(b"{")
                    else {"raw": packet_bytes.decode("utf-8")}
                )
                sgt_res = emitters.sgt.record_turn(event.session_id, p_dict)
            else:
                sgt_res = Ok("sgt_ok")

            if sgt_res and sgt_res.is_err:
                return Err(sgt_res.unwrap_err())
        except (
            AttributeError,
            OSError,
            RuntimeError,
            TypeError,
            UnicodeDecodeError,
            ValueError,
        ) as exc:
            return Err(
                Refusal(
                    code="SGT_EMISSION_FAILED",
                    message=str(exc),
                    locus="adversary.stage.application.emission.emit_event",
                )
            )

    if event.event_kind == "NARRATIVE" and emitters.uns:
        turn_text = (
            payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
        )
        uns_res = emitters.uns.record_narrative(event.session_id, turn_text)
        if uns_res.is_err:
            return Err(uns_res.unwrap_err())

    return Ok(event.ie_id)


# Type Aliases for Backward Compatibility
SymbolGamePacketSink = SgtSink
IntelligenceEvent = IntelligenceEventV1

__all__ = [
    "AntibodySink",
    "CemeterySink",
    "DdaSink",
    "DdcSink",
    "EmitterSuiteV1",
    "GenealogySink",
    "IntelligenceEvent",
    "IntelligenceEventV1",
    "SgtSink",
    "SymbolGamePacketSink",
    "UnsSink",
    "UtsSink",
    "build_intelligence_event",
    "compute_sbe_metrics",
    "emit_event",
]
