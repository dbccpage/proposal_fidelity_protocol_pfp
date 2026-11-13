# Independent grading: larger-model Hamiltonian pilot

All three final receipts are frozen and graded under the unchanged25-criterion/100-point rubric. Only delivered answer_text earns credit. The independently derived reference was frozen before any output access; no private answer, prior grade or prior counterexample was consulted.

| Workflow | Spectrum /20 | Dynamics /20 | Pure /25 | Thermal /25 | Checks /10 | Total /100 | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|
|hamiltonian_checked_v1|0|0|0|0|0|0|0.000606|
|hamiltonian_host_matrix_v1|13|0|0|0|3|16|0.002272|
|direct|6|0|0|0|4|10|0.002239|

Total settled cost: $0.005117. The checked workflow refused before delivering a final answer. Both host-matrix and direct solvers ended with finish_reason=length at4,000 output tokens, still within the spectrum/projector section. Their later requested dynamics, pure-state and thermal results are absent.

The host-matrix answer correctly derives the Hamiltonian and eigenvalues but stops during eigenvector normalization. The direct answer incorrectly adds the even-sector XX and YY terms, producing spurious00/11 exchange and false K±2J energies; its final odd projector directions also have the wrong Delta sign. Both receive partial credit for valid local work, not for their promises to cover all parts.

The16-versus10 difference is one observed truncated within-item comparison, not a statistical or general workflow/model improvement. The refusal score0 means no delivered solution, not false assertions. A valid matrix preprocessing artifact is not a certificate of the full mathematical response.

## Preserved rubric and evidence

Rubric SHA256: `eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc`. Reference SHA256: `188307c652d4094bdbd3727c2b88e517646ffcef68c3ff9248a889703f41bb99`. Original pre-output reference-file SHA256: `b6af22874b8c901dffbe788f824f1b51006d437c42de30ca1ee62fd6da1aca58`. All75 criterion decisions, exact supporting final-answer ranges and quote hashes are in criterion_evidence.json; grades.json matches summarize_runs.validate_grade.

## hamiltonian_checked_v1

Run SHA256 `5ee8216b3132685bab2ed9a03831d06cd86200a02c1a9b1b84dfc5a5633809a3`; answer SHA256 `None`. Final-answer lines: 0.

- spectrum.block_reduction: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- spectrum.energies: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- spectrum.projectors: 0/6 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- spectrum.coincident_energies: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- spectrum.zero_radius: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- dynamics.state: 0/8 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- dynamics.probability: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- dynamics.supremum: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- dynamics.earliest_and_constant_branches: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.reduced_density: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.entropy: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.concurrence: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.CHSH: 0/6 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.maximal_entanglement_reachability: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- pure_state.earliest_maximal_entanglement: 0/3 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- thermal.Gibbs_state: 0/6 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- thermal.partition_function: 0/4 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- thermal.partial_transpose: 0/7 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- thermal.entanglement_criterion: 0/5 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- thermal.thermal_limits: 0/3 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- checks.conventions: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- checks.normalization: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- checks.initial_condition: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- checks.decoupled_limit: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.
- checks.nontrivial_numerical_example: 0/2 (lines no delivered evidence). No final answer_text was delivered after representation refusal. This is missing delivered evidence, not a finding that the absent mathematical assertion is false.

## hamiltonian_host_matrix_v1

Run SHA256 `b2b5174e2a3d6ce1abf55e3a1e72690a24a24459d6c43b0d508e9dc6030fcb9b`; answer SHA256 `afc6bea9df08b42fc00d74b50a768f7c07852c49637771b1e8e32ddcb5718287`. Final-answer lines: 336.

- spectrum.block_reduction: 4/4 (lines 31–145). Correct Pauli tensors and invariant block matrix are derived explicitly.
- spectrum.energies: 4/4 (lines 147–205). Correct quadratic eigenvalue calculation yields K twice and -K plus/minus2sqrt(J^2+Delta^2).
- spectrum.projectors: 2/6 (lines 227–256, 270–301, 304–336). Credit for the even projector and a correct generic normalized plus eigenvector, with the minus direction eventually verified. No odd outer-product projectors, complete resolution of identity or H reconstruction are delivered. The later explicit plus-vector chart is unqualified at J=0,Delta<0; earlier angle notation could cover that pole but no completed projector branch is provided.
- spectrum.coincident_energies: 2/4 (lines 209–212, 231–241). Correct coincidence equations K=plus/minus omega are identified. The text does not give the resulting rank3/rank1 eigenspaces or merge the energy-K projector; its claim that K degeneracy is exceptional there is misleading.
- spectrum.zero_radius: 1/2 (lines 214–225). Correct diagonal J=Delta=0 Hamiltonian and K,K,-K,-K energies. K=0 fourfold degeneracy and the single identity spectral projector are not stated.
- dynamics.state: 0/8 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- dynamics.probability: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- dynamics.supremum: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- dynamics.earliest_and_constant_branches: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.reduced_density: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.entropy: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.concurrence: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.CHSH: 0/6 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.maximal_entanglement_reachability: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- pure_state.earliest_maximal_entanglement: 0/3 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- thermal.Gibbs_state: 0/6 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- thermal.partition_function: 0/4 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- thermal.partial_transpose: 0/7 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- thermal.entanglement_criterion: 0/5 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- thermal.thermal_limits: 0/3 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- checks.conventions: 1/2 (lines 1–19, 129–137). Correct basis, Pauli/Y sign, real Hamiltonian parameters and unit conventions. No log-base or partial-transpose convention is delivered because those sections are absent.
- checks.normalization: 2/2 (lines 295–301, 320–334). The generic plus-vector norm is explicitly computed and the final minus direction is checked against its eigenvalue. These supply the rubric equivalent normalization/eigenpair consistency check, within the chart domain; no separate state or thermal normalization is claimed.
- checks.initial_condition: 0/2 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- checks.decoupled_limit: 0/2 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.
- checks.nontrivial_numerical_example: 0/2 (lines no delivered evidence). The final answer ends during the spectrum/eigenvector calculation at line336. This requested result/check is not present. Initial-state premises and the J=Delta=0 spectrum subcase do not substitute for evolved-state or general J=0 consistency checks.

HOST-CE01: omega=1, so sqrt(2omega(omega+Delta))=0 and the displayed numerator is the zero vector. This explicit eigenvector chart is undefined despite omega>0. The earlier angle representation can cover this case, but the final answer does not assemble a chart-independent projector or state the exception.

HOST-CE02: omega=1; energies are1,1,1,-3. Energy K has multiplicity3 and its full projector must include the odd plus subspace. The generic even projector alone is not the full energy-K spectral projector.

## direct

Run SHA256 `fc9f62d6f987b882ab035e40aa5505af0ee504a608cef0e8d9f7876aba8048b2`; answer SHA256 `d5b16b783e8ba1ebcffa3f72908d92f75e5aac6c0fedd26be3dcf9fc9eabe962`. Final-answer lines: 290.

- spectrum.block_reduction: 2/4 (lines 24–59, 105–163). The invariant parity subspaces and odd block are correct. The XX+YY sum incorrectly retains2J coupling between00 and11, making the even block wrong. Half credit for the valid odd/parity reduction.
- spectrum.energies: 2/4 (lines 137–165, 204–211, 271–279). The two odd energies -K plus/minus2Omega are correct. The even energies K plus/minus2J are false for the seed; they should both equal K. Two of the four energies receive credit.
- spectrum.projectors: 1/6 (lines 213–232, 251–267, 286–290). Limited credit for explicit correct Pe/Po projectors in the zero-radius K!=0 subcase and valid even-subspace rank-one refinements. Their generic even energy labels are wrong; the final odd vectors use the wrong Delta sign and are not eigenvectors of the stated odd block. No correct generic spectral reconstruction is delivered.
- spectrum.coincident_energies: 0/4 (lines 241–247, 281–284). The generic-degeneracy analysis uses the false even eigenvalues. It misses the permanent twofold even degeneracy and does not identify/merge the true K=plus/minusOmega coincidences.
- spectrum.zero_radius: 1/2 (lines 251–267). Correct J=Delta=0 diagonal Hamiltonian and Pe/Po eigenspaces for K!=0. K=0 complete degeneracy is not separated; the unconditional two2D-eigenspace statement fails there.
- dynamics.state: 0/8 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- dynamics.probability: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- dynamics.supremum: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- dynamics.earliest_and_constant_branches: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.reduced_density: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.entropy: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.concurrence: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.CHSH: 0/6 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.maximal_entanglement_reachability: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- pure_state.earliest_maximal_entanglement: 0/3 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- thermal.Gibbs_state: 0/6 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- thermal.partition_function: 0/4 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- thermal.partial_transpose: 0/7 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- thermal.entanglement_criterion: 0/5 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- thermal.thermal_limits: 0/3 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- checks.conventions: 1/2 (lines 1–9, 24–59, 105–125). Partial credit for the explicit correct basis, Pauli matrices and units. The later tensor sum changes the Hamiltonian convention by introducing forbidden even-sector exchange; logarithm and partial-transpose conventions are absent.
- checks.normalization: 2/2 (lines 228–232). The displayed odd-vector norm is explicitly and correctly checked. This is a valid local normalization check even though the normalized vector is not the claimed eigenvector; that separate error is deducted under projectors.
- checks.initial_condition: 0/2 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.
- checks.decoupled_limit: 1/2 (lines 224–237). The J=0 odd block is explicitly checked to be diagonal and the singular chart is recognized. The eigenvector branches are not completed, and the answer never supplies state/probability/entanglement or thermal decoupled checks. Partial credit only.
- checks.nontrivial_numerical_example: 0/2 (lines no delivered evidence). No final solution content for this criterion appears before the response ends at the unfinished fourth projector on line290. Merely stating the initial condition in the problem setup is not an independent t=0 consistency check.

DIRECT-CE01: For the00-to11 entry, XX contributes1 and YY contributes-1, so the seed gives0, not2. The true spectrum is0,0,2,-2, whereas the answer claims2,-2,2,-2. Their squared traces are8 and16 respectively.

DIRECT-CE02: Omega=5. The stated plus-vector direction is v=(1,3); M=[[4,3],[3,-4]] gives Mv=(13,-9), whereas5v=(5,15). Thus the final normalized vector is not the plus eigenvector despite being correctly normalized.

DIRECT-CE03: H=0 has one energy eigenspace of dimension4 and full spectral projector I. The delivered unconditional two2D-eigenspace description does not resolve this coincidence.

## Limits

Exact source/run/answer/seed hashes bind these local artifacts; they do not authenticate a remote provider. Symbolic grading and small exact arithmetic witnesses support the listed deductions, not all possible numerical cases. No provider requests or original workflow source were modified, and no evaluator feedback entered live requests.
