# Typed workflows

Part of [Operads](Operads.md). Previous: [Rewriting and packetization](Operads-Rewriting-and-Packetization.md) · Next: [Skills, op inventory and the resolver](Operads-Skills-and-Catalog.md)

A **typed workflow** is a declared tree of operation occurrences. The v1
contract is specified in
[`typed_workflow_v1.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/documentation/typed_workflow_v1.md)
and compiled by `operads/application/typed_workflow_compiler.py`.

## The declaration

| Field | Meaning |
| --- | --- |
| `nodes` | Occurrences. Each has a unique `node_id`, an existing `operation_id`, and pins for the exact `source_digest` and `operation_digest`. Several nodes may use the same operation. |
| `bindings` | Child `source_node_id` fills parent `target_node_id` at the original `target_slot`. The slot is an exact non-negative integer, not a boolean. |
| `root_node_id` | The occurrence whose output is the workflow's output. Every other occurrence must reach it. |
| `inputs` | Every unbound `(node_id, slot)` exactly once, in the left-to-right planar order inferred from the root. A declaration cannot reorder its own boundary. |

Identifiers are bounded lowercase hyphenated names. Pins are `sha256:` followed
by 64 lowercase hex digits. An **occurrence** is not an alias for an operation:
two nodes running the same operation stay distinct all the way into the result.

The wire format is strict: duplicate keys, unknown fields and wrong types are
refused, while whitespace and key-order variations are accepted and normalised
to one canonical form (sorted keys, compact separators, ASCII escaping, one
trailing newline). The workflow digest binds the canonical meaning, not the
original formatting.

## The five-field port check

Two ports fit only if they agree exactly on all five of:

```text
colour · schema reference · schema digest · validator reference · validator digest
```

Display names are not part of the check, and colour alone is not enough: two
`Contract` ports with different schema digests do not fit. This closes a
transplant in which a foreign schema hides behind a matching colour.

## What the first compiler accepts

A rooted, acyclic, **single-consumer** tree: one producer per bound slot,
exactly one consumer for every non-root occurrence, nothing consuming the root,
nothing disconnected. Nullary operations are allowed and contribute no free
slots.

It **refuses fan-out** (one producer feeding two consumers). The generic graph
validator accepts diamonds, but it does not say whether a shared step runs
once, is copied, or is repeated, and silently duplicating effectful work is
unsafe. Shared-output policy is a separate, unimplemented obligation.

## Refusal codes

| Refused boundary | Code |
| --- | --- |
| Source or operation pin changed | `SOURCE_DIGEST_MISMATCH`, `OPERATION_DIGEST_MISMATCH` |
| Duplicate occurrence, missing root or missing declaration | `DUPLICATE_NODE_ID`, `ROOT_NODE_MISSING`, `OPERATION_MISSING` |
| Bad edge endpoint, slot out of range, or two producers for one slot | `BINDING_NODE_MISSING`, `SLOT_OUT_OF_BOUNDS`, `DUPLICATE_SLOT_BINDING` |
| Shared producer, disconnected occurrence, or wrong ordered inputs | `SHARED_OUTPUT_UNSUPPORTED`, `UNREACHABLE_NODE`, `ENTRY_BOUNDARY_MISMATCH` |
| Native graph says no, replies malformed, or is unavailable | `GRAPH_INVALID`, `GRAPH_RESULT_MALFORMED`, `GRAPH_VALIDATOR_UNAVAILABLE` |
| Full port or plan ceiling fails | the candidate compiler's `PlanRefusal` codes, such as `BOUNDARY_MISMATCH` |

The command line reports any of these as `TYPED_WORKFLOW_REFUSED` and exits
nonzero. The application checks the native report's overall `is_valid`: a list
of diagnostic stages in the report is never permission to execute.

## Substitution laws

The compiler's ordered boundary is checked against the two laws from the
[Operad primer](Operads-Primer.md):

```text
nested:    (θ ∘_i φ) ∘_(i+j) ψ  =  θ ∘_i (φ ∘_j ψ)
disjoint:  (θ ∘_i φ) ∘_(k + arity(φ) − 1) ψ  =  (θ ∘_k ψ) ∘_i φ      for i < k
```

The oracle is a hand-enumerated ordered boundary: the full five-field contracts
and root output, never a sorted multiset of colours, the arity alone or display
names. Equal boundaries do not establish that two workflows behave the same or
that their effects may be swapped.

## The worked example

`--emit-example` writes a fresh, currently pinned declaration:

```text
falsifier : (Contract) -> Audit
audit     : (Audit, Contract) -> Receipt

binding   : falsifier ──▶ audit, slot 0
free      : [(falsifier, 0), (audit, 1)]    two ordered Contract ports
order     : falsifier, then audit
```

It never rewrites an existing workflow to make stale pins pass.

```text
python -m operads.infrastructure.typed_workflow_compiler --repo-root . --emit-example
python -m operads.infrastructure.typed_workflow_compiler --repo-root . --workflow workflow.json \
    --allow-effect read_subject --allow-effect emit_finding
python -m operads.infrastructure.typed_workflow_compiler --repo-root . --show-schema
```

Allowed effects and tools default to **empty**. This example needs
`read_subject` and `emit_finding`; add `--allow-tool` only for an explicitly
permitted tool. Source declarations do not grant a licence.

## The result

The compiler returns `plan`, `workflow_digest`, `occurrence_order` and
`native_report`. The workflow digest binds the node and binding order, the
identities of workflow, root and occurrences, all pins, the ordered free
inputs and the plan digest. The candidate digest also commits the actual
instruction strings, so swapping in an instruction body of the same byte length
changes the digest.

The plan is an **unadmitted candidate** with `AuthorityEffect: None`. Compiling
performs no operation, provider call, scheduling or state change.

## Evidence grades kept apart

| Evidence | What it shows |
| --- | --- |
| Building and testing the source crate | That source crate's result |
| Calling the selected native host binary | That the host accepted these finite graphs. The output says `native_source_binding: not_attested_by_this_command`. |
| Compiling a workflow | That the declaration fits. Not that it runs, or runs correctly. |

None of these substitutes for another, and none establishes a general algebraic
claim.
