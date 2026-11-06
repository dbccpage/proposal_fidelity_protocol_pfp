"""
Packet Firewall Host and Three-Layer Verification Protocol for Paper 032.

This module implements:
1. The 4-field packet kernel: (contract, task, payload, parent_hash).
2. Closed-operator first-token linter policing mandatory evidence verbs.
3. Explicit Unicode codepoint pinning for carrier alphabet.
4. The Three Firewalls: FW-CARRIER, FW-MOVE, FW-REPLAY fail-closed.
5. SHA-256 content-addressed derivation event DAG.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Set, Tuple

# Closed-set operator vocabulary
DECLARED_OPERATORS: Set[str] = {
    "ASSERT",
    "CUT",
    "REDUCE",
    "PROVE",
    "VERIFY",
    "RETRACT",
    "REFUSE",
}

# Standard Unicode codepoint ranges for carrier validation
# ASCII basic Latin (32..126), Greek lowercase (0x03B1..0x03C9), Greek uppercase (0x0391..0x03A9)
def is_valid_carrier_codepoint(cp: int) -> bool:
    if 32 <= cp <= 126:
        return True
    if 0x0391 <= cp <= 0x03A9:
        return True
    if 0x03B1 <= cp <= 0x03C9:
        return True
    if cp in {0x2192, 0x22A2, 0x22A5, 0x2261, 0x03B4, 0x03A6}:  # ->, |-, bottom, ==, delta, Phi
        return True
    return False


class FirewallRefusalCode(Enum):
    """Refusal codes for the three host firewalls (carrier, move, replay)."""
    FW_CARRIER_VIOLATION = "FW_CARRIER_VIOLATION"
    FW_MOVE_VIOLATION = "FW_MOVE_VIOLATION"
    FW_REPLAY_VIOLATION = "FW_REPLAY_VIOLATION"
    OP_UNDECLARED = "OP_UNDECLARED"
    HASH_MISMATCH = "HASH_MISMATCH"


@dataclass(frozen=True)
class PacketKernel:
    """The 4-field core packet envelope from Paper 015 / Paper 032."""
    contract: str
    task: str
    payload: Dict[str, Any]
    parent_hash: Optional[str] = None

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 content digest."""
        serialized = json.dumps(
            {
                "contract": self.contract,
                "task": self.task,
                "payload": self.payload,
                "parent_hash": self.parent_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DerivationStep:
    """Candidate derivation move proposed by proposer (LLM)."""
    op: str
    position: int
    rule_id: str
    substitution: Dict[str, str]
    pre_state_hash: str
    post_state_hash: str
    content: str


@dataclass
class FirewallVerdict:
    """Result of host firewall evaluation."""
    admitted: bool
    refusal_code: Optional[FirewallRefusalCode] = None
    reason: Optional[str] = None
    verified_post_hash: Optional[str] = None


class PacketFirewallHost:
    """
    Host-side independent verification oracle executing the Three Firewalls fail-closed.
    """

    def __init__(self, carrier_alphabet: Optional[Set[str]] = None):
        self.carrier_alphabet = carrier_alphabet

    def lint_first_token_op(self, statement: str) -> Tuple[bool, Optional[str]]:
        """
        Enforces that the first token of every statement is in DECLARED_OPERATORS.
        """
        tokens = statement.strip().split()
        if not tokens:
            return False, "Statement is empty"
        first_op = tokens[0].upper()
        if first_op not in DECLARED_OPERATORS:
            return False, f"Operator '{first_op}' is undeclared. Mandatory first token must be in {sorted(DECLARED_OPERATORS)}"
        return True, first_op

    PERMITTED_PACKET_SYNTAX: Set[str] = set(" \t\n\r()[]{}->=:,_\"'0123456789.+-/*")

    def check_fw_carrier(self, text: str) -> FirewallVerdict:
        """
        FW-CARRIER: Asserts that all characters belong to the pinned carrier codepoint set
        or permitted structural packet syntax.
        """
        for char in text:
            cp = ord(char)
            if self.carrier_alphabet is not None:
                if char not in self.carrier_alphabet and char not in self.PERMITTED_PACKET_SYNTAX:
                    return FirewallVerdict(
                        admitted=False,
                        refusal_code=FirewallRefusalCode.FW_CARRIER_VIOLATION,
                        reason=f"Character '{char}' (U+{cp:04X}) violates pinned carrier alphabet.",
                    )
            else:
                if not is_valid_carrier_codepoint(cp):
                    return FirewallVerdict(
                        admitted=False,
                        refusal_code=FirewallRefusalCode.FW_CARRIER_VIOLATION,
                        reason=f"Codepoint U+{cp:04X} outside declared carrier.",
                    )
        return FirewallVerdict(admitted=True)

    def check_fw_payload_carrier(self, payload_text: str) -> FirewallVerdict:
        """
        Strict payload carrier check: asserts every character belongs strictly
        to the pinned carrier alphabet with zero syntax relaxation.
        """
        if self.carrier_alphabet is None:
            return self.check_fw_carrier(payload_text)
        for char in payload_text:
            if char not in self.carrier_alphabet:
                return FirewallVerdict(
                    admitted=False,
                    refusal_code=FirewallRefusalCode.FW_CARRIER_VIOLATION,
                    reason=f"Payload character '{char}' (U+{ord(char):04X}) outside exact pinned carrier alphabet.",
                )
        return FirewallVerdict(admitted=True)

    def check_fw_move(self, step: DerivationStep, licensed_rules: Dict[str, Any]) -> FirewallVerdict:
        """
        FW-MOVE: Verifies that rule_id is declared, licensed, and priced.
        """
        valid_op, op_err = self.lint_first_token_op(step.op)
        if not valid_op:
            return FirewallVerdict(
                admitted=False,
                refusal_code=FirewallRefusalCode.OP_UNDECLARED,
                reason=op_err,
            )

        if step.rule_id not in licensed_rules:
            return FirewallVerdict(
                admitted=False,
                refusal_code=FirewallRefusalCode.FW_MOVE_VIOLATION,
                reason=f"Rule '{step.rule_id}' is not in licensed rule schema (unpriced move / smuggled axiom).",
            )
        return FirewallVerdict(admitted=True)

    def check_fw_replay(
        self,
        current_state_str: str,
        step: DerivationStep,
        apply_fn: Any,
    ) -> FirewallVerdict:
        """
        FW-REPLAY: Recomputes state transition independently and checks SHA-256 digests.
        """
        computed_pre_hash = hashlib.sha256(current_state_str.encode("utf-8")).hexdigest()
        if computed_pre_hash != step.pre_state_hash:
            return FirewallVerdict(
                admitted=False,
                refusal_code=FirewallRefusalCode.HASH_MISMATCH,
                reason=f"Pre-state hash mismatch: computed {computed_pre_hash[:8]} != claimed {step.pre_state_hash[:8]}",
            )

        # Execute host deterministic application
        next_state_str = apply_fn(current_state_str, step.position, step.rule_id, step.substitution)
        computed_post_hash = hashlib.sha256(next_state_str.encode("utf-8")).hexdigest()

        if computed_post_hash != step.post_state_hash:
            return FirewallVerdict(
                admitted=False,
                refusal_code=FirewallRefusalCode.FW_REPLAY_VIOLATION,
                reason=f"Post-state hash mismatch: host produced {computed_post_hash[:8]} != claimed {step.post_state_hash[:8]}",
                verified_post_hash=computed_post_hash,
            )

        return FirewallVerdict(admitted=True, verified_post_hash=computed_post_hash)

    def evaluate_pipeline(
        self,
        current_state_str: str,
        step: DerivationStep,
        licensed_rules: Dict[str, Any],
        apply_fn: Any,
    ) -> FirewallVerdict:
        """
        Sequential execution through FW-CARRIER -> FW-MOVE -> FW-REPLAY.
        """
        v_carrier = self.check_fw_carrier(step.content)
        if not v_carrier.admitted:
            return v_carrier

        v_move = self.check_fw_move(step, licensed_rules)
        if not v_move.admitted:
            return v_move

        v_replay = self.check_fw_replay(current_state_str, step, apply_fn)
        return v_replay
