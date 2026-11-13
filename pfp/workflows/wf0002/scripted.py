"""Scripted WF2 candidate used by offline drivers and the WF2-WF5 suites.

A scripted answer is never a model call and never evidence of capability.
AuthorityEffect: None.
"""

from pfp.workflows.wf0002 import workflow as wf2


def candidate():
    slots = [
        dict(slot=row["id"], disposition="provided", value="Finite integer task.", reason="")
        for row in wf2.catalogue()["slots"]
    ]
    return dict(
        task_result={"total": 38},
        slot_report=slots,
        operad_candidates=[
            dict(
                id="sum",
                operation="sum the inputs",
                source_colours=["IntegerList"],
                target_colour="Integer",
                arity=1,
                source=dict(kind="seed_prompt", quote="input.values"),
                witness_refs=["task_result"],
            )
        ],
        ddc_moves=[
            dict(
                id="t1",
                op="T",
                operad_id="sum",
                before="input list",
                after="proposed sum",
                local_log="Candidate total emitted; host must check it.",
                refusal=None,
                witness_refs=["task_result"],
            )
        ],
    )
