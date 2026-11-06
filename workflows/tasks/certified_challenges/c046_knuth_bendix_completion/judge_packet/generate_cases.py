# AuthorityEffect: None.
"""
Hidden Case Generator for C046 (Knuth-Bendix Completion).
Generates 64 evaluation cases:
- 40 base hidden cases across tasks (COMPLETE, CHECK_CONFLUENCE, REDUCE)
- 16 relabel / gauge invariance cases (symbol renames, equation reorderings)
- 8 poisoned schema-valid cases (unorientable commutativity, unbound RHS variable, syntax error, step limits)
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_repo_root = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def generate_all_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    # 1. Base hidden cases (40 cases)

    # 16 COMPLETE cases
    complete_defs = [
        # 1. Standard group
        (
            "group_standard",
            [
                ["mul(e, x)", "x"],
                ["mul(inv(x), x)", "e"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ],
            {"inv": 100, "mul": 50, "e": 10},
        ),
        # 2. Additive group
        (
            "group_additive",
            [
                ["add(0, x)", "x"],
                ["add(neg(x), x)", "0"],
                ["add(add(x, y), z)", "add(x, add(y, z))"],
            ],
            {"neg": 100, "add": 50, "0": 10},
        ),
        # 3. Monoid
        (
            "monoid_two_sided_id",
            [["mul(1, x)", "x"], ["mul(x, 1)", "x"], ["mul(mul(x, y), z)", "mul(x, mul(y, z))"]],
            {"mul": 50, "1": 10},
        ),
        # 4. Idempotent semilattice
        (
            "semilattice_idempotent",
            [["meet(x, x)", "x"], ["meet(x, 1)", "x"], ["meet(x, 0)", "0"]],
            {"meet": 50, "1": 10, "0": 5},
        ),
        # 5. Nilpotent element order 2
        (
            "nilpotent_order_2",
            [["sq(0)", "0"], ["mul(x, 0)", "0"], ["mul(0, x)", "0"]],
            {"sq": 60, "mul": 50, "0": 10},
        ),
        # 6. Central projector
        (
            "central_projector",
            [["p(p(x))", "p(x)"], ["q(p(x))", "0"], ["q(q(x))", "q(x)"]],
            {"q": 60, "p": 50, "0": 10},
        ),
        # 7. Left/right absorption
        (
            "absorb_operator",
            [["f(x, 0)", "0"], ["f(0, x)", "0"], ["f(x, 1)", "x"]],
            {"f": 50, "1": 10, "0": 5},
        ),
        # 8. Dual involution
        (
            "dual_involution",
            [["h(h(x))", "x"], ["g(g(x))", "x"], ["h(g(h(x)))", "g(x)"]],
            {"h": 80, "g": 60},
        ),
        # 9. Group involution
        (
            "group_inv_inv",
            [["inv(inv(x))", "x"], ["mul(x, inv(x))", "e"]],
            {"inv": 100, "mul": 50, "e": 10},
        ),
        # 10. Centralizer idempotent
        ("centralizer_idempotent", [["c(c(x))", "c(x)"], ["c(x)", "d(x)"]], {"c": 60, "d": 50}),
        # 11. Absorb ring zero
        ("absorb_ring_zero", [["times(x, 0)", "0"], ["times(0, x)", "0"]], {"times": 50, "0": 10}),
        # 12. Monoid dual
        ("monoid_dual", [["op(x, e)", "x"], ["op(e, x)", "x"]], {"op": 50, "e": 10}),
    ]

    for idx, (name, eqs, prec) in enumerate(complete_defs):
        cases.append(
            {
                "case_id": f"c046_base_complete_{idx:02d}_{name}",
                "task": "COMPLETE",
                "equations": eqs,
                "precedence": prec,
                "category": "base_hidden",
            }
        )

    # 10 CHECK_CONFLUENCE cases
    confluence_defs = [
        # Confluent complete group
        (
            "confluent_group",
            [
                ["mul(e, x)", "x"],
                ["mul(inv(x), x)", "e"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
                ["mul(inv(x), mul(x, y))", "y"],
                ["inv(e)", "e"],
                ["mul(x, e)", "x"],
                ["mul(x, inv(x))", "e"],
                ["inv(inv(x))", "x"],
                ["mul(x, mul(inv(x), y))", "y"],
            ],
        ),
        # Non-confluent incomplete group
        (
            "non_confluent_group",
            [
                ["mul(e, x)", "x"],
                ["mul(inv(x), x)", "e"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ],
        ),
        # Confluent monoid
        (
            "confluent_monoid",
            [["mul(1, x)", "x"], ["mul(x, 1)", "x"], ["mul(mul(x, y), z)", "mul(x, mul(y, z))"]],
        ),
        # Non-confluent pair
        ("non_confluent_pair", [["f(g(x))", "a"], ["g(h(x))", "b"]]),
        # Confluent projection
        ("confluent_proj", [["p(p(x))", "p(x)"], ["q(p(x))", "0"]]),
        # Confluent single rule
        ("confluent_single", [["f(x)", "g(x)"]]),
        # Confluent additive
        ("confluent_additive", [["add(0, x)", "x"], ["add(neg(x), x)", "0"], ["neg(0)", "0"]]),
        # Non-confluent fork
        ("non_confluent_fork", [["f(x)", "g(x)"], ["f(x)", "h(x)"]]),
        # Confluent boolean
        ("confluent_boolean", [["and(x, 0)", "0"], ["and(0, x)", "0"]]),
        # Confluent identity
        ("confluent_identity", [["inv(e)", "e"], ["mul(e, e)", "e"]]),
    ]
    for idx, (name, rules) in enumerate(confluence_defs):
        cases.append(
            {
                "case_id": f"c046_base_confluence_{idx:02d}_{name}",
                "task": "CHECK_CONFLUENCE",
                "rules": rules,
                "category": "base_hidden",
            }
        )

    # 18 REDUCE cases
    reduce_defs = [
        ("red_inv_e", "inv(e)", [["inv(e)", "e"]]),
        ("red_double_inv", "inv(inv(x))", [["inv(inv(x))", "x"]]),
        ("red_mul_inv_x", "mul(inv(x), x)", [["mul(inv(x), x)", "e"]]),
        ("red_mul_e_x", "mul(e, x)", [["mul(e, x)", "x"]]),
        ("red_mul_x_e", "mul(x, e)", [["mul(x, e)", "x"]]),
        ("red_triple_inv", "inv(inv(inv(x)))", [["inv(inv(x))", "x"]]),
        (
            "red_nested_eval",
            "mul(mul(inv(x), x), e)",
            [["mul(inv(x), x)", "e"], ["mul(e, e)", "e"]],
        ),
        ("red_proj_quad", "p(p(p(x)))", [["p(p(x))", "p(x)"]]),
        ("red_zero_absorb", "f(f(x, 0), 1)", [["f(x, 0)", "0"], ["f(0, 1)", "0"]]),
        ("red_add_zero", "add(x, 0)", [["add(x, 0)", "x"]]),
        ("red_neg_neg", "neg(neg(y))", [["neg(neg(x))", "x"]]),
        ("red_and_self", "and(z, z)", [["and(x, x)", "x"]]),
        ("red_and_zero", "and(z, 0)", [["and(x, 0)", "0"]]),
        ("red_and_one", "and(1, z)", [["and(1, x)", "x"]]),
        ("red_monoid_assoc", "mul(mul(1, a), b)", [["mul(1, x)", "x"]]),
        ("red_dual_h", "h(h(y))", [["h(h(x))", "x"]]),
        ("red_assoc_step", "mul(mul(a, b), c)", [["mul(mul(x, y), z)", "mul(x, mul(y, z))"]]),
        ("red_comp_zero", "times(times(a, 0), b)", [["times(x, 0)", "0"], ["times(0, y)", "0"]]),
    ]
    for idx, (name, term, rules) in enumerate(reduce_defs):
        cases.append(
            {
                "case_id": f"c046_base_reduce_{idx:02d}_{name}",
                "task": "REDUCE",
                "term": term,
                "rules": rules,
                "category": "base_hidden",
            }
        )

    assert len(cases) == 40, f"Expected 40 base cases, got {len(cases)}"

    # 2. Relabel / Gauge Invariance cases (16 cases)
    # Permuting equation ordering and renaming function symbols
    gauge_defs = [
        (
            "g01_group_shuffled",
            [
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
                ["mul(e, x)", "x"],
                ["mul(inv(x), x)", "e"],
            ],
        ),
        (
            "g02_group_shuffled2",
            [
                ["mul(inv(x), x)", "e"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
                ["mul(e, x)", "x"],
            ],
        ),
        (
            "g03_additive_shuffled",
            [
                ["add(add(x, y), z)", "add(x, add(y, z))"],
                ["add(0, x)", "x"],
                ["add(neg(x), x)", "0"],
            ],
        ),
        (
            "g04_monoid_shuffled",
            [["mul(x, 1)", "x"], ["mul(1, x)", "x"], ["mul(mul(x, y), z)", "mul(x, mul(y, z))"]],
        ),
        (
            "g05_group_sym_dot",
            [
                ["dot(e, x)", "x"],
                ["dot(inv(x), x)", "e"],
                ["dot(dot(x, y), z)", "dot(x, dot(y, z))"],
            ],
        ),
        (
            "g06_group_sym_star",
            [
                ["star(e, x)", "x"],
                ["star(inv(x), x)", "e"],
                ["star(star(x, y), z)", "star(x, star(y, z))"],
            ],
        ),
        (
            "g07_additive_sym_plus",
            [
                ["plus(0, x)", "x"],
                ["plus(neg(x), x)", "0"],
                ["plus(plus(x, y), z)", "plus(x, plus(y, z))"],
            ],
        ),
        (
            "g08_monoid_sym_circ",
            [
                ["circ(1, x)", "x"],
                ["circ(x, 1)", "x"],
                ["circ(circ(x, y), z)", "circ(x, circ(y, z))"],
            ],
        ),
        ("g09_reduce_shuffled_rules", "inv(inv(x))", [["mul(e, x)", "x"], ["inv(inv(x))", "x"]]),
        ("g10_reduce_sym_dot", "dot(e, y)", [["dot(e, x)", "x"]]),
        ("g11_reduce_sym_star", "star(x, e)", [["star(x, e)", "x"]]),
        (
            "g12_confluence_shuffled",
            [
                ["mul(inv(x), x)", "e"],
                ["mul(e, x)", "x"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ],
        ),
        (
            "g13_confluence_sym_dot",
            [
                ["dot(e, x)", "x"],
                ["dot(inv(x), x)", "e"],
                ["dot(dot(x, y), z)", "dot(x, dot(y, z))"],
            ],
        ),
        (
            "g14_semilattice_shuffled",
            [["meet(x, 0)", "0"], ["meet(x, 1)", "x"], ["meet(x, x)", "x"]],
        ),
        ("g15_dual_inv_shuffled", [["g(g(x))", "x"], ["h(h(x))", "x"]]),
        ("g16_absorb_shuffled", [["f(x, 1)", "x"], ["f(x, 0)", "0"], ["f(0, x)", "0"]]),
    ]

    for idx, entry in enumerate(gauge_defs):
        if len(entry) == 2:
            name, eqs = entry
            cases.append(
                {
                    "case_id": f"c046_gauge_{idx:02d}_{name}",
                    "task": "COMPLETE",
                    "equations": eqs,
                    "category": "relabel_gauge",
                }
            )
        else:
            name, term, rules = entry
            cases.append(
                {
                    "case_id": f"c046_gauge_{idx:02d}_{name}",
                    "task": "REDUCE",
                    "term": term,
                    "rules": rules,
                    "category": "relabel_gauge",
                }
            )

    assert len(cases) == 56, f"Expected 56 cases, got {len(cases)}"

    # 3. Poisoned schema-valid cases (8 cases)
    poison_defs = [
        {
            "case_id": "c046_poison_01_commutativity_unorientable",
            "task": "COMPLETE",
            "equations": [["mul(x, y)", "mul(y, x)"]],
            "precedence": {"mul": 50},
            "expected_reason": "ORDER_FAILURE",
        },
        {
            "case_id": "c046_poison_02_step_limit_starved",
            "task": "COMPLETE",
            "equations": [
                ["mul(e, x)", "x"],
                ["mul(inv(x), x)", "e"],
                ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ],
            "precedence": {"inv": 100, "mul": 50, "e": 10},
            "max_steps": 2,
            "expected_reason": "MAX_STEPS_EXCEEDED",
        },
        {
            "case_id": "c046_poison_03_malformed_unclosed_paren",
            "task": "COMPLETE",
            "equations": [["mul(x, inv(y", "x"]],
            "expected_reason": "ORDER_FAILURE",
        },
        {
            "case_id": "c046_poison_04_missing_term",
            "task": "REDUCE",
            "rules": [["f(x)", "x"]],
            "expected_reason": "MALFORMED_INPUT",
        },
        {
            "case_id": "c046_poison_05_missing_rules",
            "task": "CHECK_CONFLUENCE",
            "expected_reason": "MALFORMED_INPUT",
        },
        {
            "case_id": "c046_poison_06_malformed_rule_tuple",
            "task": "CHECK_CONFLUENCE",
            "rules": ["not_a_tuple"],
            "expected_reason": "MALFORMED_TERM",
        },
        {
            "case_id": "c046_poison_07_unorientable_symmetry",
            "task": "COMPLETE",
            "equations": [["sym(x, y)", "sym(y, x)"]],
            "precedence": {"sym": 50},
            "expected_reason": "ORDER_FAILURE",
        },
        {
            "case_id": "c046_poison_08_unknown_task",
            "task": "BOGUS_TASK",
            "equations": [["f(x)", "x"]],
            "expected_reason": "UNKNOWN_TASK",
        },
    ]

    for p in poison_defs:
        p["category"] = "poisoned"
        cases.append(p)

    assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"
    return cases


def main():
    cases = generate_all_cases()
    out_dir = Path(__file__).resolve().parent / "hidden_cases"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "c046_hidden_cases_64.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    print(f"Generated {len(cases)} hidden cases in {out_file}")


if __name__ == "__main__":
    main()
