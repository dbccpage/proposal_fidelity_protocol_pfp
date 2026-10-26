"""Compatibility entrypoints for the unbound cohomology the city operation.

The old local script manufactured seven acts and receipts carrying a retired
self-score pass label. No cohomology execution binding exists here, so
requesting a bout must refuse.
Mathematical checking remains available through b_cohomology.runner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from .cohomology_solver import CohomologyCertificate


@dataclass(frozen=True)
class WolandSwarmResult:
    task_key: str
    verdict: str
    certificate: CohomologyCertificate | None = None
    lggr_verdict: Any = None
    billed_cost_usd: Decimal | None = None
    is_within_target_budget: bool | None = None
    output_directory: Path | None = None
    receipt_sha256: str | None = None
    refusal: str = "WOLAND_EXECUTION_UNAVAILABLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_key": self.task_key,
            "verdict": self.verdict,
            "refusal": self.refusal,
            "authority_effect": "None",
            "billed_cost_usd": None,
            "is_within_target_budget": None,
            "output_directory": None,
            "receipt_sha256": None,
        }


@dataclass(frozen=True)
class WolandBatteryResult:
    task_key: str
    verdict: str
    case_results: list[dict[str, Any]]
    total_cases: int
    passed_cases: int = 0
    pass_rate: float = 0.0
    billed_cost_usd: Decimal | None = None
    is_within_target_budget: bool | None = None
    output_directory: Path | None = None
    receipt_sha256: str | None = None
    refusal: str = "WOLAND_EXECUTION_UNAVAILABLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_key": self.task_key,
            "verdict": self.verdict,
            "refusal": self.refusal,
            "authority_effect": "None",
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "pass_rate": self.pass_rate,
            "billed_cost_usd": None,
            "is_within_target_budget": None,
            "output_directory": None,
            "receipt_sha256": None,
        }


class WolandCohomologyOverseer:
    """Refuse until the owning the city runtime exposes this challenge operation."""

    def __init__(
        self, repo_root: Path, budget_ceiling: Decimal = Decimal("0.25"), host: Any = None
    ) -> None:
        self.repo_root = repo_root

    def execute_challenge(
        self,
        challenge_id: str,
        case_data: Mapping[str, Any],
        task_key: str | None = None,
        adversarial_zero_claim: bool = False,
    ) -> WolandSwarmResult:
        return WolandSwarmResult(
            task_key=task_key or f"cohomology_{challenge_id}", verdict="REFUSE"
        )

    def execute_battery(
        self,
        cases: Sequence[Mapping[str, Any]] | None = None,
        task_key: str | None = None,
        adversarial_zero_claim: bool = False,
    ) -> WolandBatteryResult:
        requested = list(cases) if cases is not None else get_canonical_battery_cases()
        return WolandBatteryResult(
            task_key=task_key or "cohomology_battery",
            verdict="REFUSE",
            total_cases=len(requested),
            case_results=[
                {
                    "case_id": case.get("case_id", case.get("id", f"case_{index}")),
                    "status": "UNKNOWN",
                    "refusal": "WOLAND_EXECUTION_UNAVAILABLE",
                }
                for index, case in enumerate(requested)
            ],
        )


def get_canonical_battery_cases() -> list[dict[str, Any]]:
    """Canonical test cases representing all 10 challenges in b_cohomology (C011–C020)."""
    return [
        # C011: Cycle-Rank Ladder Minimum-L1 Coboundary Repair (Round-4e Diamond)
        {
            "id": "c011_round4e_diamond",
            "challenge": "c011",
            "nodes": ["a", "b", "c", "d"],
            "edges": [["a", "b"], ["b", "c"], ["c", "a"], ["b", "d"], ["d", "a"]],
            "claims": {"a->b": "1", "b->c": "2", "c->a": "3", "b->d": "1", "d->a": "2"},
            "weights": {"a->b": "1", "b->c": "2", "c->a": "3", "b->d": "1", "d->a": "2"},
        },
        # C012: Cellular Sheaf Cohomology H0/H1 and Obstruction
        {
            "id": "c012_cellular_sheaf_interval",
            "challenge": "c012",
            "vertices": ["v0", "v1"],
            "edges": [["e0", "v0", "v1"]],
            "stalk_dims_v": {"v0": 1, "v1": 1},
            "stalk_dims_e": {"e0": 1},
            "restrictions": {
                "v0<=e0": [["1"]],
                "v1<=e0": [["1"]],
            },
            "targets": [["0"]],
        },
        # C013: Integral Homology with Torsion and Smith Normal Form (RP2 Triangulation)
        {
            "id": "c013_rp2_torsion_snf",
            "challenge": "c013",
            "simplices": [
                [1, 2, 3],
                [1, 2, 4],
                [1, 3, 5],
                [1, 4, 6],
                [1, 5, 6],
                [2, 3, 6],
                [2, 4, 5],
                [2, 5, 6],
                [3, 4, 5],
                [3, 4, 6],
            ],
        },
        # C014: Exact Discrete Hodge Decomposition (Harmonic 1-form on Triangle)
        {
            "id": "c014_discrete_hodge_triangle",
            "challenge": "c014",
            "vertices": ["v0", "v1", "v2"],
            "edges": ["e0", "e1", "e2"],
            "faces": [],
            "delta0": {
                "e0": {"v0": -1, "v1": 1},
                "e1": {"v1": -1, "v2": 1},
                "e2": {"v2": -1, "v0": 1},
            },
            "flow": {"e0": 1, "e1": 1, "e2": 1},
        },
        # C015: Persistent Homology Barcodes with Certified F2 Reduction
        {
            "id": "c015_persistence_triangle_filtration",
            "challenge": "c015",
            "filtration": [
                {"simplex": [0], "value": 0},
                {"simplex": [1], "value": 0},
                {"simplex": [2], "value": 0},
                {"simplex": [0, 1], "value": 1},
                {"simplex": [1, 2], "value": 2},
                {"simplex": [0, 2], "value": 3},
                {"simplex": [0, 1, 2], "value": 4},
            ],
        },
        # C016: Alexander-Whitney Cup Products and Cohomology Ring
        {
            "id": "c016_cup_product_spaces",
            "challenge": "c016",
            "X": [[0, 1], [1, 2], [0, 2]],
            "Y": [[0, 1, 2]],
            "p": 1,
            "q": 0,
        },
        # C017: Nonabelian Lattice Holonomy and Flatness (Z2 Gauge on 2x2 Torus)
        {
            "id": "c017_lattice_holonomy_z2",
            "challenge": "c017",
            "lattice": {"L": 2, "M": 2, "periodic": False},
            "group": {
                "elements": ["e", "-1"],
                "identity": "e",
                "table": {
                    "e": {"e": "e", "-1": "-1"},
                    "-1": {"e": "-1", "-1": "e"},
                },
            },
            "edges": {
                "0,0->1,0": "e",
                "1,0->1,1": "e",
                "0,1->1,1": "e",
                "0,0->0,1": "e",
            },
        },
        # C018: Frustration Index of Signed Graphs (Signed K4)
        {
            "id": "c018_signed_k4_frustration",
            "challenge": "c018",
            "vertices": ["a", "b", "c", "d"],
            "edges": [
                ["a", "b", -1],
                ["a", "c", -1],
                ["a", "d", -1],
                ["b", "c", -1],
                ["b", "d", -1],
                ["c", "d", -1],
            ],
        },
        # C019: Degree-2 Obstructions at Scale
        {
            "id": "c019_h2_obstruction_extension",
            "challenge": "c019",
            "vertices": ["v0", "v1"],
            "edges": ["e0"],
            "faces": ["f0"],
            "partial1": [[0]],
            "partial2": [[0]],
            "B": {"f0": "0"},
            "mode": "Q",
        },
        # C020: Spectral Sequence of a Double Complex
        {
            "id": "c020_double_complex_column_filtration",
            "challenge": "c020",
            "filtration": "columns",
            "dimensions": {
                "2,0": 1,
                "1,0": 1,
                "1,1": 1,
                "0,1": 1,
            },
            "dh": {
                "2,0": [[1]],
                "1,1": [[1]],
            },
            "dv": {
                "1,1": [[1]],
            },
        },
    ]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Request a cohomology the city bout.")
    parser.add_argument("--task-key", default=None)
    parser.add_argument("--adversarial", action="store_true")
    args = parser.parse_args()
    result = WolandCohomologyOverseer(Path.cwd()).execute_battery(
        task_key=args.task_key,
        adversarial_zero_claim=args.adversarial,
    )
    print(json.dumps(result.to_dict(), sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
