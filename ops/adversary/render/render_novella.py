"""Evidence-led seven-act narrative rendering for Adversary.

Authored stage framing is not agent dialogue or execution evidence.
AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import json
from typing import Any

from ..infrastructure.native import value as native_value


def render_7act_novella(
    run_key: str,
    objective: str,
    *,
    prompt_metrics: dict[str, Any] | None = None,
    prompt_sbe: dict[str, Any] | None = None,
    antibodies_loaded: list[dict[str, Any]] | None = None,
    candidates_data: list[dict[str, Any]] | None = None,
    compilation_gate: list[dict[str, Any]] | None = None,
    critiques_data: list[dict[str, Any]] | None = None,
    adversary_sieve_text: str = "",
    sieve_sbe: dict[str, Any] | None = None,
    primal_dual_checks: list[dict[str, str]] | None = None,
    primal_dual_overall: str = "NOT_INDEPENDENTLY_VERIFIED",
    master_assessment: dict[str, Any] | None = None,
    verdict: str = "COMPOSTED",
    intern_checks: list[str] | None = None,
    mined_antibodies: list[dict[str, Any]] | None = None,
    backdoor_auditor_guidance: dict[str, Any] | None = None,
    consecration: str = "PROPOSED",
    now_utc: str = "",
) -> str:
    """Marshal supplied records without inventing execution evidence."""
    record = dict(locals())
    timestamp = now_utc or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    return native_value(
        "render", record_json=json.dumps(record, ensure_ascii=False), fallback_timestamp=timestamp
    )


__all__ = ["render_7act_novella"]
