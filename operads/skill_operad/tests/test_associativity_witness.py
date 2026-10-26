"""Registration and refusal gates for the live composition matrix.

The former paper-build associativity witness depended on a deliberately removed
operation.  This gate checks only currently admitted endpoints and prevents the
stale identifiers from silently returning.

AuthorityEffect: None. Structural registration only.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from coloured_operad import ColouredOperad


class CompositionRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.comp_path = (
            _SHARED_DIR / "json" / "composition_matrix.json"
            if (_SHARED_DIR / "json" / "composition_matrix.json").is_file()
            else _SHARED_DIR / "composition_matrix.json"
        )
        cls.sig_path = (
            _SHARED_DIR / "json" / "operad_signature.json"
            if (_SHARED_DIR / "json" / "operad_signature.json").is_file()
            else _SHARED_DIR / "operad_signature.json"
        )
        with open(cls.comp_path, encoding="utf-8") as f:
            cls.comp_data = json.load(f)
        with open(cls.sig_path, encoding="utf-8") as f:
            cls.sig = json.load(f)

    def _live_operad(self) -> ColouredOperad:
        operad = ColouredOperad("AssociativityWitnessTest")
        for col in self.sig["colours"]:
            operad.add_colour(col)
        for op in self.sig["operations"]:
            operad.add_operation(
                op_id=op["skill_id"],
                name=op["name"],
                source_colours=op["source_colours"],
                target_colour=op["target_colour"],
                equivariant=op.get("equivariant", False),
                residual_effect=op.get("residual_effect", "unknown"),
            )
        return operad

    def test_every_declared_composition_registers_with_declared_signature(self) -> None:
        operad = self._live_operad()
        for c in self.comp_data["compositions"]:
            res = operad.add_composition(
                outer=c["outer"],
                slot=c["slot"],
                inner=c["inner"],
                result=c.get("composite_id", c.get("result", "composite_op")),
            )
            self.assertTrue(
                res.is_success,
                f"composition failed for {c.get('composite_id')}: "
                f"{getattr(getattr(res, 'error', None), 'message', res)}",
            )
            composite = operad.operations[c["composite_id"]]
            self.assertEqual([colour.name for colour in composite.source], c["source_colours"])
            self.assertEqual(composite.target.name, c["target_colour"])
            self.assertTrue(c["type_valid"])

    def test_exact_live_composition_is_pinned(self) -> None:
        self.assertEqual(self.comp_data["compositions"], [])

    def test_removed_build_identifiers_have_no_claims(self) -> None:
        serialized = json.dumps(self.comp_data, sort_keys=True)
        self.assertNotIn("panepistimion-paper-build", serialized)
        self.assertNotIn("paper-build-release", serialized)
        self.assertEqual(self.comp_data.get("associativity_laws"), [])

    def test_unknown_endpoint_is_refused_without_synthesizing_result(self) -> None:
        operad = self._live_operad()
        result = operad.add_composition(
            outer="panepistimion-paper-build",
            slot=0,
            inner="panep-lean-snippet-export",
            result="unbacked-paper-build-composite",
        )
        self.assertTrue(result.is_failure)
        self.assertEqual(result.unwrap_err().code, "UNKNOWN_OPERATION")
        self.assertNotIn("unbacked-paper-build-composite", operad.operations)


if __name__ == "__main__":
    unittest.main()
