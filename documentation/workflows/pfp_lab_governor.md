# PFP Lab Exact Rational Graph Governor

**AuthorityEffect**: None.  
**Standard:** Ground Truth Verification and Claim Hygiene Standard  
**Contract:** `urn:pfp-lab:core:governor:v1`  
**Source Files:** `pfp_lab/core/governor.py`, `pfp_lab/core/graph.py`, `pfp_lab/core/obstruction.py`  

---

## 1. Mathematical Model & Exact State

`pfp_lab` implements the Proposal Fidelity Protocol over directed weighted constraint graphs using exact rational arithmetic (`fractions.Fraction`). The governor operates under zero floating-point tolerances, eliminating numerical drift.

### 1.1 Graph Definition & State Store

A constraint graph $G = (V, E, w)$ is defined by:
- A finite vertex set $V$.
- A set of directed edges $E \subseteq V \times V$, with irreflexive edges ($(u, u) \notin E$).
- Positive integer edge weights $w(u, v) \in [1, 1000]$.

The state of the governor consists of two exact rational mappings:
1. **Vertex Section ($s$):** A potential assignment $s: V \to \mathbb{Q}$. Vertices default to $0 \in \mathbb{Q}$.
2. **Edge Claims ($c$):** A set of declared potential differences $c: E \to \mathbb{Q}$, where $c(u, v)$ denotes the claimed difference $s(v) - s(u)$.

### 1.2 Exact Defect ($D$) & Primary Obstruction ($\Phi_1$)

The **Section Defect** $D(s)$ measures the weighted $L_1$ norm of constraint violations across all declared edges:

$$D(s) = \sum_{(u, v) \in E} w(u, v) \cdot |s(v) - s(u) - c(u, v)|$$

The **Primary Obstruction** $\Phi_1(c)$ measures the intrinsic inconsistency of the claim set, defined as the minimum defect achievable by any valid section:

$$\Phi_1(c) = \min_{s: V \to \mathbb{Q}} D(s)$$

$\Phi_1(c)$ is computed deterministically via minimum-weight cycle basis analysis or exact rational linear programming. When $\Phi_1(c) = 0$, the edge claims form a conservative field (all cycle holonomies vanish), meaning an exact zero-defect section exists.

---

## 2. The Four Fundamental Moves

The governor state machine exposes four fundamental operations (`MoveKind`):

```
                   [ Proposer (Untrusted Model / Agent) ]
                                     |
               +---------------------+---------------------+
               |                     |                     |
               v                     v                     v
         [ ASSERT Move ]       [ CUT Move ]        [ RETRACT Move ]
               |                     |                     |
               +---------------------+---------------------+
                                     |
                                     v
                       [ Governor Host Evaluator ]
                     (Exact Rational Defect Check)
                                     |
                   +-----------------+-----------------+
                   |                                   |
           (Defect Drops / Equal)              (Defect Rises)
                   |                                   |
                   v                                   v
             [ ADMITTED ]                         [ REFUSED ]
         State Updated & Recorded             State Left Untouched
         Status: MonotonicDescent,             Status: DefectIncrease
         ExactRepair, Idempotent
```

In parallel, **`VERIFY`** executes non-state-changing obligation audits.

---

### 2.1 ASSERT (`AssertMove`)

Records or updates a single directed edge claim $c(u, v) = q \in \mathbb{Q}$.

- **Parameters:** `source: str`, `target: str`, `value: Fraction`, `step_id: str | None`, `provisional: bool`, `enforce_monotonicity: bool`.
- **Pre-condition Checks:**
  - Irreflexivity: $u \neq v$ (`INVARIANT_VIOLATION` if $u = v$).
  - Carrier containment: $u, v \in V$ (`CARRIER_VIOLATION` if vertices are undeclared).
  - Declared edge: $(u, v) \in E$ (`MOVE_VIOLATION` if edge not in graph).
- **Monotonicity Rule:** If `enforce_monotonicity=True`, the governor computes the section defect with the trial claim. If $D_{\text{after}} > D_{\text{before}}$, the move is refused with status `DefectIncrease`, and the state remains unchanged.
- **Admission:** If admitted, state records $c(u, v) = q$ with status `Asserted` (or `ProvisionalAssert`).

---

### 2.2 CUT (`CutMove`)

Proposes a coordinated, atomic update to either the entire section or the entire claim set. Exactly one of `section` or `claims` must be provided; supplying both or neither returns a `MOVE_VIOLATION` refusal.

#### Section CUT (`CutMove(section=...)`)
Proposes a new potential assignment $s': V \to \mathbb{Q}$ for all vertices.
- **Admission Condition:** Admitted if and only if $D(s') \le D(s)$.
- **Status Classification:**
  - $D(s') = 0$ (and $D(s) > 0$): `ExactRepair`
  - $D(s') < D(s)$: `MonotonicDescent`
  - $D(s') == D(s)$: `IdempotentStationary`
  - $D(s') > D(s)$: `DefectIncrease` $\implies$ **Refused**, prior section retained.

#### Relational CUT (`CutMove(claims=...)`)
Proposes a complete replacement of all declared edge claims $c': E \to \mathbb{Q}$.
- **Admission Condition:** Admitted if and only if $\Phi_1(c') \le \Phi_1(c)$.
- **Projection Step:** Upon admission, the section is updated via canonical metric projection $s_{\text{new}} = P_S(G, c', s_{\text{old}})$, finding the closest section minimizing defect under the new claims.
- **Refusal:** If $\Phi_1(c') > \Phi_1(c)$, refused with `DefectIncrease`.

---

### 2.3 VERIFY (`VerifyMove`)

Executes an exact check against a declared formal obligation without altering governor state. Does not advance history.

Supported obligations:
1. **`ZERO_DEFECT`:** Verifies that current section defect $D(s) == 0$. Returns `Verified` or `VerificationFailed`.
2. **`ZERO_OBSTRUCTION`:** Verifies that primary obstruction $\Phi_1(c) == 0$.
3. **`EDGE_MATCH:u,v`:** Verifies that edge claim matches actual potential difference:
   $$c(u, v) == s(v) - s(u)$$

---

### 2.4 RETRACT (`RetractMove`)

Rolls back governor state to an earlier recorded step (`target_step_id`).

- Restores both the vertex section $s$ and edge claims $c$ saved at `target_step_id`.
- Recomputes the defect at the restored point.
- If `target_step_id` is missing from history, refused with `REFUSED`.
- Enables backtrack search when exploratory steps lead to dead ends or high residual defects.

---

## 3. The `Verdict` Contract

Every move returns an immutable `Verdict` record:

```python
@dataclass(frozen=True, slots=True)
class Verdict:
    step_id: str
    move: MoveKind
    admitted: bool
    status: Status
    defect_before: Fraction
    defect_after: Fraction
    details: str
```

The proposer possesses zero authority over verdict fields: `admitted`, `status`, `defect_before`, and `defect_after` are evaluated exclusively by the host governor.

---

## 4. Claim Hygiene Evaluation

1. **What the Evidence Supports:**
   - The `pfp_lab` governor provides an exact, zero-drift rational state machine for governing constraint proposals on finite graphs.
   - The defect non-increase condition prevents monotonic divergence of graph inconsistency.
2. **What the Evidence Does Not Support:**
   - The governor does not prove that an arbitrary LLM can discover a sequence of moves to solve a graph problem.
   - The model does not represent a general alignment mechanism for unconstrained natural language tasks.
3. **Narrowest Defensible Claim:**
   - In the discrete setting of weighted constraint graphs, the `pfp_lab` governor deterministically accepts or refuses candidate section and claim updates based on exact rational evaluation of $L_1$ defect descent and obstruction preservation.
4. **Next Test Needed:**
   - Benchmark multi-round LLM solvers under governor supervision across 50 randomly generated non-planar constraint graphs with planted obstructions, measuring the fraction of runs achieving `ExactRepair` within a 20-step budget.
