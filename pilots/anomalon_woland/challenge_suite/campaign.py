"""M5 matched campaign: baseline vs typed_witness PFP prompts over the challenge suite.

Each run is the existing accounted ``live_run`` with its own estimated budget and
ledger. This driver only sequences runs, keeps a campaign-wide spend total, and
collates receipts. Spend is integer micro-USD read back from each run's own
summary; a run whose cost is unknown is charged its full estimated cap.

AuthorityEffect: None. Results are candidate evidence, not ledger upgrades.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from omega_engine_pfp.infrastructure.challenge_live import choose_case, live_run, replay_live

PLAN = Path(__file__).with_name("m5_campaign.json")
SCHEMA = "pfp.m5-campaign.v1"
ACCEPTED = "HOST_ACCEPTED"


def load_plan(path=PLAN):
    plan = json.loads(Path(path).read_bytes())
    if plan.get("schema") != "pfp.m5-campaign-plan.v1":
        raise ValueError("CAMPAIGN_PLAN_SCHEMA")
    for key in ("max_total_microusd", "per_run_estimated_microusd", "max_output_tokens",
                "max_provider_calls", "stop_after_consecutive_undispatched_runs", "ordinal"):
        if type(plan[key]) is not int or plan[key] < 0:
            raise ValueError("CAMPAIGN_PLAN_INTEGER:" + key)
    # Two runs of headroom: an estimated gateway can settle above its estimate.
    if 2 * plan["per_run_estimated_microusd"] > plan["max_total_microusd"]:
        raise ValueError("CAMPAIGN_CAP_BELOW_ONE_RUN")
    structured = plan.setdefault("structured_output_models", [])
    if type(structured) is not list or not set(structured) <= set(plan["models"]):
        raise ValueError("CAMPAIGN_STRUCTURED_OUTPUT_MODELS")
    return plan


def only_models(plan, models):
    """The same plan restricted to some of its models, e.g. to rerun one model."""
    if not models:
        return plan
    if not set(models) <= set(plan["models"]):
        raise ValueError("CAMPAIGN_UNKNOWN_MODEL")
    return dict(plan, models=[m for m in plan["models"] if m in models])


def runs_of(plan):
    return [dict(model=m, arm=a, challenge=c) for m in plan["models"]
            for c in plan["challenges"] for a in plan["arms"]]


def run_dir(output, run):
    return Path(output) / "runs" / run["model"].replace("/", "__") / f"{run['challenge']}_{run['arm']}"


def charge(directory, plan):
    """Integer micro-USD charged to the campaign for one run directory."""
    if not directory.exists():
        return 0
    summary = directory / "summary.json"
    if not summary.exists():
        return plan["per_run_estimated_microusd"]
    data = json.loads(summary.read_bytes())
    if data["cost_microusd"] is not None:
        return data["cost_microusd"]
    return max(data["known_cost_subtotal_microusd"], plan["per_run_estimated_microusd"])


def spent(output, plan):
    return sum(charge(run_dir(output, run), plan) for run in runs_of(plan))


def _append(path, row):
    with path.open("ab") as stream:
        stream.write((json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii"))
        stream.flush()
        os.fsync(stream.fileno())


def openrouter_gateway(env_file):
    def open_gateway(model, directory, row, arm, plan):
        from omega_engine_pfp.infrastructure.estimated_gateway import (
            create_accounted_openrouter_gateway,
        )

        accounting = directory.with_name(directory.name + ".budget.sqlite3")
        if accounting.exists():
            raise ValueError("ACCOUNTING_ALREADY_EXISTS")
        objective = json.dumps(dict(row=row, arm=arm), sort_keys=True).encode()
        return create_accounted_openrouter_gateway(
            model, plan["max_output_tokens"], env_file=env_file,
            max_estimated_cost_microusd=plan["per_run_estimated_microusd"],
            max_calls=plan["max_provider_calls"], accounting_path=accounting,
            run_id="m5-" + uuid4().hex, objective_sha256=sha256(objective).hexdigest())
    return open_gateway


def run_campaign(output, plan, open_gateway, *, clock=time.monotonic_ns):
    """Run every planned (model, challenge, arm) once; resumable, never re-dispatches."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / "campaign_ledger.jsonl"
    total, streak = spent(output, plan), 0
    for run in runs_of(plan):
        directory = run_dir(output, run)
        if directory.exists():
            continue
        if total + 2 * plan["per_run_estimated_microusd"] > plan["max_total_microusd"]:
            _append(ledger, dict(run, event="STOPPED", reason="CAMPAIGN_CAP", spent_microusd=total))
            return dict(status="STOPPED_AT_CAP", spent_microusd=total)
        directory.parent.mkdir(parents=True, exist_ok=True)
        started, status, reason, failure, calls = clock(), None, None, None, 0
        try:
            row = choose_case(run["challenge"], plan["split"], plan["ordinal"])
            gateway = open_gateway(run["model"], directory, row, run["arm"], plan)
            records = live_run(row, directory, run["model"], run["arm"], gateway=gateway,
                max_output_tokens=plan["max_output_tokens"],
                max_provider_calls=plan["max_provider_calls"],
                structured_output=run["model"] in plan.get("structured_output_models", []))
            status = records[-1]["result"]["status"] if records else "NO_STAGE_RECORDED"
            if records:
                failure = records[-1]["result"].get("failure_class")
                reason = records[-1]["result"].get("reason")
            calls = sum(bool(r["attempted"]) for r in records)
        except Exception as exc:  # noqa: BLE001 - recorded, charged conservatively, campaign continues
            status, reason = "REFUSED", f"{type(exc).__name__}: {exc}"
        cost = charge(directory, plan)
        total += cost
        _append(ledger, dict(run, event="RUN", status=status, failure_class=failure, reason=reason,
            provider_calls=calls, charged_microusd=cost,
            spent_microusd=total, elapsed_ms=(clock() - started) // 1_000_000))
        # Only a run that reached no provider counts: a graded reply, however bad, is a result.
        streak = streak + 1 if calls == 0 else 0
        if streak >= plan["stop_after_consecutive_undispatched_runs"]:
            _append(ledger, dict(run, event="STOPPED", reason="UNDISPATCHED_RUNS", spent_microusd=total))
            return dict(status="STOPPED_UNDISPATCHED", spent_microusd=total)
    return dict(status="COMPLETE", spent_microusd=total)


def _stages(directory):
    return [json.loads((d / "receipt.json").read_bytes()) for d in sorted(directory.glob("stage_*"))
            if (d / "receipt.json").exists()]


def _tokens(receipts, key):
    return sum(r["usage"][key] for r in receipts if type(r.get("usage", {}).get(key)) is int)


def collate(output, plan, *, replay=replay_live):
    """Per-run rows, per (model, arm) totals and the matched comparison; replays every run."""
    output = Path(output)
    elapsed = {}
    ledger = output / "campaign_ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_bytes().splitlines():
            event = json.loads(line)
            if event["event"] == "RUN":
                elapsed[(event["model"], event["challenge"], event["arm"])] = event["elapsed_ms"]
    rows = []
    for run in runs_of(plan):
        directory = run_dir(output, run)
        row = dict(run, present=directory.exists(), status=None, failure_class=None,
            first_stage_status=None,
            stages=0, provider_calls=0, cost_microusd=None, known_cost_microusd=0,
            prompt_tokens=0, completion_tokens=0, charged_microusd=charge(directory, plan),
            elapsed_ms=elapsed.get((run["model"], run["challenge"], run["arm"])), replay=None)
        if (directory / "summary.json").exists():
            summary = json.loads((directory / "summary.json").read_bytes())
            receipts = _stages(directory)
            row.update(status=summary["status"], stages=summary["stages"],
                failure_class=receipts[-1]["result"].get("failure_class") if receipts else None,
                provider_calls=summary["provider_calls"], cost_microusd=summary["cost_microusd"],
                known_cost_microusd=summary["known_cost_subtotal_microusd"],
                first_stage_status=receipts[0]["result"]["status"] if receipts else None,
                prompt_tokens=_tokens(receipts, "prompt_tokens"),
                completion_tokens=_tokens(receipts, "completion_tokens"))
            try:
                row["replay"] = dict(ok=True, stages=replay(directory))
            except Exception as exc:  # noqa: BLE001 - a replay failure is a reported result
                row["replay"] = dict(ok=False, reason=f"{type(exc).__name__}: {exc}")
        rows.append(row)
    groups = {}
    for row in rows:
        g = groups.setdefault(f"{row['model']} | {row['arm']}", dict(runs=0, present=0,
            accepted=0, accepted_first_stage=0, statuses=Counter(), failure_classes=Counter(),
            provider_calls=0,
            prompt_tokens=0, completion_tokens=0, known_cost_microusd=0, unknown_cost_runs=0,
            charged_microusd=0, elapsed_ms=0, replay_failures=0))
        g["runs"] += 1
        g["charged_microusd"] += row["charged_microusd"]
        if not row["present"]:
            continue
        g["present"] += 1
        g["statuses"][row["status"] or "NO_SUMMARY"] += 1
        if row["status"] != ACCEPTED:
            g["failure_classes"][row["failure_class"] or "NONE"] += 1
        g["accepted"] += row["status"] == ACCEPTED
        g["accepted_first_stage"] += row["first_stage_status"] == ACCEPTED
        for key in ("provider_calls", "prompt_tokens", "completion_tokens", "known_cost_microusd"):
            g[key] += row[key]
        g["unknown_cost_runs"] += row["status"] is not None and row["cost_microusd"] is None
        g["elapsed_ms"] += row["elapsed_ms"] or 0
        g["replay_failures"] += row["replay"] is not None and not row["replay"]["ok"]
    for g in groups.values():
        g["statuses"] = dict(sorted(g["statuses"].items()))
        g["failure_classes"] = dict(sorted(g["failure_classes"].items()))
    matched = {}
    base, variant = plan["arms"][0], plan["arms"][1]
    by_key = {(r["model"], r["challenge"], r["arm"]): r for r in rows}
    for model in plan["models"]:
        m = dict(pairs=0, both=0, neither=0, variant_only=[], baseline_only=[])
        for challenge in plan["challenges"]:
            b, v = by_key[(model, challenge, base)], by_key[(model, challenge, variant)]
            if b["status"] is None or v["status"] is None:
                continue
            m["pairs"] += 1
            ba, va = b["status"] == ACCEPTED, v["status"] == ACCEPTED
            if ba and va:
                m["both"] += 1
            elif not ba and not va:
                m["neither"] += 1
            elif va:
                m["variant_only"].append(challenge)
            else:
                m["baseline_only"].append(challenge)
        matched[model] = m
    return dict(schema=SCHEMA, baseline_arm=base, variant_arm=variant,
        max_total_microusd=plan["max_total_microusd"],
        spent_microusd=sum(r["charged_microusd"] for r in rows), groups=groups,
        matched=matched, runs=rows, authority_effect="None",
        scope="One development case per challenge; candidate evidence, no significance claim.")


def render(collation):
    usd = lambda micro: f"${micro // 1_000_000}.{micro % 1_000_000:06d}"  # noqa: E731
    lines = ["# M5 matched campaign collation", "",
        f"Charged {usd(collation['spent_microusd'])} of the {usd(collation['max_total_microusd'])} cap "
        "(unknown costs charged at the per-run cap). AuthorityEffect: None.", "",
        "| model and arm | runs | accepted | accepted at stage 1 | calls | prompt tokens | "
        "completion tokens | known cost | unknown-cost runs | elapsed ms | replay failures |",
        "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, g in sorted(collation["groups"].items()):
        lines.append(f"| {name} | {g['present']}/{g['runs']} | {g['accepted']} | "
            f"{g['accepted_first_stage']} | {g['provider_calls']} | {g['prompt_tokens']} | "
            f"{g['completion_tokens']} | {usd(g['known_cost_microusd'])} | "
            f"{g['unknown_cost_runs']} | {g['elapsed_ms']} | {g['replay_failures']} |")
    lines += ["", f"Matched pairs ({collation['baseline_arm']} vs {collation['variant_arm']}):", ""]
    for model, m in sorted(collation["matched"].items()):
        lines.append(f"- {model}: {m['pairs']} pairs; both accepted {m['both']}, neither "
            f"{m['neither']}, only {collation['variant_arm']} {m['variant_only']}, only "
            f"{collation['baseline_arm']} {m['baseline_only']}.")
    lines += ["", "Final status and failure-class counts:", ""]
    for name, g in sorted(collation["groups"].items()):
        lines.append(f"- {name}: {g['statuses']}; failure classes {g['failure_classes']}")
    return "\n".join(lines) + "\n"


def write_collation(output, plan, **kwargs):
    collation = collate(output, plan, **kwargs)
    output = Path(output)
    (output / "collation.json").write_bytes(
        (json.dumps(collation, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii"))
    (output / "collation.md").write_bytes(render(collation).encode("utf-8"))
    return collation


def main(argv=None):
    parser = argparse.ArgumentParser(description="M5 matched PFP campaign under one total cap.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--model", action="append", default=[],
        help="restrict to this plan model (repeatable)")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="list runs and the worst case")
    action.add_argument("--run", action="store_true", help="dispatch paid runs, then collate")
    action.add_argument("--collate", action="store_true", help="replay and collate, zero calls")
    args = parser.parse_args(argv)
    plan = only_models(load_plan(args.plan), args.model)
    if args.dry_run:
        runs = runs_of(plan)
        print(json.dumps(dict(runs=len(runs), worst_case_microusd=len(runs) *
            plan["per_run_estimated_microusd"], cap_microusd=plan["max_total_microusd"],
            already_charged_microusd=spent(args.output, plan))))
        return 0
    if args.run:
        print(json.dumps(run_campaign(args.output, plan, openrouter_gateway(args.env_file))))
    collation = write_collation(args.output, plan)
    print(json.dumps(dict(spent_microusd=collation["spent_microusd"],
        groups={k: dict(accepted=g["accepted"], present=g["present"])
                for k, g in collation["groups"].items()})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
