"""Fail-closed countertests for the finite operad registry model."""

from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path
import sys

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from bulk_operad_ingest import propose_ingest
from coloured_operad import ColouredOperad
from execute_operadic_compression import run_compression
from quotient_operad import EvidenceLedger, QuotientFunctor


class OperadDeclarationTests(unittest.TestCase):
    def test_duplicate_operation_id_cannot_change_signature(self) -> None:
        operad = ColouredOperad()
        operad.add_operation("op", "Operation", ["State"], "Receipt")
        with self.assertRaisesRegex(ValueError, "different declaration"):
            operad.add_operation("op", "Operation", ["Code"], "Receipt")

    def test_predeclared_composite_with_wrong_signature_is_refused(self) -> None:
        operad = ColouredOperad()
        operad.add_operation("outer", "Outer", ["Receipt"], "Audit")
        operad.add_operation("inner", "Inner", ["State"], "Receipt")
        operad.add_operation("wrong", "Wrong", ["Code"], "Paper")
        result = operad.add_composition("outer", 0, "inner", "wrong")
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "RESULT_SIGNATURE_MISMATCH")

    def test_agent_invocation_enforces_declared_arity(self) -> None:
        operad = ColouredOperad()
        operad.add_operation(
            "op",
            "Operation",
            ["State", "Proof"],
            "Receipt",
            impl=lambda state, proof: (state, proof),
        )
        agent = operad.slice("agent", ["op"])
        result = agent.invoke("op", object())
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "ARITY_MISMATCH")


class QuotientHonestyTests(unittest.TestCase):
    def test_duplicate_run_id_does_not_inflate_evidence(self) -> None:
        ledger = EvidenceLedger("op")
        ledger.add("run", 1.0, 0.5)
        ledger.add("run", 1.0, 0.5)
        self.assertEqual(len(ledger), 1)

    def test_three_scalar_runs_do_not_merge_unrelated_operations(self) -> None:
        operad = ColouredOperad()
        operad.add_operation("a", "A", ["State"], "Receipt")
        operad.add_operation("b", "B", ["State"], "Receipt")
        quotient = QuotientFunctor(operad, min_instances=3)
        for operation in ("a", "b"):
            for index in range(3):
                quotient.record(operation, f"{operation}-{index}", 1.0, 0.5)

        comparison = quotient.build_meta_operad()
        report = quotient.report()
        self.assertIn("a", comparison.operations)
        self.assertIn("b", comparison.operations)
        self.assertFalse(quotient.congruent("a", "b"))
        self.assertEqual(report["culled"], [])
        self.assertFalse(report["automatic_merges_enabled"])
        self.assertTrue(report["candidate_classes"])

    def test_default_compression_is_read_only(self) -> None:
        operad_dir = Path(__file__).resolve().parents[1]
        governed = [
            (operad_dir / "json" / name) if (operad_dir / "json" / name).is_file() else (operad_dir / name)
            for name in [
                "operad_signature.json",
                "composition_matrix.json",
                "agent_capability_slices.json",
            ]
        ]
        before = {path: path.read_bytes() for path in governed}
        report = run_compression()
        after = {path: path.read_bytes() for path in governed}
        self.assertEqual(before, after)
        self.assertFalse(report["applied"])
        self.assertEqual(report["status"], "PROPOSED_NOT_EXECUTED")


class IngestHonestyTests(unittest.TestCase):
    def _operad_dir(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "operad_signature.json").write_text(
            json.dumps({"operations": []}),
            encoding="utf-8",
        )
        return temporary, root

    def test_ingest_refuses_caller_claimed_contraction(self) -> None:
        temporary, root = self._operad_dir()
        with temporary:
            report = propose_ingest(
                [{
                    "name": "candidate",
                    "operad_source_colours": ["State"],
                    "operad_target_colour": "Receipt",
                    "residual_effect": "contractive",
                }],
                operad_dir=root,
            )
        self.assertFalse(report["ok"])
        self.assertEqual(report["refused_count"], 1)
        self.assertIn("UNVERIFIED_RESIDUAL_EFFECT", report["refused"][0]["reason"])

    def test_ingest_refuses_path_like_skill_id(self) -> None:
        temporary, root = self._operad_dir()
        with temporary:
            report = propose_ingest(
                [{
                    "skill_id": "../escape",
                    "name": "candidate",
                    "operad_source_colours": ["State"],
                    "operad_target_colour": "Receipt",
                }],
                operad_dir=root,
            )
        self.assertFalse(report["ok"])
        self.assertIn("INVALID_SKILL_ID", report["refused"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
