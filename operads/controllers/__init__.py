"""Controllers & API Facades for OEWAS V3."""

from .python_facade import OeopApiV3
from .wire_dtos import (
    CompileCatalogRequest,
    CompileLicensedTermRequest,
    CompileProjectionRequest,
    ValidateWorkflowsRequest,
    VerifyCatalogRequest,
    WorkflowEdgeWire,
    WorkflowNodeWire,
)

__all__ = [
    "CompileCatalogRequest",
    "CompileLicensedTermRequest",
    "CompileProjectionRequest",
    "OeopApiV3",
    "ValidateWorkflowsRequest",
    "VerifyCatalogRequest",
    "WorkflowEdgeWire",
    "WorkflowNodeWire",
    "create_oeop_router",
]


def __getattr__(name: str):
    """Load the optional FastAPI adapter only when explicitly requested."""
    if name == "create_oeop_router":
        from .router import create_oeop_router

        return create_oeop_router
    raise AttributeError(name)
