"""Check differing canonical presentations through sealed bijection witnesses."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("_paper011_g03_key_bridge_port", PAPER / "code/genesis_g03_replay.py")
if spec is None or spec.loader is None:
    raise ValueError("MISSING_EXPLICIT_G03_PORT")
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)
AREA = replay.AREA


def normalized(value):
    return json.loads(replay.wire(value))


def key_regime(modules: dict, key: list):
    if len(key) != 5 or type(key[0]) is not int or not 1 <= key[0] <= 25:
        raise ValueError("MALFORMED_CANONICAL_KEY")
    n, forms, insts, rules, reqs = key
    model = modules["model"]
    history = []
    for i in range(n):
        token = f"G03:key-position:{i}"
        history += [model.Supply(token), model.AdmitDatum(token)]
    history += [model.AdmitForm(arity) for arity in forms]
    history += [model.AdmitInst(form, tuple(args)) for form, args in insts]
    history += [model.AdmitRuleAll(form) for form in rules]
    history += [model.Impose(*pair) for pair in reqs]
    regime = model.replay(history)
    identity = modules["iso"].serialize(regime, tuple(range(n)), tuple(range(len(forms))))
    if normalized(identity) != key:
        raise ValueError("CANONICAL_KEY_IS_NOT_VALID_SERIALIZED_STATE")
    return regime


def verify_witness(modules: dict, record: dict) -> list:
    regime = key_regime(modules, record["native_key"])
    pi, phi = record["data_bijection"], record["form_bijection"]
    if sorted(pi) != list(range(regime.n_data())) or sorted(phi) != list(range(len(regime.forms))):
        raise ValueError("KEY_BRIDGE_NOT_A_BIJECTION")
    key = normalized(modules["iso"].serialize(regime, pi, phi))
    if key != record["sealed_key"]:
        raise ValueError("KEY_BRIDGE_SERIALIZE_WITNESS_FAILED")
    if replay.sha(replay.wire(record["native_key"])) != record["native_key_sha256"]:
        raise ValueError("KEY_BRIDGE_NATIVE_BYTES_CHANGED")
    return key


def build_witnesses(modules: dict, response: dict) -> list:
    records = {}
    for row in response["calls"]:
        keys = [row["base_canonical_key"], *(c["key"] for c in row["classes"])]
        for key in keys:
            identity = replay.wire(key)
            if identity in records:
                continue
            regime = key_regime(modules, key)
            sealed, pi, phi = modules["iso"].canonical_witness(regime)
            record = {"native_key": key, "native_key_sha256": replay.sha(identity),
                      "sealed_key": normalized(sealed), "data_bijection": list(pi), "form_bijection": list(phi)}
            verify_witness(modules, record)
            records[identity] = record
            if len(records) % 1024 == 0:
                print(f"G03 checked sealed key witnesses: {len(records)}", flush=True)
    return [records[key] for key in sorted(records)]


def delta(modules: dict, items: list, pi: list | None = None):
    candidates = modules["candidates"]
    result = []
    for item in items:
        kind = item["kind"]
        if kind == "datum" and set(item) == {"kind"}:
            result.append(candidates.NewDatum())
        elif kind == "form" and set(item) == {"kind", "arity"}:
            result.append(candidates.NewForm(item["arity"]))
        elif kind == "rule_all" and set(item) == {"kind", "form"}:
            result.append(candidates.NewRuleAll(item["form"]))
        elif kind == "inst" and set(item) == {"kind", "form", "args"}:
            args = tuple(pi[a] if pi is not None and a < len(pi) else a for a in item["args"])
            result.append(candidates.NewInst(item["form"], args))
        else:
            raise ValueError("MALFORMED_CANDIDATE_BYTES")
    canonical = candidates.canonical_delta(result)
    if pi is None and modules["engine"].delta_json_items(canonical) != items:
        raise ValueError("CANDIDATE_NOT_CANONICALLY_ORDERED")
    return canonical


def check(modules: dict, cases: list, response: dict, reference: list, witnesses: list) -> None:
    if response["schema"] != "paper011.g03-native-response.v1" or response["adapter_id"] != replay.adapter.ADAPTER_ID:
        raise ValueError("NATIVE_SCHEMA_OR_ADAPTER_CHANGED")
    replay.check_calls(cases, response["calls"])
    mapping = {}
    for record in witnesses:
        identity = replay.wire(record["native_key"])
        if identity in mapping:
            raise ValueError("DUPLICATED_KEY_BRIDGE_WITNESS")
        mapping[identity] = verify_witness(modules, record)
    expected = {row["id"]: row for row in reference}
    native_base = {row["id"]: row for row in response["calls"] if row["variant"] == "base"}
    by_case = {row["id"]: row for row in cases}
    cached = {}
    candidates, engine = modules["candidates"], modules["engine"]
    for number, original in enumerate(response["calls"]):
        row = copy.deepcopy(original)
        case = by_case[row["id"]]
        base_id = row["id"].rsplit(":", 1)[0] + ":base"
        want = expected[base_id]
        if row["variant"] != "base":
            control_base = native_base[base_id]
            if any(row[key] != control_base[key] for key in ("base_canonical_key", "cost", "raw_count", "weak", "strong")):
                raise ValueError("NATIVE_RELABEL_INVARIANCE_FAILED")
            if [(c["key"], c["size"], c["fresh_mark"]) for c in row["classes"]] != [(c["key"], c["size"], c["fresh_mark"]) for c in control_base["classes"]]:
                raise ValueError("NATIVE_RELABEL_CLASS_INVARIANCE_FAILED")
        identity = (row["n"], row["reading"], row["variant"])
        if identity not in cached:
            cached[identity] = replay.regime(modules, case["state"])
        base = cached[identity]
        pi = replay.adapter.reversal(row["n"], row["reading"], base.n_data()) if row["variant"] == "reversal" else None
        row["base_canonical_key"] = mapping[replay.wire(row["base_canonical_key"])]
        for entry in row["classes"]:
            if entry["size"] != len(entry["members"]) or entry["representative"] != entry["members"][0]:
                raise ValueError("NATIVE_CLASS_MEMBER_CERTIFICATE_MISMATCH")
            entry["key"] = mapping[replay.wire(entry["key"])]
            members = [delta(modules, member) for member in entry["members"]]
            if any(not candidates.response_valid_naive(base, tuple(case["target"]), member) for member in members):
                raise ValueError("SEALED_NAIVE_CANDIDATE_CERTIFICATE_FAILED")
            fresh = any(replay.adapter.fresh_mark(base, tuple(case["target"]), member, candidates) for member in members)
            if entry["fresh_mark"] != fresh:
                raise ValueError("PREREGISTERED_FRESH_MARK_PREDICATE_CHANGED")
            transformed = sorted((delta(modules, member, pi) for member in entry["members"]), key=candidates._delta_key)
            entry["members"] = [engine.delta_json_items(member) for member in transformed]
            entry["representative"] = entry["members"][0]
        row["classes"].sort(key=lambda entry: entry["key"])
        transformed_raw = sorted((delta(modules, member, pi) for member in row["raw_deltas"]), key=candidates._delta_key)
        row["raw_deltas"] = [engine.delta_json_items(member) for member in transformed_raw]
        row.update({key: want[key] for key in ("id", "variant", "target")})
        if row != want:
            raise ValueError("SOURCE_NATIVE_CERTIFICATE_DISAGREEMENT_AFTER_BIJECTION:" + original["id"])
        if number and number % 1024 == 0:
            print(f"G03 independent whole-row certificate checks: {number}", flush=True)


def retained_controls(cases: list, response: dict) -> list:
    """Replay the exact already-executed controls; no native call is repeated."""
    controls = []
    reasons = {"fixed_target_reuse": "FIXED_TARGET_REUSE", "poisoned_collapse_adapter": "CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH",
               "predicates_not_on_classes": "PREDICATES_NOT_ON_CLASSES", "duplicated_pair": "DUPLICATE_PAIR_CASE",
               "restored_target": "VALID_CANDIDATE_PRESERVED"}
    names = {"duplicated_pair": "DUPLICATED_PAIR"}
    for stem, reason in reasons.items():
        process = json.loads((AREA / (stem + "_process.json")).read_bytes())
        for suffix, field in (("_request.json", "request_sha256"), ("_stdout.json", "stdout_sha256"), ("_stderr.txt", "stderr_sha256")):
            if replay.sha((AREA / (stem + suffix)).read_bytes()) != process[field]:
                raise ValueError("RETAINED_NATIVE_CONTROL_BYTES_CHANGED")
        if stem == "restored_target":
            restored = json.loads((AREA / (stem + "_stdout.json")).read_bytes())
            if process["returncode"] or restored["calls"] != response["calls"][:1]:
                raise ValueError("RETAINED_TARGET_RESTORATION_FAILED")
        elif process["returncode"] != 2 or (AREA / (stem + "_stderr.txt")).read_text(encoding="utf8").strip() != reason:
            raise ValueError("RETAINED_NATIVE_CONTROL_WRONG_REFUSAL")
        controls.append({"mutation": names.get(stem, stem.upper()), "process": process, "reason": reason})
    for stem, reason in (("dropped_pair", "CALL_POPULATION_INCOMPLETE_OR_DUPLICATED"),
                         ("duplicated_call_log", "CALL_POPULATION_INCOMPLETE_OR_DUPLICATED"),
                         ("raw_deltas_as_classes", "RAW_DELTAS_USED_AS_CLASSES")):
        path = AREA / (stem + "_mutation.json")
        mutant = json.loads(path.read_bytes())
        try:
            replay.check_calls(cases, mutant)
        except ValueError as error:
            if str(error) != reason:
                raise ValueError("RETAINED_CALL_MUTATION_WRONG_REFUSAL") from error
        else:
            raise ValueError("RETAINED_CALL_MUTATION_SURVIVED")
        controls.append({"mutation": stem.upper(), "reason": reason, "mutation_path": path.relative_to(PAPER).as_posix(),
                         "mutation_sha256": replay.sha(path.read_bytes())})
        del mutant
    stale_path = AREA / "stale_script_receipt_mutation.json"
    stale = json.loads(stale_path.read_bytes())
    if not any(replay.sha((PAPER / filename).read_bytes()) != checksum for filename, checksum in stale["registered_files"].items()):
        raise ValueError("RETAINED_STALE_SCRIPT_RECEIPT_SURVIVED")
    controls.append({"mutation": "STALE_SCRIPT_RECEIPT", "reason": "STALE_SCRIPT_RECEIPT",
                     "mutation_path": stale_path.relative_to(PAPER).as_posix(), "mutation_sha256": replay.sha(stale_path.read_bytes())})
    return controls


def close(interpreter: Path) -> dict:
    if not sys.dont_write_bytecode or not sys.pycache_prefix:
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    cache = Path(sys.pycache_prefix)
    cache.mkdir(parents=True, exist_ok=True)
    if any(cache.iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    replay.declaration()
    sources = replay.verify_sources()
    build = json.loads((AREA / "build_receipt.json").read_bytes())
    executable = Path(build["native_executable"])
    if replay.sha(executable.read_bytes()) != build["native_executable_sha256"]:
        raise ValueError("NATIVE_BINARY_CHANGED")
    process = json.loads((AREA / "full_native_process.json").read_bytes())
    for filename, field in (("full_native_request.json", "request_sha256"), ("full_native_stdout.json", "stdout_sha256"),
                            ("full_native_stderr.txt", "stderr_sha256")):
        if replay.sha((AREA / filename).read_bytes()) != process[field]:
            raise ValueError("ORIGINAL_NATIVE_PROCESS_BYTES_CHANGED")
    if process["returncode"]:
        raise ValueError("ORIGINAL_NATIVE_PROCESS_FAILED")
    paths = [Path(__file__), PAPER / "code/genesis_g03_replay.py", PAPER / "code/genesis_g03_adapter.py",
             PAPER / "code/genesis_g07_replay.py", replay.NATIVE / "transport.rs", interpreter, executable,
             AREA / "source_manifest.json", AREA / "preregistration.json", AREA / "build_receipt.json",
             replay.source.MANIFEST, *(PAPER / row["local"] for row in sources["entries"]),
             *(PAPER / row["local"] for row in replay.source.verify_sources()["entries"]),
             *(Path(path) for path in build["dependencies_after"]),
             *(AREA / name for name in ("full_native_request.json", "full_native_stdout.json", "full_native_process.json",
                                       "full_native_stderr.txt", "reference_rows.json", "source_call_log.json", "carriers.json",
                                       "key_correspondences.json")),
             *sorted((AREA / "frozen_failed_replays").glob("*")),
             *sorted(AREA.glob("*_mutation.json")),
             *(AREA / (stem + suffix) for stem in ("fixed_target_reuse", "poisoned_collapse_adapter", "predicates_not_on_classes", "duplicated_pair", "restored_target")
               for suffix in ("_process.json", "_request.json", "_stdout.json", "_stderr.txt"))]
    before = {str(path): replay.sha(path.read_bytes()) for path in paths}
    for path, expected in build["dependencies_after"].items():
        if before[path] != expected:
            raise ValueError("NATIVE_BUILD_DEPENDENCY_CHANGED")
    modules = replay.original()
    cases = replay.primary_cases(modules)
    request = json.loads((AREA / "full_native_request.json").read_bytes())
    if request["cases"] != [{key: value for key, value in case.items() if key != "history"} for case in cases]:
        raise ValueError("RETAINED_REQUEST_NOT_FULL_PREREGISTERED_POPULATION")
    response = json.loads((AREA / "full_native_stdout.json").read_bytes())
    expected = json.loads((AREA / "reference_rows.json").read_bytes())
    call_log = json.loads((AREA / "source_call_log.json").read_bytes())
    base = [case for case in cases if case["variant"] == "base"]
    replay.check_calls(base, expected)
    if len(call_log) != 3264 or {row["id"] for row in call_log} != {row["id"] for row in base}:
        raise ValueError("ORIGINAL_SEALED_CALL_LOG_POPULATION_CHANGED")
    expected_by_id = {row["id"]: row for row in expected}
    for logged in call_log:
        row = expected_by_id[logged["id"]]
        if any(logged[key] != row[key] for key in ("base_canonical_key", "target", "measure")) or logged["bounds"] != {"max_items": 2, "max_arity": 2}:
            raise ValueError("ORIGINAL_SEALED_CALL_ARGUMENTS_CHANGED")
    try:
        replay.match_native(cases, response, expected)
    except ValueError as error:
        strict_error = str(error)
        if not strict_error.startswith("INDEPENDENT_SOURCE_NATIVE_DISAGREEMENT:"):
            raise
    else:
        raise ValueError("EXPECTED_RETAINED_STRICT_LABEL_FAILURE_NOT_REPRODUCED")
    failure = {"schema": "paper011.g03-strict-label-failure.v1", "status": "UNVERIFIED_STRICT_LABEL_COMPARISON",
               "original_worker_reported_exit_code": 1, "native_process_returncode": process["returncode"],
               "reproduced_refusal": strict_error, "passing_fallback_used": False,
               "scope": "Pinned Python ranks repr strings and native code ranks structured values. An independent explicit-bijection check is required; the first worker never emitted a complete receipt."}
    (AREA / "strict_label_failure.json").write_bytes(replay.wire(failure))
    start = time.perf_counter()
    witnesses = json.loads((AREA / "key_correspondences.json").read_bytes())
    check(modules, cases, response, expected, witnesses)
    checker_seconds = time.perf_counter() - start
    mutations = retained_controls(cases, response)
    primary = [row for row in expected if row["n"] <= 15]
    distinct = {(replay.wire(row["base_canonical_key"]), tuple(row["target"]), row["measure"]) for row in primary}
    if len(primary) != 1820 or len(distinct) != 1820:
        raise ValueError("PRIMARY_ACTUAL_ARGUMENTS_NOT_DISTINCT")
    terminal = {}
    for reading in ("L", "F"):
        for measure in ("mu1", "mu2"):
            selected = [r for r in primary if r["reading"] == reading and r["measure"] == measure]
            terminal[reading + ":" + measure] = {predicate: next(([r["n"], r["i"], r["j"]] for r in selected if not r[predicate]), "holds on all 455")
                                                   for predicate in ("weak", "strong")}
    result = {"schema": "paper011.g03-finite-result.v2", "adapter_id": replay.adapter.ADAPTER_ID, "status": "SOLVED",
              "primary_calls": primary, "terminal_per_reading_measure": terminal, "held_out_calls": 1444,
              "relabel_and_reversal_calls": 6528, "native_calls": 9792,
              "original_strict_label_comparison_failed": True, "key_bridge_witnesses": len(witnesses),
              "model_arms_executed": [], "original_Arm_E_success": False,
              "scope": "Complete finite check for the new preregistered adapter, with sealed/native canonical presentations joined by checked bijections. G4 in general remains open."}
    (AREA / "result.json").write_bytes(replay.wire(result))
    after = {path: replay.sha(Path(path).read_bytes()) for path in before}
    if before != after:
        raise ValueError("INDEPENDENT_REPLAY_INPUT_CUSTODY_CHANGED")
    receipt = {"schema": "paper011.g03-key-bridge-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": replay.sha((AREA / "source_manifest.json").read_bytes()),
               "preregistration_sha256": replay.sha((AREA / "preregistration.json").read_bytes()),
               "build_receipt_sha256": replay.sha((AREA / "build_receipt.json").read_bytes()),
               "runner_argv": sys.orig_argv, "runner_cwd": str(Path.cwd()), "python_executable": str(interpreter),
               "dont_write_bytecode": sys.dont_write_bytecode, "cache_prefix": sys.pycache_prefix,
               "inputs_before": before, "inputs_after": after, "native_process": process,
               "source_oracle_calls": 3264, "native_oracle_calls": 9792, "new_min_responses_calls_in_this_replay": 0,
               "primary_distinct_calls": 1820, "key_bridge_witnesses": len(witnesses), "checker_seconds": checker_seconds,
               "mutations": mutations, "terminal_per_reading_measure": terminal,
               "artifacts": {name: replay.sha((AREA / name).read_bytes()) for name in
                             ("carriers.json", "reference_rows.json", "source_call_log.json", "result.json", "full_native_request.json",
                              "full_native_stdout.json", "key_correspondences.json", "strict_label_failure.json")},
               "complete_provider_free_finite_gate": True, "full_G03_model_experiment_completed": False,
               "original_worker_completed": False, "original_worker_exit_code": 1,
               "original_worker_final_runtime_receipt_emitted": False,
               "first_independent_replay_control_recording_failed": True,
               "new_min_responses_or_canonical_witness_searches_in_this_closure": 0,
               "entire_external_estate_workflow_executed": False, "external_owner_PR_created": False,
               "runtime_scope": "Measured before/after custody of this independent replay, original fixed source closure, retained complete engine streams, explicit Python backing executable and linked native executable/build libraries. The first worker failed its strict-label comparison; its unsaved final runtime snapshot is not claimed. OS/Pythonstdlib outside scope."}
    (AREA / "receipt.json").write_bytes(replay.wire(receipt))
    return {"status": "SOLVED", "receipt_sha256": replay.sha((AREA / "receipt.json").read_bytes()),
            "key_bridge_witnesses": len(witnesses), "checker_seconds": checker_seconds,
            "terminal_per_reading_measure": terminal}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interpreter", type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = close(args.interpreter)
    except Exception as error:
        # Typed original errors remain failed/UNKNOWN results, never SOLVED.
        failure = {"status": "UNKNOWN" if type(error).__name__ == "IsoBudgetError" else "FAILED",
                   "error_type": type(error).__name__, "reason": str(error), "complete_provider_free_finite_gate": False}
        (AREA / "independent_replay_failure.json").write_bytes(replay.wire(failure))
        raise
    print(json.dumps(outcome, indent=2))
