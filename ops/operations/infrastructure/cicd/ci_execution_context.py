"""Execution Context for local CI gate execution, receipt generation, and verification."""

from __future__ import annotations

import hashlib
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from operations.domain.cicd import (
    CandidateManifestEntryV1,
    CanonicalCandidateManifestV1,
    GateResult,
    GateSpec,
    GateStatus,
    LocalCiExecutionReceiptV3,
    LocalCiInvocationV1,
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
    ToolGateRouteV1,
    TrustedEvaluatorAnchorV1,
    active_gate_specs,
)
from operations.infrastructure.cicd.serialization import (
    canonical_gate_catalog_sha256,
)


@dataclass
class ExecutionContextConfig:
    repo_root: Path = field(default_factory=lambda: Path.cwd())
    timeout_buffer_seconds: int = 5


def _head_blob_oid(repo_root: Path, rel_path: str) -> str:
    """HEAD blob oid, or the zero oid when git cannot answer."""
    try:
        blob_res = subprocess.run(
            ["git", "ls-tree", "HEAD", rel_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "0" * 40
    parts = blob_res.stdout.split()
    if len(parts) >= 3:
        return parts[2]
    return "0" * 40


class CiExecutionContext:
    """Execution Context managing runtime repository state, gate resolution, and receipt generation."""

    def __init__(self, config: ExecutionContextConfig | None = None) -> None:
        self.config = config or ExecutionContextConfig()
        self.repo_root = self.config.repo_root.resolve()

    def get_git_oid(self, revision: str = "HEAD") -> str:
        """Fetch strict 40-char git commit OID for a revision.

        A failed rev-parse is a refusal. Forty zeros are not a commit.
        """
        try:
            res = subprocess.run(
                ["git", "rev-parse", revision],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as err:
            detail = " ".join(str(err).split()) or type(err).__name__
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.IO_ERROR,
                f"git rev-parse failed: {detail}",
            ) from err
        oid = res.stdout.strip()
        if (
            len(oid) == 40
            and oid != "0" * 40
            and all(c in "0123456789abcdef" for c in oid)
        ):
            return oid
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            f"git rev-parse returned invalid OID: {oid!r}",
        )

    def build_candidate_manifest(
        self, base_oid: str, head_oid: str
    ) -> CanonicalCandidateManifestV1:
        """Build canonical candidate manifest for changed files between base and head."""
        entries: list[CandidateManifestEntryV1] = []
        diff_argv = ["git", "diff", "--name-only", f"{base_oid}..{head_oid}"]
        try:
            res = subprocess.run(
                diff_argv,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
        except Exception as err:
            detail = " ".join(str(err).split()) or type(err).__name__
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.IO_ERROR,
                f"git diff failed: {detail}",
            ) from err
        if res.returncode != 0:
            detail = " ".join(f"{res.stderr or ''} {res.stdout or ''}".split())
            message = f"git diff exited {res.returncode}"
            if detail:
                message = f"{message}: {detail}"
            raise LocalCiReceiptError(LocalCiReceiptErrorCode.IO_ERROR, message)
        changed_paths = [
            p.strip() for p in res.stdout.splitlines() if p.strip()
        ]

        for rel_path in sorted(set(changed_paths)):
            if not rel_path or rel_path.startswith("/") or "\\" in rel_path:
                continue
            full_path = self.repo_root / rel_path
            if full_path.is_file():
                try:
                    blob_res = subprocess.run(
                        ["git", "ls-tree", head_oid, rel_path],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                    )
                    parts = blob_res.stdout.split()
                    blob_oid = parts[2] if len(parts) >= 3 else "0" * 40

                    content_bytes = full_path.read_bytes()
                    content_sha256 = hashlib.sha256(content_bytes).hexdigest()
                    entries.append(
                        CandidateManifestEntryV1(
                            path=rel_path,
                            blob_oid=blob_oid,
                            content_sha256=content_sha256,
                        )
                    )
                except Exception:
                    entries.append(
                        CandidateManifestEntryV1(
                            path=rel_path,
                            blob_oid=None,
                            content_sha256=None,
                        )
                    )
            else:
                entries.append(
                    CandidateManifestEntryV1(
                        path=rel_path,
                        blob_oid=None,
                        content_sha256=None,
                    )
                )

        return CanonicalCandidateManifestV1(
            base_oid=base_oid,
            head_oid=head_oid,
            entries=tuple(entries),
        )

    def get_evaluator_anchors(self) -> tuple[TrustedEvaluatorAnchorV1, ...]:
        """Collect trusted evaluator anchor models for core protocol files."""
        anchors: list[TrustedEvaluatorAnchorV1] = []
        target_files = [
            (
                "receipt_verifier",
                "operations/entrypoints/local_ci_receipt_verifier.py",
            ),
            (
                "host_adapter",
                "operations/infrastructure/cicd/local_ci_host.py",
            ),
        ]
        for name, rel_path in target_files:
            full_path = self.repo_root / rel_path
            if full_path.is_file():
                content = full_path.read_bytes()
                sha256_val = hashlib.sha256(content).hexdigest()
                blob_oid = _head_blob_oid(self.repo_root, rel_path)
                anchors.append(
                    TrustedEvaluatorAnchorV1(
                        name=name,
                        path=rel_path,
                        blob_oid=blob_oid,
                        content_sha256=sha256_val,
                    )
                )
            else:
                anchors.append(
                    TrustedEvaluatorAnchorV1(
                        name=name,
                        path=rel_path,
                        blob_oid="0" * 40,
                        content_sha256="0" * 64,
                    )
                )
        # `LocalCiInvocationV1` requires anchors sorted by UTF-8 ordinal bytes.
        # `target_files` above is a hand-ordered literal, and its order was
        # wrong: sorted, `host_adapter` precedes `protocol_core` (h < p). The
        # model refused its own builder's output on every invocation, so local
        # CI has never run. Sorting here rather than reordering the literal,
        # because a reordered literal breaks again the moment a third anchor is
        # appended in the obvious place.
        return tuple(sorted(anchors, key=lambda anchor: anchor.name.encode("utf-8")))

    def execute_gate_spec(
        self, gate: GateSpec, manifest: CanonicalCandidateManifestV1
    ) -> GateResult:
        """Execute a single active GateSpec in this context and capture measured result."""
        from operations.use_cases.cicd.gate_resolution import (
            build_gate_result,
            resolve_gate_invocation,
        )

        resolved = resolve_gate_invocation(gate, manifest)
        start_time = time.perf_counter()

        if isinstance(gate.route, ToolGateRouteV1) and not resolved.resolved_inputs:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return build_gate_result(
                gate,
                manifest,
                status=GateStatus.PASS,
                exit_code=0,
                duration_ms=duration_ms,
                detail="measured zero candidate Rust inputs; no process dispatched",
            )

        try:
            process = subprocess.run(
                resolved.resolved_argv,
                cwd=self.repo_root / gate.cwd,
                capture_output=True,
                text=True,
                timeout=gate.timeout_seconds,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            status = (
                GateStatus.PASS if process.returncode == 0 else GateStatus.FAIL
            )
            detail = (
                (process.stdout + "\n" + process.stderr).strip()[:4000]
                if process.returncode != 0
                else "OK"
            )
            return build_gate_result(
                gate,
                manifest,
                status=status,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                detail=detail,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return build_gate_result(
                gate,
                manifest,
                status=GateStatus.TIMEOUT,
                exit_code=None,
                duration_ms=duration_ms,
                detail=f"Execution timed out after {gate.timeout_seconds}s",
            )
        except Exception as err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            # `GateResult.detail` refuses control characters, and an exception
            # string carries newlines. Reporting a gate that failed to start
            # therefore raised from inside the error handler, replacing a named
            # gate failure with a pydantic traceback -- the failure path was
            # never exercised. Collapse whitespace so the reason survives.
            err = " ".join(str(err).split())
            return build_gate_result(
                gate,
                manifest,
                status=GateStatus.UNAVAILABLE,
                exit_code=None,
                duration_ms=duration_ms,
                detail=f"Execution failed to start: {err}",
            )

    def run_all_active_gates(
        self, base_oid: str | None = None, head_oid: str | None = None
    ) -> tuple[LocalCiExecutionReceiptV3, tuple[GateResult, ...]]:
        """Run all active gate specifications, evaluate results, and build receipt."""
        head = head_oid or self.get_git_oid("HEAD")
        base = base_oid or self.get_git_oid("HEAD~1")

        manifest = self.build_candidate_manifest(base, head)
        anchors = self.get_evaluator_anchors()
        nonce = hashlib.sha256(
            f"{head}:{time.time()}".encode("utf-8")
        ).hexdigest()

        invocation = LocalCiInvocationV1(
            expected_head=head,
            observed_head_before=head,
            expected_main=base,
            observed_main_before=base,
            nonce=nonce,
            gate_catalog_sha256=canonical_gate_catalog_sha256(),
            candidate_manifest=manifest,
            evaluator_anchors=anchors,
        )

        from operations.infrastructure.cicd.gate_catalog_loader import (
            ensure_gate_catalog,
        )

        ensure_gate_catalog()
        active = active_gate_specs()
        results: list[GateResult] = []
        for gate in active:
            result = self.execute_gate_spec(gate, manifest)
            results.append(result)

        from operations.use_cases.cicd.gate_resolution import (
            build_local_ci_receipt,
        )

        receipt = build_local_ci_receipt(
            invocation,
            observed_head_after=head,
            observed_main_after=base,
            results=results,
        )
        return receipt, tuple(results)
