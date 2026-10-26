"""Explicit disposable-copy cleanup, using the existing native retention port.

Origin: omega_engine_woland.infrastructure.teamwork_cleanup_host.

This cooperative single-writer host tool never sweeps directories. A native
DISCHARGED decision concerns only the declared clean disposable source, not the
teamwork run's OPEN_RESIDUAL verdict or a claim of detector admission.

The operator-authored plan has ``working_root`` (a repository-relative task
directory below _ic/woland/working), ``copies`` (path, sha256,
recovery_path, recovery_git_revision, recovery_git_path), and ``policy``
(active_lease, holds, dependency_refs, grace_elapsed). Recovery needs BOTH an
exact retained file and exact bytes at the pinned Git commit. All files are
preflighted before any removal; before/after receipts describe actual disk.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort

from ..domain.intelligence_digestion.ports import IntelligenceLifecyclePort
from ..use_cases.intelligence_digestion.archive_custody import (
    ArchiveCustodyError,
    bundle_entries,
    checked_path,
    relative_parts,
    require_digest,
    validate_sealed_manifest,
)
from ..use_cases.intelligence_digestion.digestion_models import (
    CHECKER_VERSION,
    EXTRACTOR_VERSION,
    SOURCE_SCHEMA,
)
from ..use_cases.intelligence_digestion.digestion_service import read_run_findings
from ..use_cases.teamwork import TeamworkRun, intelligence_sources, next_action
from .teamwork_intelligence_host import (
    _current_artifacts,
    read_intelligence,
    validate_continuation_parents,
)

_COPY_FIELDS = {"path", "sha256", "recovery_path", "recovery_git_revision", "recovery_git_path"}
_PLAN_FIELDS = {"working_root", "copies", "policy"}
_POLICY_FIELDS = {"active_lease", "holds", "dependency_refs", "grace_elapsed"}
_HOST_ROLES = ("host_ddc_store", "host_ddc_complete", "host_native_gates")


def _path(root: Path, value: str) -> Path:
    try:
        relative_parts(value)
        return checked_path(root, root.joinpath(*value.split("/")))
    except ArchiveCustodyError as exc:
        raise ValueError(f"CLEANUP_PATH_REFUSED: {exc}") from exc


def _raw(root: Path, path: Path) -> bytes:
    checked_path(root, path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("CLEANUP_REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(("git", "-C", str(root), *args), capture_output=True, check=False)


def _require_cleanup_scope(run: TeamworkRun, sources):
    if not sources:
        raise ValueError("CLEANUP_OPEN_WORK: completed scoped work is required")
    root_source = sources[0]
    if run.intelligence is None and root_source.parent_source_id is not None:
        raise ValueError("CLEANUP_INITIAL_SOURCE_REQUIRED")
    if run.work_status != "completed":
        raise ValueError("CLEANUP_OPEN_WORK: completed scoped work is required")
    if run.continuation_status.get("clarification_context") is not None:
        raise ValueError("CLEANUP_QUERY_REQUIRES_USER: retain the checked question and its unresolved inputs")
    if run.feedback_policy == "semantic_digestion_v2" and run.continuation_status["semantic_review_pending"]:
        raise ValueError("CLEANUP_LEARNING_REVIEW_REQUIRED")
    return root_source


def _acceptance_binding_matches(check, requirement, run, root_source) -> bool:
    if check.initial_task_id != root_source.initial_task_id:
        return False
    checker_id = requirement.checker_id if requirement else run.checker_id
    command = requirement.operation if requirement else run.check_command
    if check.checker_id != checker_id or check.command != command:
        return False
    if requirement is not None and check.source_id != requirement.source_id:
        return False
    return bool(check.artifacts)


def _require_acceptance(run: TeamworkRun, root_source):
    checks = [item.check for item in run.observations if item.check is not None]
    if not checks or checks[-1].exit_status != 0:
        raise ValueError("CLEANUP_ACCEPTANCE_REQUIRED")
    check = checks[-1]
    requirement = run.acceptance_check
    if not _acceptance_binding_matches(check, requirement, run, root_source):
        raise ValueError("CLEANUP_ACCEPTANCE_BINDING_INVALID")
    _current_artifacts(check.artifacts)
    if requirement is not None:
        _current_artifacts(requirement.check_source_paths)
    return check


def _current_source_readback(sources) -> dict:
    current_sources = {}
    for source in sources:
        current = read_intelligence(Path(source.source_locator), initial_task_id=source.initial_task_id,
                                    parent_source_id=source.parent_source_id)
        if current.source_id != source.source_id:
            raise ValueError("CLEANUP_SOURCE_CHANGED")
        if (set(current.findings) != set(source.findings)
                or set(current.coverage_gaps) != set(source.coverage_gaps)):
            raise ValueError("CLEANUP_SOURCE_INTERPRETATION_CHANGED")
        current_sources[source.source_locator] = current
    return current_sources


def _final_observation_index(run: TeamworkRun):
    for index in range(len(run.observations) - 1, -1, -1):
        item = run.observations[index]
        stage = item.metadata.get("learning_stage")
        if stage == "learn":
            continue
        if run.feedback_policy == "semantic_digestion_v2" and stage == "review":
            continue
        if item.metadata.get("role_id") in _HOST_ROLES:
            continue
        return index
    return None


def _prefix_before(run: TeamworkRun, index: int):
    return run.model_copy(update={"observations": run.observations[:index],
        "continuations": tuple(point for point in run.continuations
                               if point.after_observations <= index)})


def _digestion_shape_ok(final, digest_action, check) -> bool:
    if final is None or not final.intelligence or final.findings or final.intelligence.coverage_gaps:
        return False
    if final.intelligence.initial_task_id != check.initial_task_id:
        return False
    if digest_action is None or digest_action.kind != "digest" or digest_action.intelligence is None:
        return False
    if final.intelligence.parent_source_id != digest_action.intelligence.source_id:
        return False
    return final.artifacts == check.artifacts


def _final_digestion(run: TeamworkRun, check):
    final_index = _final_observation_index(run)
    final = run.observations[final_index] if final_index is not None else None
    prefix = _prefix_before(run, final_index) if final_index is not None else None
    digest_action = next_action(prefix) if prefix is not None else None
    if not _digestion_shape_ok(final, digest_action, check):
        raise ValueError("CLEANUP_FINAL_DIGESTION_REQUIRED")
    return final


def _require_final_readback(current_sources, final) -> None:
    current_final = current_sources[final.intelligence.source_locator]
    if current_final.findings or current_final.coverage_gaps:
        raise ValueError("CLEANUP_FINAL_READBACK_OPEN")


def _replay_ddc(run: TeamworkRun, root_source) -> None:
    if run.schema_version not in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
        return
    from ..use_cases.prompt_family_replay import load_ddc_program

    for item in run.observations:
        if item.ddc_program is not None:
            load_ddc_program(item.ddc_program.run_path, expected=item.ddc_program.binding,
                             initial_task_id=root_source.initial_task_id, native_support=DefaultNativeOperationPort())


def _replay_native_gates(run: TeamworkRun) -> None:
    if run.schema_version != "omega.woland.teamwork.v4":
        return
    from .teamwork_native_gates import replay_native_gate_reference

    for index, item in enumerate(run.observations):
        if "native_gate_receipt" in item.metadata:
            replay_native_gate_reference(next_action(_prefix_before(run, index)),
                                         item.metadata["native_gate_receipt"])


def _readback(run: TeamworkRun) -> dict[str, str]:
    validate_continuation_parents(run)
    sources = intelligence_sources(run)
    root_source = _require_cleanup_scope(run, sources)
    check = _require_acceptance(run, root_source)
    current_sources = _current_source_readback(sources)
    final = _final_digestion(run, check)
    _require_final_readback(current_sources, final)
    _replay_ddc(run, root_source)
    _replay_native_gates(run)
    return check.artifacts


def _inventory(root: Path, rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        path = _path(root, row["path"])
        exists = path.exists()
        result.append({"path": row["path"], "exists": exists,
                       "sha256": _sha(_raw(root, path)) if exists else None})
    return result


def _write(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _require_plan_dict(plan) -> None:
    if type(plan) is not dict or set(plan) != _PLAN_FIELDS:
        raise ValueError("CLEANUP_PLAN_INVALID")


def _policy_value_lists(policy) -> bool:
    for key in ("holds", "dependency_refs"):
        values = policy[key]
        if type(values) is not list:
            return False
        for ref in values:
            if type(ref) is not str or not ref:
                return False
    return True


def _require_rows_and_policy(plan):
    rows, policy = plan["copies"], plan["policy"]
    if type(rows) is not list or not rows or type(policy) is not dict or set(policy) != _POLICY_FIELDS:
        raise ValueError("CLEANUP_PLAN_INVALID")
    if type(policy["active_lease"]) is not bool or type(policy["grace_elapsed"]) is not bool:
        raise ValueError("CLEANUP_POLICY_INVALID")
    if not _policy_value_lists(policy):
        raise ValueError("CLEANUP_POLICY_INVALID")
    return rows, policy


def _working_root(root: Path, value: str) -> Path:
    try:
        working = _path(root, value)
    except ValueError as exc:
        raise ValueError("CLEANUP_WORKING_ROOT: use a dedicated disposable task directory") from exc
    allowed = root / "_ic/woland/working"
    if working == allowed or not working.is_relative_to(allowed):
        raise ValueError("CLEANUP_WORKING_ROOT: use a dedicated disposable task directory")
    return working


def _sealed_source_protected(path: Path, working: Path) -> bool:
    # The allowed working home still cannot disguise a sealed run directory.
    for parent in (path.parent, *path.parent.parents):
        if not parent.is_relative_to(working):
            continue
        if (parent / "receipt.json").exists() and any(
                (parent / name).exists() for name in ("dda_actions.jsonl", "ddc.jsonl")):
            return True
    return False


def _validate_one_copy(root: Path, working: Path, row) -> None:
    if type(row) is not dict or set(row) != _COPY_FIELDS:
        raise ValueError("CLEANUP_COPY_INVALID")
    path, recovery = _path(root, row["path"]), _path(root, row["recovery_path"])
    try:
        require_digest(row["sha256"])
        relative_parts(row["recovery_git_path"])
    except ArchiveCustodyError as exc:
        raise ValueError(f"CLEANUP_COPY_INVALID: {exc}") from exc
    if not isinstance(row["recovery_git_revision"], str) or not re.fullmatch(r"[0-9a-f]{40}", row["recovery_git_revision"]):
        raise ValueError("CLEANUP_GIT_REVISION_INVALID")
    if not path.is_relative_to(working) or path == working or recovery.is_relative_to(working):
        raise ValueError("CLEANUP_PATH_OUTSIDE_WORKING_SCOPE")
    if _sealed_source_protected(path, working):
        raise ValueError("CLEANUP_SEALED_SOURCE_PROTECTED")


def _validate_copies(root: Path, working: Path, rows) -> None:
    names = []
    for row in rows:
        _validate_one_copy(root, working, row)
        names.append(row["path"])
    if len(names) != len(set(names)):
        raise ValueError("CLEANUP_DUPLICATE_COPY")


def _receipt_paths(root: Path, working: Path, receipt_path: Path):
    receipt_path = checked_path(root, receipt_path.absolute())
    before_path = receipt_path.with_name(receipt_path.stem + ".before.json")
    if receipt_path.is_relative_to(working) or receipt_path.exists() or before_path.exists():
        raise ValueError("CLEANUP_RECEIPT_PATH_INVALID")
    return receipt_path, before_path


def _observation_protected(run: TeamworkRun) -> list[Path]:
    protected = []
    protected.extend(Path(item.ddc_program.run_path).absolute()
                     for item in run.observations if item.ddc_program is not None)
    protected.extend(Path(source.source_locator).absolute() for source in (
        run.intelligence, *(item.intelligence for item in run.observations if item.intelligence)) if source)
    protected.extend(Path(name).absolute() for item in run.observations for name in item.artifacts)
    return protected


def _kernel_resource_protected(check) -> list[Path]:
    protected = []
    resource = check.resource_check
    if resource is not None:
        protected.append(Path(resource.sandbox_binary_path).absolute())
    kernel = check.kernel_check
    if kernel is not None:
        protected.extend(Path(path).absolute() for path in (
            kernel.proof_artifact_path, kernel.lake_binary_path,
            kernel.observer.policy_path, kernel.observer.private_key_path))
    return protected


def _native_gate_protected(run: TeamworkRun) -> list[Path]:
    check = run.native_gate_check
    if check is None:
        return []
    protected = [Path(path).absolute() for path in (
        check.binary_path, check.witness_path, *check.source_paths) if path]
    observer = check.process_observer
    if observer is not None:
        protected.extend(Path(path).absolute() for path in (observer.policy_path, observer.private_key_path))
    protected.extend(_kernel_resource_protected(check))
    protected.extend(Path(item.metadata["native_gate_receipt"]["path"]).absolute()
                     for item in run.observations if "native_gate_receipt" in item.metadata)
    return protected


def _custody_protected(run: TeamworkRun) -> list[Path]:
    protected = []
    custody_paths = [run.episode_binding.get("path") if run.episode_binding else None]
    if run.provider_binding:
        accounting_path = (run.provider_binding.get("run_budget") or {}).get("accounting_path")
        custody_paths.extend((run.provider_binding.get("env_file"), accounting_path))
        if isinstance(accounting_path, str) and accounting_path:
            accounting = Path(accounting_path).absolute()
            protected.append(accounting.with_name(accounting.name + ".replies"))
    protected.extend(Path(path).absolute() for path in custody_paths if isinstance(path, str) and path)
    return protected


def _command_protected(root: Path, tokens) -> list[Path]:
    protected = []
    for token in tokens:
        if token.startswith("-"):
            continue
        path = Path(token)
        candidates = (path,) if path.is_absolute() else (root / path, Path.cwd() / path)
        for candidate in candidates:
            try:
                if candidate.exists():
                    protected.append(candidate.absolute())
            except OSError:
                pass  # A command argument need not be a filesystem path.
    return protected


def _protected_paths(root: Path, run: TeamworkRun, state_path: Path) -> list[Path]:
    state_path = checked_path(root, state_path.absolute())
    protected = [state_path]
    protected.extend(Path(point.parent_state_path).absolute() for point in run.continuations)
    protected.extend(_observation_protected(run))
    protected.extend(_native_gate_protected(run))
    requirement = run.acceptance_check
    if requirement is not None:
        protected.extend(Path(path).absolute() for path in requirement.check_source_paths)
    protected.extend(_custody_protected(run))
    tokens = requirement.operation if requirement else run.check_command
    protected.extend(_command_protected(root, tokens))
    return protected


def _refuse_tracked(root: Path, relative: str) -> None:
    tracked = _git(root, "ls-files", "--error-unmatch", "--", relative)
    if tracked.returncode == 0:
        raise ValueError("CLEANUP_TRACKED_SOURCE_PROTECTED")
    if tracked.returncode != 1:
        raise ValueError("CLEANUP_GIT_INVENTORY_UNAVAILABLE")


def _matching_recovery_bytes(root: Path, row, path: Path, recovery: Path) -> bytes:
    raw = _raw(root, path)
    if _sha(raw) != row["sha256"] or _raw(root, recovery) != raw:
        raise ValueError("CLEANUP_RECOVERY_READBACK_MISMATCH")
    return raw


def _require_git_recovery(root: Path, row, raw: bytes) -> None:
    revision = row["recovery_git_revision"]
    commit = _git(root, "rev-parse", "--verify", revision + "^{commit}")
    history = _git(root, "show", "--no-textconv", revision + ":" + row["recovery_git_path"])
    if commit.returncode or history.returncode or history.stdout != raw:
        raise ValueError("CLEANUP_GIT_RECOVERY_UNAVAILABLE_OR_MISMATCH")


def _seal_disposable_copy(lifecycle, root: Path, path: Path, row):
    entries = bundle_entries(root, path)
    seal_request = {"producer_id": "woland-working-cleanup", "source_class": "disposable-intelligence-copy",
                    "source_locator": row["path"], "entries": entries}
    sealed = validate_sealed_manifest(dict(lifecycle.seal_manifest(seal_request)))
    if any(sealed[key] != value for key, value in seal_request.items()):
        raise ValueError("CLEANUP_NATIVE_SEAL_MISMATCH")
    return sealed


def _lifecycle_decision(lifecycle, sealed, policy, extracted):
    return dict(lifecycle.evaluate_lifecycle({"source": {
        "source_id": sealed["source_id"], "producer_id": sealed["producer_id"],
        "source_class": sealed["source_class"], "source_schema_version": SOURCE_SCHEMA,
        "manifest_sha256": sealed["manifest_sha256"], "sealed": True,
        "producer_lease_active": policy["active_lease"],
        "review_scope": "named-disposable-copy-only"},
        "extraction": {"complete": not extracted.coverage_gaps and not extracted.parse_residuals,
            "extractor_version": EXTRACTOR_VERSION, "checker_version": CHECKER_VERSION,
            "coverage_gaps": extracted.coverage_gaps, "parse_residuals": extracted.parse_residuals},
        "findings": [{"finding_id": _sha(finding.encode()), "applicable": True,
                      "kind": "OPEN_WORKING_INTELLIGENCE_FINDING"} for finding in extracted.findings]}))


def _retention_decision(lifecycle, decision, policy):
    retention = dict(lifecycle.evaluate_retention({"digestion_state": decision["state"],
        "storage_state": "HOT", "evidence_reachable": True, **policy}))
    if (decision.get("authority_effect") != "None" or retention.get("authority_effect") != "None"
            or decision.get("state") != "DISCHARGED" or retention.get("disposal_eligible") is not True):
        raise ValueError("CLEANUP_RETENTION_REFUSED")
    return retention


def _preflight_one(root, row, protected, policy, lifecycle, item):
    try:
        path, recovery = _path(root, row["path"]), _path(root, row["recovery_path"])
        if any(path == ref or path.is_relative_to(ref) for ref in protected):
            raise ValueError("CLEANUP_LIVE_REFERENCE")
        _refuse_tracked(root, row["path"])
        raw = _matching_recovery_bytes(root, row, path, recovery)
        _require_git_recovery(root, row, raw)
        extracted = read_run_findings(path, native_support=DefaultNativeOperationPort())
        sealed = _seal_disposable_copy(lifecycle, root, path, row)
        item["sealed_manifest"] = sealed
        decision = _lifecycle_decision(lifecycle, sealed, policy, extracted)
        item["lifecycle"] = decision
        item["retention"] = _retention_decision(lifecycle, decision, policy)
    except Exception as exc:
        item["residual"] = str(exc)
        return f"{row['path']}: {exc}"
    return None


def _preflight_copies(root, rows, protected, policy, lifecycle, result) -> None:
    for row in rows:
        item = dict(row)
        result["copies"].append(item)
        residual = _preflight_one(root, row, protected, policy, lifecycle, item)
        if residual is not None:
            result["residuals"].append(residual)


def _delete_named_copies(root, run, rows, result) -> None:
    try:
        _readback(run)
        for row in rows:
            path, recovery = _path(root, row["path"]), _path(root, row["recovery_path"])
            if _sha(_raw(root, path)) != row["sha256"] or _raw(root, recovery) != _raw(root, path):
                raise ValueError("CLEANUP_SOURCE_CHANGED_BEFORE_REMOVAL")
        for row in rows:
            _path(root, row["path"]).unlink()
        result["status"] = "deleted"
    except Exception as exc:
        result["residuals"].append(str(exc))
        result["status"] = "partial" if any(not _path(root, row["path"]).exists() for row in rows) else "retained"


def _default_lifecycle():
    from omega_engine_operations.infrastructure.intelligence_digestion.native_lifecycle import (
        NativeIntelligenceLifecycle,
    )
    return NativeIntelligenceLifecycle()


def _cleanup_result(run, root, rows, policy) -> dict[str, Any]:
    sources = intelligence_sources(run)
    return {"schema_version": "omega.woland.working-cleanup.v1",
        "run_id": run.run_id, "initial_task_id": sources[0].initial_task_id if sources else run.run_id,
        "authority_effect": "None", "work_evidence_verdict": run.evidence_verdict,
        "policy": policy, "copies": [], "status": "retained", "residuals": [],
        "before": _inventory(root, rows)}


def cleanup_working_intelligence(
    run: TeamworkRun, *, repo_root: Path, state_path: Path, plan: dict,
    receipt_path: Path, lifecycle: IntelligenceLifecyclePort | None = None,
) -> dict[str, Any]:
    """Remove only exact, untracked disposable copies after all native fences.

    Expected refusal returns a retained receipt. Malformed/unsafe plans refuse
    before deletion. Existing receipt paths are never overwritten. The state
    and all task ancestors/outputs are protected even within the working root.
    """
    root = repo_root.absolute()
    _require_plan_dict(plan)
    working = _working_root(root, plan["working_root"])
    rows, policy = _require_rows_and_policy(plan)
    _validate_copies(root, working, rows)
    receipt_path, before_path = _receipt_paths(root, working, receipt_path)
    protected = _protected_paths(root, run, state_path)
    result = _cleanup_result(run, root, rows, policy)
    try:
        result["retained_artifacts"] = _readback(run)
    except Exception as exc:
        result["residuals"].append(f"READBACK_REFUSED: {exc}")
    if lifecycle is None:
        lifecycle = _default_lifecycle()
    _preflight_copies(root, rows, protected, policy, lifecycle, result)
    # Preserve the complete preflight before removing even the first named file.
    _write(before_path, result)
    result["before_receipt"] = {"path": before_path.relative_to(root).as_posix(),
                                "sha256": _sha(before_path.read_bytes())}
    if not result["residuals"]:
        _delete_named_copies(root, run, rows, result)
    result["after"] = _inventory(root, rows)
    _write(receipt_path, result)
    return result
