# Bounded repair (C, R, E, I, M, T)

Part of [Operads](operads.md). Previous: [Skills, op inventory and the resolver](operads_skills_and_catalog.md) · Next: [Local checks, global compatibility](operads_local_to_global.md)

[Paper 018](paper_018.md) applies the operad machinery to one small, real task:
testing a supplied code patch. It is an implementation study, not a theorem
about programs and not a model benchmark.

## Who owns what

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| Operads | Capability sources, typed declarations and composition | Discovering or compiling a skill does not admit its execution |
| Adversary (the execution layer) | Working copies, running checks, retaining evidence | Check commands are trusted configuration, not a sandbox |
| [EIS](eis.md) | Immune definitions, screening and activation decisions | A missing measurement is neither clearance nor activation |
| [Prompt Civilization](pciv.md) | Evolution records, genealogy and lineage | A lineage record is not a proof or a release |

The four do not merge into one runtime. Screening and lineage are injected
services, not responsibilities absorbed into the catalogue.

## The request

A repair request fixes an objective, a manifest of source-file hashes, an
allowed write set, a supplied text patch and a tuple of check commands. It has
two identities:

- the **candidate identity** hashes the patch bytes;
- the **request digest** binds the whole request.

They are not interchangeable: the same patch can be tested against different
sources or under different checks.

## The six operations

The workflow is a typed composition of six operations, compiled with the
[typed workflow](operads_typed_workflows.md) compiler and run through the
native coordinator.

| Step | Name | What it does |
| --- | --- | --- |
| **C** | capture | Check the declared source hashes, retain the request and patch, and make a fresh working copy outside the source tree |
| **R** | observe | Run the fixed checks to record a baseline |
| **E** | evaluate | Check the patch paths against the allowed files, apply the patch to the working copy, and run the same checks again |
| **I** | incorporate | Submit the bound observations to the immune and genealogy services; retain any binding or missing-service failure |
| **M** | disposition | Compare baseline and post-patch results: repaired, partly improved, ineffective, regressed, refused, or no repair needed |
| **T** | terminal | Retain the execution record. The source is not changed, and nothing is admitted or activated |

The state carries the run key, request digest and candidate identity through
all six. A missing executor binding refuses **before** any operation takes
effect, and an unavailable native compiler produces no execution receipt.

These letters are a trace of this workflow only. They overlap in spelling with
the eight letters of the Discrete Deformation Calculus on
[DDC operations](rewriting_wdp_ddc.md), but the paper states plainly that no
mathematical descent law or representation lift is inferred from the
six-letter trace. In the calculus, `E` is exact repair and `M` is typed refusal;
here `E` is "evaluate the patch" and `M` is "decide the disposition".

## The worked example

```python
def adjust(n):
    if n < 0:
        return n
    return n - 1        # the patch changes this to n + 1
```

| Check | Before | After |
| --- | --- | --- |
| Positive: `adjust(2) == 3` | fails (exit 1) | passes (exit 0) |
| Control: `adjust(-2) == -2` | passes (exit 0) | passes (exit 0) |

The disposition is `REPAIRED`. The original source file is byte-identical
afterwards; the working copy and observations are retained.

`REPAIRED` concerns **these two checks only**. The example does not test every
integer, discover the patch, call a model or install the program. Replace the
checks with weak ones and an inappropriate patch could pass, which is why the
negative control matters. Re-running with a new run id is another local replay,
not another independent trial.

## Run it in this repository

The Rust operad host has the repair slice as one command. It verifies the
source hashes, makes the working copy, applies the patch strictly, runs the
checks before and after, and writes the record. The source folder is only read.

```powershell
cd code/rust
cargo run -p pfp_operads -- repair ../../workflows/wf57_host_tested_patch_repair/examples/refused_operation/source my_run ../../workflows/wf57_host_tested_patch_repair/examples/refused_operation/request.json
```

That request repairs a small JSON file with the host's own commands as its two
checks, so it needs no other program. The host prints `"outcome":"REPAIRED"`
with check exits `[1, 0]` before the patch and `[0, 0]` after it, and `my_run`
holds the request, the patch, the record and the patched copy.

The example above, `adjust` with its two asserts, runs the same way as a test
(`pfp_core/workflow_families/tests/test_repair.py`) and gives the same exits.

[WF57](workflow_wf57.md) is the workflow around the command: a model writes the
patch, the host tests it, and a patch that was tested and did not repair is
added to the failure ledger. Its fixtures cover the negative cases: a patch
that leaves the check failing, one that breaks the control, one outside the
write set, one that does not fit the file, a changed source and a missing
check program.

In the Rust host the **I** step classifies a failed patch for the failure
ledger. It calls no immune or genealogy service, and every record says
`NOT_MEASURED` and `HOLD`.

## Engineering details that matter

- **Stale bytecode.** The check profile disables Python bytecode writes and
  clears cache overrides, because a same-size edit can otherwise reuse stale
  bytecode and report the old behaviour.
- **Truncated output.** Output is captured up to a prefix limit, and truncation
  is recorded. A hash of a captured prefix is not a hash of the whole stream.
- **Deadlines** are engineering controls, not proof of resource confinement.
- **Missing measurements stay missing.** The real immune interface returned
  `NOT_MEASURED`, which is retained as such; activation stays on hold.
- **Learning is a separate record.** If a later notification fails, it cannot
  overwrite the retained observations with a made-up successful learning result.

## The research extension

The same route is extended in [Paper 019](paper_019.md) into an outer loop that
proposes changes to a harness (its prompt, workflow options, search and context
policies) and an inner loop that evaluates them in isolated containers. The
evaluators, private fixtures, budgets, credentials and admission rules stay with
the host. The loop is implemented; the paid campaign was deferred, so no model
results are claimed.
