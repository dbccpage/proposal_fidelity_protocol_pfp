---
name: governance-research-paper-edit-publish
description: "Use to scaffold, harmonize, rebuild or republish a research paper in coda_atlas."
status: canonical
operad_source_colours: ["Paper"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
families: [coda-papers, research-governance, techne]
---

# governance-research-paper-edit-publish

Scaffold, align, rebuild, and prepare a paper package under `coda_atlas/`.

## Where the facts live

Publication laws are `omega_engine_operads/rules/papers/`. Open the rule that matches the defect. Do not copy a rule into this skill.

| Defect | Rule |
|---|---|
| Header, section skeleton, descriptions | `rl_coda_publication_and_monograph_specifications.md` |
| Template, harmonization, pandoc | `rl_research_paper_template_and_harmonization_discipline.md` |
| Packaging and Lean census | `rl_research_paper_and_monograph_packaging.md` |
| Deposit envelope and manifests | `rl_paper_deposit_release_envelope_and_manifest_fences.md` |
| Verifier, paths, filenames | `rl_paper_deposit_verifier_attestation_and_path_fences.md` |
| Harmonization, notebooks, zip members | `rl_paper_harmonization_and_provenance_discipline.md` |
| Review remediation | `rl_publication_review_remediation_and_recertification_discipline.md` |
| Evaluator and mechanism inventory | `rl_paper_epistemic_evaluator_and_namespace_discipline.md` |

## Review and Woland

There is no `omega-paper-review-swarm` skill package. `verify` and `republication-gate` call `omega_engine_research_papers.use_cases.paper_review.cli`.

Woland profiles `woland.research_paper` and `woland.paper_review` license this skill (`omega_engine_woland/use_cases/base_swarm/specializations.py`). Retired stage labels resolve in `omega_engine_woland/infrastructure/research/skill_resolution.py`. Research planning is a separate use case:

```bash
python -m omega_engine_woland.entrypoints.research.plan_cli plan <paper>
```

## Scope

Refuse work outside:

- `coda_atlas/F004_papers/`
- `coda_atlas/F005_coda/`
- `coda_atlas/_kits/paper_template/`

## Procedure

| Open this reference | When |
|---|---|
| [`references/paper_template_layout.md`](references/paper_template_layout.md) | Scaffolding a package, or checking which files may sit at the package root |
| [`references/harmonization_pipeline.md`](references/harmonization_pipeline.md) | Ordering `rebuild` |
| [`references/pandoc_tex_build_hygiene.md`](references/pandoc_tex_build_hygiene.md) | A pandoc or XeLaTeX build fails, or a PDF is missing characters |
| [`references/deposit_packaging_checklist.md`](references/deposit_packaging_checklist.md) | Assembling a deposit ZIP |
| [`references/deposit_envelope_purity.md`](references/deposit_envelope_purity.md) | Keeping review artifacts out of the deposit |
| [`references/research_paper_anti_skills.md`](references/research_paper_anti_skills.md) | Mapping a package defect to its Python rule |

```bash
python -m omega_engine_research_papers.use_cases.paper_edition.cli <subcommand> [options]
```

1. **`scaffold`** — new package from `coda_atlas/_kits/paper_template/`.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli scaffold --dest coda_atlas/F005_coda/<slug> --slug <slug> --title "<Title>" --layer FOC
   ```
2. **`align`** — put the canonical tools from `coda_atlas/_kits/paper_template/` into an existing package.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli align --paper-path coda_atlas/F005_coda/<slug>
   ```
3. **`rebuild`** — regenerate derived artifacts after a manuscript, Lean, or test edit. Run this before `verify`.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli rebuild --paper-path coda_atlas/F005_coda/<slug> --verbose
   ```
4. **`verify`** — `paper_review.cli.run_all`.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli verify --paper-path coda_atlas/F005_coda/<slug>
   ```
5. **`republication-gate`** — Stage Ω checklist in `paper_review.cli`.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli republication-gate --paper-path coda_atlas/F005_coda/<slug>
   ```
6. **`publish`** — rebuild, then the republication gate, then a receipt. It stops for the human author.
   ```bash
   python -m omega_engine_research_papers.use_cases.paper_edition.cli publish --paper-path coda_atlas/F005_coda/<slug> --output receipts/<slug>_publication_envelope.json
   ```
