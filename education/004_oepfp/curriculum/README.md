# MSS-N system integration: a runnable ascent

AuthorityEffect: None.

This folder is the canonical deep notebook path. Read the
[how to play quickstart](../../documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_how_to_play_the_symbol_game/README.md) first (ages 11 to 500,
player manual). Optional [beginner lessons](000_beginners/curriculum_25_000.md)
state ages 5 to 500 and are not a substitute for the notebooks below.

Start with a bracketed mark, then add boundaries, repairs, certificates, and
research evidence. This sequence supplies 20 worked notebooks with explicit
adversarial exercises. Each lesson names the implementation it uses and states
what remains outside its evidence.

The 30-minute MSS-N spark supplies the motivating question: how far can declared
marks and rules take us? The lessons make that question concrete without treating
a catalog title as a derived result. In the current atlas, MSS-N refers to row N
of the source-indexed stage registry. Historical tower notation needs its source
context; catalog coverage and licensed lift depth remain different quantities.

Use the [theory ascent map](../../../research/mssn_sn_tower/_theory/README.md)
for the linked dossiers, and the [research crosswalk](research_crosswalk.md) to
find a route into every in-scope research file. The full
[inventory](research_inventory.json) classifies files individually as lab-backed,
reading-only, historical, or open. A reading route does not mean that the file
has been executed or fully reviewed.

## How to learn

Read each notebook from top to bottom. Run the worked computation, predict the
adversarial exercise, then run its reference check. Change one declared input at
a time and explain why the outcome changes. Numerical fixtures use integers or
`Fraction`; a failed assertion is a useful counterexample, not a reason to
replace the assertion with a constant success.

| Route | Lessons in order | What the learner can check |
| --- | --- | --- |
| Beginners | [Marks](000_beginners/system_integration/01_marks_and_packets.ipynb), [lifts](000_beginners/system_integration/02_lifts_and_non_descent.ipynb), [cells](000_beginners/system_integration/03_edges_and_parallel_cells.ipynb), [costs](000_beginners/system_integration/04_costs_and_ties.ipynb) | Packet boundaries, preserved distinctions, parallel arrows, and retained ties |
| Novices | [Codecs](100_novices/system_integration/01_codecs_and_tamper_evidence.ipynb), [token frontier](100_novices/system_integration/02_token_frontier.ipynb), [agent composition](100_novices/system_integration/03_typed_agent_composition.ipynb), [cycle repair](100_novices/system_integration/04_cycle_repair.ipynb) | Changed bytes, zero retained mass, type and license failures, cycle invariance |
| Intermediates | [Nilpotence](200_intermediates/system_integration/01_nilpotence_and_missing_boundaries.ipynb), [LP certificates](200_intermediates/system_integration/02_exact_lp_certificates.ipynb), [quantifiers](200_intermediates/system_integration/03_quantifier_order.ipynb), [spin triangle](200_intermediates/system_integration/04_frustrated_spin_triangle.ipynb) | Missing boundary detection, primal/dual feasibility, order of choices, exhaustive finite obstruction |
| Advanced | [Four-simplex](300_advanced/system_integration/01_four_simplex_volume.ipynb), [degree-four pairing](300_advanced/system_integration/02_pairing_and_degree_four_certificate.ipynb), [survivors](300_advanced/system_integration/03_survivor_birth_and_death.ipynb), [transfer shadow](300_advanced/system_integration/04_transfer_trace_and_shadow.ipynb) | A determinant computed two ways, declared intersection pairing, exact set changes, finite return counts |
| Researchers | [Reach](400_researchers/system_integration/01_coverage_and_licensed_depth.ipynb), [immune boundary](400_researchers/system_integration/02_immune_boundary_and_negative_selection.ipynb), [prompt selection](400_researchers/system_integration/03_governed_prompt_evolution.ipynb), [source audit](400_researchers/system_integration/04_source_bound_research_audit.ipynb) | Proposal status, typed retirement refusals, negative controls, selection gates, source-bound evidence |

## Run headlessly

Use Python 3.12 or later with PyYAML and Pydantic 2 installed. These dependencies
are imported by existing package entry points; Jupyter is optional for this
plain-Python sequence. From the repository root:

```powershell
python -m pip install -r omega_engine_education/curriculum/3_the_symbol_game_proposal_fidelity_protocol_pfp/requirements.txt
python -B omega_engine_education/scripts/build_system_integration.py
python -B omega_engine_education/scripts/verify_system_integration.py
python -B -m unittest omega_engine_education.tests.test_system_integration omega_engine_operads.tests.unit.test_retired_anti_skill_boundary -v
```

The builder writes only this sequence and its manifest. The verifier starts a
fresh CPython process for every notebook and executes each ordinary Python cell
in order. It does not claim to run an IPython kernel or render widgets. It checks
UTF-8 without BOM, rejects float literals and direct float construction in cells,
and rejects constant assertions. Imported libraries can contain other numerical
paths; the exact-arithmetic claim concerns the mathematical fixtures exercised
here.

The [headless receipt](headless_receipt.json) records each notebook hash, its
declared source hashes, imported Python source hashes, code-cell count, and
output. The inventory hash binds the full research snapshot. A changed research
snapshot fails the overall receipt even when individual lessons pass; refresh
after concurrent work settles. Passing lessons do not grant publication or
admission authority.

## Connect the systems

- **Genesis:** the cost-and-tie and reach lessons explain why a selected measure
  and a licensed ascent record must be declared. External repository results are
  reading references, not rerun by these notebooks.
- **The Symbol Game:** real grammar, cochain, codec, LP, and token-frontier code
  supplies the finite checks. Neural logits and weights are not measured here.
- **Agents and skills:** real operad composition and capability checks separate
  well-typed composition from permission to invoke an operation.
- **Immune system:** the retired Python admission paths return typed refusals;
  the notebook detector is an explicitly named teaching model. The Rust pharmacy
  remains the production implementation.
- **Prompt evolution:** a bounded teaching population is filtered by schema,
  host-field canaries, and held-out Boolean outcomes before exact cost selection.
  This does not report learned model performance.
- **Geometry and physics:** finite F2 enumeration and rational determinant and
  pairing calculations are carried out independently of their broader physical
  interpretation. Named manifold fixtures need separate topology checks.

## The 125-lesson scaffold is not the front door

The [125-lesson syllabus](curriculum_125_master.md) stays on disk and is
not a second route. This sequence is the deep path. The
[review record](curriculum_125_review.md) records defects and maps older
lessons onto notebooks in this folder. Its
[per-notebook review](curriculum_125_review.json) is a historical snapshot
whose hashes bind the reviewed pre-relocation bytes. The obsolete generator
was retired after the curriculum moved here; these checked-in notebooks are
the canonical artifacts and must be reviewed and edited in place.

This sequence does not claim that all 125 existing lessons, all research
programs, or every native Rust and Lean path are complete.
