---
id: ENC-0127
kind: theorem
name: "Concrete Terminalizer Table Consistency"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "symbol_game_math_spine.md trunk Part III §3.3 'Theorem (Concrete Terminalizer Table Consistency)'"
uses: []
lean_status: MECHANIZED-PARTIAL
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_terminalizer_policy.lean"
  - "PaperER007.validator_report_exhaustive"
  - "PaperER007.terminalizer_total"
  - "PaperER007.terminalizer_deterministic"
  - "PaperER007.certificate_implies_every_gate"
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0127 — Concrete Terminalizer Table Consistency

## Statement

If each
`ValidatorReport` constructor is produced only by its corresponding validator
predicate, and the terminalizer applies the first-match table above, then the
terminalizer is total, deterministic, and consistent with checked packet state.

## Hypotheses

The "first-match table above" is the following, verbatim from the source
section:

> Let `ValidatorReport` be a finite tagged union whose constructors are disjoint.
> The terminalizer policy is the following first-match table:
>
> | Priority | Validator report predicate | Terminal |
> |---:|---|---|
> | 1 | `ParseError` or `SchemaInvalid` | `Refusal` |
> | 2 | `UnsupportedSemantics` with allowed oracle route | `OracleNeeded` |
> | 3 | `EvidenceCeilingExceeded` | `Repair` |
> | 4 | `ForbiddenMutation` or unlicensed carrier/basis/skeleton mutation | `Refusal` |
> | 5 | `TiePolicyMissing`, `TerminalMismatch`, `Suboptimal`, missing witness, or repairable boundary violation | `Repair` |
> | 6 | `LocalInvalid` with no repair witness class | `Refusal` |
> | 7 | `LocalGreen ∧ GlobalGreen ∧ TerminalClaimOK` | `Certificate` |
> | 8 | any otherwise unmatched report | `OracleNeeded` if an oracle route is declared, otherwise `Refusal` |

## Proof

`ValidatorReport` is finite. The table has a fallback row, so every
report matches at least one row. First-match evaluation returns exactly one row
for each report, so the terminalizer is deterministic. For rows 1-6 and 8, the
terminal is non-certifying and records the validator predicate that failed or
the missing local verifier capability. For row 7, the row predicate is exactly
`LocalGreen ∧ GlobalGreen ∧ TerminalClaimOK`, so `Certificate` is emitted only
when local replay, global boundary verification, and terminal consistency all
hold. Therefore no emitted terminal contradicts the checked packet state.
\(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| totality, determinism, and checked-state consistency of the concrete 8-row first-match terminalizer table | local | none identified | NOT-STARTED |

## Notes

- The source marks this section "**KEEP — net-new.** The concrete first-match
  8-row policy table and its table-specific consistency theorem/corollary are
  not reproduced in canonical §VII.1 (which states only the abstract theorem)."
  The abstract theorem is [[ENC-0097]] Terminalizer Policy Consistency; this is
  its realization-instance table.
- The source adds after the table: "The table is intentionally terminal-only.
  It does not decide customer-facing admissibility and does not upgrade
  evidence level."

- PaperER007 reconciliation (2026-07-19): PaperER007 mechanizes the finite first-match routing model and proves that Certificate implies its three checked gates. It does not prove that production validators emit only semantically correct constructors, and Certificate remains host routing rather than authority. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §3.3 "Concrete Terminalizer Policy
  Table" (statement and proof copied verbatim). Original header line:
  `**Theorem (Concrete Terminalizer Table Consistency).** If each`

## Changelog

- 2026-06-09: ENC-0127 created (M2 E2 satellite extraction).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
