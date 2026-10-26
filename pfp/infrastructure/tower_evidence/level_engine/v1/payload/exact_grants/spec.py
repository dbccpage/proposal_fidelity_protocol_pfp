"""Requests decided against an independent grant table issued by one
declared authority: a request is allowed exactly when an authority grant
names its party, resource and action verbatim.  A grant issued by anyone
else voids the table; a pattern is never a grant.

The claim: parties, resources, actions and requests (each in declared
order), ``authority(x)``, ``grants(i, p, r, a)`` (issuer ``i`` grants party
``p`` action ``a`` on resource ``r``), ``pattern(x)`` (a resource or action
name is a pattern, not a name), ``request(q, p, r, a)``, ``allow(q)`` and
``deny(q)``.

Relational clauses, all carried by derivability over the hosted claim:
``authority_given``, ``one_authority``, ``issued_by_authority`` (the refused
case: a grant not issued by the authority, such as one a party issues to
itself), ``exact_resource`` and ``exact_action`` (no grant names a
pattern), ``allow_granted`` (an allowed request has a grant naming it
verbatim), ``deny_ungranted`` (a denied request has none), ``one_request``
and the typing closures.

Nothing is decided over values: the level is answered by derivability
alone.  The authority's own identity is taken as given; it is not
authenticated here.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Total
from engine.level import Compiled, Fixture

CHALLENGE_ID = "exact_grants"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    party, res, act, req = e.form("party"), e.form("resource"), e.form("action"), e.form("request")
    auth, grants, pattern = e.form("authority"), e.form("grants"), e.form("pattern")
    request, allow, deny = e.form("request_of"), e.form("allow"), e.form("deny")
    return Compiled(
        (
            Total("authority_given", (), ((auth, ("x",)),)),
            Functional("one_authority", auth, 0),
            Closure("issued_by_authority", ((grants, ("i", "p", "r", "a")),), ((auth, ("i",)),)),
            Forbid("exact_resource", ((grants, ("i", "p", "r", "a")), (pattern, ("r",)))),
            Forbid("exact_action", ((grants, ("i", "p", "r", "a")), (pattern, ("a",)))),
            Total("allow_granted", ((request, ("q", "p", "r", "a")), (allow, ("q",))),
                  ((grants, ("i", "p", "r", "a")),)),
            Forbid("deny_ungranted", ((request, ("q", "p", "r", "a")), (deny, ("q",)), (grants, ("i", "p", "r", "a")))),
            Functional("one_request", request, 1),
            Closure("grants_typed", ((grants, ("i", "p", "r", "a")),),
                    ((party, ("i",)), (party, ("p",)), (res, ("r",)), (act, ("a",)))),
            Closure("request_typed", ((request, ("q", "p", "r", "a")),),
                    ((req, ("q",)), (party, ("p",)), (res, ("r",)), (act, ("a",)))),
        ),
    )
