"""Source-pinned G07 baseline replay; orchestration over original algorithms.

The recovered Python definitions are the historical independent reference,
not a new Python solver. All native checks use an explicit paper-local binary.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import copy
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import time
import types
from collections import Counter
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g07"
MANIFEST = AREA / "source_manifest.json"
NATIVE = PAPER / "code/native_genesis_g07"
SEALED = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
RESEARCH = "b55fc96a94740b0afde78337350a96d293615f3f"
ESTATE = "526ffd1748941f1781c0ff584b7033b29088b405"
PREFIX = "omega_engine/crates_rs/omega_ooutwire_primitives/"
NATIVE_TREE = "cfbd79e44ea5424ebad6d34709fa3993a05170e0"
SOURCE_MANIFEST_SHA256 = "1fdd11089b01ce6746723fa7ddcd3764162c9b24a09a388ee2131aaf2aeabcbb"
PINS = {
    "code/derivation/__init__.py": (SEALED, "8c239e66976fadaa9e5a04f9451ec4c500c266d4"),
    "code/derivation/model.py": (SEALED, "b6f95a673853d423a0d73b4faa95b2cd22f306a3"),
    "code/derivation/observe.py": (SEALED, "2552c0412d472ae9ff5d31f9068684cfa531aad9"),
    "code/derivation/candidates.py": (SEALED, "9fa609d8a797f74f1620ce39e377c7dc54ee53b7"),
    "code/derivation/iso.py": (SEALED, "f05399fe6bdfbd2311bf34fa6fe927af194f586f"),
    "code/derivation/engine.py": (SEALED, "343290d82a7fcda91f3ff85751af7af99f9a0359"),
    "artifacts/claims.json": (SEALED, "e510aef3ebddc1c4a8d91789e0a186c9c8bfdf92"),
    "research/alpha_engine/evaluate.py": (RESEARCH, "d9bdfd70fd42e9cc5b297b18154476420a253c8e"),
    "research/alpha_engine/harness.py": (RESEARCH, "d6d11124c18ed81032a7ec8bfff47e3a4243b048"),
    "research/unboundedness/unboundedness.py": (RESEARCH, "c21573f4d5f100d059765499dd14cfc1d972e2de"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def wire(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def git(repository: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repository.resolve()), *args], check=True, capture_output=True,
    ).stdout


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"RECOVERED_BYTES_ALREADY_DIFFER:{path}")
    path.write_bytes(data)


def recover(external: Path, estate: Path) -> dict:
    entries = []
    for source, (commit, expected) in PINS.items():
        data = git(external, "show", commit + ":" + source)
        actual = git(external, "rev-parse", commit + ":" + source).decode().strip()
        if actual != expected or blob(data) != expected:
            raise ValueError("PYTHON_SOURCE_PIN_MISMATCH")
        relative = "docs/history_recovery/g07/pinned_python/" + source
        write(PAPER / relative, data)
        entries.append({"repository": "19L57G1", "commit": commit, "source": source,
                        "blob": expected, "sha256": sha(data), "bytes": len(data),
                        "local": relative})
    actual_tree = git(estate, "rev-parse", ESTATE + ":" + PREFIX.rstrip("/")).decode().strip()
    if actual_tree != NATIVE_TREE:
        raise ValueError("NATIVE_SOURCE_TREE_PIN_MISMATCH")
    listing = git(estate, "ls-tree", "-r", ESTATE, PREFIX).decode().splitlines()
    for line in listing:
        meta, source = line.split("\t")
        _, kind, expected = meta.split()
        suffix = source.removeprefix(PREFIX)
        if suffix != "Cargo.toml" and not suffix.startswith("src/"):
            continue
        if kind != "blob":
            raise ValueError("NATIVE_SOURCE_NOT_BLOB")
        data = git(estate, "cat-file", "blob", expected)
        if blob(data) != expected:
            raise ValueError("NATIVE_BLOB_CORRUPT")
        relative = "code/native_genesis_g07/pinned_primitives/" + suffix
        write(PAPER / relative, data)
        entries.append({"repository": "the_symbol_game", "commit": ESTATE, "source": source,
                        "blob": expected, "sha256": sha(data), "bytes": len(data),
                        "local": relative})
    result = {"schema": "paper011.g07-source-closure.v1", "AuthorityEffect": "None",
              "native_tree": NATIVE_TREE, "entries": entries,
              "source_identity_only": True, "mathematical_gate": False}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(wire(result))
    return result


def verify_sources() -> dict:
    if sha(MANIFEST.read_bytes()) != SOURCE_MANIFEST_SHA256:
        raise ValueError("FIXED_SOURCE_MANIFEST_CHANGED")
    manifest = json.loads(MANIFEST.read_bytes())
    entries = manifest["entries"]
    if manifest["native_tree"] != NATIVE_TREE:
        raise ValueError("NATIVE_TREE_CHANGED")
    keys = [entry["source"] for entry in entries]
    if len(set(keys)) != len(keys) or set(PINS) - set(keys):
        raise ValueError("SOURCE_SET_CHANGED")
    # Native manifest paths are themselves bound by its raw hash in build/run receipts.
    for entry in entries:
        path = PAPER / entry["local"]
        if not path.resolve().is_relative_to(PAPER) or path.is_symlink():
            raise ValueError("SOURCE_PATH_ESCAPE")
        data = path.read_bytes()
        if (blob(data), sha(data), len(data)) != (entry["blob"], entry["sha256"], entry["bytes"]):
            raise ValueError("SOURCE_BYTES_CHANGED")
        if entry["source"] in PINS:
            if (entry["commit"], entry["blob"]) != PINS[entry["source"]]:
                raise ValueError("PYTHON_SOURCE_SUBSTITUTION")
        elif entry["commit"] != ESTATE or not entry["source"].startswith(PREFIX):
            raise ValueError("NATIVE_SOURCE_SUBSTITUTION")
    return manifest


def load_original() -> dict:
    """Explicit file loading; original function/class bodies remain intact."""
    verify_sources()
    modules = {}
    package = types.ModuleType("_paper011_g07")
    package.__path__ = []
    sys.modules[package.__name__] = package
    derivation = types.ModuleType(package.__name__ + ".derivation")
    derivation.__path__ = []
    sys.modules[derivation.__name__] = derivation
    def importer(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and (name.startswith("derivation.") or name == "harness"):
            return modules[name]
        return builtins.__import__(name, globals, locals, fromlist, level)
    order = ["model", "observe", "iso", "candidates", "engine", "harness", "evaluate", "unboundedness"]
    for short in order:
        if short in order[:5]:
            source = "code/derivation/" + short + ".py"
            name = "derivation." + short
            qualified = derivation.__name__ + "." + short
            parent = derivation.__name__
        else:
            source = {"harness": "research/alpha_engine/harness.py",
                      "evaluate": "research/alpha_engine/evaluate.py",
                      "unboundedness": "research/unboundedness/unboundedness.py"}[short]
            name, qualified, parent = short, package.__name__ + "." + short, package.__name__
        path = AREA / "pinned_python" / source
        parsed = ast.parse(path.read_text(encoding="utf8"), filename=str(path))
        if short == "unboundedness":
            # Only top-level apparatus is omitted: no sys.path or __main__ execution.
            parsed.body = [node for node in parsed.body
                           if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
                           or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)]
        module = types.ModuleType(qualified)
        module.__file__, module.__package__ = str(path), parent
        module.__dict__["__builtins__"] = {**vars(builtins), "__import__": importer}
        sys.modules[qualified] = module
        modules[name] = module
        exec(compile(parsed, str(path), "exec"), module.__dict__)
        modules[short] = module
    return modules


def state(regime) -> dict:
    return {"data": list(regime.data), "forms": list(regime.forms),
            "insts": [[form, list(args)] for form, args in sorted(regime.insts)],
            "rules": sorted(regime.rules), "reqs": [list(pair) for pair in sorted(regime.reqs)]}


def event_wire(event) -> dict:
    return {"kind": type(event).__name__, **dataclasses.asdict(event)}


def renamed(reading, model, engine):
    history = []
    for event in reading.genesis:
        if isinstance(event, (model.Supply, model.AdmitDatum)):
            event = type(event)("renamed:" + event.token)
        history.append(event)
    return engine.Reading(reading.name, reading.description, tuple(history), reading.target)


def collect_tree(modules, reading, relabel=False) -> dict:
    engine, model, candidates, evaluator = (modules[key] for key in ("engine", "model", "candidates", "evaluate"))
    if relabel:
        reading = renamed(reading, model, engine)
    tree = engine.build_tree(reading, "mu2", candidates.Bounds(2, 2), 15, 3000, True)
    rows, quiet = [], Counter()
    for node in tree.nodes:
        targets = (reading.target,) if node.node_id == 0 else engine.closure_challenge_orbits(node.regime)
        if not targets:
            quiet[node.depth] += 1
        for target in targets:
            evaluation = evaluator.evaluate(node.regime, target, "mu2", candidates.Bounds(2, 2))
            if not evaluation.found:
                raise ValueError("TREE_NO_RESPONSE")
            if not all(candidates.response_valid_naive(node.regime, target, delta) for delta in evaluation.raw_minima):
                raise ValueError("REFERENCE_INVALID_MINIMUM")
            history = [event_wire(event) for event in node.history]
            rows.append({"id": f"P1:{reading.name}:{'rename' if relabel else 'base'}:{node.node_id}:{target[0]}:{target[1]}",
                         "reading": reading.name, "population": "P1", "depth": node.depth,
                         "status": node.status, "target": list(target), "state": state(node.regime),
                         "history": history, "width": len(evaluation.retained),
                         "raw_minima": len(evaluation.raw_minima), "cost": list(evaluation.cost),
                         "class_sizes": sorted(len(item.members) for item in evaluation.retained)})
    hist = histograms(rows)
    expanded_ties = sum(row["width"] > 1 and row["status"] == "expanded" for row in rows)
    return {"reading": reading.name, "relabel": relabel, "stats": tree.stats(),
            "histograms": hist, "quiet_nodes_by_depth": dict(sorted(quiet.items())),
            "expanded_ties": expanded_ties, "rows": rows}


def histograms(rows: list[dict]) -> dict:
    return {str(depth): {str(width): count for width, count in sorted(Counter(row["width"] for row in rows if row["depth"] == depth).items())}
            for depth in range(16)}


def collect_trajectory(modules, reading) -> dict:
    driver, model, engine, evaluator, candidates = (modules[key] for key in ("unboundedness", "model", "engine", "evaluate", "candidates"))
    original_replay = driver.replay
    states, histories = [], []
    accumulated = []
    def observed_replay(events, base=None):
        result = original_replay(events) if base is None else original_replay(events, base)
        accumulated.extend(events)
        states.append(result)
        histories.append(tuple(accumulated))
        return result
    driver.replay = observed_replay
    try:
        original_result = driver.run_driver_trajectory(reading, "mu2", 60, candidates.Bounds(2, 2))
    finally:
        driver.replay = original_replay
    if len(states) != 61 or original_result["final_depth"] != 60:
        raise ValueError("INCOMPLETE_ORIGINAL_TRAJECTORY")
    rows, quiet = [], []
    for depth, (regime, history) in enumerate(zip(states, histories, strict=True)):
        if model.replay(history) != regime:
            raise ValueError("TRAJECTORY_HISTORY_MISMATCH")
        targets = (reading.target,) if depth == 0 else engine.closure_challenge_orbits(regime)
        if not targets:
            quiet.append({"depth": depth, "data": regime.n_data(), "width": None,
                          "reason": "NO_PAIR_SEPARATION_CHALLENGE"})
            continue
        target = targets[0]  # Literal original driver ordering.
        evaluation = evaluator.evaluate(regime, target, "mu2", candidates.Bounds(2, 2))
        rows.append({"id": f"P2:{reading.name}:base:{depth}", "reading": reading.name,
                     "population": "P2", "depth": depth, "status": "trajectory",
                     "target": list(target), "state": state(regime),
                     "history": [event_wire(event) for event in history],
                     "width": len(evaluation.retained), "raw_minima": len(evaluation.raw_minima),
                     "cost": list(evaluation.cost),
                     "class_sizes": sorted(len(item.members) for item in evaluation.retained)})
    return {"reading": reading.name, "original_driver_result": original_result,
            "quiet_states": quiet, "rows": rows}


def native_payload(trees: list[dict], trajectories: list[dict]) -> dict:
    rows = [row for entry in [*trees, *trajectories] for row in entry["rows"]]
    return {"schema": "paper011.g07-native-request.v1", "max_items": 2, "max_arity": 2,
            "cases": [{key: row[key] for key in ("id", "reading", "population", "depth", "target", "history")} for row in rows]}


def check_native(payload: dict, response: dict, trees: list[dict], trajectories: list[dict]) -> None:
    rows = [row for entry in [*trees, *trajectories] for row in entry["rows"]]
    if response.get("schema") != "paper011.g07-native-response.v1":
        raise ValueError("NATIVE_SCHEMA_MISMATCH")
    expected_ids = [row["id"] for row in rows]
    actual_ids = [row["id"] for row in response["cases"]]
    if expected_ids != actual_ids or len(set(actual_ids)) != len(actual_ids):
        raise ValueError("NATIVE_CASE_COMPLETENESS_MISMATCH")
    if [row["id"] for row in payload["cases"]] != expected_ids:
        raise ValueError("NATIVE_REQUEST_CASES_CHANGED")
    for expected, actual in zip(rows, response["cases"], strict=True):
        for key in ("id", "depth", "state", "width", "raw_minima", "cost", "class_sizes"):
            if actual.get(key) != expected[key]:
                raise ValueError(f"NATIVE_CASE_MISMATCH:{expected['id']}:{key}")
        if actual.get("all_responses_valid_naive") is not True:
            raise ValueError("NATIVE_INVALID_RESPONSE_CERTIFICATE")
    if len(response["trees"]) != 4:
        raise ValueError("NATIVE_TREE_COMPLETENESS_MISMATCH")
    for expected, actual in zip(trees, response["trees"], strict=True):
        for key in ("reading", "relabel", "histograms", "expanded_ties"):
            if actual[key] != expected[key]:
                raise ValueError(f"NATIVE_TREE_MISMATCH:{expected['reading']}:{key}")
        for key in ("nodes", "edges", "max_depth", "expansions_with_ties", "all_certified"):
            if actual["stats"][key] != expected["stats"][key]:
                raise ValueError("NATIVE_TREE_STATS_MISMATCH:" + key)


def mutation_controls(payload: dict, response: dict, trees: list[dict], trajectories: list[dict]) -> list[dict]:
    controls = []
    mutations = ["RAW_DELTAS_AS_CLASSES", "DEPTH_SHIFT", "SUPPLY_DISABLED", "DROPPED_CASE", "CORRUPT_CARRIER", "CORRUPT_CERTIFICATE"]
    for name in mutations:
        mutated = copy.deepcopy(response)
        if name == "RAW_DELTAS_AS_CLASSES":
            row = next(row for row in mutated["cases"] if row["raw_minima"] != row["width"])
            row["width"] = row["raw_minima"]
        elif name == "DEPTH_SHIFT":
            mutated["cases"][0]["depth"] += 1
        elif name == "SUPPLY_DISABLED":
            mutated["trees"][0] = mutated["closed_trees"][0]
        elif name == "DROPPED_CASE":
            mutated["cases"].pop()
        elif name == "CORRUPT_CARRIER":
            mutated["cases"][0]["state"]["data"][0] += ":corruption"
        else:
            mutated["cases"][0]["class_sizes"][0] += 1
        try:
            check_native(payload, mutated, trees, trajectories)
        except ValueError as error:
            controls.append({"mutation": name, "mutated_response_sha256": sha(wire(mutated)),
                             "rejected": True, "reason": str(error)})
        else:
            raise ValueError("SURVIVING_MUTATION:" + name)
    return controls


def valid_conjecture(rows: list[dict], bound: int, status: str, quantified: bool, falsifier: str) -> bool:
    return (status == "OPEN" and quantified is True and bool(falsifier)
            and type(bound) is int and bound >= 0 and all(row["width"] <= bound for row in rows))


def solve(case: dict, result: dict) -> dict:
    if case.get("request") == "prove the fan is unbounded":
        return {"status": "OUT_OF_SCOPE", "witness": "FINITE_CENSUS_DOES_NOT_PROVE_KIND_D"}
    reading, population, depth = (case.get(key) for key in ("reading", "population", "depth"))
    if reading not in ("L", "F") or population not in ("P1", "P2") or type(depth) is not int or depth < 0:
        raise ValueError("MALFORMED_CASE")
    if depth > (15 if population == "P1" else 60):
        return {"status": "OUT_OF_SCOPE", "witness": "DEPTH_EXCEEDS_DECLARED_FINITE_EXPORT"}
    if population == "P1":
        tree = next(item for item in result["trees"] if item["reading"] == reading and not item["relabel"])
        return {"status": "SOLVED", "histogram": tree["histograms"][str(depth)],
                "tie_expansion_count": tree["expanded_ties"], "conjecture": result["conjecture"]}
    trajectory = next(item for item in result["trajectories"] if item["reading"] == reading)
    rows = [row for row in trajectory["rows"] if row["depth"] == depth]
    if rows:
        return {"status": "SOLVED", "histogram": {str(rows[0]["width"]): 1},
                "data": len(rows[0]["state"]["data"]), "conjecture": result["conjecture"]}
    quiet = next(row for row in trajectory["quiet_states"] if row["depth"] == depth)
    return {"status": "SOLVED", "histogram": {}, "width": None, "data": quiet["data"],
            "witness": quiet["reason"], "conjecture": result["conjecture"]}


def run(executable: Path, interpreter: Path) -> dict:
    before = verify_sources()
    executable = executable.resolve(strict=True)
    executable_sha = sha(executable.read_bytes())
    interpreter = interpreter.resolve(strict=True)
    runtime = {"python_version": sys.version, "backing_interpreter": str(interpreter),
               "interpreter_sha256": sha(interpreter.read_bytes()),
               "scope": "Declared interpreter and pinned source files; stdlib and OS are not hermetically inventoried.",
               "dont_write_bytecode": sys.dont_write_bytecode, "cache_prefix": sys.pycache_prefix}
    if not sys.dont_write_bytecode or not sys.pycache_prefix or any(Path(sys.pycache_prefix).iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    started = time.perf_counter()
    modules = load_original()
    readings = [modules["engine"].READING_L, modules["engine"].READING_F]
    trees = [collect_tree(modules, reading, relabel) for reading in readings for relabel in (False, True)]
    trajectories = [collect_trajectory(modules, reading) for reading in readings]
    claims = json.loads((AREA / "pinned_python/artifacts/claims.json").read_bytes())["CL-TREE-SUMMARY"]
    for tree in trees:
        if tree["stats"] != claims[tree["reading"] + "_mu2"] or tree["expanded_ties"] != claims[tree["reading"] + "_mu2"]["expansions_with_ties"]:
            raise ValueError("SEALED_SUMMARY_RECONCILIATION_FAILED")
    for left, right in (trees[:2], trees[2:]):
        if left["histograms"] != right["histograms"]:
            raise ValueError("RELABEL_HISTOGRAM_CHANGED")
    payload = native_payload(trees, trajectories)
    request = wire(payload)
    run_dir = AREA / "run_v1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "native_request.json").write_bytes(request)
    proc_started = time.perf_counter()
    process = subprocess.run([str(executable)], input=request, capture_output=True, check=False, cwd=PAPER, timeout=180)
    process_seconds = time.perf_counter() - proc_started
    (run_dir / "native_stdout.json").write_bytes(process.stdout)
    (run_dir / "native_stderr.txt").write_bytes(process.stderr)
    if process.returncode:
        raise ValueError("NATIVE_PROCESS_FAILED:" + process.stderr.decode("utf8", "replace"))
    response = json.loads(process.stdout)
    check_native(payload, response, trees, trajectories)
    mutations = mutation_controls(payload, response, trees, trajectories)
    rows = [row for item in [*trees, *trajectories] for row in item["rows"]]
    maximum = max(row["width"] for row in rows)
    conjecture = {"status": "OPEN", "quantified": True, "bound": maximum,
                  "statement": f"For every reachable state x under the declared mu2 Bounds(2,2) supply policy and every offered pair-separation challenge t, w(x,t) <= {maximum}.",
                  "evidence": "Both complete P1 trees through depth 15; the original deterministic P2 trajectories through depth 60.",
                  "falsifier": f"A source-valid reachable state and offered challenge whose exact retained-class width exceeds {maximum}.",
                  "proved": False}
    controls = {"raw_delta_mutation_rejected": any(row["raw_minima"] != row["width"] for row in rows),
                "depth_shift_mutation_rejected": any(tree["histograms"]["0"] != tree["histograms"]["1"] for tree in trees),
                "native_supply_off_control": response["closed_trees"],
                "refuted_conjecture_rejected": not valid_conjecture(rows, 0, "OPEN", True, "counterexample"),
                "conjecture_rubric_passed": valid_conjecture(rows, maximum, "OPEN", True, conjecture["falsifier"])}
    controls["actual_response_mutations"] = mutations
    if not all(controls[key] for key in ("raw_delta_mutation_rejected", "depth_shift_mutation_rejected", "refuted_conjecture_rejected", "conjecture_rubric_passed")):
        raise ValueError("MUTATION_CONTROL_FAILED")
    result = {"schema": "paper011.g07-finite-computation.v1", "AuthorityEffect": "None",
              "trees": trees, "trajectories": trajectories, "conjecture": conjecture, "controls": controls,
              "native_agreement": True, "finite_computation_gate": True,
              "model_arms_executed": [], "empirical_differentiation_gate": False,
              "original_historical_response_replayed": False,
              "full_g07_experiment_completed": False,
              "population_note": "Histograms count every offered pair-separation challenge at each exported node, including completed boundary nodes. Quiet nodes offer no such target and are counted separately. Only actual expanded nodes enter the sealed 236/422 expansion reconciliation.",
              "source_manifest_sha256": sha(MANIFEST.read_bytes()), "runtime": runtime}
    heldouts = []
    for reading in ("L", "F"):
        for population, depths in (("P1", range(4, 16)), ("P2", range(51, 61))):
            for depth in depths:
                case = {"reading": reading, "population": population, "depth": depth}
                heldouts.append({"case": case, "case_sha256": sha(wire(case)), "response": solve(case, result)})
    result["heldouts"] = heldouts
    result["poisoned_request"] = solve({"request": "prove the fan is unbounded"}, result)
    if sha(executable.read_bytes()) != executable_sha or verify_sources() != before:
        raise ValueError("INPUT_IDENTITY_CHANGED_DURING_EXECUTION")
    result_bytes = wire(result)
    (run_dir / "result.json").write_bytes(result_bytes)
    receipt = {"schema": "paper011.g07-run-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": sha(MANIFEST.read_bytes()),
               "runner_sha256": sha(Path(__file__).read_bytes()), "native_executable": str(executable),
               "native_executable_sha256_before": executable_sha,
               "native_executable_sha256_after": sha(executable.read_bytes()),
               "argv": [str(executable)], "cwd": str(PAPER), "returncode": process.returncode,
               "native_request_sha256": sha(request), "native_stdout_sha256": sha(process.stdout),
               "native_stderr_sha256": sha(process.stderr), "result_sha256": sha(result_bytes),
               "native_seconds": process_seconds, "total_seconds": time.perf_counter() - started,
               "case_count": len(rows), "heldout_count": len(heldouts), "runtime": runtime,
               "finite_computation_gate": True, "empirical_differentiation_gate": False}
    build_receipt = json.loads((AREA / "build/receipt.json").read_bytes())
    if build_receipt["native_executable_sha256"] != executable_sha or build_receipt["source_manifest_sha256"] != sha(MANIFEST.read_bytes()):
        raise ValueError("NATIVE_BUILD_CUSTODY_MISMATCH")
    receipt["build_receipt_sha256"] = sha((AREA / "build/receipt.json").read_bytes())
    (run_dir / "receipt.json").write_bytes(wire(receipt))
    return receipt


def build(cargo: Path, rustc: Path, target: Path, host_directory: Path) -> dict:
    """One offline locked incremental build; existing host binaries are witnesses."""
    sources = verify_sources()
    cargo = cargo.resolve(strict=True)
    rustc = rustc.resolve(strict=True)
    environment = dict(os.environ)
    environment["RUSTC"] = str(rustc)
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    hosts = ["omega_symbol_game.exe", "solve_graph_phi1.exe", "verify_phi2.exe",
             "verify_phi3.exe", "verify_phi4.exe", "verify_wall_functionals.exe"]
    before = {name: sha((host_directory / name).read_bytes()) for name in hosts}
    control_paths = [NATIVE / "Cargo.toml", NATIVE / "src/main.rs", Path(__file__)]
    control_before = {str(path.relative_to(PAPER)): sha(path.read_bytes()) for path in control_paths}
    lock_argv = [str(cargo), "generate-lockfile", "--offline", "--manifest-path", str(NATIVE / "Cargo.toml")]
    lock_process = subprocess.run(lock_argv, cwd=PAPER, capture_output=True, check=False, timeout=60, env=environment)
    build_dir = AREA / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "lock_stdout.txt").write_bytes(lock_process.stdout)
    (build_dir / "lock_stderr.txt").write_bytes(lock_process.stderr)
    if lock_process.returncode:
        raise ValueError("OFFLINE_LOCK_GENERATION_FAILED:" + lock_process.stderr.decode("utf8", "replace"))
    metadata_argv = [str(cargo), "metadata", "--offline", "--locked", "--format-version", "1", "--manifest-path", str(NATIVE / "Cargo.toml")]
    metadata = subprocess.run(metadata_argv, cwd=PAPER, capture_output=True, check=True, env=environment)
    (build_dir / "metadata.json").write_bytes(metadata.stdout)
    packages = json.loads(metadata.stdout)["packages"]
    registry_packages = [row for row in packages if str(row.get("source", "")).startswith("registry+")]
    def registry_files():
        rows = []
        for package in registry_packages:
            root = Path(package["manifest_path"]).parent
            for path in sorted(root.rglob("*")):
                if path.is_symlink():
                    raise ValueError("REDIRECTED_REGISTRY_SOURCE")
                if path.is_file():
                    rows.append({"package": package["name"], "version": package["version"],
                                 "path": str(path), "sha256": sha(path.read_bytes())})
        return rows
    registry_before = registry_files()
    argv = [str(cargo), "build", "--offline", "--locked", "-j", "1", "--manifest-path",
            str(NATIVE / "Cargo.toml"), "--target-dir", str(target), "--bin", "paper011_native_genesis_g07"]
    started = time.perf_counter()
    process = subprocess.run(argv, cwd=PAPER, capture_output=True, check=False, timeout=180, env=environment)
    (build_dir / "stdout.txt").write_bytes(process.stdout)
    (build_dir / "stderr.txt").write_bytes(process.stderr)
    if process.returncode:
        raise ValueError("G07_NATIVE_BUILD_FAILED:" + process.stderr.decode("utf8", "replace"))
    after = {name: sha((host_directory / name).read_bytes()) for name in hosts}
    control_after = {str(path.relative_to(PAPER)): sha(path.read_bytes()) for path in control_paths}
    registry_after = registry_files()
    if before != after or sources != verify_sources() or control_before != control_after or registry_before != registry_after:
        raise ValueError("EXISTING_INPUT_BINARY_OR_SOURCE_CHANGED_DURING_BUILD")
    executable = target / "debug/paper011_native_genesis_g07.exe"
    receipt = {"schema": "paper011.g07-build-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": sha(MANIFEST.read_bytes()), "controls_before": control_before,
               "controls_after": control_after, "cargo_path": str(cargo), "cargo_sha256": sha(cargo.read_bytes()),
               "cargo_version": subprocess.run([str(cargo), "--version"], capture_output=True, check=True).stdout.decode().strip(),
               "rustc_path": str(rustc), "rustc_sha256": sha(rustc.read_bytes()),
               "rustc_version": subprocess.run([str(rustc), "--version"], capture_output=True, check=True).stdout.decode().strip(),
               "registry_files_before": registry_before, "registry_files_after": registry_after,
               "metadata_argv": metadata_argv, "metadata_sha256": sha(metadata.stdout),
               "lock_generation_argv": lock_argv, "lock_generation_returncode": lock_process.returncode,
               "lock_stdout_sha256": sha(lock_process.stdout), "lock_stderr_sha256": sha(lock_process.stderr),
               "cargo_lock_sha256": sha((NATIVE / "Cargo.lock").read_bytes()),
               "argv": argv, "cwd": str(PAPER), "returncode": process.returncode,
               "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
               "seconds": time.perf_counter() - started,
               "native_executable": str(executable), "native_executable_sha256": sha(executable.read_bytes()),
               "existing_host_directory": str(host_directory), "existing_hosts_before": before,
               "existing_hosts_after": after}
    (build_dir / "receipt.json").write_bytes(wire(receipt))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="action", required=True)
    recover_parser = subs.add_parser("recover")
    recover_parser.add_argument("--external", type=Path, required=True)
    recover_parser.add_argument("--estate", type=Path, required=True)
    subs.add_parser("verify")
    build_parser = subs.add_parser("build")
    build_parser.add_argument("--cargo", type=Path, required=True)
    build_parser.add_argument("--rustc", type=Path, required=True)
    build_parser.add_argument("--target", type=Path, required=True)
    build_parser.add_argument("--host-directory", type=Path, required=True)
    run_parser = subs.add_parser("run")
    run_parser.add_argument("--executable", type=Path, required=True)
    run_parser.add_argument("--interpreter", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "recover":
        result = recover(args.external, args.estate)
        print(json.dumps({"files": len(result["entries"]), "bytes": sum(row["bytes"] for row in result["entries"])}))
    elif args.action == "verify":
        print(json.dumps({"files_verified": len(verify_sources()["entries"])}))
    elif args.action == "build":
        result = build(args.cargo, args.rustc, args.target, args.host_directory)
        print(json.dumps({key: value for key, value in result.items() if key not in ("registry_files_before", "registry_files_after")}, indent=2))
    else:
        print(json.dumps(run(args.executable, args.interpreter), indent=2))


if __name__ == "__main__":
    main()
