"""Generate 40 hostile checker mutations for C020."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from c020_spectral_sequence_double_complex.reference_solver.solver import (
    solve,
)


def main():
    root = Path(__file__).resolve().parent
    mut_dir = root / "judge_packet" / "mutation_suite" / "mutations"
    mut_dir.mkdir(parents=True, exist_ok=True)

    # Use ex01 (worked columns) and ex03 (worked both) as baseline cases
    with (root / "participant_packet" / "examples" / "c020_ex01_worked_columns.json").open(
        encoding="utf-8"
    ) as f:
        case_col = json.load(f)
    cert_col = solve(case_col)

    with (root / "participant_packet" / "examples" / "c020_ex03_worked_both.json").open(
        encoding="utf-8"
    ) as f:
        case_both = json.load(f)
    solve(case_both)

    with (
        root / "participant_packet" / "examples" / "c020_ex08_out_of_scope_noncommuting.json"
    ).open(encoding="utf-8") as f:
        case_oos = json.load(f)
    cert_oos = solve(case_oos)

    mutations: list[dict[str, Any]] = []

    # Mut 01-05: Target bidegree corruptions
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["differentials"][0]["from"] = f"{i + 1},{i + 1}"
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Corrupted differential from position",
                "case": case_col,
                "certificate": c,
            }
        )

    # Mut 06-10: Abutment disagreement (Einf total sums disagree with H_n(Tot))
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["Einf"]["0,1"] = str(i + 1)
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Einf total degree sum disagrees with H(Tot)",
                "case": case_col,
                "certificate": c,
            }
        )

    # Mut 11-15: Recursion error (bad rank or omitting incoming rank)
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["differentials"][0]["rank"] = str(i + 2)
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Corrupted differential rank causing recursion failure",
                "case": case_col,
                "certificate": c,
            }
        )

    # Mut 16-20: Wrong filtration reported
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["filtration"] = "rows" if i % 2 == 0 else "both"
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Mismatched filtration reported",
                "case": case_col,
                "certificate": c,
            }
        )

    # Mut 21-25: Noncommuting case accepted as SOLVED
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Noncommuting out-of-scope case falsely accepted as SOLVED",
                "case": case_oos,
                "certificate": c,
            }
        )

    # Mut 26-30: Out of scope wrong reason
    for i in range(5):
        c = json.loads(json.dumps(cert_oos))
        c["witness"]["reason"] = f"WRONG_REASON_{i}"
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Wrong refusal witness reason",
                "case": case_oos,
                "certificate": c,
            }
        )

    # Mut 31-35: Corrupted E2 page dimensions
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["E2"]["2,0"] = str(i + 3)
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Corrupted E2 dimension",
                "case": case_col,
                "certificate": c,
            }
        )

    # Mut 36-40: Corrupted total homology
    for i in range(5):
        c = json.loads(json.dumps(cert_col))
        c["tot_homology"]["1"] = str(i + 1)
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Corrupted total homology dimension",
                "case": case_col,
                "certificate": c,
            }
        )

    for m in mutations:
        with (mut_dir / f"{m['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)

    print(f"Generated {len(mutations)} hostile checker mutations.")


if __name__ == "__main__":
    main()
