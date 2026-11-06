"""Original integer dossier replay through existing native homology owners."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
SOURCE = PAPER / "code/native_dossier_integral.rs"
HELPER = PAPER / "code/replay_dossier_homology.py"


def pinned_helper(build_receipt: Path) -> str:
    """Bind the shared transport before executing its module body."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_BUILD_KEY")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("NONFINITE_BUILD_VALUE")

    receipt = json.loads(build_receipt.read_bytes(), object_pairs_hook=unique, parse_constant=nonfinite)
    actual = hashlib.sha256(HELPER.read_bytes()).hexdigest()
    if receipt.get("returncode") != 0 or receipt.get("helper_sha256") != actual:
        raise ValueError("PRE_IMPORT_HELPER_PIN_MISMATCH")
    return actual


def build(args, helper) -> None:
    paths = sorted(args.deps.resolve().glob("*.rlib"), key=lambda p: p.name.encode())
    before = {str(p): helper.digest(p) for p in paths}
    source_before = helper.digest(SOURCE)
    (args.output / "source.rs").write_bytes(SOURCE.read_bytes())
    executable = args.output / "paper011_native_dossier_integral.exe"
    rustc = args.rustc.resolve(strict=True)
    argv = [str(rustc), "--edition", "2021", "--crate-name", "paper011_native_dossier_integral",
            str(SOURCE), "-L", f"dependency={args.deps.resolve()}"]
    for name, path in (("core_homology", args.homology_rlib), ("linear_algebra", args.algebra_rlib),
                       ("num_bigint", args.bigint_rlib), ("serde_json", args.serde_rlib)):
        path = path.resolve(strict=True)
        if str(path) not in before:
            raise ValueError("UNDECLARED_LIBRARY")
        argv.extend(["--extern", f"{name}={path}"])
    argv.extend(["-o", str(executable)])
    run = subprocess.run(argv, capture_output=True, check=False, cwd=PAPER, timeout=180)
    (args.output / "stdout.bin").write_bytes(run.stdout)
    (args.output / "stderr.bin").write_bytes(run.stderr)
    after = {str(p): helper.digest(p) for p in paths}
    receipt = {"schema": "paper011.dossier-integral-build.v1", "argv": argv, "cwd": str(PAPER),
               "rustc_sha256": helper.digest(rustc), "source_sha256": source_before,
               "runner_sha256": helper.digest(Path(__file__)), "helper_sha256": helper.digest(Path(helper.__file__)),
               "libraries_before": before, "libraries_after": after, "returncode": run.returncode,
               "stdout_sha256": helper.digest(args.output / "stdout.bin"),
               "stderr_sha256": helper.digest(args.output / "stderr.bin"), "AuthorityEffect": "None"}
    if executable.exists():
        receipt["executable_sha256"] = helper.digest(executable)
        receipt["executable"] = str(executable)
    helper.write(args.output / "receipt.json", receipt)
    if run.returncode or before != after or source_before != helper.digest(SOURCE):
        raise ValueError("BUILD_FAILED_OR_DRIFTED")
    print(json.dumps({"build_receipt": str(args.output / "receipt.json"), "returncode": run.returncode}))


def malformed_cases(cases: list[dict]) -> list[dict]:
    result = []
    for name in ("NONZERO_BOUNDARY", "FRACTIONAL_BOUNDARY", "RAGGED_BOUNDARY", "DROPPED_BOUNDARY"):
        case = copy.deepcopy(cases[0])
        case["case_id"] = name
        match name:
            case "NONZERO_BOUNDARY":
                case["matrices"][1][0][0] = "2"
            case "FRACTIONAL_BOUNDARY":
                case["matrices"][0][0][0] = "1/2"
            case "RAGGED_BOUNDARY":
                case["matrices"][0][0].pop()
            case "DROPPED_BOUNDARY":
                case["matrices"].pop(0)
        result.append(case)
    return result


def certificate_request(cases: list[dict], result: dict) -> dict:
    replay = []
    for case, row in zip(cases, result["cases"][:8], strict=True):
        if row["case_id"] != case["case_id"] or row.get("success") is not True:
            raise ValueError("ORIGINAL_CASE_REFUSAL_OR_BINDING")
        candidate = copy.deepcopy(case)
        candidate["certificates"] = [c["certificate"] for c in row["result"]["certificates"]]
        replay.append(candidate)
    controls = []
    for name in ("ZERO_U_ROW", "CORRUPT_D", "MISSING_CERTIFICATE", "FRACTIONAL_CERTIFICATE", "WRONG_CARRIER"):
        candidate = copy.deepcopy(replay[5] if name == "WRONG_CARRIER" else replay[0])
        candidate["case_id"] = name
        match name:
            case "ZERO_U_ROW":
                candidate["certificates"][0]["u"][0] = ["0"] * len(candidate["certificates"][0]["u"][0])
            case "CORRUPT_D":
                candidate["certificates"][0]["d"][0][0] = "999"
            case "MISSING_CERTIFICATE":
                candidate["certificates"].pop()
            case "FRACTIONAL_CERTIFICATE":
                candidate["certificates"][0]["u"][0][0] = "1/2"
            case "WRONG_CARRIER":
                candidate["matrices"][2][0] = ["3", "-3", "3", "-3"]
        controls.append(candidate)
    return {"cases": [*replay, *controls]}


def inspect_results(primary: dict, replay: dict, ids: tuple[str, ...]) -> dict:
    if primary.get("schema") != "paper011.dossier-integral-native.v1" or replay.get("schema") != primary["schema"]:
        raise ValueError("NATIVE_SCHEMA")
    originals = primary["cases"][:8]
    if [c["case_id"] for c in originals] != list(ids) or any(c.get("success") is not True for c in originals):
        raise ValueError("ORIGINAL_COMPLETENESS")
    if len(primary["cases"]) != 12 or any(c.get("success") is not False for c in primary["cases"][8:]):
        raise ValueError("INVALID_BOUNDARY_ACCEPTED")
    if [(c.get("case_id"), c.get("error")) for c in primary["cases"][8:]] != [
        ("NONZERO_BOUNDARY", "boundary maps do not compose to zero: d_1 d_2 != 0"),
        ("FRACTIONAL_BOUNDARY", "NONINTEGER"), ("RAGGED_BOUNDARY", "RAGGED_MATRIX"),
        ("DROPPED_BOUNDARY", "DECLARED_CARRIER_MISMATCH"),
    ]:
        raise ValueError("BOUNDARY_CONTROL_BINDING")
    if len(replay["cases"]) != 13 or [c["case_id"] for c in replay["cases"][:8]] != list(ids):
        raise ValueError("REPLAY_COMPLETENESS")
    if any(c.get("success") is not True or c["result"].get("certificates_verified") is not True for c in replay["cases"][:8]):
        raise ValueError("CERTIFICATE_REPLAY_REFUSAL")
    if any(c.get("success") is not False for c in replay["cases"][8:]):
        raise ValueError("CORRUPTED_CERTIFICATE_ACCEPTED")
    if [(c.get("case_id"), c.get("error")) for c in replay["cases"][8:]] != [
        ("ZERO_U_ROW", "NONUNIMODULAR_BASIS"), ("CORRUPT_D", "UAV_NE_D"),
        ("MISSING_CERTIFICATE", "CERTIFICATE_COMPLETENESS"),
        ("FRACTIONAL_CERTIFICATE", "NONINTEGER"), ("WRONG_CARRIER", "UAV_NE_D"),
    ]:
        raise ValueError("CERTIFICATE_CONTROL_BINDING")
    torsion = originals[5]["result"]["integral_homology"][2]
    if torsion["free_rank"] != 0 or torsion["torsion"] != ["2"]:
        raise ValueError("ORIGINAL_TORSION_CLAIM_MISMATCH")
    if any(c["result"].get("uct_verified") is not True for c in originals):
        raise ValueError("UCT_REFUSAL")
    return {"original_dossiers": 8, "boundary_controls_rejected": 4, "certificate_controls_rejected": 5,
            "actual_smith_certificates_replayed": sum(len(c["result"]["certificates"]) for c in originals),
            "results": [c["result"] for c in originals], "AuthorityEffect": "None"}


def run(args, helper) -> None:
    source_root = args.source_root.resolve(strict=True)
    sources = {name: source_root / name / "input.yaml" for name in helper.DOSSIERS}
    before = {name: helper.digest(path) for name, path in sources.items()}
    helper.check_source_pins(before)
    executable = args.executable.resolve(strict=True)
    executable_sha = helper.digest(executable)
    build_receipt = helper.strict(args.build_receipt.read_bytes())
    if (build_receipt.get("returncode") != 0 or build_receipt.get("executable_sha256") != executable_sha
            or build_receipt.get("source_sha256") != helper.digest(SOURCE)
            or build_receipt.get("libraries_before") != build_receipt.get("libraries_after")):
        raise ValueError("BUILD_BINDING")
    interpreter = args.interpreter.resolve(strict=True)
    if interpreter.parent != Path(sys.base_prefix).resolve(strict=True):
        raise ValueError("BACKING_INTERPRETER_MISMATCH")
    package = args.yaml_package.resolve(strict=True)
    if not (package / "__init__.py").is_file():
        raise ValueError("DECLARED_YAML_PACKAGE")
    runtime_paths = [interpreter, *sorted(package.glob("*.py")), *sorted(package.glob("*.pyd"))]
    custody_paths = [Path(__file__), Path(helper.__file__), SOURCE, args.build_receipt, executable, *runtime_paths]
    custody_before = {str(p): helper.digest(p) for p in custody_paths}
    spec = importlib.util.find_spec("yaml")
    if spec is None or spec.origin is None or Path(spec.origin).resolve(strict=True) != package / "__init__.py":
        raise ValueError("YAML_IMPORT_LOCATION_MISMATCH")
    import yaml  # noqa: PLC0415

    if Path(yaml.__file__).resolve(strict=True).parent != package:
        raise ValueError("YAML_LOADED_LOCATION_MISMATCH")
    cases = [helper.prepare_case(name, yaml.safe_load(path.read_bytes())) for name, path in sources.items()]
    for case in cases:
        case["carrier_dimensions"] = [len(case["matrices"][0][0]), *[len(m) for m in case["matrices"]]]

    def native(name, request):
        helper.write(args.output / f"{name}_request.json", request)
        execution = subprocess.run([str(executable)], input=(args.output / f"{name}_request.json").read_bytes(),
                                   capture_output=True, check=False, cwd=PAPER, timeout=120)
        (args.output / f"{name}_stdout.bin").write_bytes(execution.stdout)
        (args.output / f"{name}_stderr.bin").write_bytes(execution.stderr)
        helper.write(args.output / f"{name}_process.json", {"argv": [str(executable)], "cwd": str(PAPER),
                    "returncode": execution.returncode, "timeout_seconds": 120})
        if execution.returncode:
            raise ValueError("NATIVE_PROCESS_REFUSAL")
        return helper.strict(execution.stdout)

    primary = native("compute", {"cases": [*cases, *malformed_cases(cases)]})
    replay = native("replay", certificate_request(cases, primary))
    result = inspect_results(primary, replay, helper.DOSSIERS)
    after = {name: helper.digest(path) for name, path in sources.items()}
    custody_after = {str(p): helper.digest(p) for p in custody_paths}
    if before != after or custody_before != custody_after:
        raise ValueError("POST_EXECUTION_DRIFT")
    helper.write(args.output / "result.json", result)
    outputs = {p.name: helper.digest(p) for p in args.output.iterdir() if p.is_file()}
    helper.write(args.output / "receipt.json", {"schema": "paper011.dossier-integral-run.v1", "AuthorityEffect": "None",
                 "source_commit": helper.SOURCE_COMMIT, "source_root": str(source_root),
                 "sources_before": before, "sources_after": after, "custody_before": custody_before,
                 "custody_after": custody_after, "launcher_path": sys.executable, "backing_interpreter": str(interpreter),
                 "helper_verified_before_import": True, "yaml_package": str(package),
                 "yaml_and_source_custody_before_import_and_parsing": True,
                 "runtime_scope": "Explicit interpreter/YAML package, source inputs, machinery and native executable; OS/stdlib not inventoried.",
                 "outputs": outputs, "original_dossiers": 8, "actual_smith_certificates_replayed": result["actual_smith_certificates_replayed"]})
    print(json.dumps({"run_receipt": str(args.output / "receipt.json"), "certificates": result["actual_smith_certificates_replayed"]}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compiler = commands.add_parser("build")
    for name in ("rustc", "deps", "homology-rlib", "algebra-rlib", "bigint-rlib", "serde-rlib", "output"):
        compiler.add_argument(f"--{name}", type=Path, required=True)
    replay = commands.add_parser("run")
    for name in ("source-root", "executable", "build-receipt", "interpreter", "yaml-package", "output"):
        replay.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.pycache_prefix = str(args.output / "fresh_bytecode_prefix")
    sys.dont_write_bytecode = True
    if args.command == "run":
        pinned_helper(args.build_receipt)
    import replay_dossier_homology as helper  # noqa: PLC0415

    (build if args.command == "build" else run)(args, helper)


if __name__ == "__main__":
    main()
