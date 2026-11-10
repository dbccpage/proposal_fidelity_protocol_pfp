"""Pure, value-preserving transport for a closed characteristic-coefficient wire.

normalize_candidate(raw_text) returns a NORMALIZED or REFUSED receipt. Accepted
input is exactly {"coefficients": [five sparse term arrays]}; each term is
{"powers": [eJ,eDelta,eK], "q": "signed_integer_or_fraction"}. Exponents are
literal JSON integers 0..4. Rational strings allow one optional + or - on the
numerator, ASCII digits without leading zeros, and an optional / followed by an
unsigned positive denominator without leading zeros. Signed zero is explicit
zero. Whitespace, decimal/exponent notation and signs on denominators refuse.

Normalization reduces rationals, omits explicit zero monomials, sorts by powers
and serializes canonical JSON. Duplicate powers refuse BEFORE zero removal.
It never merges terms, invents coefficients, repairs a polynomial or certifies
its truth for a matrix/seed/final answer. No files, existing checkers, tests,
native engines, providers or evaluator material are imported or accessed.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import re

SCHEMA = "pfp.charpoly-wire.normalization.v1"
MAX_INPUT_BYTES = 32_768
MAX_JSON_DEPTH = 8
MAX_TERMS_PER_COEFFICIENT = 125
MAX_TOTAL_TERMS = 625
MAX_RATIONAL_BITS = 64
MAX_RATIONAL_CHARS = 42
RATIONAL = re.compile(r"[+-]?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z", re.ASCII)
PRESERVATION_SCOPE = (
    "Identical polynomial in Q[lambda,J,Delta,K] under the declared ascending-lambda "
    "and powers=[eJ,eDelta,eK] interpretation. Only representation is changed."
)


class WireRefusal(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WireRefusal("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _integer(token):
    # Numeric JSON is admitted only for the exponent grammar. Numeric q values
    # still fail their required string type. This also refuses exponent -0.
    if token not in {"0", "1", "2", "3", "4"}:
        raise WireRefusal("JSON_INTEGER_OUT_OF_PROFILE")
    return int(token)


def _no_number(_token):
    raise WireRefusal("FLOAT_OR_NONFINITE_FORBIDDEN")


def _depth(text):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise WireRefusal("JSON_DEPTH_LIMIT")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                raise WireRefusal("MALFORMED_JSON")


def _rational(text):
    if type(text) is not str:
        raise WireRefusal("RATIONAL_STRING_REQUIRED")
    if len(text) > MAX_RATIONAL_CHARS:
        raise WireRefusal("RATIONAL_CHARACTER_LIMIT")
    if RATIONAL.fullmatch(text) is None:
        raise WireRefusal("RATIONAL_GRAMMAR")
    numerator_text, separator, denominator_text = text.partition("/")
    numerator = int(numerator_text)
    denominator = int(denominator_text) if separator else 1
    if abs(numerator).bit_length() > MAX_RATIONAL_BITS or denominator.bit_length() > MAX_RATIONAL_BITS:
        raise WireRefusal("RATIONAL_COMPONENT_BIT_LIMIT")
    return Fraction(numerator, denominator)


def _normalize_coefficients(value):
    if type(value) is not dict or set(value) != {"coefficients"}:
        raise WireRefusal("CLOSED_COEFFICIENTS_OBJECT_REQUIRED")
    coefficients = value["coefficients"]
    if type(coefficients) is not list or len(coefficients) != 5:
        raise WireRefusal("FIVE_COEFFICIENT_ARRAYS_REQUIRED")
    normalized = []
    transformations = []
    total_terms = 0
    for coefficient, terms in enumerate(coefficients):
        if type(terms) is not list or len(terms) > MAX_TERMS_PER_COEFFICIENT:
            raise WireRefusal("COEFFICIENT_TERM_LIMIT")
        total_terms += len(terms)
        if total_terms > MAX_TOTAL_TERMS:
            raise WireRefusal("TOTAL_TERM_LIMIT")
        seen = set()
        kept = []
        for index, term in enumerate(terms):
            if type(term) is not dict or set(term) != {"powers", "q"}:
                raise WireRefusal("CLOSED_MONOMIAL_OBJECT_REQUIRED")
            powers = term["powers"]
            if (type(powers) is not list or len(powers) != 3 or
                any(type(e) is not int or not 0 <= e <= 4 for e in powers)):
                raise WireRefusal("THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED")
            exponent = tuple(powers)
            if exponent in seen:
                raise WireRefusal("DUPLICATE_POWERS")
            seen.add(exponent)
            q = _rational(term["q"])
            canonical_q = str(q)
            location = {"lambda_power": coefficient, "input_term_index": index,
                        "powers": powers.copy()}
            if canonical_q != term["q"]:
                transformations.append({**location, "operation": "reduce_rational",
                                        "from_q": term["q"], "to_q": canonical_q})
            if q == 0:
                transformations.append({**location, "operation": "omit_explicit_zero",
                                        "from_q": term["q"], "value": "0"})
            else:
                kept.append({"powers": powers.copy(), "q": canonical_q})
        sorted_terms = sorted(kept, key=lambda term: tuple(term["powers"]))
        if kept != sorted_terms:
            transformations.append({"lambda_power": coefficient, "operation": "sort_monomials",
                "from_powers": [term["powers"] for term in kept],
                "to_powers": [term["powers"] for term in sorted_terms]})
        normalized.append(sorted_terms)
    if normalized[-1] != [{"powers": [0, 0, 0], "q": "1"}]:
        raise WireRefusal("NONMONIC_LEADING_COEFFICIENT")
    return {"coefficients": normalized}, transformations


def normalize_candidate(raw_text):
    """Normalize a bounded UTF-8 JSON string without changing its polynomial.

    SHA256 values bind exact UTF-8 bytes, without a trailing newline. Rejected
    nontext/invalid-UTF8/over-character-limit inputs have no original SHA; no
    normalized SHA or semantic-preservation claim is issued on any refusal.
    """
    receipt = {"schema": SCHEMA, "status": "REFUSED", "accepted": False,
        "original_sha256": None, "normalized_sha256": None, "normalized_json": None,
        "transformations": [], "semantic_preservation": None,
        "scope": PRESERVATION_SCOPE,
        "not_established": ["correct characteristic polynomial", "matrix or seed binding",
                            "native verification", "final-answer correctness"],
        "limits": {"input_utf8_bytes": MAX_INPUT_BYTES, "json_depth": MAX_JSON_DEPTH,
            "coefficient_arrays": 5, "terms_per_coefficient": MAX_TERMS_PER_COEFFICIENT,
            "total_terms": MAX_TOTAL_TERMS, "rational_component_bits": MAX_RATIONAL_BITS,
            "rational_string_characters": MAX_RATIONAL_CHARS, "exponents": "3 exact integers 0..4"}}
    try:
        if type(raw_text) is not str:
            raise WireRefusal("TEXT_REQUIRED")
        if len(raw_text) > MAX_INPUT_BYTES:
            raise WireRefusal("INPUT_CHARACTER_LIMIT")
        try:
            raw = raw_text.encode("utf-8")
        except UnicodeEncodeError:
            raise WireRefusal("UTF8_REQUIRED") from None
        receipt["original_sha256"] = _sha(raw)
        receipt["original_utf8_bytes"] = len(raw)
        if len(raw) > MAX_INPUT_BYTES:
            raise WireRefusal("INPUT_BYTE_LIMIT")
        _depth(raw_text)
        try:
            parsed = json.loads(raw_text, object_pairs_hook=_object, parse_int=_integer,
                                parse_float=_no_number, parse_constant=_no_number)
        except (json.JSONDecodeError, RecursionError):
            raise WireRefusal("MALFORMED_JSON") from None
        normalized, transformations = _normalize_coefficients(parsed)
        serialized = _canonical(normalized)
        encoded = serialized.encode("utf-8")
        if len(encoded) > MAX_INPUT_BYTES:
            raise WireRefusal("NORMALIZED_BYTE_LIMIT")
        transformations.append({"operation": "canonical_json_serialization",
            "profile": "sorted-object-keys,compact,ASCII-escaped,no-floats",
            "changed_bytes": raw != encoded})
        receipt.update(status="NORMALIZED", accepted=True, normalized_json=serialized,
            normalized_sha256=_sha(encoded), normalized_utf8_bytes=len(encoded),
            transformations=transformations,
            semantic_preservation={"preserved": True, "scope": PRESERVATION_SCOPE,
                "basis": ["Exact rational reduction preserves each coefficient value.",
                          "Only zero-valued monomials are removed; duplicate powers were refused.",
                          "Sorting permutes distinct monomials without changing exponents or values.",
                          "JSON spelling changes preserve the same closed data structure."]})
    except WireRefusal as exc:
        receipt["refusal"] = {"code": str(exc)}
    return receipt
