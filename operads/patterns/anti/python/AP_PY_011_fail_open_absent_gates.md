---
pattern_id: AP_PY_011
name: fail_open_absent_gates
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_011_refuse_when_gates_absent
language: python
authority_effect: None
---

# Anti-Pattern: Fail-Open Absent Gates (`AP_PY_011`)

## Description

A zero-residual halt with `gates is None` is reported as `TerminalStatus.AUTHORITY`. Absent gates are treated as permission.

## Detection Signature

- A `gates is None` branch builds `TerminalOutcome(status=TerminalStatus.AUTHORITY, ...)`.
- The 2026-10-07 repair note for package 028 recorded this at residual 0. The live `detect_counterfeit_descent` returns `NON_AUTHORITY_HALT` with `RefusalReason.NON_AUTHORITY_TERMINAL` on that branch.
- Nonzero residual is refused before the gate branch. It is not this pattern.

## Hazard & Failure Mode

- A halted trace with residual 0 and no gate stack receives the authority terminal.
- A test that only covers surface signs can leave that branch unexercised.

## Dual Healthy Pattern

See [HP_PY_011_refuse_when_gates_absent](../../helpful/python/HP_PY_011_refuse_when_gates_absent.md).
