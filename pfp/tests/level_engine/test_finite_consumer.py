"""Real finite candidate checks stay separate from fixture calibration."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from hashlib import sha256

import pytest

from operations.domain.level_engine_context import (
    current_context,
)
from pfp.infrastructure.tower_evidence.level_engine import EvidenceRefusal
from pfp.infrastructure.tower_research.level_engine.finite_consumer import (
    FiniteLevelEngineConsumer,
)


def candidate(fid="pos"):
    path = current_context().resource("payload/edge_endpoints/instance.json")
    fixture = next(row for row in json.loads(path.read_bytes())["fixtures"] if row["id"] == fid)
    return json.dumps(fixture["structure"], separators=(",", ":")).encode(), tuple(
        tuple(pair) for pair in fixture["protected"]
    )


def test_actual_candidate_verifier_is_not_fixture_success():
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    checked = consumer.check("edge_endpoints", raw, binding, protected_pairs=protected)
    assert checked.accepted is True
    assert checked.candidate_code == "ACCEPT"
    assert checked.replay.terminal == "FIXTURE_EXPECTATIONS_MATCHED"
    assert checked.evidence_grade == "RESEARCH_FIXTURE_REPLAY"
    assert checked.authority_effect == "None"
    assert binding.candidate_sha256 == sha256(raw).hexdigest()
    for name in ("checker_sha256", "source_sha256", "fixture_set_sha256", "resource_sha256"):
        assert len(getattr(binding, name)) == 64


@pytest.mark.parametrize("fid,code", [
    ("own_neg", "NON_ADMISSIBLE"),
    ("near_source", "FAILS:endpoint_source"),
    ("near_target", "FAILS:endpoint_target"),
    ("near_protect", "FAILS:protect"),
])
def test_real_negative_candidate_refuses_despite_successful_fixture_replay(fid, code):
    raw, protected = candidate(fid)
    consumer = FiniteLevelEngineConsumer(current_context(), protected_pairs=protected)
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    checked = consumer.check("edge_endpoints", raw, binding, protected_pairs=protected)
    assert checked.accepted is False
    assert checked.candidate_code == code
    assert checked.replay.terminal == "FIXTURE_EXPECTATIONS_MATCHED"
    assert checked.evidence_grade == "RESEARCH_FIXTURE_REPLAY"
    assert checked.authority_effect == "None"


def test_new_valid_candidate_is_checked_not_compared_to_stored_positive():
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    structure = json.loads(raw)
    structure["tuples"] = [["arc", [1, 0]]]
    changed = json.dumps(structure).encode()
    assert changed != raw
    binding = consumer.prepare("edge_endpoints", changed, protected_pairs=protected)
    assert consumer.check("edge_endpoints", changed, binding, protected_pairs=protected).accepted


@pytest.mark.parametrize("field", [
    "candidate_sha256", "checker_sha256", "source_sha256", "fixture_set_sha256", "resource_sha256",
])
def test_tampered_binding_refuses(field):
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, replace(binding, **{field: "0" * 64}),
            protected_pairs=protected)
    assert refusal.value.code.endswith("BINDING_MISMATCH")


def test_wrong_candidate_bytes_refuse_before_checking():
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw + b"\n", binding, protected_pairs=protected)
    assert refusal.value.code == "CANDIDATE_BINDING_MISMATCH"


def test_wrong_challenge_and_changed_host_obligation_refuse():
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("another_challenge", raw, binding, protected_pairs=protected)
    assert refusal.value.code == "CHALLENGE_BINDING_MISMATCH"
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, binding, protected_pairs=())
    assert refusal.value.code == "PROTECTED_BINDING_MISMATCH"
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.prepare("../edge_endpoints", raw)
    assert refusal.value.code == "UNSUPPORTED_FINITE_CHALLENGE"


@pytest.mark.parametrize("raw", [
    b'{"sorts":[],"sorts":[]}', b'{"sorts":NaN}', b'{}', b'[]', b'```json\n{}\n```',
])
def test_malformed_actual_candidate_is_not_repaired(raw):
    consumer = FiniteLevelEngineConsumer(current_context())
    binding = consumer.prepare("edge_endpoints", raw)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, binding)
    assert refusal.value.code == "INVALID_FINITE_CANDIDATE"


@pytest.mark.parametrize("value", [True, 3.0, "3"])
def test_candidate_indices_and_counts_are_exact_integers(value):
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    structure = json.loads(raw)
    structure["sorts"][0][1] = value
    changed = json.dumps(structure).encode()
    binding = consumer.prepare("edge_endpoints", changed, protected_pairs=protected)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", changed, binding, protected_pairs=protected)
    assert refusal.value.code == "INVALID_FINITE_CANDIDATE"


def test_raw_and_host_input_bounds_are_explicit():
    consumer = FiniteLevelEngineConsumer(current_context())
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.prepare("edge_endpoints", b"x" * 65_537)
    assert refusal.value.code == "FINITE_CANDIDATE_SIZE_OR_TYPE"
    raw, _ = candidate()
    for protected in ((), ((True, 2),), ((0, 18),), [[0, 2]]):
        with pytest.raises(EvidenceRefusal) as refusal:
            consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
        assert refusal.value.code == "INVALID_PROTECTED_PAIRS"


def test_caller_cannot_rebind_the_host_selected_obligation():
    consumer = FiniteLevelEngineConsumer(current_context())
    raw, _ = candidate()
    binding = consumer.prepare("edge_endpoints", raw)
    for operation in (
        lambda: consumer.prepare("edge_endpoints", raw, protected_pairs=((0, 1),)),
        lambda: consumer.check("edge_endpoints", raw,
            replace(binding, protected_pairs=((0, 1),)), protected_pairs=((0, 1),)),
        lambda: consumer.judge({"challenge_id": "edge_endpoints", "protected_pairs": [[0, 1]]},
            json.loads(raw)),
    ):
        with pytest.raises(EvidenceRefusal) as refusal:
            operation()
        assert refusal.value.code == "PROTECTED_BINDING_MISMATCH"


def test_existing_mutation_is_decided_on_actual_candidate():
    context = current_context()
    consumer = FiniteLevelEngineConsumer(context)
    raw, _ = candidate()
    structure = json.loads(raw)
    mutation = json.loads(context.resource("payload/edge_endpoints/mutation.json").read_bytes())
    structure["tuples"].extend(mutation["add_tuples"])
    changed = json.dumps(structure).encode()
    checked = consumer.check("edge_endpoints", changed, consumer.prepare("edge_endpoints", changed))
    assert checked.accepted is False
    assert checked.candidate_code == "FAILS:protect"
    assert checked.replay.terminal == "FIXTURE_EXPECTATIONS_MATCHED"


def test_same_path_vendor_mutation_refuses_even_if_hidden_from_git_status(tmp_path):
    context = current_context()
    vendor = tmp_path / "vendor"

    def git(*args):
        return subprocess.run(["git", "-C", str(vendor), *args],
            capture_output=True, check=True).stdout

    subprocess.run(["git", "clone", "--shared", "--no-checkout", "--quiet",
        str(context.require_vendor()), str(vendor)], capture_output=True, check=True)
    git("config", "core.autocrlf", "false")
    git("config", "core.eol", "lf")
    git("sparse-checkout", "init", "--cone")
    git("sparse-checkout", "set", "code/derivation", "research/partial_decide")
    git("checkout", "--quiet", "--detach", "b368f28c39ec85798ddc5c1bb2dfe3106770bc72")
    consumer = FiniteLevelEngineConsumer(replace(context, vendor_root=vendor))
    raw, _ = candidate()
    binding = consumer.prepare("edge_endpoints", raw)
    git("update-index", "--assume-unchanged", "code/derivation/model.py")
    source = vendor / "code/derivation/model.py"
    source.write_bytes(source.read_bytes() + b"\n# changed consumed source\n")
    assert git("status", "--porcelain", "--untracked-files=no") == b""
    for operation in (lambda: consumer.prepare("edge_endpoints", raw),
                      lambda: consumer.check("edge_endpoints", raw, binding)):
        with pytest.raises(EvidenceRefusal) as refusal:
            operation()
        assert refusal.value.code == "RR-PIN"


def test_stale_process_cannot_mint_a_new_matching_checker_binding(monkeypatch):
    from pfp.infrastructure.tower_research.level_engine import finite_consumer

    sources = finite_consumer._checker_sources()
    sources["engine/level.py"] += b"\n# changed checker\n"
    monkeypatch.setattr(finite_consumer, "_checker_sources", lambda: sources)
    raw, _ = candidate()
    with pytest.raises(EvidenceRefusal) as refusal:
        FiniteLevelEngineConsumer(current_context()).prepare("edge_endpoints", raw)
    assert refusal.value.code == "STALE_CHECKER_PROCESS"


def test_actual_governance_resource_change_refuses(tmp_path):
    context = current_context()
    original = context.governance_path("PINS.json").read_bytes()
    pins = tmp_path / "PINS.json"
    pins.write_bytes(original)
    consumer = FiniteLevelEngineConsumer(replace(context, governance_root=tmp_path))
    raw, _ = candidate()
    binding = consumer.prepare("edge_endpoints", raw)
    pins.write_bytes(original + b"\n")
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, binding)
    assert refusal.value.code == "RESOURCE_BINDING_MISMATCH"


def test_historical_bytes_never_fall_back_to_active_or_working_bytes(tmp_path):
    from pfp.infrastructure.tower_evidence.level_engine import (
        LevelEngineEvidenceResolver,
    )

    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args],
            capture_output=True, check=True).stdout.decode().strip()

    git("init", "--quiet")
    git("config", "user.name", "Finite Consumer Test")
    git("config", "user.email", "finite@example.invalid")
    git("config", "core.autocrlf", "false")
    historical = b"historical exact bytes\r\n\0"
    target = tmp_path / "manifest.json"
    target.write_bytes(historical)
    git("add", "--", "manifest.json")
    git("commit", "--quiet", "-m", "Bind historical fixture")
    revision = git("rev-parse", "HEAD")
    resolver = LevelEngineEvidenceResolver(tmp_path)
    active = resolver.read_bytes("v2", "manifest.json")
    assert active != historical
    target.write_bytes(active)
    assert resolver.read_bytes("v1", "manifest.json", revision,
        sha256(historical).hexdigest()) == historical
    for version, path, rev, digest, code in (
        ("v1", "manifest.json", "0" * 40, None, "HISTORICAL_BYTES_UNAVAILABLE"),
        ("v1", "manifest.json", revision, sha256(active).hexdigest(), "EVIDENCE_DIGEST_MISMATCH"),
        ("v2", "manifest.json", revision, None, "EVIDENCE_VERSION_INVALID"),
        ("v2", "manifest.json", None, "0" * 64, "EVIDENCE_DIGEST_MISMATCH"),
        ("v2", "missing.json", None, None, "ACTIVE_RESOURCE_UNAVAILABLE"),
    ):
        with pytest.raises(EvidenceRefusal) as refusal:
            resolver.read_bytes(version, path, rev, digest)
        assert refusal.value.code == code


def test_new_reach_certificate_issuance_stays_unavailable():
    from operations.use_cases.level_engine.reach_replay import regenerate_ledger

    with pytest.raises(ValueError, match="REACH_V2_GENERATION_UNAVAILABLE"):
        regenerate_ledger()


@pytest.mark.parametrize("field,value", [
    ("sorts", [["node", 19]]),
    ("tuples", [["arc", [0, 1]]] * 65),
    ("tuples", [["arc", [True, 1]]]),
    ("tuples", [["arc", [0, 1.0]]]),
])
def test_declared_carrier_arc_and_index_bounds_are_enforced(field, value):
    raw, _ = candidate()
    structure = json.loads(raw)
    structure[field] = value
    changed = json.dumps(structure).encode()
    consumer = FiniteLevelEngineConsumer(current_context())
    binding = consumer.prepare("edge_endpoints", changed)
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", changed, binding)
    assert refusal.value.code == "INVALID_FINITE_CANDIDATE"


@pytest.mark.parametrize("name,code", [
    ("instance.json", "FIXTURE_SET_BINDING_MISMATCH"),
    ("mutation.json", "FIXTURE_SET_BINDING_MISMATCH"),
    ("expect.json", "FIXTURE_SET_BINDING_MISMATCH"),
    ("spec.py", "FINITE_SOURCE_MISMATCH"),
])
def test_actual_changed_payload_bytes_refuse(tmp_path, name, code):
    context = current_context()
    payload = tmp_path / "payload/edge_endpoints"
    shutil.copytree(context.resource("payload/edge_endpoints"), payload)
    consumer = FiniteLevelEngineConsumer(replace(context, runtime_root=tmp_path))
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    target = payload / name
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, binding, protected_pairs=protected)
    assert refusal.value.code == code


def test_actual_missing_fixture_and_missing_vendor_refuse(tmp_path):
    context = current_context()
    payload = tmp_path / "payload/edge_endpoints"
    shutil.copytree(context.resource("payload/edge_endpoints"), payload)
    (payload / "expect.json").unlink()
    raw, _ = candidate()
    for changed, code in (
        (replace(context, runtime_root=tmp_path), "FINITE_COMPONENT_UNAVAILABLE"),
        (replace(context, vendor_root=None), "PINNED_VENDOR_UNAVAILABLE"),
        (replace(context, vendor_root=tmp_path / "missing-vendor"), "RR-PIN"),
    ):
        with pytest.raises(EvidenceRefusal) as refusal:
            FiniteLevelEngineConsumer(changed).prepare("edge_endpoints", raw)
        assert refusal.value.code == code


@pytest.mark.parametrize("terminal", ["MISSING_COMPONENTS", "FIXTURE_EXPECTATIONS_MISMATCHED"])
def test_runner_unavailability_cannot_be_candidate_success(monkeypatch, terminal):
    from pfp.domain.tower.level_engine import LevelEngineOutcome
    from pfp.infrastructure.tower_research.level_engine.runner import (
        ResearchLevelEngineRunner,
    )

    consumer = FiniteLevelEngineConsumer(current_context())
    raw, protected = candidate()
    binding = consumer.prepare("edge_endpoints", raw, protected_pairs=protected)
    monkeypatch.setattr(ResearchLevelEngineRunner, "run", lambda self, challenge_id:
        LevelEngineOutcome(challenge_id, terminal, "RESEARCH_FIXTURE_REPLAY"))
    with pytest.raises(EvidenceRefusal) as refusal:
        consumer.check("edge_endpoints", raw, binding, protected_pairs=protected)
    assert refusal.value.code == terminal


@pytest.mark.parametrize("fid,expected_status", [
    ("pos", "HOST_ACCEPTED"), ("near_source", "PROVIDER_COMPLETED"),
])
def test_prepared_actual_pfp_reply_consumes_real_finite_checker(fid, expected_status):
    import base64

    from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
    from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
    from pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase

    raw, protected = candidate(fid)
    task = PfpTaskPrompt("edge-task", "Submit a bounded arc relation satisfying the host obligation.",
        {"challenge_id": "edge_endpoints", "protected_pairs": [list(pair) for pair in protected],
         "expected_answer": "HOST_ORACLE_ISOLATION_CONTROL"}, {"type": "object"})
    prompt = PreparePfpTaskTurnUseCase().execute(
        PfpPromptTemplate("Work only from public task input.", "[USER PROMPT]", {}), task, "attempt-1")
    assert "HOST_ORACLE_ISOLATION_CONTROL" not in prompt.system + prompt.user
    properties = prompt.response_schema["properties"]
    reply = b" \n" + json.dumps({
        **{name: properties[name]["const"] for name in ("task_id", "attempt_id", "input_sha256")},
        "answer": json.loads(raw),
    }).encode() + b"\r\n"
    consumer = FiniteLevelEngineConsumer(current_context(), protected_pairs=protected)
    result = CheckPfpTaskTurnUseCase().execute(task, prompt, reply,
        judges=[("level-engine:edge_endpoints", consumer.judge)], require_checker=True)
    assert result["status"] == expected_status
    assert result["schema_valid"] is True
    assert result["authority_effect"] == "None"
    assert base64.b64decode(result["raw_reply_base64"]) == reply
    assert result["raw_reply_sha256"] == sha256(reply).hexdigest()
    evidence = json.loads(result["judges"][0]["reason"])
    assert evidence["evidence_grade"] == "RESEARCH_FIXTURE_REPLAY"
    assert evidence["candidate_code"] == ("ACCEPT" if fid == "pos" else "FAILS:endpoint_source")
    assert evidence["binding"]["challenge_id"] == "edge_endpoints"
    assert evidence["binding"]["protected_pairs"] == [list(pair) for pair in protected]
