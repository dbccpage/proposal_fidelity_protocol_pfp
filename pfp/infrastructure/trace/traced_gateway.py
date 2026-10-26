"""The one orchestration seam that records dispatch outcomes automatically.

`record_preflight_refusal` existed as a correct function with no production
caller: the tests caught `ModelNotAllowed` by hand and called it. That is the
same defect this whole branch started from -- code that is right and never runs.
A refusal recorded only when someone remembers is a refusal that will eventually
go unrecorded, and an unrecorded preflight refusal is indistinguishable in the
trace from a dispatch that never happened.

So `TracedGateway.complete` is the only supported entry point. It records a gate
refusal itself, and the distinction it preserves is the expensive one:

* **preflight refusal** -- a gate said no; nothing left the process; safe to
  correct and re-run;
* **status unknown** -- intent was durable and the outcome is not; may already
  have been billed; never auto-retried.

Both are recorded by machinery rather than by discipline.

This is therefore the *normal* seam, not a specialist one. A wrapper that only
one dedicated test constructs is the same "correct code with no caller" defect in
a new costume, so the shared fixture wiring returns a `TracedGateway` and the raw
gateway is built only by tests that are specifically about the gateway.

It also cross-checks the two declarations that must agree: a gateway confined to
`DETERMINISTIC_FIXTURE` writing into a trace whose `RunStarted` says
`live_transport=True` would produce a file testifying that a scripted reply was a
paid provider call. Neither object can detect that alone -- the trace cannot see
the gateway and the gateway cannot see the trace -- so it is checked at the one
place that holds both.

**On catching the gate exceptions.** The compatibility package names resolve to
the same provider modules, so one canonical tuple catches every supported import
spelling.  `PromptTooLarge` is included: it is the first admission gate and its
receipt must be recorded while the trace can still prove that no intent was
written and no provider was called.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from omega_engine_woland.domain.providers.types import (
    BudgetExceeded,
    CandidateRequest,
    ModelNotAllowed,
    PromptInvalidUtf8,
    PromptTooLarge,
    ProviderConfigError,
)

from .execution_trace import ExecutionTrace, RunMode, RunModeRefusal
from .provider_dispatch import record_preflight_refusal

GATE_EXCEPTIONS: Tuple[type[BaseException], ...] = (
    ModelNotAllowed,
    BudgetExceeded,
    ProviderConfigError,
    PromptInvalidUtf8,
    PromptTooLarge,
)


class TracedGateway:
    """Wraps a confined gateway, recording preflight refusals without being asked.

    A wrapper rather than a subclass: the gateway is the component under
    measurement, and a measured object that carries its own recorder can no
    longer be run unmeasured for comparison.

    Wraps a `ConfinedGateway`, which is the only thing the factories in
    `gateway_factories` hand out. Its dispatch-time refusal runs inside `complete`
    and is *not* caught here, because a `RunModeRefusal` is not a gate refusal.
    Nothing was dispatched and nothing was admitted -- the combination was never
    allowed to reach a gate at all -- so recording it as
    `ProviderDispatchRefusedPreflight` would file a confinement failure under the
    heading of a pricing decision.
    """

    def __init__(self, trace: ExecutionTrace, gateway: Any) -> None:
        # A gateway that declares a run mode must agree with the trace it writes
        # into. Only checked when the gateway declares one: an object that makes
        # no such claim gets no assertion invented on its behalf.
        #
        # `getattr` rather than an isinstance check against `ConfinedGateway`:
        # importing it here would be a cycle, since the factories import this
        # module. This module deliberately does not import the raw provider
        # gateway either -- `architecture_fitness.raw_gateway_constructors`
        # pins raw imports to the two existing composition modules.
        declared: Optional[RunMode] = getattr(gateway, "mode", None)
        if declared is not None and (declared is RunMode.LIVE) != trace.live_transport:
            raise RunModeRefusal(
                f"gateway run mode {declared.value!r} contradicts the trace's "
                f"live_transport={trace.live_transport}; the records would testify "
                "to a transport this execution never used"
            )
        self.trace = trace
        self.gateway = gateway

    def complete(
        self,
        request: CandidateRequest,
        *,
        provider: Optional[Any] = None,
        model: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        # `is None`, not `or`: `Provider` subclasses `str`, so a falsy-but-
        # present value must not be silently swapped for the default.
        resolved_provider = (
            self.gateway.default_provider if provider is None else provider
        )
        resolved_model = self.gateway.default_model if model is None else model
        try:
            return self.gateway.complete(
                request, provider=resolved_provider, model=resolved_model
            )
        except GATE_EXCEPTIONS as exc:
            # A gate refused. Nothing was dispatched, so this must never be
            # recorded as an unknown outcome -- that would forbid a re-run that
            # is in fact free.
            record_preflight_refusal(
                self.trace,
                provider=resolved_provider,
                model=resolved_model,
                exc=exc,
            )
            raise
