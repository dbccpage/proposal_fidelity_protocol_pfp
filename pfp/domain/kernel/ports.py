"""Abstract Domain Protocols (Ports) for the PFP application.

Enables pure dependency inversion for external adapters (filesystem, LLM providers,
mathematical solvers, and demo runners).
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from ..contracts.contracts import ContractAuditReceipt, ContractSpec
from ..stages.demos import DemoCatalog, DemoRunReceipt, DemoSpec
from ..contracts.gates import GateReceipt, GateSpec, GateVerdict
from ..stages.modes import ModeFile, ModesManifest
from ..normal_forms import NormalFormContract, NormalFormVerificationReceipt
from ..prompts.packets import PacketEnvelope, PacketVerificationReceipt
from ..prompts.prompts import PromptPacket, PromptTemplate
from .result import Result
from ..rewriting.rewrites import RewriteReceipt, RewriteRequest
from ..contracts.schemas import SchemaCatalog, SchemaSpec, SchemaValidationResult
from ..stages.stages import BaseStageResponse, Stage5Response, StageController, StageFile


class PfpStoragePort(Protocol):
    """Protocol for reading and writing PFP YAML/JSON assets."""

    def load_stage_controller(self) -> StageController:
        ...

    def load_stage_file(self, stage_number: int) -> StageFile:
        ...

    def load_terminal_routing(self) -> Dict[str, str]:
        """PFP terminal value to `omega_types::routing::RoutingTerminal` name."""
        ...

    def load_modes_manifest(self) -> ModesManifest:
        ...

    def load_mode_file(self, mode_id: int) -> ModeFile:
        ...

    def load_gate_spec(self, gate_id: str) -> GateSpec:
        ...

    def list_gate_specs(self) -> List[GateSpec]:
        ...

    def load_contract_spec(self, contract_id: str) -> ContractSpec:
        ...

    def load_schema_catalog(self) -> SchemaCatalog:
        ...

    def load_normal_form_contract(self, nf_id: str) -> NormalFormContract:
        ...

    def list_normal_form_contracts(self) -> List[NormalFormContract]:
        ...

    def load_prompt_template(self, template_id: str) -> PromptTemplate:
        ...


class PfpDemoCatalogPort(Protocol):
    """Protocol for discovering and fetching registered demos."""

    def load_catalog(self) -> DemoCatalog:
        ...

    def get_demo(self, demo_id: str) -> Optional[DemoSpec]:
        ...


class PfpDemoRunnerPort(Protocol):
    """Protocol for executing an individual demo and recording an immutable receipt."""

    def run_demo(self, spec: DemoSpec) -> DemoRunReceipt:
        ...

    def run_all(self, catalog: DemoCatalog) -> List[DemoRunReceipt]:
        ...


class PfpGateEvaluatorPort(Protocol):
    """Protocol for evaluating Woland Tribunal gates on candidate states."""

    def evaluate_gate(self, gate_spec: GateSpec, candidate_state: Dict[str, Any]) -> GateVerdict:
        ...

    def evaluate_tribunal(self, candidate_id: str, candidate_state: Dict[str, Any]) -> GateReceipt:
        ...


class PfpLlmProviderPort(Protocol):
    """Protocol for candidate generation (offline deterministic mock or live API)."""

    def generate_candidate(
        self,
        packet: PromptPacket,
        temperature: float = 0.0,
    ) -> str:
        ...


class PfpHostVerifierPort(Protocol):
    """Protocol for the host's own Stage 5 check of the model's Stage 1-4 output.

    The host re-derives the candidate itself. It must not echo a verdict the
    model reported about its own work.
    """

    def verify(
        self,
        demo_id: str,
        prior_responses: Mapping[int, Dict[str, Any]],
    ) -> Stage5Response:
        ...

    def verify_mode(self, mode_id: int, mode_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a bounded supplied mode witness with the existing host owners."""
        ...


class PfpSolverPort(Protocol):
    """Protocol for delegating exact rational and cochain computations."""

    def evaluate_cochain_coboundary(
        self,
        d_matrix_data: Sequence[Sequence[int]],
        cochain_vals: Sequence[int],
    ) -> Tuple[int, ...]:
        ...


class GenesisCycleSolverPort(Protocol):
    """Protocol for Genesis cycle balance and Smith Normal Form solver."""

    ...


class PfpJudgeAuditPort(Protocol):
    """Protocol for executing multi-agent judge audit suites."""

    def execute_audit(self, round_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
