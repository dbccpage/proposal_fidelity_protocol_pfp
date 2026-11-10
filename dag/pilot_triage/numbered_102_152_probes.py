"""Bounded public toy checks of catalog owner limits; no dispatch or private data."""
from pathlib import Path
import copy
import importlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "workflows/tasks/certified_challenges"))
E58 = importlib.import_module("c058_straight_line_superoptimization.judge_packet.exact_checker")
I58 = importlib.import_module("c058_straight_line_superoptimization.judge_packet.independent_checker")
E59 = importlib.import_module("c059_sql_null_total_query_synthesis.judge_packet.exact_checker")
I59 = importlib.import_module("c059_sql_null_total_query_synthesis.judge_packet.independent_checker")
R60 = importlib.import_module("c060_self_verifying_checker_synthesis.reference_solver.checker")
I60 = importlib.import_module("c060_self_verifying_checker_synthesis.judge_packet.independent_checker")

case58 = {"case_id": "audit-public-singleton", "width": 32, "inputs": ["x"],
          "ops": [["z", "const", 0]] + [["dead" + str(i), "add", "x", 0] for i in range(5)],
          "out": "z", "target_len": 5}
candidate58 = {"case_id": case58["case_id"], "status": "SOLVED",
               "ops": [["d", "xor", "x", 42], ["n", "neg", "d"], ["o", "or", "d", "n"],
                       ["nz", "lshr", "o", 31], ["eq", "xor", "nz", 1]], "out": "eq"}
results = [{"id": "C058-32bit-sampling-false-accept", "case": case58, "candidate": candidate58,
            "first_checker": E58.verify_candidate(case58, candidate58),
            "second_checker": I58.check_candidate_indep(case58, candidate58),
            "counterexample": {"x": 42, "original": E58.execute_program(case58["ops"], "z", {"x": 42}, 32),
                               "candidate": E58.execute_program(candidate58["ops"], "eq", {"x": 42}, 32)}}]
assert results[0]["first_checker"][0] and results[0]["second_checker"][0]
assert results[0]["counterexample"]["original"] == 0 and results[0]["counterexample"]["candidate"] == 1

case59 = {"case_id": "audit-public-text-affinity", "schema": {"t": {"v": "TEXT"}},
          "spec": {"op": "select", "from": "t", "where": {"eq3": [{"col": "v"}, {"val": 1}]}},
          "protected": [], "test_databases": [{"t": [{"v": "1"}]}]}
candidate59 = {"case_id": case59["case_id"], "status": "SOLVED", "sql": "SELECT v FROM t WHERE v = 1",
               "preflight_sql": "SELECT 1 WHERE 0", "null_ledger": []}
results.append({"id": "C059-affinity-judge-disagreement", "case": case59, "candidate": candidate59,
                "first_checker": E59.verify_candidate(case59, candidate59),
                "second_checker": I59.independent_check(case59, candidate59)})
assert results[-1]["first_checker"][0] and not results[-1]["second_checker"][0]

case60 = {"d0": [["1"]], "omega": ["0"], "w": ["1"]}
cert60 = {"alpha": ["0"], "r": ["0"], "y": ["0"], "value": "0"}
for name, case, cert in [
    ("zero-column", {"d0": [[]], "omega": ["0"], "w": ["1"]}, dict(cert60, alpha=[])),
    ("trailing-newline", case60, dict(cert60, value="0\n")),
    ("non-string-value", case60, dict(cert60, value=0)),
    ("unicode-digit", case60, dict(cert60, value="²")),
]:
    result = {"id": "C060-" + name, "case": case, "certificate": cert,
              "reference": R60.check(case, cert)}
    try:
        result["independent"] = I60.evaluate_phi1_independent(case, cert)
    except Exception as error:
        result["independent_exception"] = type(error).__name__ + ": " + str(error)
    results.append(result)
assert results[2]["reference"]["verdict"] == "ACCEPT" and results[2]["independent"][0] == "ACCEPT"
assert results[3]["reference"]["verdict"] == "ACCEPT" and results[3]["independent"][0] == "REJECT"
assert results[4]["reference"]["code"] == "SCHEMA" and results[4]["independent"][1] == "NONCANONICAL_RATIONAL"
assert results[5]["independent_exception"].startswith("ValueError")
out = {"status": "six_public_toy_boundary_probes_reproduced", "python": sys.version,
       "model_calls": 0, "private_or_hidden_data_reads": 0, "results": results}
Path(__file__).with_name("numbered_102_152_probe_results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
