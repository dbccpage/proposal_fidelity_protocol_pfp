"""Offline two-pass controller. Scripted replies are not model performance evidence."""

import argparse
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from decimal import Context, localcontext
from pathlib import Path

from . import budget_ledger
from . import numeric_packets as numeric

PROVIDER_FAILURES = (OSError, RuntimeError, TypeError, ValueError, IndexError)


PFP = Path(__file__).resolve().parents[2]
CAP = "0.010"


def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Reply:
    raw: bytes
    simulated_cost_usd: str | None = "0"


@dataclass
class ScriptedProvider:
    replies: tuple
    reservations: tuple = ("0.005", "0.005")
    calls: list = field(default_factory=list, init=False)

    def complete(self, request):
        index = len(self.calls)
        self.calls.append(request)
        response = self.replies[index]
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, Reply) or not isinstance(response.raw, bytes):
            raise TypeError("SCRIPTED_REPLY_TYPE")
        return response


def task_read(raw):
    task = numeric.json_read(raw)
    if not isinstance(task, dict) or set(task) != {
        "source_profile",
        "target_profile",
        "source_wire",
    }:
        raise ValueError("TASK_FIELDS")
    numeric.profile_check(task["target_profile"])
    if not isinstance(task["source_wire"], str):
        raise ValueError("TASK_WIRE_TYPE")
    try:
        node = numeric.parse(task["source_wire"].encode("ascii"), task["source_profile"])
    except UnicodeError as error:
        raise ValueError("TASK_WIRE_ASCII") from error
    return task, node


def money_token(value):
    """Bounded plain decimal tokens keep the reused ledger's arithmetic exact."""
    return (
        isinstance(value, str)
        and re.fullmatch(r"(?:[0-9]{1,6}(?:\.[0-9]{1,9})?|\.[0-9]{1,9})", value) is not None
    )


def execute(task_raw, provider, run_dir):
    # At most two 16-digit monetary tokens are added. Do not inherit a caller's
    # small Decimal precision or permit unbounded exponent/mantissa inputs.
    with localcontext(Context(prec=50)):
        return _execute(task_raw, provider, run_dir)


def _execute(task_raw, provider, run_dir):
    """New output directory only; no implicit resume, retry, network or budget reset."""
    if type(provider) is not ScriptedProvider or provider.calls:
        raise ValueError("FRESH_SCRIPTED_PROVIDER_REQUIRED")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)

    def save(name, raw):
        with (run_dir / name).open("xb") as handle:
            handle.write(raw)

    save("task.bin", task_raw)
    ledger = budget_ledger.BudgetLedger(
        run_dir / "budget.json",
        pilot_cap_usd=CAP,
        campaign_cap_usd=CAP,
        balance_ceiling_usd=CAP,
    )
    receipt = {
        "schema": "sn09-offline-receipt-v1",
        "execution_mode": "offline-scripted",
        "model_calls": 0,
        "cost_usd": "0",
        "live_model_status": "NOT_RUN",
        "status": "REJECTED",
        "error_code": None,
        "task_sha256": sha(task_raw),
        "stages_accepted": [],
        "run_cap_usd": CAP,
        "code_sha256": {
            name: sha(Path(path).read_bytes())
            for name, path in (
                ("run.py", __file__),
                ("numeric_packets.py", numeric.__file__),
                ("budget_ledger.py", budget_ledger.__file__),
            )
        },
    }

    def obtain(stage, request):
        request_raw = encoded(request)
        save(f"{stage}.request.json", request_raw)
        try:
            reservation = provider.reservations[len(provider.calls)]
            if not money_token(reservation):
                raise ValueError("INVALID_RESERVATION_TOKEN")
            # The ledger file is created inside the new run directory and each stage id is
            # reserved once, so reserve() has no prior row to return here.
            ledger.reserve(
                stage,
                reservation,
                request_sha256=sha(request_raw),
                model="offline-scripted",
                pricing_sha256=sha(b"simulated-bound-not-live-pricing"),
            )
            ledger.mark_dispatched(stage)
        except (ValueError, IndexError) as error:
            receipt.update(status="REFUSED", error_code=str(error))
            return None
        try:
            reply = provider.complete(request_raw)
            save(f"{stage}.response.bin", reply.raw)
            save(f"{stage}.billing.json", encoded({"simulated_cost_usd": reply.simulated_cost_usd}))
        except PROVIDER_FAILURES as error:
            # No exception message is retained: a transport could put secrets there.
            code = type(error).__name__
            ledger.unresolved(stage, code)
            receipt.update(status="UNRESOLVED", error_code=code)
            return None
        if not money_token(reply.simulated_cost_usd):
            ledger.unresolved(stage)
            receipt.update(status="UNRESOLVED", error_code="BILLING_UNKNOWN")
            return None
        result = ledger.settle(stage, reply.simulated_cost_usd)
        if result["status"] != "COMPLETE":
            receipt.update(status="UNRESOLVED", error_code=result["error_code"])
            return None
        content = numeric.json_read(reply.raw)
        if content is None:
            raise ValueError("NULL_RESPONSE")
        return content

    try:
        task, expected = task_read(task_raw)
        draft_data = obtain(
            "draft",
            {
                "stage": "draft",
                "task_sha256": sha(task_raw),
                "task": task,
                "instruction": "Return the source expression as a typed tag/children tree. No extra fields.",
            },
        )
        if draft_data is not None:
            draft = numeric.from_data(draft_data)
            if draft != expected:
                raise ValueError("DRAFT_STRUCTURE_MISMATCH")
            receipt["stages_accepted"].append("draft")
            wire_data = obtain(
                "transcode",
                {
                    "stage": "transcode",
                    "task_sha256": sha(task_raw),
                    "target_profile": task["target_profile"],
                    "draft": numeric.to_data(draft),
                    "instruction": "Return only a JSON object with one wire string; preserve this exact tree.",
                },
            )
            if wire_data is not None:
                if (
                    not isinstance(wire_data, dict)
                    or set(wire_data) != {"wire"}
                    or not isinstance(wire_data["wire"], str)
                ):
                    raise ValueError("TRANSCODE_FIELDS")
                wire = wire_data["wire"].encode("utf-8")
                save("wire.bin", wire)
                actual = numeric.parse(wire, task["target_profile"])
                if actual != expected or actual != draft:
                    raise ValueError("WIRE_STRUCTURE_MISMATCH")
                receipt["stages_accepted"].append("transcode")
                receipt.update(status="ACCEPTED", value=str(numeric.value(actual)))
    except ValueError as error:
        receipt.update(status="REJECTED", error_code=str(error))
    receipt["scripted_provider_calls"] = len(provider.calls)
    receipt["simulated_billing"] = ledger.summary()
    receipt["artifact_sha256"] = {
        path.name: sha(path.read_bytes())
        for path in sorted(run_dir.iterdir())
        if path.is_file() and path.suffix != ".lock"
    }
    save("receipt.json", encoded(receipt))
    return receipt


def default_task():
    return encoded(
        {
            "source_profile": numeric.LEGACY,
            "target_profile": numeric.HAG,
            "source_wire": "<<rat><pos><51><2>>",
        }
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path)
    args = parser.parse_args(argv)
    raw = args.task.read_bytes() if args.task else default_task()
    # These locally generated responses exercise the controller, not an LLM.
    try:
        task, tree = task_read(raw)
        replies = (
            Reply(encoded(numeric.to_data(tree))),
            Reply(
                encoded(
                    {
                        "wire": numeric.serialize(tree, task["target_profile"]).decode("ascii"),
                    }
                )
            ),
        )
    except ValueError:
        replies = ()
    output = PFP / "pilots/pilot_output/pilot_0000033" / uuid.uuid4().hex
    receipt = execute(raw, ScriptedProvider(replies), output)
    print(json.dumps({"output": str(output.resolve()), **receipt}, indent=2))
    return 0 if receipt["status"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
