"""Canonical bytes, finite structures, hosting and decoding, and the embargo
guard.  Each refusal is asserted by its exact code."""

from __future__ import annotations

import subprocess
from itertools import chain, combinations, product

import pytest

from engine.canon import dumps, git_blob_id, loads, sha256_tag
from engine.encoding import Encoding, certify_hosting, decode, descend, encode, value_of
from engine.errors import EmbargoRefusal, ExactError, IntakeRefusal, NonAdmissible, NonDescent, Refusal
from engine.exact.q import Q
from engine.guards import EMBARGO_LIST, ResourceBound, check_delta_size, embargo_digest, refuse, request
from engine.regimek import BASE, Stage, admit_response, host
from engine.sealed import AdmitDatum, AdmitForm, AdmitRuleAll, NewInst, Regime, replay, vendored
from engine.structure import FiniteStructure, RelSym, from_json, to_json, validate

# ---------------------------------------------------------------- canonical bytes


def test_dumps_is_canonical() -> None:
    b = dumps({"b": [1, "x", None, True], "a": {"z": 0}})
    assert b == b'{\n  "a": {\n    "z": 0\n  },\n  "b": [\n    1,\n    "x",\n    null,\n    true\n  ]\n}\n'
    assert loads(b) == {"a": {"z": 0}, "b": [1, "x", None, True]}
    assert sha256_tag(b).startswith("sha256:") and len(sha256_tag(b)) == 71


@pytest.mark.parametrize(
    ("obj", "code"),
    [({"x": 0.5}, "RR-FLOAT"), ([1, [2.0]], "RR-FLOAT"), ({1: 2}, "RR-KEY"), ({"q": Q(1, 2)}, "RR-TYPE")],
)
def test_dumps_refusals(obj: object, code: str) -> None:
    with pytest.raises(ExactError) as e:
        dumps(obj)
    assert e.value.code == code


@pytest.mark.parametrize(
    ("text", "code"), [('{"a": 0.5}', "RR-FLOAT"), ('{"a": NaN}', "RR-FLOAT"), ('{"a": 1, "a": 2}', "RR-DUPLICATE-KEY")]
)
def test_loads_refusals(text: str, code: str) -> None:
    with pytest.raises(ExactError) as e:
        loads(text)
    assert e.value.code == code


def test_git_blob_id_matches_git() -> None:
    data = b"one\ntwo\n"
    got = subprocess.run(["git", "hash-object", "--stdin"], input=data, capture_output=True, check=True).stdout
    assert git_blob_id(data) == got.decode().strip()


# ---------------------------------------------------------------- structures

EDGE = {"sorts": [["node", 2]], "symbols": [{"name": "arc", "sorts": ["node", "node"]}], "tuples": [["arc", [0, 1]]]}


def test_structure_round_trip_and_helpers() -> None:
    fs = from_json({**EDGE, "sorts": [["node", 2], ["val", 1]], "values": [[2, "3/4"]]})
    assert fs.n() == 3 and fs.elements("val") == (2,) and fs.sort_of(2) == ("val", 0)
    assert fs.value(2) == Q(3, 4) and fs.value(0) is None and fs.offset("val") == 2
    assert from_json(to_json(fs)) == fs
    with pytest.raises(IndexError):
        fs.sort_of(9)
    with pytest.raises(KeyError):
        fs.offset("nothing")


@pytest.mark.parametrize(
    ("obj", "code"),
    [
        ({}, "EMPTY_FIXTURE"),
        ({"is_valid": True}, "FLAG_ONLY_FIXTURE"),
        ({**EDGE, "passes": True}, "FLAG_ONLY_FIXTURE"),
        ([], "EMPTY_FIXTURE"),
        (None, "EMPTY_FIXTURE"),
        ({"sorts": [], "symbols": []}, "EMPTY_FIXTURE"),
        ({"sorts": [["node", 2]], "symbols": []}, "MALFORMED_FIXTURE"),
        ([["node", 2]], "MALFORMED_FIXTURE"),
        ({**EDGE, "symbols": [{"name": "arc", "sorts": ["node"], "VERIFIED": 1}]}, "FLAG_ONLY_FIXTURE"),
        ({"a": [True, {"b": False}]}, "FLAG_ONLY_FIXTURE"),
        ({**EDGE, "extra": 1}, "MALFORMED_FIXTURE"),
        ({**EDGE, "tuples": {}}, "MALFORMED_FIXTURE"),
        ({**EDGE, "sorts": [["Node", 2]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "sorts": [["node", 19]]}, "SIZE_CAP"),
        ({**EDGE, "sorts": [["node", -1]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "sorts": [["arc", 2]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "tuples": [["edge", [0, 1]]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "tuples": [["arc", [0, 1]], ["arc", [0, 1]]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "tuples": [["arc", [0, True]]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "symbols": [{"name": "arc", "sorts": ["pt"]}]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "values": [[5, "1/1"]]}, "MALFORMED_FIXTURE"),
        ({**EDGE, "values": [[0, "1/1"], [0, "2/1"]]}, "MALFORMED_FIXTURE"),
    ],
)
def test_structure_intake_refusals(obj: object, code: str) -> None:
    with pytest.raises(IntakeRefusal) as e:
        from_json(obj)
    assert e.value.code == code


def test_float_in_a_fixture_is_refused() -> None:
    for bad in ({**EDGE, "values": [[0, 0.5]]}, {**EDGE, "tuples": [["arc", [0, 1.0]]]}):
        with pytest.raises(ExactError) as e:
            from_json(bad)
        assert e.value.code == "RR-FLOAT"
    with pytest.raises(ExactError) as e:
        validate(FiniteStructure((("node", 1),), (), (), ((0, 0.5),)))  # type: ignore[arg-type]
    assert e.value.code == "RR-FLOAT"


def test_the_carrier_cap_is_eighteen() -> None:
    """Round P6: the smallest cap that hosts the six-vertex closed surface
    with its ten triangles, one test cochain and one self-map."""
    from engine.structure import MAX_CARRIER

    assert MAX_CARRIER == 18
    fs = from_json({**EDGE, "sorts": [["node", 18]]})
    assert fs.n() == 18 and encode(fs).regime.n_data() == 18


D0 = "sha256:" + "ab" * 32
D1 = "sha256:" + "0f" * 32


def test_digests_are_exact_byte_values() -> None:
    """Round P6: an element may carry a digest, exactly 32 bytes, kept byte
    for byte through intake, the draft form, hosting and descent."""
    obj = {**EDGE, "digests": [[0, D0], [1, D1]]}
    fs = from_json(obj)
    assert fs.digest(0) == bytes.fromhex("ab" * 32) and fs.digest(1) == bytes.fromhex("0f" * 32)
    assert fs.digest(5) is None and len(fs.digest(0) or b"") == 32
    assert to_json(fs)["digests"] == [[0, D0], [1, D1]] and from_json(to_json(fs)) == fs
    assert "digests" not in to_json(from_json(EDGE))
    e = encode(fs)
    assert descend(e, e.regime) == fs and decode(e).digests == fs.digests
    assert fs.with_tuples(()).digests == fs.digests


@pytest.mark.parametrize(
    "digests",
    [
        [[0, "sha256:" + "AB" * 32]],
        [[0, "sha256:" + "ab" * 31]],
        [[0, "ab" * 32]],
        [[0, 7]],
        [[2, D0]],
        [[0, D0], [0, D1]],
        {"0": D0},
    ],
)
def test_malformed_digests_are_refused(digests: object) -> None:
    with pytest.raises(IntakeRefusal) as e:
        from_json({**EDGE, "digests": digests})
    assert e.value.code == "MALFORMED_FIXTURE"


def test_a_digest_is_never_a_float_nor_beside_a_value() -> None:
    with pytest.raises(ExactError) as e:
        from_json({**EDGE, "digests": [[0, 0.5]]})
    assert e.value.code == "RR-FLOAT"
    with pytest.raises(IntakeRefusal):
        from_json({**EDGE, "values": [[0, "1/1"]], "digests": [[0, D0]]})
    with pytest.raises(IntakeRefusal):
        validate(FiniteStructure((("node", 1),), (), (), (), ((0, b"short"),)))


def test_texts_are_exact_ascii_values() -> None:
    """Round P7B: an element may carry a text, printable ASCII, kept byte for
    byte through intake, the draft form, hosting and descent."""
    obj = {**EDGE, "texts": [[0, "echo release 1"], [1, ""]]}
    fs = from_json(obj)
    assert fs.text(0) == "echo release 1" and fs.text(1) == "" and fs.text(5) is None
    assert to_json(fs)["texts"] == [[0, "echo release 1"], [1, ""]] and from_json(to_json(fs)) == fs
    assert "texts" not in to_json(from_json(EDGE))
    e = encode(fs)
    assert descend(e, e.regime) == fs and decode(e).texts == fs.texts
    assert fs.with_tuples(()).texts == fs.texts


@pytest.mark.parametrize(
    "texts",
    [
        [[0, "caf\u00e9"]],
        [[0, "line\nbreak"]],
        [[0, "x" * 513]],
        [[0, 7]],
        [[2, "a"]],
        [[0, "a"], [0, "b"]],
        {"0": "a"},
    ],
)
def test_malformed_texts_are_refused(texts: object) -> None:
    with pytest.raises(IntakeRefusal) as e:
        from_json({**EDGE, "texts": texts})
    assert e.value.code == "MALFORMED_FIXTURE"


def test_a_text_is_never_a_float_nor_beside_another_value() -> None:
    with pytest.raises(ExactError) as e:
        from_json({**EDGE, "texts": [[0, 0.5]]})
    assert e.value.code == "RR-FLOAT"
    for other in ({"values": [[0, "1/1"]]}, {"digests": [[0, D0]]}):
        with pytest.raises(IntakeRefusal):
            from_json({**EDGE, **other, "texts": [[0, "a"]]})


def test_the_textbook_signature_check() -> None:
    from engine.exact.digest import as_number, sha256, signature_verifies

    n, e, d = 3233, 17, 413  # 61 * 53; e * d = 1 mod lcm(60, 52)
    m = b'{"a":1}'
    s = pow(as_number(sha256(m)) % n, d, n)
    assert signature_verifies(n, e, s, m)
    assert not signature_verifies(n, e, s, b'{"a":2}') or as_number(sha256(b'{"a":2}')) % n == as_number(sha256(m)) % n
    assert not signature_verifies(n, e, (s + 1) % n or 1, m)
    assert not signature_verifies(n, e, 0, m) and not signature_verifies(n, e, n, m)
    assert not signature_verifies(1, e, 0, m) and not signature_verifies(n, 0, s, m)


def test_the_declared_canonical_digest() -> None:
    from engine.exact.digest import canonical_json, digest_of, sha256

    assert canonical_json({"b": ["x", 1], "a": "\u00e9"}) == b'{"a":"\\u00e9","b":["x",1]}'
    assert sha256(b"").hex() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert digest_of(["P", ["->", "P", "Q"]]) == sha256(b'["P",["->","P","Q"]]')


def test_tuple_cap() -> None:
    many = tuple(("arc", (i % 12, i // 12)) for i in range(4097))
    with pytest.raises(IntakeRefusal) as e:
        validate(FiniteStructure((("node", 12),), (RelSym("arc", ("node", "node")),), many))
    assert e.value.code == "SIZE_CAP"


# ---------------------------------------------------------------- hosting


def _universe() -> list[FiniteStructure]:
    pairs = list(product(range(2), repeat=2))
    subsets = chain.from_iterable(combinations(pairs, k) for k in range(len(pairs) + 1))
    sym = (RelSym("arc", ("node", "node")),)
    return [FiniteStructure((("node", 2),), sym, tuple(sorted(("arc", p) for p in s))) for s in subsets]


def test_decode_encode_is_identity_and_encoding_is_injective() -> None:
    seen: dict[Regime, FiniteStructure] = {}
    for fs in _universe():
        e = encode(fs)
        assert replay(e.history) == e.regime
        assert decode(e) == fs
        assert e.regime not in seen
        seen[e.regime] = fs
    assert len(seen) == 16


def test_sealed_admission_refuses_malformed_claims() -> None:
    sym = (RelSym("arc", ("node", "node")),)
    for tuples in ((("arc", (0, 5)),), (("arc", (0,)),)):
        with pytest.raises(NonAdmissible) as e:
            encode(FiniteStructure((("node", 2),), sym, tuples))
        assert e.value.code == "NON_ADMISSIBLE"


def test_off_image_terms_do_not_descend() -> None:
    fs = _universe()[3]
    e = encode(fs)
    cases = {
        "NON_DESCENT_DATUM": replay(e.history + (AdmitDatum("fresh"),)),
        "NON_DESCENT_FORM": replay(e.history + (AdmitForm(2),)),
    }
    for code, r in cases.items():
        with pytest.raises(NonDescent) as err:
            descend(e, r)
        assert err.value.code == code
    with pytest.raises(NonDescent) as err:
        descend(e, replay(e.history + (AdmitRuleAll(1),)))
    assert err.value.code == "NON_DESCENT_FORM"
    shrunk = Regime(e.regime.data, e.regime.forms, frozenset(i for i in e.regime.insts if i != (0, (0,))),
                    e.regime.rules, e.regime.reqs)
    with pytest.raises(NonDescent):
        descend(e, shrunk)
    with pytest.raises(NonDescent) as err:
        value_of(e, 0)
    assert err.value.code == "NON_DESCENT_VALUE"
    ev = encode(FiniteStructure((("val", 1),), (), (), ((0, Q(2)),)))
    assert value_of(ev, 0) == Q(2)


def test_hosting_down_check_and_a_defaulting_decoder() -> None:
    encs = [encode(fs) for fs in _universe()[:4]]

    def new_terms(e: Encoding) -> list[Regime]:
        return [replay(e.history + (AdmitDatum("fresh"),))]

    good = certify_hosting(encs, new_terms)
    assert (good.old_image_cases, good.non_descent_cases, good.defaulted) == (4, 4, 0)

    def defaulting(e: Encoding, r: Regime) -> FiniteStructure:
        return e.structure  # gives every new term an old meaning

    bad = certify_hosting(encs, new_terms, defaulting)
    assert bad.defaulted == 4

    def wrong(e: Encoding, r: Regime) -> FiniteStructure:
        return _universe()[0]

    with pytest.raises(NonDescent) as err:
        certify_hosting(encs[1:2], new_terms, wrong)
    assert err.value.code == "RR-NON-DESCENT"


# ---------------------------------------------------------------- the embargo


def test_embargo_list_is_pinned() -> None:
    assert [k for k, _ in EMBARGO_LIST] == [
        "four_item_delta", "growth", "removal", "declared_responder", "first_demand_index", "second_state",
        "history_symmetry", "element_count_succession", "duration_under_changing",
        "element_count_across_isomorphism", "shortest_class_matched_witnesses", "census_undecided_rows_x6",
    ]
    assert embargo_digest() == "db0305cb640326aecbd96bc0e7484abe60f4237a5a896b2ec0554ddafa11fd23"


def test_four_item_bound_cannot_be_built() -> None:
    assert ResourceBound(3).max_items == 3
    with pytest.raises(EmbargoRefusal) as e:
        ResourceBound(4)
    assert e.value.code == "GUARD_EMBARGO"
    with pytest.raises(EmbargoRefusal):
        ResourceBound(True)
    with pytest.raises(ValueError):
        ResourceBound(-1)
    with pytest.raises(EmbargoRefusal):
        check_delta_size(4)
    check_delta_size(3)


@pytest.mark.parametrize("kind", ["growth", "removal", "declared_responder", "first_demand_index", "second_state",
                                  "history_symmetry", "element_count_succession",
                                  "duration_under_changing", "element_count_across_isomorphism"])
def test_embargoed_requests_are_refused(kind: str) -> None:
    with pytest.raises(EmbargoRefusal) as e:
        request(kind, "asked")
    assert e.value.code == "GUARD_EMBARGO" and kind in e.value.detail
    with pytest.raises(ValueError):
        refuse("something_else")


@pytest.mark.parametrize("kind", ["growth", "removal", "responder"])
def test_embargoed_stage_capabilities(kind: str) -> None:
    with pytest.raises(EmbargoRefusal) as e:
        Stage("bad", 1, frozenset({"witness_inst", kind}), 2)
    assert e.value.code == "GUARD_EMBARGO"


def test_second_derivation_state_is_never_loaded() -> None:
    with pytest.raises(EmbargoRefusal) as e:
        vendored("research/second/SEED.md")
    assert e.value.code == "GUARD_EMBARGO"
    with pytest.raises(EmbargoRefusal):
        vendored("./research/second_index/x")
    assert vendored("code/derivation/model.py").is_file()


def test_a_climbing_path_cannot_reach_the_second_derivation() -> None:
    """The embargo is a prefix check, so the path is normalised first: a
    ``..`` that lands in ``research/second*`` is embargoed, and one that
    leaves the clone, or an absolute path, is refused outright."""
    with pytest.raises(EmbargoRefusal):
        vendored("research/natural_sections/../second/SEED.md")
    for rel in ("research/../../outside.txt", "/etc/passwd", "C:/Windows/win.ini"):
        with pytest.raises(Refusal) as e:
            vendored(rel)
        assert e.value.code == "RR-VENDOR-PATH", rel
    assert vendored("./code/derivation/model.py") == vendored("code/derivation/model.py")


def test_embargo_fires_before_any_claim_check() -> None:
    """A four-item delta is refused as embargoed even when it also touches a
    claim form: the guard runs first and nothing is evaluated."""
    e = encode(_universe()[1])
    s = host(e.history, frozenset(range(e.n_claim_forms())), ())
    delta = tuple(NewInst(1, (a, b)) for a, b in product(range(2), repeat=2))
    with pytest.raises(EmbargoRefusal) as err:
        admit_response(s, BASE, delta)
    assert err.value.code == "GUARD_EMBARGO"
