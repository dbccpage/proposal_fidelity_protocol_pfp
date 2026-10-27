# Specialized Research and Compaction Procedure

**AuthorityEffect:** `None`.

This reference preserves the former WF_ADVERSARY research procedure for reviewing
specialized research missions and their history. The current `/adversary` default
is the shared `teamwork` backend described in the [workflow](../../../workflows/adversary.md).
Use `research` explicitly for the existing WF_RESEARCH_PFP controller, or
`run-live` explicitly for a configured paid native bout.

The retained procedure below is historical design context, not an additional
completion contract for ordinary IDE work. Current executable interfaces and
user scope decide applicable checks, budgets and transitions. In particular:

- Finite carriers, exact rational solvers and formal mission stages apply to the
  research claim that needs them; ordinary coding need not instantiate them.
- Synchronization copies selected packages and checks parity; it is not a
  distributed atomic transaction.
- Zero paid spend uses the IDE session. A zero financial ceiling does not promise
  an available free OpenRouter endpoint or bypass provider dispatch refusal.
- Persist current shared runs under `_ic/adversary/runs/` using the existing
  writer. Digestion and archival are distinct actions; neither is an automatic
  completion requirement or permission to delete sources.
- Use `/adversary-digests` for source-bound lessons and proposals. Antibodies remain
  candidates until the existing admission and executable binding permit use.
- Choose focused checks appropriate to the change and current user instructions;
  the old aggregate test example is not the default verification command.

## Retained Historical Procedure

# Adversary Autonomous Research, Frontier Coding & Compaction Workflow (WF_ADVERSARY)

**Entry points:** `/adversary`, `/adversary research` (`python -m adversary.entrypoints.cli research`)
**AuthorityEffect:** `None`
**Document ID:** `OE-WF-ADVERSARY-001` (supersedes `researcher.md`, `wf_long_horizon_frontier_coding.md`, and `wf_strategic_compaction.md`)
**Governing Locus:** `adversary`, `.agents/skills/adversary/SKILL.md`, `rules/swarms/rl_adversary_base_swarm_specialization.md`
**Host Controller:** `core_adversary::research_loop`, driven by `py -3.12 -m adversary.entrypoints.cli research`

---

## 1. Executive Overview & Fable-Compatible Control Law

This workflow defines the unified, bounded execution loop for **autonomous research missions**, **frontier software engineering tasks**, and **strategic context compactions**. It unifies the produce-freeze-evaluate-challenge-repair loop of the Proposal Fidelity Protocol (PFP) with the Adversary 22-character adversarial reality gate, strict railway-oriented programming (ROP) monads, and zero-loss artifact custody.

Every executing agent, producer prompt, and child swarm must observe these core control laws:

1. **Mission packet is law:** If an implementation choice is not constrained by the packet, select the smallest action that advances the Done Definition; do not invent unrequested scope or speculative theorems.
2. **When sufficient information exists, act:** Do not prompt for permission to read, test, implement, or refactor within declared owned paths.
3. **Parallelize only independent work:** Parallelize read-only analysis rings; never permit concurrent write collisions on shared pathsets.
4. **Pause only for declared critical boundaries:**
   - Destructive or shared repository operations (force-push, dropping state databases).
   - Secret provisioning or external API publication.
   - A typed refusal that cannot be repaired locally within the declared carrier.
   - Ambiguous requirements where only the human operator can decide intent.
5. **Grade verifiable artifacts and outcomes:** Terminals must be typed machine receipts (`Receipt`), test suite outputs, build logs, and Lean Lake status—never conversational self-assessment or model narrative.
6. **Receipt honesty:** Append and version execution receipts; record `PASS` only when underlying verification commands execute with exit code 0.
7. **No whole-suite test sweeps:** Never execute unbounded test sweeps (e.g. `pytest .`). Run targeted, individual test files (max 1–3 files sequentially) under `py -3.12`.
8. **Exact rational mathematics:** Zero floating-point rounding in cohomology and chain complex solvers; all calculations execute as exact rationals over $\mathbb{Q}$ using sovereign Rust crates under `engine/crates_rs/`.
9. **Clean Architecture inward dependency:** `domain/` must have zero dependencies on outer layers (`use_cases/`, `infrastructure/`, `controllers/`, `frontend/`).
10. **Multi-host parity:** Any change to workflows, skills, or rules in `.agents/` must replicate atomically to `.claude/`, `.codex/`, and `.grok/`.
11. **Claim hygiene discipline:** Un-scoped promotional or absolutist vocabulary is barred under the repository Claim Hygiene Rule. All summaries enforce the four-part evaluation envelope.

---

## 2. Standard Long-Horizon Mission Packet

Every research initiative or complex coding task must instantiate this standardized mission packet before execution commences:

```markdown
# MISSION PACKET: [INITIATIVE_NAME]
- **Mission ID:** [Stable identifier, e.g. ADVERSARY-RES-20261010-001]
- **Goal:** [One-sentence, measurable declaration of what must exist upon completion]
- **Mode:** [frontier | coding | research | deep_research | teamwork]
- **Target Swarm:** [AdversarySwarm via declared SwarmSpecializationV1]
- **Carrier Complex (K):** [Explicitly declared finite carrier, bounded context, or discrete complex K = (V, E, F)]
- **Observation Basis (B):** [Set of declared local observers, evaluation metrics, or test oracles]
- **Owned Paths:** [Explicit list of file/directory pathspecs authorized for mutation]
- **Forbidden Surfaces:** [Paths, databases, branches, or dependencies that must remain untouched]
- **Done Definition:**
  1. [Checkable condition 1: e.g. Interface implemented in owned path]
  2. [Checkable condition 2: e.g. Targeted unit tests passing locally under py -3.12]
  3. [Checkable condition 3: e.g. Negative controls / adversarial kill-tests passing]
  4. [Checkable condition 4: e.g. Four-host mirror parity verified across .agents, .claude, .codex, .grok]
- **Adversarial Kill-Tests / Falsifiers:**
  - [Kill test 1: boundary input or corrupted state that must fail closed with typed refusal]
  - [Kill test 2: local green condition that must be checked for masked global red via joint-kernel]
- **Receipt Sink:** [Path to write the immutable final execution receipt: e.g. _ic/nsa/receipts/<run_id>.json]
- **Budget Ceiling:** [Max rounds and max_cost_microusd: 0 for free-tier confinement]
- **Authority Effect:** None
```

---

## 3. PFP Stages and Execution Phases

The execution loop evaluates through 9 formal stages:

| Phase | PFP Stages | Owner | Exit Gate |
|:---|:---|:---|:---|
| **INGEST** | 1 | Host admission | Question, scope, required claims, capabilities and budget are fixed. |
| **CENSUS** | 2 | Read-only discovery | Sources and verifier routes resolved; missing inputs classified. |
| **PLAN** | 2 | Single producer | A finite task DAG with explicit done predicates. |
| **SNAPSHOT** | — | Host | Source and workspace digests recorded (`begin-round`). |
| **PRODUCE** | 2, 3, 4 | One producer | Candidate written; host freezes its bytes at stage 4. |
| **DELTA** | 5 | Host only | Bound checks run against the frozen candidate (`evaluate`). |
| **FALSIFY** | 6, 7 | Read-only critics | Adversarial cross-examination via Adversary panel (Defect Hunter, Gauge Breaker, Scope Guard, Anti Hype). |
| **ROUTE** | 8 | Model proposes, host decides | `route` returns the deterministic disposition. |
| **RECEIPT** | — | Host | Receipt bundle written; residuals offered to OEEIS / CDC as candidate antibodies. |

---

## 3.1 Panel Gate and Intergate Checks

Use the [operator CLI](../../../../adversary/documentation/live_cli.md) to prepare a typed exact-task packet and run its signed configuration through the existing native bout. The host rechecks the instruction signature, ordered body bytes, current sources, native binary, routing bytes, role allowlist, checker case and explicit cost/token ceilings before provider IO.

Use the [22-primary / 10-intergate / 3-empirical review map](../../../../adversary/documentation/panel_gate_integration.md) to declare applicability. Native transitions read `carrier_context.intergates`: each actual act edge selects a bounded list of `{intergate_id, payload, required}` rows. The ten existing diagnostic predicates execute in Rust; required BLOCKED or DIVERTED results stop traversal and retain a refusal bundle. Missing metrics cannot become PASS. Optional findings remain explicit diagnostics; neither diagnostic PASS nor persona agreement grants authorization.

The versioned `summary.json` embeds transition receipts and exact candidate artifacts inside the existing five-file bundle. Cemetery screening reads retained headstones before sandbox dispatch; farmed immune candidates remain inactive until the separate admission policy permits them. Use journal inspection for damaged/unfinished records and explicit reconciliation under the documented single-writer contract. Full primary/empirical YAML semantics, concurrent recovery and checkpoint resume remain separate research work.

---

## 4. Host Disposition Order

The host controller evaluates round outcomes in strict priority order:

1. `Refused`: Policy, authority or owned-boundary violation.
2. `InfrastructureFailure`: Transport or parser failure beyond the reserved attempts.
3. `BlockedByEvidence`: A required source or input is unavailable.
4. `NeedsExternalOracle`: A required semantic verifier is unbound or did not run.
5. `Verified`: Every done predicate has a fresh scoped PASS, both critics are accounted for, and no residual remains. `VerifiedWithResiduals` when only mission-declared optional claims remain. `StabilizedSurvivor` when the mission excludes semantic verification.
6. `OpenObstruction`: The same semantic residual persists for `max_stalled_rounds` rounds.
7. `BudgetExhausted`: The round or token limit is reached.
8. `InvalidateAndRecheck`: The candidate, source, or checker changed after review.
9. `RepairNextRound`: A confirmed repairable residual with budget remaining.
10. Otherwise `NeedsExternalOracle` when a done predicate lacks a PASS, else `OpenObstruction`.

`InvalidateAndRecheck` and `RepairNextRound` open another round; every other disposition terminates the run. Each maps onto `core_types::routing::RoutingTerminal`; the projection is recorded in `adapter_loss_ledger.jsonl`.

---

## 5. Non-Resettable Budget Confinement

1. **Single Ledger:** Exactly one host budget ledger per run.
2. **Worst-Case Reservation:** Every dispatch reserves its worst-case cost first; calls with unknown outcomes remain charged; failed attempts count.
3. **No Resets:** Rounds, retries, resumes, and prompt revisions never reset the budget.
4. **Zero-Spend Constraint:** `max_cost_microusd: 0` enforces paid dispatch is turned off; models operate via local execution or zero-cost free-tier endpoints.

---

## 6. Strategic Context Compaction Protocol

When a long-horizon session approaches context limits (>150k tokens), reaches a milestone boundary, or requires inter-agent handoff, the agent must perform strategic compaction:

```markdown
# Session Progress & State Summary

## 1. Active Goal & Scope
- **Objective:** <One-sentence summary of the active user request or overarching goal>
- **Active Sub-Goal:** <The specific component or phase currently being executed>

## 2. Verification & Completed Milestones
- <List of completed gates and green tests with exact test counts>
- <Files modified or created in this session>

## 3. Negative Findings & Rejected Hypotheses
*(Vital: records what failed or was disproven to prevent cyclic retry loops)*
- <Negative finding 1: what approach was attempted and why it failed>
- <Negative finding 2: boundary conditions or edge cases discovered>

## 4. Mandatory Claim Hygiene Envelope
1. **What it supports:** <Explicit, receipt-backed statements about what has been verified>
2. **What it does NOT support:** <Clear statement of limits; what has not been proven or generalized>
3. **Narrowest defensible claim:** <The most scoped, defensible claim possible from current evidence>
4. **Next test needed:** `<Exact executable shell command to verify the next step>`
5. **Exact git changeset shape:**
   - **Branch:** `<current branch>` (tracking `<upstream branch>`)
   - **HEAD Commit:** `<commit hash and title>`
   - **Working Tree State:** `<clean / list of modified files>`

## 5. Immediate Next Steps
1. `<Step 1: First action to take upon resumption>`
2. `<Step 2: Subsequent action>`
```

---

## 7. Run Output Custody & Post-Run Digestion

Every Adversary run must persist its immutable five-file bundle:
- **Location:** `_ic/adversary/runs/<run_id>/` (every `/adversary` and `/adversary-digests` run writes output directly to `_ic/adversary/` and nowhere else)
- **Bundle Contents:**
  1. `novella.md`: Complete human-readable narrative and bout transcript.
  2. `dda_actions.jsonl`: Cryptographically hash-chained sequence of discrete actions tagged with DDC alphabet (`E R C I Λ D M T`).
  3. `ddc.jsonl`: Byte-identical native copy of `dda_actions.jsonl`, bound separately in the receipt.
  4. `summary.json`: High-level metrics, round counts, and terminal disposition.
  5. `receipt.json`: Terminal cryptographic receipt binding the SHA-256 digests of the other four files.
- **Mandatory Digestion:** A run does not complete until intermediate outputs are digested via `python -m adversary.use_cases.intelligence_digestion.digestion_service`. Discovered defect witnesses are extracted into candidate antibodies in `_ic/cdc/antibodies/`, recorded in `pharmacy_catalog.json`, and sealed with typed transfer receipts.

---

## 8. Verification Commands

```bash
# Rust research-loop replay and hermetic pack tests
cargo test -j 1 -p core_adversary --test research_loop_replay --test research_pack

# Adversary research CLI pack validation
py -3.12 -m adversary.entrypoints.cli research check-pack

# Full Adversary 5-phase test suite
python -m pytest adversary/tests/test_panel_22_cast_totality.py adversary/tests/intergates/test_intergates_evaluator.py adversary/tests/test_fugu_autophagous_cemetery.py adversary/tests/test_fable_long_horizon_critique.py adversary/tests/test_compositional_open_games.py -v
```
