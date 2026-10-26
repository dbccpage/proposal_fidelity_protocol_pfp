---
name: episteme-clonal-affinity-maturation
description: "Mutate and decay detector rules and anti-skills over time to keep prompt context from bloating."
families: [oecog, immune]
operad_source_colours: ["Ledger", "Code"]
operad_target_colour: "State"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-clonal-affinity-maturation

**Status:** `CANDIDATE`  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_episteme`

## When to use

Use to maintain the active repertoire of detector rules, anti-skills, and prompt governors.
Provides two lifecycle mechanisms:
1. Clonal Maturation: High-affinity rules encountering genuine pathogens spawn targeted mutations.
2. Half-Life Decay: Stale rules unreinforced by active defects evaporate from hot prompt windows.

## Inputs

- `repertoire`: Current active sequence of `DetectorRule` objects.
- `stimulation_events`: Observed pathogen encounters triggering affinity updates.
- `elapsed_runs`: Number of execution cycles since last stimulation.

## Protocol

1. **Pathogen Stimulation**:
   - For rules that successfully detected a corroborated pathogen: increment `affinity_score`,
     reset `runs_idle = 0`.
2. **Somatic Hypermutation**:
   - For top quartile rules, derive syntax-preserving mutation variants (whitespace tolerance,
     prefix wildcards) to broaden protective envelope.
3. **Half-Life Decay**:
   - Increment `runs_idle` for all unstimulated rules.
   - If `runs_idle >= half_life_runs`, deactivate (`is_active = False`) and archive to cold storage.

## References

- Biological and mathematical dynamics: [`references/clonal_decay_dynamics.md`](references/clonal_decay_dynamics.md)

## Nonclaims

Simulated clonal selection and half-life decay manage computational token budgets.
They do not guarantee that an archived rule will never be needed again in future runs.
