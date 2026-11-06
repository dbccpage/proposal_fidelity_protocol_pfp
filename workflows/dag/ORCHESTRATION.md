# Orchestration: goal, team and boost

AuthorityEffect: None. This is a design for running the workflow families
with teams of model agents. It is not implemented as a runner yet, and it
grants no model any authority to accept a result.

Every node in [`workflow_dag.json`](workflow_dag.json) carries a `team`
record with four parts. Together they describe a goal-driven team: a
measurable goal, a small team that divides the work, and one bounded
escalation ("boost") when the first attempt fails.

## 1. Goal

One sentence that names the success predicate and the stop condition, for
example "a checked gluing witness or a checked obstruction class for the
declared cover". The goal is always decided by the node's `host_check`.
A team that cannot reach the goal stops with a typed record (refusal, loop
limit, budget stop); it does not lower the goal.

## 2. Team and model tiers

Each role has a model tier. The tiers divide the work like this:

| Tier | Used for | Typical roles |
| --- | --- | --- |
| Sonnet | Most of the work: writing code and encoders, running capsules, keeping custody and accounting, applying patches | `coder` |
| Opus | Deep research: derivations, certificate and checker design, hypotheses, analysis, and the boost step | `deep_researcher`, `miner`, `defender` |
| Fable | Adversarial research: countermodels, leak tests, near-self inputs, premise removal, prosecution | `adversary`, `prosecutor` |
| none | The host check, which is deterministic code | `host_checker` |

Across WF6–WF23 Sonnet holds the most seats; Opus and Fable appear where a
family needs deep or adversarial research. The counts are in each node's
`team.roles`.

## 3. Teamwork patterns

| Pattern | How the team works |
| --- | --- |
| `solo` | One worker, one host check. |
| `relay` | Workers in sequence; each reads only the frozen, sealed output of the previous one. |
| `parallel_isolated_then_global` | Isolated workers share frozen inputs, never each other's replies; the host checks each locally, then globally. |
| `sweep_with_shared_judge` | The same task under several arms or presentations, graded by one unchanged checker and compared item by item. |
| `red_team_pair` | A builder and an adversary; the adversary's cases become negative controls, never extra authority. |
| `proposer_with_residual_feedback` | One proposer receives only the checker's typed residual between attempts, within a fixed limit. |
| `tribunal` | Opposing sides submit independently and are frozen before they see each other; the host check gives the verdict. |
| `research_cell` | A deep researcher plans obligations, coders build checkers and witnesses, an adversary searches for countermodels; nothing is accepted without the host check. |

Three rules hold in every pattern:

1. **Freeze before sharing.** Guidance, submissions and stage outputs are
   hashed before another agent reads them.
2. **Isolation where independence is claimed.** Parallel solvers and tribunal
   sides never see each other's replies before they are frozen.
3. **Only the host accepts.** Agents propose; the check decides. An agent's
   agreement with another agent is not evidence.

## 4. Boost

A boost is one bounded escalation after a failed host check:

- **Trigger**: a named failure (for example "local checks pass but the global
  check fails", or "two rejections in a row").
- **Action**: a stronger tier, usually Opus, receives the typed residual and
  the attempt history. It never receives the expected answer.
- **Limit**: a per-run count, often 1. Some families set 0, because
  escalating mid-campaign would break their comparison (WF22) or because the
  right response to the failure is to stop (WF18, WF23).
- **Accounting**: boost calls are charged like any other call and appear in
  the run's records.

A boost changes who proposes next, not what counts as success.

## 5. A run, end to end

1. Read the node: goal, host check, process, team.
2. Freeze the task, the checker version and the budget.
3. Run the team pattern; freeze every intermediate output.
4. Run the host check.
5. On failure, apply the boost if its trigger matches and its limit allows;
   otherwise stop with a typed record.
6. Keep inputs, raw replies, residuals, boost calls and the final check
   together so the run can be replayed.

## What this does not claim

The tier assignments are a starting design. They are not measurements of
which model is better at which role, and no WF6–WF23 team has been run.
The first useful test is one family (WF9 is the smallest) run with and
without its boost on the same items, with the costs recorded.
