"""Explicit resources for the research Level Engine. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath

from operations.domain.level_engine_context import ContextRefusal


def _inside(root: Path, relative: str) -> Path:
    raw = relative.replace("\\", "/")
    parts = PurePosixPath(raw).parts
    if not raw or raw.startswith("/") or any(p in (".", "..") or ":" in p for p in parts):
        raise ContextRefusal("INVALID_RESOURCE_PATH", relative)
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ContextRefusal("INVALID_RESOURCE_PATH", relative)
    return target


def _verify_lean_snapshot(root: Path) -> frozenset[str]:
    """Check source and receipt custody for packaged, previously audited Lean bytes."""
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if (manifest["schema"] != "level-engine.lean-read-resources.v2"
                or manifest["authority_effect"] != "None" or manifest["canonical_root"] != "lean4"):
            raise ValueError("wrong snapshot schema or scope")
        expected_receipts = {"build_receipt.json", "axiom_audit_receipt.json"}
        if set(manifest["receipt_sha256"]) != expected_receipts:
            raise ValueError("missing build or audit receipt")
        receipts = {}
        for name, expected in manifest["receipt_sha256"].items():
            raw = _inside(root.parent, name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("receipt digest mismatch")
            receipts[name] = json.loads(raw)
        build, audit = receipts["build_receipt.json"], receipts["axiom_audit_receipt.json"]
        if (build["returncode"] != 0 or build["sources_stable"] is not True
                or audit["returncode"] != 0 or audit["elaboration_returncode"] != 0
                or build["sources"] != audit["sources"]
                or build["toolchain"] != manifest["toolchain"] or audit["toolchain"] != manifest["toolchain"]
                or audit["missing"] or audit["extra"] or audit["duplicates"] or audit["outside_policy"]
                or audit["declarations"] != audit["census"]):
            raise ValueError("build or audit is incomplete")
        expected_sources = {name: digest for name, digest in build["sources"].items()
                            if name.endswith(".lean") and name != "lakefile.lean"}
        expected_sources["research_programs/level_engine/axioms.txt"] = audit["report_sha256"]
        if set(manifest["sources"]) != set(expected_sources):
            raise ValueError("snapshot source closure differs from build")
        for canonical, entry in manifest["sources"].items():
            raw = _inside(root, entry["snapshot"]).read_bytes()
            if entry["sha256"] != expected_sources[canonical] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("snapshot source digest mismatch")
        return frozenset(str(entry["snapshot"]) for entry in manifest["sources"].values())
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        raise ContextRefusal("LEAN_SNAPSHOT_INVALID", "packaged source/audit custody cannot be verified") from exc


@dataclass(frozen=True)
class LevelEngineContext:
    runtime_root: Path
    evidence_root: Path
    governance_root: Path
    repository_root: Path | None = None
    vendor_root: Path | None = None
    output_root: Path | None = None
    lean_root: Path | None = None
    reach_root: Path | None = None

    def resource(self, relative: str) -> Path:
        return _inside(self.runtime_root, relative)

    def source(self, relative: str) -> Path:
        if relative.startswith("bindings/adapters/"):
            relative = "adapters/" + relative.removeprefix("bindings/adapters/")
        return self.resource(relative)

    def historical_path(self, relative: str) -> Path:
        return _inside(self.evidence_root / "v1", relative)

    def current_path(self, relative: str) -> Path:
        return _inside(self.output_root or self.evidence_root / "v2", relative)

    def governance_path(self, relative: str) -> Path:
        if relative in ("HISTORY.json", "RULINGS.md"):
            relative = "historical/" + relative
        return _inside(self.governance_root, relative)

    def lean_path(self, relative: str) -> Path:
        if self.lean_root is None:
            raise ContextRefusal("LEAN_RESOURCES_UNAVAILABLE", "provide the Lean resource root")
        if self.lean_root.resolve() == (self.evidence_root / "v2" / "lean" / "sources").resolve():
            if relative not in _verify_lean_snapshot(self.lean_root):
                raise ContextRefusal("LEAN_SNAPSHOT_INVALID", "requested source is outside the recorded closure")
        return _inside(self.lean_root, relative)

    def require_repository(self) -> Path:
        if self.repository_root is None:
            raise ContextRefusal("HISTORICAL_BYTES_UNAVAILABLE", "a repository is required for Git history")
        return self.repository_root

    def require_vendor(self) -> Path:
        if self.vendor_root is None:
            raise ContextRefusal("PINNED_VENDOR_UNAVAILABLE", "provide the read-only pinned vendor")
        pin = json.loads(self.governance_path("PINS.json").read_text(encoding="utf-8"))["vendored"]["19L57G1"]
        def git(*args: str) -> str:
            result = subprocess.run(["git", "-C", str(self.vendor_root), *args], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise ContextRefusal("RR-PIN", "the supplied vendor cannot be verified")
            return result.stdout.strip()
        actual = git("rev-parse", "HEAD", "HEAD^{tree}").splitlines()
        if actual != [pin["commit"], pin["tree"]] or git("status", "--porcelain", "--untracked-files=no"):
            raise ContextRefusal("RR-PIN", "the supplied vendor differs from its exact commit/tree or has tracked modifications")
        return self.vendor_root


def installed_context(*, repository_root: Path | None = None, vendor_root: Path | None = None,
                      output_root: Path | None = None, lean_root: Path | None = None,
                      governance_root: Path | None = None, evidence_root: Path | None = None,
                      reach_root: Path | None = None) -> LevelEngineContext:
    """Resolve installed resources; never infer a repository from module parents."""
    runtime = Path(str(files("pfp").joinpath("infrastructure", "tower_research", "level_engine")))
    evidence = evidence_root or Path(str(files("pfp").joinpath("infrastructure", "tower_evidence", "level_engine")))
    governance = governance_root or Path(str(files("governance"))) / "contracts" / "level_engine" / "v2"
    # This snapshot carries the recorded audit; it does not claim a fresh local build.
    lean = lean_root or evidence / "v2" / "lean" / "sources"
    return LevelEngineContext(runtime, evidence, governance, repository_root, vendor_root,
                              output_root, lean, reach_root)
