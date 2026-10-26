"""C009/C010 packet pins and independent, zero-send rescoring of actual PFP replies.

These helpers neither implement a model nor replace an anchor's original judge.
The accounted gateway owns spend admission; this module does not issue money.
"""
import base64
import json
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import comb
from pathlib import Path

LADDER = (("0.5B", "Qwen/Qwen2.5-0.5B-Instruct", 500_000_000),
    ("3B", "Qwen/Qwen2.5-3B-Instruct", 3_000_000_000),
    ("7B", "qwen/qwen-2.5-7b-instruct", 7_000_000_000),
    ("8B", "meta-llama/llama-3.1-8b-instruct", 8_000_000_000),
    ("14B", None, 14_000_000_000), ("32B", None, 32_000_000_000),
    ("70B", "meta-llama/llama-3.3-70b-instruct", 70_000_000_000))
ANCHORS = {"C009": ("C021", "C011", "C051", "C061", "C071"),
           "C010": ("C011", "C013", "C061")}


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _sha(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def coverage_at_k(n, c, k):
    """Exact Chen estimator. Duplicate draws remain in n, as the protocol requires."""
    if any(type(v) is not int for v in (n, c, k)) or not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("C010_INVALID_SAMPLE_COUNTS")
    return Fraction(1) - Fraction(comb(n - c, k) if n - c >= k else 0, comb(n, k))


def pin_ladder(routes, *, registry_sha256):
    """Pin exact registered routes; unavailable rungs stay dropped, never substituted.

    A route record is supplied by the existing registry/composition, not discovered
    by this function. Its digest is custody metadata, not live availability evidence.
    """
    if not _sha(registry_sha256) or type(routes) is not dict or set(routes) - {r[0] for r in LADDER}:
        raise ValueError("C009_REGISTRY_PIN_REQUIRED")
    result = []
    for rung, required_model, parameters in LADDER:
        route = routes.get(rung)
        if route is None:
            result.append(dict(rung=rung, status="DROPPED", reason="NO_PINNED_ROUTE"))
            continue
        if (type(route) is not dict or set(route) != {"model_id", "provider", "total_parameters", "allow_fallbacks"}
                or type(route["model_id"]) is not str or not route["model_id"].strip()
                or route["provider"] not in {"local", "openrouter"}
                or type(route["total_parameters"]) is not int
                or route["total_parameters"] != parameters or route["total_parameters"] > 70_000_000_000
                or route["allow_fallbacks"] is not False
                or (required_model is not None and route["model_id"] != required_model)):
            raise ValueError("C009_ROUTE_NOT_ORIGINAL_PIN")
        result.append(dict(rung=rung, status="PINNED_NOT_PROBED", **route))
    return dict(schema="c009.ladder-pins.v1", registry_sha256=registry_sha256, rungs=result,
        provider_calls=0, authority_effect="None")


def bind_original_anchors(protocol, source_paths, *, expected_sha256):
    """Refuse an original packet if even one required authoritative source is absent.

    Callers provide exact original paths and frozen digests. No substitute task,
    nearby file, or status label can make a missing C061/C071 packet complete.
    """
    if protocol not in ANCHORS or set(source_paths) != set(ANCHORS[protocol]) or set(expected_sha256) != set(source_paths):
        raise ValueError("ORIGINAL_ANCHOR_SET_REQUIRED")
    rows, missing = [], []
    for anchor in ANCHORS[protocol]:
        path = Path(source_paths[anchor])
        if not path.is_file():
            missing.append(anchor)
            continue
        digest = sha256(path.read_bytes()).hexdigest()
        if not _sha(expected_sha256[anchor]) or digest != expected_sha256[anchor]:
            raise ValueError("ORIGINAL_ANCHOR_SOURCE_MISMATCH:" + anchor)
        rows.append(dict(anchor=anchor, path=str(path), sha256=digest))
    if missing:
        raise ValueError("ORIGINAL_ANCHOR_SOURCE_UNAVAILABLE:" + ",".join(missing))
    return dict(protocol=protocol, original_sources=rows, sha256=_digest(rows),
        status="SOURCE_PINS_ONLY_JUDGE_PACKET_REQUIRED")


def rescore_samples(samples, *, prepare_turn, judges, judge_packet_sha256):
    """Retain and recheck every raw draw, ignoring an arm's own success labels.

    ``prepare_turn(sample_id, seed)`` rebuilds that draw's original PFP binding.
    Both supplied original judges must approve. Distinct names/functions prevent
    accidental duplicate registration; their scientific independence remains the
    anchor packet's obligation. No provider or participant code is executed here.
    """
    judges = tuple(judges)
    if (not _sha(judge_packet_sha256) or len(judges) != 2
            or len({name for name, _ in judges}) != 2
            or judges[0][1] is judges[1][1] or any(not callable(judge) for _, judge in judges)):
        raise ValueError("TWO_ORIGINAL_JUDGES_REQUIRED")
    if type(samples) is not list or not 1 <= len(samples) <= 64:
        raise ValueError("C010_BOUNDED_SAMPLES_REQUIRED")
    seen_ids, seen_seeds, rows, answers = set(), set(), [], set()
    case_digest = None
    for sample in samples:
        if (type(sample) is not dict or not {"sample_id", "seed", "raw_reply_base64", "raw_reply_sha256"} <= set(sample)
                or type(sample["sample_id"]) is not str or not sample["sample_id"].strip()
                or type(sample["seed"]) is not int or sample["sample_id"] in seen_ids or sample["seed"] in seen_seeds):
            raise ValueError("C010_INDEPENDENT_SAMPLE_IDENTITIES_REQUIRED")
        seen_ids.add(sample["sample_id"])
        seen_seeds.add(sample["seed"])
        try:
            raw = base64.b64decode(sample["raw_reply_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("C010_RAW_CUSTODY_MISMATCH") from exc
        if sha256(raw).hexdigest() != sample["raw_reply_sha256"]:
            raise ValueError("C010_RAW_CUSTODY_MISMATCH")
        turn = prepare_turn(sample["sample_id"], sample["seed"])
        # Identical input/checker bytes across independent attempts, not across cases.
        digest = _digest(dict(case=turn.task.case, checker_id=turn.checker_id))
        if case_digest is not None and case_digest != digest:
            raise ValueError("C010_UNMATCHED_CASE_BYTES")
        case_digest = digest
        checked = turn.check(raw, judges=judges, require_checker=True)
        if checked.get("answer") is not None:
            answers.add(_digest(checked["answer"]))
        rows.append(dict(sample=deepcopy(sample), pfp=checked,
            verified=checked["status"] == "HOST_ACCEPTED"))
    count = sum(row["verified"] for row in rows)
    return dict(schema="c010.rescoring.v1", samples=rows, n=len(rows), c=count,
        distinct_answers=len(answers), coverage={str(k): str(coverage_at_k(len(rows), count, k)) for k in range(1, len(rows) + 1)},
        judge_packet_sha256=judge_packet_sha256, input_case_sha256=case_digest,
        provider_calls=0, evidence="RAW_REPLY_RESCORING_NOT_A_NEW_MODEL_TRIAL")
