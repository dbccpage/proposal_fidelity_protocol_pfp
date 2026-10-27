"""End-to-end CLI check using the real Ruff adapter."""

from __future__ import annotations

import json
from pathlib import Path

from operads.frontend.cli.python_dev_cli import main


def test_quality_inventory_cli_emits_bound_json_receipt(tmp_path: Path, capsys) -> None:
    source = tmp_path / "tests" / "unit" / "test_module.py"
    source.parent.mkdir(parents=True)
    source.write_text("def value():\n    return 1\n", encoding="utf-8")

    exit_code = main(
        [
            str(tmp_path),
            "--quality-inventory",
            "--project-root",
            str(tmp_path),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["schema"] == "core.python_quality_inventory.v1"
    assert payload["status"] == "BLOCKED"
    assert payload["files"][0]["path"] == "tests/unit/test_module.py"
    statuses = {tier["tier"]: tier["status"] for tier in payload["test_tiers"]}
    assert statuses["unit"] == "MISSING_RECEIPT"
    assert "PRESENT_NOT_EXECUTED" not in statuses.values()
