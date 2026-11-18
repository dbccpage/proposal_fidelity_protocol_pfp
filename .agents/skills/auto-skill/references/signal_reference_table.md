# Autoskill Signal Reference Table & Encoding Specs


## Table of Contents
- [Signal Priority Table](#signal-priority-table)
- [Signal Quality Filter](#signal-quality-filter)
- [Mapping Signals to Skills](#mapping-signals-to-skills)

## Signal Priority Table

_Restored 2026-08-04: this table was dropped from `SKILL.md` by `d9bb12ae74` and
existed in neither file for the interval since. Without it "Signal Detection"
referenced a table that was not anywhere._

| Priority | Signal Type | Trigger | Encode Key Fields |
| ---------- | ------------ | --------- | ------------------- |
| **HIGHEST** | `correction` | User says "no/don't/always/never/convention is" | quote, implied rule |
| **HIGHEST** | `passive_rejection` | User provides alternative, edits output, reverts | proposed vs actual, implied preference |
| **HIGH** | `tool_rejection` | User blocks tool call or says "don't do that" | tool, params, alternative |
| **HIGH** | `error_pattern` | BLOB/API/DB/migration/agent errors | error msg, root cause, fix, prevention |
| **HIGH** | `mcp_tool_error` | MCP tool returns error code | tool, error code, fix |
| **HIGH** | `rust_cargo_error` | `cargo check/build` fails | error code (E0276 etc), pattern, fix |
| **HIGH** | `build_ci_failure` | pytest/build/lint/CI fails | job, error, root cause, resolution |
| **HIGH** | `linter_formatter` | ruff/mypy/eslint errors | tool, rule code, fix |
| **HIGH** | `llm_hallucination` | Phantom API, syntax bleed, semantic error, false codebase claims | type, model, wrong pattern, correction |
| **HIGH** | `prompt_injection_attempt` | Fake authority framing, fabricated defects, urgency-driven code injection directives | framing technique, fabricated claim, actual state of code, response |
| **HIGH** | `structural_compliance` | Missing Rule 002 header (.py) or Rule 009 header (SKILL.md) | rule, file, missing fields |
| **HIGH** | `team_audit_findings` | RED/BLUE/GREEN audit produces systematic findings | team, finding type, remediation |
| **HIGH** | `agent_review_findings` | Subagent produces coded findings (PED-001, SEC-003) driving edits | agent type, finding IDs, resolutions |
| **HIGH** | `core_hunter_findings` | `/core-hunter` extracts lambdas, orders, or tears | scan ID, lambdas, orders, tears |
| **HIGH** | `hyper_meta_prompt_edit` | Files in `hyper_meta_prompts/` or agent capability matrices edited | file, change type, architectural decisions |
| **HIGH** | `research_insight` | Deep technical analysis produces reusable engineering conclusions | conclusion, evidence, target skill |
| **HIGH** | `security_audit_findings` | Systematic code audit produces panic/safety/security issues | audit scope, issue count, patterns found, remediation |
| **HIGH** | `scientific_fabrication` | False citations, circular logic, mislabeled inputs, hardcoded values claiming derivation | fabrication type, location, false claim, actual state, fix |
| **HIGH** | `pr_review_feedback` | Copilot/CI/security review drives fixes | reviewer, issue, resolution, pattern |
| **HIGH** | `dormant_engine` | Working code architecturally disconnected from pipeline | module, test status, missing wiring, pipeline gap |
| **HIGH** | `architectural_event` | Major structural refactoring, engine crystallization, namespace migration, skills pruning | event type, files affected, skill implications, before/after |
| **MEDIUM** | `rules_hunter_findings` | `/rules-hunter` registers new rules or fixes integrity | rules registered, skill implications |
| **MEDIUM** | `type_checking` | mypy strict mode errors | file:line, expected vs got, fix |
| **MEDIUM** | `security_scan` | bandit/pip-audit/npm audit findings | scanner, severity, finding, fix |
| **MEDIUM** | `db_constraint` | IntegrityError, FK/UNIQUE/CHECK violations | constraint type, table, fix |
| **MEDIUM** | `db_existence_check` | "database does not exist" | DB name, root cause, correct connection |
| **MEDIUM** | `agent_skill_invocation` | NOT_FOUND_AGENT, skill load failures | agent/skill name, error type, fix |
| **MEDIUM** | `workflow_gap` | Sprint approved but not executed, workflow stuck | workflow, stuck state, resolution |
| **MEDIUM** | `workflow_order_violation` | Implementation before planning, merge before tests | expected vs actual order |
| **MEDIUM** | `git_state_error` | Branch mismatch, staged to wrong branch | symptom, actual state, prevention |
| **MEDIUM** | `structural_compliance_regression` | Rule 002/003 compliance % dropped between sprints | before/after metrics |
| **MEDIUM** | `multi_agent_orchestration` | 3+ subagents spawned (Small: 3-5, Medium: 6-9, Large: 10+) | pattern name, agent types, assembly method, late-arrival handling |
| **MEDIUM** | `integration_point_spec` | Skill adds pipeline phase/gate documentation | skill, phases, dependencies |
| **LOW** | `debug_remnant` | console.log/print left in code | file:line, type, fix |
| **LOW** | `session_continuity_gap` | Context not loaded from previous session | what was missed, prevention |
| **LOW** | `compaction_state_loss` | Important context lost in compaction | what was lost, prevention |
| **LOW** | `manual_skill_edit` | SKILL.md changed without autoskill commit | file, change summary, missed signal |
| **LOW** | `canonical_cli_sync` | Files synced between engine/ and .claude/skills/ | direction, source/dest, verification |
| **LOW** | `cross_domain_replication` | 2+ domain expert agents get identical enhancements | agents, common enhancement, template candidate |
| **LOW** | `linter_enrichment` | Linter/hook modifies SKILL.md during session | file, fields enriched, source pattern |
| **MEDIUM** | `prompt_synthesis` | Session produces/modifies master_prompt or multi-round research directive | source files, patterns applied (diagnostic->execution, aspirational->verifiable), target prompt |

---

**Copilot trigger:** If commit message contains "Copilot"/"review suggestion"/"PR feedback" → suggest `/autoskill` before commit.
**Post-merge PR review scan:** After any `fix(pr-*)` commit, run `git log --oneline --since="1 day ago" --grep="fix(pr-"` and flag for autoskill if findings exist. Catches Copilot/CI-driven fixes that bypass the stop-hook because the session focuses on "fixing reviewer comments" rather than "learning from corrections."

### 2c. Signal-Specific Notes

**Corrections**: Phrases — "no use X", "we always", "don't do X", "convention is", "next time", "that's wrong", "standard practice".

**Research Insights** (IAK-008, added 2026-02-19): When a session includes deep technical analysis producing reusable conclusions (not corrections, not errors — original analysis). Examples: "SBE uses Shannon entropy, not quantum mechanics", "Rust can't express HKTs but CAN express affine logic", "LLMs recombine, don't discover", "System becomes the problem it's solving (self-referential architecture failure)", "Dormant engines pattern (working code architecturally disconnected)", "Inert immune system (antibodies exist but never administered)". Trigger: multi-turn technical discussion + ranked conclusions + reusable across sessions. **Batch generation trigger** (IAK-018, added 2026-05-22): When 10+ files are created following identical template structure with zero deviations, this validates the template itself as a research insight. Encode: template name, file count, structure validated, abstraction opportunity (generator/linter candidate).

**Security audit findings** (IAK-016, added 2026-03-24): Systematic code audits that discover panic-inducing patterns (unwrap/expect in production), division-by-zero, unsafe blocks without documentation, or embedded secrets. Distinct from one-off bug fixes — these are pattern-based findings across multiple modules. Trigger: 3+ instances of same security pattern, or comprehensive audit scan. Encode: audit scope (files/modules scanned), issue count by severity, patterns found (unwrap/division/unsafe/secrets), remediation methodology. Example: "7 production code panics found across lambda modules; fixed via Result types + documented invariants." Primary output: reusable audit patterns for testing skills.

**Published-estate renumber / research_layout** (autoskill 2026-07-24; path-aware follow-up; **flat dual-shape 2026-07-25**):

- **Renumber / dual-alias** → compliance §5a (freeze map; dual ENC aliases; full-map registry; protect stubs; never renumber `PL-*`).
- **Path-aware double-map ban** → skip prose remap when `old_id == path_qm_NNN`; never re-run old→new once destinations live; **never prose-rewrite** `dual_alias_registry.md` / programme `README` / `paper_map` (regen from YAML).
- **Denser stubs** → re-id off dual-live old roots to free band (`200+`); leave foundation path-only (e.g. `QM_000`).
- **Post-renumber health** → map↔registry, README spine vs `paper_map`, ENC dual presence, critical paths (e.g. Hilbert) vs `origin/main`.
- **Layout companions** → compliance §5c once; lib-coda-librarian narrative; stage skills **one-line cites only**; partial improver+rip only → `/auto-symmetry-hunter`.
- **Flat programme roots (2026-07-25):** live packaging places `{stem}.md` + claim_ledger + change_log at `published/{nnn}_*/` (park extras in `_support/`). §5c **dual-accepts** flat root **or** nested `{slug}/`. When filesystem layout changes, treat stale `estate_map` / nested-only gates as `STALE_RULE` + `architectural_event` (HIGH); patch contract once + librarian map — do not re-host layout essays. Claim-ID hygiene: `engine_py/tools/claim_id_bijection.py` (diagnostic; no OPEN→PROVED). Packaging honesty fences (GTLA hold, Q quarantine) stay fences. **G8 instance closed (PR #1568, 2026-07-29):** `core_pipelines/coda_librarian.py`'s `census_estate`/`iter_estate_papers` assumed nested `{layer}/paper.md` only (8 false-blocking, 0 papers found on the live flat estate) and its README primary-paper-ref scan flagged the estate's own `FLAT_ROOT_NON_PAPER_NAMES` control files as ambiguous paper refs — both are now dual-shape aware; the K-convention-table de-linking workaround in `001_coda/README.md` can be reverted.
- **Mid-session estate re-inventory (2026-07-26):** if the operator reports paths/folders moved, fused, or re-homed while a plan is in flight (e.g. “files in this folder are changed now”), **re-list the live directory before implementing** — do not execute against stale inventory from plan mode.
- **Firewall count** → wizard universal list length must match compliance §0 pointer (14 after Python≠Rust/Lean rule).
Encode as `architectural_event` + `research_insight`. Route multi-programme checklist → lib-coda-librarian; ENC dual regen → panepistimion-math-prof.

**Symbol Game / QMCODA genesis** (autoskill 2026-07-24; P1–P3 extended):

- **Live spine:** `008_engine_runtime/007_the_symbol_game/readme.md` → `mss_reconstruction_spine.md` + `mss0_genesis_contract.md`. Wire `/panepistimion-cs-ml-prof-symbol-games` + `/core-lggr-qmcoda` (no new authority). Session map: `qmcoda_session_progress_and_next10.md`.
- **Failed inverted-genesis trials** (mssn, prompt_no_0..2, seed-echo `llm_proposals.md`) → delete; do not restore without operator order.
- **LLM Up-Lift self-cert ban:** any `nine_certificate_conditions_satisfied: true` is **REFUSED** until host audit (`tools/up_lift_auditor.py`). Scrub corpora to `false` + host note when found.
- **SPK-004 triage:** KEEP / MAYBE / KILL for MSS-0 smuggle (host, manifold, preloaded cochain-as-object).
- **P1 code map:** mech_01 → `ExpressivityProblem`/`norm`/`phi1_landing`; mech_05 → `solve_cochain_obstruction_packet` finite fixtures; no product-manifold API.
- **Stack separation (2026-07-24 disposition):** Paper 005/022b = residual **runtime**; Paper 020 = extension-descent **auditor**; MSS-N = missing **genesis law**. Compose ≠ extend ≠ promote. Council minutes ≠ MSS lift. Prefer one worked F0 derivation before Rust/Lean ports. Encode as `research_insight` + `architectural_event` → lggr-qmcoda / foundations / symbol-game-manager / lib-coda-librarian.
- **Mech code map (SPK-003):** P1 mech_01 expressivity; mech_05 cochain specialized. P2 mech_02/04 → `solve_epk_gluing_packet` (`core_epk`). P3 mech_03 → `solve_replica_extensivity_packet` (ℓ¹ disjoint-union additivity). No product-manifold API.
- **Optional catalog diagnostics:** `OPTIONAL_SPECIALIZED_DIAGNOSTICS` (`epk_gluing`, `replica_extensivity`) are **DiagnosticOnly** — never upgrade to SpecializedLocal without a new Paper-040 product path + adversary.
- **041_witness / GTOC term hygiene (2026-07-25):** adversary REJECT class = missing §5b + abstract “proves” for Conjecture + bad claim-ledger name/links + missing Part-A min sections. Producer unit repair pack → primdiff pre-pass → re-adversary → `/core-math-dev` ENC extract (DEFINED/CONJECTURE; PL-041-4 dead-storage PROVED-PROSE packaging). Capture → paper-adversary, paper-improver, paper-proof-signoff, core-math-dev, auto-symmetry-hunter.
- **ENC id collision:** always max over filesystem enc-* files before minting new IDs (concurrent 1217 clash).
- **SPK-006 host-check false-green (2026-07-25):** a host status `HOST_CHECKED_PASS` that only ran a _syntactic proxy_ (token lists, direct equalities) for canonical Condition 5 is `pr_review_feedback` + `scientific_fabrication` (mislabeled gate). Correct status is `HOST_CHECKED_SYNTACTIC_VOCABULARY_PASS`; block `NINE_HOST_ALL_DECIDABLE_PASS` while only syntactic. Capture → `panepistimion-cs-ml-prof-symbol-games` + `core-lggr-qmcoda` + adversarial fixtures. Never re-promote proxy to Condition 5 without a theorem-level checker.

**Claim-prefix / paper-number mismatch** (autoskill 2026-07-24): residual packaging or ledger rows whose claim IDs do not match the owning paper (`QM-029-C*` on `QM_014`) are hygiene signals — encode as `scientific_fabrication` (mislabeled_input) or `structural_compliance` and route to paper-improver + claim-ID ownership (compliance §5a).

**Scientific fabrication** (IAK-017, added 2026-03-25): Computational physics/math code containing false derivation claims. Distinct from bugs (logic errors) or hallucinations (wrong facts) — these are deliberate or over-enthusiastic mislabelings of fitted/phenomenological values as "derived from first principles." Trigger: "0 free parameters" claims, perfect PDG agreement (<1%), scanning parameters then claiming "forced," false citations to non-existent derivations. Encode: fabrication type (false_citation | circular_logic | mislabeled_input | hardcoded_fit | false_parameter_claim), location (file:line), false claim (quoted), actual state (what code does), fix applied, generalizability. Example: "Paper 007 line 25 claimed 'ng=3 derived in execute_15-19' but those scripts don't contain this derivation; fixed by citing actual source (execute_00 subdivision)." Primary output: fabrication detection patterns for domain verification skills (physics, mathematics, etc.).

**Dormant engines** (IAK-010, added 2026-02-19): Code that passes its own unit tests but produces no effect because it's not wired into the execution path. Distinct from dead code (unused) — dormant code IS used, just not connected. Trigger: test-passing module with no callers in the pipeline. Example: `fermionic.rs` passes 10+ tests but sieve never calls `SignAccumulator`. Encode: module name, test count, missing wiring point, pipeline gap description.

**Prompt synthesis** (IAK-015, added 2026-02-19): When a session produces or modifies a master_prompt or multi-round research directive, capture the patterns applied: diagnostic questions becoming execution tasks, aspirational advice becoming mechanically verifiable, impossibility constraints (NP-hardness) added to prevent overclaiming, "find" directives graduating to "wire" directives. Trigger: master_prompt, hyper_meta_prompt, or research directive file created/modified. Distinct from `hyper_meta_prompt_edit` (which tracks edits to existing files, not the synthesis methodology).

**Linter enrichments** (IAK-012, added 2026-02-19): When a pre-commit hook or linter modifies a SKILL.md during a session, the modifications are signal sources. Track what was enriched and whether the enrichment reflects a pattern worth propagating to family members.

**OS or encoding mismatch:** Classify the semantic signal here, then load
[os_quirks.md](os_quirks.md) only if the failure is actually platform-specific.
Do not carry PowerShell, console-codepage, or quoting trivia in the hot signal
table.

**/god panel receipts (autoskill 2026-07-24):** When `/god` (or full panel governance) is active, status-only skill-panel receipts are a **HIGH** session signal (same severity as dirty shared main). Capture for `god` skill; do not treat thin stubs as EXECUTED.

**008 archive omnibus vs thin extract / F3 (autoskill 2026-07-26):** document classes live in compliance **§5d**. Capture signals: dual monograph+archive status; soft I3 ACCEPT oversoft vs bijection/red-team; F3 work on omnibus instead of thin extract; PROVEN for undischarged P0 interfaces; claim_id dual-cell / false-match PL IDs. Route → paper-adversary, paper-improver, rip-papers, paper-proof-signoff, auto-symmetry-hunter (cite §5d; do not re-host essay).

**OE Prime triad + dual-channel audit (autoskill 2026-07-26):** session crystallized (1) Prime **000/001/002** triad + Cat_Res/No-Smuggling in `algorithm-prime-000` + `008_residual_handoff_category` + permanence checklist `oe_prime_008_permanence_checklist.md`; (2) dual-channel high-accuracy LLM force: YAML `oe.prime_prompt_000.response.v1` + Symbol Game sparse lines + host `oe_prime_prompt_admit.py` (shape-only; `->` not close-bracket); (3) Hilbert quantize-Ω / complete-QM = **IMPORTED finite H_K only**, refuse continuum derivation (qm-manager / lggr-qmcoda fences). New thin skill `/oe-prime-prompt-000`. Encode as `research_insight` + `architectural_event` + `prompt_synthesis` → algorithm-prime-000, oe-prime-prompt-000, core-foundations-manager, core-qm-manager, core-lggr-qmcoda, panepistimion-cs-ml-prof-symbol-games, auto-symmetry-hunter.

**Paper-repair campaign / B/R/G (autoskill 2026-07-25; densified r1–r6; full topology landed):** Controlling process under `engine/research/_reviews/paper_repair/` (Workflows A–E + campaign charter). Teams: **Blue** propose · **Green** recompute on disk · **Red** refuse/gate. After each unit open `{blue,red,green}_review_request_{NNN}.md` with status **exactly** `OPEN`|`IN_WORK`|`CLOSED`; **no new round** until all prior-round requests are CLOSED (Red polices). Collaboration surface for this campaign: **`main` only** — pin both inspection HEAD and `origin/main`; if campaign tree is not on main, say so (do not fake main pin). Code replace of product rails (rip/sweeper/proofer crates/skills) **hard ban until T4**. **Archive park ≠ T4 replace:** `git mv research/core_sweeper{,_fast}` → `.official_archive/` is package-then-park, not product-rail deletion or T4 license. **Workflows A–E Topology:** Workflow A read-only audit (A0–A10); Workflow B paper repair (B0–B10); Workflow C math/Lean/ENC development (C0–C9); Workflow D publication closure & source-pure build (D0–D11; ends with `HUMAN_PROMOTION_GRANTED` as terminal external act); Workflow E estate campaign & pre-merge closure (E0–E13). **Actor-scoped result tokens:** `IMPROVER_CANDIDATE_READY`, `PRODUCER_MUTATION_COMPLETE`, `ADVERSARY_ACCEPTED_INTERNAL`, `LEAN_AUDIT_PASSED` (requires `LEAN_BUILD_GREEN` clean `lake build` + zero sorry when formal proof is claimed), `PROOF_SCOPE_APPROVED`, `RELEASE_PREFLIGHT_PASSED`, `BUILD_SUCCEEDED`, `AWAITING_HUMAN_PROMOTION`, `HUMAN_PROMOTION_GRANTED` (emitted ONLY from human event). **Librarian Non-Mutation Boundary:** `index-sync-operator` generates and atomically applies projections; Librarians (`lib-coda-librarian`, `lib-lean4-librarian`, `lib-encyclopedia-librarian`, `librarian-coordinator`) perform read-only audit/certification and **never** alter the projections they certify. **Prime-000:** footer inventory on A–E (may live in **campaign receipt** + paper primitives N/A); full 12-step develop **C-only**. **Lean triad:** path-bound ≠ build-green ≠ theorem-name; lake roots may differ from cited stems. Packaging (date/author/subtitle/references/claim-ID) ≠ PROVED / full CODA green; companion date bump is a first-class Option-A unit (clears `DATE_MISMATCH` REPAIRABLE — verify gate after). **Pilots:** P1 `001_coda/coda_foc.md`; P2 `008_engine_runtime/mss0_genesis_contract.md`; P3 **`008_engine_runtime/007_the_symbol_game_monograph.md`** (flat; **not** phantom `006_symbol_game_foundations.md`; nested `007_the_symbol_game/007_…` may be gone). MSS-0: cochain/Q1/ΦΓ default N/A native. Green emits `green_rN_receipt.md` then opens `green_review_request_*`. Encode as `architectural_event` + `team_audit_findings` → paper-improver/adversary (cite), algorithm-prime-000, lib-lean4-librarian, panepistimion-cs-ml-prof-symbol-games, github (main + explicit paths).

**SciSpace mathematical wrappers / literature harvest (autoskill 2026-07-25; agent-artifacts densified 2026-07-26):** Prompt home `engine/research/prompts/`. **v002 is live** (`scispace_mathematical_wrappers_prompt_v002.md`); v001 is historical. Usefulness audit: `scispace_mathematical_wrappers_usefulness_and_v002.md`. Harvest pattern: SciSpace CSV exports under `sci_space_results/{NNN}/` → dedupe → single `literature_harvest_index.md` + `literature_harvest_receipt.json` (`core.literature_receipt.v1`) → download **arXiv PDFs only** to `downloads/` (no paywall scrape). **Agent-artifacts flatten:** under `published/008_engine_runtime/agent-artifacts-zip_*/`, combine all CSVs into root `file_urls.md` (deduped Title/Year/URL/DOI/Source), delete CSVs **only after** the MD is staged on a feature-branch/worktree PR, flatten criteria to `search_*__*.criteria.json` at root, drop empty `.keep`/subdirs. **Untracked harvest loss (HIGH):** reporting done on an untracked `file_urls.md` while CSVs are already deleted loses the harvest when concurrent `git restore`/`clean` runs (user: I do not see the MD file). Recover source zip from Recycle Bin / original archive before rebuild. Abstracts untrusted. Harvest ≠ published promotion. Out-of-scope refuse (motives/Langlands). Capture → github, lib-literature-lookup, panepistimion-math-prof, auto-symmetry-hunter. **Library estate (2026-07-26):** `engine/research/library/_code/` is the host pipeline (all_urls → arXiv-first → DOI OA Unpaywall/OpenAlex/Zenodo → parse/thin/reindex; purge SciSpace). Cite here; do not re-host the tool table in every stage skill.

**Rust architectural patterns worth capturing:** Trait impls requiring bounds not in trait definition → standalone functions. `Box<dyn Fn>` with generics → add `'static` bounds. Recursive closures → `Fn + Clone` not `FnMut`.

**Structural compliance — Rule 002 header (Python):**

```python
"""
--- yaml
title: <slug>  file_name: <name>  file_location: <path>
status: <Goo|Mature|Crystallized>  invariance_level: <Tier 0-10>
logic_system: <system>  substrate: <Python|PyTorch|Git-Hook>
"""
```

Required fields: title, file_name, file_location, status, invariance_level, logic_system, substrate.

**Multi-agent scale thresholds:** Small (3-5): parallel-task. Medium (6-9): parallel-implementation. Large (10+): parallel-implementation-manifold (requires manifest, shared-file coordination).

**Known orchestration patterns:**

- "parallel-audit-then-synthesize" (N agents → `.intelligence/` JSON or markdown synthesis → unified report; supports late-arrival via amendment commits)
  - **Adversarial verify stage (refute-by-default)**: MANDATORY before any verdict licenses an irreversible act (delete, merge, publish, overwrite). Independently re-open and confirm every finding's cited `file:line`; review subagents fabricate locations (observed: a finding citing lines 867-988 in a 172-line file). Prompt refuters to default to `refuted=true` when uncertain — a wrong "safe" destroys work, a wrong "unsafe" costs one preserved file. Measured 2026-07-22 on a delete-safety audit: **13 of 26 STALE verdicts overturned (76% of those that ran)**; without the stage a worktree holding ~600 lines of unlanded architecture would have been deleted. Synthesis counts only verified findings.
  - **Judge the verdict SET, not each file**: individually-defensible per-file calls can be collectively wrong when the files are interdependent. Same audit: keeping the "unique" files while dropping the "stale" ones produced a set that does not compile. Ask "does this partition still cohere?" before acting on it.
  - **Always return raw per-item results alongside the synthesis**: the synthesis agent is a single point of failure. One died mid-run (org auth error) returning `null`; the run stayed fully usable only because the per-item array was also returned. The task notification's `<result>` truncates (~84K) — the full payload is under `.result` in the output file, NOT at top level, and `journal.jsonl` holds one line per agent.
- "parallel-implementation-manifold" (10 agents, tier-based roles, integration verification)
  - **Shared-file rule**: NO parallel writes to mod.rs or any shared registry; reconcile post-completion
  - **Renumber-on-collision**: Agents check disk before writing; assign fallback range in prompt
  - **Late-arrival handling**: Poll TaskOutput, reconcile after all agents complete
  - **Output directory specification**: ALWAYS include exact absolute path in each agent's prompt. Subagents default to `src/` instead of `crates/<name>/src/`. Verify output locations post-completion before reconciliation.
  - **Workspace convention transmission**: Include edition, resolver, and dependency versions in prompts — subagents cannot infer workspace settings.
- "parallel-research-then-synthesize" (two-phase: N Explore agents read/scan → M writing agents produce deliverables)
  - **Phase 1 (Research)**: Explore-type agents, read-only, each assigned distinct source scope
  - **Phase 2 (Writing)**: General-purpose agents consume research digests, produce deliverables to separate files
  - **Phase 3 (Red Team, optional)**: Thanatos agent adversarially reviews outputs
  - **Pre-create shared dirs**: Create output directories before dispatching agents to avoid mkdir race conditions
  - **Timeout escalation**: Explore agents need 120s+ initial timeout; writing agents need 300s+; double on retry
- "parallel-audit-synthesize-execute" (Three-phase: N Explore agents audit scope → synthesize migration plan → M general-purpose agents execute plan → optional K agents for follow-ups)
  - **Phase 1 (Audit)**: Explore agents read/scan partitioned file sets, produce structured findings
  - **Phase 2 (Synthesis)**: Main context synthesizes findings into executable migration plan
  - **Phase 3 (Execution)**: General-purpose agents execute plan in parallel, each assigned non-overlapping file sets
  - **Phase 4 (Follow-up, optional)**: Additional agents handle lower-priority items identified during audit
  - **Key constraint**: File set partitioning must ensure zero overlap between agents in same phase
  - **Scale**: Typically 5 agents per phase (Small-Medium per phase, Large total)
- "parallel-template-instantiation" (single-phase: N agents each receive identical template + unique parameters, produce independent files)
  - **Use case**: Batch creation of contracts, configs, or scaffolds from a common format
  - **Key property**: Zero inter-agent coordination needed — each agent's output is fully independent
  - **Shared-file rule**: N/A — no shared files by design; each agent writes to its own directory
  - **Exemplar provision**: Provide 1-2 existing exemplar files in each agent's prompt for format consistency
  - **Scale**: Typically 10-17 agents; batch in groups of 10 if > 10
  - **Pre-existing check**: Before dispatching, verify which outputs already exist to avoid redundant work
  - **Verification**: Post-completion 3-step check: (1) diff expected vs actual directories, (2) per-file existence, (3) min-size filter (>1KB detects empty/corrupt files). Replaces per-agent review.
  - **Abstraction trigger**: If pattern repeats 3+ times with same template, propose generator script
- "author-gate-firewall" (tool-less author agents over hash-echoed input bundles -> deterministic host validation -> adversarial gate agents via file claim/deliver protocol -> host-only terminal status; authors and gates must be different models)
  - **Schema-repair sub-pattern**: when a gate/author reply has a mechanical schema defect, dispatch a small agent to re-emit the identical content fixing ONLY the named field — judgment preserved, host never edits model output (3x successful, 2026-06-11 sweep run_002)

**Compaction state management for multi-agent sessions:** When context is compacted mid-session with active subagents, preserve agent IDs and mission statements in summary. Mark incomplete agents explicitly. On continuation, check for late-arriving agent outputs via TaskOutput before finalizing. Late arrivals integrate via Edit tool + amendment commit.

**Sprint-driven changes exception:** `feat(sprint-X):` commits are NOT manual bypasses. Exclude from manual edit tracking.

**Web edit detection:** `git log --grep="Update.*SKILL.md"` — scan at autoskill invocation AND sprint workflow entry.

**Ignore:** Context-specific one-offs (without "always"), ambiguous feedback, contradictory signals (ask for clarification).

## Signal Quality Filter

Before proposing any change, ask:

1. Was this correction repeated, or stated as a general rule?
2. Would this apply to future sessions, or just this task?
3. Is it specific enough to be actionable?
4. Is this **new information** I wouldn't already know?
5. **For computational physics/math:** Did I verify the value is COMPUTED vs FITTED?

Only propose changes that pass all checks.

### Conservative Bias Warning (Added 2026-03-25)

**For scientific computing code:**

- Don't dismiss computed values as "fitted" just because they match experiment
- If framework is correct, it SHOULD match experiment (confirmation, not fabrication)
- Check if value comes from `calculate_X()` (computed) vs `X = 0.118` (hardcoded)

**Example:**

- ❌ TOO CONSERVATIVE: "Y = 1/6 matches SM → must be fitted"
- ✅ CORRECT: "Y = 1/6 from phase_distribution(Z_3) → computed (verify function)"

### What Counts as "New Information"

**Worth capturing:**

- Project-specific conventions ("we use `cn()` not `clsx()` here")
- Custom component/utility locations ("buttons are in `@/components/ui`")
- Team preferences that differ from defaults ("we prefer explicit returns")
- Domain-specific terminology or patterns
- Non-obvious architectural decisions ("auth logic lives in middleware, not components")
- Integrations and API quirks specific to this stack

**NOT worth capturing (I already know this):**

- General best practices (DRY, separation of concerns)
- Language/framework conventions (React hooks rules, TypeScript basics)
- Common library usage (standard Tailwind classes, typical Next.js patterns)
- Universal security practices (input validation, SQL injection prevention)
- Standard accessibility guidelines

If I'd give the same advice to any project, it doesn't belong in a skill.

### Code-Generation Session Handling

When the session is dominated by batch code generation (e.g., lambda expansion,
module scaffolding) rather than interactive debugging or PR review:

- Primary signals shift from `correction` → `research_insight` and `structural_compliance`
- Weight template extraction and pattern codification over correction capture
- `research_insight` signals (reusable encoding patterns, architectural templates) are
  the highest-value output for these sessions
- Low correction count is expected, not a detection failure
- **Security audit sessions** count as code-generation type (systematic fixes, not interactive)
- For audits: focus on `security_audit_findings` + remediation methodology, not correction count

## Mapping Signals to Skills

Match each signal to the Skill that was active and relevant during the session:

- If the signal relates to a Skill that was used, update that Skill's `SKILL.md`
- If 3+ related signals don't fit any active Skill, propose a new Skill
- Ignore signals that don't map to any Skill used in the session

### Skill Families

**Registry — MEMBERSHIP IS NOT LISTED HERE.** `_shared/family_registry.md` is generated
from the skills' own sovereign headers by `_shared/regen_family_registry.py`. Run it, read
it, and take membership from it. This section holds only propagation *patterns*.

Membership used to be duplicated in a prose table here, and it drifted: it named
`systems-lang` and `git-ci`, **neither of which exists as a declared family**, plus four
skills absent from disk. On 2026-07-22 a rule was propagated into two files under a
`systems-lang FAMILY_PROPAGATION` label for a family that does not exist — duplicated text
with no registry backing. A second copy of membership is the defect; do not restore it.

When a correction applies to one skill, check if it applies to related skills:

| Family | Example Pattern |
|--------|-----------------|
| sprint-workflow | BLOB submission format |
| code-quality | Pre-commit checks, severity thresholds |
| database | PG 18 version, connection patterns |
| code-generation | Type hints, async patterns |
| github | Branch naming, commit format |
| meta | Self-reference, metrics, rule promotion |
| testing | Test seams, failure-path coverage |
| coda-gtla-papers | AuthorityEffect None; compliance §5a/§5b/§5c by **reference** (not copy); escalate auto-symmetry-hunter on partial pipeline updates |

### Family Propagation Detection (ENHANCED)

When proposing a skill update, execute this algorithm:

```text
1. IDENTIFY source skill from correction
2. LOOKUP families containing source skill (may be multiple)
3. FOR each matching family:            # phantoms already flagged by Pre-Analysis 2c
   b. GET propagation patterns from the family table above
   c. CHECK if correction matches any pattern
   d. IF match:
      - GET all family members (excluding phantoms)
      - EXCLUDE source skill
      - CHECK: Are 2+ family members also updated in same session?
      e. IF yes → CLASSIFY as "coordinated family update" (HIGH confidence)
      f. IF no → GENERATE proposal for each target skill (standard propagation)
4. FORMAT proposals as FAMILY_PROPAGATION type:
```

**Enhanced Session-Level Family Propagation Detection:**

When same pattern/correction is applied to 2+ related skills **in same session**:

1. **Detection trigger:**
   - Skill update targets skill in established family (sprint-workflow, education, code-quality, database, etc.)
   - Same conceptual change appears in 2+ family members
   - Changes occur within same session (within ~2 hours)
   - Evidence: Identical phase names, architectural decisions, or documentation patterns across skills

2. **Encode as:**

```text
Family propagation: [family name]
Pattern type: [coordinated_update | independent_corrections]
Affected skills: [list - sorted by update order]
Common pattern: [what was changed consistently across skills]
Coordination evidence: [why this is clearly intentional propagation]
Scope: [partial family update | full family alignment]
```

3. **Confidence boost:**
   - If 2+ family members updated with identical/parallel changes: upgrade confidence to HIGH
   - If pattern appears in 3+ members: automatic HIGH confidence
   - Coordinated updates indicate architectural decision, not coincidental corrections

**Example from current session:**

```text
Family propagation: education
Pattern type: coordinated_update
Affected skills: [lib-pedagogy-improvement, lib-education-engine, lib-verification-loop]
Common pattern: Domain expert quality gating at specific pipeline phases
Coordination evidence:
  - lib-pedagogy-improvement added Phase 3.5 (domain expert gate)
  - lib-education-engine added Phase 3.5 (same name, same position)
  - lib-verification-loop added Phase 7 (domain expert verification, coordinated pattern)
  - All three reference same domain-expert-gate system
Scope: full family alignment
Confidence: HIGH (3 coordinated updates = architectural decision)
```
