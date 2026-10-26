"""PFP Prompt Templates, P* Trees, Lineage, Guidance, and System Prompt Manifest.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator
import yaml

from .base import (
    AuthorityEffect,
    CheckerId,
    EvaluationStatus,
    PfpDomainModel,
)


class PromptLineageSlot(PfpDomainModel):
    """First-class provenance and mutation ancestry slots for prompt trees."""
    prompt_id: str
    generation_id: Any = 0
    family_id: str
    parent_id: str | None = None
    template_id: str | None = None
    template_version: str | None = None
    mutation_kind: str | None = None
    mutation_notes: str | None = None
    mutation_note: str | None = None
    status: str | None = None
    created_at_utc: str | None = None
    author: str | None = None
    authority_effect: AuthorityEffect | str = AuthorityEffect.NONE

    @model_validator(mode="after")
    def _normalize_mutation_notes(self) -> PromptLineageSlot:
        notes = self.mutation_notes if self.mutation_notes is not None else self.mutation_note
        note = self.mutation_note if self.mutation_note is not None else self.mutation_notes
        if notes == self.mutation_notes and note == self.mutation_note:
            return self
        return self.model_copy(update={"mutation_notes": notes, "mutation_note": note})


class RuleSlot(PfpDomainModel):
    """Sovereign governance rule binding."""
    rule_id: str
    name: str | None = None
    statement: str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class AntibodySlot(PfpDomainModel):
    """Active immune antibody record adhering to .agents/antibodies schema."""
    antibody_id: str
    failure_class: str | None = None
    target_pattern: str | None = None
    constraint_type: str = "Restrain"
    operatorizability: str = "repairable"
    action: str = "repair"
    severity: str = "P2"
    description: str | None = None
    negative_fixture: str | None = None
    positive_fixture: str | None = None
    times_seen: int | None = 0
    evidence_sha256: str | None = None
    pharmacy_status: str | None = "candidate"
    reviewed_guidance: str | None = None
    admission_reference: dict[str, Any] | None = None
    case_id: str | None = None
    failed_proof: str | None = None
    diagnostic: str | None = None
    timestamp: str | None = None
    authority_effect: AuthorityEffect | str | None = AuthorityEffect.NONE
    model_config = ConfigDict(extra="allow")


class AntipatternSlot(PfpDomainModel):
    """Known anti-pattern signature to be projected out."""
    antipattern_id: str
    name: str
    description: str
    target_pattern: str | None = None


class HelpfulPatternSlot(PfpDomainModel):
    """Positive behavioral pattern or recommended structural idiom."""
    pattern_id: str
    name: str
    description: str
    enforcement: str | None = None


class GuidanceSlot(PfpDomainModel):
    """Active defense and behavioral guidance slots."""
    rules: list[RuleSlot] = Field(default_factory=list)
    antibodies: list[AntibodySlot | str] = Field(default_factory=list)
    antipatterns: list[AntipatternSlot] = Field(default_factory=list)
    helpful_patterns: list[HelpfulPatternSlot] = Field(default_factory=list)


class NegativeMutationFixture(PfpDomainModel):
    """Declarative specification for a negative mutation or prompt token perturbation test."""
    fixture_id: str
    checker_id: CheckerId | str
    mutation_kind: str
    target_antibody: str | None = None
    description: str
    perturbed_prompt: str | None = None
    mutated_response_payload: Any = None
    expected_status: EvaluationStatus
    expected_refusal_code: str | None = None


class PfpSemanticPolicyManifest(PfpDomainModel):
    policy_id: Literal["SPK-001"] = "SPK-001"
    required_stamp: Literal["derived_under_policy: SPK-001"] = "derived_under_policy: SPK-001"


class PfpMss0GrammarConstraint(PfpDomainModel):
    system_name: Literal["SYM SYS"] = "SYM SYS"
    atomic_glyph_count: Literal[38] = 38
    node_labels: Literal["a..z"] = "a..z"
    numeric_labels: Literal["0..9"] = "0..9"
    delimiters: list[str]
    pair_note: str
    numeric_license_rule: str
    derived_patterns_note: str


class PfpOpSemantics(PfpDomainModel):
    default_layer: int = 1
    default_meaning: str = "syntactic_binary_operator"
    forbidden_unlicensed_interpretations: list[str] = Field(default_factory=list)
    license_required_for: list[str] = Field(default_factory=list)


class PfpMss0Level(PfpDomainModel):
    level: int
    code: str
    name: str
    meaning: str


class PfpMss0TypingRules(PfpDomainModel):
    preamble: str
    levels: list[PfpMss0Level]


class PfpEvaluatorBinding(PfpDomainModel):
    evaluator: str
    promotes: str
    does_not_promote: str | None = None


class PfpEvaluatorScopeRule(PfpDomainModel):
    principle: str
    bindings: list[PfpEvaluatorBinding]


class PfpEvidenceLevel(PfpDomainModel):
    code: str
    meaning: str


class ReplacementDefault(PfpDomainModel):
    from_: str = Field(alias="from")
    to: str


class PfpClaimHygiene(PfpDomainModel):
    discipline: str | None = None
    forbidden_words: list[str] = Field(default_factory=list)
    forbidden_word_exceptions: str | None = None
    replacement_defaults: list[ReplacementDefault] = Field(default_factory=list)
    default_posture: str | None = None
    what_it_supports: str | None = None
    what_it_does_not_support: str | None = None
    next_test_needed: str | None = None


class RoleManifest(PfpDomainModel):
    persona: str
    goal: str | None = None


class SystemPromptManifest(PfpDomainModel):
    semantic_policy_manifest: PfpSemanticPolicyManifest
    mss0_grammar_constraint: PfpMss0GrammarConstraint
    op_semantics: PfpOpSemantics
    import_boundary: str
    mss0_typing_rules: PfpMss0TypingRules
    evaluator_scope_rule: PfpEvaluatorScopeRule
    evidence_levels: list[PfpEvidenceLevel]
    claim_hygiene: PfpClaimHygiene
    role: RoleManifest
    antibody_injections: list[AntibodySlot | str] = Field(default_factory=list)


class PromptTemplate(PfpDomainModel):
    """Universal prompt template carrying lineage, guidance, and system manifest."""
    lineage: PromptLineageSlot
    guidance: GuidanceSlot
    system_prompt: str
    user_prompt: str
    response_schema: str

    def parse_system_manifest(self) -> SystemPromptManifest:
        clean = self.system_prompt.strip()
        if clean.startswith("```yaml"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("\n", 1)[0]
        data = yaml.safe_load(clean)
        return SystemPromptManifest.model_validate(data)

    def parse_response_schema(self) -> dict[str, Any]:
        clean = self.response_schema.strip()
        if clean.startswith("```yaml"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("\n", 1)[0]
        data = yaml.safe_load(clean)
        return data if isinstance(data, dict) else {}


class PStarPrompt(PfpDomainModel):
    """Concrete P* instance with ground truth prompt stimulus injected."""
    lineage: PromptLineageSlot
    guidance: GuidanceSlot
    system_prompt: str
    user_prompt: str
    response_schema: str


# Aliases
SemanticPolicyManifest = PfpSemanticPolicyManifest
Mss0GrammarConstraint = PfpMss0GrammarConstraint
OpSemantics = PfpOpSemantics
Mss0Level = PfpMss0Level
Mss0TypingRules = PfpMss0TypingRules
EvaluatorBinding = PfpEvaluatorBinding
EvaluatorScopeRule = PfpEvaluatorScopeRule
EvidenceLevel = PfpEvidenceLevel
ClaimHygiene = PfpClaimHygiene
