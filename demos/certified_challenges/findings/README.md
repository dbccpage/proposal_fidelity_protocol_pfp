# Symbol Game Challenge and Demos Findings

> **Moved (2026-10-27).** This folder was `papers/symbol_game_challenge_and_demos_findings/`.
> It now sits next to the runnable challenge packages in `demos/certified_challenges/`.
> The notes are unchanged; their links still point into the source repository and do
> not resolve here. The wiki's `Test-*` pages describe the checkers without the model
> scores.

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the notice of 2026-09-28. The genesis rows of the
> master findings note are quarantined, the C041 and C042 model-matrix findings have
> no retained raw data, and every `PASS_TO_MASTER` label in these notes is a reference
> self-score, not a result for any model. Each note carries its own notice. The audit
> behind these notices is recorded in the collection's `verification/residuals.md`,
> section 8.

> **Correction notice (2026-09-28).** Many figures in this document were corrected or
> withdrawn when Papers 003, 006, 008, 009 and 010 of this collection, and the
> meron-cluster benchmark paper in `projects/fsp/meron_sign_problem`,
> were revised against the retained evidence. For example, no 28-probe study exists;
> the failure catalog holds 61 entries, of which 5 are marked active and none is applied
> by code; the paired-bout "10/10" counted a field that is true in every record; and
> every passing run of the blind cluster benchmark followed a prompt that contained the
> answer. Where this document and a paper disagree, the paper and its change log are
> authoritative. The text below is kept unchanged as a historical working record.

> **AuthorityEffect:** None · Empirical Findings & Challenge Demonstrations Hub  
> **Location:** [`atlas/coda_atlas/symbol_game/symbol_game_challenge_and_demos_findings/`](../../../../../../atlas/coda_atlas/symbol_game/symbol_game_challenge_and_demos_findings/)  
> **Parent Estate:** [`atlas/coda_atlas/symbol_game/`](../../../../../../atlas/coda_atlas/symbol_game/)  
> **Related Source:** [`projects/mssn_sn_symgam/challenges/`](../../../../../../projects/mssn_sn_symgam/challenges/)

---

## Overview

This directory houses detailed empirical results, challenge evaluations, and operational demonstration findings for the Symbol Game / Proposal Fidelity Protocol (PFP) catalog:

- **Canonical Master Retrospectives & Comprehensive Findings:**
  - [**`c046_space_bunny_and_knuth_bendix_findings.md`**](c046_space_bunny_and_knuth_bendix_findings.md): Empirical report on Challenge C046 (Knuth-Bendix Completion & Joinability Certificates) evaluating first-order term rewriting confluence under Lexicographic Path Order (LPO).
  - [**`c045_space_bunny_and_knot_findings.md`**](c045_space_bunny_and_knot_findings.md): Empirical report on Challenge C045 (Knot Polynomials from Planar Diagrams) benchmarking Space Bunny Alpha, LLaMA 3.3 70B (70.0% pass rate), and LLaMA 3.1 8B across Jones and Alexander polynomial invariants.
  - [**`c044_space_bunny_and_group_findings.md`**](c044_space_bunny_and_group_findings.md): Empirical report on Challenge C044 (Finite group identification & isomorphism witnesses) evaluating Space Bunny Alpha, LLaMA 3.3 70B, and LLaMA 3.1 8B across GAP SmallGroups catalog tasks.
  - [**`c043_space_bunny_and_combinatorial_findings.md`**](c043_space_bunny_and_combinatorial_findings.md): Empirical report on Challenge C043 (Ramsey & Van der Waerden lower bounds) evaluating OpenRouter's new Space Bunny Alpha (50.0% zero-shot pass rate) against LLaMA 3.3 70B (10.0%) and LLaMA 3.1 8B (10.0%).
  - [**`symbol_game_challenge_and_demos_findings.md`**](symbol_game_challenge_and_demos_findings.md): Comprehensive master findings report consolidating all empirical demonstration matrices: FSP Meron Blind Cluster Recovery across 5 models, C017 Non-Abelian Lattice Holonomy Transfer (Arm 5 60% pass rate), C005 Hosted Decoding Controls (405B), and MUB(6) exact rational torus proofs.
  - [**`challenges_findings_and_updates.md`**](challenges_findings_and_updates.md): Master synthesis across the 134-item empirical execution corpus, 107 multi-round transitions, 28 retraction benchmark trials, and the 50-challenge corpus (C001–C050).
- **Challenge Retrospectives & Benchmarks:** Systematic empirical assessments across challenge domains:
  - `a_mechanism` (C001–C010): Attention steering, key masking, hosted decoding controls.
  - `b_cohomology` (C011–C020): Cellular sheaves, discrete Hodge decompositions, cycle-rank ladders.
  - `c_quantum` (C021–C030): Stabilizer ground-state solvers, code distance bounds, CSS codes.
  - `d_physics_mtheory` (C031–C040): Anomaly-free chiral charge assignments, Lie algebra multiplicities.
  - `e_formal_math` (C041–C050): SAT certificate verifiers, Lean 4 proof kernels, group isomorphisms.
- **Demonstration Findings:** Empirical run transcripts, mutation testing evidence, and cross-host parity checks.
