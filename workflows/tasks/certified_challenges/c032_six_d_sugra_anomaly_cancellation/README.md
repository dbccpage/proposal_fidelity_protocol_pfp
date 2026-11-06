# Challenge C032: Six-Dimensional Supergravity Anomaly Cancellation

**Domain:** `d_physics_mtheory`  
**Tier:** `T3`  
**Budget:** $1.00 ceiling, $0.05 target  
**Model Ceiling:** $\le 70\text{B}$ open weights  
**Protocol:** SG-CP v1  
**AuthorityEffect:** None  

## Overview
C032 evaluates 6D $\mathcal{N}=(1,0)$ supergravity spectra against the 5 necessary anomaly cancellation conditions under Green-Schwarz-Sagnotti factorization:
1. Pure Gravitational: $H - V + 29T = 273$
2. Irreducible Quartic: $B_{\text{adj}} = \sum_R x_R B^R$ for groups with quartic Casimir
3. Gravitational Self-Intersection: $a \cdot a = 9 - T$
4. Gauge Vector Intersections: $a \cdot b_i, b_i \cdot b_i, b_i \cdot b_j$
5. Realizability in Signature $(1, T)$: Gram matrix inertia $n_+ \le 1, n_- \le T$ via exact $LDL^T$

## Verification Results
- 10 Canonical Examples (`participant_packet/examples/`)
- 42 Hidden Judge Cases (`cases/base/`: 28, `cases/controls/`: 8, `cases/poisoned/`: 6)
- 46 Hostile Corrupted Mutations (`mutation_suite/mutations/`)
- Dual Checkers: Checker 1 (Exact Algebraic Weight Certifier) & Checker 2 (Independent Matrix Certifier)
- Commit-Reveal State Machine: `PASS_TO_MASTER`
- Adversary Reverse Write Order Quad Bundle (`novella.md` $\to$ `dda_actions.jsonl` $\to$ `summary.json` $\to$ `receipt.json`)
