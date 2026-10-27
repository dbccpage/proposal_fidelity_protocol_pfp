"""
llm_proposer.py -- retired Plan 02 live-model session adapter.

The session loop drove the PO-032 research governor (``l1_symbol_game_governor``)
by searching ``research/mssn_sn_tower/papers/032_*/code`` and ``033_*`` for it.
Those folders were deleted, so every call failed with
``RESEARCH_GOVERNOR_UNAVAILABLE``. The corrected governor now lives only inside
the paper 004 and 005 deposits, which must stay hermetic and may not be imported
from here. Under ``RULE_RUST_CRATES_RS_EXCLUSIVE_001`` item 3 the retired runtime
fails closed with the typed refusal ``RUNTIME_RETIRED`` instead of searching the
tree for a copy.

What remains is the move protocol's parsing, which is exact and refuses rather
than drops: ``parse_move`` and ``claims_from_json``. ``scripted_proposer`` stays
as a deterministic stand-in model for offline tests.

AuthorityEffect: None. The model proposes; the host disposes.
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from operations.domain.rop.result import Refusal

#: A model is any callable taking a prompt string and returning completion text.
Completion = Callable[[str], str]

RUNTIME_RETIRED = "RUNTIME_RETIRED"
MALFORMED_MOVE = "MALFORMED_MOVE"

_EXACT_RATIONAL = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
_VERTEX = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.:]*")


class ProposerRuntimeRetired(RuntimeError):
    """The governed session runtime is retired; its refusal is typed."""

    code = RUNTIME_RETIRED

    def __init__(self) -> None:
        self.refusal = Refusal(
            RUNTIME_RETIRED,
            "the llm_proposer governed session is retired: its research governor "
            "was deleted and the corrected governor lives only in the hermetic "
            "paper 004/005 deposits; drive a governed session through the Adversary "
            "entry point instead",
            locus="adversary.infrastructure.providers.adapters.llm_proposer.run_governed_session",
        )
        super().__init__(f"{self.refusal.code}: {self.refusal.message}")


class MalformedMove(ValueError):
    """A model move that cannot be read exactly is refused, not repaired."""

    code = MALFORMED_MOVE

    def __init__(self, detail: str) -> None:
        super().__init__(f"{MALFORMED_MOVE}: {detail}")
        self.detail = detail


def run_governed_session(complete: Completion, *args: Any, **kwargs: Any) -> None:
    """Retired. Always raises ``ProposerRuntimeRetired`` before calling the model."""
    raise ProposerRuntimeRetired()


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise MalformedMove(f"duplicate JSON key {key!r}")
        obj[key] = value
    return obj


def parse_move(raw: str) -> Optional[dict]:
    """Extract the first JSON object from model output.

    Returns None when there is no JSON object. A JSON object that repeats a key
    at any depth (``{"a->b": 1, "a->b": 5}``) raises ``MalformedMove``: a plain
    ``json.loads`` would keep only the last value and hide the conflict.
    """
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0), object_pairs_hook=_unique_keys)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _exact_claim(key: str, value: object) -> Fraction:
    if type(value) is int:
        return Fraction(value)
    if type(value) is str and _EXACT_RATIONAL.fullmatch(value) is not None:
        claim = Fraction(value)
        if str(claim) != value:
            raise MalformedMove(f"claim {key!r} is not in lowest terms: {value!r}")
        return claim
    raise MalformedMove(
        f"claim {key!r} must be an integer or an exact rational string, "
        f"not {type(value).__name__} {value!r}"
    )


def claims_from_json(move: dict) -> Dict[Tuple[str, str], Fraction]:
    """Read ``proposed_claims`` exactly, or refuse the whole move.

    Keys must be ``"u->v"`` with two nonblank vertex names; values must be
    integers or exact rational strings such as ``"-3/4"``. A malformed key, a
    float, a Boolean or a missing claim object is refused with
    ``MalformedMove``; nothing is skipped and nothing is converted. A repeated
    key cannot reach this function as a dict: ``parse_move`` refuses it while
    parsing the JSON text, which is where it would otherwise be lost.
    """
    raw = move.get("proposed_claims")
    if type(raw) is not dict:
        raise MalformedMove("proposed_claims must be an object")
    claims: Dict[Tuple[str, str], Fraction] = {}
    for key, value in raw.items():
        parts = key.split("->") if type(key) is str else []
        if len(parts) != 2 or any(_VERTEX.fullmatch(part) is None for part in parts):
            raise MalformedMove(f"claim key {key!r} is not of the form 'u->v'")
        edge = (parts[0], parts[1])
        if edge in claims:
            raise MalformedMove(f"claim key {key!r} repeats an edge")
        claims[edge] = _exact_claim(key, value)
    return claims


def scripted_proposer(moves: Sequence[dict]) -> Completion:
    """A deterministic stand-in model that emits the given moves in order (JSON)."""
    seq = iter(moves)

    def _complete(_prompt: str) -> str:
        try:
            return json.dumps(next(seq))
        except StopIteration:
            return json.dumps({"move_type": "VERIFY", "obligation": "ZERO_OBSTRUCTION"})

    return _complete


__all__ = [
    "Completion",
    "MALFORMED_MOVE",
    "MalformedMove",
    "ProposerRuntimeRetired",
    "RUNTIME_RETIRED",
    "claims_from_json",
    "parse_move",
    "run_governed_session",
    "scripted_proposer",
]
