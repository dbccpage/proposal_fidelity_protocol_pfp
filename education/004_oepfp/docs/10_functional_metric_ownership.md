---
documentation_contract: symbol-game-documentation/v1
title: Functional metric ownership
kind: reference
audience:
- engineers
- coding-agents
status: active
maturity: legacy-source
claim_status: source-legacy
authority_effect: "None"
source_paths:
- omega_engine/crates_rs/omega_symbol_game/src/functional.rs
- omega_engine/crates_rs/omega_functional/src
- omega_engine_pfp/domain/solvers/retraction.py
source_revision: c419cc6beb
prerequisites: []
verification: py -3.12 -m omega_engine_pfp.scripts.docs_integrity validate
aliases: []
related: []
last_verified: 2026-10-20
verification_scope: paths in the inventory table and named refusal codes checked against tracked source; no build or test run
---


# 10. Functional Metric Ownership & Sovereign Boundaries

Named Phi1, Gamma2, and Xi calculations belong only in
`omega_engine/crates_rs/omega_functional/src`. A proposal score, parity
fraction, residual count, model confidence, or local defect is not one of
these functionals and must not be relabeled as one. Python may transport or
display a Rust-issued result once an adapter binds it to its input and
receipt. The one adapter that does this is `ExactFunctionalPort.evaluate`,
backed by the native `functional_evaluate` action (below).

## Active Symbol Game boundary

`run-turn`, `run-bout`, `run` and the top-level `--prompt` alias return
`REFUSED: RUST_FUNCTIONAL_REQUIRED` before writing output. They need a live
provider or Xi, which no Rust action serves yet. The Python `ProblemRunnerUseCase`, four
`SymbolGameRunnerUseCase` run methods, `CochainProjector.project` and seven
bridge `real_evaluators` methods raise the same typed refusal before
calculating a named value. A caller
receives a reason and a path to the sole owner instead of a synthetic zero
or a floating estimate. Historical receipt and type readers remain
importable. The finite gauge workbench uses an explicitly named parity
match score and does not issue Phi1, Gamma2, or Xi.

The DDC triad in `domain/ddc/triad.py` now refuses named calculations through
`FunctionalBoundaryUnavailable`. Its former Python LP, face-curl, and
lexicographic-edge computations were incompatible with this boundary; its Xi
in particular was not the density-distance Xi in `omega_functional`.

## The Rust action, and what it revived

`functional_evaluate` (`omega_engine/crates_rs/omega_symbol_game/src/functional.rs`)
accepts an exact complex `d0`, `d1` and a degree-one residual as canonical
rational strings. It refuses `d1 d0 != 0` (`CHAIN_LAW_VIOLATED`), any JSON float
(`FLOAT_FORBIDDEN`), non-canonical rationals and oversize input
(`BUDGET_UNKNOWN`) before evaluating. It returns Phi1 from a verified
`omega_functional::Phi1Functional` certificate, Gamma2 from
`Gamma2Functional::try_compute_exact_quotient` on the same residual, and the
class from `classify_exact`, plus an `input_digest` binding the receipt to the
request. `functional_verify` re-evaluates a request and names every receipt
field it does not reproduce. The positive, invalid and UNKNOWN cases are pinned
in `omega_engine/crates_rs/tests/omega_symbol_game/invoke_contract.rs`.

Gamma2 here is `||d1 x||_1`: the FOC quotient with no second-stage repairs
(`a2 = 0`), and every receipt says so in `second_stage_repairs`.

The OEOS seam recomputes `input_digest` and refuses a mismatch as
`HOST_INPUT_BINDING_MISMATCH`. `gate11-self`, `gate11-ingest` and
`gate11-project` now take every Phi1, Gamma2 and class through
`RustExactEngineAdapter.evaluate`; Gate 11 compares the fixture's claims against
those receipts and computes none of them.

## Remaining calculators outside this boundary

These are source locations to migrate or archive before claiming the rule
holds across the entire repository:

> **Path check (2026-10-20, pin `c419cc6beb`).** The top-level `research/` tree no longer exists, and three `omega_solvers` file names changed. Current homes found by file name:
>
> | Path in the table below | Current tracked home |
> | --- | --- |
> | `research/papers/001_the_symbol_game/code/symbol_game_governor.py` | [`015_pfp/001_.../code/symbol_game_governor.py`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/symbol_game_governor.py) (`compute_exact_phi_1` line 435, `compute_phi_1` line 648) |
> | `research/mssn_sn_tower/demos/demo_1/run_*.py` | No live copy found. |
> | `research/mssn_sn_tower/demos/demo_2/certificate_gate.py` | Retained only inside the recreated-run evidence of `015_pfp/021_recreated_demos_and_proposal_fidelity_evidence/`; separate `certificate_gate.py` files exist in [`015_pfp/001_...`](../../../../omega_engine_atlas/coda_atlas/F004_papers/015_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/certificate_gate.py) and `015_pfp/002_...`. |
> | `research/papers/012_mutually_unbiased_bases/code/mub_verify/l1_governor.py` | [`010_mub6/code/mub_verify/l1_governor.py`](../../../../omega_engine_atlas/coda_atlas/F004_papers/010_mub6/code/mub_verify/l1_governor.py); `compute_phi1` (line 287) imports `compute_graph_phi1` from `omega_engine_woland.infrastructure.providers.adapters.native_functional`. |
> | `omega_solvers/src/phi1_l1_boundary_solver.rs` | [`solver_lp_phi1_boundary.rs`](../../../../omega_engine/crates_rs/omega_solvers/src/solver_lp_phi1_boundary.rs), which imports `Phi1Functional` and `VerifiedExactPhi1` from `omega_functional`. |
> | `omega_solvers/src/exact_weighted_l1_lp.rs`, `phi1_gtoc_adapter.rs` | Not present under those names. Candidates by name: `solver_lp_phi1_quotient.rs`, `solver_graph_phi1_distance.rs`, `solver_cohomology_quotient_phi1.rs`. Not confirmed as renames. |
> | `retraction.py` `compute_obstruction_score` and `ObstructionScore` | Still present. `ObstructionScore` is now defined once, in `domain/models.py` line 204, with exact `Fraction` fields `phi_1` and `gamma_2`; `domain/bridge/symbol_game_models.py` imports it. The values are still local defect scores computed in Python under the reserved names, so the naming problem remains even though the "float" description below is out of date. |

| Source | Current computation | Scope |
| --- | --- | --- |
| `research/papers/001_the_symbol_game/code/symbol_game_governor.py` | `compute_exact_phi_1` and `compute_phi_1` solve and verify a Python weighted graph obstruction. | Frozen paper reproduction code; do not import into the new CLI. |
| `research/mssn_sn_tower/demos/demo_1/run_*.py` | Per-round scripts assign Phi1/Gamma2/Xi trace values, sometimes sentinels. | Historical demo runners; not a canonical metric backend. |
| `research/mssn_sn_tower/demos/demo_2/certificate_gate.py` and `run_demo2_r*.py` | Python Gamma2 and hardcoded or scenario-specific Phi1. | Historical demo runners; not a canonical metric backend. |
| `research/papers/012_mutually_unbiased_bases/code/mub_verify/l1_governor.py` | `compute_phi1` hands the graph to the native `omega_functional` binary through `native_functional.py`. Several MUB6 Python research scripts consume these values. | MUB6 research path; the Python `symbol_game_host.py` was retired on 2026-09-25 in favour of `omega_mub::omega_native::symbol_game_host`. |
| `omega_engine/crates_rs/omega_solvers/src/phi1_l1_boundary_solver.rs` | `solve_phi1` returns an objective and witness, and replays them as an exact certificate through `omega_functional::Phi1Functional` before returning. | Canonical Rust Phi1 boundary solver; `omega_mub`'s former copy was removed on 2026-09-25. |
| `omega_engine_pfp/domain/solvers/retraction.py` `compute_obstruction_score`, and the `phi_1`/`gamma_2` fields of both `ObstructionScore` classes (`domain/models.py`, `domain/bridge/symbol_game_models.py`) | Float boundary-violation and holonomy distances stored under the reserved names Phi1 and Gamma2. They are local defect scores, not these functionals. | Regime search. Renaming the fields touches about 20 modules and is queued as its own change. |
| `omega_engine/crates_rs/omega_solvers/src/exact_weighted_l1_lp.rs` and `phi1_gtoc_adapter.rs` | Search for primal/dual witnesses and return candidate objective values. | Rust solver dependency; the functional crate must calculate or verify any value labeled Phi1 before publication. |

This inventory is bounded to the searched Symbol Game, MUB6, Paper 001,
and Demo 1/2 source trees. It is not a claim that every repository-local
calculator has been migrated. In particular, disabling the standalone
MUB6 and paper reproduction interfaces without a replacement would remove
existing research replay. Each path rejoins live search only through
`ExactFunctionalPort.evaluate`, one path at a time; density states (Xi) still
have no Rust action.
