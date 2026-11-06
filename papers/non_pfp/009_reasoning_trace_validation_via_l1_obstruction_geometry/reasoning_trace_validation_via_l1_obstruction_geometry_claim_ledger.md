Claim Ledger — Paper 014: Reasoning Trace Validation via $\ell^1$ Obstruction Geometry
======================================================================================

**Paper Key:** `001_finite_obstruction_calculus/033_reasoning_trace_validation_via_l1_obstruction_geometry`  

**Paper:** `000_reasoning_trace_validation_via_l1_obstruction_geometry_monograph.md` (v1.0.1, 2026-06-09; finite obstruction calculus/layered authority framework compliance pass 2026-07-17 — **no version bump**)
**Pipeline stage:** Improver (Stage 1) pass of 2026-06-09; finite obstruction calculus/layered authority framework compliance cleanup of 2026-07-17.
**Red note:** `published/reviews/gtoc_gtla_red_014.md`

**Verdict shape:** layered authority framework-facing protocol paper applying the corpus obstruction calculus to trace auditing. Its mathematics is almost entirely **imported** (Φ / dual witnesses from the quotient-norm layer; observer passivity from the primitive-axiomatics paper §1.7 = ENC-0207); its own contribution is the realization boundary, the typed refusal taxonomy, and the certificate format. The §12 items are targets and are typed `[OPEN]`.

**Authority status (whole paper): none.** The paper diagnoses, prices, and routes inside $\mathsf{ObstructionRegime}(k=1)$. It mints no authority of any kind. *Validated = diagnosed*, never authorized or true. No `SemanticAuthority` is available — no semantic adapter is declared.

**Load-bearing open obligation:** **PL-014-2** (extractor adequacy). No `DetectorAdequacy` certificate exists for any extractor $\pi$, and §7 exhibits a collapsing $\pi_0$ under which **every** trace certifies `Exact`. Until PL-014-2 is discharged, an `Exact` verdict is a statement about $\pi$'s image and nothing more.

---

1. Claim-by-claim typing

------------------------

Status values are restricted to the corpus claim vocabulary.

| # | Claim | Type | Hypotheses | Proof / price location | Mechanization | Import / oracle | layered authority framework authority | Remaining obligation |
|---|---|---|---|---|---|---|---|---|
| C1 | Core doctrine — "the verifier does not judge language directly; it judges declared finite structure" | `[SCOPE FENCE]` | — | Abstract box; §13 | none | — | none; fence only | — |
| C2 | §2 realization boundary; $V_\pi(y)$ components; no extraction ⇒ `NeedsRealizationFunctor` | `[DEFINITION]` | $\pi$ deterministic or versioned | §2 | none | — | none | adequacy of $\pi$ **not** covered → C12 |
| C3 | §4 submitted defect, $B^1$, $Q^1$, $\Phi$, case table | `[DEFINITION]` | finite carrier; declared scalars | §4 | none | — | none | — |
| C3a | §4 attainment: $\Phi$ is an $\inf$, not asserted attained | `[DEFINITION]` | inherited A0–A9 "attainment only when proved" | §4 *Attainment* | none | — | none | per-instance attainment proofs |
| C3b | §4 ZeroRel: `Φ=0` is `Φ≤ε` for the certificate's declared `NumericTolerance`; float $\Phi\le\varepsilon$ is `CandidateRepair`, not `Exact` | `[DEFINITION]` | declared scalar specialization; `NumericTolerance` (§10) | §4 *ZeroRel*; §10 | none | real-scalar LP + float solver **imported** | none | pin to an exact declared ring for exact-zero certification |
| C4 | §5 dual witness lower bound $\langle\varphi,\omega_1\rangle\le\Phi(\omega_1)$; saturation certifies | `[STANDARD + citation]` | finite-dimensional LP hypotheses as declared at source | Paper 006 (corpus quotient-norm layer); **not** re-proved in §5 | none | **IMPORTED** — LP duality; not a discrete trace operation | none | — |
| C5 | §7 observer passivity $\Phi_{\mathcal O}(\mathcal O(q))\le\Phi(q)$ | `[STANDARD + citation]` | **H1** $\mathcal O:Q^1\to Q^1_{\mathcal O}$ finite, deterministic, repair-compatible **quotient** (not an arbitrary map on $C^1$); **H2** target carries the **induced quotient norm** $\Phi_{\mathcal O}(y)=\inf_{\mathcal O(r)=y}\Phi(r)$; **H3** finite dimensionality | Primitive-axiomatics §1.7 **Lemma** O1 = **ENC-0207** (`PROVED-PROSE`, `[PROVEN, CONDITIONAL]`); **not** re-proved in §7 | `MECHANIZED-PARTIAL` **at source only** ([index:index:L000_05_ObserverPassivity.lean](omega_engine/research/_indexes/_master_index.yaml), on $Q^1$); **not this paper's**, and does not cover §7's $C^1$-restriction detectors | **IMPORTED**. ENC-0207 scope fence: "not an unconditional theorem about arbitrary lossy maps, arbitrary observers, or authority-bearing terminalization" | none | — |
| C5a | §7 applicability gap: passivity is **not** available for arbitrary compressed evaluators (reward models, embedding scorers) — they satisfy none of H1–H3, and H2 is exactly what fails | `[OBSTRUCTION]` | — | §7 *Applicability gap* | none | `OracleNeeded` — would require a factorization through a repair-compatible quotient of $Q^1$ + induced norm | none | open; not discharged |
| C6 | §8 typed statuses; §9 algorithm; §10 certificate format | `[IMPLEMENTATION CONTRACT]` | declared $\pi,P,\mathcal A,\mathcal C,\tau,B$ | §§8–10 | none — **unimplemented** (see C14) | — | none; refusal-compatible; no silent promotion of untyped residual | implement with build receipt |
| C6a | §8 `Exact` means exact under the declared packet, not truth in an unqualified semantic sense | `[SCOPE FENCE]` | — | §8 | none | — | none; blocks exact-repair ⇒ truth | — |
| C7 | §11 non-claims (trace ⇏ truth; trace ⇏ reasoning; stream ⇏ inner voice; low loss ⇏ valid; embedding ⇏ exact) | `[SCOPE FENCE]` | — | §11 | none | — | none; load-bearing fence for the whole paper | — |
| C8.1 | 14.1 Certificate Soundness | `[OPEN]` | declared carrier | route: mechanical conformance of §9 steps 6–7 — PL-014-1(i); **ENC-0331 `NOT-STARTED`** | none | — | none; carrier-relative only | write out |
| C8.2 | 14.2 Witness Soundness | `[OPEN]` | $\mathcal A\subseteq C^0$; LP duality (C4) | route: witness value lower-bounds $\inf_{C^0}$, hence $\inf_{\mathcal A}$ — PL-014-1(ii); **ENC-0332 `NOT-STARTED`** | none | rests on imported C4 | none | write out |
| C8.3 | 14.3 Observer Non-Certification | `[OPEN]` | certificate requirement §§8–10 | route: **the certificate requirement, not the passivity inequality** (whose hypotheses arbitrary evaluators fail — C5a) — PL-014-1(iii); **ENC-0333 `NOT-STARTED`** | none | — | none | write out; **route corrected this pass** |
| C8.4 | 14.4 No Silent Promotion | `[POLICY RULE]` | declared evaluator law (Paper 011) | §6; restated §12 | none | — | routing refusal, **not** a governance seal | none — rule, no proof needed |
| C8.5 | 14.5 Extractor Adequacy | `[OPEN]` | — | §7; **no discharge route supplied** | none | `OracleNeeded` | none | **PL-014-2 — load-bearing; see C12** |
| C9 | Worked example: contradiction cycle $\Phi=1$; path contrast $\Phi=0$ | `[WORKED EXAMPLE]` | 3-edge carrier as declared | §5; `scipy` LP replay, expected `1.0`, `0.0` | executable — the **only** artifact in the paper | real-scalar LP imported | none | — |
| C10 | §2 inherited standing assumptions A0–A9 (finite carrier; declared ring; 2-truncated carrier; **$d_1d_0=0$**; separated $Q^1$; declared gauge $J$; fixed $\ell^1$ on $C^2$; attainment only when proved; observer = repair-compatible quotient; **no authority**) admitted as obligations on $\pi$ | `[DECLARED AXIOM]` | — | §2 *Declared regime and inherited standing assumptions*; source: primitive-axiomatics A0–A9 | none | **IMPORTED**; admitted, **not derived** | none; inherits the source's "no authority" | complex-condition certificate for text-derived $\pi$ (`OracleNeeded`) |
| C10a | $d_1\circ d_0=0$ cannot be derived at this degree for extractors over $\mathsf{Text}$ | `[OBSTRUCTION]` | — | §2 `OBSTRUCTION` block | none | `OracleNeeded` | none | open — load-bearing for `CohomologicalObstruction` ($B^1\subseteq Z^1$) |
| C11 | §2 Genesis-Bias fence — no prior reasoning process, thinker, meaning, intent, or truth-of-the-matter; "trace" is not a claim of antecedence; $\mathsf{Text}$ is an admission channel, not a prior domain | `[SCOPE FENCE]` | — | §2 *Genesis-Bias Fence* | none | — | none | — |
| C12 | **`DetectorAdequacy`**: a replayable detector is not automatically adequate; a collapsing detector makes every profile exact. Exhibited: $\pi_0$ with $C^1=0$ ⇒ $\Phi=\Gamma=0$ ⇒ **every trace `Exact`**, deterministic and replayable | `[OPEN]` | — | §7 *Detector adequacy*; schema: protected distinctions / adversarial battery / blind spots / non-collapse witness | none | `OracleNeeded` | **none supplied**; required for any authority-bearing layered authority framework use | **PL-014-2 — the paper's load-bearing open obligation; unregistered in the encyclopedia** |
| C13 | Authority firewall: `Authority: none`; *validated = diagnosed*; authority not produced by diagnostics, discrete trace, finite replay alone, or residual classification | `[SCOPE FENCE]` | — | Abstract *Authority* + *Reading "validation"*; §13; compliance note | none | — | **none** — the paper's governing fence | authority-bearing use needs a separate finite descent verification/layered authority framework descent packet + terminal seal |
| C14 | Implementation registry — **withdrawn**. `trace_realization.rs` and `trace_validator.rs` **do not exist** in the repository; `certificate.rs` exists only under `crates/mub/src/wall/` and `crates/omega_lifts/` and implements neither §10 nor trace validation | `[OPEN]` | — | Appendix (verified against the repo this pass) | **none** — protocol specified but **unimplemented**; no build receipt, no conformance test | — | none | implement §§2–10; formalization-status firewall applies to any future artifact |
| C15 | §7 anti-shortcut consequence: scalar loss / reward models / embedding agreement may not replace the finite verifier | `[POLICY RULE]` | certificate requirement §§8–10 | §7 *Anti-shortcut principle* | none | — | none | **re-derived this pass from the certificate requirement — it no longer rests on the passivity inequality (C5a)** |
| C16 | §10 "licensed lift" bound to the finite obstruction calculus lift rule (obstruction witness; preservation witness; non-destruction check; budget/authority boundary; terminalizer route) | `[SCOPE FENCE]` | — | §10 *"Licensed lift" — bound, not assumed* | none | items 4–5 are **finite descent verification/layered authority framework-owned**, outside this degree | none; paper constructs **no** lift | absent a licensed lift, carrier change ⇒ `NeedsRealizationFunctor` / `CarrierFailure` |

2. Definition-as-theorem audit

------------------------------

* **ADDRESSED (2026-06-09):** §12 items were named "Theorems" while unproven — typed as targets; 14.4 is a rule, not a theorem.
* **ADDRESSED (2026-07-17):** "target" is not corpus vocabulary — 14.1–14.3 and 14.5 are now `[OPEN]`, 14.4 `[POLICY RULE]`, consistent with ENC-0331/0332/0333 `NOT-STARTED`. No status was upgraded.
* **ADDRESSED (2026-07-17):** §7's import was stated as a **Theorem** on $C^1$ with the induced-norm hypothesis missing and `$\Phi_{\mathcal O}$` undefined. It is a **Lemma** on $Q^1$ under H1–H3 (C5). The rank inflation, the domain mismatch, and the dropped hypothesis are corrected; the applicability gap is typed `[OBSTRUCTION]` (C5a).
* **ADDRESSED (2026-07-17):** §7's Consequence was presented as following from the imported inequality. It does not; it is re-derived from the certificate requirement and typed `[POLICY RULE]` (C15).
* **ADDRESSED (2026-07-17):** the passivity "falsifier" was **vacuous** (any map exhibiting $\Phi_{\mathcal O}(\mathcal O q)>\Phi(q)$ is thereby *not* a passive observer quotient, so the test cannot fail) — withdrawn; the genuinely falsifiable claim (extractor adequacy) is named in its place.

3. Open obligations

-------------------

* **PL-014-2 — extractor adequacy (LOAD-BEARING, unregistered).** Supply a `DetectorAdequacy` certificate schema for $\pi$ (protected distinctions; adversarial battery; known blind spots; non-collapse witness) and the statement that an `Exact` verdict under an adequate $\pi$ excludes the declared adversarial cases. **Nothing in §§2–10 rules out the collapsing $\pi_0$.** Until discharged, every `Exact` verdict this protocol issues is a statement about $\pi$'s image only. *Needs an encyclopedia entry.*
* **PL-014-1** — write out 14.1–14.3: (i) 14.1 as a conformance property of the §9 algorithm (Mechanical); (ii) 14.2 from LP duality (witness value lower-bounds $\inf_{C^0}$, hence $\inf_{\mathcal A}$ for $\mathcal A\subseteq C^0$) (Prose, easy); (iii) 14.3 **from the certificate requirement of §§8–10** — *route corrected 2026-07-17: the former route via the imported passivity inequality is unavailable (C5a)*. 14.4 needs no proof (rule). ENC-0331/0332/0333 all `NOT-STARTED`.
* **Complex condition** — a per-extractor certificate discharging $d_1\circ d_0=0$ for text-derived carriers (C10a). Load-bearing for the `CohomologicalObstruction` status name.
* **ZeroRel** — pin exact-zero certification to an exact declared ring, or route float $\Phi\le\varepsilon$ to `CandidateRepair` in every implementation (C3b).
* **Implementation** — §§2–10 are specified but unimplemented (C14); any future artifact is subject to the formalization-status firewall.
* **ENC-0333 route** — the encyclopedia entry records the discharge route as "derive from the imported passivity inequality (ENC-0207)". That route is **unavailable** per C5a and should be re-pointed to the certificate requirement. *Encyclopedia edit required; out of scope for this pass (write boundary).*

4. Pass records

---------------

### finite obstruction calculus/layered authority framework compliance pass (2026-07-17)

* **P0 fixed (7):** authority smuggle ("typed refusals … provide authority semantics") + authority firewall added; DetectorAdequacy fence + collapsing-extractor counterexample; §7 import repaired (domain/rank/hypothesis/scope); implementation claim withdrawn as false + formalization firewall; inherited A0–A9 incl. $d_1d_0=0$ declared; Genesis-Bias fence added; "licensed lift" bound to the finite obstruction calculus lift rule. Compliance note + Import/Oracle boundary added.
* **P1 fixed (7):** "admissible evidence for a reasoning transition" (contradicted §11) → necessary, carrier-relative; §5 duality import-marked; min → inf; vacuous passivity falsifier withdrawn; ledger rebuilt with required columns + allowed vocabulary; `[TARGET]` → `[OPEN]`; ZeroRel declared.
* **P2:** dropped "the first formal interface" (P2-1). Not fixed (minimal-patch rule): §12/14.x numbering drift (P2-2); gauge $J$ used but not declared (P2-3).
* **Claims downgraded:** C8.1–C8.3 `[TARGET]`→`[OPEN]`; C8.4 →`[POLICY RULE]`; C5 `[PROVEN IN …]`→`[STANDARD + citation]` (imported, H1–H3 named); C15 →`[POLICY RULE]`; C14 →`[OPEN]` (claim withdrawn as false). **No claim upgraded.** No version bump.

### Improver pass (2026-06-09)

* Part A: all six verified present.
* Claims retyped: §12 ×4 (targets), §7 (import-marked).
* Edits: 3 × [VERIFY] resolved (arXiv:2307.13702, arXiv:2305.20050, Z3/TACAS 2008); ref [1] URL form; title math-delimited; changelog added; v1.0 → v1.0.1.
