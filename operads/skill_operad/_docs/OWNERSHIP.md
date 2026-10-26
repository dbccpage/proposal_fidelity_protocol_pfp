# Ownership -- `skill_operad/` executable tree

> **HISTORICAL.** `.agents/operad/` is absent. The executable tree is `omega_engine_operads/skill_operad/`. See [chapter 23](../../../omega_engine_education/documentation/008_oewas/atlas/23_plan_oewas_consolidation_oeeis_and_demo_integration.md).

**AuthorityEffect: None.**

The executable operad tree is `skill_operad/` inside `omega_engine_operads`. `.agents/operad/` is a historical path and is not on this tree.

## Current ownership boundary (this package)

| Concept | Owner |
| --- | --- |
| Coloured planar multicategory (executable substitution) | `domain/planar.py` |
| Strict typed symbolic aggregate for new code | `domain/operad.py` |
| Historical JSON-backed registry and capability API | root `coloured_operad.py` (compatibility implementation; not yet API-equivalent to `domain/operad.py`) |
| Result / ROP monad | `domain/errors.py` (`Ok`/`Err`, aliases `Success`/`Failure`) |
| Residual monoid | `domain/evidence.py` |
| AntiMorphism and common AST/pullback antibodies | `domain/antibodies.py`; root `antibodies.py` retains legacy property/differential adapters |
| HoTT-lite path metaphors for new package imports | `domain/hott.py`; root `hott.py` remains a legacy compatibility implementation |

Root `coloured_operad.py` owns the executable skill constructors and
implements the historical JSON registry API because the stricter
`domain/operad.py` aggregate is not API-equivalent. Prefer `from domain import ...`
in new code; do not claim the two registry APIs have been quotiented or collapsed.

Correct mathematical name of the structure in use: **coloured non-symmetric multicategory** (planar / ordered slots). No skill is equivariant; symmetric-group scaffolding is unused.

## Separate surfaces (do not merge)

| Surface | Job |
| --- | --- |
| `omega_engine/crates/homotopy_type_theory/` | Engine formal library (identity, truncation, quasi-category, A∞ sketches, ...) |
| `skill_operad/` | Skill multicategory typing, residual honesty, dispatch, antibody duals. This is the executable tree. |

When application code needs formal math, depend on the engine math crates. Do not re-implement identity types, univalence, or higher inductive types inside `skill_operad/`.

## Residual policy

Default `operad_residual: unknown`. Identity units may be `exact`. `contractive` only with an independent certificate path (not from `evidence_trace.json` scalars). See `SEMANTICS_MAP.md` Honest limits and `residual_honesty.py`.

Claims and unverified obligations remain distinct fields in the shared residual
carrier. Compatibility aliases never promote an obligation into a claim.

The alternate-spelling `colored_operad.py` and forwarding `hott_lite.py` and
`dda_trace_logger.py` modules are retired. Import `coloured_operad`, `hott`,
and `ddc_trace_logger` directly. DTO models live in `oeop_dto_schemas.py`;
existing WAS model names and wire schema identifiers are unchanged.
