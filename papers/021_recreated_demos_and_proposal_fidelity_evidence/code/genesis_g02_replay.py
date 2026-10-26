"""Pinned source recovery and process custody for the original G02 cut census."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g02"
PACKAGE = PAPER / "code/native_genesis_g02"
PIN = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
MANIFEST_SHA = "20a55747d7225a09256eef9ccb9881dd1d06fee626dac928b135a652511f3e59"
PATHS = ("lean4/Derivation/HigherStructure.lean", "code/derivation/higher_structure.py",
         "artifacts/primitive_completion_receipt.json")
ALLOWED_AXIOMS = {"propext", "Quot.sound"}
PUBLIC_TARGETS = {"C1", "C2", "C3", "equal_pair", "first_outside", "second_outside",
                  "zero_carrier", "one_carrier", "C3_at_nine", "C3_at_ten", "relabel_pair",
                  "poison_equal_pair", "poison_no_lower_bound"}


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


def lexical_refusal(raw: bytes) -> str | None:
    """Inspect actual candidate bytes, including comments, under the original policy."""
    text = raw.decode("utf-8", errors="strict")
    for pattern, reason in ((r"\bsorry\b", "FORBIDDEN_SORRY"),
                            (r"\bnative_decide\b", "FORBIDDEN_NATIVE_DECIDE"),
                            (r"\bopen\s+Classical\b", "FORBIDDEN_OPEN_CLASSICAL")):
        if re.search(pattern, text):
            return reason
    return None


def check_reports(reports: list) -> dict:
    public = [r for r in reports if r["public_target"] is True]
    expected = {f"ResearchPaper011G02.{name}" for name in PUBLIC_TARGETS}
    if len(public) != 13 or {r["name"] for r in public} != expected:
        raise ValueError("PUBLIC_TARGET_CENSUS")
    if len({r["name"] for r in reports}) != len(reports):
        raise ValueError("DUPLICATE_AXIOM_REPORT")
    if any(not set(r["axioms"]).issubset(ALLOWED_AXIOMS) for r in reports):
        raise ValueError("DISALLOWED_AXIOM")
    return {name: {"status": "SOLVED", "target": name,
                   "lean_names": [f"ResearchPaper011G02.{name}"],
                   "axioms": next(r["axioms"] for r in public
                                  if r["name"] == f"ResearchPaper011G02.{name}")}
            for name in ("C1", "C2", "C3")}


def mutation_suite(output: Path, compiler: Path, lean_path: Path, process) -> list:
    """Compile the five original judge mutants and a valid control; retain every stream."""
    cases = {
        "native_decide": "theorem candidate : cutCensus 5 0 1 = 8 := by native_decide\n",
        "sorry_docstring": "/-- sorry in a doc-string must still be screened. -/\n"
            "theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := C2 n hn\n",
        "open_classical": "open Classical\n"
            "theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := C2 n hn\n",
        "unverified_nat_pow": "def replacement_pow (_a _b : Nat) : Nat := 0\n"
            "axiom replacement_correct : ∀ a b, replacement_pow a b = Nat.pow a b\n"
            "theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := by\n"
            "  have h := replacement_correct 2 (n - 2)\n"
            "  exact ((C2 n hn).trans h.symm).trans h\n",
        "narrowed_pin": "theorem candidate (n : Nat) (hn : 4 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) :=\n"
            "  C2 n (by omega)\n",
        "valid_control": "theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := C2 n hn\n",
    }
    rows = []
    for name, candidate in cases.items():
        namespace = f"G02Mutation_{name}"
        raw = ("import CutTheorems\nimport Lean.Util.CollectAxioms\n"
               "open HigherStructure ResearchPaper011G02\n"
               f"namespace {namespace}\n{candidate}\nend {namespace}\n").encode()
        source = output / f"mutation_{name}.lean"
        source.write_bytes(raw)
        refusal = lexical_refusal(raw)
        audit = output / f"mutation_{name}_audit.lean"
        audit.write_bytes(raw + ("\nopen Lean Elab Command\nrun_cmd do\n"
            f"  let axioms ← liftCoreM <| Lean.collectAxioms `{namespace}.candidate\n"
            '  logInfo m!"G02_MUTATION_AXIOMS={Json.compress (toJson (axioms.map Name.toString))}"\n').encode())
        compiled = process(f"mutation_{name}_compile", [str(compiler), str(audit)], lean_path=lean_path)
        if compiled.returncode:
            raise ValueError(f"MUTANT_PROPOSAL_DID_NOT_COMPILE:{name}")
        lines = [line.split("G02_MUTATION_AXIOMS=", 1)[1]
                 for line in compiled.stdout.decode().splitlines() if "G02_MUTATION_AXIOMS=" in line]
        if len(lines) != 1:
            raise ValueError("MUTATION_AXIOM_REPORT_MISSING")
        axioms = json.loads(lines[0])
        disallowed = sorted(set(axioms) - ALLOWED_AXIOMS)
        pin_returncode = None
        if name in {"narrowed_pin", "valid_control"}:
            pinned = output / f"mutation_{name}_pin.lean"
            pinned.write_bytes(raw + (f"\nexample : ∀ n, 2 ≤ n → cutCensus n 0 1 = 2 ^ (n - 2) :=\n"
                                      f"  {namespace}.candidate\n").encode())
            pin = process(f"mutation_{name}_pin", [str(compiler), str(pinned)], lean_path=lean_path)
            pin_returncode = pin.returncode
            if name == "narrowed_pin":
                if pin.returncode == 0 or b"Type mismatch" not in pin.stdout:
                    raise ValueError("NARROWED_PIN_WAS_NOT_REJECTED")
                refusal = "STATEMENT_PIN_MISMATCH"
        if name == "native_decide" and not disallowed:
            raise ValueError("NATIVE_DECIDE_AXIOM_ESCAPE_NOT_REPRODUCED")
        if name == "unverified_nat_pow":
            if disallowed != [f"{namespace}.replacement_correct"]:
                raise ValueError("UNVERIFIED_POWER_AXIOM_NOT_REPRODUCED")
            refusal = "DISALLOWED_REPLACEMENT_AXIOM"
        expected = {"native_decide": "FORBIDDEN_NATIVE_DECIDE", "sorry_docstring": "FORBIDDEN_SORRY",
                    "open_classical": "FORBIDDEN_OPEN_CLASSICAL", "unverified_nat_pow": "DISALLOWED_REPLACEMENT_AXIOM",
                    "narrowed_pin": "STATEMENT_PIN_MISMATCH", "valid_control": None}[name]
        if refusal != expected or (name == "valid_control" and (disallowed or pin_returncode != 0)):
            raise ValueError(f"MUTATION_GATE_BINDING:{name}")
        if name in {"sorry_docstring", "open_classical", "narrowed_pin"} and disallowed:
            raise ValueError("MUTATION_CLASSIFICATION_NOT_ISOLATED")
        rows.append({"mutation": name, "candidate_path": source.name, "candidate_sha256": sha(raw),
                     "compile_returncode": compiled.returncode, "actual_axioms": axioms,
                     "disallowed_axioms": disallowed, "pin_returncode": pin_returncode,
                     "outcome": "ACCEPTED" if refusal is None else "REJECTED", "reason": refusal})
    write(output / "mutation_results.json", rows)
    return rows


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
    short = PAPER.parents[3] / ".artifacts/paper011-g02lakefinal3"
    if short.exists():
        raise ValueError("FINAL_BUILD_DIRECTORY_MUST_BE_FRESH")
    rust_source = PACKAGE / "cut_bitmask.rs"
    if sha(rust_source.read_bytes()) != build["source_sha256"] or build["libraries_before"] != build["libraries_after"]:
        raise ValueError("NATIVE_BUILD_SOURCE_OR_LIBRARY_CUSTODY")
    archives = [Path(p) for p in build["libraries_before"]]
    if any(sha(p.read_bytes()) != build["libraries_before"][str(p)] for p in archives):
        raise ValueError("NATIVE_BUILD_ARCHIVE_DRIFT")
    rustc = Path(build["argv"][0])
    if sha(rustc.read_bytes()) != build["rustc_sha256"]:
        raise ValueError("NATIVE_BUILD_COMPILER_DRIFT")
    source_paths = [Path(__file__), AREA / "source_manifest.json", executable, rust_source, rustc, *archives,
                    AREA / "native_build_v1/receipt.json", interpreter,
                    *sorted(PACKAGE.glob("*.lean")), PACKAGE / "lakefile.toml", PACKAGE / "lake-manifest.json",
                    *(PAPER / row["recovered_path"] for row in verify_sources()["files"])]
    runtime = [p for p in (toolchain / "lib/lean").rglob("*") if p.is_file() and
               (".olean" in p.name or p.suffix in (".ir", ".dll"))]
    runtime.extend(p for p in (toolchain / "bin").iterdir() if p.is_file())
    input_paths = [*source_paths, *runtime]
    before = {str(p): sha(p.read_bytes()) for p in input_paths}
    write(output / "inputs_before.json", before)
    (output / "runner_snapshot.py").write_bytes(Path(__file__).read_bytes())
    env = os.environ.copy()
    env.pop("LEAN_PATH", None)
    processes = []

    def process(name, argv, *, request=None, lean_path=None):
        task_env = env.copy()
        if lean_path is not None:
            task_env["LEAN_PATH"] = str(lean_path)
        started = time.monotonic()
        run = subprocess.run(argv, capture_output=True, input=request, check=False,
                             cwd=PACKAGE, env=task_env, timeout=180)
        (output / f"{name}_stdout.bin").write_bytes(run.stdout)
        (output / f"{name}_stderr.bin").write_bytes(run.stderr)
        row = {"name": name, "argv": argv, "cwd": str(PACKAGE), "returncode": run.returncode,
               "stdout_sha256": sha(run.stdout), "stderr_sha256": sha(run.stderr),
               "stdin_sha256": sha(request) if request is not None else None,
               "stdin_bytes": len(request) if request is not None else 0,
               "elapsed_seconds": time.monotonic() - started,
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
    targets = check_reports(reports)
    for source in (PACKAGE / "CutTheorems.lean", PACKAGE / "Pins.lean"):
        if lexical_refusal(source.read_bytes()):
            raise ValueError("ACCEPTED_PROPOSAL_LEXICAL_REFUSAL")
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
    mutations = mutation_suite(output, toolchain / "bin/lean.exe", short / "lib/lean", process)
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
          "target_statuses": targets, "mutations": mutations,
          "actual_axiom_reports": len(reports), "public_targets_and_heldouts": 13,
          "mutation_suite_complete": True, "model_arms_executed": False,
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
