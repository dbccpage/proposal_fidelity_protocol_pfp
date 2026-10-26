# Historical Genesis recovery and replay

All 25 original Genesis specifications, the suite harness, master report, and receipt were recovered from Git commit `5e5e64e441da1c357179b6979daa9f780dcc36b4`, tree `e955f8014523b5cab13843a94fbd1191402a63c0`. The directory was deleted in commit `6ab48c9c1ff04ff96a12878de557d3b5d5746b82`. These 28 files total 324,333 raw bytes. They are historical sources, separate from the current PFP source snapshot. This historical suite slice contains no sealed 19L57G1 text. The separate bounded G07 dependency recovery below includes the precise sealed mathematical definitions needed by that computation.

[The manifest](recovery_manifest.json) records every original path, Git blob, SHA-256, byte count, and recovered path. The recovery program has a fixed allowlist of original commit/path/blob identities. Verification independently recomputes the Git blob identifier from the raw bytes, checks the SHA-256 and size, rejects duplicate or omitted entries, and rejects substituted commits, paths, and blobs. Rehashing a modified file and manifest cannot authorize a replacement for a pinned historical blob.

The report's raw SHA-256 is `e957924113b7c0a14efa57714ae1c13a4c0c9f2d3c02df2c14ce16fb83d01db4`, which agrees with the retained receipt. The recovered receipt ID is `REC_GENESIS_SUITE_1790618314`, status `PARTIAL`. The findings note cites `REC_GENESIS_SUITE_1790611114`; that citation does not identify this recovered receipt. Git history for the receipt path records its creation and deletion, with no intervening replacement. The recovered receipt does not settle the provenance of the differently named receipt in the note.

Demo 10's two dossier checkers lack adjacent inputs, but all six original input/witness files are retained in the current snapshot under `demos/inputs/demo_10/<dossier>/`. [Their location accounting](demo10_input_location_accounting.json) shows that each current Git blob and every raw current file is identical to its original input at commit `dc59fbf4f1f1e9c7f650e1b321de39cc4d0c18d5`. No historical input copy or newly constructed witness is needed. The replay adapter binds those current paths and copies their pinned bytes into its temporary dossier directories. Demo 11 and 12 retain their inputs beside their checkers.

[The complete replay](genesis_replay.json) binds the manifest and records every G01–G25 source specification, its exact formal problem, output contract, capability gate, and external references. Every row separates the historical model label, the historical Lean outcome, the replayed harness flaw, and the outstanding positive computation.

## Actual retained code replay

The original [harness](recovered_sources/run_genesis_suite.py) contains executable definitions for parsing specifications, constructing prompts, parsing model JSON, the danger gate, the Lean snippet checker, and the artifact verifier. The replay selects these whole original AST definitions without changing their bodies. It omits top-level environment loading, `sys.path` mutation, and the provider/budget runner. External historical ground truth is explicitly unbound and records each attempted access; the subprocess capability is blocked. No provider, Lean compiler, Cargo build, or 19L57G1 process is invoked.

The original artifact verifier initializes `verified` to `true` and never sets it to `false`. For every one of the 25 specifications, replay supplied three explicit adversarial inputs: an empty response, a response for the wrong challenge claiming `CHECKED` without a proof, and an `UNKNOWN` response without a proof. All 75 received `verified: true`. These are reproduced verifier defects, not certified mathematical results. Each actual input and verifier output is retained with an input digest.

For G25, the original verifier emitted “confirmed 0 occurrences in source” without making a ground-truth access. The exact same behavior is reproduced with the source capability unbound. A reconstructed prompt for every challenge contains the original declaration that an identification is “FALSE BY CONSTRUCTION”; no independent correspondence study is inferred from that prompt.

The danger gate reproduces both working and defective controls. It rejects its explicit assertion pattern and a `CHECKED` claim with neither proof nor data, and permits neutral wording. It accepts nonsense placed in the data field and misses “A datum is a DDC letter.” It also rejects a sentence explicitly rejecting the phrase “identical to 19L57G1.” The original JSON parser accepts a fenced wrapper despite the prompt requiring an RFC 8259 JSON object. The original Lean lexical checker refuses forbidden tokens, including `sorry` inside a comment; these lexical refusals are not Lean compilation.

## Historical claims and unavailable bytes

The retained report reproduces the note's label census: 11 `CHECKED`, one `CHOSEN_ANALOGY`, and 13 `OPEN`. Of the 11 `CHECKED` rows, six reported Lean timeouts, two reported failures, three reported no snippet, and none reported a successful compilation.

The suite's report-construction code does **not** persist the raw provider response or `lean_code`. It retains proof sketches and Lean outcome metadata only. Thus the eight reported snippets cannot be recompiled from this source slice, and the actual historical raw responses cannot be independently parsed or rescored. Report-derived input replay is explicitly named as such. It is not a replay of the missing raw model bytes.

The historical recovered directory contains planned specifications and the batch harness, rather than the different mathematical implementations, statement pins, native action implementations, certificates, and held-out results required by the individual specifications. The historical harness replay marks none of its 25 positive capability gates satisfied. Missing historical raw model replies and submitted proof snippets do **not** imply missing external mathematical definitions: [the exact-pin availability ledger](external_pin_availability.json) resolves 69 literal 19L57G1 paths at both declared pins and 38 H3V7N5QF paths at its declared pin. Nineteen of the 69 paths exist at the sealed 19L57G1 pin; all 69 exist at the specified research pin, and all 38 H3V7N5QF paths exist at its pin. [The independent audit](external_pin_independent_replay.json) verifies all 176 pin/path checks against actual Git tree/blob bytes, including the 50 paths absent at the sealed pin. These documents establish source identity, not mathematical correctness.

[The new G07 provider-free computation](g07/README.md) separately closes the original census baseline, held-outs, and falsifiers using those available definitions and native primitives. It preserves the historical all-positive-false harness receipt. G07's model-arm experiment remains unperformed. The current canonical Genesis crosswalk demo has its own source-pinned replay elsewhere in Paper 011; an expected `NO_NATIVE_PORT` refusal does not implement G13's three required native actions.

[The new G12 Lean reconstruction](g12/README.md) separately checks all five original Iso construction obligations, including the two held-outs, through an environment census, exact Prop wrappers, concrete instances, actual axiom reports and all five original refusal controls. Its unchanged parked and full axiom-artifact gates pass; the whole external estate workflow and model-arm experiment remain unperformed. This new computation does not replace any historical report or the historical all-positive-false harness receipt.

| Challenge | Historical label | Historical Lean outcome | Outstanding intended computation |
|---|---|---|---|
| G01 | CHECKED | Timeout; snippet not persisted | Reading-F pinned non-uniqueness, five classes, and k-ary family proof/refutation |
| G02 | CHECKED | Timeout; snippet not persisted | General cut-census formula under the sealed definitions |
| G03 | OPEN | No snippet reported | Actual 455-pair adapted `min_responses` calls and complete call-log checks |
| G04 | CHECKED | No snippet reported | First-demand isomorphism invariance under the pinned contract |
| G05 | OPEN | No snippet reported | Decidable demand procedure and required checks |
| G06 | CHECKED | Timeout; snippet not persisted | NS10 commuting-square closure proof |
| G07 | OPEN | No snippet reported | Original provider-free census baseline closed separately; model-arm experiment remains unperformed |
| G08 | CHECKED | Failed; snippet not persisted | Actual source/compiled-path injections and successful reversals |
| G09 | CHECKED | Timeout; snippet not persisted | Pinned Alpha Engine Python-driver refinement |
| G10 | OPEN | No snippet reported | Actual Alpha Engine proposer integration and guarded execution |
| G11 | CHECKED | Timeout; snippet not persisted | M114 solver adapter wiring under its declared contract |
| G12 | OPEN | No snippet reported | Original provider-free P1–P4 wrappers/census/instances/axioms and falsifiers checked separately; whole-estate/model experiment remains unperformed |
| G13 | CHECKED | No snippet reported | Three native raw-byte, anchor, and wording audit actions and held-out controls |
| G14 | OPEN | No snippet reported | Licensed endogenous-demand generator search |
| G15 | OPEN | No snippet reported | Unboundedness engine driver and required evidence |
| G16 | CHECKED | No snippet reported | Tied-minima census beyond the stated original bounds |
| G17 | CHECKED | Timeout; snippet not persisted | Second-derivation challenges 3–5 |
| G18 | OPEN | No snippet reported | X6 definability census rows |
| G19 | OPEN | No snippet reported | NS5 proof-relevant cell calculus |
| G20 | OPEN | No snippet reported | H3V7N5QF closed forms |
| G21 | OPEN | No snippet reported | H3V7N5QF CR2 reachability criterion |
| G22 | OPEN | No snippet reported | H3V7N5QF A-perform lower bound |
| G23 | CHECKED | Failed; snippet not persisted | H3V7N5QF choice-free reproofs |
| G24 | OPEN | No snippet reported | Actual seed-edit ablation study and four-hole behavior |
| G25 | CHOSEN_ANALOGY | No snippet reported | Complete typed crosswalk, statement/axiom checks, and bounded native replay |

Every row's original §3, §4, and §9 in `genesis_replay.json` supplies the precise obligation; the short descriptions above are not substitutes for those contracts.

## Reproduction

Run from the Paper 011 directory with Python 3.12. Recovery needs an explicitly declared repository containing the pinned Git objects. Subsequent custody verification and harness replay use only the recovered paper files and the Python standard library.

```powershell
py -3.12 code/history_recovery.py recover --repository C:/Users/a343o/.codex/worktrees/1a33/the_symbol_game
py -3.12 code/history_recovery.py verify
py -3.12 code/history_recovery.py replay
py -3.12 -m pytest code/tests/test_paper011_history_recovery.py --basetemp C:/Users/a343o/AppData/Local/Temp/paper011-history-recovery-tests
```

[The replay receipt](replay_receipt.json) binds the replay output and authored code. The focused tests reject raw source corruption, rehashed substitutions, duplicate or omitted identities, changed commits, report/receipt digest mismatch, and a duplicate G ID even after a report is self-rehashed. They verify all 25 bug replays and keep all positive-obligation flags false.
