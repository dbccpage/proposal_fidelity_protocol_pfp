"""Audit every Level Engine declaration under the shared Lean 4.35 package.

The build receipt must match the current source bytes. Fresh evidence is written
under v2; --write replaces the canonical report only after a successful census
and axiom-policy check. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re

from operations.domain.level_engine_context import (
    ContextRefusal,
    LevelEngineResourcesPort,
    configure_context,
    current_context,
)
from operations.use_cases.level_engine.lean_build import (
    PINNED_TOOLCHAIN,
    run_lean,
    source_hashes,
    workspace,
    write_receipt,
)
from operations.use_cases.level_engine.lean_gen import reported
from pfp.domain.lean_bridge.models import STANDARD_LEAN_AXIOMS

POLICY = frozenset(STANDARD_LEAN_AXIOMS)
LINE = re.compile(r"'(?P<name>[^']+)' (?:depends on axioms: \[(?P<ax>[^\]]*)\]|does not depend on any axioms)")


def collect() -> tuple[int, dict[str, tuple[str, ...]], list[str], dict[str, str]]:
    root = workspace()
    receipt = current_context().current_path("lean/build_receipt.json")
    try:
        previous = json.loads(receipt.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as exc:
        raise ContextRefusal("LEAN_BUILD_REQUIRED", "run lean build before the axiom audit") from exc
    if (previous.get("returncode") != 0 or previous.get("sources_stable") is not True
            or previous.get("toolchain") != PINNED_TOOLCHAIN or previous.get("sources") != source_hashes(root)):
        raise ContextRefusal("LEAN_BUILD_STALE", "the successful build must match the current source bytes")
    source = current_context().lean_path("AxiomReport.lean").relative_to(root).as_posix()
    proc = run_lean(["env", "lean", source], root)
    log = current_context().current_path("lean/axiom_report.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    found: dict[str, tuple[str, ...]] = {}
    duplicates: list[str] = []
    for line in (proc.stdout + proc.stderr).splitlines():
        match = LINE.search(line)
        if match:
            name = match.group("name")
            axioms = tuple(sorted(a.strip() for a in match.group("ax").split(","))) if match.group("ax") else ()
            if name in found:
                duplicates.append(name)
            found[name] = axioms
    if previous["sources"] != source_hashes(root):
        raise ContextRefusal("LEAN_SOURCE_CHANGED", "source bytes changed during the axiom audit")
    return proc.returncode, found, duplicates, previous["sources"]


def render(found: dict[str, tuple[str, ...]]) -> bytes:
    lines = [f"{name}: {', '.join(found[name]) if found[name] else '(none)'}" for name in sorted(found)]
    return ("\n".join(lines) + "\n").encode("ascii")


def parse(data: bytes) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for line in data.decode("ascii").splitlines():
        name, _, rest = line.partition(": ")
        out[name] = () if rest == "(none)" else tuple(a.strip() for a in rest.split(","))
    return out



def snapshot_sources(report: bytes, audited_sources: dict[str, str]) -> None:
    """Publish hash-bound read resources after a complete successful audit."""
    root = workspace()
    context = current_context()
    copies: dict[str, dict[str, str]] = {}
    pending: dict[str, bytes] = {}
    prefix = "research_programs/level_engine/"
    if source_hashes(root) != audited_sources:
        raise ContextRefusal("LEAN_SOURCE_CHANGED", "source changed after the axiom audit")
    for canonical, digest in audited_sources.items():
        if not canonical.endswith(".lean") or canonical == "lakefile.lean":
            continue
        relative = canonical.removeprefix(prefix)
        data = (root / canonical).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ContextRefusal("LEAN_SOURCE_CHANGED", "source changed while publishing read resources")
        pending[relative] = data
        copies[canonical] = {"snapshot": relative, "sha256": digest}
    if source_hashes(root) != audited_sources:
        raise ContextRefusal("LEAN_SOURCE_CHANGED", "source changed while preparing read resources")
    for relative, data in pending.items():
        destination = context.current_path("lean/sources/" + relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    report_path = context.current_path("lean/sources/axioms.txt")
    report_path.write_bytes(report)
    copies[prefix + "axioms.txt"] = {"snapshot": "axioms.txt", "sha256": hashlib.sha256(report).hexdigest()}
    receipts = {name: hashlib.sha256(context.current_path("lean/" + name).read_bytes()).hexdigest()
                for name in ("build_receipt.json", "axiom_audit_receipt.json")}
    write_receipt("lean/sources/manifest.json", {
        "schema": "level-engine.lean-read-resources.v2", "authority_effect": "None",
        "canonical_root": "lean4", "toolchain": PINNED_TOOLCHAIN, "sources": copies,
        "receipt_sha256": receipts,
        "scope": "Exact read-only source and axiom-report copies from the recorded successful build and audit; no compiled artifacts or new authority.",
    })


def main(argv: list[str] | None = None, *, context: LevelEngineResourcesPort | None = None) -> int:
    if context is not None:
        configure_context(context)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    rc, found, duplicates, audited_sources = collect()
    ok = rc == 0
    if rc:
        print(f"AXIOM REPORT DID NOT ELABORATE (exit {rc})")
    want = reported()
    missing = sorted(set(want) - found.keys())
    extra = sorted(found.keys() - set(want))
    for name in missing:
        print(f"CENSUS: {name} has no axiom report")
    for name in extra + duplicates:
        print(f"CENSUS: {name} is reported but not declared, or twice")
    outside = {name: [a for a in ax if a not in POLICY] for name, ax in sorted(found.items()) if set(ax) - POLICY}
    for name, axioms in outside.items():
        print(f"RR-AXIOM: {name} depends on {', '.join(axioms)}")
    ok = ok and not missing and not extra and not duplicates and not outside
    data = render(found)
    if audited_sources != source_hashes(workspace()):
        raise ContextRefusal("LEAN_SOURCE_CHANGED", "source changed after the axiom audit")
    canonical = current_context().lean_path("axioms.txt")
    if args.write and ok:
        canonical.write_bytes(data)
    elif not canonical.exists() or canonical.read_bytes() != data:
        print("AXIOM REPORT DRIFT: the canonical axioms.txt does not match the fresh report")
        ok = False
    fresh = current_context().current_path("lean/axioms.txt")
    fresh.parent.mkdir(parents=True, exist_ok=True)
    fresh.write_bytes(data)
    write_receipt("lean/axiom_audit_receipt.json", {
        "schema_version": 2, "authority_effect": "None", "toolchain": PINNED_TOOLCHAIN,
        "sources": audited_sources, "returncode": 0 if ok else 1,
        "elaboration_returncode": rc, "declarations": len(found), "census": len(want),
        "missing": missing, "extra": extra, "duplicates": duplicates, "outside_policy": outside,
        "policy": sorted(POLICY), "report_sha256": hashlib.sha256(data).hexdigest(),
    })
    if ok:
        snapshot_sources(data, audited_sources)
    print(f"{len(found)} declarations reported, {len(want)} in the census; policy {', '.join(sorted(POLICY))}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
