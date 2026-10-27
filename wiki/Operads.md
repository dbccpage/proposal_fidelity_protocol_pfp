# Operads

[`operads/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads)
owns **capability definitions and typed composition**: what each operation
accepts and returns, and which operations may be plugged into which. It does not
run workflows; it produces candidate plans that something else must admit.

Operads sit at the centre of PFP together with **rewriting** and
**packetization**. A prompt is built as an operad tree, the tree is rewritten
under declared rules, and the result is sealed into content-addressed packets
that a host can check and replay. This section explains each step and how the
code enforces it.

```text
  prompts            rewriting               packetization
  (operad trees) ──▶ (declared rules, ──────▶ (sealed, hashed
                      typed refusals)          envelopes)
        │                   │                        │
        └──── every stage carries AuthorityEffect: None and a receipt ────┘
                                    │
                                    ▼
                        host check, then a separate decision
```

The order "prompts, then rewriting, then packetization" is written into the code
as `PipelineStage` in
[`pfp/domain/rewriting/prompt_containment.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/rewriting/prompt_containment.py).

## Pages in this section

| Page | Read it to... |
| --- | --- |
| [Operad primer](Operads-Primer.md) | Learn coloured operads from scratch: colours, operations, partial composition, units and the two associativity laws, with worked examples from the code |
| [Prompts as operad trees](Operads-Prompt-Trees.md) | See how a prompt becomes a tree of typed text spans, why one bad leaf collapses the whole tree to `NullTree`, and how constructive, interrogative and repair operations are kept apart |
| [Rewriting and packetization](Operads-Rewriting-and-Packetization.md) | Follow a prompt from tree to rewrite to sealed packet, and see where the host checks each step |
| [Typed workflows](Operads-Typed-Workflows.md) | Read the v1 workflow contract: nodes, bindings, the five-field port check, the refusal codes and the substitution laws |
| [Skills, op inventory and the resolver](Operads-Skills-and-Catalog.md) | See how skill documents compile into operations, how they are refined into small ops and guarded by anti-ops, and how the resolver composes a plan |
| [Bounded repair (C, R, E, I, M, T)](Operads-Bounded-Repair.md) | Walk through the six-operation code-repair example of Paper 028 |
| [Local checks, global compatibility](Operads-Local-to-Global.md) | Understand why parts that fit and pass locally can still fail together (Paper 025), and what typed composition does not prove |
| [Operad type inventory](Operads-Type-Inventory.md) | Look up every kind of operad thing the code defines (colours, DDC letters, skills and anti-skills, rules, helpful and anti-patterns, antibodies, agents, operands and spans), with counts, locations, duplicates and what does not exist |

## Three ideas to hold on to

1. **Fitting is not working.** Two operations whose types match can be plugged
   together, but that says nothing about whether the composite does the right
   thing. Composition yields an **unadmitted candidate** with no authority.
2. **Refuse, do not repair silently.** An unknown colour, a stale pin, a
   mismatched port or a malformed span is refused with a typed code. The code
   never "fixes" a declaration so that a compile passes.
3. **Markdown rules are specification, not enforcement.** A gate exists only
   once it is implemented in tested code and its result is recorded as a
   receipt. Citing a rule is not verification.

## Main areas of the code

| Folder | Role |
| --- | --- |
| `domain/operad/`, `application/operad/` | Colours, operations, the coloured operad, planar trees and the skill compiler |
| `contracts/`, `domain/entities/`, `application/typed_workflow_compiler.py` | Typed workflow and operation wire contracts and their compiler |
| `domain/prompt_hierarchy/` | Prompt addresses, prompt-to-operation bindings and prompt gate receipts |
| `catalog/` | The capability catalog and canonical typed lessons (rules, patterns, anti-patterns, antibodies) |
| `skills/`, `skill_operad/` | Skill documents, the op inventory, the resolver and the skill compiler gates |
| `domain/anti_skills/`, `application/anti_skill_admission/` | Patterns to avoid, and how one is admitted |
| `domain/skill_garden/`, `application/autopoiesis/` | Harvesting, pruning and archiving skills over time |
| `domain/ddc_execution/`, `application/ddc_execution/` | The bounded code-repair example |
| `governance/`, `rules/`, `hooks/` | Instruction admission, the rule register and host hooks |
| `frontend/cli/` | Command lines for operads, skills and the repair example |

The operad also has a native Rust kernel; the Python code is the reference
interpreter and calls the native port where one exists.

## Related reading

- [Rewriting](Rewriting.md): the rewriting section, from the four-glyph baseline
  up to PFP and the deformation calculus.
- [Core concepts](Core-Concepts.md): packets, obstruction, retraction and
  receipts.
- Papers [025](Paper-025.md), [027](Paper-027.md) and [028](Paper-028.md).
