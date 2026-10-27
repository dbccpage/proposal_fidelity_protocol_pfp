"""Filesystem discovery requires a validated capability catalog."""

from pathlib import Path

import hashlib
import shutil

from operads.domain.capability_catalog_v1 import encode_capability_catalog
from operads.infrastructure.typed_contract_compiler import compile_typed_contracts

from operads.domain.value_objects.identifier import EstateRef
from operads.infrastructure.fs.fs_estate_source_adapter import (
    FsEstateSourceAdapter,
)


def test_unregistered_skill_directory_cannot_replace_missing_catalog(tmp_path: Path):
    skill = tmp_path / ".agents/skills/unregistered/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Unregistered skill\n", encoding="utf-8")

    result = FsEstateSourceAdapter(tmp_path).list_skill_paths(EstateRef("fixture"))

    assert result.is_err
    assert result.unwrap_err().code == "CAPABILITY_CATALOG_MISSING"


def test_invalid_catalog_cannot_fall_back_to_skill_directories(tmp_path: Path):
    skill = tmp_path / ".agents/skills/unregistered/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Unregistered skill\n", encoding="utf-8")
    catalog = tmp_path / ".agents/operad/capability_catalog.v1.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text("{}\n", encoding="utf-8")

    result = FsEstateSourceAdapter(tmp_path).list_skill_paths(EstateRef("fixture"))

    assert result.is_err
    assert result.unwrap_err().code == "CAPABILITY_CATALOG_REFUSED"


def _typed_estate(tmp_path):
    root = Path(__file__).resolve().parents[3]
    relative = "operads/catalog/contracts/v1"
    shutil.copytree(root / relative, tmp_path / relative, ignore=shutil.ignore_patterns("lessons"))
    bundle = compile_typed_contracts(tmp_path)
    for skill_id, raw in bundle.packages:
        target = tmp_path / f".agents/skills/{skill_id}/SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(raw)
    catalog = tmp_path / ".agents/operad/capability_catalog.v1.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_bytes(encode_capability_catalog(bundle.catalog))
    return bundle


def test_generated_entrypoint_loads_canonical_document_and_refuses_changed_resources(tmp_path):
    bundle = _typed_estate(tmp_path)
    adapter = FsEstateSourceAdapter(tmp_path)
    paths = adapter.list_skill_paths(EstateRef("fixture")).unwrap()
    path = ".agents/skills/adversary-claim-audit/SKILL.md"
    assert path in paths
    document = adapter.read_compiled_skill_document(path).unwrap()
    assert document == bundle.documents[0]
    assert str(document.operations[0].operation_id) == "adversary-claim-audit"
    assert document.raw_digest.hex_digest == hashlib.sha256(
        (tmp_path / document.source_relative_path).read_bytes()
    ).hexdigest()
    instruction = tmp_path / "operads/catalog/contracts/v1/instructions/adversary_claim_audit.md"
    instruction.write_bytes(instruction.read_bytes() + b"Changed after catalog capture.\n")
    assert adapter.read_compiled_skill_document(path).is_err


def test_generated_entrypoint_cannot_fall_back_to_prose_after_host_edit(tmp_path):
    _typed_estate(tmp_path)
    adapter = FsEstateSourceAdapter(tmp_path)
    adapter.list_skill_paths(EstateRef("fixture")).unwrap()
    path = ".agents/skills/adversary-claim-audit/SKILL.md"
    target = tmp_path / path
    target.write_bytes(target.read_bytes() + b"Host-maintained edit.\n")
    assert adapter.read_compiled_skill_document(path).is_err


def test_actual_container_compiles_mixed_canonical_and_v3_packages(tmp_path):
    from operads.infrastructure.bootstrap import OeopContainer
    from operads.infrastructure.capability_catalog_compiler import compile_capability_catalog

    bundle = _typed_estate(tmp_path)
    legacy = tmp_path / ".agents/skills/legacy/SKILL.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"---\nname: legacy\ndescription: Legacy audit.\noperad_source_colours: []\noperad_target_colour: Audit\noperad_arity: 0\noperad_residual: unknown\n---\n\n~~~oewas.operation.v3\noperation_id: legacy:audit\ninputs: []\n~~~\n")
    tracked = {resource.path for skill in bundle.catalog.skills for resource in skill.package_resources}
    tracked.update(f".agents/skills/{skill_id}/SKILL.md" for skill_id, _ in bundle.packages)
    tracked.add(legacy.relative_to(tmp_path).as_posix())
    catalog = compile_capability_catalog(tmp_path, tracked_paths=tuple(sorted(tracked)))
    (tmp_path / ".agents/operad/capability_catalog.v1.json").write_bytes(encode_capability_catalog(catalog))
    container = OeopContainer(tmp_path)
    try:
        result = container.api.compile_catalog().unwrap()
        assert result.total_skills == 3 and result.total_operations == 3
        persisted = container.api.get_catalog(result.catalog_id).unwrap()
        assert set(map(str, persisted.operations)) == {"legacy:audit", "adversary-claim-audit", "adversary-scope-falsifier"}
        assert all(op.lifecycle.admission.value == "Unadmitted" for op in persisted.operations.values())
    finally:
        container.uow.close()
