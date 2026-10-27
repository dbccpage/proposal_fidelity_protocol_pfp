from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogRefusal,
    CapabilityCatalogV1,
    decode_capability_catalog,
    encode_capability_catalog,
    seal_capability_catalog,
)
from operads.infrastructure.capability_catalog_compiler import (
    HOST_NAMES,
    CatalogCompileRefusal,
    compile_capability_catalog,
    projection_bytes,
    verify_host_projections,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TRACKED_FIXTURE = (
    ".agents/agents/reviewer.md",
    ".agents/skills/review/SKILL.md",
)


def _fixture(root: Path, *, body_license: bool = False) -> None:
    skill = root / ".agents/skills/review/SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        "---\n"
        "name: review\n"
        'description: "Review code against an exact acceptance contract."\n'
        'operad_source_colours: ["Code"]\n'
        'operad_target_colour: "Audit"\n'
        "operad_arity: 1\n"
        'operad_residual: "unknown"\n'
        "families: [review]\n"
        "triggers: [review]\n"
        "---\n\n# Review\n",
        encoding="utf-8",
    )
    agent = root / ".agents/agents/reviewer.md"
    agent.parent.mkdir(parents=True, exist_ok=True)
    agent.write_text(
        "---\n"
        "name: reviewer\n"
        'description: "A bounded reviewer."\n'
        "model: fixture\n"
        "authority_effect: none\n"
        "tools: []\n"
        "standalone: true\n"
        "licensed_skills: [review]\n"
        'licensed_colours: ["Audit", "Code"]\n'
        "---\n\n# Reviewer\n"
        + ("\nlicensed_skills = ['review']\n" if body_license else ""),
        encoding="utf-8",
    )


def test_live_catalog_is_exact_replayable_and_byte_identical_across_hosts() -> None:
    catalog = compile_capability_catalog(REPO_ROOT)

    assert len(catalog.skills) >= 133
    assert len(catalog.agents) == 0
    assert decode_capability_catalog(encode_capability_catalog(catalog)) == catalog
    if all((REPO_ROOT / host / "operad").is_dir() for host in HOST_NAMES):
        verify_host_projections(REPO_ROOT, catalog)
        expected = projection_bytes(catalog)
        for filename, payload in expected.items():
            assert {
                (REPO_ROOT / host / "operad" / filename).read_bytes()
                for host in HOST_NAMES
            } == {payload}
    for agent in catalog.agents:
        assert {
            (REPO_ROOT / host / agent.source_path).read_bytes()
            for host in HOST_NAMES
        } == {(REPO_ROOT / ".agents" / agent.source_path).read_bytes()}
    for skill in catalog.skills:
        assert {
            (REPO_ROOT / host / skill.source_path).read_bytes()
            for host in HOST_NAMES
        } == {(REPO_ROOT / ".agents" / skill.source_path).read_bytes()}


def test_catalog_uses_frontmatter_descriptions_without_inventing_absent_agents() -> None:
    catalog = compile_capability_catalog(REPO_ROOT)
    skills = {item.skill_id: item for item in catalog.skills}
    agents = {item.agent_id: item for item in catalog.agents}

    assert skills["github"].description != ""
    assert skills["techne-code-lossless-parser"].equivariant is False
    assert skills["techne-code-lossless-parser"].agent_scope == (
        "all",
        "techne-code-builder",
        "techne-dev",
    )
    assert "ow-bureau-mole-hunting" in skills
    assert "meekers" not in agents  # No tracked agent source exists on this tree.
    signature = json.loads(projection_bytes(catalog)["operad_signature.json"])
    descriptions = {
        row["skill_id"]: row["description"] for row in signature["operations"]
    }
    assert descriptions["github"] == skills[
        "github"
    ].description


def test_untracked_cache_directory_cannot_become_a_skill(tmp_path: Path) -> None:
    _fixture(tmp_path)
    cache = tmp_path / ".agents/skills/cache-only"
    cache.mkdir(parents=True)
    (cache / "SKILL.md").write_text("not tracked\n", encoding="utf-8")

    catalog = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)

    assert [item.skill_id for item in catalog.skills] == ["review"]


def test_tracked_package_without_entrypoint_is_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    path = tmp_path / ".agents/skills/ghost/data.txt"
    path.parent.mkdir(parents=True)
    path.write_text("tracked fixture\n", encoding="utf-8")
    inventory = tuple(sorted((*TRACKED_FIXTURE, ".agents/skills/ghost/data.txt")))

    with pytest.raises(CatalogCompileRefusal) as excinfo:
        compile_capability_catalog(tmp_path, tracked_paths=inventory)

    assert excinfo.value.code == "TRACKED_ENTRYPOINT_MISSING"


def test_agent_body_license_text_has_no_license_effect(tmp_path: Path) -> None:
    _fixture(tmp_path)
    before = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)
    _fixture(tmp_path, body_license=True)

    after = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)
    before_agent = before.agents[0]
    after_agent = after.agents[0]

    assert after_agent.licensed_skill_ids == before_agent.licensed_skill_ids
    assert after_agent.licensed_colour_ids == before_agent.licensed_colour_ids
    assert after_agent.license_digest == before_agent.license_digest
    assert after_agent.source_digest != before_agent.source_digest
    assert after.catalog_digest != before.catalog_digest


def test_catalog_digest_tampering_is_refused(tmp_path: Path) -> None:
    _fixture(tmp_path)
    catalog = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)
    encoded = encode_capability_catalog(catalog)
    replacement = b"0" if catalog.catalog_digest[0] != "0" else b"1"
    bad_digest = replacement + catalog.catalog_digest[1:].encode("ascii")
    tampered = encoded.replace(catalog.catalog_digest.encode("ascii"), bad_digest, 1)

    with pytest.raises(CapabilityCatalogRefusal) as excinfo:
        decode_capability_catalog(tampered)

    assert excinfo.value.code == "DIGEST_MISMATCH_REFUSED"


def test_license_digest_and_unsafe_source_path_tampering_are_refused(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    catalog = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)
    encoded = encode_capability_catalog(catalog)

    license_wire = json.loads(encoded)
    license_wire["agents"][0]["license_digest"] = "0" * 64
    tampered_license = (
        json.dumps(license_wire, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    with pytest.raises(CapabilityCatalogRefusal) as license_error:
        decode_capability_catalog(tampered_license)
    assert license_error.value.code == "LICENSE_DIGEST_MISMATCH_REFUSED"

    path_wire = json.loads(encoded)
    path_wire["agents"][0]["source_path"] = "C:/outside.md"
    unsafe_path = (
        json.dumps(path_wire, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    with pytest.raises(CapabilityCatalogRefusal) as path_error:
        decode_capability_catalog(unsafe_path)
    assert path_error.value.code == "PATH_REFUSED"


def test_catalog_refuses_wrong_member_types_and_dependency_cycles(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    catalog = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)

    with pytest.raises(CapabilityCatalogRefusal) as member_error:
        CapabilityCatalogV1(
            skills=(object(),),  # type: ignore[arg-type]
            agents=catalog.agents,
            catalog_digest="0" * 64,
        )
    assert member_error.value.code == "SKILL_TYPE_REFUSED"

    cyclic = replace(catalog.skills[0], declared_dependencies=("review",))
    with pytest.raises(CapabilityCatalogRefusal) as cycle_error:
        seal_capability_catalog(skills=(cyclic,), agents=catalog.agents)
    assert cycle_error.value.code == "DEPENDENCY_CYCLE_REFUSED"


def test_catalog_decoder_refuses_duplicate_unknown_float_and_noncanonical_json(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    catalog = compile_capability_catalog(tmp_path, tracked_paths=TRACKED_FIXTURE)
    encoded = encode_capability_catalog(catalog)

    duplicate = encoded.replace(
        b'{"agents":', b'{"authority_effect":"none","agents":', 1
    )
    with pytest.raises(CapabilityCatalogRefusal) as duplicate_error:
        decode_capability_catalog(duplicate)
    assert duplicate_error.value.code == "DUPLICATE_KEY_REFUSED"

    unknown_wire = json.loads(encoded)
    unknown_wire["unknown"] = "field"
    unknown = (
        json.dumps(unknown_wire, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    with pytest.raises(CapabilityCatalogRefusal) as unknown_error:
        decode_capability_catalog(unknown)
    assert unknown_error.value.code == "FIELD_SET_REFUSED"

    float_wire = json.loads(encoded)
    float_wire["skills"][0]["package_resources"][0]["byte_length"] = 1.5
    floating = (
        json.dumps(float_wire, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    with pytest.raises(CapabilityCatalogRefusal) as float_error:
        decode_capability_catalog(floating)
    assert float_error.value.code == "FLOAT_REFUSED"

    noncanonical = (json.dumps(json.loads(encoded), indent=2) + "\n").encode("ascii")
    with pytest.raises(CapabilityCatalogRefusal) as canonical_error:
        decode_capability_catalog(noncanonical)
    assert canonical_error.value.code == "NONCANONICAL_JSON_REFUSED"


def test_catalog_domain_has_no_infrastructure_dependency() -> None:
    source = (
        REPO_ROOT
        / "operads/domain/capability_catalog_v1.py"
    )
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imported & {
        "fastapi",
        "pathlib",
        "requests",
        "sqlite3",
        "subprocess",
        "yaml",
    }
