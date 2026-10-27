"""Freeze Python Unicode 15 upper/lower mappings as a cross-language oracle.

The fixture records full-string upper()/lower() results for hand-picked
strings, every scalar whose case mapping changes, the cased and
case-ignorable sets that drive the Greek final-sigma rule, and SHA-256
fingerprints over the whole Unicode scalar range. A native port that
claims to reproduce Python casing must match this file byte for byte.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

REQUIRED_UNICODE = "15.0.0"
FIXTURE_NAME = "python_case_v1.json"
TABLES_NAME = "python_case_v1.rs"

TEXTS = ["", "hold", "unattested", "ß ﬃ ǰ ŉ ΐ ῳ", "é é Ω中🙂\U000f0000",
         "i I ı İ", "\x00\u001c ​", "\U00010d50\U00001c89",
         "AUTHORIZED", "unknown é", "ΟΣ", "ΟΣΑ", "AΣ1A", "AΣ'1", "AΣ'A",
         "AΣ́A", "AΣ́1", "AΣᵃ1", "1ΣᵃA", "ÁΣ"]


def scan() -> dict[str, object]:
    """Walk every Unicode scalar and build the oracle payload."""
    if unicodedata.unidata_version != REQUIRED_UNICODE:
        raise ValueError(f"this oracle requires Python Unicode {REQUIRED_UNICODE}, "
                         f"found {unicodedata.unidata_version}")
    mappings: dict[str, list[tuple[int, str]]] = {"upper": [], "lower": []}
    fingerprints = {name: hashlib.sha256() for name in mappings}
    cased: list[int] = []
    ignorable: list[int] = []
    contextual = hashlib.sha256()
    for point in range(0x110000):
        if 0xD800 <= point <= 0xDFFF:
            continue
        character = chr(point)
        contextual.update(point.to_bytes(4, "big"))
        for word in ("AΣ" + character + "1", "AΣ" + character + "A", "A" + character + "Σ"):
            contextual.update(word.lower().encode() + b"\x00")
        is_cased = character.islower() or character.isupper() or character.istitle()
        if is_cased:
            cased.append(point)
        # lower() probes recover the contextual final-sigma predicates.
        if (("AΣ" + character + "1").lower()[1] == "ς" if is_cased else
                ("AΣ" + character + "A").lower()[1] == "σ"):
            ignorable.append(point)
        for name, entries in mappings.items():
            text = getattr(character, name)()
            if text != character:
                entries.append((point, text))
            fingerprints[name].update(point.to_bytes(4, "big") + text.encode() + b"\x00")
    vectors = [{"text": text, "upper": text.upper(), "lower": text.lower()} for text in TEXTS]
    return {"unicode_version": unicodedata.unidata_version,
            "mappings": mappings, "vectors": vectors,
            "cased": cased, "case_ignorable": ignorable,
            "contextual_fingerprint": contextual.hexdigest(),
            "fingerprints": {name: h.hexdigest() for name, h in fingerprints.items()}}


def render_tables(payload: dict[str, object]) -> str:
    """Render the mappings and predicate sets as Rust constant tables."""
    lines = ["//! Frozen Python Unicode 15.0.0 full casing and final-sigma predicates.",
             "//! Generated from the pre-implementation python_case_v1.json oracle."]
    mappings = payload["mappings"]
    assert isinstance(mappings, dict)
    for name, entries in mappings.items():
        lines.append(f"pub(crate) const {name.upper()}: &[(u32, &str)] = &[")
        lines.extend(f"({n}, {json.dumps(s, ensure_ascii=False)})," for n, s in entries)
        lines.append("];")
    for name, key in [("CASED", "cased"), ("CASE_IGNORABLE", "case_ignorable")]:
        points = payload[key]
        assert isinstance(points, list)
        ranges: list[list[int]] = []
        for point in points:
            if ranges and ranges[-1][1] + 1 == point:
                ranges[-1][1] = point
            else:
                ranges.append([point, point])
        lines.append(f"pub(crate) const {name}: &[(u32, u32)] = &[")
        lines.extend(f"({low}, {high})," for low, high in ranges)
        lines.append("];")
    return "\n".join(lines) + "\n"


def freeze(out_dir: Path, *, emit_tables: bool = False) -> Path:
    """Write the oracle JSON (and optionally the tables) into out_dir."""
    payload = scan()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / FIXTURE_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    if emit_tables:
        (out_dir / TABLES_NAME).write_text(render_tables(payload), encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("oracle_fixtures"),
                        help="Output directory (default: ./oracle_fixtures).")
    parser.add_argument("--emit-data", action="store_true", help="Also write the Rust tables.")
    args = parser.parse_args()
    path = freeze(args.out, emit_tables=args.emit_data)
    print(f"Frozen {len(TEXTS)} upper/lower strings, two scalar and one contextual exhaustive "
          f"fingerprints and mapping tables; Unicode {unicodedata.unidata_version}; wrote {path}.")


if __name__ == "__main__":
    main()
