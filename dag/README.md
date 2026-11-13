# Mathematical audit and workflow benchmark

This directory is an evidence-producing audit paused at the user-requested publication and continuation checkpoint. Start with [handoff/README.md](handoff/README.md) and its Claude/Gemini prompts. The original objective is unfinished. Coverage, claims, and executable experiments must not be confused: an inventoried file is not a reviewed proof; a proposed workflow is not an implemented or evaluated workflow.

The immutable public benchmark input is `benchmark/seed_prompt.txt` (UTF-8, LF). Its SHA-256 and a commitment to a separately held answer key are recorded in `benchmark/commitment.json`. The answer key must never be included in workflow prompts, model contexts, retrieval indexes, or workflow artifacts. SHA-256 is an integrity commitment, not encryption. Evaluation is a separate trusted step after outputs have been frozen.

The repository already had local modifications when this audit began. The inventory records per-file hashes and the Git baseline; conclusions apply to the recorded content, with drift detected at final verification.

The old checkout work was preserved in a Git stash and a separately verified recovery archive before fast-forwarding `main` to `8050c66900899771766f33e8f5fdd200b7dd9120`. Source findings are generally recorded rather than silently repaired; explicitly requested relocation consumer fixes are recorded separately in migration custody receipts. Audit work is under `dag/`; the later explicitly requested migration of the imported pilot estate went to `pilots/`. That estate and its move, triage and retirement records were removed on 2026-11-12/13 and remain in git history.

All 204 imported numbered pilots and 17 shared owners now have an initial mechanism assessment. The explicitly authorized first quality retirement removed 138 stub/trivial folders while preserving all their original bytes in an external verified archive and their useful lessons in the DAG. The subsequent authorized demo/support relocation moved 216 private engine files and 84 PFP education files, with source deletions and consumer-path fixes recorded separately in `migrations/demo_support_verification.json`.

`derivations_dag.json` records mathematical foundations, claim dependencies, evidence and limitations. `workflows_dag.json` records existing workflows and finite, typed experimental compositions. Cyclic processes are represented by bounded, unrolled executions. No claim of all possible workflows is meaningful without a finite grammar and explicit bounds.

Paid model runs require a fail-closed aggregate budget for each run (all stages and retries), current price metadata and usage receipts. The requested per-run ceiling is USD 0.10. Design and dry runs do not establish effectiveness.

Current artifacts:

- `FOUNDATIONS.md` gives the mathematical synthesis, with assumptions and implementation limits.
- `reviews/papers_audit.json` assesses all 38 primary manuscripts. Supporting code, references and historical artifacts remain a separate review obligation. The review does not infer authorship from prose style.
- `file_inventory.json` and `structural_review.json` cover 32,261 eligible tracked files. `reviews/coverage.json` records full and partial substantive reading separately; the every-file substantive audit is unfinished.
- `research/research_01.json` through `research_10.json` contain 30 proposals from ten distinct researchers. `research/validation.json` checks their internal dependency DAGs and cited repository paths.
- `composition_catalog.json` contains 4,250 proposed compositions: 3,776 pairs and 474 triples. The finite slice has at most four macro occurrences, four paid calls and 16 expanded nodes; no four-macro sequence currently satisfies the node bound. Existing opaque workflows occur only in pairs. General branching trees, free parameter sweeps and repeated macros are outside this enumeration.
- `workflows_dag.json` includes the 49 existing families, 30 new ideas, those 4,250 compositions, 12 runnable benchmark plans. A proposed whole-run envelope is not an implemented native port. Missing calibration inputs, preservation bridges, QM checkers and billing bounds remain explicit admission obligations. The unmodified integer-sum checkers cannot grade the QM seed.
- `benchmark/reference_runner.py` preserves the exact seed, reserves aggregate whole-run billing and freezes failures. There are 12 runnable plans spanning direct/revision controls, rational panels, exact Hamiltonian context, sectioned responses and isolated native charpoly checking. These mechanisms have narrow predicates; they do not implement or validate all four named systems together. See `benchmark/LIVE_RUNNER.md` and the workflow-specific contracts.
- `benchmark/results_summary.json` records 24 graded frozen attempts, 23 with paid dispatch and one zero-dispatch infrastructure refusal. Settled provider charges total USD 0.055614, with zero held liability. No fully correct solution has been established. The best observed score is 88/100 for one self-critique run, versus 83/100 for one direct run of the same model at lower cost, token use and wall time. These exploratory observations do not establish general workflow superiority.
- `reviews/coverage.json` records 9,576 full-reading receipts, 33 partial and 22,652 pending original files. Full reading is not a correctness proof. `reviews/pending_reuse_candidates.json` supplies byte-checked reuse candidates and grants zero additional semantic coverage.
- `wiki/workflow_documentation.json` contains 17 entries including historical WF1-WF5 and the 12 benchmark plans. The [QM benchmark Wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-QM-Benchmark) and `wiki/workflow_publication_charpoly_20261110.json` record the latest published comparison. Every subsequently completed workflow needs a registry entry and Wiki documentation with results and limitations.
- `handoff/` contains the continuation brief, separate Claude and Gemini prompts, publication pointers and an inventory of generated render/test material preserved outside the loose Git diff. All paid experiments are stopped. The proposed host-derived charpoly experiment is not implemented or admitted.

Rebuild the catalogs with the repository Python environment:

```powershell
.venv\Scripts\python.exe -X utf8 dag\reviews\build_coverage.py
.venv\Scripts\python.exe -X utf8 dag\enumerate_workflows.py
.venv\Scripts\python.exe -X utf8 dag\build_dags.py
```

Run the focused offline checks:

```powershell
.venv\Scripts\python.exe -X utf8 dag\benchmark\validate_rational_panel.py
```

The source audit is pinned, and all unreviewed files retain an explicit pending status. No claimed general improvement in mathematical accuracy, cost, tokens or time follows from these designs, historical success labels, or offline fixtures.
