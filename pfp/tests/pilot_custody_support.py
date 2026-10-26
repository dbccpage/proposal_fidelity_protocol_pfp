"""Historical dossier custody checks, without reissuing an old checker verdict."""
from hashlib import sha256
import json
from pathlib import Path

import yaml


def check_historical_dossier_capsule(folder: Path) -> None:
    response=yaml.safe_load((folder/"response.yaml").read_text(encoding="utf-8"))
    spec=yaml.safe_load((folder/"test_spec.yaml").read_text(encoding="utf-8"))
    assert response["schema"]=="pfp.dossier-response.v1"
    assert response["authority_effect"]=="None"
    assert response["status"] in {"HOST_ACCEPTED","TYPED_REFUSAL"}
    for name,field in (("input.yaml","input_sha256"),("request.json","request_sha256"),
                       ("provider_response.json","provider_response_sha256")):
        assert sha256((folder/name).read_bytes()).hexdigest()==response[field], (folder,field)
    raw=json.loads((folder/"provider_response.json").read_bytes())
    assert raw["id"]==response["generation_id"]
    assert raw["usage"]==response["usage"]
    assert spec["schema"]=="pfp.test-spec.v1" and spec["authority_effect"]=="None"
    assert spec["response_file"]=="response.yaml" and spec["input_source_file"]=="input.yaml"
    assert spec["actual_outcome"]["status"]==response["status"]
    assert spec["actual_outcome"]["gate_status"]==response["status"]
    if response["status"]=="TYPED_REFUSAL":
        assert spec["actual_outcome"]["refusal_code"]==response["code"]


def is_historical_dossier(folder: Path) -> bool:
    response_path=folder/"response.yaml"
    if not response_path.is_file():
        failure_path=folder/"infrastructure_failure.yaml"
        if not failure_path.is_file():
            return False
        failure=yaml.safe_load(failure_path.read_text(encoding="utf-8"))
        spec=yaml.safe_load((folder/"test_spec.yaml").read_text(encoding="utf-8"))
        reservation=yaml.safe_load((folder/"reservation.yaml").read_text(encoding="utf-8"))
        assert failure["status"]=="INFRASTRUCTURE_ERROR" and failure["authority_effect"]=="None"
        assert failure["paid_retry_locked"] is True
        assert failure["cost_usd"] is None and failure["generation_id"] is None
        assert spec["actual_outcome"]["status"]==failure["status"]
        assert spec["actual_outcome"]["gate_status"]==failure["status"]
        assert spec["actual_outcome"]["witness_verified"] is None
        assert sha256((folder/"request.json").read_bytes()).hexdigest()==reservation["request_sha256"]
        assert not (folder/"provider_response.json").exists()
        return True  # Retained failed dispatch; no missing provider evidence is manufactured.
    response=yaml.safe_load(response_path.read_text(encoding="utf-8"))
    schema=response["schema"]
    assert schema in {"pfp.pilot-response.v1","pfp.dossier-response.v1"}, schema
    if schema=="pfp.dossier-response.v1":
        check_historical_dossier_capsule(folder)
        return True
    return False
