"""Static relocation custody on small real Git histories, not a native parity test."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess

import pytest

from pfp.infrastructure import migration_fitness as gate


def git(root, *args):
    return (
        subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
    )


@pytest.fixture(scope="module")
def moved_history(tmp_path_factory):
    root = tmp_path_factory.mktemp("move_history") / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "core.autocrlf", "false")
    source = "education/pilots/example/old.py"
    destination = "pfp/infrastructure/current.py"
    original = root / source
    original.parent.mkdir(parents=True)
    original.write_bytes(b"VALUE = 1\n")
    (root / "pyproject.toml").write_text(
        '[tool.setuptools.packages.find]\ninclude = ["pfp*", '
        '"adversary*", "education.pilots.example*"]\n'
        'exclude = ["*.tests*"]\nnamespaces = true\n',
        encoding="utf-8",
    )
    git(root, "add", ".")
    git(root, "commit", "-qm", "Original task owner")
    original_revision = git(root, "rev-parse", "HEAD")
    target = root / destination
    target.parent.mkdir(parents=True)
    target.write_bytes(original.read_bytes())
    original.unlink()
    shutil.rmtree(root / "education")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "Canonical owner introduction")
    destination_revision = git(root, "rev-parse", "HEAD")
    row = dict(
        source=source,
        destination=destination,
        owner="PFP",
        original_revision=original_revision,
        destination_revision=destination_revision,
        original_source_sha256=hashlib.sha256(b"VALUE = 1\n").hexdigest(),
        destination_sha256=hashlib.sha256(b"VALUE = 1\n").hexdigest(),
    )
    manifest = root / gate.DEFAULT_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": gate.MANIFEST_SCHEMA, "current_python_source_dispositions": [row]}
    return root, manifest, data, row


@pytest.fixture
def moved_repo(tmp_path, moved_history):
    original, manifest, data, row = moved_history
    root = tmp_path / "repo"
    shutil.copytree(original, root)
    copied = copy.deepcopy(data)
    return (
        root,
        root / manifest.relative_to(original),
        copied,
        copied["current_python_source_dispositions"][0],
    )


def check(case):
    root, manifest, data, _ = case
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return gate.check_current_python_ownership(root, manifest)


def codes(case):
    return {finding.code for finding in check(case)}


def add_caller(case, text, path="education/pilots/example/caller.py"):
    root = case[0]
    caller = root / path
    caller.parent.mkdir(parents=True, exist_ok=True)
    caller.write_text(text, encoding="utf-8")
    git(root, "add", path)


def test_real_move_provenance_accepts_current_canonical_owner(moved_repo):
    assert check(moved_repo) == ()


def test_later_current_edit_does_not_reseal_the_historical_move(moved_repo):
    root, _, _, row = moved_repo
    (root / row["destination"]).write_bytes(b"VALUE = 2\n")
    assert check(moved_repo) == ()


def test_copy_cannot_be_presented_as_an_original_owner_retirement(moved_repo):
    root, _, _, row = moved_repo
    (root / row["source"]).parent.mkdir(parents=True, exist_ok=True)
    (root / row["source"]).write_bytes(b"VALUE = 1\n")
    git(root, "add", row["source"])
    git(root, "commit", "-qm", "Copy without retirement")
    row["destination_revision"] = git(root, "rev-parse", "HEAD")
    (root / row["source"]).unlink()
    git(root, "rm", "--cached", row["source"])
    assert "PROVENANCE_MOVE_INVALID" in codes(moved_repo)


@pytest.mark.parametrize("field", ["original_source_sha256", "destination_sha256"])
def test_forged_historical_digest_refuses(moved_repo, field):
    moved_repo[3][field] = "0" * 64
    assert "PROVENANCE_DIGEST_MISMATCH" in codes(moved_repo)


@pytest.mark.parametrize("field", ["original_revision", "destination_revision"])
def test_missing_git_history_refuses(moved_repo, field):
    moved_repo[3][field] = "f" * 40
    assert "PROVENANCE_HISTORY_UNAVAILABLE" in codes(moved_repo)


def test_reversed_revision_ancestry_refuses(moved_repo):
    row = moved_repo[3]
    row["original_revision"], row["destination_revision"] = (
        row["destination_revision"],
        row["original_revision"],
    )
    assert "PROVENANCE_ANCESTRY_INVALID" in codes(moved_repo)


def test_introduction_outside_current_history_refuses(moved_repo):
    root, _, _, row = moved_repo
    row["destination_revision"] = git(
        root,
        "commit-tree",
        git(root, "rev-parse", "HEAD^{tree}"),
        "-p",
        row["destination_revision"],
        "-m",
        "Unmerged future",
    )
    assert "PROVENANCE_ANCESTRY_INVALID" in codes(moved_repo)


@pytest.mark.parametrize("rows", [None, []])
def test_missing_or_empty_register_is_not_completion(moved_repo, rows):
    if rows is None:
        del moved_repo[2]["current_python_source_dispositions"]
    else:
        moved_repo[2]["current_python_source_dispositions"] = rows
    assert "CURRENT_DISPOSITIONS_UNAVAILABLE" in codes(moved_repo)


def test_duplicate_and_case_disguised_destination_refuse(moved_repo):
    row = copy.deepcopy(moved_repo[3])
    row["source"] = "education/pilots/example/other.py"
    row["destination"] = row["destination"].replace("current.py", "Current.py")
    moved_repo[2]["current_python_source_dispositions"].append(row)
    assert "DUPLICATE_DESTINATION" in codes(moved_repo)


def test_duplicate_source_refuses(moved_repo):
    moved_repo[2]["current_python_source_dispositions"].append(copy.deepcopy(moved_repo[3]))
    assert "DUPLICATE_SOURCE" in codes(moved_repo)


@pytest.mark.parametrize("owner", [None, "Adversary"])
def test_explicit_owner_must_match_canonical_destination(moved_repo, owner):
    moved_repo[3]["owner"] = owner
    assert "CURRENT_OWNER_INVALID" in codes(moved_repo)


def test_old_active_module_cannot_return(moved_repo):
    root, _, _, row = moved_repo
    (root / row["source"]).parent.mkdir(parents=True, exist_ok=True)
    (root / row["source"]).write_bytes(b"from pfp.infrastructure.current import *\n")
    assert "RETIRED_SOURCE_PRESENT" in codes(moved_repo)


@pytest.mark.parametrize("path", [
    "education/pfp/new.py", "education/pilots/new.py",
])
def test_retired_application_package_cannot_return_outside_new_discovery(moved_repo, path):
    add_caller(moved_repo, "VALUE = 1\n", path)
    assert "RETIRED_SOURCE_PRESENT" in codes(moved_repo)


def test_current_destination_must_remain_tracked(moved_repo):
    git(moved_repo[0], "rm", "--cached", moved_repo[3]["destination"])
    assert "CURRENT_DESTINATION_UNTRACKED" in codes(moved_repo)


def test_current_destination_must_remain_package_eligible(moved_repo):
    project = moved_repo[0] / "pyproject.toml"
    project.write_text('[tool.setuptools.packages.find]\ninclude = ["adversary*"]\n')
    assert "CURRENT_DESTINATION_UNPACKAGED" in codes(moved_repo)


def test_shipped_python_package_data_cannot_hide_retired_imports(moved_repo):
    path = "pfp/tests/pilots/example/runner.py"
    add_caller(moved_repo, "import symbol_game\n", path)
    project = moved_repo[0] / "pyproject.toml"
    project.write_text(project.read_text() +
        '\n[tool.setuptools.package-data]\n"pfp" = ["tests/pilots/*/*.py"]\n')
    assert "RETIRED_IMPORT" in codes(moved_repo)
    project.write_text(project.read_text() +
        '\n[tool.setuptools.exclude-package-data]\n"pfp" = ["tests/pilots/*/*.py"]\n')
    assert check(moved_repo) == ()


def test_historical_snapshot_cannot_disguise_a_current_destination(moved_repo):
    root, _, _, row = moved_repo
    target = "pfp/source_snapshot/current.py"
    (root / target).parent.mkdir(parents=True)
    (root / row["destination"]).replace(root / target)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "Snapshot masquerading as current owner")
    row["destination"] = target
    row["destination_revision"] = git(root, "rev-parse", "HEAD")
    assert "CURRENT_OWNER_INVALID" in codes(moved_repo)


@pytest.mark.parametrize(
    "text",
    [
        "import education.pilots.example.old\n",
        "from education.pilots.example.old import VALUE\n",
        "from education.pilots.example import old\n",
        "from . import old\n",
        "from .old import VALUE\n",
        "from ..example import old\n",
        "import importlib as loader\nloader.import_module('education.pilots.example.old')\n",
        "from importlib import import_module as load\nload('.old', 'education.pilots.example')\n",
        "from importlib import import_module as load\nload(name='education.pilots.example.old')\n",
        "from importlib import import_module\nloader = import_module\nloader('education.pilots.example.old')\n",
        "__import__('education.pilots.example.old')\n",
        "from education import pfp\n",
        "from education import pilots\n",
        "import education.pilots\n",
        "import symbol_game\n",
    ],
)
def test_active_retired_import_spellings_refuse(moved_repo, text):
    add_caller(moved_repo, text)
    assert "RETIRED_IMPORT" in codes(moved_repo)


def test_native_prefixes_comments_and_frozen_driver_strings_are_not_retired_imports(moved_repo):
    add_caller(
        moved_repo,
        "import symbol_game_runtime\n"
        "import symbol_game_host\n"
        "# import symbol_game\n"
        "FROZEN_DRIVER = 'from education.pilots.example import old'\n",
        path="pfp/infrastructure/caller.py",
    )
    assert check(moved_repo) == ()


def test_undistributed_host_scripts_and_snapshots_are_outside_declared_static_scope(moved_repo):
    text = "import education.pilots.example.old\n"
    add_caller(moved_repo, text, "scripts/old_host.py")
    add_caller(moved_repo, text, "pfp/source_snapshot/original.py")
    add_caller(moved_repo, text, "pfp/receipts/r1/baseline_bytes/runtime.py")
    add_caller(moved_repo, text, "pfp/infrastructure/tower_evidence/level_engine/v1/tools/bind.py")
    assert check(moved_repo) == ()


def test_current_cli_has_separate_scope_without_changing_the_default(moved_repo, capsys):
    root, manifest, _, _ = moved_repo
    assert check(moved_repo) == ()
    assert (
        gate.main(["--current-python", "--repo-root", str(root), "--manifest", str(manifest)]) == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["scope"] == "static Python ownership and immutable migration provenance only"
    assert result["status"] == "PASS"
    assert "dynamic" in " ".join(result["limitations"])
    assert gate.main(["--repo-root", str(root)]) == 1
    old = json.loads(capsys.readouterr().out)
    assert old["scope"] == "inventory and byte custody only"
    assert old["findings"][0]["code"] == "MAP_UNAVAILABLE"


@pytest.mark.parametrize(
    "later", ["loader = None", "import math as loader", "from math import sin as loader"]
)
def test_later_alias_rebinding_cannot_hide_an_earlier_literal_import(later):
    imports = gate._static_imports(
        "import importlib as loader\n"
        "loader.import_module('symbol_game')\n" + later + "\n",
        "pfp/infrastructure/caller.py",
    )
    assert "symbol_game" in imports
