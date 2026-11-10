# PFP Pilot Modus Operandi (Operating Procedure)

**AuthorityEffect:** None.  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Normative Status:** Mandatory Standard Operating Procedure for All Empirical Pilots (`pilot_0000000` through `pilot_0000099`).  

---

Current pilot storage is `omega_engine_woland/tests/pilots`. The retained
procedure below describes the original capsule/history conventions; recorded
model IDs and source paths do not grant a new dispatch allowance. Use the
[current Woland/PFP guide](../../../omega_engine_education/documentation/004_oepfp/docs/18_woland_original_challenge_play.md)
for the supported accounted runtime.

## 1. Prime Directives & Invariants

1. **Zero Data Loss & Strict History Retention:**
   - Files and results must never be lost through negligence, truncation, or blind overwrites.
   - When iterating or evaluating new prompt guidance, **never overwrite previous versions**. Retain previous prompt files (e.g. `p_star_rewrite_10.yaml`) and create versioned generations (`p_star_rewrite_10_v2.yaml`, etc.) with explicit lineage records.
2. **Deterministic Replayability:**
   - Any follow-on researcher or autonomous agent must be able to inspect, repeat, and replay every run deterministically from raw inputs to verified receipts.
3. **Fail-Closed Sovereign Verification:**
   - Model claims have zero authority in prose. Acceptance is certified exclusively by executing sovereign host checkers (`PFP-01-EXACT-LINALG`, `PFP-02-GRAPH-FACTS`, etc.) recording typed receipts.
4. **Claim Hygiene Discipline:**
   - All pilot documentation and proposals must strictly avoid unhedged promotional hype vocabulary (`proves`, `guarantees`, `obviously`).

---

## 2. Mandatory File Structure per Pilot

Every pilot directory (`pilot_XXXXXXX/`) must strictly adhere to the following clean root-level and test capsule layout:

```text
pilot_XXXXXXX/
├── spec.yaml                   # Sovereign pilot configuration, task family, host gate checker_id, difficulty rung
├── seed.yaml                   # Single authoritative seed problem statement, carrier, expected outcome
├── prompt_template.yaml        # Most current universal prompt template (lineage, guidance, schema)
├── testplan.yaml               # Declarative testplan mapping test cases, rewrites, and expected outcomes
├── README.md                   # Comprehensive pilot monograph with Claim Hygiene envelope and test registry
├── misc/                       # Aggregated pilot matrices, comparison reports, and COT mining outputs (aggregate only; NO individual trial responses or stimulus files)
└── tests/                      # Granular, replayable test execution directories (test_00 through test_99)
    ├── test_00/
    │   ├── test_spec.yaml      # Typed test metadata (test_id, dialect, expected outcome, gate status)
    │   ├── input.yaml          # Verbatim stimulus input sent to model (plain seed or P* prompt envelope)
    │   ├── response.yaml       # Single associated response document (raw reply, JSON, reasoning, receipt, gate)
    │   ├── [named_prompt].yaml # Optional verbatim named prompt alias (e.g. seed.yaml, p_star_rewrite_06_v4.yaml)
    │   └── [named_resp].yaml   # Optional verbatim named response alias (e.g. response_p_star_rewrite_06_v4.yaml)
    ├── test_01/
    └── ...
```

### Component Details
1. **Root-Level Hygiene (Zero Loose Prompts or Responses):**
   - The pilot root directory MUST NOT contain loose trial prompts (e.g. `p_star.yaml`, `seed_rewrite_*.yaml`, `p_star_rewrite_*.yaml`) or individual model responses (`response_*.yaml`, `response_p_star*.yaml`).
   - Every trial input stimulus and its single associated model response must reside strictly inside its own designated test capsule under `tests/test_XX/`.
   - The baseline compiled $P^*$ prompt for the canonical seed resides in `tests/test_11/p_star.yaml` (with identical `input.yaml`), just as the plain unadulterated baseline seed trial resides in `tests/test_00/`.
   - The root holds only the sovereign shared pilot specifications: `spec.yaml`, `seed.yaml`, `prompt_template.yaml`, `testplan.yaml`, `README.md`, `misc/`, and `tests/`.
2. **`spec.yaml`:**
   Declares the pilot coordinates: `task_family`, `difficulty_rung`, `host_gate.checker_id`, `models`, and folder pointers. Adheres to `pfp.pilot-spec.v1`.
3. **`seed.yaml`:**
   Declares the canonical, unadulterated baseline problem statement. Adheres to `pfp.seed-prompt.v1`. Exactly one authoritative seed per pilot.
4. **`prompt_template.yaml`:**
   The universal $P^*$ prompt template. Contains:
   - `lineage`: Slot declarations (`prompt_id`, `generation_id`, `family_id`, `parent_id`).
   - `guidance`: Rules, antibodies (e.g. `AB_INTERMEDIATE_WITNESS`), antipatterns, helpful patterns (e.g. `HP_RESPONSE_ANSWER_SLOT`).
   - `system_prompt`: SPK-001 policy manifest, grammar constraints, typing rules, claim hygiene firewall.
   - `user_prompt`: Stimulus template slot.
   - `response_schema`: JSON Schema constraining candidate response envelopes.
5. **`testplan.yaml`:**
   Declarative execution testplan mapping each test case ID to its stimulus alias, dialect presentation, and expected outcome.
6. **`README.md`:**
   Must include:
   - Description & Protocol Execution.
   - Four-Point Claim Hygiene Envelope: (1) What it supports, (2) What it does not support, (3) Narrowest defensible claim, (4) Next test needed.
   - Complete Test & Trial Catalog cross-referencing `test_00` through `test_99`.
7. **`misc/` Folder (Aggregate Only):**
   Reserved exclusively for cross-test comparison reports (`comparison_results.yaml`, `comparison_results.md`, `comparison_results_obfuscated_v2.*`, `comparison_results_obfuscated_v3.*`) and COT trace mining registries (`cot_mine.yaml`). Named `misc/` rather than `results/` to prevent LLMs or autonomous agents from dumping individual run results or input files here. Contains an explicit LLM-readable `README.md` instructing models that all individual trial outputs must be placed strictly in `tests/test_NN/`. Individual trial responses and individual test specifications MUST NOT reside in `misc/`; they belong strictly in their respective `test_XX/` directories.

---

## 3. Test Organization Protocol (`test_00` through `test_99`)

To guarantee absolute transparency, zero data loss, and deterministic replayability, tests within each pilot are assigned dedicated, sequential directories from `test_00` up to a maximum of `test_99` (no pilot may exceed 100 tests):

1. **Naming Standard:** Two-digit zero-padded index: `test_00`, `test_01`, `test_02`, ..., `test_99`.
2. **Atomic Test Capsule Requirements:**
   Each test directory is a fully self-contained unit holding exactly one stimulus prompt and its single associated response:
   - **`input.yaml`:**
     The exact stimulus prompt dispatched to the model. For plain-text trials, contains `schema: pfp.seed-prompt.v1` (with `seed_prompt`). For templated $P^*$ trials, contains the complete $P^*$ envelope (`lineage`, `guidance`, `system_prompt`, `user_prompt`, `response_schema`).
   - **`response.yaml`:**
     The single associated response document matching `pfp.pilot-response.v1` (verbatim raw reply, sanitized parsed JSON, reasoning content, cryptographic receipt, and sovereign host gate evaluation).
   - **`test_spec.yaml`:**
     Typed test metadata:
     ```yaml
     test_id: p_star_rewrite_06_v4
     case_id: rewrite_06
     test_index: 30
     generation_id: 4
     dialect_name: "Matrix/Vector Presentation (Complete Operator Licensing)"
     model_id: "deepseek/deepseek-v4.1-flash"
     source_file: "p_star_rewrite_06_v4.yaml"
     expected_outcome:
       answer: 3
       status: ACCEPTED
     actual_outcome:
       extracted_answer: 3
       gate_status: ACCEPTED
       refusal_code: null
     metrics:
       duration_seconds: 5.41
       prompt_tokens: 1845
       completion_tokens: 1210
       cost_usd: 0.000912
     ```
   - **Optional Named File Aliases:**
     For maximum clarity and backward-compatibility, named files matching `source_file` (e.g. `p_star_rewrite_06_v4.yaml`) and `response_<test_id>.yaml` (e.g. `response_p_star_rewrite_06_v4.yaml`) may reside in the test folder alongside `input.yaml` and `response.yaml`.

---

## 4. Pilot Execution & Evaluation Lifecycle

1. **Step 1: Test Folder Allocation:**
   - Allocate the next sequential test index `test_XX` (e.g. `test_31`).
   - Create `omega_engine_woland/tests/pilots/pilot_XXXXXXX/tests/test_XX/`.
2. **Step 2: Input Prompt Compilation & Ingress ($P \mapsto P^*$):**
   - Transpile problem statement into the target surface dialect (Tier H, Tier D, Tier S, S(n), Genesis).
   - Assemble guidance rules, antibodies, and licensed operators.
   - Write `input.yaml` (and verbatim named prompt file) into `tests/test_XX/`.
3. **Step 3: Test Specification Authoring:**
   - Write initial `test_spec.yaml` declaring `test_id`, `case_id`, `generation_id`, `model_id`, and `expected_outcome`.
4. **Step 4: Live Provider Dispatch:**
   - Dispatch stimulus via `OpenRouterLiveProvider` using client-controlled model selection (`deepseek/deepseek-v4.1-flash`).
   - Record latency, tokens per second, prompt tokens, completion tokens, reasoning tokens, and USD cost.
5. **Step 5: Sanitization & Parsing:**
   - Strip markdown code fences (```` ```json ````).
   - Enforce duplicate key rejection and parse JSON dictionary into typed payload.
   - Record structure leakage debt characters.
6. **Step 6: Sovereign Host Gate Evaluation:**
   - Check ground truth against mathematical oracle (`PFP-01-EXACT-LINALG`, `PFP-02-GRAPH-FACTS`).
   - Conjunction check: verify Claim Hygiene in summary thesis (`CG_TRUTH_AND_HYGIENE_CONJUNCTION`).
   - Intermediate witness check: verify scratchpad binds intermediate variables (`AB_INTERMEDIATE_WITNESS`).
   - Compliant refusal check: verify `should_continue: false` routes to `MISSING_EPISTEMIC_GROUNDING` rather than `WRONG_ANSWER`.
7. **Step 7: Atomic Test Custody & Archival:**
   - Write finalized response document into `tests/test_XX/response.yaml` (and optional named response file).
   - Update `actual_outcome` and `metrics` in `tests/test_XX/test_spec.yaml`.
   - Update aggregate comparison matrices in `results/` (`comparison_results*.yaml` and `.md`).
   - Update `cot_miner.py` trace inventory.
   - Update pilot `README.md` test catalog.
