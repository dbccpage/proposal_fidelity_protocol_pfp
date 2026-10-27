# Path-Additive Coboundary Defects for Reasoning Trace Validation

**Monograph Series:** Monograph 033 (Finite Obstruction Calculus Program)  
**Author:** Jeremy H. Carroll  
**Date:** 2026-10-07  
**Version:** 2.0.0  
**License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)  
**Status:** RELEASED  
**DOI:** 10.5281/zenodo.20214112  
**Authority Notice:** *This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.*

---

**Author:** Jeremy H. Carroll  
**Date:** June 2026  
**Version:** v1.0.1 Pre-Print  

Abstract

**Main result (informal).** A reasoning trace (LLM output, tool log, proof attempt) is read only after a deterministic extractor maps it to a finite carrier $(P,\omega_1,\mathcal A,\mathcal C,\tau)$. Until PL-014-2 is discharged, an `Exact` verdict is a statement about $\pi$'s image and nothing more. An `Exact` verdict diagnoses the declared extractor. Certificate Soundness and Witness Soundness stay `[OPEN]`. The Python gap check is not a proof of certificate soundness.

This paper provides a formal finite obstruction protocol for the **auditability and validation of reasoning traces**. We establish that textual reasoning outputs from large language models (LLMs) or automated toolchains cannot be scored or validated directly via language-level heuristics or embedding similarity. Instead, we define a **realization boundary** where raw text is mapped to a finite structural carrier $(P, \omega_1, \mathcal{A}, \mathcal{C}, \tau)$ before validation occurs. The typed refusal taxonomy and the certificate format are a specification. Certificate Soundness stays `[OPEN]`. The Python gap check is not a proof of certificate soundness.

**Why a researcher should care.** Scalar reward models, embedding similarity, and chain-of-thought "scores" are vulnerable to shortcut certification: a fluent-but-wrong trace can score well. The verifier does not judge language directly. Until PL-014-2 is discharged, an `Exact` verdict is a statement about $\pi$'s image and nothing more. An `Exact` verdict diagnoses the declared extractor. Certificate Soundness and Witness Soundness stay `[OPEN]`. The Python gap check is not a proof of certificate soundness.

**The Core Doctrine:**
$$
\boxed{
\text{The verifier does not judge language directly. It judges declared finite structure.}
}
$$

**Authority:** none. This paper may diagnose, price, route, or construct structure inside a declared obstruction regime. It does not mint authority. Any authority-bearing use requires a separate descent verification packet, terminalizer, evidence ceiling, replay witness, and `IsAuth` guard.

**Reading "validation" (binding).** Throughout this paper, *validated* means **diagnosed under a declared packet** — never *authorized*, *approved*, or *true*. A `Valid` or `Exact` verdict is a carrier-relative diagnostic emission. Authority is not produced by successful diagnostics, by a discrete trace, by finite replay alone, or by residual classification; it requires a valid descent packet and terminal seal, which this paper does not supply. Exact repair does not imply semantic truth.

1. Scope: Interfacing with Modern AI Verification

Earlier papers in this series establish the abstract algebra of obstruction (Paper 012) and the governance of evaluators (Paper 011). This paper operationalizes those theories to solve the concrete problem of **trace validation**. It specifies one formal interface between raw text and replayable, carrier-relative certification.

### Operational Context

Traditional AI evaluation relies on scalar reward models, embedding similarity, or "chain-of-thought" scoring—all of which are vulnerable to **shortcut certification** and **reward-model collapse**. This paper replaces these heuristic judgments with:

* **Declared Carriers:** Explicitly defined claim/citation/tool graphs.
* **Replayable Certification:** Proof-carrying evidence that a reasoning transition is exact within the carrier.
* **Typed Refusals:** Informative failure modes (e.g., `CarrierFailure`, `BudgetUnknown`) that provide **typed diagnostic semantics** instead of binary outcomes. A typed refusal is a diagnostic emission; it carries no authority (see the Authority firewall below).

This paper does not define thinking, intelligence, or semantic understanding. It states finite structural conditions that are **necessary** — never sufficient — for a trace to be admitted as carrier-relative evidence *about a declared carrier*. It does not establish that a reasoning transition occurred (§11), and it does not make the trace true.

2. Realization Boundary

A submitted output $y\in\mathsf{Text}$ is source material. It becomes auditable only after a deterministic or versioned extractor $\pi$ emits a finite validation object

$$
V_\pi(y)=(P,C^0,C^1,C^2,d_0,d_1,\omega_1,\mathcal A,\mathcal C,\tau_\pi).
$$
The components are:

| component | finite meaning |
|---|---|
| $P$ | carrier graph of claims, citations, tool states, or proof obligations |
| $C^0$ | admissible repairs, expansions, alignments, or bridge steps |
| $C^1$ | observable distinction coordinates |
| $C^2$ | closure and dependency-obstruction coordinates |
| $d_0$ | repair-to-distinction map |
| $d_1$ | distinction-to-closure map |
| $\omega_1$ | submitted edge defect or support-demand cochain |
| $\mathcal A$ | admissible repair/operator set |
| $\mathcal C$ | admissible context family |
| $\tau_\pi$ | replayable extraction log |

No extraction means no certificate:

$$
\pi(y)=\bot\quad\Rightarrow\quad
\mathsf{Status}(y)=\mathsf{NeedsRealizationFunctor}.
$$

### Declared regime and inherited standing assumptions

This paper operates in $\mathsf{ObstructionRegime}(k=1)$: the submitted defect is $\omega_1\in C^1$, the norm is $\ell^1$, and the quotient of interest is $Q^1$. It **imports** the finite obstruction calculus of the primitive-axiomatics paper rather than reconstructing it, and therefore inherits that paper's standing assumptions A0–A9. They are **admitted here as obligations on the extractor $\pi$**, not proved:

| inherited assumption | what it obliges $\pi$ to emit | if unmet |
|---|---|---|
| finite carrier; declared ring | finite $P$, declared scalar specialization | `CarrierFailure` |
| 2-truncated carrier; $d_1\circ d_0=0$ | a genuine cochain complex $C^0\to C^1\to C^2$ | `CarrierFailure` |
| separated $Q^1$ | $\Phi$ a norm, rather than a seminorm, on $Q^1$ | `CarrierFailure` |
| declared gauge $J$; fixed $\ell^1$ on $C^2$ | declared repair gauge and closure norm | `CarrierFailure` |
| attainment only when proved | no assertion that $\inf$ is attained absent proof | see §4 |
| observer $=$ repair-compatible quotient | see §7 | see §7 |
| **no authority** | verdicts are diagnostic only | see the Authority firewall |

**$d_1\circ d_0=0$ is load-bearing and is not derived here.** The status `CohomologicalObstruction` (§8) reads $\Gamma=0,\ \Phi>0$ as a nonzero class in $H^1=Z^1/B^1$, which requires $B^1\subseteq Z^1=\ker d_1$. An extractor that emits $d_1,d_0$ with $d_1 d_0\ne 0$ produces a $Q^1=C^1/B^1$ that is a quotient but **not** a cohomology, and the status name is then unearned.

> **OBSTRUCTION.** The following cannot be derived from what is available at this degree: that an extractor $\pi$ over $\mathsf{Text}$ emits a complex satisfying $d_1\circ d_0=0$. What would have to be admitted: a per-extractor complex certificate discharging $d_1 d_0=0$ for the declared carrier. What is lost if it is admitted: the burden moves onto $\pi$, whose adequacy is itself unresolved (§7 detector adequacy) — declaring the complex condition does not make $\pi$ adequate. Tracked as an open obligation.

### Genesis-Bias Fence — No Prior Reasoning Process

This paper does not begin with a prior thinker, a prior reasoning process, a prior meaning, an author's intent, a semantic domain, or a truth of the matter that the trace is a trace *of*. It begins with an **admitted cut**: a submitted artifact $y$ and a declared extraction $\pi$ that presents finite non-sameness ($\omega_1\ne 0$) while retaining its declared pole-tokens (the carrier $P$ and the log $\tau_\pi$).

The word "trace" is retained for continuity with the literature and is **not** a claim of antecedence: nothing in this protocol requires that $y$ was produced by reasoning, or by anything at all. $\omega_1$ is a submitted defect cochain on a declared carrier — it is not a record of a prior process, and no step below reads backwards through $y$ to a generating event (§11).

Stronger readings priced: "the trace reveals what the model was doing" imports a prior cognitive host; "the extractor recovers the reasoning" imports a prior semantic domain plus a recovery functor. Neither is available at this degree; both are refused (§11).

> **GENESIS-BIAS AUDIT.** Does this section explain trace validation by presupposing a prior container, substrate, state-space, law, observer, temporal order, possibility domain, sample space, physical system, or authority source? If so, declare and price that antecedent, replace it with packet-local data, or stop with an OBSTRUCTION.

Applying the audit to $\mathsf{Text}$ itself: $\mathsf{Text}$ is **not** claimed as a prior domain that contains all possible traces. It is a declared admission channel — the type of artifacts this protocol accepts as submissions. No completeness, measure, or enumeration over $\mathsf{Text}$ is claimed or used.

3. Trace Carrier Types

The protocol permits multiple finite carriers, provided the carrier is declared before validation:

| carrier | vertices | edges | typical obstruction |
|---|---|---|---|
| claim graph | atomic claims | entails, contradicts, supports | unsupported or contradictory claim |
| citation graph | cited propositions | citation-support relation | citation does not support claim |
| tool trace graph | tool states | call, parse, transform, commit | output mismatch or hidden mutation |
| proof-obligation graph | obligations | discharge, depends-on | obligation skipped |
| reasoning trace graph | step states | inference, context carry | non-replayable transition |

The same text may realize into several carriers. A validation result is always carrier-relative:

$$
\mathsf{Valid}_{\pi,P,\mathcal A,\mathcal C}(y),
$$
not unqualified validity.

4. Submitted Defect and Repairable Mass

Given $\omega_1\in C^1$, the repairable component is the part lying in

$$
B^1=\operatorname{im}(d_0).
$$
The irreducible quotient obstruction is

$$
[\omega_1]\in Q^1=C^1/B^1.
$$
The submitted $\ell^1$ defect is

$$
I(\omega_1)=\|\omega_1\|_1.
$$
The exact repair problem is

$$
\inf_{\alpha\in C^0}\|\omega_1-d_0\alpha\|_1.
$$
Define

$$
\Phi(\omega_1)=\inf_{\alpha\in C^0}\|\omega_1-d_0\alpha\|_1.
$$

**Attainment.** Following the inherited assumption *attainment only when proved* (§2), $\Phi$ is defined as an infimum and is **not** asserted to be attained in general. Attainment must be proved per instance; where it holds (e.g. the finite linear program of §5, whose optimum is attained), $\inf$ may be written $\min$.

**ZeroRel (local sameness).** `Exact` tests $\Phi=0$, but any solver replay carries a declared `NumericTolerance` (§10). The zero test is therefore **relative to a declared ZeroRel**: a verdict of $\Phi=0$ is a verdict of $\Phi\le\varepsilon$ for the tolerance $\varepsilon$ recorded in the certificate, under the declared scalar specialization. Exact-zero certification requires either $\varepsilon=0$ over an exact declared ring, or a replayable repair witness $\alpha$ with $d_0\alpha=\omega_1$ checked exactly. A floating-point $\Phi\le\varepsilon$ is `CandidateRepair`, not `Exact` (§9, step 4).

Then:

| case | status |
|---|---|
| $\Phi=0$ and closure holds | exact or certified bridge |
| $\Phi>0$ and closure holds | cohomological obstruction |
| $d_1\omega_1\ne0$ | closure failure |
| extractor lacks coordinates | carrier failure |
| repair exists only outside $\mathcal A$ | admissibility failure |
| search budget exhausted | budget unknown |

Skipped steps are not automatically invalid. They are valid only if a replayable $\alpha$ certifies that the skipped bridge lies in $B^1$.

5. Dual Witnesses

A dual witness is a finite cochain $\varphi\in (C^1)^*$ satisfying

$$
d_0^*\varphi=0,\qquad \|\varphi\|_\infty\le 1.
$$
Any feasible dual witness gives a certified lower certificate for $\Phi$ in the sense that its value cannot exceed the primal optimum:
$$
\langle\varphi,\omega_1\rangle \le \Phi(\omega_1).
$$
When an optimal feasible witness attains equality, it certifies the obstruction value.

**[STANDARD — imported; not proved here]** The bound and the saturation case are linear-programming duality over the declared scalar specialization, imported from the corpus quotient-norm layer (Paper 006). They are **not** discrete trace operations and are not re-derived at this degree; strong duality (existence of a saturating $\varphi$) holds under the finite-dimensional LP hypotheses declared there, not by fiat here.

In a trace audit, a witness localizes irreducible defect:

1. an unsupported edge,
2. a contradiction cycle,
3. a citation-support mismatch,
4. a tool-output mismatch,
5. a dependency path that cannot be replayed under the declared carrier.

The verifier should emit the witness, not a psychological label.

### Worked Example — Irreducible Support Defect on a Claim Cycle

Realize a three-claim trace as the directed triangle $A\to B\to C\to A$ (claim $A$ entails $B$, $B$ entails $C$, $C$ entails $A$), with support-defect cochain $\omega_1=(0,0,1)$: the edges $A\!\to\!B$ and $B\!\to\!C$ replay exactly, but $C\!\to\!A$ carries an unsupported unit defect. No vertex-level repair (gauge shift $d_0\alpha$) can remove it, because the cycle sum is gauge-invariant:

$$
\Phi(\omega_1)=\min_\alpha\|\omega_1-d_0\alpha\|_1=1.
$$

The optimal dual witness $\varphi=(1,1,1)$ (with $d_0^*\varphi=0$, $\|\varphi\|_\infty\le1$) saturates $\langle\varphi,\omega_1\rangle=1=\Phi$ and localizes the irreducible contradiction to the cycle. The verifier therefore emits status `CohomologicalObstruction` ($\Gamma=0,\ \Phi>0$) with witness $\varphi$ — not a rhetorical label. (If instead the trace were the path $A\to B\to C$ carrying the same unit defect, $\Phi=0$: the gap is a `RepairableGap`, discharged by a replayable $\alpha$.)

```python
import numpy as np
from scipy.optimize import linprog
def phi(B, w):
    E, V = B.shape
    A = np.vstack([np.hstack([B, -np.eye(E)]), np.hstack([-B, -np.eye(E)])])
    return linprog(np.r_[np.zeros(V), np.ones(E)], A_ub=A, b_ub=np.r_[w, -w],
                   bounds=[(None, None)]*V + [(0, None)]*E, method="highs").fun
B = np.array([[-1,1,0],[0,-1,1],[1,0,-1]], float)            # A->B->C->A (cycle)
print(phi(B, np.array([0., 0, 1])))                          # 1.0  (obstruction)
print(phi(np.array([[-1,1,0],[0,-1,1]], float), np.array([0., 1])))  # 0.0 (path)
```

Expected output: `1.0`, `0.0`.

6. Closure

Exactness is insufficient if the trace opens a higher obstruction. Closure is measured by

$$
\Gamma(\omega_1)=\|d_1\omega_1\|_1.
$$
A local $\Phi$-decrease is not accepted when it worsens closure:

$$
\Phi(S')<\Phi(S)
\quad\text{but}\quad
\Gamma(S')>\Gamma(S)
\quad\Rightarrow\quad
\mathsf{NoPromotion}.
$$
The validator ranks proposed repairs by the declared evaluator law over
$(\Phi,\Gamma,\Xi)$, with any additional governance fields defined explicitly by the evaluator policy, not by scalar loss or rhetorical plausibility. Here $\Xi$ is the representative-distortion (dual-witness trace) functional defined in Paper 009 (elaborated in Paper 013).

7. Observer Passivity: The Anti-Shortcut Principle

A common failure mode in modern AI verification is the use of **compressed evaluators**—models that map a complex trace to a smaller diagnostic view (e.g., a "score" or a "summary") before certification.

**Definition (Detector).** A *detector* is any mapping that reduces the coordinates available for certification. Two kinds appear in this protocol: the **extractor** $\pi:\mathsf{Text}\to V_\pi(y)$ of §2, and a **compressed evaluator** $\mathcal{O}$ that restricts the defect cochain, $\mathcal{O} : C^1 \to C^1_{\mathcal{O}}$. Both are detectors. Neither is exempt from this section.

**Imported inequality (Observer Passivity / No-Creation).** **[STANDARD — imported; `[PROVEN, CONDITIONAL]` at its source; not re-proved here]** The primitive-axiomatics paper §1.7 derives, as **Lemma O1** (encyclopedia ENC-0207, `PROVED-PROSE`, `lean_status: MECHANIZED-PARTIAL`):

$$
\Phi_{\mathcal{O}}(\mathcal{O}(q)) \le \Phi(q),
$$

under **all** of the following hypotheses, which are load-bearing and are stated here in full:

1. $\mathcal O$ is a finite, deterministic, **repair-compatible quotient map $\mathcal O: Q^1 \to Q^1_{\mathcal O}$** — a quotient of the obstruction quotient $Q^1$, *not* an arbitrary map on $C^1$;
2. the target carries the **induced quotient norm** $\Phi_{\mathcal O}(y)=\inf_{\mathcal O(r)=y}\Phi(r)$;
3. finite dimensionality.

The proof is one line about induced infimum norms: $q$ lies in its own fiber, so the fiber infimum cannot exceed $\Phi(q)$.

> **SCOPE FENCE (verbatim from ENC-0207).** The imported lemma "is not an unconditional theorem about arbitrary lossy maps, arbitrary observers, or authority-bearing terminalization."

**Applicability gap — declared, not closed.** The compressed evaluators this section is aimed at (scalar reward models, embedding scorers, summarizers) generally satisfy **none** of (1)–(3): they act on text or on $C^1$ rather than on $Q^1$, they are not repair-compatible quotients, and they carry **their own learned scalar** rather than the induced infimum norm. Hypothesis (2) is exactly what fails for a reward model, and it is the hypothesis that does the work. Therefore:

> **OBSTRUCTION.** The following cannot be derived from what is available at this degree: the passivity inequality for arbitrary compressed evaluators, including the reward models and embedding scorers named below. What would have to be admitted: for each such evaluator, a factorization through a repair-compatible quotient of $Q^1$ together with the induced infimum norm on its target. What is lost if it is admitted: the evaluator would then have to expose a repair-compatible quotient structure, which learned scalar heads do not exhibit. Pending that, the inequality is asserted **only** for detectors satisfying (1)–(3).

**Anti-shortcut principle — re-derived without passivity.** The paper's operative conclusion does **not** depend on the imported inequality, and is not claimed to follow from it. It follows from the certificate requirement itself (§8–§10): a verdict is certificate-grade only if it exhibits a replayable repair witness $\alpha$ or a certified dual witness $\varphi$ **in the declared source carrier**. A scalar, boolean, or embedding judgment exhibits neither. Hence:

**Consequence [POLICY RULE, not a theorem].** Scalar loss, reward models, and embedding agreement guide *proposal search* but may not be substituted for the finite verifier — because they emit no replayable source-carrier witness, not because they have been shown to be passive. Any certification that bypasses the realization boundary is rejected as a "hidden observer erasure."

### Detector adequacy

**Detector adequacy warning.** A replayable detector/profile is not automatically adequate for a claim. A collapsing detector can make every profile exact. Any authority-bearing layered authority framework use requires a `DetectorAdequacy` certificate naming the protected distinctions, adversarial cases, and known blind spots for the declared claim scope.

**This applies first to $\pi$, and $\pi$ has no such certificate here.** §2 requires only that $\pi$ be deterministic (or versioned) and emit a replayable log $\tau_\pi$. **Determinism and replayability are not adequacy.** The failure is exhibited, not hypothetical:

> **Collapsing-extractor counterexample.** Let $\pi_0$ emit a carrier with $C^1=0$ (or, less crudely, any $\pi$ that omits the coordinate carrying the defect). Then $\omega_1=0$, hence $\Phi=0$ and $\Gamma=0$, and $\tau_{\pi_0}$ replays without error. By the §8 table, **every submitted trace certifies `Exact`** — including a fluent-but-wrong one, the exact failure this protocol was written to prevent. $\pi_0$ is deterministic, versioned, replayable, and worthless.

A verdict is therefore only as good as the extractor that produced it. **A trace validator that finds no defect may be detecting nothing.** Nothing in §§2–10 rules $\pi_0$ out; the protocol as specified admits it.

Consequently, for any use of this protocol beyond illustration, a `DetectorAdequacy` certificate for $\pi$ must accompany the verdict, declaring at minimum:

| field | content |
|---|---|
| **Protected distinctions** | the finite set of trace-level distinctions $\pi$ is asserted to preserve as distinct coordinates (e.g. supported vs. unsupported citation edge; discharged vs. skipped obligation; declared vs. actual tool output) |
| **Adversarial cases** | a declared finite battery on which $\pi$ must **not** return `Exact` — at minimum: a known-wrong trace, a fluent paraphrase of a wrong trace, a trace with a deleted supporting citation, and a trace with a silently mutated tool output |
| **Known blind spots** | distinctions $\pi$ is known **not** to carry (e.g. defects expressible only outside the declared carrier), each routed to `CarrierFailure` rather than to `Exact` |
| **Non-collapse witness** | evidence that $\pi$ separates at least the protected distinctions: exhibited traces $y\ne y'$ with $\pi(y)\ne\pi(y')$ on each protected coordinate |

**No `DetectorAdequacy` certificate is supplied by this paper for any extractor.** Absent one, an `Exact` verdict is a statement about $\pi$'s image and **nothing else** — it is not a statement about the trace, the reasoning, or the world. This obligation is open (§12, PL-014-2).

8. Typed Statuses

All statuses are relative to the extractor, carrier, admissible repair set, context family, and replay log:
$$
\mathsf{Status}_{\pi,P,\mathcal A,\mathcal C,\tau}(y).
$$
`Exact` means exact under this declared packet, not truth in an unqualified semantic sense.

| status | condition |
|---|---|
| `Exact` | $\Phi=0,\Gamma=0$, certificate replay succeeds |
| `RepairableGap` | missing bridge is supplied by replayable $\alpha$ |
| `OpenObstruction` | $\Gamma>0$ |
| `CohomologicalObstruction` | Γ=0, Φ>0 under the declared repair complex |
| `MissingData` | required evidence edge absent |
| `EvidenceBoundaryFailed` | evidence edge exists but fails support map |
| `ToolTraceMismatch` | declared tool output does not replay |
| `AdmissibilityFailure` | repair requires operator outside $\mathcal A$ |
| `CarrierFailure` | current carrier cannot represent required distinction |
| `BudgetUnknown` | search ended without proof of exactness or obstruction |
| `NeedsRealizationFunctor` | no valid extractor supplied |

These statuses are refusal-compatible. The system must not silently promote an untyped residual.

9. Validation Algorithm

Input:

$$
(y,\pi,\mathcal A,\mathcal C,B)
$$
where $B$ is a finite validation budget.

Procedure:

1. Extract $V_\pi(y)$. If extraction fails, emit `NeedsRealizationFunctor`.
2. Check carrier finiteness and operator declarations. If absent, emit `CarrierFailure`.
3. Compute $\omega_1$, $d_0$, $d_1$, and extraction log $\tau_\pi$.
4. Solve or bounded-search the exact repair problem. A bounded or heuristic search may emit `BudgetUnknown`, `CandidateRepair`, or `CandidateObstruction`. It may not emit `Exact` or `CohomologicalObstruction` unless accompanied by a replayable repair certificate, a certified optimal dual witness, or another declared finite certificate accepted by the evaluator.
5. Compute $\Phi$, $\Gamma$, and available witnesses.
6. Replay any proposed repair $\alpha$.
7. Emit typed status and certificate hash.

Output:

$$
(\mathsf{Status},\Phi,\Gamma,\varphi,\alpha,\tau_\pi,\mathsf{CertHash}).
$$

10. Certificate Format

A trace certificate contains:

```text
ExtractorId
ExtractorVersion
CarrierHash
OperatorSetHash
ContextFamilyHash
SubmittedDefectHash
RepairWitnessHash | DualWitnessHash | ClosureWitnessHash
ReplayLogHash
SolverId
SolverVersion
NumericTolerance
EvaluatorPolicyVersion
StatusRuleVersion
Budget
Status
```

The certificate must be replayable. If the extractor, operator set, or context family changes, the certificate is invalid unless a **licensed lift** preserves the old quotient structure.

**"Licensed lift" — bound, not assumed.** The term appears here and in §12; it is not an escape hatch and it names no licensor of its own. A closed survivor or an active closure failure may **trigger** lift consideration; neither *licenses* a lift. Per the finite obstruction calculus lift rule, a lift is licensed only when all five are exhibited:

1. an obstruction witness;
2. a preservation witness (the old quotient structure is carried, not discarded);
3. a non-destruction check;
4. a declared budget/authority boundary;
5. a terminalizer route.

**This paper supplies none of them and does not construct the lift.** Items 4–5 are finite descent verification/layered authority framework-owned and are outside this paper's degree: a certificate re-validated across a carrier change is an authority-bearing act requiring a descent packet and terminal seal (see the Authority firewall). Absent a licensed lift, a carrier change invalidates the certificate and the correct emission is `NeedsRealizationFunctor` or `CarrierFailure` — **not** silent re-validation under the new carrier.

11. Explicit Rejection of Cognition Claims (Non-Claims)

The structural integrity of this framework relies on the rejection of anthropomorphic equivalences. We explicitly state:

* **Trace Text $\nRightarrow$ Truth:** Textual output is source material, not a direct witness of truth.
* **Reasoning Trace $\nRightarrow$ Reasoning:** Admissibility of a trace implies structural replayability, not the presence of "thought."
* **Stream Projection $\nRightarrow$ Inner Voice:** The "chain-of-thought" is a serial emission, not a window into internal cognition or consciousness.
* **Low Scalar Loss $\nRightarrow$ Valid Trace:** Numerical optimization is not a proxy for structural exactness.
* **Embedding Agreement $\nRightarrow$ Exactness:** Semantic similarity does not satisfy the requirement for a replayable $\ell^1$ witness.

All valid claims are **finite, carrier-relative, and replay-relative**. We reject any interpretation of this work that maps cochain obstruction to cognitive or subjective states.

12. Future Proof Targets / Certification Targets

*(These are stated **targets**, not yet written-out proofs — typed individually below; the short arguments indicated are the intended discharge routes, tracked as PL-014-1.)* Items 14.1–14.4 are not republication claims until PL-014-1 is discharged. They are included to specify intended conformance and proof obligations. Status values below use the corpus claim vocabulary; each is **unproved at this revision**, and the encyclopedia entries ENC-0331 / ENC-0332 / ENC-0333 carry status `NOT-STARTED` accordingly.

**14.1, Certificate Soundness.** **[OPEN — discharge route: mechanical conformance + definitional; the verifier algorithm (§9, steps 6–7) emits `Exact` only after replaying $\alpha$. PL-014-1(i); ENC-0331 NOT-STARTED]**
If the verifier emits `Exact`, then there exists a replayable repair witness $\alpha\in C^0$ such that $d_0\alpha=\omega_1$ and $d_1\omega_1=0$ under the declared carrier. *Scope: this is soundness relative to the declared carrier only. It says nothing about the trace, and nothing about $\pi$'s adequacy (§7).*

**14.2, Witness Soundness.** **[OPEN — discharge route: LP duality; the witness value lower-bounds the infimum over all of $C^0$, hence over $\mathcal A\subseteq C^0$, so a positive certified value excludes any admissible eliminating repair. PL-014-1(ii); ENC-0332 NOT-STARTED]**
If the verifier emits `CohomologicalObstruction` with a certified optimal dual witness $\varphi$, then no admissible same-carrier repair in $\mathcal A$ eliminates the certified residual.

**14.3, Observer Non-Certification.** **[OPEN — discharge route: the certificate requirement of §8–§10, *not* the imported passivity inequality, whose hypotheses arbitrary compressed evaluators do not satisfy (§7). PL-014-1(iii); ENC-0333 NOT-STARTED]**
If a detector $\mathcal O$ collapses obstruction-distinct traces, then a downstream scalar or boolean judgment on $\mathcal O\omega_1$ cannot certify source-level exactness without an additional replayable lift.

**14.4, No Silent Promotion.** **[POLICY RULE — restates the §6 evaluator law; not a theorem and needs no proof]**
A proposed trace repair cannot be promoted if it decreases $\Phi$ while increasing $\Gamma$, violates rollback compatibility, or changes the carrier without a licensed lift in the sense of §10.

**14.5, Extractor Adequacy.** **[OPEN — no discharge route supplied. PL-014-2; not yet registered in the encyclopedia]**
No condition in this paper rules out a collapsing extractor, and §7 exhibits one ($\pi_0$) under which every trace certifies `Exact`. A `DetectorAdequacy` certificate schema for $\pi$ — protected distinctions, adversarial battery, blind spots, non-collapse witness (§7) — together with the statement that an `Exact` verdict under an adequate $\pi$ excludes the declared adversarial cases, is **open**. This is the load-bearing open obligation of the paper: **until it is discharged, an `Exact` verdict is a statement about $\pi$'s image and nothing more.**

13. Final Law

$$
\boxed{
\text{A submitted trace is valid evidence only after finite extraction, exact repair or obstruction witnessing, closure check, and replayable certification.}
}
$$
The verifier does not judge language directly. It judges declared finite structure.

**Read the law as it is written: "only after" is necessary, never sufficient.** Completing extraction, repair-or-witnessing, closure check, and certification does not make a trace valid evidence; it makes it *eligible* for a carrier-relative diagnostic verdict. The verdict is diagnostic, and its worth is bounded above by the adequacy of the extractor that produced the carrier (§7). Nothing in this paper converts the checklist into authority, and nothing converts exact repair into semantic truth.

finite obstruction calculus / layered authority framework Compliance Note

**Role:** finite obstruction calculus-facing protocol/specification paper. It specifies a realization boundary, a typed refusal taxonomy, and a certificate format for reasoning-trace diagnosis. It is *not* a foundations paper and *not* an authority paper.

**Degree:** $\mathsf{ObstructionRegime}(k=1)$. Carrier $C^0\xrightarrow{d_0}C^1\xrightarrow{d_1}C^2$, submitted defect $\omega_1\in C^1$, norm $\ell^1$, quotient $Q^1=C^1/B^1$, closure $\Gamma=\|d_1\omega_1\|_1$. Finite carriers only; declared scalar specialization (the §5 replay uses floating-point LP under a declared `NumericTolerance`).

**Consumes:** a submitted artifact $y\in\mathsf{Text}$; a declared extractor $\pi$; an admissible repair set $\mathcal A$; a context family $\mathcal C$; a finite budget $B$; the evaluator law of Paper 011; $\Xi$ from Paper 009 (elaborated in Paper 013); the standing assumptions A0–A9 of the primitive-axiomatics paper (§2).

**Produces:** a typed, carrier-relative diagnostic status (§8); $\Phi$, $\Gamma$; dual witnesses $\varphi$; repair witnesses $\alpha$; a replayable certificate hash (§10); typed refusals.

**Does not produce:** authority of any kind; semantic truth; a verdict about the trace independent of $\pi$; evidence that reasoning occurred (§11); a licensed lift (§10); an adequacy claim for any detector (§7); an implementation (Appendix).

**Authority status:** **none.** See the Authority firewall. This paper mints no `ContractAuthority`, no `VerifierScopedAuthority`, and emphatically no `SemanticAuthority` — no semantic adapter is declared, so `SemanticAuthority` is not available at this degree. Authority-bearing use would additionally require `SpecificationIdentity`, `DetectorAdequacy`, `ExhaustionWitness`, `EvidenceCeiling`, `ReplayWitness`, `Terminalizer`, and `IsAuth`; of these the paper supplies only a `ReplayWitness` shape (§10). Ownership split respected: authority *types* are finite descent verification-owned; terminalization and non-promotion discipline are layered authority framework-owned; this paper does obstruction routing and diagnosis only.

**Declared imports:** (i) LP duality for the $\Phi$ lower bound and saturation, from the corpus quotient-norm layer, Paper 006 (§5) — `[STANDARD]`, not re-proved; (ii) observer passivity, **Lemma** O1 of the primitive-axiomatics paper §1.7 = ENC-0207, `[PROVEN, CONDITIONAL]` / `PROVED-PROSE`, `lean_status: MECHANIZED-PARTIAL`, valid **only** for repair-compatible quotients of $Q^1$ under the induced infimum norm (§7); (iii) the evaluator law of Paper 011 and $\Xi$ of Paper 009/013 (§6); (iv) standing assumptions A0–A9, including $d_1d_0=0$, admitted as extractor obligations (§2); (v) real-scalar linear programming and floating-point solvers in the §5 replay. None of these are discrete trace operations; none produce authority.

**OracleNeeded / Q-gated items:** (a) **extractor adequacy** — no `DetectorAdequacy` certificate exists for any $\pi$; a collapsing $\pi_0$ makes every trace `Exact` (§7). `OracleNeeded`. (b) **$d_1\circ d_0=0$ for text-derived carriers** — admitted, not derived (§2). `OracleNeeded`. (c) **passivity for arbitrary compressed evaluators** — outside the imported lemma's hypotheses (§7). `OracleNeeded`. (d) **licensed lift** across carrier change — finite descent verification/layered authority framework-owned, not constructed (§10). (e) Any reading of a verdict as a claim about truth, cognition, or the world — `REFUSED` (§11).

**layered authority framework boundary:** verdicts here are diagnostic emissions and routing terminals; they are not authority terminals. `NoPromotion` (§6) is a routing refusal, not a governance seal. No verdict of this paper may be promoted to an authority claim without a separate finite descent verification/layered authority framework descent packet and terminal seal. The `Exact` status is fenced at §8 and must not be read as truth.

**Mechanization status:** **none.** No Lean artifact is cited by this paper. The Rust modules formerly named in the Appendix do not exist (Appendix). The only executable artifact is the §5 `scipy` LP replay. The imported passivity lemma is `MECHANIZED-PARTIAL` **at its source** ([index:index:L000_05_ObserverPassivity.lean](omega_engine/research/_indexes/_master_index.yaml), on $Q^1$) — that mechanization is not this paper's, and does not cover §7's $C^1$-restriction detectors.

**Remaining open obligations:** PL-014-1(i)–(iii) — write out 14.1–14.3 (ENC-0331/0332/0333, all `NOT-STARTED`); **PL-014-2** — `DetectorAdequacy` schema and extractor-adequacy statement (§7, 14.5), *load-bearing and unregistered*; complex-condition certificate for $\pi$ ($d_1d_0=0$, §2); ZeroRel/tolerance discipline pinned to an exact declared ring (§4); implementation of §§2–10 with build receipt (Appendix).

**Import / Oracle boundary.** Any use of Hilbert space, Born uniqueness, phase, continuum, probability semantics, dynamics, physical interpretation, tensor composition, or empirical realization is an imported representation structure unless explicitly constructed at this paper's declared degree. Imported structures are not discrete trace operations and do not produce authority. *This paper uses none of them.* Its import surface is exactly the five items listed above; in particular it makes no probabilistic reading of any quantity — $\Phi$, $\Gamma$, and $\Xi$ are finite $\ell^1$ magnitudes on declared carriers, not likelihoods, confidences, or scores. A later probabilistic adapter may read a normalized defect profile as a distribution; this paper does not supply that adapter.

Appendix: Implementation Registry

**[OPEN — no conforming implementation is present in the repository at this revision]**

**Formalization-status firewall.** Any Lean, Rust, or replay artifact cited here supports only the exact finite statement it mechanizes. It does not automatically discharge PL-finite obstruction calculus, Q, continuum, physical-realization, or layered authority framework authority obligations. A status upgrade requires an explicit theorem-ledger mapping, hypotheses check, build receipt, axiom/sorry audit, and adversary acceptance.

An earlier revision of this appendix stated that modules in the `omega_engine` **implement** the trace validation protocol. That claim is **withdrawn**: it was not true at the time and is not true now. Verified against the repository at this revision:

| module named | intended role | verified status |
|---|---|---|
| `trace_realization.rs` | trace extraction ($\pi$, §2) | **does not exist in the repository** |
| `trace_validator.rs` | validation algorithm (§9) | **does not exist in the repository** |
| `certificate.rs` | certificate format (§10) | filename exists elsewhere (`crates/mub/src/wall/`, `crates/omega_lifts/`); **neither implements the §10 format**, and neither is a trace-validation module |

The protocol of §§2–10 is therefore **specified but unimplemented**. No build receipt, conformance test, or replay artifact backs any claim in this paper, and none is cited. Any future implementation is subject to the firewall above: existence of a module named after a section does not discharge that section, and passing its own tests does not establish extractor adequacy (§7, PL-014-2).

The worked example of §5 is the **only** executable artifact in this paper: a self-contained `scipy` linear program whose declared expected output is `1.0`, `0.0`. It exercises $\Phi$ on a three-edge carrier and nothing else.

Falsifiability

A `CohomologicalObstruction` verdict is falsified by exhibiting an admissible same-carrier repair $\alpha\in\mathcal A$ that eliminates the certified residual (contradicting the dual witness). An `Exact` verdict is falsified by a replay in which $d_0\alpha\ne\omega_1$ or $d_1\omega_1\ne0$ under the declared carrier. Any certification that bypasses the realization boundary yet claims source-level exactness is rejected by construction.

**Not a falsifier (withdrawn).** An earlier revision offered: "the observer-passivity claim is falsified by a compressed observer $\mathcal O$ with $\Phi_{\mathcal O}(\mathcal O\omega_1)>\Phi(\omega_1)$." That test is **vacuous** and is withdrawn. The source corollary (primitive-axiomatics §1.7) reads: if a proposed observer map satisfies $\Phi_{\mathcal O}(\mathcal O(q))>\Phi(q)$ for some $q$, it *is not a passive observer quotient*. Any map exhibiting the inequality is thereby outside the class it would refute, so the test cannot fail. Passivity is definitional for repair-compatible quotients under the induced norm (§7); it is not an empirical claim about detectors and must not be reported as one.

**The load-bearing falsifiable claim is elsewhere.** The protocol's substantive risk is extractor adequacy, and it *is* falsifiable: exhibit two traces $y\ne y'$ that differ on a distinction $\pi$'s `DetectorAdequacy` certificate claims to protect, yet with $\pi(y)=\pi(y')$; or exhibit a trace from the declared adversarial battery on which $\pi$ returns `Exact`. Either falsifies the adequacy of that extractor — and hence every `Exact` verdict it has issued. No extractor in this paper carries such a certificate, so no extractor here has yet been exposed to this test (§7, PL-014-2).

Related Work and Positioning

1. **Chain-of-thought faithfulness / CoT scoring** [4]: this paper replaces scoring with a replayable structural verdict — trace text is source material, not a truth witness.
2. **Process / step-level reward models** [5]: process supervision still produces a scalar; here acceptance is a typed obstruction verdict carrying a dual witness.
3. **Proof-carrying code / certificate checking** [3]: the replayable certificate hash is in the proof-carrying tradition, applied to reasoning traces rather than machine code.
4. **Formal verification & SMT-checked reasoning** [6]: complementary; this layer is carrier-relative and does not certify truth beyond the declared structure.
5. **Companion corpus papers** 006 ($\Phi_1$ / dual witnesses), 011 (evaluator), 015 (domain-graph verifier) [1, 2].

References

1. Carroll, J. H. *General Theory of Finite Obstruction Calculus* 2026. Zenodo. <https://zenodo.org/uploads/20193705>
2. Carroll, J. H. *General Theory of Finite Descent Authority* 2026. Zenodo. <https://zenodo.org/records/20195157>
3. G. C. Necula, "Proof-carrying code," in *POPL '97*, ACM, 1997, 106–119.
4. T. Lanham et al., "Measuring Faithfulness in Chain-of-Thought Reasoning," arXiv:2307.13702, 2023.
5. H. Lightman et al., "Let's Verify Step by Step," arXiv:2305.20050, 2023.
6. L. de Moura and N. Bjørner, "Z3: An efficient SMT solver," in *TACAS 2008*, LNCS 4963, Springer, 2008, 337–340.

Changelog

### v1.0.1 — finite obstruction calculus/layered authority framework compliance pass (2026-07-17)

*Hygiene pass. **No version bump** (hygiene passes never bump the stamp). **No claim upgraded.** Several were retyped into the corpus claim vocabulary or downgraded. Red note: `published/reviews/gtoc_gtla_red_014.md`.*

* **Authority (P0).** §1's typed refusals no longer claim to "provide authority semantics" — they provide typed diagnostic semantics. Added the **Authority firewall** (`Authority: none`) and a binding reading rule: *validated = diagnosed, never authorized or true*. Added the necessity-not-sufficiency reading of the §13 Final Law. The imported calculus carries "no authority" among its standing assumptions; that fence is now inherited explicitly rather than dropped.
* **Detector adequacy (P0, load-bearing).** Added the **detector-adequacy fence** to §7 with a `DetectorAdequacy` schema (protected distinctions / adversarial battery / blind spots / non-collapse witness). §7 previously aimed the anti-shortcut critique at downstream evaluators while exempting its own extractor; the collapsing-extractor counterexample $\pi_0$ ($C^1=0\Rightarrow$ every trace `Exact`, deterministic and deterministically replayable) is now exhibited. Registered as **PL-014-2** and as target 14.5 ``OPEN``.
* **Import repair (P0).** §7's passivity import was restated on the wrong domain with its load-bearing hypothesis missing. Corrected against the source: it is **Lemma** O1 (not "Theorem"), on repair-compatible quotients $\mathcal O:Q^1\to Q^1_{\mathcal O}$ (not arbitrary maps on $C^1$), under the **induced quotient norm** $\Phi_{\mathcal O}(y)=\inf_{\mathcal O(r)=y}\Phi(r)$ (never previously defined here), status `[PROVEN, CONDITIONAL]` / ENC-0207 `PROVED-PROSE`, `MECHANIZED-PARTIAL` at its source. Added ENC-0207's verbatim scope fence and an `OBSTRUCTION` for the applicability gap: reward models and embedding scorers satisfy none of the hypotheses. The anti-shortcut conclusion is **re-derived from the certificate requirement** and retyped `[POLICY RULE]`; it no longer rests on the imported inequality.
* **Implementation claim withdrawn (P0).** The Appendix asserted that `trace_realization.rs`, `trace_validator.rs`, and `certificate.rs` *implement* the protocol. Verified against the repository: the first two **do not exist**; `certificate.rs` exists only under `crates/mub/src/wall/` and `crates/omega_lifts/` and implements neither §10 nor trace validation. The appendix is retyped ``OPEN`` with the **formalization-status firewall**. The protocol is specified but unimplemented.
* **Inherited assumptions (P0).** §2 now declares $\mathsf{ObstructionRegime}(k=1)$ and the inherited standing assumptions A0–A9 as obligations on $\pi$, including **$d_1\circ d_0=0$** — load-bearing for the `CohomologicalObstruction` status ($B^1\subseteq Z^1$) and never previously stated — with an `OBSTRUCTION` for text-derived carriers.
* **Genesis-Bias fence (P0).** Added *No Prior Reasoning Process*: the protocol does not begin with a prior thinker, process, meaning, intent, or truth-of-the-matter; "trace" is not a claim of antecedence; $\mathsf{Text}$ is an admission channel, not a prior domain.
* **Licensed lift (P0).** §10's undefined "licensed lift" is bound to the finite obstruction calculus lift rule (obstruction witness, preservation witness, non-destruction check, budget/authority boundary, terminalizer route); the paper supplies none and constructs no lift. Items 4–5 are finite descent verification/layered authority framework-owned.
* **Compliance note (P0).** Added the finite obstruction calculus/layered authority framework compliance note (role, degree, consumes, produces, does-not-produce, authority status, declared imports, OracleNeeded items, layered authority framework boundary, mechanization status, open obligations) and the **Import/Oracle boundary**.
* **Claim typing (P1).** §12 `[TARGET]` → ``OPEN`` ×3 with discharge routes (matching ENC-0331/0332/0333 `NOT-STARTED`); 14.4 → `[POLICY RULE]`; added 14.5 ``OPEN``. §5 duality import-marked `[STANDARD — imported]`. §1's "admissible evidence for a reasoning transition" repaired to a necessary, carrier-relative condition (it contradicted §11).
* **Attainment / ZeroRel (P1).** §4's exact-repair problem is now $\inf$, not $\min$ (the inherited assumption is *attainment only when proved*); added the ZeroRel declaration reconciling the exact `Φ=0` test with the certificate's `NumericTolerance` — a floating-point $\Phi\le\varepsilon$ is `CandidateRepair`, not `Exact`.
* **Falsifiability (P1).** Withdrew the passivity falsifier as **vacuous** (the source corollary makes any map exhibiting the inequality *not a passive observer quotient*, so the test cannot fail) and named the genuinely falsifiable claim: extractor adequacy.
* **Other.** Dropped the unpriced priority claim "the first formal interface" (§1).

### v1.0.1 (2026-06-09)

* Improver hygiene pass (Stage 1). Part A rubric verified present (lead, why-care, related work, contradiction-cycle worked example with LP replay, falsifiability, §11 non-claims).
* §12 "Theorem Targets" now typed honestly as **targets** (14.1 Mechanical-conformance; 14.2 LP-duality route sketched inline — witness lower-bounds the full-space minimum, hence the $\mathcal A$-restricted one; 14.3 passivity consequence; 14.4 operational rule). Tracked as PL-014-1.
* §7 passivity theorem marked as **imported** from the primitive-axiomatics paper (Theorem O1) under its repair-compatibility hypotheses, with the hypothesis named in the statement.
* Resolved all three `[VERIFY]` tags as verification results: [4] = Lanham et al., arXiv:2307.13702; [5] = Lightman et al., arXiv:2305.20050; SMT anchor now cites de Moura–Bjørner Z3 (TACAS 2008) as [6].
* Reference [1] URL normalized to the public `records/` form (HTTP 200); title math-delimited; version v1.0 → v1.0.1.
* Created sibling claim ledger `000_reasoning_trace_validation_claim_ledger.md`; registered PL-014-1 in `proof_ledger_20260609.md`.
* Release pre-flight: normalized all `\[…\]`/`\(…\)` math delimiters to `$$`/`$` (pandoc renders the bracket forms as raw text, breaking the LaTeX build). No content change.

<!-- claim-id-body-index:begin -->

Claim-ID body index (packaging)

| ID | Home |
|---|---|
| `C1` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C2` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C3` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C3a` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C3b` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C4` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C5` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C5a` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C6` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C6a` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C7` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C8.1` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C8.2` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C8.3` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C8.4` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C8.5` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C9` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C10` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C10a` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C11` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C12` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C13` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C14` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C15` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |
| `C16` | sibling `000_reasoning_trace_validation_via_l1_obstruction_geometry_claim_ledger.md` |

<!-- claim-id-body-index:end -->
