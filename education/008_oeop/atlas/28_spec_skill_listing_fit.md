---
documentation_contract: symbol-game-documentation/v1
title: "Specification: fitting the skill listing in its budget"
kind: architecture-reference
status: IMPLEMENTED
authority_effect: "None"
source_paths:
  - operads/skill_operad/skill_compiler/skill_listing.py
  - operads/skill_operad/skill_compiler/tests/test_skill_listing.py
  - operations/use_cases/cicd/pr_fast_gate.py
  - .agents/skills
last_verified: 2026-10-07
---

# 28 Specification: fitting the skill listing in its budget

**AuthorityEffect:** None. A short description tells the model when a skill applies. It grants the
skill nothing.

## 1. Why

Claude Code shows the model each skill it may invoke as a name and a description, inside a fixed
budget of about 1% of context. Past the budget, skills are listed by name only.
[Chapter 25](25_review_agent_setup.md) finding F4 measured 251 skills carrying about 55.7 KB of
descriptions. Only the first 74 were listed with a description. `adversary`, `research`,
`deep-research` and every `techne-*` skill reached the model as a bare name, so the model could not
tell when to use them.

The goal of OEWAS is many small composable operations. That only works if the model can see what
each one is for. This is the first part of slice 4 in chapter 25 §7.

## 2. What changed

| Change | Count | Effect |
| --- | --- | --- |
| `disable-model-invocation: true` on the empty `ext-*` stubs | 19 | Not listed; still callable by name |
| Description rewritten to one line, trigger first, at most 120 B | 199 | The other 33 already fit |
| Capability catalog and operad signature regenerated | 2 files | Copies of the descriptions match |

The `ext-*` stubs are 457-byte placeholders whose description is "Operad operation <name>". They
have no instructions, so listing them spent budget and told the model nothing.

| Measure (YAML parse of `.agents/skills/*/SKILL.md`) | Before (`d59d82d43`) | After |
| --- | --- | --- |
| Skills listed to the model | 251 | 232 |
| Description bytes | 55,181 | 24,292 |
| Names plus descriptions | 61,962 | 30,507 |
| Longest description | 629 B | 120 B |

In a 1M-token session the refreshed listing showed every repo skill with its description.

## 3. The gate

`skill_listing.py` checks three things and exits 1 on any failure:

1. every model-invocable skill has a one-line, non-empty description of at most 120 B;
2. the names plus descriptions of model-invocable skills sum to at most `LISTING_BUDGET_BYTES`
   (32,000 B: the measured 30,507 B plus about 5% headroom);
3. the tracked `capability_catalog.v1.json` and `operad_signature.json` match a fresh compile, so a
   description edit cannot leave its copies stale.

The budget is a ratchet. Lower it when the listing shrinks. Raising it needs a reason in the PR,
because each byte over the real budget pushes some skill back to name only.

```text
python -m operads.skill_operad.skill_compiler.skill_listing --repo-root .
```

`pr_fast_gate.py` runs it as `skill-listing` when a change touches a `SKILL.md` in any host mirror,
either catalog JSON, the gate itself, or the catalog compiler.

## 4. Tests

`test_skill_listing.py` covers the live tree, the 19 hidden stubs, the cap in bytes (not
characters), empty and multi-line descriptions, the budget sum, the exemption for hidden skills, and
a red mutation: one byte inserted into a copied catalog must be refused as `HOST_PROJECTION_DRIFT`.
A further test keeps the budget within 10% of the tree, so the ratchet cannot drift loose.
`test_pr_fast_gate.py` covers the trigger paths and the gate's wiring.

## 5. What this does not do yet

- **Duplicates.** Six prefix pairs and six `goo-*` skills overlap. Merging them changes callers, so
  it is its own PR.
- **Op binding.** A short description helps the model choose a skill. Slice 10 lets `/research` and
  Adversary seats choose ops through the resolver instead ([chapter 27](27_spec_op_resolver.md)).
