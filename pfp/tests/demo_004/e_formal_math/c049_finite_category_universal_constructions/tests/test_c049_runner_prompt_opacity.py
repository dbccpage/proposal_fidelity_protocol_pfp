"""C049 matrix runner: prompts carry an opaque token, never the case ID or answer fields.

Counterexample named by this test: the old runner sent the judge case ID (for example
"c045_m09_refusal_corrupt_edge"), which names the expected verdict, and some runners also
sent answer-bearing fields or read a .env file. Nothing here calls a provider.
"""

from __future__ import annotations

import importlib
import inspect

from omega_engine_pfp.infrastructure.formal_matrix import (
    map_back,
    opaque_token,
)

RUNNER = importlib.import_module(
    "omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.run_c049_matrix"
)
CASES = RUNNER.TEST_CASES
HIDDEN_KEYS = ()


def test_prompts_never_contain_case_id_or_answer_fields() -> None:
    assert CASES
    for idx, case in enumerate(CASES):
        token = opaque_token("unit-test-nonce", idx)
        prompt = RUNNER.build_prompt(case, token)
        assert token in prompt
        assert case["case_id"] not in prompt
        for key, value in case.items():
            if key in HIDDEN_KEYS or key.startswith("expected") or key == "category":
                assert f'"{key}"' not in prompt, f"{key} leaked for {case['case_id']}"
                if isinstance(value, str):
                    assert value not in prompt, f"{key} value leaked for {case['case_id']}"


def test_runner_reads_no_env_file() -> None:
    source = inspect.getsource(RUNNER)
    assert "load_dotenv" not in source
    assert ".env" not in source
    assert "parents[6]" not in source


def test_reply_is_mapped_back_to_the_real_case_id() -> None:
    case = CASES[0]
    token = opaque_token("unit-test-nonce", 0)
    assert (
        map_back({"case_id": token, "status": "SOLVED"}, token, case["case_id"])["case_id"]
        == case["case_id"]
    )
    assert (
        map_back({"case_id": "someone_else"}, token, case["case_id"])["case_id"] == "someone_else"
    )
