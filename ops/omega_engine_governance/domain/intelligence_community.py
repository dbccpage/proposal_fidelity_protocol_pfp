"""Pydantic V2 Domain Models for the Omega Engine Intelligence Community.

Validates agency membership, typed capability surfaces, artifact contracts, and definitions.
Model fields are frozen; the nested agency dictionary remains mutable.
AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Sequence

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class _CanonLoader(yaml.SafeLoader):
    """Safe YAML with string keys and no ambiguous merged/duplicate mappings."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key, value in self.construct_pairs(node, deep=deep):
            if not isinstance(key, str):
                raise ValueError("Canon mapping keys must be strings")
            if key in result:
                raise ValueError(f"Duplicate canon key: {key!r}")
            result[key] = value
        return result


class AgencyCode(str, Enum):
    """Canonical agencies comprising the Omega Engine Intelligence Community."""
    ODNI = "odni"
    CIA = "cia"
    NSA = "nsa"
    DIA = "dia"
    NRO = "nro"
    NGA = "nga"
    FBI = "fbi"
    INR = "inr"
    NCTC = "nctc"
    NCSC = "ncsc"
    NCPC = "ncpc"
    DEA = "dea"
    DHS = "dhs"
    CG = "cg"
    TREASURY = "treasury"
    DOE = "doe"
    ARMY = "army"
    ONI = "oni"
    AF = "af"
    MARINES = "marines"
    CDC = "cdc"
    DARPA = "darpa"
    NARA = "nara"
    DOD = "dod"


# 23 canonical foundational agencies loaded from intelligence_community.yaml
CANONICAL_23_AGENCIES: frozenset[AgencyCode] = frozenset(
    code for code in AgencyCode if code != AgencyCode.DOD
)

# Constituent military service branches whose artifact subfolders consolidate under _ic/dod/
DOD_SUBORDINATE_AGENCIES: frozenset[str] = frozenset({
    AgencyCode.ARMY.value,
    AgencyCode.MARINES.value,
    AgencyCode.AF.value,
    AgencyCode.CG.value,
    AgencyCode.ONI.value,
})


class AgencyDesignation(str, Enum):
    """Designation type: core member or affiliate."""
    MEMBER = "member"
    AFFILIATE = "affiliate"


class AgencyClearance(str, Enum):
    """Clearance ceiling classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    SEALED = "sealed"


class AgencyStatus(str, Enum):
    """Lifecycle status of the agency."""
    ACTIVE = "active"
    STANDBY = "standby"
    ARCHIVED = "archived"


class AgencyRecord(BaseModel):
    """Typed record carrying mandate, capability surface, artifact contract, and clearance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Full agency title.")
    abbr: str = Field(..., description="Abbreviation or acronym.")
    designation: AgencyDesignation = Field(..., description="Whether core member or affiliate.")
    tier: int = Field(..., ge=1, le=3, description="1 = executive, 2 = national, 3 = departmental/service/affiliate.")
    mandate: str = Field(..., description="Authoritative mandate statement.")
    capabilities: tuple[str, ...] = Field(..., description="Declared agency capabilities.")
    produces: tuple[str, ...] = Field(..., description="Authoritative artifact classes produced.")
    consumes: tuple[str, ...] = Field(default_factory=tuple, description="Declared artifact dependencies consumed.")
    clearance: AgencyClearance = Field(..., description="Clearance ceiling.")
    status: AgencyStatus = Field(AgencyStatus.ACTIVE, description="Lifecycle status.")
    brief: str = Field(..., description="One-line v1-compatible summary.")


def _require_unique_producers(agencies: dict[str, AgencyRecord]) -> None:
    """Refuse an artifact class claimed by more than one agency."""
    owners: dict[str, list[str]] = {}
    for code, record in agencies.items():
        for artifact_class in record.produces:
            owners.setdefault(artifact_class, []).append(code)
    duplicates = {artifact: codes for artifact, codes in owners.items() if len(codes) != 1}
    if duplicates:
        raise ValueError(f"Artifact classes must have exactly one producer: {duplicates}")


# Preserve whole existing product namespaces, including sealed run bundles.
_INTELLIGENCE_ROUTES = MappingProxyType({
    "_woland": (AgencyCode.DARPA, "the city"),
    "symbol_game": (AgencyCode.DARPA, "symbol_game"),
    "events": (AgencyCode.NSA, "events"),
    "narratives": (AgencyCode.ODNI, "narratives"),
    "unified_oe_trace.jsonl": (AgencyCode.ODNI, "unified_oe_trace.jsonl"),
    "universal_narrative_stream.md": (AgencyCode.ODNI, "universal_narrative_stream.md"),
    "_vladimir_central": (AgencyCode.FBI, "vladimir_central"),
    "red_team": (AgencyCode.DIA, "red_team"),
    "council_meetings": (AgencyCode.FBI, "council_meetings"),
    "stress_tests": (AgencyCode.DIA, "stress_tests"),
    "morphisms": (AgencyCode.NGA, "morphisms"),
    "_woland": (AgencyCode.DARPA, "woland"),
    "_oeos": (AgencyCode.ODNI, "oeos_control"),
    "oeos": (AgencyCode.ODNI, "oeos"),
    "harvest": (AgencyCode.NARA, "harvest"),
    "archive": (AgencyCode.NARA, "_archive"),
    "permanent_records": (AgencyCode.NARA, "permanent_records"),
    "research": (AgencyCode.DARPA, "research"),
    "antibodies": (AgencyCode.CDC, "antibodies"),
    "omega_paper_reviews": (AgencyCode.INR, "omega_paper_reviews"),
    "code_reviews": (AgencyCode.NRO, "code_reviews"),
    "coverage": (AgencyCode.NRO, "coverage"),
    "documentation": (AgencyCode.NRO, "documentation"),
    "omc_dags": (AgencyCode.NGA, "omc_dags"),
    "blackrod": (AgencyCode.FBI, "blackrod"),
})


def canonical_intelligence_route(legacy_relative: str) -> str:
    """Pure canonical route for a normalized legacy locator; no I/O or authority."""
    if type(legacy_relative) is not str:
        raise ValueError("legacy intelligence locator must be a string")
    parts = legacy_relative.split("/")
    if (len(parts) < 2 or parts[0] != "_intelligence"
            or any(not part or part in {".", ".."} or ":" in part or "\\" in part for part in parts)):
        raise ValueError("normalized legacy intelligence locator required")
    if parts[1] == "_woland":
        return "/".join(("_ic", "woland", *parts[2:]))
    route = _INTELLIGENCE_ROUTES.get(parts[1])
    if route is None:
        return "/".join(("_ic", AgencyCode.NARA.value, "legacy", *parts[1:]))
    agency, namespace = route
    folder = "dod" if agency.value in DOD_SUBORDINATE_AGENCIES else agency.value
    return "/".join(("_ic", folder, namespace, *parts[2:]))



# The fundamental type mapping folder name to typed agency record
IntelligenceCommunityMapping = Dict[str, AgencyRecord]


class IntelligenceCommunity(BaseModel):
    """Validated agency mapping with frozen fields and a mutable nested dictionary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agencies: IntelligenceCommunityMapping = Field(
        ...,
        description="Deterministic mapping of agency folder names to their authoritative AgencyRecord definitions."
    )

    @field_validator("agencies", mode="before")
    @classmethod
    def validate_agency_completeness_and_coerce(cls, v: Any) -> dict[str, AgencyRecord]:
        if not isinstance(v, dict):
            raise ValueError("Agency mapping must be a dictionary.")

        base_expected = {code.value for code in CANONICAL_23_AGENCIES}
        all_expected = {code.value for code in AgencyCode}
        actual_keys = set(v.keys())
        if actual_keys != base_expected and actual_keys != all_expected:
            missing = base_expected - actual_keys
            unexpected = actual_keys - all_expected
            err_msg = []
            if missing:
                err_msg.append(f"Missing mandatory agencies: {sorted(missing)}")
            if unexpected:
                err_msg.append(f"Unexpected non-agency folders: {sorted(unexpected)}")
            raise ValueError("; ".join(err_msg))

        coerced: dict[str, AgencyRecord] = {}
        for code, defn in v.items():
            if isinstance(defn, AgencyRecord):
                coerced[code] = defn
            elif isinstance(defn, dict):
                try:
                    coerced[code] = AgencyRecord.model_validate(defn)
                except Exception as exc:
                    raise ValueError(f"Invalid agency record for '{code}': {exc}") from exc
            else:
                raise ValueError(f"Agency definition for '{code}' must be an agency record.")
        _require_unique_producers(coerced)
        return coerced

    @classmethod
    def _dod_record(cls) -> AgencyRecord:
        """Authoritative record for the consolidated Department of Defense clearinghouse."""
        return AgencyRecord(
            name="Department of Defense",
            abbr="DOD",
            designation=AgencyDesignation.MEMBER,
            tier=3,
            mandate=(
                "Consolidated operational clearinghouse for military service elements "
                "(Army/INSCOM, Marine Corps/MCI, Air Force/AF-ISR, Coast Guard/CGI, and Navy/ONI)."
            ),
            capabilities=(
                "boundary patrol",
                "coverage gap detection",
                "dataset curation",
                "deep retrieval navigation",
                "drift monitoring",
                "edge and austere operation",
                "evaluation set maintenance",
                "expeditionary deployment",
                "forward reconnaissance",
                "ground-truth corpus engineering",
                "high-altitude sweeps",
                "interdiction logging",
                "latency profiling",
                "littoral telemetry",
                "live stream interception",
                "long-context charting",
                "recursion depth sounding",
                "self-contained packaging",
                "terrain modeling",
                "wide-area reconnaissance",
            ),
            produces=(
                "boundary_patrol",
                "depth_sounding",
                "edge_deployment",
                "expedition_pack",
                "ground_truth_corpus",
                "interdiction_log",
                "latency_profile",
                "long_context_chart",
                "recon_sweep",
                "terrain_model",
            ),
            consumes=(
                "clearing_brief",
                "code_audit",
                "dependency_chart",
                "morphism_dag",
                "perimeter_filter",
                "proof_gate_receipt",
                "research_dossier",
                "sigint_stream",
                "terrain_model",
                "turn_journal",
            ),
            clearance=AgencyClearance.INTERNAL,
            status=AgencyStatus.ACTIVE,
            brief="Department of Defense: Consolidated operational clearinghouse for military service elements.",
        )

    @classmethod
    def load_canon(cls, yaml_path: Path | None = None) -> IntelligenceCommunity:
        """Load a literal agency mapping; refuse duplicate YAML definitions."""
        if yaml_path is None:
            yaml_path = Path(__file__).resolve().parents[1] / "_types" / "intelligence_community.yaml"

        if not yaml_path.is_file():
            raise FileNotFoundError(f"Intelligence Community canon file not found: {yaml_path}")

        try:
            raw = yaml.load(yaml_path.read_text(encoding="utf-8"), Loader=_CanonLoader)
        except yaml.YAMLError as exc:
            raise ValueError(f"Malformed intelligence community YAML at {yaml_path}: {exc}") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("intelligence_community"), dict):
            raise ValueError(f"Malformed intelligence community YAML at {yaml_path}")

        return cls(agencies=dict(raw["intelligence_community"]))

    def is_valid_agency(self, folder_name: str) -> bool:
        """Check whether a given directory name is an authorized top-level agency folder."""
        return folder_name in self.agencies or folder_name in {AgencyCode.DOD.value, "dod"}

    def get_definition(self, agency: str | AgencyCode) -> str:
        """Get the authoritative mission definition for an agency."""
        key = agency.value if isinstance(agency, AgencyCode) else agency
        if key in {AgencyCode.DOD.value, "dod"} and key not in self.agencies:
            record = self._dod_record()
            return record.brief or record.mandate
        if key not in self.agencies:
            raise KeyError(f"'{key}' is not an authorized member of the Intelligence Community.")
        record = self.agencies[key]
        return record.brief or record.mandate

    def get_record(self, agency: str | AgencyCode) -> AgencyRecord:
        """Get the authoritative typed AgencyRecord for an agency."""
        key = agency.value if isinstance(agency, AgencyCode) else agency
        if key in {AgencyCode.DOD.value, "dod"} and key not in self.agencies:
            return self._dod_record()
        if key not in self.agencies:
            raise KeyError(f"'{key}' is not an authorized member of the Intelligence Community.")
        return self.agencies[key]

    def get_authoritative_producer(self, artifact_class: str) -> AgencyRecord:
        """Return the one agency whose `produces` contains this class."""
        matches = [record for record in self.agencies.values() if artifact_class in record.produces]
        if not matches:
            if artifact_class in self._dod_record().produces:
                return self._dod_record()
            raise KeyError(f"No canonical agency produces artifact class '{artifact_class}'.")
        if len(matches) != 1:
            owners = [record.abbr for record in matches]
            raise ValueError(f"Artifact class '{artifact_class}' has multiple producers: {owners}")
        return matches[0]

    def route_produced_artifact(self, agency: str | AgencyCode, artifact_class: str, filename: str) -> str:
        """Route an artifact produced by an agency to its authoritative relative path."""
        code = agency.value if isinstance(agency, AgencyCode) else agency
        record = self.get_record(code)
        if artifact_class not in record.produces:
            raise ValueError(f"Agency '{code}' is not authorized to produce artifact class '{artifact_class}'.")
        folder = "dod" if code in DOD_SUBORDINATE_AGENCIES or code in {AgencyCode.DOD.value, "dod"} else code
        return f"_ic/{folder}/{artifact_class}/{filename}"

    def resolve_consumed_artifact(self, consumer: str | AgencyCode, artifact_class: str) -> AgencyRecord:
        """Verify that a consumer declares consumption of an artifact class and resolve its authoritative producer."""
        code = consumer.value if isinstance(consumer, AgencyCode) else consumer
        record = self.get_record(code)
        if artifact_class not in record.consumes:
            raise ValueError(f"Agency '{code}' does not declare consumption of artifact class '{artifact_class}'.")
        return self.get_authoritative_producer(artifact_class)

    @property
    def agency_codes(self) -> Sequence[str]:
        """Return the sorted list of canonical agency folder names."""
        return tuple(sorted(self.agencies.keys()))
