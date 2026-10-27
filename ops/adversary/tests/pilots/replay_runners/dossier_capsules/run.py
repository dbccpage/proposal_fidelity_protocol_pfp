"""Read-only offline replay for the retired dossier-trials campaign.

python -m adversary.tests.pilots.replay_runners.dossier_capsules.run --replay
Live dispatch is retired; current tasks use the shared PFP/Adversary commands.
Original source snapshots, receipt bytes and checker-drift refusals are retained.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from collections import Counter
from decimal import ROUND_CEILING, Decimal
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml

from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1
from adversary.infrastructure.providers.openai_compat import build_openai_compat_body
from adversary.infrastructure.providers.wire import decode_reply

from .cases import PILOTS, canonical, sha
from .checking import evaluate
from .prepare import CAMPAIGN, ROOT, historical_bytes, historical_plan, prepare

RETIREMENT_REASON = (
    "RETIRED_DOSSIER_CAMPAIGN: live dispatch is retired; historical bytes remain read-only. "
    "For current tasks use python -m pfp.entrypoints.cli.pfp prepare-task TASK.json --attempt ID "
    "or python -m adversary.entrypoints.cli teamwork start --objective TASK --state NEW.json."
)
MAX_OUTPUT = 900
ACTIVE_DEPENDENCIES = (
    "adversary/tests/pilots/replay_runners/dossier_capsules/checking.py",
    "adversary/tests/pilots/replay_runners/dossier_capsules/cases.py",
    "adversary/tests/pilots/replay_runners/dossier_capsules/run.py",
    "pfp/domain/pilots/checker_registry.py",
    "adversary/infrastructure/providers/wire.py",
    "adversary/infrastructure/providers/openai_compat.py",
    "adversary/infrastructure/providers/openrouter_transport.py",
    "adversary/domain/providers/types.py",
)

LEGACY_SOURCE_ARCHIVE = {
    "education/pilots/dossier_trials/checking.py": "checking.py",
    "education/pilots/dossier_trials/cases.py": "cases.py",
    "education/pilots/dossier_trials/run.py": "run.py",
}
LEGACY_CHECKER_SOURCE = "education/pfp/domain/pilots/checker_registry.py"
# These exact old source identities resolve current bytes for digest comparison,
# never semantic equivalence or acceptance of a changed historical checker.
LEGACY_PROVIDER_SOURCES = {
    "providers/infrastructure/wire.py": ACTIVE_DEPENDENCIES[4],
    "providers/infrastructure/openai_compat.py": ACTIVE_DEPENDENCIES[5],
    "providers/infrastructure/openrouter_transport.py": ACTIVE_DEPENDENCIES[6],
    "providers/domain/types.py": ACTIVE_DEPENDENCIES[7],
}
LEGACY_DEPENDENCIES = tuple(LEGACY_SOURCE_ARCHIVE) + (LEGACY_CHECKER_SOURCE,) + tuple(LEGACY_PROVIDER_SOURCES)
# The intermediate active reader emitted a current checker key with old provider keys.
RELOCATED_DEPENDENCIES = ACTIVE_DEPENDENCIES[:4] + tuple(LEGACY_PROVIDER_SOURCES)
RELOCATED_LEGACY_DEPENDENCIES = tuple(LEGACY_SOURCE_ARCHIVE) + (ACTIVE_DEPENDENCIES[3],) + tuple(LEGACY_PROVIDER_SOURCES)
RELOCATED_PILOTS = frozenset(f"pilot_{index:07d}" for index in range(6))
HISTORICAL_REPLAY_ROOTS = {
    "free_followup": PILOTS / "matrix" / "replay_custody_20261011" / "free_followup",
}


def _source_bytes(path):
    """Resolve only active sources or the exact retired source snapshot."""
    if path in LEGACY_SOURCE_ARCHIVE:
        archive = (PILOTS / "pilot_0000188" / "misc" / "retired_dossier_trials_runner_v1"
                   / LEGACY_SOURCE_ARCHIVE[path])
        return archive.read_bytes()
    if path == LEGACY_CHECKER_SOURCE:
        path = ACTIVE_DEPENDENCIES[3]
    else:
        path = LEGACY_PROVIDER_SOURCES.get(path, path)
    if path not in ACTIVE_DEPENDENCIES:
        raise ValueError("UNREGISTERED_REPLAY_SOURCE")
    return (ROOT / path).read_bytes()


def environment():
    return dict(python=platform.python_version(), packages={name: importlib.metadata.version(name)
                for name in ("jsonschema", "PyYAML")}, sources={p: sha(_source_bytes(p)) for p in ACTIVE_DEPENDENCIES})


def source_bindings_match(sources):
    if not isinstance(sources, dict) or not sources:
        return False
    if set(sources) not in (set(ACTIVE_DEPENDENCIES), set(LEGACY_DEPENDENCIES),
            set(RELOCATED_DEPENDENCIES), set(RELOCATED_LEGACY_DEPENDENCIES)):
        return False
    try:
        for path, digest in sources.items():
            if not isinstance(path, str) or not isinstance(digest, str):
                return False
            if sha(_source_bytes(path)) != digest:
                return False
        return True
    except (OSError, ValueError):
        return False


def environment_matches(expected):
    if not isinstance(expected, dict):
        return False
    current = environment()
    if expected.get("python") != current.get("python") or expected.get("packages") != current.get("packages"):
        return False
    return source_bindings_match(expected.get("sources"))


def replay_root(session):
    """Use retained historical configuration when a retired session is replayed."""
    historical = HISTORICAL_REPLAY_ROOTS.get(session)
    if historical is not None and (historical / "authorization.yaml").is_file():
        return historical
    return PILOTS / "matrix" / CAMPAIGN / session


def capsule_folder(capsule):
    """Resolve the six declared relocated owners without searching another estate."""
    if (type(capsule) is not str or not capsule or "\\" in capsule
            or PurePosixPath(capsule).is_absolute() or PureWindowsPath(capsule).drive
            or any(part in ("", ".", "..") for part in capsule.split("/"))):
        raise ValueError("INVALID_CAPSULE_PATH")
    owner = ROOT / "pfp" / "tests" if capsule.split("/")[0] in RELOCATED_PILOTS else PILOTS
    folder = owner / Path(capsule)
    if not folder.resolve().is_relative_to(owner.resolve()):
        raise ValueError("INVALID_CAPSULE_PATH")
    return folder


def load_case(row):
    folder = capsule_folder(row["capsule"])
    data = (folder / "input.yaml").read_bytes()
    if sha(data) != row["input_sha256"]:
        raise ValueError("INPUT_DIGEST_MISMATCH")
    return folder, yaml.safe_load(data)


def request_for(case):
    prompt = case["prompt"]
    return CandidateRequest(prompt["system_prompt"], prompt["user_prompt"],
        decoding=DecodingParamsV1(temperature=0.0, allow_fallbacks=False,
                                 require_parameters=True, thinking="disabled"))


def request_wire(case, model):
    body = build_openai_compat_body(request_for(case), model=model, max_tokens=MAX_OUTPUT)
    body["usage"] = {"include": True}
    return body


def microusd(value):
    if type(value) not in (str, int, float, Decimal) or not Decimal(str(value)).is_finite() or Decimal(str(value)) < 0:
        raise ValueError("UNRECONCILED_COST")
    return int((Decimal(str(value))*1_000_000).to_integral_value(rounding=ROUND_CEILING))




def reservation(case, price):
    request = request_for(case)
    # One token per UTF-8 byte plus a framing allowance: deliberately conservative.
    upper_input_tokens = request.estimated_payload_bytes() + 256
    rates = price["row"]["pricing"]
    return microusd(Decimal(rates["prompt"])*upper_input_tokens + Decimal(rates["completion"])*MAX_OUTPUT)


def grade(case, raw, model):
    reply = decode_reply(raw)
    if reply.get("model") != model:
        raise ValueError("REPLY_MODEL_MISMATCH")
    if not isinstance(reply.get("id"), str) or not reply["id"]:
        raise ValueError("MISSING_GENERATION_ID")
    usage = reply.get("usage", {})
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if type(usage.get(name)) is not int or usage[name] < 0:
            raise ValueError("MISSING_USAGE")
    cost = microusd(usage.get("cost"))
    choices = reply.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("MISSING_COMPLETION")
    text = choices[0].get("message", {}).get("content")
    if not isinstance(text, str):
        raise ValueError("MISSING_COMPLETION")
    result = evaluate(case["task"], text, yaml.safe_load(case["prompt"]["response_schema"]))
    return dict(**result, model_id=model, generation_id=reply["id"], usage=usage,
                cost_microusd=cost, finish_reason=choices[0].get("finish_reason"))


def live(plan, model, budget, limit, per_call_budget=50000, session="primary"):
    """Refuse before directories, authorization, budgets, pricing or transport."""
    raise ValueError(RETIREMENT_REASON)


def replay_one(row, config):
    folder, case = load_case(row)
    receipt = yaml.safe_load((folder / "response.yaml").read_text(encoding="utf-8"))
    raw = (folder / "provider_response.json").read_bytes()
    expected = request_wire(case, config["model"])
    wire = (folder / "request.json").read_bytes()
    if (not environment_matches(receipt["environment"]) or receipt["environment"] != config["environment"]
            or receipt["input_sha256"] != row["input_sha256"] or sha(raw) != receipt["provider_response_sha256"]
            or wire != canonical(expected) or sha(wire) != receipt["request_sha256"]):
        raise ValueError("REPLAY_BINDING_MISMATCH")
    checked = grade(case, raw, config["model"])
    if any(receipt[k] != v for k, v in checked.items()):
        raise ValueError("REPLAY_RESULT_MISMATCH")
    return dict(capsule=row["capsule"], pilot_id=case["pilot_id"], rung=case["rung"],
                representation=case["representation"], response_sha256=sha(raw), **checked)


def replay(plan, session="primary"):
    root = replay_root(session)
    config_path = root / "authorization.yaml"
    if session == "free_followup":
        config = yaml.safe_load(historical_bytes("matrix/replay_custody_20261011/free_followup/authorization.yaml"))
    else:
        config = yaml.safe_load(config_path.read_text()) if config_path.exists() else None
    rows = []
    for row in plan["cases"]:
        folder, _ = load_case(row)
        rows.append(replay_one(row, config) if (folder / "response.yaml").exists() else dict(capsule=row["capsule"], status="PLANNED"))
    return dict(campaign=CAMPAIGN, planned=250, statuses=dict(Counter(r["status"] for r in rows)),
                cost_microusd=sum(r.get("cost_microusd", 0) for r in rows), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--session", choices=["primary", "free_followup"], default="primary")
    parser.add_argument("--budget-usd")
    parser.add_argument("--per-call-budget-usd", default="0.05")
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args()
    if args.live:
        parser.error(RETIREMENT_REASON)
    plan = prepare()
    if args.session == "free_followup":
        plan = historical_plan("_free")
    report = replay(plan, args.session)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
