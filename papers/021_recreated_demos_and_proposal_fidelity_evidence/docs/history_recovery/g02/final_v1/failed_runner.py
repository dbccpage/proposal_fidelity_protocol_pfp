"""Pinned source recovery and process custody for the original G02 cut census."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g02"
PACKAGE = PAPER / "code/native_genesis_g02"
PIN = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
MANIFEST_SHA = "20a55747d7225a09256eef9ccb9881dd1d06fee626dac928b135a652511f3e59"
PATHS = ("lean4/Derivation/HigherStructure.lean", "code/derivation/higher_structure.py",
         "artifacts/primitive_completion_receipt.json")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def recover(repo: Path) -> None:
    AREA.mkdir(parents=True, exist_ok=True)
    records = []
    for name in PATHS:
        blob = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{PIN}:{name}"],
                              capture_output=True, check=True, timeout=30).stdout.decode().strip()
        raw = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", blob],
                             capture_output=True, check=True, timeout=30).stdout
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != blob:
            raise ValueError("GIT_OBJECT_MISMATCH")
        target = AREA / "original" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError("SOURCE_REPLACEMENT_REFUSED")
        target.write_bytes(raw)
        records.append({"source_path": name, "git_blob": blob, "sha256": sha(raw),
                        "raw_bytes": len(raw), "recovered_path": str(target.relative_to(PAPER))})
    higher = (AREA / "original" / PATHS[0]).read_text(encoding="utf-8")
    blocks = []
    for start, end in (("def subsetsOf", "/-- The *cut census*"),
                       ("def cutCensus", "/-- On two occurrences")):
        first = higher.index(start)
        last = higher.index(end, first)
        blocks.append(higher[first:last].rstrip())
    source = "import Lean\n\nnamespace HigherStructure\n\n" + "\n\n".join(blocks) + "\n\nend HigherStructure\n"
    definitions = PACKAGE / "CutDefinitions.lean"
    definitions.parent.mkdir(parents=True, exist_ok=True)
    if definitions.exists() and definitions.read_text(encoding="utf-8") != source:
        raise ValueError("DEFINITION_SLICE_REPLACEMENT_REFUSED")
    definitions.write_text(source, encoding="utf-8")
    write(AREA / "source_manifest.json", {"schema": "paper011.g02-source-manifest.v1",
          "AuthorityEffect": "None", "source_commit": PIN, "files": records,
          "definition_slice": {"path": str(definitions.relative_to(PAPER)), "sha256": sha(definitions.read_bytes()),
             "method": "Literal original subsetsOf and cutCensus definition blocks; only import/namespace wrapper supplied."}})
    print(json.dumps({"files": len(records), "definition_slice": str(definitions)}))


def verify_sources() -> dict:
    path = AREA / "source_manifest.json"
    if sha(path.read_bytes()) != MANIFEST_SHA:
        raise ValueError("ORIGINAL_MANIFEST_CHANGED")
    manifest = json.loads(path.read_bytes())
    if manifest["source_commit"] != PIN or tuple(r["source_path"] for r in manifest["files"]) != PATHS:
        raise ValueError("ORIGINAL_SOURCE_DECLARATION")
    for row in manifest["files"]:
        raw = (PAPER / row["recovered_path"]).read_bytes()
        if sha(raw) != row["sha256"] or len(raw) != row["raw_bytes"]:
            raise ValueError("ORIGINAL_SOURCE_BYTES_CHANGED")
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != row["git_blob"]:
            raise ValueError("ORIGINAL_GIT_BLOB_MISMATCH")
    row = manifest["definition_slice"]
    if sha((PAPER / row["path"]).read_bytes()) != row["sha256"]:
        raise ValueError("ORIGINAL_DEFINITION_SLICE_CHANGED")
    return manifest


def final_run(args) -> None:
    verify_sources()
    output = AREA / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    sys.pycache_prefix = str(output / "fresh_cache")
    sys.dont_write_bytecode = True
    toolchain = args.toolchain.resolve(strict=True)
    interpreter = args.interpreter.resolve(strict=True)
    if interpreter.parent != Path(sys.base_prefix).resolve(strict=True):
        raise ValueError("BACKING_INTERPRETER_MISMATCH")
    executable = (AREA / "native_build_v1/g02_cut_bitmask.exe").resolve(strict=True)
    build = json.loads((AREA / "native_build_v1/receipt.json").read_bytes())
    if build["returncode"] != 0 or sha(executable.read_bytes()) != build["executable_sha256"]:
        raise ValueError("NATIVE_EXECUTABLE_BINDING")
    short = PAPER.parents[3] / ".artifacts/paper011-g02lakefinal"
    if short.exists():
        raise ValueError("FINAL_BUILD_DIRECTORY_MUST_BE_FRESH")
    source_paths = [Path(__file__), AREA / "source_manifest.json", executable,
                    AREA / "native_build_v1/receipt.json", interpreter,
                    *sorted(PACKAGE.glob("*.lean")), PACKAGE / "lakefile.toml",
                    *(PAPER / row["recovered_path"] for row in verify_sources()["files"])]
    runtime = [p for p in (toolchain / "lib/lean").rglob("*") if p.is_file() and
               (".olean" in p.name or p.suffix in (".ir", ".dll"))]
    runtime.extend(p for p in (toolchain / "bin").iterdir() if p.is_file())
    input_paths = [*source_paths, *runtime]
    before = {str(p): sha(p.read_bytes()) for p in input_paths}
    write(output / "inputs_before.json", before)
    env = os.environ.copy()
    env.pop("LEAN_PATH", None)
    processes = []

    def process(name, argv, *, request=None, lean_path=None):
        task_env = env.copy()
        if lean_path is not None:
            task_env["LEAN_PATH"] = str(lean_path)
        run = subprocess.run(argv, capture_output=True, input=request, check=False,
                             cwd=PACKAGE, env=task_env, timeout=180)
        (output / f"{name}_stdout.bin").write_bytes(run.stdout)
        (output / f"{name}_stderr.bin").write_bytes(run.stderr)
        row = {"name": name, "argv": argv, "cwd": str(PACKAGE), "returncode": run.returncode,
               "stdout_sha256": sha(run.stdout), "stderr_sha256": sha(run.stderr),
               "timeout_seconds": 180, "LEAN_PATH": str(lean_path) if lean_path is not None else None}
        write(output / f"{name}_process.json", row)
        processes.append(row)
        return run

    compiled = process("clean_lake_build", [str(toolchain / "bin/lake.exe"), "build"])
    if compiled.returncode:
        raise ValueError("LEAN_FINAL_BUILD_REFUSAL")
    report_lines = [line.split("G02_REPORTS=", 1)[1] for line in compiled.stdout.decode().splitlines()
                    if "G02_REPORTS=" in line]
    if len(report_lines) != 1:
        raise ValueError("AXIOM_REPORT_MISSING_OR_DUPLICATE")
    reports = json.loads(report_lines[0])
    if sum(r["public_target"] is True for r in reports) != 13:
        raise ValueError("PUBLIC_TARGET_CENSUS")
    if any(not set(r["axioms"]).issubset({"propext", "Quot.sound"}) for r in reports):
        raise ValueError("DISALLOWED_AXIOM")
    write(output / "actual_axiom_reports.json", reports)

    original = AREA / "original/code/derivation/higher_structure.py"
    spec = importlib.util.spec_from_file_location("paper011_original_g02_higher_structure", original)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cases = [{"case_id": f"n{n}_a{a}_b{b}", "n": n, "a": a, "b": b}
             for n in range(13) for a in range(n + 2) for b in range(n + 2)]
    controls = [{"case_id": "TOO_LARGE", "n": 13, "a": 0, "b": 1},
                {"case_id": "FLOAT_CARRIER", "n": 4.5, "a": 0, "b": 1}]
    request = json.dumps({"cases": [*cases, *controls]}, separators=(",", ":")).encode()
    (output / "native_request.json").write_bytes(request)
    native = process("bitmask_census", [str(executable)], request=request)
    if native.returncode:
        raise ValueError("NATIVE_CENSUS_PROCESS_REFUSAL")
    outcomes = json.loads(native.stdout)["cases"]
    if len(outcomes) != len(cases) + len(controls):
        raise ValueError("NATIVE_CENSUS_COMPLETENESS")
    rows = []
    for case, result in zip(cases, outcomes[:len(cases)], strict=True):
        actual = module.cut_census(case["n"], case["a"], case["b"])
        if result["case_id"] != case["case_id"] or result["success"] is not True:
            raise ValueError("NATIVE_CENSUS_CASE_BINDING")
        if str(actual) != result["result"]["count"] or result["result"]["visited_bitmasks"] != 2 ** case["n"]:
            raise ValueError("NATIVE_SOURCE_CENSUS_DISAGREEMENT")
        rows.append({**case, "source_sublist_count": actual, "native_count": result["result"]["count"],
                     "subsets_enumerated_per_route": 2 ** case["n"]})
    expected_errors = [("TOO_LARGE", "CARRIER_LIMIT_12"), ("FLOAT_CARRIER", "NATURAL_N_REQUIRED")]
    if [(r["case_id"], r.get("error")) for r in outcomes[-2:]] != expected_errors or any(r["success"] is not False for r in outcomes[-2:]):
        raise ValueError("NATIVE_CONTROL_BINDING")
    write(output / "census_rows.json", rows)
    after = {str(p): sha(p.read_bytes()) for p in input_paths}
    write(output / "inputs_after.json", after)
    if before != after:
        raise ValueError("FINAL_INPUT_DRIFT")
    outputs = {str(p.relative_to(output)): sha(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    generated = {str(p): sha(p.read_bytes()) for p in short.rglob("*") if p.is_file() and ".olean" in p.name}
    write(output / "receipt.json", {"schema": "paper011.g02-provider-free.v1", "AuthorityEffect": "None",
          "source_manifest_sha256": MANIFEST_SHA, "source_commit": PIN, "source_definitions_unchanged": True,
          "inputs_before_sha256": sha((output / "inputs_before.json").read_bytes()),
          "inputs_after_sha256": sha((output / "inputs_after.json").read_bytes()), "outputs": outputs,
          "compiled_outputs": generated, "processes": processes, "enumerated_pair_cases": len(cases),
          "target_statuses": {"C1": "SOLVED", "C2": "SOLVED", "C3": "SOLVED"},
          "actual_axiom_reports": len(reports), "public_targets_and_heldouts": 13,
          "mutation_suite_complete": False, "model_arms_executed": False,
          "entire_external_estate_workflow_executed": False, "full_G02_experiment_completed": False,
          "runtime_scope": "Explicit backing Python, original/authored sources, compiler/bin files and installed compiled Lean modules. OS/Python stdlib excluded; prebuilt Rust math archives not independently rebuilt."})
    print(json.dumps({"receipt": str(output / "receipt.json"), "cases": len(cases), "axiom_reports": len(reports)}))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["recover", "compile", "build-rust", "run"])
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--attempt", required=False)
    parser.add_argument("--rustc", type=Path)
    parser.add_argument("--deps", type=Path)
    parser.add_argument("--kernel-rlib", type=Path)
    parser.add_argument("--serde-rlib", type=Path)
    parser.add_argument("--interpreter", type=Path)
    args = parser.parse_args()
    if args.command == "recover":
        if args.repo is None:
            parser.error("recover requires --repo")
        recover(args.repo)
        return
    if args.command == "run":
        if None in (args.toolchain, args.attempt, args.interpreter):
            parser.error("run requires --toolchain --attempt --interpreter")
        final_run(args)
        return
    if args.command == "build-rust":
        if None in (args.rustc, args.deps, args.kernel_rlib, args.serde_rlib, args.attempt):
            parser.error("build-rust requires explicit compiler/deps/kernel/serde/attempt")
        output = AREA / args.attempt
        output.mkdir(parents=True, exist_ok=False)
        source = PACKAGE / "cut_bitmask.rs"
        executable = output / "g02_cut_bitmask.exe"
        archives = sorted(args.deps.resolve().glob("*.rlib"))
        before = {str(p): sha(p.read_bytes()) for p in archives}
        compiler = args.rustc.resolve(strict=True)
        source_sha = sha(source.read_bytes())
        (output / "source.rs").write_bytes(source.read_bytes())
        argv = [str(compiler), "--edition", "2021", "--crate-name", "paper011_g02_cut_bitmask",
                str(source), "-L", f"dependency={args.deps.resolve()}", "--extern",
                f"omega_kernel={args.kernel_rlib.resolve(strict=True)}", "--extern",
                f"serde_json={args.serde_rlib.resolve(strict=True)}", "-o", str(executable)]
        run = subprocess.run(argv, capture_output=True, check=False, cwd=PACKAGE, timeout=180)
        (output / "stdout.bin").write_bytes(run.stdout)
        (output / "stderr.bin").write_bytes(run.stderr)
        after = {str(p): sha(p.read_bytes()) for p in archives}
        write(output / "receipt.json", {"argv": argv, "cwd": str(PACKAGE), "returncode": run.returncode,
              "libraries_before": before, "libraries_after": after, "source_sha256": source_sha,
              "rustc_sha256": sha(compiler.read_bytes()), "stdout_sha256": sha(run.stdout),
              "stderr_sha256": sha(run.stderr), "executable_sha256": sha(executable.read_bytes()) if executable.exists() else None,
              "AuthorityEffect": "None", "scope": "Declared bounded Rust bitmask enumerator; prebuilt exact-integer owner archives not independently rebuilt."})
        print(json.dumps({"returncode": run.returncode, "receipt": str(output / "receipt.json")}))
        if run.returncode or before != after or source_sha != sha(source.read_bytes()):
            raise SystemExit(1)
        return
    if args.toolchain is None or args.file is None or args.attempt is None:
        parser.error("compile requires --toolchain --file --attempt")
    source = args.file.resolve(strict=True)
    compiler = (args.toolchain / "bin/lean.exe").resolve(strict=True)
    short = PAPER.parents[3] / ".artifacts/paper011-g02lean"
    short.mkdir(parents=True, exist_ok=True)
    output = AREA / "attempts" / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    (output / source.name).write_bytes(source.read_bytes())
    module_output = short / (source.stem + ".olean")
    inputs = [source, compiler, *(p for p in short.glob("*.olean") if p != module_output)]
    before = {str(p): sha(p.read_bytes()) for p in inputs}
    argv = [str(compiler), f"--root={PACKAGE}", "-o", str(module_output), str(source)]
    env = os.environ.copy()
    env["LEAN_PATH"] = str(short)
    run = subprocess.run(argv, cwd=PACKAGE, env=env, capture_output=True, check=False, timeout=120)
    (output / "stdout.bin").write_bytes(run.stdout)
    (output / "stderr.bin").write_bytes(run.stderr)
    after = {str(p): sha(p.read_bytes()) for p in inputs}
    write(output / "receipt.json", {"argv": argv, "cwd": str(PACKAGE), "LEAN_PATH": str(short),
          "returncode": run.returncode, "inputs_before": before, "inputs_after": after,
          "stdout_sha256": sha(run.stdout), "stderr_sha256": sha(run.stderr),
          "AuthorityEffect": "None", "scope": "Development compile; direct sources/binary/local imports only. Full final dependency audit pending."})
    print(run.stdout.decode("utf-8", errors="strict"))
    print(run.stderr.decode("utf-8", errors="strict"))
    print(json.dumps({"returncode": run.returncode, "receipt": str(output / "receipt.json")}))
    if run.returncode or before != after:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
