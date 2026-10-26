# AuthorityEffect: None.
"""
Tests for participant packet artifacts and runner (C028).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from participant_packet.runner import load_solver_func, run_benchmark


class TestParticipantPacket(unittest.TestCase):
    def setUp(self):
        self.pkg_root = Path(__file__).resolve().parent.parent
        self.ex_dir = self.pkg_root / "participant_packet" / "examples"
        self.answers_path = self.pkg_root / "participant_packet" / "answers.jsonl"
        self.task_md = self.pkg_root / "participant_packet" / "TASK.md"
        self.accounting_json = self.pkg_root / "participant_packet" / "accounting.json"

    def test_artifacts_exist(self):
        self.assertTrue(self.ex_dir.is_dir())
        self.assertTrue(self.answers_path.is_file())
        self.assertTrue(self.task_md.is_file())
        self.assertTrue(self.accounting_json.is_file())

    def test_example_count(self):
        examples = list(self.ex_dir.glob("*.json"))
        self.assertGreaterEqual(len(examples), 10)

    def test_runner_execution(self):
        solver = load_solver_func()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = Path(tmp_dir) / "answers.jsonl"
            count = run_benchmark(self.ex_dir, tmp_out, solver)
            self.assertGreaterEqual(count, 10)
            self.assertTrue(tmp_out.is_file())


if __name__ == "__main__":
    unittest.main()
