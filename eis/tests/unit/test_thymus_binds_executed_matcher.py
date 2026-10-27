"""The thymus screens the predicate that executes, with a bounded regex subset.

Counterexamples from the study (`infrastructure/mssn_ports.py`,
`domain/thymus.py`):

- three of four matchers ignored `match_pattern`, while the thymus screened
  that pattern as a regex, so the screened predicate was not the executed one;
- any regex was compiled, so a pattern such as `(a+)+$` could stall the screen.
"""

from __future__ import annotations

import time

import pytest

from eis.domain.ports import MatcherBindingRefusal
from eis.domain.safe_pattern import (
    UnsafePatternRefusal,
    compile_safe_pattern,
)
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import DetectorRule
from eis.infrastructure.mssn_domains import DOMAINS
from eis.infrastructure.mssn_ports import (
    DEMO3_MATCHER_ID,
    FARM_CODES,
    FARM_MATCHER_ID,
    PHARMACY_MATCHER_ID,
    PROTOCOL_CODES,
    FarmMatcher,
    PatternMatcher,
)

PROBE = next(iter(DOMAINS.values())).probes[0]
HALLUCINATION_CODE = "AM-FSP-8-UNIVERSAL-SOLVER-CLAIM"


@pytest.mark.parametrize(
    ("pattern", "code"),
    [
        (r"(a+)+$", "PATTERN_NESTED_QUANTIFIER"),
        (r"(?:a*b)*", "PATTERN_NESTED_QUANTIFIER"),
        (r"(ab|a)*c", "PATTERN_QUANTIFIED_ALTERNATION"),
        (r"(a)\1", "PATTERN_BACKREFERENCE"),
        (r"(?P<x>a)(?P=x)", "PATTERN_BACKREFERENCE"),
        (r"a{0,5000}", "PATTERN_REPEAT_BOUND"),
        (r"(unclosed", "PATTERN_SYNTAX"),
        ("", "PATTERN_EMPTY"),
        ("x" * 300, "PATTERN_TOO_LONG"),
        (r"a{0,3}", "PATTERN_ZERO_WIDTH"),
        (r"\b", "PATTERN_ZERO_WIDTH"),
        # Review counterexamples (2026-09-29): adjacent overlapping repeats.
        (r"\w*\w*\w*\w*\w*\w*\w*!", "PATTERN_UNBOUNDED_REPEAT"),
        (r".*.*.*.*.*.*.*.*=", "PATTERN_UNBOUNDED_REPEAT"),
        # Bounded but multiplicative: the choice product bounds them.
        (r"\w{0,60}\w{0,60}\w{0,60}!", "PATTERN_CHOICE_PRODUCT"),
        ("(?:a|aa)" * 10 + "!", "PATTERN_CHOICE_PRODUCT"),
        # Even one unbounded repeat is quadratic under re.search.
        (r"\w*!", "PATTERN_UNBOUNDED_REPEAT"),
        (r"universal\s+solver", "PATTERN_UNBOUNDED_REPEAT"),
    ],
)
def test_unsafe_patterns_are_refused(pattern: str, code: str) -> None:
    with pytest.raises(UnsafePatternRefusal) as caught:
        compile_safe_pattern(pattern)
    assert caught.value.code == code


@pytest.mark.parametrize(
    "pattern",
    [
        r"verified|phi1|gamma2|certified",
        r"universal\s{1,8}solver",
        r"float\s{0,4}\(",
        r"\bdef\s{1,4}\w{1,32}",
        r"[ab]{0,16}c",
        r"\w{1,8}\s{1,8}\w{1,3}!",
    ],
)
def test_ordinary_detector_patterns_are_admitted(pattern: str) -> None:
    assert compile_safe_pattern(pattern).pattern == pattern


@pytest.mark.parametrize(
    "pattern",
    [r"\w{0,63}a{0,3}!", "(?:a|aa)" * 8 + "!", r"\w{0,15}a{0,15}!", r".{0,64}="],
)
def test_admitted_worst_cases_finish_quickly_on_long_input(pattern: str) -> None:
    """The admitted subset is linear in the subject: 50,000 characters in well under 5 s."""
    compiled = compile_safe_pattern(pattern)
    started = time.perf_counter()
    compiled.search("a" * 50_000)
    assert time.perf_counter() - started < 5.0


def test_the_thymus_refuses_a_catastrophic_pattern_quickly() -> None:
    """Counterexample: `(a+)+$` on 'aaaa...b' takes exponential time in `re`."""
    thymus = ThymusGate(["a" * 40 + "b"])
    started = time.perf_counter()
    result = thymus.evaluate_rule(DetectorRule("r", "e", r"(a+)+$"))
    assert time.perf_counter() - started < 1.0
    assert result.is_admitted is False
    assert "PATTERN_NESTED_QUANTIFIER" in result.rationale


def test_the_regex_matcher_refuses_an_unsafe_pattern() -> None:
    with pytest.raises(UnsafePatternRefusal):
        PatternMatcher().match_antigen("aaaa", (DetectorRule("r", "e", r"(a*)*"),))


def test_a_non_regex_rule_cannot_pass_the_thymus_on_an_innocuous_pattern() -> None:
    """Old behaviour: a farm rule's pattern was re.escape(code), which never occurs in
    clean text, so the thymus admitted it whatever the classifier did."""
    rule = DetectorRule(HALLUCINATION_CODE, HALLUCINATION_CODE, HALLUCINATION_CODE, matcher_id=FARM_MATCHER_ID)
    # Without the executing matcher the thymus cannot screen the rule at all.
    unbound = ThymusGate([PROBE.scripted_hallucination]).evaluate_rule(rule)
    assert unbound.is_admitted is False
    assert "THYMUS_MATCHER_UNBOUND" in unbound.rationale
    # With the classifier, a self panel the classifier fires on purges the rule.
    purged = ThymusGate([PROBE.scripted_hallucination]).evaluate_rule(rule, FarmMatcher(PROBE))
    assert purged.is_admitted is False
    assert purged.autoimmune_violations == 1
    # A clean self panel admits it.
    admitted = ThymusGate([PROBE.scripted_grounded]).evaluate_rule(rule, FarmMatcher(PROBE))
    assert admitted.is_admitted is True


def test_an_inactive_rule_is_screened_as_active() -> None:
    """An inactive rule is skipped by matchers, so it must not pass the panel vacuously."""
    rule = DetectorRule(
        HALLUCINATION_CODE,
        HALLUCINATION_CODE,
        HALLUCINATION_CODE,
        matcher_id=FARM_MATCHER_ID,
        is_active=False,
    )
    result = ThymusGate([PROBE.scripted_hallucination]).evaluate_rule(rule, FarmMatcher(PROBE))
    assert result.is_admitted is False


def test_the_thymus_refuses_a_rule_bound_to_another_matcher() -> None:
    rule = DetectorRule("r", "e", "SELF_CERTIFICATION", matcher_id=PHARMACY_MATCHER_ID)
    result = ThymusGate(["clean"]).evaluate_rule(rule, PatternMatcher())
    assert result.is_admitted is False
    assert "MATCHER_BINDING_MISMATCH" in result.rationale


def test_matchers_refuse_rules_bound_elsewhere_or_naming_missing_codes() -> None:
    with pytest.raises(MatcherBindingRefusal) as caught:
        PatternMatcher().match_antigen("x", (DetectorRule("r", "e", "x", matcher_id=FARM_MATCHER_ID),))
    assert caught.value.code == "RULE_MATCHER_MISMATCH"
    # AM-FSP-6 is targeted by the probes but has no detector.
    missing = "AM-FSP-6-UNCHECKED-CLASS-CONFLATION"
    assert missing in PROBE.targeted_antimorphisms and missing not in FARM_CODES
    with pytest.raises(MatcherBindingRefusal) as caught:
        FarmMatcher(PROBE).match_antigen(
            "text", (DetectorRule(missing, missing, missing, matcher_id=FARM_MATCHER_ID),)
        )
    assert caught.value.code == "UNKNOWN_DETECTOR_CODE"


def test_the_farm_matcher_executes_the_pattern_code() -> None:
    """The rule's pattern selects the finding; the epitope is only a label."""
    selected = FarmMatcher(PROBE).match_antigen(
        PROBE.scripted_hallucination,
        (DetectorRule("label", "my-label", HALLUCINATION_CODE, matcher_id=FARM_MATCHER_ID),),
    )
    assert [(m.epitope_name, m.pattern_matched) for m in selected] == [("my-label", HALLUCINATION_CODE)]
    other = FarmMatcher(PROBE).match_antigen(
        PROBE.scripted_hallucination,
        (DetectorRule("label", "my-label", "AM-FSP-1-PSEUDO-PROOF", matcher_id=FARM_MATCHER_ID),),
    )
    assert other == ()


def test_demo3_rules_bind_their_matcher_and_code() -> None:
    assert DEMO3_MATCHER_ID == "demo3-protocol"
    assert len(PROTOCOL_CODES) == 3
