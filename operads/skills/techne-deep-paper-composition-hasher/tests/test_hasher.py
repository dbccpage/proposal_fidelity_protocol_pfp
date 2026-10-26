"""Unit and integration tests for the Deep Paper Composition Hasher skill."""

import hashlib
import json
import sys
import uuid
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import pytest
import yaml

from models import (
    AlignmentStatus,
    ClaimType,
    FormatCrossCheck,
    FormulaType,
    LocationAnchor,
    MathFormulaEntry,
    PaperCompositionManifest,
    PdfLocationAnchor,
    ProseClaimEntry,
    ProseLineEntry,
)
from hasher import (
    COMPOSITION_NAMESPACE,
    compute_sha256,
    derive_claim_uuid,
    derive_formula_uuid,
    derive_line_uuid,
    extract_math_symbols,
    normalize_latex,
    normalize_text,
    PaperCompositionExtractor,
    verify_zip_against_manifest,
)


def test_normalize_latex():
    """Verify LaTeX normalization strips outer delimiters and collapses whitespace."""
    raw1 = "$$ \\operatorname{Tr}( \\rho H ) $$"
    assert normalize_latex(raw1) == "\\operatorname{Tr}( \\rho H )"

    raw2 = "$  \\nu_e(t) \\le C e^{-\\mu d}  $"
    assert normalize_latex(raw2) == "\\nu_e(t) \\le C e^{-\\mu d}"

    raw3 = "\\[ H = \\sum_e h_e \\]"
    assert normalize_latex(raw3) == "H = \\sum_e h_e"


def test_extract_math_symbols():
    """Verify symbol token extraction captures operators and Greek letters."""
    latex = "\\operatorname{Tr}(\\rho_A) \\le \\sum_{e} \\|h_e\\|_\\infty \\nu_e"
    symbols = extract_math_symbols(latex)
    assert "\\operatorname{Tr}" in symbols
    assert "\\rho" in symbols
    assert "\\sum" in symbols
    assert "\\nu" in symbols


def test_uuid_determinism():
    """Verify deterministic UUIDv5 generation is identical across independent invocations."""
    u1 = derive_formula_uuid("\\operatorname{Tr}(\\rho)", FormulaType.DISPLAY, 1)
    u2 = derive_formula_uuid("\\operatorname{Tr}(\\rho)", FormulaType.DISPLAY, 1)
    assert u1 == u2
    assert isinstance(u1, uuid.UUID)

    c1 = derive_claim_uuid("Theorem 5.1", "All product states satisfy the bound.")
    c2 = derive_claim_uuid("Theorem 5.1", "All product states satisfy the bound.")
    assert c1 == c2


def test_pydantic_manifest_serialization():
    """Verify PaperCompositionManifest roundtrips losslessly through Pydantic, JSON, and YAML."""
    f_uuid = derive_formula_uuid("E = mc^2", FormulaType.INLINE, 1)
    c_uuid = derive_claim_uuid("Theorem 1.1", "Energy equals mass times speed of light squared.")

    formula = MathFormulaEntry(
        uuid=f_uuid,
        formula_type=FormulaType.INLINE,
        raw_latex="E = mc^2",
        normalized_latex="E = mc^2",
        sha256_raw=compute_sha256("E = mc^2"),
        sha256_normalized=compute_sha256("E = mc^2"),
        md_location=LocationAnchor(
            file_type="md",
            file_path="paper.md",
            start_line=10,
            end_line=10,
            environment="inline_dollar",
        ),
        ast_symbols=["E", "m", "c"],
    )

    claim = ProseClaimEntry(
        uuid=c_uuid,
        claim_type=ClaimType.THEOREM,
        label="Theorem 1.1",
        statement_text="Energy equals mass times speed of light squared.",
        normalized_text="Energy equals mass times speed of light squared.",
        sha256_statement=compute_sha256("Energy equals mass times speed of light squared."),
        referenced_formula_uuids=[f_uuid],
        claim_ledger_id="V1",
    )

    manifest = PaperCompositionManifest(
        paper_id="TEST-001",
        paper_title="Test Paper",
        manuscript_version="v1.0.0",
        timestamp_utc="2026-10-11T12:00:00Z",
        total_formulas_extracted=1,
        total_claims_extracted=1,
        total_lines_hashed=10,
        formulas={str(f_uuid): formula},
        claims={str(c_uuid): claim},
        code_binding_coverage=1.0,
        lean_binding_coverage=1.0,
        hygiene_clean_status=True,
    )

    # JSON roundtrip
    json_str = manifest.model_dump_json()
    reloaded = PaperCompositionManifest.model_validate_json(json_str)
    assert reloaded.paper_id == "TEST-001"
    assert str(f_uuid) in reloaded.formulas
    assert reloaded.formulas[str(f_uuid)].normalized_latex == "E = mc^2"

    # YAML roundtrip
    yaml_dict = yaml.safe_load(json_str)
    yaml_str = yaml.dump(yaml_dict)
    from_yaml = yaml.safe_load(yaml_str)
    assert from_yaml["paper_id"] == "TEST-001"
    assert from_yaml["total_formulas_extracted"] == 1


def test_extractor_on_mock_paper(tmp_path: Path):
    """Test extractor on a hermetic mock paper directory."""
    paper_dir = tmp_path / "000_projection_obstruction"
    paper_dir.mkdir()

    md_content = """# Test Title

## Section 1: Intro

Here is some text with inline math $\\rho \\in \\mathcal{S}(\\mathcal{H})$.

$$
\\operatorname{Tr}(\\rho) = 1
$$

### Theorem 1.1 (Normalization)
Every density operator satisfies trace normalization $\\operatorname{Tr}(\\rho) = 1$.

### Proposition E.6 (Trace Form)
The Jordan trace form is positive-invariant.
"""
    (paper_dir / "projection_obstruction.md").write_text(md_content, encoding="utf-8")

    tex_content = """\\section{Section 1: Intro}
Here is text.
\\begin{equation}
\\operatorname{Tr}(\\rho) = 1
\\end{equation}
"""
    (paper_dir / "projection_obstruction.tex").write_text(tex_content, encoding="utf-8")

    extractor = PaperCompositionExtractor(paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.paper_id == "PO-000"
    assert manifest.total_formulas_extracted >= 2  # 1 inline, 1 display
    assert manifest.total_claims_extracted == 2   # Theorem 1.1, Proposition E.6
    assert manifest.total_lines_hashed > 10
    assert manifest.hygiene_clean_status is True
    formula_checks = [item for item in manifest.cross_format_checks if item.item_type == "formula"]
    assert any(
        item.status == AlignmentStatus.EXACT_MATCH and item.tex_sha256 == item.md_sha256
        for item in formula_checks
    )
    claim_checks = [item for item in manifest.cross_format_checks if item.item_type == "claim"]
    assert claim_checks
    assert all(item.status == AlignmentStatus.UNMATCHED for item in claim_checks)


def test_forbidden_word_hygiene(tmp_path: Path):
    """Verify that forbidden promotional verbs trigger hygiene warnings."""
    paper_dir = tmp_path / "slop_paper"
    paper_dir.mkdir()

    md_content = """# Slop Paper
This simply proves that the algorithm is universal and flawless.
"""
    (paper_dir / "projection_obstruction.md").write_text(md_content, encoding="utf-8")

    extractor = PaperCompositionExtractor(paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.hygiene_clean_status is False
    assert len(manifest.hygiene_warnings) >= 1
    assert any("proves" in w for w in manifest.hygiene_warnings)


def test_references_section_hygiene_exemption(tmp_path: Path):
    """Verify that bibliography citation titles in the References section are exempted from claim hygiene warnings."""
    paper_dir = tmp_path / "paper_with_refs"
    paper_dir.mkdir()

    md_content = """# Clean Paper

## Section 1: Introduction
We establish bounds on projection defects under strictly defined hypotheses.

## References

1. J. C. Cresswell, "Universal entanglement timescale for Rényi entropies," Phys. Rev. A 97 (2018), 022317.
2. A. Author, "A universal lower bound that proves convergence," J. Math. Phys. (2020).
"""
    (paper_dir / "projection_obstruction.md").write_text(md_content, encoding="utf-8")

    extractor = PaperCompositionExtractor(paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.hygiene_clean_status is True
    assert len(manifest.hygiene_warnings) == 0


def _bound_manifest(code_bindings: list[str], lean_bindings: list[str]) -> PaperCompositionManifest:
    formula_id = uuid.uuid4()
    formula = MathFormulaEntry(
        uuid=formula_id,
        formula_type=FormulaType.DISPLAY,
        raw_latex="E = mc^2",
        normalized_latex="E = mc^2",
        sha256_raw=compute_sha256("E = mc^2"),
        sha256_normalized=compute_sha256("E = mc^2"),
        code_bindings=code_bindings,
        lean_bindings=lean_bindings,
    )
    return PaperCompositionManifest(
        paper_id="PO-000",
        paper_title="Zip contract",
        manuscript_version="6.9.14",
        timestamp_utc="2026-10-11T00:00:00+00:00",
        total_formulas_extracted=1,
        total_claims_extracted=0,
        total_lines_hashed=0,
        formulas={str(formula_id): formula},
        code_binding_coverage=0.0,
        lean_binding_coverage=0.0,
        hygiene_clean_status=True,
    )


def test_verify_zip_receipt_persistence(tmp_path: Path):
    """A zip passes only when every bound path is a member, and the receipt stores its digest."""
    zip_path = tmp_path / "test_release.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("code/quantum_lattice.py", "# python code\n")
        archive.writestr("lean4/Po000JordanTrace.lean", "-- lean code\n")
        archive.writestr("other.py", "# unrelated\n")

    manifest = _bound_manifest(
        ["code/quantum_lattice.py"],
        ["lean4/Po000JordanTrace.lean:JordanTrace"],
    )
    receipt_file = tmp_path / "paper_composition_receipt.json"
    receipt = verify_zip_against_manifest(zip_path, manifest, receipt_path=receipt_file)

    assert receipt["status"] == "PASS"
    assert receipt["zip_sha256"] == hashlib.sha256(zip_path.read_bytes()).hexdigest()
    assert receipt["matched_python_modules"] == ["code/quantum_lattice.py"]
    assert receipt["matched_lean_modules"] == ["lean4/Po000JordanTrace.lean"]
    assert "other.py" not in receipt["matched_python_modules"]
    saved = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert saved["status"] == "PASS"
    assert saved["zip_sha256"] == receipt["zip_sha256"]


def test_verify_zip_fails_closed(tmp_path: Path):
    """No bindings, or a zip that only contains an unrelated module, is a failure."""
    unrelated = tmp_path / "unrelated.zip"
    with zipfile.ZipFile(unrelated, "w") as archive:
        archive.writestr("code/not_bound.py", "# python code\n")

    empty = verify_zip_against_manifest(unrelated, _bound_manifest([], []))
    assert empty["status"] == "FAIL"
    assert empty["required_paths"] == []

    missing = verify_zip_against_manifest(
        unrelated,
        _bound_manifest(["code/quantum_lattice.py"], ["lean4/Po000JordanTrace.lean"]),
    )
    assert missing["status"] == "FAIL"
    assert "code/quantum_lattice.py" in missing["missing_paths"]
    assert missing["matched_python_modules"] == []


def test_verify_zip_cross_checks_checksum_manifest_and_descriptions(tmp_path: Path):
    """When SHA256SUMS or docs/descriptions.md exists, missing members fail closed."""
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    docs_dir = paper_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "descriptions.md").write_text("Zenodo descriptions\n", encoding="utf-8")
    (paper_dir / "SHA256SUMS").write_text(
        "abc12345  docs/descriptions.md\n"
        "def67890  code/quantum_lattice.py\n",
        encoding="utf-8",
    )
    zip_path = paper_dir / "paper.zip"
    # Create zip missing docs/descriptions.md
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("code/quantum_lattice.py", "x = 1\n")

    manifest = _bound_manifest(["code/quantum_lattice.py"], [])
    receipt = verify_zip_against_manifest(zip_path, manifest)
    assert receipt["status"] == "FAIL"
    assert "docs/descriptions.md" in receipt["missing_paths"]

    # Now create complete zip
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("code/quantum_lattice.py", "x = 1\n")
        archive.writestr("docs/descriptions.md", "Zenodo descriptions\n")

    receipt_pass = verify_zip_against_manifest(zip_path, manifest)
    assert receipt_pass["status"] == "PASS"
    assert "docs/descriptions.md" not in receipt_pass["missing_paths"]


def test_pdf_symbol_is_not_an_exact_match(tmp_path: Path):
    """A page that merely contains a symbol does not match a formula or a missing claim."""
    paper_dir = tmp_path / "symbol_paper"
    paper_dir.mkdir()
    (paper_dir / "projection_obstruction.md").write_text("# Title\n", encoding="utf-8")
    formula_id = uuid.uuid4()
    formula = MathFormulaEntry(
        uuid=formula_id,
        formula_type=FormulaType.DISPLAY,
        raw_latex=r"\rho = 1",
        normalized_latex=r"\rho = 1",
        sha256_raw=compute_sha256(r"\rho = 1"),
        sha256_normalized=compute_sha256(r"\rho = 1"),
        ast_symbols=["H", r"\rho"],
    )
    claim_id = uuid.uuid4()
    claim = ProseClaimEntry(
        uuid=claim_id,
        claim_type=ClaimType.THEOREM,
        label="Theorem 9.9",
        statement_text="A stated bound.",
        normalized_text="A stated bound.",
        sha256_statement=compute_sha256("A stated bound."),
    )
    extractor = PaperCompositionExtractor(paper_dir)
    checks = extractor.cross_check_formats([formula], [claim], {}, {1: "H rho"})
    formula_check = next(item for item in checks if item.item_type == "formula")
    claim_check = next(item for item in checks if item.item_type == "claim")
    assert formula_check.status == AlignmentStatus.UNMATCHED
    assert formula_check.pdf_matched is False
    assert claim_check.status == AlignmentStatus.UNMATCHED
    assert claim_check.pdf_matched is False


def test_element_level_bindings(tmp_path: Path):
    """Verify that element-level lists code_bindings, referenced_formula_uuids, and claim_ledger_id are populated."""
    paper_dir = tmp_path / "binding_paper"
    paper_dir.mkdir()

    # Create dummy claim ledger
    ledger_yaml = """paper_identity:
  paper_id: "PO-000"
claims:
  - claim_id: "V6914-TRACE"
    title: "Proposition E.6: Jordan trace form"
    paper_pointer:
      heading: "Proposition E.6"
    evidence:
      - kind: "python"
        file_location: "code/quantum_lattice.py"
      - kind: "lean4"
        file_location: "lean4/Po000JordanTrace.lean"
"""
    (paper_dir / "projection_obstruction_claim_ledger.yaml").write_text(ledger_yaml, encoding="utf-8")

    # Create dummy code and lean files
    code_dir = paper_dir / "code"
    code_dir.mkdir()
    (code_dir / "quantum_lattice.py").write_text("def trace_distance(): pass\n", encoding="utf-8")

    lean_dir = paper_dir / "lean4"
    lean_dir.mkdir()
    (lean_dir / "Po000JordanTrace.lean").write_text("theorem JordanTrace : True := trivial\n", encoding="utf-8")

    md_content = """# Title

## Section 1

### Proposition E.6 (Jordan Trace Form)
The Jordan trace form satisfies:
$$
\\operatorname{Tr}(\\rho) = 1
$$
and is positive-invariant.
"""
    (paper_dir / "projection_obstruction.md").write_text(md_content, encoding="utf-8")

    extractor = PaperCompositionExtractor(paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.total_claims_extracted == 1
    claim = list(manifest.claims.values())[0]

    assert claim.claim_ledger_id == "V6914-TRACE"
    assert len(claim.referenced_formula_uuids) >= 1
    assert len(claim.code_bindings) >= 1
    assert "code/quantum_lattice.py" in claim.code_bindings
    assert len(claim.lean_bindings) >= 1

    # Check formula bindings
    formula_uuid_str = str(claim.referenced_formula_uuids[0])
    assert formula_uuid_str in manifest.formulas
    formula = manifest.formulas[formula_uuid_str]
    assert len(formula.code_bindings) >= 1
    assert "code/quantum_lattice.py" in formula.code_bindings


def test_lean4_module_and_code_evidence_ledger_bindings(tmp_path):
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()

    md_content = """# Title

## Theorem 1 (Route C Landing)

$$
N(6) \\le 3
$$
"""
    (paper_dir / "paper.md").write_text(md_content, encoding="utf-8")

    ledger_content = """paper_id: "010_mub6"
claims:
  - id: "MUB6-C01"
    title: "Theorem 1"
    paper_pointer:
      heading: "Theorem 1"
    lean4:
      module: "RouteCFourierLandingBypass"
      theorems:
        - "fourier_count_ge_five"
    code_evidence:
      tests:
        - "tests/test_route_c_fourier_landing.py::test_transition_graph_combinatorics_21_edges"
"""
    (paper_dir / "claim_ledger.yaml").write_text(ledger_content, encoding="utf-8")

    extractor = PaperCompositionExtractor(paper_dir=paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.total_claims_extracted == 1
    claim = list(manifest.claims.values())[0]
    assert claim.claim_ledger_id == "MUB6-C01"
    assert "lean4/RouteCFourierLandingBypass.lean" in claim.lean_bindings
    assert "tests/test_route_c_fourier_landing.py" in claim.code_bindings


def test_bracket_and_paren_math_and_byte_offsets(tmp_path: Path):
    """Verify \\[...\\] and \\(...\\) formulas are extracted with byte offsets and TeX location anchors."""
    paper_dir = tmp_path / "lggr_test_paper"
    paper_dir.mkdir()

    md_content = """---
title: "Bracket Math Test"
author: "Jeremy H. Carroll"
date: "2026-10-15"
version: "1.2.4"
---

# Bracket Math Test

Inline paren math \\(\\Delta_E = E_g - E_1 E_2\\) and display bracket math:

\\[
\\Delta_E \\in \\{-1, 0, 1\\}
\\]
"""
    (paper_dir / "lggr_test_paper.md").write_text(md_content, encoding="utf-8")
    tex_content = """\\section{Intro}
Inline \\(\\Delta_E = E_g - E_1 E_2\\) and display:
\\[
\\Delta_E \\in \\{-1, 0, 1\\}
\\]
"""
    (paper_dir / "lggr_test_paper.tex").write_text(tex_content, encoding="utf-8")
    (paper_dir / "zenodo_metadata.json").write_text(
        json.dumps({
            "title": "Bracket Math Test",
            "version": "1.2.4",
            "publication_date": "2026-10-15",
            "creators": [{"name": "Carroll, Jeremy H."}],
        }),
        encoding="utf-8",
    )

    extractor = PaperCompositionExtractor(paper_dir=paper_dir)
    manifest = extractor.build_manifest()

    assert manifest.manuscript_version == "1.2.4"
    assert manifest.total_formulas_extracted == 2
    assert manifest.identity_checks["consistent"] is True
    assert manifest.dialect_warnings == []

    disp_formulas = [f for f in manifest.formulas.values() if f.formula_type == FormulaType.DISPLAY]
    assert len(disp_formulas) == 1
    df = disp_formulas[0]
    assert df.md_location is not None
    assert df.md_location.start_byte_offset is not None
    assert df.md_location.end_byte_offset > df.md_location.start_byte_offset
    assert df.md_location.location_sha256 is not None
    assert df.tex_location is not None
    assert df.tex_location.location_sha256 is not None


def test_dialect_and_identity_mismatch_detection(tmp_path: Path):
    """Verify in-house jargon, courtroom boilerplate, and version/date drift are flagged."""
    paper_dir = tmp_path / "drift_paper"
    paper_dir.mkdir()

    md_content = """# Drift Paper

**Author:** Jeremy H. Carroll
**Version:** 2.0.0
**Date:** 2026-10-15

AuthorityEffect: None.
**Deposit status.** Withdrawn as a theorem of this deposit. See [scope](REVIEW_SCOPE.md) and Paper 001.
"""
    (paper_dir / "drift_paper.md").write_text(md_content, encoding="utf-8")
    (paper_dir / "zenodo_metadata.json").write_text(
        json.dumps({
            "title": "Drift Paper",
            "version": "1.9.0",
            "publication_date": "2026-09-01",
            "creators": [{"name": "Carroll, Jeremy H."}],
        }),
        encoding="utf-8",
    )

    extractor = PaperCompositionExtractor(paper_dir=paper_dir)
    manifest = extractor.build_manifest()

    assert len(manifest.dialect_warnings) >= 4
    assert any("AuthorityEffect" in w for w in manifest.dialect_warnings)
    assert any("withdrawn theorem stamp" in w for w in manifest.dialect_warnings)
    assert any("REVIEW_SCOPE" in w for w in manifest.dialect_warnings)
    assert any("naked in-house paper number" in w for w in manifest.dialect_warnings)
    assert manifest.identity_checks["consistent"] is False
    assert len(manifest.identity_checks["mismatches"]) == 2
