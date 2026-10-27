"""The editable OEOP source controls catalogs and host projections."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from operads.domain.value_objects.identifier import EstateRef
from operads.infrastructure.capability_catalog_compiler import (
    CatalogCompileRefusal,
    compile_capability_catalog,
    write_host_projections,
)
from operads.infrastructure.fs.fs_estate_source_adapter import FsEstateSourceAdapter
from operations.use_cases.packaging.project_typed_contracts import (
    HostProjectionRefusal,
    project_typed_packages,
)
from operations.use_cases.packaging.sync_cross_host_skills import (
    HOST_SKILL_ROOTS,
    FourHostSkillMirror,
)

SOURCE = "operads/skills/demo/SKILL.md"
HOST = ".agents/skills/demo/SKILL.md"


def _helper(relative):
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location("source_owner_helper", root / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_common_guidance_and_version_views_match_owned_sources():
    root = Path(__file__).resolve().parents[3]
    guide = (root / "operads/documentation/host_instructions.md").read_bytes()
    version = (root / "operads/manifests/host_discovery_version.txt").read_bytes()
    assert version.strip() == b"0.0.0-a00"
    assert (root / "GEMINI.md").read_bytes() == guide
    for host in (".agents", ".claude", ".codex", ".grok"):
        assert (root / host / "AGENTS.md").read_bytes() == guide
        assert (root / host / "VERSION").read_bytes() == version


def test_pattern_helper_reads_owned_pattern_not_changed_host(tmp_path):
    helper = _helper("operads/skills/auto-anti-pattern-lint/scripts/anti_pattern_lint.py")
    put(tmp_path, "operads/patterns/helpful/python/HP_DEMO.md", b"## Resolution\nCanonical remedy\n")
    put(tmp_path, ".agents/patterns/helpful/python/HP_DEMO.md", b"## Resolution\nHost edit\n")
    result = helper._load_healthy_pattern("HP_DEMO", tmp_path, "python")
    assert result["resolution"] == "Canonical remedy"
    assert result["dual_pattern_path"].startswith("operads/")


def test_declared_checker_detects_source_drift_even_when_all_hosts_agree(tmp_path):
    helper = _helper("operads/skills/declared-vs-actual-gate/scripts/check_declared_programs.py")
    put(tmp_path, "operads/skills/demo/SKILL.md", document("Canonical"))
    for host in (".agents", ".claude", ".codex", ".grok"):
        put(tmp_path, f"{host}/skills/demo/SKILL.md", document("Same host edit"))
    result = helper.check_parity(tmp_path, helper.host_roots(tmp_path))
    assert result["canonical"] == "operads"
    assert result["verdict"] == "BLOCKED"
    assert len(result["rows"]) == 4


def test_inventory_and_route_lookup_use_only_the_owned_signature(tmp_path):
    from operads.skill_operad.skill_compiler.op_inventory import _coarse_ops
    from operads.skill_operad.skill_compiler.resolve import _operad_skill_ids

    canonical = "operads/skill_operad/json/operad_signature.json"
    host = ".agents/skill_operads/operad_signature.json"
    put(tmp_path, canonical, json.dumps({"operations": [{"skill_id": "source-op"}]}).encode())
    put(tmp_path, host, json.dumps({"operations": [{"skill_id": "host-edit"}]}).encode())
    assert set(_coarse_ops(tmp_path)) == {"source-op"}
    assert "source-op" in _operad_skill_ids(tmp_path)
    assert "host-edit" not in _operad_skill_ids(tmp_path)


def test_missing_owned_signature_does_not_fall_back_to_host(tmp_path):
    from operads.skill_operad.skill_compiler.op_inventory import _coarse_ops
    from operads.skill_operad.skill_compiler.resolve import _operad_skill_ids

    (tmp_path / "operads/skill_operad/json").mkdir(parents=True)
    put(tmp_path, ".agents/skill_operads/operad_signature.json", b'{"operations":[{"skill_id":"host-edit"}]}')
    with pytest.raises(FileNotFoundError):
        _coarse_ops(tmp_path)
    assert "host-edit" not in _operad_skill_ids(tmp_path)


def document(description):
    return (
        "---\nname: demo\ndescription: " + description + "\n"
        "operad_source_colours: [Code]\noperad_target_colour: Audit\n"
        "operad_arity: 1\noperad_residual: unknown\n---\n\n# Demo\n"
    ).encode()


def put(root: Path, relative: str, content: bytes):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_catalog_uses_canonical_source_even_when_host_copy_differs(tmp_path):
    original = document("Canonical instructions")
    put(tmp_path, SOURCE, original)
    put(tmp_path, HOST, document("Changed host instructions"))
    catalog = compile_capability_catalog(tmp_path, tracked_paths=tuple(sorted((SOURCE, HOST))))
    assert catalog.skills[0].source_digest == hashlib.sha256(original).hexdigest()
    assert catalog.skills[0].description == "Canonical instructions"


def test_missing_tracked_canonical_source_does_not_fall_back_to_host(tmp_path):
    put(tmp_path, HOST, document("Host instructions"))
    with pytest.raises(CatalogCompileRefusal, match="TRACKED_FILE_MISSING"):
        compile_capability_catalog(tmp_path, tracked_paths=tuple(sorted((SOURCE, HOST))))


def test_explicit_historical_host_inventory_remains_readable(tmp_path):
    put(tmp_path, HOST, document("Historical declared fixture"))
    catalog = compile_capability_catalog(tmp_path, tracked_paths=(HOST,))
    assert catalog.skills[0].description == "Historical declared fixture"


def test_filesystem_consumer_reads_canonical_bytes_not_host_copy(tmp_path):
    original = document("Canonical instructions")
    put(tmp_path, SOURCE, original)
    put(tmp_path, HOST, original)
    (tmp_path / "operads/skill_operad/json").mkdir(parents=True)
    catalog = compile_capability_catalog(tmp_path, tracked_paths=tuple(sorted((SOURCE, HOST))))
    write_host_projections(tmp_path, catalog)
    put(tmp_path, HOST, document("Changed generated host copy"))
    adapter = FsEstateSourceAdapter(tmp_path)
    result = adapter.list_skill_paths(EstateRef("canonical"))
    assert result.is_ok
    assert result.unwrap() == (SOURCE,)
    assert adapter.read_skill_bytes(SOURCE).unwrap() == original


def mirror_fixture(root):
    original = document("Canonical instructions")
    put(root, SOURCE, original)
    for host in HOST_SKILL_ROOTS:
        put(root, f"{host}/demo/SKILL.md", original)
    return FourHostSkillMirror(root=root)


def test_packaging_receipt_includes_canonical_source_and_each_host(tmp_path):
    receipt = mirror_fixture(tmp_path).receipt(["demo"])
    assert receipt.source_host == "operads/skills"
    assert set(receipt.hosts) == {"operads/skills", *HOST_SKILL_ROOTS}
    assert receipt.all_agree()


def test_equal_hosts_do_not_hide_a_changed_canonical_source(tmp_path):
    mirror = mirror_fixture(tmp_path)
    put(tmp_path, SOURCE, document("Revised canonical instructions"))
    assert not mirror.receipt(["demo"]).all_agree()


def test_typed_projection_includes_source_and_detects_a_conflicting_source(tmp_path):
    (tmp_path / "operads/skills").mkdir(parents=True)
    for host in HOST_SKILL_ROOTS:
        (tmp_path / host).mkdir(parents=True)
    packages = (("demo", document("Compiled instructions")),)
    paths = project_typed_packages(tmp_path, packages)
    assert SOURCE in paths and len(paths) == len(HOST_SKILL_ROOTS) + 1
    assert project_typed_packages(tmp_path, packages, check=True) == paths
    put(tmp_path, SOURCE, document("Conflicting manual edit"))
    before = {path: (tmp_path / path).read_bytes() for path in paths}
    with pytest.raises(HostProjectionRefusal, match="HOST_PROJECTION_CONFLICT"):
        project_typed_packages(tmp_path, packages)
    assert before == {path: (tmp_path / path).read_bytes() for path in paths}
