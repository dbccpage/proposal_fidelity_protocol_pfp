"""Current source retirement reaches the existing signed pre-dispatch boundary."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from omega_engine_woland.domain.instruction_ingress import instruction_request_digest
from omega_engine_woland.domain.models import WolandBoutRequestV1
from omega_engine_woland.infrastructure.oewas_instruction_ingress import (
    OeopSourceRouteV01, SignedOeopInstructionIngress, read_candidate_route,
    read_route_documents, workload_profile_digest,
)
from omega_engine_woland.use_cases.base_swarm.specializations import RESEARCH_PROFILE_V01
from omega_engine_operads.application.commands.compile_catalog import operation_content_digest
from omega_engine_operads.application.woland_candidate_plan import PlanNodeV01, PlanRefusal, candidate_plan_material
from omega_engine_operads.application.woland_candidate_plan import compile_candidate_plan
from omega_engine_operads.domain.value_objects.identifier import SkillId
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import LosslessMarkdownParserAdapter
from omega_engine_operads.application.woland_instruction_admission import source_snapshot_digest
from omega_engine_operads.application.woland_task_selection import WolandTaskShapeV01, select_candidate_plan
from omega_engine_operads.domain.capability_catalog_v1 import encode_capability_catalog
from omega_engine_operads.infrastructure.bootstrap import OeopContainer
from omega_engine_operads.infrastructure.capability_catalog_compiler import compile_capability_catalog

PROJECTION_PATH = "omega_engine_operads/catalog/projections/v3/selected.json"


@pytest.mark.parametrize("path", [".agents/skills/../new/SKILL.md", ".agents/skills/new//SKILL.md", ".agents/skills/new\\other/SKILL.md"])
def test_pure_projected_compiler_refuses_noncanonical_source_paths_before_io(path):
    document = LosslessMarkdownParserAdapter().parse_document(SkillId("new"), path, _source("new")).unwrap()
    with pytest.raises(PlanRefusal, match="SOURCE_PATH_INVALID"):
        compile_candidate_plan((document,), PlanNodeV01("route.new"), projection={}, projection_path=PROJECTION_PATH)


def test_pure_projected_compiler_refuses_escaping_projection_path_before_io():
    path = ".agents/skills/new/SKILL.md"
    document = LosslessMarkdownParserAdapter().parse_document(SkillId("new"), path, _source("new")).unwrap()
    projection = {"operation_records": [{"operation_id": "route.new", "admission": "Unadmitted",
        "source_path": path, "content_digest": str(operation_content_digest(document.operations[0]))}]}
    with pytest.raises(PlanRefusal, match="PROJECTION_INVALID"):
        compile_candidate_plan((document,), PlanNodeV01("route.new"), projection=projection,
                               projection_path="omega_engine_operads/catalog/projections/v3/../foreign.json")


def test_selected_digested_canonical_route_reaches_existing_instruction_reader():
    root = Path(__file__).resolve().parents[3]
    source = "omega_engine_operads/catalog/contracts/v1/lessons/woland-strict-input-pattern.json"
    route = replace(_route("woland-strict-input-pattern"), source_kind="typed_contracts", source_paths=(source,))
    documents = read_route_documents(root, route)
    assert len(documents) == 1 and documents[0].source_relative_path == source
    assert str(documents[0].operations[0].operation_id) == "woland-strict-input-pattern"
    assert documents[0].operations[0].lifecycle.admission.value == "Unadmitted"
    assert "BAD_STEP" in documents[0].operands[0].instruction_body


def _source(name, *, retired=False, replacement=None):
    port = lambda colour: {
        "name": colour.lower(), "colour_id": colour, "schema_ref": f"schema:{colour}:v1",
        "schema_digest": "a" * 64, "validator_ref": f"validator:{colour}", "validator_digest": "b" * 64,
    }
    operation = {
        "operation_id": f"route.{name}", "declaration": "Declared", "schema_binding": "Bound",
        "executor_binding": "Bound", "validation": "Validated", "admission": "Retired" if retired else "Admitted",
        "schema_digest": "c" * 64, "executor_digest": "d" * 64,
        "inputs": [port("Code")], "output": port("Audit"), "operand_refs": [f"route.{name}.body"],
    }
    if replacement is not None:
        operation["replacement_operation_id"] = replacement
    meta = {"name": name, "description": f"Check {name} evidence.", "operad_source_colours": ["Code"],
            "operad_target_colour": "Audit", "operad_arity": 1, "operad_residual": "unknown"}
    operand = {"operand_id": f"route.{name}.body", "kind": "instruction", "body": "Preserve exact source evidence."}
    return ("---\n" + yaml.safe_dump(meta) + "---\n\n```oewas.operand.v3\n" + yaml.safe_dump(operand)
            + "```\n\n```oewas.operation.v3\n" + yaml.safe_dump(operation) + "```\n").encode()


def _estate(tmp_path):
    root = tmp_path / "repo"
    for name in ("old", "new"):
        path = root / f".agents/skills/{name}/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(_source(name))
    return root, OeopContainer(root)


def _project(root, container):
    paths = tuple(sorted(path.relative_to(root).as_posix() for path in (root / ".agents/skills").glob("*/SKILL.md")))
    catalog = compile_capability_catalog(root, tracked_paths=paths)
    path = root / ".agents/operad/capability_catalog.v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_capability_catalog(catalog))
    compiled = container.api.compile_catalog().unwrap()
    projected = container.api.compile_projection(compiled.catalog_id).unwrap()
    projection_path = root / PROJECTION_PATH
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_bytes(projected.payload.encode())
    return json.loads(projected.payload), container.api.get_catalog(compiled.catalog_id).unwrap()


def _route(root_id):
    return OeopSourceRouteV01("route.selected", RESEARCH_PROFILE_V01.specialization_id,
        workload_profile_digest(RESEARCH_PROFILE_V01), "coding", (PROJECTION_PATH,),
        PlanNodeV01(root_id), "projection")


def _selection(root, request, route):
    candidate = read_candidate_route(root, route)
    operation = candidate.documents[0].operations[0]
    task = WolandTaskShapeV01(instruction_request_digest(request), route.workload_profile_id,
        route.workload_profile_digest, route.domain_id, operation.inputs, operation.output)
    return task, select_candidate_plan(task, (candidate,))


def _signed_ingress(tmp_path, root, request, route):
    task, selected = _selection(root, request, route)
    ssh = shutil.which("ssh-keygen")
    assert ssh, "existing OpenSSH signature verifier required"
    key = tmp_path / "fixture_key"
    if not key.exists():
        generated = subprocess.run([ssh, "-q", "-t", "ed25519", "-N", "", "-f", str(key)], capture_output=True)
        assert generated.returncode == 0, generated.stderr.decode(errors="replace")
    manifest = {
        "schema_version": "oewas.woland.instruction_admission.v0.1", "decision": "APPROVE",
        "reviewer_identity": "fixture.operator", "authority_effect": "None", "request_digest": task.request_digest,
        "task_shape_digest": selected.task_shape_digest, "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest, "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest, "route_id": selected.route_id,
        "plan_digest": selected.plan.plan_digest, "source_snapshot_digest": source_snapshot_digest(selected),
    }
    path = tmp_path / "admission.json"
    path.write_bytes((json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode())
    signature = tmp_path / "admission.json.sig"
    signature.unlink(missing_ok=True)
    subprocess.run([ssh, "-Y", "sign", "-f", str(key), "-n", "oewas-woland-instruction-v0.1", str(path)],
                   check=True, capture_output=True)
    trust = tmp_path / "allowed_signers"
    trust.write_text("fixture.operator " + (tmp_path / "fixture_key.pub").read_text())
    return SignedOeopInstructionIngress(repo_root=root, workload_profile=RESEARCH_PROFILE_V01,
        domain_id="coding", route_specs=(route,), task_shape=task, manifest_path=path,
        signature_path=signature, allowed_signers_path=trust, ssh_keygen=ssh)


def test_retirement_and_replacement_survive_actual_catalog_storage_and_source_replay(tmp_path):
    root, container = _estate(tmp_path)
    try:
        original, stored = _project(root, container)
        op = next(op for op in stored.operations.values() if str(op.operation_id) == "route.old")
        assert op.lifecycle.admission.value == "Unadmitted"
        assert "replacement_operation_id" not in original["operation_records"][1]
        before = operation_content_digest(op)
        assert operation_content_digest(replace(op, replacement_operation_id=None)) == before
        (root / ".agents/skills/old/SKILL.md").write_bytes(_source("old", retired=True, replacement="route.new"))
        projection, stored = _project(root, container)
        retired = next(op for op in stored.operations.values() if str(op.operation_id) == "route.old")
        assert retired.lifecycle.admission.value == "Retired"
        assert str(retired.replacement_operation_id) == "route.new"
        assert projection["catalog_digest"] != original["catalog_digest"]
        with pytest.raises(PlanRefusal, match="OPERATION_RETIRED"):
            _selection(root, WolandBoutRequestV1("Check", "retired_projection"), _route("route.old"))
        request = WolandBoutRequestV1("Check", "replacement_projection")
        _task, selected = _selection(root, request, _route("route.new"))
        assert candidate_plan_material(selected.plan)["projection"] == projection
        assert (PROJECTION_PATH, "sha256:" + hashlib.sha256((root / PROJECTION_PATH).read_bytes()).hexdigest()) in selected.plan.source_digests
        projection["operation_records"][1]["admission"] = "Unadmitted"
        (root / PROJECTION_PATH).write_bytes(json.dumps(projection, sort_keys=True, separators=(",", ":")).encode())
        with pytest.raises(PlanRefusal, match="PROJECTION_REFUSED"):
            _selection(root, request, _route("route.new"))
    finally:
        container.uow.close()


def test_actual_signed_predispatch_rejects_old_projection_then_accepts_replacement(tmp_path):
    root, container = _estate(tmp_path)
    try:
        _project(root, container)
        request = WolandBoutRequestV1("Check evidence", "signed_retirement_projection", fixture_mode=True)
        old_ingress = _signed_ingress(tmp_path, root, request, _route("route.old"))
        old_receipt = old_ingress.pre_dispatch(request).unwrap()
        (root / ".agents/skills/old/SKILL.md").write_bytes(_source("old", retired=True, replacement="route.new"))
        assert old_ingress.pre_dispatch(request).is_err
        _project(root, container)
        refused = old_ingress.pre_dispatch(request)
        assert refused.is_err and refused.unwrap_err().code == "OEWAS_OPERATION_RETIRED"
        replacement_ingress = _signed_ingress(tmp_path, root, request, _route("route.new"))
        receipt = replacement_ingress.pre_dispatch(request).unwrap()
        assert receipt.plan_digest != old_receipt.plan_digest
        assert replacement_ingress.native_admission(request).unwrap()["plan_material"]["projection_path"] == PROJECTION_PATH
        assert not (root / "_ic").exists()
    finally:
        container.uow.close()


def test_missing_replacement_holds_projection_migration(tmp_path):
    root, container = _estate(tmp_path)
    try:
        (root / ".agents/skills/old/SKILL.md").write_bytes(_source("old", retired=True, replacement="route.absent"))
        _project(root, container)
        with pytest.raises(PlanRefusal, match="replacement is missing"):
            read_route_documents(root, _route("route.new"))
    finally:
        container.uow.close()


@pytest.mark.parametrize("extra_count", [0, 90])
def test_native_consumer_refuses_signed_projection_omission_before_provider_io(tmp_path, extra_count):
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost, _runtime_request_bytes

    root, container = _estate(tmp_path)
    try:
        for index in range(extra_count):
            name = f"additional-{index:03}"
            path = root / f".agents/skills/{name}/SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_bytes(_source(name))
        _project(root, container)
        request = WolandBoutRequestV1("Check evidence", "native_retirement_projection", fixture_mode=False)
        ingress = _signed_ingress(tmp_path, root, request, _route("route.new"))
        receipt = ingress.pre_dispatch(request).unwrap()
        admission = ingress.native_admission(request).unwrap()
        transport = receipt.native_instruction_plan()
        payload = {
            "task_key": request.task_key, "objective": request.objective, "repo_root": str(root),
            "woland_output_dir": str(root / "_ic/woland"), "resources_root": str(Path(__file__).resolve().parents[3]),
            "ledger_path": str(tmp_path / "never-written.jsonl"), "bout_id": "projection-boundary",
            "config_path": str(tmp_path / "never-read.yaml"), "live": True,
            "max_rounds": request.max_rounds, "compute_budget": request.compute_budget,
            "swarm_type": request.swarm_type.value, "carrier_context": request.carrier_context,
            "ablation_flags": request.ablation_flags, "request_external_admission": request.request_external_admission,
            "instruction_plan": transport, "instruction_admission": admission, "inherit_environment": False,
        }
        if extra_count:
            encoded = _runtime_request_bytes("woland_bout", payload).unwrap()
            assert 65536 < len(encoded) < 1048576

        def native_refusal():
            envelope = RustSymbolGameHost().invoke_runtime("woland_bout", payload).unwrap()
            assert envelope["success"] is True
            return envelope["result"]["refusal"]

        healthy = native_refusal()
        assert healthy["code"] == "WOLAND_REQUEST_INVALID" and "live execution settings" in healthy["message"]
        # This fixture decision is genuinely signed again, so the missing optional
        # projection must be caught by its consumer rather than a stale signature.
        admission["plan_material"].pop("projection")
        transport["plan_digest"] = "sha256:" + hashlib.sha256(json.dumps(
            admission["plan_material"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()).hexdigest()
        manifest = json.loads(ingress.manifest_path.read_bytes())
        manifest["plan_digest"] = transport["plan_digest"]
        raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
        ingress.manifest_path.write_bytes(raw)
        transport["manifest_digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        ingress.signature_path.unlink()
        subprocess.run([ingress.ssh_keygen, "-Y", "sign", "-f", str(tmp_path / "fixture_key"),
                        "-n", "oewas-woland-instruction-v0.1", str(ingress.manifest_path)],
                       check=True, capture_output=True)
        refusal = native_refusal()
        assert refusal["code"] == "NATIVE_INSTRUCTION_ADMISSION_INVALID"
        assert not (root / "_ic").exists() and not (tmp_path / "never-written.jsonl").exists()
    finally:
        container.uow.close()
