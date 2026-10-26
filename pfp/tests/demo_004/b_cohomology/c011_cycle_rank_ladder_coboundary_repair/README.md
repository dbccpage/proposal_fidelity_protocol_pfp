# C011: Cycle-Rank Ladder Minimum-$L_1$ Coboundary Repair Challenge

**AuthorityEffect:** None. **Status:** Active. **Domain:** b_cohomology. **Tier:** T2. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Overview

The **C011 (Cycle-Rank Ladder: Minimum-$L_1$ Coboundary Repair)** challenge evaluates whether an AI model or algorithmic solver can synthesize an exact, certificate-generating 1-cochain repair solver for finite connected multigraphs with cycle rank $b_1 = |E| - |V| + 1 \in [0, 16]$ and vertex count $|V| \le 60$.

Given a finite connected multigraph $G = (V, E)$, an exact rational 1-cochain of edge claims $c \in \mathcal{C}^1(G, \mathbb{Q})$, and positive rational weights $w_e \in \mathbb{Q}^+$, the objective is to find a 0-cochain of vertex potentials $\phi \in \mathcal{C}^0(G, \mathbb{Q})$ that minimizes the weighted $L_1$ defect distance to the coboundary subspace $B^1(G, \mathbb{Q}) = \text{im}(\delta)$:

$$\Phi_1(c, \delta\phi) = \sum_{e = (u,v) \in E} w_e |c_e - (\phi(v) - \phi(u))|$$

### Strong Duality & Exact Circulation Certificate

By linear programming duality, the minimum $L_1$ coboundary repair problem is dual to a bounded circulation flow problem on the cycle space $Z_1(G, \mathbb{Q}) = \ker(\partial)$. The solver must return a dual circulation vector $z \in \mathbb{Q}^{|E|}$ satisfying:
1. **Kirchhoff Flow Conservation** at every vertex $v \in V$:
   $$\sum_{e \in \delta^-(v)} z_e = \sum_{e \in \delta^+(v)} z_e$$
2. **Capacity Bounds** on every edge $e \in E$:
   $$|z_e| \le w_e$$
3. **Strong Duality Certificate** with exact zero duality gap:
   $$\sum_{e \in E} z_e c_e = \sum_{e \in E} w_e |c_e - (\delta\phi)_e|$$

### Outcome States

The challenge separates outcomes into strictly typed states:
- `SOLVED`: Connected graphs with $b_1 \le 16$, $|V| \le 60$. Yields exact canonical potentials $\phi$, coboundary repair values, edge residuals $r_e = c_e - (\delta\phi)_e$, dual circulation $z$, objective $\Phi_1$, and certified duality gap 0.
- `UNKNOWN`: Closed-list typed refusals for malformed, disconnected, or out-of-bounds cases.

---

## 2. Directory Layout

```
omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/
├── README.md                                 # This overview and verification guide
├── TEST_READY.md                             # Test readiness report and Lev Landau falsification matrix
├── participant_packet/                       # Visible to participant models & solvers
│   ├── TASK.md                               # Mathematical specification & JSON schemas
│   ├── runner.py                             # Sandboxed execution runner -> answers.jsonl
│   ├── accounting.json                       # Provenance, tokens, and cost accounting template
│   └── examples/                             # 12 Public worked examples with exact input & output
│       ├── ex01_solved_diamond.json
│       ├── ex02_solved_k4.json
│       ├── ex03_solved_path_tree.json
│       ├── ex04_solved_star_tree.json
│       ├── ex05_solved_multigraph_parallel.json
│       ├── ex06_solved_fractional_weights.json
│       ├── ex07_solved_wheel_w5.json
│       ├── ex08_unknown_disconnected.json
│       ├── ex09_unknown_negative_weight.json
│       ├── ex10_unknown_malformed_edge.json
│       ├── ex11_unknown_cycle_rank_out_of_bounds.json
│       └── ex12_unknown_vertex_count_out_of_bounds.json
├── reference_solver/                         # Pure Python stdlib reference solver implementation
│   ├── __init__.py
│   ├── graph_cohomology.py                   # Exact rational simplex LP, cycle basis & coboundary repair
│   ├── ddc_tracer.py                         # DDC 8-letter operational tracer with SHA-256 chained receipts
│   └── solver.py                             # Exact solver def solve(case: dict) -> dict
├── judge_packet/                             # Operator judge packet (hidden seam)
│   ├── manifest.json                         # Cryptographic commit-reveal manifest of 83 files
│   ├── cases/                                # 46 hidden evaluation cases (32 base, 8 controls, 6 poisoned)
│   │   ├── base/                             # 32 base cases (b1 in 0..16, trees, large claims, fractional)
│   │   ├── controls/                         # 8 physical invariance controls (gauge, relabel, scaling)
│   │   └── poisoned/                         # 6 poisoned adversarial cases (chords, traps, AM-4)
│   ├── checkers/                             # Dual independent checkers
│   │   ├── circulation_checker.py            # Checker 1: Exact LP Dual Circulation Certifier
│   │   ├── potential_checker.py              # Checker 2: Independent Primal-Dual & Coboundary Certifier
│   │   └── dual_evaluator.py                 # Dual agreement orchestrator & disagreement detector
│   └── mutation_suite/                       # 32 corrupted certificate mutations testing 100% rejection
│       ├── test_checker_mutations.py         # Mutation harness verifying 100% kill rate (33 tests)
│       └── mutations/                        # 32 mutation JSON files
├── commitments/                              # Cryptographic commit-reveal records (SG-CP v1)
│   ├── c011_judge_commitment.json            # Phase 1: Judge manifest commitment
│   ├── c011_freeze_record.json               # Phase 2: Deliverable solver freeze record
│   └── c011_scoring_receipt.json             # Phase 3: Final scoring receipt & Woland seal
├── governance/                               # Governance, cost gate, and reality gate
│   ├── __init__.py
│   ├── budget_gate.py                        # BudgetController (< $0.05 target, <= $0.50 ceiling, <= 70B)
│   ├── woland_gate.py                        # Woland reality gate, 4-file bundle, and dual-sink persistence
│   └── commit_reveal_runner.py               # 3-Phase Commit-Reveal runner CLI
└── tests/                                    # Scoped test suite
    ├── __init__.py
    ├── test_participant_packet.py            # Tests validating schema, examples, and runner
    ├── test_reference_solver.py              # Tests validating solver, math invariants, and DDC trace
    ├── test_dual_checkers.py                 # Tests validating dual checkers and case suite
    ├── test_governance_and_commit_reveal.py  # Tests validating budget gate, Woland gate, and commit-reveal
    └── test_e2e_challenge.py                 # Comprehensive 4-tier E2E test suite (Features F1-F20)
```

---

## 3. Schemas & Wire Contracts

### Input Schema
All numbers are represented as canonical exact rational strings (`"0"`, `"5"`, `"-3"`, `"5/12"`).

```json
{
  "id": "case_diamond_01",
  "vertices": ["v0", "v1", "v2", "v3"],
  "edges": [
    {"id": "e0", "source": "v0", "target": "v1", "claim": "3", "weight": "1"},
    {"id": "e1", "source": "v1", "target": "v2", "claim": "2", "weight": "1"},
    {"id": "e2", "source": "v0", "target": "v3", "claim": "1", "weight": "1"},
    {"id": "e3", "source": "v3", "target": "v2", "claim": "6", "weight": "1"}
  ]
}
```

### Output Schemas

- **`SOLVED`**:
  ```json
  {
    "id": "case_diamond_01",
    "status": "SOLVED",
    "b1": 1,
    "objective": "2",
    "potentials": {
      "v0": "0",
      "v1": "3",
      "v2": "6",
      "v3": "1"
    },
    "repairs": {
      "e0": "3",
      "e1": "3",
      "e2": "1",
      "e3": "5"
    },
    "residuals": {
      "e0": "0",
      "e1": "-1",
      "e2": "0",
      "e3": "1"
    },
    "dual_circulation": {
      "e0": "1",
      "e1": "1",
      "e2": "-1",
      "e3": "-1"
    },
    "duality_gap": "0"
  }
  ```

- **`UNKNOWN`**:
  ```json
  {
    "id": "case_disc_01",
    "status": "UNKNOWN",
    "refusal_code": "DISCONNECTED_GRAPH"
  }
  ```

### Closed Refusal Codes
1. `VERTEX_COUNT_OUT_OF_BOUNDS`: Number of vertices $|V| < 1$ or $|V| > 60$.
2. `EDGE_COUNT_OUT_OF_BOUNDS`: Negative edges or cycle rank $b_1 = |E| - |V| + 1 > 16$.
3. `INVALID_CAPACITY`: Edge weight $w_e \le 0$, non-rational string, or zero denominator.
4. `NEGATIVE_WEIGHT`: Explicit negative edge weight.
5. `DISCONNECTED_GRAPH`: Graph is not connected (number of components $c > 1$).
6. `MALFORMED_EDGE_SPEC`: Edge endpoints missing or outside declared vertex set $V$.
7. `INVALID_TARGET_DEFECT`: Edge claim $c_e$ is not a valid canonical rational string.
8. `MALFORMED_CASE_STRUCTURE`: Missing required top-level keys or invalid field types.

---

## 4. Execution & Verification Instructions

### Running the Participant Runner
```bash
python omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/participant_packet/runner.py \
  --cases omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/participant_packet/examples \
  --output omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/participant_packet/answers.jsonl
```

### Running the Commit-Reveal Pipeline
```bash
python -m omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.governance.commit_reveal_runner
```

### Running Targeted Test Suites
In accordance with repository governance rules, **never execute whole-suite sweeps (`pytest .`)**. Run only targeted test files:

```bash
# 1. Participant packet & reference solver tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_participant_packet.py \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_reference_solver.py \
  -q

# 2. Dual checkers & mutation tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_dual_checkers.py \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py \
  -q

# 3. Governance, budget gate, and commit-reveal tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_governance_and_commit_reveal.py \
  -q

# 4. E2E comprehensive 4-tier challenge test
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_e2e_challenge.py \
  -q
```

---

## 5. Claim Hygiene

1. **What it supports:** This challenge package provides a pure Python stdlib exact rational Simplex LP solver for minimum-$L_1$ coboundary repair on connected multigraphs ($b_1 \le 16$, $|V| \le 60$), verified against 46 hidden cases with 100% dual checker agreement, 100% mutation kill rate, and certified zero duality gap.
2. **What it does not support:** This package does not support higher-dimensional simplicial complexes (e.g. 2-cochain coboundary repair on 2-complexes) or disconnected graphs (which are strictly refused as `DISCONNECTED_GRAPH`).
3. **Narrowest defensible claim:** For any valid connected graph within $b_1 \le 16$ and $|V| \le 60$, the reference solver determines exact vertex potentials and dual circulation in $< 50\text{ ms}$ with zero duality gap using exact rational arithmetic, and satisfies 100% of the 46 judge cases with 0 defects under dual independent checking.
4. **Next test needed:** Evaluation of C012 (cellular sheaf cohomology) and C018 (signed graph frustration index).
