"""One optional offline cochain demonstration, with explicit fixture mode."""

import argparse
import json
from pathlib import Path

from .pilot import check_reply, fixture_case, fixture_proposal, prepare


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument("--reply", type=Path)
    args = parser.parse_args()
    source, registry = fixture_case()
    turn = prepare(source, registry)
    if args.prepare:
        print(json.dumps({"system": turn.prompt.system, "user": turn.prompt.user,
            "response_schema": turn.prompt.response_schema, "binding": turn.binding}, sort_keys=True))
        return 0
    raw = args.reply.read_bytes() if args.reply else json.dumps({
        **{key: value for key, value in turn.binding.items() if key != "checker_id"},
        "answer": fixture_proposal(source, registry[0])}, sort_keys=True).encode("utf-8")
    checked = check_reply(turn, raw, source, registry)
    print(json.dumps({"execution_kind": "FIXTURE_VERIFIED" if args.fixture else "SUPPLIED_REPLY_CHECK",
        "provider_calls": 0, "provider_billing": "NOT_APPLICABLE_NO_SEND",
        "authority_effect": "None", "checked": checked}, sort_keys=True))
    return 0 if checked["schema_valid"] and checked["status"] == "HOST_ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
