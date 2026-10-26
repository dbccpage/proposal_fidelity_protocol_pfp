"""Content-addressed storage (CAS) for durable source artifacts.

Enforces:
- F-EVT-03: Lost or corrupted CAS bytes are detected (CAS_OBJECT_MISSING / CAS_DIGEST_MISMATCH).
- Durable on-disk persistence surviving process restart.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from typing import Dict, Optional


class ContentAddressedStorageV1:
    """Immutable content-addressed storage verifying digests upon retrieval."""

    DEFAULT_STORAGE_DIR = Path("_ic/odni/oeos/cas")

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._lock = threading.Lock()
        self.storage_dir = storage_dir or self.DEFAULT_STORAGE_DIR
        self._store: Dict[str, bytes] = {}

    def store(self, data: bytes) -> str:
        with self._lock:
            hex_digest = hashlib.sha256(data).hexdigest()
            digest = f"sha256:{hex_digest}"

            self.storage_dir.mkdir(parents=True, exist_ok=True)
            target_path = self.storage_dir / hex_digest
            if not target_path.exists():
                target_path.write_bytes(data)
            if target_path.read_bytes() != data:
                raise ValueError("CAS_DIGEST_MISMATCH: stored bytes differ from source")
            self._store[digest] = data

            return digest

    def retrieve(self, digest: str) -> bytes:
        with self._lock:
            expected_hex = digest.replace("sha256:", "")

            if digest in self._store:
                data = self._store[digest]
            else:
                file_path = self.storage_dir / expected_hex
                if not file_path.exists():
                    raise FileNotFoundError(
                        f"CAS_OBJECT_MISSING: Object with digest {digest} not found in CAS"
                    )
                data = file_path.read_bytes()
                self._store[digest] = data

            actual_hex = hashlib.sha256(data).hexdigest()
            if actual_hex != expected_hex:
                raise ValueError(
                    f"CAS_DIGEST_MISMATCH: Retrieved bytes digest {actual_hex} does not match expected {expected_hex}"
                )
            return data

    def corrupt_object_bytes_for_testing(self, digest: str) -> None:
        """Testing utility simulating storage media bit-rot or byte corruption."""
        expected_hex = digest.replace("sha256:", "")
        corrupted = b"corrupted"
        if digest in self._store:
            self._store[digest] = self._store[digest] + corrupted
        file_path = self.storage_dir / expected_hex
        if file_path.exists():
            file_path.write_bytes(file_path.read_bytes() + corrupted)


__all__ = ["ContentAddressedStorageV1"]
