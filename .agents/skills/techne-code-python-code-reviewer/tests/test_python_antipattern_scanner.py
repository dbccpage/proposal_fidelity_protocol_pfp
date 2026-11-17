"""Unit tests for Python anti-pattern and architecture scanner skill harness."""

from __future__ import annotations

import importlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

ArchitectureConfig = importlib.import_module("python_development_office.domain").ArchitectureConfig
run_cli = importlib.import_module("python_development_office.frontend.cli").main
RuleRegistry = importlib.import_module("python_development_office.use_cases.rules.registry").RuleRegistry
scan_file_ast = importlib.import_module("python_development_office.use_cases.visitor").scan_file_ast


class TestPythonAntipatternScannerSkill(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ArchitectureConfig()
        self.registry = RuleRegistry.create_default()
        self.ast_rules = self.registry.ast_rules

    def _scan_snippet(self, code: str, is_test: bool = False):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings, _ = scan_file_ast(
                temp_path, self.ast_rules, self.config, is_test_file=is_test
            )
            return findings
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_detects_mutable_default_argument(self):
        code = """
def func_a(items=[]):
    pass

def func_b(mapping=dict()):
    pass

def func_c(items=None):
    items = items or []
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertEqual(rule_codes.count("MUTABLE_DEFAULT_ARG"), 2)

    def test_detects_is_with_literals(self):
        code = """
if x is 1000:
    pass

if s is "hello":
    pass

if flag is True:
    pass
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("IS_WITH_LITERAL", rule_codes)
        self.assertIn("EXPLICIT_BOOLEAN_COMPARISON", rule_codes)

    def test_detects_equality_with_none_and_booleans(self):
        code = """
if val == None:
    pass

if flag == True:
    pass

if status == False:
    pass
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("EQUALITY_WITH_NONE", rule_codes)
        self.assertIn("EXPLICIT_BOOLEAN_COMPARISON", rule_codes)

    def test_detects_builtin_shadowing(self):
        code = """
def compute():
    list = [1, 2, 3]
    dict = {'a': 1}
    return len(list)
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertEqual(rule_codes.count("BUILTIN_SHADOWING"), 2)

    def test_detects_type_equality_check(self):
        code = """
if type(x) == int:
    pass
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("TYPE_EQUALITY_CHECK", rule_codes)

    def test_detects_wildcard_import(self):
        code = """
from math import *
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("WILDCARD_IMPORT", rule_codes)

    def test_detects_swallowed_and_bare_exceptions(self):
        code = """
try:
    something()
except:
    pass

try:
    other()
except Exception:
    pass
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("BROAD_EXCEPTION_CATCH", rule_codes)

    def test_detects_mutating_method_assignment(self):
        code = """
lst = [3, 1, 2]
lst = lst.sort()
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("MUTATING_METHOD_ASSIGNMENT", rule_codes)

    def test_detects_range_len_indexing(self):
        code = """
for i in range(len(items)):
    print(items[i])
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("RANGE_LEN_INDEXING", rule_codes)

    def test_detects_deprecated_os_system_and_shell_true(self):
        code = """
import os
import subprocess

os.system("ls -la")
subprocess.run("cat file", shell=True)
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("OS_SYSTEM_DEPRECATED", rule_codes)
        self.assertIn("SUBPROCESS_SHELL_TRUE", rule_codes)

    def test_detects_missing_self_and_missing_super_init(self):
        code = """
class Base:
    def __init__(self):
        self.x = 1

class Child(Base):
    def __init__(self):
        self.y = 2

    def bad_method():
        return 42
"""
        findings = self._scan_snippet(code)
        rule_codes = [f.rule_code for f in findings]
        self.assertIn("MISSING_SUPER_INIT", rule_codes)
        self.assertIn("MISSING_SELF_ARGUMENT", rule_codes)


class TestScannerCli(unittest.TestCase):
    """The CLI is the skill's actual entrypoint; exercise it, not just the rules."""

    def _run(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = run_cli(list(argv))
        return code, buf.getvalue()

    def test_clean_tree_reports_no_findings(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "ok.py").write_text(
                "def add(a: int, b: int) -> int:\n    return a + b\n",
                encoding="utf-8",
            )
            code, out = self._run(td)
        self.assertEqual(code, 0)
        self.assertIn("No findings detected", out)

    def test_json_output_is_parseable_and_authority_none(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "bad.py").write_text(
                "def f(items=[]):\n    return items\n", encoding="utf-8"
            )
            code, out = self._run(td, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["authority_effect"], "None")
        self.assertIn("MUTABLE_DEFAULT_ARG", [f["rule_code"] for f in payload["findings"]])
        self.assertNotEqual(code, 0)

    def test_pitfalls_only_suppresses_architecture_rules(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "bad.py").write_text(
                "def f(items=[]):\n    return items\n", encoding="utf-8"
            )
            _, out = self._run(td, "--pitfalls-only", "--json")
        categories = {f["category"] for f in json.loads(out)["findings"]}
        self.assertNotIn("clean_arch", categories)

    def test_missing_target_is_a_failing_finding(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing"
            code, out = self._run(str(missing), "--json")
        payload = json.loads(out)
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["files_scanned"], 0)
        self.assertEqual(
            [f["rule_code"] for f in payload["findings"]],
            ["UNRESOLVED_SCAN_TARGET"],
        )

    def test_missing_explicit_config_is_refused_without_traceback(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                code = run_cli([".", "--config", str(missing)])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("CONFIG_ERROR: architecture config not found", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


class TestPortedConfig(unittest.TestCase):
    def test_no_sentinelpy_dependency_exceptions_are_carried(self):
        """Upstream shipped four debt entries naming operations
        modules that do not exist in CODA. Carrying them would be a debt
        register describing a different repository."""
        self.assertEqual(ArchitectureConfig().dependency_exceptions, ())

    def test_source_roots_exist_or_are_generic(self):
        repo_root = Path(__file__).resolve().parents[4]
        generic = {"src", "app", "scripts"}
        for root in ArchitectureConfig().source_roots:
            self.assertTrue(
                root in generic or (repo_root / root).exists(),
                f"source_root {root!r} is neither generic nor present in this repo",
            )


if __name__ == "__main__":
    unittest.main()
