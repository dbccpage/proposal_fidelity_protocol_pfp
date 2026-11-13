---
pattern_id: HP_PY_016
name: fail_closed_test_suite_disk_verification
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_017_verification_chain_hallucination_phantom_tests
language: python
authority_effect: None
---

# Healthy Pattern: Fail-Closed Test Suite Disk Verification (`HP_PY_016`)

## Description

Verifying agents and gate orchestrators must verify that cited test directories exist on disk in the active worktree before executing test commands or recording verification receipts. Pass labels require actual host execution and positive non-zero collected test counts.

## Implementation Pattern

```python
from pathlib import Path
import subprocess

def run_verified_suite(test_dir: Path) -> dict:
    if not test_dir.is_dir():
        return {
            "status": "REFUSED",
            "reason": f"PHANTOM_TEST_SUITE: Directory does not exist on disk: {test_dir}",
        }
    cmd = ["pytest", str(test_dir), "-q"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"status": "FAIL", "stderr": proc.stderr}
    return {"status": "PASS", "stdout": proc.stdout}
```

## Resolution

- Prevents transitive propagation of phantom test suites across multi-agent swarms.
- Ensures all claimed test counts correspond to executed code on disk.
