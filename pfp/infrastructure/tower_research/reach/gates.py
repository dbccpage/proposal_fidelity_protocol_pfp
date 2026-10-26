"""The reach runner's steps. A checker counts in T(N) only when its registered
``gated_step`` names one of these steps.

AuthorityEffect: None. This list is the written contract; the runner at
``research/mssn_sn_tower/ci/run_reach_gates.py`` executes it locally.
"""

from __future__ import annotations

TESTS = (
    "research/mssn_sn_tower/code/python/tests/test_reach_receipt.py",
    "research/mssn_sn_tower/code/python/tests/test_reach_transport.py",
    "research/mssn_sn_tower/code/python/tests/test_reach_ledger.py",
)
TARGET_TESTS = (
    "research/mssn_sn_tower/code/python/tests/test_target_checkers.py",
    "research/mssn_sn_tower/code/python/tests/test_anti_evidence.py",
)
CLI = "omega_engine_pfp.infrastructure.tower_research.reach.cli"

# (name, argv); "{python}" is replaced by the running interpreter.
STEPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("reach-tests", ("{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *TESTS)),
    ("target-checkers", ("{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *TARGET_TESTS)),
    ("stage-registry", ("{python}", "-m", CLI, "registry-check", "--workspace", "{workspace}")),
    ("reach-ledger", ("{python}", "-m", CLI, "ledger-check", "--workspace", "{workspace}")),
)

GATED_STEPS = frozenset(name for name, _ in STEPS)
