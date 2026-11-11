"""Regressions for the 2026-11-11 review of PR #62.

1. ``decide`` must be monotone in Signal 2: an allowlisted host failure holds
   the candidate whether or not a Signal 1 rule also matched, including when
   the match cannot be shown independent of the host evidence.
2. ``normalize_python`` salvages formatting drift without a model call and
   refuses any step it cannot show to be value-preserving.
"""
import ast
import itertools

from pfp_core import immunity as imm
from pfp_core.normalize import normalize_python
from eis.domain.value_objects import DangerSeverity, DetectorRule, Signal2Danger


def rule(rule_id, pattern):
    return DetectorRule(rule_id=rule_id, target_epitope=rule_id, match_pattern=pattern)


def spanned_danger(observer, kind, span):
    return Signal2Danger(danger_type=kind, severity=DangerSeverity.HIGH, defect_count=1,
                         evidence_digest='sha256:' + '1' * 64, observer_id=observer,
                         evidence_spans=(span,))


CODE = 'total = float(amount)\n'
RULES = [rule('no_float', 'float\\(')]


def test_overlapping_signal1_no_longer_releases_a_host_failure():
    m = imm.signal1(CODE, RULES)
    assert m and m[0].offset == 8
    danger = spanned_danger('host.public_smoke', 'REPLAY_FAILURE', (0, len(CODE)))
    alone = imm.decide([], danger)
    both = imm.decide(m, danger)
    assert alone.disposition == imm.HOLD
    assert both.disposition == imm.HOLD
    assert both.refusal_code == 'TWO_SIGNAL_COLLAPSE'
    assert both.basis.startswith('host predicate refusal')


def test_decide_is_monotone_in_signal2_over_every_combination():
    m = imm.signal1(CODE, RULES)
    dangers = [None,
               imm.host_danger('REPLAY_FAILURE', 'host.public_smoke', 'trace'),
               spanned_danger('host.ast_parse', 'MALFORMED_PAYLOAD', (0, 3)),
               spanned_danger('host.contract_check', 'PROTECTED_FIELD_VIOLATION', (8, 14)),
               spanned_danger('host.transition_table', 'REPLAY_FAILURE', (100, 200))]
    rank = {imm.PASS: 0, imm.DIAGNOSTIC: 1, imm.HOLD: 2}
    for matches, danger in itertools.product([[], m], dangers):
        d = imm.decide(matches, danger)
        if danger is not None:
            assert d.disposition == imm.HOLD, (matches, danger, d)
        assert rank[imm.decide(matches, danger).disposition] >= rank[imm.decide([], danger).disposition]


def test_non_host_danger_is_still_ignored():
    m = imm.signal1(CODE, RULES)
    forged = spanned_danger('MODEL', 'REPLAY_FAILURE', (0, len(CODE)))
    d = imm.decide(m, forged)
    assert (d.disposition, d.refusal_code) == (imm.DIAGNOSTIC, 'TWO_SIGNAL_COLLAPSE')


def test_format_quirky_candidate_is_salvaged_without_a_model_call():
    quirky = '﻿```python\r\ndef add(a, b):   \r\n    return a + b\r\n```\r\n'
    assert not _parses(quirky)
    n = normalize_python(quirky)
    assert n.parses
    assert n.steps == ('strip_bom', 'crlf_to_lf', 'unwrap_markdown_fence', 'strip_trailing_whitespace')
    assert n.text == 'def add(a, b):\n    return a + b\n'
    assert n.refused == ()


def test_value_changing_whitespace_is_refused():
    src = 'BANNER = """line   \nend"""\n'
    n = normalize_python(src)
    assert n.text == src
    assert n.refused == ('NORMALIZATION_NOT_VALUE_PRESERVING:strip_trailing_whitespace',)
    assert ast.literal_eval(ast.parse(n.text).body[0].value) == 'line   \nend'


def test_unparseable_algebra_is_not_salvaged():
    bad = '```python\ndef f(x):\n    return x +\n```\n'
    n = normalize_python(bad)
    assert not n.parses and 'unwrap_markdown_fence' not in n.steps


def _parses(text):
    try:
        ast.parse(text)
        return True
    except (SyntaxError, ValueError):
        return False
