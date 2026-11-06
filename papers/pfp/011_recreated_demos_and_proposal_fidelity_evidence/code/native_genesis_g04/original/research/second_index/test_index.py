"""What the rectangle shows, and what every counter of it can do.

Three batteries, none implying the others:

* the SUBSTANTIVE tests: the first count of the exhibited histories, the
  bound from below, the two countermodels, and the agreement between the
  two independently written procedures.  Each of these is the
  computational side of a Lean theorem of this rung, and the witnesses are
  the same histories in both, so a divergence between the two sides is
  visible here rather than in prose;
* the NEGATIVE tests: every counter the committed receipt reports as zero
  is shown able to read otherwise under an injected defect.  A counter
  reading zero is not evidence unless it could have read something else;
* the RUNNER tests: the receipt is deterministic, regenerates
  byte-identically, and the ``--check`` path fails on a drifted receipt
  instead of overwriting it.
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile
import unittest
from typing import Any
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import index as ix  # noqa: E402
from index import Alphabet, Node, Stake, event_kind  # noqa: E402
import run_index as ri  # noqa: E402
from derivation.model import (  # noqa: E402
    EMPTY,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Event,
    Impose,
    Regime,
    Supply,
    replay,
)

# The same three histories the Lean countermodels exhibit, written in the
# sealed Python events.  The tokens are presentation and are never
# compared; the Lean side counts data and carries no token at all.
HISTORY_A: tuple[Event, ...] = (AdmitDatum("<n0>"), AdmitDatum("<n1>"))
HISTORY_B: tuple[Event, ...] = (
    Supply("<z>"),
    AdmitDatum("<n0>"),
    AdmitDatum("<n1>"),
)
CEASE_HISTORY: tuple[Event, ...] = (
    AdmitDatum("<n0>"),
    AdmitDatum("<n1>"),
    AdmitForm(1),
    AdmitInst(0, (0,)),
)

SMALL = Alphabet(
    supply_token="<z>",
    fresh_tokens=("<n0>", "<n1>"),
    arities=(1,),
    max_data=3,
    max_forms=1,
    max_length=2,
)


def stake_named(name: str) -> Stake:
    for stake in ix.declared_stakes():
        if stake.name == name:
            return stake
    raise KeyError(name)


class ExhibitedHistoryTests(unittest.TestCase):
    """The computational side of the Lean countermodels, on the same
    witnesses."""

    def setUp(self) -> None:
        self.seen = ix.Observations()
        self.apart = stake_named("total_apart")

    def test_two_histories_reach_one_regime_with_different_counts(self) -> None:
        self.assertEqual(replay(HISTORY_A, EMPTY), replay(HISTORY_B, EMPTY))
        self.assertEqual(
            ix.first_index_forward(EMPTY, HISTORY_A, self.apart, self.seen), 2
        )
        self.assertEqual(
            ix.first_index_forward(EMPTY, HISTORY_B, self.apart, self.seen), 3
        )

    def test_the_supply_moves_the_count_and_not_the_regime(self) -> None:
        """Why the two counts differ: the extra event of the longer history
        is a supply, which the sealed grammar proves changes no state."""
        self.assertEqual(replay((Supply("<z>"),), EMPTY), EMPTY)
        self.assertEqual(len(HISTORY_B), len(HISTORY_A) + 1)

    def test_a_demand_can_cease(self) -> None:
        at_two = replay(CEASE_HISTORY[:2], EMPTY)
        at_three = replay(CEASE_HISTORY[:3], EMPTY)
        at_four = replay(CEASE_HISTORY, EMPTY)
        self.assertTrue(self.seen.carries(self.apart, at_two))
        self.assertTrue(self.seen.carries(self.apart, at_three))
        self.assertFalse(self.seen.carries(self.apart, at_four))
        self.assertEqual(event_kind(CEASE_HISTORY[3]), "AdmitInst")

    def test_the_count_of_the_ceasing_history_is_still_two(self) -> None:
        """A first count is a first occurrence, not a threshold: the count
        of the ceasing history is the count of its two-event prefix."""
        self.assertEqual(
            ix.first_index_forward(EMPTY, CEASE_HISTORY, self.apart, self.seen), 2
        )

    def test_the_free_stake_has_no_count_on_any_exhibited_history(self) -> None:
        free = stake_named("free")
        for history in (HISTORY_A, HISTORY_B, CEASE_HISTORY):
            self.assertIsNone(
                ix.first_index_forward(EMPTY, history, free, self.seen)
            )
            self.assertIsNone(ix.first_index_scan(EMPTY, history, free, self.seen))

    def test_an_inert_run_from_a_quiet_base_has_no_count(self) -> None:
        """The base of reading L carries no demand under the same-labelling
        stake, and a run of supplies, impositions and form admissions from
        it carries none either."""
        same = stake_named("total_same")
        base = ix.base_regime("L")
        self.assertFalse(self.seen.carries(same, base))
        inert: tuple[Event, ...] = (
            Supply("<z>"),
            Impose(0, 1),
            AdmitForm(1),
            Supply("<z>"),
        )
        self.assertIsNone(ix.first_index_forward(base, inert, same, self.seen))

    def test_no_count_below_two_from_the_empty_base(self) -> None:
        """The Lean bound, checked over the whole rectangle from the empty
        base: two events must be consumed before a pair of held data
        exists."""
        report = ix.base_report("EMPTY", ix.ALPHABET)
        stakes = report["stakes"]
        assert isinstance(stakes, dict)
        for name, entry in stakes.items():
            assert isinstance(entry, dict)
            earliest = entry["earliest_index"]
            if earliest is not None:
                self.assertGreaterEqual(earliest, 2, name)

    def test_the_two_procedures_agree_on_every_exhibited_history(self) -> None:
        for history in (HISTORY_A, HISTORY_B, CEASE_HISTORY):
            for stake in ix.declared_stakes():
                self.assertEqual(
                    ix.first_index_forward(EMPTY, history, stake, self.seen),
                    ix.first_index_scan(EMPTY, history, stake, self.seen),
                    f"{stake.name}",
                )


class RectangleTests(unittest.TestCase):
    def test_the_three_bases_are_the_declared_ones(self) -> None:
        self.assertEqual(ix.BASE_NAMES, ("EMPTY", "L", "F"))
        self.assertEqual(ix.base_regime("EMPTY"), EMPTY)
        self.assertEqual(ix.base_regime("L").n_data(), 2)
        self.assertEqual(ix.base_regime("F").n_data(), 3)

    def test_an_unknown_base_is_refused(self) -> None:
        with self.assertRaises(KeyError):
            ix.base_genesis("nowhere")

    def test_every_node_replays_from_its_base(self) -> None:
        rect = ix.build_rectangle("EMPTY", SMALL)
        self.assertEqual(ix.replay_check(rect), 0)
        self.assertGreater(len(rect.nodes), 1)

    def test_a_tampered_node_is_counted_as_a_replay_mismatch(self) -> None:
        """NEGATIVE: the replay counter bites.  One node's regime replaced
        by another makes the count read one."""
        rect = ix.build_rectangle("EMPTY", SMALL)
        nodes = list(rect.nodes)
        victim = next(node for node in nodes if node.regime != rect.regime)
        position = nodes.index(victim)
        nodes[position] = Node(victim.history, EMPTY, victim.grown)
        tampered = ix.Rectangle(
            rect.base, rect.regime, tuple(nodes), rect.bound_stops,
            rect.grammar_refusals,
        )
        self.assertEqual(ix.replay_check(tampered), 1)

    def test_the_grammar_refusal_arm_is_live(self) -> None:
        """The declared alphabet offers only admissions the sealed grammar
        accepts, so the receipt's refusal count is zero.  That is a
        property of the alphabet, not a dead branch: a form of arity zero
        is refused, and the refusal is counted rather than raised."""
        self.assertFalse(ix.grammar_refuses(EMPTY, AdmitForm(1)))
        self.assertTrue(ix.grammar_refuses(EMPTY, AdmitForm(0)))
        bad = Alphabet("<z>", ("<a>",), (0,), 3, 1, 1)
        rect = ix.build_rectangle("EMPTY", bad)
        self.assertGreater(rect.grammar_refusals, 0)

    def test_the_second_enumerator_agrees_on_the_crosscheck_family(self) -> None:
        result = ix.crosscheck("EMPTY", SMALL, 2)
        self.assertTrue(result["reach_agrees"])
        self.assertEqual(
            result["first_enumerator_regimes"], result["second_enumerator_regimes"]
        )

    def test_a_disagreeing_second_enumerator_is_reported(self) -> None:
        """NEGATIVE: the cross-check bites.  A second enumerator that
        reaches a different set makes the agreement read false."""
        with mock.patch.object(
            ix, "enumerate_by_levels", return_value=(frozenset({EMPTY}), 1)
        ):
            result = ix.crosscheck("EMPTY", SMALL, 2)
        self.assertFalse(result["reach_agrees"])

    def test_the_observation_cache_is_used_and_counted(self) -> None:
        seen = ix.Observations()
        apart = stake_named("total_apart")
        self.assertEqual(seen.sizes(), (0, 0))
        seen.carries(apart, EMPTY)
        seen.carries(apart, EMPTY)
        seen.dishonoured(apart, EMPTY)
        self.assertEqual(seen.sizes(), (1, 1))


class CounterInjectionTests(unittest.TestCase):
    """Every counter the receipt reports as zero, shown able to fire."""

    def test_a_blinded_second_procedure_is_counted_as_a_disagreement(self) -> None:
        class Blinded(ix.Observations):
            def dishonoured(self, stake: Stake, regime: Regime) -> bool:
                return False

        rect = ix.build_rectangle("EMPTY", SMALL)
        report = ix.stake_report(rect, stake_named("total_apart"), Blinded())
        self.assertGreater(report.procedure_disagreements, 0)

    def test_declaring_an_admission_inert_is_counted_as_a_violation(self) -> None:
        """NEGATIVE: the inert-last-event counter bites.  The receipt reads
        zero because no first count follows an inert event; declaring the
        instance admission inert makes the same rectangle read otherwise.

        This injection moves the DECLARED set, not the grammar.  It shows
        the counter is live; it is not evidence about the grammar, and the
        theorem that the real set never fires is in `Index.lean`."""
        rect = ix.build_rectangle("EMPTY", ix.ALPHABET)
        seen = ix.Observations()
        with mock.patch.object(ix, "INERT_KINDS", frozenset({"AdmitDatum"})):
            report = ix.stake_report(rect, stake_named("total_apart"), seen)
        self.assertGreater(report.inert_last_event_violations, 0)
        clean = ix.stake_report(rect, stake_named("total_apart"), seen)
        self.assertEqual(clean.inert_last_event_violations, 0)

    def test_the_collision_counter_reads_zero_where_it_should(self) -> None:
        """A stake whose first count is zero at every sequence has no
        colliding regime, because every sequence agrees; the counter is a
        measurement and not a constant."""
        rect = ix.build_rectangle("L", SMALL)
        seen = ix.Observations()
        apart = ix.stake_report(rect, stake_named("total_apart"), seen)
        self.assertEqual(apart.earliest, 0)
        self.assertEqual(apart.colliding_regimes, 0)
        self.assertIsNone(apart.collision_witness)

    def test_the_collision_witness_is_deterministic_and_replayable(self) -> None:
        rect = ix.build_rectangle("EMPTY", ix.ALPHABET)
        seen = ix.Observations()
        first = ix.stake_report(rect, stake_named("total_apart"), seen)
        second = ix.stake_report(rect, stake_named("total_apart"), ix.Observations())
        self.assertEqual(first.collision_witness, second.collision_witness)
        witness = first.collision_witness
        assert witness is not None
        self.assertEqual(witness["indices"], [2, 3])
        histories = witness["histories"]
        assert isinstance(histories, list)
        self.assertEqual(len(histories), 2)

    def test_the_cessation_counter_names_the_kind(self) -> None:
        rect = ix.build_rectangle("EMPTY", ix.ALPHABET)
        report = ix.stake_report(rect, stake_named("total_apart"), ix.Observations())
        self.assertEqual(sorted(report.cessation_kinds), ["AdmitInst"])
        self.assertGreater(report.cessation_kinds["AdmitInst"], 0)

    def test_cessation_kinds_over_refuses_a_malformed_report(self) -> None:
        with self.assertRaises(TypeError):
            ix.cessation_kinds_over([{"stakes": []}])
        with self.assertRaises(TypeError):
            ix.cessation_kinds_over([{"stakes": {"a": 1}}])
        with self.assertRaises(TypeError):
            ix.cessation_kinds_over([{"stakes": {"a": {"cessation_kinds": 1}}}])


class DescriptorTests(unittest.TestCase):
    def test_every_event_kind_has_a_descriptor(self) -> None:
        described = ix.history_descriptor(
            (
                Supply("<z>"),
                AdmitDatum("<n0>"),
                AdmitForm(2),
                AdmitInst(0, (0, 1)),
                AdmitRuleAll(0),
                Impose(0, 1),
            )
        )
        self.assertEqual(
            described,
            (
                "Supply(<z>)",
                "AdmitDatum(<n0>)",
                "AdmitForm(2)",
                "AdmitInst(0,[0, 1])",
                "AdmitRuleAll(0)",
                "Impose(0,1)",
            ),
        )

    def test_an_unknown_event_type_is_refused(self) -> None:
        class Strange:
            pass

        with self.assertRaises(TypeError):
            ix.event_descriptor(Strange())  # type: ignore[arg-type]

    def test_the_regime_shape_carries_no_token(self) -> None:
        shape = ix.regime_shape(replay(CEASE_HISTORY, EMPTY))
        self.assertEqual(
            shape, {"data": 2, "forms": 1, "insts": 1, "rules": 0, "reqs": 0}
        )


class ReceiptTests(unittest.TestCase):
    def test_the_committed_receipt_matches_a_fresh_run(self) -> None:
        fresh = ri.render(ri.build())
        committed = (HERE / "receipts" / ri.RECEIPT_NAME).read_bytes()
        self.assertEqual(committed.replace(b"\r\n", b"\n"), fresh)

    def test_the_receipt_carries_no_environment_value(self) -> None:
        payload = ri.build()
        text = json.dumps(payload, sort_keys=True)
        for forbidden in (str(HERE), "timestamp", "hostname", "elapsed"):
            self.assertNotIn(forbidden, text)

    def test_the_receipt_stays_under_one_megabyte(self) -> None:
        self.assertLess(len((HERE / "receipts" / ri.RECEIPT_NAME).read_bytes()), 1_000_000)

    def test_the_frozen_digests_are_checkout_independent(self) -> None:
        digest = ri.frozen_digest("PROMPT.md")
        manifest = json.loads(
            (HERE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
        )
        frozen = {item["path"]: item["sha256"] for item in manifest["frozen_texts"]}
        self.assertEqual(digest, frozen["research/second_index/PROMPT.md"])

    def test_every_computational_prediction_is_scored_from_the_run(self) -> None:
        payload = ri.build()
        scored = payload["predictions_scored"]
        assert isinstance(scored, dict)
        for pid in (f"I-{n}" for n in range(12, 22)):
            self.assertIn(pid, scored)
            self.assertIn(scored[pid]["verdict"], {"HIT", "MISSED"})
        self.assertEqual(scored["I-X"]["verdict"], "PENDING")

    def test_a_doctored_report_is_scored_as_a_miss(self) -> None:
        """NEGATIVE: the scoring bites.  Every computational row is shown
        to read MISSED when the value it reads is moved, one row at a
        time, against a copy of the real reports."""
        reports = ix.all_reports()

        def doctored(mutate: Any) -> dict[str, Any]:
            copied: list[dict[str, Any]] = copy.deepcopy(reports)
            mutate(copied)
            return ri.score(copied)

        def find(rows: list[dict[str, Any]], base: str) -> dict[str, Any]:
            return next(row for row in rows if row["base"] == base)

        cases: dict[str, Any] = {
            "I-12": lambda rows: find(rows, "L").__setitem__("nodes", 1),
            "I-13": lambda rows: find(rows, "EMPTY").__setitem__("nodes", 3000),
            "I-14": lambda rows: find(rows, "EMPTY")["stakes"]["free"].__setitem__(
                "earliest_index", 1
            ),
            "I-15": lambda rows: find(rows, "L")["stakes"][
                "total_same"
            ].__setitem__("earliest_index", 99),
            "I-16": lambda rows: find(rows, "F")["stakes"]["chain"].__setitem__(
                "procedure_disagreements", 1
            ),
            "I-17": lambda rows: find(rows, "F")["stakes"]["chain"].__setitem__(
                "inert_last_event_violations", 1
            ),
            "I-18": lambda rows: find(rows, "EMPTY")["stakes"][
                "total_apart"
            ].__setitem__("cessation_kinds", {"Supply": 1}),
            "I-19": lambda rows: find(rows, "EMPTY")["stakes"][
                "total_apart"
            ].__setitem__("index_distribution", {"7": 1}),
            "I-20": lambda rows: find(rows, "EMPTY")["stakes"][
                "total_apart"
            ].__setitem__("colliding_regimes", 0),
            "I-21": lambda rows: find(rows, "EMPTY").__setitem__(
                "replay_mismatches", 1
            ),
        }
        for pid, mutate in cases.items():
            self.assertEqual(doctored(mutate)[pid]["verdict"], "MISSED", pid)
        self.assertEqual(
            ri.score(copy.deepcopy(reports))["I-21"]["verdict"], "HIT"
        )

    def test_a_disagreeing_crosscheck_is_scored_as_a_miss(self) -> None:
        reports: list[dict[str, Any]] = copy.deepcopy(ix.all_reports(SMALL))
        crosscheck = reports[0]["crosscheck"]
        assert isinstance(crosscheck, dict)
        crosscheck["reach_agrees"] = False
        self.assertEqual(ri.score(reports)["I-21"]["verdict"], "MISSED")

    def test_a_missing_receipt_fails_the_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = sys.argv
            sys.argv = ["run_index.py", "--receipts", tmp, "--check"]
            try:
                self.assertEqual(ri.main(), 1)
            finally:
                sys.argv = argv

    def test_a_drifted_receipt_fails_the_check_without_being_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / ri.RECEIPT_NAME
            target.write_bytes(b"{}\n")
            argv = sys.argv
            sys.argv = ["run_index.py", "--receipts", tmp, "--check"]
            try:
                self.assertEqual(ri.main(), 1)
            finally:
                sys.argv = argv
            self.assertEqual(target.read_bytes(), b"{}\n")

    def test_the_runner_writes_where_told_and_checks_what_it_wrote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = sys.argv
            sys.argv = ["run_index.py", "--receipts", tmp]
            try:
                self.assertEqual(ri.main(), 0)
                sys.argv = ["run_index.py", "--receipts", tmp, "--check"]
                self.assertEqual(ri.main(), 0)
            finally:
                sys.argv = argv
            self.assertTrue((pathlib.Path(tmp) / ri.RECEIPT_NAME).exists())

    def test_an_oversized_receipt_is_reported_for_splitting(self) -> None:
        """The seed requires a receipt above one megabyte to be split.  The
        committed receipt is far below that, so the notice is exercised
        here against an inflated rendering rather than left unreachable."""
        with tempfile.TemporaryDirectory() as tmp:
            argv = sys.argv
            sys.argv = ["run_index.py", "--receipts", tmp]
            try:
                with mock.patch.object(
                    ri, "render", return_value=b"x" * 1_000_001
                ):
                    self.assertEqual(ri.main(), 0)
            finally:
                sys.argv = argv

    def test_a_payload_without_a_scoring_object_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = sys.argv
            sys.argv = ["run_index.py", "--receipts", tmp]
            try:
                with mock.patch.object(
                    ri, "build", return_value={"predictions_scored": []}
                ):
                    with self.assertRaises(TypeError):
                        ri.main()
            finally:
                sys.argv = argv

    def test_the_runner_refuses_a_malformed_payload(self) -> None:
        with self.assertRaises(KeyError):
            ri._report([], "EMPTY")
        with self.assertRaises(TypeError):
            ri._stake({"stakes": []}, "free")
        with self.assertRaises(TypeError):
            ri._stake({"stakes": {"free": 1}}, "free")


class ReceiptContentTests(unittest.TestCase):
    """The committed numbers, read back and stated here, dated in
    STATUS.md.  A change to any of them changes this file too, which is
    the point: a receipt that can drift without a test noticing is not a
    receipt."""

    def setUp(self) -> None:
        self.payload: dict[str, Any] = json.loads(
            (HERE / "receipts" / ri.RECEIPT_NAME).read_text(encoding="utf-8")
        )

    def report(self, base: str) -> dict[str, Any]:
        reports = self.payload["reports"]
        assert isinstance(reports, list)
        for entry in reports:
            if entry["base"] == base:
                assert isinstance(entry, dict)
                return entry
        raise KeyError(base)

    def test_the_sibling_counts_replay(self) -> None:
        self.assertEqual(self.report("L")["nodes"], 3928)
        self.assertEqual(self.report("F")["nodes"], 14293)

    def test_the_empty_rectangle_is_the_recorded_size(self) -> None:
        self.assertEqual(self.report("EMPTY")["nodes"], 577)
        self.assertEqual(self.report("EMPTY")["distinct_regimes"], 75)

    def test_the_earliest_counts_are_the_recorded_ones(self) -> None:
        empty = self.report("EMPTY")["stakes"]
        self.assertEqual(empty["total_apart"]["earliest_index"], 2)
        self.assertEqual(empty["total_same"]["earliest_index"], 4)
        self.assertIsNone(empty["free"]["earliest_index"])
        for base in ("L", "F"):
            stakes = self.report(base)["stakes"]
            self.assertEqual(stakes["total_apart"]["earliest_index"], 0)
            self.assertEqual(stakes["total_same"]["earliest_index"], 2)

    def test_every_zero_counter_is_zero_in_the_receipt(self) -> None:
        reports = self.payload["reports"]
        assert isinstance(reports, list)
        for report in reports:
            self.assertEqual(report["replay_mismatches"], 0)
            self.assertTrue(report["crosscheck"]["reach_agrees"])
            for entry in report["stakes"].values():
                self.assertEqual(entry["procedure_disagreements"], 0)
                self.assertEqual(entry["inert_last_event_violations"], 0)

    def test_the_input_count_claim_is_absent(self) -> None:
        """This rung neither reduces the count of declared inputs nor
        proves it at a floor, and its receipt says so in those words."""
        self.assertEqual(self.payload["input_count_claim"], "none")


if __name__ == "__main__":
    unittest.main()
