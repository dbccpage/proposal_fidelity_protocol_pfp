# L1 obstruction framework claim ledger

**Scope summary (2026-10-15):** The general real $L^p$/Schatten discussion is prose mathematics, not a completed
Lean formalization. Lean modules use integer three-cycle cochains, natural
exponents and explicit hypotheses. Zero energy of a difference implies gauge-fixed
equality; this does not establish strict convexity or general minimizer uniqueness.
The finite list certificate uses capacity, circulation and saturation hypotheses.
It is not a general Fenchel-Rockafellar duality proof.

Python $p=2$ and $p=\infty$ solvers use rational arithmetic. Interior-$p$ iterations
and matrix singular values use float64. `numerical_checks_passed` reports tolerance
checks; `is_certified` is always false for the interior-$p$ iterations. The weighted
$p=\infty$ convention is $\max(w\cdot |x|)$, not the limit of the finite-$p$ convention
for nonuniform weights. Potential uniqueness needs a gauge on each component.
Normalized dual formulas require nonzero residual; at zero, zero is a dual
maximizer and uniqueness is not asserted.

Claim Ledger — 003_l1_obstruction_framework: Finite ℓ¹ Coboundary Obstructions
---

**Paper Key:** `001_finite_obstruction_calculus/003_l1_obstruction_framework`  
**Retired Paper Identity:** `FOC-004`  <!-- Retired 2026-08-18. Stamped from lean_identity_map.yaml, which describes the pre-rename tree, and restamped to the Paper Key above. Kept so an old citation to this code meets an explanation rather than nothing. -->

**Paper:** `l1_obstruction_framework.md` (v5.5.3, 2026-10-15)
**Verdict shape:** synthesis/framework monograph. Deductive text proofs (Theorems 2.1, 4.2, 5.1, Proposition E.7e) are recognized as proved in finite mathematics, explicitly distinguished from Lean mechanization scope (`general_finite_certificate_optimality`). Candidate 3-step iterator is refuted and withdrawn. False mathematical statements (residual divergence, overlapping cycle holonomy sums, Schatten-1 polyhedrality) corrected with exact counterexamples and replacement theorems. Version 5.5.3.

**Degree — all claims:** obstruction regime $k=1$, truncated. $C^2$ and $d_1$ are not constructed; $d_1\circ d_0=0$ is **assumed** via declared presheaf functoriality (flatness), and it is trivial under the §4 graph truncation $C^2:=0$. **Not proved in this paper.** Every "cohomology class" below denotes the quotient $Q^1=C^1/\operatorname{im}(d_0)$.

---

1. Claim-by-claim typing

---

| # | Claim (location) | Type | Hypotheses | Proof / price location | Mechanization | Import / oracle | Remaining obligation |
|---|---|---|---|---|---|---|---|
| C1 | Theorem 2.1 (functorial aggregation monotonicity) | [PROVED_FINITE_MATH] | $A \circ d_0^P = d_0^Q \circ \pi_*$ and $\|A\|_{\ell^1 \to \ell^1} \le 1$ | §2.2, cochain-level contraction proof; order-preserving poset surjection caveats stated | unmechanized in Lean 4 | none | Valid deductive proof in text; global cochain contraction hypothesis $\|A\|_{\ell^1 \to \ell^1} \le 1$ is load-bearing |
| C2 | Theorem 3.1 (operator-valued Schatten-p classification) | [CLASSICAL_SKETCH] | (P1) edge-additivity, (P2) faithfulness, (P3) **maximal bounded-linear** functoriality, (P4) automorphism invariance | §3.5 sketch; norming-functional (polar decomposition) + rank-one map are correct | ENC-0269 / ENC-0550 `NOT-STARTED` | **IMPORTED:** Hilbert space, Schatten-$p$ operators, trace norm, partial trace, CPTP (§3.1) | **PL-007-2** — full write-out. Remark 3.1 blocks the "CPTP forces trace norm" misreading. Ordinary automorphism invariance forces weights constant on edge orbits; uniform weights require edge transitivity or cross-edge calibration. Note that unrestricted matrix Schatten-1 is nonpolyhedral |
| C2a | Theorem 3.0 (non-commutative Hölder duality) | [CLASSICAL_RESULT] | finite-dimensional Hilbert space, Schatten-$p$ and Schatten-$q$ conjugate spaces ($1/p + 1/q = 1$) | §3.2, exact polar witness alignment $\mathrm{Tr}(X^* Y) = \|Y\|_{S_p}$ with $\|X\|_{S_q} = 1$ | unmechanized in Lean 4; float replay is diagnostic | non-commutative integration/trace theory imported | Repaired $p = \infty$ dual witness using rank-one singular vector projection $X = U |v\rangle\langle v|$ with $\|X\|_{S_1} = 1$ |
| C2b | Proposition 3.1 (Kadison unitary invariance) | [CLASSICAL_RESULT] | $p \in [1, \infty]$, complete positivity for $p \neq 2$, cone-positivity forces $V=U^*$ | §3.3 | unmechanized in Lean 4 | Kadison/Sourour isometry classification imported | Positivity of the state cone forces $V=U^*$ (Jordan *-isomorphism) |
| C3 | Definition 4.1 (3-step primal–dual candidate update) | [WITHDRAWN / REFUTED] | candidate discrete three-step update | §4.2 | ENC-0270 `NOT-STARTED` | Chambolle–Pock [14] imported as structural relative | Refuted by single-edge counterexample ($\omega=1, s=0, \phi=0, \sigma=1, \tau=1/2$); admits non-optimal fixed point and can exit dual unit ball. Retained only as historical context; not a valid solver |
| C4 | Theorem 4.2 (finite certificate inequality) | [PROVED] | equal lengths; coboundary image length; $\forall p'\,\langle z, Dp'\rangle=0$; capacity $\|z_e\|\le w_e$; gap $\|r\|_{1,w}=\langle z,\omega\rangle$ | Lean `general_finite_certificate_optimality`; Python `LocalPrimalDualIterator.certificate_dominates` | Lean 4 (no sorry) and exact rational Python | none for the integer-list inequality. Fenchel--Rockafellar and the Banach reading are not this theorem | Deduced in text via LP weak duality; integer-list inequality mechanized in Lean 4; feasible residual witness supplied by Corollary 4.2 |
| C5 | Former Conjecture 4.3 (3-step monotone descent) | [REFUTED / WITHDRAWN] | 3-step candidate update | §4.2 | **ENC-0529 `[REFUTED]`** | none | Refuted by single-edge counterexample; candidate update does not decrease defect and stalls at non-optimal points. Retained only as historical refutation |
| C6 | Proposition 4.6 / Former Heuristics 4.2, 4.6 (cycle additivity criterion & bounds) | [PROVED_FINITE_MATH] | finite scalar complex, weights $\mathbf{w}$, circulations $Z_{\mathbf{w}}$ | §4.4 (Proposition 4.6 additivity criterion) and §4.10 (capacity-normalized bound) | unmechanized in Lean 4 | none | Replaced former false divergence heuristics with exact LP duality theorem: $\Phi(\omega_1+\omega_2)=\Phi(\omega_1)+\Phi(\omega_2)$ iff they share a common dual maximizer in $Z_{\mathbf{w}}$. Overlapping cycle lower bound corrected to capacity-normalized bound $|\langle z,\omega\rangle|/M(z)$ with 2-triangle counterexample |
| C7 | Proposition 4.5 (certified cycle-supported minimizers) | [PROVED_FINITE_MATH] | $r \in C^1, \phi \in \partial\|r\|_{1,\mathbf{w}}, d_0^*\phi=0$ | §4.3 proof via Theorem 4.2 weak duality | unmechanized in Lean 4 | none | Scoped to static divergence-free cycle configurations; dynamic update is withdrawn. Counterexample $r=(2,1,1), \phi=(1,1,1)$ confirms optimal residual need not have zero divergence |
| C8 | Proposition 4.7 (one-step residual update identity) | [WITHDRAWN] | immediate from Definition 4.1 step (3) | §4.5 | ENC-0280 `NOT-STARTED` | none | Explicitly "not a proof of stable signal behavior or physical propagation" |
| C9 | Corollary 4.2 (finite-speed propagation) | [WITHDRAWN] | locality of the declared update | §4.5 | ENC-0281 `NOT-STARTED` | none | Explicitly does **not** imply Lorentz invariance, invariant speed, or frame equivalence. §6.5 open problem 2 |
| C10 | Fact 4.12 (dual feasibility constraints) | [DEFINITION / RESTATEMENT] | — | §4.9; restates Theorem 4.2's feasible set | N/A | none | **Demoted 2026-06-09** from "Theorem 4.12 (Layer B)" |
| C11 | Schemas 4.8, 4.11, 4.12(continuum), 4.13 (TV limit, interfaces, flux, connection–curvature–holonomy) | [INTERPRETIVE / Layer C formal schemas] | isotropic refinement; bounded degree; BV regularity | §4.6–§4.9, tagged in place | `NOT-STARTED` | **IMPORTED, Layer C:** $\Omega\subset\mathbb{R}^d$, BV, Radon measures, TV flow, $\Gamma$-convergence, mean-curvature motion (Chambolle 2004; van Gennip–Bertozzi 2012; Evans–Spruck; Chen–Giga–Goto) — none reproved | No $\Gamma$-limit is proved. Operator-valued TV theory open. §4.10 label drift fixed 2026-07-17 ("Theorem 4.8" → "Schema 4.8"). §4.8 ontology fixed: interfaces are **representative supports / matter-candidates**, not carriers of physical structure |
| C12 | Theorem 4.10 + Lemma 4.9 (unitary gauge structure) | [CLASSICAL_RESULT] | Kadison [9] / Sourour [10] + CP excludes transpose + positivity forces $V=U^*$ | §4.7 | ENC-0283 / ENC-0284 `NOT-STARTED` | **IMPORTED:** Kadison/Sourour isometry classification, not reproved. Complete positivity is an additional **physical** axiom, not forced by $\ell^1$ | Conclusion scoped to "conditional $U(n)/PU(n)$-type frame symmetry" — a *relabelling* symmetry. Does not derive a physical gauge field, Yang–Mills, or $SU(3)\times SU(2)\times U(1)$ |
| C13 | Theorem 4.14 (variational principle) + Prop 4.15 (subgradient conservation) | [PROVED_FINITE_MATH] | fixed observed $\omega$; KKT form; one-parameter symmetry family | §4.10–§4.11 | ENC-0289 / ENC-0291 `NOT-STARTED` | none (the *finite* statements); the "Continuum Version" is Layer C | Regularity caveat present: at $\delta_e=0$ the subdifferential is multi-valued and the conserved dual is **not unique**. These are finite/discrete results and **cannot** be spent to promote C11 |
| C14 | Theorem 5.1 (distinguishability bound across Schatten-$p$) | [PROVED_FINITE_MATH] | Schatten-$p$ operators in a common finite-dim space; composed restriction contractive; normalized metric $T_p \le \frac{1}{2} I_p(s)$ | §5.1 + worked replay (two-edge qubit path across $p \in \{1, 2, \infty\}$, taut equality case) | unmechanized in Lean 4 | **IMPORTED:** Hilbert space, density operators, trace distance. **Consumes chain composition load-bearingly** — this is where the flatness/functoriality assumption is spent | Telescoping and triangle inequality proof established in text. Directed path costs note added (quasi-pseudometric) |
| C15 | §3.6 coboundary defect vs. bipartite correlation | [NEGATIVE BOUNDARY] | local restriction morphisms | §3.6 | N/A | trace norm imported | **Was a false claim:** identification of coboundary defect $\delta_e(\Pi(\rho))$ with bipartite product defect $\|\rho - \rho_A \otimes \rho_B\|_1$. Refuted by Bell state counterexample $|\Phi^+\rangle = (|00\rangle+|11\rangle)/\sqrt{2}$: single-qubit marginals are $\rho_A = \rho_B = I/2$ so edge difference vanishes ($\delta_e = 0$), while product defect is $3/2$. $\delta_e$ measures local marginal incompatibility under restriction, not bipartite correlation |
| C16 | §5.2 fermion-sign bridge, §5.3 POVM/Born links | [CONJECTURE — quarantined] | — | §5.2–§5.3, fenced | `NOT-STARTED` | **`OracleNeeded`:** Born rule, Born uniqueness, $L^2_{\mathrm{RMS}}$ phase envelope, POVM equivalence | §5.3 notes that compatibility does not derive quantum mechanics |
| C17 | §6.5 homogenization / invariant speed / metric–dynamics coupling | [OPEN] | — | §6.5 | `NOT-STARTED` | continuum imports | Stated as open problems with the falsification test named. Gates the entire geometric extension |
| C18 | $d_1\circ d_0=0$ (§2.1, added 2026-07-17) | **[DECLARED AXIOM]** — assumed via presheaf functoriality; **not proved here** | flatness / chain-composability of the restriction system | §2.1 declared-degree block | Not proved in this package. Nilpotency is not automatic over a poset | none | Trivial under the §4 graph truncation $C^2:=0$. This package does not construct $C^2$ or $d_1$ |
| C19 | Proposition E.7e (sharp full-distribution spectral-gap comparison) | [PROVED_FINITE_MATH] | finite scalar carrier, $n\ge2$, $v_i\ge0$, supplied $\alpha>0$ with caller premise $L_0\succeq\alpha(I-P)$ | §5.4, complete weighted-Cauchy and equality-vector proof | unmechanized in Lean 4; partial raw-LF mechanization unintegrated | finite-dimensional spectral minimum and graph/Fiedler premise remain imported/composed | **OBL-1a-opt discharged for the comparison characterization.** Rigorous secular root and Loewner bound transfer in text. |

1. Definition-as-theorem audit

---

ONE CATCH (fixed 2026-06-09): former "Theorem 4.12 (Dual Field as Conserved Flux, Layer B)" asserted only the dual feasibility constraints — the definition of the feasible set from Theorem 4.2 — and is now Fact 4.12 [DEFINITION / RESTATEMENT]. No other instance found: Prop 4.7 is a genuine (if one-line) identity and says so.

Re-audited 2026-07-17: no further definition-as-theorem. **One label-drift inflation found and fixed** (§4.10 cited Layer-C "Schema 4.8" as "Theorem 4.8" — the 2026-06-09 pass fixed this in §6.2 and missed §4.10). **One ontology inflation found and fixed** (§4.8 spent Layer-B Theorems 4.14/4.15 to promote a Layer-C schema into "carriers of physical structure"). **One unscoped-quantifier inflation found and fixed** (§4.3 "no local iteration can reduce them" → scoped to the declared iterator).

1. Open obligations (global ledger cross-reference)

---

* **PL-007-1** — Convergence of the 3-step primal–dual iterator (Conjecture 4.3; backlog 899). **REFUTED AND CLOSED AS WITHDRAWN (2026-10-08).** The three-step map has non-optimal fixed points (counterexample on a single edge where $s=0, \phi=0$ with $\omega=1$ yields $\phi^1=0, s^1=0$ despite $d_0 s = \omega$ having zero residual) and step-size-dependent exits from the dual unit ball. The iterator is refuted as a solver and withdrawn; convergence is not an open gap but a refuted claim. Shipped code and retained theory verify independently supplied finite KKT certificates via linear programming duality.
* **PL-007-2** — Theorem 3.1 is presented as a classical classification sketch; a full formal write-out remains future work.
* **$C^2$/$d_1$ admission** — the §2.1 assumption. Not proved in this package.
* **`DetectorAdequacy`** — required for any certified global exactness inference from local watcher scores (§2.2).

1. E.7e comparison-floor reconciliation (2026-07-23)

---

Proposition E.7e and ENC-1216 close OBL-1a-opt only in its exact
full-distribution **comparison** sense. The root certificate binds four raw-LF
Lean files: the base source, assembly source, and both axiom audits. The
assembly establishes bracketed existence/uniqueness, the zero-load gate, a nonzero
equality vector, the exact comparison floor, and generic Loewner transfer.
The remaining concrete graph/Fiedler composition and final spectral
minimization keep the status `MECHANIZED-PARTIAL`. Finite diagnostic sweeps and
Rust certificates are computational evidence.

<!-- claim-id-body-only-sync:begin -->

Body-only ID sync (packaging)
---

| ID | Claim | Type | Status |
|---|---|---|---|
| OBL-1 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| OBL-1a-m2 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| OBL-1a-opt | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| OBL-2 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| OBL-5 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| PKT-20260722-RES-EPOCH19 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| SHA-256 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |

<!-- claim-id-body-only-sync:end -->

## Executable Pytest Test Suite References

The computational claims and exact rational solvers are verified by the unit test suite under code/tests/:

* test_004_l1_obstruction_framework.py::test_paper_evaluator_passes
* test_004_l1_obstruction_framework.py::test_l2_laplacian_cycle_c4
* test_004_l1_obstruction_framework.py::test_linf_chebyshev_cycle_c4
* test_004_l1_obstruction_framework.py::test_package_exports
