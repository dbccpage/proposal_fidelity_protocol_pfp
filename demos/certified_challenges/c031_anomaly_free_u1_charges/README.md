# C031: Anomaly-Free Chiral $U(1)$ Charge Assignments Challenge

**AuthorityEffect:** None. **Status:** Active. **Domain:** d_physics_mtheory. **Tier:** T3. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Overview

The **C031 (Anomaly-Free Chiral $U(1)$ Charge Assignments)** challenge evaluates whether an algorithmic solver or AI model can systematically discover, enumerate, and complete exact integer charge assignments for chiral fermions under a $U(1)$ gauge symmetry in $D=4, \mathcal{N}=1$ supergravity and string compactifications.

In four-dimensional chiral gauge theories coupled to gravity, quantum consistency mandates the exact vanishing of all one-loop gauge and gravitational triangle anomalies. For a single $U(1)$ gauge group with $n$ chiral fermions carrying integer charges $q = (q_1, q_2, \dots, q_n) \in \mathbb{Z}^n \setminus \{0\}$, the anomaly cancellation conditions reduce to a system of coupled Diophantine equations:

1. **Linear (Mixed Gravitational-Gauge) Anomaly Cancellation ($U(1)-(\text{gravity})^2$):**
   $$\sum_{i=1}^n q_i = 0$$

2. **Cubic Gauge Anomaly Cancellation ($U(1)^3$):**
   $$\sum_{i=1}^n q_i^3 = 0$$

### Mathematical Invariants & Structural Constraints

- **Primitivity ($\gcd = 1$):**
  A charge assignment is primitive if and only if $\gcd(|q_1|, |q_2|, \dots, |q_n|) = 1$. Non-primitive spectra (e.g. $[2, -4, 2]$) represent redundant sub-lattice embeddings and are strictly invalid.
- **Chirality (Non-Vector-Like):**
  A spectrum is vector-like if its multiset is invariant under overall negation: $\operatorname{Counter}(q) = \operatorname{Counter}(-q)$ (i.e. every charge $+q_i$ is paired with $-q_i$). A spectrum is **chiral** if and only if $\operatorname{Counter}(q) \neq \operatorname{Counter}(-q)$. Vector-like spectra decouple trivially and are strictly rejected.
- **Canonical Representative Rule:**
  To eliminate permutation gauge redundancies $S_n$ and charge conjugation $\mathbb{Z}_2$, every solution is represented in canonical form:
  $$\operatorname{canonical}(q) = \min(\operatorname{sort}(q), \operatorname{sort}(-q))$$
  where sorting is ascending and comparison is lexicographical.
- **$n \le 4$ Non-Existence Theorem:**
  For $n=3$, $a+b+c=0 \implies a^3+b^3+c^3 = 3abc = 0 \implies abc=0$, forcing a zero charge and vector-like pairing. For $n=4$, setting $d = -(a+b+c)$ yields the cubic factorization:
  $$(a+b+c)^3 - a^3 - b^3 - c^3 = 3(a+b)(b+c)(c+a) = 0$$
  This forces at least two charges to sum to zero ($b=-a \implies d=-c$), compelling vector-like triviality. Hence, **no chiral anomaly-free spectra exist for $n \le 4$**. The minimal chiral spectrum requires $n=5$.

### Outcome States

- `SOLVED`: Valid query output. For `enumerate`, returns exact count and lexicographically sorted canonical solutions. For `complete`, returns completing charges satisfying primitivity and chirality, or `completion: null` with `claim: "NO_COMPLETION"` if certified impossible.
- `OUT_OF_SCOPE`: Structural parameter violations with grounded mathematical witnesses:
  - `fixed_charge_exceeds_bound`: $|f_i| > Q$
  - `fixed_charge_zero`: $f_i = 0$
  - `too_many_fixed_charges`: number of fixed charges $m \ge n - 1$
- `UNKNOWN`: Closed-list typed refusals for malformed or out-of-bounds queries (`N_OUT_OF_BOUNDS`, `BOUND_OUT_OF_BOUNDS`, `MALFORMED_QUERY_TYPE`, `MALFORMED_CASE_STRUCTURE`).

---

## 2. Directory Layout

```
demos/certified_challenges/c031_anomaly_free_u1_charges/
├── README.md                                 # This overview and verification guide
├── TEST_READY.md                             # Test readiness report and Examiner falsification matrix
├── participant_packet/                       # Visible to participant models & solvers
│   ├── TASK.md                               # Mathematical specification & JSON schemas
│   ├── runner.py                             # Sandboxed execution runner -> answers.jsonl
│   ├── accounting.json                       # Provenance, tokens, and cost accounting template (Tier T3)
│   └── examples/                             # 12 Public worked examples with exact input & output
│       ├── ex01_enumerate_n3_empty.json
│       ├── ex02_enumerate_n4_empty.json
│       ├── ex03_enumerate_n5_bound9.json
│       ├── ex04_enumerate_n5_bound10.json
│       ├── ex05_enumerate_n6_bound5.json
│       ├── ex06_complete_n5_solvable.json
│       ├── ex07_complete_n7_solvable.json
│       ├── ex08_complete_vector_like_only.json
│       ├── ex09_complete_no_completion.json
│       ├── ex10_oos_fixed_charge_exceeds_bound.json
│       ├── ex11_oos_fixed_charge_zero.json
│       └── ex12_oos_too_many_fixed_charges.json
├── reference_solver/                         # Pure Python stdlib reference solver implementation
│   ├── __init__.py
│   ├── diophantine_u1.py                     # Diophantine solver, solve_pair resolvent, branch-and-bound, MITM
│   ├── ddc_tracer.py                         # DDC 8-letter operational tracer with SHA-256 chained receipts
│   └── solver.py                             # Exact solver def solve(case: dict) -> dict
├── judge_packet/                             # Operator judge packet (hidden seam)
│   ├── manifest.json                         # Cryptographic commit-reveal manifest of 87 files
│   ├── cases/                                # 46 hidden evaluation cases (32 base, 8 controls, 6 poisoned)
│   │   ├── base/                             # 32 base cases (12 enumerations, 20 completions with 6 no-comp)
│   │   ├── controls/                         # 8 physical invariance controls (gauge, relabel, sign)
│   │   └── poisoned/                         # 6 poisoned adversarial cases (vector traps, common factors, 2e6 bound)
│   ├── checkers/                             # Dual independent checkers
│   │   ├── u1_algebraic_checker.py           # Checker 1: Exact Algebraic & Chirality Certifier
│   │   ├── u1_mitm_checker.py                # Checker 2: Independent Meet-in-the-Middle Dual Engine
│   │   └── dual_evaluator.py                 # Dual agreement orchestrator & disagreement detector
│   └── mutation_suite/                       # 36 corrupted certificate mutations testing 100% rejection
│       ├── test_c031_checker_mutations.py         # Mutation harness verifying 100% kill rate (37 tests)
│       └── mutations/                        # 36 mutation JSON files
├── commitments/                              # Cryptographic commit-reveal records (SG-CP v1)
│   ├── c031_judge_commitment.json            # Phase 1: Judge manifest commitment
│   ├── c031_freeze_record.json               # Phase 2: Deliverable solver freeze record
│   └── c031_scoring_receipt.json             # Phase 3: Final scoring receipt & Adversary seal
├── governance/                               # Governance, cost gate, and reality gate
│   ├── __init__.py
│   ├── budget_gate.py                        # BudgetController (< $0.05 target, <= $1.00 ceiling, <= 70B, Tier T3)
│   ├── adversary_gate.py                        # Adversary reality gate, 4-file bundle, and dual-sink persistence
│   └── commit_reveal_runner.py               # 3-Phase Commit-Reveal runner CLI
└── tests/                                    # Scoped test suite
    ├── __init__.py
    ├── test_participant_packet.py            # Tests validating schema, examples, and runner
    ├── test_reference_solver.py              # Tests validating solver, math invariants, and DDC trace
    ├── test_dual_checkers.py                 # Tests validating dual checkers and case suite
    ├── test_governance_and_commit_reveal.py  # Tests validating budget gate, Adversary gate, and commit-reveal
    └── test_e2e_challenge.py                 # Comprehensive 4-tier E2E test suite (Tiers 1-4)
```

---

## 3. Schemas & Wire Contracts

### Enumerate Query Schema
```json
{
  "id": "case_enum_01",
  "query": "enumerate",
  "n": 5,
  "bound": 9
}
```

Output:
```json
{
  "id": "case_enum_01",
  "status": "SOLVED",
  "count": 1,
  "solutions": [
    [-9, -5, -1, 7, 8]
  ]
}
```

### Complete Query Schema
```json
{
  "id": "case_comp_01",
  "query": "complete",
  "n": 5,
  "bound": 10,
  "fixed": [-9, -5]
}
```

Output (Solvable):
```json
{
  "id": "case_comp_01",
  "status": "SOLVED",
  "completion": [-1, 7, 8]
}
```

Output (Certified Impossible):
```json
{
  "id": "case_comp_02",
  "status": "SOLVED",
  "completion": null,
  "claim": "NO_COMPLETION"
}
```

### OUT_OF_SCOPE Schema
```json
{
  "id": "case_oos_01",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "kind": "fixed_charge_exceeds_bound",
    "index": 0,
    "charge": 15,
    "bound": 10
  }
}
```

---

## 4. Dual Independent Checkers & Invariance Engine

Verification is performed by two strictly independent, non-communicating checking engines:
- **Checker 1 (`u1_algebraic_checker.py`):** Exact algebraic certifier verifying $\sum q_i = 0$, $\sum q_i^3 = 0$, $\gcd(|q|) = 1$, strict non-multiset negation equality, canonical representative sorting, and independent refutation of `NO_COMPLETION` claims.
- **Checker 2 (`u1_mitm_checker.py`):** Independent meet-in-the-middle dual engine that builds orthogonal sum and cubic sum lookup tables to cross-verify enumeration counts and completion existences.
- **Anti-Bypass Defenses:**
  1. *Anti-Trivial-Identity:* Rejects all vector-like cancellations $(q, -q)$.
  2. *Anti-Sub-Lattice:* Rejects non-primitive integer multiples ($k \cdot q$).
  3. *Anti-Sign-Flip:* Rejects non-canonical signs ($s_n > -s_1$ or lexicographical inversion).
  4. *Anti-Floating-Point:* Enforces exact arbitrary-precision integer arithmetic without float casting.

---

## 5. Verification & Running Instructions

In compliance with repository governance rules, **never execute whole-suite sweeps (`pytest .`)**. Tests must be run locally via targeted commands:

```bash
# 1. Participant packet tests (4 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_participant_packet.py -v

# 2. Reference solver & Diophantine engine tests (9 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_reference_solver.py -v

# 3. Dual independent checkers & cases tests (5 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_dual_checkers.py -v

# 4. Hostile mutation kill suite (37 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/judge_packet/mutation_suite/test_c031_checker_mutations.py -v

# 5. Governance, Tier T3 budget gate, Adversary gate, and Commit-Reveal runner (4 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_governance_and_commit_reveal.py -v

# 6. Comprehensive 4-Tier E2E integration test suite (12 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_e2e_challenge.py -v
```

### Commit-Reveal State Machine Execution

```bash
# Run full SG-CP v1 3-phase Commit-Reveal state machine:
python demos/certified_challenges/c031_anomaly_free_u1_charges/governance/commit_reveal_runner.py all
```
