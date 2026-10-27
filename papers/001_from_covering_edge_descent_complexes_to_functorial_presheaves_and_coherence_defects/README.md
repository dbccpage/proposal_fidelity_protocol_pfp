# Covering-Edge Descent and Coherence Defects (PO-001)

**Title:** From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects

**Author:** Jeremy H. Carroll

**Status:** Pre-Print (v2.0), with working research supplement 2026-10-14; not redeposited

**Version:** 2.0.0

**License:** CC-BY-4.0 for prose/documents; Apache-2.0 for code.

**Zenodo upload:** <https://zenodo.org/uploads/23115851> (v2.0 Pre-Print; DOI: 10.5281/zenodo.23115851; former: <https://zenodo.org/records/20710765>)

Path A extends cover maps to a strict presheaf when all saturated-chain products agree. Path B declares comparable-pair maps and records their composition defect. The finite extensions retain separate hypotheses for the additive normal form, LP certificates, routing, distinction ledger, Bell gluing, and cyclotomic holonomies. A specified observed higher-coherence realization is now available; generic non-flat cohomology remains open.

The October 14 supplement proves the all-degree strict-chain curved algebra and classifies the declared vertexwise invertible gauge action: it cannot remove nonzero curvature. Flat cover extension is a separate operation, possible exactly under saturated-path agreement. The exact Rust owner, independent Python controls, supplementary Lean kernel and replay limits are described in [the derivation review](docs/derivations_2026_10_14.md).

The requested PR #959 review adds controls for unequal-length saturated paths
and exhaustive reference enumeration of the 219 labeled four-vertex posets.
Its [scoped receipt](code/operator_incidence_pr_review.json) records 10 Rust
tests, 50 focused Python controls, 25 surrounding regressions, 85 planning
checks and six supplementary Lean declarations. The original pin remains
unreplayed; the original derivation receipt and source archives are preserved.

The next [scoped derivation review](docs/loss_incidence_angles_2026_10_14.md) adds
the flat-loss countermodel and sharp measured path-separation bounds, concrete
strict-poset Lean proofs from definitions, and metric-bound rational dihedral/
deficit enclosures. The current focused Lean replay uses deliberately migrated
stable pins. Three reusable Rust owners and independent Python controls now
cover these calculations; historical archives remain unchanged.

## Reproduce the package checks

Python 3.11 or newer is required. Install the declared dependencies, then run the verifier:

```bash
python -m pip install -e .
python scripts/verify_package.py
```

The verifier checks the 27 claim IDs and titles, cited test functions, local file links, identical manuscript aliases, fresh ordinary-Python notebook assertions from two directories, the finite pytest suite, and `SHA256SUMS`. It does not run a Lean kernel or validate a Zenodo upload. See [the dated review](docs/review_2026_10_02.md) for results and limits. The script resolves its package location, so it can also be invoked by absolute path from another directory.

For individual checks:

```bash
python -m pytest -q -p no:cacheprovider
python scripts/regen_sha256sums.py --check
```

## Reading and evidence

| Surface | Files | Scope |
|---|---|---|
| Quick start | [Guide](docs/quick_start.md) | Core identities and common inference errors |
| Descriptions | [Descriptions](docs/descriptions.md) | Summary, core theorems, formal verification, and scope boundaries |
| Notebook | [00_enter_po001.ipynb](jupyter_notebooks/00_enter_po001.ipynb) | Asserted finite examples; run from package or notebook directory |
| Canonical manuscript | [Markdown](covering_edge_descent.md) | Current claims and scope fences |
| Reader formats | [PDF](covering_edge_descent.pdf), [TeX](covering_edge_descent.tex) | Built from canonical Markdown; TeX embeds its SHA-256 |
| Claim ledgers | [Markdown](covering_edge_descent_claim_ledger.md), [YAML](covering_edge_descent_claim_ledger.yaml) | 27 stable IDs with claim-specific evidence |
| Python | [Modules and tests](code/) | Exact finite rational/cyclotomic fixtures and counterexamples |
| Lean | [Source inventory and build limits](lean4/README.md) | 20 theorem/module sources plus the Lake file; selected current pinned elaboration; older roots not blanket-certified |
| Review | [Findings and validation](docs/review_2026_10_02.md) | Corrections, reproduced failures, and evidence boundaries |
| History | [Change log](covering_edge_descent_change_log.md) | Current correction supersedes broader historical release language |

The long directory-name Markdown file is an identical companion alias. The superseded upgrade plans have been removed. Their eight corrected residuals live under `MS-PO001-RESIDUAL` in the repository's [research goal DAG](https://github.com/dbccpage/the_symbol_game/blob/main/omega_engine_atlas/coda_atlas/F004_papers/plans/goal_dag.jsonl). The all-degree algebra, declared GL gauge action, heterogeneous Lean transport, specified observed higher coherence and rational metric hinge bridge are derived under their exact scopes. The full native-history goal remains blocked; the new protected linear quotient and weighted path bounds are prerequisites rather than its completion. The [planning review](https://github.com/dbccpage/the_symbol_game/blob/main/omega_engine_atlas/coda_atlas/F004_papers/plans/README.md#po-001-upgrade-plan-review) records the scopes and rejected stronger claims. `code/monograph_narrative_harmonizer.py` is an authoring utility rather than a verifier and is not part of the reader-build pipeline.

## Rebuild the reader formats

Install Pandoc and XeLaTeX with the packages named in the bundled preamble, then run:

```bash
python scripts/build_paper.py
python scripts/regen_sha256sums.py
python scripts/verify_package.py
```

The builder writes TeX and PDF only after successful compilation, fixes the source-date epoch, rejects missing glyphs, and reports overfull boxes for inspection. Rendering is an artifact check, not mathematical evidence. The Lean toolchain and dependency pins are separate; [Lean instructions](lean4/README.md) describe their replay.

## Five connected derivations

The [current supplement](docs/five_connected_derivations_2026_10_14.md) separates
written proofs, selected Lean kernels, bounded Rust execution and independent
Python controls. Reusable owners are `omega_homology::block_embedding`,
`omega_homology::observed_2category`, `omega_functional::protected_linear_quotient`,
`omega_functional::path_error` and `omega_general_relativity::metric_hinge_transport`.
The last requires rational normal rotations and records the branch information
that holonomy alone loses. The protected quotient is a finite linear instance
of WDP minimality, with no quantum-carrier inference.
