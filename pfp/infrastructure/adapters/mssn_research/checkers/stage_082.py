"""Target checker of record for MSS-082, row 82 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 82): check digest and trusted signature chain before action.
Negative instance: an unsigned checksum is not an authenticated source.

Input (closed): ``{"artifact": text, "manifest": {"digest": d, "target": t,
"signature": s | null}, "chain": [{"n": n, "e": e, "scope": [str],
"signature": s}], "root": {"n": n, "e": e}}``.

Declared scheme: textbook RSA over SHA-256. The message of a certificate is
the canonical JSON of ``{"e", "n", "scope"}``; the message of a manifest is
the canonical JSON of ``{"digest", "target"}`` (sorted keys, no whitespace,
ASCII). A signature s by key (n, e) on message m verifies when
0 < s < n and s^e mod n equals SHA-256(m), read as an integer, mod n.

The trust anchor is pinned in this file (``TRUST_ROOTS``), never taken from
the payload: the payload names its root, and a root not pinned here is
refused. Certificate i is signed by the key before it (the root for i = 0),
which must carry the scope ``certify``; the manifest is signed by the last key,
which must carry ``release:<target>``. The digest is recomputed over the
artifact's UTF-8 bytes before any signature is read.

Declared input class: chains of textbook-RSA certificates under the pinned
toy root. The root's private exponent is published in the test fixtures, so a
PASS says the chain verifies under the declared scheme; it says nothing about
unforgeability. No revocation, expiry or padding scheme is modelled.

Clauses, decided in this order:

- C1 ``R082_UNSIGNED_CHECKSUM``: the manifest carries a digest but no
  signature (the level's negative);
- C2 ``R082_DIGEST_MISMATCH``: the digest is not the SHA-256 of the artifact;
- C3 ``R082_UNTRUSTED_ROOT``: the named root is not a pinned trust anchor;
- C4 ``R082_SCOPE``: a certificate's issuer lacks ``certify``, or the
  manifest's signer lacks ``release:<target>``;
- C5 ``R082_BAD_SIGNATURE``: a certificate's or the manifest's signature does
  not verify under its issuer's key.
"""

import hashlib
import json

STAGE = 82
ROW_SHA256 = "sha256:d0bd683b67f58634995701b4d4b8806317d789f0b07ea8b004d1f02bb13f832a"
FIELDS = ("artifact", "chain", "manifest", "root")
CLAUSES = (
    ("C1", "R082_UNSIGNED_CHECKSUM"),
    ("C2", "R082_DIGEST_MISMATCH"),
    ("C3", "R082_UNTRUSTED_ROOT"),
    ("C4", "R082_SCOPE"),
    ("C5", "R082_BAD_SIGNATURE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
# (n, e, scope) of each pinned trust anchor: a declared toy key.
TRUST_ROOTS = ((75109708789963778472059308396135863269, 65537, ("certify",)),)


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def artifact_digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def message_value(obj, n):
    return int(hashlib.sha256(_canonical(obj)).hexdigest(), 16) % n


def verifies(signature, message, n, e):
    return isinstance(signature, int) and 0 < signature < n and pow(signature, e, n) == message_value(message, n)


# The positive's certificate, kept; only the manifest's signature is gone.
OWN_NEGATIVE = {
    "artifact": "echo release 1",
    "chain": [{"e": 65537, "n": 158578801447581928812223344597329827643, "scope": ["release:deploy/app"],
               "signature": 4454402395620503103279887124456718778}],
    "manifest": {"digest": artifact_digest("echo release 1"), "signature": None, "target": "deploy/app"},
    "root": {"e": 65537, "n": 75109708789963778472059308396135863269},
}
OWN_NEGATIVE_CODE = "R082_UNSIGNED_CHECKSUM"


def _key(value):
    _require(isinstance(value, dict), "R_SCHEMA")
    n, e = _nat(value["n"]), _nat(value["e"])
    _require(n > 2 and e > 1, "R_SCHEMA")
    return n, e


def _decide(payload):
    artifact = _text(payload["artifact"])
    manifest = payload["manifest"]
    _require(isinstance(manifest, dict) and set(manifest) == {"digest", "signature", "target"}, "R_SCHEMA")
    digest, target = _text(manifest["digest"]), _text(manifest["target"])
    root = payload["root"]
    _require(isinstance(root, dict) and set(root) == {"e", "n"}, "R_SCHEMA")
    root_n, root_e = _key(root)
    chain = []
    for link in _seq(payload["chain"]):
        _require(isinstance(link, dict) and set(link) == {"e", "n", "scope", "signature"}, "R_SCHEMA")
        n, e = _key(link)
        scope = [_text(item) for item in _seq(link["scope"])]
        chain.append((n, e, scope, _nat(link["signature"])))
    signature = manifest["signature"]
    _require(signature is not None, "R082_UNSIGNED_CHECKSUM")
    signature = _nat(signature)
    _require(digest == artifact_digest(artifact), "R082_DIGEST_MISMATCH")
    anchors = {(n, e): scope for n, e, scope in TRUST_ROOTS}
    _require((root_n, root_e) in anchors, "R082_UNTRUSTED_ROOT")
    keys = [(root_n, root_e, list(anchors.get((root_n, root_e), ())))]
    keys += [(n, e, scope) for n, e, scope, _ in chain]
    for issuer in keys[:-1]:
        _require("certify" in issuer[2], "R082_SCOPE")
    _require("release:" + target in keys[-1][2], "R082_SCOPE")
    for issuer, (n, e, scope, link_signature) in zip(keys, chain):
        message = {"e": e, "n": n, "scope": scope}
        _require(verifies(link_signature, message, issuer[0], issuer[1]), "R082_BAD_SIGNATURE")
    signer = keys[-1]
    _require(verifies(signature, {"digest": digest, "target": target}, signer[0], signer[1]), "R082_BAD_SIGNATURE")
