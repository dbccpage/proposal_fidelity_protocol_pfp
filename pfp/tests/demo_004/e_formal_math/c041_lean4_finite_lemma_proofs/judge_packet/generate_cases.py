# AuthorityEffect: None.
"""
Deterministic Case Generator for C041: Lean 4 Proofs of Hidden Finite Lemmas.

Generates:
1. 40 hidden base cases (8 per family):
   - Family 1: Fin arithmetic (zero divisors, ring identities, refutations).
   - Family 2: Bounded quantifiers (small N, refutations with counterexamples, large N).
   - Family 3: List properties (sortedness, length, reverse invariance, permutation).
   - Family 4: Finite operation tables (associativity, identity, quasigroups).
   - Family 5: Nested quantifiers over Fin (witness mappings, refutations).
2. 16 relabel & gauge invariance controls.
3. 8 poisoned schema-valid cases (ill-typed preludes, false notes).
4. 48 hostile mutation cases for mutation suite.
5. Computes SHA-256 manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))


CASES_DIR = Path(__file__).resolve().parent / "cases"
MUTATION_DIR = Path(__file__).resolve().parent / "mutation_suite"
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"


def generate_base_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    # --- Family 1: Fin Arithmetic (8 cases) ---
    # F1-01: Zero divisors in Fin 13 (field, no non-trivial zero divisors)
    cases.append(
        {
            "case_id": "c041_base_01",
            "family": "f1_arithmetic",
            "statement": "∀ a b : Fin 13, a * b = 0 → a = 0 ∨ b = 0",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F1-02: Zero divisors in Fin 12 (composite, has zero divisors: 3 * 4 = 0)
    cases.append(
        {
            "case_id": "c041_base_02",
            "family": "f1_arithmetic",
            "statement": "∀ a b : Fin 12, a * b = 0 → a = 0 ∨ b = 0",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F1-03: Commutativity of addition in Fin 37
    cases.append(
        {
            "case_id": "c041_base_03",
            "family": "f1_arithmetic",
            "statement": "∀ x y : Fin 37, x + y = y + x",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F1-04: False claim: addition is idempotent in Fin 7
    cases.append(
        {
            "case_id": "c041_base_04",
            "family": "f1_arithmetic",
            "statement": "∀ x : Fin 7, x + x = x",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F1-05: Distributivity in Fin 19
    cases.append(
        {
            "case_id": "c041_base_05",
            "family": "f1_arithmetic",
            "statement": "∀ a b c : Fin 19, a * (b + c) = a * b + a * c",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F1-06: Units in Fin 5: non-zero elements have inverses
    cases.append(
        {
            "case_id": "c041_base_06",
            "family": "f1_arithmetic",
            "statement": "∀ x : Fin 5, x ≠ 0 → ∃ y : Fin 5, x * y = 1",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F1-07: False claim: units in Fin 6: all non-zero have inverses
    cases.append(
        {
            "case_id": "c041_base_07",
            "family": "f1_arithmetic",
            "statement": "∀ x : Fin 6, x ≠ 0 → ∃ y : Fin 6, x * y = 1",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F1-08: Quadratic residue in Fin 11: 3 is not a square
    cases.append(
        {
            "case_id": "c041_base_08",
            "family": "f1_arithmetic",
            "statement": "∃ x : Fin 11, x * x = 3",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )

    # --- Family 2: Bounded Quantifiers (8 cases) ---
    # F2-01: Bounded Nat inequality (small N=50)
    cases.append(
        {
            "case_id": "c041_base_09",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Nat, k < 50 → k * k < 2600",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F2-02: Bounded Nat inequality refutation (N=50, fails at 40 since 40*40=1600 > 1500)
    cases.append(
        {
            "case_id": "c041_base_10",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Nat, k < 50 → k * k < 1500",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F2-03: Bounded Nat divisibility identity
    cases.append(
        {
            "case_id": "c041_base_11",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Nat, k < 30 → (k * 2) % 2 = 0",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F2-04: False parity property
    cases.append(
        {
            "case_id": "c041_base_12",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Nat, k < 30 → (k * k) % 2 = k % 2 + 1",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F2-05: Modulo bound over Fin 60
    cases.append(
        {
            "case_id": "c041_base_13",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Fin 60, (k.val + 5) - 5 = k.val",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F2-06: Off-by-one bound decoy in Fin 50
    cases.append(
        {
            "case_id": "c041_base_14",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ k : Fin 50, k.val + 1 < 50",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F2-07: Triangle inequality on Nat up to 40
    cases.append(
        {
            "case_id": "c041_base_15",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ a b : Nat, a < 40 → b < 40 → a ≤ a + b",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F2-08: False triangle claim
    cases.append(
        {
            "case_id": "c041_base_16",
            "family": "f2_bounded_quantifiers",
            "statement": "∀ a b : Nat, a < 40 → b < 40 → a + b < 70",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )

    # --- Family 3: List Properties (8 cases) ---
    f3_prelude = (
        "def l1 : List Nat := [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n"
        "def l2 : List Nat := [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]\n"
        "def l_odd : List Nat := [1, 3, 5, 7, 9]\n"
    )
    # F3-01: Length of list l1
    cases.append(
        {
            "case_id": "c041_base_17",
            "family": "f3_lists",
            "statement": "l1.length = 10",
            "prelude": f3_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F3-02: Reverse equality between l1 and l2
    cases.append(
        {
            "case_id": "c041_base_18",
            "family": "f3_lists",
            "statement": "l1.reverse = l2",
            "prelude": f3_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F3-03: False list equality
    cases.append(
        {
            "case_id": "c041_base_19",
            "family": "f3_lists",
            "statement": "l1 = l2",
            "prelude": f3_prelude,
            "expected_kind": "REFUTATION",
        }
    )
    # F3-04: Double reverse identity on l1
    cases.append(
        {
            "case_id": "c041_base_20",
            "family": "f3_lists",
            "statement": "l1.reverse.reverse = l1",
            "prelude": f3_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F3-05: Filter odd on l1 produces l_odd
    cases.append(
        {
            "case_id": "c041_base_21",
            "family": "f3_lists",
            "statement": "l1.filter (fun x => x % 2 == 1) = l_odd",
            "prelude": f3_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F3-06: False filter result
    cases.append(
        {
            "case_id": "c041_base_22",
            "family": "f3_lists",
            "statement": "l1.filter (fun x => x % 2 == 0) = l_odd",
            "prelude": f3_prelude,
            "expected_kind": "REFUTATION",
        }
    )
    # F3-07: Head of l1 is 1
    cases.append(
        {
            "case_id": "c041_base_23",
            "family": "f3_lists",
            "statement": "l1.head? = some 1",
            "prelude": f3_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F3-08: Head of l2 is not 1
    cases.append(
        {
            "case_id": "c041_base_24",
            "family": "f3_lists",
            "statement": "l2.head? = some 1",
            "prelude": f3_prelude,
            "expected_kind": "REFUTATION",
        }
    )

    # --- Family 4: Finite Operation Tables (8 cases) ---
    f4_prelude = (
        "def op_klein (a b : Fin 4) : Fin 4 :=\n"
        "  OfNat.ofNat (a.val ^^^ b.val)\n\n"
        "def op_cyclic (a b : Fin 4) : Fin 4 :=\n"
        "  OfNat.ofNat ((a.val + b.val) % 4)\n\n"
        "def op_nonassoc (a b : Fin 3) : Fin 3 :=\n"
        "  OfNat.ofNat ((a.val + 2 * b.val + 1) % 3)\n"
    )
    # F4-01: Klein four-group table is associative
    cases.append(
        {
            "case_id": "c041_base_25",
            "family": "f4_tables",
            "statement": "∀ a b c : Fin 4, op_klein (op_klein a b) c = op_klein a (op_klein b c)",
            "prelude": f4_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F4-02: Klein four-group element 0 is two-sided identity
    cases.append(
        {
            "case_id": "c041_base_26",
            "family": "f4_tables",
            "statement": "∀ a : Fin 4, op_klein a 0 = a ∧ op_klein 0 a = a",
            "prelude": f4_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F4-03: Klein four-group all elements are self-inverse
    cases.append(
        {
            "case_id": "c041_base_27",
            "family": "f4_tables",
            "statement": "∀ a : Fin 4, op_klein a a = 0",
            "prelude": f4_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F4-04: Cyclic 4 not all elements self-inverse
    cases.append(
        {
            "case_id": "c041_base_28",
            "family": "f4_tables",
            "statement": "∀ a : Fin 4, op_cyclic a a = 0",
            "prelude": f4_prelude,
            "expected_kind": "REFUTATION",
        }
    )
    # F4-05: Cyclic 4 table is associative
    cases.append(
        {
            "case_id": "c041_base_29",
            "family": "f4_tables",
            "statement": "∀ a b c : Fin 4, op_cyclic (op_cyclic a b) c = op_cyclic a (op_cyclic b c)",
            "prelude": f4_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F4-06: Non-associative operation is NOT associative
    cases.append(
        {
            "case_id": "c041_base_30",
            "family": "f4_tables",
            "statement": "∀ a b c : Fin 3, op_nonassoc (op_nonassoc a b) c = op_nonassoc a (op_nonassoc b c)",
            "prelude": f4_prelude,
            "expected_kind": "REFUTATION",
        }
    )
    # F4-07: Klein table is commutative
    cases.append(
        {
            "case_id": "c041_base_31",
            "family": "f4_tables",
            "statement": "∀ a b : Fin 4, op_klein a b = op_klein b a",
            "prelude": f4_prelude,
            "expected_kind": "PROOF",
        }
    )
    # F4-08: Nonassoc table is NOT commutative
    cases.append(
        {
            "case_id": "c041_base_32",
            "family": "f4_tables",
            "statement": "∀ a b : Fin 3, op_nonassoc a b = op_nonassoc b a",
            "prelude": f4_prelude,
            "expected_kind": "REFUTATION",
        }
    )

    # --- Family 5: Nested Quantifiers (8 cases) ---
    # F5-01: Every element in Fin 8 has a predecessor mod 8
    cases.append(
        {
            "case_id": "c041_base_33",
            "family": "f5_nested_quantifiers",
            "statement": "∀ x : Fin 8, ∃ y : Fin 8, y + 1 = x",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F5-02: False claim: every element in Fin 8 is its own square
    cases.append(
        {
            "case_id": "c041_base_34",
            "family": "f5_nested_quantifiers",
            "statement": "∀ x : Fin 8, ∃ y : Fin 8, x * y = x ∧ y = x",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F5-03: Squaring is surjective in Fin 2
    cases.append(
        {
            "case_id": "c041_base_35",
            "family": "f5_nested_quantifiers",
            "statement": "∀ y : Fin 2, ∃ x : Fin 2, x * x = y",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F5-04: Squaring is NOT surjective in Fin 5
    cases.append(
        {
            "case_id": "c041_base_36",
            "family": "f5_nested_quantifiers",
            "statement": "∀ y : Fin 5, ∃ x : Fin 5, x * x = y",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F5-05: Double negation over Bool
    cases.append(
        {
            "case_id": "c041_base_37",
            "family": "f5_nested_quantifiers",
            "statement": "∀ b : Bool, (!(!b)) = b",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F5-06: False boolean identity
    cases.append(
        {
            "case_id": "c041_base_38",
            "family": "f5_nested_quantifiers",
            "statement": "∀ a b : Bool, (a && b) = (a || b)",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # F5-07: De Morgan law on Bool
    cases.append(
        {
            "case_id": "c041_base_39",
            "family": "f5_nested_quantifiers",
            "statement": "∀ a b : Bool, (!(a && b)) = (!a || !b)",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # F5-08: False XOR identity
    cases.append(
        {
            "case_id": "c041_base_40",
            "family": "f5_nested_quantifiers",
            "statement": "∀ a b : Bool, (a != b) = (a == b)",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )

    return cases


def generate_control_cases() -> List[Dict[str, Any]]:
    """16 relabel and gauge invariance controls."""
    controls: List[Dict[str, Any]] = []

    # C01: Alpha rename base_01 (a b -> u v)
    controls.append(
        {
            "case_id": "c041_ctrl_01",
            "base_ref": "c041_base_01",
            "family": "control_relabel",
            "statement": "∀ u v : Fin 13, u * v = 0 → u = 0 ∨ v = 0",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C02: Alpha rename base_02 (a b -> m n)
    controls.append(
        {
            "case_id": "c041_ctrl_02",
            "base_ref": "c041_base_02",
            "family": "control_relabel",
            "statement": "∀ m n : Fin 12, m * n = 0 → m = 0 ∨ n = 0",
            "prelude": "",
            "expected_kind": "REFUTATION",
        }
    )
    # C03: Disjunction swap on base_01
    controls.append(
        {
            "case_id": "c041_ctrl_03",
            "base_ref": "c041_base_01",
            "family": "control_gauge",
            "statement": "∀ a b : Fin 13, a * b = 0 → b = 0 ∨ a = 0",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C04: Reordered conjunction in base_26
    controls.append(
        {
            "case_id": "c041_ctrl_04",
            "base_ref": "c041_base_26",
            "family": "control_gauge",
            "statement": "∀ a : Fin 4, op_klein 0 a = a ∧ op_klein a 0 = a",
            "prelude": ("def op_klein (a b : Fin 4) : Fin 4 :=\n  OfNat.ofNat (a.val ^^^ b.val)\n"),
            "expected_kind": "PROOF",
        }
    )
    # C05: Alpha rename base_03 (x y -> p q)
    controls.append(
        {
            "case_id": "c041_ctrl_05",
            "base_ref": "c041_base_03",
            "family": "control_relabel",
            "statement": "∀ p q : Fin 37, p + q = q + p",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C06: Alpha rename base_05 (a b c -> x y z)
    controls.append(
        {
            "case_id": "c041_ctrl_06",
            "base_ref": "c041_base_05",
            "family": "control_relabel",
            "statement": "∀ x y z : Fin 19, x * (y + z) = x * y + x * z",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C07: Transport base_17 list through named synonym
    controls.append(
        {
            "case_id": "c041_ctrl_07",
            "base_ref": "c041_base_17",
            "family": "control_relabel",
            "statement": "my_list.length = 10",
            "prelude": "def my_list : List Nat := [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n",
            "expected_kind": "PROOF",
        }
    )
    # C08: Bounded inequality rewritten with not-le
    controls.append(
        {
            "case_id": "c041_ctrl_08",
            "base_ref": "c041_base_09",
            "family": "control_gauge",
            "statement": "∀ k : Nat, ¬ (50 ≤ k) → k * k < 2600",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C09: Alpha rename base_33 (x y -> a b)
    controls.append(
        {
            "case_id": "c041_ctrl_09",
            "base_ref": "c041_base_33",
            "family": "control_relabel",
            "statement": "∀ a : Fin 8, ∃ b : Fin 8, b + 1 = a",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C10: Commutative rewrite on base_37 (b -> x)
    controls.append(
        {
            "case_id": "c041_ctrl_10",
            "base_ref": "c041_base_37",
            "family": "control_relabel",
            "statement": "∀ x : Bool, (!(!x)) = x",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C11: Conjunction swap in de Morgan
    controls.append(
        {
            "case_id": "c041_ctrl_11",
            "base_ref": "c041_base_39",
            "family": "control_gauge",
            "statement": "∀ a b : Bool, (!(a && b)) = (!b || !a)",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C12: Alpha rename base_35 (y x -> v u)
    controls.append(
        {
            "case_id": "c041_ctrl_12",
            "base_ref": "c041_base_35",
            "family": "control_relabel",
            "statement": "∀ v : Fin 2, ∃ u : Fin 2, u * u = v",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C13: Alpha rename base_27 (a -> x)
    controls.append(
        {
            "case_id": "c041_ctrl_13",
            "base_ref": "c041_base_27",
            "family": "control_relabel",
            "statement": "∀ x : Fin 4, op_klein x x = 0",
            "prelude": "def op_klein (a b : Fin 4) : Fin 4 := OfNat.ofNat (a.val ^^^ b.val)\n",
            "expected_kind": "PROOF",
        }
    )
    # C14: Reorder addition in base_15
    controls.append(
        {
            "case_id": "c041_ctrl_14",
            "base_ref": "c041_base_15",
            "family": "control_gauge",
            "statement": "∀ a b : Nat, a < 40 → b < 40 → a ≤ b + a",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C15: Alpha rename base_11 (k -> n)
    controls.append(
        {
            "case_id": "c041_ctrl_15",
            "base_ref": "c041_base_11",
            "family": "control_relabel",
            "statement": "∀ n : Nat, n < 30 → (n * 2) % 2 = 0",
            "prelude": "",
            "expected_kind": "PROOF",
        }
    )
    # C16: Alpha rename base_30 refutation (a b c -> u v w)
    controls.append(
        {
            "case_id": "c041_ctrl_16",
            "base_ref": "c041_base_30",
            "family": "control_relabel",
            "statement": "∀ u v w : Fin 3, op_nonassoc (op_nonassoc u v) w = op_nonassoc u (op_nonassoc v w)",
            "prelude": "def op_nonassoc (a b : Fin 3) : Fin 3 := OfNat.ofNat ((a.val + 2 * b.val + 1) % 3)\n",
            "expected_kind": "REFUTATION",
        }
    )

    return controls


def generate_poison_cases() -> List[Dict[str, Any]]:
    """8 poisoned but schema-valid cases."""
    poison: List[Dict[str, Any]] = []

    # P01: Ill-typed prelude (syntax error in definition)
    poison.append(
        {
            "case_id": "c041_poison_01",
            "family": "poison",
            "statement": "foo 5 = 10",
            "prelude": "def foo (n : Nat) : Nat := n + + 5\n",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # P02: Undefined identifier in statement
    poison.append(
        {
            "case_id": "c041_poison_02",
            "family": "poison",
            "statement": "nonexistent_func 3 = 6",
            "prelude": "",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # P03: False statement with a fraudulent note claiming it is true
    poison.append(
        {
            "case_id": "c041_poison_03",
            "family": "poison",
            "statement": "∀ a b : Fin 6, a * b = 0 → a = 0 ∨ b = 0",
            "prelude": "",
            "note": "Proven in paper lemma 4.2 to be true",
            "expected_status": "SOLVED",
            "expected_kind": "REFUTATION",
        }
    )
    # P04: Type error in prelude (Nat vs Bool mismatch)
    poison.append(
        {
            "case_id": "c041_poison_04",
            "family": "poison",
            "statement": "bad_type_fn 1 = true",
            "prelude": "def bad_type_fn (x : Nat) : Bool := x + 1\n",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # P05: False statement claiming idempotence with deceptive note
    poison.append(
        {
            "case_id": "c041_poison_05",
            "family": "poison",
            "statement": "∀ x : Fin 10, x + x = x",
            "prelude": "",
            "note": "Identity property on finite ring",
            "expected_status": "SOLVED",
            "expected_kind": "REFUTATION",
        }
    )
    # P06: Prelude containing unelaborable command
    poison.append(
        {
            "case_id": "c041_poison_06",
            "family": "poison",
            "statement": "1 + 1 = 2",
            "prelude": "import NonExistentModule\n",
            "expected_status": "OUT_OF_SCOPE",
        }
    )
    # P07: False statement: all elements in Fin 4 are zero divisors
    poison.append(
        {
            "case_id": "c041_poison_07",
            "family": "poison",
            "statement": "∀ x : Fin 4, x * x = 0",
            "prelude": "",
            "expected_status": "SOLVED",
            "expected_kind": "REFUTATION",
        }
    )
    # P08: False statement: list permutation claim on unequal lengths
    poison.append(
        {
            "case_id": "c041_poison_08",
            "family": "poison",
            "statement": "[1, 2].length = [1, 2, 3].length",
            "prelude": "",
            "expected_status": "SOLVED",
            "expected_kind": "REFUTATION",
        }
    )

    return poison


def generate_hostile_mutations(base_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generates 48 hostile mutation cases that checkers must reject."""
    mutations: List[Dict[str, Any]] = []

    m_idx = 1
    # 1. 10 mutations using `by sorry`
    for i in range(10):
        case = base_cases[i]
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "sorry_axiom",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": case.get("expected_kind", "PROOF"),
                    "aux": [],
                    "proof": "by sorry",
                },
                "expected_rejection": True,
                "reason": "Uses forbidden 'sorry'",
            }
        )
        m_idx += 1

    # 2. 10 mutations using `by native_decide`
    for i in range(10):
        case = base_cases[i + 10]
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "native_decide_axiom",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": case.get("expected_kind", "PROOF"),
                    "aux": [],
                    "proof": "by native_decide",
                },
                "expected_rejection": True,
                "reason": "Uses unverified 'native_decide'",
            }
        )
        m_idx += 1

    # 3. 8 mutations with illicit aux commands (axiom, opaque, unsafe def)
    for i in range(8):
        case = base_cases[i + 20]
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "illicit_aux_command",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": case.get("expected_kind", "PROOF"),
                    "aux": ["axiom illicit_oracle : 1 = 1"],
                    "proof": "by decide",
                },
                "expected_rejection": True,
                "reason": "Auxiliary declaration contains forbidden 'axiom'",
            }
        )
        m_idx += 1

    # 4. 8 mutations submitting wrong kind (PROOF for REFUTATION or vice versa)
    for i in range(8):
        case = base_cases[i + 28]
        orig_kind = case.get("expected_kind", "PROOF")
        flipped_kind = "REFUTATION" if orig_kind == "PROOF" else "PROOF"
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "flipped_kind_lie",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": flipped_kind,
                    "aux": [],
                    "proof": "by decide",
                },
                "expected_rejection": True,
                "reason": f"Flipped kind from {orig_kind} to {flipped_kind}",
            }
        )
        m_idx += 1

    # 5. 6 mutations with set_option or macro attributes
    for i in range(6):
        case = base_cases[i]
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "banned_attribute",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": case.get("expected_kind", "PROOF"),
                    "aux": ["set_option maxHeartbeats 0"],
                    "proof": "by decide",
                },
                "expected_rejection": True,
                "reason": "Contains forbidden 'set_option'",
            }
        )
        m_idx += 1

    # 6. 6 mutations with ID mismatch or empty proof
    for i in range(6):
        case = base_cases[i + 6]
        mutations.append(
            {
                "mutation_id": f"mut_{m_idx:02d}",
                "type": "empty_proof",
                "case": case,
                "answer": {
                    "case_id": case["case_id"],
                    "status": "SOLVED",
                    "kind": case.get("expected_kind", "PROOF"),
                    "aux": [],
                    "proof": "   ",
                },
                "expected_rejection": True,
                "reason": "Empty proof body",
            }
        )
        m_idx += 1

    return mutations


def main() -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    MUTATION_DIR.mkdir(parents=True, exist_ok=True)

    base_cases = generate_base_cases()
    control_cases = generate_control_cases()
    poison_cases = generate_poison_cases()
    all_judge_cases = base_cases + control_cases + poison_cases

    print(
        f"Generated {len(base_cases)} base cases, {len(control_cases)} controls, {len(poison_cases)} poison cases."
    )
    print(f"Total judge cases: {len(all_judge_cases)}")

    # Write each judge case
    for case in all_judge_cases:
        cid = case["case_id"]
        cpath = CASES_DIR / f"{cid}.json"
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, sort_keys=True)

    # Generate mutations
    mutations = generate_hostile_mutations(base_cases)
    print(f"Generated {len(mutations)} hostile mutations.")
    for mut in mutations:
        mid = mut["mutation_id"]
        mpath = MUTATION_DIR / f"{mid}.json"
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(mut, f, indent=2, sort_keys=True)

    # Build manifest
    manifest_entries = {}
    for cfile in sorted(CASES_DIR.glob("*.json")):
        content = cfile.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        rel_path = str(cfile.relative_to(_pkg_root)).replace("\\", "/")
        manifest_entries[rel_path] = {
            "sha256": sha,
            "size_bytes": len(content),
        }

    for mfile in sorted(MUTATION_DIR.glob("*.json")):
        content = mfile.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        rel_path = str(mfile.relative_to(_pkg_root)).replace("\\", "/")
        manifest_entries[rel_path] = {
            "sha256": sha,
            "size_bytes": len(content),
        }

    manifest = {
        "challenge_id": "c041_lean4_finite_lemma_proofs",
        "toolchain": "leanprover/lean4:v4.34.1",
        "case_count": len(all_judge_cases),
        "mutation_count": len(mutations),
        "total_files": len(manifest_entries),
        "entries": manifest_entries,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"Wrote manifest with {len(manifest_entries)} hashed entries to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
