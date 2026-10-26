"""Reproduce the shared finite Unicode casefold contract using the pinned interpreter."""
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if sys.version_info[:3] != (3, 13, 11) or unicodedata.unidata_version != "15.1.0":
    raise RuntimeError("casefold producer must be CPython3.13.11 / Unicode15.1.0")
value = {
    "schema": "omega.ic.casefold.v1",
    "unicode_version": unicodedata.unidata_version,
    "producer": "CPython 3.13.11 str.casefold",
    "mappings": {str(code): chr(code).casefold() for code in range(0x110000)
                 if chr(code).casefold() != chr(code)},
}
raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                  allow_nan=False) + "\n").encode("ascii")
path = ROOT / "omega_engine_governance/_types/ic_casefold_v15_1.json"
path.write_bytes(raw)
print(json.dumps({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw), "mappings": len(value["mappings"]),
                  "unicode_version": unicodedata.unidata_version, "python": sys.version}))
