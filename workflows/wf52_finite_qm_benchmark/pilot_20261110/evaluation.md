# Independent post-freeze evaluation

The five original final responses score **1, 7, 3, 13 and 8 /100** (direct, self-critique, fixed, blind and visible respectively). All were graded against the unchanged pre-output rubric. Partial readable mathematics was scored even when the JSON envelope failed. No draft or challenge received credit.

| Workflow | Spectrum /20 | Dynamics /20 | Pure /25 | Thermal /25 | Checks /10 | Total | Final output |
|---|---:|---:|---:|---:|---:|---:|---|
| direct | 0 | 0 | 0 | 0 | 1 | 1 | length-truncated |
| self_critique | 5 | 0 | 0 | 0 | 2 | 7 | length-truncated |
| rational_fixed_panel_v1 | 0 | 0 | 0 | 1 | 2 | 3 | stopped / envelope invalid |
| rational_blind_panel_v1 | 11 | 0 | 0 | 0 | 2 | 13 | length-truncated / envelope invalid |
| rational_visible_panel_v1 | 7 | 0 | 0 | 0 | 1 | 8 | length-truncated / envelope invalid |

- **Direct:** repeats contradictory tensor-product calculations and truncates before obtaining the full Hamiltonian or any requested result.
- **Self-critique:** the final correction substitutes a wrong Hamiltonian. For J=1, Delta=K=0 its spectrum has trace-2, while the given Hamiltonian has trace0. It truncates in projectors; later parts are absent.
- **Fixed panel:** returns a schema-wrapped promise of a derivation, not the derivation. Only conventions and the general partition-function definition receive credit.
- **Blind panel:** gets the Hamiltonian block right, then loses a factor2 in its odd energies and propagates that error into degeneracies/eigenvectors. It truncates before dynamics.
- **Visible panel:** drops the -2Delta diagonal entry, derives the spectrum of that different block, and mishandles zero-radius degeneracy. It truncates before dynamics.

Four final answers hit length limits; the three panel attempts also fail their required envelope. Those operational outcomes remain distinct from mathematical scores. These five one-item, one-sample results do not establish a workflow ranking, transfer or statistical advantage.

All25 criterion scores, exact character-span evidence, deductions, counterexamples and run/answer/seed hashes are in criterion_evidence.json and grades.json. The reviewed summarize_runs.read_frozen_receipt and validate_grade checks pass for all five. The rubric uses pure_state/thermal labels; the grade adapter maps these unchanged weights to pure_entanglement/thermal_entanglement required by the summary schema.

Provenance limitation: one attempted metadata-only inspection over-expanded nested provider request/response material. No intermediate content was used for scoring. No private answer key/storage was accessed and no evaluator correction was sent to workflow requests.

## Separately frozen operational repair

The sixth run, **rational_fixed_panel_v2**, scores **10/100**: spectrum8/20, dynamics0/20, pure-state0/25, thermal0/25, checks2/10. Its required JSON envelope remains invalid and final response is length-truncated. It displays the correct detuning contribution, then drops its factor2 in the assembled Hamiltonian. At J=0, Delta=1, K=0, its odd energies are±1 instead of±2. The correct even projector and some bounded spectral subcases receive partial credit; dynamics, entanglement and thermal derivations are absent.

This revision is exploratory operational repair after seeing original formatting/length failures, not another preregistered independent replicate. It uses the same unchanged grading rubric and receives no extra credit for improved field names. Root independently reported the same detuning defect; the evaluator checked it directly against the frozen final text and its independently derived Hamiltonian.
