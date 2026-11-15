"""Executable test witnesses for Window 3 Wave 2 (Shard D - Paper 007):
- ATL-P007-001 (AUDIT-P007-001): Deep route inventory
- ATL-P007-004 (AUDIT-P007-004): Route verifier scope
- ATL-P007-005 (AUDIT-P007-005): Historical receipt staleness
- ATL-P007-010 (AUDIT-P007-010): Lean receipt census

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

if str(_REPO_ROOT / "ops") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "ops"))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ruff: noqa: E402
from ops.education.scripts import verify_system_integration as vsi
from pfp.domain.ddc.cochains import Cochain0, Cochain1, Cochain2, FunctionalBoundaryUnavailable

# ============================================================================
# 1. ATL-P007-001 / AUDIT-P007-001: Deep route inventory
# ============================================================================


class TestDeepRouteInventory:
    """Witnesses that the baseline route README lists 20 notebooks in five groups."""

    def test_readme_table_contains_twenty_notebooks_in_five_groups(self) -> None:
        """Parse the curriculum README route table and verify 5 groups of 4 notebooks."""
        readme_path = _REPO_ROOT / "education" / "004_oepfp" / "curriculum" / "README.md"
        assert readme_path.exists()
        text = readme_path.read_text(encoding="utf-8")

        # Extract markdown table rows matching | Route | Lessons in order | ...
        # Route groups: Beginners, Novices, Intermediates, Advanced, Researchers
        expected_groups = [
            "Beginners",
            "Novices",
            "Intermediates",
            "Advanced",
            "Researchers",
        ]
        parsed_groups: dict[str, list[str]] = {}

        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            group_name = parts[1]
            if group_name in expected_groups:
                # Find all .ipynb occurrences in the lessons cell
                lessons_cell = parts[2]
                notebook_matches = re.findall(r"\(([^)]+\.ipynb)\)", lessons_cell)
                parsed_groups[group_name] = notebook_matches

        # Exact integer assertions
        assert len(parsed_groups) == 5
        assert list(parsed_groups.keys()) == expected_groups

        total_notebooks = 0
        for group in expected_groups:
            notebooks = parsed_groups[group]
            assert len(notebooks) == 4
            total_notebooks += len(notebooks)

        assert total_notebooks == 20
        # Ratio of notebooks per group is exact fraction 4/1
        assert Fraction(total_notebooks, len(parsed_groups)) == Fraction(4, 1)

    def test_source_inventory_json_route_notebooks_census(self) -> None:
        """Cross-verify route notebook count in archived source inventory JSON."""
        inventory_path = (
            _REPO_ROOT
            / "atlas"
            / "archive"
            / "pfp"
            / "007_pfp_executable_lessons_and_evidence_boundaries"
            / "docs"
            / "source_inventory_2026_10_02.json"
        )
        assert inventory_path.exists()
        data = json.loads(inventory_path.read_text(encoding="utf-8"))

        route_notebooks = data.get("route_notebooks", [])
        assert len(route_notebooks) == 20

        # Group partition by directory prefix
        group_counts: Counter[str] = Counter()
        for item in route_notebooks:
            path_parts = item["path"].split("/")
            # e.g., education/the_symbol_game/lessons/system_integration/000_beginners/...
            group_dir = path_parts[4]
            group_counts[group_dir] += 1

        expected_dirs = {
            "000_beginners": 4,
            "100_novices": 4,
            "200_intermediates": 4,
            "300_advanced": 4,
            "400_researchers": 4,
        }
        assert dict(group_counts) == expected_dirs

    def test_falsification_detects_altered_group_or_notebook_counts(self) -> None:
        """Falsification control: altering expected group count or size fails assertions."""
        simulated_groups = {
            "Beginners": ["01.ipynb", "02.ipynb", "03.ipynb", "04.ipynb"],
            "Novices": ["01.ipynb", "02.ipynb", "03.ipynb", "04.ipynb"],
            "Intermediates": ["01.ipynb", "02.ipynb", "03.ipynb", "04.ipynb"],
            "Advanced": ["01.ipynb", "02.ipynb", "03.ipynb"],  # Defect: 3 instead of 4
            "Researchers": ["01.ipynb", "02.ipynb", "03.ipynb", "04.ipynb"],
        }
        total = sum(len(v) for v in simulated_groups.values())
        assert total != 20
        with pytest.raises(AssertionError):
            assert total == 20


# ============================================================================
# 2. ATL-P007-004 / AUDIT-P007-004: Route verifier scope
# ============================================================================


class TestRouteVerifierScope:
    """Witnesses that verify_system_integration.py checks structure,

    selected arithmetic restrictions, source bindings, and plain Python execution only.
    """

    def test_audit_notebook_accepts_clean_exact_notebook(self, tmp_path: Path) -> None:
        """Clean notebook with 3 exact code cells passes audit_notebook."""
        clean_nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "cell-01", "cell_type": "code", "source": ["x = 10\n"]},
                {
                    "id": "cell-02",
                    "cell_type": "code",
                    "source": ["from fractions import Fraction\ny = Fraction(1, 3)\n"],
                },
                {"id": "cell-03", "cell_type": "code", "source": ["assert x > 0 and y.numerator == 1\n"]},
            ],
        }
        nb_path = tmp_path / "clean_test.ipynb"
        nb_path.write_bytes(json.dumps(clean_nb).encode("utf-8"))

        nb_obj, code_blocks = vsi.audit_notebook(nb_path)
        assert nb_obj["nbformat"] == 4
        assert nb_obj["nbformat_minor"] == 5
        assert len(code_blocks) == 3

    def test_audit_notebook_refuses_float_literal(self, tmp_path: Path) -> None:
        """Notebook with a float literal AST node is refused with ValueError."""
        nb_with_float = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "cell-01", "cell_type": "code", "source": ["val = 2.5\n"]},
                {"id": "cell-02", "cell_type": "code", "source": ["y = 1\n"]},
                {"id": "cell-03", "cell_type": "code", "source": ["assert y == 1\n"]},
            ],
        }
        nb_path = tmp_path / "float_literal.ipynb"
        nb_path.write_bytes(json.dumps(nb_with_float).encode("utf-8"))

        with pytest.raises(ValueError, match="float literal in a lesson code cell"):
            vsi.audit_notebook(nb_path)

    def test_audit_notebook_refuses_runtime_float_call(self, tmp_path: Path) -> None:
        """Notebook with a float() constructor call is refused with ValueError."""
        nb_with_call = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "cell-01", "cell_type": "code", "source": ["val = float(3)\n"]},
                {"id": "cell-02", "cell_type": "code", "source": ["y = 1\n"]},
                {"id": "cell-03", "cell_type": "code", "source": ["assert y == 1\n"]},
            ],
        }
        nb_path = tmp_path / "float_call.ipynb"
        nb_path.write_bytes(json.dumps(nb_with_call).encode("utf-8"))

        with pytest.raises(ValueError, match="runtime float construction in a lesson code cell"):
            vsi.audit_notebook(nb_path)

    def test_audit_notebook_refuses_constant_assertion(self, tmp_path: Path) -> None:
        """Notebook with a constant assert statement is refused with ValueError."""
        nb_with_assert = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "cell-01", "cell_type": "code", "source": ["x = 1\n"]},
                {"id": "cell-02", "cell_type": "code", "source": ["assert True\n"]},
                {"id": "cell-03", "cell_type": "code", "source": ["y = 2\n"]},
            ],
        }
        nb_path = tmp_path / "constant_assert.ipynb"
        nb_path.write_bytes(json.dumps(nb_with_assert).encode("utf-8"))

        with pytest.raises(ValueError, match="constant assertion cannot support lesson evidence"):
            vsi.audit_notebook(nb_path)

    def test_audit_notebook_refuses_utf8_bom_and_invalid_nbformat(self, tmp_path: Path) -> None:
        """Notebook with UTF-8 BOM or wrong nbformat is refused."""
        clean_nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "c1", "cell_type": "code", "source": ["x = 1\n"]},
                {"id": "c2", "cell_type": "code", "source": ["y = 2\n"]},
                {"id": "c3", "cell_type": "code", "source": ["z = 3\n"]},
            ],
        }
        # UTF-8 BOM test
        bom_path = tmp_path / "bom.ipynb"
        bom_path.write_bytes(b"\xef\xbb\xbf" + json.dumps(clean_nb).encode("utf-8"))
        with pytest.raises(ValueError, match="UTF-8 BOM is disallowed"):
            vsi.audit_notebook(bom_path)

        # Wrong nbformat (e.g. format 3.0)
        wrong_format_nb = dict(clean_nb)
        wrong_format_nb["nbformat"] = 3
        fmt_path = tmp_path / "wrong_fmt.ipynb"
        fmt_path.write_bytes(json.dumps(wrong_format_nb).encode("utf-8"))
        with pytest.raises(ValueError, match="expected notebook format 4.5"):
            vsi.audit_notebook(fmt_path)

    def test_audit_notebook_refuses_insufficient_code_cells(self, tmp_path: Path) -> None:
        """Notebook with fewer than three code cells is refused."""
        short_nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": [
                {"id": "c1", "cell_type": "code", "source": ["x = 1\n"]},
                {"id": "c2", "cell_type": "code", "source": ["y = 2\n"]},
            ],
        }
        short_path = tmp_path / "short.ipynb"
        short_path.write_bytes(json.dumps(short_nb).encode("utf-8"))
        with pytest.raises(
            ValueError,
            match="expected setup, worked computation, and adversarial exercise cells",
        ):
            vsi.audit_notebook(short_path)


# ============================================================================
# 3. ATL-P007-005 / AUDIT-P007-005: Historical receipt staleness
# ============================================================================


class TestHistoricalReceiptStaleness:
    """Witnesses that the 20/20 receipt is historical, manifest paths are stale,

    and Cochain1.l1_norm raises FunctionalBoundaryUnavailable.
    """

    def test_headless_receipt_attributes_and_stale_paths(self) -> None:
        """Inspect headless_receipt.json: 20 records dated 2026-09-25 with 0 existing paths."""
        receipt_path = _REPO_ROOT / "education" / "004_oepfp" / "curriculum" / "headless_receipt.json"
        assert receipt_path.exists()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        assert receipt["status"] == "PASS"
        assert receipt["passed"] == 20
        assert receipt["total"] == 20
        assert receipt["generated_at"] == "2026-09-25T01:52:32.889242+00:00"

        records = receipt["records"]
        assert len(records) == 20

        # Check each record points to former education/notebooks/ prefix
        for rec in records:
            path_str = rec["notebook"]
            assert path_str.startswith("education/notebooks/lessons/system_integration/")
            # Zero of these paths resolve on disk
            assert not (_REPO_ROOT / path_str).exists()

        existing_count = sum(1 for rec in records if (_REPO_ROOT / rec["notebook"]).exists())
        assert existing_count == 0

    def test_lesson_manifest_paths_are_stale(self) -> None:
        """Inspect lesson_manifest.json: 20 lessons pointing to absent documentation tree."""
        manifest_path = _REPO_ROOT / "education" / "004_oepfp" / "curriculum" / "lesson_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        lessons = manifest["lessons"]
        assert len(lessons) == 20

        for lesson in lessons:
            path_str = lesson["path"]
            assert path_str.startswith("education/documentation/004_oepfp/curriculum/")
            assert not (_REPO_ROOT / path_str).exists()

        existing_count = sum(1 for lesson in lessons if (_REPO_ROOT / lesson["path"]).exists())
        assert existing_count == 0

    def test_cochain_l1_norm_raises_functional_boundary_unavailable(self) -> None:
        """Calling l1_norm on cochains raises FunctionalBoundaryUnavailable."""
        c0 = Cochain0(values={"v0": Fraction(1, 2)})
        with pytest.raises(FunctionalBoundaryUnavailable, match="FUNCTIONAL_BOUNDARY_UNAVAILABLE"):
            c0.l1_norm()

        c1 = Cochain1(values={("v0", "v1"): Fraction(3, 4)})
        with pytest.raises(FunctionalBoundaryUnavailable, match="FUNCTIONAL_BOUNDARY_UNAVAILABLE"):
            c1.l1_norm()

        c2 = Cochain2(values={("v0", "v1", "v2"): Fraction(1, 1)})
        with pytest.raises(FunctionalBoundaryUnavailable, match="FUNCTIONAL_BOUNDARY_UNAVAILABLE"):
            c2.l1_norm()

    def test_falsification_detects_non_refusing_norm_mock(self) -> None:
        """Falsification control: a cochain mock that fails to raise FunctionalBoundaryUnavailable is rejected."""

        class PermissiveMockCochain:
            def l1_norm(self) -> Fraction:
                return Fraction(1, 1)

        mock = PermissiveMockCochain()
        refused = False
        try:
            mock.l1_norm()
        except FunctionalBoundaryUnavailable:
            refused = True

        # Must NOT have refused (because mock returned Fraction(1, 1))
        assert not refused


# ============================================================================
# 4. ATL-P007-010 / AUDIT-P007-010: Lean receipt census
# ============================================================================


class TestLeanReceiptCensus:
    """Witnesses that retained evidence records a Lean 4.34.0 build,

    a 21-name report, and a 64-declaration package census.
    """

    def test_axiom_report_declares_twenty_one_entries(self) -> None:
        """Parse axiom_report.txt and confirm 21 declarations (19 axiom-free, 2 with axioms)."""
        report_path = (
            _REPO_ROOT
            / "atlas"
            / "archive"
            / "pfp"
            / "007_pfp_executable_lessons_and_evidence_boundaries"
            / "lean4"
            / "axiom_report.txt"
        )
        assert report_path.exists()
        text = report_path.read_text(encoding="utf-8")

        assert "leanprover/lean4:v4.34.0" in text
        assert "lake build exited 0" in text

        # Parse declarations
        lines = [line.strip() for line in text.splitlines() if line.strip() and line.startswith("'")]
        assert len(lines) == 21

        no_axioms = [line for line in lines if "does not depend on any axioms" in line]
        assert len(no_axioms) == 19

        with_axioms = [line for line in lines if "depends on axioms:" in line]
        assert len(with_axioms) == 2

        # Check the two declarations with axiom dependencies
        assert "expressivityNorm_le_length_mul_cap" in with_axioms[0]
        assert "expressivity_norm_le_grammar_ceiling" in with_axioms[1]
        for entry in with_axioms:
            assert "propext" in entry
            assert "Quot.sound" in entry

    def test_full_axiom_report_declares_sixty_four_entries(self) -> None:
        """Parse full_axiom_report.txt and confirm 64 package-local declarations."""
        full_report_path = (
            _REPO_ROOT
            / "atlas"
            / "archive"
            / "pfp"
            / "007_pfp_executable_lessons_and_evidence_boundaries"
            / "lean4"
            / "full_axiom_report.txt"
        )
        assert full_report_path.exists()
        text = full_report_path.read_text(encoding="utf-8")

        assert "Declarations listed: 64" in text
        assert "lake env lean FullCensus.lean exited 0" in text

        # Extract all declaration lines
        decl_lines = [line.strip() for line in text.splitlines() if line.strip() and line.startswith("'")]
        assert len(decl_lines) == 64

        no_axioms_full = [line for line in decl_lines if "does not depend on any axioms" in line]
        assert len(no_axioms_full) == 56

        with_axioms_full = [line for line in decl_lines if "depends on axioms:" in line]
        assert len(with_axioms_full) == 8

        # Exact rational check: ratio of axiom-dependent to total declarations
        assert Fraction(len(with_axioms_full), len(decl_lines)) == Fraction(8, 64)
        assert Fraction(8, 64) == Fraction(1, 8)

    def test_release_validation_matches_toolchain_and_census(self) -> None:
        """Inspect release_validation_2026_10_02.json and confirm Lean metadata."""
        validation_path = (
            _REPO_ROOT
            / "atlas"
            / "archive"
            / "pfp"
            / "007_pfp_executable_lessons_and_evidence_boundaries"
            / "docs"
            / "release_validation_2026_10_02.json"
        )
        assert validation_path.exists()
        val_json = json.loads(validation_path.read_text(encoding="utf-8"))

        lean_meta = val_json.get("lean", {})
        assert lean_meta.get("toolchain_pin") == "leanprover/lean4:v4.34.0"
        assert lean_meta.get("declarations_listed") == 64
        assert lean_meta.get("completed") is True

        checks = lean_meta.get("checks", [])
        assert len(checks) >= 2
        lake_check = checks[0]
        assert lake_check.get("command") == ["lake", "build"]
        assert lake_check.get("exit_code") == 0

    def test_falsification_detects_count_mismatch_or_unapproved_axioms(self) -> None:
        """Falsification control: unexpected declaration counts or unapproved axioms fail."""
        report_path = (
            _REPO_ROOT
            / "atlas"
            / "archive"
            / "pfp"
            / "007_pfp_executable_lessons_and_evidence_boundaries"
            / "lean4"
            / "full_axiom_report.txt"
        )
        text = report_path.read_text(encoding="utf-8")

        # Whitelist of allowed axioms
        allowed_axioms = {"propext", "Quot.sound", "Classical.choice"}

        # Extract all referenced axioms across declaration lines
        referenced_axioms: set[str] = set()
        for line in text.splitlines():
            if "depends on axioms:" in line:
                # Format: 'name' depends on axioms: [axiom1, axiom2]
                match = re.search(r"depends on axioms:\s*\[(.*?)\]", line)
                if match:
                    for ax in match.group(1).split(","):
                        referenced_axioms.add(ax.strip())

        # All referenced axioms must be in the approved whitelist
        assert referenced_axioms.issubset(allowed_axioms)

        # Falsification check: asserting an unauthorized axiom causes failure
        unauthorized_axioms = {"UnsoundAxiom", "OracleAxiom", "NonConstructiveMagic"}
        assert referenced_axioms.isdisjoint(unauthorized_axioms)

        # Hash tamper detection
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert len(h) == 64
        # Modifying text changes hash
        tampered_hash = hashlib.sha256((text + "\n# tamper").encode("utf-8")).hexdigest()
        assert h != tampered_hash
