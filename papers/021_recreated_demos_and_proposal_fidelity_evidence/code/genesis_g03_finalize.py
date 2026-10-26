"""Independent G03 custody closure and the original count-preserving poison."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("_paper011_g03_finalizer_port", PAPER / "code/genesis_g03_replay.py")
if spec is None or spec.loader is None:
    raise ValueError("MISSING_EXPLICIT_G03_PORT")
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)
AREA = replay.AREA


def require_bytes(path: Path, expected: str) -> None:
    if replay.sha(path.read_bytes()) != expected:
        raise ValueError("G03_BOUND_BYTES_CHANGED:" + str(path))


def close() -> dict:
    if not sys.dont_write_bytecode or not sys.pycache_prefix:
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    cache = Path(sys.pycache_prefix)
    cache.mkdir(parents=True, exist_ok=True)
    if any(cache.iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    receipt_path = AREA / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    if not receipt["complete_provider_free_finite_gate"] or receipt["inputs_before"] != receipt["inputs_after"]:
        raise ValueError("G03_PRIMARY_RUN_NOT_COMPLETE_OR_BOUND")
    replay.declaration()
    replay.verify_sources()
    for path, expected in receipt["inputs_after"].items():
        require_bytes(Path(path), expected)
    for name, expected in receipt["artifacts"].items():
        require_bytes(AREA / name, expected)
    for stem in ["full_native", "restored_target", "fixed_target_reuse", "poisoned_collapse_adapter",
                 "predicates_not_on_classes", "duplicated_pair"]:
        process = json.loads((AREA / (stem + "_process.json")).read_bytes())
        for suffix, field in [("_request.json", "request_sha256"), ("_stdout.json", "stdout_sha256"), ("_stderr.txt", "stderr_sha256")]:
            require_bytes(AREA / (stem + suffix), process[field])
    for control in receipt["mutations"]:
        if "mutation_path" in control:
            require_bytes(PAPER / control["mutation_path"], control["mutation_sha256"])
    recovered_manifest = PAPER / "docs/history_recovery/recovery_manifest.json"
    original_spec = PAPER / "docs/history_recovery/recovered_sources/g03_g4_finite_check_replay.md"
    expected_spec = "652b7b89f5e693bd4767b1a7be0f1b43506a8c8a66c6b3ee96507b556a40417f"
    require_bytes(original_spec, expected_spec)
    source_entry = next(row for row in json.loads(recovered_manifest.read_bytes())["entries"]
                        if row["recovered_relative_path"] == original_spec.relative_to(PAPER).as_posix())
    if (source_entry["git_blob"], source_entry["source_commit"], source_entry["sha256"]) != (
            "8c39f569b7fc68351bf36fbec23c1c89a227d28f", "5e5e64e441da1c357179b6979daa9f780dcc36b4", expected_spec):
        raise ValueError("ORIGINAL_G03_SPEC_PIN_CHANGED")
    if replay.source.blob(original_spec.read_bytes()) != source_entry["git_blob"]:
        raise ValueError("ORIGINAL_G03_SPEC_BLOB_CHANGED")
    g07_build = replay.source.AREA / "build/receipt.json"
    require_bytes(g07_build, "91bf3067e9a45c1b1e217f0ce66db76ed04a9e0384c3710d913640a85a3ece2c")
    original_build = json.loads(g07_build.read_bytes())
    hosts = {str(Path(original_build["existing_host_directory"]) / name): expected
             for name, expected in original_build["existing_hosts_after"].items()}
    for path, expected in hosts.items():
        require_bytes(Path(path), expected)
    bound_paths = [Path(__file__), receipt_path, original_spec, recovered_manifest, g07_build,
                   *(Path(path) for path in receipt["inputs_after"]),
                   *(AREA / name for name in receipt["artifacts"])]
    before = {str(path): replay.sha(path.read_bytes()) for path in bound_paths} | hosts
    modules = replay.original()
    carriers = json.loads((AREA / "carriers.json").read_bytes())
    expected_carriers = {}
    for case in replay.primary_cases(modules):
        identity = f"{case['n']}:{case['reading']}:{case['variant']}"
        expected_carriers.setdefault(identity, {"state": case["state"], "original_history": case["history"]})
    if carriers != json.loads(replay.wire(expected_carriers)):
        raise ValueError("SOURCE_EVENT_OR_CARRIER_BYTES_DO_NOT_REPLAY")
    adapter = replay.adapter
    original, _ = adapter.construct(modules, 4, "L")
    pi = list(range(original.n_data()))
    endpoint, interior = adapter.coordinate(4, "L", 0), adapter.coordinate(4, "L", 1)
    pi[endpoint], pi[interior] = pi[interior], pi[endpoint]
    poisoned = modules["iso"].rename(original, tuple(pi), tuple(range(len(original.forms))))
    observed = sorted(modules["observe"].collapsed_pairs(original))
    poisoned_pairs = sorted(modules["observe"].collapsed_pairs(poisoned))
    if len(observed) != len(poisoned_pairs) or observed == poisoned_pairs:
        raise ValueError("POISON_DOES_NOT_PRESERVE_COUNT_AND_BREAK_CORRESPONDENCE")
    all_chain_pairs = [(i, j) for i in range(5) for j in range(i + 1, 5)]
    violations = [[i, j] for i, j in all_chain_pairs
                  if (tuple(sorted((adapter.coordinate(4, "L", i), adapter.coordinate(4, "L", j)))) in poisoned_pairs)
                  != (1 <= i < j < 4)]
    if not violations:
        raise ValueError("COUNT_PRESERVING_POISON_IS_NOT_A_FALSIFIER")
    full_request = json.loads((AREA / "full_native_request.json").read_bytes())
    case = next(row for row in full_request["cases"] if row["id"] == "4:1:2:L:mu1:base")
    request = {key: value for key, value in full_request.items() if key != "cases"}
    request["cases"] = [dict(case, state=replay.source.state(poisoned))]
    executable = Path(receipt["native_process"]["argv"][0])
    _, process = replay.native(executable, request, "count_preserving_poison")
    reason = (AREA / "count_preserving_poison_stderr.txt").read_text(encoding="utf8").strip()
    if process["returncode"] != 2 or reason != "CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH":
        raise ValueError("COUNT_PRESERVING_POISON_SURVIVED_OR_WRONG_REFUSAL")
    request["cases"] = [case]
    restored, restoration = replay.native(executable, request, "count_preserving_poison_restoration")
    full_response = json.loads((AREA / "full_native_stdout.json").read_bytes())
    expected = next(row for row in full_response["calls"] if row["id"] == case["id"])
    if restoration["returncode"] or restored["calls"] != [expected]:
        raise ValueError("COUNT_PRESERVING_POISON_RESTORATION_FAILED")
    after = {path: replay.sha(Path(path).read_bytes()) for path in before}
    if before != after:
        raise ValueError("SUPPLEMENT_INPUT_CUSTODY_CHANGED")
    result = {"schema": "paper011.g03-independent-closure.v1", "AuthorityEffect": "None",
              "primary_receipt_sha256": replay.sha(receipt_path.read_bytes()),
              "original_spec": source_entry, "runner_argv": sys.orig_argv, "runner_cwd": str(Path.cwd()),
              "cache_prefix": sys.pycache_prefix, "dont_write_bytecode": sys.dont_write_bytecode,
              "inputs_before": before, "inputs_after": after,
              "source_history_and_carrier_presentations_replayed": len(expected_carriers),
              "original_collapse_pairs": observed, "poisoned_collapse_pairs": poisoned_pairs,
              "preserved_collapse_count": len(observed), "data_bijection": pi,
              "all_chain_pair_correspondence_violations": violations,
              "count_preserving_poison_process": process, "count_preserving_poison_reason": reason,
              "restoration_process": restoration,
              "all_original_provider_free_finite_controls_replayed": True,
              "full_G03_model_experiment_completed": False, "original_Arm_E_success": False,
              "external_owner_PR_created": False, "entire_external_estate_workflow_executed": False,
              "scope": "The original count-preserving poison supplements the unchanged full finite run. Existing six host binary hashes equal the prior pinned G07 build; original model arms and external whole-estate workflow remain separate."}
    (AREA / "completion_receipt.json").write_bytes(replay.wire(result))
    return {"status": "SOLVED", "receipt_sha256": replay.sha((AREA / "completion_receipt.json").read_bytes()),
            "preserved_collapse_count": len(observed), "violations": violations, "refusal": reason}


if __name__ == "__main__":
    print(json.dumps(close(), indent=2))
