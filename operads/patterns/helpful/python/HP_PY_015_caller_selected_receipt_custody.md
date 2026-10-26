---
pattern_id: HP_PY_015
name: caller_selected_receipt_custody
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_015_repository_default_live_receipt_output
language: python
authority_effect: None
---

# Healthy Pattern: Caller-Selected Receipt Custody (`HP_PY_015`)

## Description

Commands that generate live receipts require the caller to select their output
paths. Historical outputs stay in an explicit custody location with a pinned
source tree and are never selected automatically as present-run evidence.

## Structural Signature

```python
def get_receipt_path(output_dir: Path, filename: str) -> Path:
    if not filename or Path(filename).name != filename:
        raise ValueError("filename must be one nonempty relative path component")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename


parser.add_argument("--json-output", type=Path, required=True)
```

## Remediation Applied

- Use caller-selected paths for every live JSON, Markdown, or log receipt.
- Keep historical bytes under explicit receipt custody and bind that custody to
  a source commit and Git tree.
- Bind a live receipt to its command, source identity, scope, and verdict.
- Require an explicit receipt directory before evaluating freshness; a retained
  historical corpus is not a default claim about current source bytes.

## Falsifier and Limit

Reading a historical receipt is valid when the caller names that custody path
and states that the result is historical. Its existence alone does not prove a
current build, test, security, or promotion result.
