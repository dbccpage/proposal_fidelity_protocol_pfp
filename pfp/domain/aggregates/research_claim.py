"""Domain models, enums, schemas, and validation invariants for research claims and run roots.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_bytes,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
    thaw,
)
from pfp.domain.validation import (
    MAX_ARRAY_LENGTH,
    MAX_PATH_LENGTH,
    MAX_STRING_LENGTH,
    _fail,
    _require_bool,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_optional_digest,
    _require_optional_nonnegative_int,
    _require_positive_int,
    _require_stable_id,
    _require_string,
    _string_tuple_from_wire,
    _validate_ordered_unique_strings,
    _validate_repo_relative_path,
    is_valid_hex64,
)

# ---------------------------------------------------------------------------
# Schemas & Consts
# ---------------------------------------------------------------------------

RESEARCH_CLAIM_SCHEMA = "core.symbol-game.research-claim.v1"
SOURCE_ARTIFACT_SCHEMA = "core.symbol-game.source-artifact.v1"
RESEARCH_CLAIM_ITEM_SCHEMA = "core.symbol-game.research-claim-item.v1"
SOURCE_INTAKE_SCHEMA = "core.symbol-game.source-intake-receipt.v1"
SOURCE_INTAKE_BUNDLE_SCHEMA = "core.symbol-game.source-intake-bundle.v1"
RUN_ROOT_SCHEMA = "core.symbol-game.research-run-root.v1"
SEMANTIC_STEP_SCHEMA = "core.symbol-game.semantic-dda-step.v1"

RESEARCH_PACKET_FAMILY = "research_claim"
WITTEN_FINITE_FAMILY = "witten_airy_finite_v1"
WITTEN_FULL_FAMILY = "witten_chern_simons_full_v1"
GR_FINITE_FAMILY = "gr_constraint_closure_finite_v1"
GR_STRETCH_FAMILY = "gr_stretch_claims_v1"

EVALUATE_FINITE = "evaluate_finite"
REFUSE_UNSUPPORTED = "refuse_unsupported"
LOCAL_REPLAYABLE_FINITE_EVIDENCE = "LocalReplayableFiniteEvidence"
REFUSAL_ONLY = "RefusalOnly"

RESEARCH_FAMILIES = frozenset(
    {
        WITTEN_FINITE_FAMILY,
        WITTEN_FULL_FAMILY,
        GR_FINITE_FAMILY,
        GR_STRETCH_FAMILY,
    }
)
FINITE_FAMILIES = frozenset({WITTEN_FINITE_FAMILY, GR_FINITE_FAMILY})
REFUSAL_FAMILIES = frozenset({WITTEN_FULL_FAMILY, GR_STRETCH_FAMILY})

SOURCE_ROLES = frozenset(
    {
        "primary_source",
        "implementation",
        "formalization",
        "test_fixture",
        "derived_evidence",
    }
)
SOURCE_NORMALIZATIONS = frozenset({"raw-bytes", "utf8-lf-v1"})

RESEARCH_ENVELOPE_CONSTRAINTS = (
    "authority_effect_none",
    "bounded_resources",
    "content_addressed_canonical_payload",
    "deterministic_hash_binding",
    "immutable_state",
    "local_replayable_evidence",
    "no_ambient_io",
    "no_claim_promotion",
    "strict_refusal_matching",
    "untrusted_proposals_isolated",
)
RESEARCH_TERMINAL_TARGET = "human_review"
RESEARCH_EVIDENCE_CEILING = "local_replayable_evidence_only"
RESEARCH_ORACLE_POLICY = "none"
REFUSAL_REFUSAL_ERASURE = "REFUSAL_ERASURE"
REFUSAL_MARKDOWN_CLAIM_INJECTION = "MARKDOWN_CLAIM_INJECTION"
RESEARCH_ALLOWED_TRANSFORMS = ("canonical_wire",)

SOURCE_MANIFEST_DOMAIN = "core.symbol-game.research-source-manifest.v1"
CLAIM_MANIFEST_DOMAIN = "core.symbol-game.research-claim-manifest.v1"
INITIAL_STATE_DOMAIN = "core.symbol-game.research-initial-state.v1"
PAYLOAD_DOMAIN = "core.symbol-game.research-payload.v1"
SOURCE_INTAKE_BUNDLE_DOMAIN = "core.symbol-game.source-intake-bundle.v1"

RESEARCH_PACKET_MEDIA_TYPE = "application/vnd.core.research-packet+json"
SOURCE_INTAKE_MEDIA_TYPE = "application/vnd.core.source-intake+json"
DDA_TRACE_MEDIA_TYPE = "application/x-core-dda-trace+jsonl"
OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE = "application/vnd.core.oesos-evidence+json"

MAX_SOURCES = 16
MAX_CLAIMS = 32
MAX_CANONICAL_PAYLOAD_BYTES = 256 * 1024
MAX_INITIAL_STATE_WIRE_BYTES = 256 * 1024
MAX_ID_LENGTH = 128
MAX_INITIAL_COLLECTION_ITEMS = 4096
MAX_INITIAL_DEPTH = 64
MAX_SOURCE_BYTES = 64 * 1024 * 1024

MAX_TRACE_BYTES = 16 * 1024 * 1024
MAX_TRACE_LINE_BYTES = 1024 * 1024
MAX_TRACE_STEPS = 4096
MAX_SEMANTIC_DEPTH = 64
MAX_SEMANTIC_COLLECTION_ITEMS = 4096
MAX_RUN_ROOT_ARTIFACTS = 256
MAX_RUN_ROOT_CODES = 256
MAX_RUN_ROOT_STRING_BYTES = 8192

ARTIFACT_AVAILABILITIES = frozenset({"AVAILABLE", "BOUND_ONLY", "MISSING"})
RESEARCH_TERMINAL_STATUSES = frozenset(
    {
        "FINITE_NUMERICAL_SHADOW_CLOSED",
        "FINITE_NUMERICAL_SHADOW_CLOSED_EXTERNAL_SOURCE_BYTES_REQUIRED",
        "FINITE_NUMERICAL_SHADOW_CLOSED_SOURCE_UNVERIFIED",
        "FINITE_RESIDUAL_CLOSED",
        "REFUSED",
    }
)
RESEARCH_EVIDENCE_PROFILES = frozenset({"LocalReplayableFiniteEvidence", "RefusalOnly"})
_FAMILY_TERMINAL_STATUSES = {
    "witten_airy_finite_v1": frozenset(
        {
            "FINITE_NUMERICAL_SHADOW_CLOSED",
            "FINITE_NUMERICAL_SHADOW_CLOSED_EXTERNAL_SOURCE_BYTES_REQUIRED",
            "FINITE_NUMERICAL_SHADOW_CLOSED_SOURCE_UNVERIFIED",
            "REFUSED",
        }
    ),
    "gr_constraint_closure_finite_v1": frozenset({"FINITE_RESIDUAL_CLOSED", "REFUSED"}),
    "witten_chern_simons_full_v1": frozenset({"REFUSED"}),
    "gr_stretch_claims_v1": frozenset({"REFUSED"}),
}
_REFUSAL_FAMILIES = frozenset({"witten_chern_simons_full_v1", "gr_stretch_claims_v1"})

OCCURRENCE_ONLY_KEYS = frozenset(
    {
        "artifact_path",
        "challenge",
        "challenge_id",
        "created_at",
        "jsonl_path",
        "nonce",
        "occurrence_id",
        "oesos_trace",
        "output_path",
        "packet_artifact",
        "path",
        "prev_step_hash",
        "recorded_at",
        "run_id",
        "runner_id",
        "step_hash",
        "step_id",
        "source_intake_artifact",
        "temp_path",
        "temporary_path",
        "timestamp",
        "timestamp_utc",
        "trace_path",
        "uuid",
        "uuid_hex",
    }
)

_RESERVED_INITIAL_KEYS = frozenset(
    {
        "accepted",
        "authority",
        "authority_effect",
        "authorization",
        "authorized",
        "certified",
        "claim_valid",
        "passed",
        "promote",
        "promotion",
        "promotion_eligible",
        "proof_status",
        "proved",
        "succeeded",
        "success",
        "successful",
        "theorem_status",
        "trusted",
        "valid",
        "validity",
        "verified",
    }
)

RESEARCH_FAMILY_OWNER_LAWS = {
    WITTEN_FINITE_FAMILY: (
        "witten-airy-finite-five-slot-and-flow-v1",
        (
            "finite_evidence_does_not_imply_full_chern_simons",
            "source_bytes_do_not_prove_transcription",
            "witten_airy_critical_equation",
        ),
    ),
    WITTEN_FULL_FAMILY: (
        "witten-full-scope-unconstructed-v1",
        (
            "finite_evidence_does_not_imply_full_chern_simons",
            "unsupported_claims_remain_refused",
        ),
    ),
    GR_FINITE_FAMILY: (
        "finite-cochain-2-v1",
        (
            "cochain_gamma2",
            "cochain_phi1",
            "exact_rational_cochain",
            "l1_norm_ball",
        ),
    ),
    GR_STRETCH_FAMILY: (
        "gr-continuum-geometry-refusal-v1",
        (
            "continuum_from_finite_refused",
            "unsupported_claims_remain_refused",
        ),
    ),
}

_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class ResearchRunRootError(ValueError):
    """Raised when a semantic run root or one of its artifacts fails closed."""


# ---------------------------------------------------------------------------
# Enums from research_packets
# ---------------------------------------------------------------------------

class ClaimKind(Enum):
    DEFINITION = "definition"
    DERIVATION = "derivation"
    OBSTRUCTION = "obstruction"
    REPAIR = "repair"
    REFUTATION_CANDIDATE = "refutation_candidate"


class EvidenceCeiling(Enum):
    EXPLORATORY_ONLY = "exploratory_only"
    BOUNDARY_CHECKED = "boundary_checked"


class ResearchMode(Enum):
    EXPLORATORY = "exploratory"
    STRICT = "strict"


class StepRealization(Enum):
    STRUCTURAL = "structural"
    MECHANICAL = "mechanical"


class AuthorityEffect(Enum):
    None_ = "None"


# ---------------------------------------------------------------------------
# Initial State & Canonical Helpers
# ---------------------------------------------------------------------------

def _require_exact_dict(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        _fail(f"{label} must be an exact string-keyed object")
    return value


def _canonical_json_size(value: Any) -> int:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError("value is not strict JSON data") from exc
    return len(encoded)


def _canonical_string_value(node: Any, label: str) -> str:
    if (
        type(node) is not list
        or len(node) != 3
        or node[0] != "core-canonical-v1"
        or node[1] != "string"
        or type(node[2]) is not str
    ):
        _fail(f"{label} is not a canonical string")
    return _require_string(node[2], label)


def _validate_initial_state_node(node: Any, *, depth: int = 0) -> None:
    """Restrict initial state to a bounded, authority-free primitive algebra."""
    if depth > MAX_INITIAL_DEPTH:
        _fail("initial_state_payload exceeds the nesting resource limit")
    if type(node) is not list or len(node) != 3:
        _fail("initial_state_payload is not canonical wire")
    marker, tag, body = node
    if marker != "core-canonical-v1" or type(tag) is not str:
        _fail("initial_state_payload is not canonical wire")
    if tag in {"null", "bool", "int", "string"}:
        if tag == "string":
            _require_string(body, "initial state string")
        return
    if tag in {"float", "bytes"}:
        if type(body) is not list or len(body) != 1:
            _fail("initial_state_payload scalar encoding is invalid")
        _validate_initial_state_node(body[0], depth=depth + 1)
        return
    if tag in {"list", "tuple"}:
        if type(body) is not list or len(body) > MAX_INITIAL_COLLECTION_ITEMS:
            _fail("initial_state_payload collection exceeds its resource limit")
        for item in body:
            _validate_initial_state_node(item, depth=depth + 1)
        return
    if tag == "mapping":
        if type(body) is not list or len(body) < 2:
            _fail("initial_state_payload mapping encoding is invalid")
        if len(body) - 2 > MAX_INITIAL_COLLECTION_ITEMS:
            _fail("initial_state_payload mapping exceeds its resource limit")
        if (
            _canonical_string_value(body[0], "mapping module") != "builtins"
            or _canonical_string_value(body[1], "mapping type") != "dict"
        ):
            _fail("initial_state_payload mappings must be exact dictionaries")
        for entry in body[2:]:
            if (
                type(entry) is not list
                or len(entry) != 3
                or entry[0] != "core-canonical-v1"
                or entry[1] != "entry"
                or type(entry[2]) is not list
                or len(entry[2]) != 2
            ):
                _fail("initial_state_payload mapping entry is invalid")
            key = _canonical_string_value(entry[2][0], "initial state key")
            normalized_key = key.strip().lower().replace("-", "_")
            if normalized_key in _RESERVED_INITIAL_KEYS:
                _fail(f"initial_state_payload key {key!r} is authority-bearing")
            _validate_initial_state_node(entry[2][1], depth=depth + 1)
        return
    _fail(f"initial_state_payload canonical tag {tag!r} is not primitive")


def _validate_initial_state(value: Any) -> Any:
    wire = canonical_wire(value)
    if _canonical_json_size(wire) > MAX_INITIAL_STATE_WIRE_BYTES:
        _fail("initial_state_payload exceeds the canonical resource limit")
    _validate_initial_state_node(wire)
    return freeze(value)


def _source_manifest_root(sources: tuple[SourceArtifactV1, ...]) -> str:
    return domain_digest(
        SOURCE_MANIFEST_DOMAIN,
        {
            "schema_version": SOURCE_ARTIFACT_SCHEMA,
            "sources": [source.to_dict() for source in sources],
        },
    )


def _claim_manifest_root(claims: tuple[ResearchClaimV1, ...]) -> str:
    return domain_digest(
        CLAIM_MANIFEST_DOMAIN,
        {
            "schema_version": RESEARCH_CLAIM_ITEM_SCHEMA,
            "claims": [claim.to_dict() for claim in claims],
        },
    )


# ---------------------------------------------------------------------------
# Source & Claim Artifact Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SourceArtifactV1:
    """One source identity using a repository-relative path and normalized bytes."""

    source_id: str
    path: str
    role: str
    normalization: str
    sha256: str
    byte_count: int
    repository_tracked_expected: bool
    schema_version: str = field(default=SOURCE_ARTIFACT_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        _require_stable_id(self.source_id, "source_id")
        _validate_repo_relative_path(self.path, "source path")
        _require_string(self.role, "source role", nonempty=True)
        if self.role not in SOURCE_ROLES:
            _fail("source role is unsupported")
        _require_string(self.normalization, "source normalization", nonempty=True)
        if self.normalization not in SOURCE_NORMALIZATIONS:
            _fail("source normalization is unsupported")
        _require_digest(self.sha256, "source sha256")
        _require_nonnegative_int(self.byte_count, "source byte_count")
        if self.byte_count > MAX_SOURCE_BYTES:
            _fail("source byte_count exceeds the source resource limit")
        _require_bool(self.repository_tracked_expected, "repository_tracked_expected")
        if self.schema_version != SOURCE_ARTIFACT_SCHEMA:
            _fail("source artifact schema version is unsupported")
        if self.authority_effect != "None":
            _fail("source artifacts must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "path": self.path,
            "role": self.role,
            "normalization": self.normalization,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "repository_tracked_expected": self.repository_tracked_expected,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "SourceArtifactV1":
        wire = _require_exact_dict(wire, "source artifact")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "source_id",
                    "path",
                    "role",
                    "normalization",
                    "sha256",
                    "byte_count",
                    "repository_tracked_expected",
                    "authority_effect",
                }
            ),
            "source artifact",
        )
        return cls(
            source_id=_require_stable_id(wire["source_id"], "source_id"),
            path=_validate_repo_relative_path(wire["path"], "source path"),
            role=_require_string(wire["role"], "source role", nonempty=True),
            normalization=_require_string(
                wire["normalization"], "source normalization", nonempty=True
            ),
            sha256=_require_digest(wire["sha256"], "source sha256"),
            byte_count=_require_nonnegative_int(
                wire["byte_count"], "source byte_count"
            ),
            repository_tracked_expected=_require_bool(
                wire["repository_tracked_expected"],
                "repository_tracked_expected",
            ),
            schema_version=_require_string(
                wire["schema_version"], "source schema", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "source authority effect", nonempty=True
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchClaimV1:
    """A finite evaluation contract or an explicit unsupported-claim refusal."""

    claim_id: str
    statement: str
    disposition: str
    source_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    units: str
    carrier: str
    coefficient_semantics: str
    projection: str
    retraction: str
    obstruction: str
    detector: str
    comparison_map: str
    falsifier: str
    independent_checker: str
    unresolved_obligations: tuple[str, ...]
    evidence_ceiling: str
    schema_version: str = field(default=RESEARCH_CLAIM_ITEM_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        _require_stable_id(self.claim_id, "claim_id")
        _require_string(self.statement, "claim statement", nonempty=True)
        _require_string(self.disposition, "claim disposition", nonempty=True)
        if self.disposition not in {EVALUATE_FINITE, REFUSE_UNSUPPORTED}:
            _fail("claim disposition is unsupported")
        _validate_ordered_unique_strings(self.source_ids, "claim source_ids")
        if not self.source_ids:
            _fail("claims must bind at least one source")
        _validate_ordered_unique_strings(self.assumptions, "claim assumptions")
        _validate_ordered_unique_strings(
            self.unresolved_obligations, "claim unresolved_obligations"
        )
        for label, value in (
            ("units", self.units),
            ("carrier", self.carrier),
            ("coefficient_semantics", self.coefficient_semantics),
            ("projection", self.projection),
            ("retraction", self.retraction),
            ("obstruction", self.obstruction),
            ("detector", self.detector),
            ("comparison_map", self.comparison_map),
            ("falsifier", self.falsifier),
            ("independent_checker", self.independent_checker),
        ):
            _require_string(value, f"claim {label}")
        _require_string(self.evidence_ceiling, "claim evidence_ceiling", nonempty=True)
        if self.disposition == EVALUATE_FINITE:
            required_mechanics = (
                ("units", self.units),
                ("carrier", self.carrier),
                ("coefficient_semantics", self.coefficient_semantics),
                ("projection", self.projection),
                ("retraction", self.retraction),
                ("obstruction", self.obstruction),
                ("detector", self.detector),
                ("comparison_map", self.comparison_map),
                ("falsifier", self.falsifier),
                ("independent_checker", self.independent_checker),
            )
            for label, value in required_mechanics:
                _require_string(value, f"finite claim {label}", nonempty=True)
            if self.unresolved_obligations:
                _fail("finite evaluation claims cannot carry unresolved obligations")
            if self.evidence_ceiling != LOCAL_REPLAYABLE_FINITE_EVIDENCE:
                _fail("finite evaluation claims have a local replay evidence ceiling")
        else:
            if not self.unresolved_obligations:
                _fail("unsupported claims require unresolved obligations")
            if self.evidence_ceiling != REFUSAL_ONLY:
                _fail("unsupported claims have a refusal-only evidence ceiling")
        if self.schema_version != RESEARCH_CLAIM_ITEM_SCHEMA:
            _fail("research claim schema version is unsupported")
        if self.authority_effect != "None":
            _fail("research claims must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "claim_id": self.claim_id,
            "statement": self.statement,
            "disposition": self.disposition,
            "source_ids": list(self.source_ids),
            "assumptions": list(self.assumptions),
            "units": self.units,
            "carrier": self.carrier,
            "coefficient_semantics": self.coefficient_semantics,
            "projection": self.projection,
            "retraction": self.retraction,
            "obstruction": self.obstruction,
            "detector": self.detector,
            "comparison_map": self.comparison_map,
            "falsifier": self.falsifier,
            "independent_checker": self.independent_checker,
            "unresolved_obligations": list(self.unresolved_obligations),
            "evidence_ceiling": self.evidence_ceiling,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "ResearchClaimV1":
        wire = _require_exact_dict(wire, "research claim")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "claim_id",
                    "statement",
                    "disposition",
                    "source_ids",
                    "assumptions",
                    "units",
                    "carrier",
                    "coefficient_semantics",
                    "projection",
                    "retraction",
                    "obstruction",
                    "detector",
                    "comparison_map",
                    "falsifier",
                    "independent_checker",
                    "unresolved_obligations",
                    "evidence_ceiling",
                    "authority_effect",
                }
            ),
            "research claim",
        )
        return cls(
            claim_id=_require_stable_id(wire["claim_id"], "claim_id"),
            statement=_require_string(
                wire["statement"], "claim statement", nonempty=True
            ),
            disposition=_require_string(
                wire["disposition"], "claim disposition", nonempty=True
            ),
            source_ids=_string_tuple_from_wire(wire["source_ids"], "claim source_ids"),
            assumptions=_string_tuple_from_wire(
                wire["assumptions"], "claim assumptions"
            ),
            units=_require_string(wire["units"], "claim units"),
            carrier=_require_string(wire["carrier"], "claim carrier"),
            coefficient_semantics=_require_string(
                wire["coefficient_semantics"], "claim coefficient_semantics"
            ),
            projection=_require_string(wire["projection"], "claim projection"),
            retraction=_require_string(wire["retraction"], "claim retraction"),
            obstruction=_require_string(wire["obstruction"], "claim obstruction"),
            detector=_require_string(wire["detector"], "claim detector"),
            comparison_map=_require_string(
                wire["comparison_map"], "claim comparison_map"
            ),
            falsifier=_require_string(wire["falsifier"], "claim falsifier"),
            independent_checker=_require_string(
                wire["independent_checker"], "claim independent_checker"
            ),
            unresolved_obligations=_string_tuple_from_wire(
                wire["unresolved_obligations"], "claim unresolved_obligations"
            ),
            evidence_ceiling=_require_string(
                wire["evidence_ceiling"], "claim evidence_ceiling", nonempty=True
            ),
            schema_version=_require_string(
                wire["schema_version"], "claim schema", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "claim authority effect", nonempty=True
            ),
        )


@dataclass(frozen=True, slots=True)
class ResearchClaimPayloadV1:
    """A family-typed collection of sources, claims, and initial state."""

    family: str
    disposition: str
    sources: tuple[SourceArtifactV1, ...]
    claims: tuple[ResearchClaimV1, ...]
    initial_state_payload: Any
    source_manifest_root: str = field(default="")
    claim_manifest_root: str = field(default="")
    initial_state_hash: str = field(default="")
    schema_version: str = field(default=RESEARCH_CLAIM_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        _require_string(self.family, "research family", nonempty=True)
        if self.family not in RESEARCH_FAMILIES:
            _fail("research family is unsupported")
        _require_string(self.disposition, "payload disposition", nonempty=True)
        expected_disposition = (
            EVALUATE_FINITE if self.family in FINITE_FAMILIES else REFUSE_UNSUPPORTED
        )
        if self.disposition != expected_disposition:
            _fail("research family and disposition do not match")
        if type(self.sources) is not tuple or any(
            not isinstance(source, SourceArtifactV1) for source in self.sources
        ):
            _fail("payload sources must be a tuple of SourceArtifactV1")
        if type(self.claims) is not tuple or any(
            not isinstance(claim, ResearchClaimV1) for claim in self.claims
        ):
            _fail("payload claims must be a tuple of ResearchClaimV1")
        if not self.sources or not self.claims:
            _fail("research payloads require sources and claims")
        if len(self.sources) > MAX_SOURCES:
            _fail("research payload exceeds the source resource limit")
        if len(self.claims) > MAX_CLAIMS:
            _fail("research payload exceeds the claim resource limit")
        source_ids = tuple(source.source_id for source in self.sources)
        claim_ids = tuple(claim.claim_id for claim in self.claims)
        if source_ids != tuple(sorted(source_ids)) or len(source_ids) != len(
            set(source_ids)
        ):
            _fail("payload sources must have unique source IDs in sorted order")
        source_paths = tuple(source.path for source in self.sources)
        if len(source_paths) != len(set(source_paths)):
            _fail("payload source paths must be unique")
        if claim_ids != tuple(sorted(claim_ids)) or len(claim_ids) != len(
            set(claim_ids)
        ):
            _fail("payload claims must have unique claim IDs in sorted order")
        known_sources = set(source_ids)
        for claim in self.claims:
            if claim.disposition != self.disposition:
                _fail("claim disposition does not match its research family")
            if not set(claim.source_ids).issubset(known_sources):
                _fail("claim source_ids must resolve within the source manifest")

        # Freeze and validate initial state
        validated_initial = _validate_initial_state(self.initial_state_payload)
        object.__setattr__(self, "initial_state_payload", validated_initial)

        expected_source_root = _source_manifest_root(self.sources)
        expected_claim_root = _claim_manifest_root(self.claims)
        expected_initial_hash = domain_digest(
            INITIAL_STATE_DOMAIN,
            {
                "family": self.family,
                "initial_state_payload": validated_initial,
            },
        )

        if not self.source_manifest_root:
            object.__setattr__(
                self, "source_manifest_root", expected_source_root
            )
        elif self.source_manifest_root != expected_source_root:
            _fail("source_manifest_root does not match the declared sources")

        if not self.claim_manifest_root:
            object.__setattr__(self, "claim_manifest_root", expected_claim_root)
        elif self.claim_manifest_root != expected_claim_root:
            _fail("claim_manifest_root does not match the declared claims")

        if not self.initial_state_hash:
            object.__setattr__(
                self, "initial_state_hash", expected_initial_hash
            )
        elif self.initial_state_hash != expected_initial_hash:
            _fail("initial_state_hash does not match the initial state payload")

        if self.schema_version != RESEARCH_CLAIM_SCHEMA:
            _fail("research payload schema version is unsupported")
        if self.authority_effect != "None":
            _fail("research payloads must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "disposition": self.disposition,
            "source_manifest_root": self.source_manifest_root,
            "claim_manifest_root": self.claim_manifest_root,
            "initial_state_hash": self.initial_state_hash,
            "sources": [source.to_dict() for source in self.sources],
            "claims": [claim.to_dict() for claim in self.claims],
            "initial_state_payload": canonical_wire(self.initial_state_payload),
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "ResearchClaimPayloadV1":
        wire = _require_exact_dict(wire, "research claim payload")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "family",
                    "disposition",
                    "sources",
                    "source_manifest_root",
                    "claims",
                    "claim_manifest_root",
                    "initial_state_payload",
                    "initial_state_hash",
                    "authority_effect",
                }
            ),
            "research claim payload",
        )
        raw_sources = wire["sources"]
        raw_claims = wire["claims"]
        if type(raw_sources) is not list:
            _fail("payload sources must be an array")
        if type(raw_claims) is not list:
            _fail("payload claims must be an array")
        if len(raw_sources) > MAX_SOURCES:
            _fail("research payload exceeds the source resource limit")
        if len(raw_claims) > MAX_CLAIMS:
            _fail("research payload exceeds the claim resource limit")
        if _canonical_json_size(wire) > MAX_CANONICAL_PAYLOAD_BYTES:
            _fail("research payload exceeds the canonical resource limit")
        try:
            initial_state_payload = canonical_unwire(wire["initial_state_payload"])
        except (CanonicalizationError, TypeError) as exc:
            raise CanonicalizationError(
                "initial_state_payload is not canonical wire"
            ) from exc
        return cls(
            family=_require_string(wire["family"], "research family", nonempty=True),
            disposition=_require_string(
                wire["disposition"], "payload disposition", nonempty=True
            ),
            sources=tuple(SourceArtifactV1.from_dict(item) for item in raw_sources),
            claims=tuple(ResearchClaimV1.from_dict(item) for item in raw_claims),
            initial_state_payload=initial_state_payload,
            source_manifest_root=_require_digest(
                wire["source_manifest_root"], "source_manifest_root"
            ),
            claim_manifest_root=_require_digest(
                wire["claim_manifest_root"], "claim_manifest_root"
            ),
            initial_state_hash=_require_digest(
                wire["initial_state_hash"], "initial_state_hash"
            ),
            schema_version=_require_string(
                wire["schema_version"], "payload schema", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "payload authority effect", nonempty=True
            ),
        )

    @property
    def payload_digest(self) -> str:
        return domain_digest(PAYLOAD_DOMAIN, self.to_dict())

    @property
    def payload_id(self) -> str:
        return self.payload_digest


@dataclass(frozen=True, slots=True)
class SourceIntakeReceiptV1:
    """Local, non-authoritative comparison of one source against its manifest."""

    source_id: str
    path: str
    normalization: str
    available: bool
    expected_sha256: str
    observed_sha256: str | None
    hash_matches: bool
    expected_byte_count: int
    observed_byte_count: int | None
    size_matches: bool
    repository_tracked_expected: bool
    schema_version: str = field(default=SOURCE_INTAKE_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        _require_stable_id(self.source_id, "source_id")
        _validate_repo_relative_path(self.path, "source path")
        if self.normalization not in SOURCE_NORMALIZATIONS:
            _fail("source normalization is unsupported")
        _require_bool(self.available, "source availability")
        _require_digest(self.expected_sha256, "expected source sha256")
        _require_nonnegative_int(self.expected_byte_count, "expected source byte_count")
        _require_bool(self.hash_matches, "hash_matches")
        _require_bool(self.size_matches, "size_matches")
        _require_bool(self.repository_tracked_expected, "repository_tracked_expected")
        if self.observed_sha256 is not None:
            _require_digest(self.observed_sha256, "observed source sha256")
        if self.observed_byte_count is not None:
            _require_nonnegative_int(
                self.observed_byte_count, "observed source byte_count"
            )
        if self.available != (
            self.observed_sha256 is not None and self.observed_byte_count is not None
        ):
            _fail("source availability and observed values disagree")
        if self.hash_matches != (
            self.available and self.observed_sha256 == self.expected_sha256
        ):
            _fail("hash_matches does not match the observed source")
        if self.size_matches != (
            self.available and self.observed_byte_count == self.expected_byte_count
        ):
            _fail("size_matches does not match the observed source")
        if self.schema_version != SOURCE_INTAKE_SCHEMA:
            _fail("source intake schema version is unsupported")
        if self.authority_effect != "None":
            _fail("source intake receipts must carry AuthorityEffect None")

    @property
    def verified(self) -> bool:
        return self.available and self.hash_matches and self.size_matches

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "path": self.path,
            "normalization": self.normalization,
            "available": self.available,
            "expected_sha256": self.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "hash_matches": self.hash_matches,
            "expected_byte_count": self.expected_byte_count,
            "observed_byte_count": self.observed_byte_count,
            "size_matches": self.size_matches,
            "repository_tracked_expected": self.repository_tracked_expected,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "SourceIntakeReceiptV1":
        wire = _require_exact_dict(wire, "source intake receipt")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "source_id",
                    "path",
                    "normalization",
                    "available",
                    "expected_sha256",
                    "observed_sha256",
                    "hash_matches",
                    "expected_byte_count",
                    "observed_byte_count",
                    "size_matches",
                    "repository_tracked_expected",
                    "authority_effect",
                }
            ),
            "source intake receipt",
        )
        return cls(
            source_id=_require_stable_id(wire["source_id"], "source_id"),
            path=_validate_repo_relative_path(wire["path"], "source path"),
            normalization=_require_string(
                wire["normalization"], "source normalization", nonempty=True
            ),
            available=_require_bool(wire["available"], "source availability"),
            expected_sha256=_require_digest(
                wire["expected_sha256"], "expected source sha256"
            ),
            observed_sha256=_require_optional_digest(
                wire["observed_sha256"], "observed source sha256"
            ),
            hash_matches=_require_bool(wire["hash_matches"], "hash_matches"),
            expected_byte_count=_require_nonnegative_int(
                wire["expected_byte_count"], "expected source byte_count"
            ),
            observed_byte_count=_require_optional_nonnegative_int(
                wire["observed_byte_count"], "observed source byte_count"
            ),
            size_matches=_require_bool(wire["size_matches"], "size_matches"),
            repository_tracked_expected=_require_bool(
                wire["repository_tracked_expected"],
                "repository_tracked_expected",
            ),
            schema_version=_require_string(
                wire["schema_version"], "source intake schema", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"],
                "source intake authority effect",
                nonempty=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class SourceIntakeBundleV1:
    """One packet-bound aggregate of sorted local source comparisons."""

    packet_id: str
    source_manifest_root: str
    receipts: tuple[SourceIntakeReceiptV1, ...]
    schema_version: str = field(default=SOURCE_INTAKE_BUNDLE_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        _require_digest(self.packet_id, "source intake packet_id")
        _require_digest(self.source_manifest_root, "source_manifest_root")
        if type(self.receipts) is not tuple or any(
            not isinstance(receipt, SourceIntakeReceiptV1) for receipt in self.receipts
        ):
            _fail("source intake receipts must be a tuple of typed receipts")
        if not self.receipts or len(self.receipts) > MAX_SOURCES:
            _fail("source intake bundle has an invalid receipt count")
        source_ids = tuple(receipt.source_id for receipt in self.receipts)
        if source_ids != tuple(sorted(source_ids)) or len(source_ids) != len(
            set(source_ids)
        ):
            _fail("source intake receipts must have unique sorted source IDs")
        if self.schema_version != SOURCE_INTAKE_BUNDLE_SCHEMA:
            _fail("source intake bundle schema version is unsupported")
        if self.authority_effect != "None":
            _fail("source intake bundles must carry AuthorityEffect None")

    @property
    def receipt_id(self) -> str:
        return domain_digest(
            SOURCE_INTAKE_BUNDLE_DOMAIN,
            {
                "schema_version": self.schema_version,
                "packet_id": self.packet_id,
                "source_manifest_root": self.source_manifest_root,
                "receipts": [receipt.to_dict() for receipt in self.receipts],
                "authority_effect": self.authority_effect,
            },
        )

    @property
    def all_verified(self) -> bool:
        return all(receipt.verified for receipt in self.receipts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "packet_id": self.packet_id,
            "source_manifest_root": self.source_manifest_root,
            "receipts": [receipt.to_dict() for receipt in self.receipts],
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "SourceIntakeBundleV1":
        wire = _require_exact_dict(wire, "source intake bundle")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "receipt_id",
                    "packet_id",
                    "source_manifest_root",
                    "receipts",
                    "authority_effect",
                }
            ),
            "source intake bundle",
        )
        raw_receipts = wire["receipts"]
        if type(raw_receipts) is not list:
            _fail("intake bundle receipts must be an array")
        result = cls(
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            source_manifest_root=_require_digest(
                wire["source_manifest_root"], "source_manifest_root"
            ),
            receipts=tuple(
                SourceIntakeReceiptV1.from_dict(item) for item in raw_receipts
            ),
            schema_version=_require_string(
                wire["schema_version"], "bundle schema", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "bundle authority effect", nonempty=True
            ),
        )
        if result.receipt_id != wire["receipt_id"]:
            _fail("receipt_id does not bind the source intake receipts")
        return result


# ---------------------------------------------------------------------------
# Semantic DDA Step & Research Run Root
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SemanticDDAStepV1:
    """Semantic subset of an admitted DDA step line with occurrence noise removed."""

    step_index: int
    letter: str
    effect: str
    action_name: str
    cochain_dim: int
    coboundary_map: str
    input_state: Any
    output_state: Any
    witness: Any
    obstruction_id: str | None
    residual_before: float | None
    residual_after: float | None
    residual_delta: float | None
    residual_energy: float | None
    structure_delta: float | None
    evidence: Any
    refusal_reason: str | None
    authority_effect: str = "None"
    schema_version: str = SEMANTIC_STEP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "step_index": self.step_index,
            "letter": self.letter,
            "effect": self.effect,
            "action_name": self.action_name,
            "cochain_dim": self.cochain_dim,
            "coboundary_map": self.coboundary_map,
            "input_state": canonical_wire(self.input_state),
            "output_state": canonical_wire(self.output_state),
            "witness": canonical_wire(self.witness),
            "obstruction_id": self.obstruction_id,
            "residual_before": self.residual_before,
            "residual_after": self.residual_after,
            "residual_delta": self.residual_delta,
            "residual_energy": self.residual_energy,
            "structure_delta": self.structure_delta,
            "evidence": canonical_wire(self.evidence),
            "refusal_reason": self.refusal_reason,
            "authority_effect": self.authority_effect,
        }


# ---------------------------------------------------------------------------
# Types from research_packets
# ---------------------------------------------------------------------------

@dataclass
class CorpusFileRef:
    path: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        _validate_repo_relative_path(self.path, "corpus file path")
        _require_digest(self.sha256, "corpus file sha256")
        _require_nonnegative_int(self.byte_count, "corpus file byte_count")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
        }


@dataclass
class FrozenCorpus:
    source_root: str
    files: tuple[CorpusFileRef, ...]
    corpus_sha256: str
    schema_version: str = "core.frozen_corpus.v1"

    def __post_init__(self) -> None:
        if not self.source_root or not self.files:
            raise ValueError("a frozen corpus needs a source root and at least one file")
        paths = [item.path for item in self.files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("corpus files must be unique and sorted by path")
        _require_digest(self.corpus_sha256, "corpus_sha256")

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "files": [item.canonical_payload() for item in self.files],
        }

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.files)


@dataclass
class ResearchClaim:
    claim_id: str
    text: str
    kind: ClaimKind
    hypotheses: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    falsifier: str = ""

    def __post_init__(self) -> None:
        if _SAFE_ID.fullmatch(self.claim_id) is None or not self.text.strip():
            raise ValueError("claim_id and claim text must be nonempty and stable")
        if not isinstance(self.kind, ClaimKind):
            raise TypeError("claim kind must be a ClaimKind")
        if self.kind is not ClaimKind.DEFINITION and not self.falsifier.strip():
            raise ValueError("every non-definition claim needs a falsifier")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "kind": self.kind.value,
            "hypotheses": list(self.hypotheses),
            "evidence_refs": list(self.evidence_refs),
            "falsifier": self.falsifier,
        }


@dataclass
class ResearchSeedPacket:
    corpus: FrozenCorpus
    objective: str
    proposer_id: str
    mode: ResearchMode
    round_index: int = 1
    proposal_budget: int = 8
    protected_paths: tuple[str, ...] = ()
    focus_codes: tuple[str, ...] = ()
    parent_ledger_sha256: str | None = None
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.EXPLORATORY_ONLY
    authority_effect: AuthorityEffect = AuthorityEffect.None_
    schema_version: str = "core.research_seed_packet.v1"


@dataclass
class ResearchProposal:
    proposal_id: str
    seed_sha256: str
    model_id: str
    target_path: str
    summary: str
    proposed_change: str
    claims: tuple[ResearchClaim, ...]
    proof_obligations: tuple[str, ...] = ()
    cochain_problem: Mapping[str, Any] | None = None
    declared_cochain_verdict: str | None = None
    requested_terminal: str = "human_review"
    authority_effect: AuthorityEffect = AuthorityEffect.None_
    schema_version: str = "core.research_proposal.v1"


@dataclass
class ResearchStepPacket:
    carrier_sha256: str
    proposal_sha256: str
    round_index: int
    step_index: int
    realization: StepRealization = StepRealization.STRUCTURAL
    verifier_id: str | None = None
    mechanical_evidence_sha256: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.None_


@dataclass
class SymbolGameResearchPacket:
    packet_id: str = "packet_001"
    authority_effect: str = "None"


# Aliases for backward compatibility
ResearchClaimItemV1 = ResearchClaimV1


RESEARCH_CLAIM_FAMILY = "research_claim"
RESEARCH_RUN_ROOT_SCHEMA = "core.symbol-game.research-run-root.v1"

from pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from pfp.domain.entities.source_artifact import (
    SourceArtifactV1,
    SourceIntakeBundleV1,
    SourceIntakeReceiptV1,
    SOURCE_ARTIFACT_SCHEMA,
    SOURCE_INTAKE_BUNDLE_SCHEMA,
    SOURCE_INTAKE_SCHEMA,
)


# Presenter Functions
def canonical_json_artifact_bytes(value: Mapping[str, Any]) -> bytes:
    """Encode a primitive artifact deterministically for content addressing."""
    primitive = _require_exact_dict(value, "JSON artifact")
    return (
        json.dumps(
            primitive,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def render_research_run_root_markdown(root: Any) -> str:
    """Render a human-readable summary of the research run root."""
    lines = [
        f"# Research Run Root Receipt: {getattr(root, 'claim_packet_id', getattr(root, 'packet_id', 'unknown'))}",
        "",
        f"- **Family**: `{getattr(root, 'family_id', getattr(root, 'family', ''))}`",
        f"- **Terminal Status**: `{root.terminal_status}`",
        f"- **Evidence Profile**: `{root.evidence_profile}`",
        f"- **Semantic DDA Root**: `{getattr(root, 'semantic_dda_root', getattr(root, 'semantic_step_chain_root', ''))}`",
        f"- **Authority Effect**: `{root.authority_effect}`",
    ]
    return "\n".join(lines) + "\n"


def verify_markdown_does_not_mutate_claims(
    root_or_text: Any,
    markdown_or_packet_id: str,
) -> None:
    """Defensive check that markdown presentation does not smuggle claims or alter IDs."""
    if isinstance(root_or_text, str):
        if markdown_or_packet_id not in root_or_text:
            raise ValueError(f"rendered markdown omitted expected packet_id: {markdown_or_packet_id}")
        return
    markdown = markdown_or_packet_id
    if type(markdown) is not str:
        raise TypeError("markdown must be a string")
    refusals = getattr(root_or_text, "refusals", ())
    for code in refusals:
        if f"`{code}`" not in markdown:
            _fail(REFUSAL_REFUSAL_ERASURE)
    forbidden_phrases = (
        "promotion_eligible",
        "promotion eligible",
        "trusted proposal",
        "verified safe to merge",
        "authority_effect: `Promote`",
        "authority_effect: Promote",
    )
    lowered = markdown.casefold()
    for phrase in forbidden_phrases:
        if phrase.casefold() in lowered:
            _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    terminal_status = getattr(root_or_text, "terminal_status", "")
    if f"`{terminal_status}`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    if "`None`" not in markdown and "authority_effect: `None`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)


# Use Cases Functions
def normalize_source_bytes(data: bytes, normalization: str) -> bytes:
    """Normalize source bytes exactly as declared by a source artifact."""
    if type(data) is not bytes:
        raise TypeError("source data must be exact bytes")
    normalization = _require_string(
        normalization, "source normalization", nonempty=True
    )
    if normalization not in SOURCE_NORMALIZATIONS:
        _fail("source normalization is unsupported")
    if normalization == "raw-bytes":
        return data
    text = data.decode("utf-8", errors="strict")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_source_digest(data: bytes, normalization: str) -> tuple[str, int]:
    """Return the SHA-256 and length of the declared normalized byte stream."""
    normalized = normalize_source_bytes(data, normalization)
    return hashlib.sha256(normalized).hexdigest(), len(normalized)


def build_research_claim_envelope(
    payload: ResearchClaimPayloadV1,
    task_id: str,
    carrier_id: str,
    initial_state_payload: Any,
    protected_boundaries: tuple[str, ...],
    step_budget: int,
) -> PacketEnvelopeV2:
    """Bind a typed research payload into the host-owned packet envelope."""
    if not isinstance(payload, ResearchClaimPayloadV1):
        raise TypeError("payload must be a ResearchClaimPayloadV1")
    _require_string(task_id, "task_id", nonempty=True)
    _require_string(carrier_id, "carrier_id", nonempty=True)
    _validate_ordered_unique_strings(protected_boundaries, "protected_boundaries")
    expected_carrier, expected_boundaries = RESEARCH_FAMILY_OWNER_LAWS[payload.family]
    if carrier_id != expected_carrier:
        _fail("carrier_id violates the research-family owner law")
    if protected_boundaries != expected_boundaries:
        _fail("protected_boundaries violate the research-family owner law")
    _require_positive_int(step_budget, "step_budget")
    validated_initial_state = _validate_initial_state(initial_state_payload)
    supplied_initial_hash = domain_digest(
        INITIAL_STATE_DOMAIN,
        {
            "family": payload.family,
            "initial_state_payload": validated_initial_state,
        },
    )
    if supplied_initial_hash != payload.initial_state_hash:
        _fail("initial_state_payload does not match the research payload")
    return PacketEnvelopeV2(
        task_id=task_id,
        packet_family=RESEARCH_PACKET_FAMILY,
        carrier_id=carrier_id,
        initial_state_hash=payload.initial_state_hash,
        payload=payload.to_dict(),
        constraints=RESEARCH_ENVELOPE_CONSTRAINTS,
        protected_boundaries=protected_boundaries,
        terminal_target=RESEARCH_TERMINAL_TARGET,
        evidence_ceiling=RESEARCH_EVIDENCE_CEILING,
        oracle_policy=RESEARCH_ORACLE_POLICY,
        allowed_transforms=RESEARCH_ALLOWED_TRANSFORMS,
        step_budget=step_budget,
        framing_mode="strict",
        packet_kind="problem",
        parent_event_id=None,
        source_digest=payload.source_manifest_root,
        authority_effect="None",
    )


def parse_research_claim_envelope(
    value: PacketEnvelopeV2 | Mapping[str, Any],
) -> ResearchClaimPayloadV1:
    """Strictly parse and cross-check a research envelope and its payload roots."""
    if isinstance(value, PacketEnvelopeV2):
        envelope = PacketEnvelopeV2.from_dict(value.to_dict())
    else:
        envelope = PacketEnvelopeV2.from_dict(
            _require_exact_dict(value, "research packet envelope")
        )
    if envelope.packet_family != RESEARCH_PACKET_FAMILY:
        _fail("research packet family is unsupported")
    if envelope.constraints != RESEARCH_ENVELOPE_CONSTRAINTS:
        _fail("research packet constraints are not canonical")
    if envelope.terminal_target != RESEARCH_TERMINAL_TARGET:
        _fail("research packet terminal target is unsupported")
    if envelope.evidence_ceiling != RESEARCH_EVIDENCE_CEILING:
        _fail("research packet evidence ceiling is unsupported")
    if envelope.oracle_policy != RESEARCH_ORACLE_POLICY:
        _fail("research packet oracle policy is unsupported")
    if envelope.allowed_transforms != RESEARCH_ALLOWED_TRANSFORMS:
        _fail("research packet transforms are unsupported")
    if (
        envelope.packet_kind != "problem"
        or envelope.framing_mode != "strict"
        or envelope.parent_event_id is not None
        or envelope.authority_effect != "None"
    ):
        _fail("research packet framing or authority is unsupported")
    _validate_ordered_unique_strings(
        envelope.protected_boundaries, "protected_boundaries"
    )
    primitive_payload = thaw(envelope.payload)
    payload = ResearchClaimPayloadV1.from_dict(
        _require_exact_dict(primitive_payload, "research claim payload")
    )
    expected_carrier, expected_boundaries = RESEARCH_FAMILY_OWNER_LAWS[payload.family]
    if envelope.carrier_id != expected_carrier:
        _fail("carrier_id violates the research-family owner law")
    if envelope.protected_boundaries != expected_boundaries:
        _fail("protected_boundaries violate the research-family owner law")
    if envelope.source_digest != payload.source_manifest_root:
        _fail("envelope source_digest does not bind the source manifest")
    if envelope.initial_state_hash != payload.initial_state_hash:
        _fail("envelope initial_state_hash does not bind the initial state")
    return payload


