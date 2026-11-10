"""Generalized Hermetic Test Suite for PFP Pilot Runner.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).

Verifies the 6 core pillars of pilot execution across all task families:
1. P -> P* packet assembly under SPK-001 (p_star_builder.py).
2. Raw-preserving response sanitization and structure leakage debt logging.
3. TracedGateway offline fixture dry run with zero cost ($0.00).
4. Strict fail-closed parser rejection on corrupted inputs and duplicate keys.
5. Host gate verification against exact ground truth across all task families.
6. Killing compiled semantic mutants under deterministic test oracles.
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest
import yaml

_HERE = Path(__file__).resolve().parent
_PFP_DIR = _HERE.parent
_EDUCATION_ROOT = _PFP_DIR.parent
_REPO_ROOT = next((p for p in _EDUCATION_ROOT.parents if (p / ".git").exists()), _EDUCATION_ROOT.parents[2])
_PYTHON_INFRA = _PFP_DIR / "python"

for path in (_REPO_ROOT, _PYTHON_INFRA):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

if not (_PYTHON_INFRA / "infrastructure").exists():
    pytest.skip("Legacy infrastructure package has been retired.", allow_module_level=True)

from infrastructure.prompt_templates.p_star_builder import build_p_star
from infrastructure.response_sanitizers.pilot_response_sanitizer import (
    extract_and_sanitize,
    record_residual_text_debt,
)

from omega_engine_education.pfp.infrastructure.pilot_runner import (
    PfpPilotRunner,
    build_requests,
    get_ground_truth,
    grade,
    materialize_results,
)
from omega_engine_operating_system.adapters.rust_host.ffi import (
    locate_host_binary,
)
from omega_engine_operating_system.adapters.security import (
    FixtureOnlyAeadProtector,
)
from omega_engine_operating_system.infrastructure import EncryptedArtifactCas
from omega_engine_operations.domain.rop.result import Err
from omega_engine_providers.domain.types import CandidateRequest
from omega_engine_symbol_game.infrastructure.trace import (
    fixture_gateway,
    scripted_openai_payload,
)

ALL_FAMILIES = [
    "linear_algebra",
    "graph_facts",
    "graph_repair",
    "refusal",
    "cochain_defect",
    "magma_associativity",
]


def make_reply(pilot_id: str, req_id: str, ans: int | None) -> dict[str, str]:
    payload = {"answer": ans}
    if ans is None:
        payload.update(status="REFUSED", witness={"remaining": [2, 4]})
    return {"request_id": f"{pilot_id}_{req_id}", "raw_reply": json.dumps(payload)}


@pytest.mark.parametrize("family", ALL_FAMILIES)
def test_p_star_packet_assembly_all_families(family):
    """Verify stimulus P compiles into typed P* packet under SPK-001 for each task family."""
    reqs = build_requests(pilot_id=f"pilot_{family}", task_family=family)
    assert len(reqs) >= 2
    for r in reqs:
        p_star, children, receipt = build_p_star(
            r["messages"][1]["content"],
            prompt_id=f"P_STAR_{r['request_id'].upper()}",
            family_name=f"{family}_family",
            generation_id=0,
        )
        assert p_star.lineage.prompt_id.startswith("P_STAR_")
        assert p_star.lineage.generation_id == 0
        assert receipt.cardinality == 1
        assert p_star.packet_type == "PromptPacketV0_1"


def test_response_sanitizer_and_residual_text_ledger(tmp_path):
    """Verify raw-preserving extraction, fence stripping, and debt accounting."""
    truth = get_ground_truth("linear_algebra")
    first_exp = list(truth.values())[0]["expected"]
    raw = "\n".join(["```json", json.dumps({"answer": first_exp}), "```", "Extra diagnostic chatter."])
    sanitized = extract_and_sanitize(raw)
    assert sanitized.fence_stripped is True
    assert sanitized.is_valid_json is True
    assert sanitized.parsed_json == {"answer": first_exp}
    assert sanitized.structure_leakage_debt_chars > 0

    ledger = tmp_path / "residual_text_ledger.json"
    record_residual_text_debt(ledger, pilot_id="pilot_0000000", request_id="pilot_0000000_req_0", sanitized=sanitized)
    assert ledger.is_file()
    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert len(entries) == 1
    assert entries[0]["pilot_id"] == "pilot_0000000"


def test_traced_gateway_offline_dry_run(tmp_path):
    """Native budget integration with fixture bytes and zero provider spend."""
    location = locate_host_binary()
    if isinstance(location, Err):
        if location.error.code == "HOST_BINARY_NOT_FOUND" and "OMEGA_SYMBOL_GAME_HOST" not in os.environ:
            pytest.skip("Native budget integration requires a built omega_symbol_game host")
        pytest.fail(f"Native host configuration failed: {location.error.code}: {location.error.message}")

    trace_file = tmp_path / "offline_trace.jsonl"
    cas_dir = tmp_path / "cas"
    store = EncryptedArtifactCas(cas_dir, FixtureOnlyAeadProtector(b"0" * 32))

    truth = get_ground_truth("linear_algebra")
    first_exp = list(truth.values())[0]["expected"]
    valid_payload = json.dumps({"answer": first_exp})

    payloads = [json.dumps(scripted_openai_payload(valid_payload)).encode("utf-8")]
    run_gw = fixture_gateway(trace_file, payloads, artifact_store=store)

    candidate_request = CandidateRequest(
        system="Solve accurately",
        user=build_requests("pilot_0000000", "linear_algebra")[0]["messages"][1]["content"],
    )
    response, receipt = run_gw.gateway.complete(candidate_request)
    assert receipt.cost_microusd == 0
    assert response.content == valid_payload

    run_gw.trace.seal(terminal="COMPLETE")
    assert trace_file.is_file()


@pytest.mark.parametrize("family", ALL_FAMILIES)
def test_ground_truth_acceptance_all_families(family):
    """Verify exact ground truth yields ACCEPTED across all task families."""
    pilot_id = f"pilot_{family}"
    truth = get_ground_truth(family)
    replies = [make_reply(pilot_id, req_id, data["expected"]) for req_id, data in truth.items()]
    result = grade(replies, pilot_id=pilot_id, task_family=family)
    assert all(r["status"] == "ACCEPTED" for r in result["results"])


def test_missing_replies_are_not_run():
    pilot_id = "pilot_0000000"
    result = grade([], pilot_id=pilot_id, task_family="linear_algebra")
    assert all(r["status"] == "NOT_RUN" for r in result["results"])


def test_strict_duplicate_keys_and_malformed():
    pilot_id = "pilot_0000000"
    malformed = [{"request_id": f"{pilot_id}_req_0", "raw_reply": '{"answer": 1, "answer": 2}'}]
    result = grade(malformed, pilot_id=pilot_id, task_family="linear_algebra")
    assert result["results"][0]["status"] == "MALFORMED"


def test_results_materialization_and_artifacts(tmp_path):
    """Verify seed.yaml, prompt_template.yaml, p_star.yaml, and response.yaml provide 100% input proof."""
    pilot_id = "pilot_0000000"
    task_family = "linear_algebra"
    results = materialize_results(tmp_path, pilot_id=pilot_id, task_family=task_family)

    assert results["prompt_template"].is_file()
    assert results["seed"].is_file()
    assert results["p_star"].is_file()
    assert results["response"].is_file()

    # 100% Input Proof Contract
    tpl_text = results["prompt_template"].read_text(encoding="utf-8")
    p_star_text = results["p_star"].read_text(encoding="utf-8")
    seed_data = yaml.safe_load(results["seed"].read_text(encoding="utf-8"))
    seed_prompt = seed_data["seed_prompt"]

    assert "[USER PROMPT]" in tpl_text
    assert "[USER PROMPT]" not in p_star_text

    tpl_data = yaml.safe_load(tpl_text)
    p_star_data = yaml.safe_load(p_star_text)

    # Lineage slots verified
    assert p_star_data["lineage"]["prompt_id"] == f"{pilot_id}_p_star"
    assert p_star_data["lineage"]["generation_id"] == 0
    assert p_star_data["lineage"]["family_id"] == task_family
    assert p_star_data["lineage"]["parent_id"] is None

    # Guidance slots verified
    assert len(p_star_data["guidance"]["rules"]) >= 1
    assert len(p_star_data["guidance"]["antibodies"]) >= 1
    assert p_star_data["guidance"]["antibodies"][0]["antibody_id"] == "ab_general_obstruction_479dd05f"
    assert len(p_star_data["guidance"]["antipatterns"]) >= 1
    assert len(p_star_data["guidance"]["helpful_patterns"]) >= 1

    # Stimulus and Schema fidelity
    assert p_star_data["user_prompt"] == seed_prompt
    assert p_star_data["system_prompt"] == tpl_data["system_prompt"]
    assert p_star_data["response_schema"] == tpl_data["response_schema"]

    # Output Response Contract
    resp_data = yaml.safe_load(results["response"].read_text(encoding="utf-8"))
    assert resp_data["schema"] == "pfp.pilot-response.v1"
    assert resp_data["evaluation"]["status"] == "NOT_RUN"
    assert resp_data["raw_reply"] is None
    assert resp_data["receipt"]["cost_microusd"] == 0


def test_pfp_pilot_runner_class_facade(tmp_path):
    """Verify object-oriented PfpPilotRunner facade behaves identically."""
    runner = PfpPilotRunner(pilot_id="pilot_0000000", task_family="linear_algebra")
    reqs = runner.requests()
    assert len(reqs) == 2

    truth = get_ground_truth("linear_algebra")
    replies = [make_reply("pilot_0000000", req_id, data["expected"]) for req_id, data in truth.items()]
    graded = runner.grade(replies)
    assert all(r["status"] == "ACCEPTED" for r in graded["results"])

    mats = runner.materialize_results(tmp_path / "facade_results")
    assert mats["seed"].is_file()
    assert mats["response"].is_file()


@pytest.mark.parametrize("old,new", [
    ('if ans == expected:', 'if True:'),
    ('rows.append({"request_id": full_id, "status": "NOT_RUN", "raw_reply": None})', 'rows.append({"request_id": full_id, "status": "ACCEPTED", "raw_reply": None})'),
    ('expected = data["expected"]', 'expected = -999999'),
    ('if reply.request_id in by_id:', 'if False:'),
], ids=["always-accept", "missing-as-accepted", "corrupt-ground-truth", "bypass-duplicate-binding"])
def test_compiled_semantic_mutants(old, new):
    """Verify semantic mutations in runner logic are caught and killed by the test oracle."""
    runner_src_path = _PFP_DIR / "infrastructure" / "pilot_runner.py"
    source = runner_src_path.read_text(encoding="utf-8")
    assert source.count(old) >= 1
    mutant = types.ModuleType("pilot_runner_mutant")
    mutant.__dict__["__file__"] = str(runner_src_path)
    sys.modules[mutant.__name__] = mutant
    exec(compile(source.replace(old, new, 1), "pilot_runner_mutant.py", "exec"), mutant.__dict__)

    def oracle(mod):
        pilot_id = "pilot_0000000"
        task_family = "linear_algebra"
        truth = mod.get_ground_truth(task_family)
        valid_replies = [make_reply(pilot_id, req_id, data["expected"]) for req_id, data in truth.items()]
        res_valid = mod.grade(valid_replies, pilot_id=pilot_id, task_family=task_family)
        assert all(r["status"] == "ACCEPTED" for r in res_valid["results"])
        empty_res = mod.grade([], pilot_id=pilot_id, task_family=task_family)
        assert all(r["status"] == "NOT_RUN" for r in empty_res["results"])
        wrong_replies = [make_reply(pilot_id, req_id, 999999) for req_id in truth]
        res_wrong = mod.grade(wrong_replies, pilot_id=pilot_id, task_family=task_family)
        assert not any(r["status"] == "ACCEPTED" for r in res_wrong["results"])
        dups = [make_reply(pilot_id, "req_0", 1), make_reply(pilot_id, "req_0", 1)]
        try:
            mod.grade(dups, pilot_id=pilot_id, task_family=task_family)
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate ID accepted")

    with pytest.raises(AssertionError):
        oracle(mutant)
