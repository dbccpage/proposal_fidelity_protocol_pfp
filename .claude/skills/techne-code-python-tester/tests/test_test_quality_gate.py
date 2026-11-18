from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT_PATH = SCRIPT_DIR / "test_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("python_test_quality_gate", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
scan_file = MODULE.scan_file


class TestQualityGateTests(unittest.TestCase):
    def test_gate_rejects_constant_and_or_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_bad.py"
            path.write_text(
                "def test_constant():\n    assert True\n\n"
                "def test_or_true():\n    assert value is not None or True\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["WEAK_ASSERTION", "WEAK_ASSERTION"],
            )

    def test_gate_rejects_assert_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_false.py"
            path.write_text("def test_fail():\n    assert False\n", encoding="utf-8")
            self.assertEqual([finding.code for finding in scan_file(path)], ["ASSERT_FALSE"])

    def test_gate_rejects_assert_on_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_tuple.py"
            path.write_text("def test_tuple():\n    assert (x, 'message')\n", encoding="utf-8")
            self.assertEqual([finding.code for finding in scan_file(path)], ["ASSERT_ON_TUPLE"])

    def test_gate_rejects_assert_on_string(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_string.py"
            path.write_text("def test_str():\n    assert 'some message'\n", encoding="utf-8")
            self.assertEqual([finding.code for finding in scan_file(path)], ["ASSERT_ON_STRING"])

    def test_gate_rejects_empty_test(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_empty.py"
            path.write_text('def test_empty():\n    """nothing"""\n    pass\n', encoding="utf-8")
            self.assertEqual([finding.code for finding in scan_file(path)], ["EMPTY_TEST"])

    def test_gate_rejects_tautology_eq(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_tautology.py"
            path.write_text(
                "def test_ones():\n    assert 1 == 1\n\n"
                "def test_strings():\n    assert 'x' == 'x'\n\n"
                "def test_bools():\n    assert False == False\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["TAUTOLOGY_EQ", "TAUTOLOGY_EQ", "TAUTOLOGY_EQ"],
            )

    def test_gate_rejects_weak_len(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_weak_len.py"
            path.write_text(
                "def test_gte():\n    assert len(items) >= 0\n\n"
                "def test_gt():\n    assert len(items) > -1\n\n"
                "def test_inverted():\n    assert 0 <= len(items)\n\n"
                "def test_negative_c():\n    assert len(items) >= -5\n\n"
                "def test_inverted_negative():\n    assert -1 < len(items)\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["WEAK_LEN", "WEAK_LEN", "WEAK_LEN", "WEAK_LEN", "WEAK_LEN"],
            )

    def test_gate_accepts_discriminating_len(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_good_len.py"
            path.write_text(
                "def test_positive_len():\n"
                "    assert len(items) > 0\n"
                "    assert len(items) >= 1\n"
                "    assert 1 <= len(items)\n"
                "    assert len(items) == 0\n"
                "    assert len(items) == 3\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_file(path), [])

    def test_gate_rejects_sys_path_hack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_sys_path.py"
            path.write_text(
                "import sys\n"
                "sys.path.insert(0, 'foo')\n"
                "sys.path.append('bar')\n"
                "def test_ok():\n    assert compute() == 42\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["SYS_PATH_HACK", "SYS_PATH_HACK"],
            )

    def test_gate_rejects_bare_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_bare_raises.py"
            path.write_text(
                "import pytest\n"
                "def test_bare():\n"
                "    with pytest.raises(Exception):\n"
                "        dangerous_call()\n\n"
                "def test_matched():\n"
                "    with pytest.raises(Exception, match='invalid'):\n"
                "        dangerous_call()\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["BARE_RAISES"],
            )

    def test_gate_rejects_no_assertion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_no_assert.py"
            path.write_text(
                "def test_print_only():\n    print('hello world')\n    result = 1 + 1\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [finding.code for finding in scan_file(path)],
                ["NO_ASSERTION"],
            )

    def test_gate_accepts_discriminating_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_good.py"
            path.write_text(
                "import pytest\n"
                "def test_sum():\n"
                "    assert 1 + 1 == 2\n"
                "    assert (1, 2) == (1, 2)\n"
                "    assert message == 'hello'\n"
                "def test_raises_specific():\n"
                "    with pytest.raises(ValueError):\n"
                "        int('bad')\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_file(path), [])


if __name__ == "__main__":
    unittest.main()
