"""Run the gate families written in `.github/workflows/verify.yml`, locally.

AuthorityEffect: None.  The workflow file is the contract; this runner reads
its steps from it and keeps no list of gates of its own.  A pass is a local
receipt for the working tree the runner ran on, nothing more.

    python ci/run_gates.py --list            # the steps, as parsed
    python ci/run_gates.py --fast            # the single-command checks, in seconds
    python ci/run_gates.py --job python      # one job; repeatable
    python ci/run_gates.py --workers 8       # all jobs, root tests in parallel
    python ci/run_gates.py --step 'side-free' --job research

How a step runs.  Each `run:` body is written to a file and executed by bash
with `-e` (`-eo pipefail` for `shell: bash`), as the hosted runner does.  On
Windows that is Git for Windows' `bin/bash.exe`; set GATES_BASH to override.
`python`, `python3` and `coverage` are bound to the interpreter running this
script, `${{ github.workspace }}` to the repository root, and RUNNER_TEMP to a
fresh directory.  Each step starts from the caller's environment without its
Python, pytest, coverage and mypy settings or the files bash would source
(SCRUBBED_ENV, SCRUBBED_PREFIXES), with PYTHONUTF8=1, no pager, and no stdin.
A step that runs past `timeout-minutes`, or is interrupted, is killed with
the processes it started: on Windows through a job object, elsewhere through
its process group.

What it holds of its own, each checked against the workflow so that a change
there is refused until reviewed: SETUP_STEPS, the steps skipped because they
install software, with a digest of each body; ACTIONS, the actions it gives a
local meaning, with the `with:` inputs each may carry; and the body of
COVERAGE_STEP that `--workers` replaces.  Any other workflow feature the
parser does not implement is refused, including a gate step whose body
matches a software installer.

What it cannot reproduce, and does instead:
* A hosted job starts from a fresh checkout.  Here, before any step runs, the
  outputs the workflow writes into the repository root (STALE_OUTPUTS) are
  deleted, so a step cannot pass on an earlier run's output.  A step that
  rewrites a tracked file under PROTECTED_DIRS fails, and the file is put
  back, so a failed regeneration cannot become the next run's baseline.  If
  HEAD moves during a run, nothing is put back and the remaining steps are
  not run.
* A pull request is checked out as its merge commit, and without
  `fetch-depth: 0` a hosted checkout is shallow.  Here the working tree is
  checked with its full history; the checkout step fails if the history is
  shallow and reports whether `origin/main` is in HEAD's history.
* Every job gets the running interpreter, and setup-python's check compares
  its version with the workflow's.  The hosted lean job has no setup-python
  and runs the image's own `python3`.
* The workflow writes fixed `/tmp/` paths, which are private to a hosted job
  but shared by every process on this machine; a lock stops two runs of this
  script from overlapping.

Within a job, a failure stops that job's remaining steps, as on the hosted
runner; other jobs still run.  `--keep-going` runs every selected step.
Installed package versions that differ from requirements.txt are printed with
the results.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / ".github" / "workflows" / "verify.yml"

# Steps that install software on a hosted runner, skipped here, with the first
# 16 hex digits of the SHA-256 of each body: a changed body is refused until
# the change is reviewed and its digest updated.
SETUP_STEPS = {
    "Install pinned dependencies": "f634394e6be6cb44",
    "Install elan": "223ad83112f52f3f",
    "Install pinned Lean toolchain": "f5a6fa1fa83d7182",
}
# Commands that install software; a gate step containing one is refused.
_INSTALLS = re.compile(
    r"\bpip[\w.]*\s+install\b|\buv\s+(?:pip|sync|tool|add)\b|\bnpm\s+(?:ci|install)\b"
    r"|\|\s*(?:ba)?sh\b|\b(?:cargo|pipx|conda|brew)\s+install\b|\bapt(?:-get)?\b[^\n]*\binstall\b"
    r"|\belan-init\b|\belan\s+toolchain\s+install\b|\blake\s+exe\s+cache\s+get\b"
)

# Actions the workflow uses, what each is checked as here, and the `with:`
# inputs each may carry.
ACTIONS = {
    "actions/checkout@v4": "full history present; reports whether origin/main is in HEAD's history",
    "actions/setup-python@v5": "the running interpreter's version equals `with.python-version`",
}
ACTION_INPUTS = {
    "actions/checkout@v4": frozenset({"fetch-depth"}),
    "actions/setup-python@v5": frozenset({"python-version"}),
}

# The root suite under coverage, whose body `--workers N` replaces.
COVERAGE_STEP = "Tests under coverage"
COVERAGE_BODY = "coverage run -m pytest -q\ncoverage json -q\ncoverage report\n"

# A single-command check that reads a file an earlier step writes.
READS_EARLIER_OUTPUT = frozenset({"ci/check_coverage.py"})
FAST_COMMAND = re.compile(r"python3? (ci/[A-Za-z0-9_./-]+\.py)|python3? -m mypy")

# Outputs the workflow writes into the repository root, deleted before a run.
STALE_OUTPUTS = ("coverage.json", "artifacts_ci", "lake_build.log")
# Tracked output pathspecs restored after a step, including timeout or failure.
# The research receipt wrapper restores ordinary exits itself; this outer
# snapshot also covers a wrapper killed with the rest of a timed-out step.
PROTECTED_DIRS = ("artifacts", ":(glob)research/**/receipts/**")
# Caller variables that would change what a step runs or measures: every
# Python, pytest, coverage and mypy setting, and the files bash sources.
SCRUBBED_ENV = ("BASH_ENV", "ENV")
SCRUBBED_PREFIXES = ("PYTHON", "PYTEST_", "COVERAGE_", "MYPY")

TOP_KEYS = frozenset({"name", "on", "jobs"})
JOB_KEYS = frozenset({"runs-on", "steps"})
STEP_KEYS = frozenset(
    {"name", "id", "uses", "with", "run", "shell", "working-directory", "env",
     "timeout-minutes", "continue-on-error"}
)
WORKSPACE_EXPR = "${{ github.workspace }}"


class WorkflowError(Exception):
    """The workflow uses something this runner does not implement."""


@dataclasses.dataclass(frozen=True)
class Step:
    job: str
    name: str
    run: str | None
    uses: str | None = None
    with_: tuple[tuple[str, str], ...] = ()
    working_directory: str | None = None
    env: tuple[tuple[str, str], ...] = ()
    timeout_minutes: float | None = None
    shell: str | None = None
    continue_on_error: bool = False

    @property
    def is_setup(self) -> bool:
        return self.name in SETUP_STEPS

    @property
    def is_fast(self) -> bool:
        if self.job != "python" or self.run is None or self.working_directory is not None:
            return False
        match = FAST_COMMAND.fullmatch(self.run.strip())
        return match is not None and match.group(1) not in READS_EARLIER_OUTPUT


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _scalar(value: str, number: int) -> str:
    """A plain or quoted scalar; the forms this parser would misread are refused."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if "\\" in inner or value[0] in inner:
            raise WorkflowError(f"line {number}: escapes in quoted scalars are not implemented")
        return inner
    if value[:1] in ("\"", "'", "&", "*", "!", ">", "|", "{", "[") or " #" in value:
        raise WorkflowError(f"line {number}: scalar form {value!r} is not implemented")
    return value


def _block(lines: list[str], start: int, parent: int) -> tuple[str, int]:
    """A `|` block scalar: every line indented deeper than its key."""
    body: list[str] = []
    indent: int | None = None
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            body.append("")
            i += 1
            continue
        if _indent(line) <= parent:
            break
        if indent is None:
            indent = _indent(line)
        if _indent(line) < indent:
            raise WorkflowError(f"line {i + 1}: block scalar dedents inside its block")
        body.append(line[indent:])
        i += 1
    while body and body[-1] == "":
        body.pop()
    if not body:
        raise WorkflowError(f"line {start}: empty block scalar")
    return "\n".join(body) + "\n", i


def _mapping(lines: list[str], start: int, parent: int) -> tuple[dict[str, str], int]:
    """A flat mapping of scalars, indented deeper than its key."""
    mapping: dict[str, str] = {}
    i = start
    while i < len(lines):
        line = lines[i]
        if _blank_or_comment(line):
            i += 1
            continue
        if _indent(line) <= parent:
            break
        key, sep, value = line.strip().partition(":")
        if not sep or not value.strip():
            raise WorkflowError(f"line {i + 1}: expected 'key: value' in a mapping")
        if key.strip() in mapping:
            raise WorkflowError(f"line {i + 1}: duplicate key {key.strip()!r}")
        mapping[key.strip()] = _scalar(value, i + 1)
        i += 1
    return mapping, i


def _minutes(value: object, where: str) -> float:
    if not isinstance(value, str) or not value.isdigit():
        raise WorkflowError(f"{where}: timeout-minutes must be a whole number, got {value!r}")
    return float(value)


def _step(job: str, fields: dict[str, object], where: str) -> Step:
    run, uses = fields.get("run"), fields.get("uses")
    if (run is None) == (uses is None):
        raise WorkflowError(f"{where}: a step needs exactly one of run/uses")
    if run is not None and not isinstance(run, str):
        raise WorkflowError(f"{where}: run must be a string")
    if uses is not None and not isinstance(uses, str):
        raise WorkflowError(f"{where}: uses must be a string")
    if "with" in fields and uses is None:
        raise WorkflowError(f"{where}: 'with' without 'uses'")
    name = fields.get("name")
    if run is not None and not isinstance(name, str):
        raise WorkflowError(f"{where}: a run step needs a name")
    for key in ("env", "with"):
        if not isinstance(fields.get(key, {}), dict):
            raise WorkflowError(f"{where}: '{key}' must be a mapping")
    shell = fields.get("shell")
    if shell is not None and shell != "bash":
        raise WorkflowError(f"{where}: shell {shell!r} is not implemented")
    cont = fields.get("continue-on-error", "false")
    if cont not in ("true", "false"):
        raise WorkflowError(f"{where}: continue-on-error must be true or false")
    working = fields.get("working-directory")
    env = fields.get("env", {})
    with_ = fields.get("with", {})
    assert isinstance(env, dict) and isinstance(with_, dict)
    return Step(
        job=job,
        name=name if isinstance(name, str) else f"uses {uses}",
        run=run,
        uses=uses,
        with_=tuple(sorted(with_.items())),
        working_directory=working if isinstance(working, str) else None,
        env=tuple(sorted(env.items())),
        timeout_minutes=(
            _minutes(fields["timeout-minutes"], where) if "timeout-minutes" in fields else None
        ),
        shell=shell if isinstance(shell, str) else None,
        continue_on_error=cont == "true",
    )


def parse_workflow(text: str) -> list[Step]:
    """The steps of every job, in file order.

    Parses the subset of YAML this workflow uses: top-level keys at column 0,
    jobs at two spaces, job keys at four, steps at six, step keys at eight,
    flat mappings and `|` blocks beneath them.  Anything else raises.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    for number, line in enumerate(lines, 1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise WorkflowError(f"line {number}: tab indentation is not implemented")
        if line and not line[0].isspace() and not line.startswith("#"):
            key = line.partition(":")[0]
            if not re.fullmatch(r"[A-Za-z_-]+", key) or key not in TOP_KEYS:
                raise WorkflowError(f"line {number}: top-level {key!r} is not implemented")
    if "jobs:" not in lines:
        raise WorkflowError("no top-level 'jobs:' key")
    steps: list[Step] = []
    job: str | None = None
    in_steps = False
    fields: dict[str, object] | None = None
    i = lines.index("jobs:") + 1
    start = 0
    jobs_seen: set[str] = set()

    def flush() -> None:
        nonlocal fields
        if fields is not None and job is not None:
            steps.append(_step(job, fields, f"step at line {start}"))
        fields = None

    while i < len(lines):
        line = lines[i]
        if _blank_or_comment(line):
            i += 1
            continue
        indent, body = _indent(line), line.strip()
        if indent == 0:
            break
        if indent == 2:
            flush()
            if not re.fullmatch(r"[A-Za-z0-9_-]+:", body):
                raise WorkflowError(f"line {i + 1}: expected a job name")
            if body[:-1] in jobs_seen:
                raise WorkflowError(f"line {i + 1}: duplicate job {body[:-1]!r}")
            job, in_steps = body[:-1], False
            jobs_seen.add(job)
            i += 1
            continue
        if indent == 4:
            flush()
            key, _, value = body.partition(":")
            if key not in JOB_KEYS:
                raise WorkflowError(f"line {i + 1}: job key {key!r} is not implemented")
            if key == "runs-on" and not _scalar(value, i + 1).startswith("ubuntu"):
                raise WorkflowError(f"line {i + 1}: only ubuntu runners are implemented")
            in_steps = key == "steps"
            i += 1
            continue
        if not in_steps:
            raise WorkflowError(f"line {i + 1}: unexpected nesting outside steps")
        if indent == 6:
            if not body.startswith("- "):
                raise WorkflowError(f"line {i + 1}: expected a '- ' step item")
            flush()
            fields, start = {}, i + 1
            body, indent = body[2:], 8
        if indent != 8 or fields is None:
            raise WorkflowError(f"line {i + 1}: unexpected indentation")
        key, sep, value = body.partition(":")
        key, value = key.strip(), value.strip()
        if not sep:
            raise WorkflowError(f"line {i + 1}: expected 'key: value'")
        if key not in STEP_KEYS:
            raise WorkflowError(f"line {i + 1}: step key {key!r} is not implemented")
        if key in fields:
            raise WorkflowError(f"line {i + 1}: duplicate step key {key!r}")
        if value == "|":
            fields[key], i = _block(lines, i + 1, 8)
        elif value == "":
            fields[key], i = _mapping(lines, i + 1, 8)
        else:
            fields[key] = _scalar(value, i + 1)
            i += 1
    flush()
    return steps


def resolve_env(step: Step, repo: Path) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key, value in step.env:
        value = value.replace(WORKSPACE_EXPR, repo.as_posix())
        if "${{" in value:
            raise WorkflowError(f"{step.name}: expression in env {key} is not implemented")
        resolved[key] = value
    return resolved


def check_contract(steps: list[Step]) -> None:
    """The names and bodies this runner holds must still match the workflow."""
    names = {s.name for s in steps}
    missing = sorted((set(SETUP_STEPS) | {COVERAGE_STEP}) - names)
    if missing:
        raise WorkflowError(f"steps named by ci/run_gates.py are gone from the workflow: {missing}")
    for step in steps:
        if step.uses is not None:
            if step.uses not in ACTIONS:
                raise WorkflowError(f"{step.name}: action {step.uses!r} has no local meaning here")
            inputs = dict(step.with_)
            extra = sorted(set(inputs) - ACTION_INPUTS[step.uses])
            if extra:
                raise WorkflowError(f"{step.name}: inputs {extra} are not implemented")
            if inputs.get("fetch-depth", "0") != "0":
                raise WorkflowError(f"{step.name}: only fetch-depth 0 is implemented")
        if step.run is None:
            continue
        if "${{" in step.run:
            raise WorkflowError(f"{step.name}: expression in run is not implemented")
        if step.is_setup:
            digest = hashlib.sha256(step.run.encode("utf-8")).hexdigest()[:16]
            if digest != SETUP_STEPS[step.name]:
                raise WorkflowError(
                    f"{step.name}: its body changed (digest {digest}); "
                    "review the change and update SETUP_STEPS"
                )
        elif _INSTALLS.search(step.run):
            raise WorkflowError(f"{step.name}: installs software but is not in SETUP_STEPS")
        if step.name == COVERAGE_STEP and step.run != COVERAGE_BODY:
            raise WorkflowError(f"{COVERAGE_STEP}: its body changed; update --workers to match")
        resolve_env(step, REPO)


def select(steps: list[Step], jobs: list[str], fast: bool, pattern: str | None) -> list[Step]:
    """The steps to run.  An action step runs whenever any step of its job does."""
    known = {s.job for s in steps}
    unknown = sorted(set(jobs) - known)
    if unknown:
        raise WorkflowError(f"no such job {unknown}; jobs are {sorted(known)}")
    wanted = re.compile(pattern, re.IGNORECASE) if pattern is not None else None
    chosen = [
        s for s in steps
        if s.run is not None and not s.is_setup
        and (not jobs or s.job in jobs)
        and (not fast or s.is_fast)
        and (wanted is None or wanted.search(s.name))
    ]
    active = {s.job for s in chosen}
    return [s for s in steps if s in chosen or (s.uses is not None and s.job in active)]


def find_bash() -> str:
    override = os.environ.get("GATES_BASH")
    if override:
        if not Path(override).is_file():
            raise WorkflowError(f"GATES_BASH={override} is not a file")
        return override
    if sys.platform == "win32":
        # Git for Windows: <root>/mingw64/libexec/git-core -> <root>/bin/bash.exe,
        # the launcher that puts /usr/bin first.  A bare `bash` on PATH can be
        # the WSL one, which sees a different filesystem.
        exec_path = Path(_git_text(REPO, "--exec-path"))
        candidate = exec_path.parents[2] / "bin" / "bash.exe" if len(exec_path.parents) > 2 else None
        if candidate is not None and candidate.is_file():
            return str(candidate)
        raise WorkflowError("Git for Windows bash not found; set GATES_BASH")
    found = shutil.which("bash")
    if found is None:
        raise WorkflowError("bash not found; set GATES_BASH")
    return found


def _git_text(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)
    if proc.returncode != 0:
        raise WorkflowError(f"git {' '.join(args)}: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout.decode("utf-8", "replace").strip()


def _posix_exe(path: str) -> str:
    """An interpreter path bash can execute: C:\\x\\y -> /c/x/y on Windows."""
    posix = Path(path).as_posix()
    if sys.platform == "win32" and re.match(r"[A-Za-z]:/", posix):
        posix = f"/{posix[0].lower()}{posix[2:]}"
    if '"' in posix or "$" in posix or "`" in posix:
        raise WorkflowError(f"interpreter path {path!r} cannot be quoted for bash")
    return posix


def prelude(python: str) -> str:
    exe = _posix_exe(python)
    return (
        f'python() {{ "{exe}" "$@"; }}\n'
        f'python3() {{ "{exe}" "$@"; }}\n'
        f'coverage() {{ "{exe}" -m coverage "$@"; }}\n'
        "export -f python python3 coverage\n"
    )


def parallel_tests(workers: int) -> str:
    """The pytest command of CLAUDE.md's parallel recipe, as one bash body."""
    return (
        f"python -m pytest -n {workers} --dist load --cov=code --cov-branch "
        "--cov-report=json:coverage.json --cov-report=term\n"
    )


def pin_drift(repo: Path) -> list[str]:
    """Installed versions that differ from the `name==version` lines of
    requirements.txt.  The hosted runner installs the pins; this runner uses
    whatever the interpreter has, so a difference is reported, not hidden."""
    drift: list[str] = []
    for line in (repo / "requirements.txt").read_text(encoding="utf-8").splitlines():
        name, sep, pinned = line.strip().partition("==")
        if not sep:
            continue
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed = "not installed"
        if installed != pinned:
            drift.append(f"{name} {installed} (requirements.txt pins {pinned})")
    return drift


def git_status(repo: Path) -> set[str]:
    """`XY path` entries; a rename's source path is folded into its entry."""
    out = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo, capture_output=True, check=True,
    ).stdout.decode("utf-8", "replace").split("\0")
    entries: set[str] = set()
    tokens = iter(t for t in out if t)
    for token in tokens:
        if token[:1] in ("R", "C"):
            token = f"{token} <- {next(tokens, '?')}"
        entries.add(token)
    return entries


def check_top_level(repo: Path) -> None:
    top = _git_text(repo, "rev-parse", "--show-toplevel")
    if os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(repo)):
        raise WorkflowError(
            f"{repo} is not the top of its own checkout (git's top level is {top}); "
            "a plain subdirectory shares the other checkout's HEAD. "
            "Use `git worktree add ../<name>` and run from there."
        )


LOCK = Path(tempfile.gettempdir()) / "19L57G1-run_gates.lock"


@contextlib.contextmanager
def machine_lock(path: Path = LOCK) -> Iterator[None]:
    """Held for a whole run: the workflow's /tmp paths are machine-wide here."""
    handle = open(path, "a+b")
    try:
        try:
            if sys.platform == "win32":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise WorkflowError(
                f"another run of ci/run_gates.py holds {path}; the workflow's /tmp "
                "files are shared on this machine, so runs cannot overlap"
            ) from exc
        yield
    finally:
        handle.close()


def clear_stale_outputs(repo: Path) -> list[str]:
    """Delete the untracked outputs a previous run left in the repository root."""
    tracked = _git_text(repo, "ls-files", "--", *STALE_OUTPUTS).splitlines()
    removed: list[str] = []
    for name in STALE_OUTPUTS:
        path = repo / name
        if any(t == name or t.startswith(name + "/") for t in tracked):
            continue
        if not (path.exists() or path.is_symlink()):
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(name)
    return removed


def protected_snapshot(repo: Path) -> dict[str, bytes]:
    if not (repo / ".git").exists():
        return {}
    names = _git_text(repo, "ls-files", "-z", "--", *PROTECTED_DIRS).split("\0")
    return {n: (repo / n).read_bytes() for n in names if n and (repo / n).is_file()}


def restore_protected(repo: Path, snapshot: dict[str, bytes]) -> list[str]:
    restored: list[str] = []
    for name, data in snapshot.items():
        path = repo / name
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
            restored.append(name)
    return restored


def step_env(step: Step, repo: Path, runner_temp: Path) -> dict[str, str]:
    env = {
        k: v for k, v in os.environ.items()
        if k.upper() not in SCRUBBED_ENV and not k.upper().startswith(SCRUBBED_PREFIXES)
    }
    env.update(resolve_env(step, repo))
    env.update(
        PYTHONUTF8="1", GIT_PAGER="cat", PAGER="cat",
        RUNNER_TEMP=runner_temp.as_posix(), GITHUB_WORKSPACE=repo.as_posix(),
    )
    return env


def _windows_job(proc: subprocess.Popen[bytes]) -> int | None:
    """A job object holding the step's process.  Windows adds every process
    the step starts to it, including programs an MSYS shell starts by fork and
    exec, which `taskkill /T` misses because it follows parent ids.  None
    where there are no job objects or the assignment is refused."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    job = kernel32.CreateJobObjectW(None, None)
    handle = getattr(proc, "_handle", None)
    if not job:
        return None
    if handle is None or not kernel32.AssignProcessToJobObject(job, int(handle)):
        kernel32.CloseHandle(job)
        return None
    return int(job)


def _close_job(job: int | None, terminate: bool) -> None:
    if job is None or sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    if terminate:
        kernel32.TerminateJobObject(job, 1)
    kernel32.CloseHandle(job)


def _kill_tree(proc: subprocess.Popen[bytes], job: int | None) -> None:
    if sys.platform == "win32":
        _close_job(job, terminate=True)
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


@dataclasses.dataclass
class Result:
    step: Step
    outcome: str
    exit_code: int | None = None
    seconds: float = 0.0
    note: str = ""


def run_action(step: Step, repo: Path) -> Result:
    """The local meaning of an action step (see ACTIONS)."""
    wanted = dict(step.with_)
    if step.uses == "actions/setup-python@v5":
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if version == wanted.get("python-version"):
            return Result(step, "pass", 0, note=f"interpreter {version}")
        return Result(step, "FAIL", 1, note=f"interpreter {version}, workflow {wanted.get('python-version')}")
    if _git_text(repo, "rev-parse", "--is-shallow-repository") == "true":
        return Result(step, "FAIL", 1, note="shallow history")
    code = subprocess.run(
        ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
        cwd=repo, capture_output=True, check=False,
    ).returncode
    history = {
        0: "",
        1: "; origin/main is not in HEAD's history, so this is not the merge result",
    }.get(code, "; could not compare HEAD with origin/main")
    return Result(step, "pass", 0, note="working tree" + history)


def _head(repo: Path) -> str | None:
    return _git_text(repo, "rev-parse", "HEAD") if (repo / ".git").exists() else None


def _add_note(result: Result, note: str) -> None:
    result.note = "; ".join(filter(None, [result.note, note]))


def run_steps(
    steps: list[Step],
    repo: Path,
    bash: str,
    python: str,
    keep_going: bool = False,
    workers: int | None = None,
) -> list[Result]:
    """Run the steps in order.  A step that rewrites a tracked file under
    PROTECTED_DIRS fails, and the file is put back.  If HEAD moves during the
    run nothing is put back, since the files may now belong to another
    commit, and the remaining steps are not run."""
    results: list[Result] = []
    failed_jobs: set[str] = set()
    protected = protected_snapshot(repo)
    head = _head(repo)
    moved = False
    with tempfile.TemporaryDirectory(prefix="gates-") as tmp:
        scratch = Path(tmp)
        runner_temp = scratch / "runner_temp"
        runner_temp.mkdir()
        for index, step in enumerate(steps):
            if moved:
                results.append(Result(step, "not run", note="HEAD moved during the run"))
                continue
            if step.job in failed_jobs and not keep_going:
                results.append(Result(step, "not run", note="an earlier step in this job failed"))
                continue
            print(f"\n=== [{step.job}] {step.name}", flush=True)
            restored: list[str] = []
            try:
                if step.uses is not None:
                    result = run_action(step, repo)
                else:
                    result = _run_script(step, index, repo, bash, python, scratch, runner_temp, workers)
            finally:
                moved = _head(repo) != head
                if not moved:
                    restored = restore_protected(repo, protected)
            if moved:
                _add_note(result, "HEAD moved; tracked files left as the step left them")
            if restored:
                if result.outcome == "pass":
                    result.outcome = "FAIL"
                _add_note(result, "rewrote " + ", ".join(restored) + "; restored")
            if result.outcome != "pass":
                if step.continue_on_error:
                    _add_note(result, "continue-on-error")
                else:
                    failed_jobs.add(step.job)
            results.append(result)
    return results


def _run_script(
    step: Step, index: int, repo: Path, bash: str, python: str,
    scratch: Path, runner_temp: Path, workers: int | None,
) -> Result:
    assert step.run is not None
    body, note = step.run, ""
    if workers is not None and step.name == COVERAGE_STEP:
        body, note = parallel_tests(workers), f"parallel, {workers} workers"
    cwd = repo / step.working_directory if step.working_directory else repo
    if not cwd.is_dir():
        return Result(step, "FAIL", note=f"working-directory {step.working_directory} does not exist")
    script = scratch / f"step{index:03d}.sh"
    script.write_bytes((prelude(python) + body).encode("utf-8"))
    flags = ["-eo", "pipefail"] if step.shell == "bash" else ["-e"]
    started = time.monotonic()
    proc = subprocess.Popen(
        [bash, "--noprofile", "--norc", *flags, script.as_posix()],
        cwd=cwd, env=step_env(step, repo, runner_temp), stdin=subprocess.DEVNULL,
        start_new_session=sys.platform != "win32",
    )
    job = _windows_job(proc)
    try:
        code: int | None = proc.wait(
            timeout=step.timeout_minutes * 60 if step.timeout_minutes else None
        )
        outcome = "pass" if code == 0 else "FAIL"
        _close_job(job, terminate=False)
    except subprocess.TimeoutExpired:
        _kill_tree(proc, job)
        code, outcome = None, "TIMEOUT"
    except BaseException:
        # Ctrl-C included: the step's processes go too, not just this one.
        _kill_tree(proc, job)
        raise
    return Result(step, outcome, code, time.monotonic() - started, note)


def report(results: list[Result], head: str, end_head: str, before: set[str], after: set[str]) -> str:
    width = max([len(r.step.name) for r in results] + [4])
    rows = [f"{'job':<9}{'step':<{width + 2}}{'result':<9}{'seconds':>8}"]
    for r in results:
        rows.append(f"{r.step.job:<9}{r.step.name:<{width + 2}}{r.outcome:<9}{r.seconds:>8.1f}"
                    + (f"  {r.note}" if r.note else ""))
    passed = sum(r.outcome == "pass" for r in results)
    rows.append("")
    rows.append(f"{passed} of {len(results)} selected steps passed at HEAD {head}")
    if end_head != head:
        rows.append(f"HEAD moved to {end_head} during the run; the results mix the two")
    if before:
        rows.append(f"the working tree had {len(before)} uncommitted paths when the run started")
    changed = sorted(after ^ before)
    if changed:
        rows.append("git status changed during the run:")
        rows.extend(f"  {entry}" for entry in changed)
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--job", action="append", default=[], help="run only this job (repeatable)")
    parser.add_argument("--fast", action="store_true", help="only single-command python-job checks")
    parser.add_argument("--step", help="only steps whose name matches this regular expression")
    parser.add_argument("--list", action="store_true", help="print the selected steps and exit")
    parser.add_argument("--keep-going", action="store_true", help="do not stop a job at its first failure")
    parser.add_argument("--workers", type=int, help="run the root suite with pytest-xdist and N workers")
    parser.add_argument("--receipt", type=Path, help="also write the results as JSON here")
    args = parser.parse_args(argv)

    try:
        steps = parse_workflow(WORKFLOW.read_text(encoding="utf-8"))
        check_contract(steps)
        chosen = select(steps, args.job, args.fast, args.step)
        if not any(s.run is not None for s in chosen):
            raise WorkflowError("the selection is empty")
        if args.list:
            for s in chosen:
                kind = "fast " if s.is_fast else "check" if s.uses else "     "
                where = f"  (in {s.working_directory})" if s.working_directory else ""
                print(f"{s.job:<9}{kind} {s.name}{where}")
            return 0
        if args.receipt is not None and not args.receipt.resolve().parent.is_dir():
            raise WorkflowError(f"--receipt {args.receipt}: its directory does not exist")
        check_top_level(REPO)
        bash = find_bash()
        if args.workers is not None and any(s.name == COVERAGE_STEP for s in chosen):
            missing = [m for m in ("xdist", "pytest_cov") if importlib.util.find_spec(m) is None]
            if missing:
                raise WorkflowError(f"--workers needs pytest-xdist and pytest-cov; missing {missing}")
        with machine_lock():
            head = _git_text(REPO, "rev-parse", "HEAD")
            drift = pin_drift(REPO)
            removed = clear_stale_outputs(REPO)
            if removed:
                print("removed output left by an earlier run: " + ", ".join(removed))
            before = git_status(REPO)
            results = run_steps(chosen, REPO, bash, sys.executable, args.keep_going, args.workers)
            after = git_status(REPO)
            end_head = _git_text(REPO, "rev-parse", "HEAD")
    except WorkflowError as exc:
        print(f"run_gates: {exc}", file=sys.stderr)
        return 2

    print("\n" + report(results, head, end_head, before, after))
    if drift:
        print("these results come from an interpreter whose packages differ from the pins:")
        print("\n".join(f"  {line}" for line in drift))
    if args.receipt is not None:
        receipt = {
            "head": head,
            "head_at_end": end_head,
            "python": sys.version.split()[0],
            "packages_differing_from_pins": drift,
            "removed_before_run": removed,
            "uncommitted_at_start": sorted(before),
            "status_changed_during_run": sorted(after ^ before),
            "steps": [
                {"job": r.step.job, "name": r.step.name, "outcome": r.outcome,
                 "exit_code": r.exit_code, "seconds": round(r.seconds, 1), "note": r.note}
                for r in results
            ],
        }
        args.receipt.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    return 0 if all(r.outcome == "pass" or r.step.continue_on_error for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
