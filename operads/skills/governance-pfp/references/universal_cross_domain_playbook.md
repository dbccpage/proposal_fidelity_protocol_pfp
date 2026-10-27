# Bounded Cross-Domain Symbol Game Fixture Playbook & Governor Seam Guide

AuthorityEffect: None.

## 1. Overview

The Symbol Game separates **heuristic hypothesis proposal** (an untrusted model or agent) from **host-owned finite verification** (an exact rational calculator over a declared graph).

The six-step workflow below was exercised on four checked-in fixtures. It does not establish performance, cost, model-quality, or universal cross-domain claims. Any such statement requires a receipt binding the exact input, adapter, environment, and measurement.

---

## 2. The Bounded Six-Step Execution Protocol

```
[Target Domain Problem]
       │
       ▼ (1) Declare Finite Carrier Graph G = (V, E, w)
       ▼ (2) Embed Problem Relations via ASSERT moves
       │
       ├──► (3) Pre-Call Screening Against Declared Rules
       │         • Thymic Negative Selection: Rejects unadmitted tokens
       │         • Pinned Antibodies: Blocks known cancellation laundering patterns
       │
       ├──► (4) Sovereign Host Simplex Projection (solve_graph_phi1.exe)
       │         • Computes exact gauge potentials f* and Phi_1
       │         • Monotonic Lyapunov descent: D(s_{t+1}) <= D(s_t)
       │
       ├──► (5) Obstruction Gate: Dual Witness or Topological Frame Break
       │         • If Phi_1 > 0: validate a scoped finite survivor witness
       │         • OR executes sparse L1 coboundary repair / dependency inversion
       │
       └──► (6) Policy-Authorized Receipt Logging & Replay
                 • Append-only SHA-256 hash chain with DDC letters (M, H, R, T)
                 • Replay certifies the recorded bytes and declared tool only
```

### Step 1: Declare the Finite Carrier Graph
Define vertices $V$, directed edges $E$, and exact positive integer weights $w_e \in \mathbb{Z}^+$:
```python
graph = ConstraintGraph(
    vertices=("triple_T", "mu_vec_v", "curvature_wall", "zerorel_empty", "basis_B3"),
    edges=(
        Edge("triple_T", "mu_vec_v", Fraction(1)),
        Edge("mu_vec_v", "curvature_wall", Fraction(1)),
        Edge("curvature_wall", "zerorel_empty", Fraction(1)),
        Edge("zerorel_empty", "basis_B3", Fraction(2)),
        Edge("basis_B3", "triple_T", Fraction(2)),
    )
)
gov = L1SymbolGameGovernor(graph)
```

### Step 2: Assert Active Problem Relations (`ASSERT`)
The host records edge claims without trusting proposer assertions:
```python
for (u, v), val in initial_claims.items():
    verdict = gov.step_assert(u, v, Fraction(val))
```

### Step 3: Pre-Call Screening Against Declared Rules
Before an authorized model call, run deterministic local filters:
- **Vocabulary selection:** Check proposed move verbs against the admitted alphabet $\Sigma = \{\text{ASSERT}, \text{CUT}, \text{RETRACT}, \text{VERIFY}\}$.
- **Pinned antibodies:** Match only failure patterns backed by a checked-in reproducer (for example, a trace-normalization violation or circular re-export shim).

### Step 4: Sovereign Host Simplex Projection (`CUT` via `proposed_section=gauge`)
Delegate exact $L_1$ potential minimization to an explicitly configured, digest-verified `solve_graph_phi1` adapter:
```python
norm, gauge = compute_phi1(graph, gov.claims_cochain())
verdict = gov.step_cut(proposed_section=gauge)
assert verdict.admitted and verdict.defect_after <= verdict.defect_before
```

### Step 5: Obstruction Gate (Survivor Witness or Frame Break)
- If $\Phi_1 > 0$ under locked gauge, validate the cycle cochain as a witness only within the declared finite graph.
- If the obstruction stems from a false modeling assumption, execute a topological frame break via `step_cut(proposed_claims=repaired)` (e.g., dependency inversion through a Domain Protocol port or minimal edge preemption).

### Step 6: Policy-Authorized Receipt Logging & Replay
When the active data-handling policy authorizes retention, log the normalized turn into the append-only cryptographic hash chain:
```python
entry_hash = cemetery.log(
    domain_id=domain_id,
    step_index=idx,
    proposer_type=proposer_kind,
    candidate_payload=payload,
    disposition="REFUSED_DEFECT_INCREASE",
    ddc_letter="M",
    defect_before=defect_before,
    defect_after=defect_after,
    reason="Attempted defect inflation without Stiefel condition"
)
```

---

## 3. Governor Seam Safety: `step_cut` Parameter Binding

`L1SymbolGameGovernor.step_cut` has the signature:
```python
def step_cut(
    self,
    proposed_section: Optional[Dict[str, Fraction]] = None,
    proposed_claims: Optional[Dict[Tuple[str, str], Fraction]] = None,
    step_id: Optional[str] = None,
) -> GovernorVerdict:
```

### Critical Seam Invariant
- **Vertex Potentials:** When passing node potential sections `Dict[str, Fraction]`, pass as `proposed_section=gauge`.
- **Edge Claims:** When passing edge relational claims `Dict[Tuple[str, str], Fraction]`, **MUST** pass as keyword argument `proposed_claims=claims`.
- **Anti-Pattern Warning:** Passing edge claim dictionaries positionally (`gov.step_cut(claims)`) binds to `proposed_section`, where `s.get(v)` evaluates on node strings against tuple keys, resulting in silent no-ops or false stationary verdicts.

---

## 4. Test Subtree Isolation: Native Environment Fixtures

Tests exercising `L1SymbolGameGovernor` or `compute_phi1` must receive the adapter path and digest from an explicit fixture or launching environment. Tests must not discover a parent checkout or embed a developer-specific path:

```python
import pytest

@pytest.fixture(autouse=True)
def require_functional_adapter(monkeypatch, request):
    config = request.config.stash[FUNCTIONAL_ADAPTER_CONFIG]
    monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(config.path))
    monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", config.sha256)
```

If no explicit adapter configuration is supplied, the boundary must return `NativeFunctionalUnavailable` or the test must skip with that reason.

---

## 5. Cross-Domain Empirical Evidence Summary

Evaluated across four distinct problem domains in `multi_domain_symbol_game_bouts.py` (`cross_domain_symbol_game_receipt.json`):

1. **MUB-6-shaped residual fixture:** The declared graph moves from $\Phi_1 = 5$ to a checked finite witness and then to $\Phi_1 = 0$ after a scoped edge repair. This is not a MUB(6) no-go theorem.
2. **Lock-graph fixture:** A four-vertex wait-for cycle returns the expected sparse $L_1$ edge repair and final $\Phi_1 = 0$ in this fixture.
3. **Architecture-graph fixture:** A three-vertex import cycle returns the expected port-inversion repair and final $\Phi_1 = 0$ in this fixture.
4. **Ledger-graph fixture:** A declared three-edge rate cycle returns the expected exact shadow potential and final $\Phi_1 = 0$ in this fixture; it is not a market claim.

**Evidence ceiling:** the receipt supports deterministic replay of these four checked-in inputs under the recorded adapter. It does not support token-savings, billed-cost, latency, accuracy, or arbitrary-domain claims.
