# Visual Reference & Refusal Code Cheat Sheet

> **Lead Council:** `L3_glossa` & `L3_nous_panepistimion`  
> **Audience:** All Players and Evaluators  
> **AuthorityEffect:** `None`.

---

## 1. Master System Flowchart

```text
       ┌─────────────────────────────────────────────────────────────┐
       │                   UNTRUSTED PROPOSER                        │
       │     (Continuous Heuristic / LLM / Human Operator)           │
       └──────────────────────────────┬──────────────────────────────┘
                                      │ Move Proposal ($TAU_SG_V1)
                                      ▼
                      ┌───────────────────────────────┐
                      │    BIT-LEVEL CARRIER GATE     │
                      │  • Unicode codepoints pinned? │
                      │  • core-canonical-v1 seal?   │
                      └───────────────┬───────────────┘
                                      │ PASS
                                      ▼
                      ┌───────────────────────────────┐
                      │    DISCRETE HOST GOVERNOR     │
                      │  • Recompute Phi_1 over Q     │
                      │  • Check strict descent       │
                      │  • Trace fuel consumption     │
                      └───────────────┬───────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │                                                   │
            ▼ ADMITTED                                          ▼ REFUSED
┌───────────────────────────────┐               ┌───────────────────────────────┐
│ • Apply state delta           │               │ • Roll back candidate delta   │
│ • Commit hash to trace        │               │ • Record refusal in trace     │
│ • Return remaining fuel       │               │ • Decrement turn fuel         │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │      CANONICAL RECEIPT        │
                        │ • receipt.json                │
                        │ • novella.md                  │
                        │ • dda_actions.jsonl           │
                        │ • summary.json                │
                        └───────────────────────────────┘
```

---

## 2. Refusal Code Dictionary

When the host rejects a move proposal, it emits one of the following typed refusal codes:

| Refusal Code | Category | Cause | Recovery Action |
| :--- | :--- | :--- | :--- |
| `REFUSED_CARRIER_MISMATCH` | Security | Proposal contains symbols, characters, or codepoints not in $\mathcal{C}$. | Strip all emojis, unpinned unicode, or off-carrier variables. |
| `REFUSED_MALFORMED_SYNTAX` | Protocol | Broken JSON, duplicate keys, or missing required fields. | Format the payload with NFC, the `core-canonical-v1` marker, and bare SHA-256. RFC 8785 names `jcs.rs`, not this sealer. |
| `REFUSED_CARRIER_DOMAIN` | Boundary | References vertices or edges not in the active board definition. | Inspect active board topology; use only declared edge keys (e.g. `0->1`). |
| `REFUSED_MONOTONICITY_VIOLATION`| Invariant | Proposed `CUT` increased defect or left $\Phi_1$ unchanged ($\Phi_1' \ge \Phi_1$). | Ensure proposed vertex potentials strictly decrease cycle circulation. |
| `REFUSED_NONZERO_DEFECT` | Terminal | `VERIFY` called while boundary defect $\Phi_1 > 0$ or cycle holonomies remain. | Emit valid `CUT` moves to cancel circulation before calling `VERIFY`. |
| `REFUSED_FUEL_EXHAUSTED` | Lifecycle | Turn budget reached 0 without achieving terminal verification. | Optimize move sequence; use chord decoupling guidance to solve in 1 turn. |
| `REFUSED_TERMINAL_STATE` | Lifecycle | Attempted to mutate board after terminal verification was already accepted. | Terminate session; board is sealed. |

---

## 3. Canonical Graph Topologies

```text
1. The 3-Cycle (Triangle K_3)          2. The 4-Cycle with Diagonal (Square)
   Cycle rank beta_1 = 1                  Cycle rank beta_1 = 2
        (0)                                    (0) ──────► (1)
       /   \                                    │   \       │
      /     \                                   │    \      │
     v       v                                  v     v     v
    (1) ───► (2)                               (2) ──────► (3)
   1 fundamental cycle:                   2 fundamental cycles:
   C_1 = 0->1 + 1->2 - 0->2               C_1 = 0->1 + 1->3 - 0->3
                                          C_2 = 0->2 + 2->3 - 0->3

3. The Complete Graph K_4              4. The Meron Bipartite Cluster
   Cycle rank beta_1 = 3                  Zero frustrated holonomy
        (0) ──────► (1)                        (u_1) ────► (v_1)
        │ ╲       ╱ │                            │   ╲   ╱   │
        │   ╲   ╱   │                            │     X     │
        │     ╳     │                            v   ╱   ╲   v
        │   ╱   ╲   │                          (u_2) ────► (v_2)
        v ╱       ╲ v
        (2) ──────► (3)
   3 independent coupled cycles:          Meron pairing:
   Requires matrix nullspace decoupling   Positive and negative windings cancel
   to avoid stationary looping.           topologically.
```

---

## 4. The 4-File Execution Receipt

Every certified Symbol Game session produces exactly four immutable files:

1. **`receipt.json`**: Cryptographic machine record (model, task ID, seed hash, execution trace digests, final status).
2. **`novella.md`**: Human-readable narrative detailing each turn, proposed moves, and host decisions.
3. **`dda_actions.jsonl`**: Discrete Deformation Algebra audit log containing raw model token payloads and state deltas.
4. **`summary.json`**: Key performance indicators (pass/fail status, turns consumed, fuel remaining, initial vs final $\Phi_1$).
