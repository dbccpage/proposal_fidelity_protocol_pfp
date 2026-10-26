"""Digested guidance uses the existing compiler, catalog and host projector."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from omega_engine_operations.use_cases.packaging.project_typed_contracts import (
    project_typed_packages,
)
from omega_engine_operations.use_cases.packaging.sync_cross_host_skills import HOST_SKILL_ROOTS
from omega_engine_operads.contracts.typed_capabilities_v1 import (
    ROOT,
    canonical_bytes,
)
from omega_engine_operads.infrastructure.typed_contract_compiler import (
    TypedContractCompileRefusal,
    compile_typed_contracts,
)

REPO = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
KINDS = ("rule", "helpful_pattern", "anti_pattern", "antibody")


def _resource(root, relative):
    raw = (root / relative).read_bytes()
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "byte_length": len(raw)}


def _estate(tmp_path):
    shutil.copytree(REPO / ROOT, tmp_path / ROOT, ignore=shutil.ignore_patterns("lessons"))
    for host in HOST_SKILL_ROOTS:
        (tmp_path / host).mkdir(parents=True)
    return tmp_path


def _entry(root, kind):
    instruction = _resource(root, ROOT + "/instructions/woland_claim_audit.md")
    row = {
        "schema_version": "oewas.typed-capability.v1",
        "kind": kind,
        "skill_id": "digested-" + kind.replace("_", "-"),
        "description": "Review a digested input contract.",
        "binding": "woland.digested_guidance.v1",
        "instruction": instruction,
        "inputs": [{"name": "candidate", "colour": "Code", "wire_type": "code_text"}],
        "output": {
            "name": "result",
            "colour": "Code" if kind == "helpful_pattern" else "Audit",
            "wire_type": "code_text" if kind == "helpful_pattern" else "anti_skill_hits",
        },
        "dependencies": [],
        "effects": ["read_subject", "emit_finding"],
        "authority_effect": "None",
        "admission": "Unadmitted",
        "lesson": {
            "source": instruction,
            "source_revision": "reviewed-source",
            "evidence_excerpt": "claim_scope",
            "failed_claim": "Malformed inputs may be repaired silently.",
            "counterexample": "A scalar became an invented operation.",
            "cause": "Implicit coercion.",
            "correction": "Return BAD_STEP.",
            "verification": "Source review; no historical reexecution.",
            "applicability": "Declared strict ingress.",
            "exceptions": "Schema-authorized normalization.",
        },
    }
    row.update(
        {
            "rule": {
                "trigger": "Before parsing",
                "predicate": "Input matches its declared shape",
                "response": "Refuse BAD_STEP",
            },
            "helpful_pattern": {
                "conditions": "Strict input boundary",
                "construction": "Validate then parse",
                "example": "Return BAD_STEP for scalars",
            },
            "anti_pattern": {
                "failure": "Silent coercion",
                "witness": "Scalar becomes a mapping",
                "repair": "Return BAD_STEP",
            },
            "antibody": {
                "antibody_id": "ab_silent_input_schema_coercion",
                "pharmacy_status": "candidate",
                "prompt": instruction,
                "prompt_uri": "prompt://woland/digestion/input/review/TYPED_INPUT",
                "signal1_epitope": "str(raw_step)",
                "signal2_required_danger": "STRICT_INPUT_VIOLATION",
                "harmful_example": 'raw_step = {"op": str(raw_step)}',
                "benign_example": 'return Err(RefusalRecord(code="BAD_STEP"))',
            },
        }[kind]
    )
    path = root / ROOT / "lessons" / (row["skill_id"] + ".json")
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(canonical_bytes(row))
    return path, row


def test_four_digested_kinds_compile_and_generate_portable_packages(tmp_path):
    root = _estate(tmp_path)
    for kind in KINDS:
        _entry(root, kind)
    bundle = compile_typed_contracts(root)
    assert len(bundle.packages) == 6
    assert {item.skill_id for item in bundle.catalog.skills} == {
        name for name, _ in bundle.packages
    }
    assert all(not op.lifecycle.is_executable for op in bundle.operations)
    paths = project_typed_packages(root, bundle.packages)
    assert len(paths) == 24
    assert project_typed_packages(root, bundle.packages, check=True) == paths
    assert compile_typed_contracts(root) == bundle
    for name, raw in bundle.packages:
        meta = yaml.safe_load(raw.decode().split("---", 2)[1])
        assert set(meta) == {"name", "description", "metadata"}
        for host in HOST_SKILL_ROOTS:
            assert (root / host / name / "SKILL.md").read_bytes() == raw
    for kind in KINDS:
        raw = dict(bundle.packages)["digested-" + kind.replace("_", "-")].decode()
        assert "Schema-authorized normalization" in raw
        assert "Source review; no historical reexecution" in raw
        assert "--audit-subject" not in raw  # This is guidance, not the scope detector.


def test_retired_lesson_source_uses_its_exact_git_revision_without_restoring_owner(tmp_path):
    root = _estate(tmp_path)
    lesson_path, row = _entry(root, "rule")
    source = root / "_ic/nara/historical/oewas007/research/review.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"Retained claim_scope evidence.\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "-f", str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "Retain exact fixture source"], check=True, capture_output=True)
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True).stdout.decode().strip()
    row["lesson"].update(source=_resource(root, source.relative_to(root).as_posix()), source_revision=revision)
    lesson_path.write_bytes(canonical_bytes(row))
    resident = compile_typed_contracts(root)
    original = source.read_bytes()
    source.write_bytes(original + b"Changed resident source must not fall back.\n")
    with pytest.raises(TypedContractCompileRefusal, match="RESOURCE_BINDING_REFUSED"):
        compile_typed_contracts(root)
    source.write_bytes(original)
    source.unlink()
    assert compile_typed_contracts(root) == resident
    assert not source.exists()
    row["lesson"]["source_revision"] = "0" * 40
    lesson_path.write_bytes(canonical_bytes(row))
    with pytest.raises(TypedContractCompileRefusal, match="HISTORICAL_SOURCE_UNAVAILABLE"):
        compile_typed_contracts(root)
    row["lesson"]["source_revision"] = revision
    row["lesson"]["source"]["sha256"] = "a" * 64
    lesson_path.write_bytes(canonical_bytes(row))
    with pytest.raises(TypedContractCompileRefusal, match="RESOURCE_BINDING_REFUSED"):
        compile_typed_contracts(root)


@pytest.mark.parametrize(
    "change,code",
    [
        (
            lambda row: row["lesson"].update(evidence_excerpt="Invented excerpt"),
            "LESSON_SOURCE_REFUSED",
        ),
        (lambda row: row["lesson"]["source"].update(sha256="0" * 64), "RESOURCE_BINDING_REFUSED"),
        (
            lambda row: row.update(harmful_example=row["benign_example"]),
            "ANTIBODY_CONTROLS_REFUSED",
        ),
        (lambda row: row.update(prompt_uri="unbound-prompt"), "CONTRACT_SCHEMA_REFUSED"),
        (lambda row: row.update(pharmacy_status="admitted"), "CONTRACT_SCHEMA_REFUSED"),
        (lambda row: row.update(binding="model.chosen.executor"), "CONTRACT_SCHEMA_REFUSED"),
        (lambda row: row.update(skill_id="woland-claim-audit"), "CONTRACT_ID_REFUSED"),
        (lambda row: row.update(dependencies=["missing-owner"]), "DEPENDENCY_REFUSED"),
    ],
)
def test_false_provenance_detached_antibodies_and_promotion_refuse(tmp_path, change, code):
    root = _estate(tmp_path)
    path, row = _entry(root, "antibody")
    change(row)
    path.write_bytes(canonical_bytes(row))
    with pytest.raises(TypedContractCompileRefusal, match=code):
        compile_typed_contracts(root)
    assert not list((root / ".agents/skills").iterdir())


def test_prompt_attachment_reuses_existing_inert_binding(tmp_path):
    from omega_engine_operads.domain.prompt_hierarchy.evaluator import (
        evaluate_prompt_gates,
    )

    root = _estate(tmp_path)
    _, row = _entry(root, "antibody")
    bundle = compile_typed_contracts(root)
    (node,) = bundle.prompt_attachments
    assert node.source_file == row["prompt"]["path"]
    assert node.antibodies[0].antibody_id == row["antibody_id"]
    result = evaluate_prompt_gates(
        node,
        {"candidate": row["harmful_example"]},
        host_danger_signals=(row["signal2_required_danger"],),
    )
    assert result.passed  # No admission: even a harmful sighting cannot activate.
    assert not result.antibodies_fired


def test_changed_prompt_refuses_before_any_projection(tmp_path):
    root = _estate(tmp_path)
    path, row = _entry(root, "antibody")
    prompt_path = ROOT + "/review_prompt.md"
    (root / prompt_path).write_bytes(b"Review declared input boundaries.\n")
    row["prompt"] = _resource(root, prompt_path)
    path.write_bytes(canonical_bytes(row))
    compile_typed_contracts(root)  # Eligible baseline before changing only the prompt.
    (root / row["prompt"]["path"]).write_bytes(b"Changed prompt.\n")
    with pytest.raises(TypedContractCompileRefusal, match="RESOURCE_BINDING_REFUSED"):
        compile_typed_contracts(root)


def test_guidance_composition_preserves_lesson_and_original_pair_api(tmp_path):
    from omega_engine_operads.application.woland_candidate_plan import (
        PlanNodeV01,
        compile_candidate_plan,
    )

    root = _estate(tmp_path)
    _, row = _entry(root, "helpful_pattern")
    bundle = compile_typed_contracts(root)
    assert len(bundle.documents) == 2
    assert len(bundle.all_documents) == 3
    plan = compile_candidate_plan(
        bundle.guidance_documents,
        PlanNodeV01(row["skill_id"]),
        allowed_effects=frozenset({"read_subject", "emit_finding"}),
    )
    assert row["lesson"]["exceptions"] in plan.ordered_operand_bodies[0]
    assert row["construction"] in plan.ordered_operand_bodies[0]
    assert plan.admission == "Unadmitted"
    assert (
        bundle.guidance_documents[0].operations[0].lifecycle.executor_digest
        != bundle.operations[0].lifecycle.executor_digest
    )


def test_real_digested_entries_reuse_catalog_and_source_owners(tmp_path):
    from omega_engine_operads.infrastructure.capability_catalog_compiler import (
        compile_capability_catalog,
    )
    from omega_engine_operads.infrastructure.typed_contract_compiler import read_typed_package_resource
    from omega_engine_operads.domain.capability_catalog_v1 import ResourceRefV1

    root = _estate(tmp_path)
    shutil.copytree(REPO / ROOT / "lessons", root / ROOT / "lessons")
    for path in (root / ROOT / "lessons").glob("*.json"):
        row = json.loads(path.read_bytes())
        for resource in (row["lesson"]["source"], row.get("prompt", row["instruction"])):
            destination = root / resource["path"]
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(read_typed_package_resource(REPO, row["skill_id"], ResourceRefV1(**resource)))
    bundle = compile_typed_contracts(root)
    assert len(bundle.packages) == 2 + len(list((REPO / ROOT / "lessons").glob("*.json")))
    antibody = dict(bundle.packages)["woland-input-coercion-antibody"].decode()
    assert "```text\n" in antibody
    assert ">   " not in antibody
    project_typed_packages(root, bundle.packages)
    tracked = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    )
    catalog = compile_capability_catalog(root, tracked_paths=tracked)
    assert {skill.skill_id for skill in catalog.skills} == {name for name, _ in bundle.packages}
