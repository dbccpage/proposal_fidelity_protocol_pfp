"""The operad type registry matches its sources, and each rule fails on a real violation."""

from pathlib import Path

import pytest
import yaml

from operads.skill_operad.skill_compiler import operad_type_registry as registry

ROOT = registry.repo_root()


def _write(tmp_path: Path, *types: dict) -> Path:
    (tmp_path / "types.yaml").write_text(yaml.safe_dump({"types": list(types)}, allow_unicode=True), encoding="utf-8")
    return tmp_path


def _codes(tmp_path: Path, *types: dict) -> list[str]:
    return [finding.code for finding in registry.run(ROOT, _write(tmp_path, *types))[1]]


POLARITY = {"python": "pfp.domain.operad.polarity:Polarity",
            "values": ["CONSTRUCTIVE", "INTERROGATIVE", "CORRECTIVE", "GATE"]}


def _type(values, *sources, status="SETTLED", **canonical):
    return {"id": "t", "canonical": {"status": status, "values": values, **canonical}, "sources": list(sources)}


def test_the_checked_in_registry_matches_every_source():
    types, findings = registry.run(ROOT)
    assert findings == [] and len(types) >= 50
    assert {t["id"] for t in types if t["canonical"]["status"] == "PROPOSED"} >= {
        "residual_effect", "operad_colour", "obstruction_class", "operand_ddc_motif"}


def test_a_source_that_drifts_from_its_recorded_values_fails(tmp_path):
    drifted = {**POLARITY, "values": ["CONSTRUCTIVE", "INTERROGATIVE", "CORRECTIVE"]}
    assert "SOURCE_DRIFT" in _codes(tmp_path, _type(POLARITY["values"], drifted))


def test_settled_requires_agreement_and_proposed_requires_a_decision(tmp_path):
    assert "SETTLED_BUT_DIVERGENT" in _codes(tmp_path, _type(["CONSTRUCTIVE"], POLARITY))
    assert "DECISION_MISSING" in _codes(tmp_path, _type(["CONSTRUCTIVE"], POLARITY, status="PROPOSED"))
    assert "PROPOSED_BUT_AGREED" in _codes(tmp_path, _type(POLARITY["values"], POLARITY, status="PROPOSED",
                                                          decision="x"))


def test_uses_is_a_subset_and_parts_must_cover_the_set(tmp_path):
    used = {**POLARITY, "role": "uses"}
    assert _codes(tmp_path, _type(POLARITY["values"] + ["EXTRA"], used)) == []
    assert "SETTLED_BUT_DIVERGENT" in _codes(tmp_path, _type(["GATE"], used))
    part = {**POLARITY, "role": "part"}
    assert "SETTLED_BUT_DIVERGENT" in _codes(tmp_path, _type(POLARITY["values"] + ["MISSING"], part))


def test_rust_letter_map_and_open_carriers(tmp_path):
    ddc = {"rust_enum": "code/rust/core_operad_canon/src/lib.rs#DdcOp", "rust_map": "letter",
           "values": ["ExactRepair", "ResidualProjection", "ContextExposure", "Integration", "Lift", "Descent",
                      "Refusal", "Terminalize"]}
    assert _codes(tmp_path, _type(["E", "R", "C", "I", "Λ", "D", "M", "T"], ddc)) == []
    struct = {"rust_struct": "code/rust/core_operad_theory/src/foundation/colour.rs#OperadColour",
              "values": []}
    assert "SETTLED_BUT_DIVERGENT" in _codes(tmp_path, _type(["Audit"], struct, closed=True))
    assert _codes(tmp_path, _type(["Audit"], struct, closed=False)) == []


def test_letters_of_refuses_a_motif_outside_the_alphabet(tmp_path):
    uses = {"python": "operads.domain.anti_skills.anti_skill_v2:PREDICATE_MODES",
            "role": "uses", "values": ["ALL", "ANY"]}
    letters = {"id": "alphabet", "canonical": {"status": "SETTLED", "values": ["ALL", "ANY", "C", "M"]},
               "sources": [uses]}
    good = {"id": "good", "canonical": {"status": "SETTLED", "values": ["ALL"], "letters_of": "alphabet"},
            "sources": [uses]}
    findings = registry.run(ROOT, _write(tmp_path, letters, good))[1]
    assert [(f.type_id, f.code) for f in findings] == [("good", "SETTLED_BUT_DIVERGENT")]  # "ALL" is not letters
    motif = {"id": "motif", "canonical": {"status": "PROPOSED", "values": ["CM", "CP"], "letters_of": "alphabet",
             "decision": "P is not a letter"}, "sources": [{**uses, "values": ["ALL", "ANY"]}]}
    assert registry.run(ROOT, _write(tmp_path, letters, motif))[1] == []


@pytest.mark.parametrize("source", [{"python": "operads.no_such_module:X", "values": []},
                                    {"data": "no/such/file.yaml", "select": "a", "values": []}])
def test_an_unreadable_source_fails_closed(tmp_path, source):
    assert "SOURCE_UNREADABLE" in _codes(tmp_path, _type(["x"], source))


def test_the_registry_reads_values_from_the_canon_and_may_not_restate_them(tmp_path):
    canon = registry.load_canon(ROOT)
    restated = {"id": "pfp_polarity", "canonical": {"status": "SETTLED", "values": POLARITY["values"]},
                "sources": [POLARITY]}
    assert "CANONICAL_RESTATED" in _codes(tmp_path, restated)
    assert _codes(tmp_path, {"id": "pfp_polarity", "sources": [POLARITY]}) == []
    assert canon["pfp_polarity"]["values"] == POLARITY["values"]
    assert "NOT_IN_CANON" in _codes(tmp_path, {"id": "no_such_type", "sources": [POLARITY]})


def test_an_external_type_needs_no_readable_source(tmp_path):
    assert "NO_SOURCES" in _codes(tmp_path, {"id": "operad_tree", "sources": []})
    assert _codes(tmp_path, {"id": "operad_tree", "external": "not copied in", "sources": []}) == []
