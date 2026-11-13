---
id: ENC-0084
kind: definition
name: 'Fidelity Predicate $F(s, P)$'
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.5"]
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "canonical_core_math_spine.md v1.5.2 §IV.2 'Definition IV.5'"
uses: []
lean_status: MECHANIZED-PARTIAL
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_fidelity_adequacy.lean"
  - "PaperER007.fidelity_clause_mem_all"
  - "PaperER007.replay_fidelity_clause_iff"
  - "PaperER007.replay_all_eight_fidelity_iff"
  - "PaperER007.constant_pass_detector_is_total"
  - "PaperER007.constant_pass_detector_not_adequate"
  - "PaperER007.eight_clause_fidelity_does_not_certify_constant_detector"
  - "PaperER007.eight_clause_fidelity_records_no_authority_expansion"
  - "PaperER007.detector_adequacy_rejects_constant_detectors"
  - "PaperER007.finite_bool_fidelity_adequacy_separation"
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0084 — Fidelity Predicate $F(s, P)$

## Statement

Given a finite typed seed $s$ and a finite typed packet $P$, the fidelity predicate $F(s, P) = 1$ iff all of the following hold:

1. **Task identity preservation:** $\mathrm{family} = \mathrm{family}' \wedge \mathrm{instance} = \mathrm{instance}' \wedge \mathrm{carrier} = \mathrm{carrier}'$.
2. **Constraint preservation:** $\mathrm{Norm}(\mathrm{constraints}) = \mathrm{Norm}(\mathrm{constraints}')$.
3. **Protected boundary preservation:** $\mathrm{protected\_boundary} = \mathrm{protected\_boundary}'$.
4. **Terminal target preservation:** $\mathrm{terminal\_target}' \subseteq T_s$.
5. **Evidence ceiling preservation:** $e'_P \le e_s$ (or $e'_P = e_s$ if exact).
6. **Oracle policy preservation:** $\mathrm{oracle\_policy} = \mathrm{oracle\_policy}'$.
7. **Allowed transform preservation:** $\mathrm{allowed\_transforms}' \subseteq \mathrm{allowed\_transforms}$.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| definition of the seven-clause fidelity predicate \(F(s, P)\) over finite typed seed/packet schemas | local | none identified | NOT-STARTED |

## Notes

- §IV.2 is titled "The Packet Fidelity Functor"; unprimed fields belong to the
  seed $s$, primed fields to the packet $P$ (source convention).

- PaperER007 reconciliation (2026-07-19): PaperER007 mechanizes a located eight-clause contract model and keeps detector adequacy as separate data. This is partial support for the broader fidelity definition: it does not certify a shipped detector or unrestricted semantic intent. AuthorityEffect remains None.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.2
  (statement copied verbatim; definition carries no status bracket).
  Original header line:
  `**Definition IV.5 (Fidelity Predicate $F(s, P)$).** Given a finite typed seed $s$ and a finite typed packet $P$, the fidelity predicate $F(s, P) = 1$ iff all of the following hold:`

## Changelog

- 2026-06-09: ENC-0084 created (M2 E1 extraction).
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
