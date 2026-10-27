"""Epistemic no-go harness: independent reference checks over the shared fixtures.

AuthorityEffect: None.

Two fixtures are shared with the Rust kernels:

* ``engine/crates_rs/tests/core_sheaf_theory/fixtures/epistemic_no_go/
  empirical_models.json`` (``core_sheaf_theory::epistemic_observer``);
* ``engine/crates_rs/tests/core_contracts/fixtures/epistemic_no_go/
  provenance_cases.json`` (``core_contracts::three_role_authority``).

This module is a reference check, not a solver. With ``fractions.Fraction``
and enumeration it re-derives, independently of the Rust code, the parts of
every expected verdict that enumeration can decide: no-signalling, the
supported global assignments, strong and logical contextuality, the parity
cut, the nerve cohomology of the cover, a CHSH facet certificate, and the
marginalisation of a candidate joint distribution. The exact L1 defect and
its dual witness are the Rust LP's; here only their logical consequences
are checked (defect zero exactly when a global section is reported, a CHSH
violation forcing a positive defect).

The three-role demonstration runs the companion gate
``pfp.domain.provenance.ThreeRoleGate`` over the same provenance
cases the Rust contract decides, and records which layer refuses each case.
Two refusals (a prose basis, and an admitted root that is one of the parties)
exist only in the Rust contract: the gate's packet shape has no basis field
and does not compare the root with the parties.
"""

from __future__ import annotations

import itertools
import json
import unittest
from fractions import Fraction
from pathlib import Path

from pfp.domain.provenance import (
    AUTHORITY_EFFECT,
    RefusalReason,
    ThreeRoleGate,
    VerdictCode,
)


def _repo_root(start: Path = Path(__file__).resolve()) -> Path:
    for parent in start.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").is_file():
            return parent
    return start.parents[3]


ROOT = _repo_root()
MODELS_FIXTURE = (
    ROOT / "engine" / "crates_rs" / "tests" / "core_sheaf_theory" / "fixtures"
    / "epistemic_no_go" / "empirical_models.json"
)
PROVENANCE_FIXTURE = (
    ROOT / "engine" / "crates_rs" / "tests" / "core_contracts" / "fixtures"
    / "epistemic_no_go" / "provenance_cases.json"
)
BELL_COVER = ((0, 2), (0, 3), (1, 2), (1, 3))


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _q(text: str) -> Fraction:
    value = Fraction(text)
    if str(value) != text:
        raise ValueError(f"not a canonical rational string: {text!r}")
    return value


# ---------------------------------------------------------------------------
# An empirical model as the harness reads it: exact tables over contexts
# ---------------------------------------------------------------------------


class Model:
    """Tables ``p[context][outcome tuple]`` over ``questions`` with ``outcomes`` arities."""

    def __init__(self, doc: dict) -> None:
        self.name = doc["name"]
        self.arities = list(doc["outcomes"])
        self.contexts = [tuple(t["context"]) for t in doc["tables"]]
        self.tables: list[dict[tuple[int, ...], Fraction]] = []
        for context, table in zip(self.contexts, doc["tables"]):
            rows = {tuple(r["outcome"]): _q(r["p"]) for r in table["rows"]}
            full = {
                outcome: rows.get(outcome, Fraction(0))
                for outcome in itertools.product(*(range(self.arities[m]) for m in context))
            }
            if sum(full.values()) != 1 or any(p < 0 for p in full.values()):
                raise ValueError(f"{self.name}: context {context} is not a distribution")
            self.tables.append(full)

    def marginal(self, c: int, measurements: tuple[int, ...]) -> dict[tuple[int, ...], Fraction]:
        positions = [self.contexts[c].index(m) for m in measurements]
        out: dict[tuple[int, ...], Fraction] = {}
        for outcome, p in self.tables[c].items():
            key = tuple(outcome[i] for i in positions)
            out[key] = out.get(key, Fraction(0)) + p
        return out

    def signalling_witness(self) -> tuple[int, int, tuple[int, ...]] | None:
        """The first pair of contexts whose marginals disagree on their overlap."""

        for a, b in itertools.combinations(range(len(self.contexts)), 2):
            shared = tuple(m for m in self.contexts[a] if m in self.contexts[b])
            if shared and self.marginal(a, shared) != self.marginal(b, shared):
                return (a, b, shared)
        return None

    def is_no_signalling(self) -> bool:
        return self.signalling_witness() is None

    def support(self, c: int) -> set[tuple[int, ...]]:
        return {outcome for outcome, p in self.tables[c].items() if p > 0}

    def restrict(self, assignment: tuple[int, ...], c: int) -> tuple[int, ...]:
        return tuple(assignment[m] for m in self.contexts[c])

    def supported_globals(self) -> list[tuple[int, ...]]:
        return [
            g
            for g in itertools.product(*(range(k) for k in self.arities))
            if all(self.restrict(g, c) in self.support(c) for c in range(len(self.contexts)))
        ]

    def unextendable_sections(self) -> list[tuple[int, tuple[int, ...]]]:
        globals_ = self.supported_globals()
        out = []
        for c in range(len(self.contexts)):
            for outcome in sorted(self.support(c)):
                if not any(self.restrict(g, c) == outcome for g in globals_):
                    out.append((c, outcome))
        return out

    def marginalises(self, joint: dict[tuple[int, ...], Fraction]) -> bool:
        if sum(joint.values()) != 1 or any(p < 0 for p in joint.values()):
            return False
        for c in range(len(self.contexts)):
            got: dict[tuple[int, ...], Fraction] = {}
            for g, p in joint.items():
                key = self.restrict(g, c)
                got[key] = got.get(key, Fraction(0)) + p
            if any(got.get(o, Fraction(0)) != p for o, p in self.tables[c].items()):
                return False
        return True


# ---------------------------------------------------------------------------
# Parity cut over F_2 (WDP section 15.5), with the context set of every row
# ---------------------------------------------------------------------------


def parity_of_support(model: Model, c: int) -> int | None:
    context = model.contexts[c]
    if any(model.arities[m] != 2 for m in context):
        return None
    support = model.support(c)
    if len(support) != 2 ** (len(context) - 1):
        return None
    parities = {sum(outcome) % 2 for outcome in support}
    return parities.pop() if len(parities) == 1 else None


def parity_cut(model: Model) -> list[int] | None:
    """The contexts whose parity constraints sum to ``0 = 1``, or ``None``."""

    rows: list[tuple[int, int, int]] = []
    for c in range(len(model.contexts)):
        parity = parity_of_support(model, c)
        if parity is None:
            return None
        variables = sum(1 << m for m in model.contexts[c])
        rows.append((variables, parity, 1 << c))
    pivots: list[tuple[int, int, int]] = []
    for row in rows:
        for pv, prhs, pset in pivots:
            if row[0] & (pv & -pv):
                row = (row[0] ^ pv, row[1] ^ prhs, row[2] ^ pset)
        if row[0] == 0:
            if row[1] == 1:
                return [i for i in range(64) if row[2] >> i & 1]
            continue
        bit = row[0] & -row[0]
        pivots = [
            (pv ^ row[0], pr ^ row[1], ps ^ row[2]) if pv & bit else (pv, pr, ps)
            for pv, pr, ps in pivots
        ]
        pivots.append(row)
    return None


# ---------------------------------------------------------------------------
# Rational Cech cohomology of the nerve of the cover (a cover invariant)
# ---------------------------------------------------------------------------


def _rank(matrix: list[list[Fraction]]) -> int:
    rows = [list(r) for r in matrix]
    rank = 0
    cols = len(rows[0]) if rows else 0
    for col in range(cols):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][col] != 0), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][col] != 0:
                factor = rows[i][col] / rows[rank][col]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def nerve_h1_dim(cover: list[tuple[int, ...]]) -> int:
    """``dim_Q H^1`` of the nerve: cycles of the overlap graph not filled by triple overlaps."""

    sets = [set(c) for c in cover]
    edges = [(a, b) for a, b in itertools.combinations(range(len(sets)), 2) if sets[a] & sets[b]]
    triangles = [
        (a, b, c)
        for a, b, c in itertools.combinations(range(len(sets)), 3)
        if sets[a] & sets[b] & sets[c]
    ]
    d1 = [[Fraction(0)] * len(sets) for _ in edges]
    for i, (a, b) in enumerate(edges):
        d1[i][a], d1[i][b] = Fraction(-1), Fraction(1)
    d2 = [[Fraction(0)] * len(edges) for _ in triangles]
    for i, (a, b, c) in enumerate(triangles):
        d2[i][edges.index((b, c))] = Fraction(1)
        d2[i][edges.index((a, c))] = Fraction(-1)
        d2[i][edges.index((a, b))] = Fraction(1)
    rank_d1 = _rank(d1) if edges else 0
    rank_d2 = _rank(d2) if triangles else 0
    return len(edges) - rank_d1 - rank_d2


# ---------------------------------------------------------------------------
# CHSH facets: an independent certificate on the Bell cover
# ---------------------------------------------------------------------------


def correlator(model: Model, c: int) -> Fraction:
    return sum(p * (1 if sum(outcome) % 2 == 0 else -1) for outcome, p in model.tables[c].items())


def chsh_values(model: Model) -> list[Fraction]:
    """All eight CHSH functionals: one correlator negated, overall sign free."""

    e = [correlator(model, c) for c in range(4)]
    return [sign * (sum(e) - 2 * e[k]) for k in range(4) for sign in (1, -1)]


CHSH_CLASSICAL_BOUND = Fraction(2)


def chsh_classical_bound_by_enumeration() -> Fraction:
    """The bound re-derived: the maximum of every facet over the 16 deterministic strategies."""

    best = Fraction(-4)
    for strategy in itertools.product((0, 1), repeat=4):
        tables = [{tuple(strategy[m] for m in ctx): Fraction(1)} for ctx in BELL_COVER]
        doc = {
            "name": "deterministic",
            "outcomes": [2, 2, 2, 2],
            "tables": [
                {"context": list(ctx), "rows": [{"outcome": list(o), "p": "1"} for o in t]}
                for ctx, t in zip(BELL_COVER, tables)
            ],
        }
        best = max(best, max(chsh_values(Model(doc))))
    return best


# ---------------------------------------------------------------------------
# Simulated multi-agent queries
# ---------------------------------------------------------------------------


def simulate_agents(strategies: list[tuple[int, ...]], weights: list[Fraction]) -> dict:
    """Agents answering the four Bell questions by deterministic strategies, mixed by weight.

    The returned document is an empirical model whose tables are what an
    observer sees who can only ask one context at a time.
    """

    tables = []
    for ctx in BELL_COVER:
        rows: dict[tuple[int, ...], Fraction] = {}
        for strategy, w in zip(strategies, weights):
            key = tuple(strategy[m] for m in ctx)
            rows[key] = rows.get(key, Fraction(0)) + w
        table_rows = [{"outcome": list(o), "p": str(p)} for o, p in rows.items()]
        tables.append({"context": list(ctx), "rows": table_rows})
    return {"name": "simulated", "outcomes": [2, 2, 2, 2], "tables": tables}


def aggregate_reports(reports: list[tuple[str, dict]]) -> dict:
    """Peer agents each report one context's exact table; the aggregator holds them all.

    ``reports`` pairs an agent name with a fixture table document. The
    aggregator has every local section exactly and nothing else; whether the
    sections glue is decided by the model built from them.
    """

    names = [agent for agent, _ in reports]
    if len(set(names)) != len(names):
        raise ValueError("one report per agent")
    tables = [dict(table) for _, table in reports]
    return {"name": "aggregated:" + ",".join(names), "outcomes": [2, 2, 2, 2], "tables": tables}


# ---------------------------------------------------------------------------
# Tests: Pillar I (contextuality)
# ---------------------------------------------------------------------------


class EmpiricalModelFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = _load(MODELS_FIXTURE)
        self.models = {m["name"]: (Model(m), m["expected"]) for m in self.doc["models"]}

    def test_fixture_declares_no_authority_and_canonical_rationals(self) -> None:
        self.assertEqual(self.doc["schema"], "core.epistemic_no_go.empirical_models.v1")
        self.assertEqual(self.doc["authority_effect"], "None")
        self.assertEqual(len(self.models), 6)
        for model_doc in self.doc["models"]:
            for table in model_doc["tables"]:
                for row in table["rows"]:
                    self.assertEqual(str(_q(row["p"])), row["p"])

    def test_every_model_is_no_signalling(self) -> None:
        for name, (model, _) in self.models.items():
            with self.subTest(model=name):
                self.assertTrue(model.is_no_signalling())

    def test_supported_global_assignments_match(self) -> None:
        for name, (model, expected) in self.models.items():
            with self.subTest(model=name):
                self.assertEqual(
                    len(model.supported_globals()), expected["supported_global_assignments"]
                )

    def test_verdict_kinds_are_re_derived_by_enumeration(self) -> None:
        for name, (model, expected) in self.models.items():
            with self.subTest(model=name):
                globals_ = model.supported_globals()
                unextendable = model.unextendable_sections()
                if expected["verdict"] == "Strong":
                    self.assertEqual(globals_, [])
                elif expected["verdict"] == "Logical":
                    self.assertTrue(globals_)
                    self.assertEqual(
                        [[c, list(o)] for c, o in unextendable][:1],
                        [[u["table"], u["outcome"]] for u in expected["unextendable"]],
                    )
                else:
                    self.assertTrue(globals_)
                    self.assertEqual(unextendable, [])
                if expected["verdict"] in ("Strong", "Logical"):
                    self.assertNotEqual(_q(expected["l1_defect"]), 0)

    def test_global_sections_are_witnessed_by_a_verified_joint(self) -> None:
        """Where the kernel reports a global section, a joint distribution exists.

        The kernel's joint is the LP minimiser; the harness exhibits its own
        candidate, uniform over the supported global assignments, which is a
        joint for these fixtures. Its failure elsewhere decides nothing.
        """

        for name, (model, expected) in self.models.items():
            with self.subTest(model=name):
                globals_ = model.supported_globals()
                uniform = {g: Fraction(1, len(globals_)) for g in globals_} if globals_ else {}
                if expected["verdict"] == "GlobalSection":
                    self.assertEqual(_q(expected["l1_defect"]), 0)
                    self.assertTrue(model.marginalises(uniform))
                else:
                    self.assertGreater(_q(expected["l1_defect"]), 0)
                    self.assertFalse(model.marginalises(uniform))

    def test_parity_cuts_match(self) -> None:
        for name, (model, expected) in self.models.items():
            with self.subTest(model=name):
                self.assertEqual(parity_cut(model), expected["parity_cut"])

    def test_nerve_h1_is_a_cover_invariant_not_a_witness(self) -> None:
        dims = {}
        for name, (model, expected) in self.models.items():
            with self.subTest(model=name):
                dim = nerve_h1_dim(model.contexts)
                self.assertEqual(dim, expected["nerve_h1_dim"])
                dims.setdefault(tuple(model.contexts), set()).add((dim, expected["verdict"]))
        bell = dims[BELL_COVER]
        self.assertEqual({d for d, _ in bell}, {1})
        self.assertEqual(
            {v for _, v in bell}, {"Strong", "GlobalSection", "Probabilistic", "Logical"}
        )

    def test_chsh_facets_certify_probabilistic_contextuality(self) -> None:
        self.assertEqual(chsh_classical_bound_by_enumeration(), CHSH_CLASSICAL_BOUND)
        for name, (model, expected) in self.models.items():
            if tuple(model.contexts) != BELL_COVER:
                continue
            with self.subTest(model=name):
                best = max(chsh_values(model))
                if expected["verdict"] == "GlobalSection":
                    self.assertLessEqual(best, CHSH_CLASSICAL_BOUND)
                if "chsh_model_value" in expected:
                    self.assertEqual(_q(expected["chsh_classical_bound"]), CHSH_CLASSICAL_BOUND)
                    self.assertEqual(best, _q(expected["chsh_model_value"]))
                    self.assertGreater(best, CHSH_CLASSICAL_BOUND)
                    self.assertGreater(_q(expected["l1_defect"]), 0)
        self.assertEqual(max(chsh_values(self.models["pr_box"][0])), Fraction(4))


class SimulatedMultiAgentTests(unittest.TestCase):
    """Contextuality across simulated multi-agent queries.

    Agents who answer from a fixed strategy, however the strategies are
    mixed, produce tables with a global section: the mixture itself. Tables
    that no strategy supports in every context (the PR box) come from no
    such population, whatever the weights.
    """

    def test_mixtures_of_strategies_always_have_a_global_section(self) -> None:
        strategies = [(0, 1, 1, 0), (1, 1, 0, 1), (0, 0, 0, 0)]
        weights = [Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]
        model = Model(simulate_agents(strategies, weights))
        self.assertTrue(model.is_no_signalling())
        self.assertEqual(model.unextendable_sections(), [])
        self.assertTrue(model.marginalises(dict(zip(strategies, weights))))
        self.assertLessEqual(max(chsh_values(model)), CHSH_CLASSICAL_BOUND)

    def test_agents_each_holding_one_context_exactly_cannot_be_glued(self) -> None:
        """Four peers report the PR box one context each; the aggregator holds every
        local section exactly and still has no supported global assignment. The
        same peers with the a1b1 report replaced by the correlated table glue.
        """

        pr_box = next(m for m in _load(MODELS_FIXTURE)["models"] if m["name"] == "pr_box")
        agents = ["alice-1", "alice-2", "bob-1", "bob-2"]
        reports = list(zip(agents, pr_box["tables"]))
        aggregated = Model(aggregate_reports(reports))
        self.assertTrue(aggregated.is_no_signalling())
        self.assertEqual(aggregated.supported_globals(), [])
        self.assertEqual(parity_cut(aggregated), [0, 1, 2, 3])
        reports[3] = ("bob-2", {"context": [1, 3], "rows": pr_box["tables"][0]["rows"]})
        glued = Model(aggregate_reports(reports))
        self.assertTrue(glued.is_no_signalling())
        self.assertEqual(len(glued.supported_globals()), 2)
        self.assertIsNone(parity_cut(glued))
        with self.assertRaises(ValueError):
            aggregate_reports([("alice-1", pr_box["tables"][0]), ("alice-1", pr_box["tables"][1])])

    def test_pr_box_tables_come_from_no_population_of_strategies(self) -> None:
        pr_box = Model(next(m for m in _load(MODELS_FIXTURE)["models"] if m["name"] == "pr_box"))
        for strategy in itertools.product((0, 1), repeat=4):
            unsupported = [
                c for c in range(4) if pr_box.restrict(strategy, c) not in pr_box.support(c)
            ]
            self.assertTrue(unsupported, strategy)
        self.assertEqual(parity_cut(pr_box), [0, 1, 2, 3])


# ---------------------------------------------------------------------------
# Tests: Pillar IV (three-role authority) through the companion gate
# ---------------------------------------------------------------------------


OBSERVER = {
    "kernel": "support presheaf over the maximal-context cover",
    "admissibility": "noncontextual polytope",
    "norm": "L1",
    "terminal": "GlobalSection -> Admitted; obstruction -> Refused",
    "layer": "WDP-CH10-D01 diagnostic",
}
SCOPE = "epistemic-no-go"

# Which layer refuses each Rust fixture case: the companion gate, the Rust
# contract, or both. `None` in the gate column means the gate admits or
# self-attests the packet; the Rust column is the fixture's own expectation.
GATE_EXPECTATION: dict[str, tuple[VerdictCode, tuple[RefusalReason, ...]]] = {
    "distinct_roles_admitted_root": (VerdictCode.ADMITTED_FOR_AUTHORIZATION, ()),
    "asi_authorizes_its_own_proposal": (VerdictCode.REJECTED, (RefusalReason.SELF_AUTHORIZATION,)),
    "evaluator_authorizes": (VerdictCode.REJECTED, (RefusalReason.EVALUATOR_IS_AUTHORIZER,)),
    "proposer_evaluates_itself": (VerdictCode.REJECTED, (RefusalReason.EVALUATOR_IS_PROPOSER,)),
    "prose_declaration_of_authority": (VerdictCode.ADMITTED_FOR_AUTHORIZATION, ()),
    "no_admitted_root": (VerdictCode.REJECTED, (RefusalReason.UNADMITTED_ROOT,)),
    "root_is_the_proposer": (VerdictCode.ADMITTED_FOR_AUTHORIZATION, ()),
    "regime_explicitly_allows_self_authorization": (VerdictCode.SELF_ATTESTED, ()),
    "empty_identifier": (VerdictCode.REJECTED, (RefusalReason.EMPTY_IDENTIFIER,)),
}
RUST_ONLY_REFUSALS = {"prose_declaration_of_authority", "root_is_the_proposer"}


def gate_payload(case: dict) -> dict:
    packet = case["packet"]
    policy = case["policy"]

    def binding(role: str) -> dict:
        identity = packet[role]["id"]
        return {"identifier": identity, "principal": identity}

    return {
        "claim_id": packet["attempt_id"],
        "scope": SCOPE,
        "proposer": binding("proposer"),
        "evaluator": binding("evaluator"),
        "authorizer": binding("authorizer"),
        "observer": dict(OBSERVER),
        "authority_root": packet["authorizer"]["trust_root"] or "root:none",
        "policy": (
            "self_attested_permitted" if policy["allow_self_authorization"] else "pairwise_distinct"
        ),
    }


class RefusalFixtureTests(unittest.TestCase):
    """Inputs on which the Rust kernel returns a typed refusal, not a verdict."""

    def setUp(self) -> None:
        doc = _load(MODELS_FIXTURE)
        self.refusals = {r["name"]: r for r in doc["refusals"]}

    def test_the_two_workstation_refusal_cases_are_pinned(self) -> None:
        self.assertEqual(set(self.refusals), {"signalling_family", "oversized_singletons"})

    def test_signalling_family_is_not_a_presheaf(self) -> None:
        case = self.refusals["signalling_family"]
        model = Model(case)
        self.assertFalse(model.is_no_signalling())
        left, right, overlap = model.signalling_witness()
        expected = case["expected"]
        pinned = (expected["left"], expected["right"], expected["overlap"])
        self.assertEqual((left, right, list(overlap)), pinned)
        for context, key in ((left, "left_marginal"), (right, "right_marginal")):
            marginal = model.marginal(context, overlap)
            got = [str(marginal.get((o,), Fraction(0))) for o in range(2)]
            self.assertEqual(got, expected[key])

    def test_oversized_model_exceeds_the_enumeration_cap_without_enumerating(self) -> None:
        case = self.refusals["oversized_singletons"]
        model = Model(case)
        self.assertTrue(model.is_no_signalling())
        count = 1
        for arity in model.arities:
            count *= arity
        expected = case["expected"]
        self.assertEqual(count, expected["global_assignments"])
        self.assertGreater(count, expected["limit"])
        self.assertEqual(expected["limit"], 2**20)


def fiber_lemma_holds(worlds: list, available: dict, answer: dict) -> bool:
    """No f with f(available(w)) == answer(w) for every w, checked by exhausting f.

    ``available`` and ``answer`` map each world to a finite code; the search
    runs over every function from the codes of ``available`` to the codes of
    ``answer``. Returns True when the lemma's conclusion holds (no such f).
    """

    codes = sorted({available[w] for w in worlds})
    answers = sorted({answer[w] for w in worlds})
    for choice in itertools.product(answers, repeat=len(codes)):
        f = dict(zip(codes, choice))
        if all(f[available[w]] == answer[w] for w in worlds):
            return False
    return True


class FiberLemmaTests(unittest.TestCase):
    """The author's replacement foundation for clause II, with its time caveat."""

    def test_collided_worlds_with_different_answers_admit_no_decoder(self) -> None:
        worlds = [(0, 0), (0, 1), (1, 0), (1, 1)]
        available = {w: w[0] for w in worlds}
        answer = {w: w[1] for w in worlds}
        self.assertEqual(available[(0, 0)], available[(0, 1)])
        self.assertNotEqual(answer[(0, 0)], answer[(0, 1)])
        self.assertTrue(fiber_lemma_holds(worlds, available, answer))

    def test_the_lemma_needs_its_premise(self) -> None:
        worlds = [(0, 0), (0, 1), (1, 0), (1, 1)]
        available = {w: w for w in worlds}
        answer = {w: w[1] for w in worlds}
        self.assertFalse(fiber_lemma_holds(worlds, available, answer))

    def test_a_hidden_coordinate_is_the_next_report_under_swap_dynamics(self) -> None:
        """pi(a, b) = a hides b now; F(a, b) = (b, a) reveals it one step later.

        The instantaneous kernel of pi is nonzero, yet the two-step history
        separates every pair of states, so one-step privacy is not privacy.
        """

        def pi(state: tuple[int, int]) -> int:
            return state[0]

        def step(state: tuple[int, int]) -> tuple[int, int]:
            return (state[1], state[0])

        states = [(a, b) for a in range(2) for b in range(2)]
        now = {s: pi(s) for s in states}
        history = {s: (pi(s), pi(step(s))) for s in states}
        self.assertEqual(now[(0, 0)], now[(0, 1)])
        self.assertEqual(len(set(now.values())), 2)
        self.assertEqual(len(set(history.values())), 4)


class ThreeRoleAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = _load(PROVENANCE_FIXTURE)
        self.cases = {c["name"]: c for c in self.doc["cases"]}

    def test_fixture_declares_no_authority(self) -> None:
        self.assertEqual(self.doc["schema"], "core.epistemic_no_go.provenance_cases.v1")
        self.assertEqual(self.doc["authority_effect"], "None")
        self.assertEqual(AUTHORITY_EFFECT, "None")
        self.assertEqual(set(self.cases), set(GATE_EXPECTATION))

    def test_gate_verdicts_on_the_rust_cases(self) -> None:
        for name, case in self.cases.items():
            with self.subTest(case=name):
                gate = ThreeRoleGate(SCOPE, frozenset(case["policy"]["admitted_roots"]))
                verdict = gate.evaluate_mapping(gate_payload(case))
                code, reasons = GATE_EXPECTATION[name]
                self.assertEqual(verdict.code, code)
                for reason in reasons:
                    self.assertIn(reason, verdict.reasons)
                self.assertEqual(verdict.authority_effect, "None")

    def test_every_refusal_is_caught_by_at_least_one_layer(self) -> None:
        for name, case in self.cases.items():
            with self.subTest(case=name):
                gate_admits = GATE_EXPECTATION[name][0] is VerdictCode.ADMITTED_FOR_AUTHORIZATION
                rust_refuses = case["expected"] != "Pass"
                if rust_refuses and gate_admits:
                    self.assertIn(name, RUST_ONLY_REFUSALS)
                if name in RUST_ONLY_REFUSALS:
                    self.assertTrue(rust_refuses and gate_admits)

    def test_self_authorization_fails_closed_whatever_the_claimed_rank(self) -> None:
        """An agent that proposes, evaluates and authorizes its own claim is refused.

        The refusal does not depend on what the agent calls itself or on
        the certificate it says it holds: the three bindings coincide.
        """

        gate = ThreeRoleGate(SCOPE, frozenset({"root:ops"}))
        for rank in ("asi:core-9000", "proof-assistant:lean", "brain:alice", "llm:fable"):
            with self.subTest(agent=rank):
                payload = gate_payload(self.cases["distinct_roles_admitted_root"])
                for role in ("proposer", "evaluator", "authorizer"):
                    payload[role] = {"identifier": rank, "principal": rank}
                verdict = gate.evaluate_mapping(payload)
                self.assertIs(verdict.code, VerdictCode.REJECTED)
                self.assertEqual(
                    set(verdict.reasons),
                    {
                        RefusalReason.SELF_AUTHORIZATION,
                        RefusalReason.EVALUATOR_IS_PROPOSER,
                        RefusalReason.EVALUATOR_IS_AUTHORIZER,
                    },
                )
                self.assertFalse(verdict.admitted)

    def test_an_admitted_root_is_a_license_not_a_property_of_the_agent(self) -> None:
        """The same packet is admitted under one root set and refused under another."""

        case = self.cases["distinct_roles_admitted_root"]
        payload = gate_payload(case)
        admitted = ThreeRoleGate(SCOPE, frozenset({"root:ops"})).evaluate_mapping(payload)
        self.assertTrue(admitted.admitted)
        refused = ThreeRoleGate(SCOPE, frozenset({"root:other"})).evaluate_mapping(payload)
        self.assertIs(refused.code, VerdictCode.REJECTED)
        self.assertIn(RefusalReason.UNADMITTED_ROOT, refused.reasons)


if __name__ == "__main__":
    unittest.main()
