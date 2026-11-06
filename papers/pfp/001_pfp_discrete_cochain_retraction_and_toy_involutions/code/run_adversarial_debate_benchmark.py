"""Recompute historical-label metrics and replay deposited proposals.

This module performs no provider calls. Historical labels are preserved evidence,
not independent physical ground truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from certificate_gate import BqnfCertificateGate

LATTICES = {
    "c5_pentagon": {"sites": list(range(5)), "bonds": [(0,1),(1,2),(2,3),(3,4),(4,0)]},
    "kagome_cluster": {"sites": list(range(6)), "bonds": [(0,1),(1,2),(2,0),(2,3),(3,4),(4,2),(4,5),(5,0),(0,4)]},
}
U_SWEEP = [-4, -2, 0, 2, 4]
TRACE_FILE = Path(__file__).resolve().parent.parent / "results" / "demo2_r7_adversarial_debate_1790210039.jsonl"


def load_records(trace_file=TRACE_FILE):
    rows = [json.loads(line) for line in Path(trace_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {(lattice, u) for lattice in LATTICES for u in U_SWEEP}
    keys = [(row["lattice_key"], row["u_val"]) for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Trace must contain exactly one record for every declared lattice/interaction condition")
    for row in rows:
        if type(row["proposer_hallucination"]) is not bool:
            raise ValueError("Historical target labels must be booleans")
        if row["adversary_critique"]["adversary_verdict"] not in {"CHALLENGE", "CONCUR"}:
            raise ValueError("Unknown adversary verdict")
    return rows


def summarize_records(rows):
    counts = Counter()
    trials = []
    for row in rows:
        label = row["proposer_hallucination"]
        challenge = row["adversary_critique"]["adversary_verdict"] == "CHALLENGE"
        counts[(label, challenge)] += 1
        lattice, u = row["lattice_key"], row["u_val"]
        gate = BqnfCertificateGate(lattice, {**LATTICES[lattice], "U": u, "t": 1})
        status, admitted, reason = gate.verify_proposal_item(row["proposer_move"])
        trials.append({
            "lattice": lattice, "U_over_t": u,
            "proposer_move": row["proposer_move"]["move_type"],
            "historical_proposer_status": row["proposer_status"],
            "historical_hallucination_label": label,
            "adversary_verdict": row["adversary_critique"]["adversary_verdict"],
            "adversary_counter": row["adversary_critique"]["counter_move"],
            "historical_terminal_state": row["terminal_state"],
            "current_replay_status": status, "current_replay_admitted": admitted,
            "current_replay_reason": reason,
        })
    tp, fp, tn, fn = counts[True, True], counts[False, True], counts[False, False], counts[True, False]

    def ratio(n, d):
        return n / d if d else None

    return {
        "round": "demo2_r7_adversarial_debate",
        "execution_mode": "offline_deposited_trace_replay",
        "label_basis": "historical verifier labels; not independent physics ground truth",
        "reported_proposer_model": "meta-llama/llama-3.1-8b-instruct",
        "reported_adversary_model": "deepseek/deepseek-chat",
        "total_trials": len(rows),
        "historical_positive_labels": tp + fn, "historical_negative_labels": tn + fp,
        "adversary_challenges": tp + fp, "adversary_concurrences": tn + fn,
        "adversary_true_positives": tp, "adversary_false_positives": fp,
        "adversary_true_negatives": tn, "adversary_false_negatives": fn,
        "adversary_challenge_precision": ratio(tp, tp + fp),
        "adversary_challenge_recall": ratio(tp, tp + fn),
        "adversary_classification_accuracy": ratio(tp + tn, len(rows)),
        "historical_terminal_states": dict(Counter(r["terminal_state"] for r in rows)),
        "current_replay_statuses": dict(Counter(t["current_replay_status"] for t in trials)),
        "trials": trials, "authority_effect": "None",
    }


def run_benchmark(offline_replay=True, live=False, trace_file=TRACE_FILE):
    if live or not offline_replay:
        raise ValueError("Live execution is not implemented in run_benchmark(); use live_adversarial_demo.py or CLI --live for live OpenRouter debate")
    receipt = summarize_records(load_records(trace_file))
    receipt["source_trace"] = Path(trace_file).name
    receipt["source_trace_sha256"] = hashlib.sha256(Path(trace_file).read_bytes()).hexdigest()
    print(json.dumps(receipt, indent=2))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Execute live debate with OpenRouter (requires OPENROUTER_API_KEY)")
    parser.add_argument("--output-dir", type=Path, help="New directory for the live trace and receipt (required with --live)")
    parser.add_argument("--env-file", type=Path, help="File containing OPENROUTER_API_KEY=... (environment is read first)")
    parser.add_argument("--write-receipt", type=Path, help="Where to write the offline replay receipt")
    args = parser.parse_args()
    if args.live:
        from live_adversarial_demo import run_live_debate
        run_live_debate(output_dir=args.output_dir, env_file=args.env_file)
    else:
        result = run_benchmark()
        if args.write_receipt:
            args.write_receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
