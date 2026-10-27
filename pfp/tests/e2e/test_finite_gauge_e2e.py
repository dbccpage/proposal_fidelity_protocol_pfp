"""CLI end-to-end contract for the finite-gauge workbench."""

import json

from pfp.entrypoints.cli.symbol_game import main


def test_search_gauge_cli_emits_terminal_receipt(capsys) -> None:
    exit_code = main(
        [
            "search-gauge",
            "--fixture",
            "gauge_even_triangle",
            "--node-budget",
            "8",
            "--pace-ms",
            "0",
        ]
    )

    rows = [json.loads(row) for row in capsys.readouterr().out.splitlines()]
    assert exit_code == 0
    assert rows[-1]["type"] == "run_finished"
    assert rows[-1]["data"]["status"] == "GAUGE_VERIFIED"
