"""Real persistence, bounded ingestion, and genome byte-custody witnesses."""

import hashlib
import json
from pathlib import Path

import pytest

from omega_engine_operating_system.adapters.prompt_civ.cas import ContentAddressedStorageV1
from omega_engine_operating_system.adapters.prompt_civ.forge import PopulationPolicyV1
from omega_engine_operating_system.adapters.prompt_civ.record import (
    PromptGenomeV1,
    ProtectedSpanV1,
)
from omega_engine_prompt_civilization.domain.prompt_ecology.protocols import DefectWitnessV1
from omega_engine_prompt_civilization.infrastructure.prompt_ecology.telemetry import (
    JsonlTelemetrySource,
    SqliteMetabolismStore,
)
from omega_engine_prompt_civilization.use_cases.prompt_ecology.ingest import ingest_batch


class ArithmeticReplay:
    """Independent exact checker: reproduce a serialized integer addition defect."""

    def verify(self, record, source):
        a, b, claimed = record.get("a"), record.get("b"), record.get("claimed")
        if any(type(value) is not int for value in (a, b, claimed)) or a + b == claimed:
            return None
        observation = record.get("host_observation")
        if not isinstance(observation, str) or not observation:
            return None
        return DefectWitnessV1(
            "integer-addition", observation, hashlib.sha256(b"integer-addition-v1").hexdigest(),
            hashlib.sha256(json.dumps([a, b, a + b, claimed]).encode()).hexdigest(),
        )


def telemetry(root: Path, observations=("one", "two", "three")) -> Path:
    root.mkdir()
    path = root / "execution.jsonl"
    rows = [{"a": 2, "b": 3, "claimed": 7, "host_observation": name} for name in observations]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_bounded_metabolism_resumes_after_restart_and_keeps_sources(tmp_path):
    root = tmp_path / "intelligence"
    path = telemetry(root)
    before = path.read_bytes()
    database = tmp_path / "metabolism.sqlite"
    source = JsonlTelemetrySource(root)
    store = SqliteMetabolismStore(database)
    first = ingest_batch(source, store, ArithmeticReplay(), max_records=2)
    assert first.processed == 2
    assert first.candidate_ids == ()
    store.close()
    store = SqliteMetabolismStore(database)
    second = ingest_batch(source, store, ArithmeticReplay(), max_records=2)
    assert second.processed == 1
    assert len(second.candidate_ids) == 1
    payload = json.loads(store.connection.execute("SELECT payload FROM candidates").fetchone()[0])
    assert payload["custody"] == "Candidate"
    assert payload["authority_effect"] == "None"
    assert len(payload["support"]) == 3
    assert ingest_batch(source, store, ArithmeticReplay(), max_records=2).processed == 0
    assert path.read_bytes() == before
    assert store.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 3
    store.close()


def test_repeated_observation_never_becomes_independent_support(tmp_path):
    root = tmp_path / "intelligence"
    telemetry(root, ("same", "same", "same"))
    store = SqliteMetabolismStore(tmp_path / "metabolism.sqlite")
    receipt = ingest_batch(JsonlTelemetrySource(root), store, ArithmeticReplay(), max_records=3)
    assert receipt.candidate_ids == ()
    assert store.connection.execute("SELECT COUNT(*) FROM witnesses").fetchone()[0] == 1
    assert store.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 3
    store.close()


def test_source_rewrite_is_refused_before_new_ingestion(tmp_path):
    root = tmp_path / "intelligence"
    path = telemetry(root)
    store = SqliteMetabolismStore(tmp_path / "metabolism.sqlite")
    source = JsonlTelemetrySource(root)
    ingest_batch(source, store, ArithmeticReplay(), max_records=1)
    path.write_bytes(path.read_bytes().replace(b'"a": 2', b'"a": 9', 1))
    with pytest.raises(ValueError, match="TELEMETRY_SOURCE_REWRITTEN"):
        ingest_batch(source, store, ArithmeticReplay(), max_records=1)
    assert store.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
    store.close()


def test_unchecked_and_malformed_claims_are_preserved_without_candidates(tmp_path):
    root = tmp_path / "intelligence"
    root.mkdir()
    path = root / "execution.jsonl"
    path.write_bytes(b'{"a":2,"b":3,"claimed":5}\nnot json\n{"defect_id":"self-admitted"}\n')
    store = SqliteMetabolismStore(tmp_path / "metabolism.sqlite")
    result = ingest_batch(JsonlTelemetrySource(root), store, ArithmeticReplay(), max_records=3)
    assert result.refused == 3
    assert result.candidate_ids == ()
    assert store.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 3
    store.close()


def test_partial_line_waits_and_oversized_line_refuses(tmp_path):
    root = tmp_path / "intelligence"
    root.mkdir()
    path = root / "execution.jsonl"
    path.write_bytes(b"partial")
    source = JsonlTelemetrySource(root, max_record_bytes=10)
    assert list(source.read_batch({}, 1)) == []
    path.write_bytes(b"oversized record\n")
    with pytest.raises(ValueError, match="TELEMETRY_RECORD_TOO_LARGE"):
        list(source.read_batch({}, 1))


def test_genome_identity_binds_spans_and_nested_sources_are_immutable():
    references = [{"packet_id": "p", "sha256": "s"}]
    domain = {"assumptions": ["finite"]}
    a = PromptGenomeV1(references, domain, protected_spans=(ProtectedSpanV1("core", 0, 4),))
    b = PromptGenomeV1(references, domain, protected_spans=())
    assert a.prompt_id != b.prompt_id
    references[0]["sha256"] = "tampered"
    domain["assumptions"].append("unbounded")
    assert a.source_packet_refs[0]["sha256"] == "s"
    assert a.domain_model["assumptions"] == ("finite",)
    with pytest.raises(TypeError):
        a.source_packet_refs[0]["sha256"] = "mutated"
    with pytest.raises(ValueError, match="GENOME_IDENTITY_MISMATCH"):
        PromptGenomeV1(references, domain, prompt_id=a.prompt_id)


def test_population_allocation_has_no_float_rounding_at_large_cap():
    cap = 10**20 + 7
    allocations = PopulationPolicyV1().allocate_reserves(cap)
    assert sum(allocations.values()) == cap
    assert allocations == {
        "Front": 60_000_000_000_000_000_004,
        "Unmeasured": 30_000_000_000_000_000_002,
        "Baseline": 10_000_000_000_000_000_001,
    }


def test_cas_write_failure_does_not_claim_durable_success(tmp_path):
    blocked = tmp_path / "not-a-directory"
    blocked.write_bytes(b"existing data")
    store = ContentAddressedStorageV1(blocked)
    with pytest.raises(OSError):
        store.store(b"must be durable before use")
    assert store._store == {}
