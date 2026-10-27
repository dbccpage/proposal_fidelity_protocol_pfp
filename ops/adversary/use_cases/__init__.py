"""Application use cases for the Adversary Swarm.

AuthorityEffect: None.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .act_helpers import (
        execute_act1_carrier_framing,
        execute_act2_obstruction_identification,
        execute_act3_candidate_proposal_generation,
        execute_act3_epistemic_sieve,
        execute_act4_gauge_break,
        execute_act4_sandbox_verification,
        execute_act5_independent_witness,
        execute_act5_terminal_verdict,
        execute_act6_intern_report,
        execute_act6_residual_ledger,
        execute_act7_authorization_gate,
        execute_act7_crystallization,
        execute_candidate_checks,
    )
    from .bout_service import (
        AdversarySwarmService,
        execute_7act_adversary_bout,
    )
    from .governing_councils_bout_use_case import (
        GOVERNING_COUNCILS_PANEL_MAP,
        CouncilObligationV1,
        GoverningCouncilsBoutUseCase,
    )
    from .nomos_compliance_use_case import (
        BlackrodDefectLogger,
        ContractInspectionFindingV1,
        NomosComplianceReceiptV1,
        NomosContractScanner,
    )
    from .persistence import persist_bout_run_folder
    from .product_mgmt_bout_use_case import (
        PRODUCT_MGMT_PANEL_MAP,
        ProductMgmtBeatExecutionV1,
        ProductMgmtBoutUseCase,
    )
    from .software_dev_bout_use_case import (
        SOFTWARE_DEV_PANEL_MAP,
        PanelRoleMappingV1,
        SoftwareDevBoutUseCase,
    )
    from .thanatos_bout_use_case import (
        THANATOS_PANEL_MAP,
        ThanatosBeatExecutionV1,
        ThanatosBoutUseCase,
    )

__all__ = [
    "BlackrodDefectLogger",
    "ContractInspectionFindingV1",
    "CouncilObligationV1",
    "GOVERNING_COUNCILS_PANEL_MAP",
    "GoverningCouncilsBoutUseCase",
    "NomosComplianceReceiptV1",
    "NomosContractScanner",
    "PRODUCT_MGMT_PANEL_MAP",
    "ProductMgmtBeatExecutionV1",
    "ProductMgmtBoutUseCase",
    "PanelRoleMappingV1",
    "SOFTWARE_DEV_PANEL_MAP",
    "SoftwareDevBoutUseCase",
    "THANATOS_PANEL_MAP",
    "ThanatosBeatExecutionV1",
    "ThanatosBoutUseCase",
    "AdversarySwarmService",
    "execute_7act_adversary_bout",
    "execute_act1_carrier_framing",
    "execute_act2_obstruction_identification",
    "execute_act3_candidate_proposal_generation",
    "execute_act3_epistemic_sieve",
    "execute_act4_gauge_break",
    "execute_act4_sandbox_verification",
    "execute_act5_independent_witness",
    "execute_act5_terminal_verdict",
    "execute_act6_intern_report",
    "execute_act6_residual_ledger",
    "execute_act7_authorization_gate",
    "execute_act7_crystallization",
    "execute_candidate_checks",
    "persist_bout_run_folder",
]

_SUBMODULE_MAP = {
    "BlackrodDefectLogger": "nomos_compliance_use_case",
    "ContractInspectionFindingV1": "nomos_compliance_use_case",
    "CouncilObligationV1": "governing_councils_bout_use_case",
    "GOVERNING_COUNCILS_PANEL_MAP": "governing_councils_bout_use_case",
    "GoverningCouncilsBoutUseCase": "governing_councils_bout_use_case",
    "NomosComplianceReceiptV1": "nomos_compliance_use_case",
    "NomosContractScanner": "nomos_compliance_use_case",
    "PRODUCT_MGMT_PANEL_MAP": "product_mgmt_bout_use_case",
    "ProductMgmtBeatExecutionV1": "product_mgmt_bout_use_case",
    "ProductMgmtBoutUseCase": "product_mgmt_bout_use_case",
    "PanelRoleMappingV1": "software_dev_bout_use_case",
    "SOFTWARE_DEV_PANEL_MAP": "software_dev_bout_use_case",
    "SoftwareDevBoutUseCase": "software_dev_bout_use_case",
    "THANATOS_PANEL_MAP": "thanatos_bout_use_case",
    "ThanatosBeatExecutionV1": "thanatos_bout_use_case",
    "ThanatosBoutUseCase": "thanatos_bout_use_case",
    "AdversarySwarmService": "bout_service",
    "execute_7act_adversary_bout": "bout_service",
    "execute_act1_carrier_framing": "act_helpers",
    "execute_act2_obstruction_identification": "act_helpers",
    "execute_act3_candidate_proposal_generation": "act_helpers",
    "execute_act3_epistemic_sieve": "act_helpers",
    "execute_act4_gauge_break": "act_helpers",
    "execute_act4_sandbox_verification": "act_helpers",
    "execute_act5_independent_witness": "act_helpers",
    "execute_act5_terminal_verdict": "act_helpers",
    "execute_act6_intern_report": "act_helpers",
    "execute_act6_residual_ledger": "act_helpers",
    "execute_act7_authorization_gate": "act_helpers",
    "execute_act7_crystallization": "act_helpers",
    "execute_candidate_checks": "act_helpers",
    "persist_bout_run_folder": "persistence",
}


def __getattr__(name: str):
    sub = _SUBMODULE_MAP.get(name)
    if sub is not None:
        import importlib
        mod = importlib.import_module(f".{sub}", __package__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

