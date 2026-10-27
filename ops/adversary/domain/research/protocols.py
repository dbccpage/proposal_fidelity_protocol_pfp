"""Inward research protocols and ports for the Adversary stage / Adversary research panels.

AuthorityEffect: None.
Pure domain protocols for proposal gateways, stage routes, increment pads,
claim queues, and cloud kill dispatchers. No outer-layer dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from adversary.domain.providers.types import (
    BudgetReceipt,
    CandidateRequest,
    CandidateResponse,
    Provider,
)

AUTHORITY_EFFECT = "None"
SCHEMA_VERSION = "core.oears.cloud_kill_dispatch.v1"
KILL_DOMAIN_REQUIRED = "required"


@runtime_checkable
class ProposalGatewayPort(Protocol):
    """The existing proposal operation, without a concrete gateway dependency."""

    def complete(
        self,
        request: CandidateRequest,
        *,
        provider: Provider | None = None,
        model: str | None = None,
    ) -> tuple[CandidateResponse, BudgetReceipt | None]:
        """Return candidate data and an optional receipt, not execution authority."""
        ...


# ============================================================================
# Stage Route Port
# ============================================================================


@runtime_checkable
class StageRoutePort(Protocol):
    """Abstract stage route resolver and proposer."""

    def resolve_stage_route(self, stage_id: str) -> Any: ...

    def code_rust_propose_default_route(self) -> Any: ...

    def code_strict_inspect_route(self) -> Any: ...

    def run_propose_for_route(
        self,
        gateway: ProposalGatewayPort,
        route: Any,
        request: CandidateRequest,
        *,
        require_local_live: bool = False,
    ) -> tuple[Any, dict[str, Any]]: ...


_DEFAULT_STAGE_ROUTE_PORT: StageRoutePort | None = None


def register_stage_route_port(port: StageRoutePort) -> None:
    global _DEFAULT_STAGE_ROUTE_PORT
    _DEFAULT_STAGE_ROUTE_PORT = port


def get_stage_route_port() -> StageRoutePort:
    if _DEFAULT_STAGE_ROUTE_PORT is None:
        raise RuntimeError("STAGE_ROUTE_PORT_UNREGISTERED: stage route port not registered")
    return _DEFAULT_STAGE_ROUTE_PORT


# ============================================================================
# Increment Pad Port
# ============================================================================


@runtime_checkable
class IncrementPadPort(Protocol):
    """Abstract increment pad loader and merge check."""

    def load_pad(self, pad_root: Path | str) -> Any: ...

    def refuse_merge_unless_ready(
        self, pad: Any, *, authorizer_accept: bool = False
    ) -> None: ...


_DEFAULT_INCREMENT_PAD_PORT: IncrementPadPort | None = None


def register_increment_pad_port(port: IncrementPadPort) -> None:
    global _DEFAULT_INCREMENT_PAD_PORT
    _DEFAULT_INCREMENT_PAD_PORT = port


def get_increment_pad_port() -> IncrementPadPort:
    if _DEFAULT_INCREMENT_PAD_PORT is None:
        raise RuntimeError("INCREMENT_PAD_PORT_UNREGISTERED: increment pad port not registered")
    return _DEFAULT_INCREMENT_PAD_PORT


# ============================================================================
# Claim Queue Port & Types
# ============================================================================


class ClaimQueueError(ValueError):
    """Illegal claim-queue operation."""


@runtime_checkable
class ClaimQueuePort(Protocol):
    """Abstract claim queue reader."""

    def select_one_open_from_paper(
        self,
        paper_path: Path | str,
        *,
        priority_asc: bool = True,
        prefer_scale: bool = False,
    ) -> tuple[Any, Any]: ...


_DEFAULT_CLAIM_QUEUE_PORT: ClaimQueuePort | None = None


def register_claim_queue_port(port: ClaimQueuePort) -> None:
    global _DEFAULT_CLAIM_QUEUE_PORT
    _DEFAULT_CLAIM_QUEUE_PORT = port


def get_claim_queue_port() -> ClaimQueuePort:
    if _DEFAULT_CLAIM_QUEUE_PORT is None:
        raise RuntimeError("CLAIM_QUEUE_PORT_UNREGISTERED: claim queue port not registered")
    return _DEFAULT_CLAIM_QUEUE_PORT


# ============================================================================
# Cloud Kill Dispatcher Port & Types
# ============================================================================


class CloudKillDispatchError(ValueError):
    """Illegal cloud-under-kill dispatch or kill policy breach."""


@dataclass(frozen=True)
class CloudJobSpec:
    """Host-owned job request under kill domain."""

    kind: str
    work_path: str
    command: str
    budget_microusd: int = 0
    max_wall_seconds: int = 3600
    auto_resume: bool = False
    kill_domain: str = KILL_DOMAIN_REQUIRED

    def __post_init__(self) -> None:
        if self.kind not in ("lake", "cargo", "panel"):
            raise CloudKillDispatchError(
                f"kind must be lake|cargo|panel; got {self.kind!r}"
            )
        if self.kill_domain != KILL_DOMAIN_REQUIRED:
            raise CloudKillDispatchError("kill_domain must be 'required'")
        if self.auto_resume:
            raise CloudKillDispatchError(
                "auto_resume forbidden — resume requires new explicit authorize"
            )
        if self.budget_microusd < 0:
            raise CloudKillDispatchError("budget_microusd must be >= 0")
        if self.max_wall_seconds <= 0:
            raise CloudKillDispatchError("max_wall_seconds must be > 0")
        if not str(self.work_path).strip():
            raise CloudKillDispatchError("work_path required")
        if not str(self.command).strip():
            raise CloudKillDispatchError("command required")


@dataclass
class CloudJobReceipt:
    job_id: str
    kind: str
    work_path: str
    command: str
    status: str
    kill_domain: str = KILL_DOMAIN_REQUIRED
    kill_handle: str = ""
    auto_resume: bool = False
    resumed_after_kill: bool = False
    budget_microusd: int = 0
    cost_spent_microusd: int = 0
    deploys_worker: bool = False
    residual_open_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT
    claims_global_green: bool = False
    schema_version: str = SCHEMA_VERSION
    sprint: str = "sprint_ort_oears_scale_005_s2"
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if self.authority_effect != AUTHORITY_EFFECT:
            raise CloudKillDispatchError("authority_effect must be None")
        if self.claims_global_green:
            raise CloudKillDispatchError("must not claim GlobalGreen")
        if self.kill_domain != KILL_DOMAIN_REQUIRED:
            raise CloudKillDispatchError("kill_domain must be required")
        if self.auto_resume or self.resumed_after_kill:
            raise CloudKillDispatchError("auto-resume after kill forbidden")
        if not self.kill_handle:
            self.kill_handle = f"kill:{self.job_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sprint": self.sprint,
            "job_id": self.job_id,
            "kind": self.kind,
            "work_path": self.work_path,
            "command": self.command,
            "status": self.status,
            "kill_domain": self.kill_domain,
            "kill_handle": self.kill_handle,
            "auto_resume": self.auto_resume,
            "resumed_after_kill": self.resumed_after_kill,
            "budget_microusd": self.budget_microusd,
            "cost_spent_microusd": self.cost_spent_microusd,
            "deploys_worker": self.deploys_worker,
            "residual_open_ids": list(self.residual_open_ids),
            "notes": list(self.notes),
            "authority_effect": self.authority_effect,
            "claims_global_green": self.claims_global_green,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }


@runtime_checkable
class CloudKillDispatcherPort(Protocol):
    """Abstract cloud-under-kill dispatcher."""

    def admit_and_dispatch(self, spec: CloudJobSpec) -> CloudJobReceipt: ...


_DEFAULT_CLOUD_KILL_DISPATCHER_PORT: CloudKillDispatcherPort | None = None


def register_cloud_kill_dispatcher_port(port: CloudKillDispatcherPort) -> None:
    global _DEFAULT_CLOUD_KILL_DISPATCHER_PORT
    _DEFAULT_CLOUD_KILL_DISPATCHER_PORT = port


def get_cloud_kill_dispatcher_port() -> CloudKillDispatcherPort:
    if _DEFAULT_CLOUD_KILL_DISPATCHER_PORT is None:
        raise RuntimeError(
            "CLOUD_KILL_DISPATCHER_PORT_UNREGISTERED: cloud kill dispatcher port not registered"
        )
    return _DEFAULT_CLOUD_KILL_DISPATCHER_PORT


# ============================================================================
# Paper Carrier Port & Types
# ============================================================================


@runtime_checkable
class PaperCarrierPort(Protocol):
    """Abstract carrier loader, hash computation, and claim reader. Zero host I/O in domain."""

    def compute_tree_hash(self, paper_root: Path | str) -> str: ...

    def parse_claims(self, paper_root: Path | str) -> list[Any]: ...

    def load_program_profile(
        self,
        program_id: str,
        *,
        profiles_dir: Path | None = None,
    ) -> Any: ...

    def enforce_estate_path_gate(
        self,
        paper_root: Path | str,
        profile: Any,
        *,
        repo_root: Path | None = None,
    ) -> None: ...

    def list_program_ids(self, profiles_dir: Path | None = None) -> list[str]: ...

    def load_skill_program_map(self, map_path: Path | None = None) -> dict[str, Any]: ...

    def resolve_program_id(
        self,
        name: str,
        *,
        map_path: Path | None = None,
        profiles_dir: Path | None = None,
    ) -> str: ...


_DEFAULT_PAPER_CARRIER_PORT: PaperCarrierPort | None = None


def register_paper_carrier_port(port: PaperCarrierPort) -> None:
    global _DEFAULT_PAPER_CARRIER_PORT
    _DEFAULT_PAPER_CARRIER_PORT = port


def get_paper_carrier_port() -> PaperCarrierPort:
    if _DEFAULT_PAPER_CARRIER_PORT is None:
        raise RuntimeError(
            "PAPER_CARRIER_PORT_UNREGISTERED: paper carrier port not registered"
        )
    return _DEFAULT_PAPER_CARRIER_PORT


__all__ = [
    "ClaimQueueError",
    "ClaimQueuePort",
    "CloudJobReceipt",
    "CloudJobSpec",
    "CloudKillDispatchError",
    "CloudKillDispatcherPort",
    "IncrementPadPort",
    "PaperCarrierPort",
    "ProposalGatewayPort",
    "StageRoutePort",
    "get_claim_queue_port",
    "get_cloud_kill_dispatcher_port",
    "get_increment_pad_port",
    "get_paper_carrier_port",
    "get_stage_route_port",
    "register_claim_queue_port",
    "register_cloud_kill_dispatcher_port",
    "register_increment_pad_port",
    "register_paper_carrier_port",
    "register_stage_route_port",
]

