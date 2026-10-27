"""Compatibility re-exports for Pharmacy Seeder from adversary.stage.

Imports remain available if the sister package fails, but any use refuses
with the captured dependency error instead of reporting an empty harvest.
AuthorityEffect: None.
"""
from __future__ import annotations


class BridgeUnavailableError(RuntimeError):
    """The optional pharmacy bridge could not be imported."""

try:
    from eis.domain.pharmacy_catalog import (
        PharmacyCatalogRepository,
    )
    from eis.domain.pharmacy_models import (
        Antibody,
        ConstraintType,
        Operatorizability,
        PharmacyStatus,
        RuntimeAction,
        Severity,
    )
    from eis.domain.pharmacy_seeder import PharmacySeeder
    from eis.domain.pharmacy_templates import (
        ANTIBODY_TEMPLATES as DEFAULT_ANTIBODY_TEMPLATES,
    )
except Exception as exc:
    _unavailable_reason = f"pharmacy bridge unavailable: {type(exc).__name__}: {exc}"

    class _UnavailableComponent:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise BridgeUnavailableError(_unavailable_reason)

    class _UnavailableTemplates:
        def __iter__(self):
            raise BridgeUnavailableError(_unavailable_reason)

        def __len__(self) -> int:
            raise BridgeUnavailableError(_unavailable_reason)

    PharmacySeeder = _UnavailableComponent  # type: ignore[misc,assignment]
    Antibody = _UnavailableComponent  # type: ignore[misc,assignment]
    ConstraintType = _UnavailableComponent  # type: ignore[misc,assignment]
    Operatorizability = _UnavailableComponent  # type: ignore[misc,assignment]
    PharmacyStatus = _UnavailableComponent  # type: ignore[misc,assignment]
    RuntimeAction = _UnavailableComponent  # type: ignore[misc,assignment]
    Severity = _UnavailableComponent  # type: ignore[misc,assignment]
    PharmacyCatalogRepository = _UnavailableComponent  # type: ignore[misc,assignment]
    DEFAULT_ANTIBODY_TEMPLATES = _UnavailableTemplates()  # type: ignore[assignment]

__all__ = [
    "BridgeUnavailableError",
    "PharmacySeeder",
    "Antibody",
    "ConstraintType",
    "Operatorizability",
    "PharmacyStatus",
    "RuntimeAction",
    "Severity",
    "PharmacyCatalogRepository",
    "DEFAULT_ANTIBODY_TEMPLATES",
]
