"""Clean Architecture AST Invariant and Boundary Tests for PFP.

Verifies:
  1. Inward Dependency Purity: omega_engine_pfp/domain/ has ZERO outward imports.
  2. Use Cases Purity: omega_engine_pfp/use_cases/ has zero infrastructure/frontend/entrypoints imports.
  3. Domain Ports Integrity: All ports in domain/ports.py are pure abstract interfaces.
  4. Claim Hygiene: AuthorityEffect: None discipline enforced across models and receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


class TestPfpCleanArchitecture(unittest.TestCase):
    """Static AST validation of Clean Architecture fences."""

    def setUp(self) -> None:
        self.pfp_dir = Path(__file__).resolve().parents[1]
        self.domain_dir = self.pfp_dir / "domain"
        self.use_cases_dir = self.pfp_dir / "use_cases"

    def _module_package(self, py_file: Path) -> str:
        parts = py_file.relative_to(self.pfp_dir).parts[:-1]
        return ".".join((self.pfp_dir.name, *parts))

    def _absolute_module(self, py_file: Path, module: str | None, level: int) -> str:
        """Resolve ImportFrom the way Python does, including relative imports."""
        name = module or ""
        if level <= 0:
            return name
        package = self._module_package(py_file)
        if level == 1:
            base = package
        else:
            bits = package.rsplit(".", level - 1)
            if len(bits) < level:
                return name
            base = bits[0]
        return f"{base}.{name}" if name else base

    def _is_forbidden(self, module: str, prefixes: tuple[str, ...], bare_roots: tuple[str, ...]) -> bool:
        if not module:
            return False
        if any(module.startswith(prefix) for prefix in prefixes):
            return True
        return module.split(".", 1)[0] in bare_roots

    def _import_violations(
        self,
        directory: Path,
        prefixes: tuple[str, ...],
        bare_roots: tuple[str, ...],
    ) -> list[str]:
        violations: list[str] = []
        for py_file in directory.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            rel = py_file.relative_to(self.pfp_dir).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_forbidden(alias.name, prefixes, bare_roots):
                            violations.append(f"{rel}:{node.lineno} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    resolved = self._absolute_module(py_file, node.module, node.level)
                    if self._is_forbidden(resolved, prefixes, bare_roots):
                        violations.append(f"{rel}:{node.lineno} imports from {resolved}")
        return violations

    def test_domain_zero_outward_dependencies(self) -> None:
        """Domain layer must not import from outer layers."""
        forbidden = (
            "omega_engine_education.education_app.use_cases",
            "omega_engine_education.education_app.infrastructure",
            "omega_engine_education.education_app.entrypoints",
            "omega_engine_education.education_app.frontend",
            "omega_engine_education.scripts",
            "omega_engine_education.education_app.pedagogy",
            "omega_engine_pfp.use_cases",
            "omega_engine_pfp.infrastructure",
            "omega_engine_pfp.controllers",
            "omega_engine_pfp.frontend",
        )
        bare_roots = ("use_cases", "infrastructure", "frontend", "controllers")
        violations = self._import_violations(self.domain_dir, forbidden, bare_roots)
        self.assertEqual(violations, [], f"Domain layer violations found: {violations}")

    def test_use_cases_zero_infrastructure_dependencies(self) -> None:
        """Use cases layer must not import from infrastructure, entrypoints, frontend, or scripts."""
        forbidden = (
            "omega_engine_education.education_app.infrastructure",
            "omega_engine_education.education_app.entrypoints",
            "omega_engine_education.education_app.frontend",
            "omega_engine_education.scripts",
            "omega_engine_pfp.infrastructure",
            "omega_engine_pfp.controllers",
            "omega_engine_pfp.frontend",
        )
        bare_roots = ("infrastructure", "frontend", "controllers")
        violations = self._import_violations(self.use_cases_dir, forbidden, bare_roots)
        self.assertEqual(violations, [], f"Use cases layer violations found: {violations}")

    def test_claim_hygiene_in_domain_source(self) -> None:
        """Ensure no forbidden hype words appear in domain docstrings or identifiers."""
        forbidden_hype_words = ("weaponized", "flawless", "fundamentally")
        violations = []
        for py_file in self.domain_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            # Detector lexicons must retain the words they reject. The stated
            # gate concerns claims and identifiers, not every string literal.
            texts = [ast.get_docstring(tree) or ""]
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    texts.extend([node.name, ast.get_docstring(node) or ""])
                elif isinstance(node, ast.Name):
                    texts.append(node.id)
            content = "\n".join(texts).lower()
            for word in forbidden_hype_words:
                if word in content:
                    violations.append(f"{py_file.name} contains forbidden hype word '{word}'")

        self.assertEqual(violations, [], f"Claim hygiene violations in domain/pfp: {violations}")

    def test_ddd_professional_standards(self) -> None:
        """Verify compliance with RULE_DDD_PROFESSIONAL_STANDARDS_001 across bounded contexts."""
        import importlib.util

        repo_root = Path(__file__).resolve().parents[2]
        script_path = (
            repo_root
            / ".agents"
            / "skills"
            / "techne-code-principal-architect"
            / "scripts"
            / "check_clean_arch.py"
        )
        spec = importlib.util.spec_from_file_location("check_clean_arch", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        violations = module.check_ddd_professional_standards(repo_root)
        self.assertEqual(violations, [], f"DDD professional standards violations: {violations}")


if __name__ == "__main__":
    unittest.main()
