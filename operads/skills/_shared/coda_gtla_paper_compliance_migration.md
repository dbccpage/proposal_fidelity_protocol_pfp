# rip-papers CODA_GTLA Hardening — Migration + Terminal Report

**Branch:** `claude/rip-papers-coda-gtla-hardening` (worktree off `main`@`1cfbce693`).
**Status:** governed `OperatorImprovementCandidate` — **NOT activated**; awaiting independent review + human promotion (task §12). No paper was edited; Paper 000/000a used read-only as fixtures.
**Binding decision (operator):** anchor to stable Rust types; conductor-doc names (canonical terminal, receipt schemas) referenced as an alias layer (insulated from the concurrent conductor-doc workstream).

---

## 1. Deliverables map

| # | Deliverable | Artifact |
| --- | --- | --- |
| 1 | Census report | `scratchpad/rip_papers_coda_gtla_census_and_design.md` (Part 1) + 5 reader passes |
| 2 | Shared compliance contract | `_shared/coda_gtla_paper_compliance.md` |
| 3 | Updated skills | 10 SKILL.md retrofits (below) |
| 4 | Operator/gauge mappings | contract Appendix E |
| 5 | Schemas + templates | contract Appendices A (packet), B (role receipt + release bundle), C (reason codes) |
| 6 | Deterministic tests | `_shared/coda_gtla_paper_compliance_check.sh` (+ `auto-symmetry-hunter` invariant #8) |
| 7 | Fixture reports | Paper 000 + Paper 000a dry-runs (this session) |
| 8 | Migration report | this file |

## 2. Files changed (14)

**New (2):**

- `_shared/coda_gtla_paper_compliance.md` — the one contract: 12 stages bound to real repo types; §2 diagnostic≠terminal; §3 terminal set + Rust reconciliation; §4 roles; §5 mandatory checks; Appendices A–E; residuals A–D; Authority Firewall referenced (not copied).
- `_shared/coda_gtla_paper_compliance_check.sh` — deterministic gate (contract sections; every member references contract + declares ceiling + family; no-mint heuristic; producer-no-self-accept; C5 path; `_shared` link resolution; family+invariant registered). **PASS.**

**Modified skills (10):**

- `rip-papers` — orchestrator guards: one immutable carrier, role separation / no self-review, **finite repair budget (default 3)**, no recursive spawn, capture-all-incl-rejects; C5 path fix; build stays separate from pipeline.
- `paper-improver` (producer) — contract ref; producer receipt (`agent_proposal` shape); never self-accepts; C5 path fix.
- `paper-adversary` (independent evaluator) — **C1 fix: now READ-ONLY** (emits `i3_review_receipt`-shape findings, does not patch the paper); six gates reframed as reason-coded findings; C5 path fix; acceptance carries no authority.
- `paper-proof-signoff` (authority witness) — attests over receipts, emits `terminal_receipt`-shape or `RepairRequired/OpenObstruction/RefusalRecommended/OracleRequired`; **never mints `AuthorizedLocalResult`**; ENC read+regen-verify only (C2); C5 path fix.
- `paper-release` (release boundary) — **C2 fix: no longer edits ENC "in lockstep"** — routes `ClaimLedgerRepair`+`LeanObligation` and BLOCKs on drift; `PASSED` = proposal until human promotion; C5 path fix.
- `paper-build` (bundle builder) — contract ref; `BUILD: COMPLETE` mints nothing; `.zip`/Zenodo = PaperReleaseBundle proposal.
- `math-prover`, `math-adversary`, `omega-math-dev`, `panep-math-and-physics-prof` — light wiring: sovereign-header `families: [coda-gtla-papers]`, contract reference, constraints; `math-adversary` notes its six gates are the single shared list (no fork); `panep-math-and-physics-prof` marked firewall HOME (referenced, not subordinated). Existing doctrine untouched.

**Modified governance (2):**

- `_shared/family_registry.md` — new `coda-gtla-papers` family (prose section + `FAMILY_REGISTRY` dict, 10 members).
- `auto-symmetry-hunter` — invariant #8 (`MISSING_PROPAGATION`/`DUPLICATE_RULE`/`AUTHORITY_COLLISION`/`STALE_RULE` for the family).

Diffstat: 12 tracked files +368/−51, plus 2 new files.

## 3. Residuals

**Resolved (contradictions from census):**

- **C1** adversary-writes → `paper-adversary` read-only.
- **C2** ENC write-owner conflict → `entries/**` owned by `/omega-math-dev`; proof-signoff blocks-only, release routes obligations (no lockstep ENC edit).
- **C3** build enable/disable seam → single source: role table (paper-build is the separate bundle builder).
- **C4** two shared docs → one contract consolidating/cross-linking `paper_hygiene_standard.md`.
- **C5** proof-ledger path drift → corrected to `research/encyclopedia/proof_ledgers/proof_ledger_<YYYYMMDD>.md` across improver/adversary/proof-signoff/release; checker guards regression.

**Surfaced, NOT reconciled (per §1 — reported as residuals, contract Appendix D):**

- **R1** `AuthorityEffect` overloaded (firewall vs contract-taxonomy) — contract uses firewall reading.
- **R2** no single Rust terminal enum — §3 reconciliation table.
- **R3** `TypedRefusal`→`Refused(RefusalSource)`. **R4** `LiftLicenseNeeded` 3 spellings. **R5** `Invalid`/`InfrastructureFailure` only in doc+`gate_verdict`.
- **R6** promotion/receipt names design-only (conductor schemas) — **being canonicalized by the concurrent conductor-doc workstream; re-reconcile when it lands.**
- **R7** operator-manifest gaps (`observer`/`witnesses`/`operator id` absent from `omega.agent_work.v1`) → paper-operator profile (Appendix E).
- **R8** ODP §5 vs trichotomy spellings. **R9** §8 expected "S6 research-blocked"; Paper 000 records `OPEN/[CONJECTURE,CONDITIONAL]` — fixtures key on the paper. **R10** proof-ledger path (now fixed in skills; the fixture papers/ledgers themselves still carry the old pointer — a paper-edit obligation, not a skill change).

**New residuals found by the fixture dry-runs (paper-side, out of scope for this task — routed, not fixed):**

- Paper 000: 2× `NORM_TYPE_MISMATCH` (`v2_6.md:493,533` stale `1→1`), `LEAN_STATEMENT_MISMATCH` (L000_04 ℓ¹ vs J-general), stale `v2_5` source pointer + ENC-0772 title drift.
- Paper 000a: `CLAIM_LEDGER_DRIFT`+`OPEN_OBLIGATION_ERASED` risk (standalone ledger marks PL-000BN-2..6 "closed" while global ledger/ENC say NOT-STARTED); missing explicit prose-only-mechanization disclosure.

## 4. Verification / command receipts

- `sh .agents/skills/_shared/coda_gtla_paper_compliance_check.sh` → **`coda_gtla_paper_compliance_check: PASS`** (exit 0). All 7 check groups green (contract sections; 10 members reference contract + ceiling + family; no-mint heuristic; producer no-self-accept; C5 path; `_shared` links resolve; family+invariant registered).
- Paper 000 dry-run → 12 stages instantiable; terminal **StabilizedSurvivor** (`AuthorityEffect::None`); S5/S6 **OpenObstruction**; detections all fired correctly.
- Paper 000a dry-run → all 10 classes confirmed; 3 overclaim-guards correctly did NOT trigger; terminal **StabilizedSurvivor**; PL-000BN-1 **OracleNeeded**; caught the ledger `OPEN_OBLIGATION_ERASED` drift.

## 5. Acceptance criteria (§11)

Met: single 12-stage contract used by every member (checker-verified); operators separated from gauges (Appendix E); producer/evaluator/witness distinct (C1/C2); no member self-certifies/mints (checker + firewall); every run declares the 12 stages; ceremonial cohomology refused (`CEREMONIAL_COCHAIN`); paper↔ledger↔Lean↔Rust↔ENC↔proof-ledger drift detectable (fixtures demonstrated); stale build receipts detectable (§5 Lean hygiene); carrier-changing comparisons require transport; diagnostic≠terminal (§2); open obligations preserved; Paper 000/000a dry-runs produced coherent residual reports; all changed files pass the deterministic checker.

Not claimed: this proves no paper, does not establish CODA_GTLA globally, proves no citation, makes no LLM/adversary a mathematical authority, turns no Lean build into prose-equivalence proof, turns no Rust test into a theorem, and does not automate research judgment or license recursive self-modification.

## 6. Recommendations (later conductor integration)

1. **Re-reconcile R6** once the conductor-doc workstream finalizes the receipt/terminal names; the alias layer localizes the change to contract §3/§0 + Appendix B/D.
2. Automate the runtime-only checks (receipt-shape emission, per-paper Claim-Ledger parity) — today `encyclopedia_audit.py` covers the ENC NDJSON graph, not paper markdown; a `paper.claim_ledger.reconcile` operator implementation is the follow-up.
3. Route the fixture-discovered paper residuals (Paper 000 norm typing; Paper 000a ledger drift) to `/omega-math-dev` / `/rip-papers` as separate paper-edit work.
4. Run `auto-symmetry-hunter --families-only` on the family after any future skill edit (cadence: on any family edit).

---

## TERMINAL REPORT

Using only the canonical terminal set.

| Item | Terminal |
| --- | --- |
| Shared contract + 12-stage adoption across the family | **ExactRepair** |
| Family registration + `auto-symmetry-hunter` invariant + deterministic checker (PASS) | **ExactRepair** |
| C1 (adversary read-only), C2 (ENC owner), C4 (one contract), C5 (ledger path) | **ExactRepair** |
| C3 build enable/disable seam (reconciled to role table; two dated rulings still live in-file) | **StabilizedSurvivor** |
| Runtime receipt-shape emission + per-paper Claim-Ledger parity automation | **OpenObstruction** (contract specifies; not yet coded — recommendation 2) |
| R6 conductor receipt/terminal vocabulary (design-only, in-flight) | **OracleNeeded** (external: awaits the conductor-doc workstream) |
| R7 operator-manifest fields absent from `omega.agent_work.v1` | **LiftLicenseNeeded** (paper-operator profile defined; upstream schema unchanged) |
| Fixture-discovered paper residuals (Paper 000 norm typing; Paper 000a ledger drift) | **OpenObstruction** (routed to paper-edit owners; out of scope here) |
| R9 spec-vs-paper "S6 research-blocked" | **Refused** (spec expectation declined; keyed to the paper's real status) |
| Skill bundle activation | **Refused** (governed `OperatorImprovementCandidate`; human promotion required) |

No `Invalid`, no `InfrastructureFailure`. `AuthorityEffect::None` throughout; nothing here mints authority.
