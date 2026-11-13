"""Recover and check the original provider-free G12 Lean task at fixed Git pins."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g12"
PACKAGE = PAPER / "code/native_genesis_g12"
PIN = "b55fc96a94740b0afde78337350a96d293615f3f"
SEALED = "3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a"
MANIFEST_SHA = "d6dd0574c6de58f5b481120bbc1a00a8bd26120ca446cdffe6e2957792466a81"
LIB = (next((p for p in PAPER.parents if (p / ".git").exists()), None) or PAPER.parents[5]) / ".artifacts/paper011-g12lean/lib/lean"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wire(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          check=True, timeout=30).stdout


def recover(repo: Path) -> dict:
    """Recover the finite pinned import closure, with source-tree census custody."""
    AREA.mkdir(parents=True, exist_ok=True)
    originals = PACKAGE / "original"
    names = git(repo, "ls-tree", "-r", "--name-only", PIN, "lean4").decode().splitlines()
    paths = [name for name in names if name.endswith(".lean")]
    paths += ["lean4/lakefile.toml", "lean4/lean-toolchain", "lean4/lake-manifest.json",
              "ci/check_parked_audit.py", "ci/check_axiom_report.py", "ci/check_lean_audit.py",
              "ci/run_gates.py", ".github/workflows/verify.yml", "artifacts/lean_axioms.txt"]
    records = []
    for path in paths:
        blob = git(repo, "rev-parse", PIN + ":" + path).decode().strip()
        data = git(repo, "cat-file", "blob", blob)
        calculated = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != calculated:
            raise ValueError("GIT_BLOB_ID_MISMATCH")
        target = originals / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise ValueError("RECOVERY_WOULD_REPLACE_DIFFERENT_BYTES:" + path)
        target.write_bytes(data)
        records.append({"source_path": path, "git_blob": blob, "sha256": sha(data),
                        "bytes": len(data), "recovered_path": target.relative_to(PAPER).as_posix()})
    # This file predates the parked modules. Its Iso declaration is bound
    # separately, without substituting an older file into the newer closure.
    path = "lean4/Derivation/Minimality.lean"
    blob = git(repo, "rev-parse", SEALED + ":" + path).decode().strip()
    data = git(repo, "cat-file", "blob", blob)
    target = AREA / "sealed_Minimality.lean"
    target.write_bytes(data)
    record = {"source_commit": SEALED, "source_path": path, "git_blob": blob,
              "sha256": sha(data), "bytes": len(data), "recovered_path": target.relative_to(PAPER).as_posix()}
    result = {"schema": "paper011.g12-source-manifest.v1", "AuthorityEffect": "None",
              "source_commit": PIN, "source_tree": git(repo, "rev-parse", PIN + "^{tree}").decode().strip(),
              "files": records, "sealed_iso_source": record,
              "scope": "All original Lean files needed for the source-tree parked census and two roots; unchanged gate apparatus/artifact. No model replies."}
    (AREA / "source_manifest.json").write_bytes(wire(result))
    return {"files": len(records), "bytes": sum(row["bytes"] for row in records),
            "manifest_sha256": sha((AREA / "source_manifest.json").read_bytes())}


def verify_sources() -> dict:
    if sha((AREA / "source_manifest.json").read_bytes()) != MANIFEST_SHA:
        raise ValueError("SOURCE_MANIFEST_CHANGED")
    manifest = json.loads((AREA / "source_manifest.json").read_bytes())
    if manifest["source_commit"] != PIN or manifest["sealed_iso_source"]["source_commit"] != SEALED:
        raise ValueError("SOURCE_PIN_MISMATCH")
    for row in [*manifest["files"], manifest["sealed_iso_source"]]:
        data = (PAPER / row["recovered_path"]).read_bytes()
        if sha(data) != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError("RECOVERED_SOURCE_CHANGED:" + row["source_path"])
        if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != row["git_blob"]:
            raise ValueError("RECOVERED_GIT_BLOB_CHANGED")
    return manifest


def read_json_output(stem: str, marker: str) -> object:
    process = json.loads((AREA / (stem + "_process.json")).read_bytes())
    data = (AREA / (stem + "_stdout.txt")).read_bytes()
    if process["returncode"] or sha(data) != process["stdout_sha256"]:
        raise ValueError("UNBOUND_OR_FAILED_PROCESS:" + stem)
    rows = [line.split(marker, 1)[1] for line in data.decode("utf8").splitlines() if marker in line]
    if len(rows) != 1:
        raise ValueError("MISSING_OR_DUPLICATE_OUTPUT_MARKER")
    return json.loads(rows[0])


def check_independent(census: list, dump: list) -> list:
    selected = []
    for module in dump:
        if len(module["constNames"]) != len(set(module["constNames"])):
            raise ValueError("DUPLICATE_MODULE_CONSTANT")
        if module["constNames"] != [row["name"] for row in module["constants"]]:
            raise ValueError("DUMP_CONSTANT_COMPLETENESS_MISMATCH")
        selected += [(module["module"], row["name"]) for row in module["constants"]
                     if not row["is_theorem"] and row["forall_result_head"] == "Derivation.Iso"]
    actual = [(row["module"], row["definition"]) for row in census]
    if len(actual) != len(set(actual)) or set(actual) != set(selected):
        raise ValueError("INDEPENDENT_CENSUS_MISMATCH")
    return sorted(selected)


def prepare_pins() -> dict:
    census = read_json_output("census", "G12_CENSUS=")
    dump = read_json_output("independent_dump", "G12_INDEPENDENT_DUMP=")
    selected = check_independent(census, dump)
    text = "import Wrappers\n\n"
    for row in census:
        text += "example : " + row["prop_type"] + " := @" + row["wrapper"] + "\n\n"
    (PACKAGE / "FrozenPins.lean").write_text(text, encoding="utf8", newline="\n")
    (AREA / "census.json").write_bytes(wire(census))
    (AREA / "independent_walk.json").write_bytes(wire({"entries": selected, "modules": len(dump),
        "constant_count": sum(len(module["constNames"]) for module in dump),
        "census_source": "compiled Environment/ModuleData.constNames, not text",
        "dump_stdout_sha256": sha((AREA / "independent_dump_stdout.txt").read_bytes()),
        "census_stdout_sha256": sha((AREA / "census_stdout.txt").read_bytes()),
        "frozen_pin_source_sha256": sha((PACKAGE / "FrozenPins.lean").read_bytes())}))
    return {"entries": len(selected), "modules": len(dump), "constants": sum(len(m["constNames"]) for m in dump)}


def execute(argv: list[str], cwd: Path, stem: str, timeout: int = 600) -> dict:
    inputs = {str(Path(arg)): sha(Path(arg).read_bytes()) for arg in argv
              if Path(arg).is_file()}
    start = time.perf_counter()
    outcome = subprocess.run(argv, cwd=cwd, capture_output=True, check=False, timeout=timeout)
    AREA.mkdir(parents=True, exist_ok=True)
    (AREA / (stem + "_stdout.txt")).write_bytes(outcome.stdout)
    (AREA / (stem + "_stderr.txt")).write_bytes(outcome.stderr)
    after = {path: sha(Path(path).read_bytes()) for path in inputs}
    if inputs != after:
        raise ValueError("PROCESS_INPUT_CHANGED")
    record = {"argv": argv, "cwd": str(cwd), "returncode": outcome.returncode,
              "seconds": time.perf_counter() - start, "stdout_sha256": sha(outcome.stdout),
              "stderr_sha256": sha(outcome.stderr), "stdout_path": (AREA / (stem + "_stdout.txt")).relative_to(PAPER).as_posix(),
              "stderr_path": (AREA / (stem + "_stderr.txt")).relative_to(PAPER).as_posix(),
              "direct_inputs_before": inputs, "direct_inputs_after": after}
    (AREA / (stem + "_process.json")).write_bytes(wire(record))
    return record


def require_candidate_location(path: Path) -> None:
    if path.name == "ParkedAudit.lean" or "Derivation" in path.parts:
        raise ValueError("WRAPPER_IN_AUDIT_APPARATUS_OR_SEALED_TREE")


def require_census_custody(record: dict) -> None:
    expected = str(PACKAGE / "Census.lean")
    if record.get("direct_inputs_before", {}).get(expected) != sha((PACKAGE / "Census.lean").read_bytes()):
        raise ValueError("CENSUS_NOT_ENVIRONMENT_DERIVED")
    if expected not in record["argv"] or record["returncode"]:
        raise ValueError("CENSUS_NOT_ENVIRONMENT_DERIVED")


def input_custody(toolchain: Path, interpreter: Path) -> dict:
    manifest = verify_sources()
    files = sorted({*PACKAGE.rglob("*.lean"), PACKAGE / "lakefile.toml", PACKAGE / "lean-toolchain",
                    *(toolchain / "bin").glob("*"), *LIB.rglob("*.olean*"),
                    *(toolchain / "lib/lean").rglob("*.olean*"),
                    *(toolchain / "lib/lean").rglob("*.ir"),
                    *(toolchain / "lib").rglob("*.dll"),
                    AREA / "source_manifest.json", AREA / "sealed_Minimality.lean",
                    Path(__file__), interpreter, *PACKAGE.glob("*.json"),
                    *(PAPER / row["recovered_path"] for row in manifest["files"])})
    return {str(path): {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
            for path in files if path.is_file()}


def run_lean(toolchain: Path, path: Path, stem: str, compile_module: bool = False) -> dict:
    argv = [str(toolchain / "bin/lake.exe"), "env", "lean", "--root=" + str(PACKAGE), str(path.resolve())]
    if compile_module:
        argv += ["-o", str(LIB / (path.stem + ".olean"))]
    return execute(argv, PACKAGE, stem)


def controls(toolchain: Path, census: list, interpreter: Path) -> list:
    directory = PACKAGE / "controls"
    directory.mkdir(exist_ok=True)
    common = "import Audit\nopen Lean Elab Command Meta Derivation\n"
    poison = common + """
theorem G12.Poison (h : False) :
    ∀ (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length),
      (∀ q ∈ r.reqs, q.1 ≤ q.2) → Nonempty (Iso r (relabel r π φ)) := False.elim h
run_cmd liftTermElabM <| G12.checkWrapper ``Derivation.relabel_iso ``G12.Poison
"""
    dropped = common + """
theorem G12.Dropped (A B : Regime)
    (hdata : A.data = B.data) (hforms : A.forms = B.forms)
    (hInst : ∀ i, i ∈ A.insts ↔ i ∈ B.insts)
    (hRule : ∀ f, f ∈ A.rules ↔ f ∈ B.rules)
    (hReq : ∀ q, q ∈ A.reqs ↔ q ∈ B.reqs)
    (hAord : ∀ q ∈ A.reqs, q.1 ≤ q.2) : Nonempty (Iso A B) :=
  G12.Wrappers.Derivation_Iso_of_components A B hdata hforms hInst hRule hReq hAord
    (fun q hq => hAord q ((hReq q).mpr hq))
run_cmd liftTermElabM <| G12.checkWrapper ``Derivation.Iso.of_components ``G12.Dropped
"""
    outcomes = []
    for name, text, expected in (("false_hypothesis", poison, "VACUOUS_WRAPPER"),
                                 ("dropped_hypothesis", dropped, "STATEMENT_PIN_MISMATCH")):
        path = directory / (name + ".lean")
        path.write_text(text, encoding="utf8", newline="\n")
        result = run_lean(toolchain, path, name)
        output = (AREA / (name + "_stdout.txt")).read_text(encoding="utf8")
        if result["returncode"] == 0 or expected not in output:
            raise ValueError("SURVIVING_OR_UNRELATED_MUTATION:" + name)
        outcomes.append({"mutation": name, "reason": expected, "process": result})
    path = directory / "TextCensus.lean"
    text = "import ParkedAudit\nopen Lean Elab Command\nrun_cmd logInfo " + json.dumps(
        "G12_CENSUS=" + json.dumps(census, ensure_ascii=False), ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf8", newline="\n")
    result = run_lean(toolchain, path, "text_census")
    if result["returncode"]:
        raise ValueError("TEXT_CENSUS_CONTROL_DID_NOT_COMPILE")
    try:
        require_census_custody(result)
    except ValueError as error:
        outcomes.append({"mutation": "text_matched_census", "reason": str(error), "process": result})
    else:
        raise ValueError("SURVIVING_TEXT_CENSUS")
    path = directory / "ParkedAudit.lean"
    path.write_text("import Wrappers\nopen Derivation\ntheorem G12.Misplaced : Nonempty (Iso R2L R2L) :=\n"
                    "  ⟨isoRefl R2L (by decide)⟩\n", encoding="utf8", newline="\n")
    result = run_lean(toolchain, path, "misplaced_wrapper")
    if result["returncode"]:
        raise ValueError("MISPLACED_CONTROL_DID_NOT_COMPILE")
    try:
        require_candidate_location(path)
    except ValueError as error:
        outcomes.append({"mutation": "wrapper_in_ParkedAudit", "reason": str(error), "process": result})
    else:
        raise ValueError("SURVIVING_MISPLACED_WRAPPER")
    candidate = AREA / "comment_candidate/lean4"
    candidate.mkdir(parents=True, exist_ok=True)
    path = candidate / "Instances.lean"
    path.write_bytes((PACKAGE / "Instances.lean").read_bytes() + b"\n-- sorry in a comment\n")
    result = execute([str(toolchain / "bin/lake.exe"), "env", "lean", str(path)], PACKAGE, "comment_compile")
    if result["returncode"]:
        raise ValueError("COMMENT_CONTROL_DID_NOT_COMPILE")
    lexical = execute([str(interpreter), "-B", str(PACKAGE / "original/ci/check_lean_audit.py"),
                       str(AREA / "short_original_build_stdout.txt")], candidate.parent, "comment_lexical_gate")
    if lexical["returncode"] == 0 or "forbidden token 'sorry'" not in (AREA / "comment_lexical_gate_stdout.txt").read_text(encoding="utf8"):
        raise ValueError("SURVIVING_COMMENT_MUTATION")
    outcomes.append({"mutation": "sorry_in_instance_comment", "reason": "FORBIDDEN_TOKEN",
                     "compile_process": result, "gate_process": lexical})
    return outcomes


def finish(toolchain: Path, interpreter: Path) -> dict:
    if not sys.dont_write_bytecode or not sys.pycache_prefix:
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    cache = Path(sys.pycache_prefix)
    cache.mkdir(parents=True, exist_ok=True)
    if any(cache.iterdir()):
        raise ValueError("FRESH_BYTECODE_FREE_WORKER_REQUIRED")
    verify_sources()
    interpreter = interpreter.resolve(strict=True)
    before = input_custody(toolchain, interpreter)
    processes = []
    for name in ("Census", "IndependentDump", "FrozenPins", "Audit"):
        result = run_lean(toolchain, PACKAGE / (name + ".lean"), "final_" + name.lower())
        if result["returncode"]:
            raise ValueError("FINAL_LEAN_CHECK_FAILED:" + name)
        processes.append(result)
    require_census_custody(processes[0])
    census = read_json_output("final_census", "G12_CENSUS=")
    dump = read_json_output("final_independentdump", "G12_INDEPENDENT_DUMP=")
    check_independent(census, dump)
    reports = read_json_output("final_audit", "G12_REPORTS=")
    if {row["definition"] for row in reports} != {row["definition"] for row in census}:
        raise ValueError("REPORT_COMPLETENESS_MISMATCH")
    gates = []
    for gate in ("check_parked_audit", "check_axiom_report", "check_lean_audit"):
        argv = [str(interpreter), "-B", str(PACKAGE / "original/ci" / (gate + ".py"))]
        if gate != "check_parked_audit":
            argv.append(str(AREA / "short_original_build_stdout.txt"))
        result = execute(argv, PACKAGE / "original", "original_" + gate)
        if result["returncode"]:
            raise ValueError("ORIGINAL_GATE_FAILED:" + gate)
        gates.append(result)
    mutations = controls(toolchain, census, interpreter)
    after = input_custody(toolchain, interpreter)
    # New candidate/control files are allowed outputs. Every prior input must
    # stay byte-identical; no regenerated source baseline is accepted.
    if any(after.get(path) != item for path, item in before.items()):
        raise ValueError("LEAN_RUNTIME_OR_SOURCE_CHANGED")
    original = (PACKAGE / "original/lean4/Derivation/Minimality.lean").read_bytes()
    sealed = (AREA / "sealed_Minimality.lean").read_bytes()
    marker, end = b"structure Iso", b"def isoRefl"
    original_iso = original.split(marker, 1)[1].split(end, 1)[0]
    sealed_iso = sealed.split(marker, 1)[1].split(end, 1)[0]
    if original_iso != sealed_iso:
        raise ValueError("SEALED_ISO_DEFINITION_CHANGED")
    (AREA / "runtime_inputs_before.json").write_bytes(wire(before))
    (AREA / "runtime_inputs_after.json").write_bytes(wire(after))
    receipt = {"schema": "paper011.g12-provider-free-receipt.v1", "AuthorityEffect": "None",
               "source_manifest_sha256": MANIFEST_SHA, "source_pin": PIN, "sealed_iso_pin": SEALED,
               "sealed_iso_declaration_sha256": sha(marker + original_iso),
               "python_launcher": sys.executable, "python_executable": str(interpreter),
               "python_executable_sha256": sha(interpreter.read_bytes()),
               "python_version": sys.version, "dont_write_bytecode": sys.dont_write_bytecode,
               "cache_prefix": sys.pycache_prefix, "toolchain": str(toolchain),
               "lean_sha256": sha((toolchain / "bin/lean.exe").read_bytes()),
               "lake_sha256": sha((toolchain / "bin/lake.exe").read_bytes()),
               "runtime_inputs_before_sha256": sha((AREA / "runtime_inputs_before.json").read_bytes()),
               "runtime_inputs_after_sha256": sha((AREA / "runtime_inputs_after.json").read_bytes()),
               "runtime_scope": "Exact compiler/Lake bin files, installed Lean .olean variants/IR/shared libraries, local built .olean variants, all pinned source/gate/artifact files and authored Lean/Python sources. OS and Python standard library are outside this manifest.",
               "processes": processes, "original_gates": gates, "mutations": mutations, "reports": reports,
               "parked_modules": len(dump), "compiled_constants": sum(len(m["constNames"]) for m in dump),
               "provider_free_P1_P4_gate": True, "entire_external_run_gates_executed": False,
               "external_gate_scope": "Actual unchanged parked-source census and full original axiom-artifact/whitelist gates. Entire estate workflow requires unrelated Python/research/receipt populations and is not asserted.",
               "model_arms_executed": [], "empirical_differentiation_gate": False,
               "full_G12_experiment_completed": False, "historical_reports_modified": False,
               "scope": "All five original provider-free Iso construction obligations including trans/symm; fixed b55 environment, concrete R2L instances, exact Prop types, native kernel/axiom checks and original mutations. No promotion."}
    (AREA / "receipt.json").write_bytes(wire(receipt))
    return {"entries": len(reports), "modules": len(dump), "constants": receipt["compiled_constants"],
            "mutations": len(mutations), "receipt_sha256": sha((AREA / "receipt.json").read_bytes()),
            "provider_free_P1_P4_gate": True, "full_G12_experiment_completed": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("recover", "build-original", "lean", "compile", "prepare-pins", "finish"))
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--interpreter", type=Path)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--stem", default="lean")
    args = parser.parse_args()
    if args.action == "recover":
        result = recover(args.repo)
    elif args.action == "prepare-pins":
        result = prepare_pins()
    elif args.action == "finish":
        result = finish(args.toolchain, args.interpreter)
    else:
        verify_sources()
        lake = args.toolchain / "bin/lake.exe"
        if args.action == "build-original":
            result = execute([str(lake), "--no-cache", "build"], PACKAGE, "short_original_build")
        elif args.action == "compile":
            result = execute([str(lake), "env", "lean", "--root=" + str(PACKAGE), str(args.file.resolve()),
                              "-o", str(LIB / (args.file.stem + ".olean"))], PACKAGE, args.stem)
        else:
            result = execute([str(lake), "env", "lean", str(args.file.resolve())],
                             PACKAGE, args.stem)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
