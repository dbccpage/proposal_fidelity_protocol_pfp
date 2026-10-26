# Drift catalog (auto-symmetry-hunter)

**AuthorityEffect: None.** Historical + standard invariant patterns.
Load on demand from the skill progressive-disclosure table — do not inline into hot SKILL.md.

## Table of Contents

- [Standard Invariants to Enforce](#standard-invariants-to-enforce)
  - [1. Evidence Invariant](#1-evidence-invariant)
  - [2. Test Integrity Invariant](#2-test-integrity-invariant)
  - [3. Self-Certification Invariant](#3-self-certification-invariant)
  - [4. Authority Invariant](#4-authority-invariant)
  - [5. Build Policy Invariant](#5-build-policy-invariant)
  - [6. Citation / Formalization Invariant](#6-citation--formalization-invariant)
  - [7. LLM Output Invariant](#7-llm-output-invariant)
  - [8. CODA_GTLA Paper-Compliance Invariant](#8-coda_gtla-paper-compliance-invariant)
  - [9. Mechanism-surface and Genesis-Bias invariant (CODA / QM papers)](#9-mechanism-surface-and-genesis-bias-invariant-coda--qm-papers)
- [Cross-host packaging patterns (detail)](#cross-host-packaging-patterns-detail)
  - [10. Skill packaging invariant](#10-skill-packaging-invariant)
  - [Non-Invariant Content & LLM Slop Screening (`RULE_NONINVARIANT_CONTENT_PROHIBITION_001`)](#non-invariant-content--llm-slop-screening-rule_noninvariant_content_prohibition_001)

## Standard Invariants to Enforce

### 1. Evidence Invariant

All sprint/workflow/review/execution skills must say:

```text
No evidence path = no credit.

```

Missing this is `MISSING_PROPAGATION`.

Contradicting it is `DANGEROUS_DRIFT`.

---

### 2. Test Integrity Invariant

All code/test/sprint-review skills must reject:

```text
assert!(true)
assert_eq!(1, 1)
construction-only tests
is_ok() as sole assertion
unwrap/expect as sole verification
mock-only safety claims
missing failure-path tests

```

Missing this is `MISSING_PROPAGATION`.

---

### 3. Self-Certification Invariant

No skill or agent may allow:

```text
same-boundary oracle as external
self-audit as final certification
signature/HMAC called proof
internal consistency certified internally

```

Any violation is `DANGEROUS_DRIFT` or `CONTRADICTION`.

---

### 4. Authority Invariant

```text
Blackrod                      = enforcement
Woland                        = adversarial revelation
VP Engineering                = engineering diagnosis
SVP SADC                      = council decision
Techne Code Soviet Inspector  = test-quality veto        (evaluator)
Techne Code Soviet Builder    = NO authority             (producer)
techne-code-contracts-adversary = code-hygiene evaluator (ACCEPT is a proposal)
techne-code-contracts-improver  = NO authority           (producer)
techne-code-{rust,python}-code-reviewer      = evaluator (holds VETO)
techne-code-{rust,python}-principal-developer = NO authority (producer)
techne-code-{rust,python}-tester             = test-pattern reference, not a role
rip-testing / rip-papers / rip-rust / rip-python = orchestration only, mints nothing
ooutwire                      = human override

```

If any artifact reverses or confuses these roles, flag `AUTHORITY_COLLISION`.

**Producer/evaluator pairs are an authority boundary, not a workflow preference.** In
each pair the producer writes and the evaluator rules; neither may do the other's job.
Flag `AUTHORITY_COLLISION` when a producer grades its own output, when an evaluator
patches what it reviews, or when an edit grants a producer a veto. Flag
`DANGEROUS_DRIFT` when an evaluator's ACCEPT is described as authority, promotion, or
`GlobalGreen` — every ACCEPT in these families is a proposal awaiting human promotion.

---

### 5. Build Policy Invariant

For omega_engine:

```text
Linux/CI is canonical build target.
Do not compile omega_engine on Windows unless explicitly requested.
If requested, use single-threaded cargo check/test (-j 1).
No toolchain channel is pinned: a skill that hardcodes `+nightly` or
`+stable` contradicts CLAUDE.md SAGA-26 S3 and is a STALE_RULE.
Never run background builds on Windows.

```

If skills disagree, flag `CONTRADICTION`.

---

### 6. Citation / Formalization Invariant

Domain verification skills must not fabricate citations or claim formal verification without proof assistant output.

Missing this is `MISSING_PROPAGATION`.

Contradicting it is `DANGEROUS_DRIFT`.

---

### 7. LLM Output Invariant

LLM outputs may generate candidates.

They may not:

```text
self-promote to Diamond
certify truth
replace evidence
replace external oracle review

```

---

### 8. CODA_GTLA Paper-Compliance Invariant

Every member of the `coda-gtla-papers` family (membership from regenerated `family_registry.md` — pipeline stages, math loop, coda/lean4/encyclopedia librarians, former prime-governance members, domain managers) must:

Current governance coverage belongs to `governance-wdp`; this does not assign it family membership.

```text
reference _shared/coda_gtla_paper_compliance.md          (else MISSING_PROPAGATION)
carry evidence ceiling AuthorityEffect::None             (else AUTHORITY_COLLISION)
propose terminals only from the canonical set (contract §3)
research_layout companions when writing/auditing papers (contract §5c)

```

And these rules must live in the contract ONCE, not be re-hosted inline:

```text
authority / no-self-certification rules copied into a skill   → DUPLICATE_RULE
the six-gate adversary list forked between paper-adversary
  and math-adversary instead of shared                        → DUPLICATE_RULE
full research_layout essay forked outside compliance §5c
  + lib-coda-librarian narrative home                             → DUPLICATE_RULE
a producer skill that marks its own work accepted, or any
  skill that mints authority / self-certifies                 → AUTHORITY_COLLISION
proof-ledger path drift (research/proof_ledger_* without
  encyclopedia/proof_ledgers/)                                → STALE_RULE
legacy dual claim-ledger names without §5c migration intent → STALE_RULE
prose tools rewrite dual_alias_registry / programme README /
  paper_map, or remap when old_id==path_qm_NNN (double-map)     → DANGEROUS_DRIFT
denser stubs left on dual-live roots without free-band re-id    → MISSING_PROPAGATION
compliance §0 firewall count ≠ wizard universal list length     → STALE_RULE
domain managers that touch Python without wizard #14 / PROD cite → MISSING_PROPAGATION
LLM YAML `nine_certificate_conditions_satisfied: true` treated as evidence
  without host Up-Lift auditor                                        → AUTHORITY_COLLISION
panepistimion-cs-ml-prof-symbol-games / omega-lggr-qmcoda missing 007
  mss_reconstruction_spine entry when QMCODA is in scope              → MISSING_PROPAGATION
programme folder without readme map after multi-artifact bloom        → MISSING_PROPAGATION
Paper 005 runtime + 020 auditor + MSS-N genesis compressed into one
  “operad/lift” claim across managers without stack-separation note     → DANGEROUS_DRIFT
council/procurator minutes treated as MSS lift / GlobalGreen            → AUTHORITY_COLLISION
all-host SKILL.md SHA mismatch after meta skill land (four hosts: .agents/.claude/.codex/.grok) → DANGEROUS_DRIFT
live skill prose still teaching five-host / `.gemini` as promotion root (removed 2026-08-05) → STALE_RULE
OPTIONAL_SPECIALIZED_DIAGNOSTICS upgraded to SpecializedLocal without
  Paper-040 product path + independent adversary                          → AUTHORITY_COLLISION
Symbol Game SPK-003 mech receipts (P1–P3) missing from 007 map after land → MISSING_PROPAGATION
HOST_CHECKED_PASS on Condition 5 / conservativity when only a syntactic
  vocabulary proxy ran (no theorem-level checker)                              → DANGEROUS_DRIFT
HOST_CHECKED_SYNTACTIC_VOCABULARY_PASS sold as full Condition 5 or MSS-1
  (or NINE_HOST_ALL_DECIDABLE_PASS while only syntactic)                       → AUTHORITY_COLLISION
SPK-006 host checker without adversarial regressions for intro-kind,
  ZeroRel-on-old-carrier, equality closure, omit-package paths                  → MISSING_PROPAGATION
GTLA term paper missing §5b primitives box or §5c claim_ledger/change_log      → MISSING_PROPAGATION
Abstract “proves” while body labels Conjecture / Status “not proved”             → DANGEROUS_DRIFT
Legacy `*_ledger.md` dual-live with `*_claim_ledger.md`                          → CLAIM_LEDGER_DRIFT
Paper claims ACCEPT without ENC ownership and no `/omega-math-dev` handoff       → MISSING_PROPAGATION
Mint ENC id from registry tail only (ignore on-disk enc-* max)                   → DANGEROUS_DRIFT
paper-repair packaging PASS sold as CODA_CHECK_PASSED / MECHANIZED / lake green     → AUTHORITY_COLLISION
Lean path-bound sold as LEAN_BUILD_GREEN when lakefile roots ≠ cited stems         → DANGEROUS_DRIFT
paper-repair review_request not exactly OPEN|IN_WORK|CLOSED or round gate skipped → MISSING_PROPAGATION
meta skill land without all-host package (e.g. auto-review-skills missing on .grok)    → DANGEROUS_DRIFT
skill host package-count lag (e.g. .grok 30 vs .agents 61) after mirror-all order        → DANGEROUS_DRIFT
DEFAULT_SKILLS-only sync sold as full all-host garden mirror                          → DANGEROUS_DRIFT
paper-repair pilot path `006_symbol_game_foundations.md` (missing) treated as live → STALE_RULE
P3 / SG monograph nested-only path when flat `007_the_symbol_game_monograph.md` lives → STALE_RULE
archive park of research/omega_sweeper sold as T4 product-rail delete/replace         → AUTHORITY_COLLISION
paper Date bump without claim_ledger Date alignment (DATE_MISMATCH left open)         → MISSING_PROPAGATION
SciSpace/v001 wrappers prompt used after v002 exists without fence note                 → STALE_RULE
SciSpace harvest abstracts sold as PROVED / MECHANIZED / GlobalGreen                    → AUTHORITY_COLLISION
SciSpace harvest PDF promoted into published/ without packaging+adversary               → DANGEROUS_DRIFT
untracked agent-artifacts `file_urls.md` sold as landed (CSVs already deleted)          → DANGEROUS_DRIFT
agent-artifacts nested search_*/ after ordered flatten-to-root `file_urls.md`           → STALE_RULE
literature search primary clauses Langlands/motives after out-of-scope refuse           → STALE_RULE
wizard spine_index nested-only paths after flat packaging without regen                 → STALE_RULE
archive omnibus re-labeled UNIFIED_MASTER_MONOGRAPH while REJECT AS CANONICAL          → SCOPE_PROMOTION / DANGEROUS_DRIFT
omnibus sold as bijection-closed unified claim ledger (vs NON_CLAIM_SURFACE)             → AUTHORITY_COLLISION / CLAIM_LEDGER_DRIFT
F3/P0 interface resolved PROVEN on thin extract without PL discharge receipts            → AUTHORITY_COLLISION
same-session producer+adversary ACCEPT sold as fireproof without second-agent I3         → AUTHORITY_COLLISION
soft I3 six-gate PASS without claim_id_bijection / red-team residual recompute           → DANGEROUS_DRIFT

```

Missing the contract reference is `MISSING_PROPAGATION`; a re-hosted authority/hygiene block is `DUPLICATE_RULE`; a self-certifying or authority-minting member is `AUTHORITY_COLLISION`.

---

### 9. Mechanism-surface and Genesis-Bias invariant (CODA / QM papers)

Papers and skills in the `coda-gtla-papers` / CODA estate must not **overclaim** or start arguments without declaring the replayable mechanism slots:

```text
Primitive Difference · Structure/carrier · ZeroRel · Observer/profile ·
Witness · Residual · Quotient/Q¹ · CompletionLaw (or N/A) · AuthorityEffect::None

```

Breaks:

```text
MISSING_PROPAGATION — paper lacks Mechanism inventory box (compliance §5b)
DANGEROUS_DRIFT     — claim uses residual/quotient language with no ZeroRel/carrier
SMUGGLE_HOST / SMUGGLE_OBSERVER / SMUGGLE_PRIMDIFF —
  detect via /governance-wdp (focused hunter;
  auto-symmetry-hunter routes, does not re-host the full lexicon)
AUTHORITY_COLLISION — packaging residual sold as GlobalGreen or authority mint

```

**Relation to governance-wdp:** that skill owns Primitive Difference honesty and no-view-from-nowhere scans. Symmetry-hunter owns **cross-artifact** agreement that the inventory slots and fences appear consistently across paper family skills, ledgers, and estate tools. Prefer **route + reference**, not duplicate the hunter checklist.

**Omega-as-algorithm posture (interpretive, non-authority):** the stack is steered toward a **replayable packet machine** (declared slots → solve/terminalize → residual) so operators can vary signs/laws and compare engines. That is a research posture, not a license to mint continuum QM or authority. LGGR + Q + CODA packaging serves that posture when slots are explicit and flipable.


## Cross-host packaging patterns (detail)

### 10. Skill packaging invariant

```text
frontmatter `name:` != directory name                        → DANGEROUS_DRIFT
  (registers a command unreachable at its own path; 12 live
   instances 2026-07-28 — auto-auto-*, lib-lib-*, one tripled,
   two truncated. Directory is authoritative.)
package present in some hosts but not all                    → DANGEROUS_DRIFT
  (a new skill mirrored to .claude only leaves .codex/.grok short)
`.antigravity/` tree created                                 → STALE_RULE
  (.agents/skills IS Antigravity — sync_cross_host_skills.py:5)
hardcoded `+nightly` / `+stable` in any skill                 → STALE_RULE
  (CLAUDE.md SAGA-26 S3: no channel is pinned; `-j 1` is the real rule)
count literal in a skill ("all 69 skills") vs disk            → STALE_RULE

```

Gate: `_shared/verify_skill_names.py` (blocking, in `checklists/pre_commit_checklist.md`). An
invariant that lives only in a skill's prose is not enforced — it is remembered, and
memory failed twelve times before a loop caught it.

### Non-Invariant Content & LLM Slop Screening (`RULE_NONINVARIANT_CONTENT_PROHIBITION_001`)

During audit sweeps across preprints, papers, council documents, and skill files:
1. **Screen for Non-Invariant Content & LLM Slop:**
   - Scan for misspellings, adverb soup, generic fluff words ('crucial', 'essential', 'delve', 'game-changing', 'testament'), and ungrounded hype verbs ('proves', 'guarantees', 'flawless', 'weaponized') per `[user_global]` claim discipline.
   - Detect any inconsistencies or non-invariant patterns that warrant new rule candidates for `rules.yaml`.
2. **Mandatory Blackrod Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`):**
   - Whenever non-invariant content, misspellings, LLM slop, or contract/symmetry inconsistencies are discovered, automatically log a formal investigation report under:
     `omega_engine/anomalon_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
   - Detail the defect context, affected file paths, root cause analysis, and proposed `rules.yaml` additions or workflow remediations.
