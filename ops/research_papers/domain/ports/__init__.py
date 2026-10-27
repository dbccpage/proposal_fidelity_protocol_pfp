"""Domain Ports (Dependency Inversion Boundaries).

All outer dependencies (Rust crates, Lean 4 provers, filesystem, network)
are declared as pure Domain Protocols.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .lean4_verifier_port import Lean4VerifierPort
    from .literature_catalog_port import LiteratureCatalogPort
    from .receipt_attestation_port import ReceiptAttestationPort
    from .render_export_port import RenderExportPort
    from .rust_solvers_port import SovereignRustSolversPort

__all__ = ['SovereignRustSolversPort', 'Lean4VerifierPort', 'LiteratureCatalogPort', 'ReceiptAttestationPort', 'RenderExportPort']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Lean4VerifierPort': ('.lean4_verifier_port', 'Lean4VerifierPort'),
    'LiteratureCatalogPort': ('.literature_catalog_port', 'LiteratureCatalogPort'),
    'ReceiptAttestationPort': ('.receipt_attestation_port', 'ReceiptAttestationPort'),
    'RenderExportPort': ('.render_export_port', 'RenderExportPort'),
    'SovereignRustSolversPort': ('.rust_solvers_port', 'SovereignRustSolversPort'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
