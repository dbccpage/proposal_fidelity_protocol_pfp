"""Read-only helpers for the retired mode-trials campaign.

Live dispatch and spec retargeting are retired. Original source bytes remain in
pilot_0000001/misc/retired_mode_trials_runner_v1; no old grid is recreated.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .._paths import pilots_root

PILOTS = pilots_root(Path(__file__))
RETIREMENT_REASON = (
    "RETIRED_MODE_CAMPAIGN: live dispatch and spec retargeting are retired; "
    "historical bytes remain read-only. For current tasks use "
    "python -m pfp.entrypoints.cli.pfp prepare-task TASK.json --attempt ID "
    "or python -m adversary.entrypoints.cli teamwork start --objective TASK --state NEW.json."
)
PAID_MODEL = "deepseek/deepseek-v4.1-flash"
PREFERRED_MICROUSD = 1_000
LARGER_MICROUSD = 10_000
LEAK = re.compile(r'"(?:expected_answer|expected_outcome|output)"\s*:')
SYSTEM = (
    "Reply with one JSON object and no markdown. "
    "Use only the facts in the task."
)


def models_for(model_id: str) -> list[str]:
    if type(model_id) is not str or not model_id.endswith(":free"):
        raise ValueError("models list accepts only a :free id plus DeepSeek V4.1 Flash")
    if model_id == PAID_MODEL:
        raise ValueError("the free slot cannot be the metered model")
    return [model_id, PAID_MODEL]


def session_cap_microusd(estimates: list[int]) -> int:
    """0.0010 USD when the priced calls fit. 0.01 USD when they need more room."""
    if any(type(item) is not int or item < 0 for item in estimates):
        raise ValueError("estimates must be non-negative ints")
    if any(item > LARGER_MICROUSD for item in estimates):
        raise ValueError("one call exceeds 0.01 USD")
    if sum(estimates) <= PREFERRED_MICROUSD:
        return PREFERRED_MICROUSD
    return LARGER_MICROUSD


def public_messages(seed_prompt: str, answer: object) -> tuple[str, str]:
    if type(seed_prompt) is not str or not seed_prompt.strip():
        raise ValueError("seed prompt is empty")
    user = seed_prompt.strip()
    blob = SYSTEM + "\n" + user
    if LEAK.search(blob):
        raise ValueError("ANSWER_BEARING_PUBLIC_PROMPT")
    encoded = json.dumps(answer, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if type(answer) in (dict, list) and encoded in blob:
        raise ValueError("ANSWER_BEARING_PUBLIC_PROMPT")
    return SYSTEM, user


def retarget_specs(root: Path | None = None) -> list[str]:
    """Refuse before reading or mutating a retired campaign's specifications."""
    raise RuntimeError(RETIREMENT_REASON)


def host_answer_matches(parsed: object, answer: object) -> bool:
    """Match a bare oracle or the one-key envelope the seed asks the model to return."""
    if _exact(parsed, answer):
        return True
    if type(parsed) is dict and "answer" in parsed:
        return _exact(parsed["answer"], answer)
    return False


def _exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_exact(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(_exact(a, b) for a, b in zip(left, right))
    if type(left) is float:
        return False
    return left == right


def dispatch_pilots(root: Path | None = None) -> dict[str, Any]:
    """Refuse before specifications, credentials, pricing or transport are touched."""
    raise RuntimeError(RETIREMENT_REASON)


def main() -> None:
    raise SystemExit(RETIREMENT_REASON)


if __name__ == "__main__":
    main()
