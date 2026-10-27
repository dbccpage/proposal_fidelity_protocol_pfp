"""Frozen prompt relocation preserves identity without restoring an application.

Versioned directories on the active filesystem are retired in favor of clean
unversioned templates (with Git maintaining full historical versions).
"""

import hashlib
import json
from pathlib import Path

import pytest

from pfp.infrastructure.adapters import pfp_frozen_replay as frozen

ROOT = Path(__file__).resolve().parents[2]
OLD = "education/pfp/infrastructure/yaml/prompts/versioned/"
CURRENT = "pfp/infrastructure/yaml/prompts/versioned/"
SOURCES = {
    "PFP-prompt-role-registry-v1.0.0.yaml":
        "34df63f05c168570e7942dc7cd4c4ddd4911723f35996dc008390bdc4e504d68",
    "PFP-R0001-v1.0.0.yaml":
        "b742ae28054e7745ce29820f594b52f217379154778b9b24e79fd70f8ac0babe",
    "PFP-T0001-v1.0.0.yaml":
        "d5da7ada446ade90d33ba3910838bb1f74eaa9a645243c20b39a39d484638195",
    "PFP-T0002-v1.0.0.yaml":
        "783ba0fc4f809a9aa663e181e03912aaf91907fdac3b4d22232788b85201e3e0",
    "PFP-T0003-v1.0.0.yaml":
        "4da19cc6a7430a6d584c95abfa30ac92f756f716f4f73975244a802ea7626ecd",
    "README.md": "9fc9e32004dc0328441da20b6aa52bb2ffa52b4352447f635f65a897c54f7e82",
}


def destination(name):
    return CURRENT + ("historical/v1.0.0/README.md" if name == "README.md" else name)


def test_old_application_root_is_retired():
    assert not (ROOT / "education/pfp").exists()


def test_versioned_directory_is_retired():
    assert not (ROOT / CURRENT).exists()


@pytest.mark.parametrize("name,expected", SOURCES.items())
def test_original_identity_reads_exact_frozen_bytes(name, expected, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = frozen.read_frozen_prompt_source(OLD + name)
    assert hashlib.sha256(raw).hexdigest() == expected
    assert not (tmp_path / "education").exists()
    assert not (ROOT / destination(name)).exists()
    if name != "README.md":
        bundle = ROOT / "adversary/tests/pilots/evidence/pfp_ownership_migration_20261012"
        manifest = json.loads((bundle / "frozen_runtime.json").read_bytes())
        assert manifest["files"][OLD + name] == expected
        assert raw == (bundle / "frozen_sources" / (OLD + name)).read_bytes()
        snapshot = ROOT / "adversary/tests/pilots/evidence/po035_simplified_20261012/source_snapshot"
        assert raw == (snapshot / (OLD + name)).read_bytes()


@pytest.mark.parametrize("name", [
    "../README.md", OLD + "../README.md", OLD + "PFP-T0001-v1.0.2.yaml",
    CURRENT + "PFP-T0001-v1.0.0.yaml", (OLD + "README.md").replace("/", "\\"),
])
def test_original_identity_lookup_is_explicit_not_a_path_rewrite(name):
    with pytest.raises(ValueError, match="UNKNOWN_FROZEN_PROMPT_SOURCE"):
        frozen.read_frozen_prompt_source(name)


def test_unversioned_active_templates_conform_to_slug_and_prefix():
    prompts_root = ROOT / "pfp/infrastructure/yaml/prompts"
    for sub in ("templates", "schemas", "reprs"):
        sub_dir = prompts_root / sub
        assert sub_dir.exists(), f"Missing subdirectory {sub}"
        yaml_files = list(sub_dir.glob("*.yaml"))
        assert len(yaml_files) > 0, f"No yaml files in {sub}"
        for f in yaml_files:
            assert f.name.startswith("template_"), f"{f.name} missing template_ prefix"
            slug = f.stem[len("template_"):]
            assert len(slug) <= 20, f"{f.name} slug exceeds 20 characters: {slug}"


def test_current_profile_does_not_silently_read_an_old_paper(monkeypatch):
    from pfp.infrastructure import numbered_prompts
    from adversary.tests.pilots.relational_spacetime.trial_prompts import SOURCE_PATH

    source = ROOT / SOURCE_PATH
    original = Path.read_bytes

    def changed(path):
        return b"changed paper" if path == source else original(path)

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="VERSIONED_PROMPT_INPUT_CHANGED"):
        numbered_prompts.build_prompt("pilot_0000199", 1)
