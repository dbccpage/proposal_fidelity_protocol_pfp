"""Offline, reviewed final prompts; never dispatch or change historical verdicts."""

import argparse
import json

import yaml

from omega_engine_symbol_game.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)

from . import adaptive
from .cases import BY_ID, ROOT, load

FINAL = adaptive.EVIDENCE / "reviewed_final_prompts"
REVIEW = adaptive.EVIDENCE / "review_annotations_v2.json"
SELF = "omega_engine_education/pfp/infrastructure/po035/closeout.py"


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
    """Replay all stages, validate authorship, then construct the five clean contexts."""
    replayed = {row["pilot_id"]: row for row in adaptive.replay()}
    review = load(REVIEW)
    candidates = load(adaptive.EVIDENCE / "candidate_artifacts.json")
    findings = load(adaptive.EVIDENCE / "consolidated_findings.json")
    result = {}
    for pilot in BY_ID:
        row = replayed[pilot]
        original = (
            adaptive.base.EVIDENCE / pilot
            if row.get("evidence_kind") == "POSTHOC_TYPED_SIGNAL_HARVEST"
            else adaptive.EVIDENCE / pilot
        )
        items = [item for item in candidates if item["pilot_id"] == pilot]
        for item in items:
            validate_candidate(item, original)
        selected_ids = review["pilots"][pilot]["selected_candidate_ids"]
        by_id = {item["artifact_id"]: item for item in items}
        if len(by_id) != len(items) or len(set(selected_ids)) != len(selected_ids):
            raise ValueError("DUPLICATE_CANDIDATE_ID")
        guidance = []
        for artifact_id in selected_ids:
            item = by_id[artifact_id]
            guidance.append(
                {
                    **{
                        key: item[key] for key in ("artifact_id", "kind", "text", "failure_or_gain")
                    },
                    "authorship": "MODEL",
                    "prompt_id": item["prompt_id"],
                    "raw_reply_sha256": item["raw_reply_sha256"],
                    "json_pointer": item["json_pointer"],
                    "status": "EXPERIMENTAL_UNADMITTED",
                }
            )
        lineage = []
        for path in sorted(original.glob("loop_*/provider_receipt.json")):
            lineage.append(
                {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path.read_bytes())}
            )
        for index, tag in enumerate(review["pilots"][pilot]["reviewer_guidance"]):
            guidance.append(
                {
                    **tag,
                    "artifact_id": f"{pilot}:review:guidance:{index:02d}",
                    "authorship": "CODEX_REVIEWER",
                    "status": "EXPERIMENTAL_UNADMITTED",
                    "source_prompt_ids": [
                        load(path.parent / "prompt.json")["prompt_id"]
                        for path in sorted(original.glob("loop_*/provider_receipt.json"))
                    ],
                    "lineage_receipts": lineage,
                }
            )
        # Failed model proposals and rejected advice are retained in evidence,
        # but do not silently contaminate the final single-shot context.
        context = {
            "parent_prompt_id": row["context"]["parent_prompt_id"],
            "granted_lifts": row["context"]["granted_lifts"],
            "guidance": guidance,
        }
        prompt = adaptive.build_prompt(pilot, 6, context, final=True)
        prompt["prompt_id"] = f"{pilot}:po035:final:reviewed-v4"
        prompt["prompt_uri"] = f"prompt://pfp/po035/derivation/final/{pilot}/reviewed-v4"
        user = json.loads(prompt["user_prompt"])
        user["prompt_id"] = prompt["prompt_id"]
        user["guidance_scope"] = (
            "Experimental procedural advice only. Recompute every witness. Exact encoding is not correctness. Cochain identities are not exactness or physical laws. Do not infer acceptance from prior model claims or a policy flag. No final-prompt gain has been measured."
        )
        prompt["user_prompt"] = canonical(user).decode()
        prompt.update(
            recipe="po035_reviewed_closeout_v4",
            source_candidate_ids=selected_ids,
            retained_only_candidate_ids=[
                item["artifact_id"] for item in items if item["artifact_id"] not in selected_ids
            ],
            lineage_receipts=lineage,
            review_annotations_sha256=digest(REVIEW.read_bytes()),
            candidate_collection_sha256=digest(
                (adaptive.EVIDENCE / "candidate_artifacts.json").read_bytes()
            ),
            builder_sha256=digest((ROOT / SELF).read_bytes()),
            original_seed_file_sha256=digest((adaptive.PILOTS / pilot / "seed.yaml").read_bytes()),
            original_template_file_sha256=digest(
                (adaptive.PILOTS / pilot / "prompt_template.yaml").read_bytes()
            ),
            tag_status="EXPERIMENTAL_UNADMITTED",
            analytical_status="UNVERIFIED",
            paired_final_prompt_gain="UNMEASURED",
            provider_dispatches=0,
        )
        terminal = next(
            item["terminal"] for item in findings["pilots"] if item["pilot_id"] == pilot
        )
        if terminal["completed_loops"] != 5 or terminal["provider_calls"] != 5:
            raise ValueError("INCOMPLETE_PILOT")
        result[pilot] = yaml.safe_dump(prompt, sort_keys=False, allow_unicode=True).encode()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--replay", "--verify", dest="verify", action="store_true")
    args = parser.parse_args()
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
