# Operad redesign: Rust checks, Python does not

AuthorityEffect: None. This is a plan and a status table, not a result.

## The rule

Decided by Jeremy on 2026-11-14: **in this repository Python checks nothing.**
Every check of a model's output, of an operad, of a DDC trace or of a learned
rule is done by Rust. Until the workflow hosts are ported, Python may still
call the model and move files. Order of work: operads first, then the
workflow hosts.

Should anything be checked in Python here? No:

- Two checkers drift. The Python and Rust operad kernels already disagree on
  every canonical ID after the rename, and about 200 Python operad tests
  cannot pass in this repository at all.
- The Rust is already here: 35 crates, including the canon, the operad
  kernels, the DDC tape verifier and the immune system.
- One binary that anyone can run is easier to replay and to trust than a
  Python package with 109,000 lines.

Two Python tools check the repository itself and not PFP results: the
SCORING.md checker (`governance/tools/checker.py`) and the atlas builder
(`dag/build_atlas.py --check`). This plan leaves them alone.

## The design

```
model reply (typed JSON)
      │
      ▼
pfp_operad check ──► HOST_VERIFIED / UNVERIFIED_CANDIDATE / REFUSED
      │ a refusal or a wrong answer is a failure
      ▼
pfp_operad ledger append   failure ─► candidate rule ─► held-out trial ─► admission
      │
      ▼
pfp_operad ledger admitted ──► the rules the next run loads
```

- **One canon.** Colours, DDC letters, failure classes, capability kinds and
  rule statuses come from `core_operad_canon`. A name outside it is refused at
  the boundary.
- **Operations can be run.** A proposed operation carries a body from a closed
  list, so the host can execute it against the task's own data instead of
  filing it as unverified.
- **Laws are checked on behaviour.** Values, exact cost and tree shape, not
  only colour signatures. There is no float, so the NaN-residual
  counterexample (`SYS-OP-002`) cannot be built.
- **Learning is a closed loop with a record.** A failure is stored with its
  class and DDC trace. A rule proposed from it is loaded by a later run only
  after it beats the baseline on held-out cases and fires on no clean case.
  A rejected rule can be tried again; a retired one cannot.
- **Everything is typed.** Requests reject unknown fields; outcomes are one
  of `PASS`, `FAIL`, `REFUSED`.

## Gaps from the review and where each is fixed

Gap numbers are from [`dag/operad_coverage.md`](../../dag/operad_coverage.md).

| Gap | Fix | Slice | Status |
| --- | --- | --- | --- |
| 1. Failure learning is open-loop | Failure ledger with trial-gated admission | 1 | **built** |
| 1. (cont.) no workflow writes or reads it | Failure-to-antibody workflow; WF1-WF5 and WF52 write failures, every run loads admitted rules | 2 | planned |
| 2. Workflows do not use the canon | `pfp_operad check` types candidates by canon colours and runs them | 1 | **built** |
| 2. (cont.) WF2-WF5 still use their own colours | WF2-WF5 call `pfp_operad check`; their Python operad checks are deleted | 2 | planned |
| 3. Laws are signature-level only | Law battery on values, cost and tree | 1 | **built** |
| 3. (cont.) no Lean statement | Lean 4 theorems for the term model: associativity, unit, composition is evaluation | 6 | planned |
| 4. PFP 018 repair slice has no workflow | Workflow over the Rust DDC tape verifier (`code/rust/pfp/src/ddc.rs`), writing to the ledger | 3 | planned |
| 5. Operad tests cannot pass here | Retire Python `operads/` from pfp; engine-only tests go back to the engine | 5 | planned |
| 6. Canonical IDs drifted | Rust is the only source; re-pin the fixture as a regression file; fix the two stale test-domain expectations in `core_operad_theory` | 5 | planned |
| 7. Untouched families | Capability kinds, failure classes and statuses are used by the ledger; the rest are typed as workflows are ported | 1, 4 | partly built |

## Slices

1. **Operad host** (this change). Crate `code/rust/pfp_operads`, binary
   `pfp_operad`: typed terms, law battery, failure ledger, JSON entry points,
   CI. See its [README](../../code/rust/pfp_operads/README.md).
2. **Wire the workflows to it.** WF2-WF5 send candidates to `pfp_operad
   check`. A new failure-to-antibody workflow turns recorded failures into
   rules, scores them on held-out tasks and admits the winners. Offline first,
   then one cheap live run to see whether an admitted rule changes a model's
   result.
3. **Bounded DDC repair** as a workflow, from PFP 018's worked example and
   negative cases.
4. **Port the workflow hosts.** The family runtime behind WF6-WF51, then
   WF1-WF5 and WF52-WF54. After this slice Python only calls the model and
   moves files.
5. **Retire Python `operads/`** (682 files) once nothing imports it, re-pin
   the canonical ID fixture, and score the Rust files that change.
6. **Lean.** State and prove the laws for the term model, and link each
   theorem to its DAG node. Needs a machine with Lean 4.

## What slice 1 does not claim

- No workflow calls the host yet, so no model result has changed.
- A law pass covers the supplied operations on the supplied panel.
- The ledger checks that a trial is well formed and held out; it does not
  rerun the trial.
