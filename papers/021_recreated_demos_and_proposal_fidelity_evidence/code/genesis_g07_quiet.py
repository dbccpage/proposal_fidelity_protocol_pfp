"""Complete G07 quiet-state custody without rerunning the full tree census."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("_paper011_g07_replay", PAPER / "code/genesis_g07_replay.py")
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay
spec.loader.exec_module(replay)


def run(rustc: Path, primitive: Path, json_library: Path, executable: Path) -> dict:
    if not sys.dont_write_bytecode or not sys.pycache_prefix or any(Path(sys.pycache_prefix).iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    replay.verify_sources()
    area = replay.AREA / "quiet_v1"
    area.mkdir(parents=True, exist_ok=True)
    source = PAPER / "code/native_genesis_g07/quiet_controls.rs"
    deps = primitive.resolve(strict=True).parent
    # Only these prebuilt library families can be transitive dependencies of the
    # explicitly supplied JSON transport library. Native primitives have no deps.
    libraries = sorted({primitive.resolve(), json_library.resolve(),
                        *(path.resolve() for family in ("serde_core", "serde", "itoa", "memchr", "zmij")
                          for path in deps.glob("lib" + family + "-*.rlib"))})
    library_before = {str(path): replay.sha(path.read_bytes()) for path in libraries}
    source_before = replay.sha(source.read_bytes())
    rustc = rustc.resolve(strict=True)
    argv = [str(rustc), "--edition", "2021", "--crate-name", "paper011_native_genesis_g07_quiet",
            str(source), "-L", "dependency=" + str(deps), "--extern", "core_ooutwire_primitives=" + str(primitive),
            "--extern", "serde_json=" + str(json_library), "-o", str(executable)]
    build = subprocess.run(argv, cwd=PAPER, capture_output=True, check=False, timeout=60)
    (area / "build_stdout.txt").write_bytes(build.stdout)
    (area / "build_stderr.txt").write_bytes(build.stderr)
    if build.returncode:
        raise ValueError("QUIET_CONTROL_COMPILE_FAILED:" + build.stderr.decode("utf8", "replace"))
    modules = replay.load_original()
    engine, driver = modules["engine"], modules["unboundedness"]
    expected = []
    for reading in (engine.READING_L, engine.READING_F):
        original = driver.replay
        states, histories, accumulated = [], [], []
        def observed(events, base=None):
            result = original(events) if base is None else original(events, base)
            accumulated.extend(events)
            states.append(result)
            histories.append(tuple(accumulated))
            return result
        driver.replay = observed
        try:
            driver.run_driver_trajectory(reading, "mu2", 60, modules["candidates"].Bounds(2, 2))
        finally:
            driver.replay = original
        if len(states) != 61:
            raise ValueError("MISSING_TRAJECTORY_STATE")
        for depth, (regime, history) in enumerate(zip(states, histories, strict=True)):
            if depth and not engine.closure_challenge_orbits(regime):
                expected.append({"id": f"P2:{reading.name}:quiet:{depth}", "depth": depth,
                                 "state": replay.state(regime),
                                 "history": [replay.event_wire(event) for event in history]})
    payload = {"schema": "paper011.g07-quiet-request.v1", "cases": expected}
    request = replay.wire(payload)
    (area / "request.json").write_bytes(request)
    started = time.perf_counter()
    process = subprocess.run([str(executable)], input=request, cwd=PAPER, capture_output=True, check=False, timeout=30)
    (area / "stdout.json").write_bytes(process.stdout)
    (area / "stderr.txt").write_bytes(process.stderr)
    if process.returncode:
        raise ValueError("QUIET_NATIVE_CHECK_FAILED:" + process.stderr.decode("utf8", "replace"))
    response = json.loads(process.stdout)
    if response["schema"] != "paper011.g07-quiet-response.v1" or len(response["cases"]) != len(expected):
        raise ValueError("QUIET_CASE_COMPLETENESS_MISMATCH")
    for want, got in zip(expected, response["cases"], strict=True):
        if any(want[key] != got[key] for key in ("id", "depth", "state")) or got["width"] is not None or got["offered_challenges"] != []:
            raise ValueError("QUIET_NATIVE_DISAGREEMENT")
    base = json.loads((replay.AREA / "run_v1/result.json").read_bytes())
    quiet_ids = {(row["reading"], quiet["depth"]) for row in base["trajectories"] for quiet in row["quiet_states"]}
    if quiet_ids != {(row["id"].split(":")[1], row["depth"]) for row in expected}:
        raise ValueError("BASE_QUIET_CENSUS_MISMATCH")
    controls = []
    native_request = json.loads((replay.AREA / "run_v1/native_request.json").read_bytes())
    nonquiet = next(row for row in native_request["cases"] if row["population"] == "P1" and row["depth"] == 0)
    tests = {"NONQUIET_STATE": {"schema": payload["schema"], "cases": [nonquiet]},
             "UNKNOWN_EVENT": copy.deepcopy(payload), "MALFORMED_HISTORY": copy.deepcopy(payload),
             "DUPLICATE_CASE": {"schema": payload["schema"], "cases": [expected[0], expected[0]]}}
    tests["UNKNOWN_EVENT"]["cases"][0]["history"][0]["kind"] = "UnknownEvent"
    tests["MALFORMED_HISTORY"]["cases"][0]["history"].append({"kind": "AdmitInst", "form": 999, "args": [999]})
    for name, mutant in tests.items():
        mutation_bytes = replay.wire(mutant)
        outcome = subprocess.run([str(executable)], input=mutation_bytes, cwd=PAPER, capture_output=True, check=False, timeout=30)
        (area / (name.lower() + "_request.json")).write_bytes(mutation_bytes)
        (area / (name.lower() + "_stderr.txt")).write_bytes(outcome.stderr)
        if outcome.returncode == 0:
            raise ValueError("SURVIVING_QUIET_MUTATION:" + name)
        controls.append({"mutation": name, "returncode": outcome.returncode,
                         "request_sha256": replay.sha(mutation_bytes), "stdout_sha256": replay.sha(outcome.stdout),
                         "stderr_sha256": replay.sha(outcome.stderr), "reason": outcome.stderr.decode("utf8").strip()})
    library_after = {str(path): replay.sha(path.read_bytes()) for path in libraries}
    if library_before != library_after or source_before != replay.sha(source.read_bytes()):
        raise ValueError("QUIET_BUILD_INPUT_CHANGED")
    receipt = {"schema": "paper011.g07-quiet-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": replay.sha(replay.MANIFEST.read_bytes()),
               "base_run_receipt_sha256": replay.sha((replay.AREA / "run_v1/receipt.json").read_bytes()),
               "python_runner_sha256": replay.sha(Path(__file__).read_bytes()),
               "original_loader_sha256": replay.sha((PAPER / "code/genesis_g07_replay.py").read_bytes()),
               "source_sha256_before": source_before, "source_sha256_after": replay.sha(source.read_bytes()),
               "rustc": str(rustc), "rustc_sha256": replay.sha(rustc.read_bytes()),
               "build_argv": argv, "cwd": str(PAPER), "build_returncode": build.returncode,
               "build_stdout_sha256": replay.sha(build.stdout), "build_stderr_sha256": replay.sha(build.stderr),
               "libraries_before": library_before, "libraries_after": library_after,
               "native_executable": str(executable), "native_executable_sha256": replay.sha(executable.read_bytes()),
               "argv": [str(executable)], "returncode": process.returncode,
               "request_sha256": replay.sha(request), "stdout_sha256": replay.sha(process.stdout),
               "stderr_sha256": replay.sha(process.stderr), "quiet_case_count": len(expected),
               "native_seconds": time.perf_counter() - started, "controls": controls,
               "python_version": sys.version, "cache_prefix": sys.pycache_prefix, "dont_write_bytecode": sys.dont_write_bytecode}
    (area / "receipt.json").write_bytes(replay.wire(receipt))
    completion = {"schema": "paper011.g07-provider-free-completion.v1", "AuthorityEffect": "None",
                  "base_receipt_sha256": receipt["base_run_receipt_sha256"],
                  "quiet_receipt_sha256": replay.sha((area / "receipt.json").read_bytes()),
                  "width_cases": len(native_request["cases"]), "quiet_cases": len(expected),
                  "heldouts": len(base["heldouts"]), "finite_computation_gate": True,
                  "model_arms_executed": [], "empirical_differentiation_gate": False,
                  "historical_raw_model_response_replayed": False, "conjecture_status": "OPEN",
                  "scope": "Full original provider-free G07 census baseline and controls; model-arm experiment remains unperformed."}
    (replay.AREA / "provider_free_completion.json").write_bytes(replay.wire(completion))
    return completion


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("rustc", "primitive", "json-library", "executable"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.rustc, args.primitive, args.json_library, args.executable), indent=2))


if __name__ == "__main__":
    main()
