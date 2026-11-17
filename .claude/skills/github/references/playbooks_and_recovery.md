# Git & GitHub Playbooks, Conflicts, and Recovery Protocols

- **VETO (exit code 1)**: BLOCK commit, fix issues first
- **PASS (exit code 0)**: Proceed with commit

1. **Frontend changes**: If React code was modified, run `npm run test:react:run` or add E2E tests
2. **Skill changes**: If host skill trees are staged (`.claude/skills/`, `.codex/skills/`, `.agents/skills/`), suggest `/autoskill` first
   - Skills should evolve through the learning loop, not direct edits
   - Exception: Sprint-driven changes via formal sprint process
   - **Cross-host skill identity (mandatory for new/changed skills):** author under `.claude/skills/<name>/`, then mirror:
     `python scripts/sync_cross_host_skills.py --skills <name>`
     Targets: `.claude/skills`, `.codex/skills`, `.agents/skills` (Antigravity). Verify with `--check`. Runtime code lives in `engine_py/` (not triplicated under hosts; not Rust PROD via `.agents`).
3. **Retrospective Gate (HARD BLOCK for sprint commits)**:
   - If the commit message contains `sprint-{NNN}` and there's a sprint directory `engine/research/product_planning_office/plans/sprints/{NNN}/`:
     - Check that `retrospective.md` exists in that sprint directory
     - If missing: **BLOCK commit** with message: "BLOCKED: retrospective.md missing for sprint-{NNN}. Complete retrospective before committing."
     - Bypass: `--skip-retro-gate` flag (emergency use only, must document reason)
   - Non-sprint commits (no sprint reference) are not affected
4. **Branch-Sprint Matching (SOFT WARNING for sprint commits)**:
   - If on branch `sprint-{NNN}` and commit message references a different sprint:
     - **WARN**: "Branch sprint-{NNN} does not match commit sprint reference {MMM}. Continue? [y/n]"
     - Requires explicit confirmation to proceed
   - If on a non-sprint branch (feature/, fix/, etc.): no check needed

## Techne Code Inspector Gate (BLOCKING)

```python

# Gate Logic - Before ANY commit with test files
staged_test_files = get_staged_files_matching("tests/*.py")

if staged_test_files:
    result = run_test_quality_inspector(staged_test_files)

    if result.exit_code == 1:  # VETO
        OUTPUT: "COMMIT BLOCKED by Techne Code Inspector"
        OUTPUT: result.violations
        STOP: "Fix test quality issues before committing"
        # DO NOT create commit

    elif result.exit_code == 0:  # PASS
        OUTPUT: "Techne Code Inspector: PASS"
        PROCEED: "Create commit"
else:
    # No test files staged - proceed normally
    PROCEED: "Create commit"

``` ext

**Source:** Sprint Workflow Quality Enforcement (Techne Code Inspector Model)

### Autoskill Check for Skill Changes

``` ext
IF staged_files match ".claude/skills/**" OR ".codex/skills/**" OR ".agents/skills/**":
  IF session_has_autoskill_run == false:
    PROMPT: "Skill files modified. Run /autoskill to capture learnings? [y/n/skip]"
  IF skill package content changed:
    RUN: python scripts/sync_cross_host_skills.py --skills <name>
    VERIFY: python scripts/sync_cross_host_skills.py --check --skills <name>

``` ext

**Source:** Sprint 058 auto-improve-autoskill analysis (17% manual edit capture rate); session 2026-07-24 cross-host identity

### Staging Changes

```bash

# Stage specific explicitly named files only (never git add . or git add -A, never target/**)
git add -- <explicit-files>

# Stage hunks selectively
git add -p <file>  # Use with caution

# AVOID interactive staging (requires input)

# git add -i  # DO NOT USE

``` ext

### Commit Message Format

``` ext
<type>: <short summary in imperative mood>

<optional body explaining what and why>

<footer>
Co-Authored-By: Engine <noreply@sentinel.io>

``` ext

**Types:** feat, fix, refactor, docs, test, chore

### Creating Commits

```bash

# Standard commit with HEREDOC for proper formatting
git commit -m "$(cat <<'EOF'
<type>: <summary>

<body>

Co-Authored-By: Engine <noreply@sentinel.io>
EOF
)"

``` ext

### Commit Constraints

- NEVER use `--amend` on pushed commits
- NEVER use `--no-verify` to skip hooks
- ALWAYS run local CI before committing: `python scripts/local_ci.py` ext
- ONE commit per sprint (accumulate changes)

### Two-Phase Commit (Async Multi-Agent)

When coordinating multiple async subagents, don't block synthesis on the slowest agent:

1. **Initial commit:** Synthesize findings from completed agents
2. **Amendment commit:** When late-arriving agents complete, integrate via Edit tool + new commit

**Source:** FSP stress test (2026-02-19) — 8 agents, Agent 7 completed late → `3f06d9fea` (initial) + `63400a728` (amendment)

### Submodule Cleanup

When encountering broken submodule tracking (mode 160000 gitlink without .gitmodules):

1. `git rm --cached <path>` - Remove from git index
2. Add `<path>/` to `.gitignore` ext
3. Keep directory locally if needed for reference

**Source**: Sprint 047 submodule fix (STORY-047-004)

---

## 2. Pushes

### Standard Push

```bash

# Push with upstream tracking
git push -u origin <branch>

# Push to existing upstream
git push

``` ext

### Force Push (DANGEROUS)

```bash

# NEVER force push to main/master

# Only use on personal feature branches with explicit user approval
git push --force-with-lease  # Safer than --force

``` ext

### Post-Push Review

`scripts/ci_review_parser.py` does not exist (skills-audit 2026-06-09). After each
push to a branch with an open PR, review comments manually — `gh pr view <number>
--comments` — and classify actionable vs noise before the next push, otherwise bot
feedback accumulates unaddressed across cycles (PR #122: 50+ comments).

### Push Constraints

- NEVER `git push --force` to main/master
- ALWAYS verify branch before pushing
- USE `--force-with-lease` if force push is necessary

---

## 3. Pulls and Fetches

### Fetch

```bash

# Fetch all remotes
git fetch --all

# Fetch specific remote
git fetch origin

``` ext

### Pull Strategies

```bash

# Merge strategy (default)
git pull origin main

# Rebase strategy (cleaner history)
git pull --rebase origin main

``` ext

### Pull Constraints

- PREFER rebase for feature branches
- USE merge for shared branches
- ALWAYS fetch before checking remote state

---

## 4. Branches

### Branch Naming Convention

``` ext
sprint-{NNN}           # Sprint work branches
sprint-{NNN}-0         # Cleanup sprint
sprint-{NNN}-completion # Sprint completion
feature/{description}   # Feature branches
fix/{description}       # Bug fix branches
hotfix/{description}    # Critical fix branches

``` ext

### FORBIDDEN Branch Patterns

``` ext
sprint-100-fix         <- Use sprint-100-0 instead
feature-sprint-100     <- Confusing: is it sprint or feature?
my-changes             <- Non-descriptive
test                   <- Ambiguous

``` ext

### Branch Operations

```bash

# Create and switch
git checkout -b <branch-name>

# Switch to existing
git checkout <branch-name>

# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>

# List branches
git branch -a

# Show current branch
git branch --show-current

``` ext

### Multi-Instance Isolation & Ephemeral Worktree Sandbox (absorbed from goo-worktree-sandbox-manager)

**CRITICAL:** When multiple Engine instances run simultaneously or experimental trials are conducted:

- **Worktree-First Isolation:** Prevents dirty worktree contamination, foreign work sweeps, and scheduler race conditions during parallel agent execution by creating, inspecting, and pruning isolated git worktrees (`.worktrees/trial-<id>`).
- **Never Dirty `main` Worktree:** Multi-step experimental trials (paper repairs, benchmark runs, subagent explorations) run inside `.worktrees/sandbox-<name>`.
- **Execution Protocol:**
  1. `git worktree add -b feat/agent-trial-<id> .worktrees/trial-<id> origin/main` ext
  2. Execute build, tests, or code edits inside `.worktrees/trial-<id>`.
  3. Inspect diff (`git diff --stat origin/main..HEAD`) to verify non-contamination.
  4. Cherry-pick, pathspec merge, or PR trial commits into main.
  5. Teardown & prune: `git worktree remove --force .worktrees/trial-<id>` and `git branch -D feat/agent-trial-<id>`.
- **One branch (or worktree) per agent:** When >1 agent may be active, each works on its own feature branch/worktree checkout and never edits in the shared `main` checkout. Commit early so WIP isn't lost.
- Each instance MUST work on a unique branch
- Never modify `main` directly - use PR workflow
- Branch naming: `{user}-{task}` or `sprint-{NNN}-{instance}` ext
- **Blocked sync recovery:** when `pull --ff-only`/`checkout` aborts on ANOTHER
  session's dirty files, do NOT stash or touch them. Recover only your paths:
  `git restore --source=origin/main --worktree -- <your paths>` and defer the
  full sync until that session commits. (2x live, 2026-06-11 sweep session.)
- **NEVER delete another agent's untracked files.** Untracked files at the repo root
  (e.g. `.codex-*.patch`) are routinely a running agent's LIVE working state, not debris.
  A content-redundancy check does NOT establish disposability — it proves the work
  landed, not that the file is idle. **Liveness tell: if the file set or their mtimes
  change during your own session, a process is writing them right now.** Deletion is
  unrecoverable: untracked means git holds no copy and `rm -f` bypasses the Recycle Bin.
  Ask the owning session, or leave them. (30 live patches destroyed mid-sprint,
  2026-07-18.)
- **Dirty shared checkout + research/paper package PR** (autoskill 2026-07-24): do **not**
  stash foreign WIP. Prefer
  `git worktree add -b <branch> target/grok-worktrees/<slug> origin/main`, copy or edit
  only intentional paths, stage **explicit paths only**, rebase onto `origin/main`, push,
  `gh pr create --base main --head <branch>`. If a plan names a missing remote branch, base
  on `origin/main` and record that in the PR or implementation receipt.
- **Meta skill centralization PR (autoskill 2026-07-24):** when landing `/autoskill` +
  `/auto-improve-autoskill` + `/auto-symmetry-hunter` captures, stage **only** skill hosts
  (`.agents`/`.claude`/`.codex`/`.grok`/skills), `runs/coda/*` reports, and the
  accomplishment note. Refuse to sweep concurrent paper/Rust/Lean rabbits from a dirty
  shared checkout into the same PR. One agent owns that meta land.
- **Worktree path lists (Windows, autoskill 2026-07-24):** write path files with **real
  newlines** (`Path.write_text(chr(10).join(paths)+"\n")`). Never `'\\n'.join` / expandable
  PowerShell strings that bake a literal `\n` into one path — copy/`git add` then stages
  zero files. Stage only explicitly named paths. Never use `git add .`, `git add -A`, or commit anything under `target/**`.
- **PowerShell backticks destroy markdown (2026-07-25):** expandable python -c / here-strings expand markdown code spans (backticks) and break table rows. For multi-line markdown edits with backticks, LaTeX `$...$`, or guillemets, write a temp `.py` file and run it — never inline expandable PowerShell.
- **Worktree `index.lock`:** also check `.git/worktrees/<name>/index.lock` (not only
  `.git/index.lock`). Same stale rule: size 0 and unchanged mtime across two checks before
  remove.
- **Governed-crate commits from a clean worktree** (autoskill 2026-07-24 overnight):
  when staging paths under `scripts/packet_registry.json` prefixes, include a truthful
  `Packet-Ref: <packet>` trailer (or stage the packet update). Run `rustfmt` on touched
  `.rs` before push so pre-push local_ci does not fail on format-only diffs. Stage only explicitly named paths; never
  `git add -A`, `git add .`, or anything under `target/**` in a dirty shared checkout.
- **After bulk renames or full-directory copies into a worktree** (autoskill 2026-07-24 QF reorg): **diff critical paths against `origin/main`** (or restore missing trees) before stage; never treat "directory copy succeeded" as content preservation.
- **Large rename/rename PR conflicts** (autoskill 2026-07-24 lean4 001_coda / PR #1402):
  when `main` has also renamed or reorganized the same tree, do **not** hand-resolve
  hundreds of rename/rename markers. Prefer: clean worktree from `origin/main` → re-apply
  the mechanical transform (flatten/rename script) → update feature branch tip → push
  `--force-with-lease` on the **feature branch only** (never main). Then diff critical
  paths against `origin/main` before stage. Record the rebuild in the PR body.
  **Scope before choosing a strategy**: `git merge-tree --write-tree --name-only
  origin/main HEAD` reports the real conflict count and file list without touching the
  worktree — run it before assuming a large `git rev-list --left-right --count` delta
  means a large conflict. (autoskill 2026-07-28 CODA rename / PR #1567: a 76-commit,
  1225-file drift looked catastrophic from the commit count alone; `merge-tree` showed
  35 real conflicts, 30 of them generated index files resolved by rule 3 below — an
  ordinary `git merge` closed it in minutes. A blind `git pull --rebase` earlier in the
  same session, run without scoping first, hit 880 conflicted files and had to be
  aborted.)
- **Official archive trees (autoskill 2026-07-24 Symbol Game session; densified 2026-07-25):**
  `engine/.official_archive/the_symbol_game/` must remain the **full
  unzipped** tree on `main`. The sibling `the_symbol_game.zip` is **supplemental** cold
  storage, not a license to delete the tree. Mine useful files into published papers first;
  never “zip-only” `main` without an explicit operator license. If a feature branch deleted
  the tree, restore from `origin/main` before merge.
  **Research tool park (paper-repair r4):** `git mv` of `research/core_sweeper` and
  `research/core_sweeper_fast` into `.official_archive/` is **archive park**,
  not T4 product-rail replace and not bare delete. Prefer `git mv` with explicit paths; do
  not treat archive relocate as license to delete `core_rip_papers` / product crates.

---

## 5. Pull Requests

### Create PR

```bash
gh pr create --title "Title" --body "$(cat <<'EOF'

## Summary
<description>

## Test Plan
- [ ] Tests pass
- [ ] Manual verification

Co-Authored-By: Engine <noreply@sentinel.io>
EOF
)"

# Create draft PR
gh pr create --draft --title "WIP: Feature"

``` ext

**PR create failure / dual-block (autoskill 2026-07-24):** If `POST /repos/.../pulls` or `gh pr create` returns **HTTP 500** / empty body, do **not** invent open PRs. Re-list with `gh pr list --state open` / search API. Status page “operational” ≠ create works. Branch pushed ≠ open PR.

**Dual-block:** `main` require-PR (GH013) + broken create API → cannot land without either a working PR path or an **explicit operator license** for temporary unprotect.

**Authorized temporary unprotect (operator-only license; auto-improve-autoskill IA-3):** Only when the operator explicitly allows direct main land (e.g. PR process broken + “merge to main allowed”). Agent may then: (1) PUT repository ruleset to drop `pull_request` only (keep deletion/non_fast_forward), (2) push prepared worktree merge, (3) **immediately** restore `pull_request` rule, (4) report ruleset id + before/after. Without explicit allowance: wait or stop. **Never leave protection off.** Never encode temporary unprotect as durable default policy.

### Review PR

```bash

# View PR details
gh pr view <number>

# View diff
gh pr diff <number>

# Check CI status
gh pr checks <number>

# Approve PR
gh pr review <number> --approve

# Request changes
gh pr review <number> --request-changes --body "Issues found"

``` ext

### Merge PR

**Pre-merge sprint retro gate (MANDATORY, BLOCKING — runnable):** before merging a `sprint-{NNN}` PR, run the
check; a sprint PR MUST NOT merge without `engine/research/product_planning_office/plans/sprints/{NNN}/retrospective.md`. This is the merge-side counterpart to
the pre-commit retro gate (§1) and closes the bypass that let PR #306 merge Sprint 121 with **no** retrospective.

```bash

# BLOCKING pre-merge check (exit 1 = do not merge). N/A for non-sprint branches.
bash .claude/skills/github/check_sprint_merge_gate.sh "$(gh pr view <number> --json headRefName -q .headRefName)"

# Only if the gate passes (exit 0):
gh pr merge <number> --squash --delete-branch   # squash (preferred)
gh pr merge <number> --rebase                    # or rebase

``` ext

**Multi-agent collision guard (Sprint 121 incident).** A concurrent agent ran `git add -A`/commit/push in the
**shared** repo dir (not its worktree), swept unrelated workstreams (a 233k-line purge + paper/Lean track) into the
sprint branch, and merged PR #306 retro-less. Hard rules: (1) agents operate ONLY in their own worktree (see
Multi-Instance Isolation §) and never commit in the shared tree; (2) stage **explicitly** (named
paths only: `git add -- <paths>`). Stage only explicitly named paths. Never use `git add .`, `git add -A`, or commit anything under `target/**`; (3) run the pre-merge gate above before
every sprint-PR merge.

### PR Checklist

- [ ] Branch naming follows convention
- [ ] PR has description and linked issues
- [ ] CI checks pass
- [ ] Required reviews obtained
- [ ] No merge conflicts

---

## 6. Issues

### Create/Manage Issues

```bash

# Create issue
gh issue create --title "Title" --body "Description" --label bug

# List issues
gh issue list --state open --assignee @me

# Close issue
gh issue close <number> --reason completed

# Comment on issue
gh issue comment <number> --body "Update"

``` ext

---

## 7. Releases

### Create Release

```bash

# Manual release
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"

# Auto-generate notes
gh release create v1.0.0 --generate-notes

# List releases
gh release list

``` ext

---

## 8. GitHub Actions & Workflows

### List Workflows

```bash

# List all workflows in repository
gh workflow list

# View specific workflow
gh workflow view <workflow-name>

``` ext

### Check Workflow Runs

```bash

# List recent runs
gh run list

# List runs for specific workflow
gh run list --workflow=<workflow-name>

# View specific run details
gh run view <run-id>

# View run with logs
gh run view <run-id> --log

``` ext

### Trigger Workflow Manually

```bash

# Trigger workflow_dispatch event
gh workflow run <workflow-name>

# With inputs
gh workflow run <workflow-name> -f input1=value1 -f input2=value2

# On specific branch
gh workflow run <workflow-name> --ref <branch>

``` ext

### Monitor and Control Runs

```bash

# Watch a run in progress
gh run watch <run-id>

# Cancel a running workflow
gh run cancel <run-id>

# Re-run failed jobs only
gh run rerun <run-id> --failed

# Re-run entire workflow
gh run rerun <run-id>

``` ext

### Download Artifacts

```bash

# List artifacts from a run
gh run view <run-id> --json artifacts

# Download all artifacts
gh run download <run-id>

# Download specific artifact
gh run download <run-id> -n <artifact-name>

``` ext

### Workflow Status Check (Before PR Merge)

```bash

# Check if CI passed for current branch
gh pr checks

# Check specific PR
gh pr checks <pr-number>

# Wait for checks to complete
gh pr checks --watch

``` ext

### Common Workflow Patterns

| Pattern | Command |
|---------|---------|
| Check if CI passed | `gh pr checks` |
| Re-run failed CI | `gh run rerun <run-id> --failed` |
| Trigger deployment | `gh workflow run deploy.yml` |
| View CI logs | `gh run view <run-id> --log` |
| Cancel stuck run | `gh run cancel <run-id>` |

---

## 9. Conflict Resolution

### Before resolving anything (MANDATORY)

1. **Get the real file list. `gh pr view --json files` truncates at 100.**
   Use `git diff --name-status $(git merge-base origin/main <head>) <head>`.
   PR #1226 reported 100 files; it was 1133. Any conclusion drawn from the
   truncated list is a fabricated finding.
2. **Check the PR is not already superseded.** Resolve every conflict to main's
   side, then `git diff origin/main` on the merged tree. Empty ⇒ the PR
   contributes nothing: close it, do not merge a no-op. (#1224 — 26 of 36 files
   were byte-identical to main; the 10 "conflicts" were main's superset
   resisting reversion to an older, narrower fix.)
3. **Never hand-merge a GENERATED file.** If the conflicted file carries
   `GENERATED by <script>; do not hand-edit`, resolve the *generator*, then
   regenerate. Resolving its markers by hand bakes in drift neither side
   intended. (Qualifies step 2 of Resolution Strategy below.)
4. **A forward-merge trips the packet gate on already-landed work.** Merging
   main re-stages governed paths, so `commit-msg` raises
   `MissingPacketLinkage` for changes that landed and were gated on main
   already. Do NOT add a `Packet-Ref:` trailer to clear it — that asserts
   packet linkage for content the commit does not contain.
5. **Windows:** `git show <rev>:<path>` fails in Git Bash — MSYS rewrites
   `origin/b:p` into `origin\b;p` ("ambiguous argument"). Use
   `MSYS_NO_PATHCONV=1` or `git cat-file -p <rev>:<path>`.
6. **Re-verify HEAD before reporting state read from the shared checkout**, or
   cite the commit you measured at. It moves under you mid-session — observed
   `937b2c9a8` → `c68b47e36` between measurement and report, which falsified a
   conclusion already delivered.

### Detection

```bash

# Check for conflicts during merge
git merge <branch>

# Check for conflicts during rebase
git rebase <branch>

``` ext

### Resolution Strategy

1. Identify conflicted files: `git status` ext
2. Open each file and resolve markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Stage resolved files: `git add <file>` (explicit paths from the **worktree CWD** — PowerShell pathspecs outside the repo fail silently)
4. Continue operation: `git merge --continue` or `git rebase --continue` ext

**PR conflict complete only when remote tip is mergeable (autoskill 2026-07-26 PR #1521):** after markers are gone, (1) merge/rebase commit, (2) `git push` the PR head, (3) `git fetch` + verify `HEAD == origin/<headRef>`, (4) if `main` advanced, re-merge `origin/main` cleanly, (5) `gh pr view --json mergeable` must be `MERGEABLE` before `gh pr merge`. Local resolve alone ≠ fixed. “Everything up-to-date” without matching SHAs is a stale-tracking false pass.

### Abort Operations

```bash
git merge --abort
git rebase --abort
git cherry-pick --abort

``` ext

---

## 10. Stash Operations

### Save Work

```bash

# Stash with message
git stash push -m "WIP: description"

# Stash including untracked
git stash push -u -m "WIP: description"

``` ext

### Recover Work

```bash

# List stashes
git stash list

# Apply most recent
git stash pop

# WARNING: If the target branch has remote commits not yet pulled,

# stash pop may cause add/add conflicts. Pull first to reduce risk,

# e.g. `git pull --ff-only`, then consider using `git stash apply` ext

# (resolve any conflicts, verify changes) and finally `git stash drop` ext

# once you're sure the recovered work is safe.

# Apply specific stash
git stash apply stash@{N}

# Show stash contents
git stash show stash@{N} --include-untracked --name-only

# Extract via temp branch (for untracked files)
git stash branch temp-recover stash@{N}

``` ext

### Drop Stash

```bash
git stash drop stash@{N}
git stash clear  # DANGEROUS - drops all

``` ext

---

## 11. Lock and Recovery

### Git Lock Recovery

**Prove the lock is stale before removing it** — in a shared checkout it may belong to a
live operation. Stale means 0 bytes AND unchanged mtime across two checks:

```bash
stat -c "size=%s mtime=%y" .git/index.lock 2>/dev/null || stat -f "size=%z mtime=%m" .git/index.lock   # run twice; both must match
rm -f .git/index.lock                        # only if stale
git status

``` ext

**While a lock is held, `git diff` can report files as clean that are not** — git cannot
