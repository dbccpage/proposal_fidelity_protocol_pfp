"""Adversary connector to live Lake toolchain verification for Lean 4 packages.

Validates generated Lean 4 candidates (e.g. Discrete4DBianchiSpectralContraction.lean)
against a live Lake toolchain build using LakeSandboxAdapter.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.domain.lean_bridge.models import LeanVerificationRequest
from pfp.infrastructure.adapters.lake_sandbox_adapter import LakeSandboxAdapter
from .canonical_lean import (
    CANONICAL_DISCRETE_4D_BIANCHI_LEAN,
)
from adversary.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    sha256_ref,
)

DEFAULT_LEAN_TOOLCHAIN = "leanprover/lean4:v4.34.1"
DEFAULT_LAKE_PATH = r"C:\Users\a343o\.elan\toolchains\leanprover--lean4---v4.34.1\bin\lake.exe"
DEFAULT_REQUIRED_DECLARATIONS = (
    (
        "bridge_mub6_coverage_master",
        "BridgeMub6CoverageContract → "
        "0 < spectral_floor_frac.num ∧ "
        "(∀ (F : Simplicial2Cochain Int), d3 (d2 F) = 0) ∧ "
        "(∀ (ω : Simplicial1Cochain Int) (i j k l : Fin 5), curvature_closure_defect ω i j k l = 0) ∧ "
        "(∀ (phi1 : Int), 0 < phi1 → integer_closure_ratio 0 phi1 = 0)",
    ),
)


def extract_lean_source(candidate: bytes) -> tuple[bytes, str]:
    """Preserve raw bytes or exactly one complete, explicit Lean fence body."""
    if type(candidate) is not bytes or not candidate:
        raise ValueError("Require nonempty candidate bytes")
    candidate.decode("utf-8")  # Reject invalid encoding; never replace bytes.
    markers = list(re.finditer(rb"(?m)^```[^\r\n]*(?:\r?\n|\Z)", candidate))
    if not markers:
        return candidate, "raw-lean-v1"
    if len(markers) != 2:
        raise ValueError("Require exactly one complete Lean fence")
    opening, closing = markers
    if (
        re.fullmatch(rb"```(?:lean4|lean)[ \t]*\r?\n", opening.group()) is None
        or re.fullmatch(rb"```[ \t]*(?:\r?\n|\Z)", closing.group()) is None
    ):
        raise ValueError("Require an unambiguous complete Lean fence")
    source = candidate[opening.end() : closing.start()]
    if not source:
        raise ValueError("Lean fence body is empty")
    return source, "single-lean-fence-v1"


class LakeLiveCandidateChecker:
    """CandidateCheckerPort implementation verifying Lean 4 modules against live Lake build."""

    def __init__(
        self,
        *,
        lake_binary: str | Path | None = None,
        toolchain_pin: str = DEFAULT_LEAN_TOOLCHAIN,
        timeout_seconds: int = 60,
        required_declarations: tuple[tuple[str, str], ...] | None = None,
        axiom_policy: tuple[str, ...] = ("propext", "Quot.sound"),
    ) -> None:
        if lake_binary is not None:
            self.lake_binary = Path(lake_binary)
        elif os.path.exists(DEFAULT_LAKE_PATH):
            self.lake_binary = Path(DEFAULT_LAKE_PATH)
        else:
            resolved = shutil.which("lake")
            self.lake_binary = Path(resolved) if resolved else None

        self.toolchain_pin = toolchain_pin
        self.timeout_seconds = timeout_seconds
        self.required_declarations = (
            DEFAULT_REQUIRED_DECLARATIONS
            if required_declarations is None
            else tuple(tuple(pair) for pair in required_declarations)
        )
        if not self.required_declarations or any(
            len(pair) != 2 or any(type(value) is not str or not value.strip() for value in pair)
            for pair in self.required_declarations
        ):
            raise ValueError("LEAN_REQUIRED_DECLARATIONS_INVALID")
        self.axiom_policy = tuple(axiom_policy)
        if any(type(value) is not str or not value.strip() for value in self.axiom_policy):
            raise ValueError("LEAN_AXIOM_POLICY_INVALID")
        self.last_verification: dict[str, Any] | None = None

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        """Check only submitted source; a kernel pass is relative to selected obligations."""
        del carrier_context
        self.last_verification = {"processes": []}
        try:
            lean_source, profile = extract_lean_source(candidate_bytes)
        except (ValueError, UnicodeError) as exc:
            return Err(Refusal("LEAN_CANDIDATE_INVALID", str(exc), __name__))
        base = {
            "schema_version": "core.adversary.lake-check.v2",
            "authority_effect": "None",
            "run_key": run_key,
            "candidate_id": candidate_id,
            "candidate_content_sha256": sha256_ref(candidate_bytes),
            "candidate_content_hex": candidate_bytes.hex(),
            "lean_source_sha256": sha256_ref(lean_source),
            "lean_source_hex": lean_source.hex(),
            "extraction_profile": profile,
            "objective_sha256": sha256_ref(objective.encode("utf-8")),
            "checker_id": "lake_sandbox_adapter",
            "toolchain_pin": self.toolchain_pin,
            "required_declarations": [list(pair) for pair in self.required_declarations],
            "axiom_policy": list(self.axiom_policy),
            "lake_binary_path": str(self.lake_binary.resolve()) if self.lake_binary else None,
            "lake_binary_sha256": sha256_ref(self.lake_binary.read_bytes())
            if self.lake_binary and self.lake_binary.is_file()
            else None,
        }

        def capture(event):
            if event["kind"] == "process":
                self.last_verification["processes"].append(event["process"])
            elif event["kind"] == "verification_context":
                self.last_verification.update(
                    {key: value for key, value in event.items() if key != "kind"}
                )

        with tempfile.TemporaryDirectory(prefix="lake_cand_check_") as tmpdir:
            pkg_dir = Path(tmpdir) / "pkg"
            pkg_dir.mkdir()

            (pkg_dir / "lean-toolchain").write_bytes((self.toolchain_pin + "\n").encode("utf-8"))
            (pkg_dir / "lakefile.lean").write_bytes(
                (
                    "import Lake\nopen Lake DSL\n\n"
                    "package «Discrete4DBianchiSpectralContraction» where\n"
                    '  version := v!"0.1.0"\n\n'
                    "lean_lib «Discrete4DBianchiSpectralContraction» where\n"
                    '  srcDir := "."\n'
                ).encode("utf-8")
            )
            (pkg_dir / "Discrete4DBianchiSpectralContraction.lean").write_bytes(lean_source)

            adapter = LakeSandboxAdapter(
                lake_binary=self.lake_binary,
                timeout_seconds=self.timeout_seconds,
                process_observer=capture,
                verify_toolchain=True,
            )
            req = LeanVerificationRequest(
                package_digest=f"pkg_{candidate_id}",
                toolchain_pin=self.toolchain_pin,
                required_declarations=self.required_declarations,
                axiom_policy=self.axiom_policy,
            )

            result = adapter.verify(req, pkg_dir)
            if result.is_err:
                refusal = result.unwrap_err()
                partial = {
                    **base,
                    "package_manifest": self.last_verification.get("package_manifest", []),
                    "harness_source_hex": self.last_verification.get("harness_source_hex"),
                    "harness_source_sha256": self.last_verification.get("harness_source_sha256"),
                    "processes": self.last_verification["processes"],
                    "lean_receipt": None,
                    "verdict": "NOT_MEASURED",
                    "reason": refusal.code + ": " + refusal.message,
                }
                raw = json.dumps(
                    partial,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode()
                return Err(
                    Refusal(
                        refusal.code,
                        refusal.message,
                        refusal.locus,
                        details=(*refusal.details, ("lake_receipt_hex", raw.hex())),
                    )
                )
            else:
                receipt = result.unwrap()
                accepted = (
                    receipt.status == "PASS"
                    and receipt.build_success
                    and receipt.harness_elaborated
                )
                reason = receipt.refusal_code or (
                    "PASS" if accepted else "Lake verification failed"
                )
                lean_receipt_data = {
                    "status": receipt.status,
                    "build_success": receipt.build_success,
                    "harness_elaborated": receipt.harness_elaborated,
                    "refusal_code": receipt.refusal_code,
                    "axioms": [list(item) for item in receipt.axioms_by_declaration],
                }

        verdict = CheckerVerdict.ACCEPTED if accepted else CheckerVerdict.REJECTED
        content_digest = base["candidate_content_sha256"]
        receipt_dict = {
            **base,
            **self.last_verification,
            "verdict": verdict.value,
            "lean_receipt": lean_receipt_data,
            "reason": reason,
        }
        raw_receipt = json.dumps(receipt_dict, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

        return Ok(
            CandidateCheckV1(
                verdict=verdict,
                candidate_id=candidate_id,
                candidate_content_sha256=content_digest,
                checker_id="lake_sandbox_adapter",
                checker_receipt_sha256=sha256_ref(raw_receipt),
                checker_receipt_bytes=raw_receipt,
                reason=reason,
            )
        )


__all__ = [
    "CANONICAL_DISCRETE_4D_BIANCHI_LEAN",
    "DEFAULT_LAKE_PATH",
    "DEFAULT_LEAN_TOOLCHAIN",
    "LakeLiveCandidateChecker",
]
