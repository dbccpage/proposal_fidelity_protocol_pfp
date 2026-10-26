# C021: Q40-R Quantum Stabilizer Challenge Core

**AuthorityEffect:** None. **Status:** Active. **Domain:** c_quantum. **Tier:** T2. **Protocol:** [SG-CP v1](../../01_challenge_protocol.md).

---

## 1. Overview

The **C021 (Q40-R Stabilizer Challenge)** evaluates whether an AI model or algorithmic solver can synthesize an exact, certificate-generating quantum ground-state solver for finite commuting Pauli Hamiltonians on $n \le 8$ qubits and $M \le 24$ terms:

$$H = \sum_{i=1}^M w_i \frac{I - s_i P_i}{2}$$

where:
- $n \in \{1, \dots, 8\}$,
- $P_i \in \{I, X, Y, Z\}^{\otimes n}$ is an $n$-qubit Pauli word,
- $s_i \in \{-1, +1\}$ is the target eigenvalue,
- $w_i = [p_i, q_i] \in \mathbb{Q}^+$ is an exact positive rational weight ($p_i, q_i \in \mathbb{Z}^+$).

The challenge separates outcomes into three strictly typed states:
- `SOLVED`: Commuting Hamiltonians with exact rational ground energy $E_0 \in \mathbb{Q}$, full eigenspace degeneracy $|\text{argmin}| \cdot 2^{n-k}$, independent generator basis $G_1, \dots, G_k$, signed decompositions $P_i = \sigma_i \prod G_j^{e_{ij}}$ ($\sigma_i \in \{\pm 1\}$ with exact phase tracking $Y = iXZ$), and all minimizing joint eigenvalue bitmasks.
- `OUT_OF_SCOPE`: Noncommuting Hamiltonians, certified by an explicit pair witness $[id_a, id_b]$ ($id_a < id_b$ in lexicographical string order) whose terms anticommute.
- `UNKNOWN`: Closed-list typed refusals for malformed, non-positive, or out-of-bounds cases ($n > 8$, $M > 24$, duplicate term IDs, malformed Pauli words, or invalid targets).

---

## 2. Directory Layout

```
omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/
├── README.md                                 # This overview and verification guide
├── participant_packet/                       # Visible to participant models & solvers
│   ├── TASK.md                               # Mathematical specification & JSON schemas
│   ├── runner.py                             # Sandboxed execution runner -> answers.jsonl
│   ├── accounting.json                       # Provenance, tokens, and cost accounting template
│   └── examples/                             # 12 Public worked examples with exact input & output
│       ├── ex01_solved_trivial_identity.json
│       ├── ex02_solved_bell_stabilizer.json
│       ├── ex03_solved_y_heavy_phase.json
│       ├── ex04_solved_opposing_signs_frustration.json
│       ├── ex05_solved_ghz_3qubit.json
│       ├── ex06_oos_single_anticommuting_pair.json
│       ├── ex07_oos_transverse_field.json
│       ├── ex08_oos_buried_pair.json
│       ├── ex09_unknown_duplicate_term_id.json
│       ├── ex10_unknown_qubits_out_of_bounds.json
│       ├── ex11_relabel_pair_base.json
│       └── ex12_relabel_pair_permuted.json
├── reference_solver/                         # Reference solver implementation
│   ├── __init__.py
│   ├── pauli.py                              # Phase-tracked Pauli algebra (Y = iXZ) & F2 symplectic
│   ├── solver.py                             # Exact solver def solve(case: dict) -> dict
│   └── ddc_tracer.py                         # DDC 8-letter operational tracer with SHA-256 chained receipts
├── judge_packet/                             # Operator judge packet (hidden seam)
│   ├── manifest.json                         # Cryptographic commit-reveal manifest of 91 files
│   ├── cases/                                # 44 hidden evaluation cases (30 base, 8 controls, 6 poisoned)
│   ├── checkers/                             # Dual independent checkers (algebraic & spectral LDL^H)
│   └── mutation_suite/                       # 40 corrupted certificate mutations testing 100% rejection
├── commitments/                              # Cryptographic commit-reveal records (SG-CP v1)
│   ├── c021_q40_r_judge_commitment.json      # Phase 1: Judge manifest commitment
│   ├── c021_q40_r_freeze_record.json         # Phase 2: Deliverable solver freeze record
│   └── c021_q40_r_scoring_receipt.json       # Phase 3: Final scoring receipt & Woland seal
├── governance/                               # Governance, cost gate, and reality gate
│   ├── __init__.py
│   ├── budget_gate.py                        # BudgetController (< $0.05 target, <= $0.25 ceiling, <= 70B)
│   ├── woland_gate.py                        # Woland reality gate, 4-file bundle, and dual-sink persistence
│   └── commit_reveal_runner.py               # 3-Phase Commit-Reveal runner CLI
└── tests/                                    # Scoped test suite
    ├── __init__.py
    ├── test_participant_packet.py            # Tests validating schema, examples, and runner
    ├── test_reference_solver.py              # Tests validating solver, math invariants, and DDC trace
    ├── test_dual_checkers.py                 # Tests validating dual checkers and case suite
    └── test_governance_and_commit_reveal.py  # Tests validating budget gate, Woland gate, and commit-reveal
```

---

## 3. Schemas & Wire Contracts

### Input Schema
```json
{
  "id": "h_07",
  "n": 3,
  "terms": [
    {
      "id": "t_a",
      "P": "XYZ",
      "w": [3, 2],
      "target": 1
    },
    {
      "id": "t_b",
      "P": "ZZI",
      "w": [1, 1],
      "target": -1
    }
  ]
}
```

### Output Schemas
- **`SOLVED`**:
  ```json
  {
    "id": "h_07",
    "status": "SOLVED",
    "energy": [0, 1],
    "degeneracy": 2,
    "basis": ["t_a", "t_b"],
    "decomposition": [
      {"id": "t_a", "mask": 1, "phase": 1},
      {"id": "t_b", "mask": 2, "phase": 1}
    ],
    "minimizers": [2]
  }
  ```
- **`OUT_OF_SCOPE`**:
  ```json
  {
    "id": "h_08",
    "status": "OUT_OF_SCOPE",
    "witness": ["t_a", "t_c"]
  }
  ```
- **`UNKNOWN`**:
  ```json
  {
    "id": "h_09",
    "status": "UNKNOWN",
    "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"
  }
  ```

Closed refusal codes:
- `NUM_QUBITS_OUT_OF_BOUNDS` ($n < 1$ or $n > 8$)
- `TERM_COUNT_OUT_OF_BOUNDS` ($M < 0$ or $M > 24$)
- `INVALID_WEIGHT` (non-positive, non-integer, or not a 2-element pair `[num, den]`)
- `DUPLICATE_TERM_ID` (duplicate term ID within case)
- `MALFORMED_PAULI_WORD` (word length $\neq n$ or character outside `IXYZ`)
- `INVALID_TARGET_SIGN` (target not in $\{+1, -1\}$)
- `INVALID_TERM_ID` (missing, non-string, or empty term ID)
- `MALFORMED_CASE_STRUCTURE` (missing required keys or invalid top-level types)

---

## 4. Execution & Verification Instructions

### Running the Participant Runner
```bash
python omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/participant_packet/runner.py \
  --cases omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/participant_packet/examples \
  --output omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/participant_packet/answers.jsonl
```

### Running the Commit-Reveal Pipeline
```bash
python -m omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner
```

### Running the Test Suites
```bash
# Participant packet & reference solver tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/tests/test_participant_packet.py \
  omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/tests/test_reference_solver.py \
  -q

# Dual checkers & mutation tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/tests/test_dual_checkers.py \
  omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py \
  -q

# Governance, cost gate, and commit-reveal tests
python -m pytest \
  omega_engine_projects/mssn_sn_symgam/challenges/c_quantum/c021_q40_r/tests/test_governance_and_commit_reveal.py \
  -q
```

---

## 5. Claim Hygiene

1. **What it supports:** This package provides an exact, certificate-generating reference stabilizer solver, a sandboxed participant runner, 12 canonical public worked examples, an operator judge packet with 44 hidden cases (two cases that repeated public examples were removed on 2026-09-29), dual independent mathematical checkers, a 51-case mutation suite, a BudgetController cost gate (< $0.05 target, <= $0.25 ceiling, <= 70B parameter ceiling), and a cryptographic 3-phase Commit-Reveal pipeline under Woland's terminal reality gate.
2. **What it does not support:** This package does not claim that arbitrary noncommuting quantum Hamiltonians can be solved with stabilizer techniques (they are strictly refused as `OUT_OF_SCOPE`), nor does it claim that third-party LLMs will unconditionally pass without empirical evaluation under SG-CP v1.
3. **Narrowest defensible claim:** For any input conforming to the $n \le 8, M \le 24$ bound, the reference solver determines exact ground-state energy, degeneracy, and certificate decompositions in $< 50\text{ ms}$ using standard library rational arithmetic only, and satisfies 100% of the 44 hidden evaluation cases under dual independent checking with 0 defects.
4. **Next test needed:** Milestone 4 full end-to-end integration and Tier 5 adversarial hardening with Challenger red-team agents.
