"""Live Adversarial Debate Demo for PFP Paper 001.

Conducts live proposer-adversary debates on the Hubbard model sign problem
over finite lattices using OpenRouter LLM endpoints, verified against the
fail-closed BqnfCertificateGate.

Configuration is explicit. The API key comes from the OPENROUTER_API_KEY
environment variable or from a file named with --env-file; no directory is
searched. Every run writes to a caller-named output directory: each bout's
prompts, raw provider responses, parsed moves and gate result are appended to
trace.jsonl as soon as the bout ends, including responses that fail to parse.
receipt.json summarizes the run and records whether it completed.

Zero external dependencies: uses standard library urllib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure local code directory is on sys.path
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from certificate_gate import BqnfCertificateGate  # noqa: E402

LATTICES = {
    "c5_pentagon": {
        "name": "C5 Pentagonal Plaquette",
        "sites": list(range(5)),
        "bonds": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],
    },
    "kagome_cluster": {
        "name": "Kagome Trimer Cluster",
        "sites": list(range(6)),
        "bonds": [
            (0, 1), (1, 2), (2, 0),
            (2, 3), (3, 4), (4, 2),
            (4, 5), (5, 0), (0, 4),
        ],
    },
}

U_SWEEP = [-4.0, -2.0, 0.0, 2.0, 4.0]

DEFAULT_PROPOSER_MODEL = "meta-llama/llama-3.1-8b-instruct"
DEFAULT_ADVERSARY_MODEL = "deepseek/deepseek-chat"


class LiveConfigurationError(RuntimeError):
    """Missing or invalid explicit configuration; no discovery is attempted."""

    code = "LIVE_CONFIGURATION_MISSING"


def resolve_api_key(env_file: Optional[Path] = None) -> str:
    """Return OPENROUTER_API_KEY from the environment or one explicitly named file."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    if env_file is None:
        raise LiveConfigurationError(
            "OPENROUTER_API_KEY is not set. Export it in the environment, or pass "
            "--env-file PATH naming a file that contains OPENROUTER_API_KEY=... "
            "(see .env.example). No directory is searched for credentials."
        )
    try:
        lines = Path(env_file).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise LiveConfigurationError(f"cannot read --env-file {env_file}: {error}") from error
    for line in lines:
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            value = line.split("=", 1)[1].strip().strip("'\"")
            if value and not value.startswith("your_"):
                return value
    raise LiveConfigurationError(f"--env-file {env_file} does not define a usable OPENROUTER_API_KEY")


def call_openrouter(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    temperature: float = 0.0,
    max_tokens: int = 1000,
) -> Tuple[str, str]:
    """Call OpenRouter chat completions; return (message content, raw response body)."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/dbccpage/the_symbol_game",
            "X-Title": "PFP Research Paper 001",
            "User-Agent": "PFP-Paper-001-LiveDemo/1.0",
        },
        method="POST",
    )

    retries = 3
    delay = 2.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                return data["choices"][0]["message"]["content"], body
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            if err.code == 429 and attempt < retries - 1:
                print(f"  [Rate limited (429) on {model}; waiting {delay:.1f}s before retry {attempt + 1}/{retries}...]")
                time.sleep(delay)
                delay *= 2.0
                continue
            raise RuntimeError(f"OpenRouter API HTTP {err.code}: {body}") from err
        except urllib.error.URLError as err:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2.0
                continue
            raise RuntimeError(f"OpenRouter network connection error: {err.reason}") from err
    raise RuntimeError("OpenRouter call failed after retries")


def extract_json(raw: str) -> Dict[str, Any]:
    """Extract a JSON object from LLM response text, or raise ValueError."""
    raw = raw.strip()
    # Match markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Direct JSON parse attempt
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Find first '{' and last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from model response: {raw[:200]}")


def proposer_messages(lattice_key: str, u_val: float) -> List[Dict[str, str]]:
    lat = LATTICES[lattice_key]
    system_prompt = (
        "You are a computational quantum physicist analyzing the Fermionic Sign Problem (FSP) "
        "in the Hubbard model on finite lattices. You must submit a formal proposal in strict JSON format.\n"
        "Allowed moves:\n"
        "1. VERIFY_SIGN_FREE: Propose an exact sign-reversing involution xi_witness mapping states with equal weight and opposite signs.\n"
        "2. OPEN_SIGN_OBSTRUCTION: Declare an obstruction preventing sign-free simulation, with explicit topological/symmetry justification.\n\n"
        "Output ONLY valid JSON matching either:\n"
        '{"move_type": "VERIFY_SIGN_FREE", "xi_witness": {"type": "parity", "mapping": {"0": "1", ...}}}\n'
        "OR\n"
        '{"move_type": "OPEN_SIGN_OBSTRUCTION", "reason": "<precise justification>"}'
    )
    user_prompt = (
        f"Lattice: {lat['name']} ({lattice_key})\n"
        f"Sites: {lat['sites']}\n"
        f"Bonds: {lat['bonds']}\n"
        f"Parameters: hopping t = 1.0, interaction U/t = {u_val}\n\n"
        "Submit your formal proposal JSON for this lattice and interaction strength."
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def adversary_messages(lattice_key: str, u_val: float, proposer_move: Any) -> List[Dict[str, str]]:
    lat = LATTICES[lattice_key]
    system_prompt = (
        "You are an adversarial mathematical auditor. Your duty is to rigorously challenge unverified "
        "or hallucinated claims about the Fermionic Sign Problem in the Hubbard model.\n"
        "Check whether odd cycles, non-bipartite frustration, or unverified involution mappings "
        "invalidate the claim.\n"
        "Output ONLY valid JSON:\n"
        "{\n"
        '  "adversary_verdict": "CHALLENGE" or "CONCUR",\n'
        '  "detected_anti_morphism": "NONE" or "<name>",\n'
        '  "topological_analysis": "<analysis of odd cycle/bipartite/sign structure>",\n'
        '  "counter_move": "OPEN_SIGN_OBSTRUCTION" or "VERIFY_SIGN_FREE",\n'
        '  "reason": "<rigorous critique>"\n'
        "}"
    )
    user_prompt = (
        f"Lattice: {lat['name']} ({lattice_key})\n"
        f"Sites: {lat['sites']}\n"
        f"Bonds: {lat['bonds']}\n"
        f"Parameters: t = 1.0, U/t = {u_val}\n"
        f"Proposer Move:\n{json.dumps(proposer_move, indent=2)}\n\n"
        "Critique this proposal. Does it satisfy exact certificate laws or does it hallucinate?"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def _query(messages: List[Dict[str, str]], model: str, api_key: str) -> Dict[str, Any]:
    """Call the provider and keep every byte, whether or not the reply parses."""
    raw, body = call_openrouter(messages, model=model, api_key=api_key)
    record: Dict[str, Any] = {"model": model, "messages": messages, "raw": raw, "response_body": body}
    try:
        record["parsed"] = extract_json(raw)
        record["parse_error"] = None
    except ValueError as error:
        record["parsed"] = None
        record["parse_error"] = str(error)
    return record


def run_single_bout(
    lattice_key: str,
    u_val: float,
    proposer_model: str,
    adversary_model: str,
    api_key: str,
) -> Dict[str, Any]:
    """Execute a single live proposer-adversary debate round on a lattice fixture."""
    lat = LATTICES[lattice_key]
    print(f"\n[{lattice_key} | U/t={u_val}] Querying Proposer ({proposer_model})...")
    proposer = _query(proposer_messages(lattice_key, u_val), proposer_model, api_key)
    prop_move = proposer["parsed"]

    if prop_move is None:
        # An unparseable proposal is a refused proposal; the adversary sees the raw text.
        status, admitted, gate_reason = "Refused_UnparseableProposal", False, proposer["parse_error"]
    else:
        gate = BqnfCertificateGate(lattice_key, {**lat, "U": u_val, "t": 1.0})
        status, admitted, gate_reason = gate.verify_proposal_item(prop_move)
    is_hallucination = not admitted

    move_type = prop_move.get("move_type") if isinstance(prop_move, dict) else None
    print(f"  Proposer Move: {move_type} -> Gate: {status} (Admitted={admitted})")
    print(f"[{lattice_key} | U/t={u_val}] Querying Adversary ({adversary_model})...")
    adversary = _query(
        adversary_messages(lattice_key, u_val, prop_move if prop_move is not None else proposer["raw"]),
        adversary_model,
        api_key,
    )
    adv_critique = adversary["parsed"] if isinstance(adversary["parsed"], dict) else {}

    adv_verdict = adv_critique.get("adversary_verdict", "UNPARSEABLE")
    print(f"  Adversary Verdict: {adv_verdict} (Counter: {adv_critique.get('counter_move')})")

    caught = (is_hallucination and adv_verdict == "CHALLENGE") or (not is_hallucination and adv_verdict == "CONCUR")

    terminal_state = "OpenSignObstruction"
    if admitted and move_type == "VERIFY_SIGN_FREE":
        terminal_state = "VerifiedSignFree"

    governor_verdict = "Adjudicated via Gate"
    if is_hallucination and adv_verdict == "CHALLENGE":
        governor_verdict = "Adjudicated to OpenSignObstruction via Adversary Challenge"
    elif admitted:
        governor_verdict = "Admitted Proposer Move"

    return {
        "lattice_key": lattice_key,
        "lattice_name": lat["name"],
        "u_val": u_val,
        "proposer_request": proposer["messages"],
        "proposer_raw": proposer["raw"],
        "proposer_response_body": proposer["response_body"],
        "proposer_parse_error": proposer["parse_error"],
        "proposer_move": prop_move,
        "proposer_status": status,
        "proposer_hallucination": is_hallucination,
        "adversary_request": adversary["messages"],
        "adversary_raw": adversary["raw"],
        "adversary_response_body": adversary["response_body"],
        "adversary_parse_error": adversary["parse_error"],
        "adversary_critique": adv_critique,
        "adversary_caught_am": caught,
        "governor_verdict": governor_verdict,
        "terminal_state": terminal_state,
        "replay_status": status,
        "replay_admitted": admitted,
        "replay_reason": gate_reason,
    }


def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_live_debate(
    output_dir: Path,
    lattice_keys: Optional[List[str]] = None,
    u_values: Optional[List[float]] = None,
    proposer_model: str = DEFAULT_PROPOSER_MODEL,
    adversary_model: str = DEFAULT_ADVERSARY_MODEL,
    api_key: Optional[str] = None,
    env_file: Optional[Path] = None,
    delay_between_calls: float = 1.0,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Execute a live sweep, persisting every bout to output_dir before the next begins."""
    if output_dir is None:
        raise LiveConfigurationError("A live run requires an explicit output directory (--output-dir).")
    resolved_key = api_key or resolve_api_key(env_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / "trace.jsonl"
    receipt_path = output_dir / "receipt.json"
    if trace_path.exists() or receipt_path.exists():
        raise LiveConfigurationError(f"{output_dir} already holds a run; choose a new output directory")

    lattices = lattice_keys or list(LATTICES.keys())
    u_vals = u_values or U_SWEEP
    started = datetime.now(timezone.utc).isoformat()

    print("=" * 70)
    print("PFP PAPER 001: LIVE ADVERSARIAL DEBATE DEMO")
    print(f"Proposer Model:  {proposer_model}")
    print(f"Adversary Model: {adversary_model}")
    print(f"Lattices:        {lattices}")
    print(f"U/t conditions:  {u_vals}")
    print(f"Output:          {output_dir}")
    print("=" * 70)

    rows: List[Dict[str, Any]] = []
    counts: Counter = Counter()
    trials: List[Dict[str, Any]] = []
    failure: Optional[str] = None

    for lattice_key in lattices:
        for u in u_vals:
            try:
                record = run_single_bout(
                    lattice_key=lattice_key,
                    u_val=u,
                    proposer_model=proposer_model,
                    adversary_model=adversary_model,
                    api_key=resolved_key,
                )
            except RuntimeError as error:
                failure = f"{lattice_key} U/t={u}: {error}"
                _append_jsonl(trace_path, {"lattice_key": lattice_key, "u_val": u, "transport_error": str(error)})
                break
            _append_jsonl(trace_path, record)
            rows.append(record)

            label = record["proposer_hallucination"]
            challenge = record["adversary_critique"].get("adversary_verdict") == "CHALLENGE"
            counts[(label, challenge)] += 1

            trials.append({
                "lattice": lattice_key,
                "U_over_t": u,
                "proposer_move": record["proposer_move"].get("move_type") if isinstance(record["proposer_move"], dict) else None,
                "proposer_status": record["proposer_status"],
                "hallucination_label": label,
                "adversary_verdict": record["adversary_critique"].get("adversary_verdict"),
                "adversary_counter": record["adversary_critique"].get("counter_move"),
                "terminal_state": record["terminal_state"],
                "gate_admitted": record["replay_admitted"],
                "gate_reason": record["replay_reason"],
            })
            if delay_between_calls > 0:
                time.sleep(delay_between_calls)
        if failure is not None:
            break

    tp = counts[True, True]
    fp = counts[False, True]
    tn = counts[False, False]
    fn = counts[True, False]

    def ratio(n: int, d: int) -> Optional[float]:
        return n / d if d else None

    receipt = {
        "round": "demo2_r7_adversarial_debate_live",
        "execution_mode": "live_openrouter_execution",
        "run_status": "COMPLETE" if failure is None else "INCOMPLETE",
        "failure": failure,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "proposer_model": proposer_model,
        "adversary_model": adversary_model,
        "trace_file": trace_path.name,
        "total_trials": len(rows),
        "proposer_hallucinations": tp + fn,
        "proposer_valid_moves": tn + fp,
        "adversary_challenges": tp + fp,
        "adversary_concurrences": tn + fn,
        "adversary_true_positives": tp,
        "adversary_false_positives": fp,
        "adversary_true_negatives": tn,
        "adversary_false_negatives": fn,
        "adversary_challenge_precision": ratio(tp, tp + fp),
        "adversary_challenge_recall": ratio(tp, tp + fn),
        "adversary_classification_accuracy": ratio(tp + tn, len(rows)),
        "label_basis": "current gate refusal of the proposal; not independent physical ground truth",
        "terminal_states": dict(Counter(r["terminal_state"] for r in rows)),
        "trials": trials,
        "authority_effect": "None",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")

    print("\n" + "=" * 70)
    print(f"LIVE DEBATE RESULTS ({receipt['run_status']})")
    print("=" * 70)
    print(f"Total Trials:                 {len(rows)}")
    print(f"Proposer Hallucinations:      {tp + fn}")
    print(f"Adversary Challenges:         {tp + fp}")
    print(f"Adversary True Positives:     {tp}")
    print(f"Adversary False Positives:    {fp}")
    print(f"Adversary True Negatives:     {tn}")
    print(f"Adversary False Negatives:    {fn}")
    print(f"Adversary Challenge Precision:{receipt['adversary_challenge_precision']}")
    print(f"Adversary Challenge Recall:   {receipt['adversary_challenge_recall']}")
    print(f"Adversary Accuracy:           {receipt['adversary_classification_accuracy']}")
    print(f"Trace and receipt written to {output_dir}")
    print("=" * 70)

    if failure is not None:
        raise RuntimeError(f"Live run incomplete; completed bouts are preserved in {trace_path}: {failure}")
    return receipt, rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for trace.jsonl and receipt.json")
    parser.add_argument("--env-file", type=Path, help="File containing OPENROUTER_API_KEY=... (optional; environment is read first)")
    parser.add_argument("--lattice", choices=["c5_pentagon", "kagome_cluster", "both"], default="both")
    parser.add_argument("--u", type=float, help="Single U/t value (default: all -4, -2, 0, 2, 4)")
    parser.add_argument("--proposer-model", default=DEFAULT_PROPOSER_MODEL)
    parser.add_argument("--adversary-model", default=DEFAULT_ADVERSARY_MODEL)
    args = parser.parse_args()

    lattices = [args.lattice] if args.lattice != "both" else list(LATTICES.keys())
    u_vals = [args.u] if args.u is not None else U_SWEEP

    try:
        run_live_debate(
            output_dir=args.output_dir,
            lattice_keys=lattices,
            u_values=u_vals,
            proposer_model=args.proposer_model,
            adversary_model=args.adversary_model,
            env_file=args.env_file,
        )
    except LiveConfigurationError as error:
        print(f"REFUSED: {error.code}: {error}", file=sys.stderr)
        raise SystemExit(2)
    except RuntimeError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
