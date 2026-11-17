"""P1 runner: send each (task, arm) once to OpenAI chat completions. AuthorityEffect: None.

Standard library only. Every call is sent once and never retried.

Ledger: append-only JSONL, one `intent` line before the send and one `result` line after it.
A (task, arm) that already has a result is skipped. One that has an intent but no result was
interrupted, so whether the provider received it is unknown. It is held, never resent.

Costs are integer nano-USD from the reply's own usage, at the prices passed on the command line
(micro-USD per token, an integer or p/q). A hard cap in micro-USD stops the run before a call
whose bound could cross it. The bound is: prompt bytes plus 64 tokens of input, and the arm's
max_completion_tokens of output.

The key is read only from OPENAI_API_KEY in --env-file. It is never printed or written.

    python run.py --env-file ..\\..\\..\\.env --confirm-live 750000
    python run.py --dry-run          # no network; the reply is the expected answer
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import urllib.error
import urllib.request
from fractions import Fraction
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-5-mini-2025-08-07"
MAX_REPLY_BYTES = 1_000_000

Sender = Callable[[dict, str], tuple[int, bytes]]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def price(text: str) -> Fraction:
    if "." in text:
        raise SystemExit(f"PRICE_NOT_FRACTION: {text!r}; write an integer or p/q")
    value = Fraction(text)
    if value < 0:
        raise SystemExit(f"PRICE_NEGATIVE: {text!r}")
    return value


def nano(micro_per_token: Fraction, tokens: int) -> int:
    return math.ceil(micro_per_token * tokens * 1000)


def read_key(env_file: Path) -> str:
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        name, sep, value = line.strip().partition("=")
        if sep and name.strip().removeprefix("export ").strip() == "OPENAI_API_KEY":
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    raise SystemExit(f"KEY_MISSING: OPENAI_API_KEY not set in {env_file}")


def request_body(task: dict, arm: str, model: str, effort: str | None) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": task["system"]},
            {"role": "user", "content": task["arms"][arm]},
        ],
        "max_completion_tokens": task["max_completion_tokens"],
    }
    if effort:
        body["reasoning_effort"] = effort
    return body


def headers(key: str) -> dict[str, str]:
    """Exactly one Content-Type (a duplicate made OpenAI read no body, 2026-11-17)."""
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def http_sender(key: str, timeout: int = 600) -> Sender:
    def send(body: dict, _task_id: str) -> tuple[int, bytes]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(URL, data=data, headers=headers(key), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read(MAX_REPLY_BYTES + 1)
        except urllib.error.HTTPError as err:
            return err.code, err.read(MAX_REPLY_BYTES + 1)

    return send


def dry_sender(tasks: dict[str, dict]) -> Sender:
    def send(body: dict, task_id: str) -> tuple[int, bytes]:
        content = json.dumps(tasks[task_id]["expected"], sort_keys=True)
        reply = {"choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                 "model": body["model"], "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        return 200, json.dumps(reply).encode("utf-8")

    return send


def load_tasks(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def append(path: Path, record: dict) -> None:
    with path.open("ab") as fh:
        fh.write((json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
        fh.flush()


def run(tasks: list[dict], ledger: Path, send: Sender, *, model: str, effort: str | None,
        p_in: Fraction, p_out: Fraction, cap_micro: int, limit: int | None = None,
        tasks_sha256: str = "") -> dict:
    records = load_ledger(ledger)
    done = {(r["task_id"], r["arm"]) for r in records if r["kind"] == "result"}
    intents = {(r["task_id"], r["arm"]) for r in records if r["kind"] == "intent"}
    held = intents - done
    spent = sum(r.get("cost_nano_usd", 0) for r in records if r["kind"] == "result")
    sent = 0
    stop = None
    for task in tasks:
        for arm in sorted(task["arms"]):
            key = (task["task_id"], arm)
            if key in done or key in held:
                continue
            if limit is not None and sent >= limit:
                stop = "LIMIT"
                break
            body = request_body(task, arm, model, effort)
            data = json.dumps(body).encode("utf-8")
            bound = nano(p_in, len(data) + 64) + nano(p_out, task["max_completion_tokens"])
            if spent + bound > cap_micro * 1000:
                stop = "OVER_CAP"
                break
            append(ledger, {"kind": "intent", "task_id": task["task_id"], "arm": arm,
                            "request_sha256": sha(data), "model": model, "effort": effort,
                            "tasks_sha256": tasks_sha256})
            started = time.monotonic()
            try:
                status, raw = send(body, task["task_id"])
                error = None
            except Exception as err:  # transport failure: recorded, never retried
                status, raw, error = 0, b"", type(err).__name__
            wall_ms = int((time.monotonic() - started) * 1000)
            truncated = len(raw) > MAX_REPLY_BYTES
            raw = raw[:MAX_REPLY_BYTES]
            usage = {}
            if status == 200:
                try:
                    usage = json.loads(raw).get("usage") or {}
                except ValueError:
                    usage = {}
            t_in = int(usage.get("prompt_tokens", 0))
            t_out = int(usage.get("completion_tokens", 0))
            # No usage on a failed or unreadable reply: keep the bound as its cost.
            cost = nano(p_in, t_in) + nano(p_out, t_out) if usage else bound
            spent += cost
            append(ledger, {"kind": "result", "task_id": task["task_id"], "arm": arm,
                            "status": status, "error": error, "truncated": truncated,
                            "reply": raw.decode("utf-8", errors="replace"),
                            "reply_sha256": sha(raw), "prompt_tokens": t_in,
                            "completion_tokens": t_out, "cost_nano_usd": cost,
                            "cost_source": "usage" if usage else "bound", "wall_ms": wall_ms})
            done.add(key)
            sent += 1
        if stop:
            break
    return {"sent": sent, "held": sorted("|".join(k) for k in held), "stop": stop,
            "spent_micro_usd": math.ceil(Fraction(spent, 1000))}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tasks", type=Path, default=HERE / "tasks.jsonl")
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--env-file", type=Path)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--effort", default="low")
    ap.add_argument("--price-in", default="1/4", help="micro-USD per input token")
    ap.add_argument("--price-out", default="2", help="micro-USD per output token")
    ap.add_argument("--cap-micro-usd", type=int, default=750_000)
    ap.add_argument("--confirm-live", type=int, help="must equal --cap-micro-usd for a live run")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    tasks = load_tasks(args.tasks)
    tasks_sha = sha(args.tasks.read_bytes())
    if args.dry_run:
        ledger = args.ledger or HERE / "ledger_dry.jsonl"
        send = dry_sender({t["task_id"]: t for t in tasks})
    else:
        if args.confirm_live != args.cap_micro_usd:
            raise SystemExit("CONFIRM_MISSING: pass --confirm-live equal to --cap-micro-usd")
        if not args.env_file:
            raise SystemExit("ENV_FILE_MISSING: pass --env-file")
        ledger = args.ledger or HERE / "ledger_live.jsonl"
        send = http_sender(read_key(args.env_file))
    summary = run(tasks, ledger, send, model=args.model, effort=args.effort or None,
                  p_in=price(args.price_in), p_out=price(args.price_out),
                  cap_micro=args.cap_micro_usd, limit=args.limit, tasks_sha256=tasks_sha)
    summary["ledger"] = str(ledger)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
