from __future__ import annotations

import os
import json
import unittest
from unittest.mock import patch

from pathlib import Path
import sys

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from dispatch import dispatch_target


class DispatchResolutionTests(unittest.TestCase):
    def test_registered_skill_is_resolved_not_executed(self) -> None:
        result = dispatch_target("github")
        self.assertTrue(result.is_success)
        value = result.unwrap()
        self.assertEqual(value["status"], "RESOLVED_NOT_EXECUTED")
        self.assertIs(value["executed"], False)

    def test_unknown_target_is_typed_failure(self) -> None:
        result = dispatch_target("definitely-not-a-skill")
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "TARGET_NOT_FOUND")

    def test_declared_license_with_reconciled_colours_resolves(self) -> None:
        real_load = json.load
        def mock_load(f):
            data = real_load(f)
            if isinstance(data, dict) and "agents" in data and not data["agents"]:
                return {
                    "agents": {
                        "math-prof": {
                            "sub_operad": ["Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State"],
                            "licensed_skills": ["operad-quotient-verifier"],
                        }
                    }
                }
            return data

        with patch("dispatch.json.load", side_effect=mock_load):
            result = dispatch_target("operad-quotient-verifier", "math-prof")
            self.assertTrue(result.is_success)
            value = result.unwrap()
            self.assertEqual(value["status"], "RESOLVED_NOT_EXECUTED")
            self.assertIs(value["executed"], False)

    def test_valid_workflow_resolves(self) -> None:
        result = dispatch_target("contract_compliance_audit_workflow")
        self.assertTrue(result.is_success)
        value = result.unwrap()
        self.assertEqual(value["status"], "RESOLVED_NOT_EXECUTED")
        self.assertIs(value["executed"], False)


if __name__ == "__main__":
    unittest.main()
