"""Per-package summaries and the cross-package aggregate.

Definitions used throughout:

- A case is *solvable by reference* when the package's reference solver
  returned an answer whose status is not a refusal status and the package's
  own gate accepted it.
- A case is *solvable by witness* when the gate accepted some non-refusal
  answer on it (the reference answer, a participant example's answer, or a
  constant reference answer): the gate itself then certified a solution.
- *Solvable* is the union of the two. A refusal accepted on a solvable case
  is an escape: the gate passed a refusal where it had certified a solution.
- A *fixed strategy's score* is the number of cases on which one unchanging
  answer template passes the gate. The best fixed strategy is the trivial
  baseline that a results table should report beside any model.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from omega_engine_woland.tests.pilots.judge_packet_audit.static_analysis import REFUSAL_STATUS_WORDS

REFUSAL_FAMILIES = ("abstain", "refuse", "refuse_template", "case_derived")
TEMPLATE_FAMILIES = ("template_example", "constant_reference")
WITNESS_FAMILIES = ("template_example", "constant_reference")


def outcome(calls: dict[str, Any], role: str) -> str | None:
    value = calls.get(role)
    return value[0] if value else None


def _status(template: Any) -> str | None:
    if isinstance(template, dict) and isinstance(template.get("status"), str):
        return template["status"]
    return None


def is_non_refusal_answer(template: Any) -> bool:
    return (
        isinstance(template, dict)
        and bool(template)
        and _status(template) not in REFUSAL_STATUS_WORDS
    )


def summarize(
    desc: dict[str, Any], rows: list[dict[str, Any]], strategies: list[dict[str, Any]]
) -> dict[str, Any]:
    roles = [c["role"] for c in desc["checkers"]]
    templates = {s["id"]: s["template"] for s in strategies}
    ref_rows = {r["case"]: r for r in rows if r["kind"] == "reference"}
    returned = [
        c["key"]
        for c in desc["cases"]
        if ref_rows.get(c["key"], {}).get("solver", {}).get("outcome") == "RETURNED"
    ]
    ref_gate_accept = [k for k in returned if outcome(ref_rows[k]["calls"], "gate") == "ACCEPT"]
    by_reference = {
        k
        for k in ref_gate_accept
        if ref_rows[k]["solver"].get("status") not in REFUSAL_STATUS_WORDS
    }
    by_witness = set()
    for row in rows:
        if (
            row["kind"] == "responder"
            and row["family"] in WITNESS_FAMILIES
            and outcome(row["calls"], "gate") == "ACCEPT"
        ):
            if is_non_refusal_answer(templates.get(row["responder"])):
                by_witness.add(row["case"])
    solvable = by_reference | by_witness
    per_strategy: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["kind"] != "responder":
            continue
        entry = per_strategy.setdefault(
            row["responder"],
            {
                "family": row["family"],
                "status": _status(templates.get(row["responder"])),
                "gate_accept": 0,
                "gate_accept_on_solvable": 0,
                "non_verdict": 0,
                **{f"{r}_accept": 0 for r in roles},
                **{f"{r}_accept_on_solvable": 0 for r in roles},
            },
        )
        gate = outcome(row["calls"], "gate")
        if gate == "ACCEPT":
            entry["gate_accept"] += 1
            if row["case"] in solvable:
                entry["gate_accept_on_solvable"] += 1
        elif gate != "REJECT":
            entry["non_verdict"] += 1
        for role in roles:
            if outcome(row["calls"], role) == "ACCEPT":
                entry[f"{role}_accept"] += 1
                if row["case"] in solvable:
                    entry[f"{role}_accept_on_solvable"] += 1

    def best(families: tuple[str, ...], key: str) -> dict[str, Any]:
        candidates = [(v[key], sid) for sid, v in per_strategy.items() if v["family"] in families]
        if not candidates:
            return {"count": 0, "strategy": None}
        count, sid = sorted(candidates, key=lambda t: (-t[0], t[1]))[0]
        return {"count": count, "strategy": sid}

    def union(families: tuple[str, ...], role: str) -> int:
        hit = set()
        for row in rows:
            if (
                row["kind"] == "responder"
                and row["family"] in families
                and outcome(row["calls"], role) == "ACCEPT"
            ):
                if row["case"] in solvable and not is_non_refusal_answer(
                    templates.get(row["responder"])
                ):
                    hit.add(row["case"])
        return len(hit)

    empty = per_strategy.get("empty", {})
    abstain_id = next((s["id"] for s in strategies if s["family"] == "abstain"), None)
    abstain = per_strategy.get(abstain_id, {}) if abstain_id else {}
    type_confusion: dict[str, dict[str, int]] = {}
    for row in rows:
        if row["kind"] != "type_confusion":
            continue
        ref_ok = outcome(ref_rows.get(row["case"], {}).get("calls", {}), "gate") == "ACCEPT"
        entry = type_confusion.setdefault(
            row["responder"],
            {
                "applicable": 0,
                "applicable_ref_accepted": 0,
                "gate_accept": 0,
                **{f"{r}_accept": 0 for r in roles},
            },
        )
        entry["applicable"] += 1
        if ref_ok:
            entry["applicable_ref_accepted"] += 1
            if outcome(row["calls"], "gate") == "ACCEPT":
                entry["gate_accept"] += 1
            for role in roles:
                if outcome(row["calls"], role) == "ACCEPT":
                    entry[f"{role}_accept"] += 1
    mutation_rows = [r for r in rows if r["kind"] == "mutation"]
    mutation = {
        "replayed": len(mutation_rows),
        "gate_accept": sum(1 for r in mutation_rows if outcome(r["calls"], "gate") == "ACCEPT"),
        "any_checker_accept": sum(
            1 for r in mutation_rows if any(outcome(r["calls"], role) == "ACCEPT" for role in roles)
        ),
        "non_verdict": sum(
            1 for r in mutation_rows if outcome(r["calls"], "gate") not in ("ACCEPT", "REJECT")
        ),
    }
    non_verdict = Counter()
    for row in rows:
        for role, value in row.get("calls", {}).items():
            if value and value[0] not in ("ACCEPT", "REJECT"):
                non_verdict[f"{row['kind']}:{role}:{value[0]}"] += 1
    wire_form = type_confusion.pop(
        "json_roundtrip", {"applicable": 0, "applicable_ref_accepted": 0, "gate_accept": 0}
    )
    return {
        "cases": len(desc["cases"]),
        "reference_returned": len(returned),
        "reference_gate_accept": len(ref_gate_accept),
        "reference_per_checker_accept": {
            r: sum(1 for k in returned if outcome(ref_rows[k]["calls"], r) == "ACCEPT")
            for r in roles
        },
        "solvable_by_reference": len(by_reference),
        "solvable_by_witness": len(by_witness),
        "solvable_cases": len(solvable),
        "strategies": len(strategies),
        "refusal": {
            "best_fixed_overall": best(REFUSAL_FAMILIES, "gate_accept"),
            "best_fixed_on_solvable": best(REFUSAL_FAMILIES, "gate_accept_on_solvable"),
            "union_on_solvable": union(REFUSAL_FAMILIES, "gate"),
            "per_checker_union_on_solvable": {r: union(REFUSAL_FAMILIES, r) for r in roles},
            "per_checker_best_fixed_on_solvable": {
                r: best(REFUSAL_FAMILIES, f"{r}_accept_on_solvable") for r in roles
            },
        },
        "template": {
            "best_fixed_overall": best(TEMPLATE_FAMILIES, "gate_accept"),
            "best_fixed_on_solvable": best(TEMPLATE_FAMILIES, "gate_accept_on_solvable"),
        },
        "empty": {
            "gate_accept": empty.get("gate_accept", 0),
            "per_checker_accept": {r: empty.get(f"{r}_accept", 0) for r in roles},
        },
        "abstain": {
            "strategy": abstain_id,
            "gate_accept": abstain.get("gate_accept", 0),
            "gate_accept_on_solvable": abstain.get("gate_accept_on_solvable", 0),
        },
        "type_confusion": type_confusion,
        "reference_wire_form": wire_form,
        "mutation_replay": mutation,
        "non_verdict_outcomes": dict(sorted(non_verdict.items())),
        "per_strategy": per_strategy,
        "semantic": _semantic(rows, strategies),
    }


def _semantic(rows: list[dict[str, Any]], strategies: list[dict[str, Any]]) -> dict[str, Any]:
    """Per semantic mutant: cases where it applies, gate accepts, and verdicts contrary to expectation."""
    expected = {s["id"]: s.get("expected") for s in strategies if s.get("family") == "semantic"}
    out: dict[str, Any] = {}
    for row in rows:
        if row["kind"] != "responder" or row["responder"] not in expected:
            continue
        entry = out.setdefault(
            row["responder"],
            {
                "expected": expected[row["responder"]],
                "applicable": 0,
                "gate_accept": 0,
                "contrary": 0,
            },
        )
        gate = outcome(row["calls"], "gate")
        entry["applicable"] += 1
        if gate == "ACCEPT":
            entry["gate_accept"] += 1
        if gate != entry["expected"]:
            entry["contrary"] += 1
    return out


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    packages = []
    for rec in records:
        s = rec["summary"]
        dep = rec["dependence"]["per_checker"]
        cust = rec["custody"]
        man = cust["manifest"]
        leak = rec["leakage"]
        interp: Counter[str] = Counter()
        inline_flagged = 0
        for lint in leak["runner_files"].values():
            for item in lint.get("prompt_interpolations", []):
                interp.update(item["kinds"])
            inline_flagged += sum(
                1
                for c in lint.get("inline_cases", [])
                if c["verdict_words"] or c["answer_vocabulary_words"] or c["answer_bearing_fields"]
            )
        packages.append(
            {
                "package_id": rec["package_id"],
                "shape": rec["descriptor"]["shape"],
                "checkers": len(rec["descriptor"]["checkers"]),
                "cases": s["cases"],
                "reference_returned": s["reference_returned"],
                "reference_gate_accept": s["reference_gate_accept"],
                "solvable_cases": s["solvable_cases"],
                "refusal_best_fixed_overall": s["refusal"]["best_fixed_overall"]["count"],
                "refusal_best_fixed_strategy": s["refusal"]["best_fixed_overall"]["strategy"],
                "refusal_best_fixed_on_solvable": s["refusal"]["best_fixed_on_solvable"]["count"],
                "refusal_union_on_solvable": s["refusal"]["union_on_solvable"],
                "refusal_per_checker_union_on_solvable": s["refusal"][
                    "per_checker_union_on_solvable"
                ],
                "empty_gate_accept": s["empty"]["gate_accept"],
                "empty_per_checker_accept": s["empty"]["per_checker_accept"],
                "abstain_gate_accept": s["abstain"]["gate_accept"],
                "abstain_gate_accept_on_solvable": s["abstain"]["gate_accept_on_solvable"],
                "template_best_fixed_overall": s["template"]["best_fixed_overall"]["count"],
                "type_confusion_gate_accept": {
                    k: v["gate_accept"] for k, v in sorted(s["type_confusion"].items())
                },
                "reference_wire_form_applicable": s["reference_wire_form"][
                    "applicable_ref_accepted"
                ],
                "reference_wire_form_gate_reject": s["reference_wire_form"][
                    "applicable_ref_accepted"
                ]
                - s["reference_wire_form"]["gate_accept"],
                "dependence_classes": {role: d["class"] for role, d in sorted(dep.items())},
                "checkers_share_one_module": rec["dependence"]["checkers_share_one_module"],
                "manifest_counts": man["counts"] if man and "counts" in man else None,
                "commitment_timing": cust["commitment_timing"]["class"],
                "mutation_entries": rec["mutation_inventory"]["entries"],
                "mutation_distinct_pairs": rec["mutation_inventory"]["distinct_case_answer_pairs"],
                "mutation_gate_accept": s["mutation_replay"]["gate_accept"],
                "case_ids_naming_own_answer": sum(
                    1 for c in leak["per_case"] if c["id"] and c["id"]["names_own_answer"]
                ),
                "case_ids_with_verdict_words": sum(
                    1 for c in leak["per_case"] if c["id"] and c["id"]["verdict_words"]
                ),
                "cases_with_answer_bearing_fields": sum(
                    1
                    for c in leak["per_case"]
                    if any(
                        f["value_shares_answer_tokens"] or f["named_answer_field"]
                        for f in c["fields"]
                    )
                ),
                "case_ids_with_category_hints": sum(
                    1 for c in leak["per_case"] if c["id"] and c["id"]["category_hints"]
                ),
                "template_accepted_where_reference_differs": len(
                    s.get("template_accepted_where_reference_differs", [])
                ),
                "semantic": s.get("semantic", {}),
                "judge_cases_equal_to_examples": len(leak["example_duplicates"]),
                "judge_cases_equal_to_examples_that_ship_answers": sum(
                    1 for d in leak["example_duplicates"] if d["example_ships_answer"]
                ),
                "runner_prompt_interpolations": dict(sorted(interp.items())),
                "runner_inline_cases_flagged": inline_flagged,
                "pass_to_master_receipts": rec["receipts"]["pass_to_master"],
                "reference_import_error": rec.get("reference_import_error"),
                "execution_notes": rec["execution_notes"],
            }
        )
    return {"packages": packages, "totals": totals(packages)}


def totals(packages: list[dict[str, Any]]) -> dict[str, Any]:
    def count(pred: Any) -> int:
        return sum(1 for p in packages if pred(p))

    return {
        "packages": len(packages),
        "packages_reference_accepted_somewhere": count(lambda p: p["reference_gate_accept"] > 0),
        "packages_reference_import_error": count(lambda p: p["reference_import_error"] is not None),
        "packages_refusal_accepted_on_a_solvable_case": count(
            lambda p: p["refusal_union_on_solvable"] > 0
        ),
        "packages_empty_object_passes_gate": count(lambda p: p["empty_gate_accept"] > 0),
        "packages_empty_object_passes_some_checker": count(
            lambda p: any(v > 0 for v in p["empty_per_checker_accept"].values())
        ),
        "packages_type_confusion_passes_gate": count(
            lambda p: any(v > 0 for v in p["type_confusion_gate_accept"].values())
        ),
        "packages_with_answer_key_checker": count(
            lambda p: "ANSWER_KEY" in p["dependence_classes"].values()
        ),
        "packages_with_checker_importing_other_checker": count(
            lambda p: "IMPORTS_OTHER_CHECKER" in p["dependence_classes"].values()
        ),
        "packages_with_checker_sharing_reference_code": count(
            lambda p: "SHARES_REFERENCE_CODE" in p["dependence_classes"].values()
        ),
        "packages_with_both_checkers_import_independent": count(
            lambda p: (
                p["checkers"] >= 2
                and all(v == "NO_IMPORT_DEPENDENCE" for v in p["dependence_classes"].values())
            )
        ),
        "packages_with_manifest": count(lambda p: p["manifest_counts"] is not None),
        "packages_manifest_with_crlf_or_unmatched_entries": count(
            lambda p: (
                p["manifest_counts"] is not None
                and (p["manifest_counts"]["CRLF"] + p["manifest_counts"]["NEITHER"]) > 0
            )
        ),
        "packages_without_judge_commitment_record": count(
            lambda p: p["commitment_timing"] == "NO_JUDGE_COMMITMENT_RECORD"
        ),
        "packages_commitment_added_with_receipt": count(
            lambda p: p["commitment_timing"] == "COMMITMENT_ADDED_WITH_RECEIPT"
        ),
        "mutation_entries": sum(p["mutation_entries"] for p in packages),
        "mutation_distinct_pairs": sum(p["mutation_distinct_pairs"] for p in packages),
        "mutations_passing_gate": sum(p["mutation_gate_accept"] for p in packages),
        "packages_with_case_ids_naming_own_answer": count(
            lambda p: p["case_ids_naming_own_answer"] > 0
        ),
        "packages_with_case_ids_with_verdict_words": count(
            lambda p: p["case_ids_with_verdict_words"] > 0
        ),
        "packages_with_answer_bearing_fields": count(
            lambda p: p["cases_with_answer_bearing_fields"] > 0
        ),
        "packages_with_judge_cases_equal_to_examples": count(
            lambda p: p["judge_cases_equal_to_examples"] > 0
        ),
        "judge_cases_equal_to_examples": sum(p["judge_cases_equal_to_examples"] for p in packages),
        "judge_cases_equal_to_examples_that_ship_answers": sum(
            p["judge_cases_equal_to_examples_that_ship_answers"] for p in packages
        ),
        "packages_with_judge_cases_equal_to_examples_that_ship_answers": count(
            lambda p: p["judge_cases_equal_to_examples_that_ship_answers"] > 0
        ),
        "packages_with_prompt_interpolating_case_id": count(
            lambda p: p["runner_prompt_interpolations"].get("case_id", 0) > 0
        ),
        "packages_with_pass_to_master_receipt": count(lambda p: p["pass_to_master_receipts"] > 0),
    }
