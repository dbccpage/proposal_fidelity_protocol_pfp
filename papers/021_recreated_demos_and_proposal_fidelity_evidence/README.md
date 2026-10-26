# Shelf note (2026-10-04)

This directory was stored as `011_recreated_demos_and_proposal_fidelity_evidence` and is now shelf 021. It is an unfinished archive audit. It is not the meron-cluster benchmark, and it is not shelf 011. The directory that exists at shelf 011 is `011_pfp_the_minimum_theorem`. The manuscript title inside this draft is unchanged.

# Paper 011: The Broken Referee: An Archive Audit and Self-Falsification Ledger

**Date:** 2026-10-03  
**Version:** 0.1.1  
**Status:** In-progress research methods draft and archive audit log; self-falsification ledger established; complete-corpus recreation unverified.

This package develops recreations and an exhaustive self-falsification audit of the demonstrations
represented in the Symbol Game findings notes. It distinguishes source custody, archived algorithm
execution, native certificate evidence, and corrected historical model observations. The package stands
as an audit log of historical verification failures—including the broken Genesis artifact verifier (75 false
`verified: true` labels), receipt-ID discrepancies (`REC_GENESIS_SUITE_1790618314` vs. `1790611114`), Demo 5/9
homology contradictions, and the offline mock scorer fixture replays (`docs/fixture_replay_2026_10_03_meron_offline_mock`).

Start with [the manuscript](paper.md), [completion requirements](docs/requirements.md),
and [source-copy provenance](docs/source_copy_provenance.md). The
[existing-work commit scope](docs/commit_scope_2026_10_02.md) states the evidence
representation and unfinished release obligations. The source snapshot
is pending explicit bulk-copy approval. Native builds are recorded in
[the build receipt](docs/native_build_receipt.json); that receipt makes no demo
outcome claim.

The [2026-10-03 recheck register](docs/rechecked_results.md) lists that day's outcomes and names the evidence files that were not admitted to this shelf.

[The continuation prompt](docs/continuation_prompt.md) gives the next agent the
original goal, frozen results, remaining work and authorization constraints.

The [current PDF](paper.pdf) has a complete task appendix: sixty challenges,
twenty-five Genesis tasks, thirteen aggregate families, and thirty-one overlapping
dispatcher entries. [Its inventory receipt](docs/manuscript_inventory_receipt.json)
binds the rendered artifact; listing a task does not establish its completion.

[The findings inventory](docs/findings_demo_inventory.md) now maps every named
family to source and reconstruction obligations. [Its audit receipt](docs/findings_audit_receipt.json)
checks source identity separately from execution.

[The mechanism recreations](docs/mechanism_recreation_design.md) have eleven
executed finite fixtures and an explicit unresolved MUB6–Regge example. The
retained tensor run used CPU PyTorch 2.6.0+cu124. A current mechanism run
requires torch >= 2.13.0. These fixtures and native graph
checks do not establish the planned empirical model studies.

[The native MUB replay](docs/native_mub_recreated_run/final_v1/receipt.json)
has completed the original seven-triple catalog calculation with twenty-one
transition matrices. Its [reproduction instructions](docs/native_mub_replay.md)
bind the exact output-only adaptation and explicit native dependencies.

[Genesis history recovery](docs/history_recovery/README.md) retains twenty-eight
original Git blobs and replays the defective artifact verifier for G01–G25.
The seventy-five erroneous accepts are falsifiers; none satisfies the missing
positive mathematical capability gates.

[The fresh G07 baseline](docs/history_recovery/g07/README.md) completes the
original provider-free tree/width computation, including 3,617 width cases,
35 quiet histories and 44 held-outs. Its global conjecture and model studies
remain open. [The native dossier homology audit](docs/native_dossier_homology/README.md)
evaluates eight original matrix carriers and retains the specific Demo 5 and
Demo 9 claim contradictions.

[The integer carrier replay](docs/native_dossier_integral/scope.md) retains and
replays 22 Smith certificates for the same eight dossiers, including the original
torsion carrier's integer chain H2 = Z/2. Nine malformed-carrier and certificate
controls refuse; manifold and cup-product claims remain separate.
[The fresh G12 baseline](docs/history_recovery/g12/README.md) compiles the five
original wrappers and concrete instances, checks the unchanged census/axiom gates
and executes all five original controls. Its model arms remain unperformed.
[The G01 reconstruction](docs/history_recovery/g01/scope.md) records the three
reading-F targets and compares the full supplied finite populations; eight
held-out signatures are explicitly reconstructed from the original prose.
[The G02 reconstruction](docs/history_recovery/g02/README.md) records the general
cut-census formula and checks all 1,014 source/native pair cases through twelve.
Both retain their mutation controls and unperformed empirical obligations.
[The G03 finite check](docs/history_recovery/g03/README.md) covers every original
pair and held-out chain under a newly declared adapter. Its native/source
replay gives a finite refutation for that adapter, with complete class-member
correspondences; the general conjecture remains open.
[The G04 finite replay](docs/history_recovery/g04/README.md) retains the original
18,798-history rectangle and seven supplied stakes separately from any
supplementary counterexample or missing historical held-out inputs.
[The degree-three/four composition](docs/recreated_run/native_phi3_phi4_composition_scope.md)
retains four actual native witness passes and all sixteen original refusals.
[The aggregate replay](docs/aggregate_recreation_design.md) also includes the
closed original four-stage AST progression and its remaining historical gaps.
[Original source recovery](docs/aggregate_recreated_run/original_recovery_v1/README.md)
also reproduces the restricted TFI gate and all 120 historical role texts,
including the source's synthetic scores and false AST terminal.

The paper-local custody machinery runs without a monorepo checkout. For example,
from this directory:

```console
py -3.12 -m pytest code/tests/test_paper011_source_custody.py --basetemp .pytest_tmp
```

Fresh recreations use [the bounded runner](code/recreate_demos.py) and its
[explicit execution contract](docs/recreation_design.md). The closed
[five-row replay](docs/recreated_run/final_bindings_v4/batch_receipt.json) retains
positive calculations and the original C042/C049 checker residuals separately.
Do not execute archived files indiscriminately: some retained
scripts request providers, mutate case folders, or shell out to build tools.
Replays use explicit bounded runtime configurations.

The text uses the included document license. Newly authored code uses the included
code license. Historical source copies retain their original notices and terms.
No external deposit or DOI is claimed.
