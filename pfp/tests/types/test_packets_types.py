"""Tests for cycle_balance/pfp_cycle_balance_quartet.py (typed contracts of the four-object lifecycle).

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pfp_types_test_support import load_yaml, parity_problems, pfp_root  # noqa: E402
from pfp.domain.homology import cycle_balance as M

FIXTURES = {
    "problem": "01_genesis_cycle_balance_problem.json",
    "candidate": "02_genesis_cycle_balance_candidate.json",
    "verifier": "03_genesis_cycle_balance_verifier.json",
    "receipt": "04_genesis_cycle_balance_receipt.json",
}


def _validate(model, obj):
    """Strict models take enum members from JSON text, so validate through the JSON path."""
    return model.model_validate_json(json.dumps(obj))


def _raw() -> dict[str, dict]:
    base = pfp_root() / "infrastructure" / "yaml" / "cycle_balance"
    return {k: json.loads((base / v).read_text(encoding="utf-8")) for k, v in FIXTURES.items()}


def test_fixtures_validate_and_bind() -> None:
    raw = _raw()
    quartet = _validate(M.CycleBalanceQuartet, raw)
    assert quartet.receipt.verification_status is M.VerificationStatus.UNVERIFIED
    assert quartet.check_digest_bindings(raw) is True


def test_digest_binding_detects_tampering() -> None:
    raw = _raw()
    quartet = _validate(M.CycleBalanceQuartet, raw)
    tampered = copy.deepcopy(raw)
    tampered["problem"]["case_id"] = "other"
    assert quartet.check_digest_bindings(tampered) is False


def test_yaml_model_parity() -> None:
    defs = load_yaml("cycle_balance/pfp_cycle_balance_quartet.yaml")["$defs"]
    names = [
        "ArithmeticDomain", "ClaimedMove", "VerificationRule", "VerificationStatus",
        "StaticCellBounds", "Edge", "Face", "Carrier", "BoundaryMatrices", "ActiveObstruction",
        "CycleBalanceProblem", "CycleBalanceCandidate", "CycleBalanceVerifier", "ClaimHygiene",
        "CycleBalanceReceipt", "CycleBalanceQuartet",
    ]  # fmt: skip
    models = {n: getattr(M, n) for n in names}
    assert parity_problems(defs, models) == []


def _mutated(kind: str, path: list, value) -> dict:
    raw = _raw()[kind]
    node = raw
    for p in path[:-1]:
        node = node[p]
    node[path[-1]] = value
    return raw


@pytest.mark.parametrize(
    ("kind", "path", "value"),
    [
        ("problem", ["authority_effect"], "Granted"),
        ("problem", ["boundary_matrices", "d2", 0, 0], 2),  # chain law d1*d2 != 0
        ("problem", ["boundary_matrices", "d2", 0, 0], True),  # bool is not an int
        ("problem", ["boundary_matrices", "d1", 0], [1, 2]),  # wrong shape
        ("problem", ["active_obstruction", "cycle_z"], [1, 0, 0, 0, 0]),  # not in ker d1
        ("problem", ["carrier", "static_cell_bounds", "max_edges"], 4),  # exceeds bound
        ("problem", ["carrier", "edges", 0, "target"], 0),  # self-loop
        ("problem", ["carrier", "faces", 0, "boundary_edges"], ["e9"]),  # undeclared edge
        ("problem", ["arithmetic_domain"], "FLOAT"),
        ("candidate", ["problem_digest"], "xyz"),
        ("candidate", ["authority_effect"], "Self"),
        ("candidate", ["claimed_move"], "DELETE_FACE"),
        ("candidate", ["constituent_edges"], ["e2-2-3"]),
        ("candidate", ["claimed_integer_preimage_c"], [0.5, 1]),
        ("candidate", ["preserves_chain_law"], 1),
        ("verifier", ["verification_rules"], []),
        (
            "verifier",
            ["verification_rules"],
            ["STATIC_CELL_BOUNDS_CHECK", "STATIC_CELL_BOUNDS_CHECK"],
        ),
        ("receipt", ["terminal_status"], "EXACT"),  # UNVERIFIED skeleton carries no verdict
        ("receipt", ["residuals"], [0]),
        ("receipt", ["receipt_digest"], "short"),
    ],
)
def test_negative_controls_reject(kind: str, path: list, value) -> None:
    model = {
        "problem": M.CycleBalanceProblem,
        "candidate": M.CycleBalanceCandidate,
        "verifier": M.CycleBalanceVerifier,
        "receipt": M.CycleBalanceReceipt,
    }[kind]
    with pytest.raises(ValidationError):
        _validate(model, _mutated(kind, path, value))


def test_unknown_field_rejected_and_record_frozen() -> None:
    raw = _raw()["candidate"]
    raw["passed"] = True
    with pytest.raises(ValidationError):
        _validate(M.CycleBalanceCandidate, raw)
    cand = _validate(M.CycleBalanceCandidate, _raw()["candidate"])
    with pytest.raises(ValidationError):
        cand.candidate_id = "x"
