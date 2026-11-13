# Atlas: finite obstructions, checked proposals and the separation of evidence from authority

AuthorityEffect: None. This paper restates claims; it grades none of them.

## Abstract

This paper collects, in one argument, every claim made by the 38 archived papers in
[`archive/`](archive/README.md) and every derivation recorded by the repository audit in
[`dag/derivations_dag.json`](../dag/derivations_dag.json). Each claim is a row of
[`atlas_claim_ledger.md`](atlas_claim_ledger.md), cited here by its atlas ID.
The common mathematical object is a finite cochain complex with a weighted
$\ell^1$ distance to the image of its coboundary. Its value is certified by a
dual circulation, and it vanishes exactly on consistent data. The common
protocol object is a host checker that accepts a proposed witness only when a
declared relation holds. Its soundness is independent of how the proposal was
produced. The common limit is that neither object supplies authority: an exact
residual, a passing check, a hash or a status label establishes the predicate
it checks and nothing beyond it. Results are finite and conditional on declared
carriers and encodings. Many claims are implementation or measurement records,
and a substantial number are counterexamples to earlier claims.

## 1. Scope and reading

The ledger has two parts. Part I holds 607 claims copied from the archived
papers: from each paper's own claim ledger where one exists, and from the
manuscript for the six papers whose ledger is missing or holds only shared
process text (PFP 011 and 014–018). Part II holds the 740 derivation nodes that
the audit wrote directly into the DAG. Every ledger row is exactly one DAG node
and every derivation node is exactly one row; the correspondence is checked by
`python dag/build_atlas.py --check`. No archive claim is identified with an
audit node, because a claim-level match needs a reviewer's reading. Where both
concern the same paper, the ledger's paper column shows it.

The status attached to each row is a coarse reading of the source's own status
and evidence text, in the vocabulary *proved*, *mechanized*, *computed*,
*empirical*, *definition*, *imported*, *scope fence*, *not measured*,
*withdrawn* and *stated*. It records what the source says about itself. The
ledger keeps the source wording beside it.

Sections 2 and 3 give the mathematics. Section 4 states the protocol and its
composition laws. Sections 5 and 6 cover failure detectors and evidence
custody. Section 7 covers the authority papers, and Section 8 the audit
derivations. Section 9 lists what remains open. The closing index places every
row.

The introductory paper fixes the vocabulary used throughout: a finite
specification, its marked separation and its runtime execution are three
different objects, and a teaching checker refuses incomplete or ill-typed
packets without changing them (ATL-P000-001–006). The two latest papers
apply the same discipline to the workflow catalog and to a braid-compilation
tournament. Their claims are counts and implementation records: which
workflows are offline runners and which are designs, that the workflow graph is
acyclic, and that a host referee checks orthogonality, unit determinant and an
exact rational commutation defect before it accepts a compiled schedule
(ATL-P021-001–008, ATL-P020-001–012).

## 2. The finite obstruction calculus

**Setting.** Let $G=(V,E,F)$ be a finite oriented cell complex of dimension at
most two, with cochain groups $C^0=\mathbb Q^V$, $C^1=\mathbb Q^E$,
$C^2=\mathbb Q^F$ and coboundaries $(d_0u)_e=u(\mathrm{head}\,e)-u(\mathrm{tail}\,e)$
and $d_1$ the signed face boundary, so that $d_1d_0=0$
(ATL-N002-020, ATL-N003-001, ATL-N001-017, ATL-N006-015). A *report* is an edge
cochain $c\in C^1$; it is *consistent* when $c\in\operatorname{im}d_0$. For
positive weights $w$ define

$$\Phi_1(c)=\min_{u\in C^0}\sum_{e\in E}w_e\,\lvert c_e-(d_0u)_e\rvert .$$

$\Phi_1$ is a norm on the quotient $Q^1=C^1/\operatorname{im}d_0$, and its $\ell^p$
analogues are norms for every $p\in[1,\infty]$ with attained infima
(ATL-N001-001, ATL-N001-003, ATL-N001-004). It is invariant under adding a
coboundary to the report, and $\Phi_1(c)=0$ exactly when $c$ is consistent
(ATL-P001-001, ATL-P001-002, ATL-P005-003). Changing the section $u$ alone
cannot remove a nonzero class (ATL-D-PAPER005-INSTANCE-REPLACEMENT,
ATL-P007-003); nonzero classes are the nontrivial classes of
$H^1(G;\mathbb R)$ (ATL-N001-020).

**Duality and certificates.** For any circulation $y$ ($d_0^{\top}y=0$) with
$\lvert y_e\rvert\le w_e$ and any potential $v$,

$$\langle y,c\rangle=\langle y,c-d_0v\rangle\le\sum_e w_e\lvert c_e-(d_0v)_e\rvert .$$

So a feasible primal $u$ and dual $y$ with equal objectives certify the minimum,
using weak duality only (ATL-P001-003, ATL-N001-006, ATL-N001-009,
ATL-N001-010, ATL-N002-006, ATL-D-AC1120-C011). Strong duality holds as the
finite case of Fenchel–Rockafellar duality with conjugate exponent
$q=p/(p-1)$ (ATL-N001-005, ATL-N001-007, ATL-N001-008). Equality of objectives
certifies nothing until feasibility, divergence balance and the box bounds are
checked: a zero gap can coexist with failed balance (ATL-P008-006,
ATL-D-PAPER008-FEASIBILITY-BEFORE-GAP, ATL-P011-004). Conversely, a feasible
dual alone is only a lower bound; one audited judge accepted a positive dual
bound as an optimum without a primal attaining it (ATL-D-AC1120-C019).

**Cycles.** On one oriented cycle with cycle sum $s=\sum_ec_e$,

$$\Phi_1(c)=\bigl(\min_e w_e\bigr)\,\lvert s\rvert ,$$

attained by concentrating the whole residual on a cheapest edge
(ATL-P001-004, ATL-P004-012, ATL-N001-015, ATL-D-PAPER000-CYCLE-CAPSTONE,
ATL-D-PAPER004-WEIGHTED-CYCLE). With unit weights,
$\Phi_1(c)=\Gamma_2(c)=\lvert s\rvert=\max\{\langle z,c\rangle:\partial_1z=0,\ \lVert z\rVert_\infty\le1\}$
(ATL-P017-002). Examples: claims $(1,1,1)$ with weights $(1,2,3)$ give 3; the
residual of a rational triangle moves from $(1/3,1/3,1/3)$ to $(0,0,1)$ under a
potential change while its sum stays 1; each unit field on the directed
3-cycle has obstruction 1 (ATL-P005-001, ATL-P005-002, ATL-P007-002,
ATL-D-PAPER007-CYCLE-RESIDUAL-IDENTITY, ATL-N006-012, ATL-P009-002). A
reversed difference convention also telescopes, so cycle-sum assertions alone
accept a wrong-sign mutant; a coordinate check catches it (ATL-P007-012,
ATL-D-PAPER007-FAULT-SENSITIVE-CONTROL).

**Structure of minimizers.** Some optimal residual is supported on at most
$\lvert E\rvert-\operatorname{rank}d_0$ edges; a weighted null-space property on
its support suffices for uniqueness; integral data admit an integral optimum by
total unimodularity (ATL-P001-005, ATL-P001-006, ATL-N001-016). For
$p\in(1,\infty)$ the problem is uniformly convex with a $p$-Laplacian optimality
condition; $p=2$ is the Hodge–Helmholtz decomposition and $p=\infty$ Chebyshev
approximation (ATL-N001-011–014). Strict rational descent does not terminate in
general: $D_t=2^{-t}$ decreases forever (ATL-P001-007).

**Trees, chords and syndromes.** Fix a spanning tree $T$ with chords
$g_1,\dots,g_{b_1}$. The tree determines a potential $p_T^*$ from the tree
claims, and each chord has holonomy $r_m^*=c_{g_m}-(p_T^*(v_m)-p_T^*(u_m))$. The
discrete Fredholm alternative reads

$$c\in\operatorname{im}d_0\iff r_1^*=\dots=r_{b_1}^*=0\iff c=d_0p_T^*,$$

and a nonzero $r_m^*$ witnesses inconsistency (ATL-P017-009). The chord
coordinates of the fundamental cycles form the identity matrix $I_{b_1}$, so
the syndrome $\mathbf r^*=S\mathbf c$ decodes a verdict, a single-edge repair
and an audit (ATL-P017-007, ATL-P017-010). A single tree-edge error shifts a
whole subtree's potential, which edge-local retry misreads as a local defect
(ATL-P017-011). Rational coboundaries have zero holonomy on every closed walk
(ATL-N015-005). Local tolerances do not bound holonomy: positive per-edge
tolerances admit a locally acceptable field with nonzero holonomy around a
cycle of length at least three, with the tolerance sum as the sharp bound
(ATL-N015-006, ATL-N015-007, ATL-N015-012).

**Degree two and curvature.** On faces, $\Gamma_2(h)=\lVert d_1h\rVert_1$
measures what degree one cannot see; the degree-separation theorem and its
replay on $C_3$ make the two diagnostics independent (ATL-N003-002,
ATL-N003-007, ATL-N003-008). For a functorial presheaf on covering edges,
composition curvature $K$ satisfies $d_1d_0=K$, so the flat locus is $K=0$, and
a nonzero class in $H^2$ is a quotient obstruction (ATL-N004-001,
ATL-N004-005–007, ATL-N004-011, ATL-N004-012). The remaining results of that
paper, from path independence on diamonds to an exact non-abelian simplicial
holonomy, are stated as conditional proofs without mechanization
(ATL-N004-002–004, ATL-N004-008–010, ATL-N004-013, ATL-N004-016–027); promotion
to $H^2$ is open (ATL-N004-015).

**Operator extensions.** The same quotient norm extends to operator-valued
cochains with Schatten-$p$ norms, non-commutative Hölder duality, unitary gauge
invariance and a distinguishability bound (ATL-N001-018, ATL-N001-019,
ATL-N002-001–004, ATL-N002-014–016, ATL-N002-021). These are imported from
standard analysis. An integer identity used for trace metrics is
$\lVert a-b\rVert^2\lVert a+b\rVert^2=4(\lVert a\rVert^2\lVert b\rVert^2-\langle a,b\rangle^2)$
for vectors of equal norm (ATL-N005-007, ATL-N005-001–006). Several earlier
dynamic statements are withdrawn: a three-step primal–dual update, its monotone
descent, a one-step residual identity and finite-speed propagation
(ATL-N002-005, ATL-N002-007, ATL-N002-010, ATL-N002-011).

## 3. Signs, gauges and holonomy

**Signed graphs.** A finite signed graph admits a $\{\pm1\}$ vertex gauge making
every edge positive exactly when every closed walk has even parity; component
propagation returns a gauge or an odd cycle (ATL-P002-001,
ATL-D-PAPER002-FINITE-SIGNED-BALANCE). A real symmetric matrix admits a
diagonal sign change making its off-diagonal entries nonpositive exactly when
its sign graph is balanced in this sense (ATL-P002-002,
ATL-D-PAPER002-EXACT-FIXED-BASIS-REDUCTION). If $H$ has nonpositive
off-diagonal entries then $e^{-\beta H}\ge0$ entrywise for $\beta\ge0$
(ATL-P002-003). Equal-weight cancellation of paths needs a closed involution,
opposite signs and equal magnitudes; on the declared triangle Fock carrier the
target path has no partner (ATL-P002-008, ATL-P002-009, ATL-P002-012,
ATL-D-PAPER001-FIXED-FOCK-GAP). The parity identity $(-1)^{-k}=(-1)^k$ rules out
count swapping as a sign-reversing involution (ATL-D-PAPER011-SUPPORT-PARITY-OBSTRUCTION).

**Group-valued connections.** For a finite group with a verified table
(closure, identity, inverses, all associativity triples), a connection on a
rectangular lattice assigns group elements to links, and each plaquette has an
ordered product (ATL-P010-002–005, ATL-D-PAPER010-FINITE-GROUP-ADMISSION).
Reversing a plaquette inverts its product, changing its base vertex conjugates
it, and a gauge transformation conjugates it by the gauge at its first vertex
(ATL-P010-006, ATL-P010-007). A flat connection on an open lattice is
gauge-trivial; on the torus the two seam holonomies $A,B$ commute, and the
connection is trivial exactly when $A=B=e$ (ATL-P010-008,
ATL-D-PAPER010-RECTANGULAR-HOLONOMY-CLASSIFIER). Four identity links give an
identity plaquette, so such plaquettes can be skipped without changing any
verdict or witness (ATL-P010-014, ATL-P010-016,
ATL-D-PAPER010-IDENTITY-SKIP-BOUND). For $S_3$ and $Q_8$ these statements are
checked over all seam pairs, and the 100 seam connections split into 58 flat
and 42 non-flat (ATL-P010-009–013, ATL-P010-015, ATL-P010-048).

## 4. Proposals, certificates and composition

**The protocol.** A task fixes a relation $R(P,w)$ between task data and
witnesses. A proposal is any byte string; a decoder $D$ maps admitted replies to
candidate witnesses bound to $P$; a host checker $C$ returns accept or refuse.
If $C(P,w)=\text{accept}\Rightarrow R(P,w)$, then for every proposal channel
$\mu$ the set of accepted invalid candidates is empty, and so has probability
zero under $\mu$ (ATL-P017-001). Soundness gives no acceptance rate and no
completeness (ATL-D-PFP-ACCEPTANCE). A receipt over checked indices
$J_{\text{checked}}$ establishes $\bigwedge_{j\in J_{\text{checked}}}R_j(P,w)$
and nothing about an unchecked index or an invented quotation
(ATL-P013-001–004). Under declared binding, prerequisite, checker and authority
assumptions a terminal checked result is sound for the original task
(ATL-P012-011).

**Factorization.** A decoder $d$ with $d(e(x))=Q(x)$ exists exactly when $e$ is
constant on the fibres of $Q$ (ATL-P012-009); equivalently, a property factors
through observations exactly when it is constant on their fibres
(ATL-N015-004, ATL-D-PAPER011-HISTORY-FINITE-FACTORIZATION). Hence two sources
with one packet and different targets defeat every decoder of the packet
(ATL-D-FORMAL-PACKET-COLLISION), and a role-failure classification cannot
factor through a role-erasing quotient (ATL-N012-008). Composites of maps that
preserve the observation preserve the original one (ATL-P012-010).

**Re-entry.** Representations $P_0,\dots,P_n$ with backward solution maps
$b_i:\operatorname{Sol}(P_{i+1})\to\operatorname{Sol}(P_i)$ decode a checked
solution at $P_n$ by $b_0\circ\dots\circ b_{n-1}$; forward coverage maps compose
in the reverse order, and $b_if_i=\mathrm{id}$ composes. If each operation costs
at least $\delta>0$ against one budget $B$, at most $\lfloor B/\delta\rfloor$
operations run, since $n\delta\le\sum_ic_i\le B$ (ATL-P014-001, ATL-P014-004).
Soundness does not give coverage: with $\operatorname{Sol}(P)=\{0\}$ and an
empty target, the empty backward map is sound and no forward map exists
(ATL-P014-002). The free-information condition says a positive observation-cost
bound must account for what is already reported
(ATL-D-HISTORY-FREE-INFORMATION-COST).

**Local and global.** A family of locally permitted rows on scopes $S_i$ glues to
a unique assignment on $\bigcup_iS_i$ exactly when every pair agrees on its
overlap; with full cover, compatible families biject with global solutions.
The constraints $x=y$, $y=z$, $z\ne x$ are each satisfiable and jointly
unsatisfiable (ATL-P015-001–003). The same local-green, global-red pattern
recurs: in the degree DSL, in finite authority, in the authority gap and in the
operator atlas (ATL-N003-010, ATL-N003-013–015, ATL-N014-008, ATL-N014-014,
ATL-N013-007, ATL-N006-013). A complete typed execution is an integration
observation, not a gluing theorem for effectful agents (ATL-P015-004).

**Compression.** A report $q:X\to Z$ on a deterministic action table admits an
exact quotient exactly when states in one fibre share terminal labels and, per
action, enablement, cost and successor fibre; legal words, reports, costs and
the best resolution cost then descend. Splitting blocks by action signature
reaches the coarsest stable refinement after at most $\lvert X\rvert-1$ proper
splits. Identifying two zero-report states with finishing costs 1 and 3
preserves the output and loses the cost; with positive costs an optimum is a
simple path (ATL-P016-001–004).

**Proposal channels.** Prompt trees whose leaves are not byte-identical to their
declared slices form a two-sided operad ideal, so the null tree absorbs on both
sides (ATL-P017-003). Masking logits to the admissible BPE frontier keeps every
prefix viable (ATL-P017-004). Omitting the global cycle-sum equation from a
Stage-1 guard leaves a false-green kernel isomorphic to $\mathbb Z\setminus\{0\}$
on one cycle and of rank $\lvert V\rvert-1+b_1$ on a graph; staging tree then
chords lowers per-turn slot arity from $\lvert V\rvert-1+2b_1$ to
$\max(\lvert V\rvert-1,b_1)$ (ATL-P017-005–008). A status label `SOLVED`
admits infinitely many invalid witnesses unless the witness is checked
(ATL-P017-012). Measured with guards and abstention, conditional precision was
40/40, while a 7B model passed 2/40, 8/60 and 0/10 of the respective tasks
(ATL-P017-013, ATL-P017-014).

## 5. Failure detectors and retained failures

A detector is a rejection predicate $r$; it is valid for $P$ when
$r(w)\Rightarrow w\notin\operatorname{Sol}(P)$. Validity does not transfer: $r$
rejecting 1 is valid for $\operatorname{Sol}(P)=\{0\}$ and destroys the only
answer of $\operatorname{Sol}(P')=\{1\}$ (ATL-P014-003). Along a total adapter
$\alpha:Y\to X$, every source rejection set disjoint from $G_S$ transfers
safely exactly when $\alpha(G_T)\subseteq G_S$ (ATL-D-HISTORY-REJECTION-PULLBACK).
Screening against a panel is sound for every panel exactly when the executed
predicate implies the screened one (ATL-P003-022,
ATL-D-PAPER003-PREDICATE-SCREEN-SOUNDNESS). A second signal determined by the
first collapses a two-signal gate to a one-input function (ATL-P003-020,
ATL-D-PAPER003-DERIVED-SIGNAL-COLLAPSE). A Hill-type gate with constant $K$ and
exponent $n$ activates exactly when the positive inputs sum to at least
$K\,(t/(1-t))^{1/n}$, which is $K$ at $t=1/2$ (ATL-P003-021,
ATL-D-PAPER003-HILL-SUM-THRESHOLD). Zero failures in $n$ independent Bernoulli
trials bound the failure rate by $1-0.05^{1/n}$ at 95% confidence
(ATL-P003-017).

The archived immune papers record what was and was not built. Admission needs a
reproduced defect, valid near misses, a declared scope and frozen identities
(ATL-P003-014, ATL-P006-013). The retained catalog holds 61 entries in 14
failure classes, mostly placeholders; its evidence digests hash short
identifying strings, and no baseline code matches proposals against it
(ATL-P006-015, ATL-P006-017, ATL-P006-018,
ATL-D-PAPER006-CATALOG-IS-NONEXECUTING-DATA). A refusal log with a hash chain
detects tail removal, but a rewrite of both file and local header stays
self-consistent unless a separately retained head is compared
(ATL-P006-001–005, ATL-D-PAPER006-RETAINED-ANCHOR). Idle decay at fixed $\tau$
composes by telescoping floor differences (ATL-P006-012,
ATL-D-PAPER006-DECAY-AND-COST-ARITHMETIC). The phrase detectors flag their own
fixtures and cannot see negation; the stored pilot cannot establish the
planned randomized study (ATL-P003-010–012, ATL-P003-018, ATL-P003-019).

## 6. Custody, replay and the evidence record

A hash binds bytes; it authenticates neither a producer nor a build
(ATL-P004-013, ATL-P005-007). Custody of a copied corpus requires a bijection
with the declared inventory, per-file raw digests, and recorded adaptations
(ATL-P011-002, ATL-P011-003). Under this discipline the archive audits found
concrete errors: an artifact verifier that returned `verified: true` 75 times on
empty, wrong-task and unproved responses; Betti numbers that counted graph
cycles in filled complexes, so $b_1=0$ rather than 2 and 4; a claimed
$S^2\times S^2$ carrier with Betti vector $(1,0,1,2,1)$; and a consistency
checker that accepted a contradiction verdict for a zero residual
(ATL-P011-009, ATL-P011-011, ATL-P011-017). Integer Smith replay found
$H_2=\mathbb Z/2$ on the torsion carrier, in agreement with mod-two dimensions
$(1,0,1,1)$ under universal coefficients (ATL-P011-018). Fresh formal and
native replays reproduce $\operatorname{cutCensus}(n,a,b)=2^{n-2}$, the G01 and
G12 baselines, the G07 census and the MUB catalog, and refute a fresh-mark
minimality for one adapter (ATL-P011-010, ATL-P011-012–016).

Historical labels need the same care. Reference self-scores, answer-bearing
identifiers, a field that was true in every record and prompts containing the
answer all inflated earlier results (ATL-P011-005, ATL-P010-038–042,
ATL-P009-012). An adversary gate authorized a cochain with cycle sum 3 because a
later act replaced the cochain, and a critique blocked only when it contained
the words "DEFECT" or "FLAW" (ATL-P009-014–016). The minimum-theorem review
records six concrete harness defects, F01–F06 (ATL-P012-002–008). Leaked
labels, unretained runners and an undisclosed stealth model limit the model
pilots to descriptive counts (ATL-P010-021–037).

## 7. Evidence is not authority

The authority papers formalize the boundary that the preceding sections
observe. Let a terminal be authority, residual or refusal. The constructors are
disjoint, so no residual or refusal output inhabits the authority type, and for
every residual outcome $r$, $\neg\,\mathrm{IsAuth}(\mathrm{residualTerminal}\,r)$
(ATL-N010-001, ATL-N010-002, ATL-N012-007). Refusal is a left zero of the
pipeline monad, $\mathrm{bind}(\mathrm{Refusal}(e),f)=\mathrm{Refusal}(e)$, so a
refused stage halts the pipeline (ATL-N012-004, ATL-N012-005). Proposal
membership does not imply authority, and authority transported along a quotient
by universal quantification is the right adjoint of pullback (ATL-N012-001,
ATL-N012-014). A detector pass, its adequacy for a claim class, and operational
authority are three different predicates (ATL-N011-001). Under class-constancy
on $X/{\sim}$, a detector equals the adequacy predicate exactly when they agree
on one representative per class, and four calibration examples do not
establish adequacy over an unbounded class (ATL-N011-003, ATL-N011-011). A
constant terminalizer fails negative and collision calibration (ATL-N011-007,
ATL-N009-021).

Rates make the same point quantitatively. A zero conditional global-failure
rate is equivalent to almost-sure acceptance soundness, and it does not require
boundary factorization (ATL-N013-015, ATL-N013-016). If proposals arrive at rate
$r_G$ and verifications complete at rate $r_V<r_G$, the unresolved backlog grows
(ATL-N013-010, ATL-N014-026). Positive dual pairing bounds a repair residual
from below (ATL-N013-017). Adding one indistinguishable candidate to a uniquely
selected family removes uniqueness, observation-preserving extensions inflate
plenitude, and a hundred indistinguishable vacua cannot be told apart
(ATL-N015-002, ATL-N015-003, ATL-N015-010, ATL-N015-013). The Sentinel boundary
paper states the same separation as a typed coproduct of primitive difference
and structure in which a nonzero class $Q^1\neq0$ mints no authority
(ATL-N016-001, ATL-N016-005, ATL-N016-017).

The operator, regulation, observer and trace papers apply this to concrete
guards. Acceptance is a function of the diagnostic tuple
$(\Phi_1,\Gamma_2,R_{cl},\Xi)$ and policy, and an operator carries no acceptance
authority (ATL-N006-001, ATL-N006-002). A tuple with $\Phi_{\text{geom}}=0$ and
positive curvature or $\Xi$ is rejected; a lift is admitted exactly when its
penalty is below $\Delta\Phi_{\text{geom}}+\tfrac12\Delta\Phi_{\text{sat}}$
(ATL-N007-001, ATL-N007-004). With natural-number weights an observer admits
$c\to c'$ exactly when the weighted $\ell^1$ norm does not increase
(ATL-N008-001). A reasoning-trace verifier judges declared finite structure,
not language, and $d_1d_0=0$ cannot be derived for extractors over raw text
(ATL-N009-001, ATL-N009-019).

## 8. Derivations recorded by the audit

Part II of the ledger holds the audit's own derivations. They follow one
pattern: identify the predicate a source actually enforces, prove what that
predicate implies, and give a finite control where the implementation omits a
premise its name suggests.

In the PFP runtime and its formal sources, host acceptance is relative to the
configured judges, eight fidelity clauses are checked separately from detector
adequacy, and a constant-pass detector cannot meet both a positive and a
negative control (ATL-D-PFP-ACCEPTANCE, ATL-D-PFP-FIDELITY-ADEQUACY-SEPARATION).
The tower module's `zetaAt` is an arbitrary integer function, not an analytic
zeta function (ATL-D-FORMAL-TOWER-ZETA-SCOPE).

In the immune and evolution systems, support counting uses an exact maximum
independent set over declared correlation keys, which is a graph calculation
rather than statistical independence (ATL-D-SYS-EIS-004). The cochain profile
admits exactly $d_1d_0=0$, so its admitted $\phi_1$ is identically zero and
cannot discriminate inputs (ATL-D-SYS-PCIV-003). A self-computed lineage seal
is not independent provenance (ATL-D-SYS-PCIV-006). Operad signature
composition preserves ordered sources (ATL-D-SYS-OP-001); a Koszul label that
depends on a presentation name is not a resolution (ATL-D-NATIVE03-OPERADS-002).

In the native kernels, the substantive owners replay complete finite witnesses.
Lumpability checks $MH=HB$, and associativity then gives $M^nH=HB^n$
(ATL-D-RLA-C11). Characteristic polynomials agree with permutation
determinants (ATL-D-RLA-C13); the pseudoinverse replays all four Penrose
identities (ATL-D-RLA-C15); the $LDL^{\top}$ path decides positive
semidefiniteness (ATL-D-RLA-C07). Older categorical owners check presentations
rather than lawful carriers (ATL-D-RCT-C28), and a disabled A-infinity draft
treats a nonzero higher product as nonformality, which an exact example over
$\mathbb F_2$ refutes (ATL-D-RHT-C07).

In the certified challenges, each family states the exact witness that would
certify its relation: sheaf kernel and cokernel bases, integral Smith forms,
persistence reductions and modular obstructions, with the implementation gaps
recorded beside them (ATL-D-AC1120-C011–ATL-D-AC1120-C020 in the index). The
remaining rows record test, workflow, teaching and governance findings of the
same kind. They are listed by area in the index.

## 9. Open problems and non-claims

Several archived claims are registered placeholders, open conjectures or
unmeasured campaigns (ATL-N002-022–028, ATL-N003-022, ATL-N003-023,
ATL-N014-033, ATL-N016-018, ATL-P014-005, ATL-P019-006). No archived paper
establishes model improvement, general detector efficacy, learner effect, a
physical or semantic foundation, or authority from evidence
(ATL-P007-008, ATL-P018-005, ATL-P019-009, ATL-P011-023, ATL-N003-017,
ATL-N010-011). The audit itself is unfinished: per-file reading, supporting
artifact assessment and native-to-formal correspondence remain open in the DAG.

## Claim index

<!-- claim-index:start (generated by dag/build_atlas.py; do not edit by hand) -->

Every ledger row is listed here once. *Prose* counts the rows that the text above cites by ID;
the others are covered by the summary of their paper or area in the section named.

| Paper | Atlas IDs | Rows | Cited in prose | Sections |
| --- | --- | --- | --- | --- |
| pfp/000_pfp_introduction | ATL-P000-001–006 | 6 | 6 | §1 |
| pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions | ATL-P001-001–010 | 10 | 7 | §2 |
| pfp/002_pfp_signed_presentations_and_search_frontier | ATL-P002-001–012 | 12 | 6 | §3 |
| pfp/003_pfp_host_admitted_failure_detectors | ATL-P003-001–030 | 30 | 10 | §5 |
| pfp/004_pfp_native_verification_and_evidence_custody | ATL-P004-001–018 | 18 | 2 | §2, §6 |
| pfp/005_pfp_practitioners_field_manual | ATL-P005-001–019 | 19 | 4 | §2, §6 |
| pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining | ATL-P006-001–018 | 18 | 10 | §5 |
| pfp/007_pfp_executable_lessons_and_evidence_boundaries | ATL-P007-001–014 | 14 | 4 | §2, §9 |
| pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks | ATL-P008-001–020 | 20 | 1 | §2 |
| pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates | ATL-P009-001–018 | 18 | 5 | §2, §6 |
| pfp/010_pfp_holonomy_checks_and_model_pilots | ATL-P010-001–048 | 48 | 38 | §3, §6 |
| pfp/011_recreated_demos_and_proposal_fidelity_evidence | ATL-P011-001–023 | 23 | 15 | §2, §6, §9 |
| pfp/012_pfp_the_minimum_theorem | ATL-P012-001–012 | 12 | 10 | §4, §6 |
| pfp/013_pfp_task_bound_claims_and_hallucination_control | ATL-P013-001–004 | 4 | 4 | §4 |
| pfp/014_pfp_recursive_reentry_and_evidence_scope | ATL-P014-001–005 | 5 | 5 | §4, §5, §9 |
| pfp/015_pfp_local_to_global_agent_composition | ATL-P015-001–004 | 4 | 4 | §4 |
| pfp/016_pfp_future_faithful_compression_and_cost | ATL-P016-001–004 | 4 | 4 | §4 |
| pfp/017_pfp_proposal_channels_and_internal_interventions | ATL-P017-001–014 | 14 | 14 | §2, §4 |
| pfp/018_pfp_operadic_composition_and_bounded_ddc_repair | ATL-P018-001–005 | 5 | 1 | §9 |
| pfp/019_pfp_evidence_bound_harness_evolution | ATL-P019-001–009 | 9 | 2 | §9 |
| pfp/020_pfp_frontier_research | ATL-P020-001–012 | 12 | 12 | §1 |
| pfp/021_pfp_workflow_dag_process_and_mathematics | ATL-P021-001–008 | 8 | 8 | §1 |
| non_pfp/001_l1_native_cohomology | ATL-N001-001–020 | 20 | 19 | §2 |
| non_pfp/002_l1_obstruction_framework | ATL-N002-001–028 | 28 | 21 | §2, §9 |
| non_pfp/003_degree_wise_dsl | ATL-N003-001–023 | 23 | 11 | §2, §4, §9 |
| non_pfp/004_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects | ATL-N004-001–027 | 27 | 26 | §2 |
| non_pfp/005_operator_lifts_trace_metrics_and_representation_limits | ATL-N005-001–007 | 7 | 7 | §2 |
| non_pfp/006_operator_proposal_layer_for_finite_l1_obstruction_systems | ATL-N006-001–019 | 19 | 5 | §2, §4, §7 |
| non_pfp/007_constraint_level_regulation_via_multi_channel_obstruction_diagnostics | ATL-N007-001–005 | 5 | 2 | §7 |
| non_pfp/008_observer_robust_control_of_obstruction_diagnostics | ATL-N008-001–006 | 6 | 1 | §7 |
| non_pfp/009_reasoning_trace_validation_via_l1_obstruction_geometry | ATL-N009-001–025 | 25 | 3 | §7 |
| non_pfp/010_the_authority_firewall_a_machine_checked_separation_of_evidence_from_authority_in_finite_systems | ATL-N010-001–024 | 24 | 3 | §7, §9 |
| non_pfp/011_authority_firewall_and_verification_limits | ATL-N011-001–013 | 13 | 4 | §7 |
| non_pfp/012_role_non_impersonation_and_authority_preservation | ATL-N012-001–014 | 14 | 6 | §4, §7 |
| non_pfp/013_the_authority_gap | ATL-N013-001–018 | 18 | 5 | §4, §7 |
| non_pfp/014_finite_authority_and_non_terminal_computation | ATL-N014-001–033 | 33 | 4 | §4, §7, §9 |
| non_pfp/015_representation_abundance_is_not_physical_authority | ATL-N015-001–014 | 14 | 9 | §2, §4, §7 |
| non_pfp/016_the_sentinel_boundary | ATL-N016-001–018 | 18 | 4 | §7, §9 |

Audit derivations (Part II of the ledger), by the repository area their evidence cites:

**Archived papers** (104 rows, 19 cited in prose): ATL-D-PAPER000-FINITE-TEACHING-CONTRACT, ATL-D-PAPER000-CYCLE-CAPSTONE, ATL-D-PAPER000-FINITE-CAPSTONE-SCOPE, ATL-D-PAPER001-EXACT-GRAPH-CERTIFICATE, ATL-D-PAPER001-FIXED-FOCK-GAP, ATL-D-PAPER001-FORMAL-SCOPE, ATL-D-PAPER002-FINITE-SIGNED-BALANCE, ATL-D-PAPER002-EXACT-FIXED-BASIS-REDUCTION, ATL-D-PAPER002-CONTIGUOUS-SEARCH-REPLAY, ATL-D-PAPER003-DERIVED-SIGNAL-COLLAPSE, ATL-D-PAPER003-HILL-SUM-THRESHOLD, ATL-D-PAPER003-PREDICATE-SCREEN-SOUNDNESS, ATL-D-PAPER003-PACKAGE-ROLLBACK-BOUNDARY, ATL-D-PAPER004-FINITE-EXACT-WITNESS, ATL-D-PAPER004-WEIGHTED-CYCLE, ATL-D-PAPER004-CONDITIONAL-LEAN-SLICE, ATL-D-PAPER004-CUSTODY-CEILING, ATL-D-PAPER004-REUSABLE-WORKFLOW, ATL-D-PAPER005-WEIGHTED-COBOUNDARY-DISTANCE, ATL-D-PAPER005-INSTANCE-REPLACEMENT, ATL-D-PAPER006-DECAY-AND-COST-ARITHMETIC, ATL-D-PAPER006-CATALOG-IS-NONEXECUTING-DATA, ATL-D-PAPER006-CONTROLLED-REUSE-UTILITY, ATL-D-PAPER007-CYCLE-RESIDUAL-IDENTITY, ATL-D-PAPER007-FAULT-SENSITIVE-CONTROL, ATL-D-PAPER007-CONDITIONAL-FORMAL-BOUNDS, ATL-D-PAPER007-LESSON-AND-REPLAY-UTILITY, ATL-D-PAPER008-SINGLETON-LEFT-INVERSE, ATL-D-PAPER008-INTEGER-GRAPH-CERTIFICATES, ATL-D-PAPER008-FEASIBILITY-BEFORE-GAP, ATL-D-PAPER008-FORWARD-DIFFERENCE-CERTIFICATE, ATL-D-PAPER008-SCOPED-CENSUS-GATE, ATL-D-PAPER008-CONDITIONAL-PAIRED-ARITHMETIC, ATL-D-PAPER009-EXACT-TRIANGLE-INVARIANT, ATL-D-PAPER009-EXACT-HISTORICAL-RECOUNT, ATL-D-PAPER009-FINITE-FORGETFUL-COUNTERMODEL, ATL-D-PAPER009-TRIGGER-DOES-NOT-SUPPLY-LICENSE, ATL-D-PAPER009-CONTRACT-FIDELITY-IS-CONDITIONAL, ATL-D-PAPER009-BOUNDED-CPYTHON-NOTEBOOK-REPLAY, ATL-D-PAPER010-DATA-FINITE-GROUP-AND-LATTICE-ADMISSION, ATL-D-PAPER010-DATA-LOCAL-VERSUS-GLOBAL-HOLONOMY, ATL-D-PAPER010-DATA-EXTRACTION-AND-DESCRIPTIVE-RECOUNT, ATL-D-PAPER010-FINITE-GROUP-ADMISSION, ATL-D-PAPER010-RECTANGULAR-HOLONOMY-CLASSIFIER, ATL-D-PAPER010-WITNESS-ACCEPTANCE, ATL-D-PAPER010-IDENTITY-SKIP-BOUND, ATL-D-PAPER010-REPLAY-AND-RECOUNT-CEILING, ATL-D-P011-AGG-C001, ATL-D-P011-AGG-C002, ATL-D-P011-AGG-C003, ATL-D-P011-AGG-C004, ATL-D-P011-AGG-C005, ATL-D-P011-AGG-C006, ATL-D-P011CORE-C01, ATL-D-P011CORE-C02, ATL-D-P011CORE-C03, ATL-D-PAPER011-HISTORY-FINITE-FACTORIZATION, ATL-D-PAPER011-HISTORY-SHORTEST-PATH-BOUND, ATL-D-P011-FINITE-C001, ATL-D-P011-FINITE-C002, ATL-D-P011-FINITE-C003, ATL-D-P011-FINITE-C004, ATL-D-P011HIST-C01, ATL-D-P011HIST-C02, ATL-D-P011HIST-C03, ATL-D-P011HIST-C04, ATL-D-P011HIST-C05, ATL-D-P011HIST-C06, ATL-D-P011LEDGER-CL01, ATL-D-P011LEDGER-CL02, ATL-D-P011LEDGER-CL03, ATL-D-P011LEDGER-CL04, ATL-D-P011LEDGER-CL05, ATL-D-P011LEDGER-CL06, ATL-D-P011LEDGER-CL07, ATL-D-P011LEDGER-CL08, ATL-D-P011LEDGER-CL09, ATL-D-P011LEDGER-CL10, ATL-D-P011-NATIVE-C001, ATL-D-P011-NATIVE-C002, ATL-D-P011-NATIVE-C003, ATL-D-P011-NATIVE-C004, ATL-D-P011-NATIVE-C005, ATL-D-P011-NATIVE-C006, ATL-D-P011-NATIVE-C007, ATL-D-P011REC-C01, ATL-D-P011REC-C02, ATL-D-P011REC-C03, ATL-D-P011REC-C04, ATL-D-P011REC-C05, ATL-D-P011REC-C06, ATL-D-P011REC-C07, ATL-D-P011REC-C08, ATL-D-PAPER011-SUPPORT-L1-CERTIFICATE-BOUND, ATL-D-PAPER011-SUPPORT-PARITY-OBSTRUCTION, ATL-D-PUB-C01, ATL-D-PUB-C02, ATL-D-PUB-C03, ATL-D-PUB-C04, ATL-D-PUB-C05, ATL-D-PUB-C06, ATL-D-PUB-C07, ATL-D-PUB-C08, ATL-D-SUP-C1.

**Epistemic immune system** (17 rows, 1 cited in prose): ATL-D-SYS-EIS-001, ATL-D-SYS-EIS-002, ATL-D-SYS-EIS-003, ATL-D-SYS-EIS-004, ATL-D-SYS-EIS-005, ATL-D-SYS-EIS-006, ATL-D-SYS-EIS-007, ATL-D-EA-C01, ATL-D-EA-C02, ATL-D-EA-C03, ATL-D-EIS-TWO-SIGNAL-C001, ATL-D-EPE-C02, ATL-D-EPE-C05, ATL-D-EPC02, ATL-D-EPC04, ATL-D-EPTS-C03, ATL-D-MEP-C03.

**Native Rust kernels** (275 rows, 7 cited in prose): ATL-D-NATIVE-EIS-001, ATL-D-NATIVE-EIS-002, ATL-D-NATIVE-EIS-003, ATL-D-NATIVE-EIS-004, ATL-D-NATIVE-EIS-005, ATL-D-NATIVE-EIS-006, ATL-D-NATIVE-PCIV-001, ATL-D-NATIVE-PCIV-002, ATL-D-NATIVE-PCIV-003, ATL-D-NATIVE-PCIV-004, ATL-D-NATIVE-OP-001, ATL-D-NATIVE-OP-002, ATL-D-NATIVE-OP-003, ATL-D-NATIVE-OP-004, ATL-D-NATIVE-OP-005, ATL-D-NATIVE02-EIS-001, ATL-D-NATIVE02-EIS-002, ATL-D-NATIVE02-EIS-003, ATL-D-NATIVE02-OPERADS-001, ATL-D-NATIVE02-OPERADS-002, ATL-D-NATIVE02-OPERADS-003, ATL-D-NATIVE02-OPERADS-004, ATL-D-NATIVE02-PCIV-001, ATL-D-NATIVE02-PCIV-002, ATL-D-NATIVE02-PCIV-003, ATL-D-NATIVE02-PCIV-004, ATL-D-NATIVE03-OPERADS-001, ATL-D-NATIVE03-OPERADS-002, ATL-D-NATIVE03-OPERADS-003, ATL-D-NATIVE03-OPERADS-004, ATL-D-NATIVE03-OPERADS-005, ATL-D-NATIVE03-OPERADS-006, ATL-D-NATIVE03-PCIV-007, ATL-D-NATIVE03-PCIV-008, ATL-D-NATIVE03-PCIV-009, ATL-D-NATIVE03-FIXTURES-010, ATL-D-NATIVE03-FIXTURES-011, ATL-D-RAD-C01, ATL-D-RAD-C02, ATL-D-RAD-C03, ATL-D-RAD-C04, ATL-D-RAD-C05, ATL-D-RAD-C06, ATL-D-RCT-C30, ATL-D-RCT-C29, ATL-D-RCT-C28, ATL-D-RCT-C27, ATL-D-RCT-C26, ATL-D-RCT-C25, ATL-D-RCT-C24, ATL-D-RCT-C23, ATL-D-RCT-C22, ATL-D-RCT-C21, ATL-D-RCT-C20, ATL-D-RCT-C19, ATL-D-RCT-C18, ATL-D-RCT-C17, ATL-D-RCT-C16, ATL-D-RCT-C15, ATL-D-RCT-C14, ATL-D-RCT-C13, ATL-D-RCT-C12, ATL-D-RCT-C11, ATL-D-RCT-C10, ATL-D-RCT-C08, ATL-D-RCT-C09, ATL-D-RCT-C07, ATL-D-RCT-C06, ATL-D-RCT-C01, ATL-D-RCT-C02, ATL-D-RCT-C03, ATL-D-RCT-C04, ATL-D-RCT-C05, ATL-D-RDR-C01, ATL-D-RDR-C02, ATL-D-RDR-C03, ATL-D-RDR-C04, ATL-D-RFA-CL001, ATL-D-RFA-CL002, ATL-D-RFA-CL003, ATL-D-RFA-CL004, ATL-D-RFA-CL005, ATL-D-RFA-CL006, ATL-D-RFA-CL007, ATL-D-RFA-CL008, ATL-D-RFA-CL009, ATL-D-RFA-CL010, ATL-D-RFA-CL011, ATL-D-RFA-CL012, ATL-D-RFA-CL013, ATL-D-RFA-CL014, ATL-D-RFA-CL015, ATL-D-RFA-CL016, ATL-D-RFA-CL017, ATL-D-RFA-CL018, ATL-D-RFA-CL019, ATL-D-RFA-CL020, ATL-D-RFA-CL021, ATL-D-RFA-CL022, ATL-D-RFA-CL023, ATL-D-RFA-CL024, ATL-D-RFA-CL025, ATL-D-RFA-CL026, ATL-D-RFA-CL027, ATL-D-RFA-CL028, ATL-D-RFA-CL029, ATL-D-RFA-CL030, ATL-D-RFA-CL031, ATL-D-RFA-CL032, ATL-D-RFA-CL033, ATL-D-RFC-C001, ATL-D-RFC-C002, ATL-D-RFC-C003, ATL-D-RFC-C004, ATL-D-RFC-C005, ATL-D-RFC-C006, ATL-D-RFC-C007, ATL-D-RFC-C008, ATL-D-RFC-C009, ATL-D-RFC-C010, ATL-D-RFC-C011, ATL-D-RUSTHOMOLOGY-CL001, ATL-D-RUSTHOMOLOGY-CL002, ATL-D-RUSTHOMOLOGY-CL003, ATL-D-RUSTHOMOLOGY-CL004, ATL-D-RUSTHOMOLOGY-CL005, ATL-D-RUSTHOMOLOGY-CL006, ATL-D-RUSTHOMOLOGY-CL007, ATL-D-RUSTHOMOLOGY-CL008, ATL-D-RUSTHOMOLOGY-CL009, ATL-D-RUSTHOMOLOGY-CL010, ATL-D-RUSTHOMOLOGY-CL011, ATL-D-RUSTHOMOLOGY-CL012, ATL-D-RUSTHOMOLOGY-CL013, ATL-D-RUSTHOMOLOGY-CL014, ATL-D-RUSTHOMOLOGY-CL015, ATL-D-RUSTHOMOLOGY-CL016, ATL-D-RUSTHOMOLOGY-CL017, ATL-D-RUSTHOMOLOGY-CL018, ATL-D-RUSTHOMOLOGY-CL019, ATL-D-RUSTHOMOLOGY-CL020, ATL-D-RUSTHOMOLOGY-CL021, ATL-D-RUSTHOMOLOGY-CL022, ATL-D-RUSTHOMOLOGY-CL023, ATL-D-RUSTHOMOLOGY-CL024, ATL-D-RUSTHOMOLOGY-CL025, ATL-D-RUSTHOMOLOGY-CL026, ATL-D-RUSTHOMOLOGY-CL027, ATL-D-RUSTHOMOLOGY-CL028, ATL-D-RUSTHOMOLOGY-CL029, ATL-D-RHT-C01, ATL-D-RHT-C02, ATL-D-RHT-C03, ATL-D-RHT-C04, ATL-D-RHT-C05, ATL-D-RHT-C06, ATL-D-RHT-C07, ATL-D-RLA-C01, ATL-D-RLA-C02, ATL-D-RLA-C03, ATL-D-RLA-C04, ATL-D-RLA-C05, ATL-D-RLA-C06, ATL-D-RLA-C07, ATL-D-RLA-C08, ATL-D-RLA-C09, ATL-D-RLA-C10, ATL-D-RLA-C11, ATL-D-RLA-C12, ATL-D-RLA-C13, ATL-D-RLA-C14, ATL-D-RLA-C15, ATL-D-RLA-C16, ATL-D-RLA-C17, ATL-D-RLA-C18, ATL-D-RLA-C19, ATL-D-RLA-C20, ATL-D-RLA-C21, ATL-D-RLA-C22, ATL-D-RLA-C23, ATL-D-RLA-C24, ATL-D-RLA-C25, ATL-D-RLA-C26, ATL-D-RLA-C27, ATL-D-RLA-C28, ATL-D-RLA-C29, ATL-D-RLA-C30, ATL-D-RLA-C31, ATL-D-RLA-C32, ATL-D-RLA-C33, ATL-D-RLA-C34, ATL-D-RLA-C35, ATL-D-RLA-C36, ATL-D-ROUT-C001, ATL-D-ROUT-C002, ATL-D-ROUT-C003, ATL-D-ROUT-C004, ATL-D-ROUT-C005, ATL-D-ROUT-C006, ATL-D-ROUT-C007, ATL-D-ROUT-C008, ATL-D-ROUT-C009, ATL-D-ROUT-C010, ATL-D-ROUT-C011, ATL-D-ROUT-C012, ATL-D-RPF-C001, ATL-D-RPF-C002, ATL-D-RPF-C003, ATL-D-RPF-C004, ATL-D-RPF-C005, ATL-D-RPF-C006, ATL-D-RPF-C007, ATL-D-RPF-C008, ATL-D-RPF-C012, ATL-D-RPF-C010, ATL-D-RPF-C011, ATL-D-RPF-C009, ATL-D-RPF-C013, ATL-D-RPF-C014, ATL-D-RPF-C015, ATL-D-RPF-C016, ATL-D-RPF-C017, ATL-D-RPF-C018, ATL-D-RPF-C019, ATL-D-RPF-C020, ATL-D-RPF-C021, ATL-D-RPF-C022, ATL-D-QP-C001, ATL-D-QP-C002, ATL-D-QP-C003, ATL-D-QP-C004, ATL-D-QP-C005, ATL-D-QP-C006, ATL-D-QP-C007, ATL-D-QP-C008, ATL-D-QP-C009, ATL-D-QP-C010, ATL-D-QP-C011, ATL-D-QP-C012, ATL-D-QP-C013, ATL-D-QP-C014, ATL-D-QP-C015, ATL-D-QP-C016, ATL-D-QP-C017, ATL-D-QP-C018, ATL-D-QP-C019, ATL-D-QP-C020, ATL-D-QP-C021, ATL-D-QP-C022, ATL-D-QP-C023, ATL-D-QP-C024, ATL-D-QP-C025, ATL-D-QP-C026, ATL-D-QP-C027, ATL-D-QP-C028, ATL-D-QP-C029, ATL-D-QP-C030, ATL-D-QP-C031, ATL-D-QP-C032, ATL-D-QP-C033, ATL-D-RQPR-C001, ATL-D-RQPR-C002, ATL-D-RQPR-C003, ATL-D-RQPR-C004, ATL-D-RQPR-C005, ATL-D-RQPR-C006, ATL-D-RQPR-C007, ATL-D-RQPR-C008, ATL-D-RQPR-C009, ATL-D-RQPR-C010, ATL-D-RQPR-C011, ATL-D-RQPR-C012, ATL-D-RQPR-C013, ATL-D-RQPR-C014, ATL-D-RQPR-C015.

**Operads and skills** (34 rows, 1 cited in prose): ATL-D-SYS-OP-001, ATL-D-SYS-OP-002, ATL-D-SYS-OP-003, ATL-D-SYS-OP-004, ATL-D-SYS-OP-005, ATL-D-SYS-OP-006, ATL-D-OPR-C01, ATL-D-OPR-C02, ATL-D-OPR-C03, ATL-D-OPR-C04, ATL-D-ORR-C01, ATL-D-ORR-C02, ATL-D-ORR-C03, ATL-D-ORR-C04, ATL-D-OPSKILL-C001, ATL-D-OPSKILL-C002, ATL-D-OPSKILL-C003, ATL-D-OPSKILL-C004, ATL-D-OPSKILL-C005, ATL-D-OPSKILL-C006, ATL-D-OPSKILL-C007, ATL-D-OPSKILL-C008, ATL-D-OPSKILL-C009, ATL-D-OPSKILL-C010, ATL-D-OPSKILL-C011, ATL-D-OPSKILL-C012, ATL-D-OPSKILL-C013, ATL-D-OPSKILL-C014, ATL-D-OCR-C01, ATL-D-OCR-C02, ATL-D-OCR-C03, ATL-D-OCR-C04, ATL-D-OCR-C05, ATL-D-OCR-C06.

**Operations, adversary and governance code** (21 rows, 0 cited in prose): ATL-D-EDU-C08, ATL-D-GOVERNANCE-RECORD-FLOOR, ATL-D-GOV-C01, ATL-D-GOV-C02, ATL-D-GOV-C03, ATL-D-GOV-C04, ATL-D-GOV-C05, ATL-D-OAR-C01, ATL-D-OAR-C02, ATL-D-OAR-C03, ATL-D-OAR-C04, ATL-D-OAR-C05, ATL-D-OAR-C06, ATL-D-OGD-C01, ATL-D-OGD-C02, ATL-D-OGD-C03, ATL-D-OGD-C04, ATL-D-OGD-C05, ATL-D-OGD-C06, ATL-D-ASE-C01, ATL-D-ASE-C02.

**Other repository sources** (9 rows, 2 cited in prose): ATL-D-CONFIG-CLAIM-02, ATL-D-HISTORY-REJECTION-PULLBACK, ATL-D-HISTORY-REENTRY-CARRIERS, ATL-D-HISTORY-FREE-INFORMATION-COST, ATL-D-PAPER001-ARTIFACT-ARCHIVE-CUSTODY, ATL-D-PAPER001-ARTIFACT-DEBATE-ARITHMETIC, ATL-D-SUP-C3, ATL-D-WIKIT-C01, ATL-D-WIKIT-C08.

**PFP runtime, Lab, contracts and formal sources** (152 rows, 5 cited in prose): ATL-D-PFP-ACCEPTANCE, ATL-D-PFP-INPUT-BINDING, ATL-D-PFP-BOUNDED-STAGES, ATL-D-PFP-HOST-TERMINAL, ATL-D-PFP-FIDELITY-ADEQUACY-SEPARATION, ATL-D-PFP-INTERNAL-EFFECT-CLOSURE, ATL-D-CONFIG-CLAIM-01, ATL-D-FORMAL-PACKET-COLLISION, ATL-D-FORMAL-COUNT-LIFT, ATL-D-FORMAL-TOWER-ZETA-SCOPE, ATL-D-ACSET-C01, ATL-D-LCF-C1, ATL-D-LCF-C2, ATL-D-LCF-C3, ATL-D-LCF-C4, ATL-D-LCF-C5, ATL-D-LCF-C6, ATL-D-LCF-C7, ATL-D-PAPER006-RETAINED-ANCHOR, ATL-D-ADAPT-C01, ATL-D-ADAPT-C02, ATL-D-PFPAPPREM-C001, ATL-D-PFPAPPREM-C002, ATL-D-PFPAPPREM-C003, ATL-D-PFPAPPREM-C004, ATL-D-PFPAPPREM-C005, ATL-D-PFPAPPREM-C006, ATL-D-PFPAPPREM-C007, ATL-D-PFPAPPREM-C008, ATL-D-PFPAPPREM-C009, ATL-D-PFPAPPREM-C010, ATL-D-PFPAPPREM-C011, ATL-D-PFPAPPREM-C012, ATL-D-PFPAPPREM-C013, ATL-D-PFPAPPREM-C014, ATL-D-PFPDOMAIN-CL01, ATL-D-PFPDOMAIN-CL02, ATL-D-PFPDOMAIN-CL03, ATL-D-PFPDOMAIN-CL04, ATL-D-PFPDOMAIN-CL05, ATL-D-PFPDOMAIN-CL06, ATL-D-PFPDOMAIN-CL07, ATL-D-PFPDOMAIN-CL08, ATL-D-PFPDOMAIN-CL09, ATL-D-PFPDOMAIN-CL10, ATL-D-PFPDOMAIN-CL11, ATL-D-PFPDOMAIN-CL12, ATL-D-PFPDOMAIN-CL13, ATL-D-PFPDOMAIN-CL14, ATL-D-PFPDOMAIN-CL15, ATL-D-PFPDOMAIN-CL16, ATL-D-PFPDOMAIN-CL17, ATL-D-PFPDOMAIN-CL18, ATL-D-PFPDOMAIN-CL19, ATL-D-PFPDOMAIN-CL20, ATL-D-PFPDOMAIN-CL21, ATL-D-PFPDOMAIN-CL22, ATL-D-PFPDOMAIN-CL23, ATL-D-PFPDOMAIN-CL24, ATL-D-PFPDOMAIN-CL25, ATL-D-PFPDOMAIN-CL26, ATL-D-PFPDOMAIN-CL27, ATL-D-PFPINFRA-C001, ATL-D-PFPINFRA-C002, ATL-D-PFPINFRA-C003, ATL-D-PFPINFRA-C004, ATL-D-PFPINFRA-C005, ATL-D-PFPINFRA-C006, ATL-D-PFPINFRA-C007, ATL-D-PFPINFRA-C008, ATL-D-PFPINFRA-C009, ATL-D-PFPINFRA-C010, ATL-D-PFPINFRA-C011, ATL-D-PFPINFRA-C012, ATL-D-PFPINFRA-C013, ATL-D-PFPINFRA-C014, ATL-D-PFPINFRA-C015, ATL-D-PFPINFRA-C016, ATL-D-PFPINFRA-C017, ATL-D-PFPINFRA-C018, ATL-D-PFPINFRA-C019, ATL-D-PFPINFRA-C020, ATL-D-PFPTESTS-CL001, ATL-D-PFPTESTS-CL002, ATL-D-PFPTESTS-CL003, ATL-D-PFPTESTS-CL004, ATL-D-PFPTESTS-CL005, ATL-D-PFPTESTS-CL006, ATL-D-PFPTESTS-CL007, ATL-D-PFPTESTS-CL008, ATL-D-PFPTESTS-CL009, ATL-D-PFPTESTS-CL010, ATL-D-PFPTESTS-CL011, ATL-D-PFPTESTS-CL012, ATL-D-PFPTESTS-CL013, ATL-D-PFPTESTS-CL014, ATL-D-PFPTESTS-CL015, ATL-D-PFPTESTS-CL016, ATL-D-PFPTESTS-CL017, ATL-D-PFPTESTS-CL018, ATL-D-PFPTESTS-CL019, ATL-D-PFPTESTS-CL020, ATL-D-PFPTESTS-CL021, ATL-D-PFPTESTS-CL022, ATL-D-PFPTESTS-CL023, ATL-D-PFPTESTS-CL024, ATL-D-PFPTESTS-CL025, ATL-D-PFPTESTS-CL026, ATL-D-PFPTESTS-CL027, ATL-D-PFPTESTS-CL028, ATL-D-PFPTESTS-CL029, ATL-D-PFPTESTS-CL030, ATL-D-PFPTESTS-CL031, ATL-D-PFPTESTS-CL032, ATL-D-PFPTESTS-CL033, ATL-D-PFPTESTS-CL034, ATL-D-PFPTESTS-CL035, ATL-D-PFPTESTS-CL036, ATL-D-PFPTESTS-CL037, ATL-D-PFPTESTS-CL038, ATL-D-PFPTESTS-CL039, ATL-D-PFPTESTS-CL040, ATL-D-PFPTESTS-CL041, ATL-D-PFPTESTS-CL042, ATL-D-PFPTESTS-CL043, ATL-D-PFPTESTS-CL044, ATL-D-PFPTESTS-CL045, ATL-D-PFPTESTS-CL046, ATL-D-PFPTESTS-CL047, ATL-D-PFPTESTS-CL048, ATL-D-PFPTESTS-CL049, ATL-D-PFPTESTS-CL050, ATL-D-PFPTESTS-CL051, ATL-D-PFPTESTS-CL052, ATL-D-PFPTESTS-CL053, ATL-D-PFPTESTS-CL054, ATL-D-PFPTESTS-CL055, ATL-D-PFPTESTS-CL056, ATL-D-PFPTESTS-CL057, ATL-D-PFPTESTS-CL058, ATL-D-PFPTESTS-CL059, ATL-D-PFPTESTS-CL060, ATL-D-PFPTESTS-CL061, ATL-D-ASE-C03, ATL-D-ASE-C04, ATL-D-AWS-C02, ATL-D-AWS-C03, ATL-D-AWS-C04, ATL-D-AWS-C08, ATL-D-PFP-C011-L1-CERTIFICATE, ATL-D-PFP-LAB-FINITE-REPAIR, ATL-D-PFP-EXACT-SCALARS-AND-NATIVE-PORTS.

**Prompt civilization** (21 rows, 2 cited in prose): ATL-D-SYS-PCIV-001, ATL-D-SYS-PCIV-002, ATL-D-SYS-PCIV-003, ATL-D-SYS-PCIV-004, ATL-D-SYS-PCIV-005, ATL-D-SYS-PCIV-006, ATL-D-SYS-PCIV-007, ATL-D-SYS-PCIV-008, ATL-D-SYS-PCIV-009, ATL-D-SYS-PCIV-010, ATL-D-EDU-C07, ATL-D-PCIV-QUOTIENT-TAINT-C001, ATL-D-EPE-C04, ATL-D-EPE-C06, ATL-D-EPC01, ATL-D-EPC03, ATL-D-EPTS-C04, ATL-D-MEP-C01, ATL-D-MEP-C02, ATL-D-PCN-C01, ATL-D-PCN-C02.

**Teaching material and wiki** (33 rows, 0 cited in prose): ATL-D-EDU-C01, ATL-D-EDU-C02, ATL-D-EDU-C03, ATL-D-EDU-C04, ATL-D-EDU-C05, ATL-D-EDU-C06, ATL-D-EPE-C01, ATL-D-EPE-C03, ATL-D-EPTS-C01, ATL-D-EPTS-C02, ATL-D-MOT-C01, ATL-D-OEA-C01, ATL-D-OEA-C02, ATL-D-OEA-C03, ATL-D-OEA-C04, ATL-D-OEA-C05, ATL-D-OET-C01, ATL-D-OET-C02, ATL-D-OET-C03, ATL-D-WIKI-C01, ATL-D-WIKI-C02, ATL-D-WIKI-C03, ATL-D-WIKI-C04, ATL-D-WIKIT-C02, ATL-D-WIKIT-C03, ATL-D-WIKIT-C04, ATL-D-WIKIT-C05, ATL-D-WIKIT-C06, ATL-D-WIKIT-C07, ATL-D-WIKI-WFD-C01, ATL-D-WIKI-WFD-C02, ATL-D-WIKI-WFD-C03, ATL-D-WIKI-WFD-C04.

**Workflows, challenges and benchmarks** (74 rows, 3 cited in prose): ATL-D-AC1120-C011, ATL-D-AC1120-C012, ATL-D-AC1120-C013, ATL-D-AC1120-C014, ATL-D-AC1120-C015, ATL-D-AC1120-C016, ATL-D-AC1120-C017, ATL-D-AC1120-C018, ATL-D-AC1120-C019, ATL-D-AC1120-C020, ATL-D-CAA-C01, ATL-D-CAA-C02, ATL-D-AC2130-C021, ATL-D-AC2130-C022, ATL-D-AC2130-C023, ATL-D-AC2130-C024, ATL-D-AC2130-C025, ATL-D-AC2130-C026, ATL-D-AC2130-C027, ATL-D-AC2130-C028, ATL-D-AC2130-C029, ATL-D-AC2130-C030, ATL-D-AC2130-CUSTODY, ATL-D-CAQ-C027-01, ATL-D-AC31-C01, ATL-D-AC32-C01, ATL-D-AC33-C01, ATL-D-AC34-C01, ATL-D-AC35-C01, ATL-D-AC36-C01, ATL-D-AC37-C01, ATL-D-AC38-C01, ATL-D-AC39-C01, ATL-D-AC40-C01, ATL-D-CAP-C01, ATL-D-CAP-C02, ATL-D-AC41-C01, ATL-D-AC42-C01, ATL-D-AC43-C01, ATL-D-AC44-C01, ATL-D-AC45-C01, ATL-D-AC46-C01, ATL-D-AC47-C01, ATL-D-AC48-C01, ATL-D-AC49-C01, ATL-D-AC50-C01, ATL-D-CAF-C01, ATL-D-AC51-C01, ATL-D-AC52-C01, ATL-D-AC53-C01, ATL-D-AC54-C01, ATL-D-AC55-C01, ATL-D-AC56-C01, ATL-D-AC57-C01, ATL-D-AC58-C01, ATL-D-AC59-C01, ATL-D-CAG-C01, ATL-D-HAM-C001, ATL-D-HAM-C002, ATL-D-HOST-CHARPOLY-C001, ATL-D-ACSET-C02, ATL-D-NATIVE-CHARPOLY-C001, ATL-D-SUP-C2, ATL-D-REUSE-SLICE-C001, ATL-D-ASE-C05, ATL-D-WLR-C01, ATL-D-WLR-C02, ATL-D-WLR-C03, ATL-D-WLR-C04, ATL-D-AWS-C01, ATL-D-AWS-C05, ATL-D-AWS-C06, ATL-D-AWS-C07, ATL-D-RPR-C001.

<!-- claim-index:end -->
