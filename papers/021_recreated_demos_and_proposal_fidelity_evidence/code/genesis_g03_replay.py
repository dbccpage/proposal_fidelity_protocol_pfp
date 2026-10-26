"""Source-faithful G03 orchestration, explicit native checking, and byte custody."""
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
AREA = PAPER / "docs/history_recovery/g03"
NATIVE = PAPER / "code/native_genesis_g03"
SEALED = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
RESEARCH = "b55fc96a94740b0afde78337350a96d293615f3f"
PINS = {
    "code/derivation/generator.py": (SEALED, "c0c17042b76aee831d4aa4f243ccec0699692bec"),
    "paper/paper_claim_ledger.md": (RESEARCH, "b91e39703644985e1c62f158d01ca46ce9c78ce8"),
    "paper/paper_change_log.md": (RESEARCH, "86cfecebc6c8195eb84dd582fa31b01566c4c2d9"),
    "research/g1_local_class/STATUS.md": (RESEARCH, "d85086fcfab3bb1776126f4d37b52a578c89fc17"),
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("MISSING_EXPLICIT_MODULE_PORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


source = load("_paper011_g03_g07_source_port", PAPER / "code/genesis_g07_replay.py")
adapter = load("_paper011_g03_adapter", PAPER / "code/genesis_g03_adapter.py")
sha, wire = source.sha, source.wire


def recover(repository: Path) -> dict:
    records = []
    for path, (pin, expected) in PINS.items():
        data = source.git(repository, "cat-file", "blob", expected)
        if source.git(repository, "rev-parse", pin + ":" + path).decode().strip() != expected or source.blob(data) != expected:
            raise ValueError("G03_FIXED_BLOB_MISMATCH")
        target = AREA / "pinned_sources" / path
        source.write(target, data)
        records.append({"source": path, "commit": pin, "blob": expected, "sha256": sha(data),
                        "bytes": len(data), "local": target.relative_to(PAPER).as_posix()})
    original = source.git(repository, "rev-parse", RESEARCH + ":code/derivation/generator.py").decode().strip()
    if original != PINS["code/derivation/generator.py"][1]:
        raise ValueError("GENERATOR_NOT_IDENTICAL_AT_BOTH_PINS")
    result = {"schema": "paper011.g03-fixed-source.v1", "AuthorityEffect": "None", "entries": records,
              "unchanged_source_port": "code/genesis_g07_replay.py",
              "source_port_sha256": sha((PAPER / "code/genesis_g07_replay.py").read_bytes()),
              "source_dependency_manifest_sha256": source.SOURCE_MANIFEST_SHA256}
    (AREA / "source_manifest.json").write_bytes(wire(result))
    return result


def verify_sources() -> dict:
    manifest = json.loads((AREA / "source_manifest.json").read_bytes())
    if manifest["source_dependency_manifest_sha256"] != source.SOURCE_MANIFEST_SHA256:
        raise ValueError("G03_SOURCE_DEPENDENCY_CHANGED")
    if manifest["unchanged_source_port"] != "code/genesis_g07_replay.py" or manifest["source_port_sha256"] != "d14a646af554e9f90a490bff23097bf7ec48a28c4942b8ecc59f05af0f65eb19" or manifest["source_port_sha256"] != sha((PAPER / manifest["unchanged_source_port"]).read_bytes()):
        raise ValueError("G03_SOURCE_PORT_CHANGED")
    source.verify_sources()
    if len(manifest["entries"]) != len(PINS) or {row["source"] for row in manifest["entries"]} != set(PINS):
        raise ValueError("G03_SOURCE_SET_CHANGED")
    for row in manifest["entries"]:
        data = (PAPER / row["local"]).read_bytes()
        if (row["commit"], row["blob"]) != PINS[row["source"]] or (source.blob(data), sha(data), len(data)) != (row["blob"], row["sha256"], row["bytes"]):
            raise ValueError("G03_SOURCE_BYTES_CHANGED")
    return manifest


def preregister() -> dict:
    verify_sources()
    record = {"schema": "paper011.g03-declaration.v1", "AuthorityEffect": "None", "adapter_id": adapter.ADAPTER_ID,
              "operator_written_new_structure": True, "historical_adapter_reconstruction": False,
              "original_model_arms_executed": [], "original_Arm_E_success": False,
              "primary_chains": list(adapter.PRIMARY), "held_out_chains": list(adapter.HELD_OUT),
              "readings": ["L", "F"], "measures": ["mu1", "mu2"], "max_items": 2, "max_arity": 2,
              "target_map": "0 and n occupy the original <a>/<ab> positions; each interior i maps to i+1 in L or i+2 in F; F keeps <> at0",
              "anchors": "k=(n-1).bit_length extra admitted data; k unary prefix marker forms identify them observationally; bit i links interior i to anchors through already-satisfied separation requirements",
              "structural_effect": "Requirements are excluded from collapse but included in canonical keys. Anchor incidence distinguishes interiors canonically. This declared extra structure changes available repair classes; it is not the historical bare map.",
              "prefixes": "Original L/F genesis histories remain verbatim prefixes; no uniform rules are added",
              "collapse_scope": "Equivalence checked on ALL unordered pairs of original chain elements, not pair count only; auxiliary anchor and F inscription observations are distinct",
              "predicates": {"class_fresh_mark": "At least one member is exactly NewForm(1) plus NewInst(new form,[larger adapted target]); no data or rule admission",
                             "weak": "exists retained canonical minimum class with class_fresh_mark",
                             "strong": "every retained canonical minimum class has class_fresh_mark"},
              "controls": ["full carrier token renaming", "chain-reversal data bijection", "poisoned collapse adapter",
                           "fixed target injection and restoration", "dropped/duplicated pair", "raw deltas used as classes", "stale script receipt"],
              "registered_files": {str(path.relative_to(PAPER)): sha(path.read_bytes()) for path in
                                   (PAPER / "code/genesis_g03_adapter.py", NATIVE / "transport.rs")},
              "source_manifest_sha256": sha((AREA / "source_manifest.json").read_bytes()),
              "no_g03_engine_oracle_invoked_before_this_declaration": True}
    path = AREA / "preregistration.json"
    source.write(path, wire(record))
    return record


def declaration() -> dict:
    record = json.loads((AREA / "preregistration.json").read_bytes())
    for path, expected in record["registered_files"].items():
        if sha((PAPER / path).read_bytes()) != expected:
            raise ValueError("PREREGISTERED_ADAPTER_OR_PREDICATE_CHANGED")
    if record["source_manifest_sha256"] != sha((AREA / "source_manifest.json").read_bytes()):
        raise ValueError("PREREGISTERED_SOURCE_CHANGED")
    return record


def original():
    verify_sources()
    modules = source.load_original()
    modules["generator"] = load("_paper011_g03_original_generator", AREA / "pinned_sources/code/derivation/generator.py")
    return modules


def primary_cases(modules: dict, include_controls: bool = True) -> list:
    cases = []
    generator, observe, iso, model = (modules[name] for name in ("generator", "observe", "iso", "model"))
    variants = ("base", "token_renaming", "reversal") if include_controls else ("base",)
    for n in adapter.PRIMARY + adapter.HELD_OUT:
        pairs = generator.obstructions("none", n, {})
        for reading in ("L", "F"):
            regime, history = adapter.construct(modules, n, reading)
            expected = {tuple(sorted((adapter.coordinate(n, reading, i), adapter.coordinate(n, reading, j)))) for i, j in pairs}
            observed = set(observe.collapsed_pairs(regime))
            if observed != expected:
                raise ValueError("COLLAPSE_EQUIVALENCE_FAILED")
            all_pairs = [(i, j) for i in range(n + 1) for j in range(i + 1, n + 1)]
            mapped = [tuple(sorted((adapter.coordinate(n, reading, i), adapter.coordinate(n, reading, j)))) for i, j in all_pairs]
            if len(mapped) != len(set(mapped)) or any((tuple(sorted((adapter.coordinate(n, reading, i), adapter.coordinate(n, reading, j)))) in observed) != ((i, j) in pairs) for i, j in all_pairs):
                raise ValueError("FULL_PAIR_INJECTIVITY_OR_COLLAPSE_FAILED")
            for variant in variants:
                if variant == "token_renaming":
                    current = model.Regime(tuple("renamed:" + token for token in regime.data), regime.forms, regime.insts, regime.rules, regime.reqs)
                elif variant == "reversal":
                    current = iso.rename(regime, adapter.reversal(n, reading, len(regime.data)), tuple(range(len(regime.forms))))
                else:
                    current = regime
                for measure in ("mu1", "mu2"):
                    for i, j in pairs:
                        target = tuple(sorted((adapter.coordinate(n, reading, i), adapter.coordinate(n, reading, j))))
                        if variant == "reversal":
                            pi = adapter.reversal(n, reading, len(regime.data))
                            target = tuple(sorted((pi[target[0]], pi[target[1]])))
                        cases.append({"id": f"{n}:{i}:{j}:{reading}:{measure}:{variant}", "n": n, "i": i, "j": j,
                                      "reading": reading, "measure": measure, "variant": variant,
                                      "population": "primary" if n <= 15 else "held_out", "target": list(target),
                                      "state": source.state(current), "history": [source.event_wire(event) for event in history]})
    return cases


def check_calls(cases: list, calls: list) -> None:
    expected = {case["id"]: case for case in cases}
    if len(expected) != len(cases) or len(calls) != len(cases) or len({call["id"] for call in calls}) != len(calls):
        raise ValueError("CALL_POPULATION_INCOMPLETE_OR_DUPLICATED")
    for call in calls:
        want = expected.get(call["id"])
        if want is None or any(want[key] != call[key] for key in ("n", "i", "j", "reading", "measure", "variant", "target")):
            raise ValueError("FIXED_TARGET_REUSE_OR_ADAPTER_MISMATCH")
        if call["predicate_domain"] != "canonical_classes":
            raise ValueError("PREDICATES_NOT_ON_CLASSES")
        classes = call["classes"]
        if len({wire(row["key"]) for row in classes}) != len(classes) or sum(row["size"] for row in classes) != call["raw_count"]:
            raise ValueError("RAW_DELTAS_USED_AS_CLASSES")
        if call["weak"] != any(row["fresh_mark"] for row in classes) or call["strong"] != all(row["fresh_mark"] for row in classes):
            raise ValueError("CLASS_PREDICATE_MISMATCH")


def build(rustc: Path, primitive: Path, json_library: Path, executable: Path) -> dict:
    verify_sources()
    quiet_receipt = source.AREA / "quiet_v1/receipt.json"
    if sha(quiet_receipt.read_bytes()) != "41bb04c9be8a7264ebfe730885056e6b585aea5b6cb9460b42eb04658c2a9152":
        raise ValueError("ORIGINAL_NATIVE_LIBRARY_CUSTODY_CHANGED")
    known = json.loads(quiet_receipt.read_bytes())["libraries_before"]
    for path in (primitive, json_library):
        if sha(path.read_bytes()) != known.get(str(path.resolve())):
            raise ValueError("UNBOUND_NATIVE_LIBRARY")
    dependencies = sorted({primitive, json_library, *(primitive.parent.glob("libserde*.rlib")),
                           *(primitive.parent.glob("libitoa*.rlib")), *(primitive.parent.glob("libmemchr*.rlib")),
                           *(primitive.parent.glob("libzmij*.rlib"))})
    before = {str(path): sha(path.read_bytes()) for path in dependencies}
    argv = [str(rustc), "--edition", "2021", "--crate-name", "paper011_native_genesis_g03", str(NATIVE / "transport.rs"),
            "-L", "dependency=" + str(primitive.parent), "--extern", "omega_ooutwire_primitives=" + str(primitive),
            "--extern", "serde_json=" + str(json_library), "-o", str(executable)]
    start = time.perf_counter()
    process = subprocess.run(argv, cwd=PAPER, capture_output=True, check=False, timeout=60)
    (AREA / "build_stdout.txt").write_bytes(process.stdout)
    (AREA / "build_stderr.txt").write_bytes(process.stderr)
    after = {str(path): sha(path.read_bytes()) for path in dependencies}
    if process.returncode or before != after:
        raise ValueError("G03_NATIVE_BUILD_FAILED_OR_DEPENDENCY_CHANGED")
    receipt = {"schema": "paper011.g03-build.v1", "argv": argv, "cwd": str(PAPER), "returncode": process.returncode,
               "seconds": time.perf_counter() - start, "rustc_sha256": sha(rustc.read_bytes()),
               "transport_sha256": sha((NATIVE / "transport.rs").read_bytes()),
               "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
               "dependencies_before": before, "dependencies_after": after,
               "native_executable": str(executable), "native_executable_sha256": sha(executable.read_bytes()),
               "fixed_source_manifest_sha256": source.SOURCE_MANIFEST_SHA256,
               "original_dependency_build_receipt_sha256": sha((source.AREA / "build/receipt.json").read_bytes())}
    (AREA / "build_receipt.json").write_bytes(wire(receipt))
    return receipt


def regime(modules: dict, state: dict):
    return modules["model"].Regime(tuple(state["data"]), tuple(state["forms"]),
        frozenset((form, tuple(args)) for form, args in state["insts"]),
        frozenset(state["rules"]), frozenset(tuple(pair) for pair in state["reqs"]))


def reference(modules: dict, cases: list) -> tuple[list, list]:
    records, log = [], []
    candidates, iso, model, engine = (modules[name] for name in ("candidates", "iso", "model", "engine"))
    cached = {}
    for case in cases:
        if case["variant"] != "base":
            continue
        identity = (case["n"], case["reading"])
        if identity not in cached:
            base = regime(modules, case["state"])
            cached[identity] = (base, iso.canonical(base))
        base, key = cached[identity]
        target = tuple(case["target"])
        measure = case["measure"]
        # This records arguments of the actual unchanged sealed function call.
        log.append({"id": case["id"], "base_canonical_key": key, "target": target,
                    "measure": case["measure"], "bounds": {"max_items": 2, "max_arity": 2}})
        mr = candidates.min_responses(base, target, measure, candidates.Bounds(2, 2))
        if mr is None:
            raise ValueError("NO_RESPONSE_IN_DECLARED_BOUNDS")
        grouped = {}
        for delta in mr.deltas:
            child = model.replay((model.Impose(*target),) + candidates.delta_events(base, delta), base)
            grouped.setdefault(iso.canonical(child), []).append(delta)
        standard = engine._quotient(base, target, mr)
        classes = [{"key": class_key, "size": len(members),
                    "representative": engine.delta_json_items(members[0]),
                    "members": [engine.delta_json_items(delta) for delta in members],
                    "fresh_mark": any(adapter.fresh_mark(base, target, delta, candidates) for delta in members)}
                   for class_key, members in sorted(grouped.items())]
        if standard != [(members[0], len(members)) for _, members in sorted(grouped.items())]:
            raise ValueError("SOURCE_QUOTIENT_CENSUS_DISAGREEMENT")
        cost = mr.cost
        records.append({key: case[key] for key in ("id", "n", "i", "j", "reading", "measure", "variant", "target")} |
                       {"base_canonical_key": key, "cost": cost, "raw_count": len(mr.deltas),
                        "raw_deltas": [engine.delta_json_items(delta) for delta in mr.deltas], "classes": classes,
                        "predicate_domain": "canonical_classes", "weak": any(c["fresh_mark"] for c in classes),
                        "strong": all(c["fresh_mark"] for c in classes)})
        if len(records) % 256 == 0:
            print(f"G03 sealed reference: {len(records)} actual oracle calls", flush=True)
    # JSON normalization makes native/source tuple encodings comparable.
    return json.loads(wire(records)), json.loads(wire(log))


def native(executable: Path, request: dict, stem: str, timeout: int = 600) -> tuple[dict | None, dict]:
    raw = wire(request)
    start = time.perf_counter()
    process = subprocess.run([str(executable)], cwd=PAPER, input=raw, capture_output=True, check=False, timeout=timeout)
    (AREA / (stem + "_request.json")).write_bytes(raw)
    (AREA / (stem + "_stdout.json")).write_bytes(process.stdout)
    (AREA / (stem + "_stderr.txt")).write_bytes(process.stderr)
    receipt = {"argv": [str(executable)], "cwd": str(PAPER), "returncode": process.returncode,
               "seconds": time.perf_counter() - start, "request_sha256": sha(raw),
               "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr)}
    (AREA / (stem + "_process.json")).write_bytes(wire(receipt))
    return (json.loads(process.stdout) if process.returncode == 0 else None), receipt


def match_native(cases: list, response: dict, expected: list) -> None:
    if response["schema"] != "paper011.g03-native-response.v1" or response["adapter_id"] != adapter.ADAPTER_ID:
        raise ValueError("NATIVE_RESPONSE_SCHEMA_OR_ADAPTER_CHANGED")
    check_calls(cases, response["calls"])
    by_id = {row["id"]: row for row in expected}
    for row in response["calls"]:
        base_id = row["id"].rsplit(":", 1)[0] + ":base"
        want = by_id[base_id]
        if row["variant"] == "base":
            if row != want:
                raise ValueError("INDEPENDENT_SOURCE_NATIVE_DISAGREEMENT:" + row["id"])
        else:
            for key in ("base_canonical_key", "cost", "raw_count", "weak", "strong"):
                if row[key] != want[key]:
                    raise ValueError("RELABEL_CONTROL_DISAGREEMENT:" + key)
            def signatures(classes):
                return [(c["key"], c["size"], c["fresh_mark"]) for c in classes]
            if signatures(row["classes"]) != signatures(want["classes"]):
                raise ValueError("RELABEL_CLASS_CERTIFICATE_DISAGREEMENT")


def controls(executable: Path, request: dict, response: dict, cases: list) -> list:
    controls = []
    # Actual native injections run on one public case; restoration is replayed.
    public = copy.deepcopy(request)
    public["cases"] = [request["cases"][0]]
    tests = {"FIXED_TARGET_REUSE": copy.deepcopy(public),
             "POISONED_COLLAPSE_ADAPTER": copy.deepcopy(public),
             "PREDICATES_NOT_ON_CLASSES": copy.deepcopy(public),
             "DUPLICATED_PAIR": copy.deepcopy(public)}
    tests["FIXED_TARGET_REUSE"]["cases"][0]["target"] = [0, 1]
    tests["POISONED_COLLAPSE_ADAPTER"]["cases"][0]["state"]["insts"].append([0, [public["cases"][0]["target"][0]]])
    tests["PREDICATES_NOT_ON_CLASSES"]["predicate_domain"] = "raw_deltas"
    tests["DUPLICATED_PAIR"]["cases"].append(copy.deepcopy(public["cases"][0]))
    reasons = {"FIXED_TARGET_REUSE": "FIXED_TARGET_REUSE",
               "POISONED_COLLAPSE_ADAPTER": "CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH",
               "PREDICATES_NOT_ON_CLASSES": "PREDICATES_NOT_ON_CLASSES", "DUPLICATED_PAIR": "DUPLICATE_PAIR_CASE"}
    for name, candidate in tests.items():
        _, process = native(executable, candidate, name.lower())
        reason = (AREA / (name.lower() + "_stderr.txt")).read_text(encoding="utf8").strip()
        if process["returncode"] == 0 or reason != reasons[name]:
            raise ValueError("SURVIVING_LIVE_NATIVE_INJECTION:" + name)
        controls.append({"mutation": name, "process": process,
                         "reason": reason})
    restored, process = native(executable, public, "restored_target")
    if process["returncode"] or restored["calls"] != response["calls"][:1]:
        raise ValueError("LIVE_INJECTION_RESTORATION_FAILED")
    controls.append({"mutation": "RESTORED_TARGET", "process": process, "reason": "VALID_CANDIDATE_PRESERVED"})
    candidates = {"DROPPED_PAIR": response["calls"][:-1],
                  "DUPLICATED_CALL_LOG": response["calls"] + response["calls"][:1]}
    raw = copy.deepcopy(response["calls"])
    first = next(row for row in raw if any(c["size"] > 1 for c in row["classes"]))
    first["classes"] = [dict(c, size=1, members=[member], representative=member)
                        for c in first["classes"] for member in c["members"]]
    candidates["RAW_DELTAS_AS_CLASSES"] = raw
    for name, calls in candidates.items():
        path = AREA / (name.lower() + "_mutation.json")
        path.write_bytes(wire(calls))
        try:
            check_calls(cases, calls)
        except ValueError as error:
            controls.append({"mutation": name, "reason": str(error), "mutation_path": path.relative_to(PAPER).as_posix(),
                             "mutation_sha256": sha(path.read_bytes())})
        else:
            raise ValueError("SURVIVING_CALL_CERTIFICATE_MUTATION:" + name)
    stale = copy.deepcopy(declaration())
    stale["registered_files"]["code/genesis_g03_adapter.py"] = "0" * 64
    path = AREA / "stale_script_receipt_mutation.json"
    path.write_bytes(wire(stale))
    try:
        for path, expected in stale["registered_files"].items():
            if sha((PAPER / path).read_bytes()) != expected:
                raise ValueError("STALE_SCRIPT_RECEIPT")
    except ValueError as error:
        controls.append({"mutation": "STALE_SCRIPT_RECEIPT", "reason": str(error),
                         "mutation_path": path.relative_to(PAPER).as_posix(), "mutation_sha256": sha(path.read_bytes())})
    else:
        raise ValueError("SURVIVING_STALE_SCRIPT_RECEIPT")
    return controls


def run(executable: Path, interpreter: Path) -> dict:
    if not sys.dont_write_bytecode or not sys.pycache_prefix:
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    cache = Path(sys.pycache_prefix)
    cache.mkdir(parents=True, exist_ok=True)
    if any(cache.iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    declared = declaration()
    manifest = verify_sources()
    build_receipt = json.loads((AREA / "build_receipt.json").read_bytes())
    if sha(executable.read_bytes()) != build_receipt["native_executable_sha256"] or sha((NATIVE / "transport.rs").read_bytes()) != build_receipt["transport_sha256"]:
        raise ValueError("NATIVE_BINARY_OR_SOURCE_CHANGED")
    for path, expected_hash in build_receipt["dependencies_after"].items():
        if sha(Path(path).read_bytes()) != expected_hash:
            raise ValueError("LINKED_NATIVE_DEPENDENCY_CHANGED")
    inputs = {str(path): sha(path.read_bytes()) for path in [Path(__file__), PAPER / "code/genesis_g03_adapter.py",
        NATIVE / "transport.rs", interpreter, executable, AREA / "source_manifest.json", AREA / "preregistration.json",
        AREA / "build_receipt.json", *(PAPER / entry["local"] for entry in manifest["entries"]),
        *(PAPER / entry["local"] for entry in source.verify_sources()["entries"]),
        *(Path(path) for path in build_receipt["dependencies_after"]),
        PAPER / "code/genesis_g07_replay.py", source.AREA / "source_manifest.json"]}
    started = time.perf_counter()
    modules = original()
    cases = primary_cases(modules)
    primary = [case for case in cases if case["population"] == "primary" and case["variant"] == "base"]
    held = [case for case in cases if case["population"] == "held_out" and case["variant"] == "base"]
    if len(primary) != 1820 or len(held) != 1444 or len(cases) != 9792:
        raise ValueError("DECLARED_CASE_POPULATION_MISMATCH")
    carriers = {}
    for case in cases:
        key = f"{case['n']}:{case['reading']}:{case['variant']}"
        carriers.setdefault(key, {"state": case["state"], "original_history": case["history"]})
    (AREA / "carriers.json").write_bytes(wire(carriers))
    request = {"schema": "paper011.g03-native-request.v1", "adapter_id": adapter.ADAPTER_ID,
               "predicate_domain": "canonical_classes", "cases": [{k: v for k, v in case.items() if k != "history"} for case in cases]}
    expected, call_log = reference(modules, cases)
    (AREA / "reference_rows.json").write_bytes(wire(expected))
    (AREA / "source_call_log.json").write_bytes(wire(call_log))
    source_seconds = time.perf_counter() - started
    response, process = native(executable, request, "full_native", timeout=900)
    if process["returncode"]:
        failure = {"status": "UNKNOWN", "reason": (AREA / "full_native_stderr.txt").read_text(encoding="utf8"),
                   "process": process, "complete_finite_gate": False, "preregistration_sha256": sha((AREA / "preregistration.json").read_bytes())}
        (AREA / "failure_receipt.json").write_bytes(wire(failure))
        raise ValueError("NATIVE_FINITE_RUN_FAILED")
    match_native(cases, response, expected)
    actual_primary = [row for row in response["calls"] if row["n"] <= 15 and row["variant"] == "base"]
    distinct = {(wire(row["base_canonical_key"]), tuple(row["target"]), row["measure"]) for row in actual_primary}
    if len(distinct) != 1820:
        raise ValueError("ACTUAL_PRIMARY_ORACLE_ARGUMENTS_NOT_DISTINCT")
    mutations = controls(executable, request, response, cases)
    terminal = {}
    for reading in ("L", "F"):
        for measure in ("mu1", "mu2"):
            rows = [r for r in actual_primary if r["reading"] == reading and r["measure"] == measure]
            terminal[reading + ":" + measure] = {predicate: next(([r["n"], r["i"], r["j"]] for r in rows if not r[predicate]), "holds on all 455")
                                                     for predicate in ("weak", "strong")}
    after = {path: sha(Path(path).read_bytes()) for path in inputs}
    if inputs != after:
        raise ValueError("G03_INPUT_CUSTODY_CHANGED")
    result = {"schema": "paper011.g03-finite-result.v1", "adapter_id": adapter.ADAPTER_ID, "status": "SOLVED",
              "primary_calls": actual_primary, "terminal_per_reading_measure": terminal,
              "held_out_calls": 1444, "relabel_and_reversal_calls": 6528, "native_calls": 9792,
              "model_arms_executed": [], "original_Arm_E_success": False,
              "scope": "New declared adapter, complete original finite check and controls. G4 in general remains open."}
    (AREA / "result.json").write_bytes(wire(result))
    receipt = {"schema": "paper011.g03-finite-receipt.v1", "AuthorityEffect": "None", "adapter_id": adapter.ADAPTER_ID,
               "source_manifest_sha256": sha((AREA / "source_manifest.json").read_bytes()),
               "preregistration_sha256": sha((AREA / "preregistration.json").read_bytes()),
               "build_receipt_sha256": sha((AREA / "build_receipt.json").read_bytes()),
               "runner_argv": sys.orig_argv, "runner_cwd": str(Path.cwd()),
               "python_launcher": sys.executable, "python_executable": str(interpreter), "python_version": sys.version,
               "dont_write_bytecode": sys.dont_write_bytecode, "cache_prefix": sys.pycache_prefix,
               "inputs_before": inputs, "inputs_after": after, "source_seconds": source_seconds, "native_process": process,
               "source_oracle_calls": len(call_log), "native_oracle_calls": len(cases), "primary_distinct_calls": len(distinct),
               "mutations": mutations, "terminal_per_reading_measure": terminal,
               "artifacts": {name: sha((AREA / name).read_bytes()) for name in
                             ("carriers.json", "reference_rows.json", "source_call_log.json", "result.json", "full_native_request.json", "full_native_stdout.json")},
               "complete_provider_free_finite_gate": True, "full_G03_model_experiment_completed": False,
               "entire_external_estate_workflow_executed": False, "external_owner_PR_created": False,
               "runtime_scope": "Actual Python backing executable; original fixed Python/native source closure; linked native binary/build libraries and authored adapter/transport. OS/Pythonstdlib outside declared scope.",
               "scope": declared["structural_effect"]}
    (AREA / "receipt.json").write_bytes(wire(receipt))
    return {"status": "SOLVED", "adapter_id": adapter.ADAPTER_ID, "rows_sha256": receipt["artifacts"]["result.json"],
            "terminal_per_reading_measure": terminal, "receipt_sha256": sha((AREA / "receipt.json").read_bytes()),
            "source_calls": len(call_log), "native_calls": len(cases)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("recover", "preregister", "build", "run"))
    for name in ("repository", "rustc", "primitive", "json-library", "executable", "interpreter"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if args.action == "recover":
        result = recover(args.repository)
    elif args.action == "preregister":
        result = preregister()
    elif args.action == "build":
        result = build(args.rustc, args.primitive, args.json_library, args.executable)
    else:
        result = run(args.executable, args.interpreter)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
