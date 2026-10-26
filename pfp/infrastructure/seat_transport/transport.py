"""The Symbol Game seat-transport protocol: the only route from a swarm seat to a model.

A seat transport is a callable ``SeatTurnRequestV1 -> SeatTurnReplyV1`` that declares
``protocol_id == SYMBOL_GAME_PROTOCOL_V2`` and is defined inside this package. Swarm
runtimes (Woland and its specialisations) accept nothing else, so every model call is
mediated by Symbol Game code: budgeted routing (``RoutedSeatExecutor``), the OpenRouter
turn executor, or a scripted transport that makes no network call.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Callable

from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnReplyV1, SeatTurnRequestV1

SYMBOL_GAME_PROTOCOL_V2 = "omega.symbol_game.protocol.v2"
_PACKAGE_PREFIXES = ("omega_engine_pfp.", "omega_engine_woland.infrastructure.")


def is_symbol_game_transport(candidate: object) -> bool:
    """True only for a transport defined in Symbol Game or Woland infrastructure that declares the v2 protocol."""
    return (
        getattr(candidate, "protocol_id", None) == SYMBOL_GAME_PROTOCOL_V2
        and any(type(candidate).__module__.startswith(prefix) for prefix in _PACKAGE_PREFIXES)
    )


class ScriptedSeatTransport:
    """Replays scripted seat replies with no network access (fixtures, replay, tests).

    ``script`` maps a request to a reply. It must not reach a model; callers that need a
    model use ``RoutedSeatExecutor`` or ``OpenRouterTurnExecutor``.
    """

    protocol_id = SYMBOL_GAME_PROTOCOL_V2

    def __init__(self, script: Callable[[SeatTurnRequestV1], str | SeatTurnReplyV1]) -> None:
        if not callable(script):
            raise TypeError("script must be callable")
        self._script = script

    def __call__(self, request: SeatTurnRequestV1) -> str | SeatTurnReplyV1:
        return self._script(request)


__all__ = [
    "SYMBOL_GAME_PROTOCOL_V2",
    "ScriptedSeatTransport",
    "is_symbol_game_transport",
]
