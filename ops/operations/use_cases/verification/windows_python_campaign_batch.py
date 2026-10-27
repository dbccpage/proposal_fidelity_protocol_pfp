"""Run one bounded Windows Python-test batch and retain fail-closed evidence.

This runner executes one to three explicit tracked test files with the invoking
interpreter. It does not install tooling, change configuration, call providers,
or make native/Linux/broad-suite claims. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import re
import sys
import xml.etree.ElementTree as ET
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from operations.use_cases.verification.windows_campaign_preflight import (
    PreflightError,
    Recorder,
    digest,
    git,
    utc_now,
)

SCHEMA = "core.windows-python-campaign.batch.v1"
SESSION_SCHEMA = "core.windows-python-campaign.pytest-session.v1"
SESSION_OPTION = "--core-campaign-session-json"
RUNNER_PATH = (
    "operations/use_cases/verification/"
    "windows_python_campaign_batch.py"
)
DEPENDENCIES = {
    "pytest": "pytest",
    "xdist": "pytest-xdist",
    "pydantic": "pydantic",
    "PyYAML": "PyYAML",
}
LOCKFILE_NAMES = frozenset(
    {
        "Cargo.lock",
        "Pipfile.lock",
        "npm-shrinkwrap.json",
        "package-lock.json",
        "pdm.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "uv.lock",
        "yarn.lock",
    }
)
WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
PROCESS_ENVIRONMENT = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
}


def require_clean_status(status: bytes) -> None:
    """Refuse any tracked, staged, or untracked worktree input."""
    if status:
        raise PreflightError(
            "CLEAN_WORKTREE_REQUIRED: tracked and untracked inputs must be empty"
        )


def validate_external_new(root: Path, candidate: Path, label: str) -> Path:
    """Resolve a new artifact path and prove it is outside the source tree."""
    root = root.resolve()
    supplied = candidate
    if supplied.exists() or supplied.is_symlink():
        raise PreflightError(f"{label}_MUST_BE_NEW: {supplied}")
    candidate = supplied.resolve()
    if candidate == root or candidate.is_relative_to(root):
        raise PreflightError(f"{label}_MUST_BE_EXTERNAL: {candidate}")
    return candidate


def validate_test_files(
    root: Path,
    requested: Sequence[str],
    tracked_paths: set[str],
) -> list[str]:
    """Return canonical repository-relative paths for a bounded explicit batch."""
    if not 1 <= len(requested) <= 3:
        raise PreflightError("TEST_FILE_COUNT_INVALID: expected 1..3 explicit files")

    root = root.resolve()
    selected: list[str] = []
    for raw in requested:
        portable = raw.replace("\\", "/")
        relative = PurePosixPath(portable)
        if (
            not raw
            or "\x00" in raw
            or Path(raw).is_absolute()
            or WINDOWS_DRIVE.match(portable)
            or relative.is_absolute()
            or ".." in relative.parts
            or portable.startswith(":")
            or glob.has_magic(portable)
        ):
            raise PreflightError(f"TEST_FILE_NOT_EXPLICIT_RELATIVE_PATH: {raw!r}")
        if relative.suffix != ".py":
            raise PreflightError(f"TEST_FILE_NOT_PYTHON_FILE: {raw!r}")

        resolved = root.joinpath(*relative.parts).resolve()
        if not resolved.is_relative_to(root):
            raise PreflightError(f"TEST_FILE_ESCAPES_ROOT: {raw!r}")
        if not resolved.is_file():
            raise PreflightError(f"TEST_FILE_MISSING: {raw!r}")
        canonical = resolved.relative_to(root).as_posix()
        if canonical not in tracked_paths:
            raise PreflightError(f"TEST_FILE_UNTRACKED: {canonical}")
        if canonical in selected:
            raise PreflightError(f"TEST_FILE_DUPLICATE: {canonical}")
        selected.append(canonical)
    return selected


def dependency_versions() -> dict[str, str]:
    """Read installed distribution versions without importing test dependencies."""
    versions: dict[str, str] = {}
    for label, distribution in DEPENDENCIES.items():
        try:
            versions[label] = metadata.version(distribution)
        except metadata.PackageNotFoundError as error:
            raise PreflightError(
                f"REQUIRED_DISTRIBUTION_MISSING: {distribution}; installation is not automatic"
            ) from error
    return versions


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def pytest_addoption(parser: Any) -> None:
    """Expose an opt-in path used only by this runner's pytest subprocess."""
    group = parser.getgroup("core-windows-campaign")
    group.addoption(
        SESSION_OPTION,
        action="store",
        default=None,
        dest="core_campaign_session_json",
        help="write master-session collection metadata for a bounded campaign batch",
    )


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    """Record the controller's real collection count; xdist workers stay silent."""
    destination = session.config.getoption("core_campaign_session_json", default=None)
    if destination is None or hasattr(session.config, "workerinput"):
        return
    payload = {
        "schema": SESSION_SCHEMA,
        "testscollected": int(session.testscollected),
        "exitstatus": int(exitstatus),
        "role": "pytest-controller",
    }
    path = Path(destination)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


def parse_junit(payload: bytes) -> dict[str, int]:
    """Classify JUnit records without relabelling them as collection counts."""
    try:
        document = ET.fromstring(payload)
    except ET.ParseError as error:
        raise PreflightError(f"JUNIT_XML_INVALID: {error}") from error
    if _tag(document) not in {"testsuite", "testsuites"}:
        raise PreflightError(f"JUNIT_XML_ROOT_INVALID: {_tag(document)}")

    cases = [element for element in document.iter() if _tag(element) == "testcase"]
    counts = {
        "testcase_records": len(cases),
        "completed_body_records": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "xfailed": 0,
    }
    for case in cases:
        children = list(case)
        errors = [child for child in children if _tag(child) == "error"]
        failures = [child for child in children if _tag(child) == "failure"]
        skips = [child for child in children if _tag(child) == "skipped"]
        if errors:
            counts["errors"] += 1
        elif failures:
            counts["failed"] += 1
            counts["completed_body_records"] += 1
        elif skips:
            outcome_types = {
                child.attrib.get("type", "").casefold() for child in skips
            }
            if "pytest.xfail" in outcome_types:
                counts["xfailed"] += 1
                counts["completed_body_records"] += 1
            else:
                counts["skipped"] += 1
        else:
            counts["passed"] += 1
            counts["completed_body_records"] += 1
    return counts


def parse_session_stats(payload: bytes) -> dict[str, int]:
    """Validate the small master-session record emitted by this pytest plugin."""
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"PYTEST_SESSION_JSON_INVALID: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != SESSION_SCHEMA:
        raise PreflightError("PYTEST_SESSION_JSON_SCHEMA_INVALID")
    if document.get("role") != "pytest-controller":
        raise PreflightError("PYTEST_SESSION_JSON_ROLE_INVALID")
    result: dict[str, int] = {}
    for field in ("testscollected", "exitstatus"):
        value = document.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PreflightError(f"PYTEST_SESSION_JSON_{field.upper()}_INVALID")
        result[field] = value
    return result


def combine_counts(
    junit_counts: dict[str, int], session_stats: dict[str, int]
) -> dict[str, int]:
    """Combine pytest's true collection count with conservative JUnit outcomes."""
    return {
        "collected": session_stats["testscollected"],
        "executed": junit_counts["completed_body_records"],
        "passed": junit_counts["passed"],
        "failed": junit_counts["failed"],
        "errors": junit_counts["errors"],
        "skipped": junit_counts["skipped"],
        "xfailed": junit_counts["xfailed"],
        "junit_testcase_records": junit_counts["testcase_records"],
    }


def classify_batch(
    counts: dict[str, int] | None,
    *,
    exit_code: int | None,
    producer_failure: str | None,
    evidence_failures: Sequence[str],
) -> dict[str, Any]:
    """Return a fail-closed verdict for the producer and its JUnit population."""
    reasons: list[str] = []
    if producer_failure is not None:
        reasons.append("PYTEST_PRODUCER_FAILURE")
    if exit_code is None:
        reasons.append("PYTEST_EXIT_CODE_MISSING")
    elif exit_code != 0:
        reasons.append(f"PYTEST_EXIT_NONZERO:{exit_code}")
    reasons.extend(evidence_failures)
    if counts is None:
        reasons.append("TEST_COUNTS_MISSING")
    else:
        if counts["collected"] == 0:
            reasons.append("NO_COLLECTED_TESTS")
        if counts["executed"] == 0:
            reasons.append("NO_EXECUTED_TESTS")
        if counts["junit_testcase_records"] != counts["collected"]:
            reasons.append(
                "JUNIT_SESSION_COUNT_MISMATCH:"
                f"{counts['junit_testcase_records']}!={counts['collected']}"
            )
        for field, reason in (
            ("failed", "FAILED_TESTS"),
            ("errors", "TEST_OR_SETUP_ERRORS"),
            ("skipped", "SKIPPED_TESTS"),
            ("xfailed", "XFAILED_TESTS"),
        ):
            if counts[field]:
                reasons.append(f"{reason}:{counts[field]}")
    return {"status": "PASS" if not reasons else "FAILED", "reasons": reasons}


def _nul_paths(payload: bytes) -> list[str]:
    return payload.decode("utf-8", errors="surrogateescape").split("\0")[:-1]


def _file_identity(root: Path, source: str, relative: str) -> dict[str, Any]:
    worktree_payload = (
        root / Path(*PurePosixPath(relative).parts)
    ).read_bytes()
    blob_payload = git(root, "cat-file", "-p", f"{source}:{relative}")
    return {
        "path": relative,
        "blob_oid": git(root, "rev-parse", f"{source}:{relative}").decode().strip(),
        "blob_sha256": digest(blob_payload),
        "blob_bytes": len(blob_payload),
        "worktree_sha256": digest(worktree_payload),
        "worktree_bytes": len(worktree_payload),
    }


def _lockfile_identities(
    root: Path, source: str, tracked_paths: set[str]
) -> dict[str, dict[str, Any]]:
    identities = {
        relative: _file_identity(root, source, relative)
        for relative in sorted(tracked_paths)
        if PurePosixPath(relative).name in LOCKFILE_NAMES
    }
    if not identities:
        raise PreflightError("LOCKFILE_SET_EMPTY")
    return identities


def _save_batch_receipt(report_dir: Path, receipt: dict[str, Any]) -> None:
    (report_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _prepare_python_batch(root: Path, report_dir: Path, basetemp: Path, requested_tests: Sequence[str]):
    if platform.system() != "Windows":
        raise PreflightError("WINDOWS_ONLY_CAMPAIGN")
    root = root.resolve()
    if not root.is_dir():
        raise PreflightError(f"REPOSITORY_ROOT_MISSING: {root}")
    git_root = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if git_root != root:
        raise PreflightError(f"ROOT_IS_NOT_GIT_TOPLEVEL: {root}")

    report_dir = validate_external_new(root, report_dir, "REPORT_DIRECTORY")
    basetemp = validate_external_new(root, basetemp, "PYTEST_BASETEMP")
    if (
        report_dir == basetemp
        or report_dir.is_relative_to(basetemp)
        or basetemp.is_relative_to(report_dir)
    ):
        raise PreflightError("REPORT_AND_BASETEMP_MUST_NOT_OVERLAP")

    initial_status = git(
        root, "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    require_clean_status(initial_status)
    source = git(root, "rev-parse", "HEAD").decode().strip()
    source_tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    tracked_paths = set(
        _nul_paths(git(root, "ls-tree", "-r", "--name-only", "-z", source))
    )
    selected = validate_test_files(root, requested_tests, tracked_paths)
    if RUNNER_PATH not in tracked_paths:
        raise PreflightError(f"RUNNER_NOT_TRACKED_AT_SOURCE: {RUNNER_PATH}")
    versions = dependency_versions()
    lockfiles = _lockfile_identities(root, source, tracked_paths)
    test_files = [_file_identity(root, source, path) for path in selected]
    runner = _file_identity(root, source, RUNNER_PATH)

    report_dir.mkdir(parents=True, exist_ok=False)
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    if basetemp.exists() or basetemp.is_symlink():
        raise PreflightError(f"PYTEST_BASETEMP_MUST_BE_NEW: {basetemp}")
    return {
        "root": root,
        "report_dir": report_dir,
        "basetemp": basetemp,
        "source": source,
        "source_tree": source_tree,
        "selected": selected,
        "versions": versions,
        "lockfiles": lockfiles,
        "test_files": test_files,
        "runner": runner,
    }


def _read_named_artifact(report_dir: Path, path: Path, missing_code: str, parser):
    if (
        not path.is_file()
        or path.is_symlink()
        or report_dir.is_symlink()
        or path.resolve().parent != report_dir.resolve()
    ):
        return None, [missing_code], None
    try:
        payload = path.read_bytes()
    except (PreflightError, OSError) as error:
        return None, [str(error)], None
    artifact = {"sha256": digest(payload), "bytes": len(payload)}
    try:
        parsed = parser(payload)
    except (PreflightError, OSError) as error:
        return None, [str(error)], artifact
    return parsed, [], artifact


def _batch_evidence(report_dir: Path, junit_xml: Path, session_json: Path, receipt: dict, exit_code):
    evidence_failures: list[str] = []
    junit_counts, junit_failures, junit_artifact = _read_named_artifact(
        report_dir, junit_xml, "JUNIT_XML_MISSING_OR_UNSAFE", parse_junit
    )
    evidence_failures.extend(junit_failures)
    if junit_artifact is not None:
        receipt["artifacts"]["pytest.junit.xml"] = junit_artifact
    session_stats, session_failures, session_artifact = _read_named_artifact(
        report_dir, session_json, "PYTEST_SESSION_JSON_MISSING_OR_UNSAFE", parse_session_stats
    )
    evidence_failures.extend(session_failures)
    if session_artifact is not None:
        receipt["artifacts"]["pytest.session.json"] = session_artifact
    if session_stats is not None and session_stats["exitstatus"] != exit_code:
        evidence_failures.append(
            "PYTEST_SESSION_EXIT_MISMATCH:"
            f"{session_stats['exitstatus']}!={exit_code}"
        )
    counts = None
    if junit_counts is not None and session_stats is not None:
        counts = combine_counts(junit_counts, session_stats)
    return junit_counts, session_stats, counts, evidence_failures


def _source_unchanged_after(root: Path, source: str, source_tree: str, receipt: dict) -> bool:
    try:
        final_status = git(
            root, "status", "--porcelain=v1", "-z", "--untracked-files=all"
        )
        final_source = git(root, "rev-parse", "HEAD").decode().strip()
        final_tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
        source_unchanged = (
            not final_status and final_source == source and final_tree == source_tree
        )
        receipt["source_after"] = {
            "commit": final_source,
            "tree": final_tree,
            "status_sha256": digest(final_status),
        }
        return source_unchanged
    except PreflightError as error:
        receipt["source_check_failure"] = str(error)
        return False


def run_batch(
    root: Path,
    report_dir: Path,
    basetemp: Path,
    requested_tests: Sequence[str],
) -> int:
    """Run and classify one foreground Windows pytest batch."""
    prepared = _prepare_python_batch(root, report_dir, basetemp, requested_tests)
    root = prepared["root"]
    report_dir = prepared["report_dir"]
    basetemp = prepared["basetemp"]
    source = prepared["source"]
    source_tree = prepared["source_tree"]
    selected = prepared["selected"]
    versions = prepared["versions"]
    lockfiles = prepared["lockfiles"]
    test_files = prepared["test_files"]
    runner = prepared["runner"]

    environment = dict(os.environ)
    environment.update(PROCESS_ENVIRONMENT)
    recorder = Recorder(report_dir, environment)
    junit_xml = report_dir / "pytest.junit.xml"
    session_json = report_dir / "pytest.session.json"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "-p",
        "operations.use_cases.verification.windows_python_campaign_batch",
        "-n",
        "8",
        "--import-mode=importlib",
        "-o",
        "xfail_strict=true",
        "--basetemp",
        str(basetemp),
        "--junitxml",
        str(junit_xml),
        SESSION_OPTION,
        str(session_json),
        *selected,
    ]
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "authority_effect": "None",
        "status": "FAILED",
        "source_commit": source,
        "source_tree": source_tree,
        "source_clean_before": True,
        "tracked_dirty": False,
        "untracked_paths": [],
        "source_unchanged_after": False,
        "started_utc": utc_now(),
        "host": {
            "platform": platform.platform(),
            "system": platform.system(),
            "node": platform.node(),
            "machine": platform.machine(),
            "release": platform.release(),
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "process_environment": {
            key: environment[key] for key in sorted(PROCESS_ENVIRONMENT)
        },
        "dependencies": versions,
        "lockfiles": lockfiles,
        "lockfile_scope": "all tracked files with recognized lockfile basenames",
        "runner": runner,
        "scope": {
            "selected_test_files": test_files,
            "selected_count": len(selected),
            "maximum_test_files": 3,
        },
        "pytest": {
            "workers": 8,
            "import_mode": "importlib",
            "xfail_strict": True,
            "basetemp": str(basetemp),
            "junit_xml": "pytest.junit.xml",
            "session_json": "pytest.session.json",
            "count_semantics": {
                "collected": "pytest controller session.testscollected",
                "executed": (
                    "JUnit records with a completed passing, failing, or xfailed "
                    "test body"
                ),
                "errors": (
                    "conservative: setup, call, and teardown errors are not "
                    "credited as executed"
                ),
                "junit_testcase_records": "raw JUnit testcase element count",
            },
            "junit_counts": None,
            "session_stats": None,
            "counts": None,
            "exit_code": None,
        },
        "commands": recorder.records,
        "artifacts": {},
        "failure_reasons": ["RUN_NOT_COMPLETED"],
        "nonclaims": [
            "native or Rust verification",
            "broad Python-suite coverage",
            "live provider behavior",
            "Linux portability",
            "campaign completion",
        ],
    }

    _save_batch_receipt(report_dir, receipt)
    producer_failure: str | None = None
    try:
        recorder.run("pytest-batch", command, root)
    except PreflightError as error:
        producer_failure = str(error)

    record = recorder.records[-1] if recorder.records else None
    exit_code = record["exit_code"] if record is not None else None
    receipt["pytest"]["exit_code"] = exit_code
    if producer_failure is not None:
        receipt["pytest"]["producer_failure"] = producer_failure

    junit_counts, session_stats, counts, evidence_failures = _batch_evidence(
        report_dir, junit_xml, session_json, receipt, exit_code
    )
    receipt["pytest"]["junit_counts"] = junit_counts
    receipt["pytest"]["session_stats"] = session_stats
    receipt["pytest"]["counts"] = counts

    verdict = classify_batch(
        counts,
        exit_code=exit_code,
        producer_failure=producer_failure,
        evidence_failures=evidence_failures,
    )
    reasons = list(verdict["reasons"])
    source_unchanged = _source_unchanged_after(root, source, source_tree, receipt)
    receipt["source_unchanged_after"] = source_unchanged
    if not source_unchanged:
        reasons.append("SOURCE_CHANGED_DURING_TEST_BATCH")

    receipt["failure_reasons"] = reasons
    receipt["status"] = "PASS" if not reasons else "FAILED"
    receipt["finished_utc"] = utc_now()
    _save_batch_receipt(report_dir, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt": str(report_dir / "receipt.json"),
                "failure_reasons": reasons,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if receipt["status"] == "PASS" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--basetemp", type=Path, required=True)
    parser.add_argument("test_files", nargs="+")
    args = parser.parse_args(argv)
    try:
        return run_batch(
            args.root.resolve(),
            args.report_dir,
            args.basetemp,
            args.test_files,
        )
    except (PreflightError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
