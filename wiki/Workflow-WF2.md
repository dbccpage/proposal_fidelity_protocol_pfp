# WF2: collect the operations in one response

**Use this when:** you want the answer and a structured account of the operations,
missing information and proposed DDC moves. **Normal model calls:** one.

WF2 keeps WF1's typed task envelope and adds a full slot report. The host
collects records from that same reply; collection makes no extra model call.

## Before you start

Have the WF1 task, a task-specific checker, and the versioned slot catalogue.
Know the input/output types of the operations you are requesting. You can use
integer addition without learning category theory first.

## Do this

1. Prepare the original task and envelope as in [WF1](Workflow-WF1.md).
2. Put all 31 slot names in the system contract. Require one disposition for
   each: `provided`, `unresolved` or `not_applicable`, with a reason where needed.
3. Require `task_result`, `slot_report`, `operad_candidates` and `ddc_moves`
   inside the answer. Keep the expected task answer out of the prompt/schema.
4. Obtain one actual reply. Keep its bytes before parsing or extracting records.
5. Check envelope, schema and task result; then check operation metadata and
   collect every declared record occurrence, including duplicates and failures.

**Keep:** prepared inputs/schema, raw reply, check result and occurrence ledger.
Store rejected records separately from usable candidates; keep their provenance.

## The four answer sections

| Field | What belongs there |
| --- | --- |
| `task_result` | The proposed answer to the original task. |
| `slot_report` | All catalogue slots and their dispositions. |
| `operad_candidates` | Named operations, ordered input types, output type, arity and source/witness references. |
| `ddc_moves` | Proposed transitions; empty when none are proposed. |

For example, an operation taking **one list** of integers has one input port.
Three values inside the list do not make its arity three.

The [contract reference](Workflow-Contracts.md) gives the complete catalogue,
DDC alphabet and what the host must check. A missing witness should be reported
as unresolved, rather than filled with a plausible-sounding statement.

## What success means

The task's independent checker passed, the declared structural checks passed,
and actual emitted records can be traced to the raw response. An operation
description is still a candidate. It does not prove execution, operad laws or
permission to use it elsewhere.

## If it fails

A missing slot is a contract error. Wrong arity or an invented source quote is
a structural error. A schema-valid wrong answer is a task error. Keep each
category visible; a clean JSON document can still be wrong.

**Current availability:** this is a complete manual/integration recipe.
The Oct 28 automated implementation belongs to the historical monorepo
prototype, not a `pfp-lab run WF2` command. [Status and evidence](Workflow-Integration-Status.md).

**Stop here** if one explicit response is enough. Continue to
[WF3](Workflow-WF3.md) when preparing guidance before solving is useful.

## Inspect the exact reference inputs

The [historical prepared examples](Workflow-Examples.md) include the actual
P* system message, user message and typed response contract for WF2.
Use them to see the full shape; generate new attempt bindings for a new run.
