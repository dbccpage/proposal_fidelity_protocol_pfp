"""Freeze the Python oracle's casefold/printability data before native use."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path


def rust_text(value):
    return '"' + ''.join(f"\\u{{{ord(character):x}}}" for character in value) + '"'


def main():
    folded = []
    nonprintable = []
    low = None
    fold_hash,print_hash = hashlib.sha256(),hashlib.sha256()
    for point in range(0x110000):
        character = chr(point)
        output = character.casefold()
        if output != character:
            folded.append((point,output))
        printable = character.isprintable()
        if not printable and low is None:
            low = point
        elif printable and low is not None:
            nonprintable.append((low,point-1))
            low = None
        if 0xD800 <= point <= 0xDFFF:
            continue
        encoded = output.encode("utf-8")
        code = point.to_bytes(4,"big")
        fold_hash.update(code + len(encoded).to_bytes(4,"big") + encoded)
        print_hash.update(code + bytes([printable]))
    if low is not None:
        nonprintable.append((low,0x10FFFF))
    repo = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
    root = repo / "omega_engine/crates_rs/omega_types"
    source = ["// Generated from the unchanged Python oracle by generate_rust_unicode_data.py.",
        "// Do not edit by hand. The oracle version is intentionally frozen.",
        f'pub(crate) const PYTHON_UNICODE_VERSION: &str = "{unicodedata.unidata_version}";',
        "pub(crate) const CASE_FOLD: &[(u32, &str)] = &["]
    source.extend(f"    ({point}, {rust_text(value)})," for point,value in folded)
    source.extend(["];","pub(crate) const NONPRINTABLE: &[(u32, u32)] = &["])
    source.extend(f"    ({low}, {high})," for low,high in nonprintable)
    source.append("];")
    (root/"src/python_unicode_v1.rs").write_text("\n".join(source)+"\n",encoding="utf-8")
    (root/"tests/fixtures/python_unicode_v1.json").write_text(json.dumps({
        "version":unicodedata.unidata_version,"fold_entries":len(folded),
        "nonprintable_ranges":len(nonprintable),"casefold_sha256":fold_hash.hexdigest(),
        "printability_sha256":print_hash.hexdigest()},indent=2)+"\n",encoding="utf-8")
    print(f"Frozen Unicode {unicodedata.unidata_version}: {len(folded)} fold entries, {len(nonprintable)} printability ranges and two exhaustive scalar fingerprints.")


if __name__=="__main__":
    main()
