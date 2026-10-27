# YAML schema twins

**AuthorityEffect:** None.

This directory is not the live packet schema directory. The YAML files here are test twins and a register of those twins. Live packet schemas are the JSON files in `pfp/packet_schemas/`.

These files are not the public ladder. That ladder is `stage_1` through `stage_11` in `pfp/infrastructure/yaml/stages/`.

## Twins of live packet schemas

Same basename, `.yaml` here and `.json` in `packet_schemas/`:

- `packet_envelope_v2.schema.yaml`
- `llm_turn_v1.schema.yaml`
- `code_change_proposal_v1.schema.yaml`
- `candidate_artifact_v1.schema.yaml`
- `evaluation_receipt_v1.schema.yaml`
- `rust_prime_host_request_v1.schema.yaml`
- `rust_prime_host_outcome_v1.schema.yaml`
- `rust_prime_host_description_v1.schema.yaml`

`packet_schemas/` also holds live files with no YAML twin here:

- `prompt_artifact_v1.schema.json`
- `coboundary_score_v1.schema.json`
- `elimination_receipt_v1.schema.json`
- `kill_condition_refusal_map_v1.json`

## YAML only

These files are in this directory. They are not the live `packet_schemas/` set.

- `code_rewrite_packet_v1.schema.yaml`
- `ddc_tape_packet_schema.yaml`
- `lggr_defect_packet_schema.yaml`
- `prime_triad_packet_schema.yaml`
- `wdp_demarcation_packet_schema.yaml`
- `schema_register.yaml` — identity headers for the YAML files above

There is no `schema_register.py` in this directory, no `03_packetization/` directory beside it, and no `*.schema.json` file here.
