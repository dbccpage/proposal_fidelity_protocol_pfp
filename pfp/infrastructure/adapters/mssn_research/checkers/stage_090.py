"""Target checker of record for MSS-090, row 90 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 90): record source coverage and scope exceptions for human
audit. Negative instance: a missing quantified clause remains an open
residual.

Input (closed): ``{"source": text, "clauses": [{"span": [start, end],
"digest": d, "link": id | null, "exception": text | null}]}``.

The clause splitter is declared here, not supplied: a clause is a maximal run
of the source between the separators ``;`` and ``.`` (each followed by white
space or the end of the text), with surrounding white space trimmed. A clause
is quantified when it contains, as a whole word and in any case, one of
``QUANTIFIERS``. A span's digest is the SHA-256 of its UTF-8 bytes.

The record must cover the source: every clause the splitter finds is recorded
once, and every record is either linked to a formal object or carries a
stated scope exception (``OPEN`` is one), never both and never neither. A
quantified clause dropped from the record is refused by name: it has to stay
visible as an open residual, not vanish.

Declared input class: ASCII source texts; the declared splitter and
quantifier list. This is not language understanding: a clause the splitter
does not separate is one clause, and a quantifier word outside the list is not
seen.

Clauses, decided in this order:

- C1 ``R090_SPAN``: a recorded span is not a clause of the splitter, or is
  recorded twice;
- C2 ``R090_SPAN_DIGEST``: a span's digest does not hash its text;
- C3 ``R090_QUANTIFIED_CLAUSE_MISSING``: a quantified clause is not recorded
  (the level's negative);
- C4 ``R090_COVERAGE_GAP``: a clause without a quantifier is not recorded;
- C5 ``R090_UNACCOUNTED``: a record has neither a link nor an exception, or
  both.
"""

import hashlib

STAGE = 90
ROW_SHA256 = "sha256:a2b3d00d34e18ec1be673ad45ad155d6fee61726f5106bcb784c293ea5a4409f"
FIELDS = ("clauses", "source")
CLAUSES = (
    ("C1", "R090_SPAN"),
    ("C2", "R090_SPAN_DIGEST"),
    ("C3", "R090_QUANTIFIED_CLAUSE_MISSING"),
    ("C4", "R090_COVERAGE_GAP"),
    ("C5", "R090_UNACCOUNTED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
QUANTIFIERS = ("all", "any", "each", "every", "exists", "no", "none", "only", "some")
_WORD = re.compile(r"[A-Za-z]+")


def split_clauses(text):
    """The declared splitter: spans [start, end) of the trimmed clauses."""
    spans = []
    start = 0
    for index, char in enumerate(text):
        if char in ";." and (index + 1 == len(text) or text[index + 1].isspace()):
            spans.append((start, index))
            start = index + 1
    spans.append((start, len(text)))
    out = []
    for low, high in spans:
        while low < high and text[low].isspace():
            low += 1
        while high > low and text[high - 1].isspace():
            high -= 1
        if low < high:
            out.append((low, high))
    return out


def span_digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def quantified(text):
    return any(word.lower() in QUANTIFIERS for word in _WORD.findall(text))


_NEGATIVE_SOURCE = "Every edge has a source; some edges are marked."
OWN_NEGATIVE = {
    "clauses": [{"digest": span_digest("Every edge has a source"), "exception": None, "link": "F1", "span": [0, 23]}],
    "source": _NEGATIVE_SOURCE,
}
OWN_NEGATIVE_CODE = "R090_QUANTIFIED_CLAUSE_MISSING"


def _decide(payload):
    source = _text(payload["source"])
    _require(source.isascii(), "R_SCHEMA")
    records = []
    for record in _seq(payload["clauses"]):
        _require(isinstance(record, dict) and set(record) == {"digest", "exception", "link", "span"}, "R_SCHEMA")
        span = _seq(record["span"], 2)
        low, high = _nat(span[0]), _nat(span[1])
        for key in ("link", "exception"):
            _require(record[key] is None or (isinstance(record[key], str) and record[key]), "R_SCHEMA")
        records.append(((low, high), _text(record["digest"]), record["link"], record["exception"]))
    _require(records, "R_SCHEMA")
    spans = split_clauses(source)
    recorded = [span for span, _, _, _ in records]
    _require(set(recorded) <= set(spans) and len(set(recorded)) == len(recorded), "R090_SPAN")
    for (low, high), digest, _, _ in records:
        _require(digest == span_digest(source[low:high]), "R090_SPAN_DIGEST")
    for low, high in spans:
        if quantified(source[low:high]):
            _require((low, high) in recorded, "R090_QUANTIFIED_CLAUSE_MISSING")
    _require(set(spans) <= set(recorded), "R090_COVERAGE_GAP")
    for _, _, link, exception in records:
        _require((link is None) != (exception is None), "R090_UNACCOUNTED")
