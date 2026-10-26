# C012: Cellular Sheaf Cohomology $H^0$ and $H^1$ Challenge

**AuthorityEffect:** None. **Status:** Active. **Domain:** b_cohomology. **Tier:** T2. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Overview

The **C012 (Cellular Sheaf Cohomology $H^0$ and $H^1$)** challenge evaluates whether an algorithmic solver or AI model can synthesize an exact, certificate-generating cellular sheaf cohomology solver for finite directed graphs over the exact rational field $\mathbb{Q}$.

Given a finite directed graph $G = (V, E)$, with stalk dimensions $d_v \ge 0$ for $v \in V$ and $d_e \ge 0$ for $e \in E$, and linear restriction matrices $F_{u \trianglelefteq e} \in \mathbb{Q}^{d_e \times d_u}$ and $F_{v \trianglelefteq e} \in \mathbb{Q}^{d_e \times d_v}$ for each edge $e = (u, v)$, the cochain spaces are:
$$C^0(G; \mathcal{F}) = \bigoplus_{v \in V} \mathbb{Q}^{d_v}, \quad C^1(G; \mathcal{F}) = \bigoplus_{e \in E} \mathbb{Q}^{d_e}$$

The sheaf coboundary map $\delta: C^0 \to C^1$ is defined on each edge $e = (u, v)$ by:
$$(\delta x)_e = F_{v \trianglelefteq e} x_v - F_{u \trianglelefteq e} x_u$$

### Exact Cohomology Invariants
- **Global Sections ($0$-th Cohomology):** $H^0(G; \mathcal{F}) = \ker(\delta)$. Represents globally consistent assignments.
- **Obstruction Space ($1$-st Cohomology):** $H^1(G; \mathcal{F}) = C^1 / \operatorname{im}(\delta)$, with $\dim H^1 = \dim C^1 - \operatorname{rank}(\delta)$.
- **Euler Characteristic & Rank-Nullity:** $\dim H^0 - \dim H^1 = \dim C^0 - \dim C^1$.

### Gluing vs. Obstruction Certificates
For each target cochain $b \in C^1$, the solver returns:
1. **Gluing witness ($b \in \operatorname{im}\delta$):** A 0-cochain $x \in C^0$ satisfying $\delta x = b$ exactly.
2. **Obstruction witness ($b \notin \operatorname{im}\delta$):** A 1-cochain $\eta \in C^1$ satisfying $\delta^T \eta = 0$ (harmonic dual co-cycle) and $\langle \eta, b \rangle \neq 0$ (non-zero inner product).

---

## 2. Directory Layout

```
omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/
├── README.md                                 # Overview, mathematical invariants, and verification guide
├── TEST_READY.md                             # Test readiness report and Lev Landau falsification matrix
├── participant_packet/                       # Visible to participant models & solvers
│   ├── TASK.md                               # Mathematical specification & JSON wire schemas
│   ├── runner.py                             # Sandboxed execution runner -> answers.jsonl
│   ├── accounting.json                       # Provenance, tokens, and cost accounting template
│   └── examples/                             # 20 Public worked examples with exact inputs & outputs
├── reference_solver/                         # Pure Python stdlib reference solver implementation
│   ├── __init__.py
│   ├── sheaf_cohomology.py                   # Exact rational block elimination, ker/im, and dual witnesses
│   ├── ddc_tracer.py                         # DDC 8-letter operational tracer with SHA-256 chained receipts
│   └── solver.py                             # Exact solver def solve(case: dict) -> dict
├── judge_packet/                             # Secret evaluation suite for scoring submissions
│   ├── manifest.json                         # Cryptographic SHA-256 manifest
│   ├── cases/                                # 56 Hidden evaluation cases (base, controls, poisoned)
│   ├── checkers/                             # Dual independent checkers (algebraic + elimination)
│   └── mutation_suite/                       # 41 Corrupted certificate mutations
├── governance/                               # Process & policy enforcement
│   ├── budget_gate.py                        # Pre-call financial ceiling enforcement
│   ├── woland_gate.py                        # Reality arbiter generating StructureBench quad bundles
│   └── commit_reveal_runner.py               # 3-Phase Commit-Reveal verification harness
└── tests/                                    # Scoped test battery
    ├── test_participant_packet.py
    ├── test_reference_solver.py
    ├── test_dual_checkers.py
    ├── test_governance_and_commit_reveal.py
    └── test_e2e_challenge.py
```

---

## 3. How to Run the Tests

In strict adherence to the Strict Test Execution Directive, tests must be executed locally in small batches using Python 3.12:

```bash
# Run reference solver and participant packet tests
py -3.12 -m pytest omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/tests/test_reference_solver.py omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/tests/test_participant_packet.py -v

# Run dual checkers and mutation test suite
py -3.12 -m pytest omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/tests/test_dual_checkers.py omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/judge_packet/mutation_suite/test_checker_mutations.py -v

# Run governance and full e2e integration
py -3.12 -m pytest omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/tests/test_governance_and_commit_reveal.py omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c012_cellular_sheaf_h0_h1/tests/test_e2e_challenge.py -v
```

---

## 4. Claim Hygiene Evaluation

1. **What this artifact supports:**
   - Demonstrates exact rational cellular sheaf cohomology ($H^0, H^1$) computation and dual gluing/obstruction witness certification on finite graphs over $\mathbb{Q}$.
   - Validates that dual independent checkers achieve a $100\%$ kill rate on 41 corrupted mutations.
2. **What this artifact does not support:**
   - Does not show capability for sheaves on higher-dimensional cellular or simplicial complexes ($n \ge 2$).
   - Does not confer operational authority (`AuthorityEffect: None`).
3. **Narrowest defensible claim:**
   - On the declared graph instances with stalk dimensions $d \le 4$, the reference solver computes exact sheaf Betti numbers and valid gluing/obstruction certificates over $\mathbb{Q}$.
4. **Next test needed:**
   - Verify C012 under the multi-domain discovery scanner `e2e_tests/test_runner.py`.
