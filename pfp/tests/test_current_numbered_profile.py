"""Current canonical resources render; published profiles remain immutable."""

from pathlib import Path

import pytest
import yaml

from omega_engine_pfp.infrastructure import numbered_prompts as prompts
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import digest
from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import read_frozen_prompt_source
from omega_engine_woland.tests.pilots.relational_spacetime import trial_prompts


def test_current_renderer_has_one_canonical_owner_and_real_consumers():
    from omega_engine_woland.tests.pilots.relational_spacetime import compact_checks, compact_trials

    assert prompts.__name__ == "omega_engine_pfp.infrastructure.numbered_prompts"
    assert not (
        prompts.ROOT / "omega_engine_education/pilots/relational_spacetime/compact_prompts.py"
    ).exists()
    assert compact_trials.build_prompt is prompts.build_prompt
    assert compact_checks.response_schema is prompts.response_schema
    prompt = compact_trials.render("pilot_0000199", 1, {})
    assert prompt["construction_path"] == "omega_engine_pfp/infrastructure/numbered_prompts.py"


@pytest.mark.parametrize("pilot", ["pilot_0000199", "pilot_0000201"])
@pytest.mark.parametrize("stage", [1, 2, 3])
def test_current_profile_renders_current_source_without_historical_substitution(pilot, stage):
    prompt = prompts.build_prompt(pilot, stage)
    assert prompts.VERSION == "1.0.4"
    assert prompt["recipe"] == "PFP-R0001-v1.0.4"
    assert prompt["provider_dispatches"] == 0
    assert prompt["analytical_status"] == "UNVERIFIED"
    registry = yaml.safe_load((prompts.ROOT / prompt["registry_path"]).read_bytes())
    assert registry["file_sha256"][trial_prompts.SOURCE_PATH] == digest(
        (prompts.ROOT / trial_prompts.SOURCE_PATH).read_bytes()
    )
    if pilot == "pilot_0000201":
        wire = yaml.safe_load(prompt["user_prompt"])
        assert digest(wire["source_context"]["section_5"].encode()) == trial_prompts.SECTION_5_SHA256


@pytest.mark.parametrize("version,expected", [
    ("1.0.0", "34df63f05c168570e7942dc7cd4c4ddd4911723f35996dc008390bdc4e504d68"),
    ("1.0.1", "e5ffcdd0cf7082b20a63b496f32d47f983abaa3f438375fa2aebe10675924761"),
    ("1.0.2", "e2002b7ed8fa521f6912e0868112bd1191d955a80791e01b9d5fde274ab00e32"),
    ("1.0.3", "c521e936ad58caf1314cefcadd5a38922b78446b54150d6ade348468e1055892"),
])
def test_published_registry_bytes_are_preserved(version, expected):
    path = Path(prompts.ROOT / prompts.REGISTRY_PATH).with_name(
        f"PFP-prompt-role-registry-v{version}.yaml"
    )
    assert digest(path.read_bytes()) == expected
    registry = yaml.safe_load(path.read_bytes())
    for source, recorded in registry["file_sha256"].items():
        if Path(source).name not in {
            f"{name}-v{version}.yaml"
            for name in ("PFP-T0001", "PFP-T0002", "PFP-T0003", "PFP-R0001")
        }:
            continue
        raw = read_frozen_prompt_source(source) if version == "1.0.0" else (
            prompts.ROOT / source
        ).read_bytes()
        assert digest(raw) == recorded


def test_new_profile_does_not_repin_the_old_paper():
    current = prompts._registry()
    old_path = Path(prompts.ROOT / prompts.REGISTRY_PATH).with_name(
        "PFP-prompt-role-registry-v1.0.2.yaml"
    )
    old = yaml.safe_load(old_path.read_bytes())
    assert old["file_sha256"][trial_prompts.SOURCE_PATH] == (
        "0adce79a181671cc80eed9dc45076e232faa2b5ede9a5989a76a97a79075fbcc"
    )
    assert current["file_sha256"][trial_prompts.SOURCE_PATH] != old["file_sha256"][
        trial_prompts.SOURCE_PATH
    ]
    assert any(entry.get("sha256") == digest(old_path.read_bytes()) for entry in current["history"])


def test_changed_paper_is_refused_before_rendering(monkeypatch):
    original = Path.read_bytes
    source = prompts.ROOT / trial_prompts.SOURCE_PATH

    def changed(path):
        return b"Changed paper" if path == source else original(path)

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="VERSIONED_PROMPT_INPUT_CHANGED"):
        prompts.build_prompt("pilot_0000201", 1)


def test_relocation_profile_changes_source_custody_without_changing_role_contracts():
    base = Path(prompts.ROOT / prompts.REGISTRY_PATH).parent
    current = prompts._registry()
    assert any(entry.get("sha256") == digest(
        (base / "PFP-prompt-role-registry-v1.0.3.yaml").read_bytes()
    ) for entry in current["history"])
    for identity in ("PFP-T0001", "PFP-T0002", "PFP-T0003", "PFP-R0001"):
        old = yaml.safe_load((base / f"{identity}-v1.0.3.yaml").read_bytes())
        new = yaml.safe_load((base / f"{identity}-v1.0.4.yaml").read_bytes())
        assert old.pop("version") == "1.0.3"
        assert new.pop("version") == "1.0.4"
        if identity == "PFP-R0001":
            for stage in new["stages"]:
                stage["template"] = stage["template"].replace("-v1.0.4", "-v1.0.3")
        assert old == new
    for name in ("tasks.py", "trial_prompts.py"):
        path = "omega_engine_woland/tests/pilots/relational_spacetime/" + name
        assert current["file_sha256"][path] == digest((prompts.ROOT / path).read_bytes())
    assert not any(path.startswith("omega_engine_education/pilots/") for path in current["file_sha256"])
