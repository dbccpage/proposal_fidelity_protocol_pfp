# Symbol Game Challenge and Demos Findings

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

> **Source check (2026-10-20, pin `c419cc6beb`).** The files indexed here, and this readme, are copies of the notes in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/) with a `level_` prefix; the C043 note and the three hub files differ from their twins only in paths. Links to `projects/` were repointed: challenge packages now live under [`pfp/tests/demo_004/`](../../../../pfp/tests/demo_004/), and the FSP and MUB(6) estates under `atlas/coda_atlas/F004_papers/008_fsp/` and `010_mub6/`. The collection's `verification/residuals.md`, the `_intelligence/` run folders and packages for C051 to C055 and C059 are not found at the pin. Phase-3 scoring receipts are retained only for C043 and C044 (reference solver only); model matrix records are retained for C045 to C050, C056 and C058.

> **Correction notice (2026-09-28).** Many figures in this document were corrected or
> withdrawn when Papers 003, 006, 008, 009 and 010 of this collection, and the
> meron-cluster benchmark paper in `atlas/coda_atlas/F004_papers/008_fsp/000_meron_sign_problem`,
> were revised against the retained evidence. For example, no 28-probe study exists;
> the failure catalog holds 61 entries, of which 5 are marked active and none is applied
> by code; the paired-bout "10/10" counted a field that is true in every record; and
> every passing run of the blind cluster benchmark followed a prompt that contained the
> answer. Where this document and a paper disagree, the paper and its change log are
> authoritative. The text below is kept unchanged as a historical working record.

> **AuthorityEffect:** None · Empirical Findings & Challenge Demonstrations Hub  
> **Location:** [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/)  
> **Parent Estate:** [`atlas/coda_atlas/F004_papers/015_pfp/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/)  
> **Related Source:** [`pfp/tests/demo_004/`](../../../../pfp/tests/demo_004/)

---

## Overview

This directory houses detailed empirical results, challenge evaluations, and operational demonstration findings for the Symbol Game / Proposal Fidelity Protocol (PFP) catalog:

- **Canonical Master Retrospectives & Comprehensive Findings:**
  - [**`c046_space_bunny_and_knuth_bendix_findings.md`**](level_c046_space_bunny_and_knuth_bendix_findings.md): Empirical report on Challenge C046 (Knuth-Bendix Completion & Joinability Certificates) evaluating first-order term rewriting confluence under Lexicographic Path Order (LPO).
  - [**`c045_space_bunny_and_knot_findings.md`**](level_c045_space_bunny_and_knot_findings.md): Empirical report on Challenge C045 (Knot Polynomials from Planar Diagrams) benchmarking Space Bunny Alpha, LLaMA 3.3 70B (80.0% pass rate; corrected 2026-10-20 from "70.0%" to match the C045 note and its retained matrix report), and LLaMA 3.1 8B across Jones and Alexander polynomial invariants.
  - [**`c044_space_bunny_and_group_findings.md`**](level_c044_space_bunny_and_group_findings.md): Empirical report on Challenge C044 (Finite group identification & isomorphism witnesses) evaluating Space Bunny Alpha, LLaMA 3.3 70B, and LLaMA 3.1 8B across GAP SmallGroups catalog tasks.
  - [**`c043_space_bunny_and_combinatorial_findings.md`**](level_c043_space_bunny_and_combinatorial_findings.md): Empirical report on Challenge C043 (Ramsey & Van der Waerden lower bounds) evaluating OpenRouter's new Space Bunny Alpha (50.0% zero-shot pass rate) against LLaMA 3.3 70B (10.0%) and LLaMA 3.1 8B (10.0%).
  - [**`symbol_game_challenge_and_demos_findings.md`**](level_symbol_game_challenge_and_demos_findings.md): Comprehensive master findings report consolidating all empirical demonstration matrices: FSP Meron Blind Cluster Recovery across 5 models, C017 Non-Abelian Lattice Holonomy Transfer (Arm 5 60% pass rate), C005 Hosted Decoding Controls (405B), and MUB(6) exact rational torus proofs.
  - [**`challenges_findings_and_updates.md`**](level_challenges_findings_and_updates.md): Master synthesis across the 134-item empirical execution corpus, 107 multi-round transitions, 28 retraction benchmark trials, and the 50-challenge corpus (C001–C050).
- **Further challenge notes (index added 2026-10-20):** each note carries its own notices and a dated source check.
  - [`level_c047_space_bunny_and_sequence_findings.md`](level_c047_space_bunny_and_sequence_findings.md): C047, recurrence discovery and Bareiss absence certificates.
  - [`level_c048_space_bunny_and_diophantine_findings.md`](level_c048_space_bunny_and_diophantine_findings.md): C048, ternary quadratic forms and Hilbert-symbol obstructions.
  - [`level_c049_space_bunny_and_category_findings.md`](level_c049_space_bunny_and_category_findings.md): C049, finite limits, colimits and adjunctions.
  - [`level_c050_space_bunny_and_equational_findings.md`](level_c050_space_bunny_and_equational_findings.md): C050, equational rewrite proofs and finite countermodels.
  - [`level_c051_space_bunny_and_lp_findings.md`](level_c051_space_bunny_and_lp_findings.md): C051, exact LP with dual and Farkas certificates.
  - [`level_c052_space_bunny_and_maxflow_findings.md`](level_c052_space_bunny_and_maxflow_findings.md): C052, max-flow with min-cut certificates.
  - [`level_c053_space_bunny_and_bareiss_findings.md`](level_c053_space_bunny_and_bareiss_findings.md): C053, fraction-free inversion and null vectors.
  - [`level_c054_space_bunny_and_linear_systems_findings.md`](level_c054_space_bunny_and_linear_systems_findings.md): C054, exact linear systems with inconsistency witnesses.
  - [`level_c055_space_bunny_and_assignment_findings.md`](level_c055_space_bunny_and_assignment_findings.md): C055, assignment with dual potentials and Hall violators.
  - [`level_c056_space_bunny_and_dfa_findings.md`](level_c056_space_bunny_and_dfa_findings.md): C056, DFA minimization and distinguishing words.
  - [`level_c057_space_bunny_and_sorting_network_findings.md`](level_c057_space_bunny_and_sorting_network_findings.md): C057, sorting networks under the 0-1 principle.
  - [`level_c058_space_bunny_and_superoptimization_findings.md`](level_c058_space_bunny_and_superoptimization_findings.md): C058, straight-line bit-vector superoptimization.
  - [`level_c059_space_bunny_and_sql_findings.md`](level_c059_space_bunny_and_sql_findings.md): C059, SQL under three-valued logic.
- **Challenge Retrospectives & Benchmarks:** Systematic empirical assessments across challenge domains:
  - `a_mechanism` (C001–C010): Attention steering, key masking, hosted decoding controls.
  - `b_cohomology` (C011–C020): Cellular sheaves, discrete Hodge decompositions, cycle-rank ladders.
  - `c_quantum` (C021–C030): Stabilizer ground-state solvers, code distance bounds, CSS codes.
  - `d_physics_mtheory` (C031–C040): Anomaly-free chiral charge assignments, Lie algebra multiplicities.
  - `e_formal_math` (C041–C050): SAT certificate verifiers, Lean 4 proof kernels, group isomorphisms.
- **Demonstration Findings:** Empirical run transcripts, mutation testing evidence, and cross-host parity checks.
