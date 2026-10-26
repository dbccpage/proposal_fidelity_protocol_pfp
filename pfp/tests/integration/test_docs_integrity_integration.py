from __future__ import annotations

from omega_engine_pfp.documentation_integrity.inventory import (
    ClassificationContext,
    classify_source,
)


def _context(path: str, *, state: str = "tracked") -> ClassificationContext:
    contract = {
        "documentation_root": "docs",
        "education_copy_sets": [],
    }
    return ClassificationContext(
        contract,
        {},
        {},
        {},
        path,
        {"id": "documentation", "path": "docs"},
        state,
        "file",
    )


def test_documentation_markdown_is_classified_as_canonical_source() -> None:
    row = classify_source(_context("docs/reference/page.md"))
    assert row["primary_disposition"] == "canonical_source"
    assert row["destination_docs"] == ["reference/page.md"]


def test_ignored_material_is_explicitly_exempt() -> None:
    row = classify_source(_context("docs/.cache/item.bin", state="ignored"))
    assert row["mapping_status"] == "exempt"
    assert row["claim_status"] == "transient"
    assert row["exemption_reason"]
