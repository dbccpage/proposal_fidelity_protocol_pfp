"""Console formatter for python_development_office scan results."""

from __future__ import annotations

import sys
from typing import TextIO

from omega_engine_operads.domain.python_development_office.scan_result import (
    ScanResult,
)


def format_console_output(result: ScanResult, stream: TextIO = sys.stdout) -> None:
    """Render human-readable findings and summary statistics to console."""
    stream.write("=== Python Development Office: Architecture & Anti-Pattern Audit ===\n")
    stream.write(
        f"Files Scanned: {result.files_scanned} | Modules Indexed: {result.modules_indexed} | Findings: {result.total_findings}\n\n"
    )

    if not result.findings:
        stream.write(
            "No findings detected. Codebase satisfies active architecture and pitfall rules.\n"
        )
        return

    for f in result.findings:
        sev_tag = f"[{f.severity.upper()}]"
        cat_tag = f"[{f.category.upper()}]"
        code_tag = f"[{f.rule_id:03d} {f.rule_code}]"
        stream.write(f"{sev_tag} {cat_tag} {code_tag} {f.path}:{f.line}:{f.column}\n")
        stream.write(f"  Violation:   {f.message}\n")
        stream.write(f"  Remediation: {f.remediation}\n\n")
