# Skills, op inventory and the resolver

Part of [Operads](Operads.md). Previous: [Typed workflows](Operads-Typed-Workflows.md) · Next: [Bounded repair](Operads-Bounded-Repair.md)

A **skill** is a Markdown package an agent host can load, such as
`operads/skills/adversarial-receipt-audit/SKILL.md`. The operads package treats
each skill as an operation with a colour signature, then refines skills into
smaller typed ops that can be composed, guarded and run by host code.

## Skills become operations

A skill declares its signature in YAML frontmatter:

```yaml
---
name: adversarial-receipt-audit
description: "Audit receipts adversarially ..."
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---
```

`OperadCompilerService.compile_skills_garden` (in
`application/operad/compiler_service.py`) reads every `SKILL.md`, in sorted
order so receipts do not depend on directory order, and adds each one to a
`ColouredOperad`. A skill is **refused**, never repaired, when:

| Code | Cause |
| --- | --- |
| `UNREADABLE_SKILL_FILE` | The file cannot be read as UTF-8 |
| `MISSING_FRONTMATTER`, `FRONTMATTER_YAML_ERROR`, `FRONTMATTER_NOT_A_MAPPING` | No valid frontmatter block |
| `SOURCE_COLOURS_NOT_A_LIST` | Inputs are not a list |
| `UNADMITTED_TARGET_COLOUR`, `UNADMITTED_SOURCE_COLOUR` | A colour outside the admitted ten |
| `DUPLICATE_OPERATION_ID` | A second skill declares a name already taken |
| `OPERATION_NOT_ADMITTED` | The operad itself refused the operation |

Every refusal is written into the compile receipt, and **a single refusal fails
the compile**. An earlier version dropped unknown colours and defaulted an
unknown target to `Receipt`; that silently changed arities and outputs while
still reporting success. Refusing at the cause trades a silent repair for a
visible one.

A separate budget gate (`budget_service.py`) keeps each `SKILL.md` within 300
lines and 20,480 bytes, so skills stay small enough to load into a model's
context.

## The op inventory: refining a skill into small ops

The v1 operad registers each skill as one coarse operation. The v2
**op inventory** (`skill_operad/yaml/op_inventory.yaml`) breaks a skill into
ops with one output each, wired as a planar tree, plus **anti-ops** that guard
one input slot of one op:

```yaml
- skill_id: techne-silent-failure-hunter
  ops:
  - op_id: sfh.scan
    inputs: [Code]
    output: Audit.sfh_findings          # a declared subcolour of Audit
    binding: { kind: host, target: .../executors.py::_scan }
  - op_id: sfh.report
    inputs: [Audit.sfh_findings]
    output: Audit
  anti_ops:
  - op_id: sfh.refuse_bare_except
    guards: sfh.scan
    slot: 0
    inspects: Code
    refusal: SFH-PY-001
```

`skill_compiler/op_inventory.py` checks the inventory with eight rules:

| Rule | Checks |
| --- | --- |
| `OI1_SCHEMA` | The file parses into the typed models |
| `OI2_PORT` | Every port is an admitted colour or a declared `Colour.subcolour` |
| `OI3_DUPLICATE_OP` | Op and anti-op ids are unique |
| `OI4_WIRING` | Every wire matches arity and port, by building the tree with the planar composer |
| `OI5_REFINES` | The tree's leaves, read as base colours, are the coarse skill's inputs in order, and its root is the coarse skill's output |
| `OI6_UNUSED_OP` | Every declared op appears in the wiring |
| `OI7_ANTI_OP` | An anti-op guards a declared op, at a slot it has, with that slot's port |
| `OI8_BINDING` | A binding names a tracked file and a symbol defined in it |

`OI5_REFINES` is the important one: the fine-grained tree must have exactly the
boundary the coarse skill promised, so refining a skill cannot change what it
consumes or produces.

## The resolver: compose, then run

`skill_operad/resolver/resolver.py` has two commands.

**`compose`** searches the op inventory for the **smallest** planar tree whose
leaves come from the given input ports and whose root is the goal port. Every
candidate is type-checked. It returns a composition or a typed refusal
(`UNKNOWN_PORT`, `NO_ADMISSIBLE_PATH`).

```text
python -m operads.skill_operad.resolver.resolver compose --inputs Paper,Code --goal Audit
```

**`run`** executes a wiring through executors and detectors that host code
registers by op id. It checks everything **before** executing anything:

1. the wiring types (`TYPE_MISMATCH`);
2. an executor for every op and a detector for every guarding anti-op
   (`NOT_EXECUTABLE`);
3. a value for every leaf (`MISSING_INPUT`).

While running, each anti-op inspects its slot before the op it guards; if it
fires, the run stops with the anti-op's refusal code. Only host code registers
executors: model output is data and cannot add one. A binding in the inventory
says which code implements a step; it is not a call signature, so nothing is
called through it. The Python `run` is the reference interpreter; runtime
callers use the native kernel through `native_runtime.py`.

## Where new learning goes

`skill_compiler/resolve.py` decides where a lesson or invariant belongs. The
dispositions run from cheapest to most expensive:

| Disposition | Meaning |
| --- | --- |
| `NOISE` | Discard; do not edit procedural memory |
| `EXISTING_OP` | Patch or route to an existing skill |
| `SHARED_CONTRACT` | Land once in a shared contract that skills cite |
| `CODE_GATE` | Prefer a deterministic checker over prose |
| `SKILL_PROSE` | A compressive edit to an existing skill |
| `NEW_SKILL` | Last resort, proposed only, never auto-admitted |

## Typed lessons

`catalog/contracts/v1/lessons/*.json` holds four kinds of canonical guidance,
compiled by `operads.infrastructure.typed_contract_compiler`:

| Kind | Must state |
| --- | --- |
| Rule | Trigger, predicate and response |
| Helpful pattern | Conditions, construction and an example |
| Anti-pattern | Failure, witness and repair |
| Antibody | A bound review prompt, an epitope, a required independent danger signal, and harmful and benign examples |

Each lesson cites a byte-bound repository source, and its quoted excerpt must
actually occur there. That validates attribution, not interpretation. A
generated antibody prompt is review guidance, not an activated detector:
activation stays with the [EIS](EIS.md) two-signal gate. The full specification
is [`typed_canonical_contracts_v1.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/documentation/typed_canonical_contracts_v1.md).

## Anti-skills and the operad supervisor

An **anti-skill** is a pattern to avoid, bound to an operation. Admission of
anti-skills in Python is retired: the old entry points return a typed
retirement refusal and active detector work lives in the native kernel.

`OperadTregSupervisor` (`domain/operad/treg.py`) watches anti-skills during
composition. If an anti-skill's independently checked false-suppression rate
reaches 2/5, once at least 3 suppressions have been observed, it is downgraded
to diagnostic only and a receipt records why. The sample floor stops a single
false positive from downgrading a blocking gate. A checked false positive must
come from a checker other than the anti-skill itself, with 64-hex digests for
the subject and the evidence; missing evidence never counts. The EIS has its
own regulation rules; see [Regulation and custody](EIS-Regulation-and-Custody.md).

## The skill garden

`domain/skill_garden/` and `application/autopoiesis/` harvest, prune and
archive skills. Culling produces **nominations** only: the garden module has no
filesystem or execution authority, and a nomination does not delete anything.
