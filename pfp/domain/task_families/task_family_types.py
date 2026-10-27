"""Task family definitions. AuthorityEffect: None."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Callable
from pydantic import Field, field_validator
from pfp.domain.types.base import PfpBaseModel


class DomainCategory(str, Enum):
    SYMBOLIC_MATHEMATICS = "symbolic_mathematics"
    DISCRETE_STRUCTURES = "discrete_structures"
    FORMAL_LOGIC = "formal_logic"
    ALGORITHMIC_SEARCH = "algorithmic_search"
    PROGRAM_SYNTHESIS = "program_synthesis"
    NATURAL_LANGUAGE_REASONING = "natural_language_reasoning"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    DISCRETE_PHYSICS = "discrete_physics"
    PROTOCOL_VERIFICATION = "protocol_verification"
    EXTENSIONAL_PROMPT_DOMAIN = "extensional_prompt_domain"


class InputModality(str, Enum):
    PLAIN_PROSE = "plain_prose"
    MATHEMATICAL_NOTATION = "mathematical_notation"
    GRAPH_ADJACENCY = "graph_adjacency"
    RELATIONAL_TABLES = "relational_tables"
    FORMAL_CODE_AST = "formal_code_ast"
    SYMBOLIC_WIRE_PACKET = "symbolic_wire_packet"
    JSON_KV_RECORD = "json_kv_record"
    HIEROGLYPHIC_SEQUENCE = "hieroglyphic_sequence"
    CUSTOM_TEXT_PROMPT = "custom_text_prompt"


class SolutionModality(str, Enum):
    SCALAR_RATIONAL = "scalar_rational"
    DISCRETE_VECTOR_MATRIX = "discrete_vector_matrix"
    STRUCTURAL_GRAPH = "structural_graph"
    BOOLEAN_DECISION = "boolean_decision"
    REFUSAL_DECLARATION = "refusal_declaration"
    TYPED_SCHEMA_RECORD = "typed_schema_record"
    CODE_PATCH = "code_patch"
    LEAN4_PROOF_TERM = "lean4_proof_term"
    COCHAIN_POTENTIAL = "cochain_potential"
    ARBITRARY_MATCH = "arbitrary_match"


class EvaluationStrategy(str, Enum):
    EXACT_SCALAR_MATCH = "exact_scalar_match"
    DUAL_WITNESS_CIRCULATION = "dual_witness_circulation"
    ACYCLIC_POTENTIAL_GRADIENT = "acyclic_potential_gradient"
    ASSOCIATIVITY_COUNTEREXAMPLE = "associativity_counterexample"
    REFUSAL_TRUTH_TABLE = "refusal_truth_table"
    ORACLE_EXECUTION = "oracle_execution"
    LEAN4_KERNEL_ELABORATION = "lean4_kernel_elaboration"
    PROPERTY_TEST_SUITE = "property_test_suite"
    CUSTOM_PREDICATE = "custom_predicate"


class TaskFamilyDefinition(PfpBaseModel):
    family_id: str = Field(description="Unique slug identifier")
    display_name: str = Field(description="Human-readable title")
    domain_category: DomainCategory | str = Field(default=DomainCategory.EXTENSIONAL_PROMPT_DOMAIN)
    input_modality: InputModality | str = Field(default=InputModality.CUSTOM_TEXT_PROMPT)
    solution_modality: SolutionModality | str = Field(default=SolutionModality.TYPED_SCHEMA_RECORD)
    evaluation_strategy: EvaluationStrategy | str = Field(
        default=EvaluationStrategy.ORACLE_EXECUTION
    )
    checker_contract_id: str = Field(description="Identifier for verification oracle")
    supports_refusal: bool = Field(default=False)
    difficulty_metric: str = Field(default="order_or_size")
    default_rungs: dict[int, dict[str, Any]] = Field(default_factory=dict)
    is_extensional: bool = Field(default=True)
    description: str = Field(default="")

    @field_validator("family_id")
    @classmethod
    def validate_family_id(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]{1,63}$", v):
            raise ValueError(f"Invalid family_id: {v!r}. Must match '^[a-z][a-z0-9_]{{1,63}}$'")
        return v

    @field_validator("checker_contract_id")
    @classmethod
    def validate_checker_id(cls, v: str) -> str:
        if not re.match(r"^PFP-[0-9A-Z_-]+$", v):
            raise ValueError(f"Invalid checker_contract_id: {v!r}. Must match '^PFP-[0-9A-Z_-]+$'")
        return v


class TaskFamilyRegister(PfpBaseModel):
    schema_uri: str = Field(default="pfp.task-family-register.v1", alias="schema")
    authority_effect: str = Field(default="None")
    families: list[TaskFamilyDefinition] = Field(default_factory=list)


GroundTruthProvider = Callable[[int], dict[str, Any]]
