"""Pure domain entities, value objects, and aggregates for PromptArtifact and EliminationReceipt.

Built on strongly-typed Shared Kernel Value Objects, eliminating primitive obsession.
AuthorityEffect: None (const).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.errors import (
    REFUSAL_ARRAY_NOT_SORTED,
    REFUSAL_AUTHORITY_NON_NONE,
    REFUSAL_BODY_DIGEST_MISMATCH,
    REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    REFUSAL_ID_MISMATCH,
    REFUSAL_OPEN_WITH_DUAL_WITNESS,
)
from omega_engine_pfp.domain.shared_kernel import (
    DEFAULT_REQUIRED_FIELDS,
    ContentDigest,
    DemandId,
    Kind,
    ObstructionFamily,
    ObstructionId,
    RegimeKind,
    ResidualColour,
    Summary,
)
from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest
from omega_engine_pfp.domain.validation import (
    MAX_BODY_BYTES,
    MAX_CONSTRUCTORS,
    MAX_DEMANDS,
    MAX_DIGEST_REFS,
    MAX_KILL_CONDITIONS,
    MAX_OBSTRUCTIONS,
    _fail,
    _require_bool,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_int,
    _require_stable_id,
    _require_string,
    normalize_utf8_lf,
    raw_content_sha256,
)
from omega_engine_pfp.domain.value_objects.wire_keys import (
    DEMAND_ITEM_WIRE_FIELDS,
    ELIMINATION_RECEIPT_WIRE_FIELDS,
    OBJECTIVE_TYPED_WIRE_FIELDS,
    OBSTRUCTION_HINT_WIRE_FIELDS,
    PROMPT_ARTIFACT_WIRE_FIELDS,
    REGIME_KINDS,
    RESIDUAL_COLOURS,
    DemandItemWireKey,
    EliminationReceiptWireKey,
    ObjectiveTypedWireKey,
    ObstructionHintWireKey,
    PromptArtifactWireKey,
)

PROMPT_ARTIFACT_SCHEMA = "omega.symbol-game.prompt-artifact.v1"
PROMPT_ARTIFACT_FAMILY = "prompt_artifact"
PAYLOAD_DOMAIN = "omega.symbol-game.prompt-artifact-payload.v1"
REGIME_DOMAIN = "omega.symbol-game.regime-definition.v1"

ELIMINATION_RECEIPT_SCHEMA = "omega.symbol-game.elimination-receipt.v1"
ELIMINATION_RECEIPT_FAMILY = "elimination_receipt"
ELIMINATION_RECEIPT_DOMAIN = "omega.symbol-game.elimination-receipt.v1"
AUTHORITY_EFFECT_NONE = "None"
DEFAULT_REQUIRED_REPLY_FIELDS = DEFAULT_REQUIRED_FIELDS





@dataclass(frozen=True, slots=True)
class ObstructionHintV1:
    """One typed open obstruction hint bound inside a PromptArtifactV1."""

    obstruction_id: ObstructionId
    family: ObstructionFamily
    residual_colour: ResidualColour
    magnitude: float | None = None
    demand_id: DemandId | None = None
    prior_report_digests: tuple[ContentDigest, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.obstruction_id, ObstructionId):
            object.__setattr__(self, "obstruction_id", ObstructionId.from_str(self.obstruction_id))
        if not isinstance(self.family, ObstructionFamily):
            object.__setattr__(self, "family", ObstructionFamily.from_str(self.family))
        if not isinstance(self.residual_colour, ResidualColour):
            colour_val = (
                self.residual_colour.value
                if isinstance(self.residual_colour, ResidualColour)
                else str(self.residual_colour)
            )
            if colour_val not in RESIDUAL_COLOURS:
                _fail("obstruction residual_colour is unsupported")
            object.__setattr__(self, "residual_colour", ResidualColour(colour_val))
        if self.magnitude is not None:
            if type(self.magnitude) not in (int, float):
                _fail("magnitude must be a number or None")
            mag = float(self.magnitude)
            if not math.isfinite(mag):
                _fail("magnitude must be finite")
        if self.demand_id is not None and not isinstance(self.demand_id, DemandId):
            object.__setattr__(self, "demand_id", DemandId.from_str(self.demand_id))

        if type(self.prior_report_digests) is not tuple:
            _fail("prior_report_digests must be a tuple")
        if len(self.prior_report_digests) > MAX_DIGEST_REFS:
            _fail("prior_report_digests exceeds the resource limit")

        digests: list[ContentDigest] = []
        for d in self.prior_report_digests:
            if isinstance(d, ContentDigest):
                digests.append(d)
            else:
                _require_digest(d, "prior_report_digest")
                digests.append(ContentDigest.from_str(d))
        digests_tuple = tuple(digests)
        sorted_digests = tuple(sorted(set(digests_tuple), key=str))
        if sorted_digests != digests_tuple:
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        object.__setattr__(self, "prior_report_digests", digests_tuple)

    @classmethod
    def create(
        cls,
        *,
        obstruction_id: str | ObstructionId,
        family: str | ObstructionFamily,
        residual_colour: str | ResidualColour = ResidualColour.OPEN,
        magnitude: float | None = None,
        demand_id: str | DemandId | None = None,
        prior_report_digests: Sequence[str | ContentDigest] = (),
    ) -> ObstructionHintV1:
        if isinstance(residual_colour, ResidualColour):
            res_col = residual_colour
        elif str(residual_colour) in {c.value for c in ResidualColour}:
            res_col = ResidualColour(str(residual_colour))
        elif hasattr(ResidualColour, str(residual_colour).upper()):
            res_col = getattr(ResidualColour, str(residual_colour).upper())
        else:
            res_col = ResidualColour(str(residual_colour))
        return cls(
            obstruction_id=ObstructionId.from_str(obstruction_id),
            family=ObstructionFamily.from_str(family),
            residual_colour=res_col,
            magnitude=magnitude,
            demand_id=DemandId.from_str(demand_id) if demand_id is not None else None,
            prior_report_digests=tuple(
                d if isinstance(d, ContentDigest) else ContentDigest.from_str(d)
                for d in prior_report_digests
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obstruction_id": str(self.obstruction_id),
            "family": str(self.family),
            "residual_colour": (
                self.residual_colour.value
                if isinstance(self.residual_colour, ResidualColour)
                else str(self.residual_colour)
            ),
            "magnitude": self.magnitude,
            "demand_id": str(self.demand_id) if self.demand_id is not None else None,
            "prior_report_digests": [str(d) for d in self.prior_report_digests],
        }

    @classmethod
    def from_dict(cls, wire: Any) -> ObstructionHintV1:
        wire = _require_exact_dict(wire, "obstruction hint")
        _require_fields(wire, OBSTRUCTION_HINT_WIRE_FIELDS, "obstruction hint")
        digests_raw = wire["prior_report_digests"]
        if type(digests_raw) is not list:
            _fail("prior_report_digests must be an array")
        digests_tuple = tuple(
            _require_digest(item, f"prior_report_digests[{i}]")
            for i, item in enumerate(digests_raw)
        )
        if tuple(sorted(set(digests_tuple))) != digests_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: prior_report_digests must be sorted and unique on wire"
            )
        return cls.create(
            obstruction_id=wire["obstruction_id"],
            family=wire["family"],
            residual_colour=wire["residual_colour"],
            magnitude=wire["magnitude"],
            demand_id=wire["demand_id"],
            prior_report_digests=digests_tuple,
        )


@dataclass(frozen=True, slots=True)
class DemandItemV1:
    """One typed demand item forcing a specific obligation."""

    demand_id: DemandId
    kind: Kind
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.demand_id, DemandId):
            object.__setattr__(self, "demand_id", DemandId.from_str(self.demand_id))
        if not isinstance(self.kind, Kind):
            object.__setattr__(self, "kind", Kind.from_str(self.kind))
        if self.note is not None:
            _require_string(self.note, "note")

    @classmethod
    def create(
        cls,
        *,
        demand_id: str | DemandId,
        kind: str | Kind,
        note: str | None = None,
    ) -> DemandItemV1:
        return cls(
            demand_id=DemandId.from_str(demand_id),
            kind=Kind.from_str(kind),
            note=note,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "demand_id": str(self.demand_id),
            "kind": str(self.kind),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, wire: Any) -> DemandItemV1:
        wire = _require_exact_dict(wire, "demand item")
        _require_fields(wire, DEMAND_ITEM_WIRE_FIELDS, "demand item")
        return cls.create(
            demand_id=wire["demand_id"],
            kind=wire["kind"],
            note=wire["note"],
        )


@dataclass(frozen=True, slots=True)
class ObjectiveTypedV1:
    """Structured typed objective replacing free prose expansion."""

    kind: Kind
    summary: Summary
    target_obstruction_ids: tuple[ObstructionId, ...] = ()
    target_demand_ids: tuple[DemandId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, Kind):
            if type(self.kind) is not str or not self.kind.strip():
                _fail("objective kind must be nonempty string")
            object.__setattr__(self, "kind", Kind.from_str(self.kind))
        if not isinstance(self.summary, Summary):
            if (
                type(self.summary) is not str
                or not self.summary
                or self.summary.strip() != self.summary
            ):
                _fail("objective summary must be nonempty and trimmed")
            object.__setattr__(self, "summary", Summary.from_str(self.summary))
        if type(self.target_obstruction_ids) is not tuple:
            _fail("target_obstruction_ids must be a tuple")
        obs: list[ObstructionId] = []
        for idx, item in enumerate(self.target_obstruction_ids):
            if isinstance(item, ObstructionId):
                obs.append(item)
            else:
                _require_stable_id(item, f"target_obstruction_ids[{idx}]")
                obs.append(ObstructionId.from_str(item))
        obs_tuple = tuple(obs)
        if tuple(sorted(set(obs_tuple), key=lambda x: x.value)) != obs_tuple:
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        object.__setattr__(self, "target_obstruction_ids", obs_tuple)

        if type(self.target_demand_ids) is not tuple:
            _fail("target_demand_ids must be a tuple")
        dems: list[DemandId] = []
        for idx, item in enumerate(self.target_demand_ids):
            if isinstance(item, DemandId):
                dems.append(item)
            else:
                _require_stable_id(item, f"target_demand_ids[{idx}]")
                dems.append(DemandId.from_str(item))
        dem_tuple = tuple(dems)
        if tuple(sorted(set(dem_tuple), key=lambda x: x.value)) != dem_tuple:
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        object.__setattr__(self, "target_demand_ids", dem_tuple)

    @classmethod
    def create(
        cls,
        *,
        kind: str | Kind = "prompt_turn",
        summary: str | Summary = "structured prompt turn",
        target_obstruction_ids: Sequence[str | ObstructionId] = (),
        target_demand_ids: Sequence[str | DemandId] = (),
    ) -> ObjectiveTypedV1:
        return cls(
            kind=Kind.from_str(kind),
            summary=Summary.from_str(summary),
            target_obstruction_ids=tuple(
                x if isinstance(x, ObstructionId) else ObstructionId.from_str(x)
                for x in target_obstruction_ids
            ),
            target_demand_ids=tuple(
                x if isinstance(x, DemandId) else DemandId.from_str(x)
                for x in target_demand_ids
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": str(self.kind),
            "summary": str(self.summary),
            "target_obstruction_ids": [str(x) for x in self.target_obstruction_ids],
            "target_demand_ids": [str(x) for x in self.target_demand_ids],
        }

    @classmethod
    def from_dict(cls, wire: Any) -> ObjectiveTypedV1:
        wire = _require_exact_dict(wire, "objective_typed")
        _require_fields(wire, OBJECTIVE_TYPED_WIRE_FIELDS, "objective_typed")
        obs_raw = wire["target_obstruction_ids"]
        if type(obs_raw) is not list:
            _fail("target_obstruction_ids must be an array")
        obs_tuple = tuple(
            _require_stable_id(item, f"target_obstruction_ids[{i}]")
            for i, item in enumerate(obs_raw)
        )
        if tuple(sorted(set(obs_tuple))) != obs_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: target_obstruction_ids must be sorted and unique on wire"
            )

        dem_raw = wire["target_demand_ids"]
        if type(dem_raw) is not list:
            _fail("target_demand_ids must be an array")
        dem_tuple = tuple(
            _require_stable_id(item, f"target_demand_ids[{i}]")
            for i, item in enumerate(dem_raw)
        )
        if tuple(sorted(set(dem_tuple))) != dem_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: target_demand_ids must be sorted and unique on wire"
            )

        return cls.create(
            kind=wire["kind"],
            summary=wire["summary"],
            target_obstruction_ids=obs_tuple,
            target_demand_ids=dem_tuple,
        )


@dataclass(frozen=True, slots=True)
class PromptArtifactV1:
    """Content-addressed, schema-locked prompt artifact for L1 swarm communication.

    Layer A identity: domain_digest over identity_fields() (excludes prompt_artifact_id).
    Layer B content: prompt_body_sha256/byte_count over exact UTF-8 bytes shown to model.
    """

    regime_id: str
    regime_kind: str
    admitted_constructors: tuple[str, ...]
    open_obstructions: tuple[ObstructionHintV1, ...]
    demand_set: tuple[DemandItemV1, ...]
    kill_conditions: tuple[str, ...]
    required_reply_fields: tuple[str, ...]
    objective_typed: ObjectiveTypedV1
    residual_colour: str
    dual_witness_required: bool
    dual_witness_ref: str | None
    prompt_body_sha256: str
    prompt_body_byte_count: int
    parent_packet_id: str | None = None
    conversation_root_id: str | None = None
    schema_version: str = field(default=PROMPT_ARTIFACT_SCHEMA)
    family: str = field(default=PROMPT_ARTIFACT_FAMILY)
    authority_effect: str = field(default="None")
    explicit_artifact_id: str | None = None

    def __post_init__(self) -> None:
        _require_digest(self.regime_id, "regime_id")
        if self.regime_kind not in REGIME_KINDS:
            _fail("regime_kind is unsupported")
        if self.residual_colour not in RESIDUAL_COLOURS:
            _fail("residual_colour is unsupported")
        if self.authority_effect != "None":
            _fail(f"{REFUSAL_AUTHORITY_NON_NONE}: prompt artifacts must carry AuthorityEffect None")
        if self.schema_version != PROMPT_ARTIFACT_SCHEMA:
            _fail("prompt artifact schema version is unsupported")
        if self.family != PROMPT_ARTIFACT_FAMILY:
            _fail("prompt artifact family is unsupported")
        _require_bool(self.dual_witness_required, "dual_witness_required")

        # Residual honesty
        if self.residual_colour == "Exact":
            if self.dual_witness_required is not True:
                _fail(REFUSAL_EXACT_WITHOUT_DUAL_WITNESS)
            if self.dual_witness_ref is None:
                _fail(REFUSAL_EXACT_WITHOUT_DUAL_WITNESS)
            _require_digest(self.dual_witness_ref, "dual_witness_ref")
        else:
            if self.dual_witness_ref is not None:
                _fail(REFUSAL_OPEN_WITH_DUAL_WITNESS)

        if self.admitted_constructors != tuple(sorted(set(self.admitted_constructors))):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        if len(self.admitted_constructors) > MAX_CONSTRUCTORS:
            _fail("admitted_constructors exceeds resource limit")
        for idx, ctor in enumerate(self.admitted_constructors):
            _require_stable_id(ctor, f"admitted_constructors[{idx}]")

        if not self.kill_conditions or self.kill_conditions != tuple(sorted(set(self.kill_conditions))):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        if len(self.kill_conditions) > MAX_KILL_CONDITIONS:
            _fail("kill_conditions exceeds resource limit")
        for idx, kc in enumerate(self.kill_conditions):
            _require_stable_id(kc, f"kill_conditions[{idx}]")

        for idx, reply_field in enumerate(self.required_reply_fields):
            _require_string(reply_field, f"required_reply_fields[{idx}]", nonempty=True)
        if not self.required_reply_fields or self.required_reply_fields != tuple(sorted(set(self.required_reply_fields))):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        if len(self.required_reply_fields) > 32:
            _fail("required_reply_fields exceeds resource limit")

        obs_ids = tuple(str(o.obstruction_id) for o in self.open_obstructions)
        if obs_ids != tuple(sorted(obs_ids)) or len(obs_ids) != len(set(obs_ids)):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        if len(self.open_obstructions) > MAX_OBSTRUCTIONS:
            _fail("open_obstructions exceeds resource limit")

        dem_ids = tuple(str(d.demand_id) for d in self.demand_set)
        if dem_ids != tuple(sorted(dem_ids)) or len(dem_ids) != len(set(dem_ids)):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        if len(self.demand_set) > MAX_DEMANDS:
            _fail("demand_set exceeds resource limit")

        if not isinstance(self.objective_typed, ObjectiveTypedV1):
            if hasattr(self.objective_typed, "kind") and hasattr(self.objective_typed, "summary"):
                object.__setattr__(
                    self,
                    "objective_typed",
                    ObjectiveTypedV1(
                        kind=Kind.from_str(str(self.objective_typed.kind)),
                        summary=Summary.from_str(str(self.objective_typed.summary)),
                        target_obstruction_ids=tuple(getattr(self.objective_typed, "target_obstruction_ids", ())),
                        target_demand_ids=tuple(getattr(self.objective_typed, "target_demand_ids", ())),
                    ),
                )
            else:
                _fail("objective_typed must be an ObjectiveTypedV1 instance")

        _require_digest(self.prompt_body_sha256, "prompt_body_sha256")
        _require_int(self.prompt_body_byte_count, "prompt_body_byte_count", min_value=0, max_value=MAX_BODY_BYTES)

        if self.parent_packet_id is not None:
            _require_digest(self.parent_packet_id, "parent_packet_id")
        if self.conversation_root_id is not None:
            _require_digest(self.conversation_root_id, "conversation_root_id")

    def identity_fields(self) -> dict[str, Any]:
        """Layer A preimage — excludes prompt_artifact_id."""
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "regime_id": self.regime_id,
            "regime_kind": self.regime_kind,
            "admitted_constructors": list(self.admitted_constructors),
            "open_obstructions": [o.to_dict() for o in self.open_obstructions],
            "demand_set": [d.to_dict() for d in self.demand_set],
            "kill_conditions": list(self.kill_conditions),
            "required_reply_fields": list(self.required_reply_fields),
            "objective_typed": self.objective_typed.to_dict(),
            "residual_colour": self.residual_colour,
            "dual_witness_required": self.dual_witness_required,
            "dual_witness_ref": self.dual_witness_ref,
            "prompt_body_sha256": self.prompt_body_sha256,
            "prompt_body_byte_count": self.prompt_body_byte_count,
            "parent_packet_id": self.parent_packet_id,
            "conversation_root_id": self.conversation_root_id,
            "authority_effect": self.authority_effect,
        }

    @property
    def prompt_artifact_id(self) -> str:
        if self.explicit_artifact_id is not None:
            return self.explicit_artifact_id
        return domain_digest(PAYLOAD_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        wire = self.identity_fields()
        wire["prompt_artifact_id"] = self.prompt_artifact_id
        return wire

    def verify_prompt_body(self, body: bytes) -> None:
        """Verify body bytes match prompt_body_sha256 and prompt_body_byte_count."""
        digest, count = raw_content_sha256(body)
        if digest != self.prompt_body_sha256 or count != self.prompt_body_byte_count:
            _fail(REFUSAL_BODY_DIGEST_MISMATCH)

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> PromptArtifactV1:
        wire = _require_exact_dict(wire, "prompt artifact")
        _require_fields(wire, PROMPT_ARTIFACT_WIRE_FIELDS, "prompt artifact")
        expected_id = _require_digest(wire["prompt_artifact_id"], "prompt_artifact_id")

        constructors_raw = wire["admitted_constructors"]
        if type(constructors_raw) is not list:
            _fail("admitted_constructors must be an array")
        constructors_tuple = tuple(
            _require_stable_id(item, f"admitted_constructors[{i}]")
            for i, item in enumerate(constructors_raw)
        )
        if tuple(sorted(set(constructors_tuple))) != constructors_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: admitted_constructors must be sorted and unique on wire"
            )

        obstructions_raw = wire["open_obstructions"]
        if type(obstructions_raw) is not list:
            _fail("open_obstructions must be an array")
        open_obstructions = tuple(
            ObstructionHintV1.from_dict(item) for item in obstructions_raw
        )
        obs_ids = [str(obs.obstruction_id) for obs in open_obstructions]
        if tuple(sorted(obs_ids)) != tuple(obs_ids) or len(obs_ids) != len(set(obs_ids)):
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: open_obstructions must be sorted by obstruction_id on wire"
            )

        demands_raw = wire["demand_set"]
        if type(demands_raw) is not list:
            _fail("demand_set must be an array")
        demand_set = tuple(DemandItemV1.from_dict(item) for item in demands_raw)
        dem_ids = [str(dem.demand_id) for dem in demand_set]
        if tuple(sorted(dem_ids)) != tuple(dem_ids) or len(dem_ids) != len(set(dem_ids)):
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: demand_set must be sorted by demand_id on wire"
            )

        kills_raw = wire["kill_conditions"]
        if type(kills_raw) is not list:
            _fail("kill_conditions must be an array")
        kills_tuple = tuple(
            _require_stable_id(item, f"kill_conditions[{i}]")
            for i, item in enumerate(kills_raw)
        )
        if tuple(sorted(set(kills_tuple))) != kills_tuple or not kills_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: kill_conditions must be sorted and unique on wire"
            )

        reply_raw = wire["required_reply_fields"]
        if type(reply_raw) is not list:
            _fail("required_reply_fields must be an array")
        reply_tuple = tuple(
            _require_string(item, f"required_reply_fields[{i}]", nonempty=True)
            for i, item in enumerate(reply_raw)
        )
        if tuple(sorted(set(reply_tuple))) != reply_tuple or not reply_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: required_reply_fields must be sorted and unique on wire"
            )

        objective_typed = ObjectiveTypedV1.from_dict(wire["objective_typed"])

        artifact = cls(
            regime_id=_require_digest(wire["regime_id"], "regime_id"),
            regime_kind=_require_string(wire["regime_kind"], "regime_kind", nonempty=True),
            admitted_constructors=constructors_tuple,
            open_obstructions=open_obstructions,
            demand_set=demand_set,
            kill_conditions=kills_tuple,
            required_reply_fields=reply_tuple,
            objective_typed=objective_typed,
            residual_colour=_require_string(
                wire["residual_colour"], "residual_colour", nonempty=True
            ),
            dual_witness_required=_require_bool(
                wire["dual_witness_required"], "dual_witness_required"
            ),
            dual_witness_ref=(
                None
                if wire["dual_witness_ref"] is None
                else _require_digest(wire["dual_witness_ref"], "dual_witness_ref")
            ),
            prompt_body_sha256=_require_digest(
                wire["prompt_body_sha256"], "prompt_body_sha256"
            ),
            prompt_body_byte_count=_require_int(
                wire["prompt_body_byte_count"], "prompt_body_byte_count", min_value=0
            ),
            parent_packet_id=(
                None
                if wire["parent_packet_id"] is None
                else _require_digest(wire["parent_packet_id"], "parent_packet_id")
            ),
            conversation_root_id=(
                None
                if wire["conversation_root_id"] is None
                else _require_digest(wire["conversation_root_id"], "conversation_root_id")
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            family=_require_string(wire["family"], "family", nonempty=True),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )

        if artifact.prompt_artifact_id != expected_id:
            _fail(
                f"{REFUSAL_ID_MISMATCH}: wire prompt_artifact_id {expected_id!r} does not match computed {artifact.prompt_artifact_id!r}"
            )
        return artifact


@dataclass(frozen=True, slots=True)
class EliminationReceiptV1:
    """Host-issued residual elimination receipt for accepted turn steps.

    Records which obstructions were eliminated, prior -> new residual colours,
    content-addressed evidence root, and optional dual witness reference.
    AuthorityEffect is const None.
    """

    packet_id: str
    eliminated_obstruction_ids: tuple[str, ...]
    prior_residual_colour: str
    new_residual_colour: str
    evidence_root: str
    dual_witness_ref: str | None = None
    schema_version: str = field(default=ELIMINATION_RECEIPT_SCHEMA)
    family: str = field(default=ELIMINATION_RECEIPT_FAMILY)
    authority_effect: str = field(default="None")
    explicit_artifact_id: str | None = None

    def __post_init__(self) -> None:
        _require_digest(self.packet_id, "packet_id")
        _require_digest(self.evidence_root, "evidence_root")
        if self.prior_residual_colour not in RESIDUAL_COLOURS:
            _fail("prior_residual_colour is unsupported")
        if self.new_residual_colour not in RESIDUAL_COLOURS:
            _fail("new_residual_colour is unsupported")
        if self.authority_effect != "None":
            _fail(f"{REFUSAL_AUTHORITY_NON_NONE}: elimination receipts must carry AuthorityEffect None")
        if self.schema_version != ELIMINATION_RECEIPT_SCHEMA:
            _fail("elimination receipt schema version is unsupported")
        if self.family != ELIMINATION_RECEIPT_FAMILY:
            _fail("elimination receipt family is unsupported")

        if self.eliminated_obstruction_ids != tuple(sorted(set(self.eliminated_obstruction_ids))):
            _fail(REFUSAL_ARRAY_NOT_SORTED)
        for idx, obs_id in enumerate(self.eliminated_obstruction_ids):
            _require_stable_id(obs_id, f"eliminated_obstruction_ids[{idx}]")

        # Residual honesty law
        if self.new_residual_colour == "Exact":
            if self.dual_witness_ref is None:
                _fail(REFUSAL_EXACT_WITHOUT_DUAL_WITNESS)
            _require_digest(self.dual_witness_ref, "dual_witness_ref")
        else:
            if self.dual_witness_ref is not None:
                _fail(REFUSAL_OPEN_WITH_DUAL_WITNESS)

    def identity_fields(self) -> dict[str, Any]:
        """Layer A preimage — excludes elimination_receipt_id."""
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "packet_id": self.packet_id,
            "eliminated_obstruction_ids": list(self.eliminated_obstruction_ids),
            "prior_residual_colour": self.prior_residual_colour,
            "new_residual_colour": self.new_residual_colour,
            "evidence_root": self.evidence_root,
            "dual_witness_ref": self.dual_witness_ref,
            "authority_effect": self.authority_effect,
        }

    @property
    def elimination_receipt_id(self) -> str:
        return domain_digest(ELIMINATION_RECEIPT_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        wire = self.identity_fields()
        wire["elimination_receipt_id"] = self.elimination_receipt_id
        return wire

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> EliminationReceiptV1:
        wire = _require_exact_dict(wire, "elimination receipt")
        _require_fields(wire, ELIMINATION_RECEIPT_WIRE_FIELDS, "elimination receipt")
        expected_id = _require_digest(wire["elimination_receipt_id"], "elimination_receipt_id")

        elim_raw = wire["eliminated_obstruction_ids"]
        if type(elim_raw) is not list:
            _fail("eliminated_obstruction_ids must be an array")
        elim_tuple = tuple(
            _require_stable_id(item, f"eliminated_obstruction_ids[{i}]")
            for i, item in enumerate(elim_raw)
        )
        if tuple(sorted(set(elim_tuple))) != elim_tuple:
            _fail(
                f"{REFUSAL_ARRAY_NOT_SORTED}: eliminated_obstruction_ids must be sorted and unique on wire"
            )

        receipt = cls(
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            eliminated_obstruction_ids=elim_tuple,
            prior_residual_colour=_require_string(wire["prior_residual_colour"], "prior_residual_colour", nonempty=True),
            new_residual_colour=_require_string(wire["new_residual_colour"], "new_residual_colour", nonempty=True),
            evidence_root=_require_digest(wire["evidence_root"], "evidence_root"),
            dual_witness_ref=(
                None
                if wire["dual_witness_ref"] is None
                else _require_digest(wire["dual_witness_ref"], "dual_witness_ref")
            ),
            schema_version=_require_string(wire["schema_version"], "schema_version", nonempty=True),
            family=_require_string(wire["family"], "family", nonempty=True),
            authority_effect=_require_string(wire["authority_effect"], "authority_effect", nonempty=True),
        )
        if receipt.elimination_receipt_id != expected_id:
            _fail(
                f"{REFUSAL_ID_MISMATCH}: wire elimination_receipt_id {expected_id!r} != computed {receipt.elimination_receipt_id!r}"
            )
        return receipt


# Presenter Functions
def render_prompt_body(
    regime_bytes: bytes,
    *,
    objective_typed: ObjectiveTypedV1,
    admitted_constructors: Sequence[str] = (),
    open_obstructions: Sequence[ObstructionHintV1] = (),
    demand_set: Sequence[DemandItemV1] = (),
    kill_conditions: Sequence[str] = (),
    required_reply_fields: Sequence[str] = (),
) -> bytes:
    """Deterministically render canonical prompt body UTF-8 LF bytes."""
    regime_text = normalize_utf8_lf(regime_bytes).decode("utf-8").strip()

    ctors_lines = "\n".join(f"- {c}" for c in sorted(set(admitted_constructors))) or "none"

    sorted_obs = sorted(open_obstructions, key=lambda x: str(x.obstruction_id))
    obs_lines = (
        "\n".join(
            f"- {o.obstruction_id} [{o.family}] ({o.residual_colour.value})"
            + (f" mag={o.magnitude}" if o.magnitude is not None else "")
            + (f" demand={o.demand_id}" if o.demand_id is not None else "")
            for o in sorted_obs
        )
        or "none"
    )

    sorted_dem = sorted(demand_set, key=lambda x: str(x.demand_id))
    dem_lines = (
        "\n".join(
            f"- {d.demand_id} [{d.kind}]" + (f": {d.note}" if getattr(d, "note", None) else "")
            for d in sorted_dem
        )
        or "none"
    )

    kills_lines = "\n".join(f"- {k}" for k in sorted(set(kill_conditions))) or "none"

    target_obs = ",".join(sorted(set(str(x) for x in objective_typed.target_obstruction_ids))) or "none"
    target_dem = ",".join(sorted(set(str(x) for x in objective_typed.target_demand_ids))) or "none"
    reply_fields = ",".join(sorted(set(required_reply_fields))) or ",".join(
        sorted(set(DEFAULT_REQUIRED_FIELDS))
    )

    rendered = (
        f"{regime_text}\n\n"
        f"=== STRUCTURED OBJECTIVE ===\n"
        f"KIND: {objective_typed.kind}\n"
        f"SUMMARY: {objective_typed.summary}\n"
        f"TARGET_OBSTRUCTIONS: {target_obs}\n"
        f"TARGET_DEMANDS: {target_dem}\n\n"
        f"=== ADMITTED CONSTRUCTORS ===\n"
        f"{ctors_lines}\n\n"
        f"=== OPEN OBSTRUCTIONS ===\n"
        f"{obs_lines}\n\n"
        f"=== DEMAND SET ===\n"
        f"{dem_lines}\n\n"
        f"=== ACTIVE KILL CONDITIONS ===\n"
        f"{kills_lines}\n\n"
        f"=== REQUIRED REPLY FIELDS ===\n"
        f"{reply_fields}\n"
    )
    return rendered.encode("utf-8")


def render_elimination_receipt_block(receipt: EliminationReceiptV1) -> str:
    """Render the machine elimination receipt block appended after host verify."""
    elim_str = ", ".join(receipt.eliminated_obstruction_ids) if receipt.eliminated_obstruction_ids else "none"
    dual_str = receipt.dual_witness_ref if receipt.dual_witness_ref is not None else "null"
    return (
        "```elimination_receipt\n"
        f"ELIMINATED: {elim_str}\n"
        f"PRIOR_RESIDUAL_COLOUR: {receipt.prior_residual_colour}\n"
        f"NEW_RESIDUAL_COLOUR: {receipt.new_residual_colour}\n"
        f"EVIDENCE_ROOT: {receipt.evidence_root}\n"
        f"DUAL_WITNESS_REF: {dual_str}\n"
        f"AUTHORITY_EFFECT: {receipt.authority_effect}\n"
        "```\n"
    )


def parse_elimination_receipt_block(text: str) -> dict[str, str] | None:
    """Parse elimination receipt block fields if present in text."""
    pattern = re.compile(r"```elimination_receipt\s*\n(.*?)```", re.DOTALL)
    match = pattern.search(text)
    if match is None:
        return None
    block_text = match.group(1)
    fields: dict[str, str] = {}
    field_pattern = re.compile(r"^([A-Z_]+):\s*(.*)$", re.MULTILINE)
    for fm in field_pattern.finditer(block_text):
        key = fm.group(1).strip()
        value = fm.group(2).strip()
        if key in fields:
            _fail(f"duplicate elimination receipt field: {key}")
        fields[key] = value
    return fields


# Compiler Functions


def compile_prompt_artifact(
    *,
    regime_kind: str | RegimeKind,
    regime_definition_bytes: bytes,
    prompt_body_bytes: bytes,
    objective_typed: ObjectiveTypedV1,
    admitted_constructors: Sequence[str] = (),
    open_obstructions: Sequence[ObstructionHintV1] = (),
    demand_set: Sequence[DemandItemV1] = (),
    kill_conditions: Sequence[str] = (),
    required_reply_fields: Sequence[str] = (),
    residual_colour: str | ResidualColour = ResidualColour.OPEN,
    dual_witness_required: bool | None = None,
    dual_witness_ref: str | None = None,
    parent_packet_id: str | None = None,
    conversation_root_id: str | None = None,
    normalize_body: bool = True,
) -> PromptArtifactV1:
    """Host-side compile. Sorts arrays here; verify path never silent-sorts."""
    if type(regime_definition_bytes) is not bytes:
        raise TypeError("regime_definition_bytes must be exact bytes")
    if type(prompt_body_bytes) is not bytes:
        raise TypeError("prompt_body_bytes must be exact bytes")
    _require_bool(normalize_body, "normalize_body")

    regime_kind_str = (
        regime_kind.value if isinstance(regime_kind, RegimeKind) else str(regime_kind)
    )
    residual_colour_str = (
        residual_colour.value
        if isinstance(residual_colour, ResidualColour)
        else str(residual_colour)
    )

    if regime_kind_str not in REGIME_KINDS:
        _fail("regime_kind is unsupported")

    regime_id, _ = raw_content_sha256(normalize_utf8_lf(regime_definition_bytes))

    body = normalize_utf8_lf(prompt_body_bytes) if normalize_body else prompt_body_bytes
    body_sha, body_len = raw_content_sha256(body)

    constructors = tuple(sorted(set(admitted_constructors)))
    kills = tuple(sorted(set(kill_conditions))) if kill_conditions else ("F-01_inherited_meaning",)
    reply_fields = (
        tuple(sorted(set(required_reply_fields)))
        if required_reply_fields
        else tuple(sorted(set(DEFAULT_REQUIRED_FIELDS)))
    )
    obs = tuple(sorted(open_obstructions, key=lambda o: str(o.obstruction_id)))
    demands = tuple(sorted(demand_set, key=lambda d: str(d.demand_id)))

    if dual_witness_required is None:
        dual_witness_required = (residual_colour_str == ResidualColour.EXACT.value)

    return PromptArtifactV1(
        regime_id=regime_id,
        regime_kind=regime_kind_str,
        admitted_constructors=constructors,
        open_obstructions=obs,
        demand_set=demands,
        kill_conditions=kills,
        required_reply_fields=reply_fields,
        objective_typed=objective_typed,
        residual_colour=residual_colour_str,
        dual_witness_required=dual_witness_required,
        dual_witness_ref=dual_witness_ref,
        prompt_body_sha256=body_sha,
        prompt_body_byte_count=body_len,
        parent_packet_id=parent_packet_id,
        conversation_root_id=conversation_root_id,
    )


def prompt_artifact_to_content_binding(
    artifact: PromptArtifactV1,
) -> tuple[str, int]:
    """LlmTurnPayloadV1.content_sha256 must equal prompt body, not artifact id."""
    return artifact.prompt_body_sha256, artifact.prompt_body_byte_count


prompt_artifact_to_turn_content_binding = prompt_artifact_to_content_binding


def build_payload_from_prompt_artifact(
    artifact: PromptArtifactV1,
    *,
    task_id: str = "prompt_artifact_task",
    role: str = "user",
    turn_kind: str = "prose",
    candidate_budget: int = 3,
    operation_budget: int = 20,
) -> Any:
    """Build an LlmTurnPayloadV1 bound to a PromptArtifactV1."""
    from omega_engine_pfp.domain.aggregates.llm_turn_run_root import LlmTurnPayloadV1

    content_sha, content_len = prompt_artifact_to_content_binding(artifact)
    objective_summary = str(artifact.objective_typed.summary)
    objective_text = f"[prompt_artifact:{artifact.prompt_artifact_id}] {objective_summary}"
    return LlmTurnPayloadV1.create(
        task_id=task_id,
        role=role,
        turn_kind=turn_kind,
        objective=objective_text,
        prompt_artifact_id=artifact.prompt_artifact_id,
        prompt_body_sha256=content_sha,
        prompt_body_bytes_len=content_len,
        required_reply_fields=artifact.required_reply_fields,
        candidate_budget=candidate_budget,
        operation_budget=operation_budget,
    )


def create_elimination_receipt(
    *,
    packet_id: str,
    prior_residual_colour: str | ResidualColour,
    new_residual_colour: str | ResidualColour,
    evidence_root: str,
    eliminated_obstruction_ids: Sequence[str] = (),
    dual_witness_ref: str | None = None,
) -> EliminationReceiptV1:
    """Host-authored constructor for an elimination receipt.

    Sorts eliminated_obstruction_ids and enforces residual transition law.
    """
    prior_str = (
        prior_residual_colour.value
        if isinstance(prior_residual_colour, ResidualColour)
        else str(prior_residual_colour)
    )
    new_str = (
        new_residual_colour.value
        if isinstance(new_residual_colour, ResidualColour)
        else str(new_residual_colour)
    )
    elim_tuple = tuple(sorted(set(eliminated_obstruction_ids)))

    return EliminationReceiptV1(
        packet_id=packet_id,
        eliminated_obstruction_ids=elim_tuple,
        prior_residual_colour=prior_str,
        new_residual_colour=new_str,
        evidence_root=evidence_root,
        dual_witness_ref=dual_witness_ref,
    )


# Persistence Functions


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "DEFAULT_REQUIRED_FIELDS",
    "DEFAULT_REQUIRED_REPLY_FIELDS",
    "DEMAND_ITEM_WIRE_FIELDS",
    "DemandItemV1",
    "DemandItemWireKey",
    "ELIMINATION_RECEIPT_DOMAIN",
    "ELIMINATION_RECEIPT_FAMILY",
    "ELIMINATION_RECEIPT_SCHEMA",
    "ELIMINATION_RECEIPT_WIRE_FIELDS",
    "EliminationReceiptV1",
    "EliminationReceiptWireKey",
    "OBJECTIVE_TYPED_WIRE_FIELDS",
    "OBSTRUCTION_HINT_WIRE_FIELDS",
    "ObjectiveTypedV1",
    "ObjectiveTypedWireKey",
    "ObstructionHintV1",
    "ObstructionHintWireKey",
    "PAYLOAD_DOMAIN",
    "PROMPT_ARTIFACT_FAMILY",
    "PROMPT_ARTIFACT_SCHEMA",
    "PROMPT_ARTIFACT_WIRE_FIELDS",
    "PromptArtifactV1",
    "PromptArtifactWireKey",
    "REGIME_DOMAIN",
    "REGIME_KINDS",
    "RESIDUAL_COLOURS",
    "build_payload_from_prompt_artifact",
    "compile_prompt_artifact",
    "create_elimination_receipt",
    "parse_elimination_receipt_block",
    "prompt_artifact_to_content_binding",
    "prompt_artifact_to_turn_content_binding",
    "render_elimination_receipt_block",
    "render_prompt_body",
]
