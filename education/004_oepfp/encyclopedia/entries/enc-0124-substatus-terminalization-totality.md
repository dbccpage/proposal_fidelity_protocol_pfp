---
id: ENC-0124
kind: lemma
name: "Sub-Status Terminalization Totality and Decidability"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "symbol_game_math_spine.md math_spines_v002 §3.1 'Lemma (unnamed)'"
uses: []
lean_status: MECHANIZED-PARTIAL
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_terminalizer_policy.lean"
  - "PaperER007.validator_report_exhaustive"
  - "PaperER007.terminalizer_total"
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0124 — Sub-Status Terminalization Totality and Decidability

## Statement

If \(\tau\) is defined for every sub-status, terminalization is total
and decidable.

## Hypotheses

The source fixes the terminal set and terminalizer immediately above the
lemma, verbatim:

Let the terminal set be:

```text
TerminalClass = {Certificate, Refusal, Repair, OracleNeeded}
```

Let `SubStatus` be the finite set of validator-specific statuses. A
terminalizer is a function:

\[
\tau:\mathrm{SubStatus}\to \mathrm{TerminalClass}.
\]

Required examples:

```text
ValidCertificate      -> Certificate
MalformedPacket       -> Refusal
UnsupportedSemantics  -> OracleNeeded
Suboptimal            -> Repair
TerminalMismatch      -> Repair
TiePolicyMissing      -> Repair
BoundaryMutation      -> deterministic terminal selected by declared license policy
```

## Proof

`SubStatus` is finite and \(\tau\) is a finite lookup table. Lookup
terminates. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| totality + decidability of finite-lookup terminalization over `SubStatus` | local | none identified | NOT-STARTED |

## Notes

- The lemma is unnamed in the source; the entry name is editorial (the §3.1
  section title is "Sub-Status to TerminalClass Surjection").
- The source follows the proof with a caveat, verbatim: "This is a
  normalization rule, not a theorem about truth."
- The §3 split note: "The *abstract* terminalizer consistency theorem (total /
  deterministic / consistent first-match policy) is collapsed to canonical
  §VII.1 (Thm VII.1, Terminalizer Policy Consistency)" = [[ENC-0097]]; "The
  `SubStatus→Terminal` surjection lemma (§3.1) ... [is] **kept net-new** —
  canonical §VII.1 states only the general theorem and does not reproduce
  them." This lemma concerns the SG-local `SubStatus`-indexed lookup table,
  not the canonical first-match guard table of ENC-0097.

- PaperER007 reconciliation (2026-07-19): PaperER007 proves totality for its finite ValidatorReport model. It does not identify that carrier with every SubStatus implementation or prove a runtime serialization theorem. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §3.1 "Sub-Status
  to TerminalClass Surjection" under §3 "Terminal Status Normalization"
  (statement, hypotheses context, and proof copied verbatim). Original header
  line:
  `**Lemma.** If \(\tau\) is defined for every sub-status, terminalization is total`

## Changelog

- 2026-06-09: ENC-0124 created (M2 E2 satellite extraction).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
