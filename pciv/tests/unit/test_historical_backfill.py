"""Historical custody and causal import, with real durable bytes."""

import json

from omega_engine_operating_system.adapters.prompt_civ.backfill import (
    RETIRED_PARSER_IDS,
    PromptCivBackfillEngineV1,
)


def test_backfill_repeated_tasks_do_not_create_inheritance_and_replay_is_durable(tmp_path):
    root = tmp_path / "sources"
    root.mkdir()
    rows = [
        {"prompt_id": "root", "prompt_text": "same task", "occurrence_id": "run1"},
        {"prompt_id": "root", "prompt_text": "same task", "occurrence_id": "run2"},
        {"prompt_id": "retry", "prompt_text": "repair task", "occurrence_id": "run3", "parents": [
            {"parent_id": "root", "relationship": "Retry", "witness_receipt_digest": "host-causal-retry"},
        ]},
        {"prompt_id": "missing", "prompt_text": "unknown parent", "parents": [
            {"parent_id": "absent", "relationship": "Retry", "witness_receipt_digest": "host-retry"},
        ]},
        {"payload": {"parent_run_key": "missing-run", "child_run_key": "opaque-child"}},
    ]
    path = root / "records.jsonl"
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    path.write_bytes(raw)
    output = tmp_path / "output"
    first = PromptCivBackfillEngineV1(root, output_root=output)
    receipt = first.run_backfill()
    assert receipt.genomes_created == 2
    assert receipt.occurrences_recorded == 3
    assert first.aliases["root"].parents == ()
    assert len(first.aliases["retry"].parents) == 1
    assert first.aliases["retry"].parents[0]["prompt_id"] == first.aliases["root"].prompt_id
    assert {"code": "UNRESOLVED_PARENT", "subject": "missing"} in receipt.residuals_recorded
    assert {"code": "UNRESOLVED_PARENT", "subject": "opaque-child"} in receipt.residuals_recorded
    event_bytes = (output / "backfill_events.jsonl").read_bytes()
    restarted = PromptCivBackfillEngineV1(root, output_root=output)
    assert restarted.registry.total_genome_count() == 2
    assert restarted.run_backfill() == receipt
    assert (output / "backfill_events.jsonl").read_bytes() == event_bytes
    assert path.read_bytes() == raw
    assert all(
        json.loads(line)["event"]["payload"]["retrieval_eligibility"] == "Dormant"
        for line in event_bytes.splitlines()
        if json.loads(line)["event"]["kind"] == "GenomeImported"
    )


def test_backfill_retired_placeholders_self_admission_and_external_roots(tmp_path):
    root = tmp_path / "sources"
    root.mkdir()
    rows = [{"antibody_id": name} for name in sorted(RETIRED_PARSER_IDS)]
    rows += [
        {"antibody_id": "placeholder"},
        {"antibody_id": "catalog", "status": "admitted"},
        {"antibody_id": "unsigned-root", "truth_boundary_root": True},
        {"antibody_id": "signed-root", "truth_boundary_root": True, "external_decision": "pinned-by-host"},
        {"prompt_id": "identity-only"},
    ]
    (root / "records.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    engine = PromptCivBackfillEngineV1(
        root, output_root=tmp_path / "output",
        admission_verifier=lambda record, digest: record.get("external_decision") == "pinned-by-host" and len(digest) == 64,
    )
    receipt = engine.run_backfill()
    assert receipt.antibodies_refused == 4
    assert engine.antibodies["catalog"]["custody"] == "Candidate"
    assert engine.antibodies["unsigned-root"]["custody"] == "Candidate"
    assert engine.antibodies["signed-root"]["custody"] == "HumanAdmitted"
    codes = {r["code"] for r in receipt.residuals_recorded}
    assert {"PHARMACY_SELF_ADMITTED", "EXTERNAL_ADMISSION_MISSING", "PROMPT_BYTES_UNAVAILABLE"} <= codes
    assert receipt.genomes_created == 0


def test_backfill_budget_and_cycles_stay_explicit(tmp_path):
    root = tmp_path / "sources"
    root.mkdir()
    rows = [
        {"prompt_id": "a", "prompt_text": "A", "parents": [{"parent_id": "b", "relationship": "Repair", "witness_receipt_digest": "w"}]},
        {"prompt_id": "b", "prompt_text": "B", "parents": [{"parent_id": "a", "relationship": "Repair", "witness_receipt_digest": "w"}]},
    ]
    (root / "records.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    receipt = PromptCivBackfillEngineV1(root).run_backfill()
    assert receipt.genomes_created == 0
    assert sum(r["code"] == "UNRESOLVED_PARENT" for r in receipt.residuals_recorded) == 2
    bounded = PromptCivBackfillEngineV1(root, max_total_bytes=1).run_backfill()
    assert any(r["code"] == "BACKFILL_BUDGET_EXHAUSTED" for r in bounded.residuals_recorded)
