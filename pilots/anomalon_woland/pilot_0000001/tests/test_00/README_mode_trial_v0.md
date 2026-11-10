# pilot_0000001 — Graph Facts (Rung 1)

**AuthorityEffect:** None.  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Operational Framework:** [MODUS_OPERANDI.md](../MODUS_OPERANDI.md)  
**Task Family:** `graph_facts`  
**Host Checker:** `PFP-02-GRAPH-FACTS`  
**Structure Delta Metric:** `gate_boolean`  

---

## 1. Description & Protocol Execution

This pilot implements a hermetic, oracle-grounded evaluation instance for `graph_facts` under difficulty rung `1`. Ingress stimuli are compiled into typed $P^*$ envelopes via `p_star_builder.py` according to SPK-001. Model outputs are strictly sanitized by `pilot_response_sanitizer.py` to preserve verbatim byte custody while recording non-schema commentary.

Host gate verification evaluates candidate proposals against sovereign mathematical truth, distinguishing exact solutions from false certainty, schema displacements, and malformed inputs.

### Mandatory Operational Structure

Adhering to [MODUS_OPERANDI.md](../MODUS_OPERANDI.md), `pilot_0000001` maintains:
1. `seed.yaml`: Canonical seed problem defining vertices {0,1,2,3} and undirected edges {0-1, 1-2, 2-0, 0-3}.
2. `prompt_template.yaml`: Current SPK-001 prompt template with active guidance (`rule_name_the_checker_field`, `rule_carrier_is_the_whole_task`, `AB_INTERMEDIATE_WITNESS`, `HP_RESPONSE_ANSWER_SLOT`) and `GraphFactsAnswer` schema.
3. `p_star.yaml`: Compiled $P^*$ instance binding `seed.yaml` to `prompt_template.yaml`.
4. `packet.yaml`: Cryptographically sealed four-object packet (`problem`, `candidate`, `contract`, `receipt`).
5. `results/`: Historical trial logs, mode trial execution digests (`execution.yaml`), and raw live dispatches (`results/live/`).
6. `tests/`: Replayable, sequential test execution directories (`test_00` through `test_99`).

---

## 2. Claim Hygiene Envelope

### 2.1 What This Pilot Supports
- Supports that the host evaluation harness deterministically computes ground truth for `graph_facts` and enforces the `PFP-02-GRAPH-FACTS` gate without data leakage.
- Supports that `$P \mapsto P^*$ assembly under SPK-001 constructs a valid `PromptPacketV0_1` envelope preserving root lineage and containment cardinality.
- Supports that the canonical template `prompt_template.yaml` and compiled packet `p_star.yaml` natively specify lineage, active guidance, system policy manifest, and `GraphFactsAnswer` JSON schema draft 2020-12.
- Supports that empirical live trials demonstrate schema displacement (`antiskill_schema_displacement`) when checker field names are unconstrained (`test_02`), validating the requirement for `rule_name_the_checker_field`.
- Supports that at least four distinct compiled semantic mutants are caught and killed by the test oracle.

### 2.2 What This Pilot Does NOT Support
- Does **NOT** support any claim that LLMs universally or reliably solve `graph_facts` problems. Offline fixture dry runs verify software plumbing and host gates only; they provide zero empirical evidence regarding universal model capability.
- Does **NOT** authorize unbudgeted live provider dispatches without explicit allocation and authentic cryptographic receipts.

### 2.3 Narrowest Defensible Claim
- Under the declared assumptions, the host verification suite deterministically distinguishes valid mathematical solutions from invalid, malformed, or ambiguous proposals on the scoped `graph_facts` benchmark, enforces zero-spend boundaries during offline execution, and catches 100% of tested mutant discrepancies.

### 2.4 Next Test Needed
- Execute live trial of `p_star.yaml` with `rule_name_the_checker_field` active under `deepseek/deepseek-v4.1-flash` to evaluate whether the explicit field naming rule shifts `test_02`'s `MALFORMED` proposal into an `ACCEPTED` proposal.

---

## Mode trial summary

Local execution of `mode_02` against `omega_engine_education/pfp/infrastructure/yaml/modes/mode_02_packets_and_sealed_envelopes/contract.yaml`:
- The packet is the four-object seal in `packet.yaml`.
- `results/execution.yaml` records 7 variations.
- Winning condition executed: `true`.
- Digest checks ran on the four-object packet verifying edge flip detection, whitespace sensitivity, localized candidate tampering, and oracle decoupling.

---

## 4. Replayable Test Registry (`test_00` through `test_99`)

Every test within `pilot_0000001` is assigned a dedicated folder containing `test_spec.yaml`, `input.yaml`, and `response.yaml`:

| Test ID | Model ID | Input Dialect / Case | Actual Outcome | Gate Status | Failure Mode / Key Observation |
|---|---|---|---|---|---|
| [`test_00`](tests/test_00) | `mistralai/mistral-7b-instruct:free` | Mode 02 Seed | `TRANSPORT_FAILURE` | `REJECTED` | Provider HTTP 404 on free tier endpoint. |
| [`test_01`](tests/test_01) | `deepseek/deepseek-v4.1-flash` | Mode 02 Seed (Attempt 1) | `RECORDED` | `MALFORMED` | Raw reply empty string despite completion token billing. |
| [`test_02`](tests/test_02) | `deepseek/deepseek-v4.1-flash` | Mode 02 Seed (Attempt 2) | `RECORDED` | `MALFORMED` | Model returned `{"triangle": true, "bridge": true}` instead of `triangle_012` and `bridge_03`. Demonstrates `antiskill_schema_displacement`. |

---

## 5. Replay Instructions for Follow-on Users

To replay and inspect the test suite:
1. **Inspect Test Fixtures:**
   - Review inputs in `tests/test_XX/input.yaml` and responses in `tests/test_XX/response.yaml`.
2. **Execute Sovereign Gate Validation:**
   ```bash
   py -3.12 -m pytest omega_engine_education/pfp/tests/test_pilot_suite.py -v
   ```
3. **Dispatch Live Trial (Requires API Key & Preflight Budget):**
   ```bash
   py -3.12 -m omega_engine_education.pilots.live_evaluator --pilot pilot_0000001 --model deepseek/deepseek-v4.1-flash
   ```

## 3. Mode trial
Local execution of `mode_02` against `omega_engine_education/pfp/infrastructure/yaml/modes/mode_02_packets_and_sealed_envelopes/contract.yaml`.
The packet is the four-object seal in `packet.yaml`. `pilot_0000000/prompt_template.yaml` is a generated empty shell and is not copied into this pilot.
`results/execution.yaml` records 7 variations. Provider calls: 0. Spend: 0.
Winning condition executed: `true`.
Limit: Digest checks ran on the four-object packet. No model was called.
