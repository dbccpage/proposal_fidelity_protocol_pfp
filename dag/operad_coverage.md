# Operad coverage

How well the operads are tested by the workflows, and how the prose (atlas), DAG
derivations, Lean 4 and Rust layers back them. Reviewed 2026-11-14 on `main`
at `149ce3a5`. AuthorityEffect: None.

## Bottom line

- **The workflows barely touch the operad code.** No workflow imports the
  canon (`operads.canon` / `core_operad_canon`, 56 types in 6 families). The
  family runtime behind WF6-WF51 imports no operad module at all. Operad code
  is reached by three workflows only: WF52 (attack tests that call the
  associativity verifier and colour composition), and WF53 and WF54 (the
  operational trace quotient in `pfp_core/operad_pipe.py`).
- **WF1-WF5 use operad words, not operad code.** WF2-WF5 ask the model for
  `operad_candidates` and `ddc_moves`; the host checks their shape and files
  them as `UNVERIFIED_CANDIDATE`. Their colours (`Integer`, ...) are not the
  canonical colours (`Audit`, `Code`, ... `State`).
- **The laws are checked on signatures, not behaviour.** Associativity and unit
  are verified for supplied triples by comparing colour signatures (DAG
  `SYS-OP-001`, `NATIVE-OP-001`); `SYS-OP-002` records a NaN-residual
  associativity counterexample. No Lean theorem states associativity, unit or
  equivariance. Equivariance appears in no workflow.
- **The system does not yet learn from failures across runs.** Workflows learn
  inside one run (WF26 antibodies, WF19 rules, WF20 lift grants, WF51
  exclusions), then discard it. Persistent stores exist (PCIV cemetery
  `record_failure`, `ObstructionLedger` keyed by DDC letters, the pharmacy
  catalog) but no workflow writes a failure to one, and no workflow reads one.
- **Atlas, ledger, change log and DAG agree.** `dag/build_atlas.py --check`
  passes: 1,347 ledger rows (740 DAG claims, 607 archive claims), 73 matched,
  115 partial, 419 gaps. The change log was already filled (three entries,
  2026-11-13). The operad paper (PFP 018) has 1 partial claim and 4 gaps.

## Matrix

Counts are files (DAG nodes, archive claims) that name the concept. A name
match is a pointer, not proof that a law is checked; the bottom line above is
from reading the code. `*` marks a workflow with live (model) runs; the rest
are offline fixtures. Regenerate with `python dag/operad_coverage.py`
(`--json` lists the files).

| Concept | Workflow code | Workflow tests | DAG nodes | Derivations | Archive claims m/p/g | Lean | Rust src / tests | Python test files |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: |
| Colour typing of operations | WF2*, WF3*, WF5*, WF52* | WF5*, WF52* | 2 | 0 | 0/0/0 | 1 | 23 / 12 | 50 |
| Composition / substitution | WF1*, WF3*, WF52* | WF1*, WF5*, WF52* | 24 | 4 | 0/0/0 | 3 | 44 / 16 | 83 |
| Associativity law | WF52* | WF52* | 10 | 0 | 0/0/0 | 1 | 17 / 7 | 12 |
| Unit / identity law | WF52* | WF1*, WF52* | 5 | 1 | 0/0/0 | 3 | 36 / 11 | 23 |
| Symmetric / equivariance | — | — | 4 | 0 | 0/0/0 | 2 | 10 / 1 | 6 |
| DDC alphabet (E,R,C,I,Λ,D,M,T) | WF2*, WF3*, WF4*, WF5*, WF52* | WF2*, WF4* | 13 | 2 | 0/0/3 | 0 | 68 / 44 | 60 |
| DDC lift licence (Λ) | WF20, WF33, WF40 | — | 4 | 1 | 0/0/0 | 0 | 13 / 7 | 17 |
| Registered operands / motifs | — | — | 0 | 0 | 0/0/0 | 0 | 6 / 6 | 7 |
| Antibodies | WF14, WF26, WF52*, WF53, WF54 | WF1*, WF52*, WF54 | 3 | 0 | 2/0/0 | 2 | 27 / 9 | 66 |
| Anti-skills | — | — | 5 | 0 | 0/1/0 | 0 | 22 / 9 | 26 |
| Pharmacy failure classes | — | — | 5 | 1 | 2/1/0 | 0 | 18 / 12 | 42 |
| Two-signal guard dispositions | WF14, WF19, WF41, WF52*, WF53, WF54 | WF52*, WF54 | 5 | 2 | 1/3/2 | 2 | 9 / 3 | 34 |
| Typed capabilities / lifecycle | — | — | 1 | 0 | 0/0/0 | 0 | 1 / 0 | 6 |
| Contractive meta-operads / X-to-Y verifiers | — | — | 0 | 0 | 0/0/0 | 0 | 1 / 0 | 2 |
| Prompt operad (colours, anti-ops) | — | — | 0 | 0 | 0/0/0 | 0 | 1 / 0 | 4 |
| Operational trace quotient | WF53, WF54 | WF53 | 1 | 0 | 0/0/0 | 0 | 2 / 0 | 3 |

## How each workflow touches operads

| WF | What it does with operads | Mode | What is asserted |
| --- | --- | --- | --- |
| WF2-WF5 | Model proposes operad candidates (arity, source/target colours) and DDC moves | live + offline | Shape: arity = source count, unique IDs, references resolve. Candidates stay unverified. |
| WF14, WF19, WF41 | EIS two-signal admission of detector rules (`pfp_core/immunity.py`) | offline | Thymus kills rules that fire on the self panel; admission needs a host danger signal. |
| WF26 | Adds an antibody (constraint) per failed epitope during one dialogue | offline | Antibodies are answer-free; repair within budget. |
| WF20, WF33, WF40 | DDC lift (Λ) grants as host-issued licences | offline | A lift needs a grant; fuel and restart bounds hold. |
| WF52 | Calls `operads.domain.operad` associativity verifier and colour composition in attack tests | live (recorded) | Ill-typed triples refused, well-typed pass; source custody pins operad files. |
| WF53, WF54 | `quotient_workflows` collapses duplicate context skills before spend | offline | Equal traces quotient together; order of non-context ops kept. |
| Others | None | — | — |

## Test health (run 2026-11-14, Linux)

| Suite | Result | Notes |
| --- | --- | --- |
| Rust `core_operad_canon` | 7 pass | Canon table well formed; Python/JSON renderings current. Not run in CI. |
| Rust `core_operad_theory` lib | 72 pass, 2 fail | Rename slip in two expected strings (fix held back, below). |
| Rust `core_operad_theory` `canonical_parity` | 3 pass, **5 fail** | Frozen Python fixture was hashed with the pre-rename domain strings; the Rust kernel now hashes `core.*`, so every canonical ID changed. Not fixed: needs a decision (see gaps). |
| Rust `core_operads` | 56 pass | |
| Python `operads/tests` + operad-using `pfp/tests` | 1,853 pass, 297 fail, 23 errors | About 195 need engine files absent from this repo (the `core_symbol_game` binary, `.agents/`, `engine/crates_rs/`); 13 are API drift (`persist_bout_run_folder` signature); 7 need a real OpenSSH signer; the rest are mixed. CI (`operad_gates.yml`) runs 5 of these test files. |
| Python workflow families + `pfp/workflows` | all pass but 1 | `test_standalone::test_missing_optional_native_budget_is_a_typed_refusal` (message regex). |
| Lean 4 | not built | Operad theorems: `lean4/OperationTreeFold.lean` (effect closure, outputs are not authority), `education/008_oeop/lean4/WasOperads.lean` (identity is unary). No law theorems. Not in CI. |

## Ranked gaps

1. **Failure learning is open-loop.** Failures are classified and repaired
   inside a run, never stored and reused. Nothing turns an LLM's refusal or
   wrong answer into a persisted antibody, anti-skill or DDC trace that the
   next run reads, and nothing measures whether that helped.
2. **Workflows do not run the canonical operads.** 0 of 54 workflows import
   the canon. The colour vocabulary in WF2-WF5 is not the canonical one, so a
   WF2 operad candidate cannot be typed against the operad crate.
3. **Laws are signature-level only.** Associativity and unit are checked on
   colour signatures for given triples; behaviour, residuals and effects are
   not (NaN counterexample in `SYS-OP-002`). No Lean statement of any law.
   Equivariance (symmetric operads) has no workflow and one Rust test.
4. **PFP 018 (operadic composition and bounded DDC repair) is mostly
   unsupported.** P018-002 to P018-005 are gaps: the C, R, E, I, M, T repair
   slice in `operads/application/ddc_execution` has no workflow and no DAG
   node. P017-003 (non-faithful prompt trees form an operad ideal) is a gap
   with no code found.
5. **The operad test suite is mostly untestable here.** About 200 of 320 red
   tests depend on engine artifacts that live outside pfp; they can never pass
   in this repo or in CI as written. The Rust operad crates are not in CI.
6. **Canonical ID drift after the rename.** The parity fixture cannot be
   regenerated (the Python generator is retired). Either the Rust kernel keeps
   the old domain strings as stable identifiers, or the fixture is re-pinned
   from Rust and loses its independent check.
7. **Untouched families.** Registered operands, typed capabilities and
   lifecycle, contractive meta-operads and X-to-Y verifiers, and the prompt
   operad have no workflow and no derivation, and at most one DAG node each.

## Proposed workflows (not built)

Superseded on 2026-11-14 by the redesign in
[`docs/plans/operads_redesign.md`](../docs/plans/operads_redesign.md): checks move to
Rust, and gaps 1 to 3 have a first fix in `code/rust/pfp_operads`.

- **Failure-to-antibody loop.** Read frozen failure records from WF1-WF5 and
  WF52 runs, classify them with WF14, write each admitted antibody or
  anti-skill to one typed, hash-chained failure ledger with its DDC trace, and
  have the next run load only admitted entries. Score it with WF19's held-out
  gain, so a learned rule is kept only if it helps on unseen tasks. Closes
  gap 1; offline first, then one cheap live run.
- **Operad law battery.** Offline, no model. For every canonical colour and
  operation, check associativity, unit and equivariance on behaviour (outputs
  and residuals, not just signatures) in Python and Rust, with mutation
  controls that must fail. Emit one DAG node per law. Closes gap 3 and feeds a
  Lean statement of the same laws.
- **Bounded DDC repair slice.** Wrap `operads/application/ddc_execution` as a
  workflow: supplied candidate patches run C, R, E, I, M, T with the
  worked example and the negative cases from PFP 018. Closes gap 4.
- **Canon alignment for WF2-WF5.** Type the model's operad candidates against
  `operads.canon` colours and the DDC alphabet, so a proposal can be checked by
  the operad crate instead of by shape. Closes gap 2; small, no new workflow.

## Small fixes found, held back

Each is a few characters, but each file is under the SCORING.md floor and is
grandfathered only while its bytes are unchanged; editing it needs a completed
score first. They are listed here so a scoring pass can apply them.

- `code/rust/core_operad_theory/src/kernel/canonical.rs` (L4D): two unit tests
  still expect the pre-rename test domain; the code under test now
  writes `core.test`. Change the expected strings to `core.test` and both pass
  (verified: 74/74).
- `operads/tests/unit/test_prompt_hierarchy.py` and
  `test_pfp_operad_dof_and_qm_antibodies.py` (L2D): the repository-root lookup
  needs an `.agents/` folder that pfp does not have, so both files fail at
  collection. Anchoring on `operads/` plus `pyproject.toml` collects them: 20
  tests pass, 10 still need engine files (verified).

Also, the matrix comes from `dag/operad_coverage.py`, added with this report.
