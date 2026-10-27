packet_type: implementation
authority_effect: None
carrier: paper folders NNN[a-z]?_* under research/published/, including those nested one level inside NNN_* programme folders, and global proof_ledger (C⁰)
primary_residual: structural rip drift plus claim-to-PL identity mismatch represented as one exact finite GTOC input
in_scope_repairs: canonical folderizer, claim-ledger normalizer, process-global PL-ID broker, exact closure adapter, GT-tower and Symbol Game adapters
deferred_residuals: open Paper 000c proof-ledger research obligations PL-000c-1/3/7/9/11, and governance-controlled bulk rerip policy
closed_residuals: the programme-scoped paper-id ambiguity of §1 — CLOSED by operator ruling 2026-07-22 (R1 PL key = research-programme key plus paper key; R3 re-keying the collision detector is the intended discharge; R5 the dot-separated lexical rendering PL-<scope>.<paper>-<ordinal> with self-scoped roots is adopted). Rollout is a write-forward cutover (unversioned) — no pre-existing ledger byte is rewritten; a paper with flat rows starts a second independent scoped counter at ordinal 1.
seal_condition: core_rip_papers_runtime::certify_checked_rip with ExactRepair, packet-bound DescentWitness, and decided IsAuth
runtime_status: RUNTIME-CLOSED (2026-07-17)

Core Rip-Papers Automation (Obstruction Packet)
================================================

**Date:** 2026-06-20
**App:** `core_rip_papers` (Rust CLI replacing the manual `/rip-papers` skill driver)
**Scope:** Determinize folderization, Claim Ledger normalization, and global proof-ledger PL-ID stamping; evaluate the resulting structural and claim-to-PL residual through `core_pipeline::gtoc_gtla`; and keep the core CLI diagnostic. Multi-process allocation is serialized by `ProcessGlobalPlIdBroker`. Markdown and product-local terminal stamps do not mint canonical authority; only the checked-packet certifier bridge can construct `CertifiedAuthority`.

**Bundle status (A2):** load-bearing, no sibling lemma-packets. The single CLI is the load-bearing descent packet; three sub-mechanisms (`folderize`, `emit_claim_ledger`, `append_global_pl_block`) live inside one `RipPapersFace` lambda and are reported per-defect (A1), not split into sibling packets.

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The finite preorder of paper artifacts under `engine/research/published/`. Each carrier element is a paper folder `NNN[a-z]?_Title_With_Spaces_or_Underscores/` together with its in-folder companions (`NNN_*_main.md` or single-file `NNN_*.md`, optional `NNN_*_Claim_Ledger.md`, optional `theorem_ledger.md` / `math_spine.md` for GT papers) and the global ledger file `engine/research/proof_ledger_<YYYYMMDD>.md`. The 2-window inspects (i) the local folder shape against the `paper_hygiene_standard.md` rubric and (ii) the cross-boundary closure between per-paper Claim_Ledger and the day's global proof_ledger PL-IDs. Evaluation preorder: paper precedes its companions; companions precede the global ledger row.

**Programme nesting (2026-07-21).** PR #1191 partitioned the corpus into ten programme folders `000_`–`009_`. A programme folder itself matches the `NNN[a-z]?<sep>` grammar, so the previous single-level enumeration emitted each programme as a bodyless paper and hid every real paper beneath it. `enumerate_papers` now classifies a grammar-matching folder as a *programme* iff it **contains** folders that also match the grammar, and descends exactly one level into it without emitting the programme. The discriminator is deliberately "contains papers" and not "carries no manuscript": programmes routinely hold index or overview documents at their root (`001_gtoc_gtla/gt_tower_master_design.md`, `003_quantum_foundations/qm_atlas.md`, `000_witnessed_difference/000_witnessed_difference.md`), and the weaker test misclassifies all three as papers. The rule is contracted in `core/02_evidence/published_paper_carrier.contract.yaml`; a GT-tower folder is never a programme.

**Carrier well-formedness (id-injectivity) — OPEN, programme-scoped.** The folder-name $\to$ paper-id map `carrier::paper_id_of` must be *injective* over the enumerated folders. Two folders deriving one id make the carrier ambiguous: the elements become indistinguishable by id, and because §12's `append_global_pl_block` keys PL blocks by that id, one folder's rows land in another paper's block. `enumerate_papers` refuses a non-injective root with the typed `CarrierError::DuplicatePaperIds`, reporting every collision in one pass — the same doctrine as the CLI's refusal to default an underivable id to `"000"`.

**This condition no longer holds on the live tree, and the failure is structural rather than accidental.** After #1191 paper ids are unique only *within* a programme: `001_gtoc_gtla/coda_fda`, `004_projection_obstruction/001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects` and `006_ai_evaluation/001_verifiable_ai_via_the_l1_coboundary_norm` all legitimately carry id `001`.

**Census re-derived 2026-07-22** by replaying the enumeration rule (grammar + programme discriminator + GT-tower short-circuit) over `engine/research/published/`: **86** enumerated paper elements (84 `Standard`, 2 `GtTowerVariant`) across **16** distinct ids, of which **12 ids collide**, covering **82 of the 86** folders. Multiplicities: `000` ×12, `001` ×9, `002` ×9, `003` ×9, `004` ×8, `005` ×8, `006` ×8, `007` ×6, `008` ×5, `009` ×4, `010` ×2, `999` ×2. Only `011`, `012`, `101` and `901` are unique. This supersedes the earlier "roughly ten ids" figure, whose two cited colliders — `004_projection_obstruction/001_Projection_Obstruction_…` and `000_witnessed_difference/001_wd1_…` — no longer resolve on disk (#1246 lowercased every name under `research/published/`; #1271 consolidated the WD-0…WD-5 root arc into `000_wd0_5_from_primitive_difference_to_cochain_systems`). The full derivation, the two discharge options and their ledger consequences are recorded in `crates/core_rip_papers/docs/carrier_paper_id_collision_refusal_20260722.md`, which is a proposal and mints no authority.

Eleven of the twelve collisions are between real papers, so the pre-#1191 repair recorded here — rename the offending *non-paper* directory out of the grammar — does not reach them. The twelfth was not previously recorded and is different in kind: id `999` collides `001_gtoc_gtla/999_gtoc` (a GT-tower paper carrying `theorem_ledger.md` + `math_spine.md`) with `999_published_in_general_media`, which `research/published/_index.md:279` files under "Non-programme items at the published root" as popular/LinkedIn articles and PDFs. It enumerates as a `GtTowerVariant` paper because its `999` prefix falls in the contracted `993`–`999` range; the short-circuit at `carrier.rs:143` is not load-bearing for this collision, since its one subdirectory (`right_or_wrong_is_the_wrong_first_question`) does not match the grammar and programme detection would classify the folder as a paper regardless. Renaming it out of the grammar is the pre-#1191 repair and would remove one of the twelve collisions; the remaining eleven would still make `enumerate_papers` return `DuplicatePaperIds`.

The guard is therefore reporting a true residual: **the `PL-<paper>-<n>` global-ledger key is ambiguous across programmes.** Measured 2026-07-22 against the 22 dated `research/encyclopedia/proof_ledgers/proof_ledger_*.md` files, counting one occurrence per match of `PL-[A-Za-z0-9]+-[A-Za-z0-9]+` — the ordinal may be letters, not only digits (`PL-003-A`, `PL-GTOC-BB7`): **92** distinct `<paper>` keys over **1168** `PL-<key>-<ordinal>` occurrences, of which **11 keys** (`000`–`010`) carrying **119 occurrences** are ambiguous under the census above. `999` collides on the corpus but appears as no ledger key. Those 1168 are a subset of the 1222 raw `PL-` substrings in the same files; the other 54 are wildcard globs (`PL-GTOC-*`, `PL-WD0-*`), the literal template `PL-<paper>-<n>`, or prose, not ledger ids. A superseded digit-only reading gave 88 keys / 1101 occurrences / 10 ambiguous keys / 91 ambiguous occurrences and missed 59 letter-ordinal ids, so the correction *raises* the deferred residual rather than shrinking it. These are measured counts from a re-scan, not gate-verified figures: no CI gate and no `cargo` run checked them. Discharging it requires either qualifying the PL key by programme or renumbering papers to restore global uniqueness; both change a published ledger convention, so this is an operator decision and is recorded as a deferred residual rather than silently weakened. Until it is decided, `enumerate_papers` refuses the live root — a typed refusal, not a silent ambiguous pick.

### 1.1 Ruling and proposal — the ambiguity's SEMANTICS are closed; the lexical form is a proposal

**Everything above §1.1 is the historical record of the refusal and is retained verbatim.** It is why the guard existed and why the ambiguity was real; none of it is deleted, and the guard `CarrierError::DuplicatePaperIds` was never weakened. This subsection separates what the operator RULED from what an agent PROPOSED, because conflating the two on the record is itself a defect.

**RULED BY THE OPERATOR (2026-07-22).** Three rulings, all made in conversation on 2026-07-22 and all attributable to the operator, none to an agent:

* **R1 — the identity semantics.** Quoted verbatim: "The PL key should be research program key plus paper key." A bare paper key does not identify a paper across the corpus; the key is the research-programme key *plus* the paper key.
* **R2 — the rollout is date-free, and the name must say so.** The operator accepted the date-free rollout semantics and directed that the word "dated" come out: nothing in the system reads a date. Recorded below under its corrected name.
* **R3 — re-keying is the intended discharge.** Re-keying the collision detector to the ruled `PaperId` IS the intended discharge of the epic gate at `research/published/auto_allo_p.md:487` and global gate G5 at `:729` — it resolves the ambiguity rather than routing around it, and the guard still fires on a genuinely ambiguous carrier.

R1 and R3 CLOSE the ambiguity residual; R5 (below) fixes the rendering.

**R5 — RULED BY THE OPERATOR (2026-07-22): the lexical form.** The **dot separator and the self-scoped roots** were first proposed by an agent and are now **adopted by operator ruling** ("Use your dot proposal", 2026-07-22). The evidence below is the argument that was offered *for* the proposal; the operator's ruling is what adopts it. Adopted form:

```text
PL-<scope>.<paper>-<ordinal>          e.g.  PL-009.000-1
```

Evidence offered *for* the proposal (arguments, not a decision):

* **Why a dot.** `.` is disjoint from the local `paper_id_grammar.separators` (`_`, space, `-`), which `core_contracts/build.rs` asserts at build time. `paper_id_of` returns `None` for a dot but `Some(scope)` for `_` and `-`, so feeding a scoped key back through the LOCAL grammar must refuse rather than silently truncate:

  ```text
  paper_id_of("009.000") -> None       CLEAN TYPED REFUSAL
  paper_id_of("009_000") -> "009"      SILENT WRONG ANSWER
  paper_id_of("009-000") -> "009"      SILENT WRONG ANSWER
  ```

  A separator drawn from the local set would answer `Some(scope)` and collapse a corpus-wide key to a programme key with no error anywhere.

* **Why self-scoped roots.** A flat root key is already occupied: `PL-012-1` exists in the ledgers and denotes `002_finite_obstruction_calculus/006_degree_wise_dsl`, **not** the corpus-root `012_mutually_unbiased_bases`, which falsifies a flat root. So a root-level paper is self-scoped (`999_published_in_general_media` $\to$ `999.999`). Injectivity of the adopted form was checked over all 86 live corpus elements: 86 keys, 0 collisions.

**Migration — WRITE-FORWARD CUTOVER (unversioned).** Pre-existing rows are never rewritten because the ledger is append-only; what selects a row's key form is which code path minted it, not when it was written. Nothing in the system reads a date. Only new rows are scoped, and there is no legacy resolution map. This is byte-free because `global_ledger::highest_pl_id_for` and `rows_already_present` scan with `str::strip_prefix` on `format!("PL-{}-", paper_id)` — a literal byte prefix, not a regex — so the two key spaces do not alias in either direction: `"PL-000.000-1".strip_prefix("PL-000-")` is `None` and `"PL-000-1".strip_prefix("PL-000.000-")` is `None`. `global_ledger.rs` therefore needed no code change, only doc.

**The one consequence this introduces.** A paper that already has flat rows starts a SECOND, INDEPENDENT counter at 1 under its scoped key, so one ledger can hold two rows bearing ordinal 1 for the same paper:

```text
PL-009-1 | legacy a
PL-009-2 | legacy b
PL-009-3 | legacy c
PL-009.000-1 | new scoped row      <- second ordinal 1 for the same paper
PL-009-4 | flat continues
PL-009.000-2 | scoped continues
```

The two counters advance independently thereafter. An operator reading a ledger must know this; it is pinned by `tests/global_pl_block_scoped_by_programme.rs::flat_legacy_rows_do_not_seed_the_scoped_counter` and documented at `crates/core_rip_papers/src/global_ledger.rs`.

**What the refusal now reports.** `CarrierError::DuplicatePaperIds` is unchanged and still fires on a genuinely ambiguous carrier: scoping separates papers ACROSS programmes and cannot separate two papers under ONE programme, nor two under the corpus root. `tests/carrier_live_shape_regression.rs` carries that negative control alongside the live-shape mirror, so the file cannot pass by the guard having been deleted. `tests/carrier_duplicate_paper_id.rs` still refuses all four historical fixtures, now under their self-scoped ids (`001.001`, `070.070`, `993.993`).

**Measured after the change**, by the opt-in falsifier `cargo test -j 1 -p core_rip_papers --test carrier_live_shape_regression -- --ignored`: the live `research/published/` root enumerates **86 papers, pairwise-distinct scoped ids, `Ok`** — where it previously always returned `DuplicatePaperIds`. That figure agrees with the §1 census of 86 enumerated elements. It is a measured local `cargo test` result, not a CI-gated one; Actions remains disabled repository-wide.

**The packet gate reads ZERO packet bytes.** Passage of the repository packet gate is not validation of this packet. `scripts/packet_gate.py` matches staged **path names** via `git diff --cached --name-only`; it never opens the packet. An empty, contradictory, absent, or deleted packet all satisfy the gate as long as the mapped path is staged or a `Packet-Ref:` trailer names it. A reader must not infer that gate passage means this packet's contents were checked.

**Not discharged here.** Three pre-existing PL-key ownership defects — the non-prefix-free `strip_prefix`, letter-ordinal invisibility, and the `highest_pl_id_for` / `rows_already_present` ownership disagreement — are recorded with measured evidence and reachability in `crates/core_rip_papers/docs/pl_key_ownership_findings_20260722.md`. They are pre-existing at base `93952cc7c` and are NOT fixed here (operator ruling R4: record separately, fix separately). The exact-census tripwire (P1-8 S4) and the legacy flat-id resolution study (P1-8 S3) are separate sagas; the live falsifier above asserts a floor (`>= 80`), deliberately not a pin, so it does not become a second census gate that fires on every new paper.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** The manual `/rip-papers` workflow; the mixed on-disk paper-folder shapes; per-paper `*_Claim_Ledger.md` files; and global `proof_ledger_<YYYYMMDD>.md` rows keyed `PL-<paper>-<n>`. The implemented Rust owners are `core_rip_papers` for structural/closure evidence, `core_rip_papers_runtime` for the domain adapter, `core_pipeline::gtoc_gtla` for exact Phi_1/Gamma_2/trichotomy/checked packets, `core_representation::RoutedSeed` for the Symbol Game candidate, and `core_certifiers` for the sole authority bridge.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Gauge moves that preserve paper content: whitespace and CRLF/LF normalization in companion files; folder-name canonicalization `Title With Spaces` $\leftrightarrow$ `Title_With_Underscores` under the published convention (`Title_Case_With_Underscores`); idempotent Title_Case rewriting of the `*_Claim_Ledger.md` frontmatter; idempotent date stamping (`Get-Date -Format 'yyyy-MM-dd'`); idempotent re-emission of the local proof-obligation table from the per-paper claim ledger when the underlying claim set is unchanged. None of these moves change PL-IDs that already exist in `proof_ledger_<YYYYMMDD>.md`; PL-ID renumbering is **not** a $d_0$ move.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):**

1. **Naming drift.** Folder names oscillate between `000_primitive_axiomatics/` (spaces) and `002_the_sentinel_boundary/` (spaces + commas + dashes); some siblings use underscores. The skill never enforces a canonical form.
2. **Claim_Ledger schema drift.** The Title_Case frontmatter block (`title`, `subtitle`, `author`, `date`) is human-typed each rip; multi-paper runs introduce trailing-whitespace, mixed-case key, and date-format defects.
3. **PL-ID non-monotonicity.** Manual writers can collide on `PL-<paper>-<n>` numbering. The Rust path therefore requires one kernel-locked, process-global allocation critical section.
4. **No structural validation gate.** Nothing checks that every paper Claim_Ledger entry tagged `LEAN4` actually shows up in the day's global ledger, or vice versa.
5. **Authority bleed risk.** A downstream consumer could treat a markdown row or product-local terminal stamp as authority. The core CLI stays diagnostic; canonical authority requires `certify_checked_packet` through the explicit runtime wrapper.

These defects manifest as `CochainPrimitiveDifference` entries on the `(paper folder, companions, global ledger)` cochain.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two ripped-paper states are gauge-equivalent iff (a) folder names differ only by the canonical `space $\leftrightarrow$ underscore` normalization the convention already names; (b) Claim_Ledger frontmatter differs only by whitespace, key-case, or date re-stamping that does not change the date value; (c) the global ledger entries differ only by reordering within a single paper's contiguous PL-block (PL-IDs themselves are preserved). Anything that changes a PL-ID assignment, adds or removes a Claim_Ledger row, or changes a claim type tag (`[PROVEN]`, `[CONJECTURE]`, `[LEAN4]`, etc.) is **not** ZeroRel.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** After ZeroRel collapse, the residual class is exactly the one called out by the brief:

> A deterministic CLI that takes a paper path and (a) folderizes (canonical name), (b) writes a Title_Case `*_Claim_Ledger.md` against a fixed schema, (c) appends `PL-<paper>-<n>` entries to `proof_ledger_<YYYYMMDD>.md` under a process-global, monotonic counter, with all schema gates rejecting drift.

This residual was genuinely non-removable by the original $d_0$: idempotent normalization alone could not supply a new ledger-row emission rule or a process-global PL-ID broker. The delivered carrier now includes the CLI, deterministic normalization/emission functions, `ProcessGlobalPlIdBroker`, exact closure certificates, and the downstream shared-runtime adapter.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Cross-document closure across (i) the per-paper Claim_Ledger and (ii) the day's `proof_ledger_<YYYYMMDD>.md`. Concretely: every `[LEAN4]` or `[OPEN]` row in the Claim_Ledger must close to a `PL-<paper>-<n>` row in the global ledger, and conversely every `PL-<paper>-<n>` row in the global ledger must trace back to a typed Claim_Ledger row in that paper folder. `d_1` also checks the triple overlap when more than one paper is ripped on the same day: PL-IDs across papers must be disjoint within a `paper` namespace and monotone within each `paper` namespace.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass) — per defect (A1):** `core_functional::ExactGamma2Result` over the `(per-paper ledger, global ledger)` cochain, evaluated per defect within the same 2-window.

| Defect | $\Gamma_2$ | Witness |
|---|---|---|
| D1 Naming drift | $\Gamma_2 = 0$ | Folder name is local-to-folder; no cross-document cocycle, so closure across the `(folder, companions, global ledger)` overlap is vacuous for D1. |
| D2 Claim_Ledger schema drift | $\Gamma_2 = 0$ | Frontmatter is local to the per-paper companion; schema drift does not couple two cochain neighbourhoods. |
| D3 PL-ID non-monotonicity | $\Gamma_2 > 0$ before repair; $0$ after replay | `global_pl_id_broker` starts four real processes over two paper namespaces and proves unique full PL IDs plus monotone `{1,2}` allocation in each namespace. |
| D4 No structural validation gate | $\Gamma_2 > 0$ | `[LEAN4]`/`[OPEN]` Claim_Ledger rows exist without matching `PL-<paper>-<n>` (and vice versa); the `d_1` round-trip across `(Claim_Ledger, global ledger)` fails to close. |
| D5 Authority bleed risk | $\Gamma_2 = 0$ | Authority is not a closure coordinate. The core dependency firewall excludes certifier/product-terminal crates; the downstream companion exposes only the checked-packet certifier bridge. |

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass) — per defect (A1):** `core_functional::VerifiedExactPhi1` on the rip-papers carrier, evaluated by the shared exact runtime. Structural drift and claim-to-PL mismatch are composed as a direct-sum exact complex; no app-local trichotomy is authoritative.

**D4 closure $\Phi_1$ is WITNESSED, not injected (M1).** `closure::build_closure_complex` constructs a real exact-rational complex over the *union of identifiers* $U = \{\text{claim\_id} : \texttt{[LEAN4]}/\texttt{[OPEN]}\} \cup \{\text{pl\_id}\}$: $d_0$ is the genuine claim$\leftrightarrow$PL-ID incidence (each bound id gets a unit-vector gauge column; an unbound id has an all-zero $d_0$ row and cannot be repaired), and $d_1$ is the closure row that annihilates $\operatorname{im}(d_0)$ so $d_1 d_0 = 0$. Hence $\Phi_1 = \min_\alpha \lVert \omega - d_0\alpha \rVert_1$ is **computed** and equals the count of unbound identifiers. Binding is by **identity, not cardinality**: a cardinality-matched but id-mismatched input (3 claims, 3 non-corresponding PL ids) yields $\Phi_1 = 6 > 0$ (negative control in `tests/closure_phi1.rs`), and a matched bijection yields $\Phi_1 = 0$.

| Defect | $\Phi_1$ (current) | $\Phi_1$ (target) | Witness |
|---|---|---|---|
| D1 Naming drift | $\Phi_1 > 0$ | $\Phi_1 = 0$ | `folderize` is idempotent and reduces every space/underscore variant to canonical `NNN_Title_With_Underscores/`; the residual class collapses to the canonical name (exact repair under $d_0$ once the sub-mechanism exists). |
| D2 Claim_Ledger schema drift | $\Phi_1 > 0$ | $\Phi_1 = 0$ | `emit_claim_ledger` writes a fixed Title_Case frontmatter from a typed schema; idempotence test on a conformant ledger is the byte-equivalence witness. |
| D3 PL-ID non-monotonicity | $\Phi_1 > 0$ before brokered emission | $\Phi_1 = 0$ after replay | `ProcessGlobalPlIdBroker` serializes the read/allocate/rename cycle across processes; four-process/two-paper acceptance evidence is nonvacuous. |
| D4 No structural validation gate | $\Phi_1 > 0$ | $\Phi_1 = 0$ | `d_1` closure check binds every `[LEAN4]`/`[OPEN]` Claim_Ledger row to a `PL-<paper>-<n>` row and back; failure raises `ExactGamma2Result`-non-zero (D3/D4 share this gate). |
| D5 Authority bleed risk | not a Phi_1 coordinate | not a Phi_1 coordinate | The CLI has `AuthorityEffect::None`; only `core_rip_papers_runtime::certify_checked_rip` can delegate a checked exact repair to the canonical certifier. |

10. Classify System State
-------------------------

**Classification — shared exact runtime.** The first four defect coordinates feed one `GtocExactInput`; `evaluate_exact` alone produces `ExactRepair`, `StabilizedSurvivor`, or `OpenObstruction`. The fifth item is an authority firewall, not a competing classifier.

| Defect | Class |
|---|---|
| D1 Naming drift | Exact repair (no lift): `folderize` is a $d_0$-idempotent normalization once the canonical rule is implemented. |
| D2 Claim_Ledger schema drift | Exact repair (no lift): `emit_claim_ledger` against a fixed typed schema is a $d_0$-idempotent normalization. |
| D3 PL-ID non-monotonicity | `OpenObstruction` before brokered emission; `ExactRepair` after brokered, replayed emission. |
| D4 No structural validation gate | `OpenObstruction` for any symmetric-difference PL identity; `ExactRepair` only for an exact identity match. |
| D5 Authority bleed risk | Outside the obstruction trichotomy: core output is evidence-only and the certifier remains a separate gate. |

D3 and D4 required a structural extension because the manual loop had no atomic issuer or exact identity closure. The delivered `RipPapersFace`, broker, and runtime companion provide that extension without introducing another Phi_1/Gamma_2 implementation.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift / Structural Extension):** Introduce a new Rust binary crate `core_rip_papers` (workspace member under `engine/`) whose public surface is one `FaceLambda` in the DDA sense:

$$
\Meta \;=\; \mathtt{FaceLambda}\Big(\;\mathtt{RipPapersFace}\;\Big)\colon\quad
(\text{paper\_path},\,\text{date})\;\longmapsto\;
\big(\,\text{canonical\_folder},\;\text{claim\_ledger},\;\text{global\_pl\_block}\,\big)
$$

with the lift carrying a `NonDestructiveExtensionCertificate` and `FiniteLambdaStepCertificate`. The core CLI emits diagnostic evidence only. `core_rip_papers_runtime` combines the three structural coordinates with the exact claim-to-PL complex, binds the manifests, and calls `core_pipeline::gtoc_gtla::evaluate_exact`. A product `terminalize_row` result is not canonical authority. Only `certify_checked_rip`, with a packet-bound `DescentWitness` and decided `IsAuth`, delegates to `certify_checked_packet`.

**Meta licence — Oracles required (A3): none.** This packet imports no representation theorems, no external mathematical witnesses, and no transformations licensed outside the declared finite 2-window. Every operation lives inside the carrier `(paper folder, companions, global ledger)`. No sub-claim's terminal status is `OracleNeeded`.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** The execution sequence, all backed by DDA contracts already in `core_discrete_deformation_algebra`. DDA letters are drawn only from the canonical alphabet **{E, R, C, I, Meta/Lambda, D, M, T}** (A5):

1. **`D` — Descent / re-index ($d_0$ side).** Read the paper folder; build a `CochainPrimitiveDifference` over the `(folder name, companion files, claim ledger frontmatter)` cochain via `core_homology::CochainComplex::d0`. Apply $d_0$ gauge moves: canonicalize folder name; normalize Claim_Ledger frontmatter; stamp the date.
2. **`R` — Residual projection.** Project to `core_homology::QuotientSpace` to expose the irreducible residual (the structural ledger emission).
3. **`E` — Exact repair (D1, D2).** Apply the idempotent normalizers `folderize` and `emit_claim_ledger` to discharge D1 (naming drift) and D2 (Claim_Ledger schema drift); both are $d_0$-exact under ZeroRel.
4. **`Meta` (a.k.a. `Lambda`) — Lift / structural extension (`RipPapersFace`).** Run the lambda and allocate the PL block through `ProcessGlobalPlIdBroker`, whose kernel advisory lock covers one atomic read/allocate/rename critical section. Emit the NDEC and finite-lambda-step evidence.
5. **`C` — Context exposure ($d_1$ closure check).** Build the exact identity-based closure complex, direct-sum it with folder/frontmatter/ledger coordinates, and pass one bound `GtocExactInput` to the shared evaluator.
6. **`I` — Integration / DDA-log append.** Append the ordered step record to the delivered finite-lambda ledger surface.
7. **`M` — Materialize / firewall.** The core materializes evidence and has no certifier dependency. The runtime companion may cross the certifier boundary only through `certify_checked_rip`.
8. **Symbol Game candidate adapter.** `rip_symbol_game_candidate` emits a `PacketFamily::Symbol` `RoutedSeed` with `EvidenceCeiling::BoundaryChecked`, `OraclePolicy::Forbidden`, no transforms, and an explicit `authority_effect: none` payload.

`T` is not executed inside the diagnostic core. The downstream companion first produces a checked exact evaluation; canonical authority is possible only at the certifier gate and only for `ExactRepair`.

13. Terminal Status
-------------------

**Runtime status: RUNTIME-CLOSED (2026-07-17).** Product-local `RipPapersTerminalStatus::Repaired` is a diagnostic projection only. Canonical status comes from `GtocGtlaEvaluation`; canonical authority remains separately gated.

| Defect | Current | Target | Seal Condition |
|---|---|---|---|
| D1 Naming drift | `OpenObstruction` when nonzero | `ExactRepair` after normalization | Shared direct-sum replay reports exact Phi_1/Gamma_2; `runtime_adapter::structural_drift_and_closure_share_one_exact_runtime`. |
| D2 Claim_Ledger schema drift | `OpenObstruction` when nonzero | `ExactRepair` after normalization | Same shared replay and bound manifest; no local classifier. |
| D3 PL-ID non-monotonicity | `OpenObstruction` before emission | `ExactRepair` after brokered replay | `global_pl_id_broker::process_global_broker_is_disjoint_across_paper_namespaces`. |
| D4 Claim-to-PL mismatch | `OpenObstruction` on symmetric difference | `ExactRepair` on identity match | Exact core certificate is consumed, not rebuilt, by `rip_paper_gtoc_exact_input`. |
| D5 Authority bleed risk | evidence only | authority only if separately licensed | `certify_checked_rip` delegates to the sole checked-packet bridge and rejects mismatched witnesses and non-authority-bearing statuses. |

**Closed runtime deferrals and evidence:**

* `runtime-closed: PL-ID-RACE-MULTI` — `ProcessGlobalPlIdBroker` plus the four-process/two-paper test proves globally unique full IDs and monotone per-paper namespaces.
* `runtime-closed: GT-TOWER-VARIANT` — `load_gt_tower_variant` and `gt_tower_exact_input` map `theorem_ledger.md` and `math_spine.md` presence into two exact coordinates; missing evidence remains `OpenObstruction`.
* `runtime-closed: SYMBOL-GAME-ADAPTER` — `rip_symbol_game_candidate` emits candidate-only, boundary-checked, no-oracle, no-transform evidence and no authority token.
* `verified-boundary: LEAN-OBLIGATION-VERIFY` — the historical 2026-07-17 receipt records `lake build CoreCosmology` passing (8558 jobs) with axiom-free Paper 000c red-team/Sentinel/MKS/survivor theorem receipts in `crates/core_rip_papers_runtime/docs/paper000c_lean_verification_20260717.md`. After the ownership migration, the current equivalent gate is `lake build PrimitiveAxiomatics SentinelBoundary`; the historical command is not a live target.

The Lean build does not prove open rows. `PL-000c-1`, `PL-000c-3`, `PL-000c-7`, `PL-000c-9`, and `PL-000c-11` remain explicit research or hardening obligations.

For an exact repaired packet, the sole domain seal is `core_rip_papers_runtime::certify_checked_rip(evaluation, packet_bound_witness, is_auth)`. A product `Decision::Certified`, local `Repaired` enum, markdown row, or successful Lean build does not substitute for that gate.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_rip_papers_runtime::evaluate_rip_paper` and `evaluate_gt_tower` construct exact inputs and call `core_pipeline::gtoc_gtla::evaluate_exact`; the runtime adapter test and process-global PL-ID broker are present. Production convergence and a separately promoted cross-lane receipt remain owned by `S16-005`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest; the historical `runtime-converged` marker does not seal the lane.
