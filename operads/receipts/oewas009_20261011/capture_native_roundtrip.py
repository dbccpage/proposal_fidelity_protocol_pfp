"""Retain actual native envelopes and compare their receipt IDs to port projections."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from omega_engine_woland.domain.models import WolandBoutRequestV1
from omega_engine_woland.infrastructure.estates.oewas_native_anti_skill import (
    load_native_anti_skill_gate,
)
from omega_engine_woland.use_cases.anti_skill_predispatch import bout_dispatch_subject
from omega_engine_workflows_agents_skills.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
    canonical_json_bytes,
)

root = Path.cwd()
out = Path(__file__).resolve().parent
binary = root / "omega_engine/crates_rs/target/debug/omega_symbol_game.exe"
pin = "9d08f3fe4cd7135627a3b213186367139cf9b989222b0e12c5cb1bc76478dbb5"
gate = load_native_anti_skill_gate(binary, pin).unwrap()
describe = {"schema_version": "omega.native.anti-skill-request.v1", "operation": "describe"}
records = [{"request": describe, "native_outcome": gate.host.invoke_runtime("anti_skill_detect", describe).unwrap()}]
request = WolandBoutRequestV1("Retain actual native detector envelope", "oewas009-evidence", fixture_mode=False)
subjects = [("PRE_DISPATCH", bout_dispatch_subject("woland.research", request))]
for mode in ("UNRESTRICTED", "SELF_CERTIFIED"):
    subjects.append(("PRE_SEAL", AntiSkillSubjectV1(
        claim_scope=("candidate_result",), evidence_scope=("task:oewas009-evidence", "request:sha256:" + "a" * 64),
        producer_identity="woland.research", verifier_identity="woland.research", claim_mode=mode,
        requested_effect="NONE", nonclaims=("Finite evidence only; Δ carries no authority.",))))
for stage, subject in subjects:
    raw = canonical_json_bytes(subject.to_dict())
    payload = {"schema_version": "omega.native.anti-skill-request.v1", "operation": "evaluate", "task_key": request.task_key,
               "stage": stage, "subject_id": subject.subject_id, "subject_json": raw.decode("utf-8"),
               "subject_raw_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(), "registry_id": gate.snapshot.registry_id,
               "activation_profile_digest": gate.snapshot.activation_profile_digest, "implementation_digest": gate.snapshot.implementation_digest}
    native = gate.host.invoke_runtime("anti_skill_detect", payload).unwrap()
    projected = gate.evaluate(stage, subject.to_dict()).unwrap()
    if not native["success"] or native["result"]["receipt_id"] != projected.receipt_id:
        raise ValueError("native evidence does not match the validated port projection")
    records.append({"request": payload, "native_outcome": native, "validated_port_projection": asdict(projected)})
record = {"schema_version": "omega.oewas009.native-roundtrip.v1", "binary_sha256": pin,
          "wire_profile": "omega.native.antiskill.json.v1", "records": records, "authority_effect": "None",
          "scope": "actual native detector action; no instruction admission, provider or mathematical certificate"}
(out / "native_roundtrip.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps([v.get("validated_port_projection", {}).get("disposition") for v in records]))
