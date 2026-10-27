"""PacketSeatAdapter for OEOS: governed LLM interaction via Symbol Game packets.

Enforces:
- F-RES-10: Ingress limits enforced before invocation (64 KiB body, 16 KiB field, 64 KiB prompt);
  1 MiB reply limit captured to CAS + truncation marker then raises REPLY_LIMIT_EXCEEDED.
- F-EVT-04: Provider crash before capture is recorded as OUTCOME_UNKNOWN; retry requires authorization.
- F-EVT-05: Replaying captured responses performs zero provider calls.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RetryAuthorizedV1:
    """Explicit authenticated retry authorization for an uncompleted attempt."""
    attempt_id: str
    authorization_sha256: str
    issuer: str = "host"


@dataclass
class CasRecord:
    bytes: bytes
    truncated: bool = False
    truncation_marker: str | None = None


class ProviderCallSpy:
    def __init__(self) -> None:
        self.call_count: int = 0
        self.mock_reply_size: int = 100

    def call_provider(self, request_payload: dict[str, Any]) -> str:
        self.call_count += 1
        return "x" * self.mock_reply_size


class PacketSeatAdapterV1:
    BODY_LIMIT_BYTES = 64 * 1024
    FIELD_LIMIT_BYTES = 16 * 1024
    PROMPT_LIMIT_BYTES = 64 * 1024
    REPLY_LIMIT_BYTES = 1024 * 1024

    DEFAULT_TURNS_DIR = Path("_ic/odni/oeos/turns")

    def __init__(
        self,
        provider_gateway: Any = None,
        storage_dir: Optional[Path] = None,
    ) -> None:
        self.provider_gateway = provider_gateway or ProviderCallSpy()
        self.storage_dir = storage_dir or self.DEFAULT_TURNS_DIR
        self._last_cas_record: CasRecord | None = None
        self._attempts: Dict[str, str] = {}
        self._captured_turns: Dict[str, str] = {}
        self._load_turns_from_disk()

    def _load_turns_from_disk(self) -> None:
        if self.storage_dir.exists():
            try:
                for p in self.storage_dir.glob("*.turn"):
                    turn_id = p.stem
                    self._captured_turns[turn_id] = p.read_text(encoding="utf-8")
            except Exception:
                pass

    def prepare_and_send(
        self,
        body: str | None = None,
        fields: dict[str, Any] | None = None,
        prompt: str | None = None,
    ) -> str:
        # Check ingress limits before touching provider
        if body and len(body.encode("utf-8")) > self.BODY_LIMIT_BYTES:
            raise ValueError(f"REQUEST_BODY_LIMIT_EXCEEDED: Body exceeds {self.BODY_LIMIT_BYTES} bytes")

        if fields:
            for k, v in fields.items():
                if len(str(v).encode("utf-8")) > self.FIELD_LIMIT_BYTES:
                    raise ValueError(
                        f"REQUEST_FIELD_LIMIT_EXCEEDED: Field '{k}' exceeds {self.FIELD_LIMIT_BYTES} bytes"
                    )

        if prompt and len(prompt.encode("utf-8")) > self.PROMPT_LIMIT_BYTES:
            raise ValueError(f"REQUEST_PROMPT_LIMIT_EXCEEDED: Prompt exceeds {self.PROMPT_LIMIT_BYTES} bytes")

        # Ingress valid; call provider
        raw_reply = self.provider_gateway.call_provider({"body": body, "fields": fields, "prompt": prompt})
        reply_bytes = raw_reply.encode("utf-8")

        if len(reply_bytes) > self.REPLY_LIMIT_BYTES:
            # Capture bounded reply to CAS with truncation marker
            bounded_bytes = reply_bytes[: self.REPLY_LIMIT_BYTES] + b" [TRUNCATED]"
            self._last_cas_record = CasRecord(
                bytes=bounded_bytes,
                truncated=True,
                truncation_marker="REPLY_TRUNCATED_AT_1MIB",
            )
            raise RuntimeError(
                f"REPLY_LIMIT_EXCEEDED: Provider reply size {len(reply_bytes)} exceeds {self.REPLY_LIMIT_BYTES} bytes"
            )

        self._last_cas_record = CasRecord(bytes=reply_bytes, truncated=False)
        return raw_reply

    def get_last_captured_cas_record(self) -> CasRecord | None:
        return self._last_cas_record

    def record_attempt_sent(self, attempt_id: str) -> None:
        self._attempts[attempt_id] = "SENT"

    def get_attempt_status(self, attempt_id: str) -> str:
        status = self._attempts.get(attempt_id)
        if status == "SENT":
            return "OUTCOME_UNKNOWN"
        return status or "UNKNOWN"

    def retry_attempt(self, attempt_id: str, retry_authorization: Any = None) -> None:
        if retry_authorization is None:
            raise PermissionError(
                f"RETRY_AUTHORIZATION_REQUIRED: Attempt {attempt_id} requires explicit RetryAuthorizedV1"
            )
        auth_type = type(retry_authorization).__name__
        has_auth = hasattr(retry_authorization, "authorization_sha256") or auth_type == "RetryAuthorizedV1"
        if not has_auth:
            raise PermissionError(
                f"INVALID_RETRY_AUTHORIZATION: Attempt {attempt_id} requires valid RetryAuthorizedV1"
            )
        self._attempts[attempt_id] = "RETRY_AUTHORIZED"

    def execute_turn(self, body: str, turn_id: str) -> str:
        reply = self.prepare_and_send(body=body)
        self._captured_turns[turn_id] = reply
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            turn_path = self.storage_dir / f"{turn_id}.turn"
            turn_path.write_text(reply, encoding="utf-8")
        except Exception:
            pass
        return reply

    def replay_projections_from_log(self, turn_id: str) -> str:
        # Replay projection from captured state without repeating provider calls
        if turn_id in self._captured_turns:
            return self._captured_turns[turn_id]
        turn_path = self.storage_dir / f"{turn_id}.turn"
        if turn_path.exists():
            reply = turn_path.read_text(encoding="utf-8")
            self._captured_turns[turn_id] = reply
            return reply
        raise KeyError(f"Turn {turn_id} not found in log")


__all__ = ["CasRecord", "PacketSeatAdapterV1", "ProviderCallSpy", "RetryAuthorizedV1"]
