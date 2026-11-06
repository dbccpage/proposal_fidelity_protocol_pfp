# WF17: Witnessed-difference programme

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF10](../wf10_local_to_global_obstruction_certificate/README.md), [WF11](../wf11_dual_certificate_synthesis/README.md).

**Goal:** Each claimed difference has a checked witness and each equivalence a checked certificate.

## How it works

1. State two artifacts and the claimed difference or equivalence
2. Require a witness for a difference and a certificate for an equivalence
3. Pair every theorem with countermodels
4. Host checks witnesses on finite instances

## The check

Host check: witness / countermodel checker.

- `behavioral equivalence: a bisimulation relation B with (p, q) in B and matching transitions`
- `Fenchel-Rockafellar: inf_x f(x) + g(Ax) = sup_y -f^*(A^T y) - g^*(-y) under the stated qualification`
- `Cech gluing obstruction lives in the first Cech cohomology of the cover`

## Where it comes from

Sources: 0000170-0000187.

Eighteen planned capsules (W01-W18): behavioral equivalence, cochain quotients, Cech gluing, Fenchel-Rockafellar duality, LGGR I-VI, countermodels CE1-CE5; none dispatched.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000170/`](pilots/pilot_0000170/) — pilot_0000170 — W01 Retention Packet Behavioral Equivalence & Event Structures
- [`pilots/pilot_0000171/`](pilots/pilot_0000171/) — pilot_0000171 — W02 Discrete Cochain Quotients & Matroid Exact LP Circulation
- [`pilots/pilot_0000172/`](pilots/pilot_0000172/) — pilot_0000172 — W03 Gauge Holonomy, Cellular Sheaves & Double Category Descent
- [`pilots/pilot_0000173/`](pilots/pilot_0000173/) — pilot_0000173 — W04 Event Poset Adequacy & Stable Atomic-Mass Valuations
- [`pilots/pilot_0000174/`](pilots/pilot_0000174/) — pilot_0000174 — W05 Observer Category, Cellular Sheaves & Cech Gluing Obstructions
- [`pilots/pilot_0000175/`](pilots/pilot_0000175/) — pilot_0000175 — W06 Compositional Measurement Uncertainty & Affine Error Propagation
- [`pilots/pilot_0000176/`](pilots/pilot_0000176/) — pilot_0000176 — W07 Provenance Semirings, Path Aggregation & Lumpability Partitions
- [`pilots/pilot_0000177/`](pilots/pilot_0000177/) — pilot_0000177 — W08 Operational Probabilistic Theories, Effect Algebras & Contextuality
- [`pilots/pilot_0000178/`](pilots/pilot_0000178/) — pilot_0000178 — W09 Markov Categories, Terminal Profile Transport & Deontic Authority
- [`pilots/pilot_0000179/`](pilots/pilot_0000179/) — pilot_0000179 — W10 Primitive Difference Axiomatics, Evaluation Preorders & Triad Diagnostics
- [`pilots/pilot_0000180/`](pilots/pilot_0000180/) — pilot_0000180 — W11 L1-Native Cohomology & Exact Fenchel-Rockafellar Duality Solvers
- [`pilots/pilot_0000181/`](pilots/pilot_0000181/) — pilot_0000181 — W12 Local Green Global Red (LGGR I–III): Evaluated Path Kernels & Gluing
- [`pilots/pilot_0000182/`](pilots/pilot_0000182/) — pilot_0000182 — W13 Local Green Global Red (LGGR IV–VI): Chromatic Obstruction & Adjoint Probing
- [`pilots/pilot_0000183/`](pilots/pilot_0000183/) — pilot_0000183 — W14 Product Projections, Oblique Subspaces & Exact Short-Time Defect Bounds
- [`pilots/pilot_0000184/`](pilots/pilot_0000184/) — pilot_0000184 — W15 Vector Stalks & Quantum Density Geometries under Schatten-1 Trace Bounds
- [`pilots/pilot_0000185/`](pilots/pilot_0000185/) — pilot_0000185 — W16 M-Compatible Gauge Classification & Bounded-Linear Invariants
- [`pilots/pilot_0000186/`](pilots/pilot_0000186/) — pilot_0000186 — W17 SO(k)-Invariant Gauge Classification, Rigidity & J_{2,1} Separation
- [`pilots/pilot_0000187/`](pilots/pilot_0000187/) — pilot_0000187 — W18 Coordinate-Wise Additivity, Orbit-Weighted Rigidity & Countermodels CE1–CE5

## Team

Pattern `research_cell`: deep_researcher ×2 (opus); adversary ×1 (fable); coder ×2 (sonnet); host_checker ×1 (none).

Boost: when countermodel found: claim is narrowed or withdrawn; opus restates it once (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf17) · [machine-readable entry](../dag/workflow_dag.json)
