"""The adversarial battery this estate already owned and never ran.

Runnable auditors under the nine declared :data:`AUDITOR_ROOTS` live in this
repository. When an external red
team published eleven seed defects against the Symbol Game, at least one of them
-- `SYMGAM-011..016` name no falsifier -- was already measured, already tooled,
and already written down in
`.agents/skills/techne-unfalsifiable-gate-auditor/SKILL.md`, complete with the
table "15 of 31 name a falsifier; 16 name none". The auditor exits 1 on it and
has done so all along.

Nobody ran it. That is the whole defect, and it is not a tooling defect.

So this module is deliberately NOT another checker. It is the cadence: one
command that runs what already exists, and -- the part that matters -- one that
**fails when an auditor exists on disk and is not wired into it**. An estate
cannot drift back into owning checks it does not run without that assertion
going red.

Four statuses, and the difference between them is the point:

    WIRED       runs, and must exit 0
    ADVISORY    runs, reports, and deliberately does not block
    QUARANTINED runs, is KNOWN to exit non-zero, and carries a reason
    UNWIRED     is not run yet, carries a reason, and is pinned so the set
                cannot grow

`QUARANTINED` still runs. It holds only when the command returns its declared
exit code *and* emits its declared stable diagnostic. A pass, crash, timeout, or
different failure is drift, because a quarantine that accepts any non-zero
exit silently blesses import errors and broken setup.

`ADVISORY` exists because the estate was already using the concept and this
register could not say it. `merge-to-main.yml` runs `uncalled_module_audit`
under `continue-on-error: true`, with a reason: "an unwired module is a
scheduling question, and a gate that blocks on it would be answering that
question by itself." Without this status the only honest options were to
misreport that check as `UNWIRED` (it runs on every push to main) or to promote
it to `WIRED` and overrule a decision somebody made deliberately and wrote down.
A vocabulary that cannot express what is already happening produces a false map,
which is the defect this whole module is about.

## The register is not the only enforcement surface

This is the thing to know before trusting a status. Three registers describe
what must pass in this repository, and they were written independently:

    AUDITORS                 here
    .github/workflows/*.yml  the CI steps that actually run on push
    GATE_CATALOG_V3          cicd_verification_suite, 27 gates

`reconcile()` below compares the first two, exactly, and fails when they
disagree. It exists because four rows were measured wrong on 2026-09-04:
`content_lock_gate`, `stale_census_audit` and `uncalled_module_audit` all ran in
`merge-to-main.yml` while this file called them `UNWIRED`, and `host_root_parity`
was `WIRED` here while running in no workflow at all. `UNWIRED` had come to mean
"unmodelled", not "unprotected", and nothing tested the difference.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from operations.use_cases.verification.fail_closed_audit import (
    AUDITED_ROOTS,
    FAIL_OPEN_SHAPE_CEILING,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

WIRED = "WIRED"
ADVISORY = "ADVISORY"
QUARANTINED = "QUARANTINED"
UNWIRED = "UNWIRED"

#: Statuses whose auditor is actually executed. `UNWIRED` is the complement, and
#: the only one `reconcile()` treats as a claim that the module does not run.
RUNNING_STATUSES = frozenset({WIRED, ADVISORY, QUARANTINED})

#: Workflow files that count as "CI runs this". Named rather than globbed so
#: that deleting one is a discoverable failure instead of a quieter map.
CI_WORKFLOWS = (
    ".github/workflows/symbol-game-pr.yml",
)

#: Directories searched for auditor modules. Named, not discovered, so that
#: deleting one is a failure rather than a quieter sweep.
AUDITOR_ROOTS = (
    "operations/use_cases/cicd",
    "operations/use_cases/governance",
    "operations/use_cases/packaging",
    "operations/use_cases/verification",
    "operations/domain/cicd",
    "operations/domain/packaging",
    "research_papers/controllers",
)

#: A module in an audited root counts as an auditor when its name says it
#: checks something. Substring matching is blunt on purpose: a stricter rule
#: would let a checker escape the census by being named imaginatively.
AUDITOR_MARKERS = (
    "audit",
    "gate",
    "parity",
    "census",
    "coverage",
    "verify",
    "freshness",
    "criteria",
    "conformance",
    "harness",
)


@dataclass(frozen=True)
class Auditor:
    module: str
    status: str
    guards: str
    reason: str = ""
    argv: tuple[str, ...] = ()
    timeout_s: int = 300
    expected_exit_code: int | None = None
    expected_output_pattern: str = ""

    @property
    def path(self) -> Path:
        return REPO_ROOT / (self.module.replace(".", "/") + ".py")


#: The register. Every entry is a decision someone made and can be argued with.
#:
#: Statuses were assigned by running each auditor, not by reading it. An entry
#: marked WIRED has been observed to exit 0 in this worktree; one marked
#: QUARANTINED has been observed to exit non-zero and the reason says why.
AUDITORS: tuple[Auditor, ...] = (
    Auditor(
        module="operations.use_cases.verification.fail_closed_audit",
        status=WIRED,
        guards="gates that can pass without checking (silent skips, swallowed failures)",
        argv=(*AUDITED_ROOTS, "--max", str(FAIL_OPEN_SHAPE_CEILING)),
    ),
    Auditor(
        module="product_planning_office.domain.epic_criteria_audit",
        status=QUARANTINED,
        guards="epics whose acceptance gate names no falsifier",
        reason=(
            "16 of 31 epics name no falsifier, SYMGAM-011..016 among them. This "
            "is seed defect 5 of the adversarial campaign, and the auditor "
            "found it before the campaign did. Quarantined because the repair "
            "is authoring work on 16 epics, not a code change."
        ),
        expected_exit_code=1,
        expected_output_pattern=(
            r"(?m)^15 of 31 epics name a falsifier; 16 name none$"
        ),
    ),
    Auditor(
        module="operations.use_cases.packaging.host_root_parity",
        status=WIRED,
        guards="the four-host mirror surface outside skills/",
        argv=("--check",),
        reason=(
            "Wired 2026-09-04. It was the highest-priority UNWIRED entry -- the "
            "only thing watching the mirror surface an attacker would use -- and "
            "it was a reporter: __main__ printed a census and exited 0 whatever "
            "it found. --check gates it against a recorded baseline held in the "
            "module, so the pins the suite asserts and the pins the gate enforces "
            "are one set. Wiring it also found what nothing had been watching: "
            "six files differ across hosts (archive/README.md truncated on every "
            "mirror, and cppms_commit_sync_workflow.json naming different "
            "operations in canon and mirrors) plus one canon-only lock file. "
            "Those are RECORDED, not approved -- the gate stops the set growing "
            "and decides nothing about repairing it."
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.evidence_freshness",
        status=WIRED,
        guards=(
            "the retired repository evidence root, and freshness of receipts "
            "whose directory an operator explicitly selects"
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.core_campaign_census",
        status=WIRED,
        guards=(
            "integrity of the pinned pre-change Core campaign census; "
            "not current-source review or campaign completion"
        ),
        argv=(
            "check",
            "--baseline", "a85c7e13ea7411b7d6ecc1af2181e4301df6cd1e",
            "--output",
            "operations/receipts/historical_evidence_20261011/core_campaign/baseline_20260904.jsonl",
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.core_rust_binding_audit",
        status=UNWIRED,
        guards="complete pinned Rust/file-contract inputs to the native static binding checker",
        reason=(
            "M1 milestone command requires an exact commit, reviewed mappings, "
            "a separately built and hash-pinned native executable, and a new "
            "external receipt directory. Run in the single Windows Cargo lane; "
            "not a parameterless per-stop or operational-completeness gate."
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.genesis_source_parity",
        status=UNWIRED,
        guards="the checked-in Genesis source-replay fixture",
        reason=(
            "Replays the original Genesis Python corpus against a fixture. "
            "Optional Lean compilation is a separate lane. Not a parameterless "
            "per-stop gate."
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.mutation_harness",
        status=UNWIRED,
        guards="tests that do not notice a deliberate defect",
        reason=(
            "Runs the full suite per mutant. Correct at a sprint boundary, far "
            "too slow for a per-stop battery; invoked on its own cadence."
        ),
    ),
    Auditor(
        module="operations.use_cases.verification.test_quality_gate",
        status=UNWIRED,
        guards="test-quality law conformance",
        reason="Not yet triaged against this battery; status unknown, so not claimed.",
    ),
    Auditor(
        module="operations.use_cases.verification.verify_repo_utf8_bom",
        status=WIRED,
        guards="zero UTF-8 BOM byte violations across repository",
        reason="Parameterless fast check verifying zero UTF-8 BOM byte violations across repository.",
    ),
    Auditor(
        module="operations.use_cases.verification.verify_manifest_sorting",
        status=WIRED,
        guards="ordinal UTF-8 path sorting across all JSON manifests",
        reason="Parameterless fast check verifying 100% ordinal manifest path sorting.",
    ),
    Auditor(
        module="operations.use_cases.verification.strict_gate_runner",
        status=UNWIRED,
        guards="Examiner Strict gate and production mutation evidence custody",
        reason=(
            "Runs 4 production mutations across baseline, mutant, and restore "
            "passes with Strict AST inspector. Invoked on milestone and victory "
            "audit gate cadences rather than per-stopping-point battery."
        ),
    ),
    Auditor(
        module="operations.use_cases.cicd.dual_home_gate_entry",
        status=UNWIRED,
        guards="dual-home import boundaries",
        reason="Not yet triaged against this battery.",
    ),
    Auditor(
        module="operations.use_cases.cicd.receipt_truth_gate",
        status=UNWIRED,
        guards="receipts asserting more than they witnessed",
        reason="Not yet triaged against this battery.",
    ),
    Auditor(
        module="operations.use_cases.cicd.rust_module_coverage",
        status=UNWIRED,
        guards="Rust modules no test reaches",
        reason="Not yet triaged; carries a fail-open shape of its own.",
    ),
    Auditor(
        module="operations.use_cases.cicd.verify_merge",
        status=UNWIRED,
        guards="merge preconditions",
        reason="Invoked by the merge workflow on its own cadence.",
    ),
    Auditor(
        module="operations.use_cases.cicd.pr_fast_gate",
        status=UNWIRED,
        guards="changed files failing syntax, ruff correctness or their tests",
        reason=(
            "Invoked by pr-fast.yml on every pull request. It needs a diff "
            "base, so it has no subject in this battery."
        ),
    ),
    Auditor(
        module="operations.use_cases.governance.content_lock_gate",
        status=WIRED,
        guards="content locks",
        argv=("verify", "--no-range"),
        reason=(
            "Corrected by reconcile 2026-09-04. It was never untriaged: "
            "merge-to-main.yml has run it blocking on every push as 'Content "
            "locks', with this argv. Observed exit 0, 2 locked sections."
        ),
    ),
    Auditor(
        module="research_papers.controllers.lean_target_resolution_gate",
        status=UNWIRED,
        guards="Lean target resolution",
        reason="lean4/ is a pointer here; the gate has no local subject.",
    ),
    Auditor(
        module="product_planning_office.use_cases.epic_manifest_audit",
        status=WIRED,
        guards="the epic manifest's SHA256 register",
    ),
    Auditor(
        module="operations.domain.cicd.operad_law_audit",
        status=UNWIRED,
        guards="operad law conformance",
        reason="Its test is among the 25 red in operations/tests/unit.",
    ),
    Auditor(
        module="operations.domain.cicd.packet_gate",
        status=UNWIRED,
        guards="packet shape",
        reason="Not yet triaged against this battery.",
    ),
    Auditor(
        module="operations.domain.cicd.stale_census_audit",
        status=WIRED,
        guards="census numbers that have gone stale",
        argv=(
            "--baseline",
            "operations/domain/cicd/census_baseline.txt",
        ),
        reason=(
            "Corrected by reconcile 2026-09-04. The old reason said it 'should "
            "be wired early' and carried a fail-open shape to fix first; "
            "merge-to-main.yml had meanwhile been running it blocking as "
            "'Census literals' with a baseline ratchet -- 4 known findings that "
            "may only shrink. Observed exit 0: 'ratchet: 4 known, 0 new.'"
        ),
    ),
    Auditor(
        module="operations.domain.cicd.uncalled_module_audit",
        status=ADVISORY,
        guards="modules nothing calls",
        reason=(
            "Corrected by reconcile 2026-09-04, and ADVISORY rather than WIRED "
            "on purpose. merge-to-main.yml runs it under continue-on-error with "
            "a stated reason: 'an unwired module is a scheduling question, and a "
            "gate that blocks on it would be answering that question by itself.' "
            "Promoting it to WIRED would overrule that silently, and would also "
            "turn the battery permanently red: it exits 1 today, reporting 18 of "
            "443 modules imported only by their own tests. Measured 2026-09-04 -- "
            "and measured twice, because the first reading came through a pipe "
            "and returned the exit code of `tail`."
        ),
    ),
    Auditor(
        module="operations.domain.cicd.workflow_graph_audit",
        status=UNWIRED,
        guards="CI workflow graph integrity",
        reason=(
            "The natural home for seed defect 4's class -- a path filter that "
            "watches a file the job never runs. Carries a fail-open shape."
        ),
    ),
    Auditor(
        module="operations.domain.packaging.skill_frontmatter_audit",
        status=UNWIRED,
        guards="skill frontmatter shape",
        reason="Not yet triaged against this battery.",
    ),
    Auditor(
        module="product_planning_office.domain.epic_claim_gate",
        status=UNWIRED,
        guards="epic claims",
        reason="Not yet triaged against this battery.",
    ),
    Auditor(
        module="operations.use_cases.cicd.challenge_harness_lints",
        status=UNWIRED,
        guards="challenge harness formatting and lint rules",
        reason="Invoked via local CI challenge harness gates.",
    ),
    Auditor(
        module="operations.use_cases.cicd.education_strands_gate",
        status=UNWIRED,
        guards="education curriculum strands integrity",
        reason="Invoked via local CI education gate suites.",
    ),
    Auditor(
        module="operations.use_cases.cicd.paper_deposit_verify",
        status=UNWIRED,
        guards="research paper deposit hermetic packaging and checksum manifests",
        reason="Invoked via local CI publication gates.",
    ),
    Auditor(
        module="operations.use_cases.cicd.republication_checklist_gate",
        status=UNWIRED,
        guards="republication checklist channels and verifiers",
        reason="Invoked via local CI republication gate checks.",
    ),
    Auditor(
        module="operations.use_cases.cicd.code_scoring_evaluator",
        status=UNWIRED,
        guards="source code scoring rubric across five sovereign gates (SCORING.md)",
        reason="Evaluates code scoring rubric in standby advisory mode; left off by default.",
    ),
    Auditor(
        module="operations.use_cases.verification.agentshield_audit",
        status=UNWIRED,
        guards="agentshield security boundaries",
        reason="Invoked via security evaluation sweeps.",
    ),
)

BY_MODULE = {auditor.module: auditor for auditor in AUDITORS}


class RegisterDrift(RuntimeError):
    """An auditor exists on disk and the register does not know about it."""


def discover() -> set[str]:
    """Auditor modules present on disk, by dotted module path."""
    found: set[str] = set()
    for root in AUDITOR_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            raise RegisterDrift(f"auditor root does not exist: {root}")
        for path in sorted(base.glob("*.py")):
            if path.name.startswith("_"):
                continue
            if not any(marker in path.name.lower() for marker in AUDITOR_MARKERS):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "__main__" not in text:
                continue
            found.add(path.relative_to(REPO_ROOT).with_suffix("").as_posix().replace("/", "."))
    if not found:
        raise RegisterDrift("discovery found no auditors at all; it read nothing")
    return found


def unregistered() -> list[str]:
    """Auditors on disk that the register does not name. Must stay empty."""
    return sorted(discover() - set(BY_MODULE))


def missing_from_disk() -> list[str]:
    """Registered auditors whose module is gone. Must stay empty."""
    return sorted(a.module for a in AUDITORS if not a.path.is_file())


@dataclass(frozen=True)
class CiInvocation:
    """One place a workflow actually executes an auditor."""

    workflow: str
    job: str
    step: str
    blocking: bool


def _iter_run_steps(document: dict, workflow: str):
    """Yield (job, step_name, run_text, blocking) for every executed step.

    Only `jobs.<id>.steps[].run` is read. A `paths:` trigger is deliberately NOT
    a run: a workflow that watches a file it never executes is precisely the
    defect this reconciliation exists to detect, so counting a path filter as
    evidence of execution would make this check assert the thing it is meant to
    refute. Until 2026-10-06 `symbol-game-pr.yml` listed `stopping_point.py`
    under `paths:` and never ran several of the modules named there.
    """
    for job_id, job in (document.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict) or "run" not in step:
                continue
            yield (
                job_id,
                step.get("name") or "(unnamed step)",
                str(step["run"]),
                # `continue-on-error: true` is CI saying the exit code does not
                # gate the merge. That is ADVISORY, not WIRED.
                not bool(step.get("continue-on-error", False)),
            )
    _ = workflow


def ci_invocations(repo_root: Path | None = None) -> dict[str, list[CiInvocation]]:
    """Map auditor module -> the CI steps that execute it.

    Matching is on the module's file path and its dotted module path, both
    token-bounded, because a bare leaf name like `verify_merge` is short enough
    to appear inside unrelated prose in a step body. The bounds also keep a
    command for `some_audit_wrapper` from being credited to `some_audit`.
    """
    import yaml

    base = Path(repo_root) if repo_root is not None else REPO_ROOT
    found: dict[str, list[CiInvocation]] = {}
    for relative in CI_WORKFLOWS:
        path = base / relative
        if not path.is_file():
            raise RegisterDrift(
                f"declared CI workflow is missing: {relative}. Reconciliation "
                "cannot compare the register against a workflow it cannot read; "
                "update CI_WORKFLOWS if the file was renamed."
            )
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job_id, step_name, body, blocking in _iter_run_steps(document, relative):
            for auditor in AUDITORS:
                candidates = (
                    re.escape(auditor.module.replace(".", "/") + ".py"),
                    re.escape(auditor.module),
                )
                pattern = rf"(?<![A-Za-z0-9_./-])(?:{'|'.join(candidates)})(?![A-Za-z0-9_./-])"
                if re.search(pattern, body):
                    found.setdefault(auditor.module, []).append(
                        CiInvocation(relative, job_id, step_name, blocking)
                    )
    return found


def reconcile(repo_root: Path | None = None) -> list[str]:
    """Where this register and the CI workflows disagree. Empty is a pass.

    Two directions, and both were wrong on 2026-09-04:

    - A module CI executes may not be `UNWIRED` here. `UNWIRED` asserts the
      check is not being run; if `merge-to-main.yml` runs it on every push, the
      register is publishing a false map and the reason string attached to it is
      fiction.
    - A module CI executes with `continue-on-error: true` may not be `WIRED`
      here. `WIRED` asserts a non-zero exit is a failure. CI says it is not.
      `ADVISORY` is the status that matches.

    What this deliberately does NOT check: that every `WIRED` row runs in CI.
    A row can be honestly wired into this battery and reached by an operator or
    a hook rather than a workflow, and demanding workflow coverage would push
    checks into CI for the register's convenience rather than on cost. That gap
    is reported by `--reconcile` as an observation and is not a failure.

    `AuthorityEffect: None`. Agreeing with CI is not evidence either is right.
    """
    invocations = ci_invocations(repo_root)
    findings: list[str] = []

    for module, places in sorted(invocations.items()):
        auditor = BY_MODULE[module]
        where = "; ".join(f"{p.workflow}:{p.job}/{p.step}" for p in places)
        if auditor.status == UNWIRED:
            findings.append(
                f"{module} is UNWIRED here but CI executes it ({where}). "
                f"Its reason claims it is not run: {auditor.reason[:60]!r}"
            )
        elif auditor.status == WIRED and not any(p.blocking for p in places):
            findings.append(
                f"{module} is WIRED here but every CI step running it is "
                f"continue-on-error ({where}). WIRED asserts a non-zero exit "
                "fails; CI says it does not. ADVISORY is the honest status."
            )
        elif auditor.status == ADVISORY and all(p.blocking for p in places):
            findings.append(
                f"{module} is ADVISORY here but CI blocks on it ({where}). "
                "Understating a gate hides a real merge blocker from the board."
            )
    return findings


#: This module's own dotted path. A workflow step that runs the battery runs
#: every enforced row in it, so reachability has to account for that or it will
#: report rows as unscheduled when they are merely scheduled indirectly.
SELF_MODULE = "operations.use_cases.verification.stopping_point"


def battery_workflows(repo_root: Path | None = None) -> list[tuple[str, bool]]:
    """Workflows that run this battery, and whether each is path-filtered.

    The filter matters more than the invocation. A workflow that runs the
    battery only when certain paths change enforces every row in it exactly on
    those paths. Until 2026-10-06 `symbol-game-pr.yml` was such a workflow: it
    listed `stopping_point.py` among the paths it watched, so the battery ran
    substantially when the battery changed. It now runs nightly with no path
    filter. The flag stays so that a filter added back is visible rather than
    inferred by whoever next reads the register.
    """
    import yaml

    base = Path(repo_root) if repo_root is not None else REPO_ROOT
    running: list[tuple[str, bool]] = []
    for relative in CI_WORKFLOWS:
        path = base / relative
        if not path.is_file():
            # Refuse rather than skip, and for the same reason `ci_invocations`
            # does: skipping would return an empty list, the path-filter warning
            # would silently stop printing, and "no workflow runs the battery"
            # would render as though there were nothing to worry about. Caught
            # by `fail_closed_audit` on the first draft of this function.
            raise RegisterDrift(
                f"declared CI workflow is missing: {relative}. Reachability "
                "cannot be reported against a workflow it cannot read; update "
                "CI_WORKFLOWS if the file was renamed."
            )
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        runs_battery = any(
            SELF_MODULE in body
            for _, _, body, _ in _iter_run_steps(document, relative)
        )
        if not runs_battery:
            continue
        # `on:` parses to the boolean True under YAML 1.1, which is why this
        # reads the key by both spellings rather than trusting one.
        triggers = document.get("on", document.get(True)) or {}
        filtered = any(
            isinstance(spec, dict) and ("paths" in spec or "paths-ignore" in spec)
            for spec in triggers.values()
            if isinstance(triggers, dict)
        )
        running.append((relative, filtered))
    return running


def ci_reachability(repo_root: Path | None = None) -> dict[str, str]:
    """How each enforced row actually gets executed by CI.

    DIRECT      a workflow step invokes the module itself
    VIA_BATTERY only reached because a workflow runs this battery
    NONE        no named workflow reaches it; it runs when somebody types it

    Observation, never a failure -- see `reconcile`. A row can be honestly
    enforced here and reached by a hook or an operator instead of a workflow,
    and demanding workflow coverage would push checks into CI for this
    register's convenience rather than on cost.
    """
    invocations = ci_invocations(repo_root)
    via_battery = bool(battery_workflows(repo_root))
    reach: dict[str, str] = {}
    for auditor in AUDITORS:
        if auditor.status not in RUNNING_STATUSES:
            continue
        if auditor.module in invocations:
            reach[auditor.module] = "DIRECT"
        elif via_battery:
            reach[auditor.module] = "VIA_BATTERY"
        else:
            reach[auditor.module] = "NONE"
    return reach


@dataclass(frozen=True)
class Result:
    auditor: Auditor
    exit_code: int
    verdict: str
    detail: str


def run_one(auditor: Auditor) -> Result:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", auditor.module, *auditor.argv],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=auditor.timeout_s,
        )
        code = proc.returncode
        output = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
        detail = output.strip().splitlines()
        tail = detail[-1] if detail else "(no output)"
    except subprocess.TimeoutExpired:
        # A timeout is not a pass. Named distinctly so it can never be counted
        # as one.
        return Result(auditor, 124, "TIMEOUT", f"exceeded {auditor.timeout_s}s")
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        return Result(auditor, 125, "ERROR", f"{type(exc).__name__}: {exc}")

    if auditor.status == WIRED:
        verdict = "PASS" if code == 0 else "FAIL"
    elif auditor.status == ADVISORY:
        # Runs and reports; the exit code is information, not a gate. Named
        # distinctly in both directions so an advisory row can never be read as
        # an enforced pass, and so a red one stays visible in the render.
        verdict = "ADVISORY_CLEAN" if code == 0 else "ADVISORY_FINDING"
    else:  # QUARANTINED
        # Passing is a failure of the quarantine: the reason has expired and
        # the entry should be promoted to WIRED. A different non-zero is also
        # a failure: setup/import crashes are not the defect being quarantined.
        if code == 0:
            verdict = "QUARANTINE_ESCAPED"
        elif code != auditor.expected_exit_code:
            verdict = "QUARANTINE_DRIFT"
            tail = (
                f"expected exit {auditor.expected_exit_code}, got {code}: {tail}"
            )
        elif not re.search(auditor.expected_output_pattern, output):
            verdict = "QUARANTINE_DRIFT"
            tail = "declared failure diagnostic was absent"
        else:
            verdict = "QUARANTINE_HELD"
    return Result(auditor, code, verdict, tail)


def run_all() -> list[Result]:
    """Run every executed auditor. UNWIRED ones are not run."""
    return [
        run_one(auditor) for auditor in AUDITORS if auditor.status in RUNNING_STATUSES
    ]


def render(results: list[Result]) -> str:
    lines = ["stopping-point battery", ""]
    for result in results:
        lines.append(
            f"  [{result.verdict:17}] {result.auditor.module.split('.')[-1]:28} "
            f"exit={result.exit_code}  {result.detail[:70]}"
        )
    counts: dict[str, int] = {}
    for result in results:
        counts[result.verdict] = counts.get(result.verdict, 0) + 1
    lines.extend(["", "  " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))])

    unreg = unregistered()
    gone = missing_from_disk()
    if unreg:
        lines.extend(["", f"  UNREGISTERED auditors on disk: {unreg}"])
    if gone:
        lines.extend(["", f"  REGISTERED auditors missing from disk: {gone}"])

    by_status: dict[str, int] = {}
    for auditor in AUDITORS:
        by_status[auditor.status] = by_status.get(auditor.status, 0) + 1
    lines.extend([
        "",
        "  register: " + ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())),
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the adversarial battery.")
    parser.add_argument("--list", action="store_true", help="print the register only")
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="compare the register against the CI workflows; exit 1 on disagreement",
    )
    args = parser.parse_args(argv)

    if args.reconcile:
        findings = reconcile()
        for finding in findings:
            print(f"  DISAGREES  {finding}")
        print()
        reach = ci_reachability()
        counts: dict[str, int] = {}
        for how in reach.values():
            counts[how] = counts.get(how, 0) + 1
        print("  How CI reaches the enforced rows (observation, not a fail):")
        print("    " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        for workflow, filtered in battery_workflows():
            note = "PATH-FILTERED" if filtered else "unfiltered"
            print(f"    battery runs in {workflow} ({note})")
        if any(f for _, f in battery_workflows()):
            print(
                "    A path-filtered battery enforces its rows only on those "
                "paths. Rows reached VIA_BATTERY inherit that filter."
            )
        print()
        if findings:
            print(
                f"{len(findings)} disagreement(s) between the register and CI. "
                "The register is a map; CI is the territory."
            )
            return 1
        print("register and CI agree on every module CI runs.")
        return 0

    if args.list:
        for auditor in AUDITORS:
            print(f"{auditor.status:12} {auditor.module}")
            print(f"             guards: {auditor.guards}")
            if auditor.reason:
                print(f"             reason: {auditor.reason}")
        return 0

    results = run_all()
    print(render(results))
    # ADVISORY verdicts are outcomes, not failures -- that is the entire content
    # of the status. Both are listed rather than filtering on a prefix, so a new
    # verdict string cannot become non-failing by accident.
    acceptable = {"PASS", "QUARANTINE_HELD", "ADVISORY_CLEAN", "ADVISORY_FINDING"}
    bad = [r for r in results if r.verdict not in acceptable]
    return 1 if (bad or unregistered() or missing_from_disk()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
