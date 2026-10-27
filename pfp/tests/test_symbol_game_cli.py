"""Tests for Symbol Game CLI and core-symgam-workflow entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

from pfp.entrypoints.cli.symbol_game import main
import pytest

from operating_system.adapters.security import (
    FixtureOnlyAeadProtector,
)
from operating_system.infrastructure import EncryptedArtifactCas
from pfp.entrypoints.cli.code_change_commands import (
    FIXTURE_CAS_KEY,
)
from pfp.infrastructure.trace import (
    DISPATCH_COMPLETE,
    EVENT_DISPATCH_INTENT_DURABLE,
    EVENT_RESPONSE_DURABLE,
    EVENT_STAGE_REFUSED,
    STATUS_BOUNDED_RUN_COMPLETE,
    STATUS_INCOMPLETE,
    TraceRefusal,
    derive_dispatch_outcomes,
    read_status,
    scan_trace,
    terminal_digest,
    verify_trace,
)


def _fixture_store(out: Path) -> EncryptedArtifactCas:
    return EncryptedArtifactCas(
        out / "encrypted_artifacts", FixtureOnlyAeadProtector(FIXTURE_CAS_KEY)
    )


def test_cli_run_turn_from_prompt_flag(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--prompt",
            "verify formal coboundary obstruction for 1-cochain",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 2
    assert not (tmp_path / "runs").exists()


def test_cli_run_turn_subcommand(tmp_path: Path) -> None:
    exit_code = main(
        ["run-turn", "--prompt", "algebraic reduction", "--output-dir", str(tmp_path)]
    )
    assert exit_code == 2
    assert not (tmp_path / "runs").exists()


def test_cli_run_turn_empty_prompt(tmp_path: Path) -> None:
    exit_code = main(["--prompt", "", "--output-dir", str(tmp_path)])
    assert exit_code == 2
    assert not (tmp_path / "runs").exists()


def test_cli_run_turn_multi_step(tmp_path: Path) -> None:
    exit_code = main(
        [
            "run",
            "--prompt",
            "4D Regge manifold reduction",
            "--max-steps",
            "3",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 2
    assert not (tmp_path / "runs").exists()


def test_cli_code_change_run_fixture_seals_a_trace_and_writes_a_run_root(
    tmp_path: Path,
) -> None:
    """The whole code-change path, run once from the command line.

    This is the smoke test for the caller the instrumented path did not have.
    `ExecutionTrace`, `fixture_gateway` and `TracedCodeChangeController` were
    complete and tested and reachable from nothing but their own tests; until
    something ran them together, the harness recorded nothing that anyone could
    ask for.

    Each assertion answers a different way the wiring could be wrong: the command
    succeeded, the trace *derives* complete rather than merely existing, the run
    root reached disk, and -- the one that took a review to notice -- the patch
    actually travelled through the provider seam.

    That last group is load-bearing. An earlier version asserted only the first
    three, and would have passed unchanged if the gateway call were deleted and
    the patch handed straight to `submit_patch`: the run would still complete,
    still seal, and still write a run root. A smoke test for a seam has to fail
    when the seam is bypassed, so it checks both barrier records and requires the
    stored bytes to match their recorded digest.
    """
    patch = tmp_path / "fix.patch"
    patch.write_text(
        "--- a/src/x.py\n+++ b/src/x.py\n@@ -0,0 +1,1 @@\n+x = 1\n",
        encoding="utf-8",
        newline="\n",
    )
    out = tmp_path / "run"

    exit_code = main(
        [
            "code-change-run-fixture",
            "--task-id",
            "task-cli-smoke",
            "--objective",
            "record one deterministic code-change execution",
            "--patch",
            str(patch),
            "--owned-path",
            "src/x.py",
            "--protected-path",
            "README.md",
            "--output-dir",
            str(out),
        ]
    )

    assert exit_code == 0

    # Derived from the file, never read off a producer field: a trace that merely
    # exists proves the command ran, not that the run completed.
    assert read_status(out / "trace.jsonl") == STATUS_BOUNDED_RUN_COMPLETE

    run_root = json.loads((out / "run_root.json").read_text(encoding="utf-8"))
    assert run_root["schema_version"] == "core.symbol-game.code-change-run-root.v1"
    assert run_root["authority_effect"] == "None"

    # The patch went through the provider seam, not around it. Both barriers
    # left a record: intent before the socket, response bytes after.
    records = scan_trace(out / "trace.jsonl").records
    events = [r.event for r in records]
    assert EVENT_DISPATCH_INTENT_DURABLE in events
    assert EVENT_RESPONSE_DURABLE in events

    assert len(list((out / "encrypted_artifacts").rglob("*.oeos-envelope"))) == 1
    outcomes = derive_dispatch_outcomes(records, artifact_store=_fixture_store(out))
    assert [o.status for o in outcomes] == [DISPATCH_COMPLETE]


# --------------------------------------------------------------------------
# The traced code-change command, beyond the smoke test
# --------------------------------------------------------------------------
#
# Tier 1 encodes the two refusal paths that were verified by hand and left as
# ledger debt. Tier 2 covers replay and gate discrimination *through the
# command*, which the controller-level tests cannot reach: they do not see the
# dispatch attempt id or the files that land on disk.

CLEAN_DIFF = "--- a/src/x.py\n+++ b/src/x.py\n@@ -0,0 +1,1 @@\n+x = 1\n"
PROTECTED_DIFF = "--- a/README.md\n+++ b/README.md\n@@ -0,0 +1,1 @@\n+x = 1\n"
ELSEWHERE_DIFF = (
    "--- a/src/elsewhere.py\n+++ b/src/elsewhere.py\n@@ -0,0 +1,1 @@\n+x = 1\n"
)


def _run_fixture(
    tmp_path: Path,
    name: str,
    patch_text: str,
    *,
    task_id: str | None = None,
    owned: tuple[str, ...] = ("src/x.py",),
    protected: tuple[str, ...] = ("README.md",),
) -> tuple[int, Path]:
    """Run `code-change-run-fixture` once. Returns `(exit_code, output_dir)`.

    `task_id` defaults to `name` but is separable, because a replay needs two
    runs that declare the *same* execution into *different* directories.
    """
    patch = tmp_path / (name + ".patch")
    patch.write_text(patch_text, encoding="utf-8", newline="\n")
    out = tmp_path / name
    argv = [
        "code-change-run-fixture",
        "--task-id",
        task_id or name,
        "--objective",
        "exercise the traced code-change path",
        "--patch",
        str(patch),
    ]
    for path in owned:
        argv += ["--owned-path", path]
    for path in protected:
        argv += ["--protected-path", path]
    argv += ["--output-dir", str(out)]
    return main(argv), out


def _terminal(out: Path) -> str:
    return json.loads((out / "run_root.json").read_text(encoding="utf-8"))[
        "terminal_status"
    ]


def _attempt_ids(out: Path) -> list[str]:
    records = scan_trace(out / "trace.jsonl").records
    return [
        o.attempt_id
        for o in derive_dispatch_outcomes(records, artifact_store=_fixture_store(out))
    ]


def test_cli_a_malformed_patch_refuses_and_writes_no_run_root(tmp_path: Path) -> None:
    """A stage refusal is a command failure, and must not look like a run.

    The trace is left **unsealed on purpose**: the run did not complete, and a
    file deriving INCOMPLETE is the honest record of that. `StageRefused` is
    already in it, recorded before the exception was re-raised, so the file says
    what stopped rather than merely stopping.
    """
    exit_code, out = _run_fixture(tmp_path, "malformed", "this is not a unified diff\n")

    assert exit_code == 2
    assert not (out / "run_root.json").exists(), "a run that did not finish has no root"
    assert read_status(out / "trace.jsonl") == STATUS_INCOMPLETE
    assert EVENT_STAGE_REFUSED in [
        r.event for r in scan_trace(out / "trace.jsonl").records
    ]


def test_cli_an_unowned_patch_is_a_verdict_not_a_command_failure(
    tmp_path: Path,
) -> None:
    """The distinction the exit code must not collapse.

    A gate refusing a candidate is the protocol working. The command exits `0`,
    the trace seals, and the refusal is carried as a *terminal status* in the run
    root. Turning that into a non-zero exit would merge `GtocTerminal` into
    process status -- two of the three domains `status_vocabulary.md` keeps
    apart -- and would make a working refusal indistinguishable from a crash.
    """
    exit_code, out = _run_fixture(
        tmp_path, "unowned", ELSEWHERE_DIFF, owned=("src/only_here.py",)
    )

    assert exit_code == 0
    assert read_status(out / "trace.jsonl") == STATUS_BOUNDED_RUN_COMPLETE
    assert _terminal(out) == "TypedRefusal"


def test_cli_two_identical_runs_derive_identical_identities(tmp_path: Path) -> None:
    """Replay determinism through the command.

    `test_two_runs_of_one_fixture_record_identical_identities` covers the
    controller. It cannot see the dispatch attempt id or the files that reach
    disk, and those are exactly what a recovery join uses. Two runs declaring the
    same execution into different directories must agree on both.
    """
    first_code, first = _run_fixture(
        tmp_path, "replay1", CLEAN_DIFF, task_id="replay-task"
    )
    second_code, second = _run_fixture(
        tmp_path, "replay2", CLEAN_DIFF, task_id="replay-task"
    )

    assert first_code == 0 and second_code == 0
    assert _attempt_ids(first) == _attempt_ids(second), (
        "the dispatch join must be stable"
    )
    assert (first / "run_root.json").read_bytes() == (
        second / "run_root.json"
    ).read_bytes()


def test_cli_a_refused_patch_reaches_a_different_terminal_than_a_clean_one(
    tmp_path: Path,
) -> None:
    """The gates discriminate *through the command*, not only in the use case.

    Without this, every CLI test above would still pass against a wiring that
    ran the gates and discarded their verdict -- the run would seal, the run root
    would exist, and every candidate would read the same.
    """
    clean_code, clean = _run_fixture(tmp_path, "clean", CLEAN_DIFF)
    refused_code, refused = _run_fixture(tmp_path, "refused", PROTECTED_DIFF)

    assert clean_code == 0 and refused_code == 0, "both are completed runs"
    assert _terminal(clean) == "DeclaredUnverified"
    assert _terminal(refused) == "TypedRefusal"
    assert _terminal(clean) != _terminal(refused)


def test_cli_prints_the_terminal_digest_the_trace_actually_sealed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The printed digest must be the sealed record's, not merely a hex string.

    The runbook now tells an operator to carry this value off the host and check
    a trace against it later. If the CLI printed anything other than the last
    chained record's sha256 -- a stale value, a re-derived one, the genesis link
    -- that instruction would send them to compare against a number the file
    never contained, and `verify_trace` would refuse a genuine trace.

    So this asserts the round trip end to end: printed == sealed == what
    `verify_trace` accepts, and a neighbouring digest is refused.
    """
    exit_code, out = _run_fixture(tmp_path, "digest", CLEAN_DIFF)
    assert exit_code == 0

    printed = None
    for line in capsys.readouterr().out.splitlines():
        if line.strip().startswith("terminal_digest"):
            printed = line.split(":", 1)[1].strip()
    assert printed is not None, "the CLI summary must carry the digest"
    assert len(printed) == 64 and all(c in "0123456789abcdef" for c in printed)

    trace_path = out / "trace.jsonl"
    sealed = terminal_digest(scan_trace(trace_path))
    assert printed == sealed, "printed digest is not the sealed record's"

    # The value is usable for what the runbook tells an operator to do with it.
    verify_trace(trace_path, expected_terminal_digest=printed)

    # ...and it is discriminating, not merely present.
    with pytest.raises(TraceRefusal):
        verify_trace(trace_path, expected_terminal_digest="0" * 64)
