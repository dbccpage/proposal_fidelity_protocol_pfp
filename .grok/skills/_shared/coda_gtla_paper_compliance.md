# CODA_GTLA Paper Compliance Contract (shared)

**One contract. Every producer, improver, adversary, proof reviewer, release reviewer, and authority witness runs the same CODA_GTLA process.** Roles differ only in carrier access, permissions, observer position, available operators, evidence ceiling, and terminal-authority ceiling — never in the audit itself.

This is the single source of truth for paper-review authority and claim-hygiene rules. Skills reference it; they do **not** re-host these rules inline (that is the fork this contract exists to end — `auto-symmetry-hunter` enforces `DUPLICATE_RULE`/`MISSING_PROPAGATION` against it).

> Status **Coal**: this contract is a governed `OperatorImprovementCandidate`. It does not self-activate; edits to it are doctrine (Channel 2, `_shared/meta_skill_governance.md`) and are reviewed by `auto-improve-autoskill` + Blackrod for constraint changes.

---

## 0. Governing authority boundary (non-negotiable)

``` ext
Models propose.
Adversaries evaluate.
Lean and Rust produce deterministic evidence.
Authority witnesses attest to the evidence bundle.
The human promotes or refuses.

``` ext

No skill, agent, paper, claim ledger, Lean build, Rust test, certificate, adversarial acceptance, release check, or successful replay may independently create an authority-bearing result.

Every model-produced **receipt, gate output, or internal workflow attestation** carries the no-authority firewall field — the firewall reading, `core_types::authority::AuthorityEffect::None` (`engine/crates/core_types/src/authority.rs:233`). Public manuscripts and publication metadata follow §0a and do not spell this field. The only exception in internal workflow outputs is a typed refusal, represented as `Outcome::Refused(RefusalSource)` (`authority.rs:349,304`) — never as a bare `TypedRefusal` (no such variant exists).

Authority is minted **only** by `CertifiedAuthority::certify` / `certify_checked_packet` (`authority.rs:181`) after the full transition below. A valid local authority transition is the conductor receipt chain (`engine/core_conductor/protocol/`):

``` ext
agent_proposal (producer)              [authority_effect = "None"]
  + i3_review_receipt (independent I3)  [authority_effect = "None"]
  + gate_receipt (deterministic)        [host-recomputed hashes]
  + terminal_receipt (witness)          [authority_effect ∈ {None, Refused}]
  + explicit human promotion
  = AuthorizedLocalResult

``` ext

The design-vocabulary names `ProducerReceipt / IndependentEvaluationReceipt / AuthorityWitnessAttestation / ReceiptDAG / AuthorizedLocalResult / HumanPromotion` are **aliases** (see Appendix D); the wired constructs are the four conductor JSON schemas above. **This contract binds to the stable Rust types + conductor schemas; the conductor-doc terminal/receipt names are an alias layer that may still be canonicalizing — do not depend on their spelling.**

The authority firewall itself (14 universal + 6 per-layer forbidden claims) is **referenced, not copied**: see `/panep-math-and-physics-prof` → *Authority Firewall*. Anchor: **"coherence organizes, descent authorizes."** Universal #14: exploratory Python/DDA ≠ Rust/Lean authority.

## 0a. Public manuscript surface boundary

The authority-firewall vocabulary is internal receipt language. It MUST NOT be emitted into reader-facing public surfaces: paper title blocks, abstracts, mechanism inventories, generated PDF/TEX/TXT exports, public notebooks, README/quick-start prose, Zenodo descriptions, or MathOverflow posts. Forbidden public strings include `AuthorityEffect`, `Authority Effect`, `authority_effect`, and `AuthorityEffect::None`, unless quoting a machine-readable receipt schema in a support appendix explicitly labeled as such.

Use ordinary prose such as "Evidence scope" only when the reader needs it. Prefer one concise scope/nonclaim note near the beginning and move detailed proof-status, receipt, and authority-ceiling material to claim ledgers, manifests, or support docs. Do not wrap every theorem/result/example in repeated defensive prose.

Author, Date, and Version must be stacked as separate fields, not collapsed into a pseudo-paragraph.
- **Pre-Print Versioning:** Version in public paper headers MUST be formatted as `<version_number> Pre-Print` (e.g., `1.5.0 Pre-Print`).
- **Elimination of Internal Classifications:** Public paper headers, generated `.tex`, and `.pdf` MUST NOT carry internal repository metadata (`Paper ID`, `Paper Identity`, `Document class`). Those classifications belong solely in companion claim ledgers, change logs, and manifests.
- **Elimination of Placeholder DOIs:** Pre-prints must NOT embed speculative, unminted, or placeholder DOIs (`10.5281/zenodo...`) in the public manuscript title block.

---

## 1. The twelve stages (every paper operation runs these)

Each stage names the canonical repo type it binds to. Do not mint a second constructor.

| # | Stage | Binds to |
|---|---|---|
| 1 | **Declare the carrier** | ODP Carrier field + `CochainPrimitiveDifference` (`core_homological`); a title/filename is NOT a carrier |
| 2 | **Declare Primitive Difference** (the observed δ, distinct from repair map d₀) | `PrimitiveDifferenceJudgment` (`core_atlas_reconciliation/src/primitive_difference.rs:11`) |
| 3 | **Declare `ZeroRel`** (what counts as no remaining discrepancy) | ODP `ZeroRel`; `PrimitiveDifference::zero_related` |
| 4 | **Type the cochain realization** — exactly one of `Exact` / `Structural` / `Unresolved` | ODP C0/C1/C2, d₀/d₁, `FiniteCochainComplex` (`CoreCore`); d₁∘d₀ witnessed for `Exact` |
| 5 | **Compute `Q1`** (residual mod admissible local repair) | ODP Q¹ = C¹/im(d₀), `QuotientSpace` |
| 6 | **Separate `Phi1` from `Gamma2`** | ODP Φ₁ (quotient mass) vs Γ₂ (closure-failure mass); `lib-verification-loop` Phase 8 gate |
| 7 | **Declare the observer** (frozen at admission) | ODP observer/norm/terminalizer; firewall `OBSERVER_PASSIVITY` |
| 8 | **Identify witnesses** | `ReplayHash`/`ScopedReplayHash`, theorem-level `#print axioms`, `encyclopedia_audit.py`, exact fixtures |
| 9 | **Apply only licensed operators / operads / lifts** | DDA alphabet ODP §A5 `{E,R,C,I,Λ/Meta,D,M,T}`; transport = `LambdaLaw`; cross-carrier needs a transport license + loss ledger |
| 10 | **Route surviving obstructions** (typed) | routes below |
| 11 | **Produce a terminal proposal** (from the canonical set) | §3; sealed only by `terminalize_row`/`certify_checked_packet` |
| 12 | **Compare against prior work** | related-work + imported-theorem provenance; unverifiable citation ⇒ typed obligation, never asserted |

**Stage-10 typed routes:** `PaperEditNeeded · ClaimLedgerRepair · LeanObligation · RustWitnessNeeded · CitationVerificationNeeded · DetectorAdequacyNeeded · TransportLicenseNeeded · LiftLicenseNeeded · CounterexampleSearch · OracleNeeded · HumanDecision · TypedRefusal · SuccessorPacketCandidate`. A skill may *propose* a successor; it may not silently create unbounded recursive work or mark it complete.

**Never invent decorative cohomology.** If the d₁∘d₀ mapping is only structural, type it `Structural` and record the limitation. Ceremonial cochains are refused (`CEREMONIAL_COCHAIN`, Appendix C).

---

## 2. Diagnostic classes are NOT terminals

Keep two vocabularies separate (Paper 000 body:412-431 is the canonical example):

- **Diagnostic classes** (mathematical): `ExactClaimBinding · ClosedResidual · OpenResidual · NoRule · CitationUnverified · FormalizationMismatch · ImplementationMismatch`. *These do not imply authority.*
- **CODA_GTLA terminal proposals**: §3.

A closed residual is **not** automatically a stabilized survivor — stabilization requires evidence that no admissible repair remains under the declared observer, operator registry, and budget. A passing build is not approval. A certificate is not authority.

---

## 3. Canonical terminal set + reconciliation (residual R2)

The paper-compliance terminal surface (the canonical terminal set, already used by Paper 000):

``` ext
ExactRepair · StabilizedSurvivor · OpenObstruction · OracleNeeded ·
LiftLicenseNeeded · Refused · Invalid · InfrastructureFailure

``` ext

Bound to the **stable Rust types** (this is the authoritative binding; the conductor-doc terminal is the alias):

| Surface terminal | Stable Rust binding | Notes |
|---|---|---|
| `ExactRepair` | `ObstructionStatus::ExactRepair` (`core_functional/src/trichotomy.rs:16`) | core trichotomy |
| `StabilizedSurvivor` | `ObstructionStatus::StabilizedSurvivor` | ODP §5 spelling `ClosedSurvivor` (R8) |
| `OpenObstruction` | `ObstructionStatus::OpenObstruction` | ODP §5 spelling `OpenResidual`/`ActiveClosureFailure` (R8) |
| `OracleNeeded` | `RefusalSource::OracleNeeded` (`authority.rs:304`) / atlas `LicensedLift` sibling | oracle ≠ operation (ODP §A3) |
| `LiftLicenseNeeded` | `RefusalSource::NoLiftFound` / atlas `TerminalStatus::LicensedLift` | 3 spellings reconciled (R4): `LiftNeeded` (ODP) / `LicensedLift` (atlas) / `LiftLicenseNeeded` (doc+here) |
| `Refused` | `Outcome::Refused(RefusalSource)` (`authority.rs:349`) | carries a `RefusalSource`; **not** `TypedRefusal` (R3) |
| `Invalid` | `gate_receipt.gate_verdict` `Fail`/`Refuse` (`gate_receipt.schema.json`) | no core Rust enum variant (R5) |
| `InfrastructureFailure` | `gate_receipt.gate_verdict::InfrastructureFailure` | environmental; not a math result |

Broadest Rust enum for cross-checking is `core_atlas_reconciliation::row::TerminalStatus` (`row.rs:90`). **Diagnostic classes (§2) map INTO this set; they are not members of it.**

---

## 4. Roles (differ only in access/permission/observer/ceiling)

| Role | Skill | May write | Evidence ceiling | Terminal ceiling |
|---|---|---|---|---|
| **Producer** | `paper-improver` (+ `math-prover`) | the paper + its ledgers | proposes; internal no-authority receipt | may propose a terminal, cannot seal |
| **Independent evaluator** | `paper-adversary` (+ `math-adversary`) | **READ-ONLY by default** (residual C1 fix) | recomputes audit on frozen carrier; internal no-authority receipt | acceptance carries no authority |
| **Math-dev (paper-scoped)** | `core-math-dev` (rip-papers mode only) | ENC entries + proof ledgers (owned surface); **not** unbounded queue | prepares claim/ENC/Lean candidates; internal no-authority receipt | no authority; may SKIP when no Lean surface |
| **Lean producer** | `paper-lean4-improver` | `lean4/research_programs/*.lean` + lakefile roots; ledger `lean_refs` only | produces Lean + build receipts; internal no-authority receipt | may not self-ACCEPT; no MECHANIZED mint |
| **Lean independent evaluator** | `paper-lean4-adversary` | **READ-ONLY** (receipts only) | recomputes Lean audit; internal no-authority receipt | ACCEPT carries no authority |
| **Authority witness** | `paper-proof-signoff` | receipts only; paper-local ledger + `docs/lean_claim_map.md`; encyclopedia not required | inspects receipts + Lean/Rust/citation | emits attestation-shape or `RepairRequired`/`OpenObstruction`/`RefusalRecommended`/`OracleRequired`; **never** `AuthorizedLocalResult` |
| **Release boundary** | `paper-release` | tags/metadata only | parity + preflight | `pre-flight-passed` is a proposal until human promotion |
| **Bundle builder** | `paper-build` | build artifacts (`.tex/.pdf/.zip`) | LEAN4 hard gate | `BUILD: COMPLETE` mints nothing |
| **Orchestrator** | `rip-papers` | none (spawns roles) | compiles one immutable carrier; prevents self-review + recursive spawn; enforces **dual** finite repair budgets (prose + Lean) | records every attempt incl. rejects |

**Identity separation is mandatory:** a role may not review its own output. The prose producer never grades its own prose; the Lean producer never grades its own Lean; neither selects its own evaluator or promotion policy.

**Adversarial-process integrity:** separation of identity is necessary but not sufficient — an evaluator that is never contradicted is a rubber stamp. Where a process runs adversarial rounds, track the **concession rate** (findings accepted ÷ findings opened). A round at ≥ 0.9 with zero rebuttals is `CAPITULATION_SUSPECTED` and must be discharged by an independent re-derivation of the blocking findings before it closes. Both directions are failures: a producer that concedes everything is not being audited, and an evaluator whose findings are never ruled invalid is not being checked. (Live case: a 5-round dialogue closing 22 accepted of 22 opened, 2026-07-27.) Applies to `/paper-redteam-dialogue`, `/paper-adversary`, `/math-adversary`.

**ENC write-owner (residual C2 fix):** `entries/**` are hand-authored source owned by `/core-math-dev`. Paper skills are **read + `regen_encyclopedia.py`-verify only** on the encyclopedia. `indexes/**`, `registry.md`, and `indexes/ledgers/paper_*.md` are **generated — never hand-edit** (banner enforced). `paper-release` no longer edits ENC entries "in lockstep"; on a last-minute theorem-altering edit it routes `ClaimLedgerRepair` + `LeanObligation` and blocks.

**Paper-local override:** For a paper folder that already carries its prose, production `code/`, `code/tests/`, nested `lean4/`, companion claim ledger, and `docs/lean_claim_map.md`, **that folder is the evidence bundle**. Do **not** require `engine/research/encyclopedia`, ENC indexes, `paper_<NNN>.md` ledger views, or `regen_encyclopedia.py`. Missing encyclopedia is **not** a BLOCK. The ENC write-owner / ledger-ENC parity rows apply only when an encyclopedia is declared as part of that paper's evidence bundle. Stage skills win over this contract wherever they state the paper-local rule.

---

## 5. Mandatory paper-audit checks (summary; full reason codes Appendix C)

- **Primitive Difference vs d₀** kept distinct; explicit `Zero`/`ZeroRel` wherever quotient language is used.
- **Hypothesis separation** — algebraic (modules, d₀/d₁, d₁∘d₀=0, quotient) vs metric (normed carrier, separated quotient, bounded maps, attainment) vs convex/LP (finite-dim real, exact+dual gauge, strong duality) vs continuum (closure of image, ε-witnesses, compactness/reflexivity). Reject a norm/duality/finite-dim result asserted under only ring-level assumptions.
- **Observer/gauge discipline** — declared gauge; *selected* (proven) vs *chosen* gauges distinguished; calibration constants tracked; gauge-relative ≠ intrinsic/scale-invariant; detector adequacy for any authority-bearing application; collapsing observers (that make everything look exact) flagged.
- **Φ1/Γ2 separation** — quotient residual mass tracked apart from closure/composition defects; exact norm typing (`J→1`, not stale `1→1` — Paper 000 body:493,533 is the live example); reject undefined "≈ 0" without declared tolerance+observer; reject undefined tie-break quantities (e.g. `Ξ`) without a separate contract.
- **Carrier/transport discipline** — compare before/after only under the same carrier/observer/gauge/normalization; carrier-changing claims require a cochain transport + compatibility laws + loss ledger + replay witness; a Rust finite fixture cannot establish a continuum/physical claim; a Lean toy theorem cannot discharge a stronger paper theorem.
- **Theorem/proof hygiene** — no definition-as-theorem; no sketch-as-proof; no conjecture made to look proven by termination/finite search; no "by construction" without the construction + exact hypotheses; no silent weakening to match an available Lean result; split compound theorems whose clauses need different hypotheses.
- **Lean binding hygiene** — exact theorem name + source file + statement hash + import-block hash + build target + **current** build receipt + `sorry`/`admit` scan + theorem-level `#print axioms` + paper-claim-vs-Lean-statement comparison + explicit "what remains prose-only". A historical green build does not witness edits made afterward. (Paper 000a has **no** Lean dir — its mechanization is prose-only/proposed; that must be stated, not implied.) **A green build certifies elaboration and kernel-check, never that a declaration means what its own docstring says** — compare the *statement* to the docstring, not just to the paper (`DOCSTRING_STATEMENT_MISMATCH`). Live examples: a "preserves non-authority for any valid execution sequence" docstring over a `rfl` on one fixed stage chain with no quantifier; a "non-authority firewall" theorem that is `Sum.inl ≠ Sum.inr`, true for **any** two types and therefore carrying zero domain content. Count the terms: a 4-term prose theorem mechanized as a 2-term core is `MECHANIZED_CORE_ONLY`, not "mechanized".
- **Premise inhabitation & vacuity audit (`VACUOUS_PREMISE_THEOREM`)** — `#print axioms` cannot detect premise inconsistency. Audit theorem hypotheses to ensure they are jointly satisfiable (e.g. non-zero commutator premises over commutative rings like $\mathbb{R}$ make $[H,A]=0$ identically, turning $h_{non\_zero}$ into an impossible premise and rendering positivity vacuously true). Any theorem whose premises are contradictory or unsatisfied by all domain objects MUST be rejected.
- **Trivial identity overclaims (`RFL_TRIVIALITY_OVERCLAIM`)** — reject any proof consisting solely of `rfl` (e.g. `f.linearPart = f.linearPart := rfl`) when claimed as mechanization of differential structures, Jacobians, or connections without actual formalization of charts or derivatives.
- **Synthetic evidence & positivity hacks (`SYNTHETIC_POSITIVITY_HACK`)** — Python simulation or evidence scripts must NOT introduce non-physical floor clamping (e.g. `max(..., 0.1)`) or synthetic polynomials to manufacture positivity or extrapolate finite regressions. Evaluators must inspect script logic for artificial bounds.
- **Evidence independence** — a receipt is inadmissible when the artifact it attests to **emitted it**. A measurement harness that writes its own adversary receipt or proof-signoff receipt has produced no independent check (`SELF_CERTIFYING_RECEIPT`). Equally, read the harness source before grading its verdict: a `BENCHMARK_VERIFIED` disposition over a **hardcoded** comparison denominator measures the corpus, not the protocol. A receipt's self-declared status is a claim, not evidence.
- **Claimed side-effects must be verified on disk** — relocation/ingress/renumber receipts routinely assert stubs left behind, kernels moved, or indexes updated that were never performed (`CLAIMED_SIDE_EFFECT_UNPERFORMED`). Before citing such a receipt, `ls` the asserted paths. Two live instances from one 2026-07-27 relocation: promised `100_mathematical_foundations/` path-only stubs that do not exist, and Lean kernels left behind in the old programme home while the paper moved.
- **"Absent" is not "never existed"** (autoskill 2026-07-29, same `CLAIMED_SIDE_EFFECT_UNPERFORMED` family, inverse direction). A path missing at the commit you checked is not evidence it was never created — only `git log --diff-filter=AD --follow -- <path>` (or equivalent) supports a "never existed" claim; a plain absence check supports only "absent as of here." Live instance (CODA_GTLA flagship run, 2026-07-29): a repair pass fixed a stale "the archive was created" claim by rewriting it to "the archive never existed" — itself false, since the archive was created by one commit and removed by a later one, both findable in two `git log` calls. The paper-adversary caught it by re-deriving the history independently; the producer had checked disk absence and stopped there. Same rule as the sibling bullet above, opposite polarity: before writing *any* disposition sentence about a path (created, moved, removed, never existed), the claim must match the full history, not one snapshot.
- **New normative rules must be checked against the corpus that already uses their vocabulary** (autoskill 2026-07-28, `NORMATIVE_RULE_CONTRADICTS_CORPUS`). Adding a fence, dominance law, or terminal-interaction rule is a corpus-wide edit even when it lands in one paper: every published use of the same terminal/enum must remain legal under it. Run an adversarial pass whose only job is to find a *published* counterexample, and check the **ground** of each existing use, not just its scope. Live save: a drafted "witness dominance" fence would have outlawed CODA-A's own canonical global `BudgetUnknown` (§S2.5/§S11.6, GTTA-9/13/18), where every declared shadow attempt *completes* and what is missing is a cofinality proof — no budget, no incomplete classifier. The fence needed two lawful grounds, not one. A rule that makes existing published theorems illegal is a defect in the rule.
- **"Where is this handled?" is answered at the enforcement surface, not in prose** (autoskill 2026-07-28). When a reviewer asks where a property is enforced, open the code/Lean that would enforce it and read the control flow. Doctrine asserting a property, and an implementation enforcing it, are independent facts. Live case: a terminalizer tested `budget_exhausted` *before* the evidence policy and returned immediately, so a witnessed obstruction was downgraded to a resource terminal — and a sorry-free theorem certified that downgrade unconditionally. The honest answer was "it is not handled; here is the line," not a citation. Report the defect; do not paper over it with a fence that describes intent.
- **Rust binding hygiene** — crate/module/public symbol/exact test + command receipt (`gate_receipt`) + arithmetic exactness ceiling + input carrier + replay hash + explicit diagnostic-vs-evidence-vs-authority statement. A passing test is not a theorem absent a verified binding.
- **Ledger/ENC parity** — body theorem labels ↔ inline claim ledger ↔ standalone Claim Ledger ↔ changelog ↔ release status. When encyclopedia is present, also global proof ledger (`research/encyclopedia/proof_ledgers/proof_ledger_<YYYYMMDD>.md`) ↔ per-paper ENC view (`indexes/ledgers/paper_<NNN>.md`) ↔ ENC entry status/lean_refs. When encyclopedia is absent, the parity gate is **paper ↔ companion ledger ↔ `docs/lean_claim_map.md`** (paper-local override). Never erase an open obligation because a nearby weaker theorem compiled.
- **Realizability vs blind direction (Pass 37/38 C2-R11/R12)** — nontrivial joint kernel $K_e \neq \{0\}$ indicates a detector blind direction, but Local Green / Global Red requires an explicit section $s \in C^0$ realizing $I(s) > 0$ with $\Delta(s)_e \in K_e \ \forall e$. Never conflate arbitrary edge cochain coordinates $\omega_e$ with section defects $\Delta(s)_e$.
- **Path-B carrier scope (Pass 37/38 C2-R14)** — operator curvature identities such as $d_{1,\le} d_{0,\le} = \mathcal{K}$ hold on Path-B comparable-pair carriers ($C^1_\le, C^2_\le$) and must not be asserted on native cover-edge carriers $C^1_{\operatorname{cov}}$.
- **Terminal source attribution (Pass 37/38 C2-R15)** — in dependency tables, definitions and load-bearing theorems must cite their terminal derivation source (e.g. PO-003 §3.1 for observation presentation $\mathfrak{O}_m$, PO-000 §7.4 for watcher-kernel theorem, FOC-000 Lemma O1 for Observer Passivity). Scope-fence/analogy papers (CODA 011, CODA 013, FOC-001, QM-070, QM-080, QM-120) must be explicitly typed as analogy/fence and never cited as theorem premises.
- **Closed-range quotient condition (Pass 37/38 C2-R16)** — for repair distance $\Phi_1(\omega) = \inf_\alpha \|\omega - d_0 \alpha\|_1$, $\Phi_1(\omega) = 0 \iff \omega \in \operatorname{im} d_0$ requires $\operatorname{im} d_0$ to be closed (satisfied in finite dimensions or under a separated quotient norm). Use "repair-infimal" unless attainment is proved.

---

## 5a. Claim-ID ownership, residual packaging, finite notions (autoskill 2026-07-24)

- **Claim-ID ownership:** claim prefixes must match the owning paper number (`QM_014` → `QM-014-C*`, never `QM-029-C*`). Residual packaging and improver passes re-check body ↔ ledger prefixes before writing new rows. Mismatch → `CLAIM_LEDGER_DRIFT` / packaging reject.
- **Residual packaging ceiling:** freezing a finite carrier or counterexample table for a residual ID is **packaging only** — do not upgrade claim type to MECHANIZED, close PL-* Lean gates, or imply GlobalGreen/Zenodo-ready without separate `/paper-proof-signoff` receipts and human promotion. Prefer terminal label `RESIDUAL_DISCHARGED_BY_PACKAGING` when that is all that was done.
- **Finite notions (non-identification):** do not silently equate **finite cardinality**, **finite dimension**, **finite presentation**, **finite certificate**, **unbounded finite refinement**, and **completed carrier**. Completions require a declared `CompletionLaw`.
- **Time-bounded Lean:** if a focused `lake`/`cargo` build cannot finish inside the cycle, record `LEAN_BUILD_STALE` / `InfrastructureFailure` — never invent MECHANIZED.
- **Concurrent packaging branches:** if two worktrees touch the same paper, emit a path inventory + claim-ID collision scan before review/PR.
- **Dual-worktree compose (not last-writer-wins):** when two packaging worktrees diverge on shared papers, land doctrine/synthesis first, residual packaging second. Classify each shared path as orthogonal (keep both sections) vs hard compose (skeleton + residual). Write a merge plan + receipt before PR. (autoskill 2026-07-24 LGGR B→A merge.)
- **Paper renumber / dual-alias (path IDs vs ENC aliases):** when published papers renumber (e.g. foundation-first `qm_NNN`), freeze a YAML map before moves; update ENC `aliases` to dual `paper:qm{OLD}:*` **and** `paper:qm{NEW}:*`; run `regen_encyclopedia.py`; regenerate `dual_alias_registry.md` **from the full map** (not a partial table); append-only historical `proof_ledger_*.md`; never renumber `PL-*`. Path-only denser stubs must not claim `paper:qmNNN`/MECHANIZED ownership until ENC attaches. Prefer stub IDs **outside dual-live old roots** (re-id to a free band such as `200+` when a denser stub would collide with a dual-live destination); leave foundation path-only stubs (e.g. `QM_000`) unmoved when re-id would thrash. **Prose ID rewrite must be path-aware:** for each file, skip any remap where `old_id == path_qm_NNN` (double-map ban when destination NNNs already live as paths). **Never prose-rewrite** `dual_alias_registry.md`, programme `README.md`, or generated `paper_map.md` — regenerate maps from YAML after path moves. (autoskill + auto-symmetry-hunter + path-aware follow-up 2026-07-24.)
- **Dual claim-ID renumber:** if both branches invent the same claim id for different statements, renumber — never leave a silent collision (e.g. C13 completion-law vs C13 residual → C13 + C14). Re-anchor paper body, ledger, and changelog together.
- **Body ↔ ledger claim tags:** residual sections that own a ledger row must name claim <PREFIX-Cn> in the section header/lead; paper claim tables must list residual rows present in the ledger (no residual-only orphans).
- **Changelog honesty:** never state that a ledger row was enriched/retyped unless the table text actually changed; prefer fix-the-row over changelog theater.

## 5b. Engine Primitives / mechanism inventory

For internal hygiene papers and support documents that need operator/carrier context, keep an Engine Primitives or mechanism-inventory table in support docs or an appendix. Final public papers are not required to carry this box near the top; do not put it before the abstract when it makes the paper harder to read. If the inventory is included in a public paper, keep it compact, reader-facing, and free of house receipt vocabulary.

| Slot | Required content |
|---|---|
| **Primitive Differences** | admitted cut / what non-sameness is presented (not prior objects) |
| **Carriers / Structure** | exhibited finite carrier or packet field |
| **Cochain complex** | bindings for `C^0`, `C^1`, `C^2`, and `C^{>=3}` when needed (else typed absence) |
| **Coboundary maps** | `d0`, `d1`, and higher maps when needed (else typed absence) |
| **ZeroRel** | what counts as no remaining discrepancy |
| **Licensed repairs / operator family** | licensed operator/operad family or typed absence |
| **Quotient / Q1** | how Q¹ is formed when quotient language is used |
| **Residuals** | residual packaging that **distinguishes Phi1 from Gamma2** |
| **Witnesses** | witness role / receipt carrier (distinct from observer when used) |
| **Observers / profiles** | declared embedded profile locus (not view-from-nowhere) |
| **Sentinels** | sentinel packaging or typed absence |
| **CompletionLaw** | named law or `N/A` / `OPEN` / `OracleNeeded` |
| **Terminal / route** | proposed terminal or typed route |
| **Evidence scope** | optional reader-facing statement of what receipts/tests/proofs cover; omit if a concise scope note already says it |

**Typed absence only:** unused concepts require a non-empty typed value such as `N/A`, `OPEN`, or `OracleNeeded`. Empty cells and invented bare `PROVEN` claims are forbidden.

Missing slots are `MISSING_CARRIER` / `MISSING_PRIMITIVE_DIFFERENCE` / `OBSERVER_UNTYPED` / `MISSING_PRIMITIVE_SLOT` candidates — not automatic GlobalGreen. Run `/governance-wdp` (mandatory under `/lib-master-librarian` paper audit) when inventory is present but prose still smuggles hosts or cosmic observers. Lean and encyclopedia companion gates are owned by `/lib-master-librarian`.

This inventory is the support-level handle for treating the Core stack as a **replayable algorithmic carrier** (flip declared slots, re-solve, read residuals) rather than narrative doctrine. It does **not** mint authority or select physical QM. Never include an `AuthorityEffect` row or string on public paper surfaces.

**Publish-facing link policy (deterministic `coda-check-paper`):** publish Markdown must not contain local/repo links (`file:`, `sandbox:`, relative paths, Windows/Unix absolutes, raw `.agents/` / `.claude/` / `.codex/` / `.grok/` / `engine/` paths). Allowed: `https:`, DOI/Zenodo, same-document `#anchors`. Claim ledgers, proof spines, receipts, and ZIP manifests may retain canonical internal paths.

**Publish-facing dialect policy:** public Markdown, notebooks, PDF/TEX/TXT exports, and Zenodo/MO copy must not contain house receipt strings (`AuthorityEffect`, `Authority Effect`, `authority_effect`, GlobalGreen-style labels, role receipts) except inside clearly labeled machine-schema appendices. Keep the main paper in ordinary mathematical prose.

## 5c. Research-system layout (`research_layout`)

Canonical law for every paper under `engine/research/published/` (not only `001_coda`). **Do not re-host the full checklist in stage skills** — cite this section + run the gate.

```text
Gate: python -m core_pipelines coda-check-paper --paper <path> [--repo-root .]
Narrative home: /lib-master-librarian research-system layout invariants
Claim-ID diagnostic (optional companion): python engine_py/tools/claim_id_bijection.py --paper <path>

``` ext

**Dual-accepted path shapes** (both are valid papers when companions exist; snake_case only: `a-z`, `0-9`, `_`):

| Shape | Paths | Notes |
|---|---|---|
| **Flat programme root** (live CODA/WD/QM packaging 2026-07-25) | `published/{nnn}_{program}/{stem}.md` + `{stem}_claim_ledger.md` + `{stem}_change_log.md` at the **same** programme root | Park non-primaries under `_support/`; book/Principia trees may remain nested (e.g. `001_coda/009_coda/`) |
| **Nested paper folder** (legacy / still accepted) | `published/{nnn}_{program}/{paper_slug}/{paper_slug}.md` (+ companions in that folder) | Stem matches slug; optional version suffix `_vN_N` |

| Rule | Requirement |
|---|---|
| Paths | One of the dual shapes above — **not** two live homes for the same paper |
| Primary MD | Exactly one primary paper `.md` per paper identity (stem matches slug; optional `_vN_N`) |
| Companions | **`{paper_stem}_claim_ledger.md`** and **`{paper_stem}_change_log.md`** required beside the primary |
| Paper Body Separation | **Paper body (`{paper_stem}.md`) MUST NOT contain an embedded changelog or embedded claim ledger table.** All version history lives in `{paper_stem}_change_log.md`; all claim IDs and statuses live in `{paper_stem}_claim_ledger.md`. Embedded changelogs/ledgers in `{paper_stem}.md` trigger `PAPER_BODY_POLLUTION` blocking findings. |
| Changelog home | Version history **only** in `_change_log.md` — never paper body or claim ledger |
| Header | Markdown header (no YAML frontmatter); Date = last-updated `YYYY-MM-DD` |
| Min sections | Title · Subtitle · Paper MetaData · Abstract · Why care · Falsifiability · References |
| Dual ledgers | Prefer migrating legacy `*_Claim_Ledger.md` / `Adversarial_Claim_Ledger_*` when the folder is touched — never two live claim ledgers |
| Classifier | Loose control MD (`README.md`, K-tables, indexes) are **not** papers; multi-primary folders need workspace fence |

Pipeline roles: improver creates/repairs companions; adversary/proof-signoff/release/build treat missing dual companions or dual live ledgers as layout hygiene (`CLAIM_LEDGER_DRIFT` / layout BLOCKED); `rip-papers` may preflight the gate and must skip companions as targets. **Gate implementers must dual-accept flat roots** — nested-only classifiers are STALE against the 2026-07-25 estate.

**Vendored third-party bundles are FROZEN — exempt from every naming/normalization pass** (autoskill 2026-07-28). Any in-repo copy of an external artifact (Zenodo/DOI record, upstream release, licensed bundle) is verbatim evidence: its filenames and file *contents* are hash-bound by its own manifest. The snake_case/lowercase law above stops at its root. Observed cost: `4239b1f91` "Lowercase snake_case every name under research/published" rewrote a vendored Zenodo bundle's `README.md`→`readme.md`, `SHA256SUMS`→`sha256sums`, `lean-toolchain`→`lean_toolchain` **and in-file text including the Apache `LICENSE-2.0` URL**, so it no longer self-verified; recovery required re-downloading the original and a 74-file re-baseline. Rules: exclude vendored roots from bulk renames; verify with the bundle's own manifest (`sha256sum -c`) **before and after** any tree-wide pass; keep local additions in a sibling directory, never interleaved; on drift, re-fetch upstream rather than hand-repairing. Cite here — see also `frozen-surfaces` (golden fixtures, hash-bound ledgers, certificate filenames).

## 5d. Document classes — archive omnibus vs thin extract vs chapter (autoskill 2026-07-26)

Estate papers (esp. `008_engine_runtime` and compressed extracts under `100_mathematical_foundations`) must declare **exactly one** document class. Dual status is `SCOPE_PROMOTION` / packaging false-green.

| Class | Example | Claim surface | Bijection / release |
|---|---|---|---|
| **Chapter / stem paper** | FOC chapter, goals engineering spec | `{stem}_claim_ledger.md` owns IDs | claim-ID bijection is a hygiene gate |
| **Thin canonical extract** | `100_…/008_the_skill_everywhere.md` | extract ledger only; F3/P0 **interfaces + OPEN obligations** | may be Stage-2 unit; PROD LIVE still BLOCKED until PL receipts |
| **Archive omnibus** | `008_engine_master.md` | **`NON_CLAIM_SURFACE`** — concatenated historical ledgers only | body↔ledger bijection on the omnibus unit is **not** a release gate; expected REPAIRABLE/BLOCKED |

**Hard rules:**

1. Never re-label an archive omnibus `UNIFIED_MASTER_MONOGRAPH` while red-team says `REJECT AS CANONICAL MONOGRAPH`.
2. Red-team P0 repairs (DetectorAdequacy, RuntimeSafe, RuntimeStep, capability fence, 6-axis lattice) work the **thin extract path**, not by re-promoting the omnibus.
3. Specifying a P0 interface is not discharging it — demote `[PROVEN]` / "resolves all P0s" theater to DEFINITION / OPERATIONAL RULE / OPEN + `PL-*`.
4. Soft same-day I3 ACCEPT without tool recompute (bijection / red-team P0 residual) must be **SUPERSEDED** when contradicted.
5. Same-session producer+adversary → `independence_class` reduced; fireproof ACCEPT needs a **second-agent** I3 before release.
6. Claim-ledger first-column IDs only (no dual-cell `A / B`); avoid body globs that false-match claim families under `claim_id_bijection.py` (e.g. bare `PREFIX-*` or PL IDs that substring-match claim prefixes).
7. Document class and internal Paper ID declarations belong strictly in companion manifests and claim ledgers. Never insert `**Document class:**` or `**Paper ID:**` into the public manuscript title block, generated TeX, or PDF.

## Appendix A — PaperCompliancePacket (ODP profile)

A `PaperCompliancePacket` is a paper-carrier **profile of the ODP** (`engine/crates/core_contracts/src/contract_canonical_definitions/core/09_packets/core_obstruction_packet_standard.md`). A paper release **is** a promotion event (ODP §6: *"No Core artifact may be promoted unless it declares its obstruction packet"*). Fields:

``` ext
paper identity · version + artifact hash · base Git revision · carrier manifest ·
Primitive Difference · ZeroRel · cochain realization (Exact/Structural/Unresolved) ·
observer context · claim inventory · claim→ledger bindings · claim→Lean bindings ·
claim→Rust bindings · citation obligations · Phi1 residuals · Gamma2 defects ·
licensed transports/lifts · witness commands · evidence ceilings · survivor routing ·
terminal proposal · internal authority-effect receipt field (= None)

``` ext

## Appendix B — PaperRoleReceipt (conductor schemas)

One common shape reusing the conductor receipt trio (do NOT introduce new Rust types):

- **Producer** → `agent_proposal.schema.json` (`core.agent_proposal.v1`, `authority_effect="None"`).
- **Independent evaluator** → `i3_review_receipt.schema.json` (`independence_class="I3_CROSS_MODEL"`, findings `{severity P0-P3, category, blocking}`, `authority_effect="None"`).
- **Deterministic gate** → `gate_receipt.schema.json` (`gate_verdict ∈ {Pass,Fail,Refuse,Inconclusive,InfrastructureFailure}`, host-recomputed hashes).
- **Authority witness / terminal** → `terminal_receipt.schema.json` (`coda_gtla_terminal`, `authority_effect ∈ {None,Refused}`).

**PaperReleaseBundle** = final paper hash · standalone-ledger hash · ENC parity receipt · proof-ledger parity receipt · Lean receipts · Rust receipts · citation report · scope/nonclaim report · unresolved-obligation report · authority-witness attestation · human-promotion placeholder · (`.zip` + Zenodo block, `paper-build`).

## Appendix C — Reason-code namespace (maps to existing codes)

Stable machine codes; each maps to an existing repo construct (no new enums — residual R-reasoncodes):

| Reason code | Maps to |
|---|---|
| `MISSING_CARRIER` / `MISSING_PRIMITIVE_DIFFERENCE` / `MISSING_ZERO_REL` | ODP anti-patterns §11; `borges` `RawNull` |
| `CEREMONIAL_COCHAIN` / `D1_D0_UNVERIFIED` | `lib-verification-loop` Phase 8 counterfeit-descent |
| `GAUGE_UNDECLARED` / `GAUGE_SELECTION_OVERCLAIM` / `NORM_TYPE_MISMATCH` | firewall `OBSERVER_PASSIVITY`; §5 gauge discipline |
| `OBSERVER_UNTYPED` / `DETECTOR_ADEQUACY_MISSING` | firewall Ω∂ row |
| `CARRIER_TRANSPORT_MISSING` | ODP transport / `LambdaFailure` |
| `CLAIM_LEDGER_DRIFT` / `ENCYCLOPEDIA_DRIFT` / `OPEN_OBLIGATION_ERASED` | `borges` `GeneratedViewDrift`/`ProjectionLoss`; parity gate |
| `LEAN_STATEMENT_MISMATCH` / `LEAN_BUILD_STALE` / `LEAN_AXIOM_DRIFT` | `#print axioms` audit |
| `DOCSTRING_STATEMENT_MISMATCH` / `MECHANIZED_CORE_ONLY` | §5 Lean binding hygiene — declaration vs its own docstring; term-count of prose theorem vs mechanized statement |
| `SELF_CERTIFYING_RECEIPT` | §5 Evidence independence — attesting receipt emitted by the attested artifact |
| `CLAIMED_SIDE_EFFECT_UNPERFORMED` | §5 — receipt asserts moves/stubs/index updates absent on disk |
| `CAPITULATION_SUSPECTED` | §4 Adversarial-process integrity — concession rate ≥ 0.9 with zero rebuttals |
| `RUST_BINDING_MISSING` / `RUST_EXACTNESS_OVERCLAIM` | `gate_receipt` |
| `CITATION_UNVERIFIED` | Stage-12 obligation |
| `DIAGNOSTIC_TERMINAL_CONFLATION` / `CERTIFICATE_AUTHORITY_CONFLATION` / `SCOPE_PROMOTION` | firewall universal #3/#12; `AuthorityRefusal` |

## Appendix D — Known residuals (surfaced, not silently reconciled)

R1 `AuthorityEffect` overloaded (firewall vs contract-taxonomy enum) — this contract uses the **firewall** reading. R2 no single Rust terminal enum — §3 reconciliation. R3 `TypedRefusal`→`Refused(RefusalSource)`. R4 `LiftLicenseNeeded` 3 spellings. R5 `Invalid`/`InfrastructureFailure` only in doc+`gate_verdict`. R6 promotion/receipt names design-only → conductor schemas (**being canonicalized by the concurrent conductor-doc workstream**). R7 operator-manifest gaps (`observer`/`witnesses`/`operator id` absent from `core.agent_work.v1`) → paper-operator profile, Appendix E. R8 ODP §5 vs trichotomy spellings. R9 §8 spec expects "S6 research-blocked" but Paper 000 records `OPEN/CONJECTURE-CONDITIONAL` — fixture keys on the paper's real status. R10 proof-ledger path drift (skills point at `research/proof_ledger_*`; real path `research/encyclopedia/proof_ledgers/`).

## Appendix E — Operators → gauges (vendor-neutral)

Operators are the reusable transformations; skills are gauge front-ends. Each operator manifest is a **paper profile of `work_packet.schema.json` (`core.agent_work.v1`)** adding `observer`, `witnesses`, `inputs/outputs`, `operator_id` (R7). Operator IDs: `paper.intake.compile · paper.carrier.declare · paper.claim_ledger.extract · paper.claim_ledger.reconcile · paper.coda_gtla.audit · paper.improve · paper.adversary.audit · paper.math_dev.scoped · paper.lean.produce · paper.lean.adversary.audit · paper.formal_binding.audit · paper.lean.verify · paper.rust.verify · paper.citation.audit · paper.scope_fence.audit · paper.release.signoff · paper.release.preflight · paper.bundle.build`. Adapter map: `paper-improver→paper.improve`; `paper-adversary→paper.adversary.audit`; `core-math-dev` (rip-papers mode)→`paper.math_dev.scoped`; `paper-lean4-improver→paper.lean.produce`; `paper-lean4-adversary→paper.lean.adversary.audit`; `paper-proof-signoff→paper.formal_binding.audit + paper.lean.verify`; `paper-release→paper.release.preflight`; `paper-build→paper.bundle.build`; `rip-papers→` orchestrates.

---

**Constraints**

See: [constraints.md](./constraints.md)

Required: RULE_PRIME_0_0, NO_SELF_CERTIFICATION, DIAGNOSTICS_ARE_NOT_PROOF, licenseS_GATE_PROMOTION, EXTERNAL_ORACLE_REQUIRED, EVIDENCE_PATH_REQUIRED, NO_FAKE_DONE, NO_GREEN_THEATER, AUTHORITY_REQUIRES_DESCENT, OBSERVER_PASSIVITY, LOSS_LEDGER_CONSERVATION

**Family:** coda-gtla-papers (see [family_registry.md](./family_registry.md))
