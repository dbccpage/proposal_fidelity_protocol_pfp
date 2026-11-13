# Frozen Hamiltonian workflow evaluation

All eight attempts were graded against the unchanged pre-frozen 100-point rubric. Only final `answer_text` was credited. Both checked runs refused to deliver a final answer and receive **0 delivered-solution points**; they remain in the all-attempt denominator and are distinguished from wrong asserted answers.

| Family | Repetition scores /100 | Mean, all attempts | Delivered answers |
|---|---|---:|---:|
| Direct | 3, 4 | 3.5 | 2/2 |
| Checked representation | 0, 0 | 0 | 0/2 |
| Ungated representation | 4, 4 | 4 | 2/2 |
| Host-derived matrix | 4, 4 | 4 | 2/2 |

| Run (repetition) | Spectrum /20 | Dynamics /20 | Pure /25 | Thermal /25 | Checks /10 | Total /100 |
|---|---:|---:|---:|---:|---:|---:|
| direct (000) | 1 | 0 | 0 | 1 | 1 | 3 |
| direct (001) | 2 | 0 | 1 | 0 | 1 | 4 |
| checked (000) | 0 | 0 | 0 | 0 | 0 | 0 |
| checked (001) | 0 | 0 | 0 | 0 | 0 | 0 |
| host_matrix (000) | 2 | 0 | 0 | 1 | 1 | 4 |
| host_matrix (001) | 0 | 0 | 1 | 2 | 1 | 4 |
| ungated (000) | 2 | 0 | 0 | 1 | 1 | 4 |
| ungated (001) | 2 | 0 | 0 | 1 | 1 | 4 |

The six delivered answers were read in full: 29,119 characters. All six have `finish_reason: stop`; none is length-truncated. They mostly describe calculations still to be performed. No final answer delivers the evolved amplitudes, transition probability/maximizer, reduced-state entropy, optimized CHSH value, maximal-entanglement condition/time, or thermal partial-transpose spectrum and exact entanglement condition. Generic definitions receive no credit as completed task calculations; limited credit for a formal partition trace, correct special cases, and valid partial constructions is recorded criterion by criterion.

Concrete errors retained in the evidence:

- **Direct 000:** at J=Delta=0, K=1, its displayed Hamiltonian is diag(1,0,0,-1), whereas the actual matrix is diag(1,-1,-1,1).
- **Direct 001:** at J=1, Delta=K=0, its final matrix has H[01,11]=1-i but H[11,01]=0, contradicting its Hermiticity claim. Its transition formula also drops the target overlap and gives probability 1 rather than 0 at t=0 in a diagonal computational eigenbasis.
- **Ungated 001:** at J=1, Delta=K=0, it asserts eigenvalues 1,0,0,-1. The actual values are 2,-2,0,0; its own displayed matrix instead has sqrt(2),-sqrt(2),0,0.
- **Ungated 000:** its Y tensor Y action on |01> has the wrong sign. Combined with its correct X tensor X action, this falsely cancels the exchange transition instead of giving 2|10>.
- **Host matrix 000:** despite the supplied representation, its final eigenvalue list gives 0,0,-1,1 at J=1, Delta=K=0 instead of 0,0,-2,2.
- **Host matrix 001:** it asserts equal imaginary off-diagonal entries -iJ in transposed positions, so its matrix is non-Hermitian for nonzero real J. It also incorrectly calls K Z tensor Z independent spins; the nonzero-temperature Gibbs state generally has classical correlations.

The host 001 concurrence expression contains +lambda2. This alone is not treated as a pure-state falsification: the extra square-root eigenvalue vanishes for a pure state with the nonzero root ordered first. It receives limited construction credit, with deductions for missing ordering, evaluation, and derivation.

`grades.json` binds each grade to its run, answer, seed, and original rubric hashes. `criterion_evidence.json` contains all 200 criterion assessments, exact final-text character spans, omissions, and counterexamples. `evaluation_validation.json` records independent receipt/schema/hash/span/arithmetic checks and finite counterexample controls.

This is two repetitions per family on one item. The small score differences do not support a general ranking or demonstrate benefit from matrix preprocessing. The checked arm prevented delivery of an unaccepted representation, while the host control demonstrates that a correct intermediate representation alone did not ensure a correct final solution in these runs. No private answer key, intermediate proposal content, or nested provider evidence was read; the old experiment and its grades were not modified.
