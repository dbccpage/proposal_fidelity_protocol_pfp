# Worktree Sandbox Protocol & Selective Land Playbook

refresh the index, so any "clean" reading taken under a lock is unreliable. Re-verify
after clearing. To restore a file without touching the index, use `git show HEAD:<path>`
or reverse the edit textually rather than `git checkout --`. (2026-07-18.)

## Branch State Verification

```bash

# Always verify current branch before operations
git branch --show-current

# Verify branch state matches expected
git status
```

**After any scripted (Python/sed) edit to a tracked file, run `git diff --stat` before
staging.** A line count wildly larger than your change means the script rewrote the file's
line endings, not its content — observed 2026-07-22: 2020 changed lines for a 62-line edit.
This repo carries mixed CRLF/LF under `.gitattributes`; read bytes and re-encode to the
file's existing ending rather than `write_text(newline="")`, or use the Edit tool.

---

## 12. Windows Issues

### GitHub CLI Path

On Windows, the `gh` CLI may be installed via winget but not available in bash PATH. Use the full path:

```bash
"/c/Program Files/GitHub CLI/gh.exe" pr create --title "..." --body "..."

``` ext

Verify installation with:

```bash
"/c/Program Files/GitHub CLI/gh.exe" --version

``` ext

**Source:** Sprint 086 session - winget-installed tools not in bash PATH

### Staging Directives & Exclusions

Stage only explicitly named paths. Never use `git add .`, `git add -A`, or commit anything under `target/**`.

**Explicit Path Staging:**

```bash

# CORRECT - explicit paths
git add -- <explicit-files>

# FORBIDDEN - sweep staging and target/** commits
# git add .
# git add -A
# git add target/**

``` ext

**Error pattern:**

``` ext
error: open("frontend/nul"): No such file or directory
error: unable to index file 'frontend/nul'
fatal: adding files failed

``` ext

**Source:** Sprint 105-0 - git add . failed with Windows NUL device error

### Line Endings

```bash

# Configure for Windows
git config --global core.autocrlf true

``` ext

LF↔CRLF warnings are informational, but **line endings are load-bearing here**: fixtures
pin hashes of CRLF bytes, so a file restored with the wrong endings fails its own tests.

To restore a deleted/reverted file, use the form that applies the smudge filter:

```bash
git checkout <commit> -- <path>          # correct: honours .gitattributes + autocrlf
git show <commit>:<path> > <path>        # WRONG: writes raw LF, hash mismatch

``` ext

**Source:** 2026-07-19 - restoring 999_gtoc charter via `git show >` broke 11 tests.

### File Locking (npm/Electron)

```bash

# If npm operations fail with EBUSY:

# 1. Close all Electron/Node processes

# 2. Wait 5 seconds

# 3. Retry

``` ext

### Branch Delete Blocked

If a branch delete fails because it's "in use by worktree", switch to a different branch first.

### Common Windows Issues Summary

| Issue | Cause | Solution |
|-------|-------|----------|
| `nul` file errors | Windows reserved filename | Exclude with `":!nul"` |
| `~$*.xlsx` errors | Excel lock files | Add `~$*.xlsx` to `.gitignore` (pathspec `":!~$*.xlsx"` unsupported on Windows) |
| LF to CRLF warnings | Windows line ending config | Informational only, safe to ignore |
| Checkout blocked | Uncommitted local changes | Use `git stash` before checkout |
| Branch delete fails | Branch in use by worktree | Switch to different branch first |
| `gh` not found | winget-installed tools not in PATH | Use full path: `"/c/Program Files/GitHub CLI/gh.exe"` |
| EBUSY errors | npm/Electron file locks | Close Electron/Node processes, retry |
| `origin` not found | Remote named `github` not `origin` | Check `git remote -v`; use `github` |
| `git add` skips files | `.cargo/` and `engine/.core_skills/` in `.gitignore` | Use `git add -f` for skill/config files |
| `gh pr create` aborts after successful push | gh fails to associate the branch | Pass `--head <branch>` (and `--base main`) explicitly |
| `pull` after failed checkout fast-forwards WRONG branch | `git pull origin main` while still on the feature branch | Recover offline: `git branch -f main origin/main` then `git checkout main` (same commit ⇒ working tree preserved) |

---

## Protected Branch Workflow

The `main` branch is protected and requires pull requests.

**NEVER push directly to main.** Instead:

1. Create feature branch: `git checkout -b <branch-name>` ext
2. Push branch: `git push -u origin <branch-name>` ext
3. Create PR: `gh pr create` ext
4. Get approval and merge

**Operator-only temporary exception** (autoskill 2026-07-24): when the human says main protection is **disabled for now** and **explicitly** orders a direct land (no PR):

1. Prefer a worktree commit already based on current `origin/main` (dirty shared checkout still forbidden for `git add -A`).
2. `git fetch origin main`; **rebase until fast-forward-safe** — **never force-push `main`**.
3. `git push origin HEAD:main` (FF only). Concurrent agents may land between attempts — loop fetch/rebase/push, do not force.
4. **Remind the operator to re-enable protection immediately after.**

**Landed vs branch tip** (autoskill 2026-07-24): remote feature-branch tip SHA ≠ proof of land after rebase or direct-to-main. Answer “is it on main?” with `git merge-base --is-ancestor <landed-sha> origin/main`, or match commit **subject/paths** on `origin/main`. Stale pre-rebase branch tips are expected; do not report “not on main” from tip-only ancestry alone.

**PR create platform failure** (autoskill 2026-07-24): if `gh pr create` / `POST /pulls` returns HTTP 500 with empty body, treat as **GitHub outage** (not a bad branch). Confirm the push succeeded; offer the compare URL; retry later — do not rewrite history.

---

## Pre-Operation Checklist

Before any Git operation:

- [ ] Verify current branch: `git branch --show-current` ext
- [ ] **Verify isolation: `git rev-parse --show-toplevel`.** A harness claim of "operating in
      a git worktree" is NOT proof — it can resolve to the shared main checkout, where your
      edits land in a tree other agents are using. (2026-07-18.)
- [ ] **Before `gh pr create`: `git merge-base --is-ancestor <commit> origin/main`.** Parallel
      sessions may have already landed the same work; check ancestry, not assumption.
- [ ] If resuming after user edits between turns, RE-VERIFY branch (user activity may have switched branches)
- [ ] After switching branches, ensure the branch is tracking the correct remote (set once with `git push -u origin <branch>` or `git branch --set-upstream-to=origin/<branch>`), then sync with remote before making new commits via `git pull --ff-only` (or `git pull --rebase` if repository policy allows; prevents non-fast-forward rejections). If no upstream is desired, use `git fetch` followed by `git status` instead.
- [ ] Check working tree status: `git status` ext
- [ ] Run local CI for commits: `python scripts/local_ci.py` ext

**Source:** Sprint 122 session -- committed to sprint-121-0 instead of sprint-121 after user edits switched branch context

---

## Recovery Playbooks

### Playbook 1: Sprint Commit and Push

**Trigger:** User says "commit and push to sprint-NNN"

```bash

# 1. Verify current state
git branch --show-current
git status --short

# 2. Check if branch exists
git branch -a | grep sprint-{NNN}

# 3a. If branch doesn't exist, create it
git checkout -b sprint-{NNN}

# 3b. If branch exists, switch to it
git checkout sprint-{NNN}

# 4. Stage only explicitly named paths (never git add ., git add -A, or target/**)
git add -- <explicit-files>

# 5. Verify staged changes
git status --short

# 6. Commit with conventional format
git commit -m "$(cat <<'EOF'
feat(sprint-{NNN}): description

Detailed changes:
- Item 1
- Item 2

Co-Authored-By: Engine <noreply@sentinel.io>
EOF
)"

# 7. Push with upstream tracking
git push -u origin sprint-{NNN}

``` ext

| Error | Recovery |
|-------|----------|
| Branch already exists | `git checkout sprint-{NNN}` |
| Uncommitted changes block checkout | `git stash` first |
| Push rejected | `git pull --rebase origin sprint-{NNN}` then push |

### Playbook 2: Sync Local with Remote

**Trigger:** User says "sync local main with remote" or "PR merged, update local"

```bash

# 1. Check for uncommitted changes
git status --short

# 2. If changes exist, stash them
git stash push -m "WIP: before sync"

# 3. Switch to main
git checkout main

# 4. Pull latest from remote
git pull origin main

# 5. Delete merged local branches (optional)
git branch -d sprint-{NNN}

# 6. Prune stale remote refs
git remote prune origin

# 7. Restore stashed changes (if any)
git stash pop

# 8. Report final state
git status --short
git log --oneline -3

``` ext

| Error | Recovery |
|-------|----------|
| Cannot delete branch (not merged) | Use `-D` if user confirms |
| Stash conflicts on pop | `git stash show` then resolve |
| Local changes would be overwritten | Stash first |

### Playbook 3: Create Pull Request

**Trigger:** User says "create PR" or "open pull request"

```bash

# 1. Verify on correct branch (not main)
git branch --show-current

# If on main, STOP and ask user which branch

# 2. Ensure branch is pushed
git push -u origin $(git branch --show-current)

# 3. Create PR via gh CLI
gh pr create \
  --title "Sprint {NNN}: Description" \
  --body "$(cat <<'EOF'

## Summary
- Change 1
- Change 2

## Test Plan
- [ ] Local CI passes
- [ ] Manual verification

Co-Authored-By: Engine <noreply@sentinel.io>
EOF
)"

# 4. Report PR URL
gh pr view --web

``` ext

### Playbook 4: Resolve Merge Conflict

**Trigger:** User says "fix merge conflict" or sees conflict markers

```bash

# 1. Identify conflicted files
git status

# 2. For each conflicted file:

#    a. Open file

#    b. Find markers: <<<<<<< ======= >>>>>>>

#    c. Choose correct code

#    d. Remove markers

#    e. Save file

# 3. Stage resolved files
git add {resolved-file}

# 4. Continue the operation
git merge --continue   # If merging

# OR
git rebase --continue  # If rebasing

# 5. Verify clean state
git status

``` ext

### Playbook 5: Recover from Detached HEAD

**Trigger:** `git branch --show-current` returns nothing

```bash

# 1. Check current state
git status
git log --oneline -1  # Note the commit hash

# Option A: Return to existing branch
git checkout main

# Option B: Save current work as new branch
git checkout -b recovery-branch

# Option C: Cherry-pick to correct branch
git checkout main
git cherry-pick {commit-hash}

``` ext

### Playbook 6: Recover Lost Stash

**Trigger:** User accidentally dropped stash

```bash

# 1. Check stash list
git stash list

# 2. If empty, search reflog for stash commits
git fsck --unreachable | grep commit | cut -d' ' -f3 | \
  xargs git log --oneline --graph | head -50

# 3. Find the stash commit (look for "WIP on" messages)

# 4. Apply the found commit
git stash apply {commit-hash}

# 5. Verify recovered files
git status

``` ext

### Playbook 7: Undo Last Commit

**Trigger:** User says "undo commit" or "I committed to wrong branch"

**Keep changes (soft reset):**

```bash
git reset --soft HEAD~1
git status  # Changes are staged

``` ext

**Discard changes (hard reset):**

```bash
git reset --hard HEAD~1

# WARNING: Changes are lost

``` ext

**Move commit to correct branch:**

```bash

# 1. Note the commit hash
git log --oneline -1

# 2. Switch to correct branch
git checkout correct-branch

# 3. Cherry-pick the commit
git cherry-pick {hash}

# 4. Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1

``` ext

### Playbook 8: Force Push Recovery

**Trigger:** User needs to force push (DANGEROUS)

```bash

# NEVER on main/master

# Only on your own feature/sprint branch
git push --force-with-lease origin {branch}

``` ext

**If force push was accidental:**

```bash

# 1. Find the previous commit in reflog
git reflog

# 2. Reset to previous state
git reset --hard {previous-hash}

# 3. Force push the fix
git push --force-with-lease origin {branch}

``` ext

### Playbook 9: Clean Up Old Branches

**Trigger:** Repo has many stale branches

```bash

# 1. Fetch and prune remote refs
git fetch --prune

# 2. Containment test -- ancestry, NOT diff. 0 = every commit is already in main.
git rev-list --count origin/main..{branch}

#    `git diff --name-only origin/main..{branch}` is NOT this test. A branch 100

#    commits BEHIND reports thousands of "differences" that are main's newer work.

#    Observed 2026-07-22: 2924 files reported for a fully-contained branch.

# 3. ahead > 0 does NOT mean unmerged -- this repo squash-merges, so a landed

#    branch keeps non-ancestor commits and `--merged` will never clear it.

#    Compare the commit's OWN touched files against main instead:
git show {sha} --name-only --format="" | while read f; do
  git diff --quiet {sha} origin/main -- "$f" && echo "SAME  $f" || echo "DIFFERS $f"
done

#    all SAME = squash-landed, safe to `git branch -D`. Any DIFFERS = real work.

# 3b. Confirm the branch has a remote at all before deleting:
git rev-parse origin/{branch}   # fatal = local-only; unpushed commits are the ONLY copy

# 4. Delete specific remote branch
git push origin --delete {branch-name}

# 5. Prune local refs to deleted remotes
git remote prune origin

# 6. Verify cleanup
git branch -a

``` ext

**Conflicted/dirty PR: check patch identity, not just ancestry, before resolving.** The
ancestry checks above (`git rev-list --count`, per-file SAME/DIFFERS) require knowing the
branch is a straight ancestor or a squash-landed tip. They miss a third case: a PR whose
commit has a **different SHA but identical patch** to something already on `origin/main` ext
(a rebase, cherry-pick, or — commonly — a parallel/retried automated push landing the same
content twice, e.g. `cppms-fallback-*` branches from `scripts/cppms.py`). Such a PR shows
`mergeable: CONFLICTING` not because of real divergence, but because main has moved past
the duplicate landing. "Fixing conflicts and merging" it then produces an empty merge at
best, or silently reverts main's newer work built on top of the duplicate, at worst.

```bash

# Patch-identity check: does this branch's content already exist on main under a

# different commit? '-' = contained (safe to close, no merge needed); '+' = not yet landed.
git cherry origin/main origin/{branch}

# Confirm with patch-id if git cherry is ambiguous on a multi-commit branch:
git show {branch-sha} --format= --patch | git patch-id --stable
git show {main-sha}   --format= --patch | git patch-id --stable   # same id = same patch

``` ext

If every commit shows `-`, close the PR as already-landed (comment with the matching
main SHA as evidence) instead of resolving conflicts. Source: PR #1528 (2026-07-28) —
`cppms-fallback-20260728_011902`'s commit was patch-identical to main's `9e6f44acf`,
16 commits behind main's tip.

### Playbook 10: Worktree Setup for Parallel Work

**Trigger:** User wants to run multiple Engine sessions

```bash

# 1. Ensure on main and up to date
git checkout main
git pull origin main

# 2. Create worktree directory
mkdir -Force engine/worktrees

# 3. Create worktree for each sprint
git worktree add engine/worktrees/sprint-101 -b sprint-101 main
git worktree add engine/worktrees/sprint-102 -b sprint-102 main

# 4. Verify
git worktree list

``` ext

**Launch sessions:**

```powershell

# Terminal 1
cd engine/worktrees/sprint-101
claude

# Terminal 2
cd engine/worktrees/sprint-102
claude

``` ext

**Cleanup after merge:**

```bash
cd c:\Users\a343o\source\repos\sentinel

# Preflight -- RE-RUN this immediately before acting. Other sessions create

# worktrees mid-task; two appeared during a cleanup pass on 2026-07-22.
git worktree list
git -C <wt> status --porcelain | wc -l          # uncommitted work -- must be 0
git -C <wt> rev-list --count origin/main..HEAD  # unmerged commits -- must be 0

git worktree remove engine/worktrees/sprint-101
git worktree prune

``` ext

**Space without deletion:** a worktree's `target/` is regenerable build cache. Removing
it alone took one worktree from 13G to 488M with every source file untouched — reach for
that before proposing to delete a worktree you cannot prove is safe.

### Quick Decision Tree

``` ext
Problem?
+-- Can't switch branches

|   +-- Stash first: git stash
+-- Push rejected

|   +-- Pull first: git pull --rebase origin {branch}
+-- Merge conflict

|   +-- Resolve markers, git add, git merge --continue
+-- Detached HEAD

|   +-- git checkout main (or create recovery branch)
+-- Lost work

|   +-- Check: git stash list, git reflog
+-- Wrong branch

|   +-- Cherry-pick to correct, reset wrong
+-- Everything broken
    +-- git stash; git fetch origin; git reset --hard origin/main; git stash pop

``` ext

---

## Self-Improvement Loop

This skill automatically improves from corrections via autoskill integration.

### Learning Patterns

When the github-mgr agent receives corrections, trigger learning:

**Correction Detection Triggers:**

| Correction Type | Example | Learning Action |
|-----------------|---------|-----------------|
| Branch naming | "Use sprint-082 not feature-082" | Update Branch Naming Convention |
| Commit format | "Include STORY-xxx in commits" | Update Commit Message Format |
| Push strategy | "Always rebase before merge" | Update Pull Strategies |
| PR template | "Add test plan section" | Update Create PR template |
| Force push | "Never force push to develop" | Add to Push Constraints |

**Auto-Learn Flow:**

``` ext
1. Agent receives correction
2. Classify correction type (branch/commit/push/PR/etc.)
3. Trigger /autoskill
4. Propose update to this skill
5. Apply after approval

``` ext

### Error Pattern Library

Common Git errors that should trigger learning:

| Error | Pattern | Fix | Prevention |
|-------|---------|-----|------------|
| Push rejected | `non-fast-forward` | `git pull --rebase` | Always fetch before push |
| Merge conflict | `CONFLICT (content)` | Resolve markers, stage, continue | Communicate with team |
| Detached HEAD | `HEAD detached at` | `git checkout <branch>` | Always verify branch |
| Lock file | `index.lock exists` | `rm -f .git/index.lock` | Don't interrupt operations |
| Branch diverged | `have diverged` | Decide: rebase or merge | Pull frequently |
| Protected push | `protected branch` | Use PR workflow | Never push main directly |

**When errors recur despite documentation:** Flag for /autoskill to add stronger prevention steps.

### Autoskill Triggers for GitHub Skill

The following corrections should ALWAYS trigger `/autoskill`:

1. **Branch naming violations** - User corrects branch name format
2. **Commit message rejections** - User revises commit message
3. **Push strategy changes** - User specifies rebase vs merge preference
4. **PR template updates** - User adds/removes sections
5. **Force push incidents** - Any force push correction
6. **Conflict resolution patterns** - New resolution strategies

**How to trigger:**

``` ext
/autoskill

``` ext

Target skill: `engine/.core_skills/github/SKILL.md` ext

---

## Vercel CI/CD Pattern (Sentinel.com)

When working with Vercel-deployed Next.js apps (e.g., `sentinel_ai/web`):

**Auto-deploy trigger:** Vercel deploys automatically on push/merge to `main`. No manual `gh workflow run` needed.

**Pre-merge verification:**

1. Run `npm run build` locally before pushing (catches SSG/SSR errors Vercel will hit)
2. Check `next.config.js` does not have `output: 'export'` if the app uses API routes
3. Verify Edge Runtime compatibility: no `PrismaClient` imports in middleware or `auth.config.ts` ext

**Post-deploy verification:**

1. Check Vercel dashboard for deploy status (or `vercel --prod` CLI)
2. Verify API routes respond (not 404)
3. Test OAuth flow end-to-end (callback URL must include Vercel domain)

**Known failure pattern:** Serial deploy failures where each fix reveals the next error. Fix ONE issue per deploy cycle; do not stack speculative fixes.

**Source:** Sentinel.com MVP deployment session (convo.md)

---

## Operational Runbook Conventions

When generating runbooks or step-by-step operational procedures:

- Every step must contain an exact copy-pasteable command
- Every step must state the required observation (what success looks like)
- Every failure must map to exactly one named terminal state
- No step may say "figure it out", "debug as needed", or "try different approaches"
- Assume the operator is tired, stressed, and cannot rely on memory

**Source:** POC0 H200 smoke runbook session (2026-05-22) -- user rewrote runbook to stress-proof standard

---

## Jupyter Notebook Safety

For critical steps in notebooks (tests, training, validation):

- Use `subprocess.run()` + `assert result.returncode == 0`, not `!command` (shell bang silently swallows failures)
- Delete output directories before processes whose artifacts are checked post-run (prevents stale-artifact false-pass)
- Default variable values must match the notebook's stated purpose (e.g., if the notebook is for H200 Nemotron smoke, default to Nemotron, not Llama)

**Source:** POC0 smoke notebook patches (2026-05-22) -- 3 blocking safety holes identified and fixed

---

## Related Skills

| Skill | Relationship |
|-------|--------------|
| commit | DEPRECATED: redirect to this skill |
| ci-cd | Commits and PRs trigger CI pipelines |
| code-review | PRs require code review |
| sprint-execution | Commits implement sprint stories |

**Family:** github (see [family_registry.md](../../_shared/family_registry.md))

---

## Session conventions (autoskill)

- **cppms-fallback drain-loop (autoskill 2026-07-31):** after each selective-land squash-merge, re-run `gh pr list --state open` before claiming the stack is empty (#1660→#1662 mid-session). Classify ONLY_PR/ONLY_MAIN/M_diff; never full-merge tips that delete Wave/RGB/root-sprints capital.

### Stacked cppms-fallback conflict land (2026-07-31)

Operator pattern for open conflicted `cppms-fallback-*` / “sync to main” PR stacks:

1. `git fetch` + `git cherry origin/main PR_HEAD` + tree `name-status` (ONLY_PR / ONLY_MAIN / M_diff).
2. Clean worktree from `origin/main`; **never** resolve in dirty shared checkout with foreign ORT dirt.
3. Prefer **main** on governance files (skills enforcer/ooutwire, proof_packets master order, OE036 PL-5 CLOSED).
4. `git checkout PR_HEAD -- <ONLY_PR>` then intentional `git rm` for flat→nested renames only.
5. Restore root `engine/research/product_planning_office/plans/sprints/` and Wave/RGB paths the PR tip deletes.
6. Empty index after resolve → **close already-landed** with comment (patch/SHA evidence).
7. Non-empty selective tip → `force-with-lease` PR head → `gh pr merge --squash`; close superseded stack siblings.
8. Do **not** run `python scripts/cppms.py` to “fix” these PRs — it re-sweeps.

See `/goo-commit-isolation-guard` v1.1 and `/0-oe-commit` v1.3.1.

- **Paper-hygiene PR on dirty main (autoskill 2026-07-25):** never git add -A when foreign review/paper WIP is present. Use worktree from origin/main; stage only paper package + runs/coda/* receipts (+ intentional skill hosts if meta land). Meta skill land stays separate from paper/Rust rabbits when possible.
- **Paper-repair B/R/G campaign on main (symmetry 2026-07-25):** when operator locks the campaign to **`main` only**, pin receipts to `origin/main` SHA; stage **explicit** paths under `research/_reviews/paper_repair/` + named pilot papers; respect review-request `OPEN`|`IN_WORK`|`CLOSED` and round gate. Still no force-push / no `--no-verify`. Default multi-agent isolation (feature branch/worktree) is overridden **only** by that campaign ruling.
- **Untracked literature harvest / agent-artifacts (autoskill 2026-07-26):** after CSV→`file_urls.md` combine, **worktree-commit + push + PR before deleting CSVs** (or keep the source zip until PR lands). Never claim complete while `file_urls.md` is untracked-only. If the MD/CSVs vanish, check Recycle Bin for `agent-artifacts-zip_*.zip` and rebuild; do not invent rows. Dirty shared main: isolate harvest PR in `target/grok-worktrees/<slug>` — stage only the artifact tree.
- **Post-merge main sync + full skill-garden mirror (autoskill 2026-07-26):** after skill/meta PRs merge, `git fetch origin main` + `git reset --hard origin/main` (tracked only; leave untracked `engine/research/library/*.pdf` alone). Then full host mirror from `.agents/skills`: list every package dir and `python scripts/sync_cross_host_skills.py --source-host .agents/skills --skills <all>`; do **not** rely on DEFAULT_SKILLS (8 names). Verify `--check` exit 0 and equal package counts on `.agents`/`.claude`/`.codex`/`.grok`. Land the mirror on a skills-only PR if `.grok` gained packages.
- **PR conflict remote-mergeable gate (autoskill 2026-07-26):** see §9 — push + fetch/SHA + optional re-merge main + `mergeable: MERGEABLE` before merge. Lean guillemet (`«»`) rewrites and dual-home README writers: temp `.py` only (same PowerShell rule as backticks/LaTeX).

## Constraints

See: [constraints.md](../../_shared/constraints.md)

Required: NO_FORCE_PUSH, DESCRIPTIVE_COMMITS, NO_AMEND_PUSHED, BRANCH_ISOLATION

Summary:

- NEVER force push to main/master (NO_FORCE_PUSH)
- Commits must have descriptive messages (DESCRIPTIVE_COMMITS)
- NEVER amend pushed commits (NO_AMEND_PUSHED)
- Each instance works on unique branch (BRANCH_ISOLATION)

## Example Session

``` ext
User: Commit my changes with message "feat(sprint-138): event spine schema"

Core: [Invokes /github or git skill] Checks branch (sprint-138), stages files, runs pre-commit (lint/tests), then commits with provided message. No force push, no amend if already pushed.

``` ext

---

## 10. Commit Isolation & Pre-Flight Guard

**Blocking pre-flight guard** in front of `/0-oe-commit` and `/github` commit flows.

### When to Activate

- Before any commit/push/PR on a multi-agent dirty tree
- After concurrent ORT / PL2 / paper work on the same checkout
- When tempted to `git add .` or run a full-tree cppms

### Mandatory Procedure

1. `git status` + `git branch` — record foreign paths not owned by this session.
2. Build an **explicit pathspec** of session-owned files only.
3. **Refuse** `git add -A`, `git add .`, and blanket cppms if unrelated dirt exists.
4. Scan for paper zips, secrets, and generated ENC dumps in the pathspec.
5. Only then execute `/github` or `/0-oe-commit` with the pathspec list.

### Hard Refusals

- Staging another agent's sprint folder "to be helpful"
- Force-push / hook bypass suggestions
- Promotion commits without human auth (see `/human-promotion-firewall`)
- **`origin/main..HEAD` empty while porcelain is dirty** — tip may equal main, but unstaged foreign QM/PNG/paper work is still present; **STOP** blanket cppms/`git add .` ext
- Treating "session capital already tracked" as license to push the whole dirty tree — capital may already be on main via a concurrent omnibus commit (wrong message); still do not sweep remaining dirt
- **Live scheduled loops still firing** into the shared checkout (Grok `scheduler_*`, engine_looping_goal, etc.) — pause/`scheduler_delete` before pathspec commit, or the pathspec races the next fire
- **Live `/loop` / scheduler fires still writing** under `published/*/ _support/RUN_*`, Lean dual harness, or `proof_packets/` — treat those paths as **foreign until the loop is cancelled or idle**. Do not pathspec-commit mid-fire (half-written receipts + map lag).

### cppms-fallback / Stacked Conflict PRs

When resolving open PRs titled `sync to main` or `cppms-fallback-*`:

1. **Tree-diff tip vs `origin/main` first** (`git diff --name-status origin/main PR_HEAD`).
2. Classify paths: `ONLY_PR` (unique), `ONLY_MAIN` (PR would delete), `M_diff` (content diverge).
3. **Never full-merge** a tip that deletes Wave Lean, RGB receipts, root `engine/research/product_planning_office/plans/sprints/`, or richer enforcer/ooutwire on main.
4. **Selective land:** worktree from `origin/main` → `git checkout PR_HEAD -- <ONLY_PR paths>` → `git rm` only intentional flat-legacy moves → restore main on all conflict/regression paths.
5. **Empty after resolve** (`git diff --cached` empty) → **close as already-landed** (comment + evidence), do **not** force an empty squash.
6. **Stacked fallbacks** (1653⊂1654⊂1655⊂1656): land **tip unique** once; close supersedes with pointer to the land PR.
7. Prefer `gh pr merge --squash` on the rewritten PR branch after `force-with-lease` of the selective tip.
8. **Drain-loop after merge:** concurrent agents mint new `cppms-fallback-*` PRs while you land. After each squash-merge, re-run `gh pr list --state open` before declaring the stack empty.

**Verdict tokens:** `PROCEED_PATHSPEC` | `SELECTIVE_LAND` | `CLOSE_ALREADY_LANDED` | `BLOCK_REGRESSIVE_MERGE`.
