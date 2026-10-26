"""Prompt-to-Cochain execution and evaluation contracts.

Architecture Review 16 §3–§4.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from .contracts import ContractSpec, InvariantCheck, Postcondition, Precondition

PROMPT_COCHAIN_EVALUATION_CONTRACT_ID = (
    "urn:omega:pfp:contract:prompt_cochain_evaluation:v1.0.0"
)

RULE_PROMPT_COCHAIN_CHAIN_LAW_001 = "RULE_PROMPT_COCHAIN_CHAIN_LAW_001"
RULE_PROMPT_COCHAIN_ZERO_GAP_001 = "RULE_PROMPT_COCHAIN_ZERO_GAP_001"
RULE_PROMPT_COCHAIN_IMPOSSIBLE_PROFILE_001 = "RULE_PROMPT_COCHAIN_IMPOSSIBLE_PROFILE_001"
RULE_PROMPT_COCHAIN_PRIME_TRIAD_001 = "RULE_PROMPT_COCHAIN_PRIME_TRIAD_001"
RULE_PROMPT_COCHAIN_FOUR_WAY_DISPOSITION_001 = (
    "RULE_PROMPT_COCHAIN_FOUR_WAY_DISPOSITION_001"
)


class PromptCellComplexSpec(BaseModel):
    """Specification of an oriented finite cell complex C^0 -> C^1 -> C^2 over Q."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    v_count: StrictInt = Field(
        ge=0, description="Number of vertices (0-cells, C^0 dimension)"
    )
    e_count: StrictInt = Field(
        ge=0, description="Number of edges (1-cells, C^1 dimension)"
    )
    f_count: StrictInt = Field(
        ge=0,
        description="Number of faces (2-cells, C^2 dimension). 0 for zero-face complex.",
    )
    d0_matrix: list[list[Any]] = Field(
        description="Incidence matrix d_0: C^0 -> C^1 of shape [E, V]"
    )
    d1_matrix: list[list[Any]] = Field(
        default_factory=list,
        description="Incidence matrix d_1: C^1 -> C^2 of shape [F, E]",
    )


class PrimeTriadSpec(BaseModel):
    """Execution context binding Prime Triad stages (Primes 000, 001, 002)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source_bytes: StrictStr = Field(
        description="UTF-8 or raw prompt source representation"
    )
    expected_hash: StrictStr | None = Field(
        default=None,
        description="SHA-256 digest of source bytes for Prime 000 intake",
    )
    protected_answer: StrictStr | None = Field(
        default=None,
        description="Protected baseline answer for Prime 001 loss preservation",
    )
    continuation_budget: StrictInt = Field(
        default=64, ge=0, description="Remaining continuation budget for Prime 002"
    )


class CochainEvaluationReceipt(BaseModel):
    """Execution receipt emitted after prompt cochain evaluation."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    disposition: StrictStr = Field(
        description="One of: ExactCoboundary, ClosedNonExactClass, NonClosedEdgeData, Refusal"
    )
    phi1_rational: StrictStr | None = Field(
        default=None, description="Exact quotient obstruction Phi_1 in Q (n/d)"
    )
    gamma2_rational: StrictStr | None = Field(
        default=None, description="Exact closure defect Gamma_2 in Q (n/d)"
    )
    potential: list[StrictStr] = Field(
        default_factory=list, description="0-cochain potential vector a in Q^V"
    )
    dual_witness: list[StrictStr] = Field(
        default_factory=list, description="Dual certificate y in Q^E"
    )
    defect_vector: list[StrictStr] = Field(
        default_factory=list, description="Closure defect d_1 c in Q^F"
    )
    refusal_reason: StrictStr | None = Field(
        default=None, description="Refusal reason code if disposition is Refusal"
    )
    refusal_detail: StrictStr | None = Field(
        default=None, description="Refusal message if disposition is Refusal"
    )
    prime_triad_status: StrictStr = Field(
        default="VALID",
        description="Prime Triad status (e.g. VALID, BUDGET_EXHAUSTED, HASH_MISMATCH)",
    )
    invariants_verified: list[InvariantCheck] = Field(default_factory=list)
    authority_effect: StrictStr = Field(default="None")


def get_prompt_cochain_evaluation_contract() -> ContractSpec:
    """Return the canonical ContractSpec for Prompt-to-Cochain evaluation."""
    return ContractSpec(
        contract_id=PROMPT_COCHAIN_EVALUATION_CONTRACT_ID,
        title="Prompt-to-Cochain Execution and Exact Evaluation Contract",
        version="1.0.0",
        authority_effect="None",
        entry_preconditions=[
            Precondition(
                name="PRE_CELL_COMPLEX_CHAIN_LAW",
                description="Boundary composition d_1 * d_0 = 0 over Q",
                predicate="d1_matrix @ d0_matrix == 0",
            ),
            Precondition(
                name="PRE_DIMENSION_PARITY",
                description="Dimensions of c in Q^E, a in Q^V, y in Q^E match complex declarations",
                predicate="len(c) == e_count and len(a) == v_count and len(y) == e_count",
            ),
            Precondition(
                name="PRE_PRIME_000_INTAKE_INTEGRITY",
                description="Prime 000 intake: source bytes SHA-256 matches expected hash when supplied",
                predicate="expected_hash is None or sha256(source_bytes) == expected_hash",
            ),
            Precondition(
                name="PRE_PRIME_002_BUDGET_AVAILABLE",
                description="Prime 002 continuation budget must be positive",
                predicate="continuation_budget > 0",
            ),
        ],
        exit_postconditions=[
            Postcondition(
                name="POST_EXACT_DUALITY_ZERO_GAP",
                description="Dual witness certifies Phi_1 with zero duality gap in Q",
                predicate="d0_T @ y == 0 and norm_infty(y) <= 1 and y @ c == norm_1(c - d0 @ a)",
            ),
            Postcondition(
                name="POST_FOUR_WAY_TYPED_DISPOSITION",
                description="Result is classified into ExactCoboundary, ClosedNonExactClass, NonClosedEdgeData, or Refusal",
                predicate="disposition in {'ExactCoboundary', 'ClosedNonExactClass', 'NonClosedEdgeData', 'Refusal'}",
            ),
            Postcondition(
                name="POST_IMPOSSIBLE_PROFILE_FIREWALL",
                description="Phi_1 == 0 and Gamma_2 > 0 is inadmissible for a valid complex; must be refused",
                predicate="not (phi1 == 0 and gamma2 > 0 and disposition != 'Refusal')",
            ),
        ],
        invariants=[
            RULE_PROMPT_COCHAIN_CHAIN_LAW_001,
            RULE_PROMPT_COCHAIN_ZERO_GAP_001,
            RULE_PROMPT_COCHAIN_IMPOSSIBLE_PROFILE_001,
            RULE_PROMPT_COCHAIN_PRIME_TRIAD_001,
            RULE_PROMPT_COCHAIN_FOUR_WAY_DISPOSITION_001,
        ],
        winning_condition="Exact dual witness verification with zero rational duality gap and typed disposition certification",
        failure_modes=[
            "CHAIN_LAW_VIOLATION",
            "DIMENSION_MISMATCH",
            "IMPOSSIBLE_PROFILE",
            "DUAL_GAP_NONZERO",
            "DUAL_ANNIHILATOR_VIOLATION",
            "DUAL_NORM_BOUND_VIOLATION",
            "PRIME_000_HASH_MISMATCH",
            "PRIME_002_BUDGET_EXHAUSTED",
        ],
    )
