"""Final participant contexts exclude poisoned learning and bind real evidence."""

import copy
import json

import pytest
import yaml

from omega_engine_woland.tests.pilots.relational_spacetime import typed_signals as adaptive
from omega_engine_woland.tests.pilots.relational_spacetime import final_prompts as closeout
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import STAGES
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import TEMPLATE
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import digest


def test_delivered_contexts_replay_and_exclude_contradicted_advice(monkeypatch):
    from omega_engine_pfp.infrastructure.adapters import pfp_derivation

    monkeypatch.setattr(
        pfp_derivation,
        "dispatch_deadline",
        lambda *args: (_ for _ in ()).throw(AssertionError("offline used transport")),
    )
    review = json.loads(closeout.REVIEW.read_bytes())
    assert review["source_candidate_collection_sha256"] == digest(
        (adaptive.EVIDENCE / "candidate_artifacts.json").read_bytes()
    )
    for pilot, data in closeout.documents().items():
        assert (closeout.FINAL / f"{pilot}.yaml").read_bytes() == data
        prompt = yaml.safe_load(data)
        user = json.loads(prompt["user_prompt"])
        assert prompt["original_seed"] == user["original_seed"] == BY_ID[pilot]["text"]
        assert prompt["template_sha256"] == digest((closeout.ROOT / TEMPLATE).read_bytes())
        assert user["previous_model_proposal_untrusted"] is None
        assert user["prompt_id"] == prompt["prompt_id"]
        assert user["candidate_guidance"] == prompt["guidance"]
        assert len(prompt["lineage_receipts"]) == 5
        assert all(tag["status"] == "EXPERIMENTAL_UNADMITTED" for tag in prompt["guidance"])
        if pilot == "pilot_0000201":
            assert all(tag["authorship"] == "CODEX_REVIEWER" for tag in prompt["guidance"])
        if pilot == "pilot_0000202":
            assert not any("accept the witness output" in tag["text"] for tag in prompt["guidance"])
        if pilot == "pilot_0000200":
            assert not any(
                "does not imply global conservation" in tag["text"] for tag in prompt["guidance"]
            )
        for index in range(25):
            capsule = adaptive.PILOTS / pilot / "tests" / f"test_{index:02d}"
            spec = yaml.safe_load((capsule / "test_spec.yaml").read_bytes())
            assert spec["stage"] == STAGES[index % 5]
            assert (capsule / "v2/input.yaml").is_file()
            assert (capsule / "v2/response.yaml").is_file()


@pytest.mark.parametrize(
    "field,value",
    [
        ("text", "unattributed replacement"),
        ("raw_reply_sha256", "0" * 64),
        ("prompt_id", "different-prompt"),
        ("prompt_text_sha256", "0" * 64),
        ("original_seed_sha256", "0" * 64),
        ("admitted", True),
    ],
)
def test_candidate_provenance_mutations_refused(field, value):
    candidate = copy.deepcopy(
        json.loads((adaptive.EVIDENCE / "candidate_artifacts.json").read_bytes())[0]
    )
    candidate[field] = value
    with pytest.raises(ValueError, match="CANDIDATE_SOURCE_BINDING_MISMATCH"):
        closeout.validate_candidate(candidate, adaptive.base.EVIDENCE / candidate["pilot_id"])
