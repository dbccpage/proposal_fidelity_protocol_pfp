"""Domain protocols for Flagship Systems, Duality Solvers & Kernel Bridges (Prompt 12, 13, 32, 43).

AuthorityEffect: None.
Clean Architecture: Domain port protocols (@runtime_checkable).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping, Protocol, Sequence, Tuple, runtime_checkable

from ..dual_witness.models import ExactDualWitnessCertificate
from ..sandbox.models import ProcessBoundaryConfig, SeamExecutionResult
from pfp.domain.mssn_research.shared_kernel.result import Result


@runtime_checkable
class ExactDualLpPort(Protocol):
    """Protocol for exact rational linear programming and L1 projection over Q."""

    def solve_primal_dual(
        self,
        c_cost: Sequence[Fraction],
        a_matrix: Sequence[Sequence[Fraction]],
        b_bounds: Sequence[Fraction],
    ) -> Tuple[Sequence[Fraction], Sequence[Fraction], Fraction]:
        """Solves primal-dual LP in exact rational arithmetic, returning (primal_x, dual_y, gap)."""
        ...

    def solve_l1_projection(
        self,
        target: Sequence[Fraction],
        basis_matrix: Sequence[Sequence[Fraction]],
        weights: Sequence[Fraction],
    ) -> ExactDualWitnessCertificate:
        """Solves exact weighted L1 projection emitting primal-dual witness certificate."""
        ...


@runtime_checkable
class ProcessSandboxPort(Protocol):
    """Protocol for isolated process execution seam (mocked Profile A / container Profile B)."""

    def execute_seam(
        self,
        cmd: Sequence[str],
        input_payload: Mapping[str, Any],
        config: ProcessBoundaryConfig,
    ) -> Result[SeamExecutionResult, str]:
        """Executes process within declared boundary, capturing stdin/stdout and exit codes."""
        ...


@runtime_checkable
class LeanKernelBridgePort(Protocol):
    """Protocol for verifying Lean 4 formal proof kernels and Lake elaboration."""

    def verify_module_sha256(self, module_name: str, expected_sha256: str) -> bool:
        """Verifies on-disk .lean source bytes against cryptographic hash."""
        ...

    def scan_sorry_axioms(self, module_name: str) -> list[str]:
        """Scans on-disk .lean source for occurrences of unproven sorryAx / sorry."""
        ...

    def check_lake_elaboration(self) -> Tuple[int, str]:
        """Invokes Lake toolchain to verify formal proof elaboration status."""
        ...
