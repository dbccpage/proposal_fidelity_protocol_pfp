# Paper Change Log — 001_the_symbol_game

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114044> (DOI: `10.5281/zenodo.23114044`, Concept DOI: `10.5281/zenodo.23114044`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — Publication review evidence attribution and package census reconciliation

Reconciled deposit manifests (`MANIFEST.sha256`, `SHA256SUMS`) and deterministic release archive to include the full intended supplementary file set (the six companion PDFs and `docs/keywords.md`) and current preface/quiz hashes. Corrected evidence attribution in `paper.md`, `paper_claim_ledger.md`, `README.md`, and `zenodo_metadata.json`: citing `docs/release_validation_2026_10_02_review_repairs.json` for the complete package test suite, Lean build, notebook execution, and adapter/governor SHA-256 bindings, while scoping `docs/release_validation_2026_10_02_continued_review.json` to targeted follow-on checks. Clarified in `_lev_examiner_theoretical_minimum_quiz/instructor_key.md` that Lean formalization files are distributed in `lean4/`. Recompiled `paper.pdf`.

## 2026-10-02 — Continued review repairs

The Demo 1 notebook sends minimizing potentials with `str(v)` and records HOLD
for its positive optimum. That notebook is the minimum-5 triangle, separate
from the manuscript minimum of 3. The BQNF-FSIGN contract lists `stoquastic` as
the positivity-route alias and states that a concrete `Refused_*` status is the
abstract terminal `Refused`. A six-exercise notebook worksheet sits beside the
Examiner examination and does not replace it. The first-round receipt
`docs/release_validation_2026_10_02_review_repairs.json` stays in place. No
Zenodo deposit and no DOI.

## 2026-10-02 — Review repairs before release

Local repairs from the 2026-10-02 publication review. The central graph
argument is unchanged. The Examiner companion now uses the corrected operators
\(Bs\), \(B^T\lambda=0\), and \(c+B\phi\), tests uniqueness on nonzero
coboundaries in \(\operatorname{im} B\), and drops the invalid converse. The
preface labels the dialogue as fiction. The study guide separates heuristic
failure from complete exact enumeration and from a matching primal/dual pair.
Quiz and guide descriptions of fuel, the subprocess timeout, and the Lean
statements match the manuscript. `instructor_key.md` adds the worked key and
two unscored final challenges. The adapter rejects malformed native responses
with `NativeFunctionalProtocolError` and checks primal-cost consistency. The
governor reserves EXACT for cost zero, labels a positive optimum HOLD, and
rejects float, Boolean, and decimal proposals. The claim-ledger header is
0.1.0, 2026-10-02. Historical entries and the 2026-10-01 and earlier
2026-10-02 validation receipts are unchanged. No Zenodo deposit and no DOI.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-28: Version 1.3.0 author-review revision

This revision aligns the manuscript with the package code adopted on
2026-09-28 (repository commit c7970e2b9) and prepares the package for review.
The mathematics and its scope are unchanged.

Manuscript:

- Section 6 now describes both implementations. The native Rust solver returns
  `phi1`, `gauge`, and `forests_checked`, no dual circulation, caps the search
  at 100,000 forests, and refuses with `EnumerationLimit` beyond the cap; this
  was confirmed against the source and a command-line run. The paper-local
  Python reference in `code/symbol_game_governor.py` builds and independently
  verifies the full primal and dual certificate, caps tree enumeration at
  100,000 per component, and backs a governor that admits only strictly
  decreasing updates. The adapter falls back to this reference only when no
  executable exists and the native path is not required.
- Withdrawn: the statement that the governor's graph operations are retired
  with RUST_FUNCTIONAL_REQUIRED (true only of the older code baseline), and the
  statement that a binary hash binds the executable (the adapter does not hash
  or pin the binary).
- Narrowed: the Lean descriptions now state each theorem exactly; the
  NonAuthority statement is noted to hold by construction.
- The abstract says which implementation returns the dual certificate.
- Section 7 uses `cargo test -j 1`, `py -3.12`, one pytest file per command,
  the figure script, and `lake build`. The live debate demo is marked optional
  and requires the reader's own OpenRouter key. Section 7 also names the
  package figure and the historical contract files in `specs/`.
- Section 8 cites the companion papers by their actual titles (PFP II and
  PFP III) and describes the PFP III comparison as proposed and not yet run.
- The "Verification for this revision" section now points to the dated review
  receipt. Wording that triggered restricted-word warnings was rephrased.

Package:

- `docs/references.md` lists only works the manuscript cites. Placeholder DOIs
  (10.5281/zenodo.1000000 to 1000002) and uncited entries (Hatcher, Mac Lane,
  and a CODA entry) were removed. `docs/descriptions.md` and the Zenodo
  description now agree; `docs/completion_supplement.md` was updated.
- Code: all ruff findings fixed (import order, unused imports, one-line
  statements, a lambda assignment) without behavior change; governance tokens
  removed from docstrings; display text of the floating-point Fock enumerator
  renamed; a test subprocess now passes an explicit `check=False`.
- New test file `code/tests/test_manuscript_witnesses.py` ties the manuscript
  triangle, its dual certificate, exactness, strict rational descent, and Demo 1
  to pytest.
- Notebooks: `demo2_fsp_interactive.ipynb` had stale stored outputs; its first
  cell now raises on a failed expectation. All three notebooks were
  re-executed with a Python 3.12 kernel, execution-timing metadata was removed,
  and their Markdown was made plain. Each printing cell now sends its output as
  one stream message, so stored outputs do not depend on flush timing on a
  loaded machine. The Demo 3 notebook no longer says that no live
  implementation exists.
- The figure script regenerates `public_export/fig1_descent_and_obstruction.png`
  byte for byte; the deleted `fig1_overview.png` is no longer referenced.
- Release tooling was replaced with the current template versions, which
  exclude `.env`, build output, and caches from manifests and archives. The
  earlier archive had carried a placeholder-only `.env` file.
- `LICENSE` and `LICENSE-CODE` now hold the full CC BY 4.0 and PolyForm
  Noncommercial 1.0.0 texts in place of truncated excerpts. The code license
  changed from Apache-2.0 to PolyForm Noncommercial 1.0.0, following the
  series packaging contract; the crate metadata matches.
- `pyproject.toml` pins the ruff rule selection and pytest configuration.
  `zenodo_metadata.json`, `README.md`, and `.env.example` were rewritten.

## 2026-09-27: Complete methods revision

The canonical manuscript now owns finite graph repair, the exact LP witness
argument, cycle and sparsity facts, and the distinction between strict rational
descent and finite fuel. The shared triangle uses reports (1,1,1), penalties
(1,2,3), initial cost 6, and optimum 3. The Fock exposition is integrated into
Paper 002 while its code stays in this package. The old graph API is explicitly
retired; the active Rust response has no dual field. The authoring pass inspected
baseline 52cb5457f6c485ba548cfd292f6012a941ed22cf and ran no tests or builds.

The entries below are historical records, not current execution or publication
claims. Current scope is governed by paper.md and paper_claim_ledger.md.

## Retained historical metadata

**Paper Title:** PFP I: Exact Graph Repair and the Boundary Between a Proposal and a Certificate\
**Series Position:** OE-001 / author-review preprint; no deposit claimed\
**Author:** Jeremy H. Carroll\
**Date:** September 2026\
**License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

## 2026-09-24 — Review Verdict Audit & Epistemic Boundary Alignment

- **Cross-Paper Notation & Claim Reconciliation:** Added Section 3.4 to `paper.md`, establishing an explicit versioned reconciliation between section defect norm $D(s)$, invariant boundary obstruction class $\Phi_1([c])$, dual circulation certificates, and proxy metrics across PO-032, PO-033, and Paper 001.
- **Demo 1 Historical Pilot Log Corrections:** Retitled Demo 1 rounds as historical pilot behavior on partial host states. Documented the directed 3-cycle sum invariant ($1+2+2=5 \ne 0$) and $\operatorname{rank}(d_0) = 2$. Clarified that $\Gamma_2$ and $\Xi$ in pilot tables were binary admission proxies (`admitted_proxy`, `refused_proxy`), not live functional measurements. Documented that R2b and R3 prompts supplied example CUT syntax and R2b asserted only $a \to b$. Clarified that the diamond graph is a 1-skeleton complex with two $H^1$ loops, not an $H^2 \ne 0$ fixture, and documented that `_lift_hint` was never delivered to the model prompt.
- **Packet Tower Prompt Notes Demystification:** Aligned `packet_tower_llm_notes.md` with PO-032 §2 and OEWAS Spec §3, discarding speculative "soft logit masking" claims and framing prompt changes as context conditioning perturbations on the proposal distribution.
- **Demo 3 Replay Auditor & Regression Testing:** Updated `run_demo3_replay.py` contradiction checking to flag contradictions when either `action: identity` or `type: identity` is paired with nonidentity mappings, rejected non-object batch items, and added unit regression tests covering both cases (16/16 tests passing).
- **Rust Pharmacy & Runtime Executable Boundary:** Pruned `detectors_run` in `core_prompt_civilization/src/pharmacy.rs` to 11 active predicates (removed unexecuted `PERSONA_AUTHORITY_LEAK`). Hashed separately defined semantic payload (stripping version/schema labels) for `VERSION_DUPLICATION`. Bound `SCHEMA_SEMANTIC_LAUNDERING` suppression to verified host replay receipts, and preserved `raw_bytes_digest` alongside `normalized_json_digest`. Demoted theorem name laundering to diagnostic finding.

## 2026-09-24 — Demo 3 naming clarification

- Distinguished this archive's historical adversarial-debate benchmark from the later unrun controlled Demo 3 study in Paper 003. No archived result or numerical claim changed.

## PR #34 review repair (2026-09-24)

- Reproduced a four-vertex counterexample where the original dual circulation exceeded capacity despite a zero reported gap. Added feasible dual-vertex enumeration and independent certificate checking.
- Removed positivity admission by route/name and involution admission by keywords. Added host matrix/weight evidence, exact finite map evaluation, negative-weight coverage, and explicit determinant hypotheses.
- Separated alternating-site-gauge obstruction from physical sign obstruction. Generic repulsion and worst-case NP-hardness are no longer instance certificates.
- Restored actual claims/section on RETRACT, retained append-only events, bound genesis and outcomes into hashes, rejected malformed carrier inputs, and removed the false RFC 8785 claim.
- Replaced inaccurate grid quadrature with an analytic-series numerical evaluation; checked all hop-count sectors. Corrected the per-sequence amplitude bound and restricted the pairing carrier to time-integrated hopping sequences.
- Recomputed benchmark metrics from deposited records, removed fabricated live fallback, refused incomplete trace inputs, preserved all raw model JSONL, and distinguished historical labels from current verification.
- Updated demonstrations, notebooks, contract, README, manuscript and claim ledger; removed placeholder publication DOIs and unsupported empirical/Lean scope claims.
- Moved console reconfiguration from module import to CLI execution.
- Validation is recorded in `results/review_validation.json`. Original automated-review receipts were not deposited and are not certified here.

The release notes below are retained as historical claims and are superseded by the corrections above, especially their RFC 8785, prose-witness, ground-truth and physical-obstruction assertions.

## Release v1.2.0 (2026-09-24) — Mathematical Rigor, Exact Dual Solver & Zenodo Release Hardening

### 1. Exact Primal-Dual $\Phi_1([c])$ Solver

- Replaced heuristic candidate-value search in [`code/symbol_game_governor.py`](code/symbol_game_governor.py) with exact rational LP dual algorithm via spanning-tree cycle basis enumeration and Gaussian elimination on the cycle incidence submatrix.
- Implemented `compute_exact_phi_1` emitting `Phi1Certificate(phi_1, primal_potentials, dual_circulations, duality_gap=0)`.
- Corrected weighted triangle $(1, 2, 2)$ minimum from 7 to 5 (primal section $s=(0, -4, -2)$ gives $D(s)=5$; unit circulation gives matching dual lower bound 5).
- Corrected 2-edge tree $(1, 2)$ from 1 to 0 (primal $s=(0, 1, 3)$, dual circulation $x=(0, 0)$).

### 2. Distinction Between Section Defect $D(s)$ and Obstruction $\Phi_1([c])$

- Formally distinguished section potential adjustments (`CUT`) from changes to the claim's obstruction class across [`paper.md`](paper.md), [`paper_claim_ledger.md`](paper_claim_ledger.md), and governor logic.
- Enforced that a `CUT` modifies $s \in C^0$ descending $D(s)$, while $\Phi_1([c])$ is strictly invariant under `CUT` for fixed claims $c$.
- Enforced the fundamental inequality $D(s) \ge \Phi_1([c])$ at every step, refusing any defect-increasing proposal.

### 3. Certificate Gate Route Separation & 4-Law Enforcement

- Separated `Positivity` / `DeterminantalPositivity` (stoquastic systems, $U=0$ non-interacting fermions, and spin-balanced attractive Hubbard $U < 0$ continuous HS determinant squaring) from `ExactCancellation` in [`code/certificate_gate.py`](code/certificate_gate.py).
- Enforced all 4 Involution Laws for `ExactCancellation`, rejecting gibberish pseudo-witnesses ('cancel' in proof with empty mapping) with `Refused_UnverifiedInvolution_InvalidWitness` or `IncompleteLaws`.
- Adopted the signed-magnitude contribution model $\sigma(x) a(x)$ with $a(x) \ge 0$, clarifying that pairing occurs on a subset $\mathcal{P} \subseteq X$ with strictly positive thermal partition function $Z > 0$.

### 4. Representation Scoping & Negative Controls

- Clarified in [`paper.md`](paper.md) §5.3 that odd-cycle geometry is an obstruction to an alternating diagonal site sign gauge $\eta \in \{-1, +1\}^N$ in the worldline hopping representation.
- Added determinantal QMC ($U=0$ operator positivity and balanced $U < 0$ real determinant squaring) as sign-free negative controls on odd cycles ($C_3, C_5$, Kagome).
- Scoped Troyer–Wiese (2005) as establishing computational complexity of generic fermion sign problems, not a blanket classification of every individual repulsive instance.

### 5. Multi-Agent Benchmark Arithmetic Correction

- Corrected debate classification arithmetic across the 10 conditions in [`code/run_adversarial_debate_benchmark.py`](code/run_adversarial_debate_benchmark.py) and [`paper.md`](paper.md) §7.2:
  - 6 Proposer hallucinations (ground truth positives), 4 non-hallucinations (ground truth negatives).
  - 8 Adversary challenges (6 True Positives, 2 False Positives); 2 concurrences (2 True Negatives).
  - Adversary Challenge Precision: 6/8 = 75.0% (correcting the previous report of 10/10).
  - Adversary Challenge Recall: 6/6 = 100.0%.
  - Adversary Overall Accuracy: 8/10 = 80.0%.

### 6. RFC 8785 Canonical JSON Serialization & Hash Chaining

- Implemented RFC 8785 compliant canonical JSON byte serialization in [`code/symbol_game_governor.py`](code/symbol_game_governor.py) with deterministic key ordering and zero whitespace ambiguities.
- Chained every turn's evidence hash into a tamper-evident SHA-256 state ledger.

### 7. Zenodo Readiness Regression Test Suite

- Added [`code/tests/test_zenodo_regression_suite.py`](code/tests/test_zenodo_regression_suite.py) testing the five release gates:
  1. Tree $\Phi_1 = 0$ with matching primal-dual certificates.
  2. Triangle $\Phi_1 = 5$ with matching primal section (D=5) and dual circulation bound (5).
  3. `CUT` invariance of $\Phi_1([c])$ with monotonic defect descent.
  4. Rejection of the 'cancel' pseudo-witness.
  5. Physics negative controls ($U=0$ and balanced $U < 0$ recognized under determinantal routes, while odd-cycle hopping triggers obstruction).

### 8. Standalone 64-State Fock Path Enumerator & Weight Bound Verifier

- Implemented [`code/fock_path_enumerator.py`](code/fock_path_enumerator.py) proving the restricted proposition on $C_3$ at $t=1, U=2, \beta=1/4$:
  - Enumerates all 192 rooted closed 3-hop paths (96 negative, 96 positive).
  - Verifies target path weight $-\exp(-1)/384 \approx -0.0009580$ with $E_U = 4$ throughout.
  - Verifies all positive 3-hop paths have $E_U \le 2$ (weights $\ge \exp(-1/2)/384 \approx 0.0015795$).
  - Bounds 4-or-more-hop paths by $\le 1/6144 \approx 0.0001628$.
  - Certifies strict gap separation $(1/6144, \exp(-1/2)/384)$, excluding any equal-magnitude positive individual path partner.
- Added unit test [`code/tests/test_fock_path_proposition.py`](code/tests/test_fock_path_proposition.py) (13/13 tests passing overall).

### 9. Authoritative BQNF-FSIGN Specification & Purge of Legacy Spec

- Created [`specs/bqnf_fsign_contract.yaml`](specs/bqnf_fsign_contract.yaml) adhering to [`specs/normal_form_contract_schema.yaml`](specs/normal_form_contract_schema.yaml), declaring the 64-state Fock carrier, 4 involution laws, representation routes, and terminal route mapping.
- Cleanly deleted legacy `specs/nf_change_bqnf.yaml`, which pertained to unrelated database CDC query repairs.

### 10. Historical Audit Analysis & Receipt Provenance Hardening

- Documented 4 historical audit cases in [`paper.md`](paper.md) §5.2: free-fermion sign reversal, stoquastic identity map, ChatGPT turn-1 `LIFT_REQUEST`, and DeepSeek unexamined half-filling assumption.
- Updated [`results/receipt.json`](results/receipt.json) replacing legacy `adversary_caught_am=true` row-markers with true classification metrics (6/8 precision, 6/6 recall, 8/10 accuracy) and explicit representation basis annotations.
- Pre-rendered executed outputs in-place across all three interactive notebooks in [`jupyter_notebooks/`](jupyter_notebooks/).

### 11. Stoquastic Identity Involution Interception & Gate Replay Hardening

- Hardened [`code/certificate_gate.py`](code/certificate_gate.py) to explicitly intercept and refuse proposals asserting that the identity map is fixed-point free or sign-reversing under `ExactCancellation` (`Refused_UnverifiedInvolution_IdentityNotSignReversing`).
- Replaying the historical transverse-field Ising dimer trace now triggers a verified refusal with `fixed_point_free=False` and `sign_reversing=False`, preventing regex false-positive acceptance.
- Valid stoquastic systems route to `Positivity` ($w(x) \ge 0$), requiring no involution.
- Added targeted unit test `test_stoquastic_identity_involution_refusal_and_positivity_route` in [`code/tests/test_certificate_gate.py`](code/tests/test_certificate_gate.py) (14/14 tests passing).

## Release v1.1.0 (2026-09-23) — Round 7 Multi-Agent Adversarial Debate Integration

### 1. Multi-Agent Benchmark Addition

- Incorporated Round 7 Multi-Agent Adversarial Debate benchmark across $C_5$ pentagonal plaquettes and 6-site corner-sharing Kagome clusters across continuous parameter sweeps $U/t \in \{-4.0, -2.0, 0.0, +2.0, +4.0\}$.
- Documented Proposer (`meta-llama/llama-3.1-8b-instruct`) and Adversary (`deepseek/deepseek-chat`) in [`paper.md`](paper.md) §7.4.
- Added formal claims C-15, C-16, and C-17 to [`paper_claim_ledger.md`](paper_claim_ledger.md).

### 2. Code & Interactive Demonstrations

- Added [`code/run_adversarial_debate_benchmark.py`](code/run_adversarial_debate_benchmark.py) providing live OpenRouter benchmarking and offline trace replay.
- Added [`jupyter_notebooks/demo3_adversarial_debate_interactive.ipynb`](jupyter_notebooks/demo3_adversarial_debate_interactive.ipynb) providing interactive visualization of the adversarial debate trajectory.
- Updated [`code/certificate_gate.py`](code/certificate_gate.py) to generalize odd-cycle and non-bipartite frustration checks to $C_5$ and Kagome clusters.

### 3. Empirical Results Archive (`results/`)

- Packaged complete raw JSONL model prompt/response traces for all Demo 2 and Demo 3 experimental rounds into [`results/`](results/).
- Deposited canonical run receipt [`results/receipt.json`](results/receipt.json) for the 10-condition debate.

### 4. Canonical Specifications (`specs/`)

- Added `specs/nf_change_bqnf.yaml` (deleted in v1.2.0): The authoritative Boundary-Quotient Normal Form contract specification defining cochain complexes $C_0 \xrightarrow{d_0} C_1 \xrightarrow{d_1} C_2$, quotient space $Q_1 = C_1 / \operatorname{im}(d_0)$, and terminal routes.
- Added [`specs/normal_form_contract_schema.yaml`](specs/normal_form_contract_schema.yaml): Meta-schema validating Simplex normal form contracts.

## Release v1.0.0 (2026-09-23) — Initial Zenodo Deposit Release

### 1. Document Architecture & Monograph Core

- Created [`paper.md`](paper.md) providing complete academic synthesis of Proposal Fidelity Protocol (PFP), discrete manifold retraction, and empirical anti-morphism discovery.
- Created [`paper_claim_ledger.md`](paper_claim_ledger.md) establishing 1:1 bijective tracking of claims C-01 through C-14 with complete Claim Hygiene scoping.
- Created [`README.md`](README.md) with quickstart commands enabling researchers to execute all demonstrations in under 60 seconds.
- Created [`pyproject.toml`](pyproject.toml) declaring metadata and test configuration.

### 2. Standalone Runnable Code Package (`code/`)

- Implemented [`symbol_game_governor.py`](code/symbol_game_governor.py) with exact rational arithmetic, boundary operator $d_0$, section defect $D(s)$, $\Phi_1$ computation, and monotonic descent enforcement.
- Implemented [`certificate_gate.py`](code/certificate_gate.py) with the 4 Involution Laws, hardness checks (Troyer-Wiese NP-hard barrier), and odd-cycle obstruction checks.
- Implemented [`demo1_holonomy.py`](code/demo1_holonomy.py) demonstrating the 3-cycle holonomy experiment.
- Implemented [`demo2_bqnf_fsign.py`](code/demo2_bqnf_fsign.py) demonstrating BQNF-FSIGN across 6 experimental rounds.
- Implemented targeted unit test suite [`code/tests/`](code/tests/) achieving 100% test passing rate under pytest.

### 3. Formal Lean 4 Verification Kernel (`lean4/`)

- Configured [`lakefile.lean`](lean4/lakefile.lean) and [`lean-toolchain`](lean4/lean-toolchain) pinned to `v4.34.0-rc1`.
- Mechanized [`InvolutionLaws.lean`](lean4/InvolutionLaws.lean) formalizing the 4 involution laws and proving pairwise weight cancellation (`pair_cancellation`).
- Mechanized [`OddCycleObstruction.lean`](lean4/OddCycleObstruction.lean) formalizing the non-existence of alternating sign gauges on odd cycles ($C_3$).
- Mechanized [`NonAuthority.lean`](lean4/NonAuthority.lean) stating the declared non-authority policy as a type with one value.

### 4. Interactive Jupyter Demonstrations (`jupyter_notebooks/`)

- Authored [`demo1_holonomy_interactive.ipynb`](jupyter_notebooks/demo1_holonomy_interactive.ipynb).
- Authored [`demo2_fsp_interactive.ipynb`](jupyter_notebooks/demo2_fsp_interactive.ipynb).

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.3.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.
