# Derivation campaign: attempting the open DAG targets one at a time

**AuthorityEffect:** None.

This brief is for an autonomous agent (Model_g, Model_a, Agent, or a human contributor). It works through the open targets of the derivation DAG one at a time. Each target gets one pull request. The aim is to close every derivation that can be closed honestly. Where a target cannot be closed, the aim is to record precisely why and what is missing.

## The queue

`dag/pfp/campaign/derivation_queue.json` ranks every node that meets all of these conditions:
- its status is OPEN, CONDITIONAL or IMPORTED_ASSUMPTION;
- it is a mathematical statement, not a coordination or custody record;
- it has never had a non-ladder run.

The ranking is by downstream impact: the number of DAG nodes that depend on it, with trunk stages weighted ×3. Regenerate the queue from the repository root with `python -I -X utf8 dag/pfp/campaign/make_queue.py`.

- **Take targets in rank order.** Skip a target only if it is not a mathematical claim. Record the skip in `dag/pfp/campaign/skipped.md` with a one-line reason.
- **Start with rank 2, `L1-IMP-SECTOR-SYMMETRY-LAW`.** Rank 1, `TFQ-0006`, is a summary record of all L1→L2 imports and is addressed through its parts. Rank 2 is the transitive sector symmetry of the quadratic readout, an imported assumption with 142 downstream nodes, and half of what `L1-IMP-HILBERT-INNER-PRODUCT` still imports.

## What counts as a result

**Every outcome below is a result.** Choose the strongest one you can prove, and claim nothing beyond it.
1. **Derived.** The node's full statement is proved in Lean from the repository's admitted primitives, with no new imports.
2. **Reduced.** The statement is proved from a strictly weaker, explicitly named assumption. The node stays CONDITIONAL, and the bottleneck is rewritten to name the weaker import.
3. **Refuted / not derivable.** A Lean countermodel shows the statement does not follow from the stated primitives. This is valuable: it proves the import is genuinely needed.
4. **Narrowed.** A precisely stated finite or special case is proved. The node statement is narrowed to it, with the rest moved to `bottleneck`, or the special case becomes a new child node.

## The honesty gate (non-negotiable)

PR #171 promoted 14 nodes to PROVED_LEAN, and only 3 held (see #176). So these rules apply to every target:
- **No promotion without the full statement.** A node becomes PROVED_LEAN only if a Lean declaration states its **full** statement, and that declaration compiles with only `propext`, `Classical.choice` and `Quot.sound`.
  - A lemma with the target's name is not enough.
  - Neither is a `decide` over one small instance, nor a definition that makes the claim trivial.
- **Never raise a status otherwise.** When unsure, narrow.
- **Every PR body carries a statement-vs-theorem table.** One row per claim in the node statement: the claim, the Lean declaration that proves it (or "not proved"), and the verdict (FULL / NARROWED / NOT PROVED).
- **Every number in prose must be recomputed exactly,** in Lean or in the independent check below. Prose may not state a number that nothing recomputes.
- **Forbidden in added Lean:** `sorry`, `admit`, `axiom`, `native_decide`, `unsafe`.

## Deliverables per target (all in the same PR)

1. **Lean.**
   - One module, `lean4/<Descriptive>.lean`, registered in its own non-default `lean_lib` in `lean4/lakefile.lean`.
   - Built with `lake build <Module>`, Lean 4.35.0, Mathlib v4.35.0 (`56a005855ea17e0b0958f73ec801ae140b0a1679`).
   - Use the shared cache read-only through a junction `lean4\.lake\packages` → `C:\lq\l4\.lake\packages`. Never write into `C:\lq\l4`, never copy Mathlib, and remove the junction afterwards.
   - The file ends with `#print axioms` lines.
2. **Replay receipt.** `dag/research/campaign_<node-id-lowercase>_lean_replay.json` records module, sha256, exit code, toolchain, Mathlib sha, axioms and output. Model it on `dag/research/pfp_batch01_lean_replay.json`.
3. **Independent check.** `checks/independent/<node-id-lowercase>.py`, a SymPy and plain-Python script.
   - It recomputes every concrete number, identity and finite case in the claim, **without importing any repository code**. It is a second, independent route to the same answer.
   - Run it with `python -I -X utf8 checks/independent/<file>.py`. It exits 0 on success and prints what it checked.
   - If the claim has no computational content, say so in the derivation note instead.
4. **Derivation note.** `dag/derivations/independent/<node-id-lowercase>.md`, a step-by-step derivation in plain mathematical prose that a mathematician can follow without Lean.
   - Its first line must be: `Status: AI-drafted, awaiting human review.` Only a named human reviewer may change it.
   - End with "What is proved", "What is assumed" and "What is open".
5. **DAG update.** Edit through the owning fragment or `derivation_dag.json`, as `dag/derivation_dag_reading_note.md` explains:
   - new or updated `lean` references;
   - the new statement or bottleneck if the claim was narrowed or reduced;
   - a status change only under the honesty gate.

## Pipeline after any DAG change (in this order)

1. **Syncs:**
   ```
   python -I -X utf8 dag/sync_pfp_results.py
   python -I -X utf8 dag/sync_unified_dag.py
   python -I -X utf8 dag/sync_application_branches.py
   python -I -X utf8 dag/sync_pregenesis_to_wdp.py
   python -I -X utf8 dag/sync_frontier_branches.py
   python -I -X utf8 dag/sync_genesis_to_higher.py
   python -I -X utf8 dag/sync_foc035_observer_presheaf.py
   ```
2. **Generators:**
   ```
   python -I -X utf8 scripts/build_master_derivation_ledger.py
   python -I -X utf8 dag/pfp/generate_prompts.py --write --all-missing
   python -I -X utf8 scripts/build_readme_facts.py --write
   python -I -X utf8 papers/core/tools/build_results_audit_table.py --write
   ```
3. **Re-pin LAST:**
   ```
   python -I -X utf8 dag/research/repin_tensor_receipts.py --run "branch <name>" --reason "<what changed>"
   ```
4. **Checks (all must pass):**
   - each sync with `--check`;
   - `dag/sync_unified_dag.py --invariants`;
   - `dag/render_dag_views.py --check`;
   - `dag/validate_derivation_dag.py --no-files` (it must print `failures=0`);
   - `scripts/build_readme_facts.py --check`;
   - `dag/research/repin_tensor_receipts.py --check`;
   - `pytest dag/test_tensor_countermodel_receipt.py dag/test_tensor_measurement_receipt.py dag/test_application_branches.py dag/test_frontier_branches.py dag/test_genesis_to_higher.py dag/test_foc035_observer_presheaf.py`;
   - your independent check script;
   - and `build_evidence.py --check` once `dag/evidence/` exists.

## Pull request

- **Branch** `campaign/<node-id-lowercase>`, from current `origin/main`.
- **Title:** `Campaign: <node id> — <Derived|Reduced|Refuted|Narrowed>: <one line>`.
- **Body:**
  - the outcome class;
  - the statement-vs-theorem table;
  - the axiom lines;
  - the independent check output;
  - what is still open.
- **Git rules:** commit and push normally. Never force-push, never merge, never push to `main`. A maintainer reviews the statement-vs-theorem table before merging.
- **No paid API calls.** Never print or commit values from `.env`.
- **Workspace:** use a git worktree at a short path (e.g. `C:\gw\tfqm`). Remove it, and its build products, when the PR is up. Disk is shared.

## Progress log

After each target, append one line to `dag/pfp/campaign/log.md`:
```
<UTC date> | <node id> | <outcome class> | <PR url> | <one-line result>
```
