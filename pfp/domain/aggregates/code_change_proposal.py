"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    ALLOWED_TRANSFORMS,
    Any,
    CODE_CHANGE_EVIDENCE_CEILING,
    CODE_CHANGE_FAMILY,
    CODE_CHANGE_PROPOSAL_SCHEMA,
    CODE_CHANGE_TERMINAL_TARGET,
    MAX_CANDIDATE_BUDGET,
    MAX_CANONICAL_PAYLOAD_BYTES,
    MAX_OPERATION_BUDGET,
    Mapping,
    PAYLOAD_DOMAIN,
    REQUIRED_GATE_IDS,
    _canonical_json_size,
    _fail,
    _path_manifest_root,
    _path_tuple_from_wire,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_optional_digest,
    _require_positive_int,
    _require_revision,
    _require_string,
    _string_tuple_from_wire,
    _validate_ordered_unique_strings,
    _validate_path_tuple,
    domain_digest,
    field,
)


@dataclass(frozen=True, slots=True)
class CodeChangeProposalPayloadV1:
    """Strict family payload for a scoped code-change proposal task."""

    objective: str
    source_revision: str
    owned_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    allowed_transforms: tuple[str, ...]
    candidate_budget: int
    operation_budget: int
    required_gates: tuple[str, ...]
    terminal_target: str = field(default=CODE_CHANGE_TERMINAL_TARGET)
    evidence_ceiling: str = field(default=CODE_CHANGE_EVIDENCE_CEILING)
    parent_packet_id: str | None = None
    path_manifest_root: str = field(default="")
    family: str = field(default=CODE_CHANGE_FAMILY)
    schema_version: str = field(default=CODE_CHANGE_PROPOSAL_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_string(self.objective, "objective", nonempty=True)
        _require_revision(self.source_revision, "source_revision")
        owned = _validate_path_tuple(self.owned_paths, "owned_paths")
        protected = _validate_path_tuple(self.protected_paths, "protected_paths")
        object.__setattr__(self, "owned_paths", owned)
        object.__setattr__(self, "protected_paths", protected)
        if not owned:
            _fail("owned_paths must be nonempty")
        overlap = set(owned) & set(protected)
        if overlap:
            _fail(
                "protected_paths must be disjoint from owned_paths: "
                + ", ".join(sorted(overlap))
            )
        transforms = _validate_ordered_unique_strings(
            self.allowed_transforms, "allowed_transforms"
        )
        if not transforms or not set(transforms).issubset(ALLOWED_TRANSFORMS):
            _fail("allowed_transforms contains unsupported entries")
        object.__setattr__(self, "allowed_transforms", transforms)
        _require_positive_int(
            self.candidate_budget, "candidate_budget", maximum=MAX_CANDIDATE_BUDGET
        )
        _require_positive_int(
            self.operation_budget, "operation_budget", maximum=MAX_OPERATION_BUDGET
        )
        gates = _validate_ordered_unique_strings(self.required_gates, "required_gates")
        if not gates or not set(gates).issubset(REQUIRED_GATE_IDS):
            _fail("required_gates contains unsupported entries")
        object.__setattr__(self, "required_gates", gates)
        if self.terminal_target != CODE_CHANGE_TERMINAL_TARGET:
            _fail("terminal_target is unsupported")
        if self.evidence_ceiling != CODE_CHANGE_EVIDENCE_CEILING:
            _fail("evidence_ceiling is unsupported")
        if self.parent_packet_id is not None:
            _require_digest(self.parent_packet_id, "parent_packet_id")
        if self.family != CODE_CHANGE_FAMILY:
            _fail("code-change family is unsupported")
        if self.schema_version != CODE_CHANGE_PROPOSAL_SCHEMA:
            _fail("code-change proposal schema version is unsupported")
        if self.authority_effect != "None":
            _fail("code-change proposals must carry AuthorityEffect None")
        expected_root = _path_manifest_root(owned, protected)
        if self.path_manifest_root == "":
            object.__setattr__(self, "path_manifest_root", expected_root)
        else:
            _require_digest(self.path_manifest_root, "path_manifest_root")
            if self.path_manifest_root != expected_root:
                _fail("path_manifest_root does not bind owned and protected paths")
        if _canonical_json_size(self.to_dict()) > MAX_CANONICAL_PAYLOAD_BYTES:
            _fail("code-change proposal payload exceeds the canonical resource limit")

    @property
    def payload_id(self) -> str:
        return domain_digest(PAYLOAD_DOMAIN, self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "objective": self.objective,
            "source_revision": self.source_revision,
            "owned_paths": list(self.owned_paths),
            "protected_paths": list(self.protected_paths),
            "allowed_transforms": list(self.allowed_transforms),
            "candidate_budget": self.candidate_budget,
            "operation_budget": self.operation_budget,
            "required_gates": list(self.required_gates),
            "terminal_target": self.terminal_target,
            "evidence_ceiling": self.evidence_ceiling,
            "parent_packet_id": self.parent_packet_id,
            "path_manifest_root": self.path_manifest_root,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CodeChangeProposalPayloadV1":
        wire = _require_exact_dict(wire, "code-change proposal payload")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "family",
                    "objective",
                    "source_revision",
                    "owned_paths",
                    "protected_paths",
                    "allowed_transforms",
                    "candidate_budget",
                    "operation_budget",
                    "required_gates",
                    "terminal_target",
                    "evidence_ceiling",
                    "parent_packet_id",
                    "path_manifest_root",
                    "authority_effect",
                }
            ),
            "code-change proposal payload",
        )
        if _canonical_json_size(wire) > MAX_CANONICAL_PAYLOAD_BYTES:
            _fail("code-change proposal payload exceeds the canonical resource limit")
        return cls(
            objective=_require_string(wire["objective"], "objective", nonempty=True),
            source_revision=_require_revision(
                wire["source_revision"], "source_revision"
            ),
            owned_paths=_path_tuple_from_wire(wire["owned_paths"], "owned_paths"),
            protected_paths=_path_tuple_from_wire(
                wire["protected_paths"], "protected_paths"
            ),
            allowed_transforms=_string_tuple_from_wire(
                wire["allowed_transforms"], "allowed_transforms"
            ),
            candidate_budget=_require_positive_int(
                wire["candidate_budget"],
                "candidate_budget",
                maximum=MAX_CANDIDATE_BUDGET,
            ),
            operation_budget=_require_positive_int(
                wire["operation_budget"],
                "operation_budget",
                maximum=MAX_OPERATION_BUDGET,
            ),
            required_gates=_string_tuple_from_wire(
                wire["required_gates"], "required_gates"
            ),
            terminal_target=_require_string(
                wire["terminal_target"], "terminal_target", nonempty=True
            ),
            evidence_ceiling=_require_string(
                wire["evidence_ceiling"], "evidence_ceiling", nonempty=True
            ),
            parent_packet_id=_require_optional_digest(
                wire["parent_packet_id"], "parent_packet_id"
            ),
            path_manifest_root=_require_digest(
                wire["path_manifest_root"], "path_manifest_root"
            ),
            family=_require_string(wire["family"], "family", nonempty=True),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
