"""Audit original rational dossier matrices through explicit native capabilities.

Python parses/persists inputs. The unchanged native matrix owner performs rank
and multiplication. Rational homology does not verify integer torsion.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
SOURCE = PAPER / "code/native_dossier_homology.rs"
DOSSIERS = (
    "demo_5/dossier_1_planar_triangular_b1_2",
    "demo_5/dossier_2_kagome_lattice_b1_4",
    "demo_6/dossier_1_hollow_tetrahedron_b2_1",
    "demo_6/dossier_2_fused_tetrahedra_b2_2",
    "demo_7/dossier_1_hollow_4simplex_b3_1",
    "demo_7/dossier_2_torsion_bianchi_complex",
    "demo_9/dossier_1_hollow_5simplex_b4_1",
    "demo_9/dossier_2_pontryagin_chern_4manifold",
)
SOURCE_COMMIT = "526ffd1748941f1781c0ff584b7033b29088b405"
SOURCE_DIGESTS = (
    "553db30ceecf22ef79606f7d0bf9ac5902a5735896238d40e9eb959813dc08c9",
    "99590fcd38543c5aa5999078d76381f87557628162297429d060cb6d8c918bb1",
    "e852b4784c6dde21a171ebc700469d568e7399f6e9f292f5ceb26f6eb341f608",
    "2b67053d4fef537d1e344e7e3c22744f85f1ea1f111774a67f72c637beced0c3",
    "79e88d91ae0896786ed752b321f39b72af2198223d514a116dc67853eec7dd4d",
    "ec97a3e782bbddcbc291317e1b5cf28023be8da12aad0b6c4a6bb741ae3b0e75",
    "8d42d831ac369edb7411c41a5dd29804d689d4d882ac09867d0650a55a1a94aa",
    "d783119d52379dd4c100e1fc948b8d79445c3115a9fa5337724aecaa6b6e2686",
)


def digest(path: Path) -> str:
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if candidate.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"REDIRECTED_PATH:{candidate}")
    if not path.is_file():
        raise ValueError(f"NONREGULAR_FILE:{path}")
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def strict(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"NONFINITE:{value}")

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(result, dict):
        raise ValueError("NOT_OBJECT")
    return result


def prepare_case(identifier: str, parsed: dict) -> dict:
    maps = parsed["boundary_matrices"]
    if not maps or set(maps) != {f"d{k}" for k in range(len(maps))}:
        raise ValueError("INCOMPLETE_BOUNDARY_MAPS")
    if "homology" in parsed:
        homology = parsed["homology"]
        location = "homology"
    else:
        homology = parsed["topology"]["betti_numbers"]
        location = "topology.betti_numbers"
    if not any(key.startswith("b") and key[1:].isdigit() for key in homology):
        raise ValueError("MISSING_DECLARED_BETTI_CLAIMS")
    return {"case_id": identifier, "matrices": [maps[f"d{k}"] for k in range(len(maps))],
            "homology": homology, "homology_claim_source": location}


def check_source_pins(observed: dict) -> None:
    if observed != dict(zip(DOSSIERS, SOURCE_DIGESTS, strict=True)):
        raise ValueError("ORIGINAL_SOURCE_PIN_MISMATCH")


def controls(case: dict) -> list[dict]:
    changed = []
    for name in ("NONZERO_BOUNDARY_PRODUCT", "FLOAT_ENTRY", "RAGGED_MAP", "FALSE_BETTI_CLAIM"):
        row = copy.deepcopy(case)
        row["case_id"] = name
        match name:
            case "NONZERO_BOUNDARY_PRODUCT":
                row["matrices"][1][0][0] = "2"
            case "FLOAT_ENTRY":
                row["matrices"][0][0][0] = -1.0
            case "RAGGED_MAP":
                row["matrices"][0][0].pop()
            case "FALSE_BETTI_CLAIM":
                row["homology"]["b0"] = 999
        changed.append(row)
    return changed


def inspect_result(value: dict) -> dict:
    if value.get("schema") != "paper011.dossier-homology-native.v1":
        raise ValueError("NATIVE_SCHEMA")
    rows = value["cases"]
    expected = [*DOSSIERS, "NONZERO_BOUNDARY_PRODUCT", "FLOAT_ENTRY", "RAGGED_MAP", "FALSE_BETTI_CLAIM"]
    if [row.get("case_id") for row in rows] != expected:
        raise ValueError("CASE_COMPLETENESS")
    if any(row.get("success") is not True for row in rows[:8]):
        raise ValueError("ORIGINAL_NATIVE_REFUSAL")
    bad_chain, floating, ragged, bad_claim = rows[8:]
    if bad_chain["result"]["boundary_law_verified"] is not False or bad_chain["result"]["betti_over_q"] is not None:
        raise ValueError("BOUNDARY_MUTATION_ACCEPTED")
    if floating.get("success") is not False or ragged.get("success") is not False:
        raise ValueError("MALFORMED_MAP_ACCEPTED")
    if not any(c["degree"] == 0 and c["matches"] is False for c in bad_claim["result"]["declared_betti_comparisons"]):
        raise ValueError("FALSE_CLAIM_ACCEPTED")
    return {"original_dossiers": 8, "native_controls_passed": 4,
            "results": [row["result"] for row in rows[:8]], "AuthorityEffect": "None"}


def build(args) -> None:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    paths = sorted(args.deps.resolve().glob("*.rlib"), key=lambda p: p.name.encode())
    if args.runtime_rlib.resolve() not in paths or args.serde_rlib.resolve() not in paths:
        raise ValueError("UNDECLARED_LIBRARY")
    before = {str(p): digest(p) for p in paths}
    rustc = args.rustc.resolve(strict=True)
    source_before = digest(SOURCE)
    executable = output / "paper011_native_dossier_homology.exe"
    argv = [str(rustc), "--edition", "2021", "--crate-name", "paper011_native_dossier_homology",
            str(SOURCE), "-L", f"dependency={args.deps.resolve()}",
            "--extern", f"omega_symbol_game_runtime={args.runtime_rlib.resolve()}",
            "--extern", f"serde_json={args.serde_rlib.resolve()}", "-o", str(executable)]
    run = subprocess.run(argv, capture_output=True, check=False, timeout=180)
    (output / "stdout.bin").write_bytes(run.stdout)
    (output / "stderr.bin").write_bytes(run.stderr)
    after = {str(p): digest(p) for p in paths}
    receipt = {"schema": "paper011.dossier-homology-build.v1", "argv": argv,
               "rustc_sha256": digest(rustc), "source_sha256": source_before,
               "libraries_before": before, "libraries_after": after,
               "returncode": run.returncode, "stdout_sha256": digest(output / "stdout.bin"),
               "stderr_sha256": digest(output / "stderr.bin"), "AuthorityEffect": "None"}
    if executable.exists():
        receipt["executable"] = str(executable)
        receipt["executable_sha256"] = digest(executable)
    write(output / "receipt.json", receipt)
    if run.returncode or before != after or source_before != digest(SOURCE):
        raise ValueError("BUILD_FAILED_OR_DRIFTED")
    print(json.dumps({"build_receipt": str(output / "receipt.json"), "returncode": run.returncode}))


def run(args) -> None:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.pycache_prefix = str(output / "fresh_bytecode_prefix")
    sys.dont_write_bytecode = True
    import yaml  # noqa: PLC0415

    sources = {name: args.source_root.resolve() / name / "input.yaml" for name in DOSSIERS}
    before = {name: digest(path) for name, path in sources.items()}
    check_source_pins(before)
    cases = [prepare_case(name, yaml.safe_load(path.read_bytes())) for name, path in sources.items()]
    request = {"cases": [*cases, *controls(cases[2])]}
    write(output / "request.json", request)
    executable = args.executable.resolve(strict=True)
    executable_sha = digest(executable)
    build_receipt = strict(args.build_receipt.read_bytes())
    if (build_receipt.get("returncode") != 0
            or build_receipt.get("executable_sha256") != executable_sha
            or build_receipt.get("source_sha256") != digest(SOURCE)
            or build_receipt.get("libraries_before") != build_receipt.get("libraries_after")):
        raise ValueError("BUILD_BINDING")
    # Bind the actually imported YAML package; no OS/stdlib hermeticity claim.
    package = Path(yaml.__file__).parent
    interpreter = args.interpreter.resolve(strict=True)
    if interpreter.parent != Path(sys.base_prefix).resolve(strict=True):
        raise ValueError("BACKING_INTERPRETER_MISMATCH")
    runtime_paths = [interpreter, *sorted(package.glob("*.py")),
                     *sorted(package.glob("*.pyd"))]
    runtime_before = {str(p): digest(p) for p in runtime_paths}
    own_before = {str(p): digest(p) for p in (Path(__file__), SOURCE)}
    argv = [str(executable)]
    native = subprocess.run(argv, input=(output / "request.json").read_bytes(), cwd=PAPER,
                            capture_output=True, check=False, timeout=60)
    (output / "stdout.bin").write_bytes(native.stdout)
    (output / "stderr.bin").write_bytes(native.stderr)
    if native.returncode:
        raise ValueError(f"NATIVE_PROCESS:{native.returncode}")
    result = inspect_result(strict(native.stdout))
    after = {name: digest(path) for name, path in sources.items()}
    if before != after or digest(executable) != executable_sha:
        raise ValueError("SOURCE_OR_EXECUTABLE_DRIFT")
    if own_before != {str(p): digest(p) for p in (Path(__file__), SOURCE)}:
        raise ValueError("MACHINERY_DRIFT")
    if runtime_before != {str(p): digest(p) for p in runtime_paths}:
        raise ValueError("RUNTIME_DRIFT")
    write(output / "result.json", result)
    receipt = {"schema": "paper011.dossier-homology-run.v1", "AuthorityEffect": "None",
               "executable": str(executable), "executable_sha256": executable_sha,
               "argv": argv, "cwd": str(PAPER), "source_commit": SOURCE_COMMIT,
               "build_receipt_sha256": digest(args.build_receipt), "source_root": str(args.source_root.resolve()),
               "sources_before": before, "sources_after": after, "machinery": own_before,
               "runtime_files": runtime_before, "launcher_path": sys.executable,
               "backing_interpreter": str(interpreter),
               "runtime_scope": "Explicit Python interpreter and YAML package; OS/stdlib not inventoried.",
               "outputs": {name: digest(output / name) for name in ("request.json", "stdout.bin", "stderr.bin", "result.json")},
               "original_dossiers": 8, "native_controls_passed": 4, "returncode": native.returncode}
    write(output / "receipt.json", receipt)
    print(json.dumps({"run_receipt": str(output / "receipt.json"), "dossiers": 8, "controls": 4}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compiler = commands.add_parser("build")
    for name in ("rustc", "deps", "runtime-rlib", "serde-rlib", "output"):
        compiler.add_argument(f"--{name}", type=Path, required=True)
    replay = commands.add_parser("run")
    for name in ("source-root", "executable", "build-receipt", "interpreter", "output"):
        replay.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    (build if args.command == "build" else run)(args)


if __name__ == "__main__":
    main()
