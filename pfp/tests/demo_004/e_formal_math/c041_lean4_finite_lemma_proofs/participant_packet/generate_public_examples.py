# AuthorityEffect: None.
"""
Public Examples Generator for C041: Lean 4 Proofs of Hidden Finite Lemmas.

Generates 12 representative public examples across all strata:
1. 3 closed by decide (Fin arithmetic, Bool, parity)
2. 3 Nat inequalities / bounds
3. 2 refutations (false arithmetic, false list property)
4. 2 operation tables (Klein 4-group, cyclic 4)
5. 1 native_decide trap with whitelisted proof
6. 1 UNKNOWN / OUT_OF_SCOPE example
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual  # noqa: E402
from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.solver import solve  # noqa: E402

EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"
ANSWERS_PATH = Path(__file__).resolve().parent / "answers.jsonl"


def generate_public_examples() -> List[Dict[str, Any]]:
    examples = [
        # 1. decide proof: Fin 5 commutativity
        {
            "case_id": "c041_pub_01",
            "statement": "∀ a b : Fin 5, a + b = b + a",
            "prelude": "",
            "family": "f1_arithmetic",
            "description": "Small Fin arithmetic commutativity closed by decide.",
        },
        # 2. decide proof: Fin 7 zero divisors
        {
            "case_id": "c041_pub_02",
            "statement": "∀ a b : Fin 7, a * b = 0 → a = 0 ∨ b = 0",
            "prelude": "",
            "family": "f1_arithmetic",
            "description": "Prime field Fin 7 has no non-trivial zero divisors.",
        },
        # 3. decide proof: Bool identity
        {
            "case_id": "c041_pub_03",
            "statement": "∀ b : Bool, (b && true) = b",
            "prelude": "",
            "family": "f5_nested_quantifiers",
            "description": "Basic Boolean truth table identity.",
        },
        # 4. Nat bound: Small bounded quantifier
        {
            "case_id": "c041_pub_04",
            "statement": "∀ k : Nat, k < 25 → k + 0 = k",
            "prelude": "",
            "family": "f2_bounded_quantifiers",
            "description": "Bounded quantifier Nat identity.",
        },
        # 5. Nat bound: Inequality
        {
            "case_id": "c041_pub_05",
            "statement": "∀ k : Nat, k < 20 → k * 2 < 50",
            "prelude": "",
            "family": "f2_bounded_quantifiers",
            "description": "Bounded quantifier inequality.",
        },
        # 6. Nat bound: Modulo
        {
            "case_id": "c041_pub_06",
            "statement": "∀ k : Nat, k < 15 → (k * 4) % 4 = 0",
            "prelude": "",
            "family": "f2_bounded_quantifiers",
            "description": "Bounded quantifier modulo property.",
        },
        # 7. Refutation: Fin 6 zero divisors exist
        {
            "case_id": "c041_pub_07",
            "statement": "∀ a b : Fin 6, a * b = 0 → a = 0 ∨ b = 0",
            "prelude": "",
            "family": "f1_arithmetic",
            "description": "False statement requiring refutation: Fin 6 has 2*3=0.",
        },
        # 8. Refutation: False list equality
        {
            "case_id": "c041_pub_08",
            "statement": "[1, 2, 3] = [3, 2, 1]",
            "prelude": "",
            "family": "f3_lists",
            "description": "False list equality requiring refutation.",
        },
        # 9. Table property: Klein 4-group associativity
        {
            "case_id": "c041_pub_09",
            "statement": "∀ a b c : Fin 4, op_k (op_k a b) c = op_k a (op_k b c)",
            "prelude": "def op_k (a b : Fin 4) : Fin 4 := OfNat.ofNat (a.val ^^^ b.val)\n",
            "family": "f4_tables",
            "description": "XOR-based Klein 4-group associativity.",
        },
        # 10. Table property: Cyclic 4 identity
        {
            "case_id": "c041_pub_10",
            "statement": "∀ a : Fin 4, op_c a 0 = a ∧ op_c 0 a = a",
            "prelude": "def op_c (a b : Fin 4) : Fin 4 := OfNat.ofNat ((a.val + b.val) % 4)\n",
            "family": "f4_tables",
            "description": "Cyclic 4-group identity check.",
        },
        # 11. Native decide trap: whitelisted decide proof
        {
            "case_id": "c041_pub_11",
            "statement": "∀ a : Fin 16, a * 0 = 0",
            "prelude": "",
            "family": "f1_arithmetic",
            "description": "Tempting for native_decide, but closed cleanly by decide without Lean.ofReduceBool.",
        },
        # 12. OUT_OF_SCOPE example: unelaborable prelude
        {
            "case_id": "c041_pub_12",
            "statement": "bad_fun 1 = 2",
            "prelude": "def bad_fun (x : Nat) : Nat := x + + 1\n",
            "family": "out_of_scope",
            "description": "Ill-typed prelude causing elaboration failure.",
        },
    ]
    return examples


def main() -> None:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    examples = generate_public_examples()

    answers = []
    print(f"Generating and verifying {len(examples)} public examples...")

    for ex in examples:
        cid = ex["case_id"]
        # Save individual example JSON
        ex_path = EXAMPLES_DIR / f"{cid}.json"
        with open(ex_path, "w", encoding="utf-8") as f:
            json.dump(ex, f, indent=2, sort_keys=True)

        # Solve via reference solver
        ans = solve(ex)
        answers.append(ans)

        # Verify consensus
        ok, msg, meta = evaluate_dual(ex, ans)
        # A refusal never verifies; an OUT_OF_SCOPE example must at least be warranted.
        warranted_refusal = (
            ans.get("status") == "OUT_OF_SCOPE" and meta.get("outcome") == "WARRANTED_REFUSAL"
        )
        if not ok and not warranted_refusal:
            print(f"ERROR: Example {cid} failed verification: {msg}")
            sys.exit(1)
        print(f"Verified {cid}: status={ans.get('status')} kind={ans.get('kind', 'N/A')}")

    # Write answers.jsonl
    with open(ANSWERS_PATH, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(json.dumps(ans, sort_keys=True) + "\n")

    print(f"Successfully generated 12 examples and {ANSWERS_PATH}")


if __name__ == "__main__":
    main()
