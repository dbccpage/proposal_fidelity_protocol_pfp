---
pattern_id: HP_RS_007
name: explicit_boundary_completion
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
dual_pattern: ap_rs_007_assumed_boundary_completion
language: rust
authority_effect: None
---

# Helpful Pattern: Explicit Bounded Completion (`HP_RS_007`)

## Conditions and construction

Use at the concrete boundaries identified by
[AP_RS_007](../../anti/rust/ap_rs_007_assumed_boundary_completion.md):

1. **Process confinement:** on Windows, create suspended, assign the configured
   Job Object, then resume. Fail closed and terminate/close owned handles when
   any setup step fails. Check handle ownership at every FFI operation.
2. **Capture:** require a successful stdout/stderr reader result before reporting
   successful completion. EOF may outlive the parent through descendants. Bound
   collection by the declared run deadline and preserve explicit capture errors,
   timeouts and overflow outcomes. Never turn missing output into empty success.
3. **Exact phase:** for supported dyadic order `n = 2^m` with `m <= 3`, reduce
   `power.rem_euclid(n)` before multiplying by `24 / n`, or widen before reduction.
   This makes the intermediate product bounded; do not widen only after overflow.
4. **Replay:** use ordered maps or explicit canonicalization at final serialization.
   Compare final bytes from equal report data inserted in different orders; sort
   diagnostic group keys when their order is observable.

## Actual implementation bindings

- `core_sandbox/src/windows.rs`: suspended launch/assignment/resume and capture.
- `core_sandbox/tests/windows_capture.rs`: delayed overflow, pipe timeout,
  bounded descendant output, ordinary output and nonzero exit controls.
- `core_quantum_physics/src/phase_estimation.rs`: supported roots, signed
  extrema and periodicity against exact exponent reduction.
- `auto_p/bin/autop_check.rs`: serialized report insertion-order independence.

Paths are relative to `engine/crates_rs/`. Inspect test bodies and run the
smallest relevant filters against current candidate bytes. Existing test names
or a previous PASS are not proof of a new change. Use the primary shared Cargo
cache, `-j 1` and sequential targeted checks; no full canonical CI is implied.

## Limits

The Windows checks do not establish confinement on every OS or enclosing job.
Dyadic checks cover the supported root orders and integer carrier. Stable map
ordering does not stabilize arbitrary volatile report values. Keep the public
outcome schema and benign behavior intact while repairing the failure path.
