"""Independent recomputations: GV invariants, trace identities, trivial digests."""

from __future__ import annotations

import hashlib
from fractions import Fraction

import pytest
from adversary.tests.pilots.judge_packet_audit import reference_values as rv


def test_quintic_gv_invariants_match_candelas_et_al() -> None:
    result = rv.gv_invariants([1, 1, 1, 1, 1], 3)
    assert result["n"] == {"1": "2875", "2": "609250", "3": "317206375"}
    assert result["kappa"] == "5" and result["mu"] == "3125"
    assert result["all_integers"] is True


def test_sextic_n3_disagrees_with_the_c036_task_value() -> None:
    # counterexample: C036 TASK.md publishes n_3 = 9299696544 for the sextic
    computed = rv.gv_invariants([1, 1, 1, 1, 2], 3)["n"]
    assert computed["3"] == "11900417220"
    assert computed["3"] != "9299696544"


def test_task_table_parser_and_comparison() -> None:
    text = (
        "1. **Quintic**: $\\mathbb{WP}(1, 1, 1, 1, 1)$, $d = 5$, $\\kappa = 5$.\n"
        "   * $n_1 = 2875, n_2 = 609250$.\n"
        "2. **Decic**: $\\mathbb{WP}(1, 1, 1, 2, 5)$, $d = 10$.\n"
        "   * $n_1 = 168280$.\n"
    )
    rows = rv.parse_task_gv_table(text)
    assert [r["family"] for r in rows] == ["Quintic", "Decic"]
    comparison = rv.compare_gv_table(rows)
    assert [v["agrees"] for v in comparison[0]["values"]] == [True, True]
    decic = comparison[1]["values"][0]
    assert (
        decic["published"] == "168280"
        and decic["recomputed"] == "231200"
        and decic["agrees"] is False
    )


def test_weights_reject_non_int_input() -> None:
    with pytest.raises(TypeError):
        rv.gv_invariants([1, 1, 1, 1, True], 1)


@pytest.mark.parametrize(
    ("group", "rep", "triple", "status"),
    [
        ("SU(2)", "fund", (1, 0, 0), "FAIL"),  # counterexample: B = 0 and C = 0 implies tr F^4 = 0
        ("SU(2)", "fund", (1, 0, Fraction(1, 2)), "PASS"),
        ("SU(2)", "adj", (4, 0, 6), "FAIL"),
        ("SU(2)", "adj", (4, 0, 8), "PASS"),
        ("SU(3)", "adj", (6, 0, 6), "FAIL"),
        ("SU(3)", "adj", (6, 0, 9), "PASS"),
        ("Sp(1)", "adj", (4, 0, 3), "FAIL"),
        ("SU(6)", "adj", (12, 12, 6), "PASS"),
        ("SO(10)", "spinor", (2, -1, Fraction(3, 4)), "PASS"),
        ("G2", "adj", (4, 0, Fraction(5, 2)), "PASS"),
    ],
)
def test_trace_identity_check(group: str, rep: str, triple: tuple, status: str) -> None:
    result = rv.trace_identity_check(group, rep, tuple(Fraction(x) for x in triple))
    assert result["status"] == status


def test_trivial_digest_pins_flag_empty_input_digests() -> None:
    empty = hashlib.sha256(b"").hexdigest()
    brackets = hashlib.sha256(b"[]").hexdigest()
    real = hashlib.sha256(b"tokenizer bytes").hexdigest()
    pins = rv.trivial_digest_pins(
        {"tokenizer_json_sha256": empty, "template": brackets, "host": real}
    )
    assert pins == [
        {"field": "$.template", "digest_of": "[]"},
        {"field": "$.tokenizer_json_sha256", "digest_of": "empty bytes"},
    ]
