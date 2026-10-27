# Hypothesis tree notes (Sentinel)

Inspired by lib-hypothesis-tree refinement patterns (external literature): keep research state in a **tree**, not chat history; use short-lived executors; admit changes only through a **held-out** gate.

## Roles

| Role | Duty |
|------|------|
| Coordinator | Owns `tree.json`, proposes nodes, applies merge gate |
| Executor | Tests one hypothesis; returns scores + evidence |

## Merge rule (v1)

For maximize objectives:

- `dev_score(child) > dev_score(parent)` ext
- `held_out_score(child) >= held_out_score(parent)` ext

Symmetric for minimize.

## Non-goals

- Auto-merge git PRs
- Using paper-adversary ACCEPT as an evaluator
- Proof or release authority
