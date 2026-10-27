# Finite quantum discrete deformation calculus

AuthorityEffect: None. This implements a bounded exact algebra for declared
finite carriers. It does not establish that an encoding captures claim truth,
agent intent, deception, or semantic consensus. The original mission's statements
are qualified below where they conflict with finite linear algebra.

## Carrier, differential, and Hodge decomposition

Let X be a finite oriented simplicial complex with finite ordered k-simplex
sets X_k. With coefficients A = Herm_m(Q(i)), define C^k(X;A) = A^(X_k)
as a rational vector space. Density matrices form a convex set, not a vector
space: signed incidence sums do not preserve positivity or trace one.
For an oriented simplex [v_0,...,v_(k+1)],

    (d_k omega)([v_0,...,v_(k+1)])
      = sum_j (-1)^j omega([v_0,...,omit v_j,...,v_(k+1)]).

Every codimension-two face occurs twice with opposite sign, so d_(k+1)d_k=0.
Use the Euclidean simplex inner product and the real Hilbert–Schmidt inner
product on Hermitian coefficients. Then delta_k = d_(k-1)^T coefficientwise,
delta_(k-1)delta_k=0, and

    Delta_k = d_(k-1) delta_k + delta_(k+1) d_k.
    <omega,Delta_k omega> = ||delta_k omega||² + ||d_k omega||².

Finite-dimensional orthogonal decomposition gives

    C^k = im(d_(k-1)) ⊕ im(delta_(k+1)) ⊕ (ker d_k ∩ ker delta_k).
    omega = d alpha + delta beta + gamma.

The three components are unique. Potentials are defined modulo their kernels.
The existing rational solver sets free coordinates to zero as a deterministic
gauge; the Lean triangle example instead chooses a zero-mean alpha. These are
compatible component decompositions, not a claim of identical potential values.
The native implementation calls that solver and its independent certificate
replay for each real and imaginary operator coordinate, sharing one fuel budget.
Real incidence maps preserve Hermiticity.

The native input is a three-degree matrix window with checked d_next*d_prev=0.
It also accepts rational finite cochain complexes beyond simplicial incidence
matrices. It does not claim that every accepted matrix pair comes from a
simplicial complex. Nontrivial weighted stars are outside this API; with declared
positive rational Gram matrices the corresponding definition is
delta_k=G_(k-1)^(-1)d_(k-1)^T G_k, requiring a different solver contract.

## Finite deformation and harmonic transport

For Hermitian H and omega, [H,omega] is anti-Hermitian. Thus the mission's
omega+d alpha+[H,omega] is generally neither Hermitian nor a finite unitary
transformation. The physical generator is -i[H,omega]; a finite deformation is

    omega' = U (omega + d alpha) U*,   U*U = UU* = I.

The API checks an exact U over Q(i), shared over all simplices. Such conjugation
commutes with the scalar differentials, adjoints, and Hodge projections. Gauge
addition fixes gamma; the combined deformation sends gamma to U gamma U*.
Literal equality to gamma requires [U,gamma_s]=0 on every simplex. The
Hilbert–Schmidt norm of gamma is invariant. For the triangle cycle with
coefficient sigma_y, conjugation by sigma_x negates its nonzero harmonic part.
The test suite checks this counterexample and checks pure gauge invariance.

## Quantum primitives and the limits of their interpretation

| Mission statement | Finite algebraic conclusion |
| --- | --- |
| A unitary annihilates a normalized false premise | Unitaries preserve norm. Inner product -1 for normalized vectors implies anti=-claim, the same physical ray. Their formal sum is zero, but it is not a normalized quantum state. No truth test follows. |
| Off-diagonal entries measure semantic entanglement | They are basis-dependent coherence. Entanglement requires a specified tensor factorization and a nonseparability criterion. Matrix indices cannot simultaneously be treated as arbitrary agent and hypothesis labels. |
| Zero entropy is semantic consensus | Zero von Neumann entropy characterizes a pure density. The pure plus state has hypothesis probabilities (1/2,1/2). Agents can agree on the mixed state I/2, with entropy log 2. |
| Noncommuting probes differ on every state and prevent deception | Some sequential statistics can differ. A state-dependent effect is not a deception detector. Nonselective X/Z dephasing channels commute even though their rank-one projectors do not. |
| Lindblad retraction reaches zero obstruction in finite time | This requires explicit target and reachability assumptions. The finite channel below admits an exact reset; its continuous semigroup reaches that reset only in a limiting parameter regime. |

An exact interference construction needs only Q(i). Put a=(1+i)/2 and
U=a[[1,1],[1,-1]], so U*U=I. On a path ancilla,

    |0> --U--> a(|0>+|1>) --Z--> a(|0>-|1>) --U--> i|1>.

The first port is dark while total norm remains one. An incoherent I/2 input
remains I/2. Tensoring with a claim carrier preserves that carrier; it does not
determine whether the claim is false. Native tests check both controls.

For valid densities, exact purity tr(rho²)=1 is equivalent to rank one and
entropy zero. Purity is rational here; general entropy contains logarithms and
is not represented as a rational number. If a convex mixture with strictly
positive weights is pure, every constituent density equals that pure density:
positivity forces each constituent to vanish on the orthogonal complement of
the mixture's one-dimensional support. This limited theorem still does not
identify a definite named hypothesis or validate agent agreement.

For selective probes, let P=diag(1,0), Q=[[1,1],[1,1]]/2, and rho=P. The joint
probability for P then Q is 1/2; Q then P gives 1/4. The API returns the
probability and conditional density. A zero-probability branch returns null.
The two branch probabilities must be multiplied to obtain each joint
probability. Order effects alone give no computational advantage theorem over
classical models with state updates or independent verification of truth.

## Lindblad generator and exact retraction step

`Lindbladian::derivative` implements, with checked finite dimensions,

    L(rho) = -i[H,rho] + sum_j (L_j rho L_j* - {L_j*L_j,rho}/2).

It returns a Hermitian trace-zero operator, not a density. For rho=diag(1,0)
and H=sigma_x, rho+h L(rho) has determinant -h² for every nonzero rational h.
Consequently an Euler update cannot be advertised as a positive channel.
The native tests reject this update even at h=1/100. No general matrix
exponential over Q(i) is promised.

For a nonzero orthogonal projector P, write Q=I-P, r=tr(P), tau=P/r. Define

    R(rho) = P rho P + tr(Q rho) tau.
    Phi_eta(rho) = (1-eta)rho + eta R(rho),   eta in Q ∩ [0,1].

R is completely positive and trace preserving. An exact weighted Kraus witness
is P with weight 1, and P E_ij Q with weight 1/r for all matrix units E_ij.
Their weighted K* K sum is P+Q=I; their output sum is the displayed R.
`weighted_kraus` uses the existing channel constructor to check that equality.
R is idempotent, its image consists of densities supported in P, and

    q = tr(Q rho),     tr(Q Phi_eta(rho)) = (1-eta)q.

The API rechecks every returned density. At eta=1 the discrete step resets
exactly. At eta<1 and q>0, any finite number of repeated steps has positive q.
Writing formal continuous time for the finite-dimensional generator G=R-Id,

    exp(tG) = R + exp(-t)(Id-R).

Thus Phi_eta agrees with this semigroup at t=-log(1-eta) when eta<1. This is
an algebraic characterization, not numerical evaluation of a transcendental
time. Kraus operators of R, rescaled by square roots of their weights, give a
finite GKSL realization of G; those square roots need not lie in Q(i).
An additional Hamiltonian preserves the target subspace only when [H,P]=0.
The step API includes no unverified Hamiltonian splitting.

### Which target corresponds to zero DDC residual?

For positive L1 weights, Phi_1(omega)=min_alpha ||core-d alpha||_(1,w)
vanishes exactly on im d. Harmonic gamma=0 is insufficient: the filled
triangle cycle has nonzero coexact component and zero harmonic component.

`repair_projector` derives the Euclidean projector onto im d_prev by solving
the Hodge problem on each scalar basis vector. It acts on the simplex-index
Hilbert carrier, distinct from the original operator-valued cochain. A density
supported there is a mixture of exact cochain rays. For vectorized operator
coefficients the corresponding projector is P_exact tensor I on a separately
declared carrier, subject to the same size limits. An arbitrary projector
supplied to `retract` is only a declared target, not a certificate of Phi_1=0.
A zero-dimensional exact image has no normalized density supported on it and
cannot be the target of this trace-preserving reset.

The L1 dual statement also needs correction. For weighted L1, feasibility is
d^T y=0 and |y_i|<=w_i. Then <y,omega> is a lower bound for every potential;
equality certifies an optimum only after both sides' feasibility is checked.
The box is |y_i|<=1 only for unit weights. Hodge's Euclidean least-squares
potential is not generally the L1 minimizer. This module does not replace the
existing functional and dual-witness owners.

## Relation to the eight DDC normal forms

| Normal form | QDDC binding and boundary |
| --- | --- |
| `nf.ddc.hodge_canonical` | Exact componentwise solver and replay; potentials modulo kernel; Euclidean star explicitly declared. |
| `nf.ddc.dual_witness` | Existing functional owner remains responsible for weighted L1 feasibility and equality. Purity and outside probability are not L1 witnesses. |
| `nf.ddc.context_boundary` | Declare the simplex order, operator basis, matrix pair, and density carrier; switching between these carriers is an explicit encoding. |
| `nf.ddc.lift_ledger` | A scalar cochain-to-density encoding needs its own retained amplitudes and normalization. This API does not silently introduce one. |
| `nf.ddc.loss_ledger` | Existing LLNF books dropped coordinate tails and their L1 norm. An irreversible same-dimension channel is a different operation; q is not that norm or a measure of semantic information. Preserve the complete input and output in a caller-owned transcript. |
| `nf.ddc.refusal_receipt` | Native refusals, budgets, and transport errors propagate through the canonical host; no Python solver fallback. |
| `nf.ddc.terminal_partition` | A successful algebraic operation does not select a semantic terminal route or confer authorization. |
| `nf.ddc.trace_merkle` | The canonical host outcome can be committed by the existing transcript layer. A hash chain needs a separately trusted tip; hashing an output alone does not preserve erased input. |

No new normal-form certification is inferred from these correspondences.
Historical inputs, source bytes, and encoding data must be retained by any
caller that requires reversibility or replay. The pure math module owns no
filesystem or persistent ledger.

## Executable ownership and limits

- Rust: `core_quantum_physics::qddc` composes the existing exact operator,
  density, channel, and `core_solvers` Hodge owners. Public traits are
  `ExactHodge`, `ExactGenerator`, and `ExactDensityStep`.
- Host: seven `qddc_*` actions in the canonical Symbol Game dispatcher.
- Python: Pydantic v2 contracts in `domain/homology/qddc.py`, `QddcPort`, and
  the `infrastructure/adapters/qddc_rust_adapter.py` implementation.
- Lean: `formal/qddc/Qddc.lean`, pinned to Lean/mathlib v4.34.0. The native
  solver handles bounded arbitrary matrix complexes; formal Hodge statements
  here cover the filled triangle. Additive nilpotence covers arbitrary
  additive coefficient groups, including operator matrices entrywise.

Limits: operator dimension 1..8; at most 32 cells per cochain degree; at most
16 jumps; canonical reduced input rationals with numerator and denominator
at most 256 bits. Hodge arithmetic uses 4,000,000 scalar operations and
8192-bit intermediate bounds. The runtime request limit is 65,536 bytes.
Deriving a density repair projector additionally limits the simplex carrier
to 1..8. All seven host actions bound each output rational to 8192 bits in
both numerator and denominator and 6000 ASCII bytes of canonical text, matching
Python's scalar models. A result exceeding either limit returns a native
`QDDC_OUTPUT_LIMIT` refusal before a success outcome is serialized. This checks
all real and imaginary matrix entries as well as scalar results. The separate
256-bit native input gate still applies on every new call; a valid output is
not necessarily a valid input for a later call.

If a host reports success with a result that fails the Python output schema,
the adapter raises `NativeMathRefusal` with code `QDDC_OUTPUT_SCHEMA`, retains
the complete original host outcome, and chains the Pydantic validation error.
Native refusals retain their original outcomes too. Exact arithmetic can
return a resource refusal. No unbounded search, floating-point comparison, or
provider call is part of this implementation.

Validation commands, versions, scope, and source hashes are recorded in
the historical PR #1079 receipt
[`qddc_validation.json`](qddc_validation.json), dated 2026-10-16. Its native,
Python, and Lean results apply to the source hashes recorded there. The output
contract correction has a separate receipt,
[`qddc_output_contract_validation.json`](qddc_output_contract_validation.json).
It covers compiled-host refusals for the reviewed 7x7 density's 8572-bit
purity and a two-level Lindblad derivative with an 8323-bit denominator,
inclusive scalar bounds, successful execution of all seven actions, and
explicitly nonconforming reply fixtures for adapter error preservation.
The selected probe's nonzero and zero-probability branches execute through
the compiled host; no oversized probe execution is claimed. The correction
does not change or recheck the Lean proofs. Their historical reported axioms
are the standard `propext`, `Quot.sound`, and where used `Classical.choice`.

Supported claim: these bounded finite algebraic constructions and the stated
triangle lemmas execute under the recorded checks. Not supported: semantic
consensus, automatic premise falsification, deception prevention, quantum
speedup, or formal verification of the Rust solver. Further generalization
would require a formal arbitrary-complex Hodge theorem and independently
verified semantic encodings; neither is assumed by the runtime.
