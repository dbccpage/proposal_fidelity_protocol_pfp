"""Carry finished workflow runs to the failure ledger, and its rules back into a task.

This module moves files to the Rust host ``pfp_operad`` and writes down what it
answers. It reads no answer, compares nothing and counts nothing: the host judges
every stored turn, keeps the ledger, writes the seed a run loads and scores every
trial. AuthorityEffect: None.

    python -m pfp.workflows.failure_ledger record LEDGER RUN [RUN ...]
    python -m pfp.workflows.failure_ledger load LEDGER TASK --output NEW_TASK [--on-trial RULE]
    python -m pfp.workflows.failure_ledger check LEDGER TASK [--receipt RECEIPT]
    python -m pfp.workflows.failure_ledger trial LEDGER RULE --pair BASELINE TREATED RECEIPT

A run is a WF1-WF5 run folder. A turn is a folder that holds ``task.json`` and
``receipt.json``: the run folder itself (WF1, WF2) or one of its children (the
``mining``, ``solver`` and ``agent-N`` folders of WF3-WF5).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure import operad_host
from pfp.infrastructure.adapters.pfp_campaign import write_new

TASK = "task.json"
RECEIPT = "receipt.json"
LOAD_RECEIPT_SUFFIX = ".rules.json"
HELD = "PASS"


def read(path: Path) -> dict:
    return strict_json(path.read_text(encoding="utf-8"))


def stored_turn(folder: Path) -> dict:
    """The two files of a stored turn, as they are."""
    return {"task": read(folder / TASK), "receipt": read(folder / RECEIPT)}


def turns(run: Path) -> list[tuple[str, Path]]:
    """Every turn folder of a run, each with the name the ledger will know it by."""
    name = run.resolve().name
    folders = [(name, run)]
    folders += [(f"{name}/{child.name}", child) for child in sorted(run.iterdir()) if child.is_dir()]
    return [
        (label, folder)
        for label, folder in folders
        if (folder / TASK).is_file() and (folder / RECEIPT).is_file()
    ]


def ledger_call(action: str, ledger: Path, request: dict) -> dict:
    """One host command on a ledger file; the outcome is the host's."""
    return operad_host.call(("ledger", action, str(ledger)), request)


def load_receipt(task: Path) -> Path:
    """Where the host's account of a loaded task is kept: beside the task."""
    return task.with_suffix(LOAD_RECEIPT_SUFFIX)


def record(ledger: Path, runs: list[Path]) -> list[dict]:
    """Hand every stored turn to the host; append the failure records it writes."""
    rows = []
    for run in runs:
        for label, folder in turns(run):
            request = {"run": label, "turn": stored_turn(folder)}
            row = {"turn": label, "witness": operad_host.outcome("witness-turn", request)}
            if row["witness"]["status"] == HELD:
                row["entry"] = ledger_call("append", ledger, row["witness"]["result"]["record"])
            rows.append(row)
    return rows


def load(ledger: Path, task: Path, output: Path, on_trial: str | None = None) -> dict:
    """Write the task with the seed the host loads, and the host's account of it beside it."""
    spec = read(task)
    outcome = ledger_call("load", ledger, {"seed_prompt": spec["seed_prompt"], "on_trial": on_trial})
    if outcome["status"] == HELD:
        account = dict(outcome["result"])
        write_new(output, {**spec, "seed_prompt": account.pop("seed_prompt")})
        write_new(load_receipt(output), {"base_seed_prompt": spec["seed_prompt"], **account})
    return outcome


def check(ledger: Path, task: Path, receipt: Path | None = None) -> dict:
    """Ask the host whether a task's seed is what the ledger loaded."""
    account = read(receipt or load_receipt(task))
    request = {
        "base_seed_prompt": account["base_seed_prompt"],
        "seed_prompt": read(task)["seed_prompt"],
        "ledger_head": account["ledger_head"],
        "on_trial": account["on_trial"],
    }
    return ledger_call("loaded", ledger, request)


def trial(ledger: Path, rule: str, pairs: list[tuple[Path, Path, Path]]) -> dict:
    """Hand paired turns to the host; append the trial record it writes."""
    cases = []
    for baseline, treated, receipt in pairs:
        account = read(receipt)
        cases.append(
            {
                "baseline": stored_turn(baseline),
                "treated": stored_turn(treated),
                "base_seed_prompt": account["base_seed_prompt"],
                "ledger_head": account["ledger_head"],
            }
        )
    row = {"trial": ledger_call("trial", ledger, {"candidate": rule, "cases": cases})}
    if row["trial"]["status"] == HELD:
        row["entry"] = ledger_call("append", ledger, row["trial"]["result"]["record"])
    return row


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Failure ledger for WF1-WF5 runs. Every check is made by pfp_operad."
    )
    commands = root.add_subparsers(dest="command", required=True)
    entry = commands.add_parser("record", help="record the failures of finished runs")
    entry.add_argument("ledger", type=Path)
    entry.add_argument("runs", type=Path, nargs="+")
    entry = commands.add_parser("load", help="write a task whose seed carries the ledger's rules")
    entry.add_argument("ledger", type=Path)
    entry.add_argument("task", type=Path)
    entry.add_argument("--output", type=Path, required=True)
    entry.add_argument("--on-trial", help="also load this proposed rule, for the treated arm of its trial")
    entry = commands.add_parser("check", help="check a task's seed against the ledger")
    entry.add_argument("ledger", type=Path)
    entry.add_argument("task", type=Path)
    entry.add_argument("--receipt", type=Path, help="the load receipt, when it is not beside the task")
    entry = commands.add_parser("trial", help="score a rule from paired runs and record the trial")
    entry.add_argument("ledger", type=Path)
    entry.add_argument("rule")
    entry.add_argument(
        "--pair", type=Path, nargs=3, action="append", required=True,
        metavar=("BASELINE", "TREATED", "RECEIPT"),
        help="a baseline turn folder, a treated turn folder and the treated task's load receipt",
    )
    return root


def answer(args: argparse.Namespace) -> tuple[object, list[dict]]:
    """What to print, and the host outcomes that decide the exit code."""
    if args.command == "record":
        rows = record(args.ledger, args.runs)
        return rows, [row["entry"] for row in rows if "entry" in row]
    if args.command == "load":
        outcome = load(args.ledger, args.task, args.output, args.on_trial)
        return outcome, [outcome]
    if args.command == "check":
        outcome = check(args.ledger, args.task, args.receipt)
        return outcome, [outcome]
    row = trial(args.ledger, args.rule, [tuple(pair) for pair in args.pair])
    return row, list(row.values())


def main(argv: list[str] | None = None) -> int:
    """Exit 0 when the host passed every decisive outcome, 1 when it did not, 2 when it did not run."""
    args = parser().parse_args(argv)
    try:
        shown, decisive = answer(args)
    except operad_host.OperadHostError as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(shown, ensure_ascii=True, sort_keys=True))
    return int(any(outcome["status"] != HELD for outcome in decisive))


if __name__ == "__main__":
    raise SystemExit(main())
