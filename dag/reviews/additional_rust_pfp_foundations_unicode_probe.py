"""Offline finite data comparison, separate from the source-reading receipts."""
import bisect
import ctypes
import hashlib
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREFIX = pathlib.Path(__file__).with_name('additional_rust_pfp_foundations_unicode_validation.json')
names = ['python_alnum_v1.rs', 'python_case_v1.rs', 'python_unicode_v1.rs']
sources = {n: (ROOT / 'code/rust/core_types/src' / n).read_bytes() for n in names}
tables = {}
for name, raw in sources.items():
    source = raw.decode('utf-8')
    for match in re.finditer(r'pub\(crate\) const (\w+): &\[\(u32, (u32|&str)\)\] = &\[(.*?)\n\];', source, re.S):
        key, kind, body = match.groups()
        rows = []
        for line in body.splitlines():
            if not line.strip():
                continue
            row = re.fullmatch(r'\s*\((0x[0-9a-f]+|[0-9]+), (.*?)\),\s*', line)
            assert row, (key, line)
            code, value = row.groups()
            code = int(code, 16 if code.startswith('0x') else 10)
            if kind == 'u32':
                value = int(value, 16 if value.startswith('0x') else 10)
            else:
                assert value.startswith('"') and value.endswith('"')
                value = re.sub(r'\\u\{([0-9a-f]+)\}', lambda m: chr(int(m[1], 16)), value[1:-1])
                assert '\\' not in value
            rows.append((code, value))
        assert all(rows[i - 1][0] < rows[i][0] for i in range(1, len(rows)))
        if kind == 'u32':
            assert all(a <= b <= 0x10ffff for a, b in rows)
            assert all(rows[i - 1][1] < rows[i][0] for i in range(1, len(rows)))
        tables[key] = rows

assert unicodedata.unidata_version == '15.0.0', 'Use the pinned local Python 3.12 oracle'
maps = {name: dict(tables[name]) for name in ['UPPER', 'LOWER', 'CASE_FOLD']}
ranges = {name: tables[name] for name in ['ALNUM', 'CASED', 'CASE_IGNORABLE', 'NONPRINTABLE']}
starts = {name: [a for a, _ in rows] for name, rows in ranges.items()}
def member(name, code):
    index = bisect.bisect_right(starts[name], code) - 1
    return index >= 0 and code <= ranges[name][index][1]

try:
    ignorable = ctypes.pythonapi._PyUnicode_IsCaseIgnorable
    ignorable.argtypes = [ctypes.c_uint]
    ignorable.restype = ctypes.c_int
except AttributeError:
    ignorable = None
counts = {name: 0 for name in tables}
examples = {name: [] for name in tables}
scalar_count = 0
for code in range(0x110000):
    if 0xd800 <= code <= 0xdfff:
        continue
    scalar_count += 1
    char = chr(code)
    tests = {
        'UPPER': (maps['UPPER'].get(code, char), char.upper()),
        'LOWER': (maps['LOWER'].get(code, char), char.lower()),
        'CASE_FOLD': (maps['CASE_FOLD'].get(code, char), char.casefold()),
        'ALNUM': (member('ALNUM', code), char.isalnum()),
        'CASED': (member('CASED', code), char.islower() or char.isupper() or char.istitle()),
        'NONPRINTABLE': (member('NONPRINTABLE', code), not char.isprintable()),
    }
    if ignorable is not None:
        tests['CASE_IGNORABLE'] = (member('CASE_IGNORABLE', code), bool(ignorable(code)))
    for name, (actual, expected) in tests.items():
        if actual != expected:
            counts[name] += 1
            if len(examples[name]) < 10:
                examples[name].append({'code': code, 'actual': actual, 'expected': expected})
result = {
    'kind': 'exhaustive finite generated-data oracle comparison, not Rust execution or mathematical proof',
    'python': sys.version, 'executable': sys.executable, 'unicode_version': unicodedata.unidata_version,
    'source_hashes': {n: hashlib.sha256(raw).hexdigest() for n, raw in sources.items()},
    'table_sizes': {n: len(rows) for n, rows in tables.items()},
    'valid_scalars_checked': scalar_count, 'surrogates_excluded': 2048,
    'case_ignorable_private_cpython_oracle_available': ignorable is not None,
    'mismatch_counts': counts, 'mismatch_examples': examples,
    'limits': ['The Python implementation is an admitted oracle, not an independent Unicode specification proof.',
               'Only scalar mappings/properties are exhaustive; contextual string casing is owned elsewhere.',
               'No Rust compiler, provider, network or external data was used.'],
}
PREFIX.write_text(json.dumps(result, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
print(json.dumps({'scalars': scalar_count, 'mismatch_counts': counts, 'case_ignorable_checked': ignorable is not None}))
