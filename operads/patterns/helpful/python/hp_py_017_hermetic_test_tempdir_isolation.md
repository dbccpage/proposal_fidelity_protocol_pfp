---
pattern_id: HP_PY_017
name: hermetic_test_tempdir_isolation
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_018_test_induced_repository_state_mutation
language: python
authority_effect: None
---

# Healthy Pattern: Hermetic Test Tempdir Isolation (`HP_PY_017`)

## Description

All file-generating tests must execute in isolated temporary directories (`tmp_path`) and leave the repository git working tree completely clean.

## Implementation Pattern

```python
from pathlib import Path
import subprocess

def test_pipeline_export(tmp_path: Path):
    # Route all outputs strictly to tmp_path
    output_file = tmp_path / "output.json"
    generate_export(destination=output_file)
    assert output_file.exists()

def test_worktree_clean_after_run():
    # Assert repository working tree is untouched
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    assert status.stdout.strip() == "", f"Test suite dirtied worktree:\n{status.stdout}"
```

## Resolution

- Guarantees zero worktree contamination during test execution.
- Keeps release manifests and checksums stable across test runs.
