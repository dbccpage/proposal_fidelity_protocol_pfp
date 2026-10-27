"""One source-to-contract experiment through existing selection/admission ports.

The context is a literal, independently chosen ordered Adversary claim-audit
signature. This is not automatic extraction of a paper's intended semantics.
The temporary key demonstrates signature checking without installing trust.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from ...application.adversary_candidate_plan import PlanNodeV01
from ...application.adversary_instruction_admission import (
    InstructionAdmissionRefusal,
    SIGNATURE_NAMESPACE,
    source_snapshot_digest,
    verify_signed_instruction_admission,
)
from ...application.adversary_task_selection import (
    AdversaryCandidateRouteV01,
    AdversaryTaskShapeV01,
    select_candidate_plan,
)
from ...domain.entities.operation_v3 import PortSpecV3
from ...domain.value_objects.content_digest import ContentDigest
from ...domain.value_objects.identifier import ColourId, SchemaRef
from ...infrastructure.typed_contract_compiler import compile_typed_contracts


SOURCE = "operads/catalog/contracts/v1/adversary_claim_audit.json"
SOURCE_SHA256 = "dc4a3787a2947e20a9f020c43c857ccbc21afd577e2bf1b590367d8ac4eca0a4"
VALIDATOR_SHA256 = "1636ead64509ccee21b79700bcf30ad7b755fcaf38525a2b6ca5fed7e81b804d"
PROFILE = b"Adversary claim audit: ordered findings then original subject; Receipt output. v1\n"


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _port(name: str, colour: str, wire: str, schema_sha256: str) -> PortSpecV3:
    return PortSpecV3(
        name, ColourId(colour), SchemaRef(f"schema:oewas:{wire}:v1"),
        ContentDigest.sha256(schema_sha256), f"oewas:{wire}:v1",
        ContentDigest.sha256(VALIDATOR_SHA256),
    )


def prepare_context(repo_root: Path):
    """Read actual retained bytes; supply literal context, not constructor arity."""
    if _digest((repo_root / SOURCE).read_bytes()) != "sha256:" + SOURCE_SHA256:
        raise ValueError("RETAINED_SOURCE_CHANGED: review a new experiment revision")
    package = compile_typed_contracts(repo_root)
    documents = tuple(doc for doc in package.documents if doc.source_relative_path == SOURCE)
    task = AdversaryTaskShapeV01(
        request_digest=_digest(b"Audit the supplied candidate against its declared evidence scope.\n"),
        workload_profile_id="adversary.claim-audit.source-contract-v1",
        workload_profile_digest=_digest(PROFILE), domain_id="claim-hygiene",
        inputs=(
            _port("findings", "Audit", "anti_skill_hits",
                  "7674dfd6302aba3fd48759ebdacc448fbf0d884af8b4edba4237ab93d675500d"),
            _port("subject", "Contract", "anti_skill_subject",
                  "19346dd4448f3bd41bacaf9b486d8ec14854769a6e84e9a9c253dbf86071623f"),
        ),
        output=_port("receipt", "Receipt", "typed_audit_receipt",
                     "6c495f0160af63a2cd04ca761b390b973c5bc4e9a2a9bbd386ab83610bd99347"),
        required_operation_ids=frozenset({"adversary-claim-audit"}),
        allowed_effects=frozenset({"read_subject", "emit_finding"}),
        max_nodes=1, max_instruction_bytes=4096,
    )
    return task, AdversaryCandidateRouteV01(
        "route.claim-audit.source-contract-v1", task.workload_profile_id,
        task.workload_profile_digest, task.domain_id, documents,
        PlanNodeV01("adversary-claim-audit"),
    )


def sign_fixture_manifest(work_dir: Path, task, selected):
    """Create one temporary fixture trust root, never a production admission."""
    executable = shutil.which("ssh-keygen")
    if executable is None:
        raise RuntimeError("SIGNATURE_VERIFIER_UNAVAILABLE")
    work_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "oewas.adversary.instruction_admission.v0.1",
        "decision": "APPROVE", "reviewer_identity": "fixture.source-contract",
        "authority_effect": "None", "request_digest": task.request_digest,
        "task_shape_digest": selected.task_shape_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest, "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest, "route_id": selected.route_id,
        "plan_digest": selected.plan.plan_digest,
        "source_snapshot_digest": source_snapshot_digest(selected),
    }
    raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
           + "\n").encode("ascii")
    manifest_path = work_dir / "manifest.json"
    manifest_path.write_bytes(raw)
    key = work_dir / "fixture-key"
    subprocess.run(
        [executable, "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
        capture_output=True, check=True, timeout=10,
    )
    subprocess.run(
        [executable, "-Y", "sign", "-f", str(key), "-n", SIGNATURE_NAMESPACE,
         str(manifest_path)], capture_output=True, check=True, timeout=10,
    )
    signers = work_dir / "allowed-signers"
    signers.write_text("fixture.source-contract " + key.with_suffix(".pub").read_text("ascii"),
                       encoding="ascii")
    return raw, {
        "signature_path": manifest_path.with_suffix(".json.sig"),
        "allowed_signers_path": signers, "ssh_keygen": executable,
    }


def run_experiment(repo_root: Path, work_dir: Path) -> dict:
    task, route = prepare_context(repo_root)
    selected = select_candidate_plan(task, (route,))
    raw, paths = sign_fixture_manifest(work_dir, task, selected)
    arguments = dict(paths, task=task, selected=selected, request_digest=task.request_digest)
    verified = verify_signed_instruction_admission(raw, **arguments)
    document = route.documents[0]
    foreign_source = replace(document, raw_digest=ContentDigest.sha256("f" * 64))
    foreign_candidate = replace(document, operands=(replace(
        document.operands[0], instruction_body="Audit a different candidate."
    ),))
    controls = {
        "swapped": {"task": replace(task, inputs=tuple(reversed(task.inputs)))},
        "omitted": {"task": replace(task, inputs=task.inputs[:1])},
        "foreign-source": {"selected": select_candidate_plan(task, (
            replace(route, documents=(foreign_source,)),
        ))},
        "foreign-candidate": {"selected": select_candidate_plan(task, (
            replace(route, documents=(foreign_candidate,)),
        ))},
    }
    outcomes = {}
    for name, changed in controls.items():
        try:
            verify_signed_instruction_admission(raw, **{**arguments, **changed})
        except InstructionAdmissionRefusal as error:
            outcomes[name] = error.code
        else:
            raise RuntimeError(f"CONTROL_FAILED: {name} was admitted")
    return {
        "schema": "oewas.source-contract.experiment.v1", "source": SOURCE,
        "source_sha256": SOURCE_SHA256, "plan_digest": verified.plan_digest,
        "task_shape_digest": selected.task_shape_digest,
        "ordered_context": ["findings:Audit", "subject:Contract"], "output": "receipt:Receipt",
        "control": "VERIFIED_FIXTURE_SIGNATURE", "negative_controls": outcomes,
        "authority_effect": "None", "installed_admission": False,
        "interpretation": "Finite source/context custody experiment; no automatic paper interpretation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="source-contract-", dir=args.output.parent) as temporary:
        result = run_experiment(args.repo_root, Path(temporary))
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
