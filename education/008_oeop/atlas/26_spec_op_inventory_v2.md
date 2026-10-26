---
documentation_contract: symbol-game-documentation/v1
title: "Specification: operad v2 op inventory (skills as small typed ops and anti-ops)"
kind: architecture-reference
status: IMPLEMENTED
authority_effect: "None"
source_paths:
  - omega_engine_operads/skill_operad/yaml/op_inventory.yaml
  - omega_engine_operads/skill_operad/skill_compiler/op_inventory.py
  - omega_engine_operads/skill_operad/domain/planar.py
  - omega_engine_operations/use_cases/cicd/pr_fast_gate.py
last_verified: 2026-10-07
---

# 26 Specification: operad v2 op inventory

**AuthorityEffect:** None. This chapter describes a typed inventory and its checker. Nothing here
executes a skill or grants an op authority.

## 1. Why

The v1 operad (`json/operad_signature.json`) registers each skill as one coarse operation (251
skills when this chapter was written; 232 operations, one per skill, at `201dc8d` on 2026-10-15), for example `glossa-claim-hygiene-linter : (Paper, Code) → Audit`. A swarm that wants
to apply part of a skill, or to put an anti-skill in front of one step, has nothing to wire to:
the steps exist only as prose in `SKILL.md`, and an LLM picks and composes them out of sight.

Operad v2 refines a skill into small ops with typed ports, wired as a planar tree, plus anti-ops
that guard one input slot of one op. This is the data a run-time resolver needs (reform 6 of
[chapter 25](25_review_agent_setup.md)): Woland seats and `/research` can then ask which ops take
a given port, and compose them with a type check instead of a guess.

## 2. The inventory

`skill_operad/yaml/op_inventory.yaml`, schema `omega.oewas.op_inventory.v2`, typed by the
Pydantic models in `skill_compiler/op_inventory.py` (`OpInventory`, `SkillDecomposition`,
`OpSpec`, `AntiOpSpec`, `Wire`; all frozen, unknown keys refused).

| Field | Meaning |
|---|---|
| `subcolours` | Declared refinements of the ten admitted colours, e.g. `Audit.hype_hits`. A port is a colour or a declared `Colour.subcolour`. |
| `ops[]` | `op_id`, `summary`, `inputs` (ports, in slot order), `output` (one port), optional `binding`. |
| `anti_ops[]` | `op_id`, `summary`, `guards` (an op), `slot`, `inspects` (that slot's port), `refusal` (the code it emits), optional `binding`. |
| `wiring` | A tree of `{op, args}`; a bare port string in `args` is an input leaf. |
| `binding` | `path::symbol` of existing code. With a binding an op is **BOUND**; without one it is **PROSE**. |

Example (`techne-silent-failure-hunter`, coarse `(Code) → Audit`):

```yaml
ops:
  - op_id: sfh.scan          # Code -> Audit.sfh_findings, BOUND to silent_failure_hunter.py::scan_file
  - op_id: sfh.report        # Audit.sfh_findings -> Audit, BOUND to ::run_silent_failure_hunt
anti_ops:
  - op_id: sfh.refuse_bare_except   # guards sfh.scan slot 0 (Code), refusal SFH-PY-001
wiring: {op: sfh.report, args: [{op: sfh.scan, args: [Code]}]}
```

## 3. Checks

`python -m omega_engine_operads.skill_operad.skill_compiler.op_inventory --repo-root .`

| Code | Fails when |
|---|---|
| `OI1_SCHEMA` | The file does not parse into the models (unknown key, missing field). |
| `OI2_PORT` | A port names a colour outside the admitted ten, or an undeclared subcolour. |
| `OI3_DUPLICATE_OP` | An op or anti-op id appears twice in the inventory. |
| `OI4_WIRING` | The wiring names an undeclared op, or a wire mismatches arity or port. The tree is built with `planar.formal_compose`, so `ArityMismatch` and `ColorMismatch` are the refusals. |
| `OI5_REFINES` | The tree's leaves, read as base colours, are not the coarse op's source colours in order, or its root is not the coarse target colour. |
| `OI6_UNUSED_OP` | A declared op is not in the wiring. |
| `OI7_ANTI_OP` | An anti-op guards an unknown op, a slot the op lacks, or a slot whose port differs from `inspects`. |
| `OI8_BINDING` | A binding's file is missing, or the symbol (`name` or `Class.method`) is not defined in it. |

Each check has a test that turns it red with a one-line mutation
(`skill_compiler/tests/test_op_inventory.py`). One case needs the refinement check: swapping the
two scanners under `glossa.merge_hits` type-checks (both yield `Audit.hype_hits`) but changes the
leaf order to `(Code, Paper)`, so only `OI5_REFINES` fires.

The fast PR gate runs the checker as `op-inventory` when a change touches the inventory, the v1
signature, the checker or `domain/planar.py`; otherwise it reports `NOT_CHECKED`.

## 4. The five pilots

| Skill | Coarse op | Ops | Anti-ops | BOUND |
|---|---|---|---|---|
| `glossa-claim-hygiene-linter` | (Paper, Code) → Audit | 5 | 1 | 0 |
| `techne-silent-failure-hunter` | (Code) → Audit | 2 | 3 | 5 |
| `governance-test-isolation` | (Code, State) → Receipt | 3 | 2 | 1 |
| `adversarial-receipt-audit` | (State, Audit) → Receipt | 3 | 2 | 0 |
| `meta-no-comments` | (Code, Audit) → Code | 2 | 0 | 2 |
| **Total** | | **15** | **8** | **8 of 23** |

The checker reports `5 skills, 15 ops, 8 anti-ops; 8 BOUND to code, 15 PROSE`. The PROSE count is
the work left before these skills can run without an LLM reading their text.

## 5. What the decomposition found

- **Hype-word scanning has no single owner.** At least five modules keep their own
  `FORBIDDEN_HYPE_WORDS` list (`omega_engine_operations/domain/claim_hygiene/constants.py`,
  `omega_engine_education/infrastructure/pfp/gate_evaluators.py`,
  `omega_engine_education/use_cases/media/scene_generator.py`,
  `omega_engine_governance/.../blackrod_active_interceptor.py`, and a paper verifier). The
  `glossa.scan_hype_*` ops stay PROSE until one scanner is chosen and the others call it.
- **`techne-silent-failure-hunter` is fully bound.** Its five rules already live in
  `omega_engine_operations/use_cases/verification/silent_failure_hunter.py`; the skill text can
  shrink to a pointer once a resolver runs the ops.
- **`governance-test-isolation`'s script has a side effect.** `scripts/check_test_isolation.py`
  creates `scratch/` while checking for it, so `gti.layout_check` is left PROSE rather than bound
  to it.
- **`adversarial-receipt-audit` is all prose.** Its two refusals exist as catalogue entries in
  `omega_engine_research_papers/domain/models/anti_skills.py`, not as detectors.
- **The skill_operad test suite is red on `main` for reasons outside this slice:**
  `test_nonzero_obstruction_operad_refusal.py` needs `networkx`; three `test_operad_compression.py`
  tests need a Woland run directory that is not in the tree; `test_honesty.py` finds eight
  signature rows claiming `residual_effect: contractive` without a certificate. At `201dc8d`
  (2026-10-15) the same check reports 26 residual-honesty errors: 13 signature rows and 13 SKILL.md
  frontmatter fields that claim `contractive` without an independently verified certificate.
  `test_honesty.py::ResidualHonestyLive` fails on them, and `validate_operad.py` exits 1 with
  `[FAIL] Validation completed with 26 errors.`

## 6. What this does not do yet

- The inventory runs nothing itself. `skill_term` builds the typed tree with stub bodies; the
  resolver in [chapter 27](27_spec_op_resolver.md) composes and runs trees through executors that
  host code registers by op id. A binding names the code that implements a step; it is not a call
  signature.
- Anti-ops gate a run only in that resolver. The existing `AntiMorphism`
  (`skill_operad/domain/antibodies.py`) and `AntiSkillSpecV2` are not yet connected to it.
- Only five skills are refined (of 251 then; of 232 at `201dc8d`), and only one of them,
  `techne-silent-failure-hunter`, has host executors. The v1 signature stays the registry of record; the
  inventory refines it and is checked against it.
