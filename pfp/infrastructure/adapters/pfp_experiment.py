"""Versioned bounded experiment adapter; historical derivation replay stays frozen."""

from decimal import Decimal

from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1
from omega_engine_woland.infrastructure.providers.openai_compat import build_openai_compat_body
from omega_engine_woland.infrastructure.providers.openrouter_experiment_deadline import dispatch_deadline

from .pfp_derivation import PfpDerivationAdapter
from .pfp_derivation import write_current


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
        self.experiment = True
        self.profile = profile or {"ceiling_usd_per_token": "0"}
        self.rate = Decimal(self.profile["ceiling_usd_per_token"])
        if not self.rate.is_finite() or self.rate < 0 or self.rate * 120000 > Decimal("0.05"):
            raise ValueError("MODEL_PRICE_EXCEEDS_RUN_CAP")

    def begin(self, limits):
        super().begin(limits)
        write_current(self.folder / "pricing_profile.json", self.profile)

    def _maximum(self, prompt):
        maximum = prompt["max_output_tokens"]
        if type(maximum) is not int or not 0 < maximum <= 2500:
            raise ValueError("INVALID_EXPERIMENT_OUTPUT_CAP")
        return maximum

    def _timeout(self, remaining, loop):
        calls_left = self.limits.loops - loop + 1
        return min(remaining, max(0, (remaining - 2 * calls_left) / calls_left))

    def _dispatch(self, request, maximum, timeout):
        return dispatch_deadline(self.model, request, maximum, timeout)
