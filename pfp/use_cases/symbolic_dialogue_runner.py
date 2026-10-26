"""Symbolic dialogue use case.

Scenario calculators refuse until a Rust functional adapter returns a score.
This entry raises before any run directory is created.

AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_pfp.functional_boundary import require_rust_functional


def run_symbolic_dialogue(*_args: object, **_kwargs: object) -> None:
    """Refuse the dialogue loop before it writes a run directory."""
    require_rust_functional("run_symbolic_dialogue")


class SymbolicDialogueRunner:
    """Closed entry point for the retired symbolic-dialogue scenarios."""

    def __init__(self, base_output_dir: object = None) -> None:
        self.base_output_dir = base_output_dir

    def run_meron_sign_problem(self, *_args: object, **_kwargs: object) -> None:
        require_rust_functional("SymbolicDialogueRunner.run_meron_sign_problem")

    def run_frustrated_triangular_lattice(self, *_args: object, **_kwargs: object) -> None:
        require_rust_functional("SymbolicDialogueRunner.run_frustrated_triangular_lattice")

    def run_lifted_triangular_lattice_solution(self, *_args: object, **_kwargs: object) -> None:
        require_rust_functional("SymbolicDialogueRunner.run_lifted_triangular_lattice_solution")

    def run_kagome_multi_thimble_solution(self, *_args: object, **_kwargs: object) -> None:
        require_rust_functional("SymbolicDialogueRunner.run_kagome_multi_thimble_solution")


def main() -> None:
    run_symbolic_dialogue()


if __name__ == "__main__":
    main()
