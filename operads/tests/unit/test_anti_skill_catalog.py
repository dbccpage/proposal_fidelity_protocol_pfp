"""Anti-skill catalogue: one record per anti-pattern, colours read through the canon."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from operads.infrastructure import anti_skill_catalog_compiler as compiler

REPO = Path(__file__).resolve().parents[3]


def _write(root: Path, relative: str, frontmatter: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n\n## Detection Signature\n\n- x\n", encoding="utf-8")


def test_the_committed_catalogue_is_current() -> None:
    committed = (REPO / compiler.OUTPUT).read_bytes().replace(b"\r\n", b"\n")
    assert committed == compiler.render(compiler.compile_anti_skills(REPO))


def test_every_anti_pattern_is_a_candidate_record() -> None:
    catalog = compiler.compile_anti_skills(REPO)
    anti_patterns = [p for p in (REPO / compiler.ANTI_ROOT).rglob("*.md") if p.name.lower() != "readme.md"]
    assert catalog["summary"]["anti_skills"] == len(anti_patterns) == 93
    assert {r["status"] for r in catalog["anti_skills"]} == {"Candidate"}
    assert {r["detector"] for r in catalog["anti_skills"]} == {"UNBOUND"}


def test_witness_reads_as_audit() -> None:
    record = next(
        r for r in compiler.compile_anti_skills(REPO)["anti_skills"] if r["anti_skill_id"] == "AP_PY_013"
    )
    assert record["source_colours"] == ["Code"]
    assert record["target_colour"] == "Audit"
    assert record["pairing"] == "reciprocal"


@pytest.fixture
def estate(tmp_path: Path) -> Path:
    _write(tmp_path, "operads/patterns/helpful/py/HP_1_good.md", "pattern_id: HP_1\nname: good\ndual_pattern: AP_1\n")
    _write(tmp_path, "operads/patterns/helpful/py/HP_2_other.md", "pattern_id: HP_2\nname: other\ndual_pattern: AP_9\n")
    return tmp_path


def test_pairings(estate: Path) -> None:
    _write(estate, "operads/patterns/anti/py/AP_1_bad.md", "pattern_id: AP_1\nname: bad\ndual_pattern: HP_1_good\n")
    _write(estate, "operads/patterns/anti/py/AP_2_bad.md", "pattern_id: AP_2\nname: bad\ndual_pattern: HP_2\n")
    _write(estate, "operads/patterns/anti/py/AP_3_bad.md", "pattern_id: AP_3\nname: bad\ndual_pattern: HP_404\n")
    pairing = {r["anti_skill_id"]: r["pairing"] for r in compiler.compile_anti_skills(estate)["anti_skills"]}
    assert pairing == {"AP_1": "reciprocal", "AP_2": "one_sided", "AP_3": "unresolved"}


def test_an_unknown_colour_is_refused(estate: Path) -> None:
    _write(
        estate,
        "operads/patterns/anti/py/AP_1_bad.md",
        "pattern_id: AP_1\nname: bad\ndual_pattern: HP_1\noperad_source_colours: [Vibes]\n",
    )
    with pytest.raises(compiler.AntiSkillCatalogRefusal):
        compiler.compile_anti_skills(estate)


def test_duplicate_ids_are_refused(estate: Path) -> None:
    _write(estate, "operads/patterns/anti/py/AP_1_bad.md", "pattern_id: AP_1\nname: bad\ndual_pattern: HP_1\n")
    _write(estate, "operads/patterns/anti/rs/AP_1_bad.md", "pattern_id: AP_1\nname: bad\ndual_pattern: HP_1\n")
    with pytest.raises(compiler.AntiSkillCatalogRefusal):
        compiler.compile_anti_skills(estate)


def test_check_mode_reports_drift(tmp_path: Path, estate: Path) -> None:
    _write(estate, "operads/patterns/anti/py/AP_1_bad.md", "pattern_id: AP_1\nname: bad\ndual_pattern: HP_1\n")
    (estate / compiler.OUTPUT).parent.mkdir(parents=True)
    assert compiler.main(["--repo-root", str(estate), "--write"]) == 0
    assert compiler.main(["--repo-root", str(estate), "--check"]) == 0
    (estate / compiler.OUTPUT).write_text("{}", encoding="utf-8")
    assert compiler.main(["--repo-root", str(estate), "--check"]) == 1
    assert json.loads((estate / compiler.OUTPUT).read_text(encoding="utf-8")) == {}
