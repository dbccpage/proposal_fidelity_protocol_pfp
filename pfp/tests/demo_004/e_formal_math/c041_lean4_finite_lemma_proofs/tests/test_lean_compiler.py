# AuthorityEffect: None.
"""Tests for Lean 4 compiler wrapper and diagnostic/axiom parser."""

from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import (
    WHITELISTED_AXIOMS,
    compile_lean4_code,
)


def test_clean_lean4_elaboration():
    code = "theorem test_rfl : 10 + 10 = 20 := by rfl\n#print axioms test_rfl"
    res = compile_lean4_code(code, target_name="test_rfl")
    assert res.success is True
    assert res.return_code == 0
    assert res.axioms == []
    assert len(res.errors) == 0


def test_banned_token_detection():
    # Detects sorry
    res_sorry = compile_lean4_code("theorem foo : 1 = 2 := by sorry")
    assert res_sorry.success is False
    assert "sorry" in res_sorry.banned_tokens_found

    # Detects native_decide
    res_native = compile_lean4_code("theorem foo : 1 = 1 := by native_decide")
    assert res_native.success is False
    assert "native_decide" in res_native.banned_tokens_found

    # Detects axiom command
    res_ax = compile_lean4_code("axiom bad : False")
    assert res_ax.success is False
    assert "axiom" in res_ax.banned_tokens_found

    # Detects unsafe modifier
    res_unsafe = compile_lean4_code("unsafe def bad_fn : Nat := 0")
    assert res_unsafe.success is False
    assert "unsafe" in res_unsafe.banned_tokens_found


def test_axiom_parsing_whitelisted():
    code = "theorem prop_eq (p q : Prop) (h : p ↔ q) : p = q := propext h\n#print axioms prop_eq"
    res = compile_lean4_code(code, target_name="prop_eq")
    assert res.success is True
    assert "propext" in res.axioms
    disallowed = set(res.axioms) - WHITELISTED_AXIOMS
    assert len(disallowed) == 0


def test_syntax_error_diagnostics():
    bad_code = "def ill_formed (x : Nat) : Bool := x + 1"
    res = compile_lean4_code(bad_code)
    assert res.success is False
    assert len(res.errors) > 0
