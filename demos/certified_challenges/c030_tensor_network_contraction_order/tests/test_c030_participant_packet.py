# AuthorityEffect: None.
"""Unit tests for Participant Packet in C030."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestParticipantPacket(unittest.TestCase):
    def setUp(self) -> None:
        self.pkg_dir = Path(__file__).resolve().parent.parent
        self.part_dir = self.pkg_dir / "participant_packet"

    def test_examples_exist(self) -> None:
        examples = list((self.part_dir / "examples").glob("*.json"))
        self.assertGreaterEqual(len(examples), 10)

    def test_accounting_json_bounds(self) -> None:
        acc_path = self.part_dir / "accounting.json"
        self.assertTrue(acc_path.exists())
        with open(acc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("cost_ceiling_usd", data)
        self.assertLessEqual(data["cost_ceiling_usd"], 1.00)
        self.assertLessEqual(data["target_cost_usd"], 0.05)

    def test_runner_execution(self) -> None:
        runner_path = self.part_dir / "runner.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answers.jsonl"
            res = subprocess.run(
                [sys.executable, str(runner_path), "--out", str(output_path)],
                capture_output=True,
                text=True,
                cwd=str(self.part_dir),
            )
            self.assertEqual(res.returncode, 0, f"runner failed: {res.stderr}")
            self.assertIn("Wrote 10 answers", res.stdout)
            self.assertTrue(output_path.is_file())


if __name__ == "__main__":
    unittest.main()
