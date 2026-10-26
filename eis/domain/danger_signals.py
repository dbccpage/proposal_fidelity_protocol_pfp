"""Host danger signals and the independence of Signal 2 from Signal 1.

A two-signal rule is easy to satisfy vacuously. If Signal 2 is computed from
Signal 1 (for example "defect count = number of detector matches"), every
conjunct holds while only one signal exists. `EPIC-OE-IMMUNE-002` names this
`TWO_SIGNAL_COLLAPSE`: counting the same predicate twice, deriving the danger
bit from the detector match, or accepting a model-authored danger flag.

This module holds what both two-signal paths in this package share:

- `HOST_DANGER_SIGNAL_KINDS`, the closed registry of danger kinds a host check
  may report (`IMMUNE-002-W3`). An open vocabulary would let a caller call
  anything a danger signal.
- `FORBIDDEN_DANGER_OBSERVERS`, producers that may never originate Signal 2.
- `assert_signals_independent`, which witnesses independence for the screening
  path (`Signal1Match` / `Signal2Danger`) or refuses with a typed code.

The learned-guard path (`guard_activation`) applies the same rule to anti-skill
hits and danger receipts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Sequence

from .definitions_loader import load_danger_signals
from .value_objects import Signal1Match, Signal2Danger

_danger_defs = load_danger_signals()

HOST_DANGER_SIGNAL_KINDS = frozenset(
    _danger_defs.get(
        "host_danger_signal_kinds",
        (
            "REPLAY_FAILURE",
            "PROTECTED_FIELD_VIOLATION",
            "MANIFEST_CONTAMINATION",
            "MALFORMED_PAYLOAD",
        ),
    )
)

# Only a host observes danger. A model, agent or detector reporting one is the
# proposer (or Signal 1 itself) authorising its own activation.
FORBIDDEN_DANGER_OBSERVERS = frozenset(
    _danger_defs.get(
        "forbidden_danger_observers",
        ("MODEL", "LLM", "AGENT", "DETECTOR", "MATCHER"),
    )
)

INDEPENDENCE_REFUSAL_CODES = frozenset(
    _danger_defs.get(
        "independence_refusal_codes",
        (
            "TWO_SIGNAL_COLLAPSE",
            "UNWITNESSED_DANGER_SIGNAL",
            "UNREGISTERED_DANGER_KIND",
        ),
    )
)


class SignalIndependenceRefusal(ValueError):
    """Signal 2 is not shown to be independent of Signal 1."""

    def __init__(self, code: str, detail: str) -> None:
        if code not in INDEPENDENCE_REFUSAL_CODES:
            raise ValueError(f"unknown independence refusal code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def signal1_digest(matches: Sequence[Signal1Match]) -> str:
    """Content digest of a Signal 1 match set (order-independent)."""
    rows = sorted(
        [match.epitope_name, match.pattern_matched, match.offset] for match in matches
    )
    encoded = json.dumps(
        rows, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _overlapping(matches: Sequence[Signal1Match], spans: tuple[tuple[int, int], ...]) -> tuple[int, int] | None:
    for match in matches:
        start = match.offset
        stop = start + max(len(match.pattern_matched), 1)
        for low, high in spans:
            if start < high and low < stop:
                return (start, stop)
    return None


def assert_signals_independent(
    matches: Sequence[Signal1Match],
    danger: Signal2Danger | None,
    *,
    detector_id: str,
    detector_predicates: frozenset[str],
    offsets_are_content: bool,
) -> str:
    """Return the independence basis, or refuse.

    `detector_id` is the matcher that produced `matches`; `detector_predicates`
    are the host danger kinds that matcher itself evaluates (for example a
    detector that flags host-only keys evaluates `PROTECTED_FIELD_VIOLATION`).
    `offsets_are_content` says whether each match's `offset` and
    `pattern_matched` locate the match in the checked content (true for the
    regex matcher; false for matchers whose matches name a finding code). When
    it is true, a match overlapping one of Signal 2's `evidence_spans` is
    refused: one token cannot be both signals.

    Identifiers are compared case-insensitively (`str.casefold`), so
    "Regex" cannot pass as an observer distinct from the matcher "regex".
    """
    if danger is None:
        return "no Signal 2 was observed"
    if type(danger) is not Signal2Danger:
        raise TypeError("danger must be an exact Signal2Danger")
    if type(detector_id) is not str or not detector_id.strip():
        raise ValueError("detector_id must name the matcher that produced Signal 1")
    if type(detector_predicates) is not frozenset:
        raise TypeError("detector_predicates must be a frozenset of danger kinds")
    if type(offsets_are_content) is not bool:
        raise TypeError("offsets_are_content must be an exact bool")
    observer = danger.observer_id
    if not observer.strip():
        raise SignalIndependenceRefusal(
            "UNWITNESSED_DANGER_SIGNAL",
            "Signal 2 names no host observer, so its independence cannot be checked",
        )
    folded = observer.strip().casefold()
    if folded in {name.casefold() for name in FORBIDDEN_DANGER_OBSERVERS}:
        raise SignalIndependenceRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"Signal 2 was reported by {observer!r}; danger is observed by a host check, "
            "not proposed by a model or a detector",
        )
    if folded == detector_id.strip().casefold():
        raise SignalIndependenceRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"Signal 2 was observed by {observer!r}, the matcher that produced Signal 1; "
            "the danger bit is derived from the match",
        )
    if danger.danger_type not in HOST_DANGER_SIGNAL_KINDS:
        raise SignalIndependenceRefusal(
            "UNREGISTERED_DANGER_KIND",
            f"{danger.danger_type!r} is not in the closed registry: "
            + ", ".join(sorted(HOST_DANGER_SIGNAL_KINDS)),
        )
    if danger.danger_type in detector_predicates:
        raise SignalIndependenceRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"the matcher {detector_id!r} already evaluates {danger.danger_type}; "
            "the same predicate would be counted twice",
        )
    if matches and danger.evidence_digest == signal1_digest(matches):
        raise SignalIndependenceRefusal(
            "TWO_SIGNAL_COLLAPSE",
            "Signal 2's evidence is the digest of the Signal 1 matches; "
            "that is one signal counted twice",
        )
    if offsets_are_content:
        overlap = _overlapping(matches, danger.evidence_spans)
        if overlap is not None:
            raise SignalIndependenceRefusal(
                "TWO_SIGNAL_COLLAPSE",
                f"the Signal 1 match at characters [{overlap[0]}, {overlap[1]}) lies inside "
                f"the {danger.danger_type} evidence; one token cannot be both signals",
            )
    return (
        f"host observer {observer} reported {danger.danger_type} "
        f"({danger.defect_count} defect(s), evidence {danger.evidence_digest[:23]}...), "
        f"distinct from matcher {detector_id} and its matches"
    )


__all__ = [
    "FORBIDDEN_DANGER_OBSERVERS",
    "HOST_DANGER_SIGNAL_KINDS",
    "INDEPENDENCE_REFUSAL_CODES",
    "SignalIndependenceRefusal",
    "assert_signals_independent",
    "signal1_digest",
]
