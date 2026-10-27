"""`operad_structure_v1` must not print SUCCESS over a refused composition.

`.agents/operad/validate_operad.py` is a live local-CI gate
(`operations/use_cases/cicd/local_ci.py:67`). It registers every
entry in `composition_matrix.json` and, when the operad refuses one, printed
the refusal and carried on -- reaching `[SUCCESS] Structural registry
validation PASS` and exit 0.

That is the only error path in the validator that behaved this way. The
algebraic, two-layer-grading, WAS-registry and meta-operad checks all
`sys.exit(1)`. A refused composition is not registered, so every later check
runs against a structure missing that arrow and finds nothing wrong with it:
the gate reported a pass over a registry it had failed to build.

These tests drive the real script as a subprocess against a copied tree, so
they exercise the shipped gate rather than a reimplementation of it.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
OPERAD_DIR = REPO_ROOT / "operads" / "skill_operad"
VALIDATOR = OPERAD_DIR / "validate_operad.py"
HOSTS = (".agents", ".claude", ".codex", ".grok")


def _run(operad_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(operad_dir / "validate_operad.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=operad_dir,
    )


@pytest.fixture
def operad_copy(tmp_path: Path) -> Path:
    """A working copy of the skill_operad tree inside a repo skeleton.

    It reads `skills` and `registry` from `.agents` relative to the discovered repo root,
    so the copy has to include those or the gate fails for the wrong reason.
    """
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    shutil.copytree(REPO_ROOT / ".agents" / "skills", repo / ".agents" / "skills")
    shutil.copytree(REPO_ROOT / ".agents" / "registry", repo / ".agents" / "registry")
    dest = repo / "operads" / "skill_operad"
    shutil.copytree(OPERAD_DIR, dest)
    return dest


def test_the_validator_passes_on_the_real_registry() -> None:
    """Anti-vacuity. If the gate failed for an unrelated reason, the negative
    test below would pass for that reason instead of the one it names."""
    result = _run(OPERAD_DIR)
    assert result.returncode == 0, result.stdout[-3000:]
    assert "[SUCCESS]" in result.stdout


def test_a_refused_composition_fails_the_gate(operad_copy: Path) -> None:
    """The headline.

    Point one composition at an operation that does not exist. The operad
    refuses to register it; the gate must not report a pass.

    Mutation: drop the `sys.exit(1)` after the registration loop and this goes
    green again with `[SUCCESS]` in stdout.
    """
    matrix_path = (
        operad_copy / "json" / "composition_matrix.json"
        if (operad_copy / "json" / "composition_matrix.json").exists()
        else operad_copy / "composition_matrix.json"
    )
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["compositions"], "no compositions to corrupt; fixture is stale"

    matrix["compositions"][0]["inner"] = "operation_that_does_not_exist"
    matrix_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")

    result = _run(operad_copy)

    assert "[ERROR] Composition registration failed" in result.stdout
    assert "[SUCCESS]" not in result.stdout, (
        "the gate reported a pass over a composition the operad refused"
    )
    assert result.returncode == 1


def test_an_unmodified_copy_still_passes(operad_copy: Path) -> None:
    """Negative control for the fixture.

    Without this, a copy that was broken by the copying itself would make the
    test above pass for the wrong reason.
    """
    result = _run(operad_copy)
    assert result.returncode == 0, result.stdout[-3000:]
    assert "[SUCCESS]" in result.stdout


def test_every_error_path_in_the_validator_exits(operad_copy: Path) -> None:
    """The rule the composition loop was the sole exception to.

    Read from the source rather than asserted in prose: each error list the
    validator builds is followed by an exit. Mutation: delete any one of these
    guards and this names it.
    """
    source = VALIDATOR.read_text(encoding="utf-8")
    for guard in (
        "if composition_errs or grading_errs:",
        "if errs:",
        "if registry_errs:",
        "if meta_errs:",
        "if slice_errors > 0:",
    ):
        assert guard in source, f"{guard} is gone; an error path may no longer terminate"
    assert source.count("sys.exit(1)") >= 5


def test_the_four_hosts_do_not_carry_stale_operad() -> None:
    """Operad was relocated to operads/skill_operad.
    None of the four hosts should carry a stale operad directory."""
    stale = [host for host in HOSTS if (REPO_ROOT / host / "operad").exists()]
    assert stale == [], f"stale operad tree found on hosts: {stale}"
