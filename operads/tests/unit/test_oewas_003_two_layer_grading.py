"""EPIC-OE-OEWAS-003 grading falsifiers.

Substitution does not grade. A missing ``invocation:`` line is not entry.
The live composition is legal; the same edge with an entry inner is not.
``evidence_trace.json`` is not a BLAKE3 receipt.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from operads.skill_operad.application.use_cases import (
    validate_operad_use_case as operad_grading,
)

load_entry_skills = operad_grading.load_entry_skills
validate_composition_grading = operad_grading.validate_composition_grading

_REPO = Path(__file__).resolve().parents[3]
_MATRIX_DEFAULT = (
    _REPO / "operads" / "skill_operad" / "json" / "composition_matrix.json"
)
_MATRIX = _MATRIX_DEFAULT if _MATRIX_DEFAULT.is_file() else (_REPO / ".agents" / "skill_operads" / "composition_matrix.json")
_TRACE_DEFAULT = (
    _REPO / "operads" / "skill_operad" / "json" / "evidence_trace.json"
)
_TRACE = _TRACE_DEFAULT if _TRACE_DEFAULT.is_file() else (_REPO / ".agents" / "skill_operads" / "evidence_trace.json")
_SKILLS = _REPO / ".agents" / "skills"


def _skill(root: Path, folder: str, frontmatter: str) -> None:
    package = root / folder
    package.mkdir()
    (package / "SKILL.md").write_text(
        f"---\nname: {folder}\n{frontmatter}---\n\nbody\n",
        encoding="utf-8",
        newline="\n",
    )


def test_omitted_and_discipline_invocation_are_not_entry(tmp_path: Path) -> None:
    """Mutation: treat a missing line as entry and the omitted package is admitted."""
    _skill(tmp_path, "omitted", "")
    _skill(tmp_path, "disciplined", "invocation: discipline\n")
    _skill(tmp_path, "entered", "invocation: entry\n")

    entries = load_entry_skills(tmp_path)

    assert entries == {"entered"}


def test_replacing_the_inner_with_an_entry_skill_is_a_grading_violation() -> None:
    """Mutation: drop the ``inner in terminal_entries`` check and this stays silent."""
    matrix = json.loads(_MATRIX.read_text(encoding="utf-8"))
    assert matrix["compositions"] == []

    entries = load_entry_skills(_SKILLS)
    assert "rip-papers" not in entries
    assert "auto-oe-autop" in entries
    assert "panep-lean-snippet-export" not in entries

    legal, _terminal = validate_composition_grading(
        [
            {
                "outer": "auto-oe-autop",
                "inner": "panep-lean-snippet-export",
                "composite_id": "entry-over-discipline",
            }
        ],
        entries,
    )
    assert legal == []

    errors, _terminal = validate_composition_grading(
        [
            {
                "outer": "panep-lean-snippet-export",
                "inner": "auto-oe-autop",
                "composite_id": "discipline-over-entry",
            }
        ],
        entries,
    )

    assert len(errors) == 1
    assert errors[0].startswith("Two-Layer Grading Violation")
    assert "auto-oe-autop" in errors[0]


def test_composition_matrix_is_not_a_blake3_evidence_trace() -> None:
    """The composition file and the phi trace are different records."""
    matrix = json.loads(_MATRIX.read_text(encoding="utf-8"))
    trace = json.loads(_TRACE.read_text(encoding="utf-8"))

    assert "compositions" in matrix
    assert isinstance(trace, list)
    assert trace
    assert "phi_before" in trace[0]
    assert "blake3" not in json.dumps(matrix).lower()
    assert "blake3" not in json.dumps(trace).lower()


def test_entry_skills_cross_host_parity() -> None:
    """All active host roots must agree on admitted entry skills."""
    reference = load_entry_skills(_SKILLS)
    for host in [".claude", ".codex", ".grok"]:
        host_skills = _REPO / host / "skills"
        if host_skills.exists():
            assert load_entry_skills(host_skills) == reference
