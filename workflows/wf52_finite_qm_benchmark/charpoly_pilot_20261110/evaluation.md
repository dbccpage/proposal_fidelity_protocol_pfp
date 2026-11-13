The checked characteristic-polynomial workflow delivered no solution and scores **0/100**. The ungated workflow delivered a partial solution and scores **47/100** under the same unchanged 25-criterion rubric.

| Arm | Spectrum | Dynamics | Pure entanglement | Thermal | Checks | Total | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Checked | 0/20 | 0/20 | 0/25 | 0/25 | 0/10 | 0/100 | $0.001685 |
| Ungated | 20/20 | 17/20 | 4/25 | 0/25 | 6/10 | 47/100 | $0.005329 |

The checked run refused synthesis: `answer_text` and its hash are null. The initial artifact failed with `RATIONAL_NONCANONICAL`; the repair failed with `MALFORMED_JSON`. Neither reached native polynomial checking. The initial call ended normally after 196 output tokens; repair reached its 2,400-token ceiling. This is zero delivered-solution credit, not an asserted wrong final mathematical answer. The attempt remains in the denominator.

All 641 lines (35,015 characters) of the ungated final answer were read. It provides the spectrum and merged degeneracy projectors, general evolved state, probability/supremum and reduced density matrix. Its final call reaches the 12,000-token ceiling and stops mid-formula while expanding that reduced matrix. Entropy, concurrence, CHSH, maximal-entanglement reachability/timing and every thermal result are absent. Headings earn no credit.

The ungated answer also incorrectly says constant probability has no unique earliest maximizing time: on t>=0, the earliest is 0. It omits a separate zero-radius evolved ket. The generic eigenvector formulas have singular denominators at J=0; its earlier explicit computational-basis eigenvectors and energies supply that exceptional spectral branch and receive credit. No nontrivial numerical example is delivered.

Total campaign spending was 7,014 microUSD ($0.007014), with zero held charges. Only final-answer content supplied mathematical credit. Proposal/repair text, checker labels and earlier answers supplied none. Refusal codes and call metadata were inspected separately to explain delivery outcomes.

This one-item, one-attempt-per-arm result demonstrates an encoding refusal in the checked path and a truncated partial solution in the ungated path. It does not establish a general benefit of native checking, gating, or the broader system. In particular, the checked run never exercised native polynomial comparison, so its outcome does not measure that mechanism's mathematical effectiveness.

Both frozen run/answer/seed bindings, all 50 criterion judgments and exact evidence ranges are recorded in `grades.json` and `criterion_evidence.json`. `evaluation_validation.json` retains arithmetic/custody checks and the bounded controls. Reference provenance was frozen before output access; later parent authorization allowed each run to be graded after its individual freeze. No unfrozen output or private answer key was accessed.
