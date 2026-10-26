"""Woland candidate plans are ordered, source-bound, and never self-admitted."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from omega_engine_operads.application.woland_candidate_plan import (
    PlanNodeV01,
    PlanRefusal,
    compile_candidate_plan,
)
from omega_engine_operads.application.woland_instruction_admission import (
    InstructionAdmissionRefusal,
    instruction_plan_transport,
    ordered_bodies_digest,
    source_snapshot_digest,
    verify_signed_instruction_admission,
)
from omega_engine_operads.application.woland_task_selection import (
    WolandCandidateRouteV01,
    WolandTaskShapeV01,
    select_candidate_plan,
)
from omega_engine_operads.domain.value_objects.identifier import SkillId
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
)
from omega_engine_operads.infrastructure.fs.woland_operand_source import (
    read_woland_operand_sources,
)
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


def _port(colour: str) -> dict:
    return {
        "name": colour.lower(),
        "colour_id": colour,
        "schema_ref": f"schema:{colour.lower()}:v1",
        "schema_digest": "a" * 64,
        "validator_ref": f"validator:{colour.lower()}:v1",
        "validator_digest": "b" * 64,
    }


def _raw_document(name: str, inputs: tuple[str, ...], output: str, *,
                  body: str = "Do the check.", validated: bool = True,
                  effects: tuple[str, ...] = (), tool_refs: tuple[str, ...] = ()) -> bytes:
    operand = {"operand_id": f"{name}.clause", "kind": "instruction", "body": body}
    operation = {
        "operation_id": name,
        "declaration": "Declared",
        "schema_binding": "Bound",
        "executor_binding": "Bound",
        "validation": "Validated" if validated else "Unchecked",
        "admission": "Admitted",  # A source assertion must be demoted by the parser.
        "schema_digest": "c" * 64,
        "executor_digest": "d" * 64,
        "inputs": [_port(colour) for colour in inputs],
        "output": _port(output),
        "operand_refs": [f"{name}.clause"],
        "effects": list(effects),
        "tool_refs": list(tool_refs),
    }
    return (
        "```oewas.operand.v3\n" + yaml.safe_dump(operand, sort_keys=True)
        + "```\n\n```oewas.operation.v3\n"
        + yaml.safe_dump(operation, sort_keys=True) + "```\n"
    ).encode("utf-8")


def _document(name: str, inputs: tuple[str, ...], output: str, *, body: str = "Do the check.",
              validated: bool = True, effects: tuple[str, ...] = (),
              tool_refs: tuple[str, ...] = ()):
    raw = _raw_document(
        name, inputs, output, body=body, validated=validated,
        effects=effects, tool_refs=tool_refs,
    )
    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId(name),
        f"omega_engine_operads/catalog/operands/v1/test/{name}.md",
        raw,
    )
    assert result.is_ok
    return result.unwrap()


def _fixture():
    root = _document("root", ("Audit", "Contract"), "Receipt", body="Seal only checker evidence.")
    left = _document("left", ("Code",), "Audit", body="Audit the code.")
    right = _document("right", ("Paper",), "Contract", body="Read the contract.")
    return root, left, right


def test_ordered_composition_has_exact_boundary_and_no_admission() -> None:
    docs = _fixture()
    left = PlanNodeV01("left")
    right = PlanNodeV01("right")
    plan = compile_candidate_plan(docs, PlanNodeV01("root", ((1, right), (0, left))))
    assert tuple(str(port.colour_id) for port in plan.inputs) == ("Code", "Paper")
    assert str(plan.output.colour_id) == "Receipt"
    assert plan.ordered_operand_bodies == (
        "Audit the code.", "Read the contract.", "Seal only checker evidence."
    )
    assert plan.admission == "Unadmitted"
    assert plan.operation_count == 3
    assert plan.operation_ids == ("left", "right", "root")
    assert plan.effects == plan.tool_refs == ()
    assert plan.instruction_bytes == sum(
        len(body.encode("utf-8")) for body in plan.ordered_operand_bodies
    )
    assert plan.plan_digest.startswith("sha256:")
    reordered = compile_candidate_plan(docs, PlanNodeV01("root", ((0, left), (1, right))))
    assert plan.plan_digest == reordered.plan_digest


def test_retired_operation_is_not_reintroduced_as_an_unadmitted_candidate():
    doc = _document("item", ("Code",), "Audit")
    operation = doc.operations[0]
    retired = replace(
        doc, operations=(replace(
            operation, lifecycle=replace(operation.lifecycle, admission=AdmissionFacet.RETIRED),
        ),),
    )
    with pytest.raises(PlanRefusal) as refused:
        compile_candidate_plan((retired,), PlanNodeV01("item"))
    assert refused.value.code == "OPERATION_RETIRED"
    restored = compile_candidate_plan((doc,), PlanNodeV01("item"))
    assert restored.admission == "Unadmitted"
    assert restored.operation_ids == ("item",)


def test_wrong_colour_refuses_instead_of_coercing() -> None:
    root, _, right = _fixture()
    wrong = _document("left", ("Code",), "Paper")
    with pytest.raises(PlanRefusal, match="BOUNDARY_MISMATCH"):
        compile_candidate_plan(
            (root, wrong, right),
            PlanNodeV01("root", ((0, PlanNodeV01("left")), (1, PlanNodeV01("right")))),
        )


def test_source_change_changes_plan_digest() -> None:
    root, left, right = _fixture()
    tree = PlanNodeV01("root", ((0, PlanNodeV01("left")), (1, PlanNodeV01("right"))))
    first = compile_candidate_plan((root, left, right), tree)
    edited = _document("left", ("Code",), "Audit", body="Audit different bytes.")
    second = compile_candidate_plan((root, edited, right), tree)
    assert first.plan_digest != second.plan_digest


def test_nested_ordered_substitution_preserves_external_inputs() -> None:
    root, left, right = _fixture()
    inner = _document("inner", ("Paper",), "Code", body="Extract code from paper.")
    tree = PlanNodeV01(
        "root",
        ((0, PlanNodeV01("left", ((0, PlanNodeV01("inner")),))),
         (1, PlanNodeV01("right"))),
    )
    plan = compile_candidate_plan((root, left, right, inner), tree)
    assert tuple(str(port.colour_id) for port in plan.inputs) == ("Paper", "Paper")
    assert plan.ordered_operand_bodies == (
        "Extract code from paper.", "Audit the code.",
        "Read the contract.", "Seal only checker evidence.",
    )


def test_unbound_operation_and_unused_source_refuse() -> None:
    root, left, right = _fixture()
    unchecked = _document("left", ("Code",), "Audit", validated=False)
    with pytest.raises(PlanRefusal, match="OPERATION_UNBOUND"):
        compile_candidate_plan((root, unchecked, right), PlanNodeV01("root"))
    with pytest.raises(PlanRefusal, match="UNUSED_SOURCE"):
        compile_candidate_plan((root, left, right), PlanNodeV01("root"))


def test_duplicate_operation_source_refuses() -> None:
    root, left, _ = _fixture()
    with pytest.raises(PlanRefusal, match="DUPLICATE_SOURCE_ID"):
        compile_candidate_plan((root, left, left), PlanNodeV01("root"))


def test_cyclic_and_overdeep_terms_refuse_before_execution() -> None:
    root, _, _ = _fixture()
    cyclic = PlanNodeV01("root")
    object.__setattr__(cyclic, "children", ((0, cyclic),))
    with pytest.raises(PlanRefusal, match="COMPOSITION_CYCLE"):
        compile_candidate_plan((root,), cyclic)
    chain = PlanNodeV01("root")
    for _ in range(18):
        chain = PlanNodeV01("root", ((0, chain),))
    with pytest.raises(PlanRefusal, match="COMPOSITION_BUDGET_EXCEEDED"):
        compile_candidate_plan((root,), chain)


def test_catalog_reader_binds_exact_file_and_refuses_escape(tmp_path) -> None:
    catalog = tmp_path / "omega_engine_operads" / "catalog" / "operands" / "v1" / "test"
    catalog.mkdir(parents=True)
    (catalog / "item.md").write_bytes(_raw_document("test.item", ("Code",), "Audit"))
    docs = read_woland_operand_sources(tmp_path, ("test/item.md",))
    assert len(docs) == 1
    assert docs[0].source_relative_path.endswith("catalog/operands/v1/test/item.md")
    assert compile_candidate_plan(docs, PlanNodeV01("test.item")).admission == "Unadmitted"
    with pytest.raises(PlanRefusal, match="SOURCE_PATH_INVALID"):
        read_woland_operand_sources(tmp_path, ("../item.md",))
    with pytest.raises(PlanRefusal, match="SOURCE_UNAVAILABLE"):
        read_woland_operand_sources(tmp_path, ("test/missing.md",))


def test_checked_in_operand_specimen_is_unbound_source_only() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    docs = read_woland_operand_sources(repo_root, ("woland/claim_hygiene.md",))
    assert str(docs[0].operations[0].operation_id) == "woland.claim_hygiene"
    with pytest.raises(PlanRefusal, match="OPERATION_UNBOUND"):
        compile_candidate_plan(docs, PlanNodeV01("woland.claim_hygiene"))


def _task_for(plan, *, domain: str = "coding", profile: str = "woland.research", **limits):
    return WolandTaskShapeV01(
        request_digest="sha256:" + "e" * 64,
        workload_profile_id=profile,
        workload_profile_digest="sha256:" + "c" * 64,
        domain_id=domain,
        inputs=plan.inputs,
        output=plan.output,
        **limits,
    )


def _route(route_id, documents, root, *, domain="coding", profile="woland.research",
           profile_digest="sha256:" + "c" * 64):
    return WolandCandidateRouteV01(
        route_id, profile, profile_digest, domain, documents, root
    )


def test_task_selection_chooses_unique_least_node_plan_independent_of_route_order() -> None:
    root, left, right = _fixture()
    composite_tree = PlanNodeV01(
        "root", ((0, PlanNodeV01("left")), (1, PlanNodeV01("right")))
    )
    composite = compile_candidate_plan((root, left, right), composite_tree)
    direct = _document("direct", ("Code", "Paper"), "Receipt")
    routes = (
        _route("route.composite", (root, left, right), composite_tree),
        _route("route.direct", (direct,), PlanNodeV01("direct")),
    )
    task = _task_for(composite)
    selected = select_candidate_plan(task, routes)
    reordered = select_candidate_plan(task, tuple(reversed(routes)))
    assert selected.route_id == "route.direct"
    assert selected.plan.operation_count == 1
    assert selected.admission == selected.plan.admission == "Unadmitted"
    assert selected.selection_digest == reordered.selection_digest
    assert selected.applicable_routes == reordered.applicable_routes
    assert selected.considered_routes == reordered.considered_routes
    changed_request = replace(task, request_digest="sha256:" + "f" * 64)
    assert (
        select_candidate_plan(changed_request, routes).selection_digest
        != selected.selection_digest
    )
    guarded_task = replace(task, required_operation_ids=frozenset({"left"}))
    guarded = select_candidate_plan(guarded_task, routes)
    assert guarded.route_id == "route.composite"
    assert guarded.selection_digest != selected.selection_digest
    with pytest.raises(PlanRefusal, match="NO_APPLICABLE_PLAN"):
        select_candidate_plan(guarded_task, (routes[1],))


def test_task_selection_refuses_equal_minima_and_duplicate_route_ids() -> None:
    first = _document("first", ("Code",), "Audit", body="First.")
    second = _document("second", ("Code",), "Audit", body="Second.")
    task = _task_for(compile_candidate_plan((first,), PlanNodeV01("first")))
    routes = (
        _route("route.first", (first,), PlanNodeV01("first")),
        _route("route.second", (second,), PlanNodeV01("second")),
    )
    with pytest.raises(PlanRefusal, match="AMBIGUOUS_APPLICABILITY"):
        select_candidate_plan(task, routes)
    with pytest.raises(PlanRefusal, match="DUPLICATE_ROUTE_ID"):
        select_candidate_plan(task, (routes[0], routes[0]))


def test_task_selection_matches_exact_profile_domain_and_port_contract() -> None:
    first = _document("first", ("Code",), "Audit")
    plan = compile_candidate_plan((first,), PlanNodeV01("first"))
    task = _task_for(plan)
    wrong_profile = _route(
        "route.profile", (first,), PlanNodeV01("first"), profile="woland.council"
    )
    wrong_domain = _route(
        "route.domain", (first,), PlanNodeV01("first"), domain="paper"
    )
    wrong_profile_digest = _route(
        "route.profile_digest", (first,), PlanNodeV01("first"),
        profile_digest="sha256:" + "d" * 64,
    )
    wrong_output = _document("wrong", ("Code",), "Receipt")
    wrong_colour = _route("route.colour", (wrong_output,), PlanNodeV01("wrong"))
    with pytest.raises(PlanRefusal, match="NO_APPLICABLE_PLAN"):
        select_candidate_plan(
            task, (wrong_profile, wrong_profile_digest, wrong_domain, wrong_colour)
        )
    assert select_candidate_plan(
        task, (wrong_profile, _route("route.exact", (first,), PlanNodeV01("first")))
    ).route_id == "route.exact"
    exact = _route("route.exact", (first,), PlanNodeV01("first"))
    before = select_candidate_plan(task, (wrong_colour, exact))
    changed_wrong = _document("wrong", ("Code",), "Receipt", body="Different source.")
    after = select_candidate_plan(
        task, (_route("route.colour", (changed_wrong,), PlanNodeV01("wrong")), exact)
    )
    assert before.route_id == after.route_id == "route.exact"
    assert before.selection_digest != after.selection_digest


def test_candidate_plan_never_widens_effect_tool_or_resource_ceiling() -> None:
    effectful = _document(
        "effectful", ("Code",), "Audit", body="Read exact bytes.",
        effects=("filesystem.read",), tool_refs=("tool:rg",),
    )
    tree = PlanNodeV01("effectful")
    with pytest.raises(PlanRefusal, match="EFFECT_NOT_LICENSED"):
        compile_candidate_plan((effectful,), tree)
    with pytest.raises(PlanRefusal, match="TOOL_NOT_LICENSED"):
        compile_candidate_plan((effectful,), tree, allowed_effects=frozenset({"filesystem.read"}))
    allowed = compile_candidate_plan(
        (effectful,), tree,
        allowed_effects=frozenset({"filesystem.read"}),
        allowed_tool_refs=frozenset({"tool:rg"}),
    )
    assert allowed.effects == ("filesystem.read",)
    assert allowed.tool_refs == ("tool:rg",)
    with pytest.raises(PlanRefusal, match="INSTRUCTION_BUDGET_EXCEEDED"):
        compile_candidate_plan(
            (effectful,), tree,
            allowed_effects=frozenset({"filesystem.read"}),
            allowed_tool_refs=frozenset({"tool:rg"}), max_instruction_bytes=5,
        )
    with pytest.raises(PlanRefusal, match="PLAN_CEILING_INVALID"):
        compile_candidate_plan((effectful,), tree, max_nodes=0)


def test_matching_unbound_route_cannot_be_skipped_for_a_valid_route() -> None:
    valid = _document("valid", ("Code",), "Audit")
    unbound = _document("unbound", ("Code",), "Audit", validated=False)
    task = _task_for(compile_candidate_plan((valid,), PlanNodeV01("valid")))
    routes = (
        _route("route.valid", (valid,), PlanNodeV01("valid")),
        _route("route.unbound", (unbound,), PlanNodeV01("unbound")),
    )
    with pytest.raises(PlanRefusal, match="OPERATION_UNBOUND"):
        select_candidate_plan(task, routes)


def test_human_manifest_signature_binds_exact_selection_and_separate_trust_root(tmp_path) -> None:
    ssh = shutil.which("ssh-keygen")
    if ssh is None:
        pytest.skip("OpenSSH signature verifier unavailable")
    doc = _document("admitted_test", ("Code",), "Audit")
    plan = compile_candidate_plan((doc,), PlanNodeV01("admitted_test"))
    task = _task_for(plan)
    route = _route("route.admitted_test", (doc,), PlanNodeV01("admitted_test"))
    selected = select_candidate_plan(task, (route,))
    manifest = {
        "schema_version": "oewas.woland.instruction_admission.v0.1",
        "decision": "APPROVE",
        "reviewer_identity": "human.test",
        "authority_effect": "None",
        "request_digest": task.request_digest,
        "task_shape_digest": selected.task_shape_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest,
        "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest,
        "route_id": selected.route_id,
        "plan_digest": selected.plan.plan_digest,
        "source_snapshot_digest": source_snapshot_digest(selected),
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=True) + "\n").encode("ascii")
    manifest_path = tmp_path / "instruction_admission.json"
    manifest_path.write_bytes(manifest_bytes)
    key_path = tmp_path / "human_key"
    subprocess.run(
        [ssh, "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
        capture_output=True, check=True, timeout=10,
    )
    subprocess.run(
        [ssh, "-Y", "sign", "-f", str(key_path),
         "-n", "oewas-woland-instruction-v0.1", str(manifest_path)],
        capture_output=True, check=True, timeout=10,
    )
    signature_path = tmp_path / "instruction_admission.json.sig"
    trusted_signers = tmp_path / "allowed_signers"
    trusted_signers.write_text(
        "human.test " + (tmp_path / "human_key.pub").read_text(encoding="ascii"),
        encoding="ascii",
    )
    kwargs = dict(
        signature_path=signature_path, allowed_signers_path=trusted_signers,
        selected=selected, task=task, request_digest=task.request_digest,
        ssh_keygen=ssh,
    )
    verified = verify_signed_instruction_admission(manifest_bytes, **kwargs)
    assert verified.plan_digest == plan.plan_digest
    assert verified.source_snapshot_digest == source_snapshot_digest(selected)
    assert verified.ordered_operand_bodies == plan.ordered_operand_bodies
    assert verified.source_digests == plan.source_digests
    assert verified.operation_ids == plan.operation_ids
    assert verified.instruction_bytes == plan.instruction_bytes
    assert verified.ordered_bodies_digest == ordered_bodies_digest(plan.ordered_operand_bodies)
    transported = instruction_plan_transport(verified)
    assert transported["ordered_operand_bodies"] == list(plan.ordered_operand_bodies)
    assert transported["source_digests"] == [list(row) for row in plan.source_digests]
    assert transported["authority_effect"] == "None"
    assert verified.authority_effect == "None"
    assert selected.admission == "Unadmitted"  # verification never mutates the candidate

    with pytest.raises(InstructionAdmissionRefusal, match="REQUEST_MISMATCH"):
        verify_signed_instruction_admission(
            manifest_bytes, **{**kwargs, "request_digest": "sha256:" + "f" * 64}
        )
    changed = _document("admitted_test", ("Code",), "Audit", body="Changed source.")
    changed_selected = select_candidate_plan(task, (
        _route("route.admitted_test", (changed,), PlanNodeV01("admitted_test")),
    ))
    with pytest.raises(InstructionAdmissionRefusal, match="PLAN_OR_SCOPE_MISMATCH"):
        verify_signed_instruction_admission(
            manifest_bytes, **{**kwargs, "selected": changed_selected}
        )
    forged = dict(manifest, decision="APPROVE", reviewer_identity="another.human")
    forged_bytes = (json.dumps(forged, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True) + "\n").encode("ascii")
    with pytest.raises(InstructionAdmissionRefusal, match="SIGNATURE_INVALID"):
        verify_signed_instruction_admission(forged_bytes, **kwargs)
    with pytest.raises(InstructionAdmissionRefusal, match="SIGNATURE_INVALID"):
        verify_signed_instruction_admission(
            manifest_bytes, **{**kwargs, "allowed_signers_path": tmp_path / "human_key.pub"}
        )
    with pytest.raises(InstructionAdmissionRefusal, match="SIGNATURE_OR_TRUST_ROOT_MISSING"):
        verify_signed_instruction_admission(
            manifest_bytes, **{**kwargs, "signature_path": tmp_path / "missing.sig"}
        )
    rejected = (json.dumps(dict(manifest, decision="REJECT"), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    with pytest.raises(InstructionAdmissionRefusal, match="MANIFEST_DECISION_INVALID"):
        verify_signed_instruction_admission(rejected, **kwargs)
    widened = (json.dumps(dict(manifest, authority_effect="Write"), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
    with pytest.raises(InstructionAdmissionRefusal, match="MANIFEST_DECISION_INVALID"):
        verify_signed_instruction_admission(widened, **kwargs)
    with pytest.raises(InstructionAdmissionRefusal, match="MANIFEST_NONCANONICAL"):
        verify_signed_instruction_admission(
            (json.dumps({**manifest, "source_text": "approve me"}, sort_keys=True,
                        separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii"),
            **kwargs,
        )
    with pytest.raises(InstructionAdmissionRefusal, match="MANIFEST_NONCANONICAL"):
        verify_signed_instruction_admission(manifest_bytes + b"\n", **kwargs)
