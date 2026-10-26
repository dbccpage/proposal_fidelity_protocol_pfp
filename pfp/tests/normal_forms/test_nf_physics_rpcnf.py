"""The nf.physics.rpcnf flag calls the shipped relational point-coincidence check.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import RPCNF_ID
from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import checker_for
from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import evaluate_rpcnf
from omega_engine_pfp.infrastructure.normal_forms.sn_dispatch import evaluate_sn_transition

_KEY = ["phi0", "phi1", "phi2", "phi3"]
_MINIMAL_ROWS = [
    {"phi0": "0", "phi1": "0", "phi2": "0", "phi3": "0", "scalar": "a"},
    {"phi0": "1", "phi1": "0", "phi2": "0", "phi3": "0", "scalar": "b"},
    {"phi0": "0", "phi1": "1", "phi2": "0", "phi3": "0", "scalar": "c"},
    {"phi0": "0", "phi1": "0", "phi2": "1", "phi3": "0", "scalar": "d"},
    {"phi0": "0", "phi1": "0", "phi2": "0", "phi3": "1", "scalar": "e"},
]


def test_rpcnf_draft_is_not_marked_as_a_true_normal_form() -> None:
    path = Path(__file__).resolve().parents[2] / "infrastructure" / "yaml" / "normal_forms" / "nf.physics.rpcnf.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    quad = document["definition"]["quadrilateral"]
    assert document["identity"]["contract_status"] == "draft"
    assert quad["qualifies_as_true_normal_form"] is False
    assert quad["qualification_gap"] == "a draft contract is not a true normal form"
    assert checker_for("nf.physics.rpcnf") is evaluate_rpcnf


def test_rpcnf_flag_admits_keyed_row_and_refuses_bare_coordinates() -> None:
    assert RPCNF_ID == "nf.physics.rpcnf"
    assert checker_for("nf.physics.rpcnf") is evaluate_rpcnf

    keyed = {"key": _KEY, "rows": _MINIMAL_ROWS}
    admitted = evaluate_sn_transition("nf.physics.rpcnf", keyed)
    assert admitted["contract_id"] == "nf.physics.rpcnf"
    assert admitted["local_terminal"] == "RelationalPointCertified"
    assert admitted["admitted"] is True

    bare = {"rows": [{"x0": "1", "x1": "0", "x2": "0", "x3": "0"}]}
    refused = evaluate_sn_transition("nf.physics.rpcnf", bare)
    assert refused["contract_id"] == "nf.physics.rpcnf"
    assert refused["local_terminal"] == "BareCoordinateContamination"
    assert refused["admitted"] is False

    one_attribute = evaluate_rpcnf({"key": ["phi0"], "rows": _MINIMAL_ROWS})
    assert one_attribute["local_terminal"] == "NonKeyCoincidenceViolation"
    assert one_attribute["admitted"] is False

    one_row = evaluate_rpcnf({"key": _KEY, "rows": [_MINIMAL_ROWS[0]]})
    assert one_row["local_terminal"] == "NonKeyCoincidenceViolation"
    assert one_row["reason"] == "candidate key K is not minimal"
    assert one_row["admitted"] is False
