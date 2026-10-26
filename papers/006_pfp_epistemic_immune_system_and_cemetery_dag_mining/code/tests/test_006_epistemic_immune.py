"""Educational illustrations retained with PFP VI.

These toy classes are defined here and are not the production failure store,
the production two-signal gate, or any production detector. A pass shows only
that these small illustrations behave as written.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

# --- Toy models (illustration only) ---


@dataclass(frozen=True)
class DangerSignal:
    defect_mass: Fraction
    cycle_obstruction: Fraction
    unadmitted_tokens: int

    def is_quarantine_triggered(self, threshold: Fraction = Fraction(0, 1)) -> bool:
        """Toy rule: trigger when defect mass or cycle obstruction is positive.

        The production gate uses a different, two-signal contract.
        """
        return (
            self.defect_mass > threshold
            or self.cycle_obstruction > threshold
            or self.unadmitted_tokens > 0
        )


@dataclass(frozen=True)
class ThymicCheckResult:
    is_self: bool  # the token belongs to the supplied alphabet
    admitted: bool
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (self.is_self, self.admitted, self.reason) == (
            other.is_self,
            other.admitted,
            other.reason,
        )


def evaluate_thymic_selection(token: str, admitted_alphabet: set) -> ThymicCheckResult:
    """Toy membership check: admit a token only if it is in the supplied alphabet."""
    if token in admitted_alphabet:
        return ThymicCheckResult(is_self=True, admitted=True, reason="ADMITTED_SELF")
    return ThymicCheckResult(is_self=False, admitted=False, reason="REJECTED_NON_SELF")


@dataclass
class CemeteryDAGSink:
    """Toy in-memory list; each entry records the digest of its predecessor.

    It has no file persistence, header, restart check, or retained anchor.
    """

    entries: list[dict[str, Any]] = field(default_factory=list)

    def append_candidate(
        self,
        step_index: int,
        prompt_sha256: str,
        candidate_tokens: str,
        danger: DangerSignal,
        disposition: str,
        ddc_letter: str,
    ) -> str:
        prev_hash = self.entries[-1]["entry_hash"] if self.entries else "GENESIS_ROOT"
        payload = {
            "step_index": step_index,
            "prev_hash": prev_hash,
            "prompt_sha256": prompt_sha256,
            "candidate_tokens": candidate_tokens,
            "defect_mass": str(danger.defect_mass),
            "cycle_obstruction": str(danger.cycle_obstruction),
            "unadmitted_tokens": danger.unadmitted_tokens,
            "disposition": disposition,
            "ddc_letter": ddc_letter,
        }
        # Sorted-key JSON only; this is not an RFC 8785 implementation.
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        entry_hash = hashlib.sha256(canonical_bytes).hexdigest()
        record = {**payload, "entry_hash": entry_hash}
        self.entries.append(record)
        return entry_hash


# --- Tests of the toy models ---


def test_danger_signal_threshold():
    clean_signal = DangerSignal(Fraction(0, 1), Fraction(0, 1), 0)
    assert not clean_signal.is_quarantine_triggered()

    defective_signal = DangerSignal(Fraction(1, 2), Fraction(0, 1), 0)
    assert defective_signal.is_quarantine_triggered()

    unadmitted_signal = DangerSignal(Fraction(0, 1), Fraction(0, 1), 2)
    assert unadmitted_signal.is_quarantine_triggered()


def test_thymic_selection_exact_type_equality():
    alphabet = {"E", "R", "C", "I", "LAMBDA", "D", "M", "T"}
    res1 = evaluate_thymic_selection("E", alphabet)
    assert res1.admitted is True
    assert res1.is_self is True

    res2 = evaluate_thymic_selection("X_UNKNOWN", alphabet)
    assert res2.admitted is False
    assert res2.is_self is False

    # Exact-type equality: a string with the same reason is not equal.
    res3 = evaluate_thymic_selection("E", alphabet)
    assert res1 == res3
    assert not (res1 == "ADMITTED_SELF")


def test_toy_chain_links_predecessor_digests():
    sink = CemeteryDAGSink()
    prompt_hash = hashlib.sha256(b"Prompt objective").hexdigest()

    # First toy entry: a refused candidate.
    danger1 = DangerSignal(Fraction(3, 1), Fraction(1, 1), 1)
    hash1 = sink.append_candidate(
        step_index=0,
        prompt_sha256=prompt_hash,
        candidate_tokens="INVALID_TOKEN",
        danger=danger1,
        disposition="REFUSED",
        ddc_letter="M",
    )
    assert len(sink.entries) == 1
    assert sink.entries[0]["prev_hash"] == "GENESIS_ROOT"
    assert sink.entries[0]["entry_hash"] == hash1

    # Second toy entry: an admitted candidate linked to the first digest.
    danger2 = DangerSignal(Fraction(0, 1), Fraction(0, 1), 0)
    hash2 = sink.append_candidate(
        step_index=1,
        prompt_sha256=prompt_hash,
        candidate_tokens="CONTRACTIVE_EDGE",
        danger=danger2,
        disposition="ADMITTED",
        ddc_letter="C",
    )
    assert len(sink.entries) == 2
    assert sink.entries[1]["prev_hash"] == hash1
    assert sink.entries[1]["entry_hash"] == hash2

    # The refused toy entry is still present in the in-memory list.
    refused = [e for e in sink.entries if e["disposition"] == "REFUSED"]
    assert len(refused) == 1
    assert refused[0]["candidate_tokens"] == "INVALID_TOKEN"
    assert refused[0]["defect_mass"] == "3"
