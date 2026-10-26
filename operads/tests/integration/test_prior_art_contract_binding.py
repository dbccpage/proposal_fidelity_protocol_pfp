"""Retained Woland source, independent contextual interface and real admission.

These finite controls do not interpret PICARD or certify a paper's semantics.
The ephemeral SSH key is a local fixture, never an installed governance key.
"""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from omega_engine_operads.application.woland_candidate_plan import (
    PlanRefusal,
)
from omega_engine_operads.application.woland_instruction_admission import (
    InstructionAdmissionRefusal,
    verify_signed_instruction_admission,
)
from omega_engine_operads.application.woland_task_selection import (
    select_candidate_plan,
)
from omega_engine_operads.documentation.examples.prior_art_contract_binding import (
    prepare_context,
    sign_fixture_manifest,
)


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def context():
    return prepare_context(ROOT)


@pytest.fixture(scope="module")
def signed(context, tmp_path_factory):
    task, route = context
    return sign_fixture_manifest(
        tmp_path_factory.mktemp("source-contract-signature"),
        task,
        select_candidate_plan(task, (route,)),
    )


def test_literal_retained_source_context_is_selected_and_real_signature_verifies(context, signed):
    task, route = context
    selected = select_candidate_plan(task, (route,))
    assert [(port.name, str(port.colour_id)) for port in task.inputs] == [
        ("findings", "Audit"), ("subject", "Contract")
    ]
    assert selected.plan.plan_digest == (
        "sha256:b9d3d00f2077707e5aa217da492dcec7db5ff8782275c67f5deceb36641940d0"
    )
    manifest, paths = signed
    verified = verify_signed_instruction_admission(
        manifest, **paths, task=task, selected=selected, request_digest=task.request_digest
    )
    assert verified.plan_digest == selected.plan.plan_digest
    assert verified.source_digests == selected.plan.source_digests
    assert verified.authority_effect == "None"
    assert selected.admission == selected.plan.admission == "Unadmitted"


@pytest.mark.parametrize("mutation", ["swapped", "omitted", "foreign-schema"])
def test_selection_rejects_contextual_order_arity_and_schema(context, mutation):
    task, route = context
    inputs = task.inputs
    if mutation == "swapped":
        inputs = tuple(reversed(inputs))
    elif mutation == "omitted":
        inputs = inputs[:1]
    else:
        inputs = (replace(inputs[0], schema_ref=inputs[1].schema_ref), inputs[1])
    with pytest.raises(PlanRefusal, match="NO_APPLICABLE_PLAN"):
        select_candidate_plan(replace(task, inputs=inputs), (route,))


@pytest.mark.parametrize("mutation", ["swapped", "omitted", "output", "effect-ceiling"])
def test_signed_admission_rechecks_the_supplied_context_not_a_stale_selection(
    context, signed, mutation
):
    task, route = context
    selected = select_candidate_plan(task, (route,))
    changed = {
        "swapped": replace(task, inputs=tuple(reversed(task.inputs))),
        "omitted": replace(task, inputs=task.inputs[:1]),
        "output": replace(task, output=task.inputs[0]),
        "effect-ceiling": replace(task, allowed_effects=frozenset()),
    }[mutation]
    manifest, paths = signed
    with pytest.raises(InstructionAdmissionRefusal, match="PLAN_OR_SCOPE_MISMATCH"):
        verify_signed_instruction_admission(
            manifest, **paths, task=changed, selected=selected,
            request_digest=task.request_digest,
        )


@pytest.mark.parametrize("mutation", ["source", "candidate"])
def test_signed_admission_rejects_a_fresh_foreign_source_or_candidate(context, signed, mutation):
    task, route = context
    document = route.documents[0]
    if mutation == "source":
        digest = type(document.raw_digest).sha256(hashlib.sha256(b"foreign source").hexdigest())
        document = replace(document, raw_digest=digest)
    else:
        document = replace(document, operands=(replace(
            document.operands[0], instruction_body="Audit a different candidate."
        ),))
    selected = select_candidate_plan(task, (replace(route, documents=(document,)),))
    manifest, paths = signed
    with pytest.raises(InstructionAdmissionRefusal, match="PLAN_OR_SCOPE_MISMATCH"):
        verify_signed_instruction_admission(
            manifest, **paths, task=task, selected=selected, request_digest=task.request_digest
        )


def test_example_runs_without_changing_retained_source(tmp_path):
    module = "omega_engine_operads.documentation.examples.prior_art_contract_binding"
    import sys

    source = ROOT / (
        "omega_engine_operads/catalog/contracts/v1/woland_claim_audit.json"
    )
    before = source.read_bytes()
    result = subprocess.run(
        [sys.executable, "-B", "-m", module, "--repo-root", str(ROOT),
         "--output", str(tmp_path / "experiment.json")],
        capture_output=True, text=True, check=True, timeout=30,
    )
    report = json.loads(result.stdout)
    assert report["control"] == "VERIFIED_FIXTURE_SIGNATURE"
    assert report["negative_controls"] == {
        "swapped": "PLAN_OR_SCOPE_MISMATCH", "omitted": "PLAN_OR_SCOPE_MISMATCH",
        "foreign-source": "PLAN_OR_SCOPE_MISMATCH",
        "foreign-candidate": "PLAN_OR_SCOPE_MISMATCH",
    }
    assert report["authority_effect"] == "None"
    assert source.read_bytes() == before
