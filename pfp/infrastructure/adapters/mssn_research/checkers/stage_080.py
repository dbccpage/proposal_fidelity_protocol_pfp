"""Target checker of record for MSS-080, row 80 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 80): check exact resource and action against independent
authorization. Negative instance: a model-authored privilege escalation is
refused.

Input (closed): ``{"authority": id, "grants": [[issuer, principal, resource,
action]], "requests": [[principal, resource, action, decision]]}`` with
decision ``"allow"`` or ``"deny"``.

The independent authorization is the grant table issued by the declared
authority. A grant issued by anyone else, in particular by the principal it
empowers, is an escalation and voids the table. A request is allowed exactly
when an authority grant names its principal, resource and action verbatim:
no wildcard, prefix or containment matching. The checker recomputes every
decision and compares it with the claimed one.

Declared input class: finite grant tables from one authority; exact string
match on principal, resource and action. The authority's own identity is
taken as given; this checker does not authenticate it (that is MSS-082).

Clauses, decided in this order:

- C1 ``R080_ESCALATION``: a grant's issuer is not the authority (the level's
  negative, when the issuer is the principal itself);
- C2 ``R080_INEXACT_GRANT``: a grant's resource or action is a wildcard or a
  prefix pattern (contains ``*``);
- C3 ``R080_UNGRANTED_ALLOW``: a request is claimed allowed with no exact
  authority grant;
- C4 ``R080_DECISION_MISMATCH``: a request is claimed denied although an
  exact authority grant exists.
"""

STAGE = 80
ROW_SHA256 = "sha256:c421be89123b924f1d84a8ca696fc05a7813486f04834ca56e343b80da3a9da9"
FIELDS = ("authority", "grants", "requests")
CLAUSES = (
    ("C1", "R080_ESCALATION"),
    ("C2", "R080_INEXACT_GRANT"),
    ("C3", "R080_UNGRANTED_ALLOW"),
    ("C4", "R080_DECISION_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "authority": "root",
    "grants": [["root", "alice", "db/orders", "read"], ["alice", "alice", "db/orders", "write"]],
    "requests": [["alice", "db/orders", "write", "allow"]],
}
OWN_NEGATIVE_CODE = "R080_ESCALATION"


def _decide(payload):
    authority = _text(payload["authority"])
    grants = []
    for grant in _seq(payload["grants"]):
        _seq(grant, 4)
        grants.append(tuple(_text(part) for part in grant))
    requests = []
    for request in _seq(payload["requests"]):
        _seq(request, 4)
        _require(request[3] in ("allow", "deny"), "R_SCHEMA")
        requests.append(tuple(_text(part) for part in request))
    _require(requests, "R_SCHEMA")
    for issuer, _, _, _ in grants:
        _require(issuer == authority, "R080_ESCALATION")
    for _, _, resource, action in grants:
        _require("*" not in resource and "*" not in action, "R080_INEXACT_GRANT")
    granted = {(principal, resource, action) for _, principal, resource, action in grants}
    for principal, resource, action, decision in requests:
        if decision == "allow":
            _require((principal, resource, action) in granted, "R080_UNGRANTED_ALLOW")
    for principal, resource, action, decision in requests:
        if decision == "deny":
            _require((principal, resource, action) not in granted, "R080_DECISION_MISMATCH")
