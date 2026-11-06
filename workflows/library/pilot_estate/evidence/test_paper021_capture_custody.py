"""Exact historical capture bytes; no replay, provider call or verdict promotion."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
CAPTURES = (
    ROOT
    / "omega_engine_atlas/coda_atlas/F004_papers/015_pfp/021_recreated_demos_and_proposal_fidelity_evidence/docs/aggregate_recreated_run/original_recovery_v1"
)
pytestmark = pytest.mark.skipif(
    not CAPTURES.is_dir(),
    reason="Historical paper 021 capture archive not present in active workspace",
)
V3_MANIFEST_SHA = "e131fc5178875dcc4d18285d459e344526db163a4c436c7adc9218255395ed4c"
V4_MANIFEST_SHA = "1e4d254d7556cdc2f749d71ad7857724128525c99b753bb232fdcf4f9ab9eedd"
V4_RECEIPT_SHA = "7c7ef2321efd3a1962115cee8ff7b46539a3b0346ae2fdc58e277255b4854a43"
V4_SELF_SHA = "19a731b4b97fe6b43c8ca5ef6b4601c7ed9daf0d4a648189f235e39192c24264"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def check_retained_receipt(raw, original_sha):
    if hashlib.sha256(raw).hexdigest() != original_sha:
        raise ValueError("RECEIPT_BYTE_DRIFT")
    receipt = json.loads(raw)
    body = dict(receipt)
    self_digest = body.pop("self_sha256")
    if hashlib.sha256(canonical(body)).hexdigest() != self_digest:
        raise ValueError("RECEIPT_SELF_DRIFT")
    return receipt


def check_source_capture(folder, expected_manifest_sha, expected_count):
    raw = (folder / "capture_manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_manifest_sha:
        raise ValueError("MANIFEST_BYTE_DRIFT")
    records = json.loads(raw)["files"]
    if len(records) != expected_count:
        raise ValueError("SOURCE_COUNT_DRIFT")
    expected = {record["path"] for record in records}
    source_root = folder / "source_files"
    actual = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    }
    if expected != actual:
        raise ValueError("SOURCE_INVENTORY_DRIFT")
    for record in records:
        path = source_root / record["path"]
        content = path.read_bytes()
        oid = hashlib.sha1(
            b"blob " + str(len(content)).encode() + b"\0" + content, usedforsecurity=False
        ).hexdigest()
        if (
            len(content) != record["size"]
            or hashlib.sha256(content).hexdigest() != record["sha256"]
            or oid != record["git_blob_oid"]
        ):
            raise ValueError("SOURCE_BYTE_DRIFT")


def test_failed_v3_source_capture_matches_original_manifest_and_git_blobs():
    check_source_capture(CAPTURES / "final_v3", V3_MANIFEST_SHA, 21)


def test_failed_v3_adapted_dialogue_matches_existing_adaptation_journal():
    content = (CAPTURES / "final_v3/adapted_sources/symbol_game_dialogue.py").read_bytes()
    assert (
        hashlib.sha256(content).hexdigest()
        == "396fc6b23cc181a85343883479f5824aeed5c282939cd0c0a6e878c71003607d"
    )


def test_failed_v3_runner_matches_its_original_capture_tree_not_a_success_receipt():
    content = (CAPTURES / "final_v3/failed_runner.py").read_bytes()
    assert (
        hashlib.sha256(content).hexdigest()
        == "61bec494180062e9a5e85d9c697f44b791997b93dcc727391e0107499350ddb0"
    )
    diagnostic = json.loads((CAPTURES / "final_v3/diagnostic.json").read_bytes())
    assert diagnostic["status"] == "CURRENT_CANONICAL_FLOAT_REFUSAL"
    assert diagnostic["custody_closed"] is False


def test_v4_source_capture_matches_original_manifest_and_git_blobs():
    check_source_capture(CAPTURES / "final_v4", V4_MANIFEST_SHA, 23)


def test_v4_retained_receipt_restores_original_bytes_and_self_digest_without_replay():
    folder = CAPTURES / "final_v4"
    raw = (folder / "receipt.json").read_bytes()
    receipt = check_retained_receipt(raw, V4_RECEIPT_SHA)
    assert receipt["self_sha256"] == V4_SELF_SHA
    assert raw == canonical(receipt) + b"\n"
    manifest = json.loads((folder / "capture_manifest.json").read_bytes())
    assert receipt["capture_manifest"] == manifest["files"]
    assert receipt["source_commit"] == manifest["source_commit"]


def test_v4_runner_matches_pre_existing_receipt_binding():
    folder = CAPTURES / "final_v4"
    runner = (folder / "executed_runner.py").read_bytes()
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert (
        hashlib.sha256(runner).hexdigest()
        == receipt["runner_sha256"]
        == "afe080366487f191a38f85511ec4818e4b38cfa5fe49ee6121bd6e2011aca070"
    )


def test_v4_all_adapted_sources_match_retained_journal_without_importing_them():
    folder = CAPTURES / "final_v4"
    receipt = json.loads((folder / "receipt.json").read_bytes())
    records = receipt["source_adaptations"]
    assert len(records) == 12
    sources = {path.stem: path for path in (folder / "adapted_sources").glob("*.py")}
    assert set(sources) == {record["module"] for record in records}
    for record in records:
        assert (
            hashlib.sha256(sources[record["module"]].read_bytes()).hexdigest()
            == record["adapted_source_sha256"]
        )


@pytest.mark.parametrize("mutation", ["body", "coherent-self", "whitespace"])
def test_changed_receipt_cannot_rebind_original_custody(mutation):
    body = {"schema": "synthetic-retained-evidence", "observation": "original"}
    receipt = dict(body, self_sha256=hashlib.sha256(canonical(body)).hexdigest())
    original = canonical(receipt) + b"\n"
    original_sha = hashlib.sha256(original).hexdigest()
    check_retained_receipt(original, original_sha)
    if mutation == "whitespace":
        changed = original + b" "
    else:
        receipt["observation"] = "changed"
        if mutation == "coherent-self":
            body = {key: value for key, value in receipt.items() if key != "self_sha256"}
            receipt["self_sha256"] = hashlib.sha256(canonical(body)).hexdigest()
        changed = canonical(receipt) + b"\n"
    assert changed != original
    with pytest.raises(ValueError, match="RECEIPT_BYTE_DRIFT"):
        check_retained_receipt(changed, original_sha)


@pytest.fixture
def synthetic_capture(tmp_path):
    content = b"original pinned source\n"
    path = tmp_path / "source_files/example.py"
    path.parent.mkdir()
    path.write_bytes(content)
    record = {
        "path": "example.py",
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "git_blob_oid": hashlib.sha1(
            b"blob " + str(len(content)).encode() + b"\0" + content, usedforsecurity=False
        ).hexdigest(),
    }
    manifest = tmp_path / "capture_manifest.json"
    manifest.write_text(json.dumps({"files": [record]}), encoding="utf-8")
    pin = hashlib.sha256(manifest.read_bytes()).hexdigest()
    check_source_capture(tmp_path, pin, 1)
    return tmp_path, path, manifest, pin


@pytest.mark.parametrize(
    "mutation", ["source", "extra", "coherent-manifest", "manifest-only", "missing"]
)
def test_source_and_manifest_mutations_cannot_rebind_original_custody(synthetic_capture, mutation):
    root, source, manifest, pin = synthetic_capture
    if mutation == "extra":
        (source.parent / "extra.py").write_bytes(b"unregistered")
    elif mutation == "manifest-only":
        manifest.write_bytes(manifest.read_bytes() + b" ")
    elif mutation == "missing":
        source.rename(root / "moved-outside.py")
    else:
        source.write_bytes(b"changed source\n")
        if mutation == "coherent-manifest":
            record = json.loads(manifest.read_bytes())
            record["files"][0].update(
                size=source.stat().st_size, sha256=hashlib.sha256(source.read_bytes()).hexdigest()
            )
            manifest.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError):
        check_source_capture(root, pin, 1)
