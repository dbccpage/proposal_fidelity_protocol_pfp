"""All model-matrix runners in f_program_synthesis (C052-C059) and W10-W13.

Counterexamples from the 2026-09-28 audit, per runner:

- ``load_dotenv()`` at import time and ``parents[5]`` path arithmetic;
- prompts that sent the case ID (for example ``Case ID: c053_m03_singular_2x2``)
  and claimed RFC 8785 output;
- replies kept as a 200-character excerpt; provider errors scored as wrong
  answers; a checker exception aborting the sweep.

Every runner's source is checked before it is imported, so no test here can
read a ``.env`` file. No test makes a network call: the provider is a fake.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from omega_engine_pfp.infrastructure import synthesis_matrix as mrs

CHALLENGES = Path(__file__).resolve().parents[2]
RUNNERS = [
    "f_program_synthesis/c052_maxflow_mincut_certificates/run_c052_matrix.py",
    "f_program_synthesis/c053_bareiss_fraction_free_matrix_inversion/run_c053_matrix.py",
    "f_program_synthesis/c054_exact_linear_systems/run_c054_matrix.py",
    "f_program_synthesis/c055_assignment_with_potentials/run_c055_matrix.py",
    "f_program_synthesis/c056_dfa_minimization_equivalence/run_c056_matrix.py",
    "f_program_synthesis/c057_sorting_network_synthesis/run_c057_matrix.py",
    "f_program_synthesis/c058_straight_line_superoptimization/run_c058_matrix.py",
    "f_program_synthesis/c059_sql_null_total_query_synthesis/run_c059_matrix.py",
    "m_witnessed_difference_programme/w10_primitive_axiomatics_evaluation_preorders/run_w10_matrix.py",
    "m_witnessed_difference_programme/w11_l1_native_cohomology_exact_duality/run_w11_matrix.py",
    "m_witnessed_difference_programme/w12_lggr_evaluated_path_kernels_gluing/run_w12_matrix.py",
    "m_witnessed_difference_programme/w13_lggr_chromatic_obstruction_adjoint_probing/run_w13_matrix.py",
]
FORBIDDEN_SOURCE = (
    "dotenv",
    "parents[",
    "[:200]",
    "RFC 8785",
    "urllib",
    "openrouter.ai",
    "OPENROUTER_API_KEY",
)


def _load(relative: str):
    source = (CHALLENGES / relative).read_text(encoding="utf-8")
    present = [token for token in FORBIDDEN_SOURCE if token in source]
    assert not present, f"{relative} still contains {present}"
    module = "omega_engine_projects.mssn_sn_symgam.challenges." + relative[:-3].replace("/", ".")
    return importlib.import_module(module)


@pytest.mark.parametrize("relative", RUNNERS, ids=lambda r: r.split("/")[-1])
def test_runner_source_is_clean_and_uses_the_shared_support(relative):
    runner = _load(relative)
    assert isinstance(runner.SPEC, mrs.MatrixSpec)
    assert runner.main is mrs.main


@pytest.mark.parametrize("relative", RUNNERS, ids=lambda r: r.split("/")[-1])
def test_prompts_carry_opaque_tokens_and_no_answer_fields(relative):
    runner = _load(relative)
    assert not mrs.system_prompt_problems(runner.SYSTEM_PROMPT)
    prompts = runner.SPEC.prompts()
    assert len(prompts) == len(runner.TEST_CASES) == 10
    for index, (case, token, prompt) in enumerate(prompts, start=1):
        assert token == f"case_{index:02d}"
        assert case["case_id"] not in prompt
        shown = json.loads(
            prompt[prompt.index("{") : prompt.rindex("}", 0, prompt.index("Return one JSON")) + 1]
        )
        assert shown["case_id"] == token
        assert not any(mrs.is_answer_bearing_key(k) for k in shown if k != "case_id")


@pytest.mark.parametrize("relative", RUNNERS, ids=lambda r: r.split("/")[-1])
def test_two_distinct_checkers_are_wired(relative):
    runner = _load(relative)
    (first_name, first), (second_name, second) = runner.SPEC.checkers
    assert (first_name, second_name) == ("exact", "independent")
    assert first.__module__.endswith(".judge_packet.exact_checker")
    assert second.__module__.endswith(".judge_packet.independent_checker")


@pytest.mark.parametrize("relative", RUNNERS, ids=lambda r: r.split("/")[-1])
def test_provider_errors_are_infra_errors_and_replies_are_kept_whole(relative, tmp_path):
    runner = _load(relative)
    model = runner.MODELS[0]["id"]

    def failing(url, headers, payload, timeout):
        return 200, json.dumps({"error": {"code": 502, "message": "upstream unavailable"}})

    summary = mrs.run_matrix(
        runner.SPEC, tmp_path / "err", "k", model_ids=[model], transport=failing, pause_s=0
    )
    counts = summary["models"][model]["counts"]
    assert counts[mrs.OUTCOME_INFRA_ERROR] == 10 and summary["models"][model]["scored"] == 0

    long_reply = "[" + ", ".join(["1"] * 400) + "]"

    def array_reply(url, headers, payload, timeout):
        return 200, json.dumps(
            {"choices": [{"message": {"content": long_reply}, "finish_reason": "stop"}]}
        )

    summary = mrs.run_matrix(
        runner.SPEC, tmp_path / "arr", "k", model_ids=[model], transport=array_reply, pause_s=0
    )
    counts = summary["models"][model]["counts"]
    assert counts[mrs.OUTCOME_ACCEPTED] == 0 and counts[mrs.OUTCOME_INFRA_ERROR] == 0
    records = [
        json.loads(line)
        for line in next((tmp_path / "arr").glob("records_*.jsonl"))
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert all(r["content"] == long_reply for r in records)


def test_missing_key_refuses_before_any_call(monkeypatch, tmp_path, capsys):
    runner = _load(RUNNERS[0])
    monkeypatch.delenv(mrs.API_KEY_ENV, raising=False)
    assert mrs.main(runner.SPEC, ["--output-dir", str(tmp_path / "run")]) == 2
    assert "CONFIGURATION_MISSING" in capsys.readouterr().out
    assert not (tmp_path / "run").exists()
