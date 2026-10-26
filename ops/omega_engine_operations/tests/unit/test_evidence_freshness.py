"""The freshness gate, and the shipped evidence it judges.

Built in response to seed defect 10 of the adversarial campaign
(`omega_engine_pfp/documentation/atlas/13_adversarial_attack_and_evidence_plan.md`),
which observed that the shipped mutation receipt names a head that is not the
current one and concluded its rows "cannot establish present mutation coverage".

The premise is true and the conclusion does not follow, which this file settles
in both directions: the gate is tested on synthetic cases where the answer is
known, and then run against the real artifact.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from omega_engine_operations.use_cases.verification.evidence_freshness import (
    check_evidence,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def _commit(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=root, check=True)
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _evidence(root: Path, head: str, targets: list[str]) -> Path:
    path = root / "evidence.json"
    path.write_bytes(
        json.dumps(
            {
                "schema": "omega.mutation_evidence.v1",
                "head_sha": head,
                "results": [{"mutant_id": f"M{i}", "target": t}
                            for i, t in enumerate(targets)],
            },
            indent=2,
        ).encode("utf-8")
    )
    return path


class TestWhatStaleActuallyMeans:
    """Not `head_sha != HEAD`.

    Evidence is generated at one commit and committed in the next, so a
    mismatch is the normal case. Gating on it would cry wolf on every honest
    run and be switched off within a week.
    """

    def test_commits_may_pass_without_making_evidence_stale(
        self, tmp_path: Path
    ) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        (root / "unrelated.py").write_bytes(b"OTHER = 1\n")
        head = _commit(root, "base")

        evidence = _evidence(root, head, ["described.py"])
        # Move something the evidence does NOT describe, several times.
        for index in range(3):
            (root / "unrelated.py").write_bytes(f"OTHER = {index}\n".encode())
            _commit(root, f"unrelated {index}")

        verdict = check_evidence(evidence, root)
        assert verdict.status == "CURRENT", verdict.detail
        assert verdict.moved == ()

    def test_one_described_file_moving_is_enough(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        evidence = _evidence(root, head, ["described.py"])

        (root / "described.py").write_bytes(b"VALUE = 2\n")
        _commit(root, "move the described file")

        verdict = check_evidence(evidence, root)
        assert verdict.status == "STALE"
        assert verdict.moved == ("described.py",)


class TestItFailsClosed:
    def test_an_unknown_head_is_unplaceable_not_skipped(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        _commit(root, "base")
        evidence = _evidence(root, "0" * 40, ["described.py"])
        verdict = check_evidence(evidence, root)
        assert verdict.status == "UNPLACEABLE"
        assert not verdict.is_current

    @pytest.mark.parametrize("symbolic", ["HEAD", "main", "HEAD~0"])
    def test_symbolic_head_is_never_accepted_as_fresh(
        self, tmp_path: Path, symbolic: str
    ) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        _commit(root, "base")
        evidence = _evidence(root, symbolic, ["described.py"])
        verdict = check_evidence(evidence, root)
        assert verdict.status == "UNPLACEABLE"
        assert "exact full lowercase Git object ID" in verdict.detail

    def test_abbreviated_or_uppercase_head_is_never_accepted(
        self, tmp_path: Path
    ) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        for malformed in (head[:12], head.upper()):
            evidence = _evidence(root, malformed, ["described.py"])
            verdict = check_evidence(evidence, root)
            assert verdict.status == "UNPLACEABLE"

    def test_evidence_without_a_head_cannot_be_judged_current(
        self, tmp_path: Path
    ) -> None:
        root = _repo(tmp_path)
        (root / "described.py").write_bytes(b"VALUE = 1\n")
        _commit(root, "base")
        path = root / "evidence.json"
        path.write_bytes(json.dumps({"results": [{"target": "described.py"}]}).encode())
        assert check_evidence(path, root).status == "UNPLACEABLE"

    def test_evidence_describing_nothing_is_not_a_pass(self, tmp_path: Path) -> None:
        # A gate over an empty set reports green forever.
        root = _repo(tmp_path)
        (root / "x.py").write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        path = _evidence(root, head, [])
        verdict = check_evidence(path, root)
        assert verdict.status == "UNPLACEABLE"
        assert "no results" in verdict.detail

    def test_a_target_missing_at_the_recorded_head_is_unplaceable(
        self, tmp_path: Path
    ) -> None:
        root = _repo(tmp_path)
        (root / "present.py").write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        evidence = _evidence(root, head, ["missing.py"])

        verdict = check_evidence(evidence, root)

        assert verdict.status == "UNPLACEABLE"
        assert verdict.targets == 1
        assert verdict.detail == (
            "target is not a blob at the recorded commit: missing.py"
        )

    @pytest.mark.parametrize(
        "target",
        [
            ":(exclude)*",
            "../outside.py",
            "/absolute.py",
            "C:/absolute.py",
            "dir\\windows.py",
            "dir//unnormalized.py",
            "dir/./unnormalized.py",
            "line\nbreak.py",
        ],
    )
    def test_nonliteral_or_escaping_targets_are_unplaceable(
        self, tmp_path: Path, target: str
    ) -> None:
        root = _repo(tmp_path)
        (root / "present.py").write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        evidence = _evidence(root, head, [target])

        verdict = check_evidence(evidence, root)

        assert verdict.status == "UNPLACEABLE"
        assert "invalid target at results[0]" in verdict.detail

    def test_a_deleted_target_is_stale_not_unplaceable(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        target = root / "described.py"
        target.write_bytes(b"VALUE = 1\n")
        head = _commit(root, "base")
        evidence = _evidence(root, head, ["described.py"])
        target.unlink()
        _commit(root, "delete described target")

        verdict = check_evidence(evidence, root)

        assert verdict.status == "STALE"
        assert verdict.moved == ("described.py",)


class TestTheShippedArtifact:
    """A named historical receipt can still be checked against current bytes."""

    def test_the_named_historical_mutation_receipt_is_never_silently_trusted(self) -> None:
        """Missing source history produces an explicit refusal, never a pass."""
        evidence = (
            REPO_ROOT
            / "omega_engine_operations"
            / "receipts"
            / "historical_evidence_20261011"
            / "symbol_game_mutation_20260903.json"
        )
        verdict = check_evidence(evidence, REPO_ROOT)
        available = subprocess.run(
            ["git", "cat-file", "-e", f"{verdict.head_sha}^{{commit}}"],
            cwd=REPO_ROOT,
            check=False,
        ).returncode == 0
        assert verdict.status == ("CURRENT" if available else "UNPLACEABLE"), (
            f"the named historical receipt is {verdict.status}: {verdict.detail}"
        )


class TestDefaultScope:
    def test_no_selected_receipt_scope_enforces_the_retired_root(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--root", str(tmp_path)]) == 0
        assert "repository evidence directory is retired" in capsys.readouterr().out

    def test_retired_repository_evidence_root_is_a_failure(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        retired = tmp_path / "omega_engine_operations" / "evidence"
        retired.mkdir(parents=True)

        assert main(["--root", str(tmp_path)]) == 1
        assert "retired repository evidence directory is present" in capsys.readouterr().err
