---
name: techne-shared-corpus-custodian
description: "Use when touching _shared or _templates. Checks naming, size budgets, citations, dangling refs and parity."
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# techne-shared-corpus-custodian

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_techne`

## When to use

Before and after any change to `omega_engine_operads/skills/_shared/` or `_templates/`, and
whenever a skill adds a citation into either.

## Inputs

- `omega_engine_operads/skills/_shared/**` and `_templates/**`
- `omega_engine_operads/skills/_shared/_manifest.json`
- `.agents/operad/skill_compiler/routes.yaml` (across host roots)

## Protocol

Drive `_shared/verify_shared_standard.py` and act on what it reports.

1. Every file declares a `kind` and `authority_effect: None`, in frontmatter
   **and** in the manifest, and the two must agree.
2. One naming convention: `lower_snake_case`, `README.md` exempt by declaration.
3. Budgets: bytes bound every budgeted kind; lines bound only `note` and
   `checklist`, because a scaffold is many short lines by construction.
4. A `historical` file may not be cited as live law.
5. Every `routes.yaml` target resolves -- this is what makes a rename safe.
6. `_shared` and `_templates` byte-identical across four hosts.

## The distinction this custodian exists to protect

`gate` and `tool` are different kinds. `verify_skill_names.py` has a `--fix`
mode that rewrites the files it inspects, so it is a tool: something that can
mutate its own subject is not evidence about that subject. A gate here is
read-only, and `verify_shared_standard.py` has no repair mode deliberately --
the same reason `skill_budget_census.render_baseline` was never wired to
`--update`.

## Standing debt, recorded not hidden

- Three laws exceed 20 KB (41 KB, 39 KB, 28 KB) and belong under `_shared/laws/`
  beside anchor indexes.
- **48 of 49 citations name a whole file rather than a section.** A citing skill
  pulls the entire document into hot context. This is the largest context leak
  in the garden and is currently a warning, because erroring on it would block
  every commit.
- `historical_pr_immunity_campaign.md` is classified `law` while being shaped
  like a finished campaign report, because it is the live target of a route.
  Reclassifying it requires unwiring the route first.

## Terminals

`CLEAN`, `UNDECLARED`, `DRIFT`, `BUDGET_EXCEEDED`, `DANGLING_ROUTE_TARGET`.

## Nonclaims

A conforming library is not a correct one. This checks shape, declaration, and
reachability -- never whether a law says the right thing.
