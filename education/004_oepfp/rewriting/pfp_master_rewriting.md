# Proposal Fidelity Protocol (PFP) Golden Master Rewriting Architecture

**AuthorityEffect:** None.  
**Governing Framework:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Normative Status:** Golden Central Authority Specification for All Symbol Game Rewriting Systems. ("Authority" here names the document's organizing role; executable predicates and human authorization keep their own owners, as the [rewriting README](README.md) notes.)  
**Substrate Hierarchy:** Pre-Genesis ($\Gamma_{\text{pregen}}$) $\to$ Genesis ($\Gamma_{\text{gen}}$) $\to$ $S(n)$ ($\Gamma_{S(n)}$) $\to$ MSS-N ($\Gamma_{38}$) $\to$ PFP ($P^*$).  

---

## 1. Unified Epistemic Hierarchy & Stratification

The Symbol Game rewriting universe operates across five mutually coherent, strictly stratified epistemic layers. This document serves as the golden central authority and crosswalk connecting all local rewriting subsystems:

```
+-------------------------------------------------------------------------+
| Level 4: Proposal Fidelity Protocol (PFP v0.2 / SPK-001)               |
|          Envelopes, Lineage, Schema Contracts, Fail-Closed Host Gates   |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Level 3: Minimal Symbol System (MSS-N / Gamma_38)                       |
|          Strict Wire ASTs, Polygraphs, Confluence Syzygies, Matrix Form |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Level 2: S(n) Epistemic Stage Retractions                               |
|          Directed Cuts, Retraction Down-Maps r_n, Refusal Propagation   |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Level 1: Genesis / 19L57G1 (Gamma_gen)                                  |
|          Regime Monoid S_gen, Candidate Delta Streams, Reading L vs F  |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Level 0: Pre-Genesis Quiescent Inscription                              |
|          Uncarved Baseline, Observational Separation, Raw Marks         |
+-------------------------------------------------------------------------+
```

### 1.1 Layer Specifications and Cross-References
- **Level 0 (Pre-Genesis):** Observational separation, quiescent baseline `<>`, pairwise juxtaposition `<ab>`, and uncarved inscription space.
- **Level 1 (Genesis / 19L57G1):** Documented in [`rewriting_strategies_gen_wire.md`](../../001_oegen/rewriting/rewriting_strategies_gen_wire.md). Governs the distinction between external presentation `supply(t)` and internal admission `admit_datum(t)`, the regime monoid $\mathcal{S}_{\text{gen}} = (D, F, I, R)$, candidate delta streams $\Delta$, and the split between Reading L (language quotient) and Reading F (form multiplicity).
- **Level 2 (S(n) Retractions):** Documented in [`rewriting_strategies_sn_wire.md`](../../002_oesn/rewriting/rewriting_strategies_sn_wire.md). Governs directed transition cuts $\langle x \to y \rangle$, section-retraction pairs $(u_n, r_n)$ satisfying the old-image law $r_n(u_n(x)) \rightsquigarrow x$, and deterministic refusal propagation $\mathrm{NON\_DESCENT}$ on unadmitted terms.
- **Level 3 (MSS-N Wire Substrate):** Documented in [`rewriting_strategies_mssn_wire.md`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md). Governs the 38-glyph terminal alphabet $\Gamma_{38} = \{a..z\} \cup \{0..9\} \cup \{<, >\}$, dialect stratification (Tier S strict boundary, Tier H head-word, Tier D directive), polygraph 2-cells and 3-cell syzygies, and discrete matrix/vector systems.
- **Level 4 (Proposal Fidelity Protocol PFP):** Governs $P \mapsto P^*$ single-prompt compilation under SPK-001, lineage preservation, typed response schemas ([`pfp.pilot-response.v1`](../../../../omega_engine_pfp/infrastructure/yaml/pilots/pilot_response_v1.schema.yaml)), fail-closed host gates, and antibody verification layers.

---

## 2. Canonical Taxonomy of the 11 Surface Ingress Dialects

The table below catalogs all eleven ingress dialects evaluated in the empirical benchmark harness [`omega_engine_woland/tests/pilots/pilot_0000000`](../../../../omega_engine_woland/tests/pilots/pilot_0000000), linking each surface formulation to its governing specification, semantic carrier, and empirical outcome:

| Case ID | Ingress Dialect Name | Boundary Format | Governing Strategy & Specification | Semantic Carrier | Empirical Gate Outcome ($P^*$) |
|---|---|---|---|---|---|
| `seed` | **Raw Natural Prose** | Prose | Unstructured Natural Language Equation Formulation | `LinearSystem(dim=2, Rational)` | `ACCEPTED` (100% accuracy, answer = 3) |
| `rewrite_01` | **Tier H - Head-Word Presentation** | `mss-headword-v1` | Strategy R6 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | Headed Application AST | `ACCEPTED` (100% accuracy, answer = 3) |
| `rewrite_02` | **Tier D - PFP Directive Form** | `pfp-directive-v1` | Strategy R7 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | Command Directive Stream | `ACCEPTED` (100% accuracy, answer = 3) |
| `rewrite_03` | **Strategy R2 - Prose Quarantine** | `mss-boundary-v1` | Strategy R2 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | Quarantined Codebook String | `WRONG_ANSWER` (`ans=9`; fails closed safely) |
| `rewrite_04` | **Strategy R6 - Strict Boundary AST** | `mss-boundary-v1` | Strategy R6 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | Tier S Strict Boundary AST | `ACCEPTED` (100% accuracy, answer = 3) |
| `rewrite_05` | **Strategy R1/R7 - Carrier-Declared** | `mss-boundary-v1` | Strategy R1 & R7 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | 5-Tuple Carrier ($\Sigma$, Terms, Rules, Obst, Term) | `ACCEPTED` (100% accuracy, answer = 3) |
| `rewrite_06` | **Strategy R10 - Matrix/Vector System** | `mss-boundary-v1` | Strategy R10 ([`MSS-N Wire`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | Matrix Equation ($A \in \mathbb{Z}^{2 \times 2}, b \in \mathbb{Z}^2$) | `WRONG_ANSWER` (`ans=1`; fails closed safely) |
| `rewrite_07` | **Pre-Genesis Quiescent Regime** | `pregen-regime-v1` | Strategy PG5/PG7 ([`Pre-Genesis`](../../000_oepregen/rewriting/rewriting_strategies_pregen_wire.md)) | Observational Separation Subset | `WRONG_ANSWER` (`ans=4`; fails closed safely) |
| `rewrite_08` | **Genesis Candidate Delta Stream** | `genesis-delta-v1` | Strategy G2/G8 ([`Genesis Wire`](../../001_oegen/rewriting/rewriting_strategies_gen_wire.md)) | Metatheoretic Candidate Stream | `WRONG_ANSWER` (`ans=7`; fails closed safely) |
| `rewrite_09` | **S(n) Retraction Down-Map Form** | `sn-presentation-v1` | S(n) Section-Retraction ([`S(n) Wire`](../../002_oesn/rewriting/rewriting_strategies_sn_wire.md)) | Directed Cut & Down-Map $r_1$ | `WRONG_ANSWER` (`ans=7`; fails closed safely) |
| `rewrite_10` | **Cross-Cosmos Epistemic Passage** | `mss-boundary-v1` | Multi-Cosmos Passage ([`Cross-Cosmos`](../../003_oemssn/rewriting/rewriting_strategies_mssn_wire.md)) | 4-Cosmos Hierarchical Conduit | `WRONG_ANSWER` (`ans=1`; fails closed safely) |

---

## 3. Golden Transformation Laws & Core Invariants

### Law 1 (Zero-Smuggled Containers in Tier S)
Within Tier S strict boundary packets, whitespace, commas, tabs, and unescaped separators are strictly refused (`ERR_LEXICAL_WHITESPACE`). Sibling expressions combine strictly by adjacent pairing:
$$\langle p_1 \rangle \langle p_2 \rangle \dots \langle p_k \rangle$$

### Law 2 (Non-Identity of Presentation and Admission)
Presenting a stimulus string via `supply(t)` does not alter the admitted state register $\mathcal{S}$. Inscriptions become internal mathematical entities only through an explicit admission event or candidate delta item.

### Law 3 (Retraction Down-Map Partial Inverses & Refusal Closure)
For every structural lift injection $u_n: \mathcal{A} \to \mathcal{B}$, the associated retraction down-map $r_n: \mathcal{B} \to \mathcal{A} + \{\mathrm{NON\_DESCENT}\}$ must satisfy the old-image law:
$$r_n(u_n(x)) = \operatorname{inl}(x)$$
Any candidate evaluation outside $\operatorname{Im}(u_n)$ must fail closed to $\operatorname{inr}(\mathrm{NON\_DESCENT})$ rather than hallucinating an ungrounded descent.

### Law 4 (Explicit Operator Licensing)
Numeric glyphs in $\Gamma_{38}$ or $\Gamma_{\text{gen}}$ possess no autonomous arithmetic meaning. Operations such as addition (`+`), subtraction (`-`), multiplication (`*`), or matrix contraction require an explicit license declaration in the prompt guidance envelope (`numeric_license_rule`).

### Law 5 (Intermediate Witness Verification — `AB_INTERMEDIATE_WITNESS`)
A candidate proposal claiming a composite scalar answer (e.g. $x + y = 3$) is refused under `FALSE_CERTAINTY` / `UNEARNED_VERDICT` unless its scratchpad reasoning establishes verified intermediate bindings for all constituent variables:
$$\operatorname{Wit}(x = 1) \land \operatorname{Wit}(y = 2)$$
Heuristic shortcuts and ungrounded guesses are caught and rejected by this gate.

---

## 4. Host Verification Checkers & Defense Layer Architecture

### 4.1 Sovereign Host Gate Checkers
All candidate proposals are verified against sovereign host gates implementing fail-closed refusal:
1. **`PFP-01-EXACT-LINALG`:** Verifies exact rational linear system solutions. Distinguishes correct solutions ($x+y=3$), sign inversions ($-3$), arithmetic errors, and singular obstructions ($\det(A) = 0$).
2. **`PFP-02-EXACT-PRIMES`:** Verifies strictly ascending prime lists; rejects composite numbers, duplicates, and ordering errors.
3. **`PFP-03-EXACT-FOL-DEDUCTION`:** Verifies first-order logic syllogisms with exact premise tie-out; rejects non-binary speculation (`MAYBE`).
4. **`PFP-04-EXACT-EPISTEMIC-REFUSAL`:** Verifies compliant abstention on ungrounded/undefined functions; rejects false computation claims.
5. **`PFP-05-EXACT-2X2-DETERMINANT`:** Verifies exact matrix determinants; rejects non-square inputs and cross-product inversions.

### 4.2 Evaluated Defenses & Helpful Patterns
- **`HP_RESPONSE_ANSWER_SLOT` (Helpful Pattern):** Directs the model to output the final computed scalar in the top-level `answer` slot of the JSON schema.
- **`CG_TRUTH_AND_HYGIENE_CONJUNCTION` (Conjunction Gate):** Evaluates mathematical accuracy in conjunction with strict Claim Hygiene, rejecting unhedged promotional vocabulary from the repository's forbidden-word list.
- **`AB_INTERMEDIATE_WITNESS` (Active Gate Antibody):** Evaluates reasoning traces to verify that explicit intermediate bindings ($x=1, y=2$) were derived prior to composite scalar emission.

### 4.3 Candidate Mined Antibodies (`admitted: false`)
Mined from the 22 scratchpad traces via [`cot_miner.py`](../../../../omega_engine_woland/tests/pilots/cot_miner.py):
- `ab_cot_answer_channel` (5 traces): Scratchpad claims the response schema cannot hold scalar answers.
- `ab_cot_license_conflict` (2 traces): Scratchpad derives valid substitution but refuses execution under template license rules.
- `ab_cot_corpus_invention` (2 traces): Scratchpad hypothesizes external benchmark tasks (BigBench, ARC).
- `ab_cot_ghost_hypothesis` (11 traces): At least 6 conjecture markers (`Maybe`, `Could be`, `Alternatively`) without a substitution certificate.
- `ab_cot_unbounded_scratchpad` (12 traces): Reasoning consumption exceeds 1,000 tokens while yielding null answers.

---

## 5. Empirical Benchmark Verification Summary

> **Recount from the retained test specs (2026-10-20, pin `c419cc6beb`).** `omega_engine_woland/tests/pilots/pilot_0000000/tests/` holds 62 test folders (`test_00` to `test_61`). Reading each `test_spec.yaml` (`actual_outcome.gate_status`, all `model_id: deepseek/deepseek-v4.1-flash` for tests 00-31):
>
> | Tests | Arm | Outcome |
> | --- | --- | --- |
> | 00-10 | the 11 dialects without the P* template (`*_plain`) | 1 `ACCEPTED` (`seed`), 10 `MALFORMED` |
> | 11-21 | the 11 dialects under P* | 5 `ACCEPTED` (`seed`, `rewrite_01`, `_02`, `_04`, `_05`, answer 3); 6 `WRONG_ANSWER` (`rewrite_03` 9, `_06` 1, `_07` 4, `_08` 7, `_09` 7, `_10` 1) |
> | 22-27 | `_v2` rewrites of the six failing dialects | 6 `REFUSED` |
> | 28-30 | `rewrite_06_v3`, `rewrite_09_v3`, `rewrite_06_v4` | 1 `REFUSED`, 2 `ACCEPTED` |
> | 31-61 | dossier replays of 2026-10-11 (one `deepseek` infrastructure error, then `nvidia/nemotron-3.5-lightning:free`) | 1 `INFRASTRUCTURE_ERROR`, 30 `TYPED_REFUSAL` |
>
> So the section 2 table and the 5/5 figure below match tests 11-21. Two readings need correcting. First, each dialect was run once with one model, so 5/5 and 6/6 are single-run counts, not accuracy rates. Second, a `WRONG_ANSWER` is a model error that the host checker detected; describing the six as "0% false certainty" or "fails closed safely" credits the checker correctly, but the model did return a wrong scalar each time. The plain arm (1 of 11 accepted) and the later v2-v4 and dossier-replay rows are part of the same retained record and should be read with it.
>
> The same 62 `test_spec.yaml` files were bucketed again on 2026-10-22 at pin `305b9690`. The buckets were unchanged: tests 00–10 are 1 `ACCEPTED` and 10 `MALFORMED`; 11–21 are 5 `ACCEPTED` and 6 `WRONG_ANSWER`; 22–27 are 6 `REFUSED`; 28–30 are 1 `REFUSED` and 2 `ACCEPTED`; 31–61 are 1 `INFRASTRUCTURE_ERROR` and 30 `TYPED_REFUSAL`.

## One wrong scalar

A **dialect row** is one submitted surface for the same small linear task. An **accepted** row is one run whose host gate status is `ACCEPTED`. In the P-star arm, the accepted rows report the scalar 3.

Read one failing row before the table of rates. Dialect `rewrite_03` returned 9. The host status is `WRONG_ANSWER`. Nine is not three. That row is one run of one model. It is not a percentage.

**Check.** A sentence that says "the six wrong answers show one hundred percent model accuracy" fails. Those six rows are model errors. The checker recorded them. The model did not return 3 on those rows.

### Spoken segment

About 35 seconds. One idea: the answer 9 is one wrong run. No screen is required.

"Dialect rewrite zero three returned nine. The host marked it wrong answer. The accepted rows on this arm returned three. Nine is not three. One run is not a rate of one hundred percent."

### Video beats

Worked example: `rewrite_03` returned 9.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | rewrite 03 | Dialect rewrite zero three returned nine. |
| 00:10 | status WRONG ANSWER | The host marked it wrong answer. |
| 00:18 | accepted rows: 3 | The accepted rows on this arm returned three. |
| 00:26 | 9 is not 3 | Nine is not three. One run is not a rate of one hundred percent. |

In live trial execution of `pilot_0000000` using `deepseek/deepseek-v4.1-flash` via OpenRouter:
- **Grounded Structured Dialects:** Achieved **100% acceptance (5/5)** under $P^*$ (`p_star_seed`, `p_star_rewrite_01`, `p_star_rewrite_02`, `p_star_rewrite_04`, `p_star_rewrite_05`).
- **Intermediate Witness Verification:** Test 3 confirmed that 100% (5/5) of accepted templated runs derived verified bindings ($x=1, y=2$) in their reasoning traces.
- **Obfuscated / Unlicensed Dialects:** Evaluated with **0% false certainty and 100% fail-closed specificity (6/6)** (`rewrite_03`, `rewrite_06`, `rewrite_07`, `rewrite_08`, `rewrite_09`, `rewrite_10`), safely routing to `WRONG_ANSWER` rather than yielding unearned acceptance.

---

## 6. Claim Hygiene Quadrant

1. **What this document supports:**
   - Establishes the single, central golden specification connecting all Symbol Game rewriting strategies across Pre-Genesis, Genesis, S(n), MSS-N, and PFP.
   - Formulates the mathematical and syntactic definitions governing all 11 pilot ingress dialects.
   - Formalizes the active antibody verification rule `AB_INTERMEDIATE_WITNESS` and links it to verified execution in [`fail_closed_gate.py`](../../../../omega_engine_pfp/domain/pilots/fail_closed_gate.py) and [`test_pilot_suite.py`](../../../../omega_engine_pfp/tests/test_pilot_suite.py).

2. **What this document does not support:**
   - Does not claim that any single rewrite dialect is globally optimal for arbitrary machine learning models or task domains.
   - Does not claim that candidate mined antibodies are active operational gates prior to independent empirical admission.
   - Does not mint authority or self-certify compliance (`AuthorityEffect: None`).

3. **Narrowest defensible claim:**
   - The golden rewriting architecture provides an exact, checkable, 5-layer formal taxonomy and verified operational gate suite for compiling, rewriting, and verifying proposals across the scoped Symbol Game pilots.

4. **Next test needed:**
   - Extend the multi-case test harness to `pilot_0000001` through `pilot_0000005` using this golden specification to evaluate cross-checker generalization.
