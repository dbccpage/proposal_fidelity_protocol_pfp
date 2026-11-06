"""
poisoned_cases.py — 16 Poisoned but schema-valid cases for Challenge C005.

Implements `operand schema_is_shape_only.v1`.
Cases whose intuitive or templated answer produces a valid JSON structure
matching the schema, but constitutes a mathematically false witness:
- Consistency: Potentials satisfying all relations but one (Phi_1 > 0).
- Cycle repair: Zero-reaching repairs whose weighted L1 cost exceeds the true minimum.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PoisonedCase:
    case_id: str
    kind: str  # "consistency" or "cycle_repair"
    prompt: str
    edges: list[tuple[str, str, int]]
    weights: list[int]
    optimal_cost: int
    schema_valid_false_witness: dict[str, Any]
    description: str


POISONED_CASES: tuple[PoisonedCase, ...] = (
    # 8 Consistency Poisoned Cases
    PoisonedCase(
        case_id="poison_cons_01",
        kind="consistency",
        prompt="Determine consistency: A -> B = 2, B -> C = 3, C -> A = -6.",
        edges=[("A", "B", 2), ("B", "C", 3), ("C", "A", -6)],
        weights=[1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"A": "0", "B": "2", "C": "5"},  # C -> A is 0 - 5 = -5 != -6
        },
        description="Directed 3-cycle with sum -1. Naive chain leaves last edge violated.",
    ),
    PoisonedCase(
        case_id="poison_cons_02",
        kind="consistency",
        prompt="Determine consistency: X -> Y = 5, Y -> Z = 4, Z -> W = -2, W -> X = -8.",
        edges=[("X", "Y", 5), ("Y", "Z", 4), ("Z", "W", -2), ("W", "X", -8)],
        weights=[1, 1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"X": "0", "Y": "5", "Z": "9", "W": "7"},  # W -> X is 0 - 7 = -7 != -8
        },
        description="Directed 4-cycle with sum -1.",
    ),
    PoisonedCase(
        case_id="poison_cons_03",
        kind="consistency",
        prompt="Determine consistency: n1 -> n2 = 1, n2 -> n3 = 1, n3 -> n4 = 1, n4 -> n1 = 0.",
        edges=[("n1", "n2", 1), ("n2", "n3", 1), ("n3", "n4", 1), ("n4", "n1", 0)],
        weights=[1, 1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"n1": "0", "n2": "1", "n3": "2", "n4": "3"},
        },
        description="Cycle sum = 3, inconsistent, tempting valid shape with false certificate.",
    ),
    PoisonedCase(
        case_id="poison_cons_04",
        kind="consistency",
        prompt="Determine consistency: u -> v = 10, v -> w = -4, w -> u = -5.",
        edges=[("u", "v", 10), ("v", "w", -4), ("w", "u", -5)],
        weights=[1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"u": "0", "v": "10", "w": "6"},
        },
        description="Cycle sum = 1, inconsistent.",
    ),
    PoisonedCase(
        case_id="poison_cons_05",
        kind="consistency",
        prompt="Determine consistency: p -> q = 3, q -> r = 3, r -> s = 3, s -> p = -8.",
        edges=[("p", "q", 3), ("q", "r", 3), ("r", "s", 3), ("s", "p", -8)],
        weights=[1, 1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"p": "0", "q": "3", "r": "6", "s": "9"},
        },
        description="Cycle sum = 1.",
    ),
    PoisonedCase(
        case_id="poison_cons_06",
        kind="consistency",
        prompt="Determine consistency: a -> b = -7, b -> c = 2, c -> d = 4, d -> a = 2.",
        edges=[("a", "b", -7), ("b", "c", 2), ("c", "d", 4), ("d", "a", 2)],
        weights=[1, 1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"a": "0", "b": "-7", "c": "-5", "d": "-1"},
        },
        description="Cycle sum = 1, residual error on d -> a.",
    ),
    PoisonedCase(
        case_id="poison_cons_07",
        kind="consistency",
        prompt="Determine consistency: i0 -> i1 = 5, i1 -> i2 = -5, i2 -> i0 = 1.",
        edges=[("i0", "i1", 5), ("i1", "i2", -5), ("i2", "i0", 1)],
        weights=[1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"i0": "0", "i1": "5", "i2": "0"},
        },
        description="Cycle sum = 1.",
    ),
    PoisonedCase(
        case_id="poison_cons_08",
        kind="consistency",
        prompt="Determine consistency: k1 -> k2 = 4, k2 -> k3 = 4, k3 -> k4 = -9, k4 -> k1 = 0.",
        edges=[("k1", "k2", 4), ("k2", "k3", 4), ("k3", "k4", -9), ("k4", "k1", 0)],
        weights=[1, 1, 1, 1],
        optimal_cost=-1,
        schema_valid_false_witness={
            "verdict": "CONSISTENT",
            "certificate": {"k1": "0", "k2": "4", "k3": "8", "k4": "-1"},
        },
        description="Cycle sum = -1.",
    ),
    # 8 Cycle Repair Poisoned Cases (Zero-reaching but SUBOPTIMAL cost)
    PoisonedCase(
        case_id="poison_repair_01",
        kind="cycle_repair",
        prompt="Repair cycle claims [2, 3, -4] with weights [1, 2, 3] to reach zero sum.",
        edges=[("0", "1", 2), ("1", "2", 3), ("2", "0", -4)],
        weights=[1, 2, 3],
        optimal_cost=1,  # sum is 1, min weight is 1 on edge 0, so repair edge 0 to 1 with cost 1*1 = 1
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["2", "2", "-4"],  # modified edge 1: |3-2|*2 = 2 (suboptimal)
            "weighted_l1": "1",  # falsely asserts optimal cost
        },
        description="Suboptimal repair altering weight-2 edge instead of weight-1 edge, labelled optimal.",
    ),
    PoisonedCase(
        case_id="poison_repair_02",
        kind="cycle_repair",
        prompt="Repair cycle claims [5, -2, -1] with weights [3, 1, 2] to reach zero sum.",
        edges=[("0", "1", 5), ("1", "2", -2), ("2", "0", -1)],
        weights=[3, 1, 2],
        optimal_cost=2,  # sum is 2, min weight is 1 on edge 1, repair edge 1 to -4 with cost 2*1 = 2
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["3", "-2", "-1"],  # modified edge 0: |5-3|*3 = 6 (suboptimal)
            "weighted_l1": "2",
        },
        description="Suboptimal repair on highest-weight edge.",
    ),
    PoisonedCase(
        case_id="poison_repair_03",
        kind="cycle_repair",
        prompt="Repair cycle claims [1, 1, 1, -1] with weights [2, 2, 2, 1] to reach zero sum.",
        edges=[("0", "1", 1), ("1", "2", 1), ("2", "3", 1), ("3", "0", -1)],
        weights=[2, 2, 2, 1],
        optimal_cost=2,  # sum is 2, min weight is 1 on edge 3, repair edge 3 to -3 with cost 2*1 = 2
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["-1", "1", "1", "-1"],  # modified edge 0: |1 - (-1)|*2 = 4 (suboptimal)
            "weighted_l1": "2",
        },
        description="Suboptimal repair modifying weight-2 edge.",
    ),
    PoisonedCase(
        case_id="poison_repair_04",
        kind="cycle_repair",
        prompt="Repair cycle claims [4, 4, -6] with weights [2, 1, 3] to reach zero sum.",
        edges=[("0", "1", 4), ("1", "2", 4), ("2", "0", -6)],
        weights=[2, 1, 3],
        optimal_cost=2,  # sum is 2, min weight is 1 on edge 1, repair edge 1 to 2
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["4", "4", "-8"],  # modified edge 2: cost = |-6 - (-8)|*3 = 6
            "weighted_l1": "2",
        },
        description="Suboptimal repair modifying weight-3 edge.",
    ),
    PoisonedCase(
        case_id="poison_repair_05",
        kind="cycle_repair",
        prompt="Repair cycle claims [10, -3, -5] with weights [3, 2, 1] to reach zero sum.",
        edges=[("0", "1", 10), ("1", "2", -3), ("2", "0", -5)],
        weights=[3, 2, 1],
        optimal_cost=2,  # sum is 2, min weight is 1 on edge 2, repair edge 2 to -7
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["10", "-5", "-5"],  # modified edge 1: cost = |-3 - (-5)|*2 = 4
            "weighted_l1": "2",
        },
        description="Suboptimal repair modifying weight-2 edge.",
    ),
    PoisonedCase(
        case_id="poison_repair_06",
        kind="cycle_repair",
        prompt="Repair cycle claims [1, 2, 3, -5] with weights [1, 3, 3, 2] to reach zero sum.",
        edges=[("0", "1", 1), ("1", "2", 2), ("2", "3", 3), ("3", "0", -5)],
        weights=[1, 3, 3, 2],
        optimal_cost=1,  # sum is 1, min weight is 1 on edge 0, repair edge 0 to 0
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["1", "2", "3", "-6"],  # modified edge 3: cost = |-5 - (-6)|*2 = 2
            "weighted_l1": "1",
        },
        description="Suboptimal repair on edge with weight 2 instead of 1.",
    ),
    PoisonedCase(
        case_id="poison_repair_07",
        kind="cycle_repair",
        prompt="Repair cycle claims [7, -2, -3] with weights [2, 1, 3] to reach zero sum.",
        edges=[("0", "1", 7), ("1", "2", -2), ("2", "0", -3)],
        weights=[2, 1, 3],
        optimal_cost=2,  # sum is 2, min weight is 1 on edge 1, repair edge 1 to -4
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["5", "-2", "-3"],  # modified edge 0: cost = |7 - 5|*2 = 4
            "weighted_l1": "2",
        },
        description="Suboptimal repair modifying weight-2 edge.",
    ),
    PoisonedCase(
        case_id="poison_repair_08",
        kind="cycle_repair",
        prompt="Repair cycle claims [3, 3, 3, -10] with weights [3, 2, 1, 3] to reach zero sum.",
        edges=[("0", "1", 3), ("1", "2", 3), ("2", "3", 3), ("3", "0", -10)],
        weights=[3, 2, 1, 3],
        optimal_cost=1,  # sum is -1, min weight is 1 on edge 2, repair edge 2 to 4
        schema_valid_false_witness={
            "status": "SOLVED",
            "repaired": ["3", "4", "3", "-10"],  # modified edge 1: cost = |3 - 4|*2 = 2
            "weighted_l1": "1",
        },
        description="Suboptimal repair on weight-2 edge.",
    ),
)
