"""Build the canonical Level Engine Lean modules sequentially. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from omega_engine_operations.domain.level_engine_context import (
    ContextRefusal,
    LevelEngineResourcesPort,
    configure_context,
    current_context,
)

PINNED_TOOLCHAIN = "leanprover/lean4:v4.35.0"


def workspace() -> Path:
    context = current_context()
    if context.repository_root is None:
        raise ContextRefusal("LEAN_BUILD_REPOSITORY_REQUIRED", "provide the repository containing the canonical Lean package")
    root = context.repository_root / "lean4"
    if context.lean_root is None or context.lean_root.resolve() != (root / "research_programs" / "level_engine").resolve():
        raise ContextRefusal("LEAN_PACKAGE_MISMATCH", "Lean resources must belong to the supplied repository package")
    pin = root / "lean-toolchain"
    if not pin.is_file() or pin.read_text(encoding="ascii").strip() != PINNED_TOOLCHAIN:
        raise ContextRefusal("LEAN_TOOLCHAIN_MISMATCH", f"expected {PINNED_TOOLCHAIN}")
    return root


def source_hashes(root: Path) -> dict[str, str]:
    """Bind the build to every Level Engine input and the shared rational library."""
    canonical = root / "research_programs" / "level_engine"
    paths = [root / "lakefile.lean", root / "lean-toolchain", root / "ExactRat.lean"]
    paths += sorted((root / "ExactRat").rglob("*.lean"))
    paths += sorted(canonical.glob("*.lean"))
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def write_receipt(relative: str, receipt: dict[str, object]) -> None:
    path = current_context().current_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_lean(arguments: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, LEAN_NUM_THREADS="1")
    try:
        return subprocess.run(["lake", *arguments], cwd=root, env=environment, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", check=False)
    except FileNotFoundError as exc:
        raise ContextRefusal("LEAN_TOOLCHAIN_UNAVAILABLE", "lake is not installed or is absent from PATH") from exc


def main(argv: list[str] | None = None, *, context: LevelEngineResourcesPort | None = None) -> int:
    if context is not None:
        configure_context(context)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    root = workspace()
    sources = source_hashes(root)
    certificates = sorted(path.stem for path in current_context().lean_path("AxiomReport.lean").parent.glob("*.lean")
                          if path.stem != "AxiomReport")
    modules = ["ExactRat", *certificates, "AxiomReport"]
    results: list[dict[str, object]] = []
    log = current_context().current_path("lean/build.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    result_code = 0
    with log.open("w", encoding="utf-8", newline="\n") as output:
        for module in modules:
            proc = run_lean(["build", f"+{module}"], root)
            output.write(f"$ lake build +{module}\n{proc.stdout}{proc.stderr}\n")
            output.flush()
            results.append({"module": module, "returncode": proc.returncode})
            print(f"LEAN BUILD: {module} exit={proc.returncode}", flush=True)
            if proc.returncode:
                result_code = proc.returncode
                break
    stable_sources = sources == source_hashes(root)
    if not stable_sources:
        print("LEAN SOURCE CHANGED: source bytes changed during the build")
        result_code = 1
    write_receipt("lean/build_receipt.json", {
        "schema_version": 2, "authority_effect": "None", "toolchain": PINNED_TOOLCHAIN,
        "sources": sources, "sources_stable": stable_sources, "modules": results,
        "returncode": result_code,
    })
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
