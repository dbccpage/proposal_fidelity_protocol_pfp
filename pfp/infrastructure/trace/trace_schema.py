"""The closed V1 replay and V2 write execution-trace formats.

A hash chain proves a file was not *partially* edited. It says nothing about
whether the records mean anything. Before these files become the harness's only
record of what happened, "parses and links" is not a high enough bar for
admission: a record with no ``attempt_id``, a ``raw_response_byte_count`` of
``"47"``, or an event name nobody ever writes all chain perfectly and all make
recovery derive nonsense from them.

So the format is **closed**. The events are enumerated here, each with the fields
its payload must carry and the JSON types those fields must have. An event this
module does not declare cannot be written and is not admitted when read.

That closure is the point, and it has a cost worth stating: extending the trace
means editing this file. That is the trade -- a format that can grow silently is
a format whose reader cannot know what it is holding.

**Why the names live here rather than beside their writers.** They used to sit in
`provider_dispatch` and `traced_code_change`. Admission then depended on which
modules the reading process happened to have imported: a recovery tool that
imported only `execution_trace` would find every dispatch event "unknown" and
refuse a perfectly good file. Declaring the format in one module that imports
nothing from the rest of the package makes admission a property of the format
instead of a property of the importer. The writers import their names from here.

AuthorityEffect: None. A schema admits a record; it does not vouch for it.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


TRACE_SCHEMA_VERSION_V1 = "omega.symbol-game.execution-trace.v1"
TRACE_SCHEMA_VERSION_V2 = "omega.symbol-game.execution-trace.v2"
# New writers always use V2. V1 exists only as an explicitly selected reader.
TRACE_SCHEMA_VERSION = TRACE_SCHEMA_VERSION_V2
SUPPORTED_TRACE_SCHEMA_VERSIONS = frozenset(
    {TRACE_SCHEMA_VERSION_V1, TRACE_SCHEMA_VERSION_V2}
)
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ARTIFACT_REF_FIELDS = frozenset(
    {
        "artifact_schema",
        "authority_effect",
        "byte_length",
        "encrypted_envelope_digest",
        "plaintext_sha256",
        "protector_id",
        "schema",
    }
)

# ---------------------------------------------------------------------------
# Event names -- the closed set
# ---------------------------------------------------------------------------

#: The first record of every trace.
EVENT_RUN_STARTED = "RunStarted"
#: The last record of a complete trace.
EVENT_RUN_SEALED = "RunSealed"

#: Barrier 1. Intent is durable; the request may or may not have left.
EVENT_DISPATCH_INTENT_DURABLE = "ProviderDispatchIntentDurable"
#: Barrier 2. Exact response bytes are in encrypted CAS; the trace has its ref.
EVENT_RESPONSE_DURABLE = "ProviderResponseDurable"
#: Barrier 1 passed, barrier 2 not reached. Never auto-retried.
EVENT_DISPATCH_STATUS_UNKNOWN = "ProviderDispatchStatusUnknown"
#: A fail-closed gate refused ahead of dispatch. No money was spent.
EVENT_DISPATCH_REFUSED_PREFLIGHT = "ProviderDispatchRefusedPreflight"

#: The deterministic code-change path.
EVENT_PROPOSAL_CREATED = "ProposalCreated"
EVENT_CANDIDATE_SUBMITTED = "CandidateSubmitted"
EVENT_GATES_EVALUATED = "GatesEvaluated"
EVENT_RUN_FINALIZED = "RunFinalized"
EVENT_STAGE_REFUSED = "StageRefused"


# ---------------------------------------------------------------------------
# JSON types
# ---------------------------------------------------------------------------


def json_type(value: Any) -> str:
    """The JSON type name of a decoded value.

    ``bool`` is tested before ``int`` deliberately. ``isinstance(True, int)`` is
    true, so a field declared ``integer`` would otherwise admit ``true`` and be
    compared against a length as the integer 1 -- which is exactly the class of
    defect that reached recovery once already.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


class SchemaRefusal(RuntimeError):
    """A schema could not be registered, or contradicts one already registered."""


@dataclass(frozen=True)
class EventSchema:
    """What one event's payload must carry.

    ``required`` names fields that must be present. ``types`` maps a field to the
    JSON types it may have; a field may be listed in ``types`` without being
    required, in which case it is checked only when present.

    Extra fields are permitted. The format pins what recovery *reads*; forbidding
    everything else would turn every added diagnostic field into a corrupt-file
    verdict on traces that are fine.
    """

    event: str
    required: frozenset[str] = frozenset()
    types: Mapping[str, tuple[str, ...]] = None  # type: ignore[assignment]
    forbidden: frozenset[str] = frozenset()
    encrypted_artifact_refs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.event:
            raise SchemaRefusal("an event schema needs an event name")
        object.__setattr__(self, "types", dict(self.types or {}))
        unknown = set(self.required) - set(self.types)
        # Not an error: a field can be required without its type being pinned.
        # Recorded as a no-op so the asymmetry is deliberate rather than missed.
        del unknown

    def violations(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        """Every reason this payload is not admissible under this schema."""
        problems: list[str] = []
        for field in sorted(self.required):
            if field not in payload:
                problems.append(f"missing required field {field!r}")
        for field, allowed in sorted(self.types.items()):
            if field not in payload:
                continue
            actual = json_type(payload[field])
            if actual not in allowed:
                problems.append(
                    f"field {field!r} is {actual}, expected one of {allowed}"
                )
        for field in sorted(self.forbidden):
            if field in payload:
                problems.append(f"forbidden field {field!r}")
        for field in sorted(self.encrypted_artifact_refs):
            if field in payload:
                problems.extend(_artifact_ref_violations(field, payload[field]))
        return tuple(problems)


def _artifact_ref_violations(field: str, value: Any) -> list[str]:
    if type(value) is not dict:
        return [f"field {field!r} is not an exact encrypted artifact reference"]
    if set(value) != _ARTIFACT_REF_FIELDS:
        return [f"field {field!r} encrypted artifact reference fields differ"]
    problems: list[str] = []
    if value.get("schema") != "omega.oeos.encrypted-artifact-ref.v1":
        problems.append(f"field {field!r} encrypted artifact schema differs")
    if value.get("authority_effect") != "None":
        problems.append(f"field {field!r} encrypted artifact grants authority")
    for digest_field in ("plaintext_sha256", "encrypted_envelope_digest"):
        digest = value.get(digest_field)
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            problems.append(f"field {field!r}.{digest_field} is not canonical")
    for text_field in ("artifact_schema", "protector_id"):
        text = value.get(text_field)
        if type(text) is not str or not text:
            problems.append(f"field {field!r}.{text_field} is not a string")
    length = value.get("byte_length")
    if type(length) is not int or length < 0:
        problems.append(
            f"field {field!r}.byte_length is not an exact non-negative integer"
        )
    return problems


_SCHEMAS: dict[str, EventSchema] = {}


def register_event_schema(schema: EventSchema) -> EventSchema:
    """Add one event to the closed format.

    Re-registering the identical schema is a no-op, so a module that gets
    imported twice under two names -- which this estate demonstrably does -- does
    not fail on the second import. Registering a *different* schema for a name
    already taken is refused: two meanings of one event name is the defect the
    closed format exists to prevent, and last-write-wins would hide it.
    """
    existing = _SCHEMAS.get(schema.event)
    if existing is not None:
        if existing == schema:
            return existing
        raise SchemaRefusal(
            f"event {schema.event!r} is already declared with a different schema; "
            "one event name may not mean two things"
        )
    _SCHEMAS[schema.event] = schema
    return schema


def event_schema(
    event: str, schema_version: str = TRACE_SCHEMA_VERSION
) -> EventSchema | None:
    """The schema for ``event``, or ``None`` if the format does not declare it."""
    if schema_version not in SUPPORTED_TRACE_SCHEMA_VERSIONS:
        return None
    if event == EVENT_RESPONSE_DURABLE and schema_version == TRACE_SCHEMA_VERSION_V1:
        return _V1_RESPONSE_SCHEMA
    return _SCHEMAS.get(event)


def known_events() -> tuple[str, ...]:
    return tuple(sorted(_SCHEMAS))


# ---------------------------------------------------------------------------
# Shared events plus the V2 response format
# ---------------------------------------------------------------------------

_STR = ("string",)
_INT = ("integer",)
_BOOL = ("boolean",)
_ARRAY = ("array",)
_OBJECT = ("object",)

for _schema in (
    EventSchema(
        EVENT_RUN_STARTED,
        required=frozenset(
            {
                "schema_version",
                "execution_id",
                "durability",
                "live_transport",
                "run_mode",
                "durability_scope",
            }
        ),
        types={
            "schema_version": _STR,
            "execution_id": _STR,
            "durability": _STR,
            # `boolean`, not `integer`: a trace claiming `live_transport: 1`
            # would otherwise be truthy and admitted.
            "live_transport": _BOOL,
            "run_mode": _STR,
            "durability_scope": _OBJECT,
        },
    ),
    EventSchema(
        EVENT_RUN_SEALED,
        required=frozenset({"terminal"}),
        types={"terminal": _STR},
    ),
    EventSchema(
        EVENT_DISPATCH_INTENT_DURABLE,
        required=frozenset(
            {
                "attempt_id",
                "provider",
                "model",
                "live",
                "request_system_sha256",
                "request_user_sha256",
            }
        ),
        types={
            "attempt_id": _STR,
            "provider": _STR,
            "model": _STR,
            "live": _BOOL,
            "request_system_sha256": _STR,
            "request_user_sha256": _STR,
        },
    ),
    EventSchema(
        EVENT_RESPONSE_DURABLE,
        required=frozenset(
            {
                "attempt_id",
                "provider",
                "model",
                "encrypted_artifact_ref",
            }
        ),
        types={
            "attempt_id": _STR,
            "provider": _STR,
            "model": _STR,
            "encrypted_artifact_ref": _OBJECT,
        },
        forbidden=frozenset(
            {"raw_response_sha256", "raw_response_byte_count", "raw_response_path"}
        ),
        encrypted_artifact_refs=frozenset({"encrypted_artifact_ref"}),
    ),
    EventSchema(
        EVENT_DISPATCH_STATUS_UNKNOWN,
        required=frozenset(
            {
                "attempt_id",
                "provider",
                "model",
                "failure_type",
                "failure",
                "retry_permitted",
            }
        ),
        types={
            "attempt_id": _STR,
            "provider": _STR,
            "model": _STR,
            "failure_type": _STR,
            "failure": _STR,
            "retry_permitted": _BOOL,
        },
    ),
    EventSchema(
        EVENT_DISPATCH_REFUSED_PREFLIGHT,
        required=frozenset(
            {"provider", "model", "refusal_type", "refusal", "dispatched"}
        ),
        types={
            "provider": _STR,
            "model": _STR,
            "refusal_type": _STR,
            "refusal": _STR,
            "dispatched": _BOOL,
        },
    ),
    EventSchema(
        EVENT_PROPOSAL_CREATED,
        required=frozenset(
            {
                "packet_id",
                "task_id",
                "source_revision",
                "owned_paths",
                "protected_paths",
                "required_gates",
                "candidate_budget",
                "operation_budget",
            }
        ),
        types={
            "packet_id": _STR,
            "task_id": _STR,
            "source_revision": _STR,
            "owned_paths": _ARRAY,
            "protected_paths": _ARRAY,
            "required_gates": _ARRAY,
            "candidate_budget": _INT,
            "operation_budget": _INT,
        },
    ),
    EventSchema(
        EVENT_CANDIDATE_SUBMITTED,
        required=frozenset(
            {
                "packet_id",
                "candidate_id",
                "patch_id",
                "patch_sha256",
                "patch_byte_count",
                "touched_paths",
                "producer_id",
                "model_claimed_valid",
                "ledger_candidate_count",
            }
        ),
        types={
            "packet_id": _STR,
            "candidate_id": _STR,
            "patch_id": _STR,
            "patch_sha256": _STR,
            "patch_byte_count": _INT,
            "touched_paths": _ARRAY,
            "producer_id": _STR,
            # Nullable on purpose, and verified against a real run rather than
            # assumed: this path carries no typed producer claim, so the field is
            # written as `null`. Declaring it `boolean` would have refused every
            # trace the code-change controller writes.
            "model_claimed_valid": ("boolean", "null"),
            "ledger_candidate_count": _INT,
        },
    ),
    EventSchema(
        EVENT_GATES_EVALUATED,
        required=frozenset({"gates"}),
        types={"gates": _ARRAY},
    ),
    EventSchema(
        EVENT_RUN_FINALIZED,
        required=frozenset(
            {
                "packet_id",
                "terminal_status",
                "refusals",
                "open_obstruction_ids",
                "candidate_ids",
                "patch_ids",
            }
        ),
        types={
            "packet_id": _STR,
            "terminal_status": _STR,
            "refusals": _ARRAY,
            "open_obstruction_ids": _ARRAY,
            "candidate_ids": _ARRAY,
            "patch_ids": _ARRAY,
        },
    ),
    EventSchema(
        EVENT_STAGE_REFUSED,
        required=frozenset({"stage", "refusal_type", "refusal"}),
        types={"stage": _STR, "refusal_type": _STR, "refusal": _STR},
    ),
):
    register_event_schema(_schema)

del _schema

# V1 is accepted only when RunStarted declares it. It is never registered as
# the writer schema and therefore cannot be emitted by ``ExecutionTrace``.
_V1_RESPONSE_SCHEMA = EventSchema(
    EVENT_RESPONSE_DURABLE,
    required=frozenset(
        {
            "attempt_id",
            "provider",
            "model",
            "raw_response_sha256",
            "raw_response_byte_count",
            "raw_response_path",
        }
    ),
    types={
        "attempt_id": _STR,
        "provider": _STR,
        "model": _STR,
        "raw_response_sha256": _STR,
        "raw_response_byte_count": _INT,
        "raw_response_path": _STR,
    },
    forbidden=frozenset({"encrypted_artifact_ref"}),
)
