"""JSON Repository for Operad Signatures, Compositions, Slices, and Traces.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from domain.colours import ColourSignature
    from domain.evidence import DiagnosticObservation
    from omega_engine_operads.domain.operad.operad import ColouredOperad
    from omega_engine_operads.domain.operad.operation import OperationId, OperationSignature
except (ImportError, ValueError):
    from ...domain.colours import ColourSignature
    from ...domain.evidence import DiagnosticObservation
    from omega_engine_operads.domain.operad.operad import ColouredOperad
    from omega_engine_operads.domain.operad.operation import OperationId, OperationSignature


class JsonOperadRepository:
    """Repository loading and persisting operad definitions from JSON files."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.signature_file = (
            root_dir / "json" / "operad_signature.json"
            if (root_dir / "json" / "operad_signature.json").is_file()
            else root_dir / "operad_signature.json"
        )
        self.composition_file = (
            root_dir / "json" / "composition_matrix.json"
            if (root_dir / "json" / "composition_matrix.json").is_file()
            else root_dir / "composition_matrix.json"
        )
        self.slices_file = (
            root_dir / "json" / "agent_capability_slices.json"
            if (root_dir / "json" / "agent_capability_slices.json").is_file()
            else root_dir / "agent_capability_slices.json"
        )
        self.trace_file = (
            root_dir / "json" / "evidence_trace.json"
            if (root_dir / "json" / "evidence_trace.json").is_file()
            else root_dir / "evidence_trace.json"
        )

    def load_operad(self) -> ColouredOperad:
        operad = ColouredOperad()

        if self.signature_file.exists():
            data = json.loads(self.signature_file.read_text(encoding="utf-8"))
            entries = data.get("operations", []) if isinstance(data, dict) else data
            for entry in entries:
                op = OperationSignature.create(
                    op_id=entry["skill_id"],
                    source=entry["source_colours"],
                    target=entry["target_colour"],
                    arity=entry.get("arity"),
                    equivariant=entry.get("equivariant", False),
                    residual_effect=entry.get("residual_effect", "unknown"),
                )
                operad.add_operation(op)

        return operad

    def load_composition_matrix(self) -> Dict[str, Any]:
        if not self.composition_file.exists():
            return {}
        return json.loads(self.composition_file.read_text(encoding="utf-8"))

    def load_agent_capability_slices(self) -> Dict[str, Any]:
        if not self.slices_file.exists():
            return {}
        return json.loads(self.slices_file.read_text(encoding="utf-8"))

    def load_evidence_traces(self) -> List[DiagnosticObservation]:
        if not self.trace_file.exists():
            return []
        try:
            records = json.loads(self.trace_file.read_text(encoding="utf-8"))
            obs = []
            for r in records:
                obs.append(
                    DiagnosticObservation(
                        skill_id=r.get("skill_id", "unknown"),
                        run_id=r.get("run_id", "unknown"),
                        phi_before=float(r.get("phi_before", 0.0)),
                        phi_after=float(r.get("phi_after", 0.0)),
                        delta_phi=float(r.get("delta_phi", 0.0)),
                        authority_effect="None",
                    )
                )
            return obs
        except Exception:
            return []

    def save_operad_signatures(self, operad: ColouredOperad) -> None:
        signatures = [op.to_dict() for op in operad.operations.values() if not op.is_unit]
        self.signature_file.write_text(json.dumps(signatures, indent=2), encoding="utf-8")
