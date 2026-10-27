packet_type: implementation
authority_effect: None
carrier: HTTP request/response edge (Axum Router)
primary_residual: POST /solve endpoint with type-safety and JSONL lane logging (Q¹)
in_scope_repairs: Axum handler setup, DTO mapping, feature gate default OFF, firewall canary tests (d₀)
deferred_residuals: live cutover traffic, immune loop ingestion, Lean d₁ mechanization, live LLM CandidateSource
seal_condition: terminalize_row returning Decision::NotGated on FixtureSource lane tests

Core API Flagship (Obstruction Packet)
=======================================

**Date:** 2026-06-20
**App:** `core_api` (greenfield Axum binary under `engine/core_api/`, EPK business-contracts stack)
**Role:** Flagship Rust HTTP surface for `api.sentinel.com`; routes prompts -> `PromptPacket` -> Symbol Game lambda -> EPK diagnostics -> `terminalize_row`, returning ONLY a terminalized residual + obstruction packet, never an authority claim. Replaces (behind a feature flag, no cutover) the Next.js `sentinel_ai` MVP that currently mints prose authority on the public site.

**Bundle status:** load-bearing, no sibling lemma-packets. The Next.js `sentinel_ai/web/` MVP is out of scope per the current packet (kept in `$C^0$` as a black box). Per **A2**, this packet is the single load-bearing descent packet for the core_api 2-window; no supporting context-exposure (DDA `C`) lemma-packets are declared.

**Defect roster (used by the A1 per-defect tables in S8, S9, S10, S13):**

* `D_packetize` — HTTP request body is not packetized into `PromptPacket` (raw text crosses the edge; spec §10 invariant 8).
* `D_route` — no Rust path composes `PromptPacket -> SgSession::solve_with -> core_epk` Δ_E from an HTTP request.
* `D_terminal` — no `terminalize_row` emission from HTTP; lane JSONL ledger has no carrier.
* `D_canary` — markdown/TS prose paths can mint authority (firewall breach); no canary forbids `certify_checked_packet` from HTTP.
* `D_byteshape` — workspace byte-shape under `default` may drift; `sentinel_ai/web/` byte-equivalence is not pinned.

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The HTTP request/response carrier `(POST /solve, json body) -> (200, json terminal row)` realized as an Axum service over the shared diagnostic core. The 2-window is the boundary pair $(\text{intake}, \text{terminal})$:

* left slot: an incoming prompt shape ingested through `core_prompt_packets::PromptPacket` (typed, replayable, hashed-shape-only per spec §8/§9);
* right slot: the terminal row emitted by `core_sweep_kernel::terminalize_row` (free fn at `core_sweep_kernel::terminalize::terminalize_row`), signature `(row: &serde_yaml::Value, author_model: &str, gate_model: &str) -> TerminalRecord`, whose `Decision` is one of the six real variants `{Certified, Killed, Obligation, DeferredToValidator, RefusedHostAuthority, NotGated}` (no `Repaired`/`Survived` vocab — those live on a different type, `core_discrete_deformation_algebra::TerminalStatus`) and whose `host_terminal_status` string field uses TitleCase tokens `{Certificate, OracleNeeded, Refusal}`. The lane ledger is append-only JSONL.

The carrier is structured as an EPK business-contracts stack adapter (`core_facade` -> `core_business_contracts` -> `core_infra` -> `core_api`), so the HTTP edge is the only I/O site; all inner lambdas remain pure libraries.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** The existing in-tree types and crates that the API must compose without rewriting:

* `core_homology::cochain_primitive_difference::CochainPrimitiveDifference`, `core_homology::cochain_complex::CochainComplex::{d0,d1}`, `core_homology::quotient::QuotientSpace` (carrier and cochains);
* `core_functional::phi1::VerifiedExactPhi1`, `core_functional::gamma2::ExactGamma2Result`, `core_functional::observer::Observer` ($\Phi_1$ / $\Gamma_2$ instruments);
* `pfp::{SgSession, FamilyDriver, SgOutcome, SgTrace}` (LP lambda over `core_representation`);
* `core_epk` (Δ_E, G1-G4, `EpkResidualLedger`);
* `core_llm_gateway::{CandidateSource, FixtureSource, LlmCandidateSource, CandidateRequest, GatewayError}` (Gauge Breaker, performer-only);
* `core_sweep_kernel::terminalize_row` (sole minting site, private `Seal`, `author_model != gate_model` enforced) and `core_certifiers::certify_checked_packet` (the only authority bridge);
* `core_corrigibility::{halt, check_edit, verify_integrity, HumanKey}` (germline fence);
* `sentinel_councils` (Integrity Auditor / Adversary / Blackrod, diagnostic only);
* `core_business_contracts` + `core_facade` (Observed -> Composition path, prospective findings capped at `BoundaryChecked`);
* empty crate skeleton at `engine/core_api/` to be filled with an Axum router, a `/solve` handler, an `IntakeFilter`, an `OutboundEnvelope`, and a feature gate `core_api_flagship` defaulting OFF.

`sentinel_ai/web/` (the Next.js MVP) is in $C^0$ as a black box; the API may NOT edit it in this packet.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Permitted shape-preserving rewrites of the HTTP edge that do not change any inner library contract:

* adding the Axum router skeleton, a `POST /solve` handler, a `GET /healthz`, and request/response DTOs whose serialization deterministically maps to / from the existing `PromptPacket` and `terminalize_row` shapes;
* composing existing `FamilyDriver`/`SgSession::solve_with`, `core_epk`, and `core_llm_gateway::CandidateSource` calls without modifying their signatures;
* introducing the `core_api_flagship` Cargo feature gate so the binary compiles default-OFF and the live site is untouched until a separate cutover packet;
* adding `cargo test -j 1 -p core_api --features core_api_flagship` tests and a canary `grep` test that fails the build if the handler ever calls `core_certifiers::certify_checked_packet` directly from HTTP (the certifier stays human/germline-gated);
* internal refactoring of router state, handler module layout, and DTO field naming as long as the public surface (route paths, JSON keys, terminal-row JSONL schema) is preserved.

This is the gauge lambda for the flagship; no inner-library drift, no new authority path.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):**

1. **No Rust HTTP surface exists.** `engine/core_api/` is empty; there is no Axum service, no `/solve` route, no JSON DTO that round-trips a `PromptPacket`. Every prompt path the operator currently exposes to the public flows through `sentinel_ai/web/` (TypeScript).
2. **The TS MVP does not honor the ODP firewall.** `sentinel_ai/web/` stores raw `inputText` (spec §10 invariant 8 violation: "no raw text, hashed shapes only") and emits prose that reads as authority ("verified", "certified") without ever passing through `terminalize_row` or `certify_checked_packet`. Markdown / TS prose minting authority is a firewall breach (CLAUDE.md, spec §10 invariant 3).
3. **No replayable terminal-row emission from HTTP.** There is no append-only JSONL lane ledger fed by a prompt request; the immune loop (spec §6) has no carrier to trace from the HTTP edge.
4. **No post-LLM Symbol-Game / EPK seam.** Even when `core_llm_gateway` is invoked, there is no Rust path that runs `SgSession::solve_with` -> `core_epk` Δ_E -> `terminalize_row` end-to-end from an HTTP request.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two HTTP request/response traces are identified iff their canonicalized cochain shape under
$\sigma : (\text{PromptPacket}, \text{terminal row}) \to \text{blake3 digest}$
agrees. Concretely: traces that differ only by request id, wall-clock timestamp, transport-level retry, HTTP framing, JSON key ordering, or `Observer`-local field naming, but that share the same `PromptShape`, `ResidualFamilyId`, `CandidateRequest` shape, `SgOutcome` variant, EPK Δ_E value, and final `Decision` variant, are gauge-equivalent. ZeroRel is exactly the kernel of $\sigma$ at the HTTP edge.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** $C^1 / \mathrm{im}(d_0)$ is the irreducible class:

> **A typed `POST /solve` endpoint that (a) packetizes the prompt into a `PromptPacket` via `core_prompt_packets`, (b) routes the packet through the Symbol Game lambda `SgSession::solve_with` over an `core_llm_gateway::CandidateSource` (Gauge Breaker, performer-only), (c) measures obstruction via `core_epk` (Δ_E, $\Phi_1$ from `VerifiedExactPhi1`, $\Gamma_2$ from `ExactGamma2Result`), (d) emits a terminal row through `core_sweep_kernel::terminalize_row`, and (e) returns ONLY that terminalized residual + obstruction packet to the caller — never an authority claim, never the certifier bridge, never raw prompt text in shared storage.**

The shape-only ingredients (Q^1 residue): an Axum router, the `/solve` handler, the request/response DTOs, the canary grep, the `FixtureSource`-backed integration test, and the `core_api_flagship` feature gate. The TypeScript MVP is NOT part of $Q^1$; its retirement is a successor packet.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Cross-boundary coherence between the HTTP edge and the inner libraries:

* the JSON DTO round-trips to / from `core_prompt_packets::PromptPacket` such that two identical request bodies produce byte-identical `PromptPacket`s (privacy invariant: only hashed shapes leave the process);
* the `Decision` emitted by `terminalize_row` agrees with the `SgOutcome` variant returned to the caller (single-valued mapping `SgOutcome -> Decision`);
* the feature gate `core_api_flagship` is OFF in `default` so the workspace `cargo build -j 1` matches the pre-packet build byte-for-byte (no accidental binary surface);
* a canary test (`tests/firewall_canary.rs`) fails to compile or fails at test time if any path in `core_api` calls `core_certifiers::certify_checked_packet` (forbidden) or writes raw prompt text outside the JSONL hashed-shape lane.

$d_1$ is the requirement that the HTTP edge forms a globally consistent cocycle with the shared diagnostic core and with the firewall.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass) — per defect (A1):**

| Defect | $\Gamma_2$ | Witness |
|---|---|---|
| `D_packetize` | 0 (target) | JSON DTO -> `PromptPacket` byte-identical round-trip across two identical request bodies (Raw prompt text may exist ephemerally inside request handling and candidate generation. It must not be persisted, ledgered, or emitted. Shared storage receives only packet hashes/shapes). |
| `D_route` | 0 (target) | three pinned `FixtureSource` golden tests: handler invocation's `SgOutcome -> Decision` mapping agrees with `terminalize_row`'s emitted `Decision` (single-valued mapping pinned). |
| `D_terminal` | 0 (target) | replayed `FixtureSource` runs' JSONL lane output matches the pinned golden under the same input shape; append-only invariant held. |
| `D_canary` | 0 (target) | canary-grep hits inside `engine/core_api/` matching `certify_checked_packet` = 0, matching raw-prompt-text persistence = 0 (the two `tests/firewall_canary.rs` / `tests/no_raw_text_canary.rs` canaries). |
| `D_byteshape` | 0 (target) | downstream consumers whose public-API contract breaks under the feature-gated build = 0; the default build has no new public HTTP surface and only the expected allowlisted Cargo metadata changes. |

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass) — per defect (A1):** **target/pinned by-construction** on the offline `FixtureSource` lane (the `core_functional::phi1::VerifiedExactPhi1` measurement lane is NOT yet wired — it is the deferred `phi1-fixture-builder-lane` of S13; this packet pins $\Phi_1 = 0$ by construction via the typed FLSC `before.phi1 > 0 && after.phi1 == 0` certificate and the `epk.authority_effect() == None` reading, NOT by computing $\Phi_1$ on the lane's actual carrier). The live-traffic component is also explicitly deferred per S13.

| Defect | $\Phi_1$ | Witness |
|---|---|---|
| `D_packetize` | 0 (target, FixtureSource lane) | DTO -> `PromptPacket` factors through the canonical shape signature $\sigma$ (S5 ZeroRel kernel); raw prompt text may exist ephemerally inside request handling and candidate generation, but must not be persisted, ledgered, or emitted (shared storage receives only hashes/shapes). |
| `D_route` | 0 (target, FixtureSource lane) | `SgSession::solve_with` over `FixtureSource` runs end-to-end from an HTTP request; `core_epk` Δ_E is measured; no in-lane request bypasses the handler. |
| `D_terminal` | 0 (target, FixtureSource lane) | every in-lane request emits a `TerminalRecord` via `terminalize_row` and appends one JSONL row; no request reaches the caller without a terminal-row carrier. |
| `D_canary` | 0 (target, FixtureSource lane) | no in-lane code path calls `core_certifiers::certify_checked_packet` from HTTP; canary-grep tests pin this to zero. |
| `D_byteshape` | 0 (target, FixtureSource lane) | `sentinel_ai/web/` byte-equivalence held under recursive blake3 fixture; the default build has no new public HTTP surface and only the expected allowlisted Cargo metadata changes. |

The live-traffic $\Phi_1$ component — every public prompt request that today flows through `sentinel_ai/web/` without a `PromptPacket` — is explicitly deferred to successor packet `core_api_cutover_packet.md` (see S13).

10. Classify System State
-------------------------

**Classification — per defect (A1):**

| Defect | Class |
|---|---|
| `D_packetize` | ClosedSurvivor + structural extension ($\Meta$): the DTO -> `PromptPacket` boundary is a new structural edge, licensed by non-destruction (preserves `core_prompt_packets` public surface). |
| `D_route` | ClosedSurvivor + structural extension ($\Meta$): composing the existing `SgSession::solve_with` and `core_epk` calls under a new HTTP edge; inner library contracts unchanged. |
| `D_terminal` | ClosedSurvivor + structural extension ($\Meta$): a new HTTP-driven invocation site for `terminalize_row`; the kernel's authority-mint precondition (`author_model != gate_model`) intentionally fails on the FixtureSource lane, sealing the carrier as a non-minting terminal. |
| `D_canary` | ExactRepair: the firewall canary (no `certify_checked_packet` reference, no raw-prompt-text persistence) is closable by a gauge move ($E$: add the empty crate skeleton + the two canary tests). No lift required. |
| `D_byteshape` | ExactRepair: the byte-shape invariant is closable by the `core_api_flagship` feature gate (default OFF) plus the S8 recursive blake3 fixture over `sentinel_ai/web/` and the `target/release/.fingerprint/*.json` artifact set. No lift required. |

Every defect is closed under the shared diagnostic core (every ingredient — `PromptPacket`, `FamilyDriver`, `SgSession::solve_with`, `core_epk`, `core_llm_gateway`, `terminalize_row` — already exists at $C^0$ or is the subject of a sibling packet such as `core_residual_families_packet.md` / the `core_prompt_packets` backbone child spec). For the three ClosedSurvivor defects, the repair is a structural extension at the HTTP edge: a new app crate composing existing libraries, gated behind `core_api_flagship`, with a preservation witness that the TS MVP and live sentinel.com remain byte-for-byte unchanged. Those three defects jointly license one $\Meta$ (the API surface itself is a Meta) under the non-destruction discipline.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift / Structural Extension):** Mint a single
`core_discrete_deformation_algebra::FaceLambda` value representing the HTTP edge extension. The lambda is pinned as:

* **shape:** a `FaceLambda<F>` (the real generic public struct with public fields `{face: F, capacity: i64}`) parameterized on a face id type `F = &'static str` keyed at `"core_api::solve"`, with the inner composition `intake -> SgSession::solve_with -> core_epk Δ_E -> terminalize_row` realized as a fixed lambda word of length 4. The lambda value is constructed via `FaceLambda::new("core_api::solve", 4)` and asserted on in S9's AT;
* **NonDestructiveExtensionCertificate (NDEC):** the real public-fielded struct `NonDestructiveExtensionCertificate { preserves_old_vertices: bool, preserves_old_edges: bool, records_tradeoff: bool }`, constructed via `NonDestructiveExtensionCertificate::new(true, true, true).require_non_destructive()?` and asserted (`assert!(cert.preserves_old_vertices && cert.preserves_old_edges && cert.records_tradeoff)`). The certificate's three booleans witness (i) preservation of every pre-existing public surface of `core_homology`, `core_functional`, `pfp`, `core_epk`, `core_llm_gateway`, `core_sweep_kernel`, `core_certifiers`, `core_corrigibility`, `sentinel_councils`, `core_business_contracts`, `core_facade`, and `sentinel_ai/web/` (the full §2 $C^0$ list); (ii) the default build has no new public HTTP surface and only the expected allowlisted Cargo metadata changes; (iii) zero references to `certify_checked_packet` and zero raw-prompt-text persistence sites in `engine/core_api/` (the canary witnesses);
* **FiniteLambdaStepCertificate (FLSC):** the real public-fielded struct `FiniteLambdaStepCertificate { before: FiniteDiagnostic, after: FiniteDiagnostic, extension: NonDestructiveExtensionCertificate }`, constructed via `FiniteLambdaStepCertificate::new(before, after, ndec).require_valid()?`. The `before` diagnostic carries the pre-handler `{phi1, gamma2}` as a **pinned by-construction** obstruction trigger (phi1 > 0 prior to handler composition — NOT a measured value off the lane's carrier; the measuring `VerifiedExactPhi1` lane is the deferred `phi1-fixture-builder-lane` of S13); `after` carries `{phi1: 0, gamma2: 0}` post-handler — `require_valid()` enforces both legs (obstruction-before, resolved-after) plus the non-destruction extension at construction time. The lambda word length 4 (`packetize`, `solve_with`, `epk_delta`, `terminalize_row`) is bound on the `FaceLambda::capacity` field;
* **terminalizer route:** the $\Meta$ is sealed at `terminalize_row` only; `certify_checked_packet` is NOT invoked by this lambda. The returned `TerminalRecord.decision` on the FixtureSource lane is `Decision::NotGated` because the handler ships a row with an EMPTY `gated_verdict`, which the kernel routes to `Decision::NotGated` at its early fail-closed branch (`terminalize.rs` step 2, `if gated.is_empty()`) BEFORE the survivor/`Certified` arm is reached. The empty `gated_verdict` is the seal. The handler passes DISTINCT author/gate models (distinct so a survivor row would not trip `AuthorBlindGateViolation`); model distinctness is NOT the seal and would NOT block certification of a survivor row — only the absence of a survivor `gated_verdict` does. The adversarial seal test `tests/terminalize_row_seal.rs` pins both directions. The crate's authority effect is `core_types::authority::AuthorityEffect::None` (spec §10 invariant 3); the EPK seam returns `AuthorityEffect::None` by contract (`EpkResidualLedger::authority_effect()`). Minting authority for any artifact this lambda produces remains a separate, human/germline-gated step outside the API.
* **Authority and Terminalization Invariant:**
  * `terminalized` = the packet row reached a declared terminal status (e.g. `Decision::NotGated` / `Refusal`).
  * `certified` = only if a named certifier/seal path (`core_certifiers::certify_checked_packet`) proves the declared certificate.
  * `authority` = never inferred from packet structure alone (this lambda remains strictly diagnostic with `AuthorityEffect::None`).

Lift triggered by **closed-survivor structural extension** and licensed by the umbrella spec's flagship-face policy (spec §4(d), §11 build order step 6). The lambda's word is fixed; any future addition of a step is a successor $\Meta$ with its own NDEC + FLSC.

**Oracles required (A3):** none. The HTTP edge does not import a representation theorem from outside the declared finite 2-window; every step of the $\Meta$ word (`packetize`, `solve_with`, `epk_delta`, `terminalize_row`) is realized by an existing live Rust type/function in $C^0$. No sub-claim's terminal becomes `OracleNeeded`. The Lean `CoreApi` $d_1$ mirror is now implemented at `engine/lean4/core_api/src/flagship/mapping.lean`; it is a finite agreement proof, not an oracle import and not an authority surface.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus) — alphabet (A5):** the DDA letters used below are drawn exclusively from the canonical registry {`E`, `R`, `C`, `I`, `Meta`/`Lambda`, `D`, `M`, `T`}. No new letters are invented. The discrete deformation sequence is:

1. gauge repair ($E$) — add the empty `engine/core_api/` crate skeleton with `Cargo.toml` declaring the `core_api_flagship` feature OFF in `default`;
2. quotient projection ($R$) — realize `PromptPacket -> ShapeSignature` at the HTTP edge by composing the `core_prompt_packets` backbone (sibling spec) with the Axum DTO layer; raw text is dropped at this boundary;
3. lift application ($\Meta$) — apply the `FaceLambda` defined in section 11 to compose `SgSession::solve_with` over an `core_llm_gateway::CandidateSource` (default `FixtureSource` in tests; `LlmCandidateSource` opt-in) and run `core_epk` Δ_E;
4. descent ($D$) — emit the terminal row via `core_sweep_kernel::terminalize_row` (the single minting site), serialize the `Decision` + obstruction packet to the JSON response, append the JSONL lane row;
5. cross-boundary closure ($I$) — run the three `FixtureSource` golden tests + two canary tests (`tests/firewall_canary.rs`, `tests/no_raw_text_canary.rs`) and confirm $\Gamma_2 = 0$ and the `cargo build -j 1` artifact set under `default` is unchanged.

Imported representation theorems are NOT logged here as DDA operations (A3); per S11 there are none required.

Wiring binding: the app lives at `engine/core_api/` (EPK business-contracts stack member), depends on `core_facade`, `core_business_contracts`, `core_homology`, `core_functional`, `pfp`, `core_epk`, `core_llm_gateway`, `core_sweep_kernel`, and `core_corrigibility`. The crate mints no authority; the firewall (CLAUDE.md, spec §10 invariants 3 / 4 / 8) is honored: only `terminalize_row` and `certify_checked_packet` mint, and this packet routes through the former only and not the latter.

Lean obligation (implemented): `engine/lean4/core_api/src/flagship/mapping.lean` mirrors the five live Rust arms exactly: `Certified -> NotGated`, `Repaired -> NotGated`, `Refused -> RefusedHostAuthority`, `OracleNeeded -> Obligation`, and `IntentMismatch -> NotGated`. `lake build CoreApi` plus `core_api`'s `sg_outcome_to_decision_covers_all_five_arms` test are the cross-rail seal. The proof is evidence-only and mints no authority.

13. Terminal Status
-------------------

**Terminal — per defect (A1) with Current / Target / Seal Condition (A4):**

| Defect | Current | Target | Seal Condition |
|---|---|---|---|
| `D_packetize` | OpenResidual (no `POST /solve` exists; raw text crosses the TS edge) | ClosedSurvivor (FixtureSource lane: DTO -> `PromptPacket` is byte-identical and raw-prompt-text-free) | `core_sweep_kernel::terminalize_row` returning `Decision::NotGated` with `host_terminal_status: "Refusal"` on each of the three pinned `FixtureSource` golden rows (`lane_001.jsonl`), and `cargo test -j 1 -p core_api --features core_api_flagship tests/dto_promptpacket_roundtrip.rs` green. |
| `D_route` | OpenResidual (no Rust path runs `PromptPacket -> SgSession::solve_with -> core_epk` from HTTP) | ClosedSurvivor (FixtureSource lane: full route composes end-to-end) | `core_sweep_kernel::terminalize_row` returning `Decision::NotGated` on the same three pinned rows, with the route covered by `cargo test -j 1 -p core_api --features core_api_flagship tests/solve_route_fixture.rs` green; `SgOutcome -> Decision` single-valued mapping pinned by the Rust five-arm test and `lake build CoreApi` against the Lean mirror. |
| `D_terminal` | OpenResidual (no `terminalize_row` emission from HTTP; no JSONL lane row appended) | ClosedSurvivor (every in-lane request emits exactly one terminal row and one JSONL append) | `core_sweep_kernel::terminalize_row` returning `Decision::NotGated` with the JSONL append covered by `cargo test -j 1 -p core_api --features core_api_flagship tests/jsonl_lane_golden.rs` (golden compare to `tests/golden/lane_001.jsonl`) green. |
| `D_canary` | OpenResidual (no canary forbids `certify_checked_packet` from HTTP; no canary forbids raw-prompt-text persistence) | ExactRepair (firewall canaries are green and the only mint paths in the crate are the kernel and certifier surfaces) | `cargo test -j 1 -p core_api --features core_api_flagship tests/firewall_canary.rs tests/no_raw_text_canary.rs` green (zero `certify_checked_packet` references in `engine/core_api/`; zero raw-prompt-text persistence sites). The firewall remains: only `core_sweep_kernel::terminalize_row` and `core_certifiers::certify_checked_packet` (7 IsAuth guards) can mint; this packet routes through neither for authority — the kernel call is sealed as `Decision::NotGated`/`Refusal` by construction. |
| `D_byteshape` | OpenResidual (workspace `default` byte-shape unpinned; `sentinel_ai/web/` not pinned to byte equivalence) | ExactRepair (workspace artifact set under `default` produces no new public HTTP surface and only the expected allowlisted Cargo metadata changes; `sentinel_ai/web/` is byte-for-byte untouched) | `cargo test -j 1 -p core_api --features core_api_flagship tests/byteshape_fixture.rs` green: S8 recursive blake3 digest fixture over `sentinel_ai/web/` matches the pre-sprint baseline, and the default build has no new public HTTP surface and only the expected allowlisted Cargo metadata changes. |

The packet's overall posture is a diagnostic terminalization at the HTTP edge with $\Phi_1 = 0$ on the offline FixtureSource lane. Authority is NOT minted by this packet, by the markdown, or by the crate; the only authority bridge in the platform remains `core_certifiers::certify_checked_packet`, and the flagship API does not reach it. Markdown does not mint authority — only the two named seal paths above do.

**Explicit residual deferrals (per repair-pass rule 3):**

* `defer: live-cutover-traffic-phi1` — the live-traffic $\Phi_1$ component (every public prompt request that today flows through `sentinel_ai/web/` without a `PromptPacket`) is explicitly deferred to a successor packet `core_api_cutover_packet.md`; this packet drives $\Phi_1$ to zero only on the offline `FixtureSource` lane (per §9).
* `defer: immune-loop-jsonl-ingestion` — the JSONL lane ingestion into the immune loop (spec §6) is deferred to a sibling packet `core_immune_loop_intake_packet.md`.
* `repair: lean-d1-mechanization` — discharged by the Rust-mirrored Lean module at `engine/lean4/core_api/src/flagship/mapping.lean`; this repair remains evidence-only and does not activate or promote the API.
* `defer: live-LlmCandidateSource` — opting `POST /solve` into `LlmCandidateSource` (Gauge Breaker, real LLM) traffic is a per-story successor decision in a successor packet; this packet uses `FixtureSource` only.
* `defer: per-crate-cargo-public-api-diff` — the per-crate `cargo public-api --diff-git-checkouts` lane over the 11 §2 $C^0$ crates is deferred to `core_api_cutover_packet.md`; this packet covers NDEC's preservation witness via the workspace artifact fingerprint (S8) + recursive `sentinel_ai/web/` byte-equivalence (S8) instead, which is sufficient for the flagship-face-policy preservation witness named in §11.
* `defer: phi1-fixture-builder-lane` — the `Phi1Functional::verify_exact_certificate` fixture-builder lane reaching into `core_functional::phi1::testing` is deferred to the cutover packet; this packet covers $\Phi_1$ via S5's `epk.authority_effect() == AuthorityEffect::None` + S9's typed FLSC `before.phi1 > 0 && after.phi1 == 0` instead.
* `defer: per-fixture-lane-goldens` — per-fixture lane goldens for `lane_002.jsonl` + `lane_003.jsonl` are deferred to the cutover packet; this packet keeps `lane_001.jsonl` plus the typed Meta certificate triple (S9), which is the GTOC-3 license-witness leg.
* `defer: fs-write-byte-buffer-interception` — runtime interception of `fs::write` / `tokio::fs::write` byte buffers (carrier (iv) of the raw-text-drop boundary measurement) is deferred to a future hardening packet; this packet covers the boundary statically via S6's source-grep over `fs::write` patterns and dynamically via S10's three other carriers (`OutboundEnvelope` JSON, JSONL row, `serde_yaml::Value` rows to `terminalize_row`).

The packet's terminal is "diagnostic terminalization at the HTTP edge, $\Phi_1 = 0$ on the offline FixtureSource lane, with all live-traffic / cutover / Lean / LlmCandidateSource / cargo-public-api / phi1-fixture-builder / lane-goldens / fs-write-interception components explicitly deferred above". No silent residual remains.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, the fixture-source solve handler delegates exact evaluation to `core_prompt_packets::gtoc_adapter::evaluate_prompt_packets`; no API-owned live adapter or admitted live/shadow carrier exists. The offline route and focused fixture test are present, while live traffic, immune-loop ingestion, measured live Phi1, rollback, and Lean mapping remain owned by `S16-002`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The current packet hash and source manifest are recorded in the S16-001 census; file presence is not a live-cutover claim.

15. S16-002 bounded live/shadow disposition
-------------------------------------------

At observer `231fa78fb66544cad861c8aa34826d3ff9214420`, packet `375f983b876bb4fb23f90e326203aa3a3ae51294c1fee1ecdb7b327ca0f93b60` admits a default-off live composition under Cargo feature `core_api_live`. `core_llm_gateway::CandidateSource` is `Send + Sync`; `FixtureSource` uses an atomic cursor, and the provider-backed source compiles only when the explicit live feature is selected. Startup remains `disabled`, and the state machine rejects a direct `disabled -> enabled` transition.

The live and shadow lanes call `core_prompt_packets::gtoc_adapter::evaluate_prompt_packets` over one request packet plus every nonempty candidate packet. Raw request text, raw candidate text, provider response bodies, and the Symbol Game trace are dropped before durable retention. The append-only JSONL cutover ledger stores route transitions, packet ids, source metadata, exact Phi1/Gamma2/status, workflow and oracle projections, the shared `GtocTerminal`, `AuthorityEffect::None`, and a BLAKE3 record chain. Startup performs one full replay; steady-state operations validate only newly appended bytes under the standard-library file lock. Independent runtime instances refresh the shared route before admitting a request, transitions refresh and append atomically, truncation is rejected, and blank lines do not consume logical sequence numbers. Replay rejects incomplete tails, sequence/hash drift, and even a hash-consistent non-`None` authority effect.

| Defect | S16-002 disposition | Executable seal |
|---|---|---|
| `D_live_carrier` | `ExactRepair` on the bounded fixture/hostile-source carrier | disabled returns legacy; shadow compares and returns legacy; enabled returns live; rollback appends the prior mode without deleting rows |
| `D_exact` | `ExactRepair` on request-plus-candidate packet manifests | shared exact evaluator emits carrier-derived Phi1/Gamma2/status; candidate output cannot set those fields |
| `D_terminal` | `ExactRepair` for exact, mismatch, refusal, lift, and source-outage controls | shared terminal routes are `ExactRepair`, `OpenObstruction`, `Refused`, `LiftLicenseNeeded`, and `InfrastructureFailure` |
| `D_canary` | `ExactRepair` for the bounded Rust authority/privacy surface | raw canaries are absent; source canary finds no certifier bridge; hash-consistent authority forgery is rejected |
| `D_lean` | `OpenObstruction` at the S16-002 observer | no Lean mapping file existed and no Lean process ran at that observer |

**Current reconciliation (2026-07-22).** D_lean is now ExactRepair at the evidence layer: the Rust-mirrored Lean file builds, proves routing is single-valued, and pins all five arms to the live Rust mapping. This does not alter the historical S16-002 receipt, call a provider, activate production traffic, record human promotion, or create an authority constructor.

The first four bounded defects plus the conserved Lean and real-provider activation residual aggregate to `StabilizedSurvivor`. The earlier live-cutover, local immune-ledger, carrier-derived exact replay, and opt-in `LlmCandidateSource` deferrals are implemented as construction surfaces, but no real provider was called and no unrestricted traffic equivalence is claimed. Per-crate public-API diff, runtime byte-buffer interception, the named Lean theorem/axiom audit, real-provider shadow observation, production activation, and human promotion remain explicit S16-005 obligations. `AuthorityEffect` remains `None` throughout.
