---
name: aletheia-phantom-citation-auditor
description: "Use before obeying a cited governance document. Finds docs cited as live authority that do not exist on disk."
operad_source_colours: ["State", "Ledger"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# aletheia-phantom-citation-auditor

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_nous_aletheia`

## When to use

Before trusting any document that another document calls binding. A citation is
a claim about the estate, and an unchecked claim about the estate is how a rule
comes to be obeyed by nobody and questioned by no one.

## Inputs

- all `.agents/skills/*/SKILL.md`
- `omega_engine_operads/skills/_shared/**` and its `_manifest.json`
- `.agents/operad/skill_compiler/routes.yaml` in all four hosts
- `.../ooutwire/_docs/basis_registry.{md,json,yaml}`

## Protocol

1. Extract every path-shaped citation from each surface.
2. Resolve it against disk, honouring the section-relative forms documented in
   `test_claude_md_paths_resolve.py`.
3. For each unresolved citation, classify: renamed (a near-name resolves),
   moved (it resolves elsewhere), or phantom (nothing resolves).
4. Report. Never repair -- a phantom citation may mean the document is missing
   or that the citation was always wrong, and those have different remedies.

## Known findings this skill exists to keep visible

- `_shared/meta_skill_governance.md` is cited as live governance by
  `techne-sprint-retrospective/SKILL.md` and by
  `_shared/coda_gtla_paper_compliance.md`. It does not exist.
  `autoskill/references/historical_learnings.md` already records that it does
  not exist, and nothing gated on the observation.
- `_shared/security_refs.md` is advertised by `_shared/README.md`. Absent.
- `basis_registry.md` points all 27 declared domains at
  `.anomalon/cognition/universal_basis/`, a directory that does not exist; the
  real corpora live under `omega_engine_cognitive_operations/ooutwire/_docs/`.

## Terminals

`RESOLVED`, `RENAMED`, `MOVED`, `PHANTOM`. Disjoint by construction.

## Nonclaims

A resolved citation is not a correct one. This checks that a path exists, not
that the document at it says what the citer claims it says.
