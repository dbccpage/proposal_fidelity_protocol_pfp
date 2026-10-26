"""Target checker of record for MSS-017, row 17 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 17): decode with local tag dispatch and hash exact canonical
bytes. Negative instance: a changed body with unchanged digest is rejected.

Input (closed): ``{"containers": [{"tag": str, "body": object, "digest":
"sha256:<hex>"}]}``.

Tag dispatch is local and closed: ``t0`` decodes ``{"n": nat}``; ``t1``
decodes ``{"word": binary string}``. There is no default decoder. Each decode
is re-encoded and must round-trip to the body. The digest is SHA-256 over the
canonical bytes of ``{"body": body, "tag": tag}``: JSON with sorted keys, no
whitespace, ASCII (grammar 17: SHA-256, not CRC32).

Clauses:

- C1 ``R017_DIGEST_MISMATCH``: the digest is not the SHA-256 of the canonical
  bytes (the negative: a changed body under an unchanged digest);
- C2 ``R017_UNKNOWN_TAG``: the tag has no registered decoder;
- C3 ``R017_DECODE_FAILED``: the body does not decode under its tag, or does
  not round-trip.
"""

import hashlib
import json

STAGE = 17
ROW_SHA256 = "sha256:4a0d70c355e23107a0506b41999da4124d14fd6fac5d6af492b02c6cecc6ebb6"
FIELDS = ("containers",)
CLAUSES = (
    ("C1", "R017_DIGEST_MISMATCH"),
    ("C2", "R017_UNKNOWN_TAG"),
    ("C3", "R017_DECODE_FAILED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_WORD = re.compile(r"[01]+")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def container_digest(tag, body):
    return "sha256:" + hashlib.sha256(canonical({"body": body, "tag": tag})).hexdigest()


def _decode_t0(body):
    _require(isinstance(body, dict) and set(body) == {"n"}, "R017_DECODE_FAILED")
    value = body["n"]
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, "R017_DECODE_FAILED")
    return value


def _decode_t1(body):
    _require(isinstance(body, dict) and set(body) == {"word"}, "R017_DECODE_FAILED")
    value = body["word"]
    _require(isinstance(value, str) and _WORD.fullmatch(value) is not None, "R017_DECODE_FAILED")
    return value


DIALECTS = {
    "t0": (_decode_t0, lambda value: {"n": value}),
    "t1": (_decode_t1, lambda value: {"word": value}),
}
OWN_NEGATIVE = {"containers": [{"body": {"n": 6}, "digest": container_digest("t0", {"n": 5}), "tag": "t0"}]}
OWN_NEGATIVE_CODE = "R017_DIGEST_MISMATCH"


def _decide(payload):
    containers = _seq(payload["containers"])
    _require(containers, "R_SCHEMA")
    for container in containers:
        _require(isinstance(container, dict) and set(container) == {"body", "digest", "tag"}, "R_SCHEMA")
        tag = _text(container["tag"])
        _text(container["digest"])
        _require(tag in DIALECTS, "R017_UNKNOWN_TAG")
        decode, encode = DIALECTS[tag]
        _require(encode(decode(container["body"])) == container["body"], "R017_DECODE_FAILED")
        _require(container["digest"] == container_digest(tag, container["body"]), "R017_DIGEST_MISMATCH")
