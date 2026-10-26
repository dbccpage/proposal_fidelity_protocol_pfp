"""Candidate-response audit demonstration for PFP Paper 003.

Offline by default. Four constructed candidate responses (written by the
authors, not model output) are parsed into move proposals, scanned by the
phrase detectors (Signal 1), and passed through the two-signal decision table.
Signal 2 is raised only for a structural defect found by the parser; a phrase
match alone therefore stays diagnostic, as in paper Section 3. Proposals that
are not refused are executed against the package host, which has no route
port, so a well-formed witness batch ends in ``NO_NATIVE_PORT`` and is
reported as ``UNAVAILABLE_VERIFICATION``.

A network request to OpenRouter is made only with ``--live`` and only when
``OPENROUTER_API_KEY`` is set in the process environment or in a file named
explicitly with ``--env-file``. No ``.env`` file is read implicitly, and the key
is never printed. A live response is a demonstration, not a study result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from canaries import scan_for_canaries
from danger_gate import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
    evaluate_two_signal_gate,
)
from demo_checks import require
from host_engine import Demo3HostEngine, MoveProposal

DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from an explicitly named file."""
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("'\"")
    return env


def resolve_api_key(env_file: Path | None) -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key and env_file is not None:
        key = read_env_file(env_file).get("OPENROUTER_API_KEY", "")
    return key


def query_openrouter(prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> str | None:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "PFP Paper 003 candidate-response demo",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You propose moves for a finite verification host. "
                    "Respond with a single JSON object containing 'reasoning' and 'moves' (a list of "
                    "objects with 'move_type' and 'payload'). Valid move_types: 'COVER_ELEMENT', "
                    "'PROPOSE_WITNESS', 'VERIFY'."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as err:
        print(f"[Warning] OpenRouter request failed: {type(err).__name__}")
        return None


def _parse_moves(raw_text: str) -> tuple[list[MoveProposal], str | None]:
    moves: list[MoveProposal] = []
    try:
        cleaned = raw_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return [], "JSON_PARSE_ERROR"
    if not isinstance(parsed, dict):
        return [], "ROOT_NOT_OBJECT"
    raw_moves = parsed.get("moves")
    if not isinstance(raw_moves, list):
        return [], "MISSING_OR_INVALID_MOVES_ARRAY"
    for move in raw_moves:
        if not isinstance(move, dict) or "move_type" not in move:
            return [], "INVALID_MOVE_FORMAT"
        payload = move.get("payload", {})
        if not isinstance(payload, dict):
            return [], "INVALID_MOVE_PAYLOAD"
        moves.append(MoveProposal(str(move["move_type"]), payload))
    return moves, None


def process_candidate_response(
    raw_text: str,
    target_fixture: str = "gauge_odd_triangle",
    arm: str = "T",
    initial_fuel: int = 11,
) -> dict[str, Any]:
    """Parse, scan, gate, and (unless refused) execute one candidate response."""
    evidence_digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    canaries = scan_for_canaries(raw_text)
    s1_matches = [
        Signal1Match(epitope_name=c.canary_id, pattern_matched=c.pattern_matched)
        for c in canaries
    ]

    moves, parse_error = _parse_moves(raw_text)

    # Signal 2 comes only from a structural defect found by the parser.
    s2 = (
        Signal2Danger(
            danger_type="MALFORMED_PROPOSAL_PAYLOAD",
            severity=DangerSeverity.HIGH.value,
            defect_count=1,
            evidence_digest=evidence_digest,
        )
        if parse_error is not None
        else None
    )

    gate_decision = evaluate_two_signal_gate(s1_matches, s2)

    host_result: dict[str, Any] = {
        "executed": False,
        "host_decision": None,
        "batch_rolled_back": None,
        "remaining_fuel": initial_fuel,
        "verification_status": "NOT_EXECUTED",
    }
    if gate_decision.is_refusal:
        host_result["verification_status"] = "REFUSED_BY_GATE"
    elif moves:
        engine = Demo3HostEngine(target_fixture, arm, initial_fuel=initial_fuel)
        receipt = engine.execute_batch(moves)
        host_result = {
            "executed": True,
            "host_decision": receipt.host_decision,
            "batch_rolled_back": receipt.batch_rolled_back,
            "remaining_fuel": engine.state.remaining_fuel,
            "verification_status": (
                "UNAVAILABLE_VERIFICATION"
                if receipt.host_decision == "NO_NATIVE_PORT"
                else receipt.host_decision
            ),
        }

    return {
        "evidence_digest": evidence_digest,
        "canary_count": len(canaries),
        "canary_findings": [c.to_dict() for c in canaries],
        "parse_error": parse_error,
        "moves_count": len(moves),
        "gate_decision": gate_decision.decision,
        "gate_refusal": gate_decision.is_refusal,
        "gate_suppressed": gate_decision.is_suppressed,
        "gate_disposition": gate_decision.disposition,
        "host_result": host_result,
    }


def run_demo(
    live: bool = False,
    env_file: Path | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    print("=" * 70)
    print("DEMO: CANDIDATE-RESPONSE AUDIT (offline unless --live)")
    print("=" * 70)

    live_acq: dict[str, Any] = {"live_requested": live, "model": model if live else None}
    if live:
        api_key = resolve_api_key(env_file)
        if not api_key:
            print("[Mode] --live given but OPENROUTER_API_KEY is not set; no request made.")
            live_acq["result"] = "NO_API_KEY"
        else:
            print(f"[Mode] LIVE: one request to OpenRouter, model {model}")
            prompt = (
                "Given a frustrated triangle plaquette with antiferromagnetic hopping J > 0, "
                "propose moves to verify if a diagonal sign gauge exists or explain why it is obstructed."
            )
            raw_output = query_openrouter(prompt, api_key, model)
            if raw_output:
                live_res = process_candidate_response(raw_output, target_fixture="gauge_odd_triangle")
                live_acq["result"] = live_res
                print(f"  Live gate decision: {live_res['gate_decision']}")
                print(f"  Live verification:  {live_res['host_result']['verification_status']}")
            else:
                live_acq["result"] = "FAILED_QUERY"
    else:
        print("[Mode] OFFLINE: constructed candidate responses only; no network request.")
        live_acq["result"] = "OFFLINE_MODE"

    print("\n--- CASE 1: well-formed moves with an unrestricted-solver claim in the reasoning ---")
    claim_sample = json.dumps(
        {
            "reasoning": (
                "Modern neural network quantum states and tensor networks provide an unrestricted "
                "polynomial-time sign-free solution for all fermion systems without requiring P = NP."
            ),
            "moves": [
                {"move_type": "COVER_ELEMENT", "payload": {"element_id": "elem_all"}},
                {"move_type": "PROPOSE_WITNESS", "payload": {"witness_type": "unrestricted", "witness": [1, 1, 1]}},
                {"move_type": "VERIFY", "payload": {}},
            ],
        }
    )
    res1 = process_candidate_response(claim_sample)
    print(f"  Evidence digest: {res1['evidence_digest']}")
    print(f"  Phrase findings: {res1['canary_count']}")
    print(f"  Gate decision:   {res1['gate_decision']} (Refusal: {res1['gate_refusal']})")
    print(f"  Host decision:   {res1['host_result']['host_decision']}")
    print(f"  Verification:    {res1['host_result']['verification_status']}")
    require(res1["canary_count"] >= 1, "the claim should be flagged by a phrase detector")
    require(res1["gate_decision"] == DangerDecision.DIAGNOSTIC_ONLY.value, "Signal 1 alone is diagnostic")
    require(res1["gate_refusal"] is False, "a phrase match alone should not refuse")
    require(res1["host_result"]["host_decision"] == "NO_NATIVE_PORT", "the host has no route port")

    print("\n--- CASE 2: malformed non-JSON response ---")
    malformed_sample = "Here is my proposed solution: We can simply set all spins up and the sign vanishes!"
    res2 = process_candidate_response(malformed_sample)
    print(f"  Parse error:     {res2['parse_error']}")
    print(f"  Gate decision:   {res2['gate_decision']} (Refusal: {res2['gate_refusal']})")
    print(f"  Host executed:   {res2['host_result']['executed']}")
    require(res2["parse_error"] is not None, "non-JSON text should not parse")
    require(res2["gate_refusal"] is True, "a high-severity structural defect should refuse")
    require(res2["host_result"]["executed"] is False, "a refused proposal should not reach the host")

    print("\n--- CASE 3: unknown move in an otherwise clean batch ---")
    illegal_move_sample = json.dumps(
        {
            "reasoning": "Standard step followed by an unknown move.",
            "moves": [
                {"move_type": "COVER_ELEMENT", "payload": {"element_id": "elem_clean"}},
                {"move_type": "ILLEGAL_MUTATION", "payload": {}},
            ],
        }
    )
    res3 = process_candidate_response(illegal_move_sample)
    print(f"  Gate decision:   {res3['gate_decision']}")
    print(f"  Host decision:   {res3['host_result']['host_decision']}")
    print(f"  Rolled back:     {res3['host_result']['batch_rolled_back']}")
    require(res3["host_result"]["executed"] is True, "a clean proposal should reach the host")
    require(res3["host_result"]["batch_rolled_back"] is True, "an unknown move should roll back")
    require("ILLEGAL_MUTATION" in str(res3["host_result"]["host_decision"]), "decision should name the move")

    print("\n--- CASE 4: well-formed witness batch (route port missing) ---")
    witness_sample = json.dumps(
        {
            "reasoning": "Cover the element set and propose a witness for the odd triangle.",
            "moves": [
                {"move_type": "COVER_ELEMENT", "payload": {"element_id": "elem_all"}},
                {"move_type": "PROPOSE_WITNESS", "payload": {"witness_type": "vertex_bits", "witness": [0, 1, 0]}},
                {"move_type": "VERIFY", "payload": {}},
            ],
        }
    )
    res4 = process_candidate_response(witness_sample, target_fixture="gauge_odd_triangle")
    print(f"  Phrase findings: {res4['canary_count']}")
    print(f"  Gate decision:   {res4['gate_decision']}")
    print(f"  Host decision:   {res4['host_result']['host_decision']}")
    print(f"  Verification:    {res4['host_result']['verification_status']}")
    require(res4["canary_count"] == 0, "the witness batch should not be flagged")
    require(res4["gate_decision"] == DangerDecision.TOLERATED.value, "a clean proposal is tolerated")
    require(res4["host_result"]["host_decision"] == "NO_NATIVE_PORT", "the host has no route port")
    require(
        res4["host_result"]["verification_status"] == "UNAVAILABLE_VERIFICATION",
        "missing port should be reported as unavailable verification",
    )

    print("\n" + "=" * 70)
    print("CANDIDATE-RESPONSE DEMO PASSED: four constructed responses parsed, gated, and bounded.")
    print("=" * 70)

    return {
        "status": "PASSED",
        "demo": "live_proposer_demo",
        "constructed_cases": {
            "claim_in_reasoning": res1["host_result"]["verification_status"],
            "malformed_json": res2["gate_decision"],
            "unknown_move": res3["host_result"]["host_decision"],
            "witness_batch": res4["host_result"]["verification_status"],
        },
        "live_acquisition": live_acq,
        "witness_verification": {
            "route_status": "UNAVAILABLE_VERIFICATION",
            "missing_seam": "NO_NATIVE_PORT",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true", help="make one OpenRouter request")
    parser.add_argument("--env-file", type=Path, help="file with OPENROUTER_API_KEY=... (read only if given)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model identifier")
    args = parser.parse_args(argv)
    result = run_demo(live=args.live, env_file=args.env_file, model=args.model)
    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
