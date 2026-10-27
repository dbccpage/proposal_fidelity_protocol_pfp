# AuthorityEffect: None.
"""
Aggregates C041 run records from one run folder into a table of counts.

Correction (2026-09-29): an earlier version of this script wrote fixed "findings" text (pass
rates, cost ratios and routing recommendations) into every report regardless of the records
it read, and no raw prompts, replies or per-case results were retained for those rows. The
script now reports counts from the records it is given and draws no conclusions.
"""

from __future__ import annotations

import json
from pathlib import Path


def synthesize_report(runs_dir: Path) -> Path:
    """Reads c041 arm records (M*.json) from runs_dir and writes c041_matrix_report.md there."""
    runs_dir = Path(runs_dir)
    records = []
    for p in sorted(runs_dir.glob("M*.json")) + sorted(runs_dir.glob("c041_M*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["filename"] = p.name
                records.append(data)
        except Exception as e:
            print("Error reading", p, e)

    def get_tier(model_id: str) -> str:
        if "8b" in model_id:
            return "8B"
        elif "70b" in model_id:
            return "70B"
        elif "deepseek" in model_id:
            return "500B MoE"
        elif "gpt-4o" in model_id:
            return "Frontier"
        return "Other"

    lines = [
        "# C041 run records: counts",
        "",
        "**Domain:** `e_formal_math` (C041 Lean 4 Finite Lemma Proofs)  ",
        "**Host Oracle:** Read each arm's recorded `lean_version` and actual checker outcome.  ",
        "**AuthorityEffect:** None  ",
        "",
        "## Counts per arm",
        "",
        "| Tier | Model | Intervention Method | Pass Rate | Billed Cost ($) | Cost / Verified Proof ($) | Avg Prompt Tok | Avg Compl Tok |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in records:
        tier = get_tier(r.get("model", ""))
        model = r.get("model", "")
        method = r.get("method", "")
        passed = r.get("passed_cases", 0)
        total = r.get("total_cases", 10)
        rate_pct = (passed / total * 100) if total > 0 else 0
        rate = f"{passed}/{total} ({rate_pct:.0f}%)"
        cost_val = r.get("total_cost_usd")
        cost = f"${cost_val:.5f}" if cost_val is not None else "UNKNOWN"
        subtotal = r.get("total_cost_known_subtotal_usd")
        if cost_val is None and subtotal is not None:
            cost += f" (known subtotal ${subtotal:.5f})"
        cpp_val = r.get("cost_per_verified_success_usd")
        cpp = f"${cpp_val:.5f}" if cpp_val is not None else "N/A"
        p_tok = int((r.get("total_prompt_tokens") or 0) / max(1, total))
        c_tok = int((r.get("total_completion_tokens") or 0) / max(1, total))
        lines.append(
            f"| {tier} | `{model}` | **{method}** | {rate} | {cost} | {cpp} | {p_tok} | {c_tok} |"
        )

    lines.extend(
        [
            "",
            "This report states counts from the records above only and draws no conclusions from them.",
        ]
    )

    out_md = "\n".join(lines)
    report_file = runs_dir / "c041_matrix_report.md"
    report_file.write_text(out_md, encoding="utf-8")
    print(f"Successfully generated unified report at {report_file}")
    return report_file


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: synthesize_matrix_report.py <run folder>")
    synthesize_report(Path(sys.argv[1]))
