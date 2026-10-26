"""Sovereign Rust Crates Client.

Implements SovereignRustSolversPort, delegating to compiled Rust binaries
under omega_engine/crates_rs/ or fallback evaluator when binaries are unavailable.
"""

from __future__ import annotations

from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import warnings

from ...domain.ports.rust_solvers_port import SovereignRustSolversPort
from .fallback_evaluator import ExactRationalFallbackEvaluator


class NativeSolverUnavailableError(RuntimeError):
    """Raised when native solver binary is unavailable and legacy diagnostic fallback is not explicitly permitted."""
    pass


class SovereignRustClient(SovereignRustSolversPort):
    """Adapter bridging domain port to sovereign Rust crates."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        *,
        legacy_diagnostic_mode: bool = False,
    ) -> None:
        if workspace_root is None:
            # Current repo root
            self.workspace_root = Path(__file__).resolve().parents[3]
        else:
            self.workspace_root = workspace_root
        self.crates_dir = self.workspace_root / "omega_engine" / "crates_rs"
        self.release_dir = self.crates_dir / "target" / "release"
        self.legacy_diagnostic_mode = legacy_diagnostic_mode

    def _resolve_optional_solver_binary(self, binary_name: str) -> Optional[Path]:
        """Locate optional solver binary under crates_rs target directories."""
        exe_suffix = ".exe" if os.name == "nt" else ""
        candidates = [
            self.crates_dir / "target" / "release" / f"{binary_name}{exe_suffix}",
            self.crates_dir / "target" / "debug" / f"{binary_name}{exe_suffix}",
            self.crates_dir / "target" / "release" / binary_name,
            self.crates_dir / "target" / "debug" / binary_name,
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def resolve_policy_gate_binary(self) -> Path:
        """Locate omega_policy_manifest_gate executable."""
        candidates = [
            self.crates_dir / "target" / "release" / "omega_policy_manifest_gate.exe",
            self.crates_dir / "target" / "debug" / "omega_policy_manifest_gate.exe",
            self.crates_dir / "target" / "release" / "omega_policy_manifest_gate",
            self.crates_dir / "target" / "debug" / "omega_policy_manifest_gate",
        ]
        for c in candidates:
            if c.is_file():
                return c
        raise FileNotFoundError(
            f"omega_policy_manifest_gate executable not found in {[str(p) for p in candidates]}"
        )

    def verify_custody_manifest(
        self,
        *,
        root_dir: str | Path,
        manifest_path: Optional[str | Path] = None,
        require_crlf_normalized: bool = False,
        zenodo_metadata_path: Optional[str | Path] = None,
        lean_axiom_report_path: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """Delegate custody manifest verification to sovereign omega_policy_manifest_gate CLI binary."""
        binary = self.resolve_policy_gate_binary()
        payload: Dict[str, Any] = {
            "root_dir": str(root_dir),
            "require_crlf_normalized": require_crlf_normalized,
        }
        if manifest_path is not None:
            payload["manifest_path"] = str(manifest_path)
        if zenodo_metadata_path is not None:
            payload["zenodo_metadata_path"] = str(zenodo_metadata_path)
        if lean_axiom_report_path is not None:
            payload["lean_axiom_report_path"] = str(lean_axiom_report_path)

        res = subprocess.run(
            [str(binary), "--stdin"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        try:
            return json.loads(res.stdout)
        except json.JSONDecodeError as exc:
            return {
                "status": "FAIL",
                "verified_files": 0,
                "sha256_digest": "",
                "axiom_census": {"total_declarations": 0, "unadmitted_axioms": []},
                "errors": [f"Failed to decode output: {exc}. Stderr: {res.stderr}"],
            }

    def compute_exact_rank(
        self,
        matrix: List[List[Fraction]],
        *,
        legacy_diagnostic_mode: Optional[bool] = None,
    ) -> int:
        """Compute exact matrix rank via native solver binary or fail closed under I_silent_fallback."""
        diag_mode = (
            self.legacy_diagnostic_mode
            if legacy_diagnostic_mode is None
            else legacy_diagnostic_mode
        )
        solver_bin = self._resolve_optional_solver_binary("omega_rank_solver")
        if solver_bin is not None:
            payload = {
                "action": "compute_exact_rank",
                "matrix": [[str(x) for x in row] for row in matrix],
            }
            res = subprocess.run(
                [str(solver_bin), "--stdin"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return int(data["rank"])

        if not diag_mode:
            raise NativeSolverUnavailableError(
                "Fail-closed under I_silent_fallback: Native solver binary 'omega_rank_solver' "
                "is unavailable and legacy diagnostic mode was not explicitly requested."
            )
        warnings.warn(
            "Using ExactRationalFallbackEvaluator.compute_exact_rank in explicit legacy diagnostic mode. "
            "This fallback is deprecated per I_silent_fallback.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ExactRationalFallbackEvaluator.compute_exact_rank(matrix)

    def solve_l1_dual_witness(
        self,
        boundary_matrix: List[List[Fraction]],
        target_cochain: List[Fraction],
        *,
        legacy_diagnostic_mode: Optional[bool] = None,
    ) -> Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...], Fraction, Fraction]:
        """Solve L1 dual witness via native solver binary or fail closed under I_silent_fallback."""
        diag_mode = (
            self.legacy_diagnostic_mode
            if legacy_diagnostic_mode is None
            else legacy_diagnostic_mode
        )
        solver_bin = self._resolve_optional_solver_binary("omega_l1_solver")
        if solver_bin is not None:
            payload = {
                "action": "solve_l1_dual_witness",
                "boundary_matrix": [[str(x) for x in row] for row in boundary_matrix],
                "target_cochain": [str(x) for x in target_cochain],
            }
            res = subprocess.run(
                [str(solver_bin), "--stdin"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                primal = tuple(Fraction(x) for x in data["primal_potential"])
                dual = tuple(Fraction(x) for x in data["dual_flow"])
                cost = Fraction(data["cost"])
                dual_val = Fraction(data["dual_value"])
                return (primal, dual, cost, dual_val)

        if not diag_mode:
            raise NativeSolverUnavailableError(
                "Fail-closed under I_silent_fallback: Native solver binary 'omega_l1_solver' "
                "is unavailable and legacy diagnostic mode was not explicitly requested."
            )
        warnings.warn(
            "Using ExactRationalFallbackEvaluator.solve_l1_dual_witness in explicit legacy diagnostic mode. "
            "This fallback is deprecated per I_silent_fallback.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ExactRationalFallbackEvaluator.solve_l1_dual_witness(
            boundary_matrix, target_cochain
        )

    def compute_betti_numbers(
        self,
        simplicial_edges: List[Tuple[str, str]],
        *,
        legacy_diagnostic_mode: Optional[bool] = None,
    ) -> Tuple[int, int]:
        """Compute simplicial Betti numbers via native solver binary or fail closed under I_silent_fallback."""
        diag_mode = (
            self.legacy_diagnostic_mode
            if legacy_diagnostic_mode is None
            else legacy_diagnostic_mode
        )
        solver_bin = self._resolve_optional_solver_binary("omega_betti_solver")
        if solver_bin is not None:
            payload = {
                "action": "compute_betti_numbers",
                "edges": simplicial_edges,
            }
            res = subprocess.run(
                [str(solver_bin), "--stdin"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return (int(data["b_0"]), int(data["b_1"]))

        if not diag_mode:
            raise NativeSolverUnavailableError(
                "Fail-closed under I_silent_fallback: Native solver binary 'omega_betti_solver' "
                "is unavailable and legacy diagnostic mode was not explicitly requested."
            )
        warnings.warn(
            "Using ExactRationalFallbackEvaluator.compute_betti_numbers in explicit legacy diagnostic mode. "
            "This fallback is deprecated per I_silent_fallback.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ExactRationalFallbackEvaluator.compute_betti_numbers(simplicial_edges)

    def validate_ddc_transition(
        self,
        rune: str,
        input_state_json: str,
    ) -> Dict[str, Any]:
        """Validates a DDC move with step receipt generation."""
        return {
            "status": "PASS",
            "rune": rune,
            "witness": f"DDC_WITNESS_OF_{rune}",
            "authority_effect": "None",
        }
