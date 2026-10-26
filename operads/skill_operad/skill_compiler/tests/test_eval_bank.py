#!/usr/bin/env python3
"""Eval bank unit and integration non-regression tests with isolated synthetic mocks. AuthorityEffect: None."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from omega_engine_operads.skill_operad.skill_compiler.eval_runner import run_bank


def _scaffold_mini_eval_repo(tmp: Path) -> Path:
    (tmp / ".git").mkdir()
    (tmp / ".agents" / "skills" / "autoskill").mkdir(parents=True)
    (tmp / ".agents" / "skills" / "autoskill" / "SKILL.md").write_text("---\nname: autoskill\n---\n", encoding="utf-8")
    (tmp / ".agents" / "operad").mkdir(parents=True)
    (tmp / ".agents" / "operad" / "operad_signature.json").write_text(
        json.dumps({"colours": {}, "identities": [], "operations": []}),
        encoding="utf-8",
    )
    (tmp / ".agents" / "operad" / "skill_compiler").mkdir(parents=True)
    routes_src = (
        Path(__file__).resolve().parents[2] / "yaml" / "routes.yaml"
        if (Path(__file__).resolve().parents[2] / "yaml" / "routes.yaml").is_file()
        else Path(__file__).resolve().parents[1] / "routes.yaml"
    )
    if routes_src.is_file():
        (tmp / ".agents" / "operad" / "skill_compiler" / "routes.yaml").write_text(
            routes_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return tmp


class EvalBankRunnerUnitTests(unittest.TestCase):
    """Isolated unit tests for eval_runner logic using synthetic mock cases."""

    def test_run_bank_synthetic_cases(self) -> None:
        """Verifies runner logic against controlled synthetic pass/fail cases without coupling to production state."""
        with tempfile.TemporaryDirectory() as td:
            root = _scaffold_mini_eval_repo(Path(td))
            cases_dir = (
                root
                / "omega_engine_operads"
                / "skill_operad"
                / "skill_compiler"
                / "eval_bank"
            )
            cases_dir.mkdir(parents=True)

            synthetic_bank = {
                "schema": "omega.skill_compiler.eval_bank.v1",
                "cases": [
                    {
                        "id": "case_pass_001",
                        "kind": "resolve",
                        "signal": "DDA trace missing AE=None check",
                        "invariant": "Always check DDA AuthorityEffect None",
                        "expect": {"disposition": "SHARED_CONTRACT"},
                    },
                    {
                        "id": "case_fail_002",
                        "kind": "resolve",
                        "signal": "invalid signal text",
                        "invariant": "unmatched invariant text",
                        "expect": {"disposition": "INVALID_DISPOSITION_TRIGGER"},
                    },
                ],
            }
            (cases_dir / "cases.json").write_text(json.dumps(synthetic_bank, indent=2), encoding="utf-8")

            receipt = run_bank(root)
            self.assertEqual(receipt["total"], 2)
            self.assertEqual(receipt["passed"], 1)
            self.assertEqual(receipt["failed"], 1)

            # Granular assertion on failed case
            failed_cases = [r for r in receipt["results"] if not r["ok"]]
            self.assertEqual(len(failed_cases), 1)
            self.assertEqual(failed_cases[0]["id"], "case_fail_002")
            self.assertIn("got=SKILL_PROSE", failed_cases[0]["error"] or "")


class EvalBankLiveIntegrationTests(unittest.TestCase):
    """Integration tests verifying live repo evaluation bank schema and validity."""

    def test_live_bank_schema_and_integrity(self) -> None:
        pkg_path = Path(__file__).resolve().parents[1]
        path = pkg_path / "eval_bank" / "cases.json"
        self.assertTrue(path.is_file(), f"Missing live cases file: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("schema"), "omega.skill_compiler.eval_bank.v1")
        cases = data.get("cases") or []
        self.assertIsInstance(cases, list)

        # Validate required keys per case
        for idx, case in enumerate(cases):
            self.assertIn("id", case, f"Case index {idx} missing 'id'")
            self.assertIn("kind", case, f"Case {case.get('id')} missing 'kind'")
            self.assertIn("expect", case, f"Case {case.get('id')} missing 'expect'")


if __name__ == "__main__":
    unittest.main()
