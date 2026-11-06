"""Freeze JSON truthiness and seeded float-rendering fingerprints.

Two Python behaviours that a native renderer must reproduce exactly:
bool(json.loads(raw)) for edge-case JSON values, and json.dumps() of
262,144 floats drawn from every bit pattern a seeded 64-bit linear
congruential generator produces (including NaN, infinities, subnormals
and negative zero). The float stream is summarised by one SHA-256.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

FIXTURE_NAME = "python_json_acceptance_v1.json"
SEED = 480
COUNT = 262144

RAWS = ["null", "true", "false", "0", "-0", "1", "-1", str(2**512), "0.0", "-0.0",
        "1.0", "-1.0", "1e999", "-1e999", '""', '"text"', '"\\u0000"', "[]", "[null]",
        "{}", '{"key":null}']


def float_stream_sha256(seed: int = SEED, count: int = COUNT) -> str:
    """Hash raw bits plus json.dumps of each float in the seeded stream."""
    state = seed
    digest = hashlib.sha256()
    for _ in range(count):
        state = (state * 6364136223846793005 + 1442695040888963407) % 2**64
        raw = state.to_bytes(8, "big")
        number = struct.unpack("!d", raw)[0]
        digest.update(raw)
        digest.update(json.dumps(number, ensure_ascii=False, indent=2).encode())
        digest.update(b"\x00")
    return digest.hexdigest()


def build_payload() -> dict[str, object]:
    return {
        "schema": "core.python-json-acceptance.v1",
        "freeze": "after-native-implementation",
        "truthiness": [{"input_json": raw, "output": bool(json.loads(raw))} for raw in RAWS],
        "float_stream": {"seed": SEED, "count": COUNT, "sha256": float_stream_sha256()},
        "float_special": [
            {"bits": "7ff8000000000000", "output": "NaN"},
            {"bits": "fff8000000000000", "output": "NaN"},
            {"bits": "7ff0000000000000", "output": "Infinity"},
            {"bits": "fff0000000000000", "output": "-Infinity"},
        ],
    }


def freeze(out_dir: Path) -> Path:
    """Write the acceptance JSON into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / FIXTURE_NAME
    path.write_text(json.dumps(build_payload(), indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("oracle_fixtures"),
                        help="Output directory (default: ./oracle_fixtures).")
    args = parser.parse_args()
    path = freeze(args.out)
    print(f"Acceptance: {len(RAWS)} truthiness cases, four special floats and {COUNT} seeded "
          f"float samples; sha256={hashlib.sha256(path.read_bytes()).hexdigest()}; wrote {path}.")


if __name__ == "__main__":
    main()
