"""C042: no answer leakage, trivial refutations flagged, refusals never verified.

Counterexamples named by these tests:
- the prompt carried ``expected_kind`` and cut the CNF at 1,200 characters without saying so;
- pub_10 contains the empty clause and pub_06 is refuted by unit propagation, so the proof
  text "0" passed as an UNSAT certificate;
- UNKNOWN with an allowed code, and OUT_OF_SCOPE with any reason, passed the dual evaluator;
- the harness loaded antibodies from other runs, models and methods, and a provider error
  aborted or was scored as a wrong answer.
No provider is called: ``call_openrouter`` is replaced by a local stub.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.drat_checker import get_canonical_cnf, trivial_refutation_reason
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
from omega_engine_pfp.infrastructure.formal_matrix import (
    ArmAntibodyStore,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver import symbol_game_routing as routing

EXAMPLES = sorted(
    (Path(__file__).resolve().parent.parent / "participant_packet" / "examples").glob("*.json")
)
CASES = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in EXAMPLES}


@pytest.mark.parametrize("name", sorted(CASES))
def test_prompts_withhold_expected_kind_and_send_full_cnf(name: str) -> None:
    case = CASES[name]
    cnf_text, _ = get_canonical_cnf(case)
    for msgs in (routing.format_prompt_m1(case), routing.format_prompt_m3(case, 1)):
        user = msgs[-1]["content"]
        assert "expected_kind" not in user
        assert "trivially_refutable" not in user
        assert cnf_text in user


def test_trivially_refutable_cases_are_marked_and_detected() -> None:
    assert CASES["c042_pub_06"]["trivially_refutable"] == "UNIT_PROPAGATION"
    assert CASES["c042_pub_10"]["trivially_refutable"] == "EMPTY_CLAUSE"
    for name, case in CASES.items():
        detected = trivial_refutation_reason(get_canonical_cnf(case)[0])
        assert detected == case.get("trivially_refutable"), name


@pytest.mark.parametrize("name", ["c042_pub_06", "c042_pub_10"])
def test_bare_zero_proof_is_not_counted_as_solving(name: str) -> None:
    case = CASES[name]
    _, cnf_hash = get_canonical_cnf(case)
    answer = {
        "case_id": name,
        "status": "SOLVED",
        "kind": "UNSAT",
        "proof_format": "DRAT",
        "proof_text": "0",
        "cnf_sha256": cnf_hash,
    }
    ok, _msg, meta = evaluate_dual(case, answer)
    assert ok is True
    assert meta["trivial_refutation"] == case["trivially_refutable"]
    assert routing.classify_outcome(ok, answer, meta) == "VERIFIED_TRIVIAL"


def test_bare_zero_proof_fails_on_a_nontrivial_unsat_case() -> None:
    case = CASES["c042_pub_02"]
    _, cnf_hash = get_canonical_cnf(case)
    answer = {
        "case_id": "c042_pub_02",
        "status": "SOLVED",
        "kind": "UNSAT",
        "proof_format": "DRAT",
        "proof_text": "0",
        "cnf_sha256": cnf_hash,
    }
    assert evaluate_dual(case, answer)[0] is False


@pytest.mark.parametrize("code", ["SOLVER_TIMEOUT", "OUT_OF_RESOURCES", "SEARCH_EXHAUSTED", ""])
def test_unknown_is_never_verified(code: str) -> None:
    ok, msg, meta = evaluate_dual(
        CASES["c042_pub_02"], {"case_id": "c042_pub_02", "status": "UNKNOWN", "code": code}
    )
    assert ok is False and meta.get("abstained") is True, msg


def test_out_of_scope_needs_a_case_without_canonical_cnf() -> None:
    oos = {"status": "OUT_OF_SCOPE", "witness": {"reason": "ANY"}}
    assert evaluate_dual(CASES["c042_pub_01"], oos)[0] is False
    assert evaluate_dual({"case_id": "x", "family": "not_a_family"}, oos)[0] is True


def test_harness_reads_no_env_file_and_invents_no_answer() -> None:
    source = inspect.getsource(routing)
    assert "load_dotenv" not in source
    assert '".env"' not in source
    assert "[:1200]" not in source and "[:200]" not in source


def test_antibodies_are_scoped_to_run_and_arm(monkeypatch: pytest.MonkeyPatch) -> None:
    case = CASES["c042_pub_02"]
    calls: list[list[dict[str, str]]] = []

    def fake_call(_key, _model, messages, **_kw):
        calls.append(messages)
        body = json.dumps(
            {
                "case_id": case["case_id"],
                "status": "SOLVED",
                "kind": "SAT",
                "solution": {"colour": [0, 0, 0]},
            }
        )
        return {
            "ok": True,
            "content": body,
            "reasoning": "",
            "usage": {},
            "elapsed": 0.0,
            "raw_body": body,
        }

    monkeypatch.setattr(routing, "call_openrouter", fake_call)
    other_arm = ArmAntibodyStore("70b_M3_RETRACTION")
    other_arm.mint(case["case_id"], "foreign", "from another arm")
    store = ArmAntibodyStore("8b_M3_RETRACTION")
    result = routing.run_case("k", "m", "M3_RETRACTION", case, store)
    assert [r["injected_antibody_ids"] for r in result["rounds"]] == [
        [],
        ["ab_8b_M3_RETRACTION_c042_pub_02_1"],
        ["ab_8b_M3_RETRACTION_c042_pub_02_1", "ab_8b_M3_RETRACTION_c042_pub_02_2"],
    ]
    assert all("from another arm" not in m[-1]["content"] for m in calls)


def test_provider_error_is_infra_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routing,
        "call_openrouter",
        lambda *_a, **_k: {
            "ok": False,
            "outcome": "INFRA_ERROR",
            "error": "HTTP 502",
            "raw_body": "bad gateway",
            "elapsed": 0.0,
        },
    )
    result = routing.run_case(
        "k", "m", "M3_RETRACTION", CASES["c042_pub_01"], ArmAntibodyStore("a")
    )
    assert result["outcome"] == "INFRA_ERROR"
    assert len(result["rounds"]) == 1
    assert result["rounds"][0]["raw_body"] == "bad gateway"
