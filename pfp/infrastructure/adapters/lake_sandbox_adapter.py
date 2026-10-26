"""Sandboxed Lake 4 Verification Adapter (U17).

Executes sandboxed Lean 4 builds, statement elaboration harnesses, and axiom audits.
AuthorityEffect: None.
"""

from __future__ import annotations

import os
import hashlib
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import (
    Err,
    Ok,
    Refusal,
    Result,
)
from omega_engine_pfp.domain.lean_bridge.models import (
    LeanVerificationRequest,
    LeanVerificationReceipt,
)
from omega_engine_pfp.domain.ports.lean_port import LeanVerifierPort
from omega_engine_pfp.ffi import RustSymbolGameHost, get_default_host


class LakeSandboxAdapter(LeanVerifierPort):
    """Sandboxed execution harness for checking submitted Lean 4 packages."""

    def __init__(
        self,
        host: RustSymbolGameHost | None = None,
        lake_binary: str | Path | None = None,
        timeout_seconds: int = 60,
        *,
        process_observer: Callable[[dict[str, Any]], None] | None = None,
        verify_toolchain: bool = False,
    ) -> None:
        self._host = host if host is not None else get_default_host()
        self._lake_binary = str(lake_binary) if lake_binary is not None else None
        self._timeout_seconds = timeout_seconds
        self._process_observer = process_observer
        self._verify_toolchain = verify_toolchain

    def verify(
        self,
        request: LeanVerificationRequest,
        package_path: Path,
    ) -> Result[LeanVerificationReceipt, Refusal]:
        """Verify a Lean 4 submission package against required declarations and axiom policy."""
        if self._process_observer is not None or self._verify_toolchain:
            return self._verify_observed(request, package_path)
        return self._verify_legacy(request, package_path)

    def _verify_observed(
        self,
        request: LeanVerificationRequest,
        package_path: Path,
    ) -> Result[LeanVerificationReceipt, Refusal]:
        """Capture actual processes and reject changes to the selected package."""
        resolved = self._lake_binary if self._lake_binary is not None else shutil.which("lake")
        if resolved is None or not Path(resolved).is_file():
            return Err(
                Refusal("LEAN_TOOLCHAIN_UNAVAILABLE", "Selected Lake executable is unavailable")
            )
        lake = Path(resolved).resolve()
        if not package_path.is_dir():
            return Err(
                Refusal("PACKAGE_PATH_NOT_FOUND", "Selected package directory is unavailable")
            )

        def digest(raw: bytes) -> str:
            return "sha256:" + hashlib.sha256(raw).hexdigest()

        def emit(event: dict[str, Any]) -> None:
            if self._process_observer is not None:
                self._process_observer(event)

        with tempfile.TemporaryDirectory(prefix="lean_verify_") as tmpdir:
            pkg = Path(tmpdir) / "pkg"
            shutil.copytree(package_path, pkg)
            sources = []
            try:
                for path in sorted(pkg.rglob("*.lean")):
                    if ".lake" not in path.relative_to(pkg).parts:
                        sources.append(
                            {
                                "file": path.relative_to(pkg).as_posix(),
                                "content": path.read_bytes().decode("utf-8"),
                            }
                        )
            except (OSError, UnicodeError) as exc:
                return Err(Refusal("SOURCE_READ_ERROR", str(exc)))
            modules = [
                Path(entry["file"]).with_suffix("").as_posix().replace("/", ".")
                for entry in sources
                if entry["file"] not in ("lakefile.lean", "Verify.lean")
            ]
            if not modules:
                return Err(
                    Refusal(
                        "LEAN_SOURCE_MODULES_UNAVAILABLE", "No submitted Lean modules to verify"
                    )
                )
            scan = self._host.lean_scan_sources(
                sources=sources, forbidden_constructs=request.forbidden_set
            )
            if scan.is_err:
                return Err(scan.unwrap_err())
            raw_scan = scan.unwrap()
            findings = raw_scan.get("result", raw_scan).get("findings", [])
            lines = ["-- Auto-generated Judge Verification Harness", "import " + " ".join(modules)]
            check_names = []
            for index, (name, statement) in enumerate(request.required_declarations, 1):
                check_name = f"judge_check_{index}"
                check_names.append(check_name)
                lines.extend(
                    (f"theorem {check_name} : {statement} := {name}", f"#print axioms {check_name}")
                )
            harness = ("\n".join(lines) + "\n").encode("utf-8")
            (pkg / "Verify.lean").write_bytes(harness)
            protected = sorted(
                {entry["file"] for entry in sources} | {"Verify.lean", "lean-toolchain"}
            )

            def manifest() -> list[list[str]]:
                return [[name, digest((pkg / name).read_bytes())] for name in protected]

            try:
                original_manifest = manifest()
                original_lake = digest(lake.read_bytes())
            except OSError as exc:
                return Err(Refusal("SOURCE_READ_ERROR", str(exc)))
            emit(
                {
                    "kind": "verification_context",
                    "package_manifest": original_manifest,
                    "harness_source_hex": harness.hex(),
                    "harness_source_sha256": digest(harness),
                }
            )

            def unchanged() -> bool:
                try:
                    return (
                        manifest() == original_manifest
                        and digest(lake.read_bytes()) == original_lake
                    )
                except OSError:
                    return False

            def run(
                label: str, argv: list[str]
            ) -> Result[subprocess.CompletedProcess[bytes], Refusal]:
                if not unchanged():
                    return Err(
                        Refusal(
                            "LEAN_SOURCE_CHANGED", "Selected package or Lake executable changed"
                        )
                    )
                started = time.time_ns() // 1_000_000
                try:
                    proc = subprocess.run(
                        argv,
                        cwd=pkg,
                        capture_output=True,
                        text=False,
                        timeout=self._timeout_seconds,
                        shell=False,
                    )
                except subprocess.TimeoutExpired as exc:
                    out, err = exc.stdout, exc.stderr
                    emit(
                        {
                            "kind": "process",
                            "process": {
                                "label": label,
                                "argv": argv,
                                "cwd": str(pkg),
                                "exit_code": None,
                                "stdout_hex": out.hex() if out is not None else None,
                                "stdout_sha256": digest(out) if out is not None else None,
                                "stderr_hex": err.hex() if err is not None else None,
                                "stderr_sha256": digest(err) if err is not None else None,
                                "started_at_ms": started,
                                "completed_at_ms": None,
                                "direct_child_completed": False,
                                "shell": False,
                            },
                        }
                    )
                    return Err(
                        Refusal("TIMEOUT", f"{label} timed out after {self._timeout_seconds}s")
                    )
                except OSError as exc:
                    return Err(Refusal("LEAN_TOOLCHAIN_UNAVAILABLE", str(exc)))
                completed = time.time_ns() // 1_000_000
                emit(
                    {
                        "kind": "process",
                        "process": {
                            "label": label,
                            "argv": argv,
                            "cwd": str(pkg),
                            "exit_code": proc.returncode,
                            "stdout_hex": proc.stdout.hex(),
                            "stdout_sha256": digest(proc.stdout),
                            "stderr_hex": proc.stderr.hex(),
                            "stderr_sha256": digest(proc.stderr),
                            "started_at_ms": started,
                            "completed_at_ms": completed,
                            "direct_child_completed": True,
                            "shell": False,
                        },
                    }
                )
                if not unchanged():
                    return Err(
                        Refusal(
                            "LEAN_SOURCE_CHANGED",
                            "Selected package or Lake executable changed after execution",
                        )
                    )
                return Ok(proc)

            if self._verify_toolchain:
                version_result = run("toolchain", [str(lake), "env", "lean", "--version"])
                if version_result.is_err:
                    return Err(version_result.unwrap_err())
                version_proc = version_result.unwrap()
                try:
                    version = re.search(
                        r"Lean \(version ([^,\s]+)", version_proc.stdout.decode("utf-8")
                    )
                except UnicodeError as exc:
                    return Err(Refusal("LEAN_TOOLCHAIN_VERSION_INVALID", str(exc)))
                expected = request.toolchain_pin.removeprefix("leanprover/lean4:v")
                if (
                    version_proc.returncode != 0
                    or version is None
                    or not request.toolchain_pin.startswith("leanprover/lean4:v")
                    or version[1] != expected
                ):
                    return Err(
                        Refusal(
                            "LEAN_TOOLCHAIN_VERSION_MISMATCH",
                            "Measured Lean version differs from selected toolchain",
                        )
                    )
            build_result = run(
                "build", [str(lake), "build", *(f"+{module}:olean" for module in modules)]
            )
            if build_result.is_err:
                return Err(build_result.unwrap_err())
            build_success = build_result.unwrap().returncode == 0
            harness_elaborated = False
            axioms_output = ""
            if build_success:
                elaborate = run("elaborate", [str(lake), "env", "lean", "Verify.lean"])
                if elaborate.is_err:
                    return Err(elaborate.unwrap_err())
                proc = elaborate.unwrap()
                harness_elaborated = proc.returncode == 0
                try:
                    axioms_output = proc.stdout.decode("utf-8") + "\n" + proc.stderr.decode("utf-8")
                except UnicodeError as exc:
                    return Err(Refusal("LEAN_OUTPUT_ENCODING_INVALID", str(exc)))
            audit = self._host.lean_audit_report(
                axioms_output=axioms_output,
                policy=request.axiom_policy,
                required_declarations=check_names,
                build_success=build_success,
                harness_elaborated=harness_elaborated,
                forbidden_findings=findings,
            )
            if audit.is_err:
                return Err(audit.unwrap_err())
            raw_audit = audit.unwrap()
            report = raw_audit.get("result", raw_audit)
            axioms = report.get("axioms_by_declaration", {})
            status, refusal = report.get("status", "FAIL"), report.get("refusal_code")
            if build_success and harness_elaborated:
                if any(name not in axioms for name in check_names):
                    status, refusal = "FAIL", "AXIOM_CENSUS_INCOMPLETE"
                elif any(set(axioms[name]) - set(request.axiom_policy) for name in check_names):
                    status, refusal = "FAIL", "AXIOM_POLICY_VIOLATION"
            return Ok(
                LeanVerificationReceipt(
                    status=status,
                    build_success=build_success,
                    harness_elaborated=harness_elaborated,
                    axioms_by_declaration=tuple(
                        (name, tuple(values)) for name, values in axioms.items()
                    ),
                    forbidden_findings=tuple(report.get("forbidden_findings", ())),
                    refusal_code=refusal,
                    details=report.get("details"),
                    authority_effect="None",
                )
            )

    def _verify_legacy(
        self, request: LeanVerificationRequest, package_path: Path,
    ) -> Result[LeanVerificationReceipt, Refusal]:
        resolved_lake = self._lake_binary or shutil.which("lake")
        if not resolved_lake or not os.path.exists(resolved_lake):
            return Err(
                Refusal(
                    code="LEAN_TOOLCHAIN_UNAVAILABLE",
                    message="Lake executable not found on host or sandbox environment",
                )
            )

        if not package_path.exists():
            return Err(
                Refusal(
                    code="PACKAGE_PATH_NOT_FOUND",
                    message=f"Package directory does not exist: {package_path}",
                )
            )

        # 1. Collect all .lean sources and scan with host action
        source_entries = []
        for p in sorted(package_path.rglob("*.lean")):
            if ".lake" in p.relative_to(package_path).parts:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                rel_path = p.relative_to(package_path).as_posix()
                source_entries.append({"file": rel_path, "content": content})
            except Exception as e:
                return Err(
                    Refusal(
                        code="SOURCE_READ_ERROR",
                        message=f"Failed to read source {p}: {e}",
                    )
                )

        modules = [
            Path(entry["file"]).with_suffix("").as_posix().replace("/", ".")
            for entry in source_entries
            if entry["file"] not in ("lakefile.lean", "Verify.lean")
        ]
        if not modules:
            return Err(Refusal(code="LEAN_SOURCE_MODULES_UNAVAILABLE", message="No submitted Lean modules to verify"))

        scan_outcome = self._host.lean_scan_sources(
            sources=source_entries,
            forbidden_constructs=request.forbidden_set,
        )
        if scan_outcome.is_err:
            return Err(scan_outcome.unwrap_err())

        raw_scan = scan_outcome.unwrap()
        scan_report = raw_scan.get("result", raw_scan)
        findings = scan_report.get("findings", [])

        # 2. Build in sandboxed temp directory
        with tempfile.TemporaryDirectory(prefix="lean_verify_") as tmpdir:
            work_dir = Path(tmpdir)
            shutil.copytree(package_path, work_dir / "pkg", dirs_exist_ok=True)
            pkg_dir = work_dir / "pkg"

            # 3. Write judge harness Verify.lean
            harness_lines = [
                "-- Auto-generated Judge Verification Harness",
            ]
            # A Lake package may have no default target. Build and import every
            # submitted module explicitly; lakefile.lean is configuration and
            # Verify.lean is reserved for this judge-owned harness.
            harness_lines.append("import " + " ".join(modules))

            check_names = []
            for idx, (claimed_name, hidden_statement) in enumerate(request.required_declarations, start=1):
                check_name = f"judge_check_{idx}"
                check_names.append(check_name)
                harness_lines.append(f"theorem {check_name} : {hidden_statement} := {claimed_name}")
                harness_lines.append(f"#print axioms {check_name}")

            harness_path = pkg_dir / "Verify.lean"
            harness_path.write_text("\n".join(harness_lines) + "\n", encoding="utf-8")

            # 4. Run lake build
            try:
                build_proc = subprocess.run(
                    [resolved_lake, "build", *(f"+{module}:olean" for module in modules)],
                    cwd=pkg_dir,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds,
                )
                build_success = build_proc.returncode == 0
            except subprocess.TimeoutExpired:
                return Err(
                    Refusal(
                        code="TIMEOUT",
                        message=f"Lake build timed out after {self._timeout_seconds}s",
                    )
                )
            except Exception:
                build_success = False

            # 5. Run lake env lean Verify.lean
            axioms_output = ""
            harness_elaborated = False
            if build_success:
                try:
                    lean_proc = subprocess.run(
                        [resolved_lake, "env", "lean", "Verify.lean"],
                        cwd=pkg_dir,
                        capture_output=True,
                        text=True,
                        timeout=self._timeout_seconds,
                    )
                    harness_elaborated = lean_proc.returncode == 0
                    axioms_output = (lean_proc.stdout or "") + "\n" + (lean_proc.stderr or "")
                except subprocess.TimeoutExpired:
                    return Err(
                        Refusal(
                            code="TIMEOUT",
                            message=f"Lean elaboration timed out after {self._timeout_seconds}s",
                        )
                    )
                except Exception:
                    harness_elaborated = False

            # 6. Dispatch to native Rust auditor
            audit_outcome = self._host.lean_audit_report(
                axioms_output=axioms_output,
                policy=request.axiom_policy,
                required_declarations=check_names,
                build_success=build_success,
                harness_elaborated=harness_elaborated,
                forbidden_findings=findings,
            )
            if audit_outcome.is_err:
                return Err(audit_outcome.unwrap_err())

            raw_audit = audit_outcome.unwrap()
            audit_report = raw_audit.get("result", raw_audit)

            axioms_map = tuple(
                (k, tuple(v))
                for k, v in audit_report.get("axioms_by_declaration", {}).items()
            )

            receipt = LeanVerificationReceipt(
                status=audit_report.get("status", "FAIL"),
                build_success=audit_report.get("build_success", False),
                harness_elaborated=audit_report.get("harness_elaborated", False),
                axioms_by_declaration=axioms_map,
                forbidden_findings=tuple(audit_report.get("forbidden_findings", ())),
                refusal_code=audit_report.get("refusal_code"),
                details=audit_report.get("details"),
                authority_effect="None",
            )
            return Ok(receipt)
