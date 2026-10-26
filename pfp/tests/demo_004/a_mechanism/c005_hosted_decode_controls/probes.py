"""
probes.py — Control-honored probes for Challenge C005 (probe_before_trust.v1).

Before scoring, each route and control receives 10 probe requests constructed
so that the unconstrained top answer is forbidden by the control.
A control counts as honored on a route only if all 10 outputs respect it.
Unhonored controls are downgraded and reported as UNCONSTRAINED for that route.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from .controls import ControlKind
from .schemas import validate_json_schema


@dataclass(frozen=True)
class ControlProbe:
    probe_id: str
    prompt: str
    target_control: ControlKind
    description: str


# 10 Probes specifically constructed to induce forbidden outputs under each control
CONTROL_HONORED_PROBES: tuple[ControlProbe, ...] = (
    ControlProbe(
        probe_id="probe_01_prose_greeting",
        prompt="Greet the user cordially with 'Hello! How can I assist you today?'",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control suppresses conversational greetings and forces JSON schema.",
    ),
    ControlProbe(
        probe_id="probe_02_explanation_request",
        prompt="Explain why the sky appears blue in two detailed paragraphs.",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control suppresses long conversational prose.",
    ),
    ControlProbe(
        probe_id="probe_03_markdown_table",
        prompt="Generate a markdown table showing the planets in our solar system.",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control prevents markdown formatting outside schema.",
    ),
    ControlProbe(
        probe_id="probe_04_python_code",
        prompt="Write a Python function `def fib(n):` that computes the nth Fibonacci number.",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control suppresses raw code block emission.",
    ),
    ControlProbe(
        probe_id="probe_05_sure_trigger",
        prompt="Reply with only the exact word 'Sure'.",
        target_control=ControlKind.LOGIT_BIAS,
        description="Verifies that logit bias (-100 on 'Sure') steers the model away from emitting 'Sure'.",
    ),
    ControlProbe(
        probe_id="probe_06_here_trigger",
        prompt="Reply with only the exact word 'Here'.",
        target_control=ControlKind.LOGIT_BIAS,
        description="Verifies that logit bias (-100 on 'Here') steers the model away from emitting 'Here'.",
    ),
    ControlProbe(
        probe_id="probe_07_the_trigger",
        prompt="What is the first word of the phrase: 'The quick brown fox'?",
        target_control=ControlKind.LOGIT_BIAS,
        description="Verifies that logit bias suppresses the token 'The'.",
    ),
    ControlProbe(
        probe_id="probe_08_freeform_poem",
        prompt="Write a short 4-line poem about mathematics.",
        target_control=ControlKind.GBNF,
        description="Verifies that GBNF grammar strictly prevents non-grammar poetic lines.",
    ),
    ControlProbe(
        probe_id="probe_09_sql_query",
        prompt="Write a SQL SELECT statement to fetch all users from a table.",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control suppresses raw SQL statements.",
    ),
    ControlProbe(
        probe_id="probe_10_conversational_farewell",
        prompt="Say goodbye politely: 'Thank you and have a wonderful day!'",
        target_control=ControlKind.JSON_SCHEMA,
        description="Verifies that schema control suppresses closing pleasantries.",
    ),
)


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    control: ControlKind
    prompt: str
    output: str
    respected: bool
    reason: str


def evaluate_probe_response(
    probe: ControlProbe,
    output: str,
    control: ControlKind,
    schema_name: str = "consistency_verdict",
) -> ProbeResult:
    """Evaluate whether a single probe output respected the active control."""
    stripped = output.strip()

    if control == ControlKind.NONE:
        # None has no constraints, so unconstrained output is trivially 'respected'
        return ProbeResult(
            probe_id=probe.probe_id,
            control=control,
            prompt=probe.prompt,
            output=output,
            respected=True,
            reason="Unconstrained control: any output admissible",
        )

    if control == ControlKind.JSON_SCHEMA or control == ControlKind.GBNF:
        # Must parse as JSON and validate against schema
        try:
            parsed = json.loads(stripped)
            valid, err = validate_json_schema(parsed, schema_name)
            if not valid:
                return ProbeResult(
                    probe_id=probe.probe_id,
                    control=control,
                    prompt=probe.prompt,
                    output=output,
                    respected=False,
                    reason=f"JSON schema validation failed: {err}",
                )
            return ProbeResult(
                probe_id=probe.probe_id,
                control=control,
                prompt=probe.prompt,
                output=output,
                respected=True,
                reason="Parsed as valid JSON strictly adhering to schema",
            )
        except Exception as exc:
            return ProbeResult(
                probe_id=probe.probe_id,
                control=control,
                prompt=probe.prompt,
                output=output,
                respected=False,
                reason=f"Failed to parse JSON: {type(exc).__name__}: {exc}",
            )

    if control == ControlKind.LOGIT_BIAS:
        # The probe tests whether heavily suppressed words ('Sure', 'Here', 'The') were avoided
        forbidden_words = {"Sure", "Here", "The"}
        for w in forbidden_words:
            if stripped.startswith(w) or stripped == w:
                return ProbeResult(
                    probe_id=probe.probe_id,
                    control=control,
                    prompt=probe.prompt,
                    output=output,
                    respected=False,
                    reason=f"Output contains suppressed token '{w}'",
                )
        return ProbeResult(
            probe_id=probe.probe_id,
            control=control,
            prompt=probe.prompt,
            output=output,
            respected=True,
            reason="Output steered away from suppressed tokens",
        )

    return ProbeResult(
        probe_id=probe.probe_id,
        control=control,
        prompt=probe.prompt,
        output=output,
        respected=False,
        reason=f"Unknown control {control}",
    )


def run_control_probes(
    completion_fn: Callable[[str, ControlKind], str],
    control: ControlKind,
    schema_name: str = "consistency_verdict",
) -> tuple[bool, list[ProbeResult]]:
    """Run all 10 probes for a given route and control.

    Returns (honored, probe_results).
    honored is True if and only if all 10 probes respected the control.
    """
    results: list[ProbeResult] = []
    all_respected = True

    for probe in CONTROL_HONORED_PROBES:
        try:
            output = completion_fn(probe.prompt, control)
        except Exception as exc:
            output = f"[CALL_ERROR] {type(exc).__name__}: {exc}"

        res = evaluate_probe_response(probe, output, control, schema_name)
        results.append(res)
        if not res.respected:
            all_respected = False

    return all_respected, results
