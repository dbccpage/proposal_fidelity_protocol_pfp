from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from omega_engine_operads.application.woland_candidate_plan import (
    PlanNodeV01,
    compile_candidate_plan,
)
from omega_engine_operads.contracts.typed_capabilities_v1 import (
    ROOT as CONTRACT_ROOT,
)
from omega_engine_operads.contracts.typed_capabilities_v1 import (
    canonical_bytes,
    contract_json_schema,
    parse_typed_capability,
)
from omega_engine_operads.domain.capability_catalog_v1 import (
    decode_capability_catalog,
    encode_capability_catalog,
)
from omega_engine_operads.infrastructure.typed_contract_compiler import (
    TypedContractCompileRefusal,
    compile_typed_contracts,
)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())


def test_generated_markdown_exposes_the_typed_signature_to_existing_discovery():
    import omega_engine_operations.infrastructure.skill_parser_registration  # noqa: F401
    from omega_engine_operations.domain.packaging.skill_frontmatter_audit import audit_document

    bundle = compile_typed_contracts(ROOT)
    assert bundle.packages
    for skill_id, raw in bundle.packages:
        finding = audit_document(skill_id, raw)
        assert finding.is_clean, finding.render()
        assert b'omega-residual: "unknown"' in raw
        assert b"Source admission: `Unadmitted`" in raw


def test_typed_pair_reuses_catalog_and_composes_without_self_admission():
    bundle = compile_typed_contracts(ROOT)
    assert decode_capability_catalog(encode_capability_catalog(bundle.catalog)) == bundle.catalog
    assert {s.skill_id for s in bundle.catalog.skills}.issuperset({
        "woland-claim-audit",
        "woland-scope-falsifier",
    })
    assert all(s.executor.state == "UNBOUND" for s in bundle.catalog.skills)
    assert all(not op.lifecycle.is_executable for op in bundle.operations)
    plan = compile_candidate_plan(
        bundle.documents,
        PlanNodeV01("woland-claim-audit", ((0, PlanNodeV01("woland-scope-falsifier")),)),
        allowed_effects=frozenset({"read_subject", "emit_finding"}),
    )
    assert plan.operation_count == 2
    assert tuple(str(port.colour_id) for port in plan.inputs) == ("Contract", "Contract")
    assert str(plan.output.colour_id) == "Receipt"
    assert plan.admission == "Unadmitted"
    assert all(bundle.contracts_digest in body for body in plan.ordered_operand_bodies)


def _estate(tmp_path):
    shutil.copytree(ROOT / CONTRACT_ROOT, tmp_path / CONTRACT_ROOT,
                    ignore=shutil.ignore_patterns("lessons"))
    return tmp_path


def _edit(root, filename, change):
    path = root / CONTRACT_ROOT / filename
    value = json.loads(path.read_bytes())
    change(value)
    path.write_bytes(canonical_bytes(value))


@pytest.mark.parametrize(
    "change",
    [
        lambda v: v.update(admission="Admitted"),
        lambda v: v.update(unknown_field="ignored?"),
        lambda v: v.update(binding="arbitrary.module.function"),
        lambda v: v.update(kind="rule"),
        lambda v: v["instruction"].update(byte_length=True),
        lambda v: v["instruction"].update(path="../escape"),
        lambda v: v["inputs"][0].update(extra="ignored?"),
        lambda v: v["inputs"][0].update(colour="Proof"),
        lambda v: v.update(effects=["read_subject", "publish"]),
        lambda v: v.update(description=" unnormalized description"),
        lambda v: v["inputs"][1].update(name=v["inputs"][0]["name"]),
        lambda v: v.update(dependencies=["z-guard", "a-guard"]),
        lambda v: v.update(effects=["emit_finding", "read_subject"]),
        lambda v: v["instruction"].update(path=".agents/skills/foreign/SKILL.md"),
    ],
)
def test_source_cannot_promote_coerce_or_add_unrecognized_semantics(tmp_path, change):
    root = _estate(tmp_path)
    _edit(root, "woland_claim_audit.json", change)
    with pytest.raises(TypedContractCompileRefusal, match="CONTRACT_SCHEMA_REFUSED"):
        compile_typed_contracts(root)


def test_listing_cap_refuses_before_projection(tmp_path):
    root = _estate(tmp_path)
    _edit(root, "woland_claim_audit.json", lambda value: value.update(description="x" * 121))
    with pytest.raises(TypedContractCompileRefusal, match="DESCRIPTION_REFUSED"):
        compile_typed_contracts(root)


@pytest.mark.parametrize(
    "transform",
    [
        lambda raw: b"\xef\xbb\xbf" + raw,
        lambda raw: raw.replace(b"\n", b"\r\n"),
        lambda raw: b" " + raw,
        lambda raw: raw.replace(b'"kind":"skill"', b'"kind":"skill","kind":"skill"'),
        lambda raw: raw.replace(b'"kind":"skill"', b'"kind":"skill","\\u006bind":"skill"'),
        lambda raw: raw.replace(b'"byte_length":', b'"byte_length":NaN,"discard":'),
    ],
)
def test_wire_refuses_ambiguous_or_noncanonical_bytes(transform):
    raw = (ROOT / CONTRACT_ROOT / "woland_claim_audit.json").read_bytes()
    with pytest.raises(ValueError):
        parse_typed_capability(transform(raw))


def test_resource_edit_refuses_until_new_digest_is_explicitly_authored(tmp_path):
    root = _estate(tmp_path)
    body = root / CONTRACT_ROOT / "instructions/woland_claim_audit.md"
    body.write_bytes(body.read_bytes() + b"Additional scoped instruction.\n")
    with pytest.raises(TypedContractCompileRefusal, match="RESOURCE_BINDING_REFUSED"):
        compile_typed_contracts(root)
    raw = body.read_bytes()
    _edit(
        root,
        "woland_claim_audit.json",
        lambda v: v["instruction"].update(
            sha256=hashlib.sha256(raw).hexdigest(),
            byte_length=len(raw),
        ),
    )
    original, changed = compile_typed_contracts(ROOT), compile_typed_contracts(root)
    assert changed.contracts_digest != original.contracts_digest
    assert changed.packages != original.packages


def test_predicate_mutation_cannot_redefine_the_named_scope_binding(tmp_path):
    root = _estate(tmp_path)
    _edit(
        root,
        "woland_scope_falsifier.json",
        lambda v: v["predicate"]["atoms"][0].update(
            operator="EQUAL_FIELDS",
        ),
    )
    with pytest.raises(TypedContractCompileRefusal, match="CONTRACT_SCHEMA_REFUSED"):
        compile_typed_contracts(root)


def test_relabelled_controls_fail_real_evaluation_even_with_updated_pins(tmp_path):
    from omega_engine_operads.domain.anti_skills import (
        AntiSkillFixtureBankV1,
        canonical_json_bytes,
    )

    root = _estate(tmp_path)
    bank = compile_typed_contracts(root).fixture_bank
    first = replace(bank.cases[0], expected_hit=False, negative_control=True, case_digest="")
    bank = AntiSkillFixtureBankV1(cases=(first, *bank.cases[1:]))
    path = root / CONTRACT_ROOT / "scope_falsifier_fixtures.json"
    raw = canonical_json_bytes(bank.to_dict())
    path.write_bytes(raw)
    _edit(
        root,
        "woland_scope_falsifier.json",
        lambda v: v["fixtures"].update(
            sha256=hashlib.sha256(raw).hexdigest(),
            byte_length=len(raw),
        ),
    )
    with pytest.raises(TypedContractCompileRefusal, match="FALSIFIER_CONTROLS_REFUSED"):
        compile_typed_contracts(root)


@pytest.mark.parametrize(
    "filename,change",
    [
        ("woland_claim_audit.json", lambda v: v["inputs"].reverse()),
        ("woland_claim_audit.json", lambda v: v.update(guard="unknown-guard")),
        ("woland_scope_falsifier.json", lambda v: v.update(dependencies=["woland-claim-audit"])),
    ],
)
def test_composition_and_dependency_errors_refuse(tmp_path, filename, change):
    root = _estate(tmp_path)
    _edit(root, filename, change)
    with pytest.raises(TypedContractCompileRefusal):
        compile_typed_contracts(root)


def test_generated_files_use_standard_frontmatter_and_existing_estate_catalog(tmp_path):
    import yaml

    from omega_engine_operads.infrastructure.capability_catalog_compiler import (
        CatalogCompileRefusal,
        compile_capability_catalog,
    )

    root = _estate(tmp_path)
    bundle = compile_typed_contracts(root)
    tracked = set()
    for skill_id, markdown in bundle.packages:
        path = f".agents/skills/{skill_id}/SKILL.md"
        target = root / path
        target.parent.mkdir(parents=True)
        target.write_bytes(markdown)
        tracked.add(path)
        frontmatter = yaml.safe_load(markdown.decode().split("---", 2)[1])
        assert set(frontmatter) == {"name", "description", "metadata"}
        assert all(type(value) is str for value in frontmatter["metadata"].values())
    for skill in bundle.catalog.skills:
        tracked.update(resource.path for resource in skill.package_resources)
    catalog = compile_capability_catalog(root, tracked_paths=tuple(sorted(tracked)))
    for compiled, scoped in zip(catalog.skills, bundle.catalog.skills):
        assert set(scoped.package_resources).issubset(compiled.package_resources)
        assert len(compiled.package_resources) == len(scoped.package_resources) + 1
    target.write_bytes(markdown + b"Host edit that must remain visible.\n")
    with pytest.raises(CatalogCompileRefusal, match="TYPED_PROJECTION_DRIFT"):
        compile_capability_catalog(root, tracked_paths=tuple(sorted(tracked)))


def test_exported_schema_matches_strict_adapter_and_has_no_unknown_fields():
    schema = json.loads((ROOT / CONTRACT_ROOT / "typed_capability.schema.json").read_bytes())
    assert schema == contract_json_schema()
    assert schema["$defs"]["SkillWireV1"]["additionalProperties"] is False
    assert schema["$defs"]["AntiSkillWireV1"]["additionalProperties"] is False
