"""Unit tests for AST pitfall rules in python_development_office."""

from __future__ import annotations

import unittest
from pathlib import Path

from operads.application.python_development_office.rules.registry import (
    RuleRegistry,
)
from operads.application.python_development_office.visitor import (
    scan_source_ast,
)
from operads.domain.python_development_office import (
    ArchitectureConfig,
)


class TestPythonPitfallRules(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ArchitectureConfig()
        self.registry = RuleRegistry.create_default()
        self.ast_rules = self.registry.ast_rules

    def _scan_snippet(self, code: str, is_test: bool = False):
        findings, _ = scan_source_ast(
            code, Path("snippet.py"), self.ast_rules, self.config, is_test_file=is_test
        )
        return findings

    def test_mutable_default_args(self) -> None:
        code = """
def bad1(items=[]):
    pass

def bad2(opts=dict()):
    pass

def good(items=None):
    items = items or []
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertEqual(codes.count("MUTABLE_DEFAULT_ARG"), 2)

    def test_inline_suppression(self) -> None:
        code = """
def bad1(items=[]):  # noqa: MUTABLE_DEFAULT_ARG
    pass

def bad2(opts=dict()):  # noqa
    pass

def bad3(s={}):
    pass
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertEqual(codes.count("MUTABLE_DEFAULT_ARG"), 1)

    def test_literal_identity_and_booleans(self) -> None:
        code = """
if x is 100:
    pass
if name is "test":
    pass
if status == True:
    pass
if val == None:
    pass
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertIn("IS_WITH_LITERAL", codes)
        self.assertIn("EXPLICIT_BOOLEAN_COMPARISON", codes)
        self.assertIn("EQUALITY_WITH_NONE", codes)

    def test_range_len_checks(self) -> None:
        code = """
for i in range(len(data)):
    print(data[i])

for j in range(0, len(data)):
    print(data[j])
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertEqual(codes.count("RANGE_LEN_INDEXING"), 2)

    def test_mutating_method_assignment(self) -> None:
        code = """
items = [3, 1, 2]
items = items.sort()
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertIn("MUTATING_METHOD_ASSIGNMENT", codes)

    def test_builtin_shadowing(self) -> None:
        code = """
def compute():
    list = [1, 2]
    dict = {'a': 1}
    return len(list)
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertEqual(codes.count("BUILTIN_SHADOWING"), 2)

    def test_exception_hygiene(self) -> None:
        code = """
try:
    f()
except:
    pass

try:
    g()
except Exception:
    pass
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertIn("BROAD_EXCEPTION_CATCH", codes)

    def test_missing_super_init(self) -> None:
        code = """
class Base:
    def __init__(self):
        self.a = 1

class Child(Base):
    def __init__(self):
        self.b = 2
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertIn("MISSING_SUPER_INIT", codes)

    def test_nested_function_missing_self_not_flagged(self) -> None:
        code = """
class Service:
    def process(self):
        def helper():
            return 42
        return helper()
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertNotIn("MISSING_SELF_ARGUMENT", codes)

    def test_strided_range_len_not_flagged(self) -> None:
        code = """
for i in range(0, len(items), 3):
    batch = items[i:i + 3]
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertNotIn("RANGE_LEN_INDEXING", codes)

    def test_eq_type_check_not_flagged(self) -> None:
        code = """
class ValueObject:
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return True
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertNotIn("TYPE_EQUALITY_CHECK", codes)

    def test_suppression_aliases_and_trailers(self) -> None:
        code = """
try:
    dangerous()
except Exception as exc:  # noqa: BLE001 - supervised boundary
    pass
"""
        findings = self._scan_snippet(code)
        codes = [f.rule_code for f in findings]
        self.assertNotIn("BROAD_EXCEPTION_CATCH", codes)


if __name__ == "__main__":
    unittest.main()
