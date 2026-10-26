# Typed workflow occurrences v1

AuthorityEffect: None. [EPIC-OE-OEWAS-011 R2](../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_011_consolidated_residual_plan.md#r2-typed-workflow-and-native-composition) records the bounded Python/native contract and its remaining research boundaries. The [earlier integration verification receipt](../receipts/oewas_002_20261010/verification.json) remains limited to its original sources, commands and finite controls; it supplies no runtime approval for subsequent changes.

## Existing architecture and additive contract

[OperationV3](../domain/entities/operation_v3.py) and catalog-bound `SkillDocumentV3` sources remain authoritative operation declarations. [compile_candidate_plan](../application/woland_candidate_plan.py) owns exact port matching, ordered instruction compilation, source binding and existing caller ceilings. [ValidateWorkflowsHandler](../application/queries/validate_workflows.py) already delegates explicit generic node/edge topology to [native graph.rs](../../omega_engine/crates_rs/omega_operads/src/graph.rs). The typed workflow adapter connects these public ports; it does not create another catalog, substitution engine, graph algorithm or execution service.

The strict [wire model](../contracts/typed_workflow_v1.py) adapts to the [TypedWorkflowV1 domain entity](../domain/entities/typed_workflow.py). Its version is `oewas.typed-workflow.v1`; authority is None. Encoding reuses `oewas.sorted-ascii-json.v1`: sorted keys, compact separators, ASCII escaping, no NaN and one trailing LF. This Python JSON profile is not RFC 8785. Ingress is semantically strict: reject duplicate decoded keys, unknown fields and coercible wrong types. Valid JSON whitespace and key-order variations are accepted and normalized to canonical output; the workflow digest binds the canonical semantic declaration, not the original formatting. This instruction/workflow wire does not replace governance `omega.contract.v2` contracts.

| Field | Meaning and invariant |
| --- | --- |
| `nodes` | Unique nonempty occurrence `node_id`, existing `operation_id`, exact `source_digest` and `operation_digest`. Multiple nodes may reference the same operation declaration. |
| `bindings` | Child `source_node_id` supplies the parent `target_node_id` at ORIGINAL `target_slot`. The operation has one output; index is an exact nonnegative integer, not a boolean. |
| `root_node_id` | The occurrence whose output is the workflow output; every other occurrence reaches it. |
| `inputs` | Every unbound `(node_id, slot)` exactly once, in the left-to-right planar order inferred from the root and original slots. A declaration cannot independently reorder the external boundary. |

Workflow and occurrence identifiers remain bounded lowercase hyphenated names;
pins use `sha256:` plus 64 lowercase hexadecimal digits. Referenced operation
identifiers use the existing bounded `OperationId` contract, including legacy
dots, colons and underscores. Occurrence identity is never an operation alias.

The application checks source/operation pins against compiled `SkillDocumentV3` aggregates, snapshots those declarations before the injected graph callback, and does not attest raw-file correspondence. The CLI freshly obtains the canonical pair from the existing source compiler, which owns raw-file custody. Derive native graph port identifiers from input positions and the sole output; caller-provided port labels cannot hide an index collision or schema change. Lower an accepted graph to `PlanNodeV01` and call the existing candidate compiler. Preserve occurrence IDs and the graph binding in the workflow result alongside the candidate plan; do not collapse distinct occurrences into an operation-ID map.

## Supported graph and authority ceiling

The first typed compiler accepts a rooted acyclic single-consumer graph: one producer per bound input slot, exactly one consumer per non-root occurrence, no consumer of the root, no disconnected occurrences. Distinct node IDs may repeat an operation; a cycle concerns occurrence edges, not repeated operation names. Free slots become the ordered external input boundary. Nullary operations are legal and contribute no free slots.

Refuse fanout/shared producers in this typed subset. The existing generic native validator supports diamond topology; it does not say whether a shared producer runs once, copies an output, or repeats instructions. `PlanNodeV01` expands a shared child once per occurrence/edge. This adapter must not silently turn a diamond into duplicated effectful work. Multiple producers for one slot, duplicate IDs, missing nodes, cycles, stale pins and full-port mismatches also refuse.

A bound port agrees on exactly colour, schema reference, schema digest, validator reference and validator digest. Port display names are not part of that existing five-field contract; original slot positions retain ordering. The application must check the entire native report's `is_valid`, since native diagnostic stages may be present even when colour/port findings make the report invalid. A stage list alone is never permission to execute.

Compilation produces an Unadmitted candidate with `AuthorityEffect: None`. It performs no operation execution, provider call, parallel scheduling or state transition. Existing allowed effects/tools and node/instruction budgets remain bounded by the existing candidate compiler. Independently signed runtime consumption, shared-output policy and effect-aware algebra are separate owned obligations. Both CLI allow-lists default to empty: the current pair requires explicit `--allow-effect read_subject --allow-effect emit_finding`; repeat `--allow-tool` only for an explicitly permitted tool reference. Source declarations do not grant a license, and these candidate ceilings do not authorize actual execution.

## Ordered substitution and evidence ceiling

For valid slots, nested substitution is `(theta o_i phi) o_(i+j) psi = theta o_i (phi o_j psi)`. For original slots `i < k`, disjoint substitution is `(theta o_i phi) o_(k+arity(phi)-1) psi = (theta o_k psi) o_i phi`. Nullary substitution removes a slot, so the later slot shifts to `k-1`; unary substitution keeps it at `k`.

Use the manually enumerated ordered typed boundary as the oracle. Compare the five-field contracts and root output, not a sorted colour multiset, arity alone or display names. The existing [slot-law tests](../tests/unit/test_planar_slot_laws.py) cover finite colour examples; typed workflow controls add schema/validator custody. Canonical bodies retain the candidate compiler's slot-ordered postorder. Equal boundaries do not establish operation equivalence or authorize swapping effects. No cohomology, general theorem or research novelty is established by these examples.

## Public ports and finite validation

The application entry is [compile_typed_workflow](../application/typed_workflow_compiler.py). The [CLI](../infrastructure/typed_workflow_compiler.py) provides these invocations; actual results and final source pins belong in the verification receipt:

```text
python -m omega_engine_operads.infrastructure.typed_workflow_compiler --repo-root . --emit-example
python -m omega_engine_operads.infrastructure.typed_workflow_compiler --repo-root . --workflow workflow.json --allow-effect read_subject --allow-effect emit_finding
python -m omega_engine_operads.infrastructure.typed_workflow_compiler --repo-root . --show-schema
```

`--emit-example` creates a new current-source-pinned declaration and writes it to stdout. It never rewrites an existing workflow to make stale pins pass. The current example binds falsifier Contract→Audit into audit original slot 0 of (Audit, Contract)→Receipt; free entries are exactly `[(falsifier, 0), (audit, 1)]`, yielding two ordered Contract ports. Compilation order is falsifier then audit; no instruction is executed.

The result contains `plan`, `workflow_digest`, `occurrence_order` and `native_report`. The workflow digest binds the normalized node/binding declaration order, workflow/root/occurrence identities, source/operation pins, ordered free entries and existing plan digest. Changing node identity or a bound source changes the binding even when the colour boundary is unchanged.

The candidate digest also commits the actual ordered instruction strings. This closes
an equal-byte-length body transplant through caller-supplied compiled aggregates.
Source pins at that seam are metadata; the fresh canonical compiler owns original
resource-byte verification. Previously recorded candidate hashes and signatures
need fresh compilation and external signing before reuse with this digest payload.
Historical receipts remain unchanged; this compiler does not re-sign them.

| Refused boundary | Public application code |
| --- | --- |
| Source or operation pin changed | `SOURCE_DIGEST_MISMATCH`, `OPERATION_DIGEST_MISMATCH` |
| Duplicate occurrence, absent root or missing declaration | `DUPLICATE_NODE_ID`, `ROOT_NODE_MISSING`, `OPERATION_MISSING` |
| Invalid edge endpoint, target slot or competing producer | `BINDING_NODE_MISSING`, `SLOT_OUT_OF_BOUNDS`, `DUPLICATE_SLOT_BINDING` |
| Shared producer, disconnected occurrence or wrong ordered free inputs | `SHARED_OUTPUT_UNSUPPORTED`, `UNREACHABLE_NODE`, `ENTRY_BOUNDARY_MISMATCH` |
| Native negative, malformed result or unavailable port | `GRAPH_INVALID`, `GRAPH_RESULT_MALFORMED`, `GRAPH_VALIDATOR_UNAVAILABLE` |
| Full typed port or existing candidate ceiling fails | Existing candidate `PlanRefusal` codes are retained, including `BOUNDARY_MISMATCH` |

Native typed `ApiErrorDTO` codes remain preserved; the CLI emits `TYPED_WORKFLOW_REFUSED` with the application refusal and exits nonzero. Native positive replies must have exact counts, complete occurrence coverage and valid stage ordering as well as no reported defects.

| Control | Independent expected result |
| --- | --- |
| Strict wire and example replay | Valid declarations with formatting variations emit the same canonical bytes; duplicate/escaped keys, unknown fields and booleans as slots refuse. |
| Repeated occurrence and nested join | Fresh node IDs may reuse a declaration; ordered free inputs and instruction occurrence count match a literal hand calculation. |
| Original-slot and nullary cases | Nonzero nested `i+j` and disjoint shifted slot preserve exact order; a nullary child removes only its bound slot. |
| Identity and topology refusal | Duplicate IDs, missing root/node, self-loop, longer cycle, disconnected node, competing slot producers and fanout refuse without operation execution. |
| Binding transplant and recovery | Reordered/omitted/duplicated free inputs and same-colour foreign schema/validator digest refuse; correcting only the changed binding recovers. |
| Source and ceiling controls | Changed source or operation pin, excessive budget, or an unlicensed tool or effect refuses. An equal-length instruction transplant keeps the declared pins and changes both digests. Accepted output stays Unadmitted. |
| Real native topology | Existing valid/invalid finite graph cases pass through the actual native public port under a pinned host/source snapshot; generic diamond compatibility remains intact. |

Observe a real public-port RED before each absent behavior's minimal GREEN implementation; already-GREEN behavior documents reuse. The epic names the focused test files and commands. For the actual mutation control, bypass the linked production nested `i+j` expression, require RED, restore exact bytes and replay. The separate [kernel mutation receipt](../receipts/oewas_002_20261010/planar_slot_laws/receipt.json) must not be stretched into full workflow acceptance. Additional source-pinned application/native guard bypasses must target the actual boundary with fresh controls. Mock verdicts or a mutated test oracle do not supply that evidence.

Freshly building and passing the source crate graph test establishes a source-crate result. Real integration separately exercises the selected existing main-checkout host binary. That host's source equivalence is not attested by the workflow command or integration run: CLI output explicitly records `native_source_binding: not_attested_by_this_command`. Preserve these evidence grades separately; a real host invocation cannot substitute for an attested source-to-binary build.

The actual `workflow_graph` action accepts an optional `oewas.typed-graph.v1`
payload. The Python compiler supplies declarations, source/operation pins, the
root occurrence and ordered free `(node_id, slot)` entries. Native validation
compares the operation content digest and all five port fields; its returned
typed interface must match the Python compiler's literal ordered boundary.
Nullary and unary operations are supported without widening the separate
canonical capability-pair schema. The ordinary generic graph API retains its
topology behavior, including generic diamonds; typed graphs still refuse shared
producers, unreachable occurrences and competing slots.

The selected native build and real-host controls establish this finite declared
graph boundary. Raw source-file custody remains with the source compiler; passing
caller-supplied source-digest text alone is not raw-file attestation. General
fanout/loop semantics, effect-aware execution and runtime admission remain with
their existing owners. No general algebraic or zero-allocation claim follows.
