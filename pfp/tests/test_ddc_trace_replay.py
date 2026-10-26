"""Replay actual canonical DDC output and retain the historical DDA profile."""

import hashlib
import json

import pytest

from omega_engine_pfp.domain.aggregates.research_run_root import (
    ResearchRunRootError,
    semantic_dda_from_trace,
)
from omega_engine_operads.skill_operad.ddc_trace_logger import TraceLogger


def trace(tmp_path):
    logger = TraceLogger("meron-replay", trace_dir=tmp_path, auto_lifecycle=False)
    for letter, before, after in (("C", "seed", "scoped"), ("R", "scoped", "audited"),
                                  ("I", "audited", "checked"), ("T", "checked", "retained")):
        logger.record_step(letter, "retain:" + letter, before, after, "source-bound readback",
                           evidence={"prompt_sha256": "a" * 64, "family_id": "meron-finite-v1"})
    return logger.jsonl_path


def write_records(path, records):
    previous = None
    for record in records:
        record["prev_step_hash"] = previous
        body = {k: v for k, v in record.items() if k != "step_hash"}
        record["step_hash"] = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        previous = record["step_hash"]
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_current_logger_replays_without_rewriting_original_bytes(tmp_path):
    path = trace(tmp_path)
    raw = path.read_bytes()
    steps, root = semantic_dda_from_trace(path)
    assert [s.letter for s in steps] == ["C", "R", "I", "T"]
    assert len(root) == 64
    assert path.read_bytes() == raw
    assert semantic_dda_from_trace(path) == (steps, root)


def test_legacy_profile_remains_supported(tmp_path):
    path = trace(tmp_path)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    for index, r in enumerate(records, 1):
        r["schema_version"] = "omega.dda.trace.v2"
        r["dda_dialect"] = r.pop("ddc_dialect")
        r["step_id"] = f"DDA_STEP_{index:03d}"
    write_records(path, records)
    steps, _ = semantic_dda_from_trace(path)
    assert [s.letter for s in steps] == ["C", "R", "I", "T"]


@pytest.mark.parametrize("schema", [[], {}, None, 1, True, "unknown"])
def test_invalid_schema_is_a_typed_refusal(tmp_path, schema):
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps({"schema_version": schema}) + "\n", encoding="utf-8")
    with pytest.raises(ResearchRunRootError, match="unsupported schema"):
        semantic_dda_from_trace(path)


@pytest.mark.parametrize("mutation", ["digest", "mixed_profile", "alias", "prefix", "authority", "elimination"])
def test_tampered_or_incoherent_current_trace_is_refused(tmp_path, mutation):
    path = trace(tmp_path)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    if mutation == "digest":
        records[1]["witness"] = "changed without rehash"
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    else:
        if mutation == "mixed_profile":
            records[1]["schema_version"] = "omega.dda.trace.v2"
            records[1]["dda_dialect"] = records[1].pop("ddc_dialect")
            records[1]["step_id"] = "DDA_STEP_002"
        elif mutation == "alias":
            records[0]["dda_dialect"] = records[0]["ddc_dialect"]
        elif mutation == "prefix":
            records[0]["step_id"] = "DDA_STEP_001"
        elif mutation == "authority":
            records[0]["authority_effect"] = "Promote"
        else:
            records[1]["letter"] = "E"
            records[1]["effect"] = "obstruction_eliminated"
        write_records(path, records)
    with pytest.raises(ResearchRunRootError):
        semantic_dda_from_trace(path)


@pytest.mark.parametrize("letter", ["C.E", "CE", "C E", "C.E.R", "E.C"])
def test_each_record_contains_one_operation_with_its_own_obligations(tmp_path, letter):
    from omega_engine_pfp.domain.aggregates.research_run_root import semantic_dda_from_records

    path = trace(tmp_path)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[0]["letter"] = letter
    write_records(path, records)
    with pytest.raises(ResearchRunRootError, match="exactly one letter"):
        semantic_dda_from_trace(path)
    with pytest.raises(ResearchRunRootError, match="exactly one letter"):
        semantic_dda_from_records(tuple(records))
