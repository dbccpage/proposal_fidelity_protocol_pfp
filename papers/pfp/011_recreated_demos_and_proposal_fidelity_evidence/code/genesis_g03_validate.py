"""Record only the focused G03 tests and lint process; no oracle rerun."""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g03"


def record(stem: str, argv: list[str]) -> None:
    start = time.perf_counter()
    process = subprocess.run(argv, cwd=PAPER, capture_output=True, check=False, timeout=600)
    (AREA / (stem + "_stdout.txt")).write_bytes(process.stdout)
    (AREA / (stem + "_stderr.txt")).write_bytes(process.stderr)
    receipt = {"argv": argv, "cwd": str(PAPER), "returncode": process.returncode,
               "seconds": time.perf_counter() - start,
               "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(process.stderr).hexdigest()}
    (AREA / (stem + "_process.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(stem, process.returncode, process.stdout.decode("utf8", "replace"), flush=True)
    if process.returncode:
        raise ValueError("G03_FOCUSED_VALIDATION_FAILED:" + stem)


if __name__ == "__main__":
    record("focused_tests", ["py", "-3.12", "-B", "-X", "pycache_prefix=docs/history_recovery/g03/runtime_cache_tests_2",
                            "-m", "pytest", "code/tests/test_paper011_genesis_g03.py", "-q",
                            "--junitxml=docs/history_recovery/g03/focused_tests_junit.xml",
                            "--basetemp", "C:/Users/a343o/AppData/Local/Temp/paper011-g03-tests-20261002-2"])
    record("ruff", ["py", "-3.12", "-B", "-m", "ruff", "check", "code/genesis_g03_adapter.py", "code/genesis_g03_replay.py",
                    "code/genesis_g03_key_bridge.py", "code/genesis_g03_finalize.py", "code/genesis_g03_pack.py",
                    "code/genesis_g03_validate.py", "code/tests/test_paper011_genesis_g03.py"])
