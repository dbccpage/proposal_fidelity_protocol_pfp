---
name: techne-code-lean4-anti-patterns
description: "Audit Lean 4 sources for sorry claims, unconstrained Lake rebuilds, and unhedged limit assertions."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: neutral
families: [techne, quality, lean4]
---

# Techne Code Lean 4 Anti-Patterns

**Status:** canonical-candidate
**AuthorityEffect:** None

Specialist skill for the Lean 4 catalog at `operads/patterns/anti/lean4/`. OEAUTOP calls this package on every run.

## Canonical Anti-Patterns

| ID | Anti-Pattern | Hazard | Dual Healthy Pattern |
|---|---|---|---|
| `AP_LN_001` | Unmechanized `sorry` in Lean source | A proof claim that the kernel did not check | [`HP_LN_001`](../../patterns/helpful/lean4/HP_LN_001_zero_sorry_axiom_allowlist.md) |
| `AP_LN_002` | `lake build` or `lake update` without `lake exe cache get` in the same shell script | Uncached Mathlib rebuild | [`HP_LN_002`](../../patterns/helpful/lean4/HP_LN_002_scoped_target_cache_build.md) |
| `AP_LN_003` | `theorem` naming `thermodynamic_limit` without a finite envelope on that line | Unhedged infinite-limit claim | [`HP_LN_003`](../../patterns/helpful/lean4/HP_LN_003_finite_difference_envelope.md) |

`sorry` inside a `--` comment or a `/- -/` block is not `AP_LN_001`.

## Auditor

```bash
py -3.12 operads/skills/techne-code-lean4-anti-patterns/scripts/lean4_anti_pattern_auditor.py --path . --check
py -3.12 operads/skills/techne-code-lean4-anti-patterns/scripts/lean4_anti_pattern_auditor.py --path . --report-out runs/lean4_anti_pattern_receipt.json
```

`--check` exits 1 when any finding is present. AuthorityEffect stays None.

## Integration

[`auto-oe-autop`](../auto-oe-autop/SKILL.md) calls this skill with the other `*anti-pattern*` packages. [`auto-code-anti-pattern-hunter`](../auto-code-anti-pattern-hunter/SKILL.md) names it as the Lean 4 specialist.
