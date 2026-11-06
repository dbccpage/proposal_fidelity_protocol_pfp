# WF13: Exact-domain capsule battery

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF7](../wf07_typed_refusal/README.md).

**Goal:** One checked answer or refusal per domain capsule.

## How it works

1. One catalog challenge becomes one capsule
2. A domain checker is registered before dispatch
3. One reply or typed refusal per capsule
4. Results stay per domain; no cross-domain average is claimed

## The check

Host check: per-domain registered checker.

- `stabilizer codes: generators commute iff their symplectic product is 0 mod 2`
- `U(1) anomaly freedom: sum_i q_i = 0 and sum_i q_i^3 = 0 over the declared charges`
- `Regge deficit: epsilon = 2 pi - sum of dihedral angles at a hinge`
- `commutator [g, h] = g^-1 h^-1 g h, checked in the declared finite group`

## Where it comes from

Sources: 0000065-0000114, 0000177, 0000176, 0000178, 0000187.

Fifty planned single-capsule pilots, one per catalog challenge, each naming a domain checker id; none was dispatched.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000055/`](pilots/pilot_0000055/) — pilot_0000055 — C011 Cycle-Rank Ladder: Minimum-L1 Coboundary Repair
- [`pilots/pilot_0000056/`](pilots/pilot_0000056/) — pilot_0000056 — C012 Cellular Sheaf Cohomology H^0 and H^1
- [`pilots/pilot_0000057/`](pilots/pilot_0000057/) — pilot_0000057 — C013 Integral Homology with Torsion and Smith Normal Form Certificates
- [`pilots/pilot_0000058/`](pilots/pilot_0000058/) — pilot_0000058 — C014 Exact Discrete Hodge Decomposition
- [`pilots/pilot_0000059/`](pilots/pilot_0000059/) — pilot_0000059 — C015 Persistent Homology Barcodes with Reduction Certificates
- [`pilots/pilot_0000060/`](pilots/pilot_0000060/) — pilot_0000060 — C016 Cohomology Rings: Telling Spaces Apart with Cup Products
- [`pilots/pilot_0000061/`](pilots/pilot_0000061/) — pilot_0000061 — C017 Nonabelian Lattice Holonomy and Flatness
- [`pilots/pilot_0000062/`](pilots/pilot_0000062/) — pilot_0000062 — C018 Frustration Index of Signed Graphs
- [`pilots/pilot_0000063/`](pilots/pilot_0000063/) — pilot_0000063 — C019 Degree-2 Obstructions at Scale
- [`pilots/pilot_0000064/`](pilots/pilot_0000064/) — pilot_0000064 — C020 Spectral Sequence Pages of a Double Complex
- [`pilots/pilot_0000065/`](pilots/pilot_0000065/) — pilot_0000065 — C021 Q40-R: The ChatGPT Stabilizer Challenge Run as Specified
- [`pilots/pilot_0000066/`](pilots/pilot_0000066/) — pilot_0000066 — C022 Stabilizer Code Distance with Lower-Bound Certificates
- [`pilots/pilot_0000067/`](pilots/pilot_0000067/) — pilot_0000067 — C023 Clifford Circuit Synthesis from Tableaux
- [`pilots/pilot_0000068/`](pilots/pilot_0000068/) — pilot_0000068 — C024 Local-Clifford Equivalence of Graph States
- [`pilots/pilot_0000069/`](pilots/pilot_0000069/) — pilot_0000069 — C025 Exact Mutually Unbiased Bases in Prime-Power Dimensions
- [`pilots/pilot_0000070/`](pilots/pilot_0000070/) — pilot_0000070 — C026 Frustration-Free Projector Hamiltonians
- [`pilots/pilot_0000071/`](pilots/pilot_0000071/) — pilot_0000071 — C027 Kochen-Specker Sets and Contextuality Certificates
- [`pilots/pilot_0000072/`](pilots/pilot_0000072/) — pilot_0000072 — C028 Fermion-to-Qubit Mappings with Exact CAR Checks
- [`pilots/pilot_0000073/`](pilots/pilot_0000073/) — pilot_0000073 — C029 Minimum-Weight Surface-Code Decoding
- [`pilots/pilot_0000074/`](pilots/pilot_0000074/) — pilot_0000074 — C030 Tensor-Network Contraction Order Under a Cost Bound
- [`pilots/pilot_0000075/`](pilots/pilot_0000075/) — pilot_0000075 — C031 Anomaly-Free Chiral U(1) Charge Assignments
- [`pilots/pilot_0000076/`](pilots/pilot_0000076/) — pilot_0000076 — C032 Six-Dimensional Supergravity Anomaly Cancellation
- [`pilots/pilot_0000077/`](pilots/pilot_0000077/) — pilot_0000077 — C033 Weight Multiplicities of Simple Lie Algebras
- [`pilots/pilot_0000078/`](pilots/pilot_0000078/) — pilot_0000078 — C034 Calabi-Yau Hodge Numbers from Reflexive Polytopes
- [`pilots/pilot_0000079/`](pilots/pilot_0000079/) — pilot_0000079 — C035 Mathieu Moonshine from the K3 Elliptic Genus
- [`pilots/pilot_0000080/`](pilots/pilot_0000080/) — pilot_0000080 — C036 Genus-Zero Invariants of the Quintic via Mirror Symmetry
- [`pilots/pilot_0000081/`](pilots/pilot_0000081/) — pilot_0000081 — C037 Fusion Rules from the Verlinde Formula
- [`pilots/pilot_0000082/`](pilots/pilot_0000082/) — pilot_0000082 — C038 Combinatorial Curvature and Discrete Gauss-Bonnet
- [`pilots/pilot_0000083/`](pilots/pilot_0000083/) — pilot_0000083 — C039 Lattice Gauge Theory: Gauss Law and Topological Degeneracy
- [`pilots/pilot_0000084/`](pilots/pilot_0000084/) — pilot_0000084 — C040 M-Theory on Tori: Cremmer-Julia Scalar Counting
- [`pilots/pilot_0000085/`](pilots/pilot_0000085/) — pilot_0000085 — C041 Lean 4 Proofs of Hidden Finite Lemmas
- [`pilots/pilot_0000086/`](pilots/pilot_0000086/) — pilot_0000086 — C042 SAT Encodings with DRAT and LRAT Certificates
- [`pilots/pilot_0000087/`](pilots/pilot_0000087/) — pilot_0000087 — C043 Ramsey and van der Waerden Lower-Bound Constructions
- [`pilots/pilot_0000088/`](pilots/pilot_0000088/) — pilot_0000088 — C044 Finite Group Identification with Isomorphism Witnesses
- [`pilots/pilot_0000089/`](pilots/pilot_0000089/) — pilot_0000089 — C045 Knot Polynomials from Planar-Diagram Codes
- [`pilots/pilot_0000090/`](pilots/pilot_0000090/) — pilot_0000090 — C046 Knuth-Bendix Completion with Joinability Certificates
- [`pilots/pilot_0000091/`](pilots/pilot_0000091/) — pilot_0000091 — C047 Recurrence and Generating-Function Discovery
- [`pilots/pilot_0000092/`](pilots/pilot_0000092/) — pilot_0000092 — C048 Ternary Quadratic Forms: Solution or Local Obstruction
- [`pilots/pilot_0000093/`](pilots/pilot_0000093/) — pilot_0000093 — C049 Universal Constructions in Finite Categories
- [`pilots/pilot_0000094/`](pilots/pilot_0000094/) — pilot_0000094 — C050 Equational Theorem Proving with Checkable Rewrite Proofs
- [`pilots/pilot_0000095/`](pilots/pilot_0000095/) — pilot_0000095 — C051 Exact LP Solver with Dual and Farkas Certificates
- [`pilots/pilot_0000096/`](pilots/pilot_0000096/) — pilot_0000096 — C052 Max-Flow with Min-Cut Certificates
- [`pilots/pilot_0000097/`](pilots/pilot_0000097/) — pilot_0000097 — C053 Bareiss Fraction-Free Matrix Inversion
- [`pilots/pilot_0000098/`](pilots/pilot_0000098/) — pilot_0000098 — C054 Exact Linear Systems with Inconsistency Witnesses
- [`pilots/pilot_0000099/`](pilots/pilot_0000099/) — pilot_0000099 — C055 Assignment Problems with Dual Potentials
- [`pilots/pilot_0000100/`](pilots/pilot_0000100/) — pilot_0000100 — C056 DFA Minimization and Equivalence with Distinguishing Strings
- [`pilots/pilot_0000101/`](pilots/pilot_0000101/) — pilot_0000101 — C057 Sorting Network Synthesis
- [`pilots/pilot_0000102/`](pilots/pilot_0000102/) — pilot_0000102 — C058 Straight-Line Superoptimization
- [`pilots/pilot_0000103/`](pilots/pilot_0000103/) — pilot_0000103 — C059 SQL Synthesis under Three-Valued-Logic Fences
- [`pilots/pilot_0000104/`](pilots/pilot_0000104/) — pilot_0000104 — C060 Checker Synthesis Scored by Mutation Kill Rate
- [`pilots/pilot_0000105/`](pilots/pilot_0000105/) — pilot_0000105 — C061 Chemical and Redox Equation Balancing
- [`pilots/pilot_0000106/`](pilots/pilot_0000106/) — pilot_0000106 — C062 Reaction-Network Deficiency Theory
- [`pilots/pilot_0000107/`](pilots/pilot_0000107/) — pilot_0000107 — C063 Isomer Enumeration by Polya Counting
- [`pilots/pilot_0000108/`](pilots/pilot_0000108/) — pilot_0000108 — C064 Flux Balance Analysis with Shadow Prices
- [`pilots/pilot_0000109/`](pilots/pilot_0000109/) — pilot_0000109 — C065 Designing Kinetic Proofreading Schemes
- [`pilots/pilot_0000110/`](pilots/pilot_0000110/) — pilot_0000110 — C066 Attractors of Boolean Gene-Regulatory Networks
- [`pilots/pilot_0000111/`](pilots/pilot_0000111/) — pilot_0000111 — C067 HP Lattice Protein Folding
- [`pilots/pilot_0000112/`](pilots/pilot_0000112/) — pilot_0000112 — C068 Maximum-Parsimony Phylogenies with Optimality Certificates
- [`pilots/pilot_0000113/`](pilots/pilot_0000113/) — pilot_0000113 — C069 Exact R0 Threshold Decisions
- [`pilots/pilot_0000114/`](pilots/pilot_0000114/) — pilot_0000114 — C070 Self/Nonself Detector Cover
- [`pilots/pilot_0000115/`](pilots/pilot_0000115/) — pilot_0000115 — C071 All Nash Equilibria of Bimatrix Games
- [`pilots/pilot_0000116/`](pilots/pilot_0000116/) — pilot_0000116 — C072 Linear Fisher Market Equilibrium
- [`pilots/pilot_0000117/`](pilots/pilot_0000117/) — pilot_0000117 — C073 Stable Matching with Couples and Ties
- [`pilots/pilot_0000118/`](pilots/pilot_0000118/) — pilot_0000118 — C074 Revenue-Optimal Auctions by Linear Programming
- [`pilots/pilot_0000119/`](pilots/pilot_0000119/) — pilot_0000119 — C075 Kemeny Rank Aggregation
- [`pilots/pilot_0000120/`](pilots/pilot_0000120/) — pilot_0000120 — C076 Arbitrage as Nontrivial Holonomy
- [`pilots/pilot_0000121/`](pilots/pilot_0000121/) — pilot_0000121 — C077 Ledger Reconciliation as First Cohomology
- [`pilots/pilot_0000122/`](pilots/pilot_0000122/) — pilot_0000122 — C078 Shapley Values and Core Nonemptiness
- [`pilots/pilot_0000123/`](pilots/pilot_0000123/) — pilot_0000123 — C079 Leontief Input-Output Productivity
- [`pilots/pilot_0000124/`](pilots/pilot_0000124/) — pilot_0000124 — C080 A Compute Market for Arms and Models

## Team

Pattern `solo`: coder ×1 (sonnet); deep_researcher ×1 (opus); host_checker ×1 (none).

Boost: when checker rejects: one opus attempt with the checker message (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf13) · [machine-readable entry](../dag/workflow_dag.json)
