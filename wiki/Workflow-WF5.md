# WF5: rewrite the task without losing its meaning

**Use this when:** you need an explicit grammar representation before the
five-agent procedure. **Normal model calls in the demonstrated variant:** six.

The demonstrated rewrite is deterministic: zero rewrite model calls, one miner,
five concurrent solvers. A future model-written rewrite must add its calls and
costs explicitly.

## Before you start

Choose a grammar **and its public start production**, decoder, rewrite strategy
and protected query. Decide what the independent host can actually verify.
The demonstrated source language was canonical integer-sum sentences. Other
language and research tasks require their own preservation contracts.

## Do this

1. Keep the original seed bytes and label every source span: task, context,
   constraints, operands, requested output and unresolved meaning.
2. Rewrite the entire supported seed into one grammar. Keep original prose as
   audit data; do not silently drop it or append it as an unexamined fallback.
3. Parse the rewritten form, decode its declared meaning and check preservation
   against the original protected query. Stop on unresolved meaning.
4. Mine guidance against the preserved rewritten task; screen and freeze it.
5. Run [WF4's five-agent/global checks](Workflow-WF4.md), checking proposed
   answers against the **original** public input.

**Keep:** original bytes, span ledger, grammar/decoder/strategy versions, rewrite
and preservation checks, frozen mining, all five responses and accounting.

## The worked rewrite

Original:

```text
Calculate the exact sum of 17, 25, and -4.
```

PFP packet:

```text
op<<sum><exact><once>op<<values><p17><p25><n4>><total>>
```

The selected `packet` grammar uses the existing PFP packet syntax. Its explicit
decoder interprets `pN` as a nonnegative magnitude and `nN` as its negative,
preserves every operand occurrence, and names `task_result.total` as the output.
Syntax alone does not supply those arithmetic meanings.

The host checked complete source coverage, source/decoded query equality,
public input equality, output-interface preservation and canonical source
round-trip. It never inserted the expected sum into a prompt.

## What success means

For the declared finite language, the rewritten task preserves the checked
query and constraints. The final independent task check passes. This is not a
proof of arbitrary English equivalence or a solution to an unbounded problem.

MSS-N has several explicit grammar starts; a boundary packet is not an assumed
default for all of them. See [MSS-N rewriting](Rewriting-MSS-N.md) and
[PFP rewriting](Rewriting-PFP.md) when choosing a different representation.

## What the real experiment taught us

Four miners failed before any solver call: a field name used as a colour, an
invalid witness reference and two malformed provider outputs. The accepted
variant simplified the provider schema while preserving exact host checks.
Every failed reply and cost stayed in the record.

The accepted path used 4,540 tokens and $0.00069292. Whole-development use was
10,069 tokens and $0.00152852 across ten model actions. Those are different
measurements. The reused seed baseline was never called again.

**Current availability:** the automated standalone runner is
`python -m pfp.workflows.wf0005`. See [Install and run](Workflow-Running.md)
for tested commands, budget limits, offline controls and replay.
Historical measurement versions remain separate from the migrated implementation.

**Stop here** after preserving the checked result. Future refinements belong to
new, named recipes in the [workflow library](Workflow-Library.md).

## Inspect the exact reference inputs

The [historical prepared examples](Workflow-Examples.md) include the actual
P* system message, user message and typed response contract for WF5.
Use them to see the full shape; generate new attempt bindings for a new run.
