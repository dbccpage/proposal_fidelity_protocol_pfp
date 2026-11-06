"""
mod_authority_gap_core.py

Packet-shape demonstration and structural consistency reference schema for the
Seven-Layer AI Authority Control Stack, Negative Gluing Defect (NGD),
Authority Coverage Ratio (ACR), and Exactness Fraud Criterion for finite authority systems.

Note on Authority Semantics:
This module demonstrates packet structure, length-delimited byte encodings, and
internal invariant consistency. Passing checks in this reference module establishes
only that a packet is structurally consistent under its declared observer; it does not
constitute independent evidence verification, cryptographic provenance attestation,
or institutional certification. Verified descent remains reserved for external,
independently held receipts and execution verifiers.

Author: Jeremy H. Carroll
License: Apache-2.0
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, List, Optional, Sequence, Tuple


class TerminalStatus(str, Enum):
    """Permitted terminal statuses under a declared observer."""
    PROPOSAL_ONLY = "proposal_only"
    REPAIR = "repair"
    REFUSE = "refuse"
    ESCALATE = "escalate"
    AUTHORIZED_UNDER_OBSERVER = "authorized_under_observer"


def canonical_encode_string(s: str) -> bytes:
    """Length-delimited byte encoding for a single string: <len>:<utf8_bytes>."""
    raw = s.encode("utf-8")
    return f"{len(raw)}:".encode("ascii") + raw


def canonical_encode_sequence(tag: str, items: Sequence[str]) -> bytes:
    """Length-delimited byte encoding for a sequence of strings: <tag>[<count>]:<item1><item2>...;."""
    prefix = f"{tag}[{len(items)}]:".encode("ascii")
    return prefix + b"".join(canonical_encode_string(item) for item in items) + b";"


@dataclass(frozen=True)
class Proposal:
    """Layer 1: Generated option, plan, or candidate output. Carries zero authority."""
    proposal_id: str
    generator_id: str
    payload: str
    context: str = ""


@dataclass(frozen=True)
class TraceRecord:
    """Layer 2: Tamper-evident custody record of actions, sources, and tool calls."""
    trace_id: str
    actions: Tuple[str, ...]
    tool_calls: Tuple[str, ...]
    sources: Tuple[str, ...]
    content_hash: str
    proposal_id: str = ""

    @classmethod
    def canonical_bytes(
        cls,
        trace_id: str,
        actions: Sequence[str],
        tool_calls: Sequence[str],
        sources: Sequence[str],
        proposal_id: str = "",
        proposal_payload: str = "",
        proposal_context: str = "",
    ) -> bytes:
        """Length-delimited byte serialization binding trace fields and proposal."""
        return b"".join([
            b"trace_record_v1;",
            canonical_encode_string(trace_id),
            b";",
            canonical_encode_string(proposal_id),
            b";",
            canonical_encode_string(proposal_payload),
            b";",
            canonical_encode_string(proposal_context),
            b";",
            canonical_encode_sequence("actions", actions),
            canonical_encode_sequence("tool_calls", tool_calls),
            canonical_encode_sequence("sources", sources),
        ])

    @classmethod
    def compute_hash(
        cls,
        trace_id: str,
        actions: Sequence[str],
        tool_calls: Sequence[str],
        sources: Sequence[str],
        proposal_id: str = "",
        proposal_payload: str = "",
        proposal_context: str = "",
    ) -> str:
        h = hashlib.sha256()
        h.update(cls.canonical_bytes(trace_id, actions, tool_calls, sources, proposal_id, proposal_payload, proposal_context))
        return h.hexdigest()

    @classmethod
    def create(
        cls,
        trace_id: str,
        actions: List[str],
        tool_calls: List[str],
        sources: List[str],
        proposal: Optional[Proposal | str] = None,
    ) -> TraceRecord:
        prop_id = ""
        prop_payload = ""
        prop_context = ""
        if isinstance(proposal, Proposal):
            prop_id = proposal.proposal_id
            prop_payload = proposal.payload
            prop_context = proposal.context
        elif isinstance(proposal, str) and proposal:
            prop_payload = proposal

        content_hash = cls.compute_hash(
            trace_id=trace_id,
            actions=actions,
            tool_calls=tool_calls,
            sources=sources,
            proposal_id=prop_id,
            proposal_payload=prop_payload,
            proposal_context=prop_context,
        )
        return cls(
            trace_id=trace_id,
            actions=tuple(actions),
            tool_calls=tuple(tool_calls),
            sources=tuple(sources),
            content_hash=content_hash,
            proposal_id=prop_id,
        )

    def verify_content_hash(self, proposal: Optional[Proposal | str] = None) -> bool:
        """Verify that the stored content_hash matches the length-delimited record."""
        prop_id = self.proposal_id
        prop_payload = ""
        prop_context = ""
        if isinstance(proposal, Proposal):
            if prop_id and prop_id != proposal.proposal_id:
                return False
            prop_id = proposal.proposal_id
            prop_payload = proposal.payload
            prop_context = proposal.context
        elif isinstance(proposal, str):
            prop_payload = proposal

        expected = self.compute_hash(
            trace_id=self.trace_id,
            actions=self.actions,
            tool_calls=self.tool_calls,
            sources=self.sources,
            proposal_id=prop_id,
            proposal_payload=prop_payload,
            proposal_context=prop_context,
        )
        return self.content_hash == expected


@dataclass(frozen=True)
class ObserverPacket:
    """Layer 3: Declared finite evaluation specification."""
    carrier: str
    local_states: Tuple[str, ...]
    comparisons: Tuple[str, ...]
    defects: Tuple[str, ...]
    admissible_repairs: Tuple[str, ...]
    gauge: str
    closure_diagnostics: Tuple[str, ...]


@dataclass(frozen=True)
class Residual:
    """Layer 4: Explicit ledger of unresolved defects, unverified scope, and losses."""
    defect_mass: Fraction
    unverified_scope: Tuple[str, ...]
    refusal_reasons: Tuple[str, ...]

    @property
    def is_exact(self) -> bool:
        return (
            self.defect_mass == Fraction(0, 1)
            and len(self.unverified_scope) == 0
            and len(self.refusal_reasons) == 0
        )


@dataclass(frozen=True)
class Terminal:
    """Layer 5: Accountable decision made by a designated institutional decider."""
    status: TerminalStatus
    decider_id: str
    is_human_or_delegated_body: bool
    justification: str
    claims_exactness: bool = True
    tolerated_defect_mass: Fraction = Fraction(0, 1)
    tolerated_unverified_scope: Tuple[str, ...] = ()
    tolerated_refusal_reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Attestation:
    """Layer 6: Proof that declared descent was executed across layers 1-5."""
    descent_executed: bool
    verification_hash: str
    replay_receipt: Optional[str] = None


@dataclass(frozen=True)
class Institution:
    """Layer 7: Legal, organizational, and regulatory standing."""
    entity_id: str
    governing_jurisdiction: str
    accountable_officer: str
    appeal_path: str


@dataclass(frozen=True)
class AuthorityPacket:
    """Encapsulation of the complete seven-layer authority descent pipeline."""
    proposal: Proposal
    trace: TraceRecord
    observer: ObserverPacket
    residual: Residual
    terminal: Terminal
    attestation: Attestation
    institution: Institution

    def compute_canonical_binding_record(self) -> bytes:
        """Construct a canonical, length-delimited byte record binding all seven layers."""
        chunks = [
            b"authority_packet_binding_v1;",
            # Layer 1: Proposal
            canonical_encode_string(self.proposal.proposal_id),
            canonical_encode_string(self.proposal.generator_id),
            canonical_encode_string(self.proposal.payload),
            canonical_encode_string(self.proposal.context),
            # Layer 2: Trace
            canonical_encode_string(self.trace.trace_id),
            canonical_encode_sequence("actions", self.trace.actions),
            canonical_encode_sequence("tool_calls", self.trace.tool_calls),
            canonical_encode_sequence("sources", self.trace.sources),
            canonical_encode_string(self.trace.content_hash),
            # Layer 3: Observer (Evaluator specification)
            canonical_encode_string(self.observer.carrier),
            canonical_encode_string(self.observer.gauge),
            canonical_encode_sequence("local_states", self.observer.local_states),
            canonical_encode_sequence("comparisons", self.observer.comparisons),
            canonical_encode_sequence("defects", self.observer.defects),
            canonical_encode_sequence("admissible_repairs", self.observer.admissible_repairs),
            canonical_encode_sequence("closure_diagnostics", self.observer.closure_diagnostics),
            # Layer 4: Residual
            canonical_encode_string(str(self.residual.defect_mass)),
            canonical_encode_sequence("unverified_scope", self.residual.unverified_scope),
            canonical_encode_sequence("refusal_reasons", self.residual.refusal_reasons),
            # Layer 5: Terminal (Decision)
            canonical_encode_string(self.terminal.status.value),
            canonical_encode_string(self.terminal.decider_id),
            canonical_encode_string("human" if self.terminal.is_human_or_delegated_body else "model"),
            canonical_encode_string(self.terminal.justification),
            canonical_encode_string("exact_claim" if self.terminal.claims_exactness else "scoped_authorization"),
            canonical_encode_string(str(self.terminal.tolerated_defect_mass)),
            canonical_encode_sequence("tolerated_unverified_scope", self.terminal.tolerated_unverified_scope),
            canonical_encode_sequence("tolerated_refusal_reasons", self.terminal.tolerated_refusal_reasons),
            # Layer 6: Attestation (Evidence metadata)
            canonical_encode_string("descent_executed" if self.attestation.descent_executed else "descent_not_executed"),
            canonical_encode_string(self.attestation.replay_receipt or ""),
            # Layer 7: Institution
            canonical_encode_string(self.institution.entity_id),
            canonical_encode_string(self.institution.governing_jurisdiction),
            canonical_encode_string(self.institution.accountable_officer),
            canonical_encode_string(self.institution.appeal_path),
        ]
        return b"".join(chunks)

    def compute_binding_hash(self) -> str:
        return hashlib.sha256(self.compute_canonical_binding_record()).hexdigest()

    def validate_layers(self) -> Tuple[bool, List[str]]:
        """
        Validate invariant structural consistency constraints across the 7-layer stack.
        This is a structural consistency check under the declared observer; it does not
        substitute for external institutional verification or physical replay.
        """
        errors: List[str] = []

        # Invariant 1: Proposal generator cannot own terminal authority (Self-Critique Non-Authority)
        if self.proposal.generator_id == self.terminal.decider_id:
            errors.append("Proposal generator cannot be the terminal decider (Self-Critique Non-Authority Violation).")

        # Invariant 2: Terminal authority requires accountable decider
        if not self.terminal.is_human_or_delegated_body:
            errors.append("Terminal decision must be governed by an accountable human or institutional body.")

        # Invariant 3: Trace custody and proposal binding integrity
        if not self.trace.verify_content_hash(self.proposal):
            errors.append("Trace custody failure: Trace content_hash does not match canonical length-delimited record bound to proposal.")

        # Invariant 4: Exactness Fraud Criterion & Authorized Status checks
        if self.terminal.status == TerminalStatus.AUTHORIZED_UNDER_OBSERVER:
            if not self.attestation.descent_executed:
                errors.append("Counterfeit descent: Authorized status claimed without executed descent attestation.")
            
            # Distinct evaluation: ExactClaim vs Scoped Authorization
            if self.terminal.claims_exactness:
                if not self.residual.is_exact:
                    errors.append(
                        f"Exactness fraud violation: Exactness claimed with non-zero residual "
                        f"(defect mass: {self.residual.defect_mass}, unverified: {len(self.residual.unverified_scope)}, "
                        f"refusals: {len(self.residual.refusal_reasons)})."
                    )
            else:
                # Scoped authorization evaluated against declared tolerance rule
                if self.residual.defect_mass > self.terminal.tolerated_defect_mass:
                    errors.append(
                        f"Scoped authorization violation: Residual defect mass {self.residual.defect_mass} "
                        f"exceeds declared tolerance {self.terminal.tolerated_defect_mass}."
                    )
                unauthorized_scope = [
                    s for s in self.residual.unverified_scope
                    if s not in self.terminal.tolerated_unverified_scope
                ]
                if unauthorized_scope:
                    errors.append(
                        f"Scoped authorization violation: Unverified scope items {unauthorized_scope} "
                        f"not authorized in declared tolerated_unverified_scope."
                    )
                unauthorized_refusals = [
                    r for r in self.residual.refusal_reasons
                    if r not in self.terminal.tolerated_refusal_reasons
                ]
                if unauthorized_refusals:
                    errors.append(
                        f"Scoped authorization violation: Evaluator refusal reasons {unauthorized_refusals} "
                        f"not authorized in declared tolerated_refusal_reasons."
                    )

            if not self.attestation.replay_receipt:
                errors.append("Attestation evidence missing: Authorized status requires an inspectable replay_receipt.")
            if not self.institution.entity_id or not self.institution.accountable_officer:
                errors.append("Institutional standing missing: Authorized status requires declared entity_id and accountable_officer.")
            if self.attestation.verification_hash:
                expected_hash = self.compute_binding_hash()
                if self.attestation.verification_hash != expected_hash:
                    errors.append("Attestation binding mismatch: verification_hash does not match canonical length-delimited packet binding.")
            else:
                errors.append("Attestation verification hash missing: Authorized status requires verification_hash.")

        return len(errors) == 0, errors


def create_bound_attestation(
    proposal: Proposal,
    trace: TraceRecord,
    observer: ObserverPacket,
    residual: Residual,
    terminal: Terminal,
    institution: Institution,
    replay_receipt: str,
    descent_executed: bool = True,
) -> Attestation:
    """Helper to generate an Attestation whose verification_hash is bound to the canonical packet record."""
    dummy_attestation = Attestation(descent_executed=descent_executed, verification_hash="", replay_receipt=replay_receipt)
    dummy_packet = AuthorityPacket(
        proposal=proposal,
        trace=trace,
        observer=observer,
        residual=residual,
        terminal=terminal,
        attestation=dummy_attestation,
        institution=institution,
    )
    binding_hash = dummy_packet.compute_binding_hash()
    return Attestation(descent_executed=descent_executed, verification_hash=binding_hash, replay_receipt=replay_receipt)


def evaluate_exactness_fraud_criterion(packet: AuthorityPacket) -> Tuple[bool, str]:
    """
    Evaluate structural consistency constraints across the authority packet:
    Refutes any packet claiming authorized status without executed descent attestation,
    claiming exactness with masked non-zero residuals/refusals (Exactness Fraud),
    exceeding scoped defect tolerances, exhibiting broken trace custody, or lacking
    bound attestation hashes.

    Note: This is a packet-shape demonstration and structural consistency schema
    under the declared observer; it refutes invalid structural claims in the red direction,
    but a passing result returns "Structurally consistent but unverified until an
    independent verifier binds and checks the evidence."
    """
    valid, errors = packet.validate_layers()
    if not valid:
        return False, "; ".join(errors)
    return True, "Structurally consistent but unverified until an independent verifier binds and checks the evidence."


def calculate_ngd(path_evaluations: List[dict[str, Any]]) -> Optional[Fraction]:
    """
    Calculate the Negative Gluing Defect (NGD):
    NGD = N(local_green and global_red) / N(local_green)
    Returns exact Fraction, or None when local_green count is zero (conditional rate is undefined).
    Rejects malformed flags (non-boolean values).
    """
    local_green_count = 0
    local_green_and_global_red_count = 0

    for idx, item in enumerate(path_evaluations):
        if not isinstance(item, dict):
            raise TypeError(f"Evaluation item at index {idx} must be a dict, got {type(item).__name__}")
        
        lg = item.get("local_green", False)
        gr = item.get("global_red", False)

        if not isinstance(lg, bool):
            raise TypeError(f"Malformed local_green flag at index {idx}: expected bool, got {type(lg).__name__} ({lg!r})")
        if not isinstance(gr, bool):
            raise TypeError(f"Malformed global_red flag at index {idx}: expected bool, got {type(gr).__name__} ({gr!r})")

        if lg:
            local_green_count += 1
            if gr:
                local_green_and_global_red_count += 1

    if local_green_count == 0:
        return None

    return Fraction(local_green_and_global_red_count, local_green_count)


def calculate_acr(verified_count: int, proposal_count: int) -> Optional[Fraction]:
    """
    Calculate the Authority Coverage Ratio (ACR) over a discrete cohort/window W:
    ACR_count = N_W(verified_packets) / N_W(proposals_generated)
    Under stationary throughput within window W, ACR_count = (r_V * Delta t) / (r_G * Delta t) = r_V / r_G.
    Requires integer counts with 0 <= verified_count <= proposal_count.
    Returns exact Fraction in [0, 1], or None when proposal_count == 0 (undefined ratio for empty denominator).
    Rejects malformed flags and floats.
    """
    if isinstance(verified_count, bool) or isinstance(proposal_count, bool):
        raise TypeError("Counts must be integers, not booleans")
    if isinstance(verified_count, float) or isinstance(proposal_count, float):
        raise TypeError("Floats are rejected; counts must be exact integers")
    if not isinstance(verified_count, int) or not isinstance(proposal_count, int):
        raise TypeError("Counts must be integers")

    if proposal_count < 0:
        raise ValueError("proposal_count must be non-negative")
    if verified_count < 0:
        raise ValueError("verified_count must be non-negative")
    if verified_count > proposal_count:
        raise ValueError(
            f"verified_count ({verified_count}) cannot exceed proposal_count ({proposal_count})"
        )
    if proposal_count == 0:
        return None
    return Fraction(verified_count, proposal_count)


def calculate_acr_rate(rate_verification: Fraction | int, rate_generation: Fraction | int) -> Fraction:
    """
    Calculate instantaneous Authority Coverage Ratio from rates:
    ACR_rate = r_V / r_G
    Requires rate_generation > 0 and rate_verification >= 0.
    Rejects floats and non-rational inputs; returns exact Fraction.
    """
    if isinstance(rate_verification, (bool, float)) or isinstance(rate_generation, (bool, float)):
        raise TypeError("Floats and booleans are rejected; rates must be exact Fraction or int")

    if isinstance(rate_verification, int):
        rate_verification = Fraction(rate_verification, 1)
    if isinstance(rate_generation, int):
        rate_generation = Fraction(rate_generation, 1)

    if not isinstance(rate_verification, Fraction) or not isinstance(rate_generation, Fraction):
        raise TypeError("Rates must be exact Fraction or int")

    if rate_generation <= Fraction(0, 1):
        raise ValueError("rate_generation must be strictly positive")
    if rate_verification < Fraction(0, 1):
        raise ValueError("rate_verification must be non-negative")
    return rate_verification / rate_generation


def calculate_backlog_accumulation(
    rate_generation: Fraction | int,
    rate_verification: Fraction | int,
    time_units: Fraction | int,
) -> Fraction:
    """
    Calculate authority backlog accumulation over a given time duration:
    dU/dt = r_G - r_V
    Delta U = (r_G - r_V) * Delta t
    Rejects floats and booleans; returns exact Fraction.
    """
    if isinstance(rate_generation, (bool, float)) or isinstance(rate_verification, (bool, float)) or isinstance(time_units, (bool, float)):
        raise TypeError("Floats and booleans are rejected; provide exact Fraction or int")

    if isinstance(rate_generation, int):
        rate_generation = Fraction(rate_generation, 1)
    if isinstance(rate_verification, int):
        rate_verification = Fraction(rate_verification, 1)
    if isinstance(time_units, int):
        time_units = Fraction(time_units, 1)

    if not isinstance(rate_generation, Fraction) or not isinstance(rate_verification, Fraction) or not isinstance(time_units, Fraction):
        raise TypeError("Inputs must be exact Fraction or int")

    if time_units < Fraction(0, 1):
        raise ValueError("time_units must be non-negative")
    rate_diff = rate_generation - rate_verification
    return rate_diff * time_units

