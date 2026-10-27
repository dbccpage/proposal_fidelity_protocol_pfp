"""Adversarial replay checks for the declared stage-zero lift model."""

from dataclasses import replace
import hashlib
from itertools import product
import json
from pathlib import Path
import sys
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from pfp.domain.mssn_research.grammar.lift_policies import (
    check_lift_necessity_certificate,
    execute_bounded_lift_necessity_search,
)
from pfp.domain.mssn_research.grammar.spectral_geometry import LiftGoal
from pfp.domain.mssn_research.shared_kernel.value_objects import ContentDigest, StageLevel


class TestLiftNecessityReplayBoundary(unittest.TestCase):
    def certificate(self, goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION):
        return execute_bounded_lift_necessity_search(StageLevel(0), goal).unwrap()

    def refused(self, certificate, label):
        result = check_lift_necessity_certificate(certificate)
        self.assertTrue(result.is_refusal())
        self.assertIn(label, result.refusal.message)

    def test_empty_diagonal_or_off_domain_target_cannot_reuse_valid_digest(self):
        valid = self.certificate()
        for witness in ("R={}", "R={(0,0)}", "R={(0,2)}", "invalid"):
            with self.subTest(witness=witness):
                self.refused(replace(valid, target_resolution_witness=witness), "REFUSED_TARGET_WITNESS")

    def test_distinct_names_require_the_canonical_resolving_pair(self):
        valid = self.certificate(LiftGoal.DISTINCT_NAME_GENERATION)
        self.assertTrue(check_lift_necessity_certificate(valid).is_ok())
        for witness in ("GEN={}", "GEN={<0>}", "GEN={<0>,<0>}", "R={(0,1)}"):
            with self.subTest(witness=witness):
                self.refused(replace(valid, target_resolution_witness=witness), "REFUSED_TARGET_WITNESS")

    def test_noncanonical_valid_relation_is_outside_this_certificate_format(self):
        # This relation satisfies the goal but is not the declared first witness.
        self.refused(replace(self.certificate(), target_resolution_witness="R={(1,0)}"), "REFUSED_TARGET_WITNESS")

    def test_unsupported_stage_rejects_forged_flag_and_all_arbitrary_evidence(self):
        valid = self.certificate()
        for stage in (2, 20, 100):
            forged = replace(valid, source_stage=StageLevel(stage), target_stage=StageLevel(stage + 1),
                             goal=LiftGoal.BARE_ASSERTION, evaluated_configurations_count=0,
                             exhaustion_proof_digest=ContentDigest("f" * 64), target_resolution_witness="invalid")
            self.refused(forged, "REFUSED_UNIMPLEMENTED_STAGE_SEARCH")
            self.assertTrue(execute_bounded_lift_necessity_search(StageLevel(stage), valid.goal).is_refusal())

    def test_resealed_obstruction_and_carrier_changes_are_rejected(self):
        valid = self.certificate()
        forged_obstruction = "NO_OBSTRUCTION"
        old_trace = (f"SOURCE=0:GOAL={valid.goal.value}:CONFIGS=2:OBSTRUCTION={forged_obstruction}"
                     ":TARGET=1:WITNESS=(0,1)")
        forged_digest = ContentDigest(hashlib.sha256(old_trace.encode()).hexdigest())
        self.refused(replace(valid, surviving_obstruction_code=forged_obstruction,
                             exhaustion_proof_digest=forged_digest), "REFUSED_OBSTRUCTION_MISMATCH")
        for source, target in ((2, 3), (1, 3), (1000000, 1000001)):
            self.refused(replace(valid, carrier_size_source=source, carrier_size_target=target), "REFUSED_CARRIER_DOMAIN")

    def test_count_goal_and_verification_flag_do_not_replace_replay(self):
        valid = self.certificate()
        for count in (0, 1, 3, 16):
            self.refused(replace(valid, evaluated_configurations_count=count), "REFUSED_INCOMPLETE_EXHAUSTION")
        self.refused(replace(valid, goal=LiftGoal.BARE_ASSERTION), "REFUSED_LIFT_UNEARNED")
        self.refused(replace(valid, is_verified=False), "REFUSED_UNVERIFIED_CERTIFICATE")

    def test_boolean_and_negative_integer_fields_are_not_admitted(self):
        valid = self.certificate()
        for field in ("carrier_size_source", "carrier_size_target", "evaluated_configurations_count"):
            with self.subTest(field=field), self.assertRaises(TypeError):
                replace(valid, **{field: True})
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(valid, **{field: -1})

    def test_digest_matches_independent_exhaustion_and_binds_target_witness(self):
        # Cartesian Boolean vectors are independent of the implementation's bit masks.
        def relation_rows(size):
            edges = tuple(product(range(size), repeat=2))
            rows = []
            for flags in product((False, True), repeat=len(edges)):
                relation = tuple(edge for edge, enabled in zip(edges, flags) if enabled)
                mask = sum((1 << index) for index, enabled in enumerate(flags) if enabled)
                row = {"configuration": "R={" + ",".join(f"({a},{b})" for a, b in relation) + "}",
                       "satisfies_goal": bool(relation) and all(a != b for a, b in relation)}
                rows.append((mask, row))
            return [row for _, row in sorted(rows)]

        source_rows, target_rows = relation_rows(1), relation_rows(2)
        self.assertEqual(len(source_rows), 2)
        self.assertEqual(len(target_rows), 16)
        self.assertEqual(sum(row["satisfies_goal"] for row in source_rows), 0)
        self.assertEqual(sum(row["satisfies_goal"] for row in target_rows), 3)
        valid = self.certificate()
        replay = {"schema": "mssn.stage-zero-lift-replay.v2", "source_stage": 0, "target_stage": 1,
                  "goal": valid.goal.value, "carrier_size_source": 1, "carrier_size_target": 2,
                  "source_configurations": source_rows, "target_configurations": target_rows,
                  "surviving_obstruction_code": "OBSTRUCTION_SUBSINGLETON_DIAGONAL_SELF_RELATION",
                  "target_resolution_witness": "R={(0,1)}"}
        digest = lambda value: ContentDigest(hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest())
        self.assertEqual(valid.exhaustion_proof_digest, digest(replay))
        replay["target_resolution_witness"] = "R={}"
        self.assertNotEqual(valid.exhaustion_proof_digest, digest(replay))
        self.refused(replace(valid, target_resolution_witness="R={}", exhaustion_proof_digest=digest(replay)), "REFUSED_TARGET_WITNESS")


if __name__ == "__main__":
    unittest.main()
