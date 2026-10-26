"""PFP packet and receipt JSON Schemas.

These are not stages. The staged pipeline is
`omega_engine_pfp/infrastructure/yaml/stages/`. Each file here is the JSON
Schema twin of a YAML schema in `infrastructure/yaml/schemas/` with the same
stem.

AuthorityEffect: None.
"""

from pathlib import Path

PACKET_SCHEMAS_ROOT = Path(__file__).resolve().parent

PACKET_ENVELOPE_V2 = PACKET_SCHEMAS_ROOT / "packet_envelope_v2.schema.json"
PROMPT_ARTIFACT_V1 = PACKET_SCHEMAS_ROOT / "prompt_artifact_v1.schema.json"
CANDIDATE_ARTIFACT_V1 = PACKET_SCHEMAS_ROOT / "candidate_artifact_v1.schema.json"
LLM_TURN_V1 = PACKET_SCHEMAS_ROOT / "llm_turn_v1.schema.json"
COBOUNDARY_SCORE_V1 = PACKET_SCHEMAS_ROOT / "coboundary_score_v1.schema.json"
CODE_CHANGE_PROPOSAL_V1 = PACKET_SCHEMAS_ROOT / "code_change_proposal_v1.schema.json"
EVALUATION_RECEIPT_V1 = PACKET_SCHEMAS_ROOT / "evaluation_receipt_v1.schema.json"
ELIMINATION_RECEIPT_V1 = PACKET_SCHEMAS_ROOT / "elimination_receipt_v1.schema.json"
RUST_PRIME_HOST_REQUEST_V1 = PACKET_SCHEMAS_ROOT / "rust_prime_host_request_v1.schema.json"
RUST_PRIME_HOST_OUTCOME_V1 = PACKET_SCHEMAS_ROOT / "rust_prime_host_outcome_v1.schema.json"
RUST_PRIME_HOST_DESCRIPTION_V1 = (
    PACKET_SCHEMAS_ROOT / "rust_prime_host_description_v1.schema.json"
)
KILL_CONDITION_REFUSAL_MAP_V1 = PACKET_SCHEMAS_ROOT / "kill_condition_refusal_map_v1.json"

__all__ = [
    "CANDIDATE_ARTIFACT_V1",
    "COBOUNDARY_SCORE_V1",
    "CODE_CHANGE_PROPOSAL_V1",
    "ELIMINATION_RECEIPT_V1",
    "EVALUATION_RECEIPT_V1",
    "KILL_CONDITION_REFUSAL_MAP_V1",
    "LLM_TURN_V1",
    "PACKET_ENVELOPE_V2",
    "PACKET_SCHEMAS_ROOT",
    "PROMPT_ARTIFACT_V1",
    "RUST_PRIME_HOST_DESCRIPTION_V1",
    "RUST_PRIME_HOST_OUTCOME_V1",
    "RUST_PRIME_HOST_REQUEST_V1",
]
