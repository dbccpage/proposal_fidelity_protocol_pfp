"""Historical paths can replay after deletion and leave the checkout clean."""

import hashlib
import json
import subprocess

import pytest

from adversary.tests.pilots.challenge_suite.replay_snapshots import replay


@pytest.mark.parametrize(
    "module",
    [
        "education/pilots/challenge_suite/live.py",
        "pfp/infrastructure/challenge_live.py",
    ],
)
@pytest.mark.parametrize("fails", [False, True])
def test_deleted_captured_paths_are_temporary_even_on_replay_failure(tmp_path, fails, module):
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(checkout), *args], text=True)

    git("init", "-q")
    (checkout / "README.md").write_text("Current tree has no historical package.\n")
    git("add", "--", "README.md")
    git(
        "-c",
        "user.name=Replay test",
        "-c",
        "user.email=replay@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    git("checkout", "--detach", "-q")
    evidence = tmp_path / "evidence"
    run = evidence / "live" / "old_run"
    (run / "stage_1").mkdir(parents=True)
    (run / "summary.json").write_text("{}")
    (run / "stage_1/receipt.json").write_text("{}")
    sources = {
        "education/__init__.py": b"",
        "pfp/__init__.py": b"",
        "pfp/infrastructure/__init__.py": b"",
        "education/pilots/challenge_suite/__init__.py": b"",
        module: (
            b"def replay_live(path):\n    raise ValueError('fixture failure')\n"
            if fails
            else b"def replay_live(path):\n    return 1\n"
        ),
    }
    for name, raw in sources.items():
        target = run / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (run / "config.json").write_text(
        json.dumps(
            {"sources": {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()}}
        )
    )
    result = replay(checkout, evidence, tmp_path / "receipt.json")
    assert result["status"] == ("FAIL" if fails else "PASS")
    assert not (checkout / "education").exists()
    assert git("status", "--porcelain") == ""
