---
documentation_contract: symbol-game-documentation/v1
title: "Specification: the planar op resolver and native execution plan"
kind: architecture-reference
status: IMPLEMENTED
authority_effect: "None"
source_paths:
  - operads/skill_operad/resolver/resolver.py
  - operads/skill_operad/resolver/native_runtime.py
  - engine/crates_rs/core_workflows_agents_skills/src/operad_runtime.rs
  - operads/skill_operad/resolver/executors.py
  - operads/skill_operad/yaml/op_inventory.yaml
last_verified: 2026-10-15
---

# 27 Specification: the planar op resolver

**AuthorityEffect:** None. Checked terms authorize only their explicitly supplied
executors. A successful finite run is neither a mathematical theorem nor an
admission decision for a new learned detector.

## 1. Current boundary

The v3 inventory has typed `host` and `pfp_turn` bindings; the v2 reader remains.
The existing Rust workflow action validates terms through `core_operad_theory`
and emits an ordered execution plan. `run_native` dispatches that plan through
explicit host callbacks. It does not call the Python tree interpreter. The
Python `run` function remains the differential oracle.

Identity is a structural input leaf. A name resembling an identity does not
remove an operation. Inputs are ordered occurrences, including repeated colours;
repeated colours require an ordered value sequence rather than a colour-keyed
map. Tuple-valued outputs remain one slot value. Residuals accumulate once.

Nested substitution uses zero-based slots:
`(A compose_i B) compose_(i+j) C = A compose_i (B compose_j C)`.
Independent-slot interchange has a separate reindexing law. This path is planar;
it does not generate permutations or automatic symmetric closure.

## 2. Compose and run

Run from the repository root with the project dependencies installed:

```text
python -m operads.skill_operad.skill_compiler.op_inventory
python -m operads.skill_operad.resolver.resolver compose --inputs Paper,Code --goal Audit --max-ops 4
python -m operads.skill_operad.resolver.resolver run --skill techne-silent-failure-hunter --input 'Code=["path/to/file.py"]'
```

The run command requires the existing native Symbol Game host (set
`CORE_SYMBOL_GAME_HOST` to the built executable). Composition searches bounded
well-typed trees, chooses the fewest operations and breaks ties by serialized
wire order. It reports ordered leaves, unused inputs and guards. `--bound-only`
filters declared bindings; registration coverage is reported separately.

For repeated colours and injected PFP executors, use the existing Python port:

```python
from operads.skill_operad.resolver.native_runtime import run_native

result = run_native(inventory, wire, ordered_values, executors, detectors)
print(result.to_json())
```

All operation registrations and guard slots are checked before effects. Unknown
operations, missing executors, ill-typed terms, missing input occurrences and
unbound typed anti-skills refuse before dispatch. Executor and detector failures
become typed refusals; unavailable detectors do not count as cleared guards.

## 3. Executable coverage and evidence

The bounded host catalog currently supplies 15 operations and eight guards
across five skills: silent-failure hunting, claim-hygiene scanning, test isolation,
source-byte audit and comment-purge proposals. Their outputs state their scope.
The purge adapter checks Python AST preservation and needs a bound clean audit;
it does not silently rewrite source files or claim native-language support.
Source equality is not semantic verification. Unimplemented meta-operations
return `NOT_EXECUTABLE`; declarations are not counted as executed work.

The v2 run record binds input and inventory digests, interpreter version, native
term and plan, operation provenance, per-step inputs and outputs, guard events,
and available execution accounting. Unknown usage/cost remains explicit.
Digests use the named Python sorted-JSON profile, not a claim of RFC 8785.
Historical records and inventory versions retain their original bytes.

`PfpTurnExecutor` reuses PFP preparation, transport and reply checking. It checks
the exact turn binding and actual reply bytes; cached accepted verdicts are not
admission state. Role/version, lineage, operation, actual model, usage, cost and
verdict travel in the execution record. A missing transport is unavailable.

## 4. Adversary and research routes

Every new full-22 Panel step has a checked operation term before preparation
or dispatch. The shared Python/IDE backend carries operation and guard identity
through actions and records only actual execution. Existing research skill
packages resolve stage routes. Declared metadata routes without an executor
remain explicitly unavailable. Older Panel plans remain readable.

The pilot's A5 arm executes a native three-operation PFP/check/report tree.
Composition answers come from the model: the composer remains checker-side.
The existing Treg and OEEIS owners handle optional learned-detector regulation;
independent benign checks are required and mandatory task/budget/provenance
checks cannot be suspended.

## 5. Focused verification

The sole resolver test owner is
`operads/skill_operad/resolver/tests/`.
The byte-identical duplicate under Operations was removed. Focused controls
cover identity, repeated colours, substitution, tuple values, residual counting,
exceptions, guard slots, source binding, historical readers and all five bounded
adapters. Native/Python tests compare interfaces, trees and values over explicit
finite depth-three cases, including a poisoned-Python-oracle control proving
native dispatch does not delegate tree execution to the oracle.

The tests are finite evidence. They do not establish every law for arbitrary
host functions or all possible workflow trees. Frozen pilot artifacts are
excluded from collection and new test output goes to temporary directories.

## 6. Practical limits

The composer is a bounded search for a small inventory. Host effects remain
explicit callbacks; Rust determines the admitted term and execution order.
The CLI prints records, leaving retention to the caller. Structured output does
not establish answer correctness. Model/provider failures and unknown accounting
remain visible; no fallback or retry is inferred from a failed request.

See [OEWAS-012](../../../../product_planning_office/plans/epics/oewas/epic_oe_oewas_012_adversary_operad_binding_and_management_ladder_pilot_plan.md)
for the bounded experiment and the external MUB owner. The new management ladder
preserves v1 and distinguishes storage compression from provider-token savings.
