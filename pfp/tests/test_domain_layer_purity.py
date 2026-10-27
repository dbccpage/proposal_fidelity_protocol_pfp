"""Targeted Clean Architecture Layer Purity Test.

Verifies that domain modules in `pfp/domain/cohomology`
and `pfp/domain/ddc` have zero imports from outer layers,
specifically `ffi.py` (process FFI seam) and `infrastructure/`.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


class TestDomainLayerPurity(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.symbol_game_root = self.repo_root / "pfp"
        self.cohomology_dir = self.symbol_game_root / "domain" / "cohomology"
        self.ddc_dir = self.symbol_game_root / "domain" / "ddc"

    def _get_imports(self, py_path: Path) -> list[tuple[int, str]]:
        """Parse Python source and extract all import targets and their line numbers."""
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        imports: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                # node.module can be None for relative imports like `from . import foo`
                mod = node.module or ""
                dots = "." * node.level
                full_rel = f"{dots}{mod}" if node.level > 0 else mod
                imports.append((node.lineno, full_rel))
        return imports

    def _check_forbidden_imports(self, target_dir: Path) -> list[str]:
        """Check all python files in target_dir for imports from ffi or infrastructure."""
        violations: list[str] = []
        py_files = sorted(target_dir.glob("*.py"))
        for py_path in py_files:
            rel_path = py_path.relative_to(self.symbol_game_root)
            imports = self._get_imports(py_path)
            for lineno, imp in imports:
                # Level 3 relative import from domain/cohomology/foo.py:
                # `...ffi` resolves to `pfp.ffi`
                # `...infrastructure` resolves to `pfp.infrastructure`
                is_ffi = (
                    imp == "...ffi"
                    or imp.endswith(".ffi")
                    or "pfp.ffi" in imp
                )
                is_infra = (
                    imp == "...infrastructure"
                    or ".infrastructure" in imp
                    or "pfp.infrastructure" in imp
                )
                if is_ffi:
                    violations.append(
                        f"{rel_path}:{lineno} illegally imports FFI seam '{imp}'"
                    )
                if is_infra:
                    violations.append(
                        f"{rel_path}:{lineno} illegally imports infrastructure '{imp}'"
                    )
        return violations

    def test_domain_ddc_zero_outer_imports(self) -> None:
        """Verify domain/ddc has zero imports from ffi or infrastructure."""
        violations = self._check_forbidden_imports(self.ddc_dir)
        self.assertEqual(
            violations,
            [],
            f"Found forbidden outer-layer imports in {self.ddc_dir}:\n" + "\n".join(violations),
        )

    def test_domain_cohomology_zero_outer_imports(self) -> None:
        """Verify domain/cohomology has zero imports from ffi or infrastructure."""
        violations = self._check_forbidden_imports(self.cohomology_dir)
        self.assertEqual(
            violations,
            [],
            f"Found forbidden outer-layer imports in {self.cohomology_dir}:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
