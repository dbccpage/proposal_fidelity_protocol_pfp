"""The 52-Point Republication Gate (27 Static Predicates + 25 Dynamic Obligations).

AuthorityEffect: None.

Implements the complete verification gate matching the canonical Zenodo republication
gate specification, checklist.py, and core-paper-review-swarm standards.

Decomposed into cohesive submodules under use_cases.gate_52:
- models: GateItemResult, Gate52Report
- utils: snapshot, identity, checksum, safe_name, resolve_paper_paths
- evaluator: evaluate_domain_model_52_gate (27 static + 25 dynamic predicates)
- package_auditor: audit_paper_package (Stage Ω disk bytes verification)
"""

from __future__ import annotations

from .gate_52 import (
    CACHES,
    MAX_FILE_BYTES,
    MAX_PAYLOAD_BYTES,
    SOURCE_REF,
    Gate52Report,
    GateItemResult,
    Verification52Gate,
    _checksums,
    _digest,
    _identity,
    _multiline,
    _normalize,
    _regular,
    _safe_name,
    _snapshot,
    _stored_output,
    audit_paper_package,
    evaluate_domain_model_52_gate,
    resolve_paper_paths,
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
