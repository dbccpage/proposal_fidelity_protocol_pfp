"""Unit tests for ProjectScanner, module graph, and two-pass scan orchestration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from operads.application.python_development_office.project import (
    ProjectScanner,
)
from operads.domain.python_development_office import (
    ArchitectureConfig,
)
from operads.infrastructure.python_development_office.source_repository import (
    FileSystemSourceRepository,
)


class TestProjectScannerAndGraph(unittest.TestCase):
    def test_unreadable_utf8_source_is_a_finding_and_scan_continues(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "bad.py").write_bytes(b"\xff")
            (root / "good.py").write_text("answer = 42\n", encoding="utf-8")
            scanner = ProjectScanner(
                config=ArchitectureConfig(),
                project_root=root,
                sources=FileSystemSourceRepository(),
            )

            result = scanner.scan([root])

            self.assertEqual(result.files_scanned, 2)
            self.assertEqual(result.modules_indexed, 1)
            self.assertEqual(result.total_findings, 1)
            self.assertEqual(result.findings[0].rule_code, "UNPARSEABLE_FILE")
            self.assertEqual(result.findings[0].path, str(root / "bad.py"))

    def test_project_scanner_builds_graph_and_runs_two_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            # Create mock Clean Architecture project
            domain_dir = root / "myapp" / "domain"
            domain_dir.mkdir(parents=True)
            (domain_dir / "__init__.py").write_text("", encoding="utf-8")
            (domain_dir / "models.py").write_text(
                "import requests\n\ndef get_user(items=[]):\n    pass\n",
                encoding="utf-8",
            )

            usecase_dir = root / "myapp" / "use_cases"
            usecase_dir.mkdir(parents=True)
            (usecase_dir / "__init__.py").write_text("", encoding="utf-8")
            (usecase_dir / "service.py").write_text(
                "from myapp.domain.models import get_user\n",
                encoding="utf-8",
            )

            config = ArchitectureConfig()
            scanner = ProjectScanner(
                config=config, project_root=root, sources=FileSystemSourceRepository()
            )
            result = scanner.scan(targets=[root])

            self.assertEqual(result.files_scanned, 4)  # 2 inits + 2 modules
            self.assertGreaterEqual(result.modules_indexed, 2)

            codes = [f.rule_code for f in result.findings]
            # AST pitfall
            self.assertIn("MUTABLE_DEFAULT_ARG", codes)
            # DDD domain purity violation (requests in domain)
            self.assertIn("DDD_DOMAIN_IMPURE", codes)


if __name__ == "__main__":
    unittest.main()
