# PFP Packet and Receipt JSON Schemas

**AuthorityEffect:** None.
**Location:** `omega_engine_pfp/packet_schemas/`

These files are JSON Schemas for packets and receipts. They are not pipeline
stages. Until 2026-10-17 this folder was called `stages/` and its files carried
`stage_N_` prefixes. Those numbers were not a run order. No runner loaded the
files, and three of them rejected real producer output.

The staged pipeline is `omega_engine_pfp/infrastructure/yaml/stages/`, and
`stage_models.yaml` there declares its order. This folder holds packets, which
are content-addressed envelopes. A host checks a packet and issues a receipt.
Rule `RULE_PROMPT_PACKET_STAGE_MODE_001` keeps prompts, packets, stages and
modes apart.

## Inventory

A YAML twin is the schema of the same name in
`omega_engine_pfp/infrastructure/yaml/schemas/`. "Producer" names the code
whose output `tests/test_packet_schema_conformance.py` validates against the
schema.

| File | `$id` | YAML twin | Producer |
| :--- | :--- | :--- | :--- |
| `packet_envelope_v2.schema.json` | `omega.symbol-game.packet-envelope.v2` | yes | `build_llm_turn_envelope`, `build_code_change_proposal_envelope` |
| `llm_turn_v1.schema.json` | `omega.symbol-game.llm-turn.v1` | yes | `LlmTurnPayloadV1` (`domain/shared_kernel/llm_payload.py`) |
| `code_change_proposal_v1.schema.json` | `omega.symbol-game.code-change-proposal.v1` | yes | `CodeChangeProposalPayloadV1` (`domain/aggregates/code_change_proposal.py`) |
| `prompt_artifact_v1.schema.json` | `omega.symbol-game.prompt-artifact.v1` | no | `compile_prompt_artifact` (`domain/aggregates/prompt_artifact.py`) |
| `candidate_artifact_v1.schema.json` | `omega.symbol-game.candidate-artifact.v1` | yes | `CandidateArtifactV1` (`domain/entities/candidate_artifact.py`) |
| `coboundary_score_v1.schema.json` | `omega.symbol-game.coboundary-score.v1` | no | `CoboundaryScoreResult` (`domain/entities/coboundary_score.py`) |
| `elimination_receipt_v1.schema.json` | `omega.symbol-game.elimination-receipt.v1` | no | `create_elimination_receipt` (`domain/aggregates/prompt_artifact.py`) |
| `evaluation_receipt_v1.schema.json` | `omega.oesos.evaluation-receipt.v1` | yes | host |
| `rust_prime_host_request_v1.schema.json` | `omega.oesos.rust-prime-host-request.v1` | yes | host |
| `rust_prime_host_outcome_v1.schema.json` | `omega.oesos.rust-prime-host-outcome.v1` | yes | host |
| `rust_prime_host_description_v1.schema.json` | `omega.oesos.rust-prime-host-description.v1` | yes | host |
| `kill_condition_refusal_map_v1.json` | `omega.symbol-game.kill-condition-refusal-map.v1` | no | data, not a schema |

## How they fit together

- An envelope carries one payload family, either an LLM turn
  (`llm_turn_v1`) or a code-change proposal (`code_change_proposal_v1`).
- A prompt artifact is compiled before a turn, and the turn payload is built
  from it.
- A candidate artifact is what a producer returns for a packet. It does not
  certify itself.
- The host writes the coboundary score, the evaluation receipt and the
  elimination receipt. Rationals in a score are canonical `"p/q"` strings,
  never floats.
- The refusal map is a closed vocabulary. It maps kill conditions to host
  refusals and obstruction families.

## Changing a schema

Change a schema and its YAML twin in the same commit, then run
`tests/test_packet_schema_conformance.py`. A schema that rejects real producer
output, or accepts a field the producer never writes, fails that test.
