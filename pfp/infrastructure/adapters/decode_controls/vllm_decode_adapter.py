"""Hosted vLLM and OpenRouter decode control adapter for structured outputs and logit biases.

AuthorityEffect: None.
Clean Architecture Layer: Infrastructure Adapter
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from omega_engine_pfp.domain.ports.decode_control_port import (
    ControlKind,
    DecodeControlPort,
    DecodeControlReceipt,
    DecodeControlSpec,
)
from omega_engine_pfp.ffi import get_default_host


class VllmDecodeAdapter(DecodeControlPort):
    """Adapter executing structured JSON schema, GBNF grammar, and logit bias controls.

    Formats API request parameters and checks control-honored probes.
    """

    def __init__(
        self,
        provider: str = "vllm_local",
        model_id: str = "meta-llama/Llama-3.1-8B-Instruct",
        runner: Callable[[dict[str, Any]], tuple[str, list[int], bool]] | None = None,
        *,
        fixture_mode: bool = False,
    ) -> None:
        self._provider = provider
        if type(fixture_mode) is not bool:
            raise TypeError("fixture_mode must be an exact bool")
        self._model_id = model_id
        self._runner = runner or (self._default_mock_runner if fixture_mode else None)

    def format_request_body(self, spec: DecodeControlSpec, prompt: str) -> dict[str, Any]:
        """Construct the provider API request payload reflecting the active decoding control."""
        body: dict[str, Any] = {
            "model": self._model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": spec.max_tokens,
            "temperature": float(spec.temperature),
        }

        if spec.control_kind == ControlKind.JSON_SCHEMA and spec.grammar_mask is not None:
            body["response_format"] = {
                "type": "json_object",
                "schema": json.loads(spec.grammar_mask.grammar_text),
            }
        elif spec.control_kind == ControlKind.GBNF and spec.grammar_mask is not None:
            body["grammar"] = spec.grammar_mask.grammar_text
        elif spec.control_kind == ControlKind.LOGIT_BIAS and spec.logit_bias is not None:
            body["logit_bias"] = {str(k): v for k, v in spec.logit_bias.biases.items()}

        return body

    def apply_decode_control(
        self,
        spec: DecodeControlSpec,
        prompt: str,
        case_id: str = "case_unknown",
    ) -> tuple[str, DecodeControlReceipt]:
        if self._runner is None:
            raise RuntimeError("EXECUTION_UNAVAILABLE: configure a runner or explicit fixture_mode")
        request_body = self.format_request_body(spec, prompt)
        text, tokens, honored = self._runner(request_body)

        receipt_id = f"rcpt_vllm_{uuid.uuid4().hex[:12]}"

        logit_biases_tuple = (
            tuple(sorted(spec.logit_bias.biases.items())) if spec.logit_bias is not None else ()
        )
        grammar_sha256 = spec.grammar_mask.grammar_sha256 if spec.grammar_mask is not None else None

        receipt = DecodeControlReceipt(
            receipt_id=receipt_id,
            case_id=case_id,
            control_kind=spec.control_kind.value,
            output_tokens=tuple(tokens),
            allowed_tokens=(),
            logit_biases=logit_biases_tuple,
            grammar_sha256=grammar_sha256,
            honored=honored,
            authority_effect="None",
        )
        return text, receipt

    def verify_decode_receipt(
        self,
        receipt: DecodeControlReceipt,
    ) -> dict[str, Any]:
        """Verify the receipt outside the model using native Rust verifier."""
        try:
            host = get_default_host()
            outcome = host.verify_decode_receipt(receipt.to_dict())
            if outcome.is_ok:
                val = outcome.unwrap()
                return dict(val.get("result", val))
            refusal = outcome.unwrap_err()
            return {
                "status": "REFUSAL",
                "refusal_code": getattr(refusal, "code", "VERIFICATION_ERROR"),
                "detail": str(refusal),
                "authority_effect": "None",
            }
        except Exception as exc:
            return {
                "status": "REFUSAL",
                "refusal_code": "VERIFIER_UNAVAILABLE",
                "detail": type(exc).__name__,
                "authority_effect": "None",
            }

    @staticmethod
    def _default_mock_runner(request_body: dict[str, Any]) -> tuple[str, list[int], bool]:
        """Deterministic mock runner for offline verification."""
        if "response_format" in request_body:
            return '{"status": "SOLVED", "answer": "CONSISTENT"}', [201, 202, 203], True
        return "CONSISTENT", [201, 202], True
