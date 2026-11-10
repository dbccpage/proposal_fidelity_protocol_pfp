"""Audit retained report bytes and recount Tables 3 and 4 without a model call.

Table 3 recounts recorded acceptance flags, not fresh certificate verification.
Table 4 recounts the author's categories and an earlier checker replay record.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "historical_evidence"
MODELS = (
    "stealth/space-bunny-alpha",
    "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
)


def load(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def verify_source_bytes() -> int:
    """Check the SHA-256 and Git blob SHA of every bundled historical file."""
    files = load("provenance.json")["files"]
    if len({entry["file"] for entry in files}) != len(files):
        raise ValueError("duplicate historical source path")
    for entry in files:
        data = (EVIDENCE / entry["file"]).read_bytes()
        git_digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if (hashlib.sha256(data).hexdigest(), git_digest) != (
            entry["sha256"], entry["git_blob_sha"]
        ):
            raise ValueError(f"historical source hash mismatch: {entry['file']}")
    return len(files)


def count_model(result: dict) -> tuple[int, tuple[str, ...]]:
    """Reject inconsistent summary counts or panels before reporting a count."""
    records = result.get("records", result.get("results"))
    if not isinstance(records, list):
        raise ValueError("a model report must retain a list of case records")
    ids = tuple(record["case_id"] for record in records)
    if len(ids) != 10 or len(set(ids)) != 10:
        raise ValueError("a reported model panel must have ten distinct case identifiers")
    # C045's 8B report records one JSON_ERROR without an acceptance flag.
    # That explicit parse failure is an unaccepted response, not a missing success.
    flags = [record.get("passed", record.get("pass",
             False if record.get("status") == "JSON_ERROR" else None)) for record in records]
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("acceptance flags must be booleans")
    total = sum(flags)
    if result["passed"] != total:
        raise ValueError("summary passed count differs from case flags")
    if "total" in result and result["total"] != len(ids):
        raise ValueError("summary panel size differs from case records")
    return total, ids


def table3() -> dict[str, tuple[int, ...]]:
    rows = {}
    for name in ("c045", "c046", "c047", "c048", "c049_panel_b", "c050_run_1", "c050_run_2"):
        report = load(name + ".json")
        models = {result["model_id"]: result for result in report["models"].values()}
        if set(models) != set(MODELS) or report["total_cases"] != 10:
            raise ValueError("unexpected models or panel size")
        counted = [count_model(models[model]) for model in MODELS]
        if any(ids != counted[0][1] for _, ids in counted):
            raise ValueError("models were scored on different panels within a table row")
        rows[name] = tuple(total for total, _ in counted)
    models = {}
    for index in range(3):
        report = load(f"c049_panel_a_{index}.json")
        models[report["model"]] = report
    if set(models) != set(MODELS):
        raise ValueError("unexpected C049 panel A models")
    counted = [count_model(models[model]) for model in MODELS]
    if any(ids != counted[0][1] for _, ids in counted):
        raise ValueError("C049 panel A models were scored on different panels")
    rows["c049_panel_a"] = tuple(total for total, _ in counted)
    return dict(sorted(rows.items()))


def table4() -> dict[str, tuple[int, int, int, int]]:
    rows = {}
    for name, panel in load("formal_math_baselines.json")["challenges"].items():
        ids = set(panel["panel_case_ids"])
        if len(ids) != 10 or panel["panel_size"] != 10:
            raise ValueError("baseline panel must have ten distinct identifiers")
        categories = panel["identifier_reading_ids"]
        flat = [identifier for category in categories.values() for identifier in category]
        if len(flat) != 10 or set(flat) != ids:
            raise ValueError("author identifier categories must partition the panel")
        counts = tuple(len(categories[key]) for key in ("verdict_or_answer", "object", "neither"))
        if counts != tuple(panel["identifier_reading"][key] for key in
                           ("verdict_or_answer", "object", "neither")):
            raise ValueError("identifier count differs from author annotation")
        for answer in panel["trivial_answers"].values():
            passed = answer["cases_passed"]
            if len(set(passed)) != len(passed) or not set(passed) <= ids:
                raise ValueError("invalid baseline passed case list")
            if answer["both_accept"] != len(passed):
                raise ValueError("baseline count differs from recorded passed cases")
            if not 0 <= answer["both_accept"] <= min(
                answer["exact_checker_accepts"], answer["second_checker_accepts"]
            ) <= 10:
                raise ValueError("inconsistent baseline checker counts")
        best = max(answer["both_accept"] for answer in panel["trivial_answers"].values())
        if panel["best_trivial_both_accept"] != best:
            raise ValueError("best baseline count differs from recorded candidates")
        rows[name] = (*counts, best)
    return rows


def verify_c017_extraction() -> int:
    """Compare all retained extraction fields with the original C017 reports."""
    claims = json.loads((ROOT / "code/data/c017/model_claims.json").read_text())
    checked = 0
    for run in claims["runs"]:
        source_path = EVIDENCE / Path(run["source"]).name
        data = source_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != run["report_sha256"]:
            raise ValueError("C017 source report digest differs from extraction provenance")
        source = json.loads(data)
        records = {record["case_id"]: record for record in source["cases_evaluated"]}
        if len(records) != 5 or len(run["cases"]) != 5:
            raise ValueError("C017 run must contain five distinct cases")
        if (source["model"], source["timestamp_utc"]) != (run["model"], run["timestamp_utc"]):
            raise ValueError("C017 run metadata mismatch")
        for entry in run["cases"]:
            record = records[entry["harness_case_id"]]
            if entry["harness_expected_verdict"] != record["expected_verdict"]:
                raise ValueError("C017 expected verdict mismatch")
            if run["run"] in ("arm1", "arm2"):
                result = record["baseline" if run["run"] == "arm1" else "immune_assisted"]
                claim = None
            else:
                result = record
                claim = {key: value for key, value in record["solution"].items()
                         if key not in ("scratchpad", "raw")}
            wanted = (result["verdict"], result["passed"], result["reason"],
                      result["meta"]["out_tokens"], claim)
            actual = tuple(entry[key] for key in ("recorded_verdict", "recorded_passed",
                                                  "recorded_reason", "completion_tokens", "claim"))
            if actual != wanted:
                raise ValueError(f"C017 extraction mismatch: {run['run']} {entry['case']}")
            checked += 1
    return checked


def main() -> int:
    print(f"Source custody: {verify_source_bytes()} original historical files match both hashes")
    print(f"C017 extraction: {verify_c017_extraction()} recorded case entries match source reports")
    print("Table 3: recorded acceptances, out of ten; model order: " + ", ".join(MODELS))
    for name, counts in table3().items():
        print(name, *counts)
    print("Table 4: author categories (verdict/object/neither), best earlier baseline count")
    for name, counts in table4().items():
        print(name, *counts)
    print("Scope: offline recount only; no model call and no fresh C045-C050 checker execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
