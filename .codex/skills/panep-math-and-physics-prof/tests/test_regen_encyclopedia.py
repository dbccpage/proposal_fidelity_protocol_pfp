import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import regen_encyclopedia as r


def test_paper_alias_pid_families():
    # published NNN[a], QM qmNNN[a], the GTOC tower gtocpN, and the
    # 008_engine_runtime programme erNNN all mint views; unknown families do
    # not (prevents accidental paper:NNN collisions).
    assert r._PAPER_ALIAS_RE.match("paper:004:Theorem-3").group(1) == "004"
    assert r._PAPER_ALIAS_RE.match("paper:000b:C2").group(1) == "000b"
    assert r._PAPER_ALIAS_RE.match("paper:qm028:U1SELECTOR-001").group(1) == "qm028"
    assert r._PAPER_ALIAS_RE.match("paper:gtocp2:P2-C5").group(1) == "gtocp2"
    assert r._PAPER_ALIAS_RE.match("paper:gtocp2a:P2-C5").group(1) == "gtocp2a"
    assert r._PAPER_ALIAS_RE.match("paper:gtocp3:P3-C5").group(1) == "gtocp3"
    assert r._PAPER_ALIAS_RE.match("paper:tuft101:THM-9").group(1) == "tuft101"
    assert r._PAPER_ALIAS_RE.match("paper:er004:C36").group(1) == "er004"
    assert r._PAPER_ALIAS_RE.match("paper:er008:C12").group(1) == "er008"
    # erNNN must stay distinct from the flat published NNN it displaced
    assert r._PAPER_ALIAS_RE.match("paper:004:C36").group(1) != "er004"
    assert r._PAPER_ALIAS_RE.match("pl:PL-000-1") is None
    assert r._PAPER_ALIAS_RE.match("paper:gtoc:P2-C5") is None


def test_parse_gtmur_heading_strips_markdown_marker():
    assert r._parse_stmt("## GTMUR-T01 \u2014 Certificate Pasting Theorem") == (
        "Theorem",
        "GTMUR-T01",
        "Certificate Pasting Theorem",
    )
    assert r._parse_stmt("### GTMUR-L02 \u2013 Terminal Non-Bypass Lemma") == (
        "Lemma",
        "GTMUR-L02",
        "Terminal Non-Bypass Lemma",
    )


def test_coda_nested_ground_up_keeps_gg_namespace():
    tower = "engine/research/published/001_coda/coda_fda/paper.md"
    ground = "engine/research/published/001_coda/gtoc/001_gtoc_time/001_gtoc_time.md"
    assert r._qualified_pid("001", tower) == "gt001"
    assert r._qualified_pid("001", ground) == "gg001"


def test_source_paper_ids_are_path_qualified_and_case_stable():
    ground = "engine/research/published/001_coda/gtoc/001_gtoc_time/001_gtoc_time.md §3"
    quantum = (
        "engine/research/published/003_quantum_foundations/"
        "qm_004_state_effect_pairing_audit/qm_004_state_effect_pairing_audit.md"
    )
    assert r._source_paper_pid(ground) == "gg001"
    assert r._source_paper_pid(quantum) == "qfQM_004"
    assert r._source_paper_pid("non_numeric_source.md") is None
