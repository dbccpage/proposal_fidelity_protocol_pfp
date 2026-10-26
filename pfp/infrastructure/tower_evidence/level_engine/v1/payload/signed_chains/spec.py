"""A body is acted on only after its digest and a chain of signed keys are
checked: the claimed digest must be the digest of the body; the chain must
start at the one root this level pins; each key after the root is vouched
for by the key before it, which must be allowed to vouch; the last key must
be allowed to act on the aim; and every signature must verify.

The claim: one body (a text), one sum (a digest, the claimed digest of the
body), one aim (a text, what the body is for), keys (each carrying its
modulus, a natural) with their powers (each carrying its exponent), grants
(each a text a key is allowed) and marks (each carrying a signature, a
natural); ``covers(d, b)``, ``aims(d, a)``, ``marked(d, m)`` (the sum's
signature), ``root(k)``, ``raised(k, p)``, ``may(k, g)`` and
``vouched(k, m)`` (the signature on key ``k``'s grant).  The chain is the
root followed by the other keys in declared order; a key's grants are read
in declared order.

Declared conventions, supplied and classified in the restatement: the pinned
root (its modulus and exponent, allowed ``certify``); a key may vouch when it
is allowed ``certify``, and may act on aim ``t`` when it is allowed
``release:`` followed by ``t``; the text a key's signature covers is the
canonical JSON of ``{"e", "n", "scope"}`` (its exponent, its modulus, its
grants), the text the sum's signature covers is the canonical JSON of
``{"digest", "target"}`` (the sum written ``sha256:<hex>``, the aim); the
digest of a body is the SHA-256 of its bytes; a signature ``s`` by key
``(n, e)`` on a text verifies when ``0 < s < n`` and ``s^e mod n`` is the
text's SHA-256, read as a natural, mod ``n`` (``signature_verifies``).

Relational clauses, carried by derivability over the hosted claim:
``digest_marked`` (the refused case: a digest with no signature),
``sum_given``, ``one_sum``, ``covers_given``, ``one_body``, ``aims_given``,
``one_aim``, ``one_sum_mark``, ``marked_typed``, ``covers_typed``,
``aims_typed``, ``root_named``, ``one_root``, ``root_typed``,
``keys_raised``, ``one_power``, ``raised_typed``, ``root_unvouched``,
``root_ungranted``, ``one_mark``, ``vouched_typed`` and ``may_typed``.

Decoded clauses, decided outside the grammar: ``digest_recomputed``,
``root_pinned``, ``grants_hold`` and ``signatures_verify`` (every key after
the root carries a signature, and every signature present verifies; that
the sum carries one is ``digest_marked``'s, decided natively).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.exact.digest import canonical_json, sha256, signature_verifies
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure, fmt_digest
from payload.lists import nat
from payload.shared import rows

CHALLENGE_ID = "signed_chains"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("digest_recomputed", "root_pinned", "grants_hold", "signatures_verify")

# The one root this level trusts: supplied here, never read from the claim.
PINNED_ROOT = (75109708789963778472059308396135863269, 65537)
PINNED_GRANTS = ("certify",)
VOUCH = "certify"
ACT = "release:"


def _key(fs: FiniteStructure, k: int) -> tuple[int, int]:
    powers = [p for kk, p in rows(fs, "raised") if kk == k]
    return nat(fs, k), (nat(fs, powers[0]) if len(powers) == 1 else -1)


def _grants(fs: FiniteStructure, k: int) -> list[str] | None:
    mine = {g for kk, g in rows(fs, "may") if kk == k}
    out = [fs.text(g) for g in fs.elements("grant") if g in mine]
    return None if any(t is None for t in out) else [t for t in out if t is not None]


def chain(fs: FiniteStructure) -> list[int]:
    """The root, then the other keys in declared order."""
    roots = [k for (k,) in rows(fs, "root")]
    return roots[:1] + [k for k in fs.elements("key") if k not in roots[:1]]


def _sum(fs: FiniteStructure) -> int:
    return fs.elements("sum")[0]


def _one(fs: FiniteStructure, name: str, first: int) -> int | None:
    got = [b for a, b in rows(fs, name) if a == first]
    return got[0] if len(got) == 1 else None


def pinned(fs: FiniteStructure) -> bool:
    ks = chain(fs)
    return bool(ks) and _key(fs, ks[0]) == PINNED_ROOT


def grants_of(fs: FiniteStructure, k: int, first: bool) -> list[str] | None:
    """A key's grants; the root's are the pin's, and only when it is pinned."""
    if first:
        return list(PINNED_GRANTS) if pinned(fs) else []
    return _grants(fs, k)


def digest_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    b = _one(fs, "covers", _sum(fs))
    text = None if b is None else fs.text(b)
    return text is not None and fs.digest(_sum(fs)) == sha256(text.encode("ascii"))


def root_pinned(fs: FiniteStructure, _o: Oracle) -> bool:
    return pinned(fs)


def grants_hold(fs: FiniteStructure, _o: Oracle) -> bool:
    ks = chain(fs)
    a = _one(fs, "aims", _sum(fs))
    aim = None if a is None else fs.text(a)
    held = [grants_of(fs, k, i == 0) for i, k in enumerate(ks)]
    if aim is None or not ks or any(g is None for g in held):
        return False
    return all(VOUCH in (g or []) for g in held[:-1]) and ACT + aim in (held[-1] or [])


def signatures_verify(fs: FiniteStructure, _o: Oracle) -> bool:
    ks = chain(fs)
    if not ks:
        return False
    for issuer, k in zip(ks, ks[1:]):
        n, e = _key(fs, issuer)
        kn, ke = _key(fs, k)
        m = _one(fs, "vouched", k)
        grants = _grants(fs, k)
        if m is None or grants is None or kn < 0 or ke < 0:
            return False
        if not signature_verifies(n, e, nat(fs, m), canonical_json({"e": ke, "n": kn, "scope": grants})):
            return False
    d, a, m = _sum(fs), _one(fs, "aims", _sum(fs)), _one(fs, "marked", _sum(fs))
    if m is None:
        return True  # an unsigned sum is refused by digest_marked, natively
    digest, aim = fs.digest(d), None if a is None else fs.text(a)
    if digest is None or aim is None:
        return False
    n, e = _key(fs, ks[-1])
    return signature_verifies(n, e, nat(fs, m), canonical_json({"digest": fmt_digest(digest), "target": aim}))


def describe(fs: FiniteStructure) -> dict[str, object]:
    b = _one(fs, "covers", _sum(fs))
    text = None if b is None else fs.text(b)
    return {"body_digest": None if text is None else fmt_digest(sha256(text.encode("ascii"))),
            "chain": [str(nat(fs, k)) for k in chain(fs)]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    body, sm, aim, key, power, grant, mark = (e.form("body"), e.form("sum"), e.form("aim"), e.form("key"),
                                              e.form("power"), e.form("grant"), e.form("mark"))
    covers, aims, marked, root, raised, may, vouched = (e.form("covers"), e.form("aims"), e.form("marked"),
                                                        e.form("root"), e.form("raised"), e.form("may"),
                                                        e.form("vouched"))
    return Compiled(
        (
            Total("digest_marked", ((sm, ("d",)),), ((marked, ("d", "m")),)),
            Total("sum_given", (), ((sm, ("d",)),)),
            Functional("one_sum", sm, 0),
            Total("covers_given", ((sm, ("d",)),), ((covers, ("d", "b")),)),
            Functional("one_body", covers, 1),
            Total("aims_given", ((sm, ("d",)),), ((aims, ("d", "a")),)),
            Functional("one_aim", aims, 1),
            Functional("one_sum_mark", marked, 1),
            Closure("marked_typed", ((marked, ("d", "m")),), ((sm, ("d",)), (mark, ("m",)))),
            Closure("covers_typed", ((covers, ("d", "b")),), ((body, ("b",)),)),
            Closure("aims_typed", ((aims, ("d", "a")),), ((aim, ("a",)),)),
            Total("root_named", (), ((root, ("k",)),)),
            Functional("one_root", root, 0),
            Closure("root_typed", ((root, ("k",)),), ((key, ("k",)),)),
            Total("keys_raised", ((key, ("k",)),), ((raised, ("k", "p")),)),
            Functional("one_power", raised, 1),
            Closure("raised_typed", ((raised, ("k", "p")),), ((key, ("k",)), (power, ("p",)))),
            Forbid("root_unvouched", ((root, ("k",)), (vouched, ("k", "m")))),
            Forbid("root_ungranted", ((root, ("k",)), (may, ("k", "g")))),
            Functional("one_mark", vouched, 1),
            Closure("vouched_typed", ((vouched, ("k", "m")),), ((key, ("k",)), (mark, ("m",)))),
            Closure("may_typed", ((may, ("k", "g")),), ((key, ("k",)), (grant, ("g",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("digest_recomputed", digest_recomputed), ("root_pinned", root_pinned), ("grants_hold", grants_hold),
            ("signatures_verify", signatures_verify))),
    )
