"""Model dispatch for research runs through a Symbol Game transport.

Adversary reaches a model only through Symbol Game (``RULE_ADVERSARY_LLM_MEDIATION_001``): this
adapter prepares a bound PFP turn, sends it through the existing accounted transport,
and checks the actual response before handing text to the independent research checker.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.infrastructure.seat_transport.transport import (
    is_symbol_game_transport,
)
from pfp.infrastructure.task_turn import prepare_task_turn
from adversary.domain.researcher.models import Dispatch, DispatchOutcomeV1

_LOCUS = "adversary.infrastructure.researcher.symbol_game_dispatch"


class SymbolGameModelDispatch:
    def __init__(self, transport: Any) -> None:
        if not is_symbol_game_transport(transport):
            raise TypeError(
                "LLM_PROTOCOL_UNMEDIATED: research dispatch needs a Symbol Game transport"
            )
        self._transport = transport
        self.last_pfp_result: dict | None = None

    def send(
        self,
        request: Mapping[str, Any],
        *,
        raw_dir: str,
        raw_name: str,
        ceiling_microusd: int,
    ) -> Result[DispatchOutcomeV1, Refusal]:
        self.last_pfp_result = None
        try:
            original = deepcopy(dict(request))
            messages = original.get("messages")
            system = original.get("system") or "You are a Adversary research operator."
            if type(system) is not str or type(messages) is not list or not messages:
                raise ValueError("research dispatch requires a system string and nonempty messages")
            prepared = prepare_task_turn(system=system,
                user=json.dumps(messages, ensure_ascii=False, allow_nan=False),
                task_id="adversary-research",
                attempt_id=sha256(json.dumps([raw_dir, raw_name]).encode("utf-8")).hexdigest(),
                context={"provider_options_json": json.dumps(
                    {key: value for key, value in original.items()
                        if key not in ("messages", "system")},
                    sort_keys=True, ensure_ascii=False, allow_nan=False)})
            mediated = deepcopy(original)
            mediated["system"] = prepared.prompt.system
            # Preserve earlier assistant/tool blocks verbatim. The final user turn
            # carries the bound task; do not invent an assistant turn or tool result.
            if messages[-1].get("role") == "user":
                content = mediated["messages"][-1].get("content")
                if type(content) is str:
                    mediated["messages"][-1]["content"] = content + "\n\n" + prepared.prompt.user
                elif type(content) is list:
                    content.append({"type": "text", "text": prepared.prompt.user})
                else:
                    raise ValueError("final user content must be text or content blocks")
            elif messages[-1].get("role") == "assistant":
                mediated["messages"].append({"role": "user", "content": prepared.prompt.user})
            else:
                raise ValueError("final message role must be user or assistant")
        except (AttributeError, TypeError, ValueError) as exc:
            return Err(Refusal("PFP_RESEARCH_REQUEST_INVALID", str(exc), _LOCUS))
        sent = self._transport.send(
            mediated, raw_dir=raw_dir, raw_name=raw_name, ceiling_microusd=ceiling_microusd
        )
        if isinstance(sent, Err):
            return sent
        outcome = sent.value
        replied = outcome.get("response") or {}
        raw = outcome.get("raw") or {}
        try:
            text = replied.get("text")
            refusal = outcome.get("refusal") or outcome.get("parse_refusal")
            if outcome["dispatch"] == "REPLIED" and refusal is None:
                checked = prepared.check_completion(text) if type(text) is str else prepared.check(b"")
                self.last_pfp_result = checked
                if checked["schema_valid"] and checked["failure_class"] == "NONE":
                    text = checked["answer"]
                    try:
                        # JSON escapes can hide a lone surrogate in a valid outer
                        # envelope. The research parser consumes UTF-8 text only.
                        text.encode("utf-8")
                    except UnicodeEncodeError:
                        text = None
                        refusal = {"code": "PFP_RESEARCH_REPLY_INVALID",
                            "message": "INVALID_ANSWER_UNICODE", "pfp_result": checked}
                else:
                    # A bad reply still happened and remains charged/persisted.
                    # Report a failed occurrence, never a pre-dispatch refusal.
                    text = None
                    refusal = {"code": "PFP_RESEARCH_REPLY_INVALID",
                        "message": str(checked.get("reason") or checked["failure_class"]),
                        "pfp_result": checked}
            return Ok(
                DispatchOutcomeV1(
                    dispatch=Dispatch(outcome["dispatch"]),
                    refusal=refusal,
                    raw_path=raw.get("path"),
                    raw_sha256=raw.get("sha256"),
                    text=text,
                    usage=replied.get("usage"),
                    metered_cost_microusd=outcome.get("metered_cost_microusd"),
                    quote_microusd=outcome.get("quote_microusd"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return Err(Refusal("ANTHROPIC_OUTCOME_INVALID", str(exc), _LOCUS))


__all__ = ["SymbolGameModelDispatch"]
