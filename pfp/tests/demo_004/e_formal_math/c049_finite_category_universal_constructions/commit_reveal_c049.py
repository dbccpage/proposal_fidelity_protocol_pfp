"""Reference self-consistency run for C049: Finite Category Universal Constructions.

AuthorityEffect: None.

Scores the frozen reference solver against this package's own judge packet and
checks that the judge's hostile mutations are rejected. It evaluates no model
and is not a Woland verdict. Labels: REFERENCE_SELF_CONSISTENT or
REFERENCE_SELF_INCONSISTENT.

Custody, stated plainly: the solver and judge file digests are computed when
this script runs, after the judge cases are visible. They bind the receipt to
the bytes that were scored; they are not a commitment made before the run
(``"pre_run_commitment": false``). Digests are SHA-256 over bytes with CRLF
normalised to LF, so they equal git-blob content on every platform.

The run folder is built in a staging directory beside its destination under
``<intelligence root>/_intelligence/_woland/runs/`` and moved into place with
os.replace. A crash moves a failure receipt into the run folder instead of
leaving an empty folder. Nothing under ``_intelligence/`` is deleted.
"""

# ruff: noqa: E402
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

for _parent in Path(__file__).resolve().parents:
    if (_parent / "omega_engine_pfp").is_dir() and (_parent / "omega_engine_woland").is_dir():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.judge_packet.exact_checker import (
    check_solution,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.reference_solver import (
    solve,
)

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c049_finite_category_universal_constructions"
RUN_PREFIX = "c049"
GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
MUTATION_ANSWER_KEYS: tuple[str, ...] = ("candidate",)
MUTATION_KILL_RULE = "EITHER_CHECKER_REJECTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"


class ReferenceRunError(ValueError):
    """Typed refusal raised by this runner (custody, empty suite, malformed mutation)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class RunFolderExistsError(FileExistsError):
    """Raised instead of overwriting an existing run folder."""


def lf_normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def hash_file(filepath: Path) -> str:
    """SHA-256 of the LF-normalised file bytes."""
    return hashlib.sha256(lf_normalized_bytes(filepath)).hexdigest()


def digest_tree(root: Path, paths: Sequence[Path]) -> tuple[str, dict[str, str]]:
    """Per-file digests keyed by path relative to root, plus a digest over the sorted pairs."""
    per_file = {p.relative_to(root).as_posix(): hash_file(p) for p in paths}
    combined = hashlib.sha256()
    for rel in sorted(per_file, key=lambda s: s.encode("utf-8")):
        combined.update(f"{rel}\0{per_file[rel]}\n".encode("utf-8"))
    return combined.hexdigest(), per_file


def mutation_answer(data: Mapping[str, Any]) -> Any:
    """Return the mutated answer under the first declared key that is present; refuse if none is."""
    for key in MUTATION_ANSWER_KEYS:
        if key in data:
            return data[key]
    raise ReferenceRunError(
        "MUTATION_PAYLOAD_MISSING",
        f"none of {MUTATION_ANSWER_KEYS} in mutation {data.get('mutation_id')!r}",
    )


def _checker_pair(case: Mapping[str, Any], answer: Any) -> tuple[bool, str, bool, str]:
    """Run both checkers; a checker verdict counts as acceptance only if it is exactly True."""
    exact_raw, exact_msg = check_solution(case, answer)
    indep_raw, indep_msg = independent_check(case, answer)
    return exact_raw is True, str(exact_msg), indep_raw is True, str(indep_msg)


def label_run(
    total_cases: int, passed_cases: int, total_mutations: int, killed_mutations: int, crashed: int
) -> str:
    """Exact-count label. Empty suites and any checker crash are inconsistent."""
    for name, value in (
        ("total_cases", total_cases),
        ("passed_cases", passed_cases),
        ("total_mutations", total_mutations),
        ("killed_mutations", killed_mutations),
        ("crashed", crashed),
    ):
        if type(value) is not int or value < 0:
            raise TypeError(f"{name} must be a non-negative int, got {value!r}")
    if total_cases == 0 or total_mutations == 0 or crashed != 0:
        return TERMINAL_REFUSE
    if passed_cases == total_cases and killed_mutations == total_mutations:
        return TERMINAL_REFERENCE_SELF_CONSISTENT
    return TERMINAL_REFUSE


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data


def write_bundle(
    staging: Path,
    report_md: str,
    dda_rows: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> dict[str, str]:
    """Write report, DDC rows, summary and a receipt binding their digests into the staging dir."""
    novella_bytes = report_md.encode("utf-8")
    (staging / "novella.md").write_bytes(novella_bytes)
    dda_bytes = "".join(json.dumps(row, sort_keys=True) + "\n" for row in dda_rows).encode("utf-8")
    (staging / "dda_actions.jsonl").write_bytes(dda_bytes)
    summary_bytes = _write_json(staging / "summary.json", summary)
    digests = {
        "dda_actions_sha256": hashlib.sha256(dda_bytes).hexdigest(),
        "novella_sha256": hashlib.sha256(novella_bytes).hexdigest(),
        "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
    }
    receipt_bytes = _write_json(staging / "receipt.json", {**receipt, **digests})
    digests["receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    return digests


def _fail_into_place(staging: Path, run_dir: Path, error: BaseException) -> None:
    """Write a failure receipt into staging and move it to run_dir; never delete anything."""
    try:
        _write_json(
            staging / FAILURE_RECEIPT_NAME,
            {
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "error_code": getattr(error, "code", None),
                "error_message": str(error),
                "error_type": type(error).__name__,
                "files_present": sorted(p.name for p in staging.iterdir()),
                "status": "RUN_FAILED",
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
        if not run_dir.exists():
            os.replace(staging, run_dir)
    except OSError as custody_error:
        error.add_note(
            f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging}"
        )


def run_gate(intelligence_repo_root: Path | None = None) -> bool:
    """Score the reference solver, check the mutations, and persist the run folder. Returns True when consistent."""
    challenge_dir = Path(__file__).resolve().parent
    ref_solver_dir = challenge_dir / "reference_solver"
    judge_dir = challenge_dir / "judge_packet"
    cases_dir = judge_dir / "cases"
    mutations_dir = judge_dir / "hostile_mutations"

    t0 = time.time()
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(t0)) + f"{int((t0 % 1) * 1_000_000):06d}Z"
    run_id = f"{RUN_PREFIX}_eval_{stamp}"
    repo_root = (
        intelligence_repo_root
        if intelligence_repo_root is not None
        else resolve_intelligence_repo_root()
    )
    run_dir = repo_root / "_ic/darpa/woland" / "runs" / run_id
    if run_dir.exists():
        raise RunFolderExistsError(f"run folder already exists: {run_dir}")
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f".{run_id}.staging.", dir=str(run_dir.parent)))

    try:
        solver_files = sorted(ref_solver_dir.glob("*.py"))
        case_files = sorted(cases_dir.glob("*.json"))
        mutation_files = sorted(mutations_dir.glob("*.json"))
        checker_files = sorted(judge_dir.glob("*.py"))
        if not solver_files:
            raise ReferenceRunError(
                "EMPTY_SOLVER", f"no reference solver files in {ref_solver_dir}"
            )
        if not case_files:
            raise ReferenceRunError("EMPTY_JUDGE_SUITE", f"no judge case files in {cases_dir}")
        if not mutation_files:
            raise ReferenceRunError("EMPTY_MUTATION_SUITE", f"no mutation files in {mutations_dir}")

        solver_digest, solver_hashes = digest_tree(challenge_dir, solver_files)
        judge_digest, judge_hashes = digest_tree(
            challenge_dir, case_files + mutation_files + checker_files
        )

        case_results: list[dict[str, Any]] = []
        passed_cases = 0
        crashed = 0
        for cf in case_files:
            case = json.loads(cf.read_text(encoding="utf-8"))
            try:
                answer = solve(case)
                exact_ok, exact_msg, indep_ok, indep_msg = _checker_pair(case, answer)
                error = None
            except Exception as exc:  # recorded as a failed case, never as a pass
                exact_ok = indep_ok = False
                exact_msg = indep_msg = ""
                error = f"{type(exc).__name__}: {exc}"
                crashed += 1
            case_passed = exact_ok and indep_ok
            passed_cases += 1 if case_passed else 0
            case_results.append(
                {
                    "case_file": cf.name,
                    "error": error,
                    "exact_checker": {"accepted": exact_ok, "msg": exact_msg},
                    "independent_checker": {"accepted": indep_ok, "msg": indep_msg},
                    "passed": case_passed,
                }
            )

        mutation_results: list[dict[str, Any]] = []
        killed_mutations = 0
        for mf in mutation_files:
            data = json.loads(mf.read_text(encoding="utf-8"))
            try:
                exact_ok, exact_msg, indep_ok, indep_msg = _checker_pair(
                    data["case"], mutation_answer(data)
                )
                error = None
                killed = bool((not exact_ok) or (not indep_ok))
            except ReferenceRunError:
                raise
            except Exception as exc:  # a crash is not a rejection; it makes the run inconsistent
                exact_ok = indep_ok = False
                exact_msg = indep_msg = ""
                error = f"{type(exc).__name__}: {exc}"
                killed = False
                crashed += 1
            killed_mutations += 1 if killed else 0
            mutation_results.append(
                {
                    "error": error,
                    "exact_checker": {"accepted": exact_ok, "msg": exact_msg},
                    "independent_checker": {"accepted": indep_ok, "msg": indep_msg},
                    "killed": killed,
                    "mutation_file": mf.name,
                }
            )

        total_cases = len(case_files)
        total_mutations = len(mutation_files)
        verdict = label_run(total_cases, passed_cases, total_mutations, killed_mutations, crashed)
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))

        counts = {
            "checker_crashes": crashed,
            "killed_mutations": killed_mutations,
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "total_mutations": total_mutations,
        }
        summary = {
            **counts,
            "authority_effect": "None",
            "case_results": case_results,
            "challenge_id": CHALLENGE_ID,
            "gate_scope": GATE_SCOPE,
            "mutation_kill_rule": MUTATION_KILL_RULE,
            "mutation_results": mutation_results,
            "run_id": run_id,
            "verdict": verdict,
        }
        receipt = {
            **counts,
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "commitment_timing": "COMPUTED_AT_REVEAL",
            "digest_normalization": "CRLF_TO_LF",
            "gate_scope": GATE_SCOPE,
            "judge_files_sha256": judge_hashes,
            "judge_tree_sha256": judge_digest,
            "mutation_kill_rule": MUTATION_KILL_RULE,
            "pre_run_commitment": False,
            "run_id": run_id,
            "solver_files_sha256": solver_hashes,
            "solver_tree_sha256": solver_digest,
            "timestamp_utc": timestamp_utc,
            "verdict": verdict,
        }
        report_md = "\n".join(
            [
                "# Reference self-consistency report: C049: Finite Category Universal Constructions",
                "",
                f"- Run ID: `{run_id}`",
                f"- Label: `{verdict}`",
                f"- Scope: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet; "
                "no model was evaluated and this is not a Woland verdict.",
                "- Digests were computed at reveal time; there is no commitment made before the run.",
                f"- Judge cases passed by both checkers: {passed_cases}/{total_cases}",
                f"- Hostile mutations rejected ({MUTATION_KILL_RULE}): {killed_mutations}/{total_mutations}",
                f"- Checker crashes: {crashed}",
                f"- Solver tree digest: `{solver_digest}`",
                f"- Judge tree digest: `{judge_digest}`",
                "",
            ]
        )
        dda_rows = [
            {
                "letter": "C",
                "action": "intake_judge_files",
                "case_count": total_cases,
                "mutation_count": total_mutations,
            },
            {
                "letter": "R",
                "action": "score_reference_outputs",
                "passed_cases": passed_cases,
                "checker_crashes": crashed,
            },
            {
                "letter": "D",
                "action": "run_hostile_mutations",
                "killed_mutations": killed_mutations,
            },
            {"letter": "T", "action": "emit_self_consistency_label", "label": verdict},
        ]
        write_bundle(work, report_md, dda_rows, summary, receipt)
    except BaseException as error:
        _fail_into_place(work, run_dir, error)
        raise

    os.replace(work, run_dir)
    print(
        f"{CHALLENGE_ID}: {verdict} (cases {passed_cases}/{total_cases}, mutations {killed_mutations}/{total_mutations}); run folder {run_dir}"
    )
    return verdict == TERMINAL_REFERENCE_SELF_CONSISTENT


if __name__ == "__main__":
    sys.exit(0 if run_gate() else 1)
