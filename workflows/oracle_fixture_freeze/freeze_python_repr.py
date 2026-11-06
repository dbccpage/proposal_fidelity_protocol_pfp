"""Freeze Python string repr() vectors and an every-scalar repr fingerprint.

repr() decides quoting, escapes and which characters print raw. A native
helper that claims to reproduce it must match these vectors and the
fingerprint taken over every Unicode scalar value.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

FIXTURE_NAME = "python_repr_v1.json"

SAMPLES = ["", "plain", "'", '"', "'\"", "a\\b", "\n\r\t", "é", "é", "🙂",
           "\x00\x01\x7f", " ", " ", "​", "", "\U000f0000",
           "'with space'", '"with​space"', "\u001c\u001d\u001e\u001f"]


def scalar_fingerprint() -> str:
    """SHA-256 over (code point, length, repr bytes) for every scalar."""
    fingerprint = hashlib.sha256()
    for code in range(0x110000):
        if 0xD800 <= code <= 0xDFFF:
            continue
        encoded = repr(chr(code)).encode()
        fingerprint.update(code.to_bytes(4, "big") + len(encoded).to_bytes(4, "big") + encoded)
    return fingerprint.hexdigest()


def freeze(out_dir: Path) -> Path:
    """Write the repr oracle JSON into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / FIXTURE_NAME
    path.write_text(json.dumps({
        "unicode_version": unicodedata.unidata_version,
        "scalar_repr_sha256": scalar_fingerprint(),
        "vectors": [{"text": text, "repr": repr(text)} for text in SAMPLES],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("oracle_fixtures"),
                        help="Output directory (default: ./oracle_fixtures).")
    args = parser.parse_args()
    path = freeze(args.out)
    print(f"Frozen {len(SAMPLES)} repr vectors and one exhaustive scalar fingerprint; wrote {path}.")


if __name__ == "__main__":
    main()
