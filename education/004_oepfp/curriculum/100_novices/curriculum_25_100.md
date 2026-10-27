# Track 100: Novices (Software & Prompt Engineering)

AuthorityEffect: None.

## 25-Lesson Syllabus

| Lesson ID | Title | Core Concept | Existing Anchor |
| :--- | :--- | :--- | :--- |
| **100.01** | [The Hallucination of Consistency](concepts/lesson_100_01_the_hallucination_of_consistency.md) | Unconstrained models agree with contradictions unless gated | `bench/head_to_head` |
| **100.02** | [The Prompt as a State Vector](concepts/lesson_100_02_the_prompt_as_a_state_vector.md) | Prompts as formal typed packets with declared carrier sets | `TYPED_PACKETS.md` |
| **100.03** | [The Three Layers of Control](concepts/lesson_100_03_the_three_layers_of_control.md) | Pre-training, decoding logit masks, and host verification | `Paper 032 §2` |
| **100.04** | [The Cost of Unpriced Rewrites](concepts/lesson_100_04_the_cost_of_unpriced_rewrites.md) | Token churn vs monotone retraction cost | `Adversary Axiom` |
| **100.05** | [The First Automated Gate](concepts/lesson_100_05_the_first_automated_gate.md) | Wrapping model outputs in a deterministic rejection oracle | `l1_governor.py` |
| **100.06** | [The 38-Glyph Wire Alphabet](concepts/lesson_100_06_the_38_glyph_wire_alphabet.md) | Canonical codepoint allowlists preventing homoglyph attacks | `wire.py` |
| **100.07** | [Lossless Wire Codecs](concepts/lesson_100_07_lossless_wire_codecs.md) | Compact canonical, postfix, and tagged JSON roundtrip parity | `checks.py` |
| **100.08** | [Deterministic Parsing](concepts/lesson_100_08_deterministic_parsing.md) | Deterministic LL(1) state machine without backtracking | `wire.py` |
| **100.09** | [Value Object Immutability](concepts/lesson_100_09_value_object_immutability.md) | Frozen dataclasses enforcing exact-type equality guards | `RULE_VO_EXACT_TYPE_EQUALITY_001` |
| **100.10** | [DAG Deduplication](concepts/lesson_100_10_dag_deduplication.md) | Structural hashing eliminating duplicate subexpressions | `dag_dedup.py` |
| **100.11** | [The PacketEnvelope Schema](concepts/lesson_100_11_the_packetenvelope_schema.md) | The 4-field kernel binding carrier, input, candidate, and host | `PacketEnvelope.v2` |
| **100.12** | [RFC 8785 Canonical JSON](concepts/lesson_100_12_rfc_8785_canonical_json.md) | Retained standard-topic title; finite selected-Python-encoder examples and explicit number limits | `RFC 8785` |
| **100.13** | [SHA-256 Envelope Sealing](concepts/lesson_100_13_sha_256_envelope_sealing.md) | Cryptographic digest binding types to exact byte representations | `hashlib` |
| **100.14** | [Typed Refusal Payloads](concepts/lesson_100_14_typed_refusal_payloads.md) | Replacing generic exceptions with structured refusal codes | `RefusalCode` |
| **100.15** | [The Four-File Receipt](concepts/lesson_100_15_the_four_file_receipt.md) | receipt.json, novella.md, ddc_actions.jsonl, and summary.json | `Adversary Specification` |
| **100.16** | [The Token Frontier Concept](concepts/lesson_100_16_the_token_frontier_concept.md) | Computing admissible next-token sets from active grammar states | `TokenFrontier` |
| **100.17** | [Dynamic Logit Masking](concepts/lesson_100_17_dynamic_logit_masking.md) | Setting off-frontier logits to negative infinity at decode time | `CarrierProjection` |
| **100.18** | [Retained Probability Mass](concepts/lesson_100_18_retained_probability_mass.md) | Bayes conditioning: p_constrained = p_base / M_retained | `Bayes Conditioning` |
| **100.19** | [Zero Retained Mass Refusal](concepts/lesson_100_19_zero_retained_mass_refusal.md) | Fail-stop refusal on unconstrained generation escape | `REFUSED_ZERO_RETAINED_MASS` |
| **100.20** | [Measuring Entropy Reduction](concepts/lesson_100_20_measuring_entropy_reduction.md) | Quantifying reasoning density and perplexity drops under mask | `Attention Entropy` |
| **100.21** | [Building a Model Adapter](concepts/lesson_100_21_building_a_model_adapter.md) | Clean Architecture ports for OpenAI, Anthropic, and local LLMs | `ports.py` |
| **100.22** | [The Offline Mock Runner](concepts/lesson_100_22_the_offline_mock_runner.md) | Testing multi-turn game loops without API keys or token costs | `MockProposer` |
| **100.23** | [Multi-Turn Retraction Loop](concepts/lesson_100_23_multi_turn_retraction_loop.md) | Iterative proposal and rejection descending until Phi_1 = 0 | `Retraction Turn` |
| **100.24** | [Catching Carrier Smuggling](concepts/lesson_100_24_catching_carrier_smuggling.md) | Detecting off-carrier codepoint injection attempts | `FW-CARRIER-CODEPOINT` |
| **100.25** | [Novice Capstone](concepts/lesson_100_25_novice_capstone.md) | Deploying a self-correcting microservice with verified receipts | `Demo 1 Capstone` |

---

## Integrated System Integration Route

For end-to-end executable system integration labs alongside the 25 topic lessons, see [verified_route.md](verified_route.md) and the integrated laboratories in [`system_integration/`](system_integration/):
- **01:** [Codecs and Tamper Evidence](system_integration/01_codecs_and_tamper_evidence.ipynb) — Lossless wire codec roundtrips & SHA-256 DAG tampering refusal
- **02:** [Token Frontier](system_integration/02_token_frontier.ipynb) — Grammar token frontier conditioning & zero retained mass refusal
- **03:** [Typed Agent Composition](system_integration/03_typed_agent_composition.ipynb) — Coloured operad partial composition & agent capability slice verification
- **04:** [Cycle Repair](system_integration/04_cycle_repair.ipynb) — Discrete cochain coboundary potential repairs & cycle sum conservation

