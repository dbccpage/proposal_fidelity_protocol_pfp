"""Collate all thirty original identities without promoting finite observations.

Reads existing task sources and reported historical observations. External raw
captures stay labelled external; current local-model bytes are linked separately.
"""
import base64
import json
import re
from hashlib import sha256
from pathlib import Path

from adversary.tests.pilots.challenge_suite.catalog import ROOT, SOURCE

DOC = "education/documentation/004_oepfp/docs/18_original_challenge_play.md"
SESSION_DOC = "education/documentation/004_oepfp/docs/19_bounded_mechanism_sessions.md"


def _pin(path):
    source = ROOT / path
    return dict(path=path, sha256=sha256(source.read_bytes()).hexdigest())


def recheck_local_trial(trial, *, recipe):
    """Recompute local evidence from actual raw bytes; stored verdicts are inert."""
    from adversary.tests.pilots.challenge_suite.local_mechanism_trials import (
        cases,
        judge,
        second_judge,
        turn_for,
    )
    originals = {case["id"]: case for case in cases()}
    case = trial["case"]
    if originals.get(case.get("id")) != case:
        raise ValueError("LOCAL_TRIAL_CASE_SOURCE_MISMATCH")
    try:
        raw = base64.b64decode(trial["raw_reply_base64"], validate=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("LOCAL_TRIAL_RAW_MISMATCH") from exc
    if sha256(raw).hexdigest() != trial["raw_reply_sha256"]:
        raise ValueError("LOCAL_TRIAL_RAW_MISMATCH")
    turn = turn_for(case, attempt_id=trial["binding"]["attempt_id"], recipe=recipe)
    if turn.binding != trial["binding"] or turn.prompt.to_dict() != trial["prepared_prompt"]:
        raise ValueError("LOCAL_TRIAL_PROMPT_BINDING_MISMATCH")
    return turn.check(raw, judges=(("finite-original-certificate", lambda _c, a: judge(case, a)),
        ("secondary-domain-python", lambda _c, a: second_judge(case, a))), require_checker=True)


def build(*, local_trials=None, local_learned=None, baseline_calibration_repair=None,
          learned_calibration_repair=None):
    source = SOURCE
    observation_text = (ROOT / DOC).read_text(encoding="utf-8")
    historical = {}
    pattern = r"\| (C\d{3}) / `([^`]+)` \| ([A-Z_]+) \| (\d+) \| ([0-9.]+) \| ([0-9.]+) \|"
    for cid, case, failure, replies, cost, elapsed in re.findall(pattern, observation_text):
        historical[cid] = dict(case_id=case, model="openai/gpt-4o-mini", executor="openrouter",
            result="REJECTED_OR_PARTIAL", final_failure=failure, provider_replies=int(replies),
            known_cost_usd=cost, unknown_cost_replies=0, end_to_end_seconds=elapsed,
            input_tokens=None, output_tokens=None, raw_custody="EXTERNAL_RAW_CAPTURE_DOCUMENTED",
            source_revision="5399938449736116ad45eb547b10fb1feaad8bc7", source=_pin(DOC))
    details = {
        "C001": "Finite original distractor-prose Adversary/PFP route; full local attention/hidden/native protocol remains open.",
        "C002": "Real eager attention-column hook and tokenizer offsets; bounded tiny-model proposals. Original public grid selection, hidden/random controls and 7B/8B replication remain open.",
        "C003": "Real pre-o_proj head capture, patch and scale; finite null/undo controls. Original 300-pair attribution/ranking and replicated hidden campaign remain open.",
        "C004": "Real tokenizer finite-language trie plus existing integer-slot component. Arbitrary original grammar ladder, matched decode arms and hidden campaign remain open.",
        "C005": "Finite canonical hosted route and preserved historical decode-control replay; whole original program/held-out control protocol remains open.",
        "C006": "Original ASSERT/CUT/LIFT/VERIFY route; approved versioned 12-public/60-hidden/20-relabel/12-poison panel and exact native/independent controls. Matched model campaign and statistics remain open.",
        "C007": "Original six-stage 30-48-turn text driver, 40-hidden/12-relabel/16-poison data, protected-ID/retention/replay controls. Real finite KV mechanics available; full long-horizon KV matched campaign remains open.",
        "C008": "Actual residual contrast/addition/null/negated mechanics and bounded Pauli proposals. Original normalized 200-pair selection, native phase parity, hidden campaign and replication remain open.",
        "C009": "Exact ladder pins/drop rules and original-anchor source binding; no model-ladder campaign. Missing authoritative C061 and C071 sources block the original five-anchor packet.",
        "C010": "Exact Coverage@k, duplicate-retaining raw-PFP two-judge rescoring and identity controls. Original 120-case pool lacks C061; whole-session/hybrid allocation and matched frontier not run.",
        "C025": "Finite original witness route; numeric second-checker tolerance remains explicit, not an exact proof.",
        "C027": "Finite contextuality witness route; bounded enumeration does not supply original LRAT machinery.",
        "C029": "Current Python GF(2) coset optimality check is independent of matching; historical packet unchanged. Original matching-dual semantics, Rust judges, decoder synthesis and matched hidden campaign remain open.",
    }
    local_paths = dict(baseline=local_trials, learned=local_learned,
        baseline_calibration_repair=baseline_calibration_repair,
        learned_calibration_repair=learned_calibration_repair)
    local_runs = {name: json.loads(Path(path).read_bytes()) for name, path in local_paths.items() if path is not None}
    quarantined, counted = [], []
    for name, local in local_runs.items():
        source_pin = _pin(Path(local_paths[name]).resolve().relative_to(ROOT).as_posix())
        for trial in local["trials"]:
            recipe = "local-mechanism-v1.0.1" if name.startswith("learned") else "local-mechanism-v1.0.0"
            checked = recheck_local_trial(trial, recipe=recipe)
            entry = dict(case_id=trial["case"]["id"], protocol=trial["case"]["protocol"],
                arm="learned" if name.startswith("learned") else "baseline",
                recipe=recipe, result=checked["status"], failure_class=checked["failure_class"],
                schema_valid=checked["schema_valid"], raw_reply_sha256=trial["raw_reply_sha256"],
                evidence="ZERO_SEND_CURRENT_JUDGE_RECHECK_OF_RETAINED_RAW",
                model=local["pipeline"]["model_id"], model_revision=local["pipeline"]["revision"],
                output_tokens=len(trial["generation"]["token_ids"]),
                input_tokens=trial["generation"].get("input_tokens"), source=source_pin,
                billed_usd="0", provider_calls=0, elapsed_seconds=trial["generation"]["elapsed_seconds"])
            if name in {"baseline", "learned"} and trial["case"]["protocol"] == "C008":
                quarantined.append(dict(entry, reason="TARGET_CERTIFICATE_CONDITIONED_RESIDUAL_DIRECTION_EXCLUDED"))
            else:
                counted.append(entry)
    rows = []
    for number in range(1, 31):
        cid = f"C{number:03d}"
        paths = sorted(source.glob(f"*/{cid.lower()}*.md"))
        if not paths:
            folders = sorted(source.glob(f"*/{cid.lower()}*"))
            paths = [path for folder in folders for path in
                (folder / "participant_packet/TASK.md", folder / "TASK.md") if path.is_file()]
        if not paths:
            raise ValueError("ORIGINAL_TASK_SOURCE_MISSING:" + cid)
        task = paths[0]
        own = [trial for trial in counted if trial["protocol"] == cid]
        rows.append(dict(challenge=cid, task_source=_pin(task.relative_to(ROOT).as_posix()),
            original_protocol_status="OPEN", current_scope=details.get(cid,
                "Original finite witness CLI/judges and documented bounded attempt exist; full original synthesis/hidden/matched scientific protocol remains open."),
            runnable_state="SOURCE_BLOCKED_ORIGINAL_POOL" if cid in {"C009", "C010"} else
                "FINITE_HOST_SESSION" if cid in {"C006", "C007"} else
                "BOUNDED_LOCAL_MECHANISM" if cid in {"C002", "C003", "C004", "C008"} else "FINITE_ADVERSARY_WITNESS",
            historical_reported_observations=[historical[cid]] if cid in historical else [],
            additional_observation_source=_pin(SESSION_DOC if cid == "C006" else DOC) if cid in {"C001", "C005", "C006", "C011"} else None,
            local_model_trials=own,
            orchestration_ide_cost_usd=None, orchestration_ide_elapsed_seconds=None,
            acceptance_ceiling="Finite checked proposal/control only; AuthorityEffect None; no original protocol completion."))
    return dict(schema="pfp.original-protocol-collation.v1", authority_effect="None",
        source_base="13d18fb1dd425ad0158f7c754b3fd828207caf99", rows=rows,
        historical_known_subtotal=dict(provider_replies=87, known_cost_usd="0.03540475",
            unknown_cost_replies=0, custody="REPORTED_IN_RETAINED_RUNBOOKS_RAW_CAPTURES_EXTERNAL",
            sources=[_pin(DOC), _pin(SESSION_DOC)]),
        local_model_comparison=dict(counted_trials=counted, excluded_trials=quarantined,
            arms={arm: dict(trials=sum(row["arm"] == arm for row in counted),
                schema_valid=sum(row["arm"] == arm and row["schema_valid"] for row in counted),
                verified=sum(row["arm"] == arm and row["result"] == "HOST_ACCEPTED" for row in counted))
                for arm in ("baseline", "learned")},
            efficacy_claim="NONE_FINITE_SMALL_UNREPLICATED_INTERVENTION_CASES",
            guidance_status="CANDIDATE_NOT_ADMITTED", provider_calls=0, billed_usd="0"),
        original_protocols_closed=0, identity_count=len(rows),
        unavailable_original_sources=["pfp/tests/demo_004/g_chem_bio/c061_redox_equation_balancing.md",
            "pfp/tests/demo_004/h_economics/c071_bimatrix_all_nash_equilibria.md"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-trials", type=Path)
    parser.add_argument("--local-learned", type=Path)
    parser.add_argument("--baseline-calibration-repair", type=Path)
    parser.add_argument("--learned-calibration-repair", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(local_trials=args.local_trials, local_learned=args.local_learned,
        baseline_calibration_repair=args.baseline_calibration_repair,
        learned_calibration_repair=args.learned_calibration_repair)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(dict(identities=result["identity_count"], original_protocols_closed=0)))
