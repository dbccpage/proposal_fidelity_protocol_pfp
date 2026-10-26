"""Target checker of record for MSS-015, row 15 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 15): bind verifier digest and scope before accepting any
terminal authority. Negative instance: a candidate-authored Green verdict is
rejected.

Input (closed): ``{"claim": {"items": [nat], "total": nat}, "claim_value":
"GREEN" | "RED", "scope": str, "verifier_sha256": digest, "output_sha256":
digest}``.

The host holds one pinned verifier (``HOST_VERIFIER``, a sum check, scope
``sum``). It accepts a terminal claim only after binding, in this order: the
verifier digest to the pinned one, the scope to the verifier's own scope, the
terminal to the host's own re-run, and the output digest to that re-run's
canonical output. Nothing the candidate writes about the result is read as
the result.

Clauses:

- C1 ``R015_VERIFIER_UNBOUND``: the verifier digest is not the host's pinned
  verifier (for example the candidate's own script: the negative);
- C2 ``R015_SCOPE_ESCALATION``: the declared scope is not the verifier's;
- C3 ``R015_TERMINAL_NOT_EARNED``: the declared terminal is not what the host's
  re-run gives (a default-true GREEN);
- C4 ``R015_OUTPUT_MISMATCH``: the output digest is not the digest of the
  host's re-run output.
"""

import hashlib
import json

STAGE = 15
ROW_SHA256 = "sha256:af62b613397ae066e62ddffdd49ac3a35e706610a0bb541f41ffdb6335238434"
FIELDS = ("claim", "claim_value", "output_sha256", "scope", "verifier_sha256")
CLAUSES = (
    ("C1", "R015_VERIFIER_UNBOUND"),
    ("C2", "R015_SCOPE_ESCALATION"),
    ("C3", "R015_TERMINAL_NOT_EARNED"),
    ("C4", "R015_OUTPUT_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
HOST_VERIFIER = "the_symbol_game stage-015 host verifier: sum/v1"
HOST_SCOPE = "sum"


def digest(obj):
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


HOST_VERIFIER_SHA256 = "sha256:" + hashlib.sha256(HOST_VERIFIER.encode("ascii")).hexdigest()
CANDIDATE_SCRIPT_SHA256 = "sha256:" + hashlib.sha256(b"candidate self-check: return GREEN").hexdigest()


def host_run(claim):
    """The pinned verifier's re-run: its canonical output."""
    return {"sum": sum(claim["items"]), "total": claim["total"]}


OWN_NEGATIVE = {
    "claim": {"items": [1, 2, 3], "total": 6},
    "claim_value": "GREEN",
    "output_sha256": digest({"sum": 6, "total": 6}),
    "scope": "sum",
    "verifier_sha256": CANDIDATE_SCRIPT_SHA256,
}
OWN_NEGATIVE_CODE = "R015_VERIFIER_UNBOUND"


def _decide(payload):
    claim = payload["claim"]
    _require(isinstance(claim, dict) and set(claim) == {"items", "total"}, "R_SCHEMA")
    items = [_nat(item) for item in _seq(claim["items"])]
    total = _nat(claim["total"])
    _require(items, "R_SCHEMA")
    for key in ("output_sha256", "scope", "verifier_sha256"):
        _text(payload[key])
    _require(payload["claim_value"] in ("GREEN", "RED"), "R_SCHEMA")
    _require(payload["verifier_sha256"] == HOST_VERIFIER_SHA256, "R015_VERIFIER_UNBOUND")
    _require(payload["scope"] == HOST_SCOPE, "R015_SCOPE_ESCALATION")
    output = host_run({"items": items, "total": total})
    earned = "GREEN" if output["sum"] == output["total"] else "RED"
    _require(payload["claim_value"] == earned, "R015_TERMINAL_NOT_EARNED")
    _require(payload["output_sha256"] == digest(output), "R015_OUTPUT_MISMATCH")
