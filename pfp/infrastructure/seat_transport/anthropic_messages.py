"""The Anthropic Messages transport (Rust ``anthropic_messages`` host action) for research runs.

The provider call, the worst-case quote, the cost ceiling and raw-reply custody all run in
Rust (``omega_providers::anthropic``). A ceiling of 0 is refused before the key is read or
a socket is opened. The key comes only from ``ANTHROPIC_API_KEY`` in the environment the
host process was launched with. Prices come from dated observations the caller supplies.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from .transport import SYMBOL_GAME_PROTOCOL_V2

_LOCUS = "omega_engine_pfp.infrastructure.seat_transport.anthropic_messages"
ANTHROPIC_MAX_REPLY_BYTES = 16 * 1024 * 1024


def _retained_reference(raw: Mapping[str, Any], status: int):
    from pathlib import Path
    import re
    if (not isinstance(raw, Mapping) or not isinstance(raw.get('path'), str)
            or not raw['path'].strip() or type(raw.get('bytes')) is not int
            or not 0 <= raw['bytes'] <= ANTHROPIC_MAX_REPLY_BYTES
            or not isinstance(raw.get('sha256'), str)
            or re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}', raw['sha256']) is None
            or type(status) is not int or not 200 <= status < 300):
        raise ValueError('REPLAY_REFERENCE_INVALID')
    path = Path(raw['path'])
    if not path.is_absolute():
        raise ValueError('REPLAY_REFERENCE_INVALID: absolute retained path required')
    return path.resolve()


def read_retained_reply(raw: Mapping[str, Any], status: int) -> bytes:
    """Bound the accounting read before allocation; native replay checks it again."""
    from hashlib import sha256
    path = _retained_reference(raw, status)
    with path.open('rb') as handle:
        if path.stat().st_size != raw['bytes']:
            raise ValueError('REPLAY_RAW_MISMATCH')
        data = handle.read(ANTHROPIC_MAX_REPLY_BYTES + 1)
    if len(data) != raw['bytes'] or sha256(data).hexdigest() != raw['sha256'].removeprefix('sha256:'):
        raise ValueError('REPLAY_RAW_MISMATCH')
    return data


class AnthropicMessagesTransport:
    """Sends one rendered Messages request per call; never retries on its own."""

    protocol_id = SYMBOL_GAME_PROTOCOL_V2

    def __init__(
        self,
        *,
        observations: Sequence[Mapping[str, Any]],
        at_utc: str,
        advisor_pairings: Sequence[tuple[str, str]] = (),
        host: RustSymbolGameHost | None = None,
    ) -> None:
        self._observations = [dict(item) for item in observations]
        self._at_utc = at_utc
        self._pairings = [list(pair) for pair in advisor_pairings]
        self._host = host if host is not None else RustSymbolGameHost()

    def send(
        self,
        request: Mapping[str, Any],
        *,
        raw_dir: str,
        raw_name: str,
        ceiling_microusd: int,
        quote_only: bool = False,
    ) -> Result[Mapping[str, Any], Refusal]:
        """The host outcome: ``dispatch`` is ``NOT_SENT``, ``OUTCOME_UNKNOWN`` or ``REPLIED``."""
        response = self._host.invoke_runtime_with_file(
            "anthropic_messages",
            {
                "request": dict(request),
                "raw_dir": raw_dir,
                "raw_name": raw_name,
                "ceiling_microusd": ceiling_microusd,
                "observations": self._observations,
                "at_utc": self._at_utc,
                "advisor_pairings": self._pairings,
                "quote_only": quote_only,
            },
            file_action="anthropic_messages_file",
        )
        if isinstance(response, Err):
            return response
        envelope = response.value
        if not envelope["success"]:
            return Err(Refusal("ANTHROPIC_NATIVE_DISPATCH_FAILED", str(envelope["error"]), _LOCUS))
        reply = envelope["result"]
        if reply["refusal"] is not None:
            error = reply["refusal"]
            return Err(Refusal(error["code"], error["message"], _LOCUS))
        outcome = reply["outcome"]
        if outcome.get("dispatch") not in {"NOT_SENT", "OUTCOME_UNKNOWN", "REPLIED"}:
            return Err(
                Refusal(
                    "ANTHROPIC_OUTCOME_INVALID",
                    f"unknown dispatch {outcome.get('dispatch')!r}",
                    _LOCUS,
                )
            )
        return Ok(outcome)

    def replay(self, request: Mapping[str, Any], *, raw: Mapping[str, Any], status: int):
        """Reprice retained bytes through the same native parser; never send."""
        try:
            if not isinstance(request, Mapping):
                raise ValueError('REPLAY_REQUEST_INVALID')
            path = _retained_reference(raw, status)
        except (ValueError, TypeError, OSError, RuntimeError) as error:
            return Err(Refusal('ANTHROPIC_REPLAY_BINDING_INVALID', str(error), _LOCUS))
        response=self._host.invoke_runtime_with_file('anthropic_messages',dict(request=dict(request),
            raw_dir=str(path.parent),raw_name=path.name,ceiling_microusd=0,
            replay_raw={**raw,'status':status},observations=self._observations,
            at_utc=self._at_utc,advisor_pairings=self._pairings,quote_only=False),
            file_action='anthropic_messages_file')
        if isinstance(response,Err): return response
        envelope=response.value
        if not envelope['success']:
            return Err(Refusal('ANTHROPIC_NATIVE_REPLAY_FAILED',str(envelope['error']),_LOCUS))
        reply=envelope['result']
        if reply['refusal'] is not None:
            error=reply['refusal']; return Err(Refusal(error['code'],error['message'],_LOCUS))
        outcome=reply['outcome']
        if outcome.get('replayed') is not True or outcome.get('provider_calls')!=0:
            return Err(Refusal('ANTHROPIC_REPLAY_BINDING_INVALID','Expected read-only replay.',_LOCUS))
        return Ok(outcome)


__all__ = ["AnthropicMessagesTransport"]
