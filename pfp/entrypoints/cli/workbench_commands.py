"""CLI entrypoints for the finite live Symbol Game workbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.adapters.finite_gauge.input_yaml import (
    parse_input_yaml,
)
from pfp.infrastructure.composition.finite_gauge import build_run
from pfp.use_cases.finite_gauge_workbench import (
    fixtures,
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def cmd_search_gauge(args: argparse.Namespace) -> int:
    if args.list_fixtures:
        sys.stdout.write(_json({"fixtures": fixtures()}) + "\n")
        return 0

    input_text = None
    if args.input_file is not None:
        if args.fixture is not None or args.node_budget is not None or args.pace_ms is not None:
            raise ValueError("--input-file cannot be combined with fixture, budget, or pace flags")
        input_text = args.input_file.read_text(encoding="utf-8")
        config = parse_input_yaml(input_text)
    else:
        config = RunConfig(args.fixture or "gauge_even_triangle",
                           args.node_budget if args.node_budget is not None else 8,
                           args.pace_ms if args.pace_ms is not None else 0)
    run = build_run(
        config,
        event_sink=lambda event: (sys.stdout.write(_json(event) + "\n"), sys.stdout.flush()),
        input_text=input_text,
    )
    outcome = run.execute()
    snapshot = outcome.unwrap() if outcome.is_ok else run.snapshot()
    if args.output_dir is not None:
        output_dir: Path = args.output_dir
        if output_dir.exists() and any(output_dir.iterdir()):
            raise ValueError("output directory must be empty or absent")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "events.jsonl").write_text(
            "".join(_json(event) + "\n" for event in snapshot["events"]), encoding="utf-8"
        )
        (output_dir / "run.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0 if snapshot["status"] != "FAILED" else 2


def cmd_serve_workbench(args: argparse.Namespace) -> int:
    try:
        import uvicorn

        from pfp.entrypoints.web.workbench import app
    except ModuleNotFoundError as exc:
        raise ValueError("FastAPI workbench requires: pip install -e '.[web]'") from exc
    uvicorn.run(app, host="127.0.0.1", port=args.port)
    return 0
