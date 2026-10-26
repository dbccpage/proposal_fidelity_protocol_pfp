#!/usr/bin/env python3
"""Operad honesty and residual classification tests. AuthorityEffect: None."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

OPERAD_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(OPERAD_DIR))

from bulk_operad_ingest import WRITE_ENV, apply_ingest, propose_ingest  # noqa: E402
from residual_honesty import (  # noqa: E402
    check_signature,
    check_skill_frontmatter,
    load_contractive_runs,
    run_checks,
)


class ResidualHonestyLive(unittest.TestCase):
    def test_live_repo_classifies_legacy_rows_without_upgrading_them(self) -> None:
        repo = REPO_ROOT
        receipt = run_checks(repo)
        self.assertEqual(receipt["contractive_skills_with_evidence"], [])
        self.assertEqual(receipt["legacy_residual_observations"], 7)
        self.assertEqual(receipt["observation_claim_effect"]["contractivity"], False)
        self.assertEqual(receipt["errors"], [])


class ResidualHonestyUnit(unittest.TestCase):
    def test_signature_contractive_without_trace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            operad = root / ".agents" / "operad"
            operad.mkdir(parents=True)
            (operad / "operad_signature.json").write_text(
                json.dumps(
                    {
                        "colours": {},
                        "operations": [
                            {
                                "skill_id": "fake-contractive",
                                "name": "fake",
                                "arity": 1,
                                "source_colours": ["State"],
                                "target_colour": "State",
                                "residual_effect": "contractive",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (operad / "evidence_trace.json").write_text("[]", encoding="utf-8")
            (root / ".agents" / "skills").mkdir(parents=True)
            errs = check_signature(
                operad / "operad_signature.json",
                load_contractive_runs(operad / "evidence_trace.json"),
            )
            self.assertTrue(any("fake-contractive" in e for e in errs))

    def test_nested_admitted_skill_frontmatter_caught(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skills = root / ".agents" / "skills"
            nested = skills / "family" / "nested-skill"
            nested.mkdir(parents=True)
            (nested / "SKILL.md").write_text(
                "---\nname: nested-skill\noperad_residual: \"contractive\"\n---\n\n# nested\n",
                encoding="utf-8",
            )
            # archive path must be ignored even if contractive
            arch = skills / "ooutwire" / "proposal"
            arch.mkdir(parents=True)
            (arch / "SKILL.md").write_text(
                "---\nname: proposal\noperad_residual: \"contractive\"\n---\n",
                encoding="utf-8",
            )
            errs = check_skill_frontmatter(
                skills, {}, signature_contractive=set()
            )
            self.assertTrue(
                any("nested-skill" in e and "family/nested-skill" in e for e in errs),
                errs,
            )
            self.assertFalse(any("proposal" in e for e in errs), errs)


class BulkIngestQuarantine(unittest.TestCase):
    def test_default_is_dry_run(self) -> None:
        os.environ.pop(WRITE_ENV, None)
        plan = propose_ingest(
            [{"name": "x-tool", "description": "does audit security scan"}],
            origin="test",
            operad_dir=OPERAD_DIR,
        )
        self.assertGreaterEqual(plan["proposed_count"], 0)
        self.assertFalse(plan["write_allowed"])

    def test_apply_refuses_without_env(self) -> None:
        os.environ.pop(WRITE_ENV, None)
        out = apply_ingest(
            [{"name": "y-tool", "description": "code refactor lint"}],
            origin="test",
            operad_dir=OPERAD_DIR,
        )
        self.assertFalse(out.get("applied"))
        self.assertIn("refused", out.get("error") or "")

    def test_ingest_forces_unknown_residual(self) -> None:
        plan = propose_ingest(
            [{"name": "z-tool", "description": "lean theorem proof"}],
            origin="test",
            operad_dir=OPERAD_DIR,
        )
        for op in plan["proposed"]:
            self.assertEqual(op["residual_effect"], "unknown")
            self.assertEqual(op["def_op"], "DEF-OP-01")

    def test_batch_normalization_collision_fail_closed(self) -> None:
        plan = propose_ingest(
            [
                {"name": "a-b", "description": "code lint"},
                {"name": "a_b", "description": "code lint"},
            ],
            origin="x",
            operad_dir=OPERAD_DIR,
        )
        self.assertFalse(plan.get("ok"))
        self.assertEqual(plan.get("proposed_count"), 0)
        self.assertTrue(plan.get("collisions"))
        self.assertIn("collision", (plan.get("error") or "").lower())


class HighTrafficSpoe(unittest.TestCase):
    def test_current_and_legacy_compositions_resolve_to_current_skills(self) -> None:
        signature = json.loads((REPO_ROOT / ".agents/skill_operads/operad_signature.json").read_text())
        ids = {row["skill_id"] for row in signature["operations"]}
        matrices = [json.loads(path.read_text()) for path in (
            REPO_ROOT / ".agents/skill_operads/composition_matrix.json",
            OPERAD_DIR / "json/composition_matrix.json")]
        self.assertEqual(matrices[0], matrices[1])
        for matrix in matrices:
            for row in matrix["compositions"]:
                self.assertIn(row["outer"], ids)
                self.assertIn(row["inner"], ids)
            for row in matrix["synthesized_meta_skills"]:
                self.assertIn(row["id"], ids)

    def test_meta_chain_typed(self) -> None:
        sig_file = (
            OPERAD_DIR / "json" / "operad_signature.json"
            if (OPERAD_DIR / "json" / "operad_signature.json").is_file()
            else OPERAD_DIR / "operad_signature.json"
        )
        sig = json.loads(sig_file.read_text(encoding="utf-8"))
        ids = {op["skill_id"] for op in sig["operations"]}
        for sid in (
            "auto-skill",
            "auto-oe-autop",
            "auto-symmetry-hunter",
            "auto-improve-autoskill",
            "auto-review-agents",
            "auto-review-skills",
            "auto-suggest-new-skills",
            "github",
            "panep-lean-snippet-export",
        ):
            self.assertIn(sid, ids, f"missing SPOE typing for {sid}")
            op = next(o for o in sig["operations"] if o["skill_id"] == sid)
            if sid == "0-oe-commit":
                pass
            elif sid.startswith("auto"):
                self.assertEqual(op["residual_effect"], "unknown")
        self.assertNotIn(
            "rip-papers",
            ids,
            "deleted skill must not return as an orphaned operation",
        )
        self.assertNotIn(
            "panepistimion-paper-build",
            ids,
            "deliberately removed skill must not return as an orphaned operation",
        )


if __name__ == "__main__":
    unittest.main()
