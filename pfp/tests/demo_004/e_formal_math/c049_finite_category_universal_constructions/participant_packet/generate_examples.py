import json
import os

from pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.reference_solver import (
    solve,
)

out_dir = "projects/mssn_sn_symgam/challenges/e_formal_math/c049_finite_category_universal_constructions/participant_packet/examples"
os.makedirs(out_dir, exist_ok=True)

examples = [
    # 1. Product in poset
    {
        "case_id": "ex_01_product",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["p", "0", "1"],
            ["q", "0", "2"],
        ],
        "comp": {"id1": {"p": "p"}, "id2": {"q": "q"}},
        "diagram": ["1", "2"],
    },
    # 2. Equalizer of parallel pair
    {
        "case_id": "ex_02_equalizer",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["e", "0", "1"],
            ["f", "1", "2"],
            ["g", "1", "2"],
            ["fe", "0", "2"],
        ],
        "comp": {"f": {"e": "fe"}, "g": {"e": "fe"}},
        "diagram": ["f", "g"],
    },
    # 3. Pullback of cospan
    {
        "case_id": "ex_03_pullback",
        "task": "LIMIT",
        "shape": "pullback",
        "objects": ["0", "1", "2", "3"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["id3", "3", "3"],
            ["p1", "0", "1"],
            ["p2", "0", "2"],
            ["f", "1", "3"],
            ["g", "2", "3"],
            ["fp1", "0", "3"],
        ],
        "comp": {"f": {"p1": "fp1"}, "g": {"p2": "fp1"}},
        "diagram": ["f", "g"],
    },
    # 4. Monoid with no product (DOES_NOT_EXIST)
    {
        "case_id": "ex_04_monoid_no_product",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"]],
        "comp": {"a": {"a": "id0"}},  # Z_2 monoid
        "diagram": ["0", "0"],
    },
    # 5. Pushout of span
    {
        "case_id": "ex_05_pushout",
        "task": "COLIMIT",
        "shape": "pushout",
        "objects": ["0", "1", "2", "3"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["id3", "3", "3"],
            ["f", "0", "1"],
            ["g", "0", "2"],
            ["i1", "1", "3"],
            ["i2", "2", "3"],
            ["i1f", "0", "3"],
        ],
        "comp": {"i1": {"f": "i1f"}, "i2": {"g": "i1f"}},
        "diagram": ["f", "g"],
    },
    # 6. Terminal object
    {
        "case_id": "ex_06_terminal",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {"id1": {"f": "f"}},
        "diagram": [],
    },
    # 7. Initial object
    {
        "case_id": "ex_07_initial",
        "task": "COLIMIT",
        "shape": "initial",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {"id1": {"f": "f"}},
        "diagram": [],
    },
    # 8. Coproduct
    {
        "case_id": "ex_08_coproduct",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["i1", "0", "2"],
            ["i2", "1", "2"],
        ],
        "comp": {},
        "diagram": ["0", "1"],
    },
    # 9. Non-adjoint pair with cardinality witness
    {
        "case_id": "ex_09_non_adjoint_cardinality",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"], ["g", "0", "1"]],
            "comp": {},
        },
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {
            "objects": {"0": "0", "1": "0"},
            "morphisms": {"id0": "id0", "id1": "id0", "f": "id0", "g": "id0"},
        },
    },
    # 10. Adjoint pair (identity functors)
    {
        "case_id": "ex_10_adjoint_pair",
        "task": "ADJUNCTION",
        "category_C": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
            "comp": {},
        },
        "category_D": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
            "comp": {},
        },
        "F": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1", "f": "f"}},
        "G": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1", "f": "f"}},
    },
    # 11. Non-associative table (OUT_OF_SCOPE)
    {
        "case_id": "ex_11_non_associative",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["b", "0", "0"], ["c", "0", "0"]],
        "comp": {"a": {"b": "c"}, "b": {"c": "a"}},
        "diagram": ["0", "0"],
    },
    # 12. Empty diagram limit
    {
        "case_id": "ex_12_empty_limit",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"]],
        "comp": {},
        "diagram": [],
    },
]

for ex in examples:
    res = solve(ex)
    print(
        f"{ex['case_id']}: status={res.get('status')} kind={res.get('kind')} apex={res.get('apex')}"
    )
    path = os.path.join(out_dir, f"{ex['case_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"input": ex, "expected": res}, f, indent=2)

print("Generated 12 public worked examples successfully.")
