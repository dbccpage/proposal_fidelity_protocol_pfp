"""
controls.py — Decoding control specifications and parameter builders for Challenge C005.

Defines the four decoding controls:
1. NONE (unconstrained)
2. LOGIT_BIAS (-100 on prose starters, +5 on digits/signs/punctuation)
3. JSON_SCHEMA (strict schema structured outputs)
4. GBNF (formal grammar constraint)

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .schemas import (
    CONSISTENCY_GBNF_GRAMMAR,
    CONSISTENCY_JSON_SCHEMA,
    CYCLE_REPAIR_GBNF_GRAMMAR,
    CYCLE_REPAIR_JSON_SCHEMA,
)


class ControlKind(str, Enum):
    NONE = "none"
    LOGIT_BIAS = "logit_bias"
    JSON_SCHEMA = "json_schema"
    GBNF = "gbnf"


# Prose-starting prefixes to suppress with -100
PROSE_STARTER_PIECES = (
    "Sure",
    " Here",
    "Here",
    " I",
    "I",
    " The",
    "The",
    " Based",
    "Based",
    " According",
    "According",
    " Let",
    "Let",
    " To",
    "To",
    " As",
    "As",
    " In",
    "In",
    " Output",
    "Output",
    " Answer",
    "Answer",
    " Note",
    "Note",
    " Yes",
    "Yes",
    " No",
    "No",
    " Well",
    "Well",
    " First",
    "First",
)

# Digits, signs, separators to boost with +5
STRUCTURE_PIECES = (
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "-",
    ":",
    ",",
    "{",
    "}",
    "[",
    "]",
    '"',
    " ",
    "\n",
    "CONSISTENT",
    "INCONSISTENT",
    "SOLVED",
    "UNPARSEABLE",
    "verdict",
    "certificate",
    "status",
    "repaired",
    "weighted_l1",
)


@dataclass(frozen=True)
class DecodingControlConfig:
    kind: ControlKind
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "parameters": self.parameters,
        }


def build_logit_bias_map(
    tokenizer: Any | None = None,
    custom_token_mapping: dict[str, int] | None = None,
) -> dict[int, int]:
    """Construct the logit bias dictionary: -100 for prose starters, +5 for structural tokens.

    If a tokenizer is provided (e.g. tiktoken encoding or HuggingFace PreTrainedTokenizerFast),
    token IDs are computed directly. Alternatively, a custom token mapping can be supplied.
    """
    bias_map: dict[int, int] = {}

    if tokenizer is not None:
        # Check for tiktoken or huggingface interface
        if hasattr(tokenizer, "encode"):
            for piece in PROSE_STARTER_PIECES:
                try:
                    ids = tokenizer.encode(piece)
                    for tid in ids:
                        bias_map[tid] = -100
                except Exception:
                    pass
            for piece in STRUCTURE_PIECES:
                try:
                    ids = tokenizer.encode(piece)
                    for tid in ids:
                        bias_map[tid] = 5
                except Exception:
                    pass
    elif custom_token_mapping is not None:
        for piece, tid in custom_token_mapping.items():
            if any(piece.strip().startswith(p.strip()) for p in PROSE_STARTER_PIECES):
                bias_map[tid] = -100
            elif piece in STRUCTURE_PIECES:
                bias_map[tid] = 5

    return bias_map


def get_control_config(
    kind: ControlKind,
    task_family: str = "consistency",
    tokenizer: Any | None = None,
) -> DecodingControlConfig:
    """Factory creating the appropriate DecodingControlConfig for a given task family."""
    if kind == ControlKind.NONE:
        return DecodingControlConfig(kind=ControlKind.NONE, parameters={})

    elif kind == ControlKind.LOGIT_BIAS:
        bias_map = build_logit_bias_map(tokenizer=tokenizer)
        return DecodingControlConfig(
            kind=ControlKind.LOGIT_BIAS,
            parameters={"logit_bias": bias_map, "bias_strength": {"suppress": -100, "boost": 5}},
        )

    elif kind == ControlKind.JSON_SCHEMA:
        schema = (
            CONSISTENCY_JSON_SCHEMA if task_family == "consistency" else CYCLE_REPAIR_JSON_SCHEMA
        )
        return DecodingControlConfig(
            kind=ControlKind.JSON_SCHEMA,
            parameters={
                "response_format": {
                    "type": "json_schema",
                    "json_schema": schema,
                }
            },
        )

    elif kind == ControlKind.GBNF:
        grammar = (
            CONSISTENCY_GBNF_GRAMMAR if task_family == "consistency" else CYCLE_REPAIR_GBNF_GRAMMAR
        )
        return DecodingControlConfig(
            kind=ControlKind.GBNF,
            parameters={"grammar": grammar},
        )

    raise ValueError(f"Unknown ControlKind: {kind}")
