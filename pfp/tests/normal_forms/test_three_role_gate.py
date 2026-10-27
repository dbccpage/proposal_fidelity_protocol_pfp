"""Three-role provenance gate: fail-closed separation of proposer, evaluator and authorizer.

AuthorityEffect: None.

Expected verdicts are read from
``pfp/domain/fixtures/three_role_provenance_fixtures.json``; the
tests also mutate admitted packets field by field to show that every
refusal reason is reachable and that no verdict ever carries authority.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pfp.domain.provenance import (
    AUTHORITY_EFFECT,
    GateVerdict,
    ObserverDeclaration,
    PacketShapeError,
    ProvenancePacket,
    RefusalReason,
    Role,
    RoleBinding,
    RolePolicy,
    ThreeRoleGate,
    VerdictCode,
)


# Exact strings from `core_sheaf_theory::empirical_presheaf` for the Bell
# scenario `evaluate_l1_claim` binds: contexts {0,2}|{0,3}|{1,2}|{1,3},
# arities 2,2,2,2. NORM_L1, ADMISSIBILITY_NONCONTEXTUAL, TERMINAL_RULE_L1
# and LAYER_DIAGNOSTIC.
RUST_ADMISSIBILITY_NONCONTEXTUAL = "noncontextual polytope conv(A)"
RUST_NORM_L1 = "L1"
RUST_TERMINAL_RULE_L1 = (
    "defect = 0 -> ExactRepair; defect > 0 and a support-level global section "
    "exists -> ClosedResidual; defect > 0 and none exists -> OpenObstruction"
)
RUST_LAYER_DIAGNOSTIC = "WDP-CH10-D01 diagnostic"
RUST_BELL_KERNEL = (
    "support presheaf over the maximal-context cover "
    "{0,2}|{0,3}|{1,2}|{1,3} with arities 2,2,2,2"
)

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "domain"
    / "fixtures"
    / "three_role_provenance_fixtures.json"
)


def load_fixture() -> dict:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


class ThreeRoleGateFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = load_fixture()
        self.gate = ThreeRoleGate(self.doc["scope"], frozenset(self.doc["admitted_roots"]))
        self.admitted = next(
            case for case in self.doc["cases"] if case["name"] == "separated_roles_admitted"
        )["packet"]

    def test_fixture_declares_no_authority(self) -> None:
        self.assertEqual(self.doc["authority_effect"], "None")
        self.assertEqual(AUTHORITY_EFFECT, "None")

    def test_every_fixture_case_matches_its_expected_verdict(self) -> None:
        names = [case["name"] for case in self.doc["cases"]]
        self.assertEqual(len(names), len(set(names)))
        for case in self.doc["cases"]:
            with self.subTest(case=case["name"]):
                verdict = self.gate.evaluate_mapping(case["packet"])
                self.assertEqual(verdict.code.value, case["expected"]["code"])
                self.assertEqual(
                    [r.value for r in verdict.reasons], case["expected"]["reasons"]
                )
                self.assertEqual(verdict.authority_effect, "None")

    def test_every_refusal_reason_is_reached_by_some_fixture_case(self) -> None:
        reached = {
            reason
            for case in self.doc["cases"]
            for reason in case["expected"]["reasons"]
        }
        self.assertEqual(reached, {reason.value for reason in RefusalReason})

    def test_self_certification_sentence_is_rejected_on_three_counts(self) -> None:
        case = next(
            c for c in self.doc["cases"] if c["name"] == "i_verified_this_and_certify_it"
        )
        verdict = self.gate.evaluate_mapping(case["packet"])
        self.assertIs(verdict.code, VerdictCode.REJECTED)
        self.assertEqual(
            verdict.reasons,
            (
                RefusalReason.SELF_AUTHORIZATION,
                RefusalReason.EVALUATOR_IS_PROPOSER,
                RefusalReason.EVALUATOR_IS_AUTHORIZER,
            ),
        )

    def test_admitted_verdict_still_carries_no_authority(self) -> None:
        verdict = self.gate.evaluate_mapping(self.admitted)
        self.assertTrue(verdict.admitted)
        self.assertEqual(verdict.authority_effect, "None")
        with self.assertRaises(ValueError):
            GateVerdict(VerdictCode.ADMITTED_FOR_AUTHORIZATION, (), "x", authority_effect="Promote")
        with self.assertRaises(ValueError):
            GateVerdict(VerdictCode.REJECTED, (), "no reason")
        with self.assertRaises(ValueError):
            GateVerdict(VerdictCode.SELF_ATTESTED, (RefusalReason.SCOPE_MISMATCH,), "x")

    def test_dropping_any_field_rejects_rather_than_defaults(self) -> None:
        for field in list(self.admitted):
            with self.subTest(field=field):
                payload = copy.deepcopy(self.admitted)
                del payload[field]
                verdict = self.gate.evaluate_mapping(payload)
                self.assertIs(verdict.code, VerdictCode.REJECTED)
                self.assertEqual(verdict.reasons, (RefusalReason.MISSING_FIELD,))
                self.assertIn(field, verdict.detail)

    def test_dropping_any_observer_component_is_undeclared_observer(self) -> None:
        for component in list(self.admitted["observer"]):
            with self.subTest(component=component):
                payload = copy.deepcopy(self.admitted)
                del payload["observer"][component]
                verdict = self.gate.evaluate_mapping(payload)
                self.assertEqual(verdict.reasons, (RefusalReason.UNDECLARED_OBSERVER,))
                self.assertEqual(verdict.detail, component)
                payload = copy.deepcopy(self.admitted)
                payload["observer"][component] = ""
                verdict = self.gate.evaluate_mapping(payload)
                self.assertEqual(verdict.reasons, (RefusalReason.UNDECLARED_OBSERVER,))

    def test_typed_shape_errors_name_their_reason(self) -> None:
        with self.assertRaises(PacketShapeError) as caught:
            ProvenancePacket.from_mapping({**self.admitted, "policy": 7})
        self.assertIs(caught.exception.reason, RefusalReason.MALFORMED_PACKET)
        with self.assertRaises(PacketShapeError) as caught:
            ProvenancePacket.from_mapping([])  # type: ignore[arg-type]
        self.assertIs(caught.exception.reason, RefusalReason.MALFORMED_PACKET)
        with self.assertRaises(PacketShapeError) as caught:
            RoleBinding(Role.PROPOSER, "", "process:x")
        self.assertIs(caught.exception.reason, RefusalReason.EMPTY_IDENTIFIER)
        with self.assertRaises(PacketShapeError) as caught:
            ObserverDeclaration("k", "a", "n", "", "l")
        self.assertIs(caught.exception.reason, RefusalReason.UNDECLARED_OBSERVER)

    def test_role_bindings_must_match_their_slot(self) -> None:
        packet = ProvenancePacket.from_mapping(self.admitted)
        swapped = RoleBinding(Role.AUTHORIZER, packet.proposer.identifier, packet.proposer.principal)
        with self.assertRaises(PacketShapeError) as caught:
            ProvenancePacket(
                packet.claim_id,
                packet.scope,
                swapped,
                packet.evaluator,
                packet.authorizer,
                packet.observer,
                packet.authority_root,
                packet.policy,
            )
        self.assertIs(caught.exception.reason, RefusalReason.MALFORMED_PACKET)

    def test_separation_failures_are_computed_on_identifiers_and_principals(self) -> None:
        packet = ProvenancePacket.from_mapping(self.admitted)
        self.assertEqual(ThreeRoleGate.separation_failures(packet), ())
        one = RoleBinding(Role.EVALUATOR, "other-id", packet.proposer.principal)
        shared = ProvenancePacket(
            packet.claim_id,
            packet.scope,
            packet.proposer,
            one,
            packet.authorizer,
            packet.observer,
            packet.authority_root,
            packet.policy,
        )
        self.assertEqual(
            ThreeRoleGate.separation_failures(shared), (RefusalReason.SHARED_PRINCIPAL,)
        )

    def test_weak_regime_is_self_attested_not_admitted(self) -> None:
        payload = copy.deepcopy(self.admitted)
        payload["policy"] = RolePolicy.SELF_ATTESTED_PERMITTED.value
        payload["evaluator"] = dict(payload["proposer"])
        verdict = self.gate.evaluate_mapping(payload)
        self.assertIs(verdict.code, VerdictCode.SELF_ATTESTED)
        self.assertFalse(verdict.admitted)
        self.assertEqual(verdict.reasons, ())
        # The same packet under the separated policy is a rejection.
        payload["policy"] = RolePolicy.PAIRWISE_DISTINCT.value
        verdict = self.gate.evaluate_mapping(payload)
        self.assertIs(verdict.code, VerdictCode.REJECTED)
        self.assertIn(RefusalReason.EVALUATOR_IS_PROPOSER, verdict.reasons)

    def test_gate_construction_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            ThreeRoleGate("", frozenset({"root:x"}))
        with self.assertRaises(ValueError):
            ThreeRoleGate("prod", frozenset())
        with self.assertRaises(ValueError):
            ThreeRoleGate("prod", {"root:x"})  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ThreeRoleGate("prod", frozenset({" "}))

    def test_non_packet_object_is_rejected(self) -> None:
        verdict = self.gate.evaluate("certified")  # type: ignore[arg-type]
        self.assertIs(verdict.code, VerdictCode.REJECTED)
        self.assertEqual(verdict.reasons, (RefusalReason.MALFORMED_PACKET,))

    def test_non_string_mapping_key_is_a_typed_refusal_at_every_level(self) -> None:
        # Review finding on #1080: a non-string key reached ``', '.join`` and
        # escaped ``evaluate_mapping`` as a TypeError. It is now refused as a
        # malformed packet at the top level, inside a role binding and inside
        # the observer, without the key being coerced to a string.
        for path in ((), ("proposer",), ("observer",)):
            with self.subTest(path=path):
                payload = copy.deepcopy(self.admitted)
                target = payload
                for step in path:
                    target = target[step]
                target[7] = "x"
                verdict = self.gate.evaluate_mapping(payload)
                self.assertIs(verdict.code, VerdictCode.REJECTED)
                self.assertEqual(verdict.reasons, (RefusalReason.MALFORMED_PACKET,))
                self.assertIn("a key is not a string", verdict.detail)
                self.assertNotIn("7", verdict.detail)
                with self.assertRaises(PacketShapeError) as caught:
                    ProvenancePacket.from_mapping(payload)
                self.assertIs(caught.exception.reason, RefusalReason.MALFORMED_PACKET)


    def test_admitted_observer_matches_rust_l1_constants(self) -> None:
        observer = self.admitted["observer"]
        self.assertEqual(observer["norm"], RUST_NORM_L1)
        self.assertEqual(observer["admissibility"], RUST_ADMISSIBILITY_NONCONTEXTUAL)
        self.assertEqual(observer["terminal"], RUST_TERMINAL_RULE_L1)
        self.assertEqual(observer["layer"], RUST_LAYER_DIAGNOSTIC)
        self.assertEqual(observer["kernel"], RUST_BELL_KERNEL)
        verdict = self.gate.evaluate_mapping(self.admitted)
        self.assertTrue(verdict.admitted)


if __name__ == "__main__":
    unittest.main()
