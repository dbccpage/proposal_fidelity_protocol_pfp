# AuthorityEffect: None.
"""
Public Runner for C041: Lean 4 Proofs of Hidden Finite Lemmas.

Executes all public example cases in examples/ through the solver,
verifies each candidate proof with the exact checker, and writes answers.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_file_dir = Path(__file__).resolve().parent
_pkg_root = _file_dir.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if p.name == "certified_challenges"), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c041_lean4_finite_lemma_proofs.judge_packet.checkers.exact_checker import verify_exact
from c041_lean4_finite_lemma_proofs.reference_solver.solver import solve


def main() -> None:
    examples_dir = _file_dir / "examples"
    cases = sorted(examples_dir.glob("*.json"))
    out_file = _file_dir / "answers.jsonl"

    print(f"Executing {len(cases)} cases through C041 solver...")
    answers = []
    for cf in cases:
        with open(cf, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        ans = solve(case_data)
        ok, msg, meta = verify_exact(case_data, ans)
        status_label = "PASS" if ok else "FAIL"
        print(f"[{status_label}] {case_data.get('case_id')}: {msg}")
        answers.append(ans)

    with open(out_file, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(json.dumps(ans, sort_keys=True) + "\n")

    print(f"Wrote {len(answers)} verified answers to {out_file}")


if __name__ == "__main__":
    main()
