"""Source-pinned provider-free reconstruction of the original G01 contract."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
PACKAGE = PAPER / "code/native_genesis_g01"
AREA = PAPER / "docs/history_recovery/g01"
SEALED = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
HEAD = "b55fc96a94740b0afde78337350a96d293615f3f"
TOOLCHAIN = Path("C:/Users/a343o/source/repos/.elan/toolchains/leanprover--lean4---v4.33.0")
REPOSITORY = PAPER.parents[3]
RUSTC = Path("C:/Users/a343o/source/repos/.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin/rustc.exe")
DEPS = REPOSITORY / ".artifacts/epic0-cargo/debug/deps"
BUILD = REPOSITORY / ".artifacts/paper011-g01lean"
WHITELIST = {"propext", "Quot.sound"}
PYTHON_EXE = Path("C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0/python.exe")
PYTHON_SHA = "5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wire(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def git(repository: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repository), *args], check=True,
                          capture_output=True, timeout=30).stdout


def recover(repository: Path) -> dict:
    paths = [(SEALED, "lean4/Derivation/" + name + ".lean")
             for name in ("Basic", "Inertia", "Minimality")]
    paths += [(HEAD, "lean4/Derivation/" + name + ".lean")
              for name in ("Mention", "MinimalityF")]
    paths += [(SEALED, "code/derivation/" + name + ".py")
              for name in ("__init__", "model", "observe", "candidates", "iso", "engine")]
    paths += [(SEALED, "artifacts/challenges.json")]
    rows = []
    for commit, path in paths:
        blob = git(repository, "rev-parse", commit + ":" + path).decode().strip()
        data = git(repository, "cat-file", "blob", blob)
        calculated = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if calculated != blob:
            raise ValueError("GIT_BLOB_MISMATCH")
        destination = PACKAGE / "original" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError("RECOVERY_WOULD_REPLACE_DIFFERENT_BYTES:" + path)
        destination.write_bytes(data)
        row = {"commit": commit, "source_path": path, "git_blob": blob,
               "sha256": sha(data), "bytes": len(data),
               "path": destination.relative_to(PAPER).as_posix()}
        if path.startswith("lean4/Derivation/") and commit == SEALED:
            other = git(repository, "rev-parse", HEAD + ":" + path).decode().strip()
            if blob != other:
                raise ValueError("B55_DEFINITION_NOT_BYTE_EQUIVALENT:" + path)
            row["b55_identical_blob"] = other
        rows.append(row)
    manifest = {"schema": "paper011.g01-source-manifest.v1", "AuthorityEffect": "None",
                "sealed_pin": SEALED, "head_pin": HEAD, "files": rows,
                "scope": "Five unchanged original Lean modules and the sealed finite Python import closure; no estate mutation."}
    AREA.mkdir(parents=True, exist_ok=True)
    (AREA / "source_manifest.json").write_bytes(wire(manifest))
    return {"files": len(rows), "bytes": sum(row["bytes"] for row in rows),
            "manifest_sha256": sha(wire(manifest))}


def verify_sources() -> dict:
    raw = (AREA / "source_manifest.json").read_bytes()
    if sha(raw) != "d75572466b0950fab585e1d5150e73fdac28dbd336fc28c66ad729eed250e4ec":
        raise ValueError("SOURCE_MANIFEST_CHANGED")
    manifest = json.loads(raw)
    if manifest["sealed_pin"] != SEALED or manifest["head_pin"] != HEAD:
        raise ValueError("SOURCE_PIN_MISMATCH")
    for row in manifest["files"]:
        data = (PAPER / row["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != row["git_blob"] or sha(data) != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError("SOURCE_BYTES_MISMATCH:" + row["path"])
    return manifest


def execute(argv: list[str], stem: str, timeout: int = 600) -> dict:
    inputs = {str(Path(arg)): sha(Path(arg).read_bytes()) for arg in argv if Path(arg).is_file()}
    result = subprocess.run(argv, cwd=PACKAGE, capture_output=True, check=False, timeout=timeout)
    AREA.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = AREA / (stem + "_stdout.txt"), AREA / (stem + "_stderr.txt")
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    after = {path: sha(Path(path).read_bytes()) for path in inputs}
    if after != inputs:
        raise ValueError("PROCESS_INPUT_DRIFT")
    receipt = {"argv": argv, "cwd": str(PACKAGE), "returncode": result.returncode,
               "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
               "stdout_path": stdout_path.relative_to(PAPER).as_posix(),
               "stderr_path": stderr_path.relative_to(PAPER).as_posix(),
               "inputs_before": inputs, "inputs_after": after,
               "representation": "RAW_SUBPROCESS_BYTES"}
    (AREA / (stem + "_process.json")).write_bytes(wire(receipt))
    return receipt


def file_map(files: list[Path]) -> dict[str, str]:
    return {str(path): sha(path.read_bytes()) for path in sorted(set(files)) if path.is_file()}


def native_dependencies() -> dict:
    target = subprocess.run([str(RUSTC), "--print", "target-libdir"], check=True,
                            capture_output=True, timeout=30).stdout.decode().strip()
    paths = [*DEPS.glob("*.rlib"), *DEPS.glob("*.dll"), *DEPS.glob("*.lib"), RUSTC,
             *Path(target).glob("*.rlib"), *Path(target).glob("*.lib"),
             *RUSTC.parent.glob("*.dll"), PACKAGE / "second_checker.rs",
             Path(__file__).resolve(), PYTHON_EXE,
             *(REPOSITORY / "omega_engine/crates_rs/omega_ooutwire_primitives/src").rglob("*.rs"),
             REPOSITORY / "omega_engine/crates_rs/omega_ooutwire_primitives/Cargo.toml"]
    return file_map(paths)


def build_native(identity: str) -> dict:
    destination = AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    before = native_dependencies()
    primitive = DEPS / "libomega_ooutwire_primitives-7419c0b1b3d813be.rlib"
    serde = DEPS / "libserde_json-1a3e70913255bad6.rlib"
    executable = destination / "g01_second_checker.exe"
    argv = [str(RUSTC), "--edition", "2021", "--crate-name", "paper011_genesis_g01",
            str(PACKAGE / "second_checker.rs"), "-L", "dependency=" + str(DEPS),
            "--extern", "omega_ooutwire_primitives=" + str(primitive),
            "--extern", "serde_json=" + str(serde), "-o", str(executable)]
    result = subprocess.run(argv, cwd=PACKAGE, capture_output=True, check=False, timeout=300)
    after = native_dependencies()
    if before != after:
        raise ValueError("NATIVE_BUILD_INPUT_DRIFT")
    (destination / "stdout.bin").write_bytes(result.stdout)
    (destination / "stderr.bin").write_bytes(result.stderr)
    receipt = {"schema": "paper011.g01-native-build.v1", "AuthorityEffect": "None",
               "argv": argv, "returncode": result.returncode, "dependencies_before": before,
               "dependencies_after": after, "stdout_sha256": sha(result.stdout),
               "stderr_sha256": sha(result.stderr), "executable": str(executable),
               "executable_sha256": sha(executable.read_bytes()) if executable.exists() else None,
               "source_head": "526ffd1748941f1781c0ff584b7033b29088b405",
               "scope": "Existing native crate and exact archived dependencies, not a Cargo rebuild; OS/linker installation outside this archive manifest."}
    (destination / "receipt.json").write_bytes(wire(receipt))
    return {"returncode": result.returncode, "receipt_path": str(destination / "receipt.json")}


def load_original() -> object:
    verify_sources()
    if sha(PYTHON_EXE.read_bytes()) != PYTHON_SHA or sys.version_info[:2] != (3, 12):
        raise ValueError("PYTHON_INTERPRETER_IDENTITY_MISMATCH")
    sys.dont_write_bytecode = True
    sys.pycache_prefix = tempfile.mkdtemp(prefix="paper011-g01-empty-cache-")
    namespace = "paper011_g01_sealed_derivation"
    directory = PACKAGE / "original/code/derivation"
    if namespace in sys.modules:
        raise ValueError("ORIGINAL_NAMESPACE_ALREADY_LOADED")
    spec = importlib.util.spec_from_file_location(namespace, directory / "__init__.py",
                                                 submodule_search_locations=[str(directory)])
    if spec is None or spec.loader is None:
        raise ValueError("MISSING_SOURCE_LOADER")
    module = importlib.util.module_from_spec(spec)
    sys.modules[namespace] = module
    spec.loader.exec_module(module)
    from importlib import import_module
    return {name: import_module(namespace + "." + name)
            for name in ("model", "observe", "candidates", "iso", "engine")}


def python_finite(original: dict, reading: str, measure: str) -> dict:
    engine, candidate, iso, model = (original[name] for name in ("engine", "candidates", "iso", "model"))
    rd = engine.READING_F if reading == "F" else engine.READING_L
    base = model.replay(rd.genesis)
    mr = candidate.min_responses(base, rd.target, measure, candidate.Bounds(2, 2))
    if mr is None:
        raise ValueError("NO_ORIGINAL_MINIMUM")
    rows = []
    grouped = {}
    for delta in mr.deltas:
        child = model.replay((model.Impose(*rd.target),) + candidate.delta_events(base, delta), base)
        key, brute = iso.canonical(child), iso.canonical_bruteforce(child)
        items = engine.delta_json_items(delta)
        rows.append({"items": items, "key": key, "brute_key": brute})
        grouped.setdefault(key, []).append(items)
    full_valid = []
    for cost in range(3):
        full_valid += [engine.delta_json_items(delta) for delta in candidate.iter_full_deltas(base, cost, candidate.Bounds(2, 2))
                       if candidate.response_valid_naive(base, rd.target, delta)]
    # For mu1 the independently unpruned grammar must contain exactly the ten/six minima.
    if measure == "mu1" and sorted(wire(row["items"]) for row in rows) != sorted(wire(delta) for delta in full_valid):
        raise ValueError("PRUNED_ENUMERATION_DISAGREES_WITH_FULL_SPACE")
    for a in rows:
        for b in rows:
            if (a["key"] == b["key"]) != (a["brute_key"] == b["brute_key"]):
                raise ValueError("REFINED_BRUTE_PARTITION_DISAGREEMENT")
    return {"request": {"reading": reading, "measure": measure, "max_items": 2, "max_arity": 2},
            "cost": list(mr.cost) if measure == "mu2" else [mr.cost[0], -1], "deltas": rows,
            "classes": [{"key": key, "size": len(members)} for key, members in sorted(grouped.items())],
            "unpruned_valid_count": len(full_valid), "computation": "SOURCE_RECREATION_PYTHON"}


def normalize_finite(value: dict) -> dict:
    return json.loads(wire({"cost": value["cost"], "deltas": value["deltas"],
        "classes": [{"key": row["key"], "size": row["size"]} for row in value["classes"]]}))


def finite(identity: str, build_receipt: Path) -> dict:
    build = json.loads(build_receipt.read_bytes())
    if build["returncode"] or build["dependencies_before"] != build["dependencies_after"]:
        raise ValueError("UNVERIFIED_NATIVE_BUILD")
    for path, digest in build["dependencies_after"].items():
        if sha(Path(path).read_bytes()) != digest:
            raise ValueError("NATIVE_BUILD_DEPENDENCY_CHANGED:" + path)
    executable = Path(build["executable"])
    if sha(executable.read_bytes()) != build["executable_sha256"]:
        raise ValueError("NATIVE_EXECUTABLE_CHANGED")
    destination = AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    original = load_original()
    rows = []
    for reading in ("F", "L"):
        for measure in ("mu1", "mu2"):
            python = python_finite(original, reading, measure)
            stem = reading + "_" + measure
            request = wire(python["request"])
            result = subprocess.run([str(executable)], input=request, capture_output=True, check=False, timeout=60)
            native = json.loads(result.stdout)
            if result.returncode or native.get("status") != "COMPUTED" or native["request"] != python["request"]:
                raise ValueError("NATIVE_SECOND_CHECKER_REFUSED")
            if normalize_finite(native) != normalize_finite(python):
                raise ValueError("PYTHON_NATIVE_DISAGREEMENT")
            for suffix, data in (("request.json", request), ("stdout.bin", result.stdout), ("stderr.bin", result.stderr),
                                 ("python.json", wire(python))):
                (destination / (stem + "_" + suffix)).write_bytes(data)
            rows.append({"reading": reading, "measure": measure, "deltas": len(native["deltas"]),
                         "classes": len(native["classes"]), "cost": native["cost"],
                         "request_sha256": sha(request), "stdout_sha256": sha(result.stdout),
                         "stderr_sha256": sha(result.stderr), "python_sha256": sha(wire(python)),
                         "python_native_exact_match": True, "returncode": result.returncode})
    verify_sources()
    if native_dependencies() != build["dependencies_after"] or sha(executable.read_bytes()) != build["executable_sha256"]:
        raise ValueError("FINITE_POSTFLIGHT_DRIFT")
    receipt = {"schema": "paper011.g01-finite-receipt.v1", "AuthorityEffect": "None", "rows": rows,
               "build_receipt_sha256": sha(build_receipt.read_bytes()), "source_manifest_sha256": sha((AREA / "source_manifest.json").read_bytes()),
               "empty_cache_prefix": sys.pycache_prefix, "dont_write_bytecode": sys.dont_write_bytecode,
               "provider_calls": 0, "scope": "Declared finite max_items=2/max_arity=2; not the optional F-5+ Lean completeness theorem."}
    (destination / "receipt.json").write_bytes(wire(receipt))
    return receipt


def token_violations(source: str) -> list[str]:
    hits = sorted(set(re.findall(r"\b(?:sorry|admit|unsafe|partial)\b", source)))
    if re.search(r"(?m)^\s*axiom\b", source):
        hits.append("axiom-line")
    if re.search(r"(?m)^\s*import\s+Mathlib(?:\.|\s|$)", source):
        hits.append("outside-core-import")
    return hits


CANDIDATE_GUARD = '''
run_cmd do
  let ci ← liftTermElabM <| Lean.getConstInfo ``candidate
  unless ci.isTheorem do throwError "NOT_A_THEOREM"
  let expected ← liftTermElabM <| Lean.Meta.whnf (Lean.mkConst ``G01Targets.F1)
  let matched ← liftTermElabM <| Lean.Meta.isDefEq expected ci.type
  unless matched do throwError "STATEMENT_PIN_MISMATCH"
  let axioms ← liftCoreM <| Lean.collectAxioms ``candidate
  logInfo m!"G01_CANDIDATE_AXIOMS={Lean.Json.compress (Lean.toJson (axioms.map Lean.Name.toString))}"
  for a in axioms do
    unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {a}"
  logInfo "G01_CANDIDATE_ACCEPTED"
'''


def mutation_sources() -> dict[str, str]:
    preamble = "import G01Targets\nimport Lean\nopen Lean Elab Command\n"
    good = "theorem candidate : G01Targets.F1 := ResearchG01.F_1\n"
    return {
        "M01_comment": preamble + "-- sorry\n" + good,
        "M02_native_decide": preamble + '''theorem candidate : G01Targets.F1 := by
  have h : (0 : Nat) = 0 := by native_decide
  exact Eq.mp (congrArg (fun _ : Nat => G01Targets.F1) h) ResearchG01.F_1
''',
        "M03_classical_em": preamble + '''theorem candidate : G01Targets.F1 :=
  Or.elim (Classical.em G01Targets.F1) id
    (fun h => False.elim (h ResearchG01.F_1))
''',
        "M04_mathlib": "import Mathlib\n" + preamble + good,
        "M05_false_hypothesis": preamble + '''theorem candidate (h : False) : G01Targets.F1 := False.elim h
example : G01Targets.F1 := candidate
''',
        "M06_axiom_line": preamble + "axiom fabricated : G01Targets.F1\ntheorem candidate : G01Targets.F1 := fabricated\n",
        "M07_partial_def": preamble + "partial def loop : Nat := loop\n" + good,
        "VALID_CONTROL": preamble + good,
    }


def prepare_mutations(identity: str) -> dict[str, Path]:
    paths = {}
    for name, source in mutation_sources().items():
        path = PACKAGE / ("G01Mutation_" + identity + "_" + name + ".lean")
        data = (source + CANDIDATE_GUARD).encode()
        if path.exists() and path.read_bytes() != data:
            raise ValueError("WOULD_REPLACE_MUTATION_BYTES")
        path.write_bytes(data)
        paths[name] = path
    return paths


def run_mutations(paths: dict[str, Path], identity: str) -> list[dict]:
    rows = []
    expected = {"M02_native_decide": "DISALLOWED_AXIOM candidate._native.native_decide.ax_1_1",
                "M03_classical_em": "DISALLOWED_AXIOM Classical.choice",
                "M05_false_hypothesis": "STATEMENT_PIN_MISMATCH"}
    for name, path in paths.items():
        source = path.read_text(encoding="utf8")
        hits = token_violations(source)
        row = {"id": name, "source_path": path.relative_to(PAPER).as_posix(),
               "source_sha256": sha(path.read_bytes()), "token_hits": hits}
        if hits:
            row.update({"gate": "LEXICAL_CORE_GATE", "accepted": False, "compile_attempted": False})
        else:
            process = execute([str(TOOLCHAIN / "bin/lake.exe"), "env", "lean",
                               "--root=" + str(PACKAGE), str(path)], identity + "_" + name)
            output = (PAPER / process["stdout_path"]).read_text(encoding="utf8")
            if name == "VALID_CONTROL":
                accepted = process["returncode"] == 0 and "G01_CANDIDATE_ACCEPTED" in output
                if not accepted:
                    raise ValueError("VALID_SELF_CONTROL_REJECTED")
            else:
                accepted = process["returncode"] == 0
                if accepted or expected[name] not in output:
                    raise ValueError("MUTATION_DID_NOT_HIT_EXACT_GATE:" + name)
            row.update({"gate": "NATIVE_LEAN_AXIOM_AND_STATEMENT_PIN", "accepted": accepted,
                        "compile_attempted": True, "process": process,
                        "expected_gate_error": expected.get(name)})
        rows.append(row)
    return rows


def lean_runtime_inputs(*, include_local: bool) -> dict:
    if sha(PYTHON_EXE.read_bytes()) != PYTHON_SHA or sys.version_info[:2] != (3, 12):
        raise ValueError("PYTHON_INTERPRETER_IDENTITY_MISMATCH")
    paths = [Path(__file__).resolve(), PYTHON_EXE, AREA / "source_manifest.json",
             PAPER / "docs/history_recovery/recovered_sources/g01_reading_f_nonuniqueness_lean.md",
             *PACKAGE.rglob("*.lean"), *PACKAGE.rglob("*.py"), PACKAGE / "lakefile.toml",
             PACKAGE / "lean-toolchain", *TOOLCHAIN.joinpath("bin").iterdir()]
    installed = TOOLCHAIN / "lib/lean"
    paths += [p for p in installed.rglob("*") if p.is_file() and
              (".olean" in p.name or p.suffix in {".ir", ".dll", ".lib"})]
    if include_local:
        paths += [p for p in (BUILD / "lib/lean").rglob("*") if p.is_file() and ".olean" in p.name]
    return file_map(paths)


def output_marker(process: dict, marker: str) -> object:
    data = (PAPER / process["stdout_path"]).read_bytes()
    if process["returncode"] or sha(data) != process["stdout_sha256"]:
        raise ValueError("FAILED_OR_UNBOUND_JUDGE_OUTPUT")
    lines = [line.split(marker, 1)[1] for line in data.decode().splitlines() if marker in line]
    if len(lines) != 1:
        raise ValueError("MISSING_OR_DUPLICATE_MARKER:" + marker)
    return json.loads(lines[0])


def prove(identity: str) -> dict:
    destination = AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    verify_sources()
    mutations = prepare_mutations(identity)
    for name in ("ResearchG01.lean", "G01Targets.lean"):
        if token_violations((PACKAGE / name).read_text(encoding="utf8")):
            raise ValueError("POSITIVE_SOURCE_FAILED_TOKEN_GATE")
    before = lean_runtime_inputs(include_local=False)
    (destination / "inputs_before.json").write_bytes(wire(before))
    clean = execute([str(TOOLCHAIN / "bin/lake.exe"), "clean"], identity + "_clean")
    if clean["returncode"]:
        raise ValueError("CLEAN_FAILED")
    build = execute([str(TOOLCHAIN / "bin/lake.exe"), "build"], identity + "_build")
    if build["returncode"]:
        raise ValueError("FULL_CLEAN_BUILD_FAILED")
    if before != lean_runtime_inputs(include_local=False):
        raise ValueError("BUILD_SOURCE_OR_TOOLCHAIN_DRIFT")
    runtime_before = lean_runtime_inputs(include_local=True)
    judge = execute([str(TOOLCHAIN / "bin/lake.exe"), "env", "lean", "--root=" + str(PACKAGE),
                     str(PACKAGE / "G01Judge.lean")], identity + "_judge")
    census = output_marker(judge, "G01_CENSUS=")
    axioms = output_marker(judge, "G01_AXIOMS=")
    pins = output_marker(judge, "G01_PINS=")
    if len(pins) != 11 or not all(row["matched"] for row in pins):
        raise ValueError("INCOMPLETE_OR_FAILED_TARGET_PINS")
    names = [row["name"] for row in census]
    if len(names) != len(set(names)):
        raise ValueError("DUPLICATE_ENVIRONMENT_CONSTANT")
    expected_theorems = {row["name"] for row in census if row["is_theorem"]}
    if expected_theorems != {row["name"] for row in axioms}:
        raise ValueError("AXIOM_CENSUS_INCOMPLETE")
    if any(not set(row["axioms"]) <= WHITELIST for row in axioms):
        raise ValueError("AXIOM_WHITELIST_FAILURE")
    controls = run_mutations(mutations, identity)
    runtime_after = lean_runtime_inputs(include_local=True)
    if runtime_before != runtime_after:
        raise ValueError("LEAN_RUNTIME_OR_SOURCE_DRIFT")
    for name, value in (("census.json", census), ("axioms.json", axioms), ("pins.json", pins),
                        ("mutations.json", controls), ("runtime_before.json", runtime_before),
                        ("runtime_after.json", runtime_after)):
        (destination / name).write_bytes(wire(value))
    outputs = file_map(list(destination.iterdir()))
    receipt = {"schema": "paper011.g01-provider-free-theorem-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": sha((AREA / "source_manifest.json").read_bytes()),
               "source_pin": SEALED, "mu2_witness_pin": HEAD,
               "original_spec_sha256": sha((PAPER / "docs/history_recovery/recovered_sources/g01_reading_f_nonuniqueness_lean.md").read_bytes()),
               "target_source_sha256": sha((PACKAGE / "G01Targets.lean").read_bytes()),
               "clean_build": clean["returncode"] == 0 and build["returncode"] == 0,
               "processes": [clean, build, judge], "outputs": outputs,
               "theorems": len(axioms), "environment_constants": len(census), "target_pins": len(pins),
               "axiom_whitelist": sorted(WHITELIST), "all_axioms_within_whitelist": True,
               "heldouts": [{"id": "H" + str(i).zfill(2), "outcome": "SOLVED" if i <= 5 else "OUT_OF_SCOPE",
                             "witness": pins[i + 2]["proof"]} for i in range(1, 9)],
               "mutations_rejected": sum(not row["accepted"] for row in controls if row["id"] != "VALID_CONTROL"),
               "valid_control_accepted": next(row["accepted"] for row in controls if row["id"] == "VALID_CONTROL"),
               "runtime_before_sha256": sha(wire(runtime_before)), "runtime_after_sha256": sha(wire(runtime_after)),
               "provider_calls": 0, "model_accuracy_gate": False, "owner_pr_gate": False,
               "estate_twelve_family_gate": False, "F5_plus_Lean_exact_class_gate": False,
               "scope": "Literal reconstructed G01 target signatures at original definitions; original prose supplies eight obligation descriptions but no retained frozen TASK packet. Full local theorem/finite gates remain separate from original model, estate and owner-PR requirements. OS/Python stdlib outside custody."}
    (destination / "receipt.json").write_bytes(wire(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("recover", "build", "lean", "build-native", "finite", "prove"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--file", default="ResearchG01.lean")
    parser.add_argument("--identity", default="proof_diagnostic_v1")
    parser.add_argument("--build-receipt", type=Path)
    args = parser.parse_args()
    if args.action == "recover":
        print(json.dumps(recover(args.repository)))
        return 0
    verify_sources()
    if args.action == "prove":
        result = prove(args.identity)
        print(json.dumps({key: result[key] for key in ("clean_build", "theorems", "target_pins", "mutations_rejected", "valid_control_accepted")}))
        return 0
    if args.action == "build-native":
        result = build_native(args.identity)
        print(json.dumps(result))
        return result["returncode"]
    if args.action == "finite":
        result = finite(args.identity, args.build_receipt)
        print(json.dumps(result["rows"]))
        return 0
    if args.action == "build":
        result = execute([str(TOOLCHAIN / "bin/lake.exe"), "build"], args.identity)
    else:
        result = execute([str(TOOLCHAIN / "bin/lake.exe"), "env", "lean",
                          "--root=" + str(PACKAGE), str(PACKAGE / args.file)], args.identity)
    print(json.dumps({"returncode": result["returncode"], "identity": args.identity}))
    return result["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
