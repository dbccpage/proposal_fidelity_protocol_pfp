"""The estate may not own a check it does not account for.

This is the assertion that answers the actual defect. Not "we lacked auditors" --
there are twenty-odd, and one of them had already found seed defect 5 of the
adversarial campaign and written the finding into its own skill file. The defect
is that nothing required anyone to run them, and nothing noticed that nobody
had.

A register with a completeness test is what makes that state unreachable: an
auditor added to the estate and not accounted for is a failing test on the day
it lands, not a discovery an outsider makes two sprints later.

Three ways this stays honest, each with a test below:

*It cannot go quiet.* Discovery reading zero files raises rather than returning
an empty set that subtracts to nothing.

*It cannot be padded.* A registered auditor whose module is gone is a failure,
so the register cannot be kept "complete" by naming things that do not exist.

*A quarantine cannot become permanent or catch-all.* `QUARANTINED` entries still
run, and hold only on the declared exit code and stable diagnostic. Passing or
failing for a different reason is drift.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from operations.use_cases.verification.stopping_point import (
    ADVISORY,
    AUDITORS,
    BY_MODULE,
    CI_WORKFLOWS,
    QUARANTINED,
    RUNNING_STATUSES,
    UNWIRED,
    WIRED,
    RegisterDrift,
    Auditor,
    battery_workflows,
    ci_invocations,
    ci_reachability,
    discover,
    missing_from_disk,
    reconcile,
    run_one,
    unregistered,
)


class TestTheRegisterAccountsForEveryAuditor:
    def test_no_auditor_on_disk_is_unregistered(self) -> None:
        """The one that matters.

        An auditor nobody wired is an auditor nobody runs, which is how this
        estate came to own a tool that had already measured a defect an
        external campaign then reported as a finding.
        """
        missing = unregistered()
        assert not missing, (
            "these auditors exist on disk and the stopping-point register does "
            f"not name them: {missing}. Add each with a status and a reason -- "
            "UNWIRED with an honest reason is acceptable; silence is not."
        )

    def test_no_registered_auditor_is_missing_from_disk(self) -> None:
        gone = missing_from_disk()
        assert not gone, (
            f"registered auditors no longer exist: {gone}. A register padded "
            "with dead entries reports complete while covering less."
        )

    def test_discovery_refuses_to_report_an_empty_estate(self) -> None:
        # Without this, a broken marker list or a moved root would empty the
        # discovered set, the subtraction above would yield nothing, and the
        # completeness test would pass by checking nothing.
        import operations.use_cases.verification.stopping_point as sp

        original = sp.AUDITOR_MARKERS
        try:
            sp.AUDITOR_MARKERS = ("zzz-matches-nothing",)
            with pytest.raises(RegisterDrift, match="read nothing"):
                discover()
        finally:
            sp.AUDITOR_MARKERS = original

    def test_a_missing_root_raises_rather_than_narrowing_the_sweep(self) -> None:
        import operations.use_cases.verification.stopping_point as sp

        original = sp.AUDITOR_ROOTS
        try:
            sp.AUDITOR_ROOTS = ("no_such_directory_anywhere",)
            with pytest.raises(RegisterDrift, match="does not exist"):
                discover()
        finally:
            sp.AUDITOR_ROOTS = original


class TestEveryEntryCarriesItsJustification:
    @pytest.mark.parametrize("auditor", AUDITORS, ids=lambda a: a.module.split(".")[-1])
    def test_the_status_is_one_of_the_four(self, auditor) -> None:
        # ADVISORY joined on 2026-09-04. The estate was already using the
        # concept -- CI runs uncalled_module_audit under continue-on-error --
        # and a vocabulary that cannot say what is already happening forces a
        # false entry either way.
        assert auditor.status in {WIRED, ADVISORY, QUARANTINED, UNWIRED}

    @pytest.mark.parametrize("auditor", AUDITORS, ids=lambda a: a.module.split(".")[-1])
    def test_it_says_what_it_guards(self, auditor) -> None:
        assert auditor.guards.strip(), f"{auditor.module} does not say what it guards"

    @pytest.mark.parametrize("auditor", AUDITORS, ids=lambda a: a.module.split(".")[-1])
    def test_not_running_it_requires_a_reason(self, auditor) -> None:
        """An exemption without a reason is an exemption nobody can review.

        WIRED needs no reason: it runs and must pass. Everything else is a
        decision not to enforce something, and those are the decisions most
        worth writing down.
        """
        if auditor.status == WIRED:
            return
        assert len(auditor.reason.strip()) > 30, (
            f"{auditor.module} is {auditor.status} with no substantive reason. "
            "Say why it is not enforced, or enforce it."
        )

    @pytest.mark.parametrize(
        "auditor", [a for a in AUDITORS if a.status == QUARANTINED]
    )
    def test_each_quarantine_names_one_exit_and_one_diagnostic(self, auditor) -> None:
        assert isinstance(auditor.expected_exit_code, int)
        assert auditor.expected_exit_code != 0
        assert auditor.expected_output_pattern.strip()

    def test_the_register_is_not_all_exemption(self) -> None:
        # A register of twenty-four UNWIRED entries is a list, not a battery.
        # A floor to raise, and raising it is the work. Raised 3 -> 8 on
        # 2026-09-04: host_root_parity was wired, and reconcile found three
        # more rows CI had been running all along. A floor that lags the real
        # count stops being a ratchet, because the set can decay back to it
        # without anything going red.
        enforced = [a for a in AUDITORS if a.status in RUNNING_STATUSES]
        assert len(enforced) >= 8, (
            f"only {len(enforced)} auditors are actually run. The register has "
            "decayed into an inventory."
        )


class TestTheKnownRedIsNamed:
    """The quarantine ledger, asserted rather than remembered."""

    def test_the_epic_falsifier_auditor_is_quarantined_and_says_why(self) -> None:
        entry = BY_MODULE[
            "product_planning_office.domain.epic_criteria_audit"
        ]
        assert entry.status == QUARANTINED
        # The reason must name the campaign's seed, so the connection between
        # our known-red and their finding cannot be lost.
        assert "seed defect 5" in entry.reason

    def test_the_mirror_surface_auditor_is_wired_and_runs_as_a_gate(self) -> None:
        """Was the highest-priority UNWIRED entry; wired 2026-09-04.

        The status alone is not the claim worth pinning -- flipping a string to
        `WIRED` while the command stays a reporter would register a permanent
        PASS, which is worse than the honest UNWIRED it replaced. So the argv is
        asserted too: this entry only means anything while it runs `--check`.
        """
        entry = BY_MODULE[
            "operations.use_cases.packaging.host_root_parity"
        ]
        assert entry.status == WIRED
        assert entry.argv == ("--check",), (
            "without --check the module prints a census and exits 0 whatever it "
            "finds, so a WIRED entry would be a guaranteed PASS"
        )

    def test_the_repaired_epic_manifest_auditor_is_wired(self) -> None:
        entry = BY_MODULE[
            "product_planning_office.use_cases.epic_manifest_audit"
        ]
        assert entry.status == WIRED

    def test_receipt_freshness_retirement_guard_is_wired(self) -> None:
        entry = BY_MODULE[
            "operations.use_cases.verification.evidence_freshness"
        ]
        assert entry.status == WIRED
        assert "operator explicitly selects" in entry.guards


class TestCampaignCensusExecution:
    MODULE = "operations.use_cases.verification.core_campaign_census"
    EXPECTED_ARGV = (
        "check",
        "--baseline", "a85c7e13ea7411b7d6ecc1af2181e4301df6cd1e",
        "--output",
        "operations/receipts/historical_evidence_20261011/core_campaign/baseline_20260904.jsonl",
    )

    def test_snapshot_checker_is_wired_to_the_independent_baseline(self) -> None:
        entry = BY_MODULE.get(self.MODULE)
        assert entry is not None, "campaign census is not registered"
        assert entry.status == WIRED, "campaign census must execute at every stop"
        assert entry.argv == self.EXPECTED_ARGV
        assert "not current-source review" in entry.guards

    @pytest.mark.parametrize(("exit_code", "verdict"), [(0, "PASS"), (2, "FAIL")])
    def test_battery_invokes_census_and_preserves_its_exit(
        self, monkeypatch, exit_code: int, verdict: str
    ) -> None:
        import operations.use_cases.verification.stopping_point as sp

        calls = []

        def execute(argv, **kwargs):
            if argv[2] == self.MODULE:
                calls.append((argv, kwargs))
                return sp.subprocess.CompletedProcess(
                    argv, exit_code, "CENSUS_RESULT\n", ""
                )
            auditor = BY_MODULE[argv[2]]
            if auditor.status == QUARANTINED:
                return sp.subprocess.CompletedProcess(
                    argv, 1,
                    "15 of 31 epics name a falsifier; 16 name none\n", ""
                )
            return sp.subprocess.CompletedProcess(argv, 0, "OK\n", "")

        monkeypatch.setattr(sp.subprocess, "run", execute)
        results = sp.run_all()
        census = [result for result in results if result.auditor.module == self.MODULE]
        assert len(calls) == len(census) == 1, "registered census was not executed once"
        argv, kwargs = calls[0]
        assert argv == [sp.sys.executable, "-m", self.MODULE, *self.EXPECTED_ARGV]
        assert kwargs["cwd"] == sp.REPO_ROOT
        assert census[0].exit_code == exit_code
        assert census[0].verdict == verdict
        assert sp.main([]) == (0 if exit_code == 0 else 1)


class TestQuarantineFailureIdentity:
    @staticmethod
    def _quarantine() -> Auditor:
        return Auditor(
            module="synthetic.quarantine",
            status=QUARANTINED,
            guards="the declared synthetic defect",
            reason="synthetic quarantine used to prove failure identity",
            expected_exit_code=7,
            expected_output_pattern=r"(?m)^EXPECTED_REFUSAL$",
        )

    def test_declared_exit_and_diagnostic_hold(self, monkeypatch) -> None:
        import operations.use_cases.verification.stopping_point as sp

        completed = sp.subprocess.CompletedProcess(
            args=[], returncode=7, stdout="EXPECTED_REFUSAL\n", stderr=""
        )
        monkeypatch.setattr(sp.subprocess, "run", lambda *args, **kwargs: completed)
        assert run_one(self._quarantine()).verdict == "QUARANTINE_HELD"

    @pytest.mark.parametrize(
        ("returncode", "stdout"),
        [(2, "EXPECTED_REFUSAL\n"), (7, "Traceback: import crashed\n")],
    )
    def test_wrong_exit_or_wrong_diagnostic_is_drift(
        self, monkeypatch, returncode: int, stdout: str
    ) -> None:
        import operations.use_cases.verification.stopping_point as sp

        completed = sp.subprocess.CompletedProcess(
            args=[], returncode=returncode, stdout=stdout, stderr=""
        )
        monkeypatch.setattr(sp.subprocess, "run", lambda *args, **kwargs: completed)
        assert run_one(self._quarantine()).verdict == "QUARANTINE_DRIFT"

    def test_passing_quarantine_escapes(self, monkeypatch) -> None:
        import operations.use_cases.verification.stopping_point as sp

        completed = sp.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="EXPECTED_REFUSAL\n", stderr=""
        )
        monkeypatch.setattr(sp.subprocess, "run", lambda *args, **kwargs: completed)
        assert run_one(self._quarantine()).verdict == "QUARANTINE_ESCAPED"


class TestReconciliationAgainstCi:
    """The register is a map. CI is the territory. These pin them together.

    Added 2026-09-04 after the map was measured wrong in both directions: three
    rows CI had been running on every push to main were recorded here as
    UNWIRED with reasons claiming they were untriaged, and one row was WIRED
    while no workflow ran it. `UNWIRED` had drifted to mean "unmodelled" rather
    than "unprotected", and nothing tested the difference.
    """

    @staticmethod
    def _workflow(tmp_path, body: str, name: str = "symbol-game-pr.yml"):
        """Write one workflow, and stub every other declared one.

        `ci_invocations` refuses when a declared workflow is unreadable, so a
        fixture that writes only the file under test would fail on the refusal
        instead of on the behaviour it means to exercise.
        """
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True, exist_ok=True)
        for relative in CI_WORKFLOWS:
            stub = wf / relative.rsplit("/", 1)[-1]
            if not stub.exists():
                stub.write_text(
                    "name: stub\non:\n  workflow_dispatch: {}\njobs: {}\n",
                    encoding="utf-8",
                    newline="\n",
                )
        (wf / name).write_text(body, encoding="utf-8", newline="\n")
        return tmp_path

    def test_the_tree_reconciles_today(self) -> None:
        """The whole point of the check, asserted against the real workflows."""
        assert reconcile() == []

    def test_a_module_ci_runs_may_not_be_unwired(self, tmp_path) -> None:
        """Negative control for the direction that was wrong three times."""
        target = next(a for a in AUDITORS if a.status == UNWIRED)
        self._workflow(
            tmp_path,
            "name: t\non:\n  push:\n    branches: [main]\n"
            "jobs:\n  gates:\n    steps:\n"
            f"      - name: Runs it\n        run: python -m {target.module}\n",
        )
        findings = reconcile(tmp_path)
        assert any(target.module in f and "UNWIRED" in f for f in findings), findings

    def test_a_continue_on_error_step_may_not_be_wired(self, tmp_path) -> None:
        """WIRED asserts a non-zero exit fails. continue-on-error says otherwise."""
        target = next(a for a in AUDITORS if a.status == WIRED)
        self._workflow(
            tmp_path,
            "name: t\non:\n  push:\n    branches: [main]\n"
            "jobs:\n  gates:\n    steps:\n"
            "      - name: Advisory\n        continue-on-error: true\n"
            f"        run: python -m {target.module}\n",
        )
        findings = reconcile(tmp_path)
        assert any("ADVISORY is the honest status" in f for f in findings), findings

    def test_a_blocking_step_may_not_be_recorded_advisory(self, tmp_path) -> None:
        """The other direction: understating a gate hides a real merge blocker."""
        target = next((a for a in AUDITORS if a.status == ADVISORY), None)
        assert target is not None, "no ADVISORY row to exercise"
        self._workflow(
            tmp_path,
            "name: t\non:\n  push:\n    branches: [main]\n"
            "jobs:\n  gates:\n    steps:\n"
            f"      - name: Blocking\n        run: python -m {target.module}\n",
        )
        findings = reconcile(tmp_path)
        assert any("CI blocks on it" in f for f in findings), findings

    def test_a_paths_filter_is_not_an_invocation(self, tmp_path) -> None:
        """The defect this check must not itself commit.

        A workflow that WATCHES a file it never runs is seed-defect-4's class.
        If reconciliation counted a path trigger as evidence of execution it
        would assert the very thing it exists to refute -- and the Symbol Game
        PR gate really does list auditor modules under its triggers that it
        never invokes.
        """
        target = next(a for a in AUDITORS if a.status == UNWIRED)
        as_path = target.module.replace(".", "/") + ".py"
        self._workflow(
            tmp_path,
            "name: t\non:\n  push:\n    branches: [main]\n"
            f'    paths:\n      - "{as_path}"\n'
            "jobs:\n  gates:\n    steps:\n"
            "      - name: Unrelated\n        run: echo hello\n",
        )
        assert reconcile(tmp_path) == []
        assert target.module not in ci_invocations(tmp_path)

    def test_a_longer_module_name_is_not_credited_to_an_auditor(
        self, tmp_path
    ) -> None:
        """A wrapper or sibling name is not execution of the registered module."""
        target = next(a for a in AUDITORS if a.status == UNWIRED)
        self._workflow(
            tmp_path,
            "name: t\non:\n  push:\n    branches: [main]\n"
            "jobs:\n  gates:\n    steps:\n"
            f"      - name: Different module\n"
            f"        run: python -m {target.module}_wrapper\n",
        )
        assert target.module not in ci_invocations(tmp_path)
        assert reconcile(tmp_path) == []

    def test_a_missing_declared_workflow_refuses(self, tmp_path) -> None:
        """An empty parse must not read as perfect agreement."""
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        with pytest.raises(RegisterDrift, match="declared CI workflow is missing"):
            reconcile(tmp_path)

    def test_the_declared_workflows_exist(self) -> None:
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[3]
        for relative in CI_WORKFLOWS:
            assert (root / relative).is_file(), (
                f"{relative} is gone; update CI_WORKFLOWS"
            )

    def test_reachability_separates_direct_from_via_battery(self) -> None:
        """A row reached only because the battery runs is not independently run."""
        reach = ci_reachability()
        expected = {a.module for a in AUDITORS if a.status in RUNNING_STATUSES}
        assert set(reach) == expected
        assert set(reach.values()) <= {"DIRECT", "VIA_BATTERY", "NONE"}

    def test_an_advisory_finding_does_not_fail_the_battery(self, monkeypatch) -> None:
        """The entire content of the ADVISORY status, and it was wrong first.

        `main` filtered on a hardcoded {PASS, QUARANTINE_HELD}, so the first
        ADVISORY row to report a finding turned the battery red -- exactly the
        blocking behaviour the status exists to avoid, and exactly what CI had
        already decided against with `continue-on-error`. Nothing caught it
        because the check was run through a pipe and `$?` was the pipe's.
        """
        import operations.use_cases.verification.stopping_point as sp

        advisory = next(a for a in AUDITORS if a.status == ADVISORY)
        monkeypatch.setattr(
            sp, "run_all", lambda: [sp.Result(advisory, 1, "ADVISORY_FINDING", "x")]
        )
        monkeypatch.setattr(sp, "unregistered", list)
        monkeypatch.setattr(sp, "missing_from_disk", list)
        assert sp.main([]) == 0

    def test_a_wired_failure_still_fails_the_battery(self, monkeypatch) -> None:
        """The control for the test above: it must not have made everything pass."""
        import operations.use_cases.verification.stopping_point as sp

        wired = next(a for a in AUDITORS if a.status == WIRED)
        monkeypatch.setattr(
            sp, "run_all", lambda: [sp.Result(wired, 1, "FAIL", "x")]
        )
        monkeypatch.setattr(sp, "unregistered", list)
        monkeypatch.setattr(sp, "missing_from_disk", list)
        assert sp.main([]) == 1

    def test_the_battery_runs_unfiltered(self) -> None:
        """The battery's workflow runs nightly with no path filter.

        Until 2026-10-06 it ran in a path-filtered PR gate whose filter listed
        this module itself, so rows reached only via the battery were enforced
        substantially when the battery changed. The gate now runs on a
        schedule. If a path filter comes back, this test fails and the
        reachability claim in `battery_workflows` must be revisited with it.
        """
        running = battery_workflows()
        assert running, "no workflow runs the battery at all"
        assert not any(filtered for _, filtered in running), running

    def test_the_battery_workflow_is_scheduled(self) -> None:
        """Pin the exact trigger claim, not merely the absence of a filter."""
        import pathlib

        import yaml

        root = pathlib.Path(__file__).resolve().parents[3]
        for workflow, _ in battery_workflows():
            document = yaml.safe_load((root / workflow).read_text(encoding="utf-8"))
            triggers = document.get("on", document.get(True)) or {}
            assert "schedule" in triggers, f"{workflow} runs the battery but has no schedule"
