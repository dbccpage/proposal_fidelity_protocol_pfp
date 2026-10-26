"""Domain models for Prompt Civilization.

Demographic tiers, prompt genomes, protected spans, genealogy links, and state transitions.
AuthorityEffect: None.
"""

from __future__ import annotations

import enum
import hashlib
import json
import threading
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Sequence

from .canonical import (
    digest,
    exact_object,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
    wire_tuple,
)

# =============================================================================
# DEMOGRAPHIC LIFECYCLE MODELS (Symbol Game & Swarm Governance)
# =============================================================================

@enum.unique
class PopulationTier(str, enum.Enum):
    """The 4-population demographic lifecycle tiers (+ Cemetery refusal store).

    - WILD: Untrusted inbound user queries and uncurated model continuations.
    - CANDIDATE: Synthesized failure motifs and candidate anti-skills (no authority).
    - REVIEWED: Passed negative selection and holdout banks (provisional, no normative authority).
    - ADMITTED: Human-authorized, versioned, cryptographically sealed formulary.
    - CEMETERY: Permanently refused or discarded failure archive.
    """

    WILD = "WILD"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    ADMITTED = "ADMITTED"
    CEMETERY = "CEMETERY"


class UnauthorizedAdmissionError(Exception):
    """Raised when attempting to promote a prompt to ADMITTED without an operator cryptographic signature.

    Enforces the Demographic Law: Recurrence and PageRank propose candidates;
    they never grant normative authority.
    """


@dataclass(frozen=True)
class CivilizationPrompt:
    """A prompt or behavioral instruction residing in a demographic tier."""

    prompt_id: str
    content: str
    tier: PopulationTier
    pagerank_score: Fraction = Fraction(0, 1)
    operator_signature: str | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if isinstance(self.pagerank_score, float):
            raise TypeError("Float pagerank_score violates Zero-Float law; use Fraction")
        if not isinstance(self.pagerank_score, Fraction):
            object.__setattr__(self, "pagerank_score", Fraction(self.pagerank_score))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.prompt_id == other.prompt_id
            and self.content == other.content
            and self.tier == other.tier
            and self.pagerank_score == other.pagerank_score
            and self.operator_signature == other.operator_signature
            and self.authority_effect == other.authority_effect
        )


@dataclass(frozen=True)
class PromotionDecision:
    """Decision recording demographic promotion or refusal."""

    prompt_id: str
    from_tier: PopulationTier
    to_tier: PopulationTier
    is_admitted: bool
    status: str
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.prompt_id == other.prompt_id
            and self.from_tier == other.from_tier
            and self.to_tier == other.to_tier
            and self.is_admitted == other.is_admitted
            and self.status == other.status
            and self.reason == other.reason
        )


@dataclass
class CivilizationState:
    """State machine governing the 4-population lifecycle."""

    prompts: dict[str, CivilizationPrompt] = field(default_factory=dict)

    def register_wild_prompt(self, prompt_id: str, content: str) -> CivilizationPrompt:
        """Register an untrusted inbound prompt in the WILD tier."""
        p = CivilizationPrompt(
            prompt_id=prompt_id,
            content=content,
            tier=PopulationTier.WILD,
            pagerank_score=Fraction(0, 1),
        )
        self.prompts[prompt_id] = p
        return p

    def promote_to_candidate(
        self, prompt_id: str, pagerank_score: Fraction = Fraction(1, 10)
    ) -> PromotionDecision:
        """Promote a prompt from WILD to CANDIDATE based on recurring motif."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.WILD:
            raise ValueError(
                f"Prompt {prompt_id} must be in WILD tier, currently in {prompt.tier}"
            )

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.CANDIDATE,
            pagerank_score=Fraction(pagerank_score),
            operator_signature=None,
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.CANDIDATE,
            is_admitted=False,
            status="PROMOTED_TO_CANDIDATE",
            reason="Prompt synthesized into candidate anti-skill; no normative authority",
        )

    def promote_to_reviewed(self, prompt_id: str) -> PromotionDecision:
        """Promote a prompt from CANDIDATE to REVIEWED after negative selection."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.CANDIDATE:
            raise ValueError(f"Prompt {prompt_id} must be in CANDIDATE tier, currently in {prompt.tier}")

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.REVIEWED,
            pagerank_score=prompt.pagerank_score,
            operator_signature=None,
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.REVIEWED,
            is_admitted=False,
            status="PROMOTED_TO_REVIEWED",
            reason="Passed negative selection and holdout bank falsifiers",
        )

    def promote_to_admitted(
        self, prompt_id: str, operator_signature: str | None = None
    ) -> PromotionDecision:
        """Refuse untrusted tokens; authenticated custody belongs to the controller."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.REVIEWED:
            raise ValueError(f"Prompt {prompt_id} must be in REVIEWED tier, currently in {prompt.tier}")

        raise UnauthorizedAdmissionError(
            "EXTERNAL_REVIEW_NOT_AUTHENTICATED: token shape grants no custody; "
            "use the controller with a host-bound PromptCustodyLedgerV1"
        )

    def promote_to_cemetery(
        self, prompt_id: str, reason: str = "Refused"
    ) -> PromotionDecision:
        """Move a prompt to the permanent CEMETERY refusal tier."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.CEMETERY,
            pagerank_score=Fraction(0, 1),
            operator_signature=None,
            authority_effect="None",
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.CEMETERY,
            is_admitted=False,
            status="CEMETERY_ARCHIVED",
            reason=reason,
        )

    banish_to_cemetery = promote_to_cemetery


# =============================================================================
# CUSTODY, PROTECTED SPANS & PROMPT GENOMES
# =============================================================================

class CustodyTier(str, enum.Enum):
    WILD = "Wild"
    CANDIDATE = "Candidate"
    REVIEWED = "Reviewed"
    ADMITTED = "Admitted"
    SUSPENDED = "Suspended"
    REVOKED = "Revoked"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class ProtectedSpanV1:
    """Immutable declared byte slice within a prompt artifact."""

    name: str
    start_byte: int
    end_byte: int

    def __post_init__(self) -> None:
        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError(f"Invalid byte span: [{self.start_byte}, {self.end_byte})")


@dataclass(frozen=True)
class PromptGenomeV1:
    """Immutable prompt genome with birth custody and content-addressed ID."""

    source_packet_refs: Sequence[Dict[str, str]]
    domain_model: Any
    parents: Sequence[Dict[str, Any]] = ()
    birth_custody: CustodyTier = CustodyTier.WILD
    prompt_id: str = ""
    generation: int = 0
    protected_spans: Sequence[ProtectedSpanV1] = ()

    def __post_init__(self) -> None:
        for name in ("source_packet_refs", "domain_model", "parents", "protected_spans"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))
        payload = [
            _plain(self.source_packet_refs),
            _plain(self.domain_model),
            _plain(self.parents),
            self.birth_custody.value if hasattr(self.birth_custody, "value") else str(self.birth_custody),
            [asdict(span) for span in self.protected_spans],
        ]
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        identity = "genome_" + hashlib.sha256(b"omega-prompt-genome-v1:" + raw).hexdigest()
        if self.prompt_id and self.prompt_id != identity:
            raise ValueError("GENOME_IDENTITY_MISMATCH")
        object.__setattr__(self, "prompt_id", identity)

    def to_dict(self) -> Dict[str, Any]:
        """Lossless JSON representation for durable host storage."""
        return {
            "source_packet_refs": _plain(self.source_packet_refs),
            "domain_model": _plain(self.domain_model),
            "parents": _plain(self.parents),
            "birth_custody": self.birth_custody.value,
            "prompt_id": self.prompt_id,
            "generation": self.generation,
            "protected_spans": [asdict(span) for span in self.protected_spans],
        }

    @classmethod
    def from_dict(cls, fields: Dict[str, Any]) -> "PromptGenomeV1":
        values = dict(fields)
        values["birth_custody"] = CustodyTier(values["birth_custody"])
        values["protected_spans"] = tuple(ProtectedSpanV1(**span) for span in values["protected_spans"])
        return cls(**values)

    @classmethod
    def create_verified(
        cls,
        *,
        source_packet_refs: Sequence[Dict[str, str]],
        domain_model: Dict[str, Any],
        parents: Sequence[Dict[str, Any]],
        declared_generation: int,
        protected_spans: Sequence[ProtectedSpanV1] = (),
        birth_custody: CustodyTier = CustodyTier.WILD,
        allowed_boundary_names: Optional[Sequence[str]] = None,
    ) -> "PromptGenomeV1":
        if parents:
            expected_generation = max(p.get("generation", 0) for p in parents) + 1
        else:
            expected_generation = 0

        if declared_generation != expected_generation:
            raise ValueError(
                f"DERIVED_FIELD_MISMATCH: declared_generation {declared_generation} "
                f"does not match expected derived generation {expected_generation}"
            )

        known_boundaries = set(allowed_boundary_names or ["system_framing", "type_signatures", "claim_hygiene", "authority_effect", "core"])
        for span in protected_spans:
            if span.name not in known_boundaries:
                raise ValueError(f"PROTECTED_BOUNDARY_UNRESOLVED: boundary '{span.name}' could not be resolved")

        return cls(
            source_packet_refs=source_packet_refs,
            domain_model=domain_model,
            parents=parents,
            generation=declared_generation,
            protected_spans=protected_spans,
            birth_custody=birth_custody,
        )


@dataclass(frozen=True)
class PromptViewV1:
    """Replayable projection view of a genome at a specific ledger revision."""

    prompt_id: str
    ledger_revision: int
    current_custody: CustodyTier


@dataclass(frozen=True)
class ExecutionOccurrenceV1:
    """Execution occurrence of an unchanged prompt, generating telemetry without duplicating genome."""

    occurrence_id: str
    prompt_id: str
    session_id: str
    input_packet_id: str
    output_packet_id: str


@dataclass(frozen=True)
class DomainPlacementV1:
    """Placement binding a content digest to a domain assignment and read scope."""

    placement_id: str
    content_digest: str
    domain_assignment: str
    read_scope: Sequence[str]
    disposition: str


def scope_covers(scope: str, target: str) -> bool:
    """Exact scope, `*`, or a `stem.*` label with a dot boundary.

    An exact label does not grant its children. `math.*` does not cover `mathematics`.
    """
    if scope == "*" or scope == target:
        return True
    if scope.endswith(".*"):
        stem = scope[:-2]
        return bool(stem) and (target == stem or target.startswith(stem + "."))
    return False


def hard_domain_eligible(placement: DomainPlacementV1, required_domain: str) -> bool:
    """Predicate evaluating hard domain eligibility.

    Requires disposition ADMITTED_LOCAL and a read_scope entry that covers the
    required domain. domain_assignment is origin metadata and does not grant scope.
    """
    if placement.disposition != "ADMITTED_LOCAL":
        return False
    return any(scope_covers(scope, required_domain) for scope in placement.read_scope)


# =============================================================================
# LINEAGE, CEMETERY & RE-ENTRY VALUE OBJECTS (the city / Woland Parity)
# =============================================================================

@dataclass(frozen=True, slots=True)
class CemeteryHeadstoneV1:
    """Record for a killed candidate in the cemetery (the failure gold seam)."""

    candidate_id: str
    run_key: str
    scene_id: str
    cause_of_death: str
    killing_seat_id: str
    evidence_refs: tuple[str, ...]
    candidate_payload_sha256: str
    round_index: int = 0

    def __post_init__(self) -> None:
        identifier(self.candidate_id, "candidate_id")
        identifier(self.run_key, "run_key")
        identifier(self.scene_id, "scene_id")
        text(self.cause_of_death, "cause_of_death")
        identifier(self.killing_seat_id, "killing_seat_id")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", allow_empty=True),
        )
        digest(self.candidate_payload_sha256, "candidate_payload_sha256")
        integer(self.round_index, "round_index", minimum=0)

    @property
    def headstone_id(self) -> str:
        return semantic_id(
            "omega.oeas.headstone.v1",
            {
                "run_key": self.run_key,
                "scene_id": self.scene_id,
                "candidate_id": self.candidate_id,
                "cause_of_death": self.cause_of_death,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "headstone_id": self.headstone_id,
            "candidate_id": self.candidate_id,
            "run_key": self.run_key,
            "scene_id": self.scene_id,
            "cause_of_death": self.cause_of_death,
            "killing_seat_id": self.killing_seat_id,
            "evidence_refs": list(self.evidence_refs),
            "candidate_payload_sha256": self.candidate_payload_sha256,
            "round_index": self.round_index,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "CemeteryHeadstoneV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "headstone_id",
                    "candidate_id",
                    "run_key",
                    "scene_id",
                    "cause_of_death",
                    "killing_seat_id",
                    "evidence_refs",
                    "candidate_payload_sha256",
                    "round_index",
                }
            ),
            "cemetery headstone",
        )
        parsed = cls(
            candidate_id=identifier(wire["candidate_id"], "candidate_id"),
            run_key=identifier(wire["run_key"], "run_key"),
            scene_id=identifier(wire["scene_id"], "scene_id"),
            cause_of_death=text(wire["cause_of_death"], "cause_of_death"),
            killing_seat_id=identifier(wire["killing_seat_id"], "killing_seat_id"),
            evidence_refs=wire_tuple(wire["evidence_refs"], "evidence_refs"),
            candidate_payload_sha256=digest(
                wire["candidate_payload_sha256"], "candidate_payload_sha256"
            ),
            round_index=integer(wire.get("round_index", 0), "round_index"),
        )
        if digest(wire["headstone_id"], "headstone_id") != parsed.headstone_id:
            raise ValueError("cemetery headstone identity does not match its payload")
        return parsed


@dataclass(frozen=True, slots=True)
class AntibodyEntryV1:
    """Active negative constraint entry accumulated from recurring failures."""

    antibody_id: str
    failure_pattern: str
    occurrences: int
    constraint_rule: str
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        identifier(self.antibody_id, "antibody_id")
        text(self.failure_pattern, "failure_pattern")
        integer(self.occurrences, "occurrences", minimum=1)
        text(self.constraint_rule, "constraint_rule")
        identifier(self.status, "status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "antibody_id": self.antibody_id,
            "failure_pattern": self.failure_pattern,
            "occurrences": self.occurrences,
            "constraint_rule": self.constraint_rule,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "AntibodyEntryV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "antibody_id",
                    "failure_pattern",
                    "occurrences",
                    "constraint_rule",
                    "status",
                }
            ),
            "antibody entry",
        )
        return cls(
            antibody_id=identifier(wire["antibody_id"], "antibody_id"),
            failure_pattern=text(wire["failure_pattern"], "failure_pattern"),
            occurrences=integer(wire["occurrences"], "occurrences"),
            constraint_rule=text(wire["constraint_rule"], "constraint_rule"),
            status=identifier(wire["status"], "status"),
        )


@dataclass(frozen=True, slots=True)
class GenealogyEntryV1:
    """Re-entry lineage link recording parent->child mutation details."""

    parent_run_key: str
    child_run_key: str
    structural_deficiencies: tuple[str, ...]
    concrete_fixes: tuple[str, ...]
    next_run_guidance: str
    re_entry_reason: str = "COMPOST_GUIDED_MUTATION"

    def __post_init__(self) -> None:
        identifier(self.parent_run_key, "parent_run_key")
        identifier(self.child_run_key, "child_run_key")
        object.__setattr__(
            self,
            "structural_deficiencies",
            string_tuple(
                self.structural_deficiencies, "structural_deficiencies"
            ),
        )
        object.__setattr__(
            self,
            "concrete_fixes",
            string_tuple(self.concrete_fixes, "concrete_fixes"),
        )
        text(self.next_run_guidance, "next_run_guidance")
        identifier(self.re_entry_reason, "re_entry_reason")

    @property
    def lineage_id(self) -> str:
        return semantic_id(
            "omega.oeas.genealogy.v1",
            {
                "parent_run_key": self.parent_run_key,
                "child_run_key": self.child_run_key,
                "re_entry_reason": self.re_entry_reason,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "parent_run_key": self.parent_run_key,
            "child_run_key": self.child_run_key,
            "structural_deficiencies": list(self.structural_deficiencies),
            "concrete_fixes": list(self.concrete_fixes),
            "next_run_guidance": self.next_run_guidance,
            "re_entry_reason": self.re_entry_reason,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "GenealogyEntryV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "lineage_id",
                    "parent_run_key",
                    "child_run_key",
                    "structural_deficiencies",
                    "concrete_fixes",
                    "next_run_guidance",
                    "re_entry_reason",
                }
            ),
            "genealogy entry",
        )
        parsed = cls(
            parent_run_key=identifier(wire["parent_run_key"], "parent_run_key"),
            child_run_key=identifier(wire["child_run_key"], "child_run_key"),
            structural_deficiencies=wire_tuple(
                wire["structural_deficiencies"], "structural_deficiencies"
            ),
            concrete_fixes=wire_tuple(wire["concrete_fixes"], "concrete_fixes"),
            next_run_guidance=text(
                wire["next_run_guidance"], "next_run_guidance"
            ),
            re_entry_reason=identifier(wire["re_entry_reason"], "re_entry_reason"),
        )
        if digest(wire["lineage_id"], "lineage_id") != parsed.lineage_id:
            raise ValueError("genealogy identity does not match its payload")
        return parsed



@dataclass(frozen=True)
class PromptPerception:
    """Prompt perception metrics extracted from input payload."""

    prompt_class: str = "Assertion"
    prompt_length: int = 0
    complexity_rank: int = 1
    intent_family: str = "Directive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_class": self.prompt_class,
            "prompt_length": self.prompt_length,
            "complexity_rank": self.complexity_rank,
            "intent_family": self.intent_family,
        }



class PromptViewEngineV1:
    """Derives projection views of prompt genomes bound to declared ledger revisions."""

    def derive_view(self, genome: PromptGenomeV1, ledger_revision: int) -> PromptViewV1:
        return PromptViewV1(
            prompt_id=genome.prompt_id,
            ledger_revision=ledger_revision,
            current_custody=genome.birth_custody,
        )


class PromptGenomeRegistryV1:
    """Content-addressed registry managing prompt genomes and occurrences."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._genomes: Dict[str, PromptGenomeV1] = {}
        self._occurrences: Dict[str, ExecutionOccurrenceV1] = {}

    def register_genome(self, genome: PromptGenomeV1) -> None:
        with self._lock:
            self._genomes[genome.prompt_id] = genome

    def get_genome(self, prompt_id: str) -> Optional[PromptGenomeV1]:
        with self._lock:
            return self._genomes.get(prompt_id)

    def record_occurrence(self, occurrence: ExecutionOccurrenceV1) -> None:
        with self._lock:
            self._occurrences[occurrence.occurrence_id] = occurrence

    def record_execution(
        self,
        prompt_id: str,
        session_id: str,
        input_packet_id: str,
        output_packet_id: str,
    ) -> ExecutionOccurrenceV1:
        raw = f"{prompt_id}:{session_id}:{input_packet_id}:{output_packet_id}".encode("utf-8")
        occ_id = f"occ_{hashlib.sha256(raw).hexdigest()[:16]}"
        occ = ExecutionOccurrenceV1(
            occurrence_id=occ_id,
            prompt_id=prompt_id,
            session_id=session_id,
            input_packet_id=input_packet_id,
            output_packet_id=output_packet_id,
        )
        self.record_occurrence(occ)
        return occ

    def get_occurrences_for_prompt(self, prompt_id: str) -> List[ExecutionOccurrenceV1]:
        with self._lock:
            return [occ for occ in self._occurrences.values() if occ.prompt_id == prompt_id]

    def total_genome_count(self) -> int:
        with self._lock:
            return len(self._genomes)

    def total_occurrence_count(self) -> int:
        with self._lock:
            return len(self._occurrences)


__all__ = [
    "AntibodyEntryV1",
    "CemeteryHeadstoneV1",
    "CivilizationPrompt",
    "CivilizationState",
    "CustodyTier",
    "DomainPlacementV1",
    "ExecutionOccurrenceV1",
    "GenealogyEntryV1",
    "PopulationTier",
    "PromotionDecision",
    "PromptGenomeV1",
    "PromptPerception",
    "PromptViewV1",
    "PromptGenomeRegistryV1",
    "PromptViewEngineV1",
    "ProtectedSpanV1",
    "UnauthorizedAdmissionError",
    "hard_domain_eligible",
]
