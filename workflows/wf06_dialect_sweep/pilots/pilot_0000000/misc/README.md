# Miscellaneous Aggregate Reports (`misc/`)

**AuthorityEffect:** None.  
**Governing Directive:** PFP Pilot Capsule Invariant (SPK-001 / MODUS OPERANDI).  

---

> [!CAUTION]
> **CRITICAL DIRECTIVE FOR LLMS AND AUTONOMOUS AGENTS:**  
> **DO NOT DUMP RESULT, INPUT, OR PROMPT FILES INTO THIS DIRECTORY (`misc/`).**  
> **DO NOT DUMP FILES INTO THE PILOT ROOT DIRECTORY.**  

---

## 1. Directory Purpose: Aggregate Artifacts Only

This directory (`misc/`) is reserved **EXCLUSIVELY** for cross-test aggregate summaries, analytical comparison matrices, and CoT trace mining outputs:
- `comparison_results.yaml` / `comparison_results.md` (cross-trial comparison matrices)
- `comparison_results_obfuscated_v2.*` / `comparison_results_obfuscated_v3.*` (multi-generational aggregate reports)
- `cot_mine.yaml` (aggregate Chain-of-Thought trace mining outputs)

**NOTHING ELSE BELONGS IN THIS DIRECTORY.**

---

## 2. Forbidden Files in `misc/`

Under no circumstances should any LLM, autonomous agent, or tool place any of the following into `misc/`:
- ❌ Individual model responses (`response.yaml`, `response_*.yaml`)
- ❌ Trial input stimulus prompts (`input.yaml`, `p_star.yaml`, `seed.yaml`, `p_star_rewrite_*.yaml`, `seed_rewrite_*.yaml`)
- ❌ Individual test specifications (`test_spec.yaml`)

---

## 3. Mandatory Location for All Trial Files: `tests/test_{NN}/`

Every test trial MUST be completely self-contained in its own dedicated, sequentially indexed directory under `tests/test_{NN}/` (where `{NN}` is a two-digit zero-padded index, e.g. `test_00`, `test_01`, ..., `test_30`, ..., `test_99`):

Each `tests/test_{NN}/` directory MUST contain:
1. **`input.yaml`:** The exact stimulus prompt dispatched to the model (plain seed prompt or complete $P^*$ envelope).
2. **`response.yaml`:** The single associated model response matching `pfp.pilot-response.v1` (raw output, parsed JSON, reasoning traces, cryptographic receipt, and host gate result).
3. **`test_spec.yaml`:** The typed test specification matching `pfp.test-spec.v1` (declaring `test_id`, `case_id`, `generation_id`, `dialect_name`, `model_id`, `expected_outcome`, `actual_outcome`, and `metrics`).
4. *(Optional verbatim aliases)*: `[named_prompt].yaml` (e.g. `seed_rewrite_01.yaml`, `p_star_rewrite_06_v4.yaml`) and `response_[test_id].yaml`.

---

## 4. Summary Table for LLMs

| Content Type | Permitted Path | FORBIDDEN Paths |
|---|---|---|
| Single test response | `tests/test_{NN}/response.yaml` | ❌ `misc/`, ❌ pilot root |
| Single test stimulus / prompt | `tests/test_{NN}/input.yaml` | ❌ `misc/`, ❌ pilot root |
| Single test metadata / spec | `tests/test_{NN}/test_spec.yaml` | ❌ `misc/`, ❌ pilot root |
| Cross-trial comparison report | `misc/comparison_results.yaml` | ❌ `tests/test_{NN}/` |
| CoT trace mining matrix | `misc/cot_mine.yaml` | ❌ `tests/test_{NN}/` |
