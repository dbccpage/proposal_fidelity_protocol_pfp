"""The audit itself, and a ratchet on what it finds.

Two different jobs, kept apart on purpose:

*The audit works.* Synthetic cases where the answer is known, including the
empty-scan case -- because a scanner that reads nothing prints the same words as
a scanner that found nothing wrong.

*The estate does not get worse.* A ratchet on the observed set. It is a ratchet
and not a target: 64 fail-open shapes is not a passing grade, it is a measured
starting point that may not grow while the prioritised subset is worked down.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast

import pytest

from omega_engine_operations.use_cases.verification.fail_closed_audit import (
    AUDITED_ROOTS,
    EXCLUDED_PARTS,
    FAIL_OPEN_SHAPE_CEILING,
    SILENT_SKIP,
    SWALLOWED,
    EmptyScan,
    Finding,
    _Visitor,
    audit,
    render,
)

#: Exact so both growth and an unrecorded repair fail; a loose ceiling silently
#: loses its grip every time the estate improves. Single source of truth is
#: FAIL_OPEN_SHAPE_CEILING imported from the audit module.
KNOWN_SHAPE_COUNT = FAIL_OPEN_SHAPE_CEILING

#: Substrings that identify a module whose job is to detect something. A
#: fail-open shape here is worth more than one anywhere else: it is a hole in
#: the layer that would report the other holes.
GATE_MARKERS = (
    "gate",
    "audit",
    "parity",
    "census",
    "coverage",
    "verify",
    "conformance",
    "baseline",
)

#: Modules that call themselves gates and can pass without checking.
#: This is the prioritised work list, pinned so the list cannot grow unmonitored.
KNOWN_SOFT_GATES = frozenset(
    {
        "omega_engine_governance/contracts/dual_home_import_auditor.py",
        "omega_engine_governance/tests/contexts/cicd_process_flow/test_pr_audit_campaign_store.py",
        "omega_engine_governance/tests/contexts/swarm_control/test_pass4_p3_00_baseline.py",
        "omega_engine_governance/tests/unit/test_contract_estate_conformance.py",
        "omega_engine_operations/domain/cicd/stale_census_audit.py",
        "omega_engine_operations/domain/cicd/workflow_graph_audit.py",
        "omega_engine_operations/tests/cicd/test_verify_merge.py",
        "omega_engine_operations/use_cases/cicd/rust_module_coverage.py",
        "omega_engine_operations/use_cases/packaging/host_root_parity.py",
        "omega_engine_operations/use_cases/verification/verify_repo_utf8_bom.py",
        "omega_engine_woland/infrastructure/research_swarm/source_audit.py",
        "omega_engine_woland/tests/test_legacy_rip_manifest_absence_gate.py",
    }
)


def _findings(source: str) -> list[Finding]:
    visitor = _Visitor("synthetic.py")
    visitor.visit(ast.parse(source))
    return visitor.findings


class TestTheAuditFindsWhatItClaimsTo:
    def test_a_missing_path_that_continues_is_a_silent_skip(self) -> None:
        found = _findings(
            "for p in paths:\n"
            "    if not p.exists():\n"
            "        continue\n"
            "    assert p.is_file()\n"
        )
        assert [f.category for f in found] == [SILENT_SKIP]

    @pytest.mark.parametrize("escape", ["continue", "return", "pass"])
    def test_every_pure_escape_counts(self, escape: str) -> None:
        found = _findings(f"def f(p):\n    if not p.is_file():\n        {escape}\n")
        assert len(found) == 1

    def test_an_import_failure_turned_into_a_skip_is_found(self) -> None:
        found = _findings(
            "try:\n"
            "    import thing\n"
            "except ImportError:\n"
            "    pytest.skip('absent', allow_module_level=True)\n"
        )
        assert any(f.category == SILENT_SKIP for f in found)

    def test_a_swallowed_exception_is_found(self) -> None:
        found = _findings("try:\n    go()\nexcept Exception:\n    pass\n")
        assert [f.category for f in found] == [SWALLOWED]


class TestTheAuditDoesNotCryWolf:
    def test_a_guard_that_actually_asserts_is_not_a_finding(self) -> None:
        # The distinction the whole module turns on: leaving is the defect,
        # not checking existence.
        assert not _findings(
            "for p in paths:\n"
            "    if not p.exists():\n"
            "        raise AssertionError(p)\n"
        )

    def test_a_handler_that_records_is_not_a_finding(self) -> None:
        assert not _findings(
            "try:\n    go()\nexcept Exception as e:\n    log(e)\n"
        )

    def test_an_ordinary_existence_check_with_a_body_is_not_a_finding(self) -> None:
        assert not _findings(
            "if not p.exists():\n    p.mkdir()\n    build(p)\n"
        )


class TestItRefusesToReportCleanAfterReadingNothing:
    """The defect the audit committed against itself on its first run.

    Its exclusion list contained `worktrees`; this repository is checked out
    under `.claude/worktrees/<branch>/`, so every path matched, zero files were
    read, and it printed "no fail-open shapes found".
    """

    def test_an_empty_root_set_raises_rather_than_passing(self) -> None:
        with pytest.raises(EmptyScan):
            audit(())

    def test_a_root_that_does_not_exist_raises(self) -> None:
        with pytest.raises(EmptyScan, match="does not exist"):
            audit(("no_such_package_anywhere",))

    def test_render_says_something_different_from_a_clean_result(self) -> None:
        # "no fail-open shapes found" must be reachable ONLY through a real
        # scan, which the two tests above guarantee.
        assert render([]) == "no fail-open shapes found"


class TestTheEstateRatchet:
    def test_the_number_of_fail_open_shapes_matches_the_recorded_baseline(self) -> None:
        found = audit(AUDITED_ROOTS)
        assert len(found) == KNOWN_SHAPE_COUNT, (
            f"fail-open shapes changed to {len(found)} from the exact pinned "
            f"count {KNOWN_SHAPE_COUNT}. Record each repair or regression and "
            "move the pin in the same change.\n\n" + render(found)
        )

    def test_the_declared_scope_and_exclusions_are_exact(self) -> None:
        assert AUDITED_ROOTS == (
            "omega_engine_governance",
            "omega_engine_operations",
            "omega_engine_woland",
            "omega_engine_pfp",
        )
        assert EXCLUDED_PARTS == frozenset(
            {"__pycache__", "node_modules", ".git", ".venv", "historical_evidence_20261011"}
        )

    def test_no_new_module_starts_calling_itself_a_gate_while_failing_open(
        self,
    ) -> None:
        """The sharp end: detectors that can pass without detecting.

        20 of the 64 shapes sit in modules whose own names say they audit,
        gate, or census something. Those are the ones an attacker wants,
        because they are the layer that would have reported the rest.
        """
        found = audit(AUDITED_ROOTS)
        soft = {
            f.path
            for f in found
            if any(marker in f.path.lower() for marker in GATE_MARKERS)
        }
        new = sorted(soft - KNOWN_SOFT_GATES)
        assert not new, (
            f"these detector modules newly contain a fail-open shape: {new}. "
            "A gate that can pass without checking is worse than no gate, "
            "because it is trusted."
        )

    def test_the_pinned_soft_gates_still_exist(self) -> None:
        # Otherwise the pin above decays into a list of paths nobody maintains,
        # and its subtraction silently stops subtracting anything.
        from omega_engine_operations.use_cases.verification.fail_closed_audit import (
            REPO_ROOT,
        )

        missing = sorted(p for p in KNOWN_SOFT_GATES if not (REPO_ROOT / p).is_file())
        assert not missing, (
            f"pinned soft-gate modules no longer exist: {missing}. Remove them "
            "from KNOWN_SOFT_GATES, or find where they moved."
        )
