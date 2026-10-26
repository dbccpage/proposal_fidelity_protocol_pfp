---
name: auto-review-skills
description: "Review skill quality and usage evidence; propose consolidation or archival via a reviewed PR."
invocation: discipline
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# auto-review-skills

AuthorityEffect: None.

## Review procedure

1. Run the canonical manifest audit in scripts/skills_audit.py and inspect
   the skill compiler's scoped regression evaluations. Compiler routing tests
   alone do not establish the effectiveness of a skill.
2. Read the existing skill_garden usage ledger, explicit transcript imports and
   AutoP artifact observations. State which hosts and invocation paths were observed.
3. Inspect overlap, broken references, conflicting rules and missing execution
   routes. Prefer consolidation into an existing parent package.
4. Use 30 days without observed activity as a review signal only when coverage
   over that period is known. Git modification time and reference counts are
   not invocation telemetry. Missing coverage means UNKNOWN.
5. Propose archival in a focused PR with explicit evidence and affected paths.
   Preserve `_shared`, `_templates`, `ooutwire` and skills named in live agent licences.
   Hard deletion still requires human retirement evidence.
6. On approved archival, synchronize the tracked host roster, regenerate affected
   indexes and verify that live agent licences and references still resolve.

The owner-approved AutoP implementation plan replaces automatic archival based
solely on edit recency with reviewed usage evidence. No archival occurs as a
side effect of a learning or maintenance run.
