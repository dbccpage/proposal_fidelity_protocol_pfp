packet_type: implementation
authority_effect: None
carrier: TerminalizedRow, CheckedPacket, DescentWitness, ReplayHash, BigRational (C⁰)
primary_residual: missing loop_step Kleisli arrow (Q¹)
in_scope_repairs: loop_step signature, phi1 non-increase, replay_hash preservation, AuthorityEffect::None firewall (d₀)
deferred_residuals: stagnation detection, bounded retry count, strict-improvement preference, cycle detection, observer-law idempotency, multi-step descent proptest, epk_row_shape_extension
seal_condition: terminalize_row returning Decision::Certified on fixture row composition test

Core Certifier Loop (Obstruction Packet)
=========================================

**Packet date:** 2026-06-20
**App:** `core_certifier_loop` — greenfield diagnostic **guard-only no-op** Kleisli step over sealed rows (honesty pass 2026-06-22: the arrow is a guard, not an "improver" — see §13).
**Carrier crates:** `core_certifiers`, `core_pipeline`, `core_homology`, `core_functional`, `core_discrete_deformation_algebra`.
**Authority surface:** none. This packet does not mint authority. Only `core_sweep_kernel::terminalize_row` and `core_certifiers::certify_checked_packet` can do that, and they sit outside the loop step described here.
**Bundle status (A2):** load-bearing, no sibling lemma-packets. The whole `core_certifier_loop` descent — single missing Kleisli arrow with two named defects (Q1-S, Q1-D) — fits inside one packet's $d_0 \to d_1$ flow; no separate context-exposure (DDA `C`) lemma-packets are required.

Defect roster (A1 keys)
-----------------------

This packet carries two named defects inside the one 2-window. All per-defect tables (§§8, 9, 10, 13) are keyed by these IDs:

| Defect ID | Statement |
|-----------|-----------|
| **Q1-S** | Seal preservation under composition: `then(loop_step, loop_step)` produces an intermediate `CheckedPacket` whose manifest hash equals the manifest hash of the same row computed by a single-step descent (closure leg of $d_1$). |
| **Q1-D** | $\Phi_1$ non-increase under improvement: on every Acceptance branch, `row_out.phi1().value() <= row.phi1().value()` as `BigRational` (quotient leg of $Q^1$). |

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** Sealed terminalized rows that have already passed the `CheckedPacket` boundary in `core_certifiers::checked_packet` and now sit as data on the descent ledger (manifest hash + verified $\Phi_1$ certificate + verified $\Gamma_2$ residual + recorded `DescentWitness::replay_hash`). The carrier is the preorder $(\mathcal{R}, \le_{\Phi_1})$ on such rows, ordered by the verified-exact $\Phi_1$ value carried in their attached `VerifiedExactPhi1` (smaller is better). The 2-window inspects (row at step $n$, candidate Meta $\Meta_n$, row at step $n+1$): three slots wide, no further look-ahead. `core_pipeline::kleisli` supplies the Kleisli ambient (`Refusable<Y>` monad) in which loop step arrows compose; the EPK lane (`core_epk`) observes but does not adjudicate.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** The current local assignments are the present-day shape of the two crates plus their seams:

* `core_certifiers::checked_packet::{CheckedPacket, CheckedPacketArgs, CertificateVerdict}` — the data the loop reads from a terminalized row. The constructor is `CheckedPacket::new_checked(args)` (there is no `try_new`).
* `core_certifiers::certify_checked_packet(packet: &CheckedPacket, witness: DescentWitness, is_auth: IsAuth) -> Result<CertifiedAuthority, TerminalizeError>` — re-exported at the crate root; the only minting bridge in `core_certifiers`; the loop step MUST NOT call it.
* `core_sweep_kernel::terminalize_row(row: &serde_yaml::Value, author_model: &str, gate_model: &str) -> TerminalRecord` — the OTHER minting bridge (free fn, no `Result`); the loop step MUST NOT call it. Success path is `Decision::Certified` with `host_terminal_status == "Certificate"` (NOT `"Repaired"`).
* `core_pipeline::kleisli::{id_k, compose_k, then}` over `core_types::Refusable` — composition machinery the loop step plugs into.
* `core_pipeline::pipeline` — the existing five-stage $\Pi_S^{\#}$ shape (STORY-110-003) which currently has no improver stage.
* `core_homology::CochainPrimitiveDifference`, `CochainComplex::d0`, `CochainComplex::d1`, `QuotientSpace` — the cochain carrier behind a row.
* `core_functional::phi1::VerifiedExactPhi1` (accessors: `.value() -> &BigRational`, `.primal_residual() -> &[BigRational]`, `.d0() -> &[Vec<BigRational>]`, `.alpha() -> &[BigRational]`, `.dual_witness() -> &[BigRational]`; sole constructor is `Phi1Functional::verify_exact_certificate(cert)`), `core_functional::gamma2::ExactGamma2Result` (accessors: `.residual()`, `.d0()`, `.coboundary()`, `.value() -> &BigRational`; sole constructor is `Gamma2Functional::try_compute_exact_quotient(&residual)`), `core_functional::Observer` (struct of `{id: String, kind: ObserverKind}` — NOT a trait, NO `.observe()` method) — the verified obstruction masses attached to the row.
* `core_discrete_deformation_algebra::{FaceLambda, NonDestructiveExtensionCertificate, FiniteLambdaStepCertificate}` — the Meta vocabulary the loop must accept as input. Note these crate / type names are PRESERVED per the 2026-06-20 vocab ruling (the doctrine rename "lift → Meta" applies to prose; Rust type names are unchanged).
* `core_epk::EpkResidualLedger` — diagnostic-only carrier; `ledger.authority_effect()` ALWAYS returns `AuthorityEffect::None` and `ledger.as_outcome()` ALWAYS returns `Outcome::Refused(RefusalSource::Residual)` by firewall contract. `core_types::authority::AuthorityEffect` has FOUR variants: `None` / `Certified(CertifiedAuthority)` / `Refused` / `Uncertified` — there is NO `EvidenceOnly` variant.

There is no `loop_step` arrow anywhere in `core_pipeline::src/` today (the `kleisli`, `gtlanf`, `pipeline` modules cover composition, the GTLA-NF normal form, and the five-stage pipeline only). Improvement is therefore a manual edit between cycles.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Permitted primitive cochain moves on a row:

* Apply a `CochainPrimitiveDifference` along $d_0$ inside `core_homology` (gauge slide on $C^0$).
* Rephrase a row by an internal rename / reorder of `EvidenceRef` entries inside `CheckedPacketArgs` that does not change the manifest hash.
* Replace a candidate $\Meta$ proposal by a propositionally equal `FaceLambda` (same face $F$, same coefficient).
* Compose two Kleisli arrows via `core_pipeline::kleisli::compose_k` provided neither escapes the refusal monad.

None of these moves are allowed to change the verified $\Phi_1$ value of an already-sealed row; sealed rows are immutable carriers.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):**

1. There is no Rust arrow of type `fn(row: TerminalizedRow, meta: MetaCandidate) -> Refusable<(TerminalizedRow, EpkResidualLedger)>` in the workspace (the diagnostic carrier type is `core_epk::EpkResidualLedger`, NOT a non-existent `EpkDiagnostic`). The improvement loop is hand-driven between sprints.
2. The five-stage `Π_S^{#}` pipeline in `core_pipeline::pipeline` exposes no extension hook for an improver stage that could be `then`-composed without copy-pasting the whole pipeline.
3. There is no $\Phi_1$-non-increase invariant anywhere — nothing in the crate stack mechanically forbids a hand-written improver step from ACCEPTING a candidate whose attached `VerifiedExactPhi1` value strictly exceeds the predecessor's.
4. There is no documented diagnostic-only contract for the loop output; an ad-hoc improver could accidentally attach an `core_types::authority::AuthorityEffect` value other than `AuthorityEffect::None` (e.g. construct an `AuthorityEffect::Certified(CertifiedAuthority)` payload from inside the loop step) and trip the authority firewall. The only valid loop-step `AuthorityEffect` is the bare unit `AuthorityEffect::None` returned by `EpkResidualLedger::authority_effect()`.
5. There is no property test in `core_pipeline` exercising "for all (row, Meta) accepted by the loop, $\Phi_1(\text{out}) \le \Phi_1(\text{in})$".

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two candidate loop steps $L, L'$ are gauge-equivalent when, for every accepted input row $r$ and every Meta candidate $m$ that both accept:

* The post-rows agree up to `CheckedPacket` manifest hash equality (`packet_id`, `schema_hash`, `carrier_hash`, `payload_hash` all equal — i.e. the rows are indistinguishable by `core_certifiers::checked_packet`).
* The verified $\Phi_1$ values agree as `BigRational` (the `VerifiedExactPhi1::value()` getters return equal `&BigRational` in $\mathbb{Q}$).
* The attached `core_epk::EpkResidualLedger` diagnostics differ only in serialization order (no behavioral difference under the firewall: both `ledger.authority_effect()` calls return `AuthorityEffect::None` and both `ledger.as_outcome()` calls return `Outcome::Refused(RefusalSource::Residual)` — the diagnostic-only firewall contract on `core_epk` is unchanged).

Any internal refactor of the loop step body that preserves these three is a $d_0$-gauge move and is identified to zero.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** Modding out ZeroRel from $C^1$ leaves one non-removable class:

> **PRIMARY RESIDUAL Q1.** The missing Kleisli arrow `loop_step(row, $\Meta$_candidate) -> Refusable<(row', diagnostic)>` with the invariant `Phi_1(row') <= Phi_1(row)` on the Acceptance branch and a typed refusal on the Reject branch.

Defects (2)–(5) collapse into Q1 once it is discharged: an arrow with this signature, plumbed via `core_pipeline::kleisli::then`, automatically provides the extension hook for $\Pi_S^{\#}$ (defect 2); the invariant is the missing $\Phi_1$ guard (defect 3); typing the output's attached `EpkResidualLedger` such that `ledger.authority_effect() == AuthorityEffect::None` discharges defect 4 by construction (positive AND negative case: a unit test that attempts to construct a non-`None` `AuthorityEffect` from inside the loop step must fail at the type level or be rejected by the Reject branch); and a `proptest` over its acceptance branch discharges defect 5. None of these survives as an independent residual.

**Q1 sub-leg checklist (each MUST have a matching AT in the sprint discharging this packet):**

* Q1-Φ: $\Phi_1(\text{row}') \le \Phi_1(\text{row})$ on Acceptance, measured as `BigRational` comparison of `row.phi1().value()` vs `row_out.phi1().value()`.
* Q1-R: `row.replay_hash` is preserved verbatim into the emitted diagnostic's audit field (must also be checked under the proptest, not only in a single-case test — packet §11 preservation witness has TWO conjuncts and both must travel with the proptest).
* Q1-A: `ledger.authority_effect() == AuthorityEffect::None` POSITIVE case AND a NEGATIVE-case test that the loop step cannot mint a non-`None` `AuthorityEffect` (the firewall-leakage leg of §8's third Γ₂ failure).
* Q1-S: under `then(loop_step, loop_step)` the sealed-boundary invariant (§7 d_1 second clause) holds — the `CheckedPacket` manifest hash of the intermediate row that survives composition is bit-identical to the manifest hash of the same row computed by a single-step descent. This is "seal-preservation under composition" and is NOT discharged by Kleisli identity/associativity laws alone.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Closure on a triple $(\text{row}_n, \Meta_n, \text{row}_{n+1})$:

* The output row must round-trip through `CheckedPacket::new_checked` (NOTE: the actual constructor is `core_certifiers::checked_packet::CheckedPacket::new_checked`; there is no `try_new`) — i.e., its attached `VerifiedExactPhi1` is reproducible from the row's recorded `ReplayHash` and the descent witness.
* The Kleisli composition law holds at the seam: `then(loop_step, loop_step)` of two acceptance branches yields the same output row as one direct two-step descent — no drift across the sealed boundary. Concretely: the `CheckedPacket` manifest hash of the composed-step output equals the manifest hash of two single-step outputs glued by a $d_0$ gauge move. This "seal-preservation under composition" is a SEPARATE leg from the Kleisli identity/associativity laws and MUST be witnessed by its own AT (see Q1-S in §6).
* The diagnostic emitted by the loop step carries an `core_epk::EpkResidualLedger` whose `authority_effect()` returns `AuthorityEffect::None` and whose `as_outcome()` returns `Outcome::Refused(RefusalSource::Residual)`, so it can pass through the certifier without ever entering the `certify_checked_packet` path.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass — per defect, A1):**

| Defect | $\Gamma_2$ | Witness |
|--------|-----------|---------|
| **Q1-S** | $> 0$ | Hand-edited improver rounds (current practice) cannot compose as `then(L, L)` — there is no `L` at the type level, so the seal-preservation square `(row -> row' -> row'') vs (row -> row'')` cannot even be formed. The closure of two consecutive single-step descents against one direct two-step descent is structurally non-cocycle: the intermediate `CheckedPacket` manifest hash does not exist as a typed object that downstream consumers can compare. |
| **Q1-D** | $> 0$ (firewall-leg) | Two superimposed failures on the $d_1$ leg: (i) no $\Phi_1$ guard exists, so a hand-edited step that raises $\Phi_1$ silently survives the seam (the closure of "accepted improvement" with "diagnostic-only output" fails on the $\Phi_1$ leg); (ii) no diagnostic-only contract is declared, so an improver could leak a non-`AuthorityEffect::None` value across the seam to a downstream consumer (e.g. attach an `AuthorityEffect::Certified(_)` payload to its output) — this is the firewall-leakage leg attached to Q1-D's quotient. |

Aggregate: $\Gamma_2$ is non-trivially positive but mass-bounded — exactly the two failure legs above, and discharging Q1 (both Q1-S and Q1-D witnesses) collapses both simultaneously.

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass — per defect, A1):**

| Defect | $\Phi_1$ | Witness |
|--------|---------|---------|
| **Q1-S** | $> 0$ | The non-gauge mass is the absence of a `loop_step` Kleisli arrow whose `then(loop_step, loop_step)` provably preserves the `CheckedPacket` manifest hash at the intermediate seam. No $d_0$ move can manufacture this arrow — a new top-level Kleisli arrow in `core_pipeline` is a structural extension, not a gauge slide. Localized in `engine/crates/core_pipeline/src/`. |
| **Q1-D** | $> 0$ | The non-gauge mass is the absence of a typed $\Phi_1$ non-increase invariant on the same `loop_step` arrow: nothing in the crate stack mechanically forbids accepting a candidate whose attached `VerifiedExactPhi1` value strictly exceeds the predecessor's. This is one residual class, finite, concretely localized in `engine/crates/core_pipeline/src/`. The non-`None` `AuthorityEffect` leakage (firewall leg) rides on this same residual: until the loop-step type signature pins the diagnostic output's `authority_effect()` to `AuthorityEffect::None`, the $\Phi_1$-non-increase contract and the firewall contract are jointly under-typed. |

Aggregate note: Q1-S and Q1-D share one structural cause (the missing `loop_step` arrow), but they sit on different cochain legs — Q1-S on the closure leg ($d_1$) and Q1-D on the quotient leg ($Q^1$) — and so are reported per-defect under A1 even though a single PR can discharge both simultaneously.

10. Classify System State
-------------------------

**Classification (per defect, A1):**

| Defect | Class | Note |
|--------|-------|------|
| **Q1-S** | ActiveClosureFailure | $\Gamma_2 > 0$ on the composition-seam leg; the local $d_0$ vocabulary cannot generate the missing Kleisli arrow whose `then(L, L)` preserves manifest hashes, so a Meta is licensed. |
| **Q1-D** | ActiveClosureFailure | $\Gamma_2 > 0$ on the firewall leg AND $\Phi_1 > 0$ on the non-increase leg; the local $d_0$ vocabulary cannot manufacture a typed $\Phi_1$ non-increase invariant or an `AuthorityEffect::None` pin, so a Meta is licensed. |

Aggregate: both defects land in **ActiveClosureFailure**. None are ExactRepair, ClosedSurvivor, or NoRule. Because both defects are ActiveClosureFailure and licensed by the same missing arrow, the Meta of §11 discharges both simultaneously.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**Oracles required (A3):** none. The Meta proposed below is built entirely from the declared finite 2-window — `core_pipeline::kleisli`, `core_discrete_deformation_algebra::{FaceLambda, NonDestructiveExtensionCertificate, FiniteLambdaStepCertificate}`, `core_functional::{phi1, gamma2, Observer}`, and `core_epk::EpkResidualLedger` — and licenses no transformation from outside that window. No imported representation theorem is invoked; no sub-claim acquires the `OracleNeeded` terminal.

**$\Meta$ (Lift / Structural Extension):** Introduce one new lambda `loop_step` and bind it to a `FaceLambda` instance whose face $F$ is the new Kleisli arrow's signature.

Concretely:

* Pin $\Meta$ as a `FaceLambda<LoopStepFace>` (constructed via `FaceLambda::new(face, capacity)` from `core_discrete_deformation_algebra`) where `LoopStepFace` is a new face type added under a new sibling module `core_pipeline::loop_step` carrying the signature
  $$ \Meta : (\text{TerminalizedRow}, \Meta_{\text{cand}}) \longrightarrow \mathrm{Refusable}\bigl((\text{TerminalizedRow}, \mathrm{EpkResidualLedger})\bigr). $$

* **Obstruction witness:** the live $\Phi_1$ value attached to the input row, read as `row.phi1().value()` returning `&BigRational` (the real accessor is `VerifiedExactPhi1::value()`, NOT `reported_value()`).
* **Preservation witness:** a `NonDestructiveExtensionCertificate` from `core_discrete_deformation_algebra`, constructed via `NonDestructiveExtensionCertificate::new(preserves_old_vertices, preserves_old_edges, records_tradeoff)`. Its three `bool` fields encode the loop-step contract as:
  * `preserves_old_vertices = true` iff $\Phi_1(\text{out}) \le \Phi_1(\text{in})$ pointwise in $\mathbb{Q}$ (no new "vertex" of obstruction mass introduced);
  * `preserves_old_edges = true` iff the input row's `replay_hash` is preserved verbatim in the diagnostic's audit field (no sealed "edge" between row and replay re-routed);
  * `records_tradeoff = true` iff the Acceptance branch records the input $\Phi_1$ and output $\Phi_1$ values in the emitted `EpkResidualLedger` (the trade-off is recorded, not hidden).
  The certificate is then sealed by `require_non_destructive()` returning `Ok(self)` only when all three are `true`. NOTE: the underlying `NonDestructiveExtensionCertificate` is a three-bool gate, not a `BigRational` comparator — the actual numeric comparison is performed by the loop step body and is recorded into the three booleans as a precondition for constructing the certificate.

* **Non-destruction check:** a `FiniteLambdaStepCertificate` wrapping the above `NonDestructiveExtensionCertificate`, constructed via `FiniteLambdaStepCertificate::new(before, after, extension)` where `before` and `after` are `FiniteDiagnostic { phi1: u64, gamma2: u64 }` snapshots and `extension` is the preservation witness above; sealed by `require_valid()` returning `Ok(self)` only when (1) `before` has obstruction, (2) `after` is resolved (`phi1 == 0` AND `gamma2 == 0`), (3) the extension is non-destructive. WARNING: `require_valid()` enforces that the after-step is fully resolved — for the proptest's "non-increase" leg (which permits `phi1_after > 0`) construct an UNSEALED `FiniteLambdaStepCertificate` and assert only the `before`/`extension` fields; reserve `require_valid()` for the terminal seal in S8 against a fixture row that descends to $\Phi_1 = 0$.
* **Terminalizer route:** none from inside the loop step. The new arrow MUST refuse (typed `Refusable::Refused(RefusalSource::Refusal)`) any attempt to bypass the existing terminalizer; sealing the new row is exclusively the job of `core_sweep_kernel::terminalize_row` (free fn returning a `TerminalRecord` whose success path is `Decision::Certified` with `host_terminal_status == "Certificate"`) / `core_certifiers::certify_checked_packet`, called downstream by an unchanged stage of $\Pi_S^{\#}$.

**GTOC-3 (lift trigger != lift license):** the Meta is licensed only when both the `NonDestructiveExtensionCertificate` and the (unsealed-or-sealed) `FiniteLambdaStepCertificate` are constructed and attached to the diagnostic in the SAME emit. The sprint discharging this packet MUST land the Meta and both witnesses in a single PR — splitting the Meta introduction across two PRs (one introduces the lambda, a later one attaches the witnesses) is a GTOC-3 violation and the adversary gate (b) must block it.

This is a lift, not a repair: the new arrow extends the lambda vocabulary of `core_pipeline`. It is licensed by Q1 + the architecture rule that diagnostic improvers are first-class Kleisli arrows under the refusal monad.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):**

1. **Gauge slide ($E$):** Normalize the input row via `core_homology::CochainPrimitiveDifference` so that its $d_0$-image is canonical; this is a pure $d_0$ move and changes nothing observable.
2. **Quotient projection ($R$):** Read off the input `VerifiedExactPhi1` and the input `ExactGamma2Result` from the row; project to the quotient class in $Q^1$ via `core_functional::Observer`.
3. **Lambda lift ($\Meta$):** Apply the new `FaceLambda<LoopStepFace>` to the pair (row, Meta candidate). On Acceptance, emit `(row', ledger)` where `ledger: EpkResidualLedger` carries the `NonDestructiveExtensionCertificate` and `FiniteLambdaStepCertificate` (the latter unsealed by `require_valid()` unless the step achieves `phi1_after == 0`); on Reject, emit `Refusable::Refused(RefusalSource::Refusal)` via `core_types::Refusable`.
4. **Descent ($D$):** Compose the new arrow with the existing $\Pi_S^{\#}$ via `core_pipeline::kleisli::then`, so the next pipeline stage sees `row'` as if it had always been there. The terminalizer route stays where it is — `core_sweep_kernel::terminalize_row` continues to be the sole minter — and the loop step does not touch it.

Property test (mechanizes the invariant in §6 — covers BOTH Q1-Φ AND Q1-R legs of the preservation witness):

```
cargo test -j 1 -p core_pipeline loop_step::phi1_nonincrease_and_replay_hash_preserved
```

A `proptest` generator over `(row, Meta candidate)` pairs from the existing `core_functional::phi1::tests` fixtures must show, on every `Refusable::Value((row_out, ledger))` branch and across at least 256 cases:

1. `row_out.phi1().value() <= row.phi1().value()` as `&BigRational` (Q1-Φ leg).
2. The `replay_hash` recorded on the emitted `ledger` matches `row.replay_hash` bit-for-bit (Q1-R leg).

A separate test (NOT under proptest; this is the negative case for the firewall leg) must assert: any attempt by the loop-step body to attach an `AuthorityEffect` value other than `AuthorityEffect::None` is either a compile-time error (preferred) OR is rejected at runtime by the Reject branch (Q1-A leg).

A separate integration test under `tests/` (composition-seam witness, Q1-S leg) must compose `then(loop_step, loop_step)` on a fixture row and assert that the intermediate `CheckedPacket` manifest hash matches the manifest hash produced by a single-step direct descent — this is seal-preservation under composition and is NOT implied by Kleisli identity/associativity.

13. Terminal Status
-------------------

**Terminal Status (per defect, A1; with A4 Current / Target / Seal Condition split):**

| Defect | Current | Target | Seal Condition |
|--------|---------|--------|----------------|
| **Q1-S** | ActiveClosureFailure | **CONDITIONAL** (guard-only) | **DEMOTED 2026-06-22 (red-team #911 P1 L6).** The arrow is a **guard-only no-op**: on Acceptance the row is propagated verbatim, so the seal-preservation equality is a *guard invariant* (the guard does not break the seal between `then(guard, guard)` and a single pass) and NOT a witnessed non-identity descent. The seam AT (`loop_step::compose::seal_preserved_under_composition`) is genuine for the guard (and now carries an `assert_ne!` discriminator proving `manifest_hash` is not constant), and S8 (`tests/loop_step_terminalize.rs::terminalize_row_seal_certificates_on_loop_output_derived_input`) feeds `core_sweep_kernel::terminalize_row` an input DERIVED from the loop output's manifest hash (returns `Decision::Certified` / `host_terminal_status == "Certificate"`). Q1-S is CONDITIONAL on a future arrow performing a real manifest-hash-invariant non-identity rewrite — which is **not available** on a sealed `CheckedPacket` (it derives `Serialize` over an ordered `evidence_refs`, so any reorder changes the hash). Until such an arrow exists, this stays CONDITIONAL / Lift-Needed. |
| **Q1-D** | ActiveClosureFailure | **CONDITIONAL** (Φ leg guard-only; A/R legs Repaired) | **Q1-Φ DEMOTED 2026-06-22 (red-team #911 P1 L6/L4).** The arrow does not apply the candidate delta to the row, so `row_out.phi1().value() <= row.phi1().value()` is `x <= x` (a guard invariant, NOT a witnessed descent) — the candidate's proposed delta is *surfaced* in the diagnostic's `output_phi1` audit field for a downstream rewrite scheduler outside the sealed boundary. The Q1-A firewall leg (`authority_effect() == AuthorityEffect::None`, positive + negative tests) and the Q1-R replay-hash-preservation leg ARE genuinely discharged. The NDEC gate is now DISCRIMINATING: `preserves_old_edges` is derived (a destructive candidate makes `require_non_destructive()` FAIL → refuse, proven by `reject::require_non_destructive_fails_on_destructive_candidate`) and `records_tradeoff` is gated on the emit. Q1-Φ stays CONDITIONAL until the arrow performs a real Φ₁-decreasing rewrite. |

NOTE on vocabulary: this packet's "Repaired" Target label is the GTOC canonical terminal status for the obstruction-packet ledger and is NOT a `Decision` variant on `TerminalRecord`. The actual `core_sweep_kernel::terminalize_row` returns `TerminalRecord { decision: Decision::Certified | Killed | Obligation | DeferredToValidator | RefusedHostAuthority | NotGated, host_terminal_status: "Certificate" | "OracleNeeded" | "Refusal", ... }` — there is no `Decision::Repaired` and no `host_terminal_status == "Repaired"`. The Seal Condition above names the real `Decision::Certified` / `host_terminal_status == "Certificate"` gate on `core_sweep_kernel::terminalize_row` (per the firewall: that function and `core_certifiers::certify_checked_packet` are the only authority-minting paths); this packet's "Repaired" label is bookkeeping for the GTOC packet ledger, applied by the sprint's S8 markdown edit after the seal succeeds.

Aggregate discharge condition (both defects collapse together): the `loop_step` arrow ships in `core_pipeline`, the `proptest` above passes under `cargo test -j 1`, the composition-seam AT passes, the negative-case firewall test passes, and the `core_epk` output carries an `EpkResidualLedger` whose `authority_effect()` returns `AuthorityEffect::None`. The minting boundary (`core_sweep_kernel::terminalize_row`, `core_certifiers::certify_checked_packet`) is unchanged and stays outside the loop. Until those hold, both defects remain in the Active-closure-failure class of §10.

**Closure note (2026-06-21, SUPERSEDED).** Both defects were originally stamped `Repaired`. This was an OVERCLAIM (red-team #911 P1 L6): it rested on cannot-fail tests (`x <= x` Φ₁ non-increase, hash-of-clone seal, hardcoded-`true` NDEC booleans) over an identity arrow.

**Honesty revision (2026-06-22, red-team #911 remediation).** The `loop_step` arrow is now honestly classified a **guard-only no-op** (it gates a candidate and surfaces the proposed delta for a downstream scheduler; it does NOT rewrite the sealed row — per packet §3 sealed rows are immutable carriers, and no manifest-hash-invariant non-identity rewrite exists on a `CheckedPacket`). Accordingly:

* **Q1-Φ and Q1-S are DEMOTED to CONDITIONAL** (see the §13 table). They are guard invariants, not witnessed descents.
* **Q1-A (firewall) and Q1-R (replay-hash) ARE genuinely discharged** by discriminating tests.
* The NDEC gate is now **discriminating**: a destructive candidate makes `require_non_destructive()` FAIL and the arrow refuse (negative control `loop_step::tests::reject::require_non_destructive_fails_on_destructive_candidate`), paired with the positive control `non_destructive_candidate_is_accepted_with_sealed_ndec`.
* The S8 terminal-seal integration test is now `engine/crates/core_pipeline/tests/loop_step_terminalize.rs::terminalize_row_seal_certificates_on_loop_output_derived_input`: it DERIVES the `terminalize_row` input from the loop output's manifest hash (binding it into the YAML `packet_id` + `required_witness`) and asserts the sealed record carries that derived id back — a genuine round-trip, not two disjoint fixtures. It confirms the kernel success arm (`Decision::Certified` + `host_terminal_status == "Certificate"` + `authority_ceiling == "established_within_declared_scope"` + `status == "survived"`).
* The 256-case proptest `loop_step::phi1_nonincrease_and_replay_hash_preserved` carries a live cross-case non-vacuity guard (`value_branch_observed_at_least_16_times`) replacing the dead per-case `Cell`.

All the above are green under `cargo test -j 1 -p core_pipeline`.

**Q1 sub-leg accounting (each must be discharged or explicitly deferred). Mapping to the A1 defect IDs above: Q1-Φ, Q1-R, Q1-A all feed Q1-D's seal condition; Q1-S (here) is the same defect named Q1-S in the per-defect table at the top of the packet:**

* Q1-Φ — `Phi_1(out) <= Phi_1(in)` (feeds Q1-D): **CONDITIONAL (2026-06-22).** The guard does not apply the candidate delta, so this is `x <= x` — a guard invariant, not a witnessed descent. The 256-case S7 proptest checks it on the guard; the proposed delta is surfaced in `output_phi1` for downstream rewrite scheduling. CONDITIONAL until a real Φ₁-decreasing rewrite exists.
* Q1-R — replay_hash preservation (feeds Q1-D): **discharged** by the sprint's S7 proptest (256+ cases, second conjunct: `row_out.replay_hash()` and `diag.prev_replay_hash` both equal the input).
* Q1-A — non-`None` `AuthorityEffect` cannot be attached (feeds Q1-D's firewall leg): **discharged** by the S4 negative-case test (`firewall::cannot_attach_non_none_authority_effect` sweeps all ledger states) + the discriminating positive control (`firewall::firewall_pin_catches_a_non_none_authority_effect`).
* Q1-S — seal-preservation under `then(loop_step, loop_step)`: **CONDITIONAL (2026-06-22).** A genuine guard invariant (the seam AT `loop_step::compose::seal_preserved_under_composition` compares `CheckedPacket` manifest hashes AND carries an `assert_ne!` discriminator), but it is hash-equality between the SAME propagated sealed carrier, not a non-identity descent. CONDITIONAL until a manifest-hash-invariant non-identity rewrite exists (unavailable on the current `CheckedPacket` `Serialize` shape).

`defer:` (residuals carried out of this packet to a successor):

* `defer: loop_step_convergence_packet` — successor packet for convergence guarantees, addressing:
  * **stagnation detection** (detecting when descent makes no progress)
  * **bounded retry count** (guarding against infinite loops in automatic improvement)
  * **strict-improvement preference** (preferring steps that strictly decrease $\Phi_1$ over those that merely non-increase)
  * **cycle detection** (breaking infinite cycles across loop steps)
  * **observer-law idempotency** (originally deferred to `loop_step_followup_packet#loop_step_observer_idempotency`)
  * **multi-step descent proptest** (originally deferred to `loop_step_followup_packet#multi_step_descent_proptest`)
* `defer: loop_step_followup_packet#epk_row_shape_extension` — if the `EpkResidualLedger` shape needs to grow to carry the obstruction / preservation / non-destruction witnesses inline (rather than alongside as audit fields), that is an `core_epk` structural extension, has its own NDEC/FLSC, and belongs in a separate packet bound to `core_epk`.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_pipeline::rewrite_scheduler::schedule_exact_rewrite` applies a proposed non-identity exact input through `core_pipeline::gtoc_gtla::evaluate_exact`, and the focused scheduler tests are present. Bounded retry/stagnation controls, complete consumer closure, and a current terminal receipt remain owned by `S16-004`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest and supersedes guard-only implementation language while preserving its historical defect statement.

15. S16-004 bounded-rewrite disposition
---------------------------------------

At frozen base `46d91fb4165e6cb83fbb8c41168ed56739db478e`, S16-004 packet `01bd1e82e29810bf940ae962ebf3b50c87b54ba79dfd42a1d9dedfedc8f55e7b` supersedes the guard-only current-state description for the admitted scheduler carrier. Every unsealed candidate is exact-evaluated, replay identity is checked before descent, and selection prefers maximum exact Phi1 reduction then Gamma2 reduction. The controller bounds attempts and steps, detects known-state cycles and stagnation, and runs an observer gate without mutating sealed rows or diagnostics.

The 11 focused tests include a nonidentity two-step `OpenObstruction -> StabilizedSurvivor -> ExactRepair` trace, Phi1-first preference, and deterministic stagnation, cycle, retry-exhaustion, and observer-refusal cases. Output retains `AuthorityEffect::None`. This is finite bounded evidence; it does not prove global termination, global optimality, an EPK row-shape extension, or autonomous succession.
