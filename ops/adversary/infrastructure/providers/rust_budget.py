"""Native budget protocol adapter. Arithmetic remains in core_adversary::providers Rust."""

import re
from datetime import datetime, timezone

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err
from adversary.domain.providers.types import BudgetExceeded, ProviderConfigError


class NativeBudgetUnavailable(ProviderConfigError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"{code}: native budget unavailable")


class RustBudgetRuntime:
    def __init__(self, host=None) -> None:
        self._host = host

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

    def invoke(self, operation: str, **payload: object):
        response = (self._host or RustSymbolGameHost()).invoke_runtime(
            "provider_budget", {"operation": operation, **payload}
        )
        if isinstance(response, Err):
            raise NativeBudgetUnavailable(response.error.code)
        try:
            if response.value["success"] is not True:
                raise ProviderConfigError("NATIVE_BUDGET_REFUSED")
            reply = response.value["result"]
            refusal = reply["refusal"]
            if refusal is None:
                if reply["outcome"] is None:
                    raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
                outcome = reply["outcome"]
                # Validate wire shapes only; Rust owns all financial arithmetic.
                if operation in ("state", "debit", "settle"):
                    fields = ("spent_microusd", "delta_microusd") if operation == "settle" else ("spent_microusd", "remaining_microusd")
                    if type(outcome) is not dict or any(type(outcome.get(k)) is not int for k in fields):
                        raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
                    if outcome["spent_microusd"] < 0 or (operation != "settle" and outcome["remaining_microusd"] < 0):
                        raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
                elif operation in ("parse_cost", "estimate", "leg_cost"):
                    if type(outcome) is not int or outcome < 0:
                        raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
                return outcome
            code, message = refusal["code"], refusal["message"]
            if type(code) is not str or type(message) is not str:
                raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
        except (KeyError, TypeError, AttributeError):
            raise ProviderConfigError("NATIVE_BUDGET_MALFORMED") from None
        if code.startswith("PRICE_OBSERVATION_"):
            from adversary.domain.providers.budget import PricingObservationUnavailable
            raise PricingObservationUnavailable(code, payload["model"], payload["at_utc"])
        if code == "BUDGET_EXCEEDED":
            values = re.fullmatch(r"budget exceeded: requested=([0-9]+) limit=([0-9]+) micro-USD", message)
            if values is None:
                raise ProviderConfigError("NATIVE_BUDGET_MALFORMED")
            raise BudgetExceeded(requested=int(values[1]), limit=int(values[2]))
        if code == "PROVIDER_TYPE_ERROR":
            raise TypeError(message)
        raise ValueError(message)
