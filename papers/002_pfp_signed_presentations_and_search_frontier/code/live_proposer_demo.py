"""Live LLM Proposer & Exact Governor Demo for PFP Paper 002.

Prompts an LLM (via OpenRouter API) to propose diagonal sign gauges (alpha in {0, 1}^V)
or identify odd-cycle obstructions on signed presentation graphs.
All LLM proposals are strictly treated as untrusted and audited by the exact local governor
(verify_gauge / verify_odd_cycle).

Prerequisites:
  Your own OpenRouter key, from the OPENROUTER_API_KEY environment variable or
  from a file named with --env-file (see .env.example). No directory is
  searched for credentials. Without a key the demo refuses and exits nonzero;
  --mock runs a labelled offline check that makes no provider call.
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
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

if __package__:
    from .genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
    )
    from .native_sign_graph import (
        classify_sign_graph,
        verify_gauge,
        verify_odd_cycle,
    )
else:
    from genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
    )
    from native_sign_graph import (
        classify_sign_graph,
        verify_gauge,
        verify_odd_cycle,
    )

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"


def find_and_load_api_key(env_file: Optional[Path] = None) -> str:
    """Return OPENROUTER_API_KEY from the environment or one explicitly named file.

    Returns an empty string when neither supplies a usable key. No directory is
    searched, so a key is never picked up from an unrelated .env file.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key or env_file is None:
        return key
    try:
        lines = Path(env_file).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        print(f"[!] Cannot read --env-file {env_file}: {error}")
        return ""
    for line in lines:
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            val = line.split("=", 1)[1].strip().strip("'\"")
            if val and not val.startswith("your_"):
                return val
    return ""


def call_openrouter(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    temperature: float = 0.0,
    max_tokens: int = 800,
) -> str:
    """Call OpenRouter chat completions via standard library urllib."""
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
            "HTTP-Referer": "https://github.com/the-symbol-game/pfp-paper-002",
            "X-Title": "PFP Paper 002 Live Proposer",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter API HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error connecting to OpenRouter: {e.reason}") from e


def extract_json_block(text: str) -> Optional[dict]:
    """Extract a JSON object from LLM response text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    for m in matches:
        try:
            return json.loads(m.strip())
        except json.JSONDecodeError:
            continue

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(text[first:last + 1])
        except json.JSONDecodeError:
            pass

    return None


def run_live_challenge(
    vertices: Tuple[str, ...],
    edges: Tuple[SignedRewrite, ...],
    model: str,
    api_key: str,
    description: str,
) -> bool:
    print(f"\n--- Challenge: {description} ---")
    print(f"Vertices ({len(vertices)}): {vertices}")
    print(f"Edges ({len(edges)}): {[(e.source, e.target, 'odd (1)' if e.odd else 'even (0)') for e in edges]}")

    ground_truth = classify_sign_graph(vertices, edges)
    expected_type = "GAUGE" if isinstance(ground_truth, GaugeWitness) else "ODD_CYCLE"
    print(f"Ground Truth Oracle: {expected_type}")

    prompt = f"""You are an adversarial mathematical reasoning assistant evaluating a signed graph presentation for quantum Monte Carlo sign-gauge elimination.

Graph Vertices: {list(vertices)}
Signed Edges (rewrites):
{[{"source": e.source, "target": e.target, "odd": e.odd} for e in edges]}

Task:
Determine whether this signed presentation admits an exact Z2 diagonal sign gauge alpha in {{0, 1}}^V such that for every edge:
  alpha[source] XOR alpha[target] == edge.odd
Or whether it contains a frustrated odd-cycle obstruction.

You MUST respond strictly with a valid JSON object matching ONE of these formats:

If a valid gauge exists:
{{
  "claim": "GAUGE",
  "bits": [0, 1, ...],  // exactly {len(vertices)} integers (each 0 or 1) ordered matching vertices
  "explanation": "brief reasoning"
}}

If an odd-cycle obstruction exists:
{{
  "claim": "ODD_CYCLE",
  "cycle_steps": [
    {{"edge_index": 0, "departure": "{vertices[0]}", "arrival": "..."}},
    ...
  ],
  "explanation": "brief reasoning"
}}
"""

    print(f"Querying model '{model}' via OpenRouter...")
    t0 = time.time()
    try:
        reply = call_openrouter(
            messages=[
                {"role": "system", "content": "You are a precise discrete mathematics auditor. Always return clean, parseable JSON."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            api_key=api_key,
        )
        elapsed = time.time() - t0
        print(f"Received reply in {elapsed:.2f}s")
    except Exception as e:
        print(f"[!] OpenRouter query failed: {e}")
        return False

    parsed = extract_json_block(reply)
    if not parsed or not isinstance(parsed, dict):
        print(f"[!] Malformed LLM response: expected JSON object, got {type(parsed).__name__ if parsed else 'None'}:\n{reply[:300]}...")
        return False

    raw_claim = parsed.get("claim")
    if not isinstance(raw_claim, str):
        print(f"[!] Malformed LLM response: missing or non-string 'claim' field ({raw_claim!r})")
        return False
    claim = raw_claim.strip().upper()
    print(f"LLM Claim: {claim}")
    print(f"LLM Explanation: {parsed.get('explanation', 'None')}")

    if claim == "GAUGE":
        bits = parsed.get("bits")
        if not isinstance(bits, list):
            print(f"[X] REJECTED: 'bits' field must be a list, got {type(bits).__name__}")
            return False
        if len(bits) != len(vertices):
            print(f"[X] REJECTED: bits array length {len(bits)} does not match vertex count {len(vertices)}")
            return False
        for i, b in enumerate(bits):
            if type(b) is not int or b not in (0, 1):
                print(f"[X] REJECTED: bit at index {i} is not integer 0 or 1 (got {b!r} of type {type(b).__name__})")
                return False
        witness = GaugeWitness(vertices=vertices, bits=tuple(bits))
        is_valid = verify_gauge(vertices, edges, witness)
        if is_valid:
            print(f"[+] AUDIT PASSED: LLM proposed valid gauge witness bits={witness.bits}")
            return True
        else:
            print("[X] AUDIT FAILED: Proposed gauge violates parity constraint on one or more edges!")
            return False

    elif claim == "ODD_CYCLE":
        raw_steps = parsed.get("cycle_steps")
        if not isinstance(raw_steps, list):
            print(f"[X] REJECTED: 'cycle_steps' must be a list, got {type(raw_steps).__name__}")
            return False
        steps = []
        for i, s in enumerate(raw_steps):
            if not isinstance(s, dict):
                print(f"[X] REJECTED: cycle_step at index {i} is not a dictionary (got {s!r})")
                return False
            e_idx = s.get("edge_index")
            dep = s.get("departure")
            arr = s.get("arrival")
            if type(e_idx) is not int or not isinstance(dep, str) or not isinstance(arr, str):
                print(f"[X] REJECTED: malformed cycle_step at index {i}: edge_index={e_idx!r}, departure={dep!r}, arrival={arr!r}")
                return False
            if not (0 <= e_idx < len(edges)):
                print(f"[X] REJECTED: cycle_step edge_index {e_idx} out of range [0, {len(edges)-1}]")
                return False
            if dep not in vertices or arr not in vertices:
                print(f"[X] REJECTED: cycle_step vertices ({dep!r}, {arr!r}) not in vertex set")
                return False
            steps.append((e_idx, dep, arr))
        witness = OddCycleWitness(steps=tuple(steps))
        is_valid = verify_odd_cycle(vertices, edges, witness)
        if is_valid:
            print("[+] AUDIT PASSED: LLM provided valid odd cycle witness!")
            return True
        else:
            print("[X] AUDIT FAILED: Proposed cycle steps do not form a valid closed odd walk!")
            return False
    else:
        print(f"[X] REJECTED: Unknown claim type '{claim}'")
        return False


def run_live_demo(model: str = DEFAULT_MODEL, env_file: Optional[Path] = None) -> bool:
    print("=" * 72)
    print("LIVE PROPOSER & EXACT GOVERNOR DEMO (PAPER 002)")
    print("=" * 72)

    api_key = find_and_load_api_key(env_file)
    if not api_key:
        print("\nREFUSED: no OpenRouter key was supplied, so no live call was made.")
        print("To run the live demo with your own key, either export OPENROUTER_API_KEY or")
        print("copy .env.example to a private file, replace the placeholder, and pass it:")
        print("  py -3.12 code/run_demos.py --live --env-file .env")
        print("For a labelled offline check without a provider call, use:")
        print("  py -3.12 code/live_proposer_demo.py --mock")
        return False

    print(f"[*] API Key detected. Target Model: {model}")

    # Challenge 1: Frustration-free 4-cycle
    v1 = ("v0", "v1", "v2", "v3")
    e1 = (
        SignedRewrite("v0", "v1", 1),
        SignedRewrite("v1", "v2", 0),
        SignedRewrite("v2", "v3", 1),
        SignedRewrite("v0", "v3", 0),
    )
    res1 = run_live_challenge(v1, e1, model, api_key, "Gaugeable 4-Cycle (Product of Parities = Even)")

    # Challenge 2: Frustrated 3-cycle
    v2 = ("u0", "u1", "u2")
    e2 = (
        SignedRewrite("u0", "u1", 1),
        SignedRewrite("u1", "u2", 0),
        SignedRewrite("u2", "u0", 0),
    )
    res2 = run_live_challenge(v2, e2, model, api_key, "Frustrated 3-Cycle (Product of Parities = Odd)")

    print("\n" + "=" * 72)
    print("LIVE DEMO SUMMARY")
    print(f"  Challenge 1 Result: {'PASS' if res1 else 'FAIL/REFUSED'}")
    print(f"  Challenge 2 Result: {'PASS' if res2 else 'FAIL/REFUSED'}")
    print("=" * 72)
    return bool(res1 and res2)


def run_offline_mock() -> bool:
    print("\n--- Offline mock mode: no provider call; this is not a live result ---")
    v = ("v0", "v1", "v2")
    e = (
        SignedRewrite("v0", "v1", 1),
        SignedRewrite("v1", "v2", 0),
    )
    print("Mock Proposer: Suggests gauge bits (0, 1, 1)")
    witness = GaugeWitness(v, (0, 1, 1))
    valid = verify_gauge(v, e, witness)
    print(f"Local Governor Check: {'PASS' if valid else 'FAIL'}")
    return bool(valid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Proposer Demo for Paper 002")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenRouter model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--env-file", type=Path, help="File containing OPENROUTER_API_KEY=... (environment is read first)")
    parser.add_argument("--mock", action="store_true", help="Run the labelled offline check; no provider call")
    args = parser.parse_args()
    ok = run_offline_mock() if args.mock else run_live_demo(model=args.model, env_file=args.env_file)
    raise SystemExit(0 if ok else 1)
