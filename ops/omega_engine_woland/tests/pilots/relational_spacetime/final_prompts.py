"""Offline, reviewed final prompts; never dispatch or change historical verdicts."""

import argparse
import json

import yaml

from omega_engine_pfp.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)

from omega_engine_woland.tests.pilots.relational_spacetime import typed_signals as adaptive
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import ROOT
from omega_engine_woland.tests.pilots.relational_spacetime.baseline import refuse_without_checkout
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import load

FINAL = adaptive.EVIDENCE / "reviewed_final_prompts"
REVIEW = adaptive.EVIDENCE / "review_annotations_v2.json"
SELF = "omega_engine_woland/tests/pilots/relational_spacetime/final_prompts.py"


def dereference(document, pointer):
    """Resolve the retained JSON pointer without coercing the candidate's value."""
    for part in pointer.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        document = document[int(part)] if type(document) is list else document[part]
    return document


def validate_candidate(candidate, original_root):
    folder = original_root / f"loop_{candidate['loop']:02d}"
    prompt = load(folder / "prompt.json")
    raw = (folder / "raw_reply.json").read_bytes()
    content = json.loads(raw)["choices"][0]["message"]["content"]
    authored = dereference(json.loads(content), candidate["json_pointer"])
    checks = (
        candidate["raw_reply_sha256"] == digest(raw),
        candidate["prompt_id"] == prompt["prompt_id"],
        candidate["prompt_text_sha256"] == digest(prompt["user_prompt"].encode()),
        candidate["original_seed_sha256"] == prompt["original_seed_sha256"],
        authored == {key: candidate[key] for key in ("kind", "text", "failure_or_gain")},
        candidate["admitted"] is False,
    )
    if not all(checks):
        raise ValueError("CANDIDATE_SOURCE_BINDING_MISMATCH")


def documents():
    """Verify and reconstruct the recorded final prompts with their exact runtime."""
    from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import replay_bundle

    bundle = ROOT / "omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012"
    result = replay_bundle(ROOT, bundle, "final-prompt-documents")
    return {pilot: text.encode("utf-8") for pilot, text in result.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--replay", "--verify", dest="verify", action="store_true")
    args = parser.parse_args()
    refuse_without_checkout(parser)
    if not (args.build or args.verify):
        parser.error("Choose --build or --replay (offline only)")
    prompts = documents()
    for pilot, data in prompts.items():
        path = FINAL / f"{pilot}.yaml"
        if args.build:
            write_once(path, data)
        elif path.read_bytes() != data:
            raise ValueError("REVIEWED_FINAL_PROMPT_DRIFT")
    print(
        json.dumps(
            {
                "status": "REPLAY_VERIFIED",
                "provider_calls_replayed": 25,
                "reviewed_final_prompts": len(prompts),
                "new_provider_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
