"""Tests for operand registry loading and candidate filtering (U04).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path


def filter_promoted_operands(
    operands_data: list[dict], target_colour: str | None = None
) -> list[dict]:
    """Filters operands for injection: only promoted, max 3, max 1600 bytes."""
    selected = []
    total_tokens = 0
    for op in operands_data:
        # Strict promotion invariant
        if op.get("status") != "promoted":
            continue
        # Size limit
        text = op.get("prompt_injection_text", "")
        if len(text.encode("utf-8")) > 1600 or op.get("token_estimate", 0) > 400:
            continue
        # Colour matching
        if target_colour is not None and op.get("target_colour") != target_colour:
            continue
        if len(selected) >= 3 or total_tokens + op.get("token_estimate", 0) > 1200:
            break
        selected.append(op)
        total_tokens += op.get("token_estimate", 0)
    return selected


def test_operand_registry_loading_and_promotion_filter():
    repo_root = Path(__file__).resolve().parents[3]
    primary_path = repo_root / ".agents" / "skill_operads" / "operand_registry.json"
    legacy_path = (
        repo_root / "operations" / "skill_operad" / "json" / "operand_registry.json"
    )
    registry_path = primary_path if primary_path.is_file() else legacy_path
    assert registry_path.is_file(), f"registry missing at {registry_path}"

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "core.operad.operand_registry.v1"
    assert data["authority_effect"] == "None"

    operands = data["operands"]
    assert len(operands) >= 2

    selected = filter_promoted_operands(operands, target_colour="Closed")
    assert len(selected) == 2
    assert {op["operand_id"] for op in selected} == {
        "op_exact_cochain_coboundary_repair",
        "op_meron_surgery_sign_inversion",
    }
    assert all(op["status"] == "promoted" for op in selected)
