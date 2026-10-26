"""
Tests for the Paper 033 practitioner toolkit (§4 scaffold, §7 runner).
"""

from symbol_game_toolkit import (
    CLOSED_OPERATORS,
    prompt_scaffold,
    run_to_terminal,
)


def test_prompt_scaffold_has_eight_surfaces_and_closed_ops():
    s = prompt_scaffold(["a", "b", "c"], ["R"], "REDUCE holonomy on a->b->c->a")
    for surface in ("[SYSTEM", "[K: CARRIER", "[VOCABULARY]", "[GLYPH CALCULUS]",
                    "[LAWS/AXIOMS]", "[REFUSALS]", "[D: ACTIVE DEMAND]", "[TAU]"):
        assert surface in s
    for op in CLOSED_OPERATORS:
        assert op in s
    assert "a, b, c" in s


def test_run_to_terminal_reaches_zero_defect_on_holonomy(native_functional):
    r = run_to_terminal(
        ["a", "b", "c"],
        [("a", "b", 1), ("b", "c", 2), ("c", "a", 2)],
        {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
    )
    assert r["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert r["final_phi1"] == "0"
    moves = [s["move"] for s in r["trace"]]
    assert moves.count("ASSERT") == 3
    assert "CUT" in moves
    assert moves[-1] == "VERIFY"


def test_run_to_terminal_coboundary_target_needs_no_cut(native_functional):
    # claims (1, -1, 0) = delta(c0) for c0 = (0, 1, 0): already a coboundary, Phi_1 = 0.
    r = run_to_terminal(
        ["a", "b", "c"],
        [("a", "b", 1), ("b", "c", 1), ("c", "a", 1)],
        {("a", "b"): 1, ("b", "c"): -1, ("c", "a"): 0},
    )
    assert r["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert r["final_phi1"] == "0"
    assert "CUT" not in [s["move"] for s in r["trace"]]
