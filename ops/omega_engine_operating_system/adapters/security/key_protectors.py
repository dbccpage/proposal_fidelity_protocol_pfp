"""Current-user live key protection and an explicit fixture-only adapter.

Protected bytes are opaque to this module's callers. Neither implementation
logs, serializes, or exposes its secret material. AuthorityEffect: None.
"""

from __future__ import annotations

import ctypes
import hmac
import secrets
import sys
from ctypes import wintypes

from ...application import SecurityPortError

_FIXTURE_DOMAIN = b"omega.oeos.fixture-protector.v1\x00"
_DPAPI_DESCRIPTION = "AnomalonPy OEOS artifact"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


def _exact_bytes(value: object, field: str) -> bytes:
    if type(value) is not bytes:
        raise SecurityPortError(
            "INVALID_PROTECTOR_INPUT", f"{field} must be exact bytes"
        )
    return value


class FixtureOnlyAeadProtector:
    """Small authenticated test double that is forbidden in live composition."""

    fixture_only = True
    protector_id = "fixture-only-hmac-stream.v1"

    def __init__(self, key: bytes) -> None:
        key = _exact_bytes(key, "key")
        if len(key) < 32:
            raise SecurityPortError("FIXTURE_KEY_TOO_SHORT", "fixture key is too short")
        self._key = key

    def _stream(self, nonce: bytes, entropy: bytes, length: int) -> bytes:
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            stream.extend(
                hmac.digest(
                    self._key,
                    _FIXTURE_DOMAIN
                    + b"stream\x00"
                    + entropy
                    + nonce
                    + counter.to_bytes(8, "big"),
                    "sha256",
                )
            )
            counter += 1
        return bytes(stream[:length])

    def protect(self, plaintext: bytes, *, entropy: bytes) -> bytes:
        plaintext = _exact_bytes(plaintext, "plaintext")
        entropy = _exact_bytes(entropy, "entropy")
        nonce = secrets.token_bytes(32)
        stream = self._stream(nonce, entropy, len(plaintext))
        ciphertext = bytes(left ^ right for left, right in zip(plaintext, stream))
        tag = hmac.digest(
            self._key,
            _FIXTURE_DOMAIN + b"tag\x00" + entropy + nonce + ciphertext,
            "sha256",
        )
        return nonce + ciphertext + tag

    def unprotect(self, protected: bytes, *, entropy: bytes) -> bytes:
        protected = _exact_bytes(protected, "protected")
        entropy = _exact_bytes(entropy, "entropy")
        if len(protected) < 64:
            raise SecurityPortError(
                "PROTECTED_PAYLOAD_INVALID", "protected payload is truncated"
            )
        nonce, body = protected[:32], protected[32:]
        ciphertext, supplied_tag = body[:-32], body[-32:]
        expected_tag = hmac.digest(
            self._key,
            _FIXTURE_DOMAIN + b"tag\x00" + entropy + nonce + ciphertext,
            "sha256",
        )
        if not hmac.compare_digest(supplied_tag, expected_tag):
            raise SecurityPortError(
                "PROTECTED_PAYLOAD_AUTHENTICATION_FAILED",
                "protected payload authentication failed",
            )
        stream = self._stream(nonce, entropy, len(ciphertext))
        return bytes(left ^ right for left, right in zip(ciphertext, stream))

    def diagnostic(self) -> dict[str, object]:
        return {
            "fixture_only": True,
            "protector_id": self.protector_id,
            "status": "HEALTHY",
        }


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]  # noqa: MUTABLE_CLASS_ATTRIBUTE - ctypes.Structure specification


class WindowsDpapiKeyProtector:
    """Windows DPAPI CurrentUser adapter; machine scope is never requested."""

    fixture_only = False
    protector_id = "windows-dpapi-current-user.v1"

    def __init__(self, *, context_entropy: bytes = b"omega.oeos.local.v1") -> None:
        self._context_entropy = _exact_bytes(context_entropy, "context_entropy")
        if sys.platform != "win32":
            raise SecurityPortError(
                "DPAPI_PLATFORM_UNAVAILABLE", "Windows DPAPI requires win32"
            )

    @staticmethod
    def _blob(value: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
        buffer = ctypes.create_string_buffer(value, max(1, len(value)))
        blob = _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
        return blob, buffer

    @staticmethod
    def _zero(buffer: object, length: int) -> None:
        if length:
            ctypes.memset(ctypes.addressof(buffer), 0, length)

    def _crypt(self, value: bytes, entropy: bytes, *, decrypt: bool) -> bytes:
        source_blob, source_buffer = self._blob(value)
        bound_entropy = self._context_entropy + b"\x00" + entropy
        entropy_blob, entropy_buffer = self._blob(bound_entropy)
        output_blob = _DataBlob()
        description = wintypes.LPWSTR()
        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        local_free = kernel32.LocalFree
        local_free.argtypes = [wintypes.HLOCAL]
        local_free.restype = wintypes.HLOCAL
        try:
            if decrypt:
                function = crypt32.CryptUnprotectData
                function.argtypes = [
                    ctypes.POINTER(_DataBlob),
                    ctypes.POINTER(wintypes.LPWSTR),
                    ctypes.POINTER(_DataBlob),
                    wintypes.LPVOID,
                    wintypes.LPVOID,
                    wintypes.DWORD,
                    ctypes.POINTER(_DataBlob),
                ]
                function.restype = wintypes.BOOL
                ok = function(
                    ctypes.byref(source_blob),
                    ctypes.byref(description),
                    ctypes.byref(entropy_blob),
                    None,
                    None,
                    _CRYPTPROTECT_UI_FORBIDDEN,
                    ctypes.byref(output_blob),
                )
            else:
                function = crypt32.CryptProtectData
                function.argtypes = [
                    ctypes.POINTER(_DataBlob),
                    wintypes.LPCWSTR,
                    ctypes.POINTER(_DataBlob),
                    wintypes.LPVOID,
                    wintypes.LPVOID,
                    wintypes.DWORD,
                    ctypes.POINTER(_DataBlob),
                ]
                function.restype = wintypes.BOOL
                ok = function(
                    ctypes.byref(source_blob),
                    _DPAPI_DESCRIPTION,
                    ctypes.byref(entropy_blob),
                    None,
                    None,
                    _CRYPTPROTECT_UI_FORBIDDEN,
                    ctypes.byref(output_blob),
                )
            if not ok:
                raise SecurityPortError(
                    "DPAPI_OPERATION_FAILED",
                    f"Windows DPAPI error {ctypes.get_last_error()}",
                )
            result = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            return bytes(result)
        finally:
            self._zero(source_buffer, len(value))
            self._zero(entropy_buffer, len(bound_entropy))
            if output_blob.pbData:
                ctypes.memset(output_blob.pbData, 0, output_blob.cbData)
                local_free(ctypes.cast(output_blob.pbData, wintypes.HLOCAL))
            if description:
                local_free(ctypes.cast(description, wintypes.HLOCAL))

    def protect(self, plaintext: bytes, *, entropy: bytes) -> bytes:
        return self._crypt(
            _exact_bytes(plaintext, "plaintext"),
            _exact_bytes(entropy, "entropy"),
            decrypt=False,
        )

    def unprotect(self, protected: bytes, *, entropy: bytes) -> bytes:
        return self._crypt(
            _exact_bytes(protected, "protected"),
            _exact_bytes(entropy, "entropy"),
            decrypt=True,
        )

    def diagnostic(self) -> dict[str, object]:
        return {
            "fixture_only": False,
            "protector_id": self.protector_id,
            "scope": "CurrentUser",
            "status": "HEALTHY",
        }


__all__ = ["FixtureOnlyAeadProtector", "WindowsDpapiKeyProtector"]
