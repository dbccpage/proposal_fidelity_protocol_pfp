"""Commit-reveal runner for C039 (Lattice Z2 Gauge Theory Gauss Law).

AuthorityEffect: None.

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Woland verdict):

  * Phase 1 verifies every entry of judge_packet/manifest.json against the files
    on disk and records the manifest digest in commitments/c039_judge_commitment.json.
  * Phase 2 records digests of the reference solver files in
    commitments/c039_freeze_record.json, bound to the Phase 1 manifest digest.
  * Phase 3 re-verifies the manifest file, every manifest entry and every frozen
    solver file, refuses judge case files the manifest does not list and solver
    files that were not frozen, scores the solver with both checkers, labels the
    run with the reference self-consistency gate, persists a run folder and
    writes commitments/c039_scoring_receipt.json.
  * inspect_commitments() and verify_commitments() check Phases 1 and 2
    against the files on disk and their commitment_status marker, and check the
    scoring receipt as the record it is: a receipt written by this runner must
    bind the current commitment, and a historical receipt must bind the
    superseded commitment named in a regenerated Phase 1 record. A receipt that
    binds neither is refused.

All digests are SHA-256 over file bytes with CRLF normalised to LF, so they
equal git-blob content on every platform. Commitments and receipts are written
atomically (temporary file plus os.replace). If Phase 3 fails, a failure receipt
is written to commitments/c039_scoring_failure_receipt.json before the error
propagates. Each phase accepts ``challenge_dir`` (default: this package) and
Phase 3 accepts ``base_dir`` (the directory that contains ``_intelligence/``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

for _parent in Path(__file__).resolve().parents:
    if (_parent / "omega_engine_projects").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.governance.woland_gate import (  # noqa: E402
    GATE_SCOPE,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_VERDICTS,
    WolandGate,
    determine_terminal_verdict,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.judge_packet.checkers.dual_evaluator import (  # noqa: E402
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c039_lattice_z2_gauge_theory_gauss_law.reference_solver.solver import (  # noqa: E402
    solve,
)

CHALLENGE_ID = "c039_lattice_z2_gauge_theory_gauss_law"
FILE_PREFIX = "c039"
CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
SOLVER_DIR = CHALLENGE_DIR / "reference_solver"
COMMITMENTS_DIR = CHALLENGE_DIR / "commitments"
JUDGE_CASE_DIRS: tuple[str, ...] = ("base", "controls", "poisoned")
DIGEST_NORMALIZATION = "CRLF_TO_LF"
AGREEMENT_KEY = "agreed"


class ManifestCustodyError(ValueError):
    """A judge manifest, manifest entry, case file or frozen solver file failed custody checks."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def utc_now() -> str:
    """Canonical ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def lf_normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_file(path: Path) -> str:
    """SHA-256 of the LF-normalised file bytes."""
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON through a temporary file in the same directory and os.replace it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(tmp_name, path)


def _ordinal(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=lambda p: p.name.encode("utf-8"))


def manifest_entries(manifest: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Return (relative path, sha256) pairs from any of the manifest layouts in use."""
    for key in ("files", "manifest", "entries"):
        raw = manifest.get(key)
        if isinstance(raw, list):
            return [(str(entry["path"]), str(entry["sha256"])) for entry in raw]
        if isinstance(raw, dict):
            return [
                (str(rel), str(value["sha256"] if isinstance(value, Mapping) else value))
                for rel, value in raw.items()
            ]
    raise ManifestCustodyError(
        "MANIFEST_HAS_NO_ENTRIES", "no files/manifest/entries list in the judge manifest"
    )


def verify_manifest_entries(manifest_file: Path, challenge_root: Path) -> set[Path]:
    """Verify every manifest entry against the LF-normalised bytes on disk; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = manifest_entries(manifest)
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    verified: set[Path] = set()
    for rel, expected in entries:
        candidate = manifest_file.parent / rel
        path = candidate if candidate.is_file() else challenge_root / rel
        if not path.is_file():
            raise ManifestCustodyError("MANIFEST_ENTRY_MISSING", f"{rel} is listed but absent")
        actual = sha256_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH", f"{rel}: expected {expected}, got {actual}"
            )
        verified.add(path.resolve())
    return verified


def _layout(challenge_dir: Path | None) -> tuple[Path, Path, Path, Path]:
    root = CHALLENGE_DIR if challenge_dir is None else Path(challenge_dir)
    return root, root / "judge_packet", root / "reference_solver", root / "commitments"


def _verify_frozen_solver(challenge: Path, solver_dir: Path, freeze: Mapping[str, Any]) -> None:
    frozen = freeze.get("files")
    if not isinstance(frozen, Mapping) or not frozen:
        raise ManifestCustodyError("FREEZE_HAS_NO_FILES", "the freeze record lists no solver files")
    for rel_path, expected in frozen.items():
        solver_file = challenge / rel_path
        if not solver_file.is_file():
            raise ManifestCustodyError(
                "SOLVER_FILE_MISSING", f"frozen solver file {rel_path} is absent"
            )
        actual = sha256_file(solver_file)
        if actual != expected:
            raise ManifestCustodyError(
                "SOLVER_FILE_MISMATCH",
                f"Solver file tampered! {rel_path} expected {expected}, got {actual}",
            )
    on_disk = {sf.relative_to(challenge).as_posix() for sf in solver_dir.glob("*.py")}
    unfrozen = sorted(on_disk - set(frozen), key=lambda s: s.encode("utf-8"))
    if unfrozen:
        raise ManifestCustodyError(
            "SOLVER_FILE_NOT_FROZEN", f"solver files not in the freeze record: {unfrozen}"
        )


def reference_claim_hygiene(
    verdict: str, total: int, passed: int, agreements: int
) -> dict[str, str]:
    """Claim hygiene derived from the measured counts of this run."""
    return {
        "supports": (
            f"The frozen reference solver's outputs were accepted on {passed}/{total} judge cases, "
            f"with checker agreement on {agreements}/{total}."
        ),
        "does_not_support": (
            "Any statement about a model (none was evaluated), about checker soundness or independence, "
            "or a Woland verdict."
        ),
        "narrowest_defensible_claim": (
            f"Reference self-consistency label {verdict} on the {total} judge case files that match the committed manifest."
        ),
        "next_test_needed": (
            "Score a participant submission under a commitment made before the run and have the Woland swarm "
            "evaluate the bound checker receipts."
        ),
    }


def phase1_commit_judge(*, challenge_dir: Path | None = None) -> dict[str, Any]:
    """Phase 1: verify every manifest entry, then record the manifest digest."""
    challenge, judge, _solver, commitments = _layout(challenge_dir)
    manifest_file = judge / "manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Missing manifest file: {manifest_file}")

    verified = verify_manifest_entries(manifest_file, challenge)
    manifest_bytes = lf_normalized_bytes(manifest_file)
    manifest_data = json.loads(manifest_bytes.decode("utf-8"))

    record = {
        "authority_effect": "None",
        "challenge_id": CHALLENGE_ID,
        "declared_file_count": manifest_data.get("files_count", manifest_data.get("file_count")),
        "digest_normalization": DIGEST_NORMALIZATION,
        "file_count": len(verified),
        "manifest_path": "judge_packet/manifest.json",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "manifest_size_bytes": len(manifest_bytes),
        "phase": "PHASE_1_JUDGE_COMMITMENT",
        "protocol": "SG-CP v1",
        "timestamp_utc": utc_now(),
    }
    atomic_write_json(commitments / f"{FILE_PREFIX}_judge_commitment.json", record)
    return record


def phase2_freeze_solver(*, challenge_dir: Path | None = None) -> dict[str, Any]:
    """Phase 2: record digests of the reference solver files, bound to the Phase 1 digest."""
    challenge, _judge, solver, commitments = _layout(challenge_dir)
    phase1_file = commitments / f"{FILE_PREFIX}_judge_commitment.json"
    if not phase1_file.is_file():
        raise RuntimeError("Phase 1 commitment missing. Run phase 1 first.")
    phase1_data = json.loads(phase1_file.read_text(encoding="utf-8"))

    solver_files = _ordinal(list(solver.glob("*.py")))
    if not solver_files:
        raise FileNotFoundError(f"No solver files found in {solver}")

    file_hashes: dict[str, str] = {}
    combined_hasher = hashlib.sha256()
    for sf in solver_files:
        digest = sha256_file(sf)
        rel = sf.relative_to(challenge).as_posix()
        file_hashes[rel] = digest
        combined_hasher.update(rel.encode("utf-8"))
        combined_hasher.update(digest.encode("utf-8"))

    record = {
        "authority_effect": "None",
        "challenge_id": CHALLENGE_ID,
        "digest_normalization": DIGEST_NORMALIZATION,
        "files": file_hashes,
        "phase": "PHASE_2_SOLVER_FREEZE",
        "phase1_binding_sha256": phase1_data["manifest_sha256"],
        "protocol": "SG-CP v1",
        "solver_freeze_sha256": combined_hasher.hexdigest(),
        "timestamp_utc": utc_now(),
    }
    atomic_write_json(commitments / f"{FILE_PREFIX}_freeze_record.json", record)
    return record


def phase3_reveal_and_score(
    *,
    challenge_dir: Path | None = None,
    base_dir: Path | None = None,
    task_key: str | None = None,
    persist_woland: bool = True,
) -> dict[str, Any]:
    """Phase 3: verify custody, score the frozen solver, label the run and persist it.

    A failure writes commitments/c039_scoring_failure_receipt.json before the
    exception propagates.
    """
    _challenge, _judge, _solver, commitments = _layout(challenge_dir)
    try:
        return _phase3(
            challenge_dir=challenge_dir,
            base_dir=base_dir,
            task_key=task_key,
            persist_woland=persist_woland,
        )
    except BaseException as error:
        atomic_write_json(
            commitments / f"{FILE_PREFIX}_scoring_failure_receipt.json",
            {
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "error_code": getattr(error, "code", None),
                "error_message": str(error),
                "error_type": type(error).__name__,
                "phase": "PHASE_3_REVEAL_AND_SCORING_FAILED",
                "protocol": "SG-CP v1",
                "task_key": task_key,
                "timestamp_utc": utc_now(),
            },
        )
        raise


def _phase3(
    *,
    challenge_dir: Path | None,
    base_dir: Path | None,
    task_key: str | None,
    persist_woland: bool,
) -> dict[str, Any]:
    challenge, judge, solver, commitments = _layout(challenge_dir)
    p1_file = commitments / f"{FILE_PREFIX}_judge_commitment.json"
    p2_file = commitments / f"{FILE_PREFIX}_freeze_record.json"
    if not p1_file.is_file() or not p2_file.is_file():
        raise RuntimeError("Previous phase commitments missing. Complete Phases 1 & 2 first.")

    # 1. Custody: manifest file, every manifest entry, the freeze binding, every solver file.
    manifest_file = judge / "manifest.json"
    p1_data = json.loads(p1_file.read_text(encoding="utf-8"))
    manifest_digest = sha256_file(manifest_file)
    if manifest_digest != p1_data["manifest_sha256"]:
        raise ManifestCustodyError(
            "MANIFEST_DIGEST_MISMATCH",
            f"Judge manifest tampered after Phase 1 commitment! Expected {p1_data['manifest_sha256']}, "
            f"got {manifest_digest}",
        )
    verified_paths = verify_manifest_entries(manifest_file, challenge)
    p2_data = json.loads(p2_file.read_text(encoding="utf-8"))
    if p2_data.get("phase1_binding_sha256") != p1_data["manifest_sha256"]:
        raise ManifestCustodyError(
            "FREEZE_NOT_BOUND_TO_COMMITMENT",
            "the freeze record does not bind the Phase 1 manifest digest",
        )
    _verify_frozen_solver(challenge, solver, p2_data)

    # 2. Judge cases: every case file must be listed in the verified manifest.
    case_files: list[Path] = []
    for sub in JUDGE_CASE_DIRS:
        case_dir = judge / "cases" / sub
        if case_dir.is_dir():
            case_files.extend(_ordinal(list(case_dir.glob("*.json"))))
    for case_file in case_files:
        if case_file.resolve() not in verified_paths:
            raise ManifestCustodyError(
                "CASE_FILE_NOT_IN_MANIFEST", f"{case_file.name} is not listed in the judge manifest"
            )
    if not case_files:
        raise ManifestCustodyError(
            "EMPTY_JUDGE_SUITE", "no judge case files were found; an empty suite is refused"
        )

    # 3. Score every case with both checkers; count on exact values only.
    evaluations: list[dict[str, Any]] = []
    dda_actions: list[dict[str, Any]] = []
    passed_count = 0
    agreed_count = 0
    for idx, case_file in enumerate(case_files):
        case_data = json.loads(case_file.read_text(encoding="utf-8"))
        result = solve(case_data)
        eval_res = evaluate_dual(case_data, result)
        evaluations.append(eval_res)
        case_passed = eval_res.get("verdict") == "PASS"
        case_agreed = eval_res.get(AGREEMENT_KEY) is True
        passed_count += int(case_passed)
        agreed_count += int(case_agreed)
        dda_actions.append(
            {
                AGREEMENT_KEY: case_agreed,
                "case_id": case_data.get("case_id") or case_data.get("id"),
                "step": idx + 1,
                "verdict": eval_res.get("verdict"),
            }
        )

    total = len(case_files)
    defect_count = total - passed_count
    verdict = determine_terminal_verdict(
        total, passed_count, agreed_count, defect_count=defect_count
    )
    claim_hygiene = reference_claim_hygiene(verdict, total, passed_count, agreed_count)
    dda_actions.append(
        {
            "action": "emit_self_consistency_label",
            "agreed_count": agreed_count,
            "case_count": total,
            "label": verdict,
            "passed_count": passed_count,
            "scope": GATE_SCOPE,
            "step": total + 1,
        }
    )

    receipt: dict[str, Any] = {
        "agreements_count": agreed_count,
        "all_agreed": agreed_count == total,
        "all_passed": passed_count == total,
        "authority_effect": "None",
        "case_count": total,
        "challenge_id": CHALLENGE_ID,
        "claim_hygiene": claim_hygiene,
        "defect_count": defect_count,
        "digest_normalization": DIGEST_NORMALIZATION,
        "gate_scope": GATE_SCOPE,
        "judge_manifest_entries_verified": len(verified_paths),
        "passed_count": passed_count,
        "phase": "PHASE_3_SCORING_RECEIPT",
        "phase1_manifest_sha256": p1_data["manifest_sha256"],
        "protocol": "SG-CP v1",
        "solver_freeze_sha256": p2_data["solver_freeze_sha256"],
        "timestamp_utc": utc_now(),
        "verdict": verdict,
        "concordance_rate": f"{agreed_count}/{total}",
        "dual_agreements": agreed_count,
        "dual_passes": passed_count,
        "evaluations_sample": evaluations[:10],
        "final_verdict": verdict,
        "total_cases": total,
    }

    woland_digests: dict[str, str] = {}
    if persist_woland:
        gate = WolandGate(task_key=task_key or CHALLENGE_ID, base_dir=base_dir)
        summary_data = {
            "agreements_count": agreed_count,
            "challenge_id": CHALLENGE_ID,
            "claim_hygiene": claim_hygiene,
            "defect_count": defect_count,
            "passed_count": passed_count,
            "timestamp_utc": utc_now(),
            "total_cases": total,
            "verdict": verdict,
        }
        novella_text = gate.generate_novella(
            verdict,
            {
                "agreements_count": agreed_count,
                "claim_hygiene": claim_hygiene,
                "defect_count": defect_count,
                "passed_count": passed_count,
                "total_cases": total,
            },
        )
        gate.persist_run_bundle(
            receipt=receipt,
            summary=summary_data,
            dda_actions=dda_actions,
            novella=novella_text,
        )
        woland_digests = dict(gate.last_bundle_digests)

    scoring_receipt = {**receipt, "woland_digests": woland_digests}
    atomic_write_json(commitments / f"{FILE_PREFIX}_scoring_receipt.json", scoring_receipt)
    return scoring_receipt


COMMITMENT_STATUS_REGENERATED = "CURRENT_REGENERATED_NOT_A_PRE_RUN_COMMITMENT"
RECEIPT_BINDS_CURRENT_COMMITMENT = "CURRENT_COMMITMENT"
RECEIPT_BINDS_SUPERSEDED_COMMITMENT = "SUPERSEDED_COMMITMENT"
_HEX_DIGITS = frozenset("0123456789abcdef")


class CommitmentVerificationError(ValueError):
    """A judge commitment, freeze record or scoring receipt failed verification."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class CommitmentVerification:
    """Typed result of inspect_commitments.

    verified is True only when every check passed, and code names the first
    failure (VERIFIED otherwise). receipt_binding names the Phase 1 commitment
    the scoring receipt binds: CURRENT_COMMITMENT for a receipt written by this
    runner, SUPERSEDED_COMMITMENT for a historical receipt. commitment_status is
    the marker on the current records (None when written by this runner's phases).
    """

    verified: bool
    code: str
    detail: str
    receipt_binding: str | None = None
    commitment_status: str | None = None


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= _HEX_DIGITS


def _load_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CommitmentVerificationError(
            "RECORD_NOT_AN_OBJECT", f"{path.name} is not a JSON object"
        )
    return data


def _commitment_status(record: Mapping[str, Any], name: str, superseded_key: str) -> str | None:
    """Return the record's commitment_status marker; None for a record written by this runner's phases."""
    status = record.get("commitment_status")
    if status is None:
        if superseded_key in record:
            raise CommitmentVerificationError(
                "COMMITMENT_STATUS_MISSING",
                f"the {name} names a superseded record but carries no commitment_status",
            )
        return None
    if status != COMMITMENT_STATUS_REGENERATED:
        raise CommitmentVerificationError(
            "UNKNOWN_COMMITMENT_STATUS", f"the {name} has commitment_status {status!r}"
        )
    superseded = record.get(superseded_key)
    if not isinstance(superseded, Mapping) or not _is_sha256(superseded.get("file_sha256")):
        raise CommitmentVerificationError(
            "SUPERSEDED_RECORD_MALFORMED",
            f"the regenerated {name} must name the record it replaced in {superseded_key}",
        )
    return status


def verify_phase1_commitment(*, challenge_dir: Path | None = None) -> dict[str, Any]:
    """Check the Phase 1 record against the manifest file and every manifest entry on disk; return it."""
    challenge, judge, _solver, commitments = _layout(challenge_dir)
    record = _load_record(commitments / f"{FILE_PREFIX}_judge_commitment.json")
    manifest_file = judge / "manifest.json"
    manifest_hash = sha256_file(manifest_file)
    if record.get("manifest_sha256") != manifest_hash:
        raise CommitmentVerificationError(
            "MANIFEST_DIGEST_MISMATCH",
            f"the judge commitment binds {record.get('manifest_sha256')!r}; the manifest on disk hashes to {manifest_hash}",
        )
    verify_manifest_entries(manifest_file, challenge)
    _commitment_status(record, "judge commitment", "superseded_commitment")
    return record


def verify_phase2_freeze(
    phase1_record: Mapping[str, Any], *, challenge_dir: Path | None = None
) -> dict[str, Any]:
    """Check the freeze record's binding to Phase 1 and every frozen solver file on disk; return it."""
    challenge, _judge, solver, commitments = _layout(challenge_dir)
    record = _load_record(commitments / f"{FILE_PREFIX}_freeze_record.json")
    if record.get("phase1_binding_sha256") != phase1_record.get("manifest_sha256"):
        raise CommitmentVerificationError(
            "FREEZE_NOT_BOUND_TO_COMMITMENT",
            "the freeze record does not bind the Phase 1 manifest digest",
        )
    _verify_frozen_solver(challenge, solver, record)
    status = _commitment_status(record, "freeze record", "superseded_freeze_record")
    if status != phase1_record.get("commitment_status"):
        raise CommitmentVerificationError(
            "COMMITMENT_STATUS_INCONSISTENT",
            "the judge commitment and the freeze record carry different markers",
        )
    return record


def check_scoring_receipt(
    receipt: Mapping[str, Any],
    phase1_record: Mapping[str, Any],
    phase2_record: Mapping[str, Any],
) -> str:
    """Check the scoring receipt as the record it is and return which commitment it binds.

    A receipt written by this runner carries gate_scope; it must bind the current
    judge commitment and solver freeze and carry REFERENCE_SELF_CONSISTENT. A
    receipt without gate_scope is historical (written before the corrections and
    kept unchanged): it must bind the superseded commitment recorded in a
    regenerated Phase 1 record, and its own counts must show that every case
    passed with checker agreement; its retired label is not read. A historical
    receipt whose digest merely equals the regenerated commitment's is refused:
    that commitment was made after the receipt.
    """
    bound = receipt.get("phase1_manifest_sha256")
    if "gate_scope" in receipt:
        if receipt["gate_scope"] != GATE_SCOPE:
            raise CommitmentVerificationError(
                "RECEIPT_SCOPE_UNKNOWN", f"gate_scope is {receipt['gate_scope']!r}"
            )
        if bound != phase1_record.get("manifest_sha256") or receipt.get(
            "solver_freeze_sha256"
        ) != phase2_record.get("solver_freeze_sha256"):
            raise CommitmentVerificationError(
                "RECEIPT_BINDS_NO_COMMITMENT",
                "the receipt does not bind the current judge commitment and solver freeze",
            )
        if receipt.get("verdict") != TERMINAL_REFERENCE_SELF_CONSISTENT:
            raise CommitmentVerificationError(
                "RECEIPT_NOT_SELF_CONSISTENT", f"verdict is {receipt.get('verdict')!r}"
            )
        return RECEIPT_BINDS_CURRENT_COMMITMENT

    if (
        receipt.get("verdict") in TERMINAL_VERDICTS
        or receipt.get("final_verdict") in TERMINAL_VERDICTS
    ):
        raise CommitmentVerificationError(
            "RECEIPT_SCOPE_MISSING",
            "a receipt carrying a current gate label must also carry gate_scope",
        )
    superseded = phase1_record.get("superseded_commitment")
    if phase1_record.get("commitment_status") != COMMITMENT_STATUS_REGENERATED or not isinstance(
        superseded, Mapping
    ):
        raise CommitmentVerificationError(
            "RECEIPT_BINDS_NO_COMMITMENT",
            "a historical receipt can bind only the superseded commitment named in a regenerated judge commitment",
        )
    if not _is_sha256(bound) or bound != superseded.get("manifest_sha256"):
        raise CommitmentVerificationError(
            "RECEIPT_BINDS_NO_COMMITMENT",
            "the historical receipt does not bind the superseded judge commitment",
        )
    cases = receipt.get("case_count")
    agreed = receipt.get("agreements_count")
    passed = receipt.get("dual_passes", cases)
    if (
        type(cases) is not int
        or cases <= 0
        or type(agreed) is not int
        or agreed != cases
        or passed != cases
        or receipt.get("all_passed") is not True
        or receipt.get("all_agreed") is not True
    ):
        raise CommitmentVerificationError(
            "HISTORICAL_RECEIPT_NOT_ALL_PASSED",
            "the historical receipt does not record every case passed and agreed",
        )
    return RECEIPT_BINDS_SUPERSEDED_COMMITMENT


def inspect_commitments(*, challenge_dir: Path | None = None) -> CommitmentVerification:
    """Verify Phases 1 and 2 against the files on disk, then check the scoring receipt as a record."""
    _challenge, judge, _solver, commitments = _layout(challenge_dir)
    required = [
        judge / "manifest.json",
        commitments / f"{FILE_PREFIX}_judge_commitment.json",
        commitments / f"{FILE_PREFIX}_freeze_record.json",
        commitments / f"{FILE_PREFIX}_scoring_receipt.json",
    ]
    missing = [p.name for p in required if not p.is_file()]
    if missing:
        return CommitmentVerification(False, "MISSING_RECORDS", f"missing: {missing}")
    try:
        phase1 = verify_phase1_commitment(challenge_dir=challenge_dir)
        phase2 = verify_phase2_freeze(phase1, challenge_dir=challenge_dir)
        receipt = _load_record(commitments / f"{FILE_PREFIX}_scoring_receipt.json")
        binding = check_scoring_receipt(receipt, phase1, phase2)
    except (CommitmentVerificationError, ManifestCustodyError) as error:
        return CommitmentVerification(False, error.code, str(error))
    except (OSError, ValueError, KeyError, TypeError) as error:
        return CommitmentVerification(
            False, "UNREADABLE_RECORD", f"{type(error).__name__}: {error}"
        )
    return CommitmentVerification(
        True,
        "VERIFIED",
        f"Phases 1 and 2 match the files on disk; the scoring receipt binds the {binding.lower().replace('_', ' ')}",
        receipt_binding=binding,
        commitment_status=phase1.get("commitment_status"),
    )


def verify_commitments(*, challenge_dir: Path | None = None) -> bool:
    """Boolean form of inspect_commitments; prints the outcome."""
    result = inspect_commitments(challenge_dir=challenge_dir)
    if not result.verified:
        print(f"Verification failed: {result.code}: {result.detail}")
        return False
    print(
        f"All commitments, freezes, and scoring receipts verified successfully ({result.detail})."
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C039 reference self-consistency commit-reveal runner"
    )
    parser.add_argument(
        "phase", choices=["phase1", "phase2", "phase3", "all", "verify"], help="Phase to execute"
    )
    args = parser.parse_args()

    if args.phase in ("phase1", "all"):
        record = phase1_commit_judge()
        print(
            f"Phase 1 committed (manifest SHA-256 over LF bytes: {record['manifest_sha256'][:16]}...)"
        )
    if args.phase in ("phase2", "all"):
        record = phase2_freeze_solver()
        print(f"Phase 2 frozen (solver freeze SHA-256: {record['solver_freeze_sha256'][:16]}...)")
    if args.phase in ("phase3", "all"):
        receipt = phase3_reveal_and_score()
        print(
            f"Phase 3 scored: label {receipt['verdict']}, passed {receipt['passed_count']}/{receipt['case_count']}, "
            f"agreement {receipt['agreements_count']}/{receipt['case_count']}"
        )
    if args.phase == "verify":
        return 0 if verify_commitments() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
