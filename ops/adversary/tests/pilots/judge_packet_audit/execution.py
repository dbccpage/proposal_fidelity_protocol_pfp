"""Runs worker jobs in subprocesses with timeouts and restart-at-next-item.

Each job is written to a temporary JSON file and executed by
``worker.py`` with the working directory set to the challenge package.
Items are processed in order. When the worker exits early (a watchdog
timeout, a crash, or a hard wall-clock kill), the item in progress is
recorded with that outcome and a new worker resumes at the following item.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

WORKER_PATH = Path(__file__).resolve().parent / "worker.py"
STDERR_TAIL = 1200
EXIT_TIMEOUT = 3


@dataclass
class JobResult:
    """Per-item records keyed by item index, plus launch diagnostics."""

    records: dict[int, dict[str, Any]] = field(default_factory=dict)
    import_error: str | None = None
    launches: int = 0
    crashes: list[dict[str, Any]] = field(default_factory=list)


def worker_env(intelligence_root: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["CORE_INTELLIGENCE_ROOT"] = str(intelligence_root)
    return env


def run_job(
    job: dict[str, Any],
    n_items: int,
    *,
    cwd: Path,
    intelligence_root: Path,
    scratch_dir: Path,
    wall_timeout_s: float,
    python: str | None = None,
) -> JobResult:
    """Runs ``job`` until every one of ``n_items`` items has a record."""
    result = JobResult()
    start = 0
    scratch_dir.mkdir(parents=True, exist_ok=True)
    env = worker_env(intelligence_root)
    exe = python or sys.executable
    while start < n_items or (n_items == 0 and result.launches == 0):
        payload = dict(job, start=start)
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=scratch_dir, delete=False, encoding="utf-8", newline="\n"
        )
        with handle:
            json.dump(payload, handle, sort_keys=True)
        job_path = Path(handle.name)
        result.launches += 1
        try:
            proc = subprocess.run(
                [exe, str(WORKER_PATH), str(job_path)],
                cwd=str(cwd),
                env=env,
                capture_output=True,
                timeout=wall_timeout_s,
                check=False,
            )
            stdout, stderr, returncode, hard_timeout = (
                proc.stdout,
                proc.stderr,
                proc.returncode,
                False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            returncode, hard_timeout = None, True
        finally:
            job_path.unlink(missing_ok=True)
        last = start - 1
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if "import_error" in record:
                result.import_error = record["import_error"]
                return result
            if "i" in record:
                index = int(record["i"])
                result.records[index] = record
                last = max(last, index)
        if n_items == 0:
            break
        next_start = last + 1
        if next_start >= n_items:
            break
        if returncode != EXIT_TIMEOUT or hard_timeout:
            outcome = "HARD_TIMEOUT" if hard_timeout else "WORKER_CRASH"
            tail = stderr.decode("utf-8", errors="replace")[-STDERR_TAIL:]
            result.records[next_start] = {
                "i": next_start,
                "worker_failure": outcome,
                "returncode": returncode,
            }
            result.crashes.append(
                {
                    "item": next_start,
                    "outcome": outcome,
                    "returncode": returncode,
                    "stderr_tail": tail,
                }
            )
            next_start += 1
        start = next_start
    return result
