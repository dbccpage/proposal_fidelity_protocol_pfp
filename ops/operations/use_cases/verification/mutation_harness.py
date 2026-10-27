"""Replay a mutation catalogue and emit evidence, not a count.

`techne-mutation-evidence-custody` states the law this implements:

    A mutation count is a claim about work nobody can repeat. A mutation table
    is evidence. Quote the table or quote nothing.

The estate's central quality claim -- roughly 200 killed mutants across 39
sprints -- exists only as scalars in markdown, written by the same pipeline that
ran the mutation, with no target, no anchor, no per-mutation failure set and no
residue proof. One sprint's retrospective describes *editing* the harness, so it
existed on disk and was never committed. This is that harness, committed.

Five fields, and a claim missing any of them is a candidate
-----------------------------------------------------------

===========  ==================================================================
``target``   the file, so a reader knows what was weakened
``anchor``   the exact text replaced. An anchor matching zero or many times is
             a **setup failure, never a result** -- reported as ANCHOR, and it
             does not count toward any denominator
``applied``  the replacement, so the mutation reconstructs byte for byte
``failures`` *which* tests failed, by name. A count cannot show whether the
             witness was the one the criterion names
``restore``  proof the tree returned to its prior state, by digest
===========  ==================================================================

Three things this deliberately does
-----------------------------------

**Declares the expectation up front.** A mutant is registered as ``killed`` or
``equivalent`` before it runs. An equivalent mutant is a fact about the code and
must be recorded as equivalent rather than chased or buried; burying it inflates
the denominator. A mutant declared ``killed`` that survives is the interesting
result, and gets its own row rather than a silent absence.

**Records survivors.** "A table that only records the mutations that were easy
to kill is a table about the author's confidence."

**Restores in a ``finally``, then proves it.** A harness that leaves a mutation
on disk after a crash has corrupted the tree it was auditing. The digest
comparison is the proof, and a failed restore is reported as loudly as a
surviving mutant.

Interruption is the normal case, not the exception
--------------------------------------------------

A full replay takes tens of minutes, and three of the first five runs were
killed part-way through. A harness that loses everything to a kill will be run
rarely, and evidence that is expensive to produce stops being produced.

So results are written to the JSON **after every mutant**, and ``--resume``
picks up where a killed run stopped. The resume is guarded by the repository
HEAD: resuming across a commit would blend results from two different states of
the code into one table, which is a subtler version of the very thing this
harness exists to prevent. A changed HEAD refuses rather than merges.

The readable table is generated FROM the accumulated JSON at the end of a run,
so the two artifacts cannot disagree -- they did once, when one was generated
and the other assembled by hand, and the pair said "18 of 18" beside a record of
23 mutants and a survivor. A table covering fewer mutants than the catalogue
declares says so at the top rather than reading as a complete result.

A ``finally`` is not enough, and this was measured
--------------------------------------------------

The first run of this harness was killed mid-flight and **left M12 applied to
`row_rederivation.py`**. `finally` does not run when the process is killed, so
the guarantee it offers covers exceptions and nothing else. A tree silently
carrying a mutation is worse than no harness: every subsequent test run is
green-or-red about code nobody wrote.

Two mechanisms close it, and both are cheap:

* **A pre-flight clean check.** Every target must be clean in git before any
  mutation is applied. A leftover from a killed run therefore blocks the next
  run loudly instead of being mutated on top of. It also makes the restore
  proof mean something: restoring to a dirty tree proves only that the harness
  put back what it found.
* **A journal.** The target and its pre-mutation digest are written to
  ``.mutation-journal.json`` *before* the file is touched and removed only
  after a verified restore. A journal found at startup names the exact file and
  mutant to restore, so recovery does not depend on the operator remembering
  what was running.

AuthorityEffect: None. This runs an experiment and prints what happened. Under
the LLM Boundary Law an agent may generate the candidate and may not certify it;
a green table is not a promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "Mutant",
    "MutationResult",
    "render_table",
    "run_catalogue",
    "run_mutant",
]

#: pytest's `-rf` short summary, one line per failure:
#:     FAILED path/to/test_x.py::TestClass::test_name - AssertionError: ...
_FAILED = re.compile(r"^FAILED\s+(\S+)")

#: Same summary, for a collection or import error. These are NOT kills: a
#: mutant that stops the suite from importing has broken the harness, not
#: demonstrated a test's discrimination.
_ERROR = re.compile(r"^ERROR\s+(\S+)")

#: `cargo test` prints one line per test; a failure reads
#:     test packets::tests::a_round_record_cannot_be_deserialized_at_all ... FAILED
_CARGO_FAILED = re.compile(r"^test\s+(\S+)\s+\.\.\.\s+FAILED")

#: pytest's own end-of-run summary, e.g. "3 failed, 619 passed in 37.28s".
#: Its ABSENCE is the point: a run that produced no summary produced no result,
#: and must not be read as a run that found nothing wrong.
_PYTEST_SUMMARY = re.compile(r"^=*\s*\d+\s+(?:passed|failed|error)|\b\d+\s+(?:passed|failed)\b")

#: A mutation that does not compile has broken the harness, not shown a test
#: discriminating -- the Rust equivalent of a pytest collection error.
#:
#: Matching `^error` is WRONG here and was the first version of this. On a
#: genuine kill `cargo test` prints
#:
#:     error: test failed, to rerun pass `-p core_symbol_game_runtime --lib`
#:
#: so `^error` converted every kill into a setup failure, and all four Rust
#: mutants reported ANCHOR while the tests were killing them correctly. Cargo
#: names a compile failure specifically, and that is the only thing that makes
#: a run void.
_CARGO_DID_NOT_COMPILE = "could not compile"

#: Both runners colour their output when they think a terminal is attached, and
#: a captured pipe is not reliably exempt. The first version of this harness
#: matched `^FAILED` against lines that actually began `\x1b[31mFAILED`, parsed
#: nothing, and reported every mutant as SURVIVED -- the exact opposite of the
#: truth, silently. `--color=no` is passed as well; this is the belt to that
#: pair of braces, because a harness that fails open is worse than none.
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

#: Repository governance caps every pytest process at three test files. The
#: harness still evaluates the complete declared selection; it does so through
#: deterministic small batches and accumulates every named witness.
PYTEST_BATCH_SIZE = 3


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


def _command(
    runner: str,
    selection: tuple[str, ...],
    python: str,
    exclude: tuple[str, ...] = (),
) -> list[str]:
    """The command a runner uses to execute `selection`.

    `exclude` drops paths from the run. It exists for one specific hazard: the
    catalogue's own anchor test asserts that each mutant's anchor matches, and
    while that mutant is APPLIED its anchor is gone. Left in, it fails on every
    single run and witnesses every mutation -- so a genuinely surviving mutant
    would be reported as killed by the harness's own bookkeeping. A harness must
    not be a witness in its own experiment.

    `-j 1` on cargo is mandatory in this workspace and is not a tuning choice:
    LLVM OOMs otherwise. See `.agents/skills/_shared/rust_build_policy.md`.
    """
    if runner == "pytest":
        return [
            python, "-m", "pytest", *selection,
            *[f"--ignore={path}" for path in exclude],
            "-q", "--no-header", "--tb=no", "-rf", "--color=no",
            "-p", "no:cacheprovider",
        ]
    if runner == "cargo":
        # The catalogue owns the whole argument list after `cargo`, because a
        # toolchain prefix (`+stable`) must come first and only the catalogue
        # knows whether this host needs one. `-j 1` is still enforced, as a
        # check rather than as a hardcoded position.
        if "-j" not in selection:
            raise ValueError(
                "a cargo selection must pass `-j 1`; LLVM OOMs on this workspace "
                "otherwise, and that is a build policy, not a tuning choice"
            )
        return ["cargo", *selection]
    raise ValueError(f"unknown runner {runner!r}; expected 'pytest' or 'cargo'")


def _pytest_batches(selection: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Partition an explicit pytest selection into governance-sized batches."""
    return tuple(
        selection[index : index + PYTEST_BATCH_SIZE]
        for index in range(0, len(selection), PYTEST_BATCH_SIZE)
    )


def _parse(runner: str, output: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Failure names and harness-level errors, by runner."""
    lines = _plain(output).splitlines()
    if runner == "pytest":
        failures = tuple(
            m.group(1) for line in lines if (m := _FAILED.match(line))
        )
        errors = tuple(m.group(1) for line in lines if (m := _ERROR.match(line)))
        if not errors and not any(_PYTEST_SUMMARY.search(line) for line in lines):
            # No summary means the suite did not finish -- it crashed, was
            # killed, or never collected. Zero parsed failures is then a fact
            # about the OUTPUT, not about the code, and calling it a survivor
            # is the same absence-of-evidence error as the ANSI bug and the
            # unverified write before it. The cargo branch below has always
            # made this check; pytest never did, and a long sequence produced
            # two false survivors at roughly the same position because of it.
            #
            # A named FAILED line is a different fact. pytest --no-header on
            # this host prints the progress bar and the -rf names and omits
            # the "N failed, M passed" sentence. Those names still discriminate.
            # Treating them as a setup failure hid eleven real kills.
            if failures:
                return failures, ()
            return failures, ("pytest produced no summary; the suite did not finish",)
        return failures, errors
    failures = tuple(
        dict.fromkeys(m.group(1) for line in lines if (m := _CARGO_FAILED.match(line)))
    )
    if _CARGO_DID_NOT_COMPILE in "\n".join(lines):
        return failures, (
            next(
                (line.strip()[:160] for line in lines if _CARGO_DID_NOT_COMPILE in line),
                "cargo could not compile the mutated crate",
            ),
        )
    if not any(line.startswith("test result:") for line in lines):
        # No compile error and no results either: cargo failed for some third
        # reason -- a missing toolchain, a lock, a killed build. Reporting that
        # as "survived" would credit an empty run as a passing one.
        return failures, ("cargo produced no test results at all",)
    return failures, ()


@dataclass(frozen=True, slots=True)
class Mutant:
    """One weakening, declared before it is run."""

    #: Stable identifier, quoted in commit messages. Never reused.
    mutant_id: str
    #: The DECISION this weakens, in words. Not "changed <= to ==" -- that is
    #: the `applied` field. This says what would be true of the system if the
    #: mutation survived, which is what a reader needs to judge the result.
    intent: str
    #: Repo-relative path.
    target: str
    #: Exact text to replace. Must occur EXACTLY once.
    anchor: str
    #: Replacement text.
    applied: str
    #: What this mutant is expected to do. `equivalent` means the mutation
    #: provably changes no observable behaviour, and surviving is the correct
    #: outcome; it is recorded rather than chased.
    expectation: str = "killed"
    #: Test selection passed to the runner. Empty means the catalogue default.
    tests: tuple[str, ...] = field(default_factory=tuple)
    #: `pytest` or `cargo`. Empty means the catalogue default. Both live in one
    #: catalogue on purpose: a defect that spans the FFI seam should be
    #: mutated on both sides from one record, not two that can drift apart.
    runner: str = ""
    #: Working directory for the runner, relative to the repo root. The Rust
    #: workspace root is not the repo root, and cargo must be invoked from it.
    cwd: str = ""


@dataclass(frozen=True, slots=True)
class MutationResult:
    """What happened, including the parts nobody wants in a summary."""

    mutant: Mutant
    #: killed | survived | equivalent | ANCHOR | RESTORE
    status: str
    failures: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    tests_run: tuple[str, ...] = field(default_factory=tuple)
    anchor_count: int = 1
    restored: bool = True
    detail: str = ""

    @property
    def counts_toward_denominator(self) -> bool:
        """A setup failure is not a result.

        An anchor that matched zero or many times never ran an experiment, and
        a failed restore invalidates whatever it did run. Neither is a mutant
        the suite survived or killed, so neither belongs in `N of M`.
        """
        return self.status in {"killed", "survived", "equivalent"}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


JOURNAL_NAME = ".mutation-journal.json"


def _journal_path(root: Path) -> Path:
    return root / JOURNAL_NAME


def check_no_orphaned_mutation(root: Path) -> str | None:
    """Describe an interrupted run, or `None` if the tree is clean.

    Called before anything is mutated. A journal on disk means a previous run
    died between writing a mutation and restoring it, and the tree is carrying
    code nobody wrote.
    """
    journal = _journal_path(root)
    if not journal.is_file():
        return None
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return f"{JOURNAL_NAME} exists and is unreadable ({error}); restore by hand"
    return (
        f"an interrupted run left {record.get('mutant_id')} applied to "
        f"{record.get('target')}. Restore it (`git checkout -- "
        f"{record.get('target')}`), confirm the file digests "
        f"{record.get('digest_before')}, then delete {JOURNAL_NAME}."
    )


def _dirty_targets(root: Path, mutants: list[Mutant]) -> list[str]:
    """Targets git reports as modified.

    Refusing to mutate a dirty file is not fastidiousness. Restoring to a dirty
    tree proves only that the harness put back what it found, which is not the
    claim the restore field makes.
    """
    targets = sorted({mutant.target for mutant in mutants})
    try:
        # `git diff` alone reports only UNSTAGED changes, so a target that was
        # edited and `git add`ed read as clean and the harness mutated on top
        # of uncommitted work while recording tree_dirty: false. Diffing
        # against HEAD sees staged and unstaged alike.
        completed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", *targets],
            cwd=root, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError) as error:
        # Fail CLOSED. Returning "nothing is dirty" because git could not be
        # consulted is the same shape as reporting "no failures" because the
        # output could not be parsed -- an absence of evidence read as evidence
        # of absence, which is the one direction this harness must never move.
        return [f"(git could not be consulted: {error})"]
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _dirty_tree(root: Path) -> list[str]:
    """Every tracked or untracked path not described by ``HEAD``.

    Target cleanliness protects restoration. Whole-tree cleanliness protects
    attribution: the harness, catalogue, and witness tests are part of the
    experiment too, and an evidence row bound to ``HEAD`` must not have used
    uncommitted versions of any of them.
    """
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as error:
        return [f"(git could not be consulted: {error})"]
    return [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]


def _pytest_directory_refusal(
    mutant: Mutant,
    runner: str,
    selection: tuple[str, ...],
    workdir: Path,
) -> MutationResult | None:
    if runner != "pytest":
        return None
    directories = [
        item
        for item in selection
        if not item.startswith("-")
        and (workdir / item.split("::", 1)[0]).is_dir()
    ]
    if not directories:
        return None
    return MutationResult(
        mutant,
        "ANCHOR",
        tests_run=selection,
        detail=(
            "pytest selections must name explicit files or test nodes; "
            "whole-directory execution is forbidden by repository "
            f"governance ({directories})"
        ),
    )


def _execute_mutant_batches(
    runner: str,
    batches: tuple,
    python: str,
    exclude: tuple[str, ...],
    workdir: Path,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    parsed_failures: list[str] = []
    parsed_errors: list[str] = []
    for batch in batches:
        completed = subprocess.run(
            _command(
                runner,
                batch,
                python,
                exclude if runner == "pytest" else (),
            ),
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        batch_failures, batch_errors = _parse(
            runner, completed.stdout + completed.stderr
        )
        parsed_failures.extend(batch_failures)
        parsed_errors.extend(batch_errors)
        if batch_errors:
            # A setup failure voids the experiment. Later batches cannot
            # turn it into a result, so do not spend more work pretending.
            break
    return tuple(dict.fromkeys(parsed_failures)), tuple(dict.fromkeys(parsed_errors))


def _apply_mutant_and_run(
    mutant: Mutant,
    *,
    target: Path,
    original: bytes,
    before: str,
    source: str,
    journal: Path,
    selection: tuple[str, ...],
    runner: str,
    workdir: Path,
    exclude: tuple[str, ...],
    python: str,
) -> MutationResult | tuple[tuple[str, ...], tuple[str, ...]]:
    failures: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    try:
        # Written BEFORE the file is touched. If this process dies between the
        # two writes, the journal is what tells the next run what to undo.
        journal.write_text(
            json.dumps(
                {
                    "mutant_id": mutant.mutant_id,
                    "target": mutant.target,
                    "digest_before": before,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        mutated = source.replace(mutant.anchor, mutant.applied)
        target.write_bytes(mutated.encode("utf-8"))

        # Read it back before trusting the run. A mutation that is not on disk
        # when the tests execute produces a SURVIVED that means nothing, and a
        # false survivor is worse than a false kill: it sends a reader chasing
        # a gap that does not exist and quietly discredits the whole table.
        #
        # This guard exists because one run reported M19 SURVIVED and no
        # re-run reproduced it -- alone, immediately after M18, or in sequence.
        # The cause was never identified (Windows write visibility is the
        # suspicion, not a finding). An undiagnosed transient cannot be fixed,
        # but it can be made to announce itself instead of masquerading as a
        # result.
        readback = target.read_text(encoding="utf-8")
        if readback != mutated:
            return MutationResult(
                mutant,
                "ANCHOR",
                tests_run=selection,
                detail=(
                    "the mutation was not on disk after being written; no "
                    "experiment ran, and this is a setup failure rather than a "
                    "survivor"
                ),
            )
        batches = _pytest_batches(selection) if runner == "pytest" else (selection,)
        failures, errors = _execute_mutant_batches(
            runner, batches, python, exclude, workdir
        )
    finally:
        # In a `finally` because a harness that leaves a mutation on disk after
        # an exception has corrupted the very tree it was auditing. This does
        # NOT cover being killed -- see the journal above, which does.
        #
        # The journal is cleared HERE, not after the block. It used to sit
        # below, which the early return on a failed read-back skipped: the file
        # was restored correctly and the journal survived, so the NEXT run
        # refused with a false statement -- "an interrupted run left M19
        # applied" about a file byte-identical to HEAD. Any exception from the
        # runner did the same. Every exit path now clears it, and only after
        # the restore is confirmed by digest.
        target.write_bytes(original)
        if _digest(target) == before:
            journal.unlink(missing_ok=True)
    return failures, errors


def _mutation_outcome(
    mutant: Mutant,
    failures: tuple[str, ...],
    errors: tuple[str, ...],
    selection: tuple[str, ...],
    restored: bool,
) -> MutationResult:
    if not restored:
        return MutationResult(
            mutant, "RESTORE", failures, errors, selection,
            restored=False,
            detail="the file did not return to its prior bytes; treat this run as void",
        )
    if errors:
        # A mutant that breaks collection, or does not compile, has broken the
        # harness rather than shown a test discriminating. Counting it as a kill
        # would be the laundering this estate keeps finding.
        detail = (
            "the mutation broke the build or test collection; no discrimination "
            f"was shown ({errors[0]})"
        )
        return MutationResult(
            mutant, "ANCHOR", failures, errors, selection, restored=True, detail=detail
        )
    detail = ""
    if failures:
        status = "killed"
        if mutant.expectation == "equivalent":
            detail = (
                "declared EQUIVALENT but tests failed -- either the mutation is "
                "not equivalent, or a test asserts an implementation detail"
            )
    else:
        status = "equivalent" if mutant.expectation == "equivalent" else "survived"
        if status == "survived":
            detail = "nothing in the selection distinguishes this decision"
    return MutationResult(mutant, status, failures, errors, selection, detail=detail)


def run_mutant(
    mutant: Mutant,
    *,
    root: Path,
    default_tests: tuple[str, ...],
    default_runner: str = "pytest",
    exclude: tuple[str, ...] = (),
    python: str = sys.executable,
) -> MutationResult:
    """Apply one mutation, run the tests, restore, and prove the restore."""
    target = root / mutant.target
    if not target.is_file():
        return MutationResult(
            mutant, "ANCHOR", anchor_count=0, detail=f"{mutant.target} is not a file"
        )

    original = target.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    source = original.decode("utf-8")
    journal = _journal_path(root)

    occurrences = source.count(mutant.anchor)
    if occurrences != 1:
        # Reported, and deliberately NOT counted. An anchor that no longer
        # matches usually means the code moved on and the catalogue did not --
        # which is exactly the drift this harness exists to surface, and is a
        # different finding from a surviving mutant.
        return MutationResult(
            mutant,
            "ANCHOR",
            anchor_count=occurrences,
            detail=(
                f"anchor matched {occurrences} times; it must match exactly once, "
                "or the mutation is not the one the catalogue describes"
            ),
        )

    selection = mutant.tests or default_tests
    runner = mutant.runner or default_runner
    workdir = root / mutant.cwd if mutant.cwd else root
    directory_refusal = _pytest_directory_refusal(mutant, runner, selection, workdir)
    if directory_refusal is not None:
        return directory_refusal

    outcome = _apply_mutant_and_run(
        mutant,
        target=target,
        original=original,
        before=before,
        source=source,
        journal=journal,
        selection=selection,
        runner=runner,
        workdir=workdir,
        exclude=exclude,
        python=python,
    )
    if isinstance(outcome, MutationResult):
        return outcome
    failures, errors = outcome
    return _mutation_outcome(
        mutant, failures, errors, selection, _digest(target) == before
    )


def run_catalogue(
    mutants: list[Mutant],
    *,
    root: Path,
    default_tests: tuple[str, ...],
    default_runner: str = "pytest",
    exclude: tuple[str, ...] = (),
    only: str | None = None,
) -> list[MutationResult]:
    results = []
    for mutant in mutants:
        if only and mutant.mutant_id != only:
            continue
        result = run_mutant(
            mutant,
            root=root,
            default_tests=default_tests,
            default_runner=default_runner,
            exclude=exclude,
        )
        print(f"  [{result.status.upper():9}] {result.mutant.mutant_id}  {result.mutant.intent}")
        results.append(result)
    return results


def _render_records(records: list[dict], head_sha: str) -> str:
    """The same table, rendered from persisted records rather than live results.

    Exists so a resumed run can print every mutant recorded at this commit, not
    only the ones this invocation happened to execute.
    """
    lines: list[str] = []
    if head_sha:
        lines.append(f"Mutation evidence, replayed at {head_sha}.")
        lines.append("")
    counted = [r for r in records if r["status"] in {"killed", "survived", "equivalent"}]
    for record in sorted(records, key=lambda r: r["mutant_id"]):
        lines.append(f"{record['mutant_id']}  {record['target']}")
        lines.append(f"    intent   {record['intent']}")
        lines.append(f"    anchor   {record['anchor'].strip()[:100]!r}")
        lines.append(f"    applied  {record['applied'].strip()[:100]!r}")
        lines.append(f"    status   {record['status'].upper()}")
        if record["detail"]:
            lines.append(f"    note     {record['detail']}")
        if record["failures"]:
            lines.append(f"    failures {len(record['failures'])} test(s):")
            for name in record["failures"]:
                lines.append(f"               {name}")
        else:
            lines.append("    failures none")
        lines.append(
            "    restore  "
            + ("byte-identical, verified by digest" if record["restored"] else "FAILED")
        )
        lines.append("")

    killed = [r for r in counted if r["status"] == "killed"]
    survived = [r for r in counted if r["status"] == "survived"]
    equivalent = [r for r in counted if r["status"] == "equivalent"]
    setup = [r for r in records if r not in counted]
    lines.append(f"{len(killed)} killed of {len(counted)} counted.")
    if equivalent:
        lines.append(
            f"{len(equivalent)} equivalent (recorded, not chased): "
            + ", ".join(r["mutant_id"] for r in equivalent)
        )
    if survived:
        lines.append(
            f"{len(survived)} SURVIVED: " + ", ".join(r["mutant_id"] for r in survived)
        )
    if setup:
        lines.append(
            f"{len(setup)} setup failure(s), excluded from the denominator: "
            + ", ".join(f"{r['mutant_id']} ({r['status']})" for r in setup)
        )
    return "\n".join(lines)


def render_table(results: list[MutationResult], *, head_sha: str = "") -> str:
    """The five-field table, in the form the custody skill's example uses."""
    lines: list[str] = []
    if head_sha:
        lines.append(f"Mutation evidence, replayed at {head_sha}.")
        lines.append("")
    for result in results:
        mutant = result.mutant
        lines.append(f"{mutant.mutant_id}  {mutant.target}")
        lines.append(f"    intent   {mutant.intent}")
        lines.append(f"    anchor   {mutant.anchor.strip()[:100]!r}")
        lines.append(f"    applied  {mutant.applied.strip()[:100]!r}")
        lines.append(f"    status   {result.status.upper()}")
        if result.detail:
            lines.append(f"    note     {result.detail}")
        if result.failures:
            lines.append(f"    failures {len(result.failures)} test(s):")
            for name in result.failures:
                lines.append(f"               {name}")
        elif result.counts_toward_denominator:
            lines.append("    failures none")
        lines.append(
            "    restore  "
            + ("byte-identical, verified by digest" if result.restored else "FAILED")
        )
        lines.append("")

    counted = [r for r in results if r.counts_toward_denominator]
    killed = [r for r in counted if r.status == "killed"]
    survived = [r for r in counted if r.status == "survived"]
    equivalent = [r for r in counted if r.status == "equivalent"]
    setup = [r for r in results if not r.counts_toward_denominator]

    lines.append(f"{len(killed)} killed of {len(counted)} counted.")
    if equivalent:
        lines.append(
            f"{len(equivalent)} equivalent (recorded, not chased): "
            + ", ".join(r.mutant.mutant_id for r in equivalent)
        )
    if survived:
        lines.append(
            f"{len(survived)} SURVIVED: "
            + ", ".join(r.mutant.mutant_id for r in survived)
        )
    if setup:
        lines.append(
            f"{len(setup)} setup failure(s), excluded from the denominator: "
            + ", ".join(f"{r.mutant.mutant_id} ({r.status})" for r in setup)
        )
    return "\n".join(lines)


MARKDOWN_PREAMBLE = """# Mutation evidence

**AuthorityEffect:** `None`. This records an experiment. A green table is not a
promotion, and `LocalGreen` is not `GlobalGreen`.

Generated by
`python -m operations.use_cases.verification.mutation_harness`
replaying `{catalogue}`. Do not edit: regenerate it. This file and its `.json`
sibling are emitted by the SAME run, because the first time they were not, one
said 18 of 18 while the other recorded 23 mutants and a survivor.

Every mutant carries the five fields `techne-mutation-evidence-custody`
requires: target, anchor, applied, the failing tests **by name**, and a restore
verified by digest.

An `EQUIVALENT` row is a mutation that provably changes no observable
behaviour. It is recorded rather than chased, because burying it would inflate
the denominator and writing a test to kill it would be writing a test that
asserts an implementation detail.

The selection is the whole suite, never a per-mutant subset: choosing the tests
most likely to fail is how a table comes to describe the author's confidence
rather than the suite's power.

"""


def _record(result: MutationResult) -> dict:
    return {
        "mutant_id": result.mutant.mutant_id,
        "intent": result.mutant.intent,
        "target": result.mutant.target,
        "anchor": result.mutant.anchor,
        "applied": result.mutant.applied,
        "expectation": result.mutant.expectation,
        "status": result.status,
        "failures": list(result.failures),
        "tests_run": list(result.tests_run),
        "restored": result.restored,
        "detail": result.detail,
    }


def load_results(path: Path, head_sha: str) -> dict[str, dict]:
    """Prior results for THIS commit, keyed by mutant id.

    A file recorded at a different HEAD is not a partial run of this one. Two
    commits' results in one table would be a claim about code that never
    existed in that combination, so a mismatch discards rather than merges --
    and says so, because silently starting over would look like a slow run.
    """
    if not path.is_file():
        return {}
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        # Announced, like the head_sha mismatch below. Results are written
        # after every mutant, so a file truncated by a kill is exactly the case
        # this path handles -- and silently re-running the whole catalogue
        # "would look like a slow run", which is this module's own phrasing for
        # the failure it is trying to avoid.
        print(f"  (existing results are unreadable: {error} -- starting over)")
        return {}
    if not isinstance(body, dict) or body.get("head_sha") != head_sha:
        print(
            f"  (existing results are from {body.get('head_sha', 'an unknown commit')!r}, "
            f"not {head_sha!r} -- starting over rather than mixing two code states)"
        )
        return {}
    return {r["mutant_id"]: r for r in body.get("results", [])}


def save_results(
    path: Path,
    head_sha: str,
    catalogue: str,
    results: dict[str, dict],
    *,
    tree_dirty: bool = False,
) -> None:
    """Persist the accumulated results.

    `tree_dirty` is recorded because a commit SHA does not describe uncommitted
    edits, and evidence produced against a dirty tree is evidence about code
    that is not in the repository.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "core.mutation_evidence.v1",
                "authority_effect": "None",
                "head_sha": head_sha,
                "tree_dirty": tree_dirty,
                "catalogue": catalogue,
                "results": list(results.values()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _head_sha(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mutation_harness",
        description="Replay a mutation catalogue and emit the evidence table.",
    )
    parser.add_argument(
        "--catalogue",
        default="pfp.tests.mutation_catalogue",
        help="Importable module exposing MUTANTS and DEFAULT_TESTS",
    )
    parser.add_argument("--only", help="Run a single mutant by id")
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip mutants already recorded in --json AT THIS COMMIT. A full "
            "replay takes tens of minutes and interruption is the normal case; "
            "results are saved after every mutant so a kill costs one mutant."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Run even though the repository has uncommitted changes (weakens "
            "both the HEAD attribution and the restore proof)"
        ),
    )
    parser.add_argument("--json", help="Also write the results as JSON to this path")
    parser.add_argument(
        "--markdown",
        help=(
            "Also write the readable evidence table to this path. Emitted by the "
            "SAME run as --json so the two cannot disagree; assembling one of "
            "them by hand from a different run is the custody problem this "
            "harness exists to fix, and it happened once."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root; targets are resolved relative to it",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()

    orphan = check_no_orphaned_mutation(root)
    if orphan:
        print(f"REFUSING TO RUN: {orphan}", file=sys.stderr)
        return 2

    module = __import__(args.catalogue, fromlist=["MUTANTS"])
    mutants: list[Mutant] = list(module.MUTANTS)
    default_tests: tuple[str, ...] = tuple(module.DEFAULT_TESTS)
    default_runner: str = getattr(module, "DEFAULT_RUNNER", "pytest")
    exclude: tuple[str, ...] = tuple(getattr(module, "EXCLUDE_FROM_RUNS", ()))

    dirty_targets = _dirty_targets(root, mutants)
    dirty_tree = _dirty_tree(root)
    dirty = list(dict.fromkeys([*dirty_targets, *dirty_tree]))
    if dirty and args.allow_dirty:
        print(
            "  (running against a DIRTY tree: the restore proof shows only that "
            "the harness put back what it found, and the recorded head_sha does "
            "not describe the code that was tested)"
        )
    if dirty and not args.allow_dirty:
        print(
            "REFUSING TO RUN: these mutation targets have uncommitted changes:\n  "
            + "\n  ".join(dirty)
            + "\n\nA restore onto a dirty tree proves only that the harness put "
            "back what it found, which is not what the restore field claims. "
            "Commit or stash, or pass --allow-dirty and read the table knowing "
            "the proof is weaker.",
            file=sys.stderr,
        )
        return 2

    head = _head_sha(root)
    json_path = Path(args.json) if args.json else None
    # Prior records are loaded whenever the file exists, NOT only under
    # --resume. `save_results` writes whatever `done` holds, so starting empty
    # meant `--only M12 --json <the committed evidence>` overwrote 23 records
    # with one -- and the result still carried a valid schema and a matching
    # head_sha, so nothing downstream could tell it had been truncated.
    # Re-checking a single mutant is the natural use of --only, which made that
    # easy to hit and silent when hit.
    done: dict[str, dict] = load_results(json_path, head) if json_path else {}
    if done and args.resume:
        print(f"resuming: {len(done)} of {len(mutants)} already recorded at {head}")

    # --resume decides what to SKIP; it never decides what to keep.
    #
    # A SETUP FAILURE is not a result, so it must not satisfy a resume: an
    # ANCHOR or RESTORE row means no experiment ran, and skipping it would make
    # a transient permanent and leave the table quietly short of the catalogue.
    settled = {
        mid for mid, rec in done.items()
        if rec.get("status") in {"killed", "survived", "equivalent"}
    }
    pending = [m for m in mutants if not (args.resume and m.mutant_id in settled)]
    if args.only:
        pending = [m for m in pending if m.mutant_id == args.only]
    print(f"Replaying {len(pending)} mutant(s) from {args.catalogue}\n")

    results: list[MutationResult] = []
    for mutant in pending:
        result = run_mutant(
            mutant,
            root=root,
            default_tests=default_tests,
            default_runner=default_runner,
            exclude=exclude,
        )
        print(f"  [{result.status.upper():9}] {result.mutant.mutant_id}  {result.mutant.intent[:88]}")
        results.append(result)
        done[mutant.mutant_id] = _record(result)
        if json_path:
            # After EVERY mutant. A kill then costs one mutant, not the hour.
            save_results(
                json_path, head, args.catalogue, done, tree_dirty=bool(dirty_tree)
            )

    table = render_table(results, head_sha=head)
    print("\n" + table)

    if args.markdown:
        # Rendered from the ACCUMULATED set, not from this invocation's slice,
        # so a resumed run produces a table covering every mutant recorded at
        # this commit rather than only the tail.
        missing = [m.mutant_id for m in mutants if m.mutant_id not in done]
        banner = ""
        if missing:
            banner = (
                f"> **INCOMPLETE.** {len(missing)} of {len(mutants)} mutant(s) in "
                f"the catalogue were not replayed at this commit: "
                f"{', '.join(missing)}. Re-run with `--resume` to finish. This "
                "table is not a result about them.\n\n"
            )
        Path(args.markdown).write_text(
            MARKDOWN_PREAMBLE.format(catalogue=args.catalogue)
            + banner
            + "```text\n"
            + _render_records(list(done.values()), head)
            + "\n```\n",
            encoding="utf-8",
        )

    # A survivor, a setup failure or a failed restore is a non-zero exit: each
    # means the run did not establish what the catalogue claims it establishes.
    unclean = [r for r in done.values() if r["status"] in {"survived", "ANCHOR", "RESTORE"}]
    return 1 if unclean else 0


if __name__ == "__main__":
    raise SystemExit(main())
