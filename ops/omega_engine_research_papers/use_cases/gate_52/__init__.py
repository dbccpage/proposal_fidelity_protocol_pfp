"""52-Point Republication Gate Subpackage.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ...domain.coda.dual_witness import DualWitnessCertificate
from ...domain.coda.halt_guards import HaltGuardResult
from ...domain.ddc.trace import DDCTrace
from ...domain.models.claim_ledger import ClaimLedger
from ...domain.models.paper_spec import PaperSpecification
from ...domain.models.republication_checklist import RepublicationGateReceipt
from .evaluator import evaluate_domain_model_52_gate
from .models import Gate52Report, GateItemResult
from .package_auditor import audit_paper_package
from .utils import (
    CACHES,
    MAX_FILE_BYTES,
    MAX_PAYLOAD_BYTES,
    SOURCE_REF,
    _checksums,
    _digest,
    _identity,
    _multiline,
    _normalize,
    _regular,
    _safe_name,
    _snapshot,
    _stored_output,
    resolve_paper_paths,
)


class Verification52Gate:
    """Evaluates the 52-point republication gate."""

    @classmethod
    def evaluate(
        cls,
        paper: PaperSpecification,
        claim_ledger: Optional[ClaimLedger] = None,
        ddc_trace: Optional[DDCTrace] = None,
        dual_witness: Optional[DualWitnessCertificate] = None,
        halt_guards: Optional[HaltGuardResult] = None,
        markdown_content: str = "",
    ) -> Gate52Report:
        """Domain model evaluation preserving backwards compatibility."""
        return evaluate_domain_model_52_gate(
            paper=paper,
            claim_ledger=claim_ledger,
            ddc_trace=ddc_trace,
            dual_witness=dual_witness,
            halt_guards=halt_guards,
            markdown_content=markdown_content,
        )

    @classmethod
    def audit_paper_package(
        cls,
        paper_dir: Path | str,
        monograph_path: Optional[Path | str] = None,
        evidence_path: Optional[Path | str] = None,
    ) -> RepublicationGateReceipt:
        """Execute Stage Ω Canonical Severe Zenodo Republication Gate on disk bytes."""
        return audit_paper_package(
            paper_dir=paper_dir,
            monograph_path=monograph_path,
            evidence_path=evidence_path,
        )

    @classmethod
    def verify_manifest_with_sovereign_gate(
        cls,
        package_root: Path | str,
        *,
        manifest_path: Optional[Path | str] = None,
        require_crlf_normalized: bool = False,
        zenodo_metadata_path: Optional[Path | str] = None,
        lean_axiom_report_path: Optional[Path | str] = None,
    ) -> Dict[str, Any]:
        """Delegate custody manifest verification, CRLF normalization, Zenodo validation,
        and Lean 4 axiom audit to sovereign CLI binary omega_policy_manifest_gate.
        """
        from ...infrastructure.rust_bridge.crate_client import SovereignRustClient

        client = SovereignRustClient()
        return client.verify_custody_manifest(
            root_dir=package_root,
            manifest_path=manifest_path,
            require_crlf_normalized=require_crlf_normalized,
            zenodo_metadata_path=zenodo_metadata_path,
            lean_axiom_report_path=lean_axiom_report_path,
        )


__all__ = [
    "CACHES",
    "MAX_FILE_BYTES",
    "MAX_PAYLOAD_BYTES",
    "SOURCE_REF",
    "GateItemResult",
    "Gate52Report",
    "Verification52Gate",
    "evaluate_domain_model_52_gate",
    "audit_paper_package",
    "resolve_paper_paths",
    "_digest",
    "_safe_name",
    "_regular",
    "_snapshot",
    "_identity",
    "_checksums",
    "_normalize",
    "_multiline",
    "_stored_output",
]
