# Detailed definition: Pull Request Scope & Branch-Diff Audit (1)

**AuthorityEffect:** None.

Parent: [Pull Request Scope & Branch-Diff Audit](../../../../../rules/git/rl_pr_scope_and_branch_diff_audit.md). Load for the matching predicate, not every task.

# Rule: Pull Request Scope & Branch-Diff Audit

**AuthorityEffect:** None.

Cross-reference: [`../claims/rl_review_evidence_reproducibility.md`](../../../../../rules/claims/rl_review_evidence_reproducibility.md).

---

## Pull Request Claim Hygiene & Branch-Diff Audit Invariant

> **PR Scope & Merge-Base Diff Auditing:**
>
> 1. **Merge-Base Diff Inspection:** For PR reviews and branch audits, do not restrict checks to `git status --short`. The audit MUST inspect `git diff $(git merge-base main HEAD)...HEAD` and the full text of all files modified in the branch.
> 2. **Zero Forbidden Words Across Touched Files:** Any file modified or introduced in a pull request must maintain zero forbidden hype vocabulary (*proves*, *guarantees*, *mathematically verifies*, *fundamentally*, *true intelligence*, *impossible*, *universal*, *flawless*, *perfectly*, *clearly*, *obviously*, *simply*, *merely*, *weaponized*) unless explicitly justified in academic quotation.
> 3. **Explicit Staging:** In concurrent environments, stage files by exact relative path (`git add <path>`). Wildcard staging (`git add .`, `git add -A`) is forbidden to prevent committing incomplete background task files.

---

## GitHub Asynchronous Merge & Stacked PR Protocol Invariant (`RULE_GIT_ASYNC_MERGE_PROTOCOL_001`)

> **Asynchronous Merge & Auto-Pruned Ref Protocol:**
>
> 1. **Stacked / Queue Merge Gate Detection:** When merging pull requests in repositories protected by merge queues or stacked PR policies, agents must not invoke `gh pr merge` or synchronous GraphQL/REST merge endpoints. If an error occurs indicating a stacked PR requirement:
>    - Enqueue merge via the asynchronous REST endpoint:
>      `gh api -X PUT repos/{owner}/{repo}/pulls/{number}/merge-async -f merge_method={merge|rebase}`
>    - Never assume `squash` is permitted; inspect repository allowed merge methods or default to `merge`.
> 2. **UUID Polling Discipline:** Extract the pending `details.uuid` and poll `gh api repos/{owner}/{repo}/pulls/{number}/merge-async/<UUID>` until `status` transitions to `"merged"` (recording `details.sha`).
> 3. **Post-Merge Remote Ref Pruning:** Repositories configured with automatic head branch deletion delete remote refs upon merge completion. Autonomous agents must not invoke `git push origin --delete <branch>`, which errors on missing refs. Instead, agents must synchronize via `git remote prune origin` (or `git fetch --prune`) and delete local branches with `git branch -d <branch>`.
