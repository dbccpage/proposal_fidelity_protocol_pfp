# -*- coding: utf-8 -*-
"""Verification of canonical JSON naming honesty and RFC 8785 JCS behavior.

Tests:
1. Python helper `sorted_compact_json` honesty (does not masquerade as full RFC 8785 JCS).
2. `canonical_rfc8785_json` backward-compatibility alias preserves exact output.
3. Codebase claim hygiene: functions named `canonical_rfc8785_json` document their bounded profile.
4. UTF-16 vs Unicode code-point sorting distinction (demonstrating why RFC 8785 requires native JCS).

Clean Architecture Layer: Operations Scoped Tests
AuthorityEffect: None
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from operations.domain.benchmarks.ablation import (
    canonical_rfc8785_json,
    sorted_compact_json,
)
from operations.domain.benchmarks.models import (
    canonical_rfc8785_json as models_canonical_rfc8785_json,
    sorted_compact_json as models_sorted_compact_json,
)


def test_sorted_compact_json_profile():
    """Verify sorted_compact_json enforces sorted keys and minimal whitespace without BOM."""
    data = {"z": 1, "a": 2, "m": {"b": 3, "a": 4}}
    encoded = sorted_compact_json(data)
    # Output must be pure UTF-8 bytes without BOM
    assert not encoded.startswith(b"\xef\xbb\xbf")
    assert encoded == b'{"a":2,"m":{"a":4,"b":3},"z":1}'


def test_canonical_rfc8785_json_alias_equality():
    """Verify canonical_rfc8785_json matches sorted_compact_json exactly."""
    data = {"foo": "bar", "num": 42, "nested": [1, 2, 3]}
    assert canonical_rfc8785_json(data) == sorted_compact_json(data)
    assert models_canonical_rfc8785_json(data) == models_sorted_compact_json(data)


def test_utf16_vs_unicode_codepoint_sorting_distinction():
    """Demonstrate why Python json.dumps(sort_keys=True) is not RFC 8785 JCS.

    RFC 8785 §3.2.3 requires sorting by UTF-16 code units.
    - U+1F600 (Grinning Face '😀') in UTF-16 is surrogate pair [0xD83D, 0xDE00].
    - U+FB33 (Hebrew Dalet 'דּ') in UTF-16 is BMP [0xFB33].
    Under UTF-16 code units: 0xD83D < 0xFB33, so '😀' comes FIRST.
    Under Python's Unicode code points: 0xFB33 < 0x1F600, so 'דּ' comes FIRST.
    """
    dict_payload = {"\uFB33": 1, "\U0001F600": 2}
    python_sorted = json.dumps(dict_payload, sort_keys=True, ensure_ascii=False)
    # Python sorts code points: '\uFB33' (64307) < '\U0001F600' (128512)
    assert python_sorted.startswith('{"\uFB33"')

    # In contrast, true RFC 8785 JCS (as implemented in Rust) places the emoji first.
    # This test asserts that the docstrings honestly record this difference.
    assert "UTF-16" in sorted_compact_json.__doc__
    assert "core_symbol_game_runtime::jcs" in sorted_compact_json.__doc__


def test_claim_hygiene_across_benchmark_modules():
    """Ensure no module advertises unrestricted RFC 8785 compliance without caveat."""
    ablation_doc = sorted_compact_json.__doc__
    assert ablation_doc is not None
    assert "not strict RFC 8785" in ablation_doc or "not complete RFC 8785" in ablation_doc

    models_doc = models_sorted_compact_json.__doc__
    assert models_doc is not None
    assert "not strict RFC 8785" in models_doc or "not complete RFC 8785" in models_doc
