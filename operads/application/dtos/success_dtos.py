"""Success DTOs for OEWAS V3 Application Handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class CompileCatalogResultDTO:
    catalog_id: str
    estate_ref: str
    epoch: int
    total_skills: int
    total_operations: int
    catalog_digest: str


@dataclass(frozen=True, slots=True)
class VerifyCatalogResultDTO:
    catalog_id: str
    is_valid: bool
    total_operations_verified: int
    errors: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectionResultDTO:
    projection_id: str
    catalog_id: str
    target_format: str
    manifest_digest: str
    payload: str


@dataclass(frozen=True, slots=True)
class SignedManifestEnvelopeDTO:
    manifest_id: str
    catalog_id: str
    epoch: int
    target_format: str
    content_digest: str
    signer_id: str
    signature_algorithm: str
    signature_hex: str
    payload: str


@dataclass(frozen=True, slots=True)
class LicensedTermResultDTO:
    agent_id: str
    term_expr: str
    is_authorized: bool
    normalized_digest: str


@dataclass(frozen=True, slots=True)
class WorkflowValidationResultDTO:
    is_valid: bool
    node_count: int
    edge_count: int
    cycles: Tuple[Tuple[str, ...], ...] = ()
    colour_mismatches: Tuple[str, ...] = ()
    orphaned_edges: Tuple[str, ...] = ()
    topological_order: Tuple[str, ...] = ()
    execution_stages: Tuple[Tuple[str, ...], ...] = ()
    #: Node ids supplied more than once. The node map is keyed by id, so a
    #: duplicate silently overwrote its predecessor and only the last node's
    #: ports and colours were ever checked. Reported rather than collapsed.
    duplicate_node_ids: Tuple[str, ...] = ()
    typed_interface: dict | None = None
