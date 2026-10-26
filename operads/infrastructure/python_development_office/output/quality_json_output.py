"""JSON rendering for Python quality inventory receipts and typed refusals."""

from __future__ import annotations

import json
from dataclasses import asdict

from omega_engine_operads.domain.python_development_office.quality_errors import (
    PythonQualityGateError,
)
from omega_engine_operads.domain.python_development_office.quality_inventory import (
    QualityInventoryReceipt,
)


def format_quality_receipt(receipt: QualityInventoryReceipt) -> str:
    """Serialize a receipt without promoting static evidence."""

    return json.dumps(asdict(receipt), indent=2, sort_keys=True)


def format_quality_refusal(error: PythonQualityGateError) -> str:
    """Serialize a typed fail-closed execution refusal."""

    return json.dumps(
        {
            "schema": "omega.python_quality_inventory.v1",
            "status": "REFUSED",
            "error": {"code": error.code, "detail": error.detail},
            "authority_effect": "None",
        },
        indent=2,
        sort_keys=True,
    )
