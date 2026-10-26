"""Woland Seven-Act Circuit, gate receipts, and reality gate verification.

Enforces:
- F-WOLAND-01: Act VII authorization diagnostic containment (AuthorityEffect: None).
- F-WOLAND-02: Preflight refusal terminates with gate_status=NOT_RUN.
- F-RES-01: Judge stability under order swap (JUDGE_ORDER_UNSTABLE).
- F-RES-02: Gate is deterministic host logic (novella renderer removal leaves host records byte-identical).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from omega_engine_woland.stage.domain.topology import (
    SwarmCompositionV1,
    validate_swarm_composition,
)

from .evidence import canonical_rational, is_sha256_ref, parse_exact_rational
from .specialization import WOLAND_BASE_SPECIALIZATION_V1

JOINT_KERNEL_STATUSES = frozenset({"NOT_MEASURED", "OPEN_RESIDUAL", "ZERO_ON_DECLARED_CARRIER"})


def validate_algorithm_metadata(
    ddc_trace_hash: str | None,
    lggr_joint_kernel_status: str,
    phi1: str | None,
    gamma2: str | None,
    carrier_degree: int | None,
) -> None:
    """Validate scoped evidence metadata; zero is never an LGGR cover theorem."""
    if ddc_trace_hash is not None and not is_sha256_ref(ddc_trace_hash):
        raise ValueError("ddc_trace_hash must be a sha256 reference or None")
    if (
        type(lggr_joint_kernel_status) is not str
        or lggr_joint_kernel_status not in JOINT_KERNEL_STATUSES
    ):
        raise ValueError("unknown lggr_joint_kernel_status")
    if carrier_degree is not None and (type(carrier_degree) is not int or carrier_degree < 0):
        raise ValueError("carrier_degree must be a nonnegative exact integer or None")
    for value in (phi1, gamma2):
        if value is not None and (
            type(value) is not str
            or canonical_rational(parse_exact_rational(value)) != value
            or parse_exact_rational(value) < 0
        ):
            raise ValueError("CODA measurements must be nonnegative canonical rational strings")
    if (phi1 is None) != (gamma2 is None):
        raise ValueError("CODA measurements must be supplied together")
    measured = phi1 is not None
    if (lggr_joint_kernel_status != "NOT_MEASURED") != measured:
        raise ValueError("joint-kernel metadata requires measured CODA values")
    if measured and carrier_degree != 1:
        raise ValueError("measured Woland CODA values require declared cochain degree one")
    if measured and (
        (phi1 == "0" and gamma2 == "0") != (lggr_joint_kernel_status == "ZERO_ON_DECLARED_CARRIER")
    ):
        raise ValueError("joint-kernel status disagrees with exact CODA values")


#: The base composition is the base specialisation's; it is not declared twice.
WOLAND_SWARM_COMPOSITION_V1 = WOLAND_BASE_SPECIALIZATION_V1.composition


def validate_woland_swarm_composition(composition: SwarmCompositionV1) -> bool:
    """Check Woland's declared spine before composing any runtime adapters."""
    if type(composition) is not SwarmCompositionV1:
        raise TypeError("composition must be exact SwarmCompositionV1")
    if type(composition.swarm_ancestry) not in (list, tuple) or (
        "omega.woland.swarm.v1" not in composition.swarm_ancestry
    ):
        raise ValueError("WOLAND_INHERITANCE_REQUIRED: Woland ancestry must be declared")
    if type(composition.required_skills) not in (list, tuple) or (
        "/woland" not in composition.required_skills
    ):
        raise ValueError("WOLAND_SKILL_REQUIRED: /woland must be required")
    if composition.llm_protocol != "omega.symbol_game.protocol.v2":
        raise ValueError("SYMBOL_GAME_PROTOCOL_REQUIRED: Symbol Game v2 is required")
    if composition.authority_effect != "None":
        raise ValueError("AUTHORITY_EFFECT_FORBIDDEN: composition grants no authority")
    return validate_swarm_composition(composition)


@dataclass(frozen=True, slots=True)
class WolandGateReceiptV1:
    run_id: str
    profile_digest: str
    input_packet_digest: str
    output_packet_digest: str
    gate_status: str
    refusal_code: str | None = None
    is_completed_gated_run: bool = True
    open_residuals: list[str] = field(default_factory=list)
    authority_effect: str = "None"
    ddc_trace_hash: str | None = None
    lggr_joint_kernel_status: str = "NOT_MEASURED"
    coda_potential_phi1: str | None = None
    coda_closure_gamma2: str | None = None
    carrier_degree: int | None = None

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("Woland gate receipts grant no authority")
        if type(self.is_completed_gated_run) is not bool:
            raise TypeError("is_completed_gated_run must be an exact bool")
        validate_algorithm_metadata(
            self.ddc_trace_hash,
            self.lggr_joint_kernel_status,
            self.coda_potential_phi1,
            self.coda_closure_gamma2,
            self.carrier_degree,
        )
        if (
            self.gate_status == "AUTHORIZED"
            and self.coda_potential_phi1 is not None
            and (self.coda_potential_phi1 != "0" or self.coda_closure_gamma2 != "0")
        ):
            raise ValueError("AUTHORIZED measured carrier must have exact joint zero")
        if self.gate_status == "NOT_RUN" and (
            self.is_completed_gated_run
            or self.ddc_trace_hash is not None
            or self.carrier_degree is not None
            or self.coda_potential_phi1 is not None
        ):
            raise ValueError("NOT_RUN cannot claim completed execution or algorithm measurements")


@dataclass(frozen=True, slots=True)
class WolandSevenActCircuit:
    fail_preflight: bool = False
    refusal_code: str = ""
    run_id: str = "run-default"
    input_packet: Any = None
    profile: Any = None
    acts_runner: Any = None

    def create_not_run_receipt(
        self, refusal_code: str = "PREFLIGHT_REFUSED"
    ) -> WolandGateReceiptV1:
        return WolandGateReceiptV1(
            run_id=self.run_id,
            profile_digest="",
            input_packet_digest="",
            output_packet_digest="",
            gate_status="NOT_RUN",
            refusal_code=refusal_code,
            is_completed_gated_run=False,
            open_residuals=[],
            authority_effect="None",
        )

    def execute(self) -> WolandGateReceiptV1:
        if self.fail_preflight or self.input_packet is None:
            return self.create_not_run_receipt(
                self.refusal_code
                or ("PREFLIGHT_REFUSED" if self.fail_preflight else "UNCONFIGURED_CIRCUIT")
            )
        if not callable(self.acts_runner):
            return self.create_not_run_receipt("ACTS_RUNNER_REQUIRED")
        return self.acts_runner(self.input_packet, self.profile, self.run_id)


@dataclass(frozen=True, slots=True)
class JudgeVerdictV1:
    winner: str
    first_proposal: str
    second_proposal: str


class DebateJudgePairV1:
    def evaluate(self, first: str, second: str) -> JudgeVerdictV1:
        # Position-biased mock: picks whichever option was presented first
        winner = "A" if "Argument A" in first else "B"
        return JudgeVerdictV1(
            winner=winner,
            first_proposal=first,
            second_proposal=second,
        )


@dataclass(frozen=True, slots=True)
class OrderInvarianceResultV1:
    stable: bool
    diagnostic_code: str | None = None


class OrderSensitivityDetectorV1:
    def verify_order_invariance(
        self,
        forward_verdict: JudgeVerdictV1,
        swapped_verdict: JudgeVerdictV1,
    ) -> OrderInvarianceResultV1:
        # If the preferred winner changes when positions swap, the judge is order-sensitive
        if forward_verdict.winner != swapped_verdict.winner:
            return OrderInvarianceResultV1(
                stable=False,
                diagnostic_code="JUDGE_ORDER_UNSTABLE",
            )
        return OrderInvarianceResultV1(stable=True)


@dataclass(frozen=True, slots=True)
class HostExecutionRecordBundleV1:
    gate_receipt_digest: str
    host_records_digest: str


class WolandExecutionEngineV1:
    def execute_run(
        self,
        run_context: dict[str, Any],
        enable_novella_renderer: bool = True,
    ) -> HostExecutionRecordBundleV1:
        # Deterministic host logic hashes
        canonical_context = json.dumps(run_context, sort_keys=True).encode("utf-8")
        gate_digest = hashlib.sha256(b"gate_receipt:" + canonical_context).hexdigest()
        host_digest = hashlib.sha256(b"host_records:" + canonical_context).hexdigest()

        # Novella renderer is presentation-only and has zero authority effect on host digests
        if enable_novella_renderer:
            _novella_text = f"# Novella\nDeterministic story for {run_context}"

        return HostExecutionRecordBundleV1(
            gate_receipt_digest=gate_digest,
            host_records_digest=host_digest,
        )


__all__ = [
    "DebateJudgePairV1",
    "HostExecutionRecordBundleV1",
    "JudgeVerdictV1",
    "OrderInvarianceResultV1",
    "OrderSensitivityDetectorV1",
    "SwarmCompositionV1",
    "WOLAND_SWARM_COMPOSITION_V1",
    "WolandExecutionEngineV1",
    "WolandGateReceiptV1",
    "WolandSevenActCircuit",
    "validate_woland_swarm_composition",
]
