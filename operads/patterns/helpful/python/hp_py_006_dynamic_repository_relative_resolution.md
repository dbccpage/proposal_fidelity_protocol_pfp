---
pattern_id: HP_PY_006
name: dynamic_repository_relative_resolution
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_006_host_absolute_path_injection
language: python
authority_effect: None
---

# Healthy Pattern: Dynamic Repository-Relative Resolution (`HP_PY_006`)

## Description

Resolving filesystem locations dynamically relative to the executing module's anchor (`Path(__file__).resolve().parent`) or discovered repository boundary markers (`.git`, `pixi.toml`), ensuring all generated links and persistent references remain strictly portable across all hosts, developer machines, and worktrees.

## Structural Signature

```python
from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for parent in [p, *p.parents]:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[3]
```

In Markdown links, always use relative POSIX paths (e.g. `../../target_dir/`) rather than host-absolute `file:///` URLs.

## Remediation Applied

- Replaced static strings `file:///c:/Users/a343o/...` with dynamically computed relative POSIX paths via `os.path.relpath(target, file_dir).replace('\\', '/')`.
- Standardized documentation domain location pointers to relative current-folder targets (`.`).

## Verification Receipt

Checked by `test_rule_gate.py` (`R4_HOST_ABSOLUTE_LINK`) and repository link linters.
