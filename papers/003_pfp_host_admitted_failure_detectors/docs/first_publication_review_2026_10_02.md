# Paper 003: first-publication review

2026-10-02 · Version 0.1.0 · AuthorityEffect: None

**Verdict:** suitable for a first Zenodo methods preprint after incorporating
this revision. Its contribution is a detector-admission protocol, a source audit
with elementary exact lemmas, and a proposed evaluation design. It establishes
neither active detector efficacy nor a general reduction in hallucination.

The starting deposit was `e11c07ce90318309f058c8097ffd1c440a8ffb84`.
All 69 archived source members were checked against their Git blob identities.
The original manifests and deterministic archive passed before editing.
The revised execution record is
[first_publication_validation_2026_10_02.json](first_publication_validation_2026_10_02.json).
Tested working-file hashes, rather than the starting commit alone, bind the
revised code and publication assets.

## Findings and repairs

| Priority | Finding in the submitted candidate | Repair and evidence |
| --- | --- | --- |
| High | A fuel bound can be read as a bound on the whole host. The canonical host continues appending receipts after terminal refusal and fuel imposes no batch-byte or elapsed-time bound. | Sections 4 and 9 now bound charged batches only and identify the separate resource obligations. Baseline `_blocked` and `_commit` were source-inspected. |
| High | The exact threshold helper accepted `True`, `1.5`, and `Fraction(3,2)` as exponents; panel helpers accepted Boolean masks and silently ignored bits outside the declared universe. | Added integer/positive-scale and mask/universe validation with 14 parametrized regression cases. The suite preserves all original finite lemma checks. |
| High | “Independence” could be confused with statistical independence or inferred from separate fields and table coverage. The baseline gate is also not strict conjunction. | Added the complete six-case table and distinguished separate check derivation, constructed input coverage, package policy, and the historical corrected policy. |
| Medium | “No particle-hole symmetry at all” exceeded the declared local transformation; “equal populations” omitted one-body spin and decoupling assumptions. | Scoped the real uniform-hopping triangle claim, stated equal spin chemical potentials and real spin-independent dynamics for the determinant-square argument, and added Wu–Zhang's primary reference. |
| Medium | A sum threshold was liable to be read as agreement by distinct independent agents; identical screened/executed predicates could be read as coverage of every valid input. | Appendix A now distinguishes positive entries from independent witnesses and panel soundness from open-input coverage. The original lemmas and their proof limits remain intact. |
| Medium | The false-suppression denominator and joint safety confidence needed to be explicit. | Defined the conditional denominator; excluded invalid proposals from it; required prespecified route multiplicity and repeated-look handling; clarified that D-minus-R estimates policy plus feedback. |
| Medium | Public v0.1 headers coexisted with unqualified internal v1.2/current-branch wording and inconsistent pytest requirements. | Aligned the current ledger and descriptions with 0.1.0, retained the earlier 1.x history, separated all source pins, and pinned pytest 8.3.5 to match the reproduction commands. |
| Medium | Five short quiz questions had a skeletal embedded key and a repository-only worksheet dependency. | Replaced them with 24 problems across levels 0–7, a worked study guide, a separate instructor key, local replay instructions, and a 96-point rubric. All companion links resolve within the deposit. |

The helper's input fixes preserve its mathematical domain and do not change
the host or danger-gate policy. The PDF has been regenerated from the revised
manuscript; the manifests and deterministic release archive are refreshed
against the final file set.

## What was checked

- **Python:** 59 passed, one skipped. The skip is the native Python/Rust parity
  check, which requires the Rust binary. Ruff 0.14.13 passes.
- **Educational arithmetic:** exact Hill fractions, singleton-panel
  counterexample, the 298/299 confidence threshold, and the 407/408 Bonferroni
  threshold replay. All 24 questions have matching keyed answers.
- **Offline demonstrations:** host transactions, gate cases, phrase fixtures,
  and the constructed candidate-response audit execute without a provider.
- **Historical source:** main host/domain/gate/tests at `52cb5457f6c4`; immune
  gate, allostery, thymus, matcher ports, and control runner at `30609de2c392`;
  the correction commit identity; and the regression assertion describing
  the canonical self panel. This is source inspection, not a full repository run.
- **Harvest provenance:** 112 rows: 102 marked scripted and 10 live. All 102
  scripted responses equal one of the 12 scripted prompt-specification values.
  Those counts do not establish detector accuracy or model error frequency.
- **Publication packaging:** PDF compilation/rendering, final file census and
  hashes, deterministic ZIP membership/envelope, and verification of an extracted
  copy of the release.

The current environment has no Cargo/Rust binary. Native rebuild/parity,
full-repository integration, historical provider-certificate replay, and the
proposed randomized experiment were **not run**. Earlier receipts retain
their own source pins and cannot fill those gaps.

## Teaching material

The new curriculum requires learners to compute the policy before discussing
its effect. It covers phrase negation and valid near misses; gate variants and
derived signals; fuel and rollback; receipts and historical evidence; all three
appendix lemmas; the three distinct physics conditions; and allocation,
denominators, safety intervals, and study stopping.

The study guide teaches prerequisites and new worked examples. The instructor
key gives every answer, exact calculations, proof sketches, acceptable scope,
and a standard-library replay worksheet. Neither the curriculum nor its rubric
claims historical Landau authority, measured learning gains, or operational
authorization.

## Remaining research work

Detector admission and activation require independently checked positive
defects and applicable valid near misses, bound predicates/actions/checkers,
and working validated route adapters. A performance claim requires the actual
frozen allocation and held-out experiment, not a successful protocol matrix
or a historical certificate label. A complete resource guarantee requires
the additional limits identified above.

These are explicit ceilings of the methods preprint. They are not hidden
acceptance claims and do not need to be solved to publish the stated method.

## Publication files and source

Use the revised `paper.pdf`, `paper.md`, and matching 2026-10-02 release ZIP.
Retain the current metadata version 0.1.0 and the existing distinct text/code
license declarations. This review creates a candidate; it makes no external
deposit or DOI claim.

The added physics citation is the primary paper
[Wu and Zhang, Physical Review B 71, 155115 (2005)](https://arxiv.org/abs/cond-mat/0407272v3).
The manuscript separately cites the primary Troyer–Wiese, Majorana-positivity,
meron-cluster, Reflexion, and Self-Refine papers. The signed-cycle gauge
argument, lemma proofs, and confidence calculation state their assumptions
explicitly.
