# pilot_0000000 — Linear Algebra (Rung 1)

**AuthorityEffect:** None.  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Task Family:** `linear_algebra`  
**Host Checker:** `PFP-01-EXACT-LINALG`  
**Structure Delta Metric:** `exact_rational_delta`  

---

## 1. Description & Protocol Execution
This pilot implements a hermetic, oracle-grounded evaluation instance for `linear_algebra` under difficulty rung `1`. Ingress stimuli are compiled into typed `$P^*$ envelopes via`p_star_builder.py` according to SPK-001. Model outputs are strictly sanitized by `pilot_response_sanitizer.py` to preserve verbatim byte custody while recording non-schema commentary to `residual_text_ledger.json`.

Host gate verification evaluates candidate proposals against sovereign mathematical truth, distinguishing exact solutions from false certainty and malformed inputs.

---

## 2. Claim Hygiene Envelope

### 2.1 What This Pilot Supports
- Supports that the host evaluation harness deterministically computes ground truth for `linear_algebra` and enforces the `PFP-01-EXACT-LINALG` gate without data leakage.
- Supports that `$P \mapsto P^*$ assembly under SPK-001 constructs a valid`PromptPacketV0_1` envelope preserving root lineage and containment cardinality.
- Supports that the shared sovereign specifications (`spec.yaml`, `seed.yaml`, `prompt_template.yaml`, `testplan.yaml`) sit at the pilot root, while all trial stimulus prompts and their associated model responses are decomposed into granular, self-contained test capsules under `tests/test_00/` through `tests/test_30/`, with aggregate comparison reports and CoT mining matrices persisted to `misc/`. `prompt_template.yaml` and instantiated $P^*$ prompts natively specify `lineage` (`prompt_id`, `generation_id`, `family_id`, `parent_id`) and active `guidance` (`rules`, `antibodies`, `antipatterns`, `helpful_patterns`).
- Supports that live manual dispatch of `p_star.yaml` to DeepSeek V4 yielded a schema-valid `PromptResponse` under SPK-001 with exact mathematical solution ($x + y = 3$) and compliant claim hygiene fields (`tests/test_11/response.yaml`).
- Supports that `pilot_response_sanitizer.py` strips markdown code fences, enforces duplicate key rejection, and logs structure leakage debt.
- Supports that at least four distinct compiled semantic mutants are caught and killed by the test oracle.

### 2.2 What This Pilot Does NOT Support
- Does **NOT** support any claim that LLMs universally or reliably solve `linear_algebra` problems. Offline fixture dry runs verify software plumbing and host gates only; they provide zero empirical evidence regarding model capability or behavior.
- Does **NOT** authorize live provider dispatch without explicit budget allocation and authentic cryptographic receipts.

### 2.3 Narrowest Defensible Claim
- Under the declared assumptions, the host verification suite deterministically distinguishes valid mathematical solutions from invalid, malformed, or ambiguous proposals on the scoped `linear_algebra` benchmark, enforces zero-spend boundaries during offline execution, and catches 100% of tested mutant discrepancies.

### 2.4 Next Test Needed
- Deploy live model trial through `live_gateway` under strictly preflighted budget constraints (`budget <= $0.001`) with authentic provider receipts to record empirical proposal fidelity across model classes.

---

## 3. Chain-of-Thought (COT) Mining Analysis & Schema Review

### 3.1 Schema Review
- **Catalog Structure:** [`omega_engine_pfp/infrastructure/yaml/pilots/`](../../infrastructure/yaml/pilots/) serves as the canonical catalog for specification, seed, $P^*$, rewrite test plan, response, and comparison contracts.
- **Eleven Seed Dialects:** The eleven dialects (plain-text through proof-style) constitute the ingress surface forms that the scratchpad treats as the complete task carrier.
- **Response Contract as Primary Lever:** The schema contract `pfp.pilot-response.v1` defines structural admittance. `PromptResponsePayload` requires `derived_under_policy: SPK-001`, `summary` (`narrowest_defensible_thesis`, `evidence_scope`, `next_concrete_test`), and `process_integrity`. It originally omitted a designated checker answer slot, with `sections` left empty.
- **Trace Extraction:** The miner loads field names directly from the schema. In baseline traces without the answer slot, correct numeric evaluations were frequently placed in `narrowest_defensible_thesis` leaving the gate status `MALFORMED`, whereas `seed_plain` directly returned `{"answer": 3}` and evaluated as `ACCEPTED`. `response.yaml` is skipped during mining when `reasoning_content` is absent.

### 3.2 Mined Candidates

| Kind | Id | Traces | Answer matches |
|---|---|---|---|
| Skill | `skill_substitute_then_report` | 7 | 7 |
| Skill | `skill_parse_before_arithmetic` | 7 | 7 |
| Antiskill | `antiskill_schema_displacement` | 11 | 4 |
| Antiskill | `antiskill_answer_channel_displacement` | 5 | 2 |
| Antiskill | `antiskill_template_withdrew_license` | 2 | 1 |
| Antiskill | `antiskill_corpus_invention` | 2 | 0 |
| Antiskill | `antiskill_clarification_retreat` | 7 | 0 |
| Antiskill | `antiskill_ghost_hypothesis_stack` | 11 | 0 |
| Antiskill | `antiskill_unbounded_scratchpad` | 12 | 0 |

The two skills correspond to the same seven traces (`seed_plain`, `rewrite_01_plain`, `rewrite_02_plain`, `p_star_seed`, `p_star_rewrite_01`, `p_star_rewrite_04`, `p_star_rewrite_05`). In these traces, the scratchpad parses the carrier, outputs a single `Substitute` or `=>` statement, and reports the resulting value.

### 3.3 Candidate Antibodies (`admitted: false`)
- `ab_cot_answer_channel` (5 traces): The scratchpad concludes that the response schema lacks a field to hold the scalar answer.
- `ab_cot_license_conflict` (2 traces): `p_star_rewrite_01` and `p_star_rewrite_02` perform substitution and subsequently refuse under `numeric_license_rule` / `forbidden_unlicensed_interpretations` declared in the prompt template.
- `ab_cot_corpus_invention` (2 traces): Extraneous benchmark corpora are posited by the model (`rewrite_03_plain` invents BigBench; `rewrite_10_plain` invents ARC), despite being absent from source prompts.
- `ab_cot_ghost_hypothesis` (11 traces): At least 6 conjecture markers (`Maybe`, `Could be`, `Alternatively`, `Hmm`) accumulate without a substitution certificate line (`rewrite_08_plain` registers 105 markers).
- `ab_cot_unbounded_scratchpad` (12 traces): Reasoning token consumption reaches or exceeds 1,000 tokens while yielding a null extracted answer (e.g., `rewrite_06_plain` at 13,902 tokens and `rewrite_08_plain` at 12,019 tokens).
- *Pattern Retention:* A license phrase echoing the template rule without a substitution certificate remains cataloged as pattern `license_rule_echo` (`p_star_rewrite_06`, `_07`, `_10`) and is not promoted to an antiskill.

### 3.4 Five Prompt Manipulations (Rules)
1. `rule_name_the_checker_field` (applies to all 11 $P^*$ traces): Explicitly declare the checker field name in the task envelope so proposals populate `answer` rather than burying values in `narrowest_defensible_thesis`.
2. `rule_license_the_operators` (`p_star_rewrite_01`, `_02`): When the template restricts unlicensed arithmetic, explicitly license the primitive arithmetic operators (`+`, `-`, `*`) used by the carrier.
3. `rule_carrier_is_the_whole_task` (11 traces): Explicitly state that the provided surface form is self-contained to suppress external benchmark guesses (BigBench, ARC, Dyck).
4. `rule_cap_the_scratchpad` (12 traces): Bound reasoning consumption at 1,000 tokens unless a concrete substitution certificate has been registered.
5. `rule_require_one_substitution_line` (11 traces): Mandate exactly one substitution step before emitting schema or domain commentary.

---

## 4. Replayable Test Registry (`test_00` through `test_30`)

In accordance with [MODUS_OPERANDI.md](../../../omega_engine_adversary/tests/pilots/MODUS_OPERANDI.md), every test in `pilot_0000000` is housed in a dedicated subfolder (`tests/test_XX/`) containing `test_spec.yaml`, `input.yaml`, and `response.yaml`:

### 4.1 Plain Ingress Traces (Generation 0)
- [`tests/test_00`](tests/test_00): `seed_plain` — `ACCEPTED` ($x+y=3$, answer: 3).
- [`tests/test_01`](tests/test_01): `rewrite_01_plain` (Tier H) — `MALFORMED` (answer inside thesis).
- [`tests/test_02`](tests/test_02): `rewrite_02_plain` (Tier D) — `MALFORMED` (answer inside thesis).
- [`tests/test_03`](tests/test_03): `rewrite_03_plain` (Obfuscated) — `WRONG_ANSWER` (unlicensed BigBench conjecture).
- [`tests/test_04`](tests/test_04): `rewrite_04_plain` (Tier S) — `MALFORMED` (answer inside thesis).
- [`tests/test_05`](tests/test_05): `rewrite_05_plain` (MSS-0 Proof-Style) — `MALFORMED` (answer inside thesis).
- [`tests/test_06`](tests/test_06): `rewrite_06_plain` (S(n) Obfuscated) — `WRONG_ANSWER` (unbounded scratchpad 13,902 tokens).
- [`tests/test_07`](tests/test_07): `rewrite_07_plain` (S(n) Obfuscated) — `WRONG_ANSWER` (unbounded scratchpad 8,245 tokens).
- [`tests/test_08`](tests/test_08): `rewrite_08_plain` (Gen Wire Obfuscated) — `WRONG_ANSWER` (ghost hypothesis 12,019 tokens).
- [`tests/test_09`](tests/test_09): `rewrite_09_plain` (Sn Wire Retraction) — `WRONG_ANSWER` (unbounded scratchpad 7,330 tokens).
- [`tests/test_10`](tests/test_10): `rewrite_10_plain` (MSSN Wire ARC) — `WRONG_ANSWER` (ARC conjecture 9,634 tokens).

### 4.2 Templated $P^*$ v1 Traces (Generation 1, `HP_RESPONSE_ANSWER_SLOT`)
- [`tests/test_11`](tests/test_11): `p_star_seed` — `ACCEPTED` (answer: 3).
- [`tests/test_12`](tests/test_12): `p_star_rewrite_01` (Tier H) — `ACCEPTED` (answer: 3).
- [`tests/test_13`](tests/test_13): `p_star_rewrite_02` (Tier D) — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, compliant under license rule).
- [`tests/test_14`](tests/test_14): `p_star_rewrite_03` (Obfuscated) — `WRONG_ANSWER` (BigBench guessing).
- [`tests/test_15`](tests/test_15): `p_star_rewrite_04` (Tier S) — `ACCEPTED` (answer: 3).
- [`tests/test_16`](tests/test_16): `p_star_rewrite_05` (MSS-0 Proof-Style) — `ACCEPTED` (answer: 3).
- [`tests/test_17`](tests/test_17): `p_star_rewrite_06` (S(n) Obfuscated) — `WRONG_ANSWER`.
- [`tests/test_18`](tests/test_18): `p_star_rewrite_07` (S(n) Obfuscated) — `WRONG_ANSWER`.
- [`tests/test_19`](tests/test_19): `p_star_rewrite_08` (Gen Wire Obfuscated) — `WRONG_ANSWER`.
- [`tests/test_20`](tests/test_20): `p_star_rewrite_09` (Sn Wire Retraction) — `WRONG_ANSWER`.
- [`tests/test_21`](tests/test_21): `p_star_rewrite_10` (MSSN Wire ARC) — `WRONG_ANSWER`.

### 4.3 Generation 2 Obfuscated Runs (`rule_name_the_checker_field` + `rule_carrier_is_the_whole_task`)
- [`tests/test_22`](tests/test_22): `p_star_rewrite_03_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).
- [`tests/test_23`](tests/test_23): `p_star_rewrite_06_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).
- [`tests/test_24`](tests/test_24): `p_star_rewrite_07_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).
- [`tests/test_25`](tests/test_25): `p_star_rewrite_08_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).
- [`tests/test_26`](tests/test_26): `p_star_rewrite_09_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).
- [`tests/test_27`](tests/test_27): `p_star_rewrite_10_v2` — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, 100% compliant refusal).

### 4.4 Generation 3 & 4 Operator Licensing Shift (`rule_license_the_operators`)
- [`tests/test_28`](tests/test_28): `p_star_rewrite_06_v3` (Matrix/Vector System) — `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`, model computed $x=1, y=2, ans=3$, but halted on unlicensed `neg` token).
- [`tests/test_29`](tests/test_29): `p_star_rewrite_09_v3` (S(n) Retraction Down-Map) — **`ACCEPTED`** (answer: 3, intermediate witness verified).
- [`tests/test_30`](tests/test_30): `p_star_rewrite_06_v4` (Matrix/Vector System with `neg` license) — **`ACCEPTED`** (answer: 3, intermediate witness verified).

---

## 5. Replay Instructions for Follow-on Users

To repeat our work and replay the evaluations:
1. **Run Unit & Pilot Suite Tests:**
   ```bash
   py -3.12 -m pytest omega_engine_pfp/tests/test_pilot_suite.py omega_engine_pfp/tests/test_cot_miner.py -v
   ```
2. **Replay Chain-of-Thought Miner:**
   ```bash
   py -3.12 -m omega_engine_adversary.tests.pilots.cot_miner
   ```
3. **Inspect Granular Test Results:**
   Every test directory under `tests/test_00/` through `tests/test_30/` holds the exact input prompt (`input.yaml`), response document (`response.yaml`), and typed outcome specification (`test_spec.yaml`).

