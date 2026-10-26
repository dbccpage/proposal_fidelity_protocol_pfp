"""Construct traced fixture and live gateways with dispatch confinement.

Plan v2.5 §2.2: P1b's value depends on passing through the *real* provider
adapter, and that path has two fail-closed gates ahead of the transport:

```
complete() -> admit() -> ModelAllowlist.check      (gate 1)
                      -> PriceTable.quote          (gate 2)
           -> transport()                          (the socket)
```

Registering the scripted model in both gates is not a workaround: it means P1b
exercises the allowlist and pricing path instead of proving something about a
code path production never takes.

# Why this module exists in this shape

Confinement has now failed twice in the same way, and both failures were of
*inspection* rather than of *construction*.

**First:** the mode was checked when the gateway was built and then discarded, so
`complete(provider=..., model=...)` dispatched whatever it liked.

**Second:** the mode was re-checked at dispatch, but whether the transport was
scripted was still *guessed* -- by walking `.inner` attributes looking for a
`ScriptedTransport`. An ordinary closure defeats that in three lines:

```python
script = ScriptedTransport([...])
def hidden(provider, model, request):     # no `.inner` anywhere
    return script(provider, model, request)
```

`hidden` was classified non-scripted, so a scripted socket could be sealed under
`Provider.OPENROUTER`, admitted by both production gates, and recorded in a trace
that said `deterministic_fixture`. The predicate was not weak; it was answering a
question that cannot be answered by looking at an object. Any callable can hide
anything.

So the guess is gone. `fixture_gateway` **constructs** the scripted transport
itself and therefore *knows* what it built: it takes declared response bytes, not
a callable, and owns the provider, the run mode, the scripted transport, the
durable wrapper and the trace. There is no argument through which a fixture run
can name a real vendor, because there is no such argument.

Live execution gets its own factory. `live_gateway` still accepts a real
callable -- a live transport is an arbitrary socket by definition -- and its
`_refuse_scripted` check is honestly labelled: it is a courtesy, not a guarantee,
and the guarantee for fixtures does not depend on it.

# What is deliberately not claimed

Python has no private state. `ConfinedGateway` holds no reference to the raw
gateway as an attribute -- the dispatch is a closure -- but `__closure__` exists
and `gc` exists. This module's traced factories expose supported paths that
return confined gateways. The separate `estimated_gateway` composition API owns
OpenRouter accounting and returns gateways with its own financial policy; it
does not claim fixture confinement. `architecture_fitness.raw_gateway_constructors`
pins the exact construction calls in both existing factories and rejects raw
imports elsewhere. It checks source drift, not runtime policy or Python privacy.

**Comparison is by value, never by identity.** Provider types now have one
canonical home in `omega_engine_woland.domain.providers.types`, with no research-host
aliases. Confinement still compares declared values: serialized inputs and
independently constructed enum values must not bypass the fixture boundary.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Tuple

from omega_engine_woland.domain.providers.allowlist import (
    ModelAllowlist,
)
from omega_engine_woland.domain.providers.budget import (
    DEFAULT_BUDGET_MICROUSD,
    DEFAULT_MAX_OUTPUT_TOKENS,
    BudgetController,
    GatewayPolicy,
    PriceTable,
    fixture_pricing_observation,
    utc_now,
)
from omega_engine_woland.domain.providers.types import Provider
from omega_engine_woland.domain.providers.ledger import BudgetLedger
from omega_engine_woland.infrastructure.providers.gateway import (
    OearsLlmGateway,
)

from .execution_trace import (
    DURABILITY_FSYNC_LIVE,
    ExecutionTrace,
    RunMode,
    RunModeRefusal,
    require_run_mode,
)
from .provider_dispatch import (
    SCRIPTED_MODEL,
    SCRIPTED_PRICE_MICROUSD_PER_MTOK,
    DurableDispatchTransport,
    EncryptedArtifactStorePort,
    ScriptedTransport,
    provider_label,
)
from .traced_gateway import TracedGateway

#: Deliberately not a real vendor. The gateway's `_parse` sends FIXTURE through
#: `parse_openai_compat_response`, so the real parser runs without borrowing a
#: real provider's identity for a reply no provider sent.
SCRIPTED_PROVIDER = Provider.FIXTURE
#: The declared value, which is what every check below actually compares. The
#: enum member is only one of at least two class objects carrying it.
SCRIPTED_PROVIDER_VALUE = SCRIPTED_PROVIDER.value

#: Real vendor identities. A scripted transport may never sit behind one.
LIVE_PROVIDERS = frozenset(p for p in Provider if p is not Provider.FIXTURE)
#: The same set, as declared values. Membership is tested against this rather than
#: against the members -- but honestly: today the two are equivalent. `Provider`
#: mixes in `str`, and `str` precedes `Enum` in the MRO, so members hash and
#: compare exactly like their values; a set of members already matches a legacy
#: member and a bare `"openrouter"` alike. This form is kept because that
#: equivalence is an accident of the mixin rather than anything anyone declared:
#: remove `str` from `Provider` and the member set silently stops matching across
#: the two module identities, while this one does not. Unlike the `is` comparison
#: it replaced, it is not closing a live evasion.
LIVE_PROVIDER_VALUES = frozenset(p.value for p in LIVE_PROVIDERS)


def assert_mode_admissible(
    *, provider: Any, model: str, mode: RunMode, scripted_transport: bool
) -> None:
    """The three refusals, enforced in one place and by value.

    ``scripted_transport`` is a **fact supplied by whoever built the transport**,
    not a property inferred from it. That is the correction: the previous version
    walked the object graph looking for a `ScriptedTransport`, which a closure
    hides completely. Only the constructor knows what it constructed, so only the
    constructor may answer this.
    """
    mode = require_run_mode(mode)
    label = provider_label(provider)
    if model == SCRIPTED_MODEL and mode is RunMode.LIVE:
        raise RunModeRefusal(
            f"{SCRIPTED_MODEL} is a deterministic fixture and may not run in LIVE mode; "
            "a scripted reply recorded as live is a false durability claim"
        )
    if scripted_transport and label in LIVE_PROVIDER_VALUES:
        raise RunModeRefusal(
            f"a scripted transport may not sit behind real provider identity "
            f"{label}; use {SCRIPTED_PROVIDER_VALUE}"
        )
    if mode is RunMode.LIVE and label == SCRIPTED_PROVIDER_VALUE:
        raise RunModeRefusal(
            f"{SCRIPTED_PROVIDER_VALUE} is not a live provider; "
            "LIVE mode requires a real provider identity"
        )


def scripted_allowlist(*, register: bool = True) -> ModelAllowlist:
    """The builtin allowlist, optionally plus the scripted entry.

    ``register=False`` exists so a test can remove exactly one gate's knowledge
    of the model and observe the refusal, which is acceptance test 42.
    """
    allowlist = ModelAllowlist.builtin()
    if register:
        allowlist = allowlist.allow(SCRIPTED_PROVIDER, SCRIPTED_MODEL)
    return allowlist


def scripted_price_table(*, register: bool = True) -> PriceTable:
    """The builtin price table, optionally plus the scripted row (priced zero)."""
    prices = PriceTable.builtin()
    if register:
        prices = prices.with_observation(
            fixture_pricing_observation(
                SCRIPTED_MODEL,
                SCRIPTED_PRICE_MICROUSD_PER_MTOK,
                SCRIPTED_PRICE_MICROUSD_PER_MTOK,
            )
        )
    return prices


class ConfinedGateway:
    """A gateway that re-checks its run mode on every call and exposes no other.

    Holds **no attribute referring to the underlying gateway**. Dispatch is a
    closure created in this module, so there is no supported expression that gets
    from a confined gateway back to an unconfined one -- the previous shape gave
    up the whole property to `traced.gateway.gateway.complete(...)`, which is a
    documented attribute chain and therefore an API, whatever the comment beside
    it said. See the module docstring for what this does and does not claim.

    In ``DETERMINISTIC_FIXTURE`` the pair sealed at construction is the *only*
    admissible pair. An override naming anything else is refused outright rather
    than re-checked against the general rules -- the scripted transport is what
    sits underneath, and the general rules would happily admit a second
    fixture-provider model that no script was ever written for. In ``LIVE`` the
    general rules apply, because a live gateway legitimately dispatches to more
    than one provider.
    """

    __slots__ = (
        "_dispatch",
        "mode",
        "sealed_provider",
        "sealed_model",
        "default_provider",
        "default_model",
        "scripted_transport",
    )

    def __init__(
        self,
        dispatch: Callable[[Any, Any, str], Tuple[Any, Any]],
        *,
        mode: RunMode,
        provider: Any,
        model: str,
        scripted_transport: bool,
    ) -> None:
        self._dispatch = dispatch
        self.mode = require_run_mode(mode)
        #: Stored as declared values, not enum members: the pair a caller passes
        #: at dispatch may come from either module identity.
        self.sealed_provider = provider_label(provider)
        self.sealed_model = model
        self.default_provider = provider
        self.default_model = model
        self.scripted_transport = scripted_transport

    def assert_dispatch_admissible(self, provider: Any, model: str) -> None:
        """Refuse a provider/model pair this execution may not dispatch."""
        label = provider_label(provider)
        if self.mode is RunMode.DETERMINISTIC_FIXTURE and (
            label != self.sealed_provider or model != self.sealed_model
        ):
            raise RunModeRefusal(
                "deterministic-fixture execution is confined to the sealed pair "
                f"({self.sealed_provider}, {self.sealed_model}); "
                f"({label}, {model}) was requested at dispatch. A scripted "
                "transport must not serve a provider or model it was not sealed "
                "with, whatever the allowlist and price table would admit"
            )
        assert_mode_admissible(
            provider=provider,
            model=model,
            mode=self.mode,
            scripted_transport=self.scripted_transport,
        )

    def complete(
        self,
        request: Any,
        *,
        provider: Optional[Any] = None,
        model: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        # `is None`, not `or`: `Provider` is a `str` subclass, and a falsy-but-
        # present value must not be silently swapped for the default.
        resolved_provider = self.default_provider if provider is None else provider
        # The sealed model, not the gateway's per-provider resolution. Under
        # fixture confinement there is exactly one admissible model, and letting
        # `_resolve_model` pick one would reintroduce a pair nobody sealed.
        resolved_model = self.default_model if model is None else model
        self.assert_dispatch_admissible(resolved_provider, resolved_model)
        return self._dispatch(request, resolved_provider, resolved_model)


class FixtureRun:
    """One fully-constructed deterministic fixture execution.

    Returned instead of a bare gateway because a caller needs the trace and needs
    to be able to see whether the socket was reached -- and the previous way to
    get either was to reach through the gateway into its internals, which is the
    access this whole change exists to remove. Everything here is confined
    evidence: the traced gateway, the trace it writes, the artifact directory, and
    the calls the declared script was actually asked for.
    """

    __slots__ = (
        "gateway",
        "trace",
        "artifact_store",
        "provider",
        "model",
        "_script",
    )

    def __init__(
        self,
        *,
        gateway: TracedGateway,
        trace: ExecutionTrace,
        artifact_store: EncryptedArtifactStorePort,
        script: ScriptedTransport,
    ) -> None:
        self.gateway = gateway
        self.trace = trace
        self.artifact_store = artifact_store
        self.provider = SCRIPTED_PROVIDER
        self.model = SCRIPTED_MODEL
        self._script = script

    @property
    def calls(self) -> tuple[tuple[str, str], ...]:
        """`(provider, model)` pairs the scripted socket was actually asked for.

        Read-only: a test asserting "the transport was never reached" is making a
        claim about what happened, and it should not be holding an object it
        could have driven itself.
        """
        return tuple(self._script.calls)

    def complete(self, request: Any, **kwargs: Any) -> Tuple[Any, Any]:
        """Convenience passthrough to the traced, confined gateway."""
        return self.gateway.complete(request, **kwargs)


def _confined_gateway(
    transport: Callable[..., Any],
    *,
    mode: RunMode,
    provider: Any,
    model: str,
    scripted_transport: bool,
    register_in_allowlist: bool = True,
    register_in_price_table: bool = True,
    budget_microusd: int = DEFAULT_BUDGET_MICROUSD,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    allowlist: Optional[ModelAllowlist] = None,
    prices: Optional[PriceTable] = None,
    pricing_clock: Callable[[], str] = utc_now,
    budget_ledger: BudgetLedger | None = None,
) -> ConfinedGateway:
    """Build the real gateway and immediately close over it.

    Private, and the traced factory construction site pinned by
    `architecture_fitness.raw_gateway_constructors`.
    The gateway is referenced only by the closure below, so the confined object
    that escapes carries no attribute leading back to it.
    """
    mode = require_run_mode(mode)
    assert_mode_admissible(
        provider=provider,
        model=model,
        mode=mode,
        scripted_transport=scripted_transport,
    )
    gateway = OearsLlmGateway(
        allowlist=allowlist or scripted_allowlist(register=register_in_allowlist),
        policy=GatewayPolicy(
            prices=prices
            if prices is not None
            else scripted_price_table(register=register_in_price_table),
            budget=BudgetController(budget_microusd, ledger=budget_ledger),
            max_output_tokens=max_output_tokens,
            pricing_clock=pricing_clock,
        ),
        transport=transport,
        default_provider=provider,
        default_model=model,
    )

    def _dispatch(request: Any, dispatch_provider: Any, dispatch_model: str):
        return gateway.complete(
            request, provider=dispatch_provider, model=dispatch_model
        )

    return ConfinedGateway(
        _dispatch,
        mode=mode,
        provider=provider,
        model=model,
        scripted_transport=scripted_transport,
    )


def fixture_gateway(
    trace_path: str | os.PathLike[str],
    responses: Sequence[Any],
    *,
    artifact_store: EncryptedArtifactStorePort,
    execution_id: Optional[str] = None,
    durability: str = DURABILITY_FSYNC_LIVE,
    register_in_allowlist: bool = True,
    register_in_price_table: bool = True,
    budget_microusd: int = DEFAULT_BUDGET_MICROUSD,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    allowlist: Optional[ModelAllowlist] = None,
) -> FixtureRun:
    """A complete deterministic fixture execution, constructed here and nowhere else.

    Takes **declared response bytes**, not a transport. That is the entire point:
    a factory that accepts a callable cannot know what the callable does, and the
    previous attempt to find out by inspection was defeated by a closure. Owning
    the construction is the only way the run mode can be a fact rather than a
    hope.

    There is deliberately **no `provider`, `model` or `mode` parameter**. A
    fixture execution is `Provider.FIXTURE`, the scripted model, and
    `RunMode.DETERMINISTIC_FIXTURE`; offering an argument for any of them would be
    offering a way to be something else. This also closes a hole a type annotation
    was carrying alone: `mode="deterministic_fixture"` passed as a *string* made
    both `mode is RunMode.LIVE` and `mode is RunMode.DETERMINISTIC_FIXTURE` false,
    which silently skipped the sealed-pair check.

    An element of ``responses`` that is a `BaseException` is raised by the socket
    instead of returned, so transport failures stay inside closed construction.

    ``durability`` remains a choice because it is genuinely orthogonal: a fixture
    execution may select `fsync_live` to exercise the barriers without claiming a
    provider was ever contacted. The trace records `live_transport=False` and
    `run_mode=deterministic_fixture` regardless.

    The two ``register_*`` switches stay because each corresponds to one
    fail-closed gate, and acceptance test 42 is that failing *either* refuses
    before dispatch.
    """
    script = ScriptedTransport(responses)
    trace = ExecutionTrace(
        trace_path,
        execution_id=execution_id or Path(trace_path).stem,
        durability=durability,
        live_transport=False,
        run_mode=RunMode.DETERMINISTIC_FIXTURE,
    )
    durable = DurableDispatchTransport(
        trace, script, artifact_store=artifact_store, live=False
    )
    confined = _confined_gateway(
        durable,
        mode=RunMode.DETERMINISTIC_FIXTURE,
        provider=SCRIPTED_PROVIDER,
        model=SCRIPTED_MODEL,
        # Known, not guessed: this function built the `ScriptedTransport` three
        # lines up.
        scripted_transport=True,
        register_in_allowlist=register_in_allowlist,
        register_in_price_table=register_in_price_table,
        budget_microusd=budget_microusd,
        max_output_tokens=max_output_tokens,
        allowlist=allowlist,
        pricing_clock=lambda: "2000-01-01T00:00:00.000000Z",
    )
    return FixtureRun(
        gateway=TracedGateway(trace, confined),
        trace=trace,
        artifact_store=artifact_store,
        script=script,
    )


def live_gateway(
    trace: ExecutionTrace,
    transport: Callable[..., Any],
    *,
    artifact_store: EncryptedArtifactStorePort,
    provider: Any,
    model: str,
    allowlist: Optional[ModelAllowlist] = None,
    prices: Optional[PriceTable] = None,
    budget_microusd: int = DEFAULT_BUDGET_MICROUSD,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    pricing_clock: Callable[[], str] = utc_now,
    budget_ledger: BudgetLedger | None = None,
) -> TracedGateway:
    """The live counterpart, kept separate so neither can be mistaken for the other.

    **The factory owns both barriers.** ``transport`` is the raw socket; this
    wraps it in `DurableDispatchTransport` itself. An earlier version passed the
    caller's transport straight into the gateway, so a perfectly ordinary live
    transport dispatched and returned with *no intent record and no response
    record* -- a paid call leaving no trace at all, on the only supported live
    path. The tests did not catch it because each of them wrapped the transport by
    hand before calling this, which is exactly the arrangement a caller cannot be
    relied on to repeat. Barriers that depend on the caller remembering them are
    not barriers.

    An already-wrapped transport is refused rather than wrapped twice: double
    wrapping writes two intent records per dispatch, which recovery would read as
    two attempts and now correctly calls malformed.

    What still cannot be closed here is the socket itself. A live transport is an
    arbitrary callable by definition, so `_refuse_scripted` is best-effort and is
    labelled as such -- a closure hides a scripted transport from it exactly as it
    did from the predicate that was removed. Nothing depends on it: fixture
    confinement is guaranteed by construction in `fixture_gateway`, not by
    recognising fakes.
    """
    if trace.run_mode is not RunMode.LIVE:
        raise RunModeRefusal(
            f"live_gateway requires a trace opened in LIVE mode; this trace "
            f"declared {trace.run_mode.value!r}"
        )
    if isinstance(transport, DurableDispatchTransport):
        raise RunModeRefusal(
            "live_gateway wraps the transport in its own durability barriers; "
            "pass the raw socket, not a DurableDispatchTransport. Wrapping twice "
            "writes two intent records for one dispatch"
        )
    _refuse_scripted(transport)
    durable = DurableDispatchTransport(
        trace, transport, artifact_store=artifact_store, live=True
    )
    confined = _confined_gateway(
        durable,
        mode=RunMode.LIVE,
        provider=provider,
        model=model,
        scripted_transport=False,
        allowlist=allowlist or ModelAllowlist.builtin(),
        prices=prices if prices is not None else PriceTable.builtin(),
        budget_microusd=budget_microusd,
        max_output_tokens=max_output_tokens,
        pricing_clock=pricing_clock,
        budget_ledger=budget_ledger,
    )
    return TracedGateway(trace, confined)


def _refuse_scripted(transport: Callable[..., Any]) -> None:
    """Best-effort: refuse a transport that is *visibly* scripted.

    Not a guarantee, and not relied on. Kept because the obvious mistake --
    handing `live_gateway` the fixture's own transport -- is worth catching, and
    catching it costs two `isinstance` calls.
    """
    seen: set[int] = set()
    current: object = transport
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, ScriptedTransport):
            raise RunModeRefusal(
                "a scripted transport may not be used for live execution; "
                "build fixtures with fixture_gateway()"
            )
        current = getattr(current, "inner", None)
