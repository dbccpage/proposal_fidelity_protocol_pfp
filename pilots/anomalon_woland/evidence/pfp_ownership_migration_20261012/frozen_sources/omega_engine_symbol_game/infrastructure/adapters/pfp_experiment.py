"""Versioned bounded experiment adapter; historical derivation replay stays frozen."""

import time
from decimal import Decimal

from omega_engine_providers.domain.types import CandidateRequest, DecodingParamsV1
from omega_engine_providers.infrastructure.openai_compat import build_openai_compat_body
from omega_engine_providers.infrastructure.openrouter_experiment_deadline import dispatch_deadline
from omega_engine_symbol_game.use_cases.pfp_derivation_loops import DerivationStop

from .pfp_derivation import PfpDerivationAdapter, microusd, provider_result
from .pfp_evidence import canonical, digest, write_once


def request_for(prompt):
    config = prompt["experiment_decoding"]
    return CandidateRequest(
        prompt["system_prompt"],
        prompt["user_prompt"],
        decoding=DecodingParamsV1(
            seed=config["seed"],
            temperature=config["temperature"],
            allow_fallbacks=False,
            require_parameters=True,
            thinking=config.get("thinking", "disabled"),
            logit_bias=config.get("logit_bias"),
        ),
    )


def wire_for(prompt, model):
    wire = build_openai_compat_body(
        request_for(prompt), model=model, max_tokens=prompt["max_output_tokens"]
    )
    wire["usage"] = {"include": True}
    return wire


class PfpExperimentAdapter(PfpDerivationAdapter):
    """Reuse durable ledger, receipts and terminal accounting with per-stage decoding.

    Route/endpoint admission occurs before construction. Every attempt holds its
    conservative byte-token upper bound at the verified worst endpoint rate.
    """

    def __init__(self, *, profile=None, **kwargs):
        super().__init__(**kwargs)
        self.profile = profile or {"ceiling_usd_per_token": "0"}
        self.rate = Decimal(self.profile["ceiling_usd_per_token"])
        if not self.rate.is_finite() or self.rate < 0 or self.rate * 120000 > Decimal("0.05"):
            raise ValueError("MODEL_PRICE_EXCEEDS_RUN_CAP")

    def begin(self, limits):
        super().begin(limits)
        write_once(self.folder / "pricing_profile.json", self.profile)

    def propose(self, loop, context):
        remaining = self.limits.seconds - (time.monotonic() - self.start)
        if remaining <= 0:
            raise DerivationStop("TIME_CAP")
        state = self.state()
        if any(row["state"] != "settled" for row in state["attempts"].values()):
            raise DerivationStop("UNRECONCILED_ATTEMPT")
        if state["spent"] >= self.limits.microusd:
            raise DerivationStop("COST_CAP")
        prompt = self.prompt_builder(self.pilot, loop, context)
        output_cap = prompt["max_output_tokens"]
        if type(output_cap) is not int or not 0 < output_cap <= 2500:
            raise ValueError("INVALID_EXPERIMENT_OUTPUT_CAP")
        wire = canonical(wire_for(prompt, self.model))
        hold = len(wire) + 512 + output_cap
        reserved_cost = microusd(self.rate * hold)
        consumed = sum(row["tokens"] for row in state["attempts"].values())
        if consumed + hold > self.limits.tokens:
            raise DerivationStop("TOKEN_CAP")
        if state["spent"] + reserved_cost > self.limits.microusd:
            raise DerivationStop("COST_CAP")
        path = self.folder / f"loop_{loop:02d}"
        write_once(path / "prompt.json", prompt)
        write_once(path / "request.json", wire)
        with self.ledger.transaction(self.limits.microusd) as state:
            attempt = str(loop)
            if attempt in state["attempts"]:
                raise DerivationStop("ATTEMPT_ALREADY_RECORDED")
            state["attempts"][attempt] = dict(
                state="reserved",
                reserved=reserved_cost,
                token_hold=hold,
                sequence=loop,
                prompt_sha256=digest(canonical(prompt)),
                request_sha256=digest(wire),
            )
            state["spent"] += reserved_cost
        remaining = self.limits.seconds - (time.monotonic() - self.start)
        # Each scheduled call gets an equal share of remaining time, minus host
        # overhead. A slow first arm cannot consume the other arm's whole interval.
        calls_left = self.limits.loops - loop + 1
        timeout = min(remaining, max(0, (remaining - 2 * calls_left) / calls_left))
        if timeout <= 0:
            write_once(
                path / "infrastructure_error.json",
                {
                    "code": "TIME_CAP_BEFORE_DISPATCH",
                    "hold_retained": True,
                    "raw_sha256": None,
                },
            )
            raise DerivationStop("TIME_CAP")
        result = None
        try:
            raw = dispatch_deadline(self.model, request_for(prompt), output_cap, timeout)
            write_once(path / "raw_reply.json", raw)
            result = provider_result(raw, self.model)
            if result["usage"]["completion_tokens"] > output_cap:
                raise ValueError("STAGE_OUTPUT_CAP_EXCEEDED")
            if result["tokens"] > hold or result["cost_microusd"] > reserved_cost:
                raise ValueError("PROVIDER_EXCEEDED_RESERVATION")
        except Exception as exc:
            raw_path = path / "raw_reply.json"
            observed = None
            if result is not None:
                observed = {"tokens": result["tokens"], "cost_microusd": result["cost_microusd"]}
                with self.ledger.transaction(self.limits.microusd) as state:
                    liability = max(reserved_cost, result["cost_microusd"])
                    state["spent"] += liability - reserved_cost
                    state["attempts"][attempt].update(
                        reserved=liability, tokens=result["tokens"], observed=observed
                    )
            write_once(
                path / "infrastructure_error.json",
                {
                    "code": type(exc).__name__,
                    "hold_retained": True,
                    "raw_sha256": digest(raw_path.read_bytes()) if raw_path.exists() else None,
                    "deadline_seconds": timeout,
                    "observed_unsettled_usage": observed,
                },
            )
            raise DerivationStop("INFRASTRUCTURE_ERROR") from None
        with self.ledger.transaction(self.limits.microusd) as state:
            if any(
                r.get("generation_id") == result["generation_id"]
                for r in state["attempts"].values()
            ):
                write_once(
                    path / "infrastructure_error.json",
                    {
                        "code": "DUPLICATE_GENERATION",
                        "hold_retained": True,
                        "raw_sha256": digest(raw),
                    },
                )
                raise DerivationStop("INFRASTRUCTURE_ERROR")
            state["spent"] += result["cost_microusd"] - reserved_cost
            state["attempts"][attempt].update(
                state="settled",
                actual=result["cost_microusd"],
                tokens=result["tokens"],
                generation_id=result["generation_id"],
            )
        receipt = {key: value for key, value in result.items() if key != "content"}
        receipt.update(
            raw_sha256=digest(raw),
            prompt_sha256=digest(canonical(prompt)),
            request_sha256=digest(wire),
            elapsed_seconds=time.monotonic() - self.start,
            stage_name=prompt["experiment_stage"],
            deadline_seconds=timeout,
        )
        write_once(path / "provider_receipt.json", receipt)
        self.rows.append(receipt)
        return prompt, result, receipt
