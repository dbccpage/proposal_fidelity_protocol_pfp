"""Byte-level checks for the checked-in C014 governance artifacts.

The judge commitment and freeze record are current regenerations over LF bytes;
the scoring receipt is a historical record and keeps its bytes. The receipt is
therefore checked against the commitment it recorded itself (kept in the
``superseded_commitment`` / ``superseded_freeze_record`` blocks of the current
files), never against the regenerated digests.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CURRENT_STATUS = "CURRENT_REGENERATED_NOT_A_PRE_RUN_COMMITMENT"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load(name: str) -> dict:
    return json.loads((ROOT_DIR / "commitments" / name).read_text(encoding="utf-8"))


def test_current_commitment_and_freeze_bind_the_checked_in_bytes():
    """The regenerated Phase 1 and Phase 2 records bind the LF bytes on disk.

    Counterexample: the earlier commitment hashed the manifest over CRLF bytes, so
    it matched no checkout.
    """
    commitment = _load("c014_judge_commitment.json")
    freeze = _load("c014_freeze_record.json")

    manifest_path = ROOT_DIR / commitment["manifest_path"]
    manifest_digest = _lf_sha256(manifest_path)
    assert commitment["manifest_sha256"] == manifest_digest
    assert commitment["digest_normalization"] == "CRLF_TO_LF"
    assert freeze["phase1_binding_sha256"] == manifest_digest

    combined = hashlib.sha256()
    assert [r["path"] for r in freeze["solver_files"]] == sorted(
        r["path"] for r in freeze["solver_files"]
    )
    for record in freeze["solver_files"]:
        data = (ROOT_DIR / record["path"]).read_bytes().replace(b"\r\n", b"\n")
        digest = hashlib.sha256(data).hexdigest()
        assert record["sha256"] == digest
        assert record["size_bytes"] == len(data)
        combined.update(digest.encode("utf-8"))
    assert freeze["freeze_sha256"] == combined.hexdigest()


def test_regenerated_records_are_marked_current_and_not_a_pre_run_commitment():
    """Counterexample: a regenerated file read as if it were the pre-run commitment."""
    for name in ("c014_judge_commitment.json", "c014_freeze_record.json"):
        record = _load(name)
        assert record["commitment_status"] == CURRENT_STATUS
        assert "not a commitment made before any run" in record["regeneration_note"]


def test_historical_receipt_binds_the_commitment_it_recorded():
    """The unchanged historical receipt binds the superseded commitment and freeze, not the current ones.

    Counterexample: comparing the historical receipt with the regenerated digests
    fails for a reason that says nothing about the receipt.
    """
    receipt = _load("c014_scoring_receipt.json")
    superseded_commitment = _load("c014_judge_commitment.json")["superseded_commitment"]
    superseded_freeze = _load("c014_freeze_record.json")["superseded_freeze_record"]

    assert HEX64.match(receipt["judge_manifest_sha256"])
    assert HEX64.match(receipt["freeze_sha256"])
    assert receipt["judge_manifest_sha256"] == superseded_commitment["manifest_sha256"]
    assert receipt["freeze_sha256"] == superseded_freeze["freeze_sha256"]
    assert receipt["verdict"] == "OPEN_RESIDUAL"
    assert receipt["verification_status"] == "INVALIDATED_PENDING_RESCORE"
