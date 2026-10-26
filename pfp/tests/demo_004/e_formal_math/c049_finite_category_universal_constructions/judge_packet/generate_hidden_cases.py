"""Generate 64 hidden evaluation cases for C049 Judge Packet.
Includes 40 base cases, 16 relabel/duality controls, and 8 poisoned cases.
"""

import json
import os

cases_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
os.makedirs(cases_dir, exist_ok=True)

cases = []


# Helper to construct a discrete category
def make_discrete(n):
    objs = [str(i) for i in range(n)]
    mors = [[f"id{i}", str(i), str(i)] for i in range(n)]
    return objs, mors, {}


# Helper to construct linear poset 0 -> 1 -> ... -> n-1
def make_linear_poset(n):
    objs = [str(i) for i in range(n)]
    mors = []
    comp = {}
    for i in range(n):
        mors.append([f"id{i}", str(i), str(i)])
    for i in range(n):
        for j in range(i + 1, n):
            mors.append([f"f_{i}_{j}", str(i), str(j)])
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                g = f"f_{j}_{k}"
                f = f"f_{i}_{j}"
                gf = f"f_{i}_{k}"
                if g not in comp:
                    comp[g] = {}
                comp[g][f] = gf
    return objs, mors, comp


# 1-12: Limit / Colimit existing cases (12 cases)
# 1: Poset product
objs3, mors3, comp3 = make_linear_poset(3)
cases.append(
    {
        "case_id": "c049_base_01_product_poset_3",
        "task": "LIMIT",
        "shape": "product",
        "objects": objs3,
        "morphisms": mors3,
        "comp": comp3,
        "diagram": ["1", "2"],
    }
)

# 2: Poset product of 4
objs4, mors4, comp4 = make_linear_poset(4)
cases.append(
    {
        "case_id": "c049_base_02_product_poset_4",
        "task": "LIMIT",
        "shape": "product",
        "objects": objs4,
        "morphisms": mors4,
        "comp": comp4,
        "diagram": ["2", "3"],
    }
)

# 3: Equalizer trivial (equal morphisms)
cases.append(
    {
        "case_id": "c049_base_03_equalizer_same",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {},
        "diagram": ["f", "f"],
    }
)

# 4: Equalizer non-trivial parallel pair
cases.append(
    {
        "case_id": "c049_base_04_equalizer_parallel",
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
    }
)

# 5: Pullback cospan
cases.append(
    {
        "case_id": "c049_base_05_pullback_cospan",
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
    }
)

# 6: Terminal object
cases.append(
    {
        "case_id": "c049_base_06_terminal_linear",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": objs3,
        "morphisms": mors3,
        "comp": comp3,
        "diagram": [],
    }
)

# 7: Coproduct in linear poset
cases.append(
    {
        "case_id": "c049_base_07_coproduct_poset",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": objs3,
        "morphisms": mors3,
        "comp": comp3,
        "diagram": ["0", "1"],
    }
)

# 8: Coequalizer trivial
cases.append(
    {
        "case_id": "c049_base_08_coequalizer_same",
        "task": "COLIMIT",
        "shape": "coequalizer",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {},
        "diagram": ["f", "f"],
    }
)

# 9: Pushout span
cases.append(
    {
        "case_id": "c049_base_09_pushout_span",
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
    }
)

# 10: Initial object
cases.append(
    {
        "case_id": "c049_base_10_initial_linear",
        "task": "COLIMIT",
        "shape": "initial",
        "objects": objs3,
        "morphisms": mors3,
        "comp": comp3,
        "diagram": [],
    }
)

# 11: Terminal object in 4-poset
cases.append(
    {
        "case_id": "c049_base_11_terminal_4",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": objs4,
        "morphisms": mors4,
        "comp": comp4,
        "diagram": [],
    }
)

# 12: Initial object in 4-poset
cases.append(
    {
        "case_id": "c049_base_12_initial_4",
        "task": "COLIMIT",
        "shape": "initial",
        "objects": objs4,
        "morphisms": mors4,
        "comp": comp4,
        "diagram": [],
    }
)

# 13-24: Limit / Colimit non-existing cases (12 cases)
# 13: Discrete 2-object category has no product
disc2_o, disc2_m, disc2_c = make_discrete(2)
cases.append(
    {
        "case_id": "c049_base_13_no_product_disc2",
        "task": "LIMIT",
        "shape": "product",
        "objects": disc2_o,
        "morphisms": disc2_m,
        "comp": disc2_c,
        "diagram": ["0", "1"],
    }
)

# 14: Discrete 3-object category has no terminal
disc3_o, disc3_m, disc3_c = make_discrete(3)
cases.append(
    {
        "case_id": "c049_base_14_no_terminal_disc3",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": disc3_o,
        "morphisms": disc3_m,
        "comp": disc3_c,
        "diagram": [],
    }
)

# 15: Discrete category has no initial
cases.append(
    {
        "case_id": "c049_base_15_no_initial_disc3",
        "task": "COLIMIT",
        "shape": "initial",
        "objects": disc3_o,
        "morphisms": disc3_m,
        "comp": disc3_c,
        "diagram": [],
    }
)

# 16: Discrete category has no coproduct
cases.append(
    {
        "case_id": "c049_base_16_no_coproduct_disc2",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": disc2_o,
        "morphisms": disc2_m,
        "comp": disc2_c,
        "diagram": ["0", "1"],
    }
)

# 17: Monoid Z_2 has no product
cases.append(
    {
        "case_id": "c049_base_17_no_product_monoid_z2",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"]],
        "comp": {"a": {"a": "id0"}},
        "diagram": ["0", "0"],
    }
)

# 18: Monoid Z_3 has no coproduct
cases.append(
    {
        "case_id": "c049_base_18_no_coproduct_monoid_z3",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["a2", "0", "0"]],
        "comp": {"a": {"a": "a2", "a2": "id0"}, "a2": {"a": "id0", "a2": "a"}},
        "diagram": ["0", "0"],
    }
)

# 19: Equalizer of distinct parallel arrows with no arrows into domain
cases.append(
    {
        "case_id": "c049_base_19_no_equalizer",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"], ["g", "0", "1"]],
        "comp": {},
        "diagram": ["f", "g"],
    }
)

# 20: Coequalizer of parallel arrows with no arrows out of codomain
cases.append(
    {
        "case_id": "c049_base_20_no_coequalizer",
        "task": "COLIMIT",
        "shape": "coequalizer",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"], ["g", "0", "1"]],
        "comp": {},
        "diagram": ["f", "g"],
    }
)

# 21: Pullback with no span completion
cases.append(
    {
        "case_id": "c049_base_21_no_pullback",
        "task": "LIMIT",
        "shape": "pullback",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f", "0", "2"],
            ["g", "1", "2"],
        ],
        "comp": {},
        "diagram": ["f", "g"],
    }
)

# 22: Pushout with no cospan completion
cases.append(
    {
        "case_id": "c049_base_22_no_pushout",
        "task": "COLIMIT",
        "shape": "pushout",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f", "0", "1"],
            ["g", "0", "2"],
        ],
        "comp": {},
        "diagram": ["f", "g"],
    }
)

# 23: Discrete 4 has no product
disc4_o, disc4_m, disc4_c = make_discrete(4)
cases.append(
    {
        "case_id": "c049_base_23_no_product_disc4",
        "task": "LIMIT",
        "shape": "product",
        "objects": disc4_o,
        "morphisms": disc4_m,
        "comp": disc4_c,
        "diagram": ["1", "2"],
    }
)

# 24: Discrete 4 has no coproduct
cases.append(
    {
        "case_id": "c049_base_24_no_coproduct_disc4",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": disc4_o,
        "morphisms": disc4_m,
        "comp": disc4_c,
        "diagram": ["2", "3"],
    }
)

# 25-40: 16 Adjunction cases (8 adjoint, 8 not adjoint)
# 25: Identity adjunction on poset 2
pos2_o, pos2_m, pos2_c = make_linear_poset(2)
cases.append(
    {
        "case_id": "c049_base_25_adj_id_poset2",
        "task": "ADJUNCTION",
        "category_C": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "category_D": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "F": {"objects": {o: o for o in pos2_o}, "morphisms": {m[0]: m[0] for m in pos2_m}},
        "G": {"objects": {o: o for o in pos2_o}, "morphisms": {m[0]: m[0] for m in pos2_m}},
    }
)

# 26: Identity adjunction on poset 3
cases.append(
    {
        "case_id": "c049_base_26_adj_id_poset3",
        "task": "ADJUNCTION",
        "category_C": {"objects": objs3, "morphisms": mors3, "comp": comp3},
        "category_D": {"objects": objs3, "morphisms": mors3, "comp": comp3},
        "F": {"objects": {o: o for o in objs3}, "morphisms": {m[0]: m[0] for m in mors3}},
        "G": {"objects": {o: o for o in objs3}, "morphisms": {m[0]: m[0] for m in mors3}},
    }
)

# 27: Identity adjunction on discrete 2
cases.append(
    {
        "case_id": "c049_base_27_adj_id_disc2",
        "task": "ADJUNCTION",
        "category_C": {"objects": disc2_o, "morphisms": disc2_m, "comp": disc2_c},
        "category_D": {"objects": disc2_o, "morphisms": disc2_m, "comp": disc2_c},
        "F": {"objects": {o: o for o in disc2_o}, "morphisms": {m[0]: m[0] for m in disc2_m}},
        "G": {"objects": {o: o for o in disc2_o}, "morphisms": {m[0]: m[0] for m in disc2_m}},
    }
)

# 28: Galois connection (inclusion of subposet): 2 -> 3
# F: {0, 1} -> {0, 1, 2} mapping 0->0, 1->2. G: {0, 1, 2} -> {0, 1} mapping 0->0, 1->1, 2->1
# For Galois: F(c) <= d <=> c <= G(d)
cases.append(
    {
        "case_id": "c049_base_28_adj_galois_2_3",
        "task": "ADJUNCTION",
        "category_C": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "category_D": {"objects": objs3, "morphisms": mors3, "comp": comp3},
        "F": {
            "objects": {"0": "0", "1": "1"},
            "morphisms": {"id0": "id0", "id1": "id1", "f_0_1": "f_0_1"},
        },
        "G": {
            "objects": {"0": "0", "1": "1", "2": "1"},
            "morphisms": {
                "id0": "id0",
                "id1": "id1",
                "id2": "id1",
                "f_0_1": "f_0_1",
                "f_0_2": "f_0_1",
                "f_1_2": "id1",
            },
        },
    }
)

# 29: Adjunction on 1-object trivial
cases.append(
    {
        "case_id": "c049_base_29_adj_trivial_1",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
    }
)

# 30: Identity adjunction on discrete 3
cases.append(
    {
        "case_id": "c049_base_30_adj_id_disc3",
        "task": "ADJUNCTION",
        "category_C": {"objects": disc3_o, "morphisms": disc3_m, "comp": disc3_c},
        "category_D": {"objects": disc3_o, "morphisms": disc3_m, "comp": disc3_c},
        "F": {"objects": {o: o for o in disc3_o}, "morphisms": {m[0]: m[0] for m in disc3_m}},
        "G": {"objects": {o: o for o in disc3_o}, "morphisms": {m[0]: m[0] for m in disc3_m}},
    }
)

# 31: Identity adjunction on linear 4
cases.append(
    {
        "case_id": "c049_base_31_adj_id_poset4",
        "task": "ADJUNCTION",
        "category_C": {"objects": objs4, "morphisms": mors4, "comp": comp4},
        "category_D": {"objects": objs4, "morphisms": mors4, "comp": comp4},
        "F": {"objects": {o: o for o in objs4}, "morphisms": {m[0]: m[0] for m in mors4}},
        "G": {"objects": {o: o for o in objs4}, "morphisms": {m[0]: m[0] for m in mors4}},
    }
)

# 32: Adjunction on terminal category: C -> 1
cases.append(
    {
        "case_id": "c049_base_32_adj_to_terminal",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
    }
)

# 33-40: 8 Non-adjoint cases
# 33: Non-adjoint cardinality mismatch (1 obj vs 2 obj discrete)
cases.append(
    {
        "case_id": "c049_base_33_not_adj_card_1_2",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {"objects": disc2_o, "morphisms": disc2_m, "comp": disc2_c},
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {"objects": {"0": "0", "1": "0"}, "morphisms": {"id0": "id0", "id1": "id0"}},
    }
)

# 34: Non-adjoint cardinality mismatch (parallel arrows in D)
cases.append(
    {
        "case_id": "c049_base_34_not_adj_card_parallel",
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
    }
)

# 35: Non-adjoint (reversed poset arrows)
cases.append(
    {
        "case_id": "c049_base_35_not_adj_reversed_poset",
        "task": "ADJUNCTION",
        "category_C": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "category_D": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "F": {
            "objects": {"0": "1", "1": "0"},
            "morphisms": {"id0": "id1", "id1": "id0", "f_0_1": "id1"},
        },  # breaks order
        "G": {
            "objects": {"0": "0", "1": "1"},
            "morphisms": {"id0": "id0", "id1": "id1", "f_0_1": "f_0_1"},
        },
    }
)

# 36: Non-adjoint discrete to linear
cases.append(
    {
        "case_id": "c049_base_36_not_adj_disc_to_linear",
        "task": "ADJUNCTION",
        "category_C": {"objects": disc2_o, "morphisms": disc2_m, "comp": disc2_c},
        "category_D": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "F": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1"}},
        "G": {
            "objects": {"0": "0", "1": "0"},
            "morphisms": {"id0": "id0", "id1": "id0", "f_0_1": "id0"},
        },
    }
)

# 37: Non-adjoint monoid Z_2
cases.append(
    {
        "case_id": "c049_base_37_not_adj_monoid_z2",
        "task": "ADJUNCTION",
        "category_C": {
            "objects": ["0"],
            "morphisms": [["id0", "0", "0"], ["a", "0", "0"]],
            "comp": {"a": {"a": "id0"}},
        },
        "category_D": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0", "a": "id0"}},
        "G": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
    }
)

# 38: Non-adjoint discrete 3 to 2
cases.append(
    {
        "case_id": "c049_base_38_not_adj_disc_3_2",
        "task": "ADJUNCTION",
        "category_C": {"objects": disc3_o, "morphisms": disc3_m, "comp": disc3_c},
        "category_D": {"objects": disc2_o, "morphisms": disc2_m, "comp": disc2_c},
        "F": {
            "objects": {"0": "0", "1": "1", "2": "1"},
            "morphisms": {"id0": "id0", "id1": "id1", "id2": "id1"},
        },
        "G": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1"}},
    }
)

# 39: Non-adjoint linear 3 to 2
cases.append(
    {
        "case_id": "c049_base_39_not_adj_lin_3_2",
        "task": "ADJUNCTION",
        "category_C": {"objects": objs3, "morphisms": mors3, "comp": comp3},
        "category_D": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "F": {
            "objects": {"0": "0", "1": "0", "2": "1"},
            "morphisms": {
                "id0": "id0",
                "id1": "id0",
                "id2": "id1",
                "f_0_1": "id0",
                "f_0_2": "f_0_1",
                "f_1_2": "f_0_1",
            },
        },
        "G": {
            "objects": {"0": "0", "1": "2"},
            "morphisms": {"id0": "id0", "id1": "id2", "f_0_1": "f_0_2"},
        },
    }
)

# 40: Non-adjoint swap on 2-object
cases.append(
    {
        "case_id": "c049_base_40_not_adj_swap",
        "task": "ADJUNCTION",
        "category_C": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "category_D": {"objects": pos2_o, "morphisms": pos2_m, "comp": pos2_c},
        "F": {
            "objects": {"0": "1", "1": "0"},
            "morphisms": {"id0": "id1", "id1": "id0", "f_0_1": "id1"},
        },
        "G": {
            "objects": {"0": "1", "1": "0"},
            "morphisms": {"id0": "id1", "id1": "id0", "f_0_1": "id1"},
        },
    }
)

# 41-56: 16 Relabel and Duality Controls
# 41: Relabelled product
cases.append(
    {
        "case_id": "c049_gauge_41_relabel_product",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["A", "B", "C"],
        "morphisms": [
            ["idA", "A", "A"],
            ["idB", "B", "B"],
            ["idC", "C", "C"],
            ["p", "A", "B"],
            ["q", "A", "C"],
        ],
        "comp": {},
        "diagram": ["B", "C"],
    }
)

# 42: Duality control: colimit in C^op of product diagram
cases.append(
    {
        "case_id": "c049_gauge_42_duality_coproduct_poset",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["p", "1", "0"],
            ["q", "2", "0"],
        ],
        "comp": {},
        "diagram": ["1", "2"],
    }
)

# 43: Relabelled equalizer
cases.append(
    {
        "case_id": "c049_gauge_43_relabel_equalizer",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["X", "Y"],
        "morphisms": [["idX", "X", "X"], ["idY", "Y", "Y"], ["f", "X", "Y"]],
        "comp": {},
        "diagram": ["f", "f"],
    }
)

# 44: Duality control: coequalizer in C^op
cases.append(
    {
        "case_id": "c049_gauge_44_duality_coequalizer",
        "task": "COLIMIT",
        "shape": "coequalizer",
        "objects": ["X", "Y"],
        "morphisms": [["idX", "X", "X"], ["idY", "Y", "Y"], ["f", "X", "Y"]],
        "comp": {},
        "diagram": ["f", "f"],
    }
)

# 45: Relabelled terminal
cases.append(
    {
        "case_id": "c049_gauge_45_relabel_terminal",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": ["Alpha", "Beta"],
        "morphisms": [
            ["idAlpha", "Alpha", "Alpha"],
            ["idBeta", "Beta", "Beta"],
            ["arr", "Alpha", "Beta"],
        ],
        "comp": {},
        "diagram": [],
    }
)

# 46: Duality control: initial in C^op
cases.append(
    {
        "case_id": "c049_gauge_46_duality_initial",
        "task": "COLIMIT",
        "shape": "initial",
        "objects": ["Alpha", "Beta"],
        "morphisms": [
            ["idAlpha", "Alpha", "Alpha"],
            ["idBeta", "Beta", "Beta"],
            ["arr", "Alpha", "Beta"],
        ],
        "comp": {},
        "diagram": [],
    }
)

# 47: Shuffled morphisms product
cases.append(
    {
        "case_id": "c049_gauge_47_shuffle_morphisms",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["q", "0", "2"],
            ["id1", "1", "1"],
            ["p", "0", "1"],
            ["id0", "0", "0"],
            ["id2", "2", "2"],
        ],
        "comp": {},
        "diagram": ["1", "2"],
    }
)

# 48: Shuffled morphisms equalizer
cases.append(
    {
        "case_id": "c049_gauge_48_shuffle_equalizer",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["0", "1"],
        "morphisms": [["f", "0", "1"], ["id1", "1", "1"], ["id0", "0", "0"]],
        "comp": {},
        "diagram": ["f", "f"],
    }
)

# 49-56: 8 more gauge controls (relabelled adjunctions and dualities)
for i in range(8):
    cases.append(
        {
            "case_id": f"c049_gauge_{i + 49}_relabel_adj_{i}",
            "task": "ADJUNCTION",
            "category_C": {
                "objects": [f"c{k}" for k in range(2)],
                "morphisms": [[f"idc{k}", f"c{k}", f"c{k}"] for k in range(2)],
                "comp": {},
            },
            "category_D": {
                "objects": [f"d{k}" for k in range(2)],
                "morphisms": [[f"idd{k}", f"d{k}", f"d{k}"] for k in range(2)],
                "comp": {},
            },
            "F": {
                "objects": {f"c{k}": f"d{k}" for k in range(2)},
                "morphisms": {f"idc{k}": f"idd{k}" for k in range(2)},
            },
            "G": {
                "objects": {f"d{k}": f"c{k}" for k in range(2)},
                "morphisms": {f"idd{k}": f"idc{k}" for k in range(2)},
            },
        }
    )

# 57-64: 8 Poisoned cases
# 57: Non-associative table
cases.append(
    {
        "case_id": "c049_poison_57_non_associative",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["b", "0", "0"], ["c", "0", "0"]],
        "comp": {"a": {"b": "c"}, "b": {"c": "a"}},
        "diagram": ["0", "0"],
    }
)

# 58: Missing identity morphism
cases.append(
    {
        "case_id": "c049_poison_58_missing_identity",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["f", "0", "1"]],  # missing id1
        "comp": {},
        "diagram": ["0", "1"],
    }
)

# 59: Unclosed composition table
cases.append(
    {
        "case_id": "c049_poison_59_unclosed_composition",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f", "0", "1"],
            ["g", "1", "2"],
        ],
        "comp": {},  # g ∘ f missing!
        "diagram": ["1", "2"],
    }
)

# 60: Poisoned note claiming textbook cartesian product
cases.append(
    {
        "case_id": "c049_poison_60_note_textbook_claim",
        "note": "The product is the standard cartesian product with apex 0.",
        "task": "LIMIT",
        "shape": "product",
        "objects": disc2_o,
        "morphisms": disc2_m,
        "comp": disc2_c,  # Discrete 2 has no product!
        "diagram": ["0", "1"],
    }
)

# 61: Adjunction with non-associative category C
cases.append(
    {
        "case_id": "c049_poison_61_adj_non_assoc_C",
        "task": "ADJUNCTION",
        "category_C": {
            "objects": ["0"],
            "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["b", "0", "0"], ["c", "0", "0"]],
            "comp": {"a": {"b": "c"}, "b": {"c": "a"}},
        },
        "category_D": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "F": {
            "objects": {"0": "0"},
            "morphisms": {"id0": "id0", "a": "id0", "b": "id0", "c": "id0"},
        },
        "G": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
    }
)

# 62: Adjunction with missing identity in D
cases.append(
    {
        "case_id": "c049_poison_62_adj_missing_id_D",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {"objects": ["0", "1"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {"objects": {"0": "0", "1": "0"}, "morphisms": {"id0": "id0"}},
    }
)

# 63: Non-associative category with colimit
cases.append(
    {
        "case_id": "c049_poison_63_colimit_non_assoc",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["b", "0", "0"], ["c", "0", "0"]],
        "comp": {"a": {"b": "c"}, "b": {"c": "a"}},
        "diagram": ["0", "0"],
    }
)

# 64: Functor that fails to preserve identity in adjunction
cases.append(
    {
        "case_id": "c049_poison_64_unclosed_comp_in_D",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {
            "objects": ["0", "1", "2"],
            "morphisms": [
                ["id0", "0", "0"],
                ["id1", "1", "1"],
                ["id2", "2", "2"],
                ["f", "0", "1"],
                ["g", "1", "2"],
            ],
            "comp": {},
        },
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {
            "objects": {"0": "0", "1": "0", "2": "0"},
            "morphisms": {"id0": "id0", "id1": "id0", "id2": "id0", "f": "id0", "g": "id0"},
        },
    }
)

assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"

for c in cases:
    fpath = os.path.join(cases_dir, f"{c['case_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

print(f"Successfully generated {len(cases)} hidden evaluation cases in {cases_dir}.")
