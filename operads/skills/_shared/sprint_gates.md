---
kind: law
authority_effect: None
status: live
owner: techne-council
---
# Shared Sprint Gates

Referenced by: techne-sprint-planning, techne-sprint-execution, techne-sprint-planning-review, techne-sprint-retrospective.
Single source of truth for gates duplicated across sprint skills.

---

## Pre-Invocation Check: Uncaptured Learnings (IAK-007)

**MANDATORY:** Before executing any sprint skill, scan for uncaptured GitHub web edits:

```bash
git log --oneline --since="7 days ago" --grep="Update.*SKILL.md" --all -- ".claude/skills/*/SKILL.md"

```

If results > 0:

```text
OUTPUT: "{count} uncaptured GitHub web edits detected in last 7 days."
SUGGEST: "Run /autoskill to process these learnings before proceeding."
DO NOT BLOCK: This is advisory, not a gate.

```

**Why:** GitHub web edits often contain learnings that bypass autoskill. This scan closes a gap where web edit capture rate was 0% (24 missed edits in 30 days).

**Source:** Sprint 214 auto-improve-autoskill analysis (IAK-007)

---

## Pre-Gate: Already Committed

Before starting any sprint phase, check if the sprint was already committed:

```bash
git log --oneline --grep="sprint-{NNN}" -- | head -5

```

If a `feat(sprint-{NNN}):` or `fix(sprint-{NNN}):` commit exists:

- Do NOT re-run the current phase
- If completion.md missing: write it from the commit contents
- If retrospective.md missing: write it from commit + sprint artifacts
- If both exist: sprint is fully closed

**Source:** Sprint 113-0 session -- full planning/review ran for already-committed sprint

---

## Required Sprint Documents

### Stage: Planning (techne-sprint-planning creates)

**Directories:**

- `0_planning_documents/`
- `1_issues/`

> **No-code / design-spike / cleanup exception (empty `0_planning_documents/`):** A no-code sprint that
> produces **no planning artifacts** in `0_planning_documents/` legitimately leaves that directory empty at
> review/execution time. This covers two cases: **(a)** deliverables routed *into* `0_planning_documents/`
> during execution (the directory is the **execution-output destination**); and **(b)** cleanup/documentation
> sprints whose deliverables are **external edits** (e.g. spine `.md`, gate-skill, or audit-doc changes) with
> witness artifacts recorded under `omega_engine_product_planning_office/plans/sprints/{NNN}/evidence/` -- *not* in `0_planning_documents/`. In both cases the
> empty-directory HARD BLOCK in the review/execution/retro pre-gates is satisfied by a **documented exception**
> in `review.md` that cites the plan's acceptance criteria. Do not silently bypass; record it.
> (Source: Sprint 107 -- Π♯ design spike; broadened in Sprint 107-0 to cover external-edit cleanup sprints.)
>
> **Canonical machine-readable marker (Sprint 108 STORY-108-005):** the pre-gates now honor the exception
> **programmatically**. A no-code/design-spike/cleanup sprint declares the literal token
> `0_PLANNING_DOCUMENTS_EMPTY_OK` in `quality_gates.md` (visible to the review pre-gate, which runs before
> `review.md` exists) and/or `review.md` (visible to the execution pre-gate). An empty `0_planning_documents/`
> **with** the marker passes with a NOTE; **without** it still HARD-BLOCKS. This replaces the prior
> comment-only pointer that required manual interpretation. (Wires Sprint 107-0 retro action item #1.)

**Files:**

- `backlog.md` (optional - ooutwire input)
- `kickoff.md`
- `quality_gates.md`
- `sprint_0NN_plan.md`

### Stage: Review (techne-sprint-planning-review creates)

**Files:**

- `review.md`

### Stage: Retrospective (techne-sprint-retrospective creates)

**Files:**

- `completion.md`
- `retrospective.md`

### Ticket Verification vs. Sprint Closure Invariant

- **Ticket Verification (Per-Story):** Execution and DevOps review cycle per story. Each completed story requires verifiable evidence recorded under `omega_engine_product_planning_office/plans/sprints/{NNN}/evidence/` (test report log, build output, or diff summary). Rule: **No path = No credit.**
- **Sprint Closure (Whole-Sprint):** Retrospective closes the sprint and emits `completion.md` only after **every committed story** has an explicit, recorded disposition:
  1. Delivered with verified evidence receipt, OR
  2. Formally designated as carryover with rationale, OR
  3. Formally recorded as a typed open residual (`OPEN_RESIDUAL`).
  A single ticket passing its verification gate does NOT close the sprint. Closure consumes the complete local CI receipt artifact.

---

## Cleanup Sprint Workflow (MANDATORY)

**CRITICAL:** Cleanup sprints (N-0 pattern) require the FULL sprint workflow.

Do NOT skip planning or review for cleanup sprints. The workflow is:

```text
/techne-sprint-planning {N}-0 → /techne-sprint-planning-review {N}-0 → /techne-sprint-execution {N}-0 → /techne-sprint-retrospective {N}-0

```

**Why:** Cleanup sprints address technical debt and retrospective action items.
They deserve the same rigor as primary sprints to ensure quality.

**Source:** Sprint 061-0 - explicit correction about secondary sprint workflow

### Cleanup-Chain Stopping Rule (MANDATORY)

Cleanup sprints can recurse (`104 → 104-0 → 104-0-0`). Each tier is individually
justifiable, but an unbounded chain is a smell. Apply this stopping rule to every
cleanup tier:

```text
IF a cleanup sprint's retrospective records ZERO new code/content defects
   (only logged policy decisions, confirmations, or "verified faithful" findings):
  DO NOT spawn the next tier (no N-0-0-0).
  Record the termination explicitly in retrospective.md:
    "Stopping rule: 0 defects found this tier; no Sprint {N}-...-0 created.
     Manufacturing a further cleanup tier for a logged decision is phantom churn."
ELSE (new actionable defects found):
  The next tier is justified -- but its plan MUST cite the specific defect rows,
  not a vague "finish cleanup".

```

**Why:** Without a stopping rule, each cleanup surfaces a slightly deeper layer and
spawns another, even when the deeper layer is a non-defect. The rule terminates the
chain at the first zero-defect tier.

**Source:** Sprint 104-0-0 retrospective:62-63 (chain `104 → 104-0 → 104-0-0`; "no
Sprint 104-0-0-0 is created... manufacturing a fourth cleanup tier for a logged
policy decision would be phantom churn").

---

## Crystallization Gate -- RETIRED

> **RETIRED (2026-06-19 sprint-system modernization).** The `CrystallizationWatchdog` engine
> does not exist; this gate was already marked REMOVED in `techne-sprint-planning-review` and `techne-sprint-execution`.
> Do not run it. It may return only if the engine is ever built.

---

## Omega Truth Assignment Gate -- RETIRED

> **RETIRED (2026-06-19 sprint-system modernization).** The `OmegaAssigner` engine does not exist;
> this gate was already marked REMOVED in `techne-sprint-planning-review` and `techne-sprint-execution`. Do not run it.
> It may return only if the engine is ever built.

---

## Pre-Execution Gate (MANDATORY)

No skills, code, or artifacts may be promoted without completing the sprint workflow:

1. `/techne-sprint-planning` → Creates plan, kickoff, quality_gates
2. `/techne-sprint-planning-review` → Gets approval from Product Owner
3. `/techne-sprint-execution` → Implements approved stories
4. `/techne-sprint-retrospective` → Captures learnings

**Violation Response:** HALT all commits, rollback uncommitted changes, complete proper workflow.

**Source:** Sprint 069 - skills copied before planning (Blackrod enforcement)

---

## Calibration Tooling (Commitment/Outcome) -- Documentation Sprints

The per-story Commitment/Outcome readiness check (techne-sprint-execution Step 6) is a **SOFT gate**. When the
DB-backed Commitment/Outcome tools (`submit_commitment` / `submit_outcome`) are unreachable in a
session, per-story tracking is skipped with a WARNING -- it is **never** a hard block.

> **Documented exception (no-code / documentation-only sprints):** A documentation- or process-only sprint
> that changes no executable code produces **no calibration data**, and this is **accepted, not a failure**.
> The tools' reachability is session/infra-dependent (DB connectivity), not fixable inside a no-code sprint,
> so the absence of Commitment/Outcome submissions for such a sprint must not be read as an incomplete
> sprint. Record the readiness result (reachable / unreachable) in `completion.md`'s Commitment/Outcome
> Tracking table and proceed.
> (Source: Sprint 107-0 STORY-107-0-004 -- settled the recurring "tools unavailable → no calibration data"
> warning; calibration MCP tools confirmed unreachable in a normal session.)

---

## Pre-Sprint Discovery Gate (HARD BLOCK at planning handoff)

**Purpose:** Stop the `N → N-0` cleanup-sprint spawn at its root. Every `-0` sprint
audited (101-0, 103-0, 104-0, 104-0-0, 107-0) traced back to verification work that
was *deferred from planning into execution/retrospective*. By the time the gap
surfaced, the sprint was closed, so the only place to put the work was a new `-0`.

**The binding principle (why prior "MANDATORY" discovery prose failed):** A prose
instruction to "run discovery" cannot detect that discovery was done by glancing.
This gate binds on a **witness artifact**, not on a promise. Discovery is "done" only
when the witness file exists and contains *pasted real evidence* -- never a placeholder.

### Witness artifact (required)

Planning MUST produce `omega_engine/omega_engine_product_planning_office/plans/sprints/{N}/0_planning_documents/discovery.md`. Handoff to
`/techne-sprint-planning-review` HARD-BLOCKS unless this file exists and every required row below
contains real evidence (no `TBD`, no empty cells, no "see above").

```markdown

# Sprint {N} Pre-Sprint Discovery Witness

## 1. Build/test baseline (paste real command tails -- NOT "passes")

**Capture it before the first edit.** A baseline is a measurement of the tree
you are about to change, so a run taken after any of the sprint's own files
exist is not one. A sprint recorded 73 Rust tests as its baseline from a run
that happened after its new test module was already declared in `lib.rs`; six of
the sprint's own tests were counted as pre-existing, and the "baseline
preserved" gate would then have passed on a number that included the work being
gated. The true figure was 67.

This fails in form-compliant sprints: the gate asks for a pasted tail and gets
one, and nothing in the paste says when it was taken. If a baseline must be
re-derived after work has started, subtract the sprint's own additions
explicitly and say so in the witness -- do not quietly restate the later number.

<!-- Rust sprints -->
$ cargo test -j 1 --no-run    → <paste tail: error count or "compiles clean">
$ git status --short          → <paste, then classify EACH entry below>

# If touching omega_contracts / anomalon_councils / authority crates, also paste

$ cargo test -j 1 -p omega_contracts -p anomalon_councils  → <v1 gate: loaded count + 0 findings>
<!-- Python sprints: pytest --collect-only / ruff check tails instead -->

## Working-tree classification (every uncommitted entry accounted for)

| Path | Disposable? | Depended-on by this sprint? | Disposition |
|------|-------------|-----------------------------|-------------|

## 2. Per-story discovery (one row per story -- no placeholders)

| Story | Discovery command run | Pasted result | Estimate impact |
|-------|-----------------------|---------------|-----------------|

## 3. Content-claim sampling (for ACs asserting SOURCE content)

| AC | Source file:line opened | Claimed element quoted from source? | Verdict |
|----|--------------------------|--------------------------------------|---------|

## 4. Correctness-AC plan (for merge/port/consolidate/"remove duplicates" ACs)

| AC | "Done" defined as | Dual-side evidence the story will produce |
|----|-------------------|-------------------------------------------|

```

### The four checks (each binds on pasted evidence)

1. **Real-command baseline, not a glance.** §1 must contain the *pasted tail* of the
   actual baseline command (`cargo test -j 1 --no-run`, or `pytest --collect-only` /
   `ruff check` for Python sprints) and a `git status --short` with **every** entry
   classified as disposable or sprint-dependency. An estimate set without this row is
   rejected. *(Source: Sprint 101-0 retrospective:26 -- a "3 broken tests / 5 pt" story
   was really 22 errors across 8 files; "pre-sprint discovery should run `cargo test
   --no-run` to get the actual error count". Sprint 104 retrospective:52-54 -- planning
   assumed 131 uncommitted changes were disposable; they were a dependency.)*

2. **Content-claim sampling.** For any AC asserting that SOURCE content exists
   ("harvest the ROI engine from doc X", "merge §7 of paper Y"), §3 must quote the
   claimed element from the opened source. File existence is NOT sufficient. *(Source:
   Sprint 104-0 retrospective:49-50 -- an AC said "merge ROI from monograph 036" but 036
   had no ROI engine; surfaced only at execution.)*

3. **Presence ≠ correctness.** A story whose AC is a *transformation* (merge, port,
   consolidate, dedup, "remove duplicates") may NOT be marked DONE on a presence check
   (grep for a header, file count). §4 must pre-declare the **dual-side quoted
   evidence** the story will produce (source-side and result-side, side by side). This
   is distinct from check 2: sampling verifies the source at plan time; this verifies
   the *result is faithful* at done time. *(Source: Sprint 104-0 retrospective:83-86 --
   9 merges were "presence-verified only"; semantic verification had to be spawned as
   Sprint 104-0-0.)*

4. **Audit before close, not after.** Any audit a sprint relies on (proof-obligation
   catalog, theorem merge, spine consistency) runs *during planning/execution as a
   blocking check*, and its findings land as in-sprint story rows -- not as
   retrospective action items deferred to `-0`. *(Source: Sprint 103 retrospective:35-39
   -- a doc audit found "7 proofs exist but catalog says OPEN" + an enum contradiction;
   5 findings were deferred to 103-0. Sprint 107 retrospective:40-42 -- a spike caught a
   roadmap overclaim post-hoc.)*

### Sprint-type scoping

Not every check applies to every sprint type. The witness file MUST state the sprint
type and mark non-applicable checks `N/A` **with a reason** (silent omission =
incomplete witness). Guidance:

| Sprint type | §1 baseline | §2 per-story | §3 content | §4 correctness |
|-------------|-------------|--------------|------------|----------------|
| Rust/code | required | required | if any content AC | if any transform AC |
| Python/code | required (pytest/ruff) | required | if any content AC | if any transform AC |
| Documentation / no-code | `git status` only | required | **required** | **required** |
| Design spike | `git status` only | required | if any content AC | N/A (reason) |

The empty-`0_planning_documents/` exception above does NOT exempt a sprint from the
discovery witness -- `discovery.md` is the witness even when other deliverables are
external. *(Source: Sprint 107 retrospective:55-59 -- gates must be sprint-type-aware.)*

**Enforcement point:** `sprint_planning.json` Step 5 quality gate carries
`discovery_witness_present` (required, `on_failure: return_to_step_4`). The
`techne-sprint-planning` skill Step 8 produces this artifact.

---

## Current-System Gates (2026-06 modernization)

> Added 2026-06-19 to align the sprint gate layer with the Rust-primary, governance + contracts +
> obstruction codebase. These **reuse existing Rust/CI machinery -- no new engines**. Scope is
> deliberately **scoped**: contract/governance gates HARD-block only sprints that touch those crates;
> other sprints attest. Source: `omega_engine/omega_engine_product_planning_office/plans/sprints/epic_omega_platform/sprint_system_modernization_plan.md`.

### Sprint-Type Classification (declared in `quality_gates.md`)

Every sprint declares `rust-code | python-code | ts-app | doc/no-code`. This selects which Pre-Merge
gate block in `quality_gates.md` is in force. Non-applicable gates are marked `N/A -- <reason>`
(silent omission = incomplete).

### Contracts Corpus Gate  [HARD -- scoped]

A sprint touching `omega_contracts`, `anomalon_councils`, `omega_operator_algebra`, or any crate
consuming contracts MUST run:

```bash
cargo test -j 1 -p omega_contracts -p anomalon_councils

```

and show the v1 corpus gate green (≥510 contracts loaded, zero findings). Reuses
`omega_contracts/tests/v1_corpus_gate.rs` (the same command `omega-contracts-ci.yml` runs).
A non-touching sprint records the attestation `[ ] No contract change` in `quality_gates.md`.

### Governance-Strict Gate  [HARD -- scoped]

A story that expands authority, mutates doctrine, relaxes a boundary, or promotes a residual MUST
attach a complete 10-field `GovernanceRecord` and pass
`omega_atlas_reconciliation::governance::check_governance_strict` (role-power separation -- Blackrod
cannot vote/waive, Woland cannot enforce; no self-cert). `PontiusPilate::judge` adjudicates the
contract↔code symbol binding at review. A non-authority sprint records `[ ] No authority change`
in `quality_gates.md`.

### Test-Tier Coverage  [HARD]

Every code story declares, and the exit gate verifies: (a) new modules have **unit** tests;
(b) cross-crate behavior has an **integration** test; (c) ≥1 **e2e** path runs
(`cargo test -j 1 --test '*_e2e'` for Rust; `pytest -m e2e` for Python). Enforced via the
`/techne-code-soviet-inspector` veto, extended to check tier presence. A behavior-adding story missing its
required tier is VETOed.

### Obstruction Diagnostics  [clippy HARD on touched crates; rest ADVISORY]

- **clippy (HARD):** `cargo clippy -j 1 -p <touched-or-new-crate> --all-targets -- -D warnings` → 0
  warnings. (Repo-wide `-D warnings` is a deferred burndown; the per-sprint gate enforces it on
  touched crates now.)
- **advisory diagnostics:** `python -m omega_engine_research_papers reconcile <stale|next>` under `governance-wdp` (code↔claim↔contract drift) on every code
  sprint; `/projection-obstruction` and `/epk-path-kernels` ONLY for stories touching composed-agent
  or projection logic. Findings record as PrimitiveDifference rows -- diagnostic-only; they never block
  by themselves and never authorize.

### Worktree Isolation  [HARD -- pre-execution]

Before execution: `git rev-parse --abbrev-ref HEAD` MUST match `sprint-{NNN}`; record
`git worktree list` in `kickoff.md`; never `git add -A` / `git add .` while other agents may be active
(stage named paths only). Turns the CLAUDE.md *Concurrent-Agent Isolation* prose into a checked gate
(closes the Sprint 121 shared-tree collision that merged a ~233k-line purge retro-less).

### DevOps Review  [HARD -- pre-retrospective]

`/techne-sprint-devops-review` runs after execution, before retrospective: CI green · clippy `-D warnings`
on touched crates · contracts gate (if touched) · no Python runtime path · `-j 1` discipline.
`BLOCKED@devops` is an honest terminal.
