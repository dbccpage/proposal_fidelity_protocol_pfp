"""Filesystem storage adapter for PFP YAML manifests, specs, and demo catalogs.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.contracts.contracts import ContractSpec
from ..domain.contracts.gates import GateSpec
from ..domain.contracts.schemas import SchemaCatalog, SchemaSpec
from ..domain.kernel.ports import PfpDemoCatalogPort, PfpStoragePort
from ..domain.normal_forms import NormalFormContract
from ..domain.prompts.prompts import PromptTemplate
from ..domain.rewriting.wires import SyntaxProfile
from ..domain.stages.demos import DemoCatalog, DemoSpec
from ..domain.stages.modes import ModeFile, ModesManifest
from ..domain.stages.stages import StageController, StageFile
from .terminal_routing import load_terminal_routing
from .yaml_loading import strict_yaml_load


class PfpFileSystemStorageAdapter(PfpStoragePort, PfpDemoCatalogPort):
    """Loads PFP assets from one declared resource directory."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        if data_root is not None:
            self.root = Path(data_root)
        else:
            self.root = Path(__file__).resolve().parent / "yaml"
        if not self.root.is_dir():
            raise FileNotFoundError(self.root)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"PFP YAML file not found: {path}")
        return strict_yaml_load(path.read_text(encoding="utf-8"))

    def load_stage_controller(self) -> StageController:
        p = self.root / "stages" / "controller.yaml"
        data = self._load_yaml(p)
        return StageController.model_validate(data)

    def load_stage_file(self, stage_number: int) -> StageFile:
        stage_dir = self.root / "stages"
        candidates = list(stage_dir.glob(f"stage_{stage_number}_*.yaml"))
        if not candidates:
            raise FileNotFoundError(f"No stage file found for stage {stage_number} in {stage_dir}")
        data = self._load_yaml(candidates[0])
        return StageFile.model_validate(data)

    def load_terminal_routing(self) -> Dict[str, str]:
        return load_terminal_routing()

    def load_modes_manifest(self) -> ModesManifest:
        p = self.root / "modes" / "modes_manifest.yaml"
        data = self._load_yaml(p)
        return ModesManifest.model_validate(data)

    def load_mode_file(self, mode_id: int) -> ModeFile:
        mode_dir = self.root / "modes"
        candidates = list(mode_dir.glob(f"mode_{mode_id:02d}_*/contract.yaml"))
        if not candidates:
            raise FileNotFoundError(f"No mode file found for mode {mode_id} in {mode_dir}")
        data = self._load_yaml(candidates[0])
        return ModeFile.model_validate(data)

    def load_gate_spec(self, gate_id: str) -> GateSpec:
        gates_dir = self.root / "gates"
        for p in gates_dir.glob("*.yaml"):
            if p.name == "gate_register.yaml":
                continue
            data = self._load_yaml(p)
            if data.get("gate_id") == gate_id or p.stem == gate_id:
                return GateSpec.model_validate(data)
        raise FileNotFoundError(f"Gate {gate_id} not found in {gates_dir}")

    def list_gate_specs(self) -> List[GateSpec]:
        gates_dir = self.root / "gates"
        specs = []
        for p in sorted(gates_dir.glob("*.yaml")):
            if p.name == "gate_register.yaml":
                continue
            data = self._load_yaml(p)
            specs.append(GateSpec.model_validate(data))
        return specs

    def load_contract_spec(self, contract_id: str) -> ContractSpec:
        c_dir = self.root / "contracts"
        for p in c_dir.glob("*.yaml"):
            data = self._load_yaml(p)
            if data.get("contract_id") == contract_id or p.stem == contract_id:
                return ContractSpec.model_validate(data)
        raise FileNotFoundError(f"Contract {contract_id} not found in {c_dir}")

    def load_schema_catalog(self) -> SchemaCatalog:
        s_dir = self.root / "schemas"
        schemas: Dict[str, SchemaSpec] = {}
        for p in sorted(s_dir.glob("*.yaml")):
            data = self._load_yaml(p)
            s_id = data.get("$id", p.stem)
            title = data.get("title", p.stem)
            schemas[s_id] = SchemaSpec(
                schema_id=s_id,
                title=title,
                definition=data,
            )
        return SchemaCatalog(schemas=schemas)

    def _resolve_nf_dir(self) -> Path:
        for candidate in [self.root / "normal_forms", self.root / "nf"]:
            if candidate.is_dir():
                return candidate
        return self.root / "normal_forms"

    def load_normal_form_contract(self, nf_id: str) -> NormalFormContract:
        nf_dir = self._resolve_nf_dir()
        for p in nf_dir.glob("nf.*.yaml"):
            data = self._load_yaml(p)
            if data.get("identity", {}).get("id") == nf_id or p.stem == nf_id:
                return NormalFormContract.model_validate(data)
        raise FileNotFoundError(f"Normal form {nf_id} not found in {nf_dir}")

    def list_normal_form_contracts(self) -> List[NormalFormContract]:
        nf_dir = self._resolve_nf_dir()
        contracts = []
        for p in sorted(nf_dir.glob("nf.*.yaml")):
            data = self._load_yaml(p)
            contracts.append(NormalFormContract.model_validate(data))
        return contracts

    def load_prompt_template(self, template_id: str) -> PromptTemplate:
        p_dir = self.root / "prompts"
        candidates = list(p_dir.glob(f"{template_id}.yaml")) or list(p_dir.glob("*.yaml"))
        for p in candidates:
            data = self._load_yaml(p)
            if data.get("template_id") == template_id or p.stem == template_id:
                return PromptTemplate.model_validate(data)
        # Default fallback template
        return PromptTemplate(
            template_id=template_id,
            version="1.0.0",
            system_format="You are a Symbol Game evaluator.",
            user_format="Evaluate seed: {seed}",
        )

    def load_syntax_profile(self, profile_id: str) -> SyntaxProfile:
        w_dir = self.root / "wires"
        for p in w_dir.glob("*.yaml"):
            data = self._load_yaml(p)
            stem = p.stem.lower()
            p_id = data.get("profile_id", "").lower()
            target = profile_id.lower()
            if target == stem or target == p_id or target in stem or target in p_id:
                return SyntaxProfile.model_validate(data)
        raise FileNotFoundError(f"Syntax profile {profile_id} not found in {w_dir}")

    # DemoCatalogPort implementation
    def load_catalog(self) -> DemoCatalog:
        demos = [
            DemoSpec(
                id="demo_000",
                title="MSS-N 50-Seed Canonical Verification Suite",
                profile="standard",
                seed="seed_mssn_000",
                model_seed="mssn_50",
            ),
            DemoSpec(
                id="demo_001",
                title="Round 00-99 Gate Evaluator Suite",
                profile="gate_audit",
                seed="seed_demo_001",
                model_seed="rounds_100",
            ),
            DemoSpec(
                id="demo_002",
                title="Generalization & Problem Declaration Suite",
                profile="generalization",
                seed="seed_demo_002",
                model_seed="gen_100",
            ),
            DemoSpec(
                id="demo_003",
                title="Multi-Demo Master Suite (Demos 1-12 & MUB6 Regge)",
                profile="multi_demo",
                seed="seed_demo_003",
                model_seed="multi_12",
            ),
            DemoSpec(
                id="demo_004",
                title="150-Test Challenge & Cohomology Agenda Suite",
                profile="challenge_150",
                seed="seed_demo_004",
                model_seed="challenges_150",
            ),
            DemoSpec(
                id="demo_sn_000",
                title="S(n) Adversarial Machine Gate Benchmark Suite",
                profile="sn_adversarial",
                seed="seed_sn_000",
                model_seed="sn_50",
            ),
        ]
        return DemoCatalog(demos=demos)

    def get_demo(self, demo_id: str) -> Optional[DemoSpec]:
        catalog = self.load_catalog()
        return catalog.get_by_id(demo_id)
