# Operads

[`operads/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads)
owns **capability definitions and typed composition**: what each operation
accepts and returns, and which operations may be plugged into which. It does not
run workflows; it produces candidate plans that something else must admit.

## The idea

An operation has typed input slots and one output. A workflow is a tree of
operation occurrences in which each child's output fills one of its parent's
input slots. Two ports fit only if they agree exactly on colour, schema
reference, schema digest, validator reference and validator digest.

Composition yields an **unadmitted candidate** with no authority. A type graph
that fits together is not evidence that the composed workflow behaves
correctly.

## Typed workflows (v1)

A workflow declaration lists `nodes` (occurrences pinned to a source digest and
an operation digest), `bindings` (which child fills which parent slot), a
`root_node_id`, and its free `inputs` in left-to-right order.

The first compiler accepts only a rooted, acyclic, single-consumer tree. It
refuses:

- shared producers (fan-out), because it is unclear whether a shared step runs
  once or is repeated, and silently duplicating effectful work is unsafe;
- cycles, duplicate ids, missing nodes, stale pins and port mismatches.

Allowed effects and tools default to empty and must be granted explicitly on the
command line. See
[`typed_workflow_v1.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/documentation/typed_workflow_v1.md).

## Main areas

| Folder | Role |
| --- | --- |
| `domain/operad/`, `application/operad/` | Operations, typed workflows and their compiler |
| `catalog/`, `contracts/` | Capability catalog and wire contracts |
| `skills/`, `skill_operad/` | Skill documents compiled into typed operations |
| `domain/anti_skills/`, `application/anti_skill_admission/` | Patterns to avoid, and how one is admitted |
| `domain/skill_garden/`, `application/autopoiesis/` | Harvesting, pruning and archiving skills over time |
| `application/ddc_execution/` | The bounded code-repair example from Paper 028 |
| `governance/`, `rules/`, `hooks/` | Instruction admission, the rule register and host hooks |
| `frontend/cli/` | Command lines for operads, skills and the repair example |

## A governing principle

Markdown rules are specification, not enforcement. A gate exists only once it
is implemented in tested code and its result is recorded as a receipt. Citing a
rule is not verification.

Related papers: [025](Paper-025.md), [027](Paper-027.md), [028](Paper-028.md).
