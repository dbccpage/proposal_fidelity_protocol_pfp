# AuthorityEffect: None.
"""Reference self-consistency gate and run-folder persistence for C029 (Minimum-Weight Surface-Code Decoding).

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. Decisions use exact
counts only:

- REFERENCE_SELF_CONSISTENT: at least one case was scored and every case was
  accepted; at least one mutation was run and every mutation was rejected;
  no critical error or defect was reported; the exact billed cost does not
  exceed the exact ceiling.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty case suite,
  an empty mutation suite, or counts that contradict each other.
- OPEN_RESIDUAL: reserved label (this gate does not emit it).

Costs are exact USD (int or fractions.Fraction); floats and booleans are
refused. Run folders hold a four-file bundle (report written as novella.md,
dda_actions.jsonl, summary.json, receipt.json) derived only from the inputs.
Each bundle is staged beside its destination under ``<repo>/_intelligence``
and moved into place with os.replace. An existing destination always raises
RunFolderExistsError. If writing fails, a failure_receipt.json is written and
the staged files are moved into the run folder anyway: nothing under
``_intelligence/`` is ever deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c029_surface_code_min_weight_decoding"
CHALLENGE_TITLE = "C029 (Minimum-Weight Surface-Code Decoding)"
TIER = "T3"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
LABEL_INCONSISTENT_WITH_COUNTS = "LABEL_INCONSISTENT_WITH_COUNTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"
BUNDLE_FILE_ORDER = ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json")


class RunFolderExistsError(FileExistsError):
    """Raised when attempting to overwrite an existing run directory."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


def utc_timestamp_now() -> str:
    """Returns canonical UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sanitize_run_key(key: str) -> str:
    """Sanitizes run key for directory safety while preserving deterministic naming."""
    clean = re.sub(r"[^a-zA-Z0-9_-]", "_", key.strip())
    if not clean or clean == "_":
        return f"c029_run_{int(datetime.now(timezone.utc).timestamp())}"
    return clean


def canonical_json_bytes(obj: Any) -> bytes:
    """Sorted-key compact JSON bytes (ASCII, no NaN)."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_digest_bytes(data: bytes) -> str:
    """Returns hexadecimal SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path) -> str:
    """SHA-256 of the file bytes with CRLF normalised to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require_count(name: str, value: Any) -> int:
    """A count is a non-negative int (bool and float refused)."""
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int; got {value!r}")
    return value


def exact_usd(name: str, value: Any) -> Fraction:
    """An amount in USD as an exact int or Fraction (bool and float refused), non-negative."""
    if type(value) is int or type(value) is Fraction:
        if value < 0:
            raise ValueError(f"{name} must be non-negative; got {value}")
        return Fraction(value)
    raise TypeError(
        f"{name} must be an exact int or Fraction USD amount; got {type(value).__name__}"
    )


def decide_label(
    cases_evaluated: int,
    cases_passed: int,
    mutations_killed: int,
    mutations_total: int,
    cost_usd: Any,
    ceiling_usd: Any,
    critical_errors: int = 0,
    defect_count: int = 0,
) -> tuple[str, str]:
    """Return (label, reason) from exact counts and exact costs."""
    cases_evaluated = require_count("cases_evaluated", cases_evaluated)
    cases_passed = require_count("cases_passed", cases_passed)
    mutations_killed = require_count("mutations_killed", mutations_killed)
    mutations_total = require_count("mutations_total", mutations_total)
    critical_errors = require_count("critical_errors", critical_errors)
    defect_count = require_count("defect_count", defect_count)
    cost = exact_usd("cost_usd", cost_usd)
    ceiling = exact_usd("ceiling_usd", ceiling_usd)

    if cases_passed > cases_evaluated or mutations_killed > mutations_total:
        return (
            TERMINAL_REFUSE,
            "Counts contradict each other (passed > evaluated or killed > total)",
        )
    if cases_evaluated == 0:
        return TERMINAL_REFUSE, "Empty judge suite: 0 cases scored"
    if mutations_total == 0:
        return TERMINAL_REFUSE, "Empty mutation suite: 0 mutations run"
    if critical_errors > 0 or defect_count > 0:
        return (
            TERMINAL_REFUSE,
            f"{critical_errors} critical errors and {defect_count} defects reported",
        )
    if cases_passed != cases_evaluated:
        return (
            TERMINAL_REFUSE,
            f"{cases_evaluated - cases_passed} of {cases_evaluated} cases failed",
        )
    if mutations_killed != mutations_total:
        return (
            TERMINAL_REFUSE,
            f"{mutations_total - mutations_killed} of {mutations_total} mutations survived the checkers",
        )
    if cost > ceiling:
        return TERMINAL_REFUSE, f"Billed cost {cost} USD exceeds ceiling {ceiling} USD"
    return (
        TERMINAL_REFERENCE_SELF_CONSISTENT,
        f"Reference outputs accepted on {cases_passed}/{cases_evaluated} cases; "
        f"{mutations_killed}/{mutations_total} mutations rejected",
    )


def derived_claim_hygiene(
    verdict: str,
    cases_evaluated: int,
    cases_passed: int,
    mutations_killed: int,
    mutations_total: int,
) -> dict[str, str]:
    """Claim hygiene derived from the measured counts of this run."""
    return {
        "supports": (
            f"The frozen reference solver's outputs were accepted on {cases_passed}/{cases_evaluated} judge cases, "
            f"and the dual evaluator rejected {mutations_killed}/{mutations_total} hostile mutations."
        ),
        "does_not_support": (
            "Any statement about a model (none was evaluated), about checker soundness or independence, "
            "about cases outside this judge packet, or a Woland verdict."
        ),
        "narrowest_defensible_claim": (
            f"Reference self-consistency label {verdict} on the {cases_evaluated} judge case files and "
            f"{mutations_total} mutation files that match the committed manifest."
        ),
        "next_test_needed": (
            "Score a participant submission under a commitment made before the run and have the Woland swarm "
            "evaluate the bound checker receipts."
        ),
    }


def _write_failure_receipt(staging_dir: Path, target_dir: Path, error: BaseException) -> None:
    payload = {
        "authority_effect": "None",
        "error_message": str(error),
        "error_type": type(error).__name__,
        "files_present": sorted(p.name for p in staging_dir.iterdir()),
        "status": "RUN_FAILED",
        "target_dir": target_dir.name,
        "timestamp_utc": utc_timestamp_now(),
    }
    (staging_dir / FAILURE_RECEIPT_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def write_bundle(target_dir: Path, files: Mapping[str, bytes]) -> Path:
    """Stage the bundle beside target_dir, then os.replace it into place.

    On failure a failure_receipt.json is written and the staged files are moved
    into target_dir; if that move fails the staging directory is left in place.
    Nothing is deleted.
    """
    if target_dir.exists():
        raise RunFolderExistsError(f"Directory {target_dir} already exists.")
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{target_dir.name}.staging.", dir=str(target_dir.parent))
    )
    try:
        for name in BUNDLE_FILE_ORDER:
            (staging_dir / name).write_bytes(files[name])
    except BaseException as error:
        try:
            _write_failure_receipt(staging_dir, target_dir, error)
            os.replace(staging_dir, target_dir)
        except OSError as custody_error:
            error.add_note(
                f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging_dir}"
            )
        raise
    os.replace(staging_dir, target_dir)
    return target_dir


def chain_dda_events(dda_events: Sequence[Mapping[str, Any]]) -> tuple[bytes, str]:
    """Hash-chain events: each line is sorted-key JSON of {event_index, parent_sha256, payload}."""
    parent_sha = "0" * 64
    lines: list[bytes] = []
    for idx, ev in enumerate(dda_events):
        line_bytes = canonical_json_bytes(
            {"event_index": idx, "parent_sha256": parent_sha, "payload": dict(ev)}
        )
        parent_sha = sha256_digest_bytes(line_bytes)
        lines.append(line_bytes + b"\n")
    return b"".join(lines), parent_sha


class WolandRealityGate:
    """Reference self-consistency gate and run-folder writer for C029 (historical class name kept).

    ``base_repo_root`` is the directory that contains ``_intelligence/``; by
    default it is resolved with ``resolve_intelligence_repo_root()``.
    """

    def __init__(
        self, challenge_id: str = CHALLENGE_ID, *, base_repo_root: Path | None = None
    ) -> None:
        self.challenge_id = challenge_id
        self.repo_root = (
            Path(base_repo_root) if base_repo_root is not None else resolve_intelligence_repo_root()
        )

    def evaluate_verdict(
        self,
        cases_evaluated: int,
        cases_passed: int,
        mutations_killed: int,
        mutations_total: int,
        cost_usd: Any,
        ceiling_usd: Any,
        critical_errors: int = 0,
        defect_count: int = 0,
    ) -> str:
        """Return the self-consistency label decided on exact counts and exact USD amounts."""
        label, _reason = decide_label(
            cases_evaluated,
            cases_passed,
            mutations_killed,
            mutations_total,
            cost_usd,
            ceiling_usd,
            critical_errors=critical_errors,
            defect_count=defect_count,
        )
        return label

    def emit_novella(
        self,
        task_key: str,
        verdict: str,
        cases_evaluated: int,
        cases_passed: int,
        mutations_killed: int,
        mutations_total: int,
        cost_usd: Any,
        evidence_summary: Mapping[str, Any],
    ) -> str:
        """Render the run report from measured values only (kept under the historical method name)."""
        cost = exact_usd("cost_usd", cost_usd)
        hygiene = derived_claim_hygiene(
            verdict, cases_evaluated, cases_passed, mutations_killed, mutations_total
        )
        lines = [
            f"# Reference self-consistency report: {CHALLENGE_TITLE}",
            "",
            f"**Task key**: `{task_key}`  ",
            f"**Label**: `{verdict}`  ",
            f"**Scope**: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet. "
            "No model was evaluated and this is not a Woland verdict.  ",
            "**AuthorityEffect**: None  ",
            "",
            "## Measured values",
            "",
            "| Quantity | Value |",
            "| --- | --- |",
            f"| Judge cases scored | {cases_evaluated} |",
            f"| Cases accepted by the dual evaluator | {cases_passed} |",
            f"| Mutations run | {mutations_total} |",
            f"| Mutations rejected | {mutations_killed} |",
            f"| Billed cost (exact USD) | {cost} |",
            f"| Ceiling (exact USD) | {evidence_summary.get('ceiling_usd', 'not reported')} |",
            "",
            "## Four-Part Claim Hygiene Summary",
            "",
            f"1. **Supports**: {hygiene['supports']}",
            f"2. **Does not support**: {hygiene['does_not_support']}",
            f"3. **Narrowest defensible claim**: {hygiene['narrowest_defensible_claim']}",
            f"4. **Next test needed**: {hygiene['next_test_needed']}",
            "",
        ]
        return "\n".join(lines)

    def persist_run(
        self,
        task_key: str,
        verdict: str,
        cases_evaluated: int,
        cases_passed: int,
        mutations_killed: int,
        mutations_total: int,
        cost_usd: Any,
        dda_events: Sequence[Mapping[str, Any]],
        evidence_summary: Mapping[str, Any],
        allow_overwrite: bool = False,
    ) -> Path:
        """Persist the four-file bundle to both run stores; return the _woland run folder.

        ``allow_overwrite`` is accepted for compatibility and deletes nothing: an
        existing destination always raises RunFolderExistsError. A
        REFERENCE_SELF_CONSISTENT label that the counts do not support is refused.
        """
        del allow_overwrite
        if verdict not in TERMINAL_VERDICTS:
            raise ValueError(f"unknown label {verdict!r}")
        for name, value in (
            ("cases_evaluated", cases_evaluated),
            ("cases_passed", cases_passed),
            ("mutations_killed", mutations_killed),
            ("mutations_total", mutations_total),
        ):
            require_count(name, value)
        cost = exact_usd("cost_usd", cost_usd)
        counts_consistent = (
            cases_evaluated > 0
            and cases_passed == cases_evaluated
            and mutations_total > 0
            and mutations_killed == mutations_total
        )
        if verdict == TERMINAL_REFERENCE_SELF_CONSISTENT and not counts_consistent:
            raise ValueError(
                f"{LABEL_INCONSISTENT_WITH_COUNTS}: {verdict} is not supported by the counts"
            )

        safe_key = sanitize_run_key(task_key)
        target_dir = self.repo_root / "_ic/darpa/woland" / "runs" / safe_key
        symgam_dir = self.repo_root / "_ic/darpa/symbol_game" / "runs" / safe_key
        if target_dir.exists():
            raise RunFolderExistsError(f"Directory {target_dir} already exists.")
        if symgam_dir.exists():
            raise RunFolderExistsError(f"Directory {symgam_dir} already exists.")

        novella_bytes = self.emit_novella(
            task_key=safe_key,
            verdict=verdict,
            cases_evaluated=cases_evaluated,
            cases_passed=cases_passed,
            mutations_killed=mutations_killed,
            mutations_total=mutations_total,
            cost_usd=cost,
            evidence_summary=evidence_summary,
        ).encode("utf-8")
        novella_sha = sha256_digest_bytes(novella_bytes)

        dda_bytes, dda_head_sha = chain_dda_events(dda_events)
        dda_sha = sha256_digest_bytes(dda_bytes)

        summary_data = {
            "authority_effect": "None",
            "billed_cost_usd": str(cost),
            "cases_evaluated": cases_evaluated,
            "cases_passed": cases_passed,
            "challenge_id": self.challenge_id,
            "claim_hygiene": derived_claim_hygiene(
                verdict, cases_evaluated, cases_passed, mutations_killed, mutations_total
            ),
            "domain": "c_quantum",
            "evidence_summary": dict(evidence_summary),
            "gate_scope": GATE_SCOPE,
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "task_key": safe_key,
            "tier": TIER,
            "timestamp_utc": utc_timestamp_now(),
            "verdict": verdict,
        }
        summary_bytes = canonical_json_bytes(summary_data)
        summary_sha = sha256_digest_bytes(summary_bytes)

        receipt_data = {
            "authority_effect": "None",
            "challenge_id": self.challenge_id,
            "dda_actions_sha256": dda_sha,
            "dda_head_sha256": dda_head_sha,
            "gate_scope": GATE_SCOPE,
            "novella_sha256": novella_sha,
            "receipt_id": f"rcpt_{safe_key}",
            "summary_sha256": summary_sha,
            "task_key": safe_key,
            "timestamp_utc": utc_timestamp_now(),
            "verdict": verdict,
        }
        receipt_bytes = canonical_json_bytes(receipt_data)

        files = {
            "novella.md": novella_bytes,
            "dda_actions.jsonl": dda_bytes,
            "summary.json": summary_bytes,
            "receipt.json": receipt_bytes,
        }
        write_bundle(target_dir, files)
        write_bundle(symgam_dir, files)
        return target_dir


__all__ = [
    "CHALLENGE_ID",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "LABEL_INCONSISTENT_WITH_COUNTS",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "WolandRealityGate",
    "canonical_json_bytes",
    "chain_dda_events",
    "compute_file_sha256",
    "decide_label",
    "derived_claim_hygiene",
    "exact_usd",
    "require_count",
    "sanitize_run_key",
    "sha256_digest_bytes",
    "write_bundle",
]
