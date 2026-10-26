::: {align="center"}
# PFP II: Signed Certificates, Resumable Search, and a Restricted Path-Pairing Obstruction

Jeremy H. Carroll\
2026-10-02 · Version 0.1.0 · Research paper · Author-review revision
:::

Code baseline: `c819bec432446dd3c9b1edf1583384cfe76c6c71`.

## Abstract

When a search fails to find a sign transformation, three explanations
remain: the transformation does not exist, the search has not finished,
or the allowed transformations were too restrictive. This paper gives a
small implementation in which those possibilities remain distinct.
Within the Proposal Fidelity Protocol (PFP, historically the Symbol
Game), a finite signed graph admits either an independently checkable
vertex-sign assignment or an odd closed-walk obstruction. An exact real
symmetric matrix adapter supplies a complete instance for diagonal sign
changes in a fixed basis. A deterministic bounded search records the
unexamined suffix and requires replay of every earlier segment before
continuation. We also present an exact Fock-space example in which one
negative integrated hopping sequence has no positive sequence of equal
magnitude. That result rules out a specific pairing operation, not all
representations of the Hamiltonian. The contribution is a reproducible
certificate and evidence protocol joining established signed-graph
reasoning to honest incomplete search, with a worked physical example
whose representation boundary is explicit.

## 1. The question must include the presentation

Imagine changing the signs of rows and the corresponding columns of a
symmetric matrix. Can every nonzero off-diagonal entry become negative?
This is a precise finite question. It differs from asking whether an
arbitrary change of basis, a determinant identity, or a regrouping of
paths can produce a useful nonnegative simulation.

A *presentation* records the object, its representation, and the
permitted moves. A negative answer concerns that entire tuple. PFP
stores this tuple beside a candidate and asks the host to verify the
candidate again; a retrieved answer is a proposal until checked.

The running matrix is

$$H=\begin{pmatrix}0&1&-1\\1&0&1\\-1&1&0\end{pmatrix}.$$

The diagonal matrix $D=\operatorname{diag}(1,-1,1)$ turns all three
off-diagonal pairs negative in $DHD$. A reader can verify this by
multiplying each entry $H_{ij}$ by $D_{ii}D_{jj}$. Conversely, a
triangle whose three off-diagonal pairs are all positive cannot be
repaired by these sign changes: each of its three edges asks its
endpoints to receive opposite signs.

These examples are small enough to inspect completely. Their value is
the clean boundary between an answer, a witness, and the larger
scientific question that motivated the matrix.

## 2. Signed graphs and a complete certificate pair

Let $V$ be a finite ordered list of distinct vertex names and $E$ a
finite list of undirected edges. Multiple edges and self-loops are
allowed. Give each edge $e=uv$ a bit $c_e\in\{0,1\}$. We seek bits
$\alpha_v$ satisfying

$$\alpha_u\mathbin{\oplus}\alpha_v=c_e
\quad\text{for every edge }e.$$

Here $\oplus$ is addition modulo two. An edge with bit one requires
opposite vertex bits; an edge with bit zero requires equal bits.
Equivalently, switching vertex signs should turn every edge sign
$(-1)^{c_e}$ positive.

**Signed-graph criterion.** Such an assignment exists if and only if
every closed walk has total edge parity zero.

For necessity, XOR all edge equations around a closed walk. Every vertex
occurrence contributes twice, so the left side vanishes. For
sufficiency, choose a root in each component and set its bit to zero.
Assign every other vertex the XOR of edge bits along a path from the
root. Two choices of path form a closed walk, so the assumed condition
makes this assignment independent of the choice. Appending one edge
establishes the required endpoint equation.

The proof yields two independently checkable witness types:

  -----------------------------------------------------------------------
  Outcome                 Witness                 Host checks
  ----------------------- ----------------------- -----------------------
  A gauge exists          One bit for every       Every endpoint equation
                          vertex in the declared
                          order

  No gauge exists in this A nonempty closed walk  Edge identities,
  grammar                 with odd total parity   adjacency, closure, and
                                                  XOR
  -----------------------------------------------------------------------

The implementation in
[sign_graph.py](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/sign_graph.py)
constructs a spanning forest by breadth-first traversal. A conflicting
edge closes an odd walk through the tree. If there is no conflict, the
assigned bits form a gauge. Construction is linear in the graph's
vertices and edges. The separate witness verifiers do not trust the
constructor's verdict.

For the running example, the edge bits on $01,12,20$ are $1,1,0$. The
assignment $(0,1,0)$ works. For the all-positive matrix, the edge bits
are $1,1,1$, and the triangle itself witnesses parity one. A single odd
self-loop is the smallest obstruction because it requires
$\alpha_v\oplus\alpha_v=1$.

This is the classical balance criterion for signed graphs (Harary,
1953), presented here as a host-checkable protocol. We claim no new
graph theorem.

The parity carrier must not be confused with the rational edge reports
of the companion paper PFP I (Carroll, 2026; see
[docs/references.md](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/docs/references.md)).
Reports $(1,1,0)$ around an oriented triangle have even parity but
rational sum two. Their uniform-weight rational repair cost is two. The
coefficient system and the allowed changes are part of the claim.

## 3. Exact matrices and the boundary of stoquasticity

Assume $H$ is a finite real symmetric matrix with entries represented by
integers or exact fractions in a declared basis. For every nonzero
off-diagonal entry, assign

$$c_{ij}=\mathbf{1}[H_{ij}>0],\qquad
D_{\alpha,ii}=(-1)^{\alpha_i}.$$

Then

$$(D_\alpha H D_\alpha)_{ij}
=(-1)^{\alpha_i+\alpha_j}H_{ij}.$$

Therefore all its nonzero off-diagonal entries are negative exactly when
$\alpha_i\oplus\alpha_j=c_{ij}$. Zero entries impose no equation. The
signed-graph checker completely decides this fixed-basis diagonal-sign
problem. It rejects floating-point, nonsquare, and nonsymmetric inputs
rather than silently changing the mathematical question.

A real symmetric matrix with nonpositive off-diagonal entries is called
*stoquastic* in that basis. If $H'$ has this property and $\beta\geq0$,
choose $a\geq\max_i H'_{ii}$. Then $B=aI-H'$ is entrywise nonnegative,
and

$$e^{-\beta H'}=e^{-\beta a}\sum_{k=0}^{\infty}
\frac{\beta^kB^k}{k!}$$

is entrywise nonnegative. Finite dimensionality ensures convergence
under declared assumptions, and each summand has nonnegative entries.
This establishes a positivity statement for this matrix expansion; it
does not establish rapid sampling or a low-variance estimator for every
observable.

Other transformation grammars can answer different questions. Allowing
an unrestricted global eigenbasis makes any finite Hermitian matrix
diagonal, but obtaining that basis and expressing observables may be
computationally prohibitive. Local basis changes are more constrained
and more general than our diagonal signs. Klassen and Terhal (2019)
analyze such changes for two-local qubit Hamiltonians; their results are
not supplied by our graph checker.

## 4. Search that can stop without inventing an obstruction

The complete graph algorithm is already efficient. Why retain an
exponential candidate search? Its purpose is to exercise the protocol
used when a future candidate grammar lacks such a simple complete
solver.

[frontier_search.py](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/frontier_search.py)
enumerates the $2^{|V|}$ bit assignments in lexicographic order. It
checks fixed batches of at most eight, independent of worker count, and
consumes completed results in canonical order. Thread scheduling
therefore cannot select a different first witness or reorder the
recorded checks. This is deterministic batch enumeration; it has no
Monte Carlo tree-search policy and makes no CPU speedup claim.

A receipt records the presentation and graph digests, start index,
budget, ordered candidate checks, remaining suffix, witness if present,
and a digest of that record. Its statuses are:

- **GAUGE_VERIFIED:** a returned gauge passes the exact verifier.
- **UNKNOWN:** the tested segment failed and an unexamined suffix
  remains.
- **RESTRICTED_OBSTRUCTION:** the finite grammar is exhausted and the
  independent graph constructor supplies a verified odd walk.

In the running three-vertex example, indices zero and one represent
$000$ and $001$, both invalid. With a budget of two, the correct outcome
is UNKNOWN and the remaining interval is $[2,8)$. Resuming with a budget
of one examines $010$, verifies it, and leaves the cursor at three. This
is a worked control trace, not a benchmark of search efficiency.

A nonzero starting cursor is accepted only when prior UNKNOWN receipts
replay as a contiguous chain beginning at zero. Each recorded bit vector
and verdict is checked again; a recomputed digest by itself is
insufficient. Skipping an earlier segment or importing a chain for a
different graph must fail. Completeness is therefore tied to verified
coverage, rather than to a caller's assertion that earlier work
happened.

The presentation key includes Hamiltonian digest, basis, ensemble,
filling, boundary, representation, estimator, observables, inverse
temperature, parameters, transformation grammar, adapter digest, and
checker version. The index intersects all key fields and then tests
full-key equality. Even identical Hamiltonian bytes do not justify
moving a gauge between different declared representations. Matching a
key still does not prove that the claimed Hamiltonian-to-matrix adapter
is scientifically correct.

## 5. What an equal-weight pairing must prove

For a finite signed sum

$$Z=\sum_{x\in\Omega}\sigma(x)A(x),\qquad
\sigma(x)\in\{-1,1\},\quad A(x)>0,$$

a cancellation certificate can specify a subset $P\subseteq\Omega$ and a
map $I:P\to P$. It must verify $I(I(x))=x$, $I(x)\neq x$,
$\sigma(I(x))=-\sigma(x)$, and $A(I(x))=A(x)$. The paired contribution
then cancels term by term. If all survivors have nonnegative
contribution, the remaining sum is nonnegative.

Checking only that the total is nonnegative is weaker. Contributions
$+2,-1,-1$ sum to zero, but no negative term has a positive term of
equal magnitude. Pairing every term of a positive thermal partition
function is also obstructed: for a Hermitian Hamiltonian on a nonzero
finite-dimensional Hilbert space and real finite $\beta$,
$\operatorname{Tr}e^{-\beta H}>0$. A complete cancellation would give
zero. The same argument applies to an absolutely convergent expansion
when all terms are paired.

These observations motivate a sharply bounded physical example. Its
certificate excludes one operation on one carrier; it neither classifies
all algorithms nor rules out regrouping several terms together.

## 6. A restricted Fock-space obstruction with exact bounds

Use a three-site triangle with spin-up modes followed by spin-down modes
in the order

$$(\uparrow0,\uparrow1,\uparrow2,\downarrow0,\downarrow1,\downarrow2).$$

An occupation state is a six-bit string, so there are $2^6=64$ states.
Set hopping amplitude $t=1$, on-site repulsion $U=2$, chemical potential
zero, and inverse temperature $\beta=1/4$. The diagonal energy is

$$E(x)=2\sum_{i=0}^{2}n_{\uparrow i}n_{\downarrow i}.$$

The hopping matrix element of $-H_{\mathrm{hop}}$ moves one particle
between two different sites of the same spin and is $(-1)^q$, where $q$
counts occupied modes strictly between the two positions in the declared
mode order.

Our carrier consists of rooted closed hopping sequences after their
ordered jump times have been integrated out. For a sequence with $n$
jumps, its weight is the product of hopping signs times

$$\int_{0<\tau_1<\cdots<\tau_n<\beta}
\exp\!\left[-\sum_{j=0}^{n} E(x_j)(\tau_{j+1}-\tau_j)\right]
\,d\tau_1\cdots d\tau_n,$$

where $x_n=x_0$, $\tau_0=0$, and $\tau_{n+1}=\beta$. Sequences at
different lengths belong to this carrier; it is not a finite set solely
because its state space is finite.

Consider the three-hop cycle

$$110;111\ \longrightarrow\ 101;111\
\longrightarrow\ 011;111\ \longrightarrow\ 110;111.$$

Its hopping-sign product is negative, every visited state has energy
four, and its integrated weight is exactly

$$-W_\star=-e^{-1}\frac{(1/4)^3}{3!}
=-\frac{e^{-1}}{384}.$$

The retained [exact
checker](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/exact_fock_gap.py)
enumerates all rooted three-hop sequences. Its asserted finite facts are
192 sequences, evenly split into 96 positive and 96 negative, with every
positive three-hop sequence visiting only energies at most two. It also
checks the global energy range $0\leq E\leq6$, absence of one-hop
closures, and symmetric unit-magnitude hopping.

These facts imply the following bounds for an individual positive
sequence:

  Jump count   Positive integrated weight
  ------------ --------------------------------
  0            At least $e^{-3/2}$
  1            No closed sequence
  2            At least $e^{-3/2}/32$
  3            At least $e^{-1/2}/384$
  $n\geq4$     At most $(1/4)^n/n!\leq1/6144$

The lower bounds use the maximum energy during the path and the simplex
volume $\beta^n/n!$. The upper bound uses nonnegative energies and
unit-magnitude hopping. Its final expression decreases for $n\geq4$. It
bounds one sequence, not the sum of all long sequences.

The strict separations

$$\frac1{6144}<W_\star<
\frac{e^{-1/2}}{384},\qquad
W_\star<\frac{e^{-3/2}}{32}<e^{-3/2}$$

exclude every possible positive partner on the declared carrier. The
checker establishes these inequalities with rational enclosures for
$e^{-1}$, $e^{-1/2}$, and $e^{-3/4}$, squaring the last lower bound. For
$0\leq x\leq1$, the alternating series for $e^{-x}$ has decreasing term
magnitudes; odd partial sums are lower bounds and even partial sums are
upper bounds. Thus no floating-point comparison is needed.

The conclusion combines finite enumeration at length three with an
analytic bound covering every longer length. A sign-reversing
equal-magnitude map that covers this negative sequence does not exist on
this carrier. Time-labelled maps before integration, determinant
identities, collective regroupings, other bases, and other estimators
remain outside the statement. Establishing a useful sign-free simulation
in any such representation requires its own construction and
observable-preservation argument.

## 7. Reproduction, custody, and negative controls

The four frozen finite-graph files were copied from the author's non-Git
Genesis workspace on 2026-09-23. The matrix snapshot repair of
2026-09-24 changed the search module and one regression test. The
[provenance
record](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/PROVENANCE.md)
retains both original and repaired hashes and records later packaging
changes with their current hashes. The baseline named above supplies the
exact repository revision for the sources discussed here.

The repaired code snapshots matrix rows before validation, hashing, and
classification. Before that repair, a one-shot iterator could be
consumed during validation and subsequently interpreted as an empty
matrix. This is a concrete reason to bind checking and hashing to the
same immutable input.

From the package root, run one test file per command. The commands use
`py -3.12`, the Windows launcher for Python 3.12; on other systems,
substitute a Python 3.12 interpreter.

``` powershell
py -3.12 -m pytest code/tests/test_sign_graph.py -q
py -3.12 -m pytest code/tests/test_frontier_search.py -q
py -3.12 -m pytest code/tests/test_manuscript_examples.py -q
py -3.12 -m pytest code/tests/test_exact_fock_gap.py -q
py -3.12 -m pytest code/tests/test_native_sign_graph.py -q
py -3.12 -m pytest code/tests/test_native_refusals.py -q
py -3.12 code/exact_fock_gap.py
py -3.12 code/run_demos.py --all
```

The file `test_manuscript_examples.py` checks the worked examples of
Sections 1, 2, and 4. The exact checker prints the 192, 96, and 96 path
counts and the rational bounds of Section 6. The dated review receipt
for this revision records the interpreter, each command, tool versions,
exit statuses, and the tested scope; see "Verification for this
revision". Historical 18-test and 19-test receipts apply to their dated
snapshots only. The package also contains an optional native Rust
implementation of the graph checker, described in the
[README](README.md); the statements of this paper rest on the proofs and
the Python checkers.

Useful negative controls include an odd self-loop, an all-positive
triangle, a malformed closed walk, floating-point matrix input, a
changed presentation key, a skipped frontier interval, and a one-shot
matrix iterator. The
[notebook](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/jupyter_notebooks/signed_exchange_and_frontier.ipynb)
illustrates the finite checker; its saved outputs are not independent
experimental data.

This package contains no machine-checked proof of the signed-graph
implementation. The small formal proofs accompanying the companion paper
PFP I, a pair-cancellation law and a triangle sign obstruction, concern
their own restricted types. Historical model conversations and their
terminal labels are also insufficient to establish physical
preservation, model success rates, or current runtime operation.

## 8. Related work and practical use

Harary's signed-graph balance result supplies the underlying parity
criterion. Our contribution is the explicit witness interface, the
bounded search record, and the separation of complete graph
classification from incomplete exploration. The classical graph
algorithm is the right baseline when this exact grammar is the entire
problem.

Troyer and Wiese (2005) establish worst-case computational difficulty
for a generic solution of the fermion sign problem. That result does not
certify failure of an individual Hamiltonian, basis, or pairing
proposal. Our Fock example provides a different kind of evidence: a
concrete obstruction to a specifically defined operation.

The methods are useful for testing certificate interfaces, replaying
bounded search, and identifying where an adapter must supply new
scientific evidence. A physical application must pin its Hamiltonian,
ensemble, basis, boundaries, mode ordering, measure, observables, and
transformation grammar. It must show preservation of the partition
function and observable numerators, then analyze estimator cost if
computational usefulness is claimed. This package implements finite
graph and matrix checks and the restricted path example. It does not
provide that general physical adapter.

## Verification for this revision

The package verifier (`verify_deposit.py`) checks the manifest and the
two-way file census; `tools/rebuild_release.py --check` checks the
release archive. The package tests, lint, and notebook replay are
executed by the dated review receipt recorded with this revision; that
receipt lists each command, tool version, exit status, and tested scope.
Historical receipts in this package keep their original dates and scope
and are not current execution evidence.

## References

- Carroll, Jeremy H. (2026). *PFP I: Exact Graph Repair and the Boundary
  Between a Proposal and a Certificate*. Version 1.3.0, author-review
  preprint, Paper 001 in this series. Repository path
  `omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions`.
- Harary, Frank (1953). "On the notion of balance of a signed graph."
  *Michigan Mathematical Journal*, 2(2), 143--146.
  [doi:10.1307/mmj/1028989917](https://doi.org/10.1307/mmj/1028989917).
- Klassen, Joel, and Barbara M. Terhal (2019). "Two-local qubit
  Hamiltonians: when are they stoquastic?" *Quantum*, 3, article 139.
  [doi:10.22331/q-2019-05-06-139](https://doi.org/10.22331/q-2019-05-06-139);
  [author preprint, arXiv:1806.05405](https://arxiv.org/abs/1806.05405).
- Troyer, Matthias, and Uwe-Jens Wiese (2005). "Computational Complexity
  and Fundamental Limitations to Fermionic Quantum Monte Carlo
  Simulations." *Physical Review Letters*, 94(17), article 170201.
  [doi:10.1103/PhysRevLett.94.170201](https://doi.org/10.1103/PhysRevLett.94.170201);
  [author preprint,
  arXiv:cond-mat/0408370](https://arxiv.org/abs/cond-mat/0408370).
