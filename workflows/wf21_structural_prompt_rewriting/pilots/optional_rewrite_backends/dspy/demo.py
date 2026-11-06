"""Optional DSPy Signature/Predict through PFP, with zero-send fixtures only."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Literal

import dspy

from omega_engine_pfp.infrastructure.task_turn import PfpTurnRefusal, prepare_task_turn

TEMPLATE_ID = "pfp.optional.typed-proposal.v001"
TEMPLATE_TEXT = "Return only the declared typed proposal; preserve the seed's constraints."


class RewriteSeed(dspy.Signature):
    """Preserve exact seed text and select the registered typed proposal template."""

    seed: str = dspy.InputField()
    preserved_seed: str = dspy.OutputField()
    template_id: Literal["pfp.optional.typed-proposal.v001"] = dspy.OutputField()


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "preserved_seed": {"type": "string"},
        "template_id": {"type": "string", "enum": [TEMPLATE_ID]},
    },
    "required": ["preserved_seed", "template_id"],
    "additionalProperties": False,
}


def protected_seed_judge(case, answer):
    return (
        answer["preserved_seed"] == case["context"]["protected_seed"]
        and answer["template_id"] == TEMPLATE_ID
    ), (
        "Compared exact Unicode seed text and the single registered host template selector."
    )


class FixturePfpLM(dspy.BaseLM):
    """DSPy's LM boundary accepts only a single prepared, exact PFP conversation.

    This class has no provider transport. Fixtures return raw envelope bytes,
    which the adapter checks before DSPy can parse or repair anything.
    """

    def __init__(self, fixture=None):
        super().__init__("fixture/pfp-only", cache=False, num_retries=0)
        self.fixture = fixture or preserving_fixture
        self.turn = None
        self.calls = 0
        self.records = []

    def forward(self, prompt=None, messages=None, **kwargs):
        turn, self.turn = self.turn, None
        if turn is None or prompt is not None or kwargs:
            raise ValueError("PREPARED_PFP_TURN_REQUIRED")
        expected = [
            {"role": "system", "content": turn.prompt.system},
            {"role": "user", "content": turn.prompt.user},
        ]
        if messages != expected:
            raise ValueError("PFP_MESSAGE_BINDING_MISMATCH")
        self.calls += 1
        raw = self.fixture(turn)
        if type(raw) is not bytes:
            raise TypeError("RAW_FIXTURE_BYTES_REQUIRED")
        checked = turn.check(
            raw,
            judges=(("exact-seed-and-template-v002", protected_seed_judge),),
            require_checker=True,
        )
        self.records.append({"turn": turn, "raw": raw, "checked": checked})
        if checked["status"] != "HOST_ACCEPTED":
            raise PfpTurnRefusal(checked)
        # This is a local fixture completion, not provider wire or billing evidence.
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=raw.decode("utf-8")))],
            usage={},
            model=self.model,
        )


def preserving_fixture(turn):
    seed = turn.task.case["context"]["protected_seed"]
    return json.dumps(
        {
            **{key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")},
            "answer": {
                "preserved_seed": seed,
                "template_id": TEMPLATE_ID,
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")


class StrictPfpAdapter(dspy.Adapter):
    """Use PFP's checker instead of DSPy's repair/coercion/fallback adapters."""

    def __call__(self, lm, lm_kwargs, signature, demos, inputs):
        if type(lm) is not FixturePfpLM or signature is not RewriteSeed:
            raise ValueError("DEMO_BOUNDARY_REQUIRED")
        if lm_kwargs or demos or set(inputs) != {"seed"} or type(inputs["seed"]) is not str:
            raise ValueError("SINGLE_UNMODIFIED_SIGNATURE_REQUIRED")
        turn = prepare_task_turn(
            system=signature.instructions,
            user=inputs["seed"],
            task_id="optional-dspy-seed-rewrite-v002",
            attempt_id=f"fixture:{lm.calls}",
            answer_schema=ANSWER_SCHEMA,
            context={"protected_seed": inputs["seed"], "source_mode": "OFFLINE_FIXTURE"},
            checker_id="exact-seed-and-template-v002",
        )
        lm.turn = turn
        completions = lm(messages=[
            {"role": "system", "content": turn.prompt.system},
            {"role": "user", "content": turn.prompt.user},
        ])
        if len(completions) != 1:
            raise ValueError("ONE_COMPLETION_REQUIRED")
        return [lm.records[-1]["checked"]["answer"]]


def run_demo(seed: str):
    lm = FixturePfpLM()
    with dspy.context(lm=lm, adapter=StrictPfpAdapter(), disable_history=True):
        prediction = dspy.Predict(RewriteSeed)(seed=seed)
    return {
        "status": "FIXTURE_VERIFIED",
        "source_mode": "OFFLINE_FIXTURE",
        "outgoing_provider_calls": 0,
        "fixture_attempts": lm.calls,
        "preserved_seed": prediction.preserved_seed,
        "template_id": prediction.template_id,
        "host_resolved_instruction": TEMPLATE_TEXT,
        "raw_reply_sha256": lm.records[-1]["checked"]["raw_reply_sha256"],
        "claim_ceiling": "DSPy/PFP integration only; no measured LLM efficacy or dollar billing.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", default="Find a nontrivial exact cochain certificate on the supplied graph.")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.seed), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
