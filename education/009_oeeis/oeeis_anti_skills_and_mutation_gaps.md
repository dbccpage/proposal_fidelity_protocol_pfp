---
documentation_contract: symbol-game-documentation/v1
title: "OEEIS Anti-Skills, Mutation Gaps & Adversarial Invariant Register"
kind: reference
audience:
  - engineers
  - coding-agents
  - researchers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - omega_engine_education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_epistemic_immune_system_eis/oeeis_anti_skills_and_mutation_gaps.md
source_revision: 44aff3782
prerequisites: []
verification: py -3.12 -m pytest omega_engine_education/the_symbol_game/tests/test_documentation_route_canonical.py
aliases: []
related:
  - oeeis_notes.md
  - ../2_symbol_game_packets/packet_verifier_contracts.md
last_verified: 2026-09-30
---

# OEEIS Anti-Skills, Mutation Gaps & Adversarial Invariant Register

**AuthorityEffect:** None. Defect patterns, mutation requirements, and epistemic firewall invariants.

---

## 1. Five Mandatory Mutation Test Gaps

These five mutation patterns represent critical testing gaps identified across test harnesses T01–T51 that must be actively checked and killed:

| Gap ID | Defect Target | Vulnerability Description | Required Mutation Coverage |
| :--- | :--- | :--- | :--- |
| **GAP-MUT-01** | Two-Sided Branch Rewriting | If peak reduction only evaluates the left branch, mutating right branch steps fails silently. | Mandate independent left-branch ($M_L$), right-branch ($M_R$), and branch-swap ($M_S$) mutations. |
| **GAP-MUT-02** | Float32 Underflow Boundary | Testing underflow below $-103.97$ nats misses subnormal float behavior between $-100.0$ and $-103.0$. | Require explicit interval boundary checks across $[-100.0, -103.0]$ to verify subnormal float behavior. |
| **GAP-MUT-03** | Directional Control Ranges | Testing only `U+202E` (Right-to-Left Override) leaves Trojan Source isolate controls unmutated. | Test all isolate control ranges (`U+2066..U+2069`) and embedding overrides (`U+202A..U+202E`). |
| **GAP-MUT-04** | Graph Adjacency Serialization | Edge serialization relies on sorted vertex keys; mutating the comparator must invalidate serialization. | Verify that reversing or permuting edge sort keys alters the canonical SHA-256 digest. |
| **GAP-MUT-05** | Kleene $\bot$ Short-Circuiting | In 3-valued Kleene logic, $\bot \wedge \text{False} = \text{False}$, but $\bot \wedge \text{True} = \bot$. | Verify that mutation of expression evaluation order cannot short-circuit or misreport $\bot$. |

---

## 2. Annotated Trace Anti-Divergence Rules

Mined from runtime divergences between script execution logs and append-only packet ledgers:

### `ANTI-SCRIPT-LEDGER-DIVERGENCE`
- **Rule:** A terminal outcome (e.g. `EXACT_REPAIR`) absent from the canonical append-only packet ledger cannot be promoted from console output or script text.
- **Invariant:** The ledger is the sole authority for completed rounds; console printouts are untrusted proposal logs.

### `ANTI-FLOAT-AS-EXACT`
- **Rule:** Printed decimal (e.g. `0.000`) or hex-float diagnostics (e.g. `0x1.0p-1`) are not exact rational certificates.
- **Invariant:** Exact certificates must cross wire boundaries as reduced rational fraction pairs $(p, q) \in \mathbb{Z} \times \mathbb{N}^+$.

### `ANTI-ID-CONFLATION`
- **Rule:** `run_id`, `task_id`, and `packet_id` represent distinct structural bindings and must not be used interchangeably.
- **Invariant:** A `run_id` binds an execution session; a `task_id` binds a discrete computational step; a `packet_id` binds the content hash of the payload.

---

## 3. Top-Level Adversarial Anti-Skills

Mined from comprehensive top-level adversarial reviews (`adv_00_top`, `adv_llm`):

### `ANTI-UNIDENTIFYING-KEY`
- **Rule:** A key that does not uniquely determine the object it keys is not a key.
- **Application:** Applies to rewrite rules (must include redex position), parallel graph edges (must identify distinct multi-edges), candidate IDs, and carrier bindings.

### `ANTI-UNFENCED-GROUND`
- **Rule:** Re-computation of derivation steps against producer-supplied carriers or axioms does not constitute independent verification.
- **Receipt Metadata Contract:** Every verification receipt must record explicit four-party authorship:
  ```yaml
  authorship:
    problem: operator      # Who posed the problem
    carrier: host          # Who supplied the carrier alphabet and graph
    candidate: producer    # Who generated the proposal
    verifier: host         # Who verified the derivation
  ```

### `ANTI-SINGLE-VERIFIER-COLLUSION`
- **Rule:** A single host verifier can harbor implementation bugs or silent regressions.
- **Invariant:** High-value claims must support `DifferentialVerifierProfile` deploying independent N-version verifier implementations over shared problem digests with normalized result comparators.

### `ANTI-ALPHABET-SEAM-CONFUSION`
- **Rule:** The three distinct alphabets in language model interaction must remain strictly separated:
  1. **Character Carrier Alphabet:** Validated UTF-8 codepoints under strict NFC normalization.
  2. **Tokenizer Vocabulary:** Model token IDs and byte mappings $V_{\text{tok}}$.
  3. **Host Action Alphabet:** Verified constructors, AST nodes, and transition laws.

### `ANTI-DENOTATION-CONFLATION`
- **Rule:** Syntactic or certified manipulation within a formal calculus does not establish external denotational truth.
- **Invariant:** Packets are interface envelopes and proof certificates within declared models, not global metaphysical claims.

### `ANTI-NFKC-CONFUSABLE-TRAP`
- **Rule:** NFKC normalization fails against characters with empty decomposition strings (such as `U+237A` APL functional symbol alpha) and silently folds distinct mathematical variables (such as `U+1D6C2` $\to$ `U+03B1`).
- **Invariant:** Carrier verification requires dual test fixtures: exact NFC equivalence and an explicit static confusable map (`MANUAL_CONFUSABLES`).

### `ANTI-ONE-STEP-INFERENCE-LIFT`
- **Rule:** Masking a single token transition during decoding cannot be claimed as conditioning the full-sequence distribution on eventual acceptance.
- **Invariant:** Local renormalization $Q_{\text{GCD}}(\tau \mid h)$ must be distinguished from recursive Expected Future Grammaticality (EFG) $Q_{P,G}(\tau \mid h)$.

### `ANTI-PREFIX-COMPLETION-CONFLATION`
- **Rule:** Prefix legality $\operatorname{Pref}(L)$ is not completed-language membership $L$.
- **Invariant:** If decoding halts by token budget exhaustion or timeout, prefix legality does not imply that the emitted string is a valid grammatical sentence in $L(G)$.

### `ANTI-PRODUCER-RE-DERIVATION`
- **Rule:** Producer-asserted tags such as `host_rederived: true` or `PROVED-PROSE` are untrusted proposal content.
- **Invariant:** All verifier status fields are minted exclusively by the host verification runtime under the Deletion Test.

---

## 4. Provenance, Verification Pipeline & Transaction Anti-Skills

Mined from PR integration reviews, historical work orders, and source reading maps:

### `ANTI-PROVENANCE-CONFUSION-MSS-GENESIS`
- **Rule:** MSS-N denotes pinned row $N$ of `stages.tsv`; Genesis comparisons are external and do not establish derivation toward an MSS target.
- **Invariant:** Pinned stage identity is defined by the SHA-256 digest of row bytes. Cross-system comparisons must not be conflated with formal derivation ascent.

### `SNAPSHOT-INVALIDATION-ON-SOURCE-CHANGE`
- **Rule:** Any modification to underlying source files invalidates bound snapshot manifests and requires fresh review.
- **Invariant:** Artifact counts or notebook tallies alone cannot refresh verification; receipts bind exact byte digests.

### `UNSUPPORTED-STAGE-MUST-REFUSE`
- **Rule:** A lift checker or domain verifier must immediately refuse unsupported higher stages with an explicit fail-closed typed refusal.
- **Invariant:** Never bypass substantive checks or fall through into a weak/default verifier when encountering an unmechanized stage.

### `VALIDATE-BEFORE-MUTATE`
- **Rule:** Transactions, state machines, and batch operations must execute complete validation prior to applying any state mutation ($\text{validate} \to \text{commit}$).
- **Invariant:** Never mutate state while validation is in progress; a malformed element midway through a batch must leave system state unmodified.

### `MISSING-LOAD-BEARING-PREMISE`
- **Rule:** Formal theorem statements must explicitly declare all premises required for semantic validity.
- **Invariant:** Admitted proofs (`sorry` in Lean) or missing trace-validity premises must not be promoted to verified mathematical theorems.

### `MISSING-REPLAY-DATA-MUST-FAIL`
- **Rule:** If input data required for verification replay is absent, the verifier must immediately emit a typed refusal.
- **Invariant:** Never silently substitute mock data, synthetic constants, or fallback defaults for missing replay inputs.

### `PILOT-NOT-CAUSAL-EXPERIMENT`
- **Rule:** Historical pilot runs or small-scale tests cannot be interpreted as controlled or causal detector effects.
- **Invariant:** Claims of causal efficacy require randomized controlled trials with declared error budgets and registered protocols.

### `PRESERVE-TRANSIENT-FAILURE-RECORDS`
- **Rule:** Never erase or overwrite a transient failed execution record because a subsequent rerun succeeded.
- **Invariant:** Both the failure record and the clean rerun must be preserved in custody logs to maintain audit fidelity.

### `ANTI-SKILL-NOT-ANTIMORPHISM`
- **Rule:** A detector that recognizes a failure pattern (anti-skill) is not an inverse or reversal morphism.
- **Invariant:** Detection and diagnosis $(\Phi_1)$ are distinct from reversible state deformations or homotopy inverses $(\Gamma_2, \Xi)$.

### `RETIRED-PATHS-MUST-BE-TYPED-AS-RETIRED`
- **Rule:** Deprecated adapters, retired shims, or obsolete runtime engines must emit explicit typed retirement refusals (`RETIRED_PATH_REFUSAL`).
- **Invariant:** Outdated components must not be presented as active or capable execution environments.

### `SORTED-KEY-JSON-NOT-RFC-8785`
- **Rule:** Naive sorted-key JSON serialization is not a complete implementation of RFC 8785 (Canonical JSON).
- **Invariant:** Lightweight serializers must be explicitly typed as restricted profiles and not advertised as general RFC 8785 canonicalizers.

### `SAME-CONTEXT-REPAIR-TARGET-INVARIANCE`
- **Rule:** Same-context repair modifies the candidate proposal or its internal representation, never the frozen problem statement.
- **Invariant:** Replacing target constraints with values a model prefers solves a different problem; the goal specification remains immutable during repair.

### `FINITE-FIXTURE-NOT-GENERAL-THEORY`
- **Rule:** A successful finite computation does not establish general ascent, steering beyond the declared fixture, or a physical theory.
- **Invariant:** Claims must be strictly bounded to the declared finite carrier and exact predicate checked.

### `PLANNED-NOT-EXECUTED`
- **Rule:** Architectural roadmaps, campaign visions, and planned multi-agent trials are planning artifacts, not executed evidence.
- **Invariant:** Design plans must never be cited as demonstrations of working software.

### `NO-PROVIDER-CALLS-MEANS-NO-LIVE-MODEL-RESULT`
- **Rule:** Executing harnesses against local mock fixtures or deterministic synthetic stubs produces zero evidence about live large language model behavior.
- **Invariant:** Claims regarding model sensitivity or prompt efficacy require live, credential-authenticated provider execution records.

---

## 5. Status at 201dc8d (2026-10-15): four unconnected anti-op registries

Re-checked on `origin/main` at `201dc8d`. Four registries hold anti-skills or anti-ops. None is
connected to another, and none except the last is read by the OEWAS op resolver.

| Registry | Location | Content at `201dc8d` |
| :--- | :--- | :--- |
| `ACTIVE_ANTI_SKILLS` | `omega_engine_operads/domain/anti_skills/research_papers.py:31` | 87 definitions |
| Antibodies | `.agents/antibodies/` | 51 top-level entries: 37 JSON and 12 YAML antibody files, plus the `definitions/` and `specs/` folders. The host mirrors hold 9 top-level entries each. |
| Admitted antiskill registry | `.agents/antiskills/admitted/registry.json` | `specs: []` (empty); a `truth_boundary_v2/` folder beside it holds 5 files |
| Op-inventory anti-ops | `omega_engine_operads/skill_operad/yaml/op_inventory.yaml` | 8 anti-ops; 3 bound to code, 3 with host detectors (all in `techne-silent-failure-hunter`) |

**How the inventory anti-ops act** (`IMPLEMENTED`). Each is a guard predicate on one input slot of
one op. The resolver's `run` evaluates it on that slot's value before the guarded op runs
(`skill_operad/resolver/resolver.py:295-300`), and a firing anti-op stops the run with its own
refusal code. In `compose` the anti-ops are only listed beside the chosen tree
(`resolver.py:224`). They never prune the search, so `compose` returns the same tree with or
without them.

**Planned direction** (`PROPOSED`, workstream I4 of
[EPIC-OE-OEWAS-012](../../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_012_woland_operad_binding_and_management_ladder_pilot_plan.md)). Fold the four registries into one anti-op
type. A candidate anti-op is admitted through OEEIS negative selection: it is screened against a
sealed clean self-panel (the thymus gate of [Level 03](levels/level_03_central_tolerance_and_thymus_gate.md)),
and one that fires on clean material is dropped. OEEIS owns admission; OEWAS owns composition and
the run-time guard. None of this is built at `201dc8d`.

## 6. Status at 201dc8d (2026-10-15): certificate fields that are literals

A same-day review of `omega_engine/crates_rs/omega_mub` (report
`/mnt/project-files/reports/omega_mub_review_2026-10-15/report.md`; draft PR #1025) found the
failure this document's anti-skills exist to catch, at scale. The exact layer is sound
(`Cyc24` arithmetic, exact PSD, the interval and basis cover engines). Many certificate verdicts
built on it are literals or hold by construction, for example:

| Field | Location | What the review found |
| :--- | :--- | :--- |
| Φ1 circulations and "13/13 classified" | `mub6_g1_variety.rs:374-390`; `bin/mub6_gap_solver.rs` | Φ1 values are literals; the classifier always assigns a class, so the count cannot fail |
| verify_all step 2.5 | `mub6_continuous_chaining.rs:1342-1349` | Passes on hard-coded `true` values; every receipt row is written `passed:true` |
| Flat-extension rank gap | `mub6_moment_ledger.rs:603-628` | Ranks hard-coded; status CERTIFIED whatever the computed flag says |
| Triad non-existence | `szollosi_triad_solver.rs:428, 481` | Tests 64 of 360 points, misses {I, F6, Gauss·F6}, receipt says `VerifiedTriadNonExistence` |
| Global gluing B2 | `mub6_global_gluing.rs:982` | A disjunction that is always true |

No anti-skill in the four registries of §5 fires on any of these, and no mutation test turns
them red. The committed `omega_mub_verify_all_receipt.json` reads 24/24 while the current code
exits 1. (`[test]`, from the omega_mub review's local run.)

**Candidate anti-op** (`PROPOSED`, not admitted): `CERTIFICATE-FIELD-NOT-COMPUTED`. It fires when
a receipt or certificate field that carries a verdict is a constant, or does not change under a
mutation of its stated input. Admission follows the §5 direction: screened against a clean
self-panel, with the receipts above as seeded positives. It belongs with the repository's
mutation-bite pattern (one mutation per verdict field). Whether those receipts are downgraded to
fixtures is decision D5 of
[EPIC-OE-OEWAS-012](../../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_012_woland_operad_binding_and_management_ladder_pilot_plan.md).
