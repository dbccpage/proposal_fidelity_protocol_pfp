# Research 08: finite checker adequacy and fault propagation

Status: **proposed, not evaluated**. The companion `research_08.json` carries the full typed DAGs, assumptions, evidence spans, hypotheses, ablations and conditional budgets. I did not read `seed_prompt.txt`, the private benchmark storage or answer key. No benchmark answer, model output, paid call or runtime campaign is included.

The three proposals separate three failure surfaces: a broken checker, an extractor that erases a relevant distinction, and a workflow that loses a correct local finding before its final output. They combine existing PFP checking, EIS finite clean-panel screening, PCIV protected mutation lineage and OPERADS typed interfaces. The adaptations remain unimplemented.

| Proposal | Mechanism | Model calls | Conditional full-path reserve |
|---|---|---:|---:|
| R08-I01 | Cross checker mutations with independently labelled artifact faults before one draft/repair pair | 2 | USD 0.045 |
| R08-I02 | Challenge extractor-detector interfaces with equal-extraction, unequal-label pairs | 2 | USD 0.042 |
| R08-I03 | Inject artifact, receipt and routing faults; require findings to reach dependent sinks | 1 | USD 0.039 |

These reservations assume input <= USD 0.000001/token, output including reasoning <= USD 0.000005/token, zero per-call fees and USD 0.01 reserved for fully bounded other charges. They are admission thresholds, not live price quotations. Every request includes the unchanged seed and all context in its input allowance. Zero retries and fallbacks are permitted. All paths share the USD 0.10 ledger; calibration is bounded unmetered local computation, or its charge must fit the reserve. Unknown charges refuse execution. A campaign requires a separate aggregate limit.

## R08-I01: two-axis checker assurance

Ordinary mutation testing asks whether a checker rejects a corrupted candidate. This workflow also asks whether the test panel exposes a corrupted checker. Freeze a public synthetic relation, independently implemented labels, nonempty clean/fault panels and operators such as inverted comparisons, omitted feasibility checks and stale binding acceptance. PCIV protects those contracts while recording checker mutations. EIS screens the actual bound executable against clean controls. PFP independently replays counterexamples. OPERADS carries the resulting scoped receipt.

For labelled cases `(x_i,y_i)` and mutated checkers `V_j`, publish `K_ij = 1` only when the original agrees with `y_i` and the executable mutant disagrees. Crashes, timeouts, unsupported results and mutants of unknown equivalence remain separate categories. Constant-accept and constant-reject variants must fail their dedicated controls. A syntactic mutation is not automatically a semantic fault.

The typed path is `FrozenRunContract -> CalibrationReceipt -> CandidateArtifact -> ScopedFindingList -> repaired CandidateArtifact -> FrozenResponse`. A preflight failure ends the branch without paid calls. The longest path uses 14,000 aggregate input and 4,200 output tokens. The comparator is a matched two-call draft/review with candidate-only mutation controls. The hypothesis fails if false certification does not decline on the frozen synthetic confirmation panel or clean rejection rises more than two percentage points. Checker/reference specification errors remain possible.

## R08-I02: protected-distinction challenges

Let `E:X->Z` be an extractor and `D` a deterministic detector over its output. If `E(x)=E(y)` while the intended public relation gives different labels, `D` cannot classify both correctly. This is an interface-level impossibility witness, even when `D` is nonconstant elsewhere. A finite panel with no collisions does not establish global injectivity or completeness.

Use separately authored synthetic pairs for copied-input drift, deleted citations, unsupported-node deletion and changed values with unchanged shape, alongside semantics-preserving controls. Independently replay their labels. A cochain admission channel that enforces `d1*d0=0` and then reports its norm cannot distinguish semantic faults among admitted inputs on that channel alone. Keep structural admission and semantic validity as different fields.

PCIV freezes extraction policies; EIS preserves valid controls; PFP supplies relation witnesses; OPERADS propagates unseparated-pair residuals. The path is `FrozenInterfaceContract -> DistinctionReceipt -> CandidateArtifact -> ScopedFindingList -> repaired CandidateArtifact -> FrozenResponse`. It uses at most 12,000 aggregate input and 4,000 output tokens. Compare against nonconstant-output/syntax controls alone, including held-out fault families rather than only fresh values of the same templates. The hypothesis fails if the protected-pair screen does not reduce false certification. Any globally certified equal-extraction/unequal-label pair directly falsifies the scope contract.

## R08-I03: end-to-end propagation canaries

Local detection is insufficient when a later stage drops a residual or reuses a stale receipt. For each required edge `u->v`, require unresolved obligations at `u` to remain at `v` unless a checked repair discharges the specific obligation with new artifact bindings. Record a fault-by-stage matrix and count an end-to-end success only when every required dependent sink receives a replayable finding or becomes explicitly open.

Inject public synthetic faults into values, checker receipts and routing: stale parent hashes, bypassed checks, same-type invalid receipt substitution, dropped residuals, codec mismatch, duplicated correlated signals and cancelling intermediate errors. Distinguish final-value validity from proof-trace validity; a false intermediate step can coexist with a correct final value. Use the independent host health/custody condition for EIS's second signal, never another model assertion.

The path is `FrozenPipelineContract -> PropagationMatrix -> AdmittedPipelineReceipt -> CandidateArtifact -> BoundReceiptDAG -> FrozenResponse`. It uses one model call with at most 9,000 input and 4,000 output tokens. Compare against local-only checking at the same model cap. A mandatory fault reaching a certified dependent sink without a checked discharge falsifies propagation. The scheduler and receipt verifier remain explicit trusted components.

## Evidence and limits

- `lean4/FidelityAdequacy.lean:146-180` derives rejection of constant detectors from positive/negative controls and records protected distinctions and blind spots.
- `pciv/profile/cochain_profile.py:132-158` admits only zero `d1*d0`, making its returned `phi1` zero for admitted inputs.
- `pfp/use_cases/detector_adequacy/detectors.py:230-299` distinguishes lenient extraction, a first-citation tree, and strict relation extraction.
- `pfp/tests/test_detector_adequacy_battery.py:26-52,88-98` retains explicit tree, citation and upstream blind spots; these tests were inspected, not rerun.
- `pfp/use_cases/detector_adequacy/witness_replay.py:56-101` re-derives synthetic relation witnesses and separately checks final answers.
- `eis/domain/thymus.py:145-178` tests the actual bound matcher and avoids the inactive-rule vacuity. Its clean-panel scope is explicit at lines 1-16.
- `eis/domain/danger_gate.py:184-222`, `pciv/use_cases/research_mutation.py:8-31`, and `operads/domain/operad/operad.py:85-124` supply provenance checks, protected mutation and typed substitution components.

The inspected `detectors.py:303-324` obstruction branch references `core.items()` without an assignment in that function. This apparent runtime defect was reported to the coordinating agent and was not repaired. Any calibration exception must be reported as infrastructure failure, never a mutation kill.

Mutation analysis is established, and its relation to real faults is empirical rather than universal. The original study by [Just et al.](https://homes.cs.washington.edu/~rjust/publ/mutants_real_faults_fse_2014.pdf) supports investigating that relation while documenting limits. [Ojdanic et al.](https://arxiv.org/abs/2112.14508) motivates checking semantic fault effects rather than relying on syntactic resemblance. [Petrovic et al.](https://arxiv.org/abs/2102.11378) motivates bounded mutation inventories. None establishes adequacy for this benchmark.

Development panels and independently seeded confirmation panels are separate public synthetic resources. Freeze candidate checker/pipeline selection before confirmation; a failed confirmation does not trigger in-run tuning. Distinct random seeds do not establish independence of implementations or source assumptions. Freeze benchmark answers before trusted private evaluation and never route its scores, labels or diagnostics back into online stages.

The reusable primitive is `FiniteAdequacyReceiptV1`: hashes bind relation, checker, extractor, reference, panel, mutation plan and artifacts; statuses separate finite-panel pass, control failure, unsupported scope and infrastructure error; residuals retain blind spots and shared dependencies. Finite controls can falsify some adequacy claims. Their success cannot establish global semantic adequacy.
