from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pciv.domain import (
    CemeteryHeadstoneV1,
    GenealogyEntryV1,
)
from pciv.infrastructure.genealogy_adapter import (
    FileAntibodyAdapter,
    FileCemeteryAdapter,
    FileGenealogyAdapter,
)


def test_cemetery_records_headstone(tmp_path: Path) -> None:
    adapter = FileCemeteryAdapter(tmp_path / "cemetery")
    headstone = CemeteryHeadstoneV1(
        candidate_id="cand_dead_1",
        run_key="run_test_1",
        scene_id="act2_panel_debate",
        cause_of_death="CHEAP_GATE_FAILED: Empty response",
        killing_seat_id="seat_syntax_prefilter",
        evidence_refs=(),
        candidate_payload_sha256="sha256:" + hashlib.sha256(b"dummy").hexdigest(),
        round_index=1,
    )
    res = adapter.record_headstone(headstone)
    assert res.is_ok

    written = tmp_path / "cemetery" / f"{headstone.headstone_id.removeprefix('sha256:')}.headstone.json"
    assert written.exists()
    assert CemeteryHeadstoneV1.from_dict(json.loads(written.read_text(encoding="utf-8"))) == headstone


def test_cemetery_filename_is_not_derived_from_candidate_path(tmp_path: Path) -> None:
    adapter = FileCemeteryAdapter(tmp_path / "cemetery")
    headstone = CemeteryHeadstoneV1(
        candidate_id="candidate/../../escape",
        run_key="run_test_1",
        scene_id="act2_panel_debate",
        cause_of_death="REFUSED",
        killing_seat_id="seat_syntax_prefilter",
        evidence_refs=(),
        candidate_payload_sha256="sha256:" + hashlib.sha256(b"dummy").hexdigest(),
    )
    assert adapter.record_headstone(headstone).is_ok
    assert not (tmp_path / "escape.headstone.json").exists()
    assert len(tuple((tmp_path / "cemetery").glob("*.headstone.json"))) == 1


def test_sightings_never_activate_an_antibody(tmp_path: Path) -> None:
    adapter = FileAntibodyAdapter(tmp_path / "antibodies")
    for _ in range(5):
        recorded = adapter.record_failure(
            "TYPE_COERCION_OVERFLOW", "Require explicit uint64 bound"
        )
        assert recorded.is_ok and recorded.unwrap() is None

    restarted = FileAntibodyAdapter(tmp_path / "antibodies")
    loaded = restarted.load_antibodies("same objective")
    assert loaded.is_ok and loaded.unwrap() == ()
    (stored,) = tuple((tmp_path / "antibodies").glob("ab_*.json"))
    record = json.loads(stored.read_text(encoding="utf-8"))
    assert record["status"] == "PENDING"
    assert record["occurrences"] == 5


def test_admitted_antibody_keeps_its_status_when_seen_again(tmp_path: Path) -> None:
    adapter = FileAntibodyAdapter(tmp_path / "antibodies")
    first = adapter.record_failure("UNBOUND_WITNESS", "Bind every witness")
    assert first.is_ok and first.unwrap() is None
    (stored,) = tuple((tmp_path / "antibodies").glob("ab_*.json"))
    record = json.loads(stored.read_text(encoding="utf-8"))
    # Admission is an act outside this store; it rewrites the record as ACTIVE.
    stored.write_text(json.dumps({**record, "status": "ACTIVE"}), encoding="utf-8")

    restarted = FileAntibodyAdapter(tmp_path / "antibodies")
    seen = restarted.record_failure("UNBOUND_WITNESS", "Bind every witness")
    assert seen.is_ok
    admitted = seen.unwrap()
    assert admitted is not None
    assert admitted.status == "ACTIVE"
    assert admitted.occurrences == 2
    loaded = restarted.load_antibodies("any objective")
    assert loaded.is_ok and loaded.unwrap() == (admitted,)


def test_a_rejected_antibody_is_not_demoted_when_seen_again(tmp_path: Path) -> None:
    adapter = FileAntibodyAdapter(tmp_path / "antibodies")
    assert adapter.record_failure("FALSE_ALARM", "Ignore it").unwrap() is None
    (stored,) = tuple((tmp_path / "antibodies").glob("ab_*.json"))
    record = json.loads(stored.read_text(encoding="utf-8"))
    stored.write_text(json.dumps({**record, "status": "REJECTED"}), encoding="utf-8")

    restarted = FileAntibodyAdapter(tmp_path / "antibodies")
    assert restarted.record_failure("FALSE_ALARM", "Ignore it").unwrap() is None
    record = json.loads(stored.read_text(encoding="utf-8"))
    assert record["status"] == "REJECTED"
    assert record["occurrences"] == 2
    assert restarted.load_antibodies("any objective").unwrap() == ()


def test_antibody_load_refuses_corrupt_persisted_record(tmp_path: Path) -> None:
    antibody_dir = tmp_path / "antibodies"
    antibody_dir.mkdir()
    (antibody_dir / "ab_corrupt.json").write_text("{not-json}", encoding="utf-8")
    loaded = FileAntibodyAdapter(antibody_dir).load_antibodies("objective")
    assert loaded.is_err


def test_genealogy_records_lineage(tmp_path: Path) -> None:
    adapter = FileGenealogyAdapter(tmp_path / "genealogy.jsonl")
    entry = GenealogyEntryV1(
        parent_run_key="run_parent_1",
        child_run_key="run_child_1",
        structural_deficiencies=("Non-invertible arithmetic",),
        concrete_fixes=("Use exact Peano arithmetic",),
        next_run_guidance="Focus on machine representation bounds",
    )
    res = adapter.record_lineage(entry)
    assert res.is_ok

    lookup = adapter.get_lineage("run_child_1")
    assert lookup.is_ok and lookup.unwrap() is not None
    assert lookup.unwrap().parent_run_key == "run_parent_1"

    restarted_lookup = FileGenealogyAdapter(tmp_path / "genealogy.jsonl").get_lineage(
        "run_child_1"
    )
    assert restarted_lookup.is_ok and restarted_lookup.unwrap() == entry


def test_genealogy_discards_complete_unterminated_tail_before_append(
    tmp_path: Path,
) -> None:
    genealogy_file = tmp_path / "genealogy.jsonl"
    adapter = FileGenealogyAdapter(genealogy_file)
    first = GenealogyEntryV1(
        parent_run_key="run_parent_1",
        child_run_key="run_child_1",
        structural_deficiencies=("first",),
        concrete_fixes=("fix",),
        next_run_guidance="retry",
    )
    unacknowledged = GenealogyEntryV1(
        parent_run_key="run_child_1",
        child_run_key="run_child_2",
        structural_deficiencies=("torn",),
        concrete_fixes=("replace",),
        next_run_guidance="retry",
    )
    replacement = GenealogyEntryV1(
        parent_run_key="run_child_1",
        child_run_key="run_child_2",
        structural_deficiencies=("recovered",),
        concrete_fixes=("append safely",),
        next_run_guidance="continue",
    )

    assert adapter.record_lineage(first).is_ok
    assert adapter.record_lineage(unacknowledged).is_ok
    genealogy_file.write_bytes(genealogy_file.read_bytes().removesuffix(b"\n"))

    restarted = FileGenealogyAdapter(genealogy_file)
    assert restarted.get_lineage(first.child_run_key).unwrap() == first
    assert restarted.get_lineage(unacknowledged.child_run_key).unwrap() is None
    assert restarted.record_lineage(replacement).is_ok

    raw_lines = genealogy_file.read_bytes().splitlines(keepends=True)
    assert len(raw_lines) == 2
    assert all(line.endswith(b"\n") for line in raw_lines)
    assert FileGenealogyAdapter(genealogy_file).get_lineage(
        replacement.child_run_key
    ).unwrap() == replacement


def test_genealogy_refuses_conflicting_child_identity(tmp_path: Path) -> None:
    adapter = FileGenealogyAdapter(tmp_path / "genealogy.jsonl")
    first = GenealogyEntryV1(
        parent_run_key="run_parent_1",
        child_run_key="run_child_1",
        structural_deficiencies=("first",),
        concrete_fixes=("fix",),
        next_run_guidance="retry",
    )
    conflict = GenealogyEntryV1(
        parent_run_key="run_parent_2",
        child_run_key="run_child_1",
        structural_deficiencies=("second",),
        concrete_fixes=("fix",),
        next_run_guidance="retry",
    )
    assert adapter.record_lineage(first).is_ok
    assert adapter.record_lineage(conflict).is_err
