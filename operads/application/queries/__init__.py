"""Query Handlers for OEWAS V3."""

from .get_catalog import GetCatalogHandler
from .validate_workflows import ValidateWorkflowsHandler

__all__ = [
    "GetCatalogHandler",
    "ValidateWorkflowsHandler",
]
