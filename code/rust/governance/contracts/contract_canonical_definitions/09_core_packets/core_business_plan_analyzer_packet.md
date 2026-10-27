packet_type: implementation
authority_effect: None
carrier: finite claim/evidence/owner/deadline preorder (C⁰)
primary_residual: unwitnessed-claim mass (Q¹)
in_scope_repairs: citation extension, ownership extension, deadline adjoining (d₀)
deferred_residuals: stale evidence (C¹_stale), circular evidence (C¹_circ)
seal_condition: terminalize_row returning Decision::Certified on canary_business_plan.md post-Meta rows

Core Business Plan Analyzer (Obstruction Descent Packet)
=========================================================

**Date:** 2026-06-20
**App:** `core_business_plan_analyzer`
**Bundle status:** load-bearing, no sibling lemma-packets. (Successor packets `core_business_plan_evidence_refresh_packet.md` and `core_business_plan_portfolio_packet.md` carry the deferred $C^1_{\text{stale}}$ and $C^1_{\text{circ}}$ classes and are independent packets in their own right, not DDA-`C` lemma-packets supporting this one.)
**Role:** EPK-LGGR diagnostic analyzer over a business-plan document. Takes a markdown plan, emits a typed obstruction packet (Carrier + $C^1$ + $Q^1$ + $\Gamma_2$ + recommended Metas) as JSON. Diagnostic only; the analyzer does NOT mint authority. Only `core_sweep_kernel::terminalize_row` / `core_certifiers::certify_checked_packet` can seal a terminal.

**Driving obstruction:** Business-plan critiques today are prose. There is no typed $Q^1$ over a claim-to-evidence cochain, and no $\Gamma_2$ measuring whether the local "claim cited by evidence cited by owner-with-deadline" overlaps cocycle-close into a globally consistent plan.

---

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The finite preorder $\mathcal{P}$ extracted from a single business-plan document, with four sorts:

* $\mathrm{Claim}$ — typed assertions (revenue projection, market size, competitive moat, hiring forecast, milestone).
* $\mathrm{Evidence}$ — citations (URL, internal doc id, dataset row, prior-art reference, primary source).
* $\mathrm{Owner}$ — a named agent responsible for the claim (person, team, vendor).
* $\mathrm{Deadline}$ — a typed temporal bound (ISO-8601 date or quarter id).

The 2-window inspects the local cochain $\mathrm{Claim} \xrightarrow{d_0} \mathrm{Evidence}$ at one window and the closure $\mathrm{Evidence} \xrightarrow{d_1} (\mathrm{Owner}, \mathrm{Deadline})$ at the next window, with overlap on shared evidence rows. Carrier is built via `core_homology::CochainComplex` (cf. `CochainPrimitiveDifference`) with sort tags carried as `core_types` authority-vocabulary labels — never a certifier.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Current local assignments are the parsed rows of the markdown plan:

* a `Vec<ClaimCell>` (claim-id, prose, sort tag),
* a `Vec<EvidenceCell>` (evidence-id, source uri, hash),
* a `Vec<OwnerCell>` (owner-id, display name),
* a `Vec<DeadlineCell>` (deadline-id, ISO-8601 instant),
* and the four typed cite-relations $r_{ce}, r_{eo}, r_{cd}, r_{co}$ already present in the document.

Realized as `CochainComplex.C0` in `core_homology`; the four relation tables are the explicit 0-cochains in the analyzer carrier.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The cochain map

$$
d_0 \colon C^0(\mathrm{Claim}) \to C^1(\mathrm{Claim} \times \mathrm{Evidence})
$$

sending a claim $c$ to the formal difference $\sum_{e \in r_{ce}(c)} (c, e) - \delta_c$, where $\delta_c$ is the "expected citation" sentinel attached to the sort tag of $c$. Permitted $d_0$-trivial moves are exactly the gauge moves of §5: rewording, citation re-ordering, evidence-id renumbering, and rephrasing that preserves the cited URI/hash. Bound to `core_homology::CochainComplex::d0`.

**Implementation note (witnessed carrier).** The analyzer's `carrier.rs` realizes $d_0$ as the **cite-telescope incidence**: a genuinely non-zero $c_1 \times c_0$ coboundary whose rows are cyclic differences $e_i - e_{(i+1)\bmod n}$ (coordinate-sum zero), so $\operatorname{im}(d_0)$ is the balanced-citation subspace. $d_1$ is the non-zero all-ones closure row; $d_1 \circ d_0 = 0$ holds on these non-zero matrices and is **verified by `CochainComplex::new`** (a perturbed non-telescope carrier is rejected with `CoboundaryLawViolation` — see the `carrier_rejects_non_zero_d1_d0` negative control). This is NOT a decorative all-zero complex.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** The 1-cochain enumerates per-claim defects:

* $C^1_{\text{cite}}$ — claim with no cited evidence (unwitnessed-claim cell).
* $C^1_{\text{own}}$ — claim with evidence but no owner.
* $C^1_{\text{date}}$ — claim with owner but no deadline.
* $C^1_{\text{stale}}$ — claim with an evidence row whose hash no longer matches the source (drifted citation).
* $C^1_{\text{circ}}$ — claim whose evidence row is itself an internal claim (self-citation cycle).

Each defect is a typed `CochainPrimitiveDifference` row, NEVER a free-form prose finding. The analyzer's CLI emits the full $C^1$ population as a JSON array of primitive-difference cells.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two $C^1$ cells are ZeroRel-equivalent iff they differ only by:

* whitespace, casing, or markdown formatting of claim prose;
* claim-id, evidence-id, owner-id, or deadline-id permutation that preserves the four relation tables;
* evidence-row deduplication where two rows have identical normalized URI and identical content-hash.

ZeroRel is the gauge equivalence transported through `core_homology::QuotientSpace`; the analyzer never charges a defect against $\Phi_1$ when the only difference is a ZeroRel move.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** $Q^1 = C^1 / \operatorname{im}(d_0)$ under ZeroRel. The primary residual is the **unwitnessed-claim mass**:

$$
Q^1_{\text{prim}} = \big[\, c \in \mathrm{Claim} \;\big|\; r_{ce}(c) = \emptyset \;\text{ in the ZeroRel-quotient} \,\big].
$$

This is the irreducible mass of claims that no ZeroRel-permissible rewording can cite away. Computed via the `QuotientSpace` projection emitted by `core_homology`; the analyzer reports $|Q^1_{\text{prim}}|$ alongside the per-cell witness list.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** The closure cochain

$$
d_1 \colon C^1(\mathrm{Claim} \times \mathrm{Evidence}) \to C^2(\mathrm{Claim} \times \mathrm{Evidence} \times \mathrm{Owner} \times \mathrm{Deadline})
$$

demands triple-overlap coherence: every $(c, e)$ pair extends to a quadruple $(c, e, o, t)$ with $o \in r_{eo}(e) \cap r_{co}(c)$ and $t \in r_{cd}(c)$ such that $t$ is in the future of the document timestamp. Bound to `core_homology::CochainComplex::d1`.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass) — per-defect (A1):** Cocycle closure failure of $d_1 \circ d_0$ is reported per defect class, not as a single packet-wide value. Computed by `core_functional::ExactGamma2Result` against the analyzer's `Observer` over the four relation tables. The CLI emits a Gamma2 cross-section keyed by defect alongside $Q^1$.

| Defect | $\Gamma_2$ (closure-failure mass) | Witness |
|--------|------------------------------------|---------|
| $C^1_{\text{cite}}$ | 0 (no $(c,e)$ pair exists for an unwitnessed claim, so no quadruple to close) | $r_{ce}(c) = \emptyset$ |
| $C^1_{\text{own}}$ | count of $(c,e)$ with $r_{eo}(e) \cap r_{co}(c) = \emptyset$ | evidence cited by claim but disowned by every owner attached to that claim |
| $C^1_{\text{date}}$ | count of $(c,e,o)$ with $t \in r_{cd}(c)$ in the past of document timestamp, or $r_{cd}(c) = \emptyset$ | deadlines in the past, or owner with no path through evidence to a dated commitment |
| $C^1_{\text{stale}}$ | DEFERRED (closure measured by successor packet; not in this window) | hash-refresh oracle out of scope here |
| $C^1_{\text{circ}}$ | DEFERRED (closure measured by successor packet; not in this window) | cross-plan cycle detection lives in `core_business_plan_portfolio_packet.md` |

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass) — per-defect (A1):** Non-removable exactness failure is the **weighted-$\ell^1$ quotient distance** $\Phi_1([\omega]) = \min_\alpha \lVert \omega - d_0\alpha \rVert_{1,w}$ of the observed defect cochain $\omega$ from $\operatorname{im}(d_0)$ — NOT the raw cardinality $\lvert Q^1_{\text{prim}}\rvert$ (the sprint adversary gate (c) forbids that identification). Computed via `core_functional::VerifiedExactPhi1`, whose sole constructor `Phi1Functional::verify_exact_certificate(ExactPhi1Certificate)` replays a primal–dual certificate proving optimality (the dual witness annihilates $\operatorname{im}(d_0)$ and matches the primal residual). The in-scope value **folds in the $\Gamma_2$ closure mass**: $\Phi_1^{\text{in-scope}} = (\text{surviving cite cells}) + \Gamma_2^{\text{in-scope}}(\text{own}+\text{date})$, so witnessed/closed cells (coboundaries) are projected out of the residual and the value is strictly below $\lvert C^1\rvert$. The integer mass is read from the verified `value(): BigRational` (asserted integral). The Definition of Done is computed on the in-scope subset; the deferred subset is reported as a non-zero `defer_mass` field in the emitted JSON and explicitly routed to a successor packet (§13.A), never folded into the DoD inequality and never deleted from $Q^1$.

**Witnessed descent (M1).** The in-scope $\Phi_1$ before-state is **computed** $> 0$ on the non-degenerate telescope carrier of §3 (asserted in `phi1::tests::phi1_before_state_is_nonzero_computed_quotient` and `meta::tests::m1_phi1_descent_witnessed_on_real_carrier`), and the after-state is **recomputed** from the post-$\Meta$ carrier on the same `BigRational` rail and asserted $= 0$. The before-mass is never a hardcoded literal and the carrier is never all-zero.

| Defect | $\Phi_1$ (per class) | Scope |
|--------|----------------------|-------|
| $C^1_{\text{cite}}$ | count of unwitnessed-claim cells surviving ZeroRel | in-scope (closable by $\Meta_{\text{cite}}$); contributes to $\Phi_1^{\text{in-scope}}$; DoD requires $= 0$ on canary |
| $C^1_{\text{own}}$ | count of evidence-without-owner cells surviving ZeroRel | in-scope (closable by $\Meta_{\text{own}}$); contributes to $\Phi_1^{\text{in-scope}}$; DoD requires $= 0$ on canary |
| $C^1_{\text{date}}$ | count of owner-without-deadline cells surviving ZeroRel | in-scope (closable by $\Meta_{\text{own}}$, which also adjoins $r_{cd}$); contributes to $\Phi_1^{\text{in-scope}}$; DoD requires $= 0$ on canary |
| $C^1_{\text{stale}}$ | count of `defer:stale` cells surviving ZeroRel | deferred; contributes to $\Phi_1^{\text{deferred}}$ / `defer_mass`; NOT in DoD inequality |
| $C^1_{\text{circ}}$ | count of `defer:circ` cells surviving ZeroRel | deferred; contributes to $\Phi_1^{\text{deferred}}$ / `defer_mass`; NOT in DoD inequality |

Per A1, the in-scope rows are the classes where this window can act and the deferred rows are where this window cannot — the same 2-window is exact-repair-track for one defect and no-rule-track for another. The analyzer reports each row, $\Phi_1^{\text{in-scope}}$ (cite+own+date), $\Phi_1^{\text{deferred}}$ (stale+circ), and their sum $\Phi_1$ as non-negative integers.

10. Classify System State
-------------------------

**Per-defect (A1):** Each defect class lands on its own row of the four-way trichotomy {Exact repair, Closed survivor, Active closure failure, No rule}. A single 2-window can be exact repair for one class and no rule for another — that is the per-defect content of A1.

| Defect | Class |
|--------|-------|
| $C^1_{\text{cite}}$ | Active closure failure — $\Phi_1 > 0$ until $\Meta_{\text{cite}}$ adjoins the missing $(e^\star, \text{uri}, \text{hash})$ row. |
| $C^1_{\text{own}}$ | Active closure failure — $\Gamma_2 > 0$ until $\Meta_{\text{own}}$ adjoins $(o^\star, t^\star)$ plus $r_{co}, r_{eo}$. |
| $C^1_{\text{date}}$ | Active closure failure — $\Gamma_2 > 0$ until $\Meta_{\text{own}}$ adjoins $(o^\star, t^\star)$ plus $r_{cd}$. |
| $C^1_{\text{stale}}$ | No rule — hash-refresh Meta is not in this packet's $\Meta$ menu; deferred to successor packet (§13.A). |
| $C^1_{\text{circ}}$ | No rule — cycle-break Meta over internal-claim DAG is structurally outside $\Meta_{\text{cite}}/\Meta_{\text{own}}$; deferred to portfolio packet (§13.A). |

(The typical business plan exhibits $Q^1_{\text{prim}} > 0$ and $\Gamma_2 > 0$ simultaneously across the in-scope rows — unwitnessed claims AND missing owner/deadline closure — while the deferred rows stay on the no-rule track.)

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Meta / Structural Extension):** Pin to two concrete `core_discrete_deformation_algebra::FaceLambda` candidates, in this strict order:

1. **$\Meta_{\text{cite}}$ — citation Meta.** A `FaceLambda` over the $C^0(\mathrm{Claim})$ face that extends the carrier with a new `EvidenceCell` row $(e^\star, \text{uri}, \text{hash})$ and a new entry in $r_{ce}$, witnessed by a `NonDestructiveExtensionCertificate` proving that no existing $C^0$ or $C^1$ cell is rewritten — the carrier is only EXTENDED, never contracted. Triggered when $Q^1_{\text{prim}} > 0$.

2. **$\Meta_{\text{own}}$ — ownership Meta.** A `FaceLambda` over the $(\mathrm{Claim} \times \mathrm{Evidence})$ face that adjoins an $(o^\star, t^\star)$ pair plus entries in $r_{co}, r_{cd}, r_{eo}$, witnessed by a `FiniteLambdaStepCertificate` recording the finite-step preservation of the four relation tables. Triggered when $\Gamma_2 > 0$ AND $Q^1_{\text{prim}} = 0$.

Both Metas honor the firewall: the lambda extends the carrier and emits a non-destruction certificate, but the certificate itself does NOT mint authority — only `core_sweep_kernel::terminalize_row` / `core_certifiers::certify_checked_packet` can do that downstream. The analyzer CLI's `--propose-meta` flag emits the two `FaceLambda` candidates as JSON; it does not seal anything.

**Oracles required (A3):** none. Both $\Meta_{\text{cite}}$ and $\Meta_{\text{own}}$ are carrier-internal `FaceLambda` extensions licensed inside the declared finite 2-window — no imported representation theorem is invoked. No sub-claim of this packet carries the `OracleNeeded` terminal. (The deferred classes $C^1_{\text{stale}}$ and $C^1_{\text{circ}}$ do NOT require oracles inside this window either; they require a different Meta menu housed in a successor packet — that is a per-defect "No rule" terminal at this window, not an import.)

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Executable Rust pipeline backed by `core_discrete_deformation_algebra`:

1. **Parse** — markdown plan $\to$ four `Vec<*Cell>` tables and four relation tables.
2. **Construct carrier** — feed tables into `core_homology::CochainComplex` via the `pfp` adapter for any `lp<…>`-shaped claims.
3. **Quotient projection ($R$)** — apply ZeroRel via `QuotientSpace` and emit $Q^1$.
4. **Closure measurement** — compute $\Gamma_2$ via `core_functional::ExactGamma2Result`.
5. **Residual measurement** — compute $\Phi_1$ via `core_functional::VerifiedExactPhi1`.
6. **Meta proposal ($\Meta$)** — emit ordered `FaceLambda` candidates per §11.
7. **EPK cross-check ($D$)** — pass the carrier through `core_epk::EpkResidualLedger` (constructed via `EpkResidualLedger::from_metrics(&metrics)`, then chained with `.with_obstruction_status(status)` where `status: core_functional::trichotomy::ObstructionStatus`). The ledger projects to `AuthorityEffect::None` and `Outcome::Refused(RefusalSource::Residual)` BY CONSTRUCTION — diagnostic only; EPK never mints authority. The analyzer asserts those two invariants on the post-Meta row but does NOT read a "Repaired" classification off the ledger (no such variant exists).
8. **Emit** — serialize the whole packet (Carrier + $Q^1$ + $\Gamma_2$ + $\Phi_1^{\text{in-scope}}$ + $\Phi_1^{\text{deferred}}$ + `defer_mass` + Meta candidates + EPK ledger row) as a JSON document next to a canary markdown fixture.

A successor sprint (not this packet) routes the JSON through `core_sweep_kernel::terminalize_row` if and only if the operator authorizes sealing; the analyzer itself never calls the terminalizer.

13. Terminal Status
-------------------

**Per-defect terminal status (A1 + A4):** Current and Target are reported per defect class, and each row names a concrete authority-minting Seal Condition. The markdown does NOT mint authority; the strings "Repaired" / "Sealed" / "Terminalized" never appear as authority claims in this packet. Only `core_sweep_kernel::terminalize_row` (returning `Decision::Certified` on the row) or, on the packet path, `core_certifiers::certify_checked_packet` (7 IsAuth guards) can flip Current to Target downstream.

> [!IMPORTANT]
> `Decision::Certified` certifies ONLY the **diagnostic repair packet**, not the truth or validity of the business plan itself.
> `Certified` means: this obstruction row was repaired under the declared analyzer carrier. It does not certify the business claim, market forecast, legal truth, or commercial viability.
>
> All user-facing outputs are renamed to avoid any authoritative or approval-adjacent language (such as "business plan approved"). The canonical user-facing outputs are:
> - **Certified diagnostic row** (the terminalized/repaired obstruction row)
> - **Boundary-checked plan packet** (the serialized carrier + residuals)
> - **Unresolved residuals** (the surviving/deferred defects in $Q^1$)

| Defect | Current | Target | Seal Condition |
|--------|---------|--------|----------------|
| $C^1_{\text{cite}}$ | ActiveClosureFailure ($\Phi_1 > 0$, $Q^1_{\text{prim}}$ non-empty) | Repaired | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` with `host_terminal_status = "Certificate"` on the post-$\Meta_{\text{cite}}$ row of the canary fixture (`canary_business_plan.md`). |
| $C^1_{\text{own}}$ | ActiveClosureFailure ($\Gamma_2 > 0$) | Repaired | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the post-$\Meta_{\text{own}}$ row of the canary fixture. |
| $C^1_{\text{date}}$ | ActiveClosureFailure ($\Gamma_2 > 0$) | Repaired | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the post-$\Meta_{\text{own}}$ row (which adjoins $r_{cd}$) of the canary fixture. |
| $C^1_{\text{stale}}$ | NoRule (deferred; carried as `defer:stale` in $Q^1$) | NoRule at this window; ExactRepair routed to successor | Successor packet `core_business_plan_evidence_refresh_packet.md` (not yet written) must seal via its own `core_sweep_kernel::terminalize_row` call after a hash-refresh Meta; this packet seals nothing here. |
| $C^1_{\text{circ}}$ | NoRule (deferred; carried as `defer:circ` in $Q^1$) | NoRule at this window; ExactRepair routed to successor | Successor packet `core_business_plan_portfolio_packet.md` must seal via its own `core_sweep_kernel::terminalize_row` call after a cycle-break Meta over the internal-claim DAG; this packet seals nothing here. |

The analyzer ships as a Rust CLI under a new workspace crate `core_business_plan_analyzer` that consumes the bindings above, takes a markdown plan on stdin or `--input <path>`, and emits the JSON packet on stdout. The canary fixture (a deliberately defect-rich one-page plan covering ALL FIVE $C^1$ defect classes — see §13.A below) is green when the JSON contains a non-empty $Q^1$ AND a non-empty $\Gamma_2$ AND a non-empty `meta_candidates` array AND $\Phi_1^{\text{in-scope}}$ matches the expected count (zero on the post-Meta row) for the fixture.

### 13.A Canary $C^1$ coverage (no silent classes)

The canary fixture MUST exercise every $C^1$ defect class declared in §4 — no orphan classes:

* $C^1_{\text{cite}}$ — 3 cells (closed by $\Meta_{\text{cite}}$ in §11).
* $C^1_{\text{own}}$ — 2 cells (closed by $\Meta_{\text{own}}$ in §11).
* $C^1_{\text{date}}$ — 1 cell (closed by $\Meta_{\text{own}}$ in §11, which adjoins the $(o^\star, t^\star)$ pair plus $r_{cd}$ — see §11.2).
* $C^1_{\text{stale}}$ — 1 cell. **Defer:** closure of $C^1_{\text{stale}}$ requires a hash-refresh Meta (re-fetch the source URI and recompute the content hash) that is NOT part of this packet's $\Meta$ menu. Successor packet: `core_business_plan_evidence_refresh_packet.md` (not yet written). Until then, the canary AT asserts that $C^1_{\text{stale}}$ cells appear in $C^1$ and survive into $Q^1$ as a tracked `defer:stale` annotation, NOT as a Phi_1 contribution that fails DoD.
* $C^1_{\text{circ}}$ — 1 cell. **Defer:** closure of $C^1_{\text{circ}}$ requires a cycle-break Meta over the internal-claim DAG (not a single carrier extension) and is structurally outside the $\Meta_{\text{cite}}/\Meta_{\text{own}}$ pair. Successor packet: `core_business_plan_portfolio_packet.md` (already named in sprint §7 Out of scope; cross-plan cycle detection lives there). Until then, the canary AT asserts that $C^1_{\text{circ}}$ cells appear in $C^1$ and survive into $Q^1$ as a tracked `defer:circ` annotation.

The DoD "$\Phi_1 = 0$ on canary" is computed AGAINST the in-scope subset $\{C^1_{\text{cite}}, C^1_{\text{own}}, C^1_{\text{date}}\}$. The deferred subset $\{C^1_{\text{stale}}, C^1_{\text{circ}}\}$ is surfaced in $Q^1$ with explicit `defer:<class>` ids so the residual is NEVER silent. Per §9, $\Phi_1 = \Phi_1^{\text{in-scope}} + \Phi_1^{\text{deferred}}$; the DoD inequality is on the first term and the second is reported alongside as a non-zero `defer_mass` field in the emitted JSON.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_business_plan_analyzer::gtoc_adapter::evaluate_business_plan` constructs `GtocExactInput` and calls `core_pipeline::gtoc_gtla::evaluate_exact`; production corpora and focused adapter tests are present. Consumer refresh, stale/circular successor classes, and a current terminal receipt remain owned by `S16-004`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census carries the current packet hash and source manifest and supersedes any earlier statement that the adapter or corpora are absent.

15. S16-004 deferred-control disposition
----------------------------------------

At frozen base `46d91fb4165e6cb83fbb8c41168ed56739db478e`, S16-004 packet `01bd1e82e29810bf940ae962ebf3b50c87b54ba79dfd42a1d9dedfedc8f55e7b` protects the plan document through the prompt-packet boundary before parsing and exact evaluation. The bounded `EvidenceRefreshOracle` returns verified, unavailable, or timeout receipts. Verified bytes must match the plan-declared content hash before mutation. Cycle repair requires an exact pre-edit graph hash, removed edge, replacement evidence, nonempty issuer, and attestation; the analyzer then recomputes C1, Phi1, Gamma2, deferred mass, and the shared exact terminal.

Focused deferred-control tests pass 5/5 and prompt-boundary tests pass 2/2. Unavailable and timeout route to `OracleNeeded`; drift and irreducible cycles route to `OpenObstruction`; unlicensed edits route to `LiftLicenseNeeded`. The admitted repaired fixture reaches `ExactRepair`. Results are diagnostic with `AuthorityEffect::None`; no source truth, plan truth, commercial viability, gate activation, or promotion is certified.
