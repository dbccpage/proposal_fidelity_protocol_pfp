"""Pure PASS_TO_MASTER terminal-obligation policy."""

from dataclasses import dataclass
from typing import Any

from .errors import StructureBenchError
from .strict_json import decode_json

TERMINAL_ZERO_FIELDS = ("phi_1", "gamma_2")


@dataclass(frozen=True, slots=True)
class ObligationFindings:
    """Failed and unreachable evidence branches for a terminal verdict."""

    unmet: tuple[str, ...]
    unreachable: tuple[str, ...]


def terminal_zero_obligation(final: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Check exact terminal ``phi_1 = 0`` and ``gamma_2 = 0`` evidence."""
    unmet: list[str] = []
    unreachable: list[str] = []
    payload = final.get("payload")
    if "payload" in final and not isinstance(payload, dict):
        unmet.append("the terminal DDC step's `payload` is not an object")
        payload = None
    nested = payload if isinstance(payload, dict) else {}
    for field in TERMINAL_ZERO_FIELDS:
        located = _located_values(field, final, nested)
        if not located:
            unreachable.append(
                f"the terminal DDC step records no `{field}` at the top level or under `payload`"
            )
            continue
        tokens = _exact_tokens(field, located, unmet)
        _record_token_disagreement(field, tokens, unmet)
        unmet.extend(
            f"terminal step {where} {field}={token!r}, not zero"
            for where, token in tokens
            if token != "0"
        )
    return unmet, unreachable


def _located_values(
    field: str, final: dict[str, Any], nested: dict[str, Any]
) -> list[tuple[str, Any]]:
    return [
        (where, source[field])
        for where, source in (("top level", final), ("payload", nested))
        if field in source
    ]


def _exact_tokens(
    field: str, located: list[tuple[str, Any]], unmet: list[str]
) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    for where, value in located:
        if type(value) is float:
            unmet.append(
                f"terminal step has float values ({where} {field}={value!r}); "
                "exact integer/token 0 is required with no float matching"
            )
        elif type(value) not in {int, str}:
            unmet.append(
                f"terminal step {where} {field}={value!r} is "
                f"{type(value).__name__}, not an exact integer or token"
            )
        else:
            tokens.append((where, str(value)))
    return tokens


def _record_token_disagreement(field: str, tokens: list[tuple[str, str]], unmet: list[str]) -> None:
    if len({token for _, token in tokens}) > 1:
        unmet.append(
            f"terminal step disagrees on {field}: "
            + ", ".join(f"{where}={token!r}" for where, token in tokens)
        )


def inspect_obligations(
    *, novella: bytes | None, tape: bytes | None, tape_name: str, receipt: Any
) -> ObligationFindings:
    """Inspect the three obligations in stable detail order."""
    novella_unmet = _novella_unmet(novella)
    tape_unmet, tape_unreachable = _tape_findings(tape, tape_name)
    receipt_unmet, receipt_unreachable = _receipt_findings(receipt)
    return ObligationFindings(
        unmet=tuple(novella_unmet + tape_unmet + receipt_unmet),
        unreachable=tuple(tape_unreachable + receipt_unreachable),
    )


def _novella_unmet(novella: bytes | None) -> list[str]:
    if novella is None:
        return ["novella.md is absent"]
    lines = [row.strip() for row in novella.decode("utf-8", errors="replace").splitlines()]
    act_seven_idx = next(
        (
            index
            for index, row in enumerate(lines)
            if any(
                row == f"{prefix} Act VII:" or row.startswith(f"{prefix} Act VII: ")
                for prefix in ("#", "##")
            )
        ),
        -1,
    )
    if act_seven_idx < 0:
        return ["no Act VII scene"]
    if not any(lines[act_seven_idx + 1 :]):
        return ["Act VII scene is empty"]
    return []


def _tape_findings(tape: bytes | None, tape_name: str) -> tuple[list[str], list[str]]:
    if tape is None:
        return [f"{tape_name} is absent"], []
    lines = [line for line in tape.splitlines() if line.strip()]
    if not lines:
        return ["no terminal DDC step"], []
    try:
        final = decode_json(lines[-1])
    except StructureBenchError as exc:
        return [f"the terminal DDC step is not JSON: {exc}"], []
    if not isinstance(final, dict):
        return ["the terminal DDC step is not an object"], []
    return terminal_zero_obligation(final)


def _receipt_findings(receipt: Any) -> tuple[list[str], list[str]]:
    if not isinstance(receipt, dict):
        return ["receipt.json is absent or not an object"], []
    if "lean4_proof_hash" not in receipt:
        return [], ["the receipt has no `lean4_proof_hash` field to inspect"]
    if not receipt["lean4_proof_hash"]:
        return ["`lean4_proof_hash` is empty"], []
    return [], []


__all__ = ["ObligationFindings", "inspect_obligations", "terminal_zero_obligation"]
