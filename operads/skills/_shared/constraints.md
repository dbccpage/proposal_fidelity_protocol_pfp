# Skill Constraints Catalog

Reusable constraints that skills can reference by ID. This enables:

- Consistent constraint language across skills
- Easier constraint analysis
- Reduced duplication

## How to Use

In your SKILL.md, reference constraints:

```markdown

## Constraints

Required: APPROVAL_REQUIRED, NO_DELETE, PRESERVE_STRUCTURE
Optional: ADDITIVE_CHANGES

``` ext

Or for full constraint text, include this file.

---

## Core Constraints

### APPROVAL_REQUIRED

**Text**: Wait for explicit user approval before making any changes.
**Applies to**: Skills that edit files, make commits, or modify system state.

### NO_DELETE

**Text**: Never delete existing content without explicit instruction.
**Applies to**: Refactoring skills, autoskill, any skill that modifies files.

### PRESERVE_STRUCTURE

**Text**: Preserve existing file structure and formatting tone.
**Applies to**: Skills that edit existing files.

### ADDITIVE_CHANGES

**Text**: Prefer additive changes over rewrites. One concept per change for easy revert.
**Applies to**: autoskill, any skill that proposes modifications.

---

## Analysis Constraints

### EVIDENCE_BASED

**Text**: All proposals must cite specific evidence (files, patterns, metrics).
**Applies to**: Meta-skills, review skills, analysis skills.

### MIN_SPECIMENS

**Text**: Never propose abstractions from fewer than 3 specimens.
**Applies to**: auto-symmetry-hunter, pattern detection skills.

### PRESERVE_VARIATION

**Text**: Not all differences are accidents. Preserve meaningful domain-specific variations.
**Applies to**: auto-symmetry-hunter, refactoring skills.

---

## Meta-Skill Constraints

### SELF_REFERENCE

**Text**: Always check if findings apply to the skill itself. Include self-modification proposals when applicable.
**Applies to**: All meta-skills (autoskill, auto-improve-autoskill, auto-symmetry-hunter).

### ROI_FOCUSED

**Text**: Abstractions must reduce total complexity, not just move it. Estimate ROI before proposing.
**Applies to**: auto-symmetry-hunter, abstraction proposals.

---

## Code Modification Constraints

### NO_HARDCODED_SECRETS

**Text**: Never commit secrets, tokens, passwords, or API keys.
**Applies to**: All skills that write code.

### MAINTAIN_TESTS

**Text**: When modifying code, ensure tests still pass. Add tests for new functionality.
**Applies to**: debug, refactor, any implementation skill.

### PATHSPEC_STAGING_ONLY

**Text**: Stage by explicit pathspec (`git add -- <files>`) and never by sweep.
`git add .`, `git add -A`, `git add --all`, and `git commit -a` are forbidden
unconditionally, as is any commit or PR described as "sync all local changes"
or "filesystem sync". A sweep stages whatever the working tree happens to hold
— other agents' in-flight work, private files, build output, sibling worktrees
— and produces a diff nobody chose and therefore nobody reviewed. If you cannot
enumerate the paths, stop and inspect; do not widen the pathspec.
**Check**: `git diff --cached --name-only | cut -d/ -f1 | sort | uniq -c` — an
unexpected top-level directory is a stop signal.
**Applies to**: Every skill that commits, including autonomous landing flows.

### RENAME_IS_REPOINT

**Text**: A rename is a repoint, never a re-create. After renaming a module or
crate, redirect every import; never leave the old tree beside the new one. A
crate `X` may not coexist with `X_theory`, and no two modules under
`omega_engine/crates` may share a normalized body. Every mathematics crate
carries the `_theory` suffix; a bare-named math crate is the stale copy.
**Gate**: `python omega_engine_operations/domain/module_shadow_scan.py --repo-root .`
**Applies to**: Any skill that renames, moves, or prefixes modules.

### IDENTIFIER_SAFE_MODULE_NAMES

**Text**: Every module and package name must be a valid Python identifier and
must not be a reserved keyword. Renaming a package onto `lambda`, `class`,
`import`, `for`, `None` — or giving a module a stem containing a dot, space, or
hyphen — makes it unimportable *by construction*: `from pkg.lambda.x import y`
is a `SyntaxError` the parser raises before any import resolves, so no import
repair can reach it. Check the name with `str.isidentifier()` and
`keyword.iskeyword()` before renaming, not after.
**Gate**: `python omega_engine_operations/domain/module_shadow_scan.py --repo-root .`
(`NON_IDENTIFIER_MODULE`)
**Applies to**: Any skill that renames, moves, or prefixes modules or packages.

### SYNTAX_GATES_USE_COMPILE

**Text**: Validate Python syntax with `compile(source, path, "exec")`, never
with `ast.parse` alone. `ast.parse` compiles under `PyCF_ONLY_AST`, which skips
checks the import machinery still enforces — most notably future-statement
placement. A gate built on `ast.parse` will certify a file CLEAN that Python
outright refuses to import. Where the AST is needed for analysis, parse *and*
compile.
**Applies to**: import_boundary, tautology_scan, any syntax or contract gate.

### MIRROR_BEFORE_COMMIT

**Text**: A skill-garden edit is incomplete until it exists identically on all
four hosts. Edit canon in `.agents/skills/`, run
`sync_cross_host_skills.py`, then stage canon and mirrors in the same commit.
Never commit a canon edit alone: the next parity check inherits the drift, and
the host that reads the stale copy behaves differently from the one that reads
canon.
**Check**: `python omega_engine_operations/use_cases/sync_cross_host_skills.py --check`
**Applies to**: Every skill that writes under `.agents/skills/`.

### VERIFY_PEER_CLAIMS

**Text**: Measure another agent's factual claims against the current refs
before acting on them. A handoff note describes the state when it was written,
not the state now — an overlap count, a file census, or a merge-order
constraint can be stale by the time it is read. Re-derive the number; then act.
**Applies to**: Skills that consume handoff receipts, merge-order notes, or
peer review reports.

### VERIFY_IMPORT_PROVIDER

**Text**: When repairing an import after a rename, verify the module is the
*intended provider*, not merely that the symbol resolves there. Two modules may
define the same name; an import that loads is not evidence it is correct.
**Applies to**: Skills that repair imports, enforce prefixes, or migrate call sites.

### GUARD_MUST_OBSERVE

**Text**: A guard computes its verdict from the thing it guards. Removing a
subject from an admitted roster changes its *admission*, never its
*observation*: keep probing, and report `exists` as measured. A hardcoded
verdict is a check that cannot fail, which is the shape `tautology_scan.py`
exists to catch.
**Applies to**: Census, parity, roster, and conformance checkers.

### SECURITY_FIRST

**Text**: Review security implications before making changes. Do not introduce OWASP vulnerabilities.
**Applies to**: All code-modifying skills.

---

## Git Constraints

### NO_FORCE_PUSH

**Text**: Never force push to main/master. Warn user if requested.
**Applies to**: commit, github.

### DESCRIPTIVE_COMMITS

**Text**: Commit messages must describe the "why", not just the "what".
**Applies to**: commit.

### NO_AMEND_PUSHED

**Text**: Never amend commits that have been pushed to remote.
**Applies to**: commit.

---

## Sprint Constraints

### QUALITY_GATES

**Text**: All quality gates must pass before story/sprint completion. Blockers must be escalated immediately.
**Applies to**: Sprint workflow skills, any skill that enforces completion criteria.

### EVIDENCE_PATH_REQUIRED

**Text**: All approvals and decisions must cite specific file/line evidence. No approval without traceable provenance.
**Applies to**: sprint-review, any skill that grants approval or sign-off.

---

## Database Constraints

### PG18_ONLY

**Text**: PostgreSQL 18+ required. No backwards compatibility with older PostgreSQL versions. Use PG18-specific features freely.
**Applies to**: database-config, alembic-migration, any database skill.

---

## Git & Branch Constraints

### BRANCH_ISOLATION

**Text**: All operations must occur on isolated feature branches, never direct-to-main. Create branch before editing.
**Applies to**: github, commit, any skill that modifies tracked files.

---

## Execution Mode Constraints

### READ_ONLY_DEFAULT

**Text**: Default mode is observation and analysis. Write operations require explicit user escalation or approval.
**Applies to**: cartographer, explore agents, any skill that may modify files.

### PARALLEL_EXECUTION

**Text**: Subagents may run concurrently with no sequential dependency. Design for parallelism.
**Applies to**: gym, orchestrator skills, any skill spawning multiple agents.

### AGGREGATE_RESULTS

**Text**: Combine outputs from multiple subagents into a unified report. No fragmented output.
**Applies to**: gym, green, any skill that orchestrates multiple agents.

---

## Integrity Constraints

### NO_GREEN_THEATER

**Text**: Do not simulate passing tests or fabricate success metrics. All green must be earned.
**Applies to**: gym, run-tests, any skill that reports test results.

### ZERO_HALLUCINATION

**Text**: Every claim must have a traceable causal path. No assertions without evidence.
**Applies to**: omega-hunter, aletheia, any truth-verification skill.

### ROOT_CAUSE_FIRST

**Text**: Identify and document root cause before proposing any fix. No symptomatic patches.
**Applies to**: systematic-debugging, debug, any diagnostic skill.

---

## Categorical Constraints

### CATEGORY_THEORETIC

**Text**: All reasoning must map to categorical constructs (functors, natural transformations, adjunctions).
**Applies to**: omega-hunter, rules-hunter, any skill operating at Tier 9+.

### RULIAD_AWARE

**Text**: Operate at the limit of computational possibility space. Consider all reachable states.
**Applies to**: omega-hunter, theoretical analysis skills.

### DIAMOND_HARDNESS

**Text**: Output must meet Tier 0 verification standards (Diamond Hardness 8-10).
**Applies to**: omega-hunter, green, any skill producing crystallized artifacts.

---

## Testing Constraints

### NO_WEAK_ASSERTIONS

**Text**: Tests must make strong, falsifiable claims. No `assert True` or tautological checks.
**Applies to**: write-unit-tests, run-tests, any skill that writes or reviews tests.

### DETERMINISTIC_TESTS

**Text**: Tests must produce identical results on every run. No flaky tests, no random seeds without control.
**Applies to**: write-unit-tests, e2e-runner, any testing skill.

---

## Hard Anomalon Gates

### RULE_PRIME_0_0

**Text**: All actions must preserve system integrity and safety. No override without authorized council witness.
**Applies to**: All skills. Mandatory base constraint.

### NO_SELF_CERTIFICATION

**Text**: A skill, agent, module, test, or governance component may not certify its own correctness, promotion, or completion.
**Applies to**: governance, meta-skills, sprint workflow, audit skills, oracle/certification systems.

### NO_MOCK_ONLY_SAFETY

**Text**: Mocks may scaffold tests but may not certify external trust, cryptographic soundness, safety, or oracle independence.
**Applies to**: testing, governance, oracle systems, security, AI-safety.

### DIAGNOSTICS_ARE_NOT_PROOF

**Text**: Diagnostics may observe and report but may not be promoted to proof or policy without license and external validation.
**Applies to**: diagnostics, quantum observables, model checks, audit systems.

### NO_FAKE_DONE

**Text**: Completion claims require passing evidence paths; partial scaffolding must be labeled partial or quarantined.
**Applies to**: sprint workflow, code-review, run-tests, Blackrod, VP Engineering.

### licenseS_GATE_PROMOTION

**Text**: Claims may not be promoted in strength or policy effect without the required license and evidence.
**Applies to**: MSS-N, AutoP, diagnostics, proof/audit skills, operator governance.

### NO_WEAK_RUST_VERIFICATION

**Text**: Rust verification must use explicit result matching or matches! patterns. No implicit panic-masking in tests.
**Applies to**: systems-lang, testing, mss_n.

### FIXTURE_UNWRAP_ALLOWED

**Text**: .unwrap() and .expect() are allowed only for test fixture preparation, never for final verification.
**Applies to**: systems-lang, testing.

### EXTERNAL_ORACLE_REQUIRED

**Text**: High-integrity mutations require at least one independent external oracle witness.
**Applies to**: governance, mss_n, oracle systems.

---

## Change Management Constraints

### COMPRESSIVE_CHANGES

**Text**: Prefer reducing token count and complexity over adding new content. Compress, don't expand.
**Applies to**: autoskill, auto-improve-autoskill, any skill that modifies skills or documentation.

---

## Constraint Combinations

Common constraint sets for skill types:

### File-Editing Skills

``` ext
APPROVAL_REQUIRED, NO_DELETE, PRESERVE_STRUCTURE, ADDITIVE_CHANGES

``` ext

### Meta-Skills

``` ext
APPROVAL_REQUIRED, EVIDENCE_BASED, SELF_REFERENCE, ROI_FOCUSED

``` ext

### Code Implementation Skills

``` ext
NO_HARDCODED_SECRETS, MAINTAIN_TESTS, SECURITY_FIRST

``` ext

### Git Skills

``` ext
NO_FORCE_PUSH, DESCRIPTIVE_COMMITS, NO_AMEND_PUSHED, BRANCH_ISOLATION

``` ext

### Database Skills

``` ext
PG18_ONLY, APPROVAL_REQUIRED, NO_DELETE

``` ext

### Testing Skills

``` ext
MAINTAIN_TESTS, NO_WEAK_ASSERTIONS, DETERMINISTIC_TESTS, NO_GREEN_THEATER

``` ext

### Orchestration Skills

``` ext
PARALLEL_EXECUTION, AGGREGATE_RESULTS, APPROVAL_REQUIRED

``` ext

### Categorical/Omega Skills

``` ext
CATEGORY_THEORETIC, RULIAD_AWARE, ZERO_HALLUCINATION, DIAMOND_HARDNESS

``` ext

### Debugging Skills

``` ext
ROOT_CAUSE_FIRST, EVIDENCE_BASED, MAINTAIN_TESTS

``` ext

### Retinue Character Skills

``` ext
(None required - execution-only wrappers that invoke woland_cli)

``` ext

---

## Path Conventions

### CANONICAL_PATHS

**Text**: Sprint artifacts live under `coda_project_planning/sprints/{NNN}/`. Agent definitions live under `.agents/agents/`. Skills live under `.agents/skills/`. The `sdlc/`, `.anomalon/`, `.claude/`, and `omega_engine/docs/sprints/` directories are deprecated.
**Applies to**: All sprint-workflow skills, any skill referencing filesystem paths.

**Source:** Sprint 112 path update. Updated 2026-08-05 to reflect `.agents/` and `coda_project_planning/sprints/` canonical locations.

---

## Constraint Status

Constraints may have a status field:

- **Active**: In use by 1+ skills (default, no annotation needed)
- **Low usage**: Defined but referenced by 0-1 skills. Review for deprecation.
- **Deprecated**: Scheduled for removal. Migration path documented.

---

## Adding New Constraints

When adding a constraint:

1. Give it a SCREAMING_CASE ID
2. Provide one-sentence **Text**
3. List which skill types it **Applies to**
4. Add to appropriate section
5. Update relevant constraint combinations

## Constraint Usage Tracking

To track which skills use which constraints:

```bash
grep -r "APPROVAL_REQUIRED\|NO_DELETE\|PRESERVE_STRUCTURE" .claude/skills/*/SKILL.md

``` ext

This helps identify:

- Underutilized constraints
- Skills missing important constraints
- Patterns in constraint usage
