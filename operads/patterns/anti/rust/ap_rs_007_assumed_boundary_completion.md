---
pattern_id: AP_RS_007
name: assumed_boundary_completion
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "unknown"
dual_pattern: hp_rs_007_explicit_boundary_completion
language: rust
authority_effect: None
---

# Anti-Pattern: Assumed Boundary Completion (`AP_RS_007`)

## Failure and witnesses

A local success is promoted to a stronger boundary guarantee without checking
the intervening operation. The Rust estate audit observed four concrete forms:

| Assumption | Consequence | Deciding check |
| --- | --- | --- |
| Parent exit implies output capture finished | An inherited pipe timeout defaults to empty successful output, dropping a delayed 4,096-byte overflow under a 64-byte limit. | Native delayed-descendant capture test. |
| Job assignment after spawn confines all execution | Candidate code can execute before restrictions apply; earlier descendants are not established as members by later parent assignment. | Observe the child suspended before assignment, then resume only after assignment succeeds. |
| Reduction makes an earlier fixed-width multiply safe | For valid `m=3`, `i64::MAX * 3` panics with overflow checks or yields exponent 5 instead of 21 without them. | Compare extrema against widened/reduced exact arithmetic. |
| Sorting console output stabilizes report JSON | Serialized `HashMap` fields retain randomized iteration order. | Compare final report bytes from different insertion orders. |

The historical native probes reproduced capture loss and exponent overflow.
The initial job-ordering and JSON findings were source-confirmed, not independent
exploit executions. Preserve that distinction when citing the original review.

## Repair and controls

Establish the complete precondition before execution or success. Do not default
an absent capture to success. Create suspended, assign the job, then resume.
Reduce a valid exponent before multiplying or widen safely. Canonicalize each
serialized map rather than only a separate display projection.

Benign controls preserve ordinary empty output, bounded descendant output,
nonzero exit codes, small/negative exponents and reports with equal values in
different insertion orders. Test the actual consuming implementation. These
finite regressions do not certify every platform, process tree or artifact.

See [HP_RS_007](../../helpful/rust/hp_rs_007_explicit_boundary_completion.md),
[the Rust review skill](../../../skills/techne-code-rust-code-reviewer/SKILL.md)
and the [capture antibody candidate](../../../antibodies/specs/anti_rust_capture_completion_loss.yaml).
