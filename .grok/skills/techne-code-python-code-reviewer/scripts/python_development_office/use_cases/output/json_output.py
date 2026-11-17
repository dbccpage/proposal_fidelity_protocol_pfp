"""JSON serializer for python_development_office scan results."""

from __future__ import annotations

import json
from dataclasses import asdict

from python_development_office.domain.scan_result import (
    ScanResult,
)


def format_json_output(result: ScanResult) -> str:
    """Serialize ScanResult to formatted JSON string."""
    data = {
        "schema": result.schema,
        "files_scanned": result.files_scanned,
        "modules_indexed": result.modules_indexed,
        "total_findings": result.total_findings,
        "findings": [asdict(f) for f in result.findings],
        "authority_effect": result.authority_effect,
    }
    return json.dumps(data, indent=2, sort_keys=True)
