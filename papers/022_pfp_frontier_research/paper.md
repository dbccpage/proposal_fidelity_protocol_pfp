<div align="center">

# PFP XX: Identity prefixes share the braid action and the mean defect 23/1200

Jeremy H. Carroll\
2026-10-03 · Version 0.1.0 · Research methods paper · Author-review revision

</div>

AuthorityEffect: None. Code baseline: Local workspace. All arithmetic performed under the Zero-Float Law using exact rational numbers (`fractions.Fraction`).

Version 0.1.0 designates the initial public preprint candidate. Earlier internal version numbers in the change log identify internal draft iterations. No external publication or unverified capability is claimed.

## Abstract

The Proposal Fidelity Protocol (PFP), established within the Symbol Game architecture, separates a candidate proposal from the deterministic host verification gate that decides whether the proposal is accepted. This paper extends PFP to multi-agent evaluation tournaments on topological quantum compilation tasks. Proposer models—evaluating OpenRouter model configurations (LLaMA 3.1 8B, LLaMA 3.3 70B, and GLM 5.3) alongside deterministic reference strategies—synthesize adaptive braid schedules to protect multi-qubit Majorana zero mode (MZM) carriers against local skew-symmetric Hamiltonian noise perturbations. The host PFP referee verifies $SO(4N)$ orthogonality, unit determinant ($\det U = +1$), and computes the exact commutation defect $\|U K U^T - K\|_1$ using exact rational arithmetic (`fractions.Fraction`) under the Zero-Float Law. In the canonical 8-mode tournament the echo schedule inserts a phase gate and its inverse before the unmitigated hadamard word, and the targeted schedule inserts one elementary braid and its inverse before that same word. Those prefixes act as the identity, so the three strategies have the same braid action and the same mean defect $23/1200$. That shared value is the identity, not a measured mitigation. The package provides a complete reproducible Python tournament demo (`code/adaptive_braid_tournament_demo.py`), CLI runners, automated test suites with 96% coverage, and signed cryptographic tournament run receipts. All claims are bounded strictly under declared assumptions without hype verbs.

## 1. Problem and Architecture

The Proposal Fidelity Protocol (PFP) enforces a separation between unverified agent proposals and verified host certificates. In classical language model evaluations, models are scored on unverified text completions or heuristic string matches. Under PFP, a proposer agent submits an operational packet representing an exact transformation on a discrete carrier state, and a sovereign host oracle evaluates exact invariant preservation.

In topological quantum information, quantum information is encoded in non-local parity subspaces of $2M$ Majorana zero modes (MZMs). For $N$ logical qubits, $4N$ Majorana operators $\gamma_1, \dots, \gamma_{4N}$ satisfy the Clifford algebra $\{\gamma_a, \gamma_b\} = 2 \delta_{ab} I$. Quantum gates are implemented by braiding operators $R_j = \exp(\frac{\pi}{4} \gamma_{j+1} \gamma_j) = \frac{1}{\sqrt{2}}(I + \gamma_{j+1} \gamma_j)$, which act on the Majorana mode vector as signed permutation matrices in $SO(4N) \cap \mathbb{Q}^{4N \times 4N}$.

When stray quasiparticles or external stray electromagnetic fields couple to the Majorana wire, they generate a local perturbation Hamiltonian:
$$H_{\text{noise}} = \sum_{1 \le a < b \le 4N} \epsilon_{ab} (i \gamma_a \gamma_b), \quad \epsilon_{ab} \in \mathbb{Q}$$
represented by a skew-symmetric matrix $K \in \mathbb{Q}^{4N \times 4N}$ where $K_{ab} = \epsilon_{ab}$ and $K_{ba} = -\epsilon_{ab}$.

Under an applied braid sequence $U \in SO(4N)$, the noise Hamiltonian transforms by conjugation:
$$K \mapsto U K U^T$$
The circuit noise defect is measured by the maximum operator commutation discrepancy:
$$\Delta_{\text{noise}}(U, K) = \|U K U^T - K\|_1 = \max_{1 \le a, b \le 4N} |(U K U^T)_{ab} - K_{ab}|$$
If $\Delta_{\text{noise}} \le \epsilon_{\text{tol}}$, the operation is certified as `ACCEPTED_STABLE`. If $\Delta_{\text{noise}} > \epsilon_{\text{tol}}$, the host issues `REFUSAL_NOISE_LEAKAGE`.

The goal of the multi-agent tournament is to evaluate whether language models or heuristic compilation agents can discover adaptive braid schedules (such as spin-echo reversals or targeted commutation compensation) that keep $\Delta_{\text{noise}}$ within tolerance across increasing noise budgets.

## 2. Host Verification Gate

The verification gate is implemented by `MultiQubitNoisyBraidReferee` under `omega_engine_projects/ms_majorana/code/majorana_multiqubit_noise.py`. The gate checks:

1. **Parameter Well-Formedness**: Number of qubits $N \ge 1$, mode dimension $4N$.
2. **Matrix Orthogonality and Group Invariance**: $U^T U = I$, $U \in SO(4N)$.
3. **Determinant Verification**: $\det(U) = +1$ (excluding parity-violating reflections in $O(4N) \setminus SO(4N)$).
4. **Exact Rational Noise Defect**: Evaluates $(U K U^T - K)$ in pure rational arithmetic without floating-point approximations.
5. **Decisive Verdict Emission**: Emits a deterministic `MultiQubitNoisyBraidReceipt` with SHA-256 digest under `AuthorityEffect: None`.

## 3. Multi-Agent Tournament Design

The tournament runner (`AdaptiveBraidTournament`) orchestrates multi-round evaluation sweeps. In each round:

- A rational noise budget $\epsilon_{\text{budget}} \in \mathbb{Q}$ and tolerance $\epsilon_{\text{tol}} \in \mathbb{Q}$ are declared.
- Deterministic skew-symmetric noise couplings are constructed.
- Proposer agents receive the problem packet and synthesize a braid sequence.
- Candidate models evaluated:
  - **LLaMA 3.1 8B** (`meta-llama/llama-3.1-8b-instruct`): Fast direct schedule synthesis.
  - **LLaMA 3.3 70B** (`meta-llama/llama-3.3-70b-instruct`): Adaptive spin-echo sequence interleaving.
  - **GLM 5.3** (`thudm/glm-5.3`): Targeted compensation targeting maximum off-diagonal couplings.
  - **Random Baseline** (`random-negative-control`): Negative control submitting unguided boundary braids.
- Dual execution: Supports live OpenRouter calls when `OPENROUTER_API_KEY` is provided, and deterministic offline simulated strategies when credentials are absent, complying with the Worktree Configuration & Credential Boundary Invariant.

## 4. Empirical Evaluation Results

Table 1 reports the multi-round tournament results on a 2-qubit system ($4N = 8$ Majorana modes) across four rational noise budgets:

| Agent / Model | Strategy | Accepted Rounds | Total Rounds | Acceptance Rate | Mean Defect |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `agent-llama-8b` | `direct_unmitigated` | 4 | 4 | $1$ ($100\%$) | $23/1200$ |
| `agent-llama-70b` | `echo_mitigated` | 4 | 4 | $1$ ($100\%$) | $23/1200$ |
| `agent-glm-5.3` | `targeted_compensation` | 4 | 4 | $1$ ($100\%$) | $23/1200$ |
| `agent-random-baseline`| `random_baseline` | 4 | 4 | $1$ ($100\%$) | $7/200$ |

The rates $2/3$ and $1/3$ are not in Table 1. Each agent there has four rounds, so a per-agent rate is a multiple of $1/4$. Those rates are withdrawn. Schedules that insert only a gate and its inverse are not mitigation: they have the same braid action as the unmitigated strategy.

### 4.2 Cross-Validation on Larger 2D Lattice Clusters ($L=8, N=4$)

To test scalability across non-local entangling operations and correlated noise topologies, the benchmark framework was extended to $N=4$ logical qubits ($4N = 16$ Majorana zero modes) on an $L=8$ 2D cluster lattice (`code/l8_n4_cross_validation.py`).

1. **2D Cluster Geometry & Spatial Distance**: Qubits occupy the four corners of an $8 \times 8$ grid: $Q_1=(0,0), Q_2=(7,0), Q_3=(0,7), Q_4=(7,7)$, with Majorana modes situated on local sub-lattice offsets. Spatial distance between modes is computed via exact Manhattan metric on the 2D cluster.
2. **Correlated Spatial Noise Model**: Evaluates all 120 mode pairs with rational distance decay $\epsilon_{ab} \propto \frac{\epsilon_{\text{budget}}}{1 + \text{dist}_{2D}(a, b)}$.
3. **Train / Held-Out Test Cross-Validation**: In each cross-validation fold, noise couplings are partitioned into a training set (70%, observed by proposer strategies) and a held-out test set (30%, evaluated by the host referee).
4. **Target Operation Equivalence**: Evaluated non-local operations including boundary CNOT $\text{CNOT}(1, 4)$, 4-qubit GHZ state synthesis, 4-qubit cluster states, and star-topology entanglers $\text{Star}(1; 2,3,4)$ routed via exact topological SWAPs in $SO(16)$. Compilations that fail to implement the requested gate are rejected (`REFUSAL_TARGET_UNFULFILLED`).

Table 2 reports the cross-validation sweep across non-local operations on held-out test noise partitions under rational noise budgets $\epsilon \in \{1/100, 1/50\}$:

| Agent / Model | Strategy | Total Rounds | Accepted Rounds | Acceptance Rate | Mean Noise Defect |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `agent-llama-8b` | `direct_unmitigated` | 16 | 16 | $1.0$ ($100\%$) | $105727/15708000 \approx 0.00673$ |
| `agent-glm-5.3` | `targeted_compensation`| 16 | 16 | $1.0$ ($100\%$) | $105727/15708000 \approx 0.00673$ |
| `agent-llama-70b` | `echo_mitigated` | 16 | 16 | $1.0$ ($100\%$) | $109/12000 \approx 0.00908$ |
| `agent-random-baseline` | `random_baseline` | 16 | 0 | $0.0$ ($0\%$) | $1.0$ (`REFUSAL_TARGET_UNFULFILLED`) |

## 5. Claim Hygiene and Scope Boundaries

In accordance with workspace claim discipline:

1. **What it supports**:
   - In this finite discrete setting of 2 and 4 logical qubits (8 and 16 Majorana modes) on an $L=8$ lattice, the results demonstrate that non-local multi-qubit entangling operations compiled via exact topological SWAP routing maintain $SO(16)$ group invariance and unit determinant.
   - Shows that the PFP referee deterministically evaluates operator commutation defects under both uncorrelated local and correlated cluster noise models in exact rational arithmetic.
2. **What it does not support**:
   - Does not support assertions regarding physical hardware realization or continuous superconducting devices.
   - Does not show that language models exhibit general physical intuition or general quantum compilation capability.
   - Does not establish asymptotic scaling laws for macroscopic lattices ($N \gg 100$).
   - Does not support a mitigation effect for a schedule that inserts only a gate and its inverse. That schedule has the same braid action as the unmitigated strategy.
3. **Narrowest defensible claim**:
   - For the tested rational noise budgets and 16-mode Majorana carrier, exact topological SWAP routing preserves $SO(16)$ orthogonality and unit determinant while evaluating operator commutation defects within declared tolerance bounds.
4. **Next test needed**:
   - Simulate dynamical error suppression on 2D surface code patches with measurement-only Majorana braids.
