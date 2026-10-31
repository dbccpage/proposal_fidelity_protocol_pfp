# Workflow contracts: the reference

**You do not need to memorize this page.** Use it while building a WF2–WF5
adapter, or when a checker reports a missing field.

## What P* contributes

P* is the prompt template around your seed: it declares the task environment,
the allowed operations, their concrete application and the required terminal
answer. WF1 uses its basic typed form. WF2 adds the full slot catalogue below.

The seed is public task input. The expected answer belongs only to the host's
independent checker. A more elaborate prompt must not leak that answer.

## All 31 reference slots

Every slot has an explicit disposition. The six **required** slots must be
populated. For other slots, record applicable material or a reason for absence;
do not invent a gauge group or mathematical witness to fill a box.

| Slot | Group | Meaning | Required |
| --- | --- | --- | --- |
| `carrier` | L0 environment | Declared finite carrier. | Yes |
| `equality_policy` | L0 environment | Equality used for the task. | Yes |
| `algebraic_ring` | L0 environment | Declared coefficient/arithmetic domain. | Explicit disposition |
| `ambient_space` | L0 environment | Ambient structure. | Explicit disposition |
| `assumptions` | L0 environment | Explicit assumptions. | Explicit disposition |
| `vacuum_state` | L0 environment | Optional reference state. | Explicit disposition |
| `gauge_group` | L0 environment | Optional gauge declaration. | Explicit disposition |
| `observer_budget` | L0 environment | Finite resource limits. | Explicit disposition |
| `operands` | Operands and colours | Input operands and source references. | Yes |
| `colours` | Operands and colours | Types of inputs and outputs. | Yes |
| `operators` | L1 operations | Typed operator signatures and arities. | Yes |
| `grafting_sequence` | Composition | Ordered composition. | Explicit disposition |
| `root` | Composition | Final root operation. | Explicit disposition |
| `ordered_ports` | Composition | Input port order. | Explicit disposition |
| `intermediate_bindings` | Composition | Intermediate values. | Explicit disposition |
| `compatibility_obligations` | Composition | Type/port matching obligations. | Explicit disposition |
| `concrete_spans` | L2 bindings | Concrete source spans. | Explicit disposition |
| `parameter_bindings` | L2 bindings | Actual parameter values. | Explicit disposition |
| `boundary_conditions` | L2 bindings | Declared boundary conditions. | Explicit disposition |
| `instantiated_arguments` | L2 bindings | Arguments supplied to operators. | Explicit disposition |
| `congruence_ideals` | L2 invariants | Task constraints or ideals. | Explicit disposition |
| `preservation_obligations` | L2 invariants | What each operation must preserve. | Explicit disposition |
| `invariant_witnesses` | L2 invariants | Checkable invariant witnesses. | Explicit disposition |
| `annihilators` | Negative and repair material | Counterexamples and decoy refutations. | Explicit disposition |
| `anti_patterns` | Negative and repair material | Identified failure patterns. | Explicit disposition |
| `helpful_patterns` | Negative and repair material | Useful task patterns. | Explicit disposition |
| `repair_candidates` | Negative and repair material | Proposed repairs. | Explicit disposition |
| `unresolved_obligations` | Negative and repair material | Remaining obligations. | Explicit disposition |
| `witness_anchors` | Witness anchors | Available code/paper/formal anchors, or explicit absence. | Explicit disposition |
| `ddc_trace` | DDC trace | References to all explicitly emitted DDC move records. | Explicit disposition |
| `terminal` | Terminal | Task result, scope, remaining obligations. | Yes |

The four task-grounded L2 fields checked by the WF3 reference are
`concrete_spans`, `parameter_bindings`, `instantiated_arguments` and
`preservation_obligations`. They need actual task references and values,
not general advice such as “be careful.” [WF3](Workflow-WF3.md) shows the difference.

## DDC move names

Collect every **explicitly emitted** move, including duplicates and its source
location. Empty means none emitted. Never infer a hidden reasoning trace.

| Code | Name |
| --- | --- |
| `E` | Exact repair |
| `R` | Residual projection |
| `C` | Context exposure |
| `I` | Integration |
| `Λ` | Structural lift |
| `D` | Scale descent |
| `M` | Typed refusal |
| `T` | Terminalisation |

These are protocol names, not an invitation to execute a proposed move.
Preconditions and semantics belong to the [DDC reference](Rewriting-WDP-DDC.md).
A record emitted by a model is a proposal, not a proof that its preconditions hold.

## Keep these records separate

| Record | What it establishes |
| --- | --- |
| Raw response bytes | What was actually returned. |
| Parsed typed answer | Whether the response met the declared shape and bindings. |
| Independent task check | Whether the declared task property passed. |
| Operad/DDC collection | What candidates were emitted and where. |
| Provider accounting | Whether actual charged cost settled within the admitted allowance. |
| Human or application decision | What may be done with the checked proposal. |

None of these automatically establishes another. Preserve all failed records.
The exact historical catalogue, including its original source identity, is
[available as JSON](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/contracts/slot_catalogue.json).
It is the reference workflow profile, not a claim that every PFP application
must use these 31 fields.

[Choose a workflow](Workflows.md) · [Troubleshooting](Workflow-Troubleshooting.md)
