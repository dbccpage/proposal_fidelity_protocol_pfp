"""C057 matrix runner prompt: no leaked worked answer, bounds or case IDs.

Counterexamples from the 2026-09-28 audit: the prompt's example was the optimal
n = 4 network, it stated the proven bounds used by the infeasible cases
(k < 25 for n = 9, k < 29 for n = 10), each case was sent with a descriptive ID
such as ``c057_m08_infeasible_n4_k4``, and the runner called ``load_dotenv``.
The runner is imported only after its source is shown not to read ``.env``.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

RUNNER_PATH = Path(__file__).resolve().parents[1] / "run_c057_matrix.py"
RUNNER_MODULE = (
    "pfp.tests.demo_004.f_program_synthesis."
    "c057_sorting_network_synthesis.run_c057_matrix"
)
SOURCE = RUNNER_PATH.read_text(encoding="utf-8")


def _runner():
    assert "dotenv" not in SOURCE, "runner must not read .env files"
    return importlib.import_module(RUNNER_MODULE)


def test_runner_requires_explicit_configuration_and_keeps_full_text():
    assert "dotenv" not in SOURCE
    assert ".env" not in SOURCE.replace("``.env``", "")
    assert "parents[" not in SOURCE
    assert "[:200]" not in SOURCE
    assert "RFC 8785" not in SOURCE


def test_system_prompt_has_no_worked_network_and_no_bounds():
    prompt = _runner().SYSTEM_PROMPT
    assert "RFC 8785" not in prompt
    assert not re.search(r"\[\s*0\s*,\s*2\s*\]", prompt), "worked n=4 network leaked"
    for leaked in ("k < 25", "k < 29", "25 for n", "29 for n", "log2(n!)"):
        assert leaked not in prompt


def test_user_prompts_carry_opaque_tokens_not_case_ids():
    runner = _runner()
    prompts = runner.SPEC.prompts()
    assert len(prompts) == len(runner.TEST_CASES) == 10
    for index, (case, token, prompt) in enumerate(prompts, start=1):
        assert token == f"case_{index:02d}"
        assert case["case_id"] not in prompt
        assert "infeasible" not in prompt and "poison" not in prompt
        shown = json.loads(
            prompt[prompt.index("{") : prompt.rindex("}", 0, prompt.index("Return one JSON")) + 1]
        )
        assert shown["case_id"] == token
        assert {k for k in shown if k != "case_id"} == {k for k in case if k != "case_id"}
