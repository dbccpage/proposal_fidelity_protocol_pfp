"""Configuration, layer mapping, and suppression management infrastructure for python_development_office."""

from __future__ import annotations

import json
import re
from pathlib import Path

from operads.domain.python_development_office.architecture_config import (
    ArchitectureConfig,
    DependencyException,
)

_NOQA_RE = re.compile(r"#\s*noqa(?::\s*([^#\n\r-]+))?", re.IGNORECASE)

_RULE_CODE_ALIASES: dict[str, str] = {
    "BLE001": "BROAD_EXCEPTION_CATCH",
    "E711": "NONE_COMPARISON",
    "E712": "EXPLICIT_BOOLEAN_COMPARISON",
    "E721": "TYPE_EQUALITY_CHECK",
}


def load_config(config_path: Path | str | None = None) -> ArchitectureConfig:
    """Load configuration from file or return standard Clean Architecture defaults."""
    if config_path is None:
        return ArchitectureConfig()

    path = Path(config_path)
    if not path.is_file():
        return ArchitectureConfig()

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        defaults = ArchitectureConfig()
        raw_exceptions = data.get("dependency_exceptions")
        dependency_exceptions = (
            defaults.dependency_exceptions
            if raw_exceptions is None
            else tuple(DependencyException(**exception) for exception in raw_exceptions)
        )
        return ArchitectureConfig(
            source_roots=tuple(data.get("source_roots", defaults.source_roots)),
            layers=data.get("layers", defaults.layers),
            allowed_dependencies=data.get("allowed_dependencies", defaults.allowed_dependencies),
            dependency_exceptions=dependency_exceptions,
            forbidden_frameworks_in_domain=tuple(
                data.get(
                    "forbidden_frameworks_in_domain",
                    defaults.forbidden_frameworks_in_domain,
                )
            ),
            test_file_patterns=tuple(data.get("test_file_patterns", defaults.test_file_patterns)),
            max_controller_loc=int(data.get("max_controller_loc", 400)),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid architecture config {path}: {exc}") from exc


def parse_suppressions(source_lines: list[str]) -> dict[int, set[str]]:
    """Map 1-indexed line numbers to suppressed rule codes.

    `# noqa` suppresses all rules on that line.
    `# noqa: RULE_A, RULE_B` suppresses specified rule codes on that line.
    """
    suppressions: dict[int, set[str]] = {}
    for idx, line in enumerate(source_lines, start=1):
        match = _NOQA_RE.search(line)
        if match:
            codes_str = match.group(1)
            if codes_str:
                rule_set: set[str] = set()
                for c in codes_str.split(","):
                    cleaned = c.strip().upper()
                    if cleaned:
                        rule_set.add(cleaned)
                        if cleaned in _RULE_CODE_ALIASES:
                            rule_set.add(_RULE_CODE_ALIASES[cleaned])
                suppressions[idx] = rule_set if rule_set else {"*"}
            else:
                suppressions[idx] = {"*"}
    return suppressions


def is_suppressed(line_suppressions: dict[int, set[str]], line: int, rule_code: str) -> bool:
    """Check if rule is suppressed on the given line."""
    if line not in line_suppressions:
        return False
    allowed = line_suppressions[line]
    return "*" in allowed or rule_code.upper() in allowed
