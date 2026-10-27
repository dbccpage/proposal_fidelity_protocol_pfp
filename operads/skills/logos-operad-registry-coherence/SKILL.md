---
name: logos-operad-registry-coherence
description: "Use before registering a skill. Checks frontmatter, operad signature, capability slices and prose agree."
operad_source_colours: ["Contract", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# logos-operad-registry-coherence

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L2_logos`

## When to use

Before a skill is registered, before an agent is licensed to use one, and
whenever an agent's prose lists capabilities its slice does not grant.

## Inputs

- all `.agents/skills/*/SKILL.md` frontmatter
- `.agents/skill_operads/operad_signature.json`
- `.agents/skill_operads/agent_capability_slices.json`
- Current Adversary Panel role declarations and typed package contracts; standalone agent manifests are retired.

## Protocol

1. Compare the manifest colours of each skill against its registry entry
   (`REGISTRY_SIGNATURE_DRIFT`).
2. For each agent, check every licensed skill's colours lie inside that agent's
   `sub_operad` (`CAPABILITY_ESCAPE`).
3. Compare each agent's body prose against its JSON slice, both directions.
4. Emit a coherence receipt. Repair nothing: three of these four files have
   different owners.

## Historical findings (pre-retirement; not current agent census)

- **Six of 39 agents drift** between body prose and slice. `meekers.md` claims
  six licensed `ow-*` skills in prose; the JSON grants zero.
- `nous-council.md` claims `dianoia-dime`, whose target colour `Diagram` is
  outside nous's `sub_operad` of `{Ledger, Paper, Post, Proof}`. **Syncing the
  JSON to the prose would fire `CAPABILITY_ESCAPE` immediately** -- the prose is
  what is wrong, and the obvious repair direction is the destructive one.
- Six agents declare an `operad_*` colour in their own frontmatter that escapes
  their slice; nothing checks agent frontmatter against the slice at all.

## Boundary with `operad-quotient-verifier`

That skill owns term validity -- arity, colours, planar substitution. This one
owns cross-file agreement and delegates every term question to it.

## Terminals

`COHERENT`, `REGISTRY_SIGNATURE_DRIFT`, `CAPABILITY_ESCAPE`, `PROSE_JSON_DRIFT`.

## Nonclaims

Coherence is not correctness. Four files can agree perfectly on a colouring that
is wrong for the skill.
