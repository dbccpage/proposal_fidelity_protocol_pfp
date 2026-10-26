import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import regen_spine_index as r


def test_extract_paper_rows(tmp_path):
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "001_Projection_Obstruction.md").write_text("# x", encoding="utf-8")
    (pub / "000_Primitive Axiomatics.md").write_text("# y", encoding="utf-8")
    rows = r.extract_paper_rows(pub, tmp_path)
    assert [row[0] for row in rows] == ["000", "001"]
    assert rows[1][1] == "Projection Obstruction"
    assert rows[0][2] == "pub/000_Primitive Axiomatics.md"


def test_folderized_paper_titled_with_companion_token(tmp_path):
    # A paper whose own title contains a companion token (e.g. "Audit") must
    # still be indexed: the file stem matching the folder name IS the paper.
    pub = tmp_path / "pub"
    folder = pub / "qm_004_state_effect_pairing_audit"
    folder.mkdir(parents=True)
    (folder / "qm_004_state_effect_pairing_audit.md").write_text("# p", encoding="utf-8")
    (folder / "qm_004_state_effect_pairing_audit_claim_ledger.md").write_text(
        "# l", encoding="utf-8"
    )
    rows = r.extract_paper_rows(pub, tmp_path)
    assert [row[0] for row in rows] == ["QM_004"]
    assert rows[0][1] == "State Effect Pairing Audit"


def test_nested_series_monograph_is_indexed_without_ledger(tmp_path):
    pub = tmp_path / "pub"
    series = pub / "040_Symbol_Game_Series"
    monograph_dir = series / "041_the_symbol_game"
    monograph_dir.mkdir(parents=True)
    (monograph_dir / "040m_the_symbol_game_monograph.md").write_text(
        "# monograph", encoding="utf-8"
    )
    (monograph_dir / "040m_the_symbol_game_proof_ledger.md").write_text(
        "# ledger", encoding="utf-8"
    )

    rows = r.extract_paper_rows(pub, tmp_path)

    assert rows == [
        (
            "040m",
            "the symbol game monograph",
            "pub/040_Symbol_Game_Series/041_the_symbol_game/040m_the_symbol_game_monograph.md",
        )
    ]


def test_extract_gtoc_rows(tmp_path):
    gt = r.gtoc_papers_dir(tmp_path)
    (gt / "001_GTFOC").mkdir(parents=True)
    (gt / "001_GTFOC" / "paper.md").write_text("# p", encoding="utf-8")
    (gt / "001_GTFOC" / "_inventory.md").write_text("# i", encoding="utf-8")
    (gt / "001_GTFOC" / "theorem_ledger.md").write_text("# t", encoding="utf-8")
    (gt / "999_gtoc").mkdir()
    (gt / "999_gtoc" / "00_series_charter.md").write_text("# c", encoding="utf-8")
    (gt / "gt_tower_master_design.md").write_text("# d", encoding="utf-8")
    (gt / "_goal_report.md").write_text("# g", encoding="utf-8")
    rows = r.extract_gtoc_rows(gt, tmp_path)
    assert [(row[0], row[1]) for row in rows] == [
        ("gt001", "CODA-FOC"),
        ("gt999", "GTOC"),
        ("gt", "GT tower master design"),
    ]
    assert rows[0][2].endswith("001_GTFOC/paper.md")
    assert rows[1][2].endswith("999_gtoc/00_series_charter.md")


def test_extract_gtoc_rows_missing_dir(tmp_path):
    assert r.extract_gtoc_rows(r.gtoc_papers_dir(tmp_path), tmp_path) == []


def test_gtoc_ids_never_collide_with_published_ids(tmp_path):
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "001_Projection_Obstruction.md").write_text("# x", encoding="utf-8")
    gt = r.gtoc_papers_dir(tmp_path)
    (gt / "001_GTFOC").mkdir(parents=True)
    (gt / "001_GTFOC" / "paper.md").write_text("# p", encoding="utf-8")
    paper_ids = {row[0] for row in r.extract_paper_rows(pub, tmp_path)}
    gtoc_ids = {row[0] for row in r.extract_gtoc_rows(gt, tmp_path)}
    assert paper_ids == {"001"}
    assert gtoc_ids == {"gt001"}
    assert not paper_ids & gtoc_ids


def test_generate_renders_gtoc_section_when_present(tmp_path):
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "001_Foo_Bar.md").write_text("# z", encoding="utf-8")
    spine = tmp_path / "spine.md"
    spine.write_text("## I. Base\n", encoding="utf-8")
    gt = r.gtoc_papers_dir(tmp_path)
    (gt / "002_GTFDA").mkdir(parents=True)
    (gt / "002_GTFDA" / "paper.md").write_text("# p", encoding="utf-8")
    out = r.generate(pub, spine, tmp_path)
    assert "## GTOC foundations tower" in out
    assert "| gt002 | CODA-FDA |" in out


def test_extract_spine_headings(tmp_path):
    spine = tmp_path / "spine.md"
    spine.write_text("# Title\n## I. Base\n### I.1 Sub\ntext\n#### too deep\n", encoding="utf-8")
    assert r.extract_spine_headings(spine) == ["## I. Base", "### I.1 Sub"]


def test_generate_contains_all_sections(tmp_path):
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "001_Foo_Bar.md").write_text("# z", encoding="utf-8")
    spine = tmp_path / "spine.md"
    spine.write_text("## I. Base\n", encoding="utf-8")
    out = r.generate(pub, spine, tmp_path)
    assert "## Paper index" in out
    assert "| 001 | Foo Bar |" in out
    assert "## Spine section anchors" in out
    assert "## Routing table" in out
    assert "Langlands" in out  # extension row present


def _anchor_lines(out: str) -> list[str]:
    body = out.split("## Spine section anchors", 1)[1]
    body = body.split("## Routing table", 1)[0]
    return [ln for ln in body.splitlines() if ln.strip().startswith("- ")]


def test_spine_anchors_strip_hashes_and_indent_by_level(tmp_path):
    """The anchor branch was dead: its regex was `r"...\\\\s+..."`, a literal
    backslash, so no heading ever matched and every anchor rendered as the raw
    line `- ## I. Base`. Nothing covered it, so nothing caught it."""
    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "001_Foo_Bar.md").write_text("# z", encoding="utf-8")
    spine = tmp_path / "spine.md"
    spine.write_text("## I. Base\n### I.1 Sub\n## II. Next\n", encoding="utf-8")

    anchors = _anchor_lines(r.generate(pub, spine, tmp_path))

    assert anchors == ["- I. Base", "  - I.1 Sub", "- II. Next"]
    assert not any("#" in line for line in anchors)


def test_nested_coda_ground_up_is_discovered_without_blank_support_rows(tmp_path):
    pub = tmp_path / "omega_engine" / "research" / "published"
    tower = pub / "001_coda" / "coda_fda"
    ground = pub / "001_coda" / "gtoc" / "001_gtoc_time"
    controls = pub / "001_coda" / "gtoc"
    book = pub / "001_coda" / "009_coda"
    unassigned = pub / "001_coda" / "gtoc" / "011_calculus_of_observation"
    tower.mkdir(parents=True)
    ground.mkdir(parents=True)
    book.mkdir(parents=True)
    unassigned.mkdir(parents=True)
    (tower / "paper.md").write_text("# tower", encoding="utf-8")
    (ground / "001_gtoc_time.md").write_text("# time", encoding="utf-8")
    (controls / "00_series_charter.md").write_text("# charter", encoding="utf-8")
    (book / "README.md").write_text("# book", encoding="utf-8")
    (unassigned / "calculus_of_obstruction.md").write_text(
        "# not yet assigned a paper id", encoding="utf-8"
    )

    rows = r.extract_paper_rows(pub, tmp_path)

    assert {(r.qualify_paper_id(pid, rel), rel) for pid, _, rel in rows} == {
        (
            "gg001",
            "omega_engine/research/published/001_coda/gtoc/001_gtoc_time/001_gtoc_time.md",
        ),
    }
    assert all(pid for pid, _, _ in rows)


def test_gtoc_rows_follow_relocated_coda_estate(tmp_path):
    estate = r.gtoc_papers_dir(tmp_path)
    layer = estate / "coda_foc"
    controls = estate / "gtoc"
    book = estate / "009_coda"
    layer.mkdir(parents=True)
    controls.mkdir(parents=True)
    book.mkdir(parents=True)
    (layer / "paper.md").write_text("# layer", encoding="utf-8")
    (controls / "00_series_charter.md").write_text("# charter", encoding="utf-8")
    (book / "gt_tower_master_design.md").write_text("# design", encoding="utf-8")

    rows = r.extract_gtoc_rows(estate, tmp_path)

    assert [pid for pid, _, _ in rows] == ["gt000", "gt008", "gt009"]


def test_programme_overview_does_not_duplicate_local_paper_zero(tmp_path):
    pub = tmp_path / "omega_engine" / "research" / "published"
    programme = pub / "000_witnessed_difference"
    paper = programme / "000_wd0_5"
    paper.mkdir(parents=True)
    (programme / "000_witnessed_difference.md").write_text("# programme overview", encoding="utf-8")
    (paper / "000_wd0_5.md").write_text("# paper", encoding="utf-8")

    rows = r.extract_paper_rows(pub, tmp_path)

    assert [(r.qualify_paper_id(pid, rel), rel) for pid, _, rel in rows] == [
        (
            "wd000",
            "omega_engine/research/published/000_witnessed_difference/000_wd0_5/000_wd0_5.md",
        )
    ]


def test_gtoc_entry_resolves_from_folder_named_md(tmp_path):
    """Relocated papers are named after their folder: 007_gtla/007_gtla.md."""
    estate = r.gtoc_papers_dir(tmp_path)
    layer = estate / "007_gtla"
    layer.mkdir(parents=True)
    (layer / "007_gtla.md").write_text("# gtla", encoding="utf-8")
    (layer / "007_gtla_change_log.md").write_text("# log", encoding="utf-8")
    rows = r.extract_gtoc_rows(estate, tmp_path)
    assert [(pid, claim) for pid, claim, _ in rows] == [("gt007", "GTLA")]
    assert rows[0][2].endswith("007_gtla/007_gtla.md")


def test_gtoc_entry_resolves_from_layer_suffix_md(tmp_path):
    """006_coda_a holds coda_a.md -- the suffix, not the full folder name."""
    estate = r.gtoc_papers_dir(tmp_path)
    layer = estate / "006_coda_a"
    layer.mkdir(parents=True)
    (layer / "coda_a.md").write_text("# a", encoding="utf-8")
    rows = r.extract_gtoc_rows(estate, tmp_path)
    assert [(pid, claim) for pid, claim, _ in rows] == [("gt006", "CODA-A")]
    assert rows[0][2].endswith("006_coda_a/coda_a.md")


def test_gtoc_entry_prefers_paper_md_when_present(tmp_path):
    estate = r.gtoc_papers_dir(tmp_path)
    layer = estate / "007_gtla"
    layer.mkdir(parents=True)
    (layer / "paper.md").write_text("# p", encoding="utf-8")
    (layer / "007_gtla.md").write_text("# g", encoding="utf-8")
    rows = r.extract_gtoc_rows(estate, tmp_path)
    assert rows[0][2].endswith("007_gtla/paper.md")


def test_gtoc_book_dir_without_entry_yields_only_master_design(tmp_path):
    """009_coda has no 009_coda.md -- it is the book, not a layer paper."""
    estate = r.gtoc_papers_dir(tmp_path)
    book = estate / "009_coda"
    book.mkdir(parents=True)
    (book / "009_coda_change_log.md").write_text("# log", encoding="utf-8")
    (book / "gt_tower_master_design.md").write_text("# d", encoding="utf-8")
    rows = r.extract_gtoc_rows(estate, tmp_path)
    assert [pid for pid, _, _ in rows] == ["gt009"]
    assert rows[0][1] == "CODA tower master design"
