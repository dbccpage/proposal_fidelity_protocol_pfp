#!/usr/bin/env python3
"""Run skill-compiler eval bank (non-regression).

Cases live under `eval_bank/cases.json`.
AuthorityEffect: None. Does not admit skills.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from knowledge_parity import scan_file  # noqa: E402
from resolve import repo_root_from, resolve_text  # noqa: E402

DEFAULT_CASES = Path(
    "operads/skill_operad/skill_compiler/eval_bank/cases.json"
)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"No cases in {path}")
    return cases


def _match_contains(blob: str, needles: list[str]) -> bool:
    low = blob.lower()
    return any(n.lower() in low for n in needles)


def _check_resolve(repo_root: Path, case: dict[str, Any]) -> str | None:
    result = resolve_text(
        repo_root,
        signal=str(case.get("signal") or ""),
        proposed_invariant=str(case.get("invariant") or ""),
        locus=str(case.get("locus") or ""),
        confidence=str(case.get("confidence") or "MEDIUM"),
    )
    exp = case.get("expect") or {}
    want = exp.get("disposition")
    if want and result.disposition != want:
        return (
            f"disposition want={want} got={result.disposition} "
            f"rules={result.matched_rules}"
        )
    skill_id = exp.get("skill_id")
    if skill_id and result.skill_id != skill_id:
        return f"skill_id want={skill_id} got={result.skill_id}"
    needles = exp.get("matched_any_contains") or []
    if needles:
        blob = " ".join(result.matched_rules + [result.target, result.rationale])
        if not _match_contains(blob, needles):
            return f"matched_any_contains {needles} not in {blob!r}"
    return None


def _check_parity_fixture(bank_dir: Path, case: dict[str, Any]) -> str | None:
    rel = case.get("fixture") or ""
    path = bank_dir / rel
    if not path.is_file():
        return f"missing fixture {path}"
    hits = scan_file(path)
    must_fail = bool((case.get("expect") or {}).get("must_fail"))
    if must_fail and not hits:
        return "expected knowledge_parity hits, got none"
    if not must_fail and hits:
        return f"expected clean parity, got {hits}"
    return None


def _structure_ok(text: str, expect: dict[str, Any]) -> str | None:
    lines = text.splitlines()
    min_lines = int(expect.get("min_lines") or 0)
    if min_lines and len(lines) < min_lines:
        return f"line count {len(lines)} < min_lines {min_lines}"
    for needle in expect.get("must_contain") or []:
        if needle not in text:
            return f"missing required substring {needle!r}"
    return None


def _check_skill_structure(repo_root: Path, case: dict[str, Any]) -> str | None:
    skill = case.get("skill") or ""
    path = repo_root / "operads" / "skills" / skill / "SKILL.md"
    if not path.is_file() and skill == "autoskill":
        alt_path = repo_root / "operads" / "skills" / "auto-skill" / "SKILL.md"
        if alt_path.is_file():
            path = alt_path
    elif not path.is_file() and skill == "auto-skill":
        alt_path = repo_root / "operads" / "skills" / "autoskill" / "SKILL.md"
        if alt_path.is_file():
            path = alt_path
    if not path.is_file():
        return f"missing skill package {path}"
    text = path.read_text(encoding="utf-8", errors="ignore")
    return _structure_ok(text, case.get("expect") or {})


def _check_structure_fixture(bank_dir: Path, case: dict[str, Any]) -> str | None:
    path = bank_dir / (case.get("fixture") or "")
    if not path.is_file():
        return f"missing fixture {path}"
    text = path.read_text(encoding="utf-8", errors="ignore")
    err = _structure_ok(text, case.get("expect") or {})
    must_fail = bool((case.get("expect") or {}).get("must_fail"))
    if must_fail:
        if err is None:
            return "expected structure failure on hollow fixture, got pass"
        return None
    return err


def run_bank(
    repo_root: Path,
    cases_path: Path | None = None,
) -> dict[str, Any]:
    path = cases_path or (repo_root / DEFAULT_CASES)
    bank_dir = path.parent
    cases = _load_cases(path)
    results: list[dict[str, Any]] = []
    failed = 0
    for case in cases:
        cid = str(case.get("id") or "unnamed")
        kind = str(case.get("kind") or "")
        err: str | None
        if kind == "resolve":
            err = _check_resolve(repo_root, case)
        elif kind == "knowledge_parity_fixture":
            err = _check_parity_fixture(bank_dir, case)
        elif kind == "skill_structure":
            err = _check_skill_structure(repo_root, case)
        elif kind == "skill_structure_fixture":
            err = _check_structure_fixture(bank_dir, case)
        else:
            err = f"unknown kind {kind!r}"
        ok = err is None
        if not ok:
            failed += 1
        results.append(
            {
                "id": cid,
                "kind": kind,
                "ok": ok,
                "error": err,
                "source_failure": case.get("source_failure"),
            }
        )
    return {
        "schema": "core.skill_compiler.eval_receipt.v1",
        "cases_path": str(path.relative_to(repo_root)).replace("\\", "/"),
        "total": len(cases),
        "passed": len(cases) - failed,
        "failed": failed,
        "results": results,
        "authority_effect": "None",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--cases",
        default=None,
        help="Path to cases.json (default: eval_bank/cases.json)",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON receipt")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    cases = Path(args.cases).resolve() if args.cases else None
    receipt = run_bank(root, cases)
    if args.json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    else:
        print("=== SKILL COMPILER EVAL BANK ===")
        print(f"cases: {receipt['cases_path']}")
        for row in receipt["results"]:
            mark = "PASS" if row["ok"] else "FAIL"
            print(f"  [{mark}] {row['id']} ({row['kind']})")
            if not row["ok"]:
                print(f"         {row['error']}")
        print(
            f"\n{receipt['passed']}/{receipt['total']} passed; "
            f"{receipt['failed']} failed."
        )
    return 1 if receipt["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
