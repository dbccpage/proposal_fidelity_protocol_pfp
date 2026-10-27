---
documentation_contract: symbol-game-documentation/v1
title: "2_symbol_game_pfp: Proposal Fidelity Protocol (PFP) & Packet Envelopes"
kind: grammar-reference
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: specified
authority_effect: "None"
source_paths:
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/001_the_symbol_game_and_packets.md  # not found at source pin c419cc6beb (2026-10-20)
prerequisites:
  - ./meta_00_symbol_game_foundations.md
  - ./meta_01_symbol_game_historical_curriculum.md
aliases:
  - 2_symbol_game.md
  - 2_symbol_game
related:
  - ./meta_00_symbol_game_foundations.md
  - ./meta_01_symbol_game_historical_curriculum.md
  - ./meta_03_symbol_game_proof_ledger.md
last_verified: 2026-09-29
---

# 2_symbol_game_pfp: Proposal Fidelity Protocol (PFP) & Packet Envelopes

**AuthorityEffect:** None.  
**Scope:** Simple, direct, and terse exposition of the Proposal Fidelity Protocol (PFP), packet envelope schema, stealth cochains, $L_1$ projection, and the tri-lingual execution loop (Paper OE-001).

---

## 1. PFP Core Architecture: Proposer vs. Checker

The Proposal Fidelity Protocol enforces absolute separation between **generation** and **verification**:

```text
┌─────────────────────────┐       Candidate Proposal       ┌─────────────────────────┐
│     Untrusted Neural    ├───────────────────────────────►│      Deterministic      │
│     Proposer (LLM)      │◄───────────────────────────────┤    Host Checker (Rust)  │
└─────────────────────────┘      Typed Replay / Refusal    └────────────┬────────────┘
                                                                        │
                                      Emits Immutable Receipt           ▼
                                                          ┌───────────────────────────┐
                                                          │   Residual Loss Ledger    │
                                                          │   (Zero Authority Mints)  │
                                                          └───────────────────────────┘
```

1. **Untrusted Proposer:** Proposers may generate candidate tokens, syntax trees, or proof steps. Proposer output is never trusted as truth.
2. **Deterministic Host Checker:** Validates candidates against frozen schemas, cochain boundaries, and exact rational invariants.
3. **Semantic Loss Ledger & Finite Collision:** Packetization can identify semantically distinct source states under the declared finite representation; the residual loss ledger records what the selected representation does not preserve. As stated in Lean in [`lean4/TypedPacketShadow.lean`](../../../../lean4/TypedPacketShadow.lean) (`no_typed_packet_decoder_of_collision`, `L043_03`; a root of the default Lean library, not built in the 2026-10-20 check; there is no `Paper043.lean`), the existence of colliding pairs demonstrates that finite typed projections cannot admit a total semantic decoder, without asserting that every packet forgets all truth.

---

## 2. Anatomy of a Packet Envelope

Every Symbol Game packet envelope contains six frozen slots:

| Envelope Slot | Function & Formal Role |
|---|---|
| `schema_id` | Declares the immutable packet family (one of 16 canonical families). |
| `task_data` | Frozen input target and problem specification. |
| `protected_boundary` | Immutable constraints that cannot be modified by any repair operator. |
| `budget` | Exact integer limits on operations, search depth, and repair steps. |
| `candidate_payload` | The untrusted payload submitted by the proposer. |
| `witness_data` | Replayable execution trace, assignment, or proof term. |

---

## 3. Stealth Cochains & Residual Geometry

When a packet family declares a cochain representation, discrepancy is measured via combinatorial cohomology:

$$C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$$

- **Boundary Defect ($\Phi_1$):** Measures the quotient-norm distance from candidate 1-cochain $c \in C^1$ to the repair gauge $\operatorname{im}(d_0)$:
  $$\Phi_1 = \|[c]\|_{C^1/\operatorname{im}(d_0)}$$
- **Cycle Defect ($\Gamma_2$):** Measures the failure of the 1-cochain to close under coboundary $d_1$:
  $$\Gamma_2 = \|d_1 c\|_{C^2}$$
- **Total Residual ($\Xi$):** The composite invariant $\Xi = \Phi_1 + \Gamma_2$. A candidate is accepted if and only if $\Xi = 0$ over the declared observer. Because $d_1 d_0 = 0$, $\Phi_1 = 0$ already forces $\Gamma_2 = 0$, so $\Xi = 0$ exactly when $\Phi_1 = 0$. *Example (2026-10-20):* on the oriented triangle $0 \to 1 \to 2 \to 0$ with one declared face, $c = (1, 1, 1)$ gives $\Phi_1 = 3$ and $\Gamma_2 = 3$, so $\Xi = 6$; $c = (1, 1, -2)$ is $d_0(0, 1, 2)$, so $\Phi_1 = \Gamma_2 = \Xi = 0$.

---

## 4. Optional Neural Proposer Intervention: Attention Nullspace & Logit Masking (Experimental)

For systems coupling untrusted neural models directly to PFP packet generators, attention nullspace filtering provides an experimental, optional sampling constraint:

> [!NOTE]
> **Scoping & Formal Status:**  
> The identification between neural attention vector spaces $\ker(W_Q W_K^\top)$ and discrete cochain spaces $C^1$ is an empirical adapter architecture, not a general mathematical equivalence. The Lean 4 core does not mechanize neural attention weights; this mechanism is strictly an optional frontend proposer heuristic.

1. **Residual Mask Space:** Let $W_Q, W_K$ be query and key projection matrices. An experimental attention nullspace mask may be defined across embedding coordinates:
   $$\mathcal{N}_{\mathrm{att}} = \ker(W_Q W_K^\top) \cap C^1$$
2. **$L_1$-Sparse Projection:** Candidate logits are projected onto the sparse affine subspace that satisfies the declared linear boundary constraints:
   $$\min_{z} \|z - z_0\|_1 \quad \text{subject to} \quad A_{\mathrm{boundary}} z = b$$
3. **Result:** Tokens explicitly excluded by the declared boundary mask receive infinite negative logit penalties ($-\infty$), which prevents sampling of tokens explicitly excluded by the declared mask.

---

## 5. Digest Trees & Canonical Serialization

To support cross-platform determinism:
- **Canonical Serialization:** Packet payloads sealed by `PacketCodec.seal` use NFC, the `core-canonical-v1` marker, and a bare SHA-256 digest. `engine/crates_rs/core_symbol_game_runtime/src/canonical.rs` frames that digest. RFC 8785 is the separate `jcs.rs` module in that crate, not this sealer.
- **Digest:** The sealer digest is bare SHA-256. It is not a blake3 Merkle tree.
- **Symbol Stability:** Identifiers remain stable across models, toolchains, and protocol versions.

---

## 6. The Tri-Lingual Verification Loop

The verification pipeline binds three representations into an atomic receipt:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      TRI-LINGUAL VERIFICATION LOOP                     │
├─────────────────────┬──────────────────────────────────────────────────┤
│ Representation      │ Verification Role & Engine                       │
├─────────────────────┼──────────────────────────────────────────────────┤
│ 1. Native Rust      │ Executable host checker; exact/certified math;   │
│                     │ executes declared evaluator; cochain families    │
│                     │ compute exact rational residuals Φ₁, Γ₂, Ξ.      │
├─────────────────────┼──────────────────────────────────────────────────┤
│ 2. Formal Lean 4    │ Lean statements in `lean4/*.lean` (PaperER007);   │
│                     │ mechanizes finite bounds and structural lemmas.      │
├─────────────────────┼──────────────────────────────────────────────────┤
│ 3. JSON Receipt     │ Immutable receipt recording input digests,       │
│                     │ checker bytes, and scoped terminal disposition.  │
└─────────────────────┴──────────────────────────────────────────────────┘
```

### Scoped Terminal Status Taxonomy

The eight names match `CodaTerminal` in [`core_state/src/coda_gtla_protocol.rs`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs) (checked 2026-10-20). The routing axis is a separate enum, `RoutingTerminal` in [`core_types/src/routing.rs`](../../../../engine/crates_rs/core_types/src/routing.rs).

The host checker terminates in exactly one of eight typed statuses:
- `ExactRepair`: Residual resolved to zero via licensed same-level repair.
- `StabilizedSurvivor`: Residual cannot be zeroed; survives as an admitted cocycle.
- `OpenObstruction`: Residual persists; repair budget exhausted; candidate held.
- `OracleNeeded`: Verification requires an external oracle outside the active stage.
- `LiftLicenseNeeded`: Scoped exhaustion reached; qualifies for Context Extension.
- `Refused`: Candidate violates protected boundary or contains banned tokens.
- `Invalid`: Syntax error, malformed JSON, or schema mismatch.
- `InfrastructureFailure`: Resource timeout, memory exhaustion, or toolchain error.

**Governing Law:** Local green never implies global truth. Packetization never mints authority.

---

## 7. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal specification of the 6-slot packet envelope and deterministic host referee verification dynamics.
   - Bounded cohomology evaluation equations for cochain-bearing packet families and exact 8-status terminal taxonomy.
2. **What this does not support:**
   - Does not establish neural attention weights as mathematically identical to combinatorial cochains.
   - Does not grant operational authority or claim global truth from local green test vectors.
3. **The narrowest defensible claim:**
   - The Proposal Fidelity Protocol separates untrusted generation from deterministic verification across `core-canonical-v1` envelopes. The digest is bare SHA-256 over NFC text. RFC 8785 names `jcs.rs`, not this sealer.
4. **Next test needed:**
   - Cross-validate envelope schema serialization against `PacketCodec.seal`: NFC, the `core-canonical-v1` marker, and bare SHA-256.
