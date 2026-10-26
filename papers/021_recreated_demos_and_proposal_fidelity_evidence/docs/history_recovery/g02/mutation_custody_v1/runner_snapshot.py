"""Replay original G02 mutations with each generated compiler input bound before use."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g02"
BASE_RECEIPT_SHA = "15c1365812f8b369ddf072e2109c0092a1f513778ab3f6421bff95475f7eeec8"
BASE_HELPER_SHA = "187ba1c0bc231857890dd7cd22f8c3f1fa787d61aa23d3e568e1629b71a15a33"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("--interpreter", required=True, type=Path)
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    output = AREA / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    sys.pycache_prefix = str(output / "fresh_cache")
    sys.dont_write_bytecode = True
    interpreter = args.interpreter.resolve(strict=True)
    if interpreter.parent != Path(sys.base_prefix).resolve(strict=True):
        raise ValueError("BACKING_INTERPRETER_MISMATCH")
    baseline = AREA / "final_v3"
    receipt_path = baseline / "receipt.json"
    helper_path = PAPER / "code/genesis_g02_replay.py"
    if sha(receipt_path.read_bytes()) != BASE_RECEIPT_SHA or sha(helper_path.read_bytes()) != BASE_HELPER_SHA:
        raise ValueError("BASELINE_CUSTODY_REFUSAL")
    base = json.loads(receipt_path.read_bytes())
    for name, digest in base["outputs"].items():
        if sha((baseline / name).read_bytes()) != digest:
            raise ValueError("BASELINE_OUTPUT_CORRUPTION")
    prior_inputs = json.loads((baseline / "inputs_before.json").read_bytes())
    if prior_inputs != json.loads((baseline / "inputs_after.json").read_bytes()):
        raise ValueError("BASELINE_INPUT_DRIFT")
    toolchain = args.toolchain.resolve(strict=True)
    compiler = toolchain / "bin/lean.exe"
    if str(compiler) not in prior_inputs or str(interpreter) not in prior_inputs:
        raise ValueError("EXPLICIT_RUNTIME_NOT_IN_BASELINE")
    for path, digest in {**prior_inputs, **base["compiled_outputs"]}.items():
        if sha(Path(path).read_bytes()) != digest:
            raise ValueError(f"BASELINE_DEPENDENCY_CHANGED:{path}")
    inputs = [Path(p) for p in {**prior_inputs, **base["compiled_outputs"]}]
    inputs.extend((Path(__file__), receipt_path))
    before = {str(p): sha(p.read_bytes()) for p in inputs}
    write(output / "inputs_before.json", before)
    (output / "runner_snapshot.py").write_bytes(Path(__file__).read_bytes())
    spec = importlib.util.spec_from_file_location("_paper011_g02_frozen_mutations", helper_path)
    assert spec and spec.loader
    replay = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = replay
    spec.loader.exec_module(replay)
    replay.verify_sources()
    lean_path = Path(next(iter(base["compiled_outputs"]))).parent
    env = os.environ.copy()
    env["LEAN_PATH"] = str(lean_path)
    processes = []

    def process(name, argv, *, lean_path):
        generated = [Path(arg).resolve(strict=True) for arg in argv[1:] if arg.endswith(".lean")]
        source_before = {str(p): sha(p.read_bytes()) for p in generated}
        started = time.monotonic()
        native = subprocess.run(argv, capture_output=True, check=False, timeout=120,
                                cwd=replay.PACKAGE, env=env)
        source_after = {str(p): sha(p.read_bytes()) for p in generated}
        (output / f"{name}_stdout.bin").write_bytes(native.stdout)
        (output / f"{name}_stderr.bin").write_bytes(native.stderr)
        row = {"name": name, "argv": argv, "cwd": str(replay.PACKAGE), "LEAN_PATH": str(lean_path),
               "returncode": native.returncode, "compiler_inputs_before": source_before,
               "compiler_inputs_after": source_after, "stdin_sha256": None, "stdin_bytes": 0,
               "stdout_sha256": sha(native.stdout), "stderr_sha256": sha(native.stderr),
               "elapsed_seconds": time.monotonic() - started, "timeout_seconds": 120}
        write(output / f"{name}_process.json", row)
        processes.append(row)
        if source_before != source_after:
            raise ValueError("GENERATED_COMPILER_INPUT_DRIFT")
        return native

    mutations = replay.mutation_suite(output, compiler, lean_path, process)
    if mutations != base["mutations"]:
        raise ValueError("ORIGINAL_MUTATION_OUTCOMES_CHANGED")
    for row in processes:
        for path, digest in row["compiler_inputs_before"].items():
            if sha(Path(path).read_bytes()) != digest:
                raise ValueError("GENERATED_COMPILER_INPUT_CHANGED_AFTER_RUN")
    after = {str(p): sha(p.read_bytes()) for p in inputs}
    write(output / "inputs_after.json", after)
    if before != after:
        raise ValueError("MUTATION_DEPENDENCY_DRIFT")
    outputs = {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    write(output / "receipt.json", {"schema": "paper011.g02-mutation-custody.v1", "AuthorityEffect": "None",
          "baseline_receipt_sha256": BASE_RECEIPT_SHA, "baseline_helper_sha256": BASE_HELPER_SHA,
          "processes": processes, "mutations": mutations, "outputs": outputs,
          "scope": "Mutation-only replay of the original five controls and valid candidate. Each actual generated Lean input has a pre/post compiler hash; baseline inputs and compiled imports remain unchanged. No model/estate completion or new census execution is claimed."})
    print(json.dumps({"receipt": str(output / "receipt.json"), "controls": len(mutations),
                      "processes": len(processes)}))


if __name__ == "__main__":
    main()
