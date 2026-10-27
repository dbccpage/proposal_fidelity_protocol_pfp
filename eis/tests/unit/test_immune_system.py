"""Targeted unit tests for Epistemic Immune System (EIS) domain models and gates.

Verifies:
  1. Exact-type equality guard on all domain value objects.
  2. Polly Matzinger's Two-Signal Danger Gate activation semantics.
  3. Thymic Central Tolerance negative selection against clean self-panels.
  4. Sigmoidal Hill cooperativity in AllostericConsensusGate.
  5. Clonal affinity maturation and half-life decay.
"""

from __future__ import annotations

import unittest

from eis.domain import (
    AllostericConsensusGate,
    ClonalSelectionEngine,
    DangerDecision,
    DangerSeverity,
    DetectorRule,
    HillParameters,
    Signal1Match,
    Signal2Danger,
    ThymusGate,
    TwoSignalDangerGate,
)


class DummyClass:
    """Class used to assert exact-type equality guard rejection."""
    pass


class TestEpistemicImmuneSystem(unittest.TestCase):
    def test_exact_type_equality_guards(self) -> None:
        """Assert Value Objects reject comparison against foreign classes."""
        s1 = Signal1Match(epitope_name="HAL-01", pattern_matched="universal_solver", confidence=0.95, offset=12)
        s2 = Signal2Danger(danger_type="PARITY_BREACH", severity=DangerSeverity.HIGH, defect_count=3, evidence_digest="abc123")
        hp = HillParameters(hill_coefficient=2, half_maximal_constant=2)
        rule = DetectorRule(rule_id="RULE-01", target_epitope="HAL-01", match_pattern=r"universal\s{1,4}solver")

        dummy = DummyClass()
        self.assertFalse(s1 == dummy)
        self.assertFalse(s2 == dummy)
        self.assertFalse(hp == dummy)
        self.assertFalse(rule == dummy)

        # Equal instances should evaluate to True and hash identically
        s1_clone = Signal1Match(epitope_name="HAL-01", pattern_matched="universal_solver", confidence=0.95, offset=12)
        self.assertEqual(s1, s1_clone)
        self.assertEqual(hash(s1), hash(s1_clone))

    def test_two_signal_danger_gate_clean_tolerated(self) -> None:
        """Assert zero signals yields clean tolerated execution."""
        res = TwoSignalDangerGate.evaluate(signal1_matches=[], signal2_danger=None)
        self.assertEqual(res.decision, DangerDecision.TOLERATED)
        self.assertFalse(res.is_suppressed)
        self.assertEqual(res.signal1_count, 0)

    def test_two_signal_danger_gate_signal1_alone_is_diagnostic(self) -> None:
        """Assert Signal 1 alone (antigen match without tissue stress) is NOT suppressed."""
        match = Signal1Match(epitope_name="TODO_SYNTAX", pattern_matched="TODO: fixme", confidence=0.8, offset=0)
        res = TwoSignalDangerGate.evaluate(signal1_matches=[match], signal2_danger=None)
        self.assertEqual(res.decision, DangerDecision.DIAGNOSTIC_ONLY)
        self.assertFalse(res.is_suppressed)
        self.assertEqual(res.signal1_count, 1)

    def test_two_signal_danger_gate_signal2_alone_is_diagnostic(self) -> None:
        """Signal 2 alone (damage without an epitope match) does not suppress.

        The docstring requires both signals; the old code locked down on a
        HIGH or CRITICAL Signal 2 alone.
        """
        danger = Signal2Danger(
            danger_type="AUTHORITY_ESCALATION",
            severity=DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest="dig-99",
        )
        res = TwoSignalDangerGate.evaluate(signal1_matches=[], signal2_danger=danger)
        self.assertEqual(res.decision, DangerDecision.DIAGNOSTIC_ONLY)
        self.assertFalse(res.is_suppressed)

    def test_two_signal_danger_gate_cooccurrence_quarantines(self) -> None:
        """Assert Signal 1 AND Signal 2 co-occurrence quarantines the pathogen."""
        match = Signal1Match(epitope_name="UNIVERSAL_CLAIM", pattern_matched="solves all instances", confidence=0.99)
        danger = Signal2Danger(
            danger_type="NON_DESCENT",
            severity=DangerSeverity.CRITICAL,
            defect_count=5,
            evidence_digest="dig-def-5",
        )
        res = TwoSignalDangerGate.evaluate(signal1_matches=[match], signal2_danger=danger)
        self.assertEqual(res.decision, DangerDecision.QUARANTINED)
        self.assertTrue(res.is_suppressed)

    def test_thymus_negative_selection_purges_autoimmune_rule(self) -> None:
        """Assert candidate detector binding clean self-tissue is rejected via apoptosis."""
        clean_self_panel = [
            "class CleanArchitecturePort:\n    def execute(self) -> None:\n        pass",
            "theorem exact_involution : P (P x) = P x := by rfl",
            "def safe_evaluator(x: Nat) : Nat := x + 1",
        ]
        thymus = ThymusGate(clean_self_panel)

        # Overzealous rule matching standard Python 'def ' keyword
        bad_rule = DetectorRule(rule_id="BAD-DEF", target_epitope="OVERZEALOUS", match_pattern=r"\bdef\s{1,4}\w{1,32}")
        result = thymus.evaluate_rule(bad_rule)

        self.assertFalse(result.is_admitted)
        self.assertTrue(result.autoimmune_violations > 0)
        self.assertIn("Autoimmune apoptosis", result.rationale)

    def test_thymus_negative_selection_admits_self_tolerant_rule(self) -> None:
        """Assert candidate detector specific to genuine pathogen is admitted."""
        clean_self_panel = [
            "class CleanArchitecturePort:\n    def execute(self) -> None:\n        pass",
            "theorem exact_involution : P (P x) = P x := by rfl",
            "def safe_evaluator(x: Nat) : Nat := x + 1",
        ]
        thymus = ThymusGate(clean_self_panel)

        # Specific rule matching known red-team prompt exploit
        good_rule = DetectorRule(
            rule_id="GOOD-PATHOGEN",
            target_epitope="JAILBREAK",
            match_pattern=r"ignore\s{1,4}all\s{1,4}previous\s{1,4}instructions",
        )
        result = thymus.evaluate_rule(good_rule)

        self.assertTrue(result.is_admitted)
        self.assertEqual(result.autoimmune_violations, 0)
        self.assertIn("Self-tolerance certified", result.rationale)

    def test_allosteric_cooperativity_sigmoidal_curve(self) -> None:
        """Exact Hill response; activation is a threshold on the summed signals."""
        from fractions import Fraction

        params = HillParameters(hill_coefficient=3, half_maximal_constant=2)
        gate = AllostericConsensusGate(parameters=params, activation_threshold=Fraction(1, 2))

        # Sum 1: H(1) = 1 / (8 + 1) = 1/9 < 1/2
        sub_decision = gate.evaluate_quorum({"a": Fraction(1, 2), "b": Fraction(1, 2)})
        self.assertFalse(sub_decision.is_activated)
        self.assertEqual(sub_decision.hill_value, Fraction(1, 9))

        # Sum 5/2: H(5/2) = (125/8) / (8 + 125/8) = 125/189 >= 1/2
        act_decision = gate.evaluate_quorum({"a": 1, "b": 1, "c": Fraction(1, 2)})
        self.assertTrue(act_decision.is_activated)
        self.assertEqual(act_decision.hill_value, Fraction(125, 189))

    def test_clonal_selection_maturation_and_decay(self) -> None:
        """Assert rule stimulation increases affinity and decay evaporates idle rules."""
        rule = DetectorRule(
            rule_id="RULE-CLONE-1",
            target_epitope="MALICIOUS_PROMPT",
            match_pattern=r"disable_safety",
            affinity_score=1.0,
            half_life_runs=3,
            runs_idle=0,
            is_active=True,
        )

        # Stimulation upon pathogen detection
        stimulated = ClonalSelectionEngine.stimulate(rule, affinity_boost=0.5)
        self.assertEqual(stimulated.affinity_score, 1.5)
        self.assertEqual(stimulated.runs_idle, 0)

        # Simulating 3 idle runs
        r1 = ClonalSelectionEngine.apply_decay(stimulated)
        self.assertTrue(r1.is_active)
        self.assertEqual(r1.runs_idle, 1)

        r2 = ClonalSelectionEngine.apply_decay(r1)
        self.assertTrue(r2.is_active)
        self.assertEqual(r2.runs_idle, 2)

        r3 = ClonalSelectionEngine.apply_decay(r2)
        # Reached half_life_runs=3 -> evaporated
        self.assertFalse(r3.is_active)
        self.assertEqual(r3.runs_idle, 3)

        # Filter active repertoire
        active_repertoire = ClonalSelectionEngine.filter_active_repertoire([r1, r3])
        self.assertEqual(len(active_repertoire), 1)
        self.assertEqual(active_repertoire[0].rule_id, "RULE-CLONE-1")

    def test_immune_guarded_substitute_tolerated_and_suppressed(self) -> None:
        """Planar substitution guarded by the independent two-signal gate through the port."""
        from operads.application.immune_guards import (
            immune_guarded_substitute,
        )
        from operads.application.ports.immune_screen_port import (
            DetectorIdentity,
            DetectorMatch,
            HostDangerObservation,
        )
        from operads.domain.planar_substitution import (
            OperadOperation,
            SubstitutionError,
        )
        from operads.infrastructure.immune import OeeisImmuneAdapter

        immune = OeeisImmuneAdapter()
        detector = DetectorIdentity("prompt-scanner", frozenset(), False)

        theta = OperadOperation(name="theta", source_colours=("Audit", "State"), target_colour="Receipt")
        phi = OperadOperation(name="phi", source_colours=("Ledger",), target_colour="Audit")

        # 1. Clean substitution succeeds
        comp = immune_guarded_substitute(theta, 0, phi, immune=immune, detector=detector)
        self.assertEqual(comp.source_colours, ("Ledger", "State"))
        self.assertEqual(comp.target_colour, "Receipt")

        # 2. Signal 1 alone (benign/diagnostic) still succeeds
        match = DetectorMatch(epitope="BENIGN", matched_text="test", offset=0)
        comp2 = immune_guarded_substitute(theta, 0, phi, immune=immune, detector=detector, matches=(match,))
        self.assertEqual(comp2.target_colour, "Receipt")

        # 3. Signal 1 + an independent host Signal 2 raises SubstitutionError
        danger = HostDangerObservation(
            kind="REPLAY_FAILURE",
            severity="CRITICAL",
            defect_count=2,
            evidence_digest="sha256:" + "c" * 64,
            observer_id="host-replayer",
        )
        with self.assertRaises(SubstitutionError) as ctx:
            immune_guarded_substitute(
                theta, 0, phi, immune=immune, detector=detector, matches=(match,), danger=danger
            )
        self.assertEqual(ctx.exception.code, "DANGER_GATE_SUPPRESSION")

    def test_workflow_immune_guard_policy(self) -> None:
        """Workflow report gated by DangerSignalPolicy through the port."""
        from operads.application.immune_guards import (
            validate_workflow_immune_guard,
        )
        from operads.application.ports.immune_screen_port import (
            DetectorIdentity,
            DetectorMatch,
            HostDangerObservation,
        )
        from operads.domain.planar_substitution import OperadOperation
        from operads.domain.workflow_graph import (
            DangerSignalPolicy,
            WorkflowReport,
        )
        from operads.infrastructure.immune import OeeisImmuneAdapter

        immune = OeeisImmuneAdapter()
        detector = DetectorIdentity("prompt-scanner", frozenset(), False)

        op = OperadOperation(name="dummy_wf", source_colours=("State",), target_colour="Receipt")
        report = WorkflowReport(workflow_id="wf-test", declared=op, composed=op, findings=())

        match = DetectorMatch(epitope="MALICIOUS_PROMPT", matched_text="attack", offset=0)
        danger = HostDangerObservation(
            kind="PROTECTED_FIELD_VIOLATION",
            severity="HIGH",
            defect_count=1,
            evidence_digest="sha256:" + "d" * 64,
            observer_id="host-protected-field-check",
        )

        # Gated with enforce_danger_gate=True -> suppresses
        policy = DangerSignalPolicy(enforce_danger_gate=True)
        gated_report = validate_workflow_immune_guard(
            report, policy, immune=immune, detector=detector, matches=(match,), danger=danger
        )
        self.assertFalse(gated_report.is_valid)
        self.assertIsNone(gated_report.composed)
        self.assertEqual(gated_report.findings[0].code, "DANGER_GATE_SUPPRESSION")

        # Gated with enforce_danger_gate=False -> passes through
        pass_policy = DangerSignalPolicy(enforce_danger_gate=False)
        passed_report = validate_workflow_immune_guard(
            report, pass_policy, immune=immune, detector=detector, matches=(match,), danger=danger
        )
        self.assertTrue(passed_report.is_valid)
        self.assertIsNotNone(passed_report.composed)

    def test_allosteric_consensus_planar_substitution(self) -> None:
        """Planar substitution gated by the exact allosteric gate through the immune port."""
        from fractions import Fraction

        from operads.application.immune_guards import (
            allosteric_consensus_substitute,
        )
        from operads.application.ports.immune_screen_port import (
            SensorReading,
        )
        from operads.domain.planar_substitution import (
            OperadOperation,
            SubstitutionError,
        )
        from operads.infrastructure.immune import OeeisImmuneAdapter

        immune = OeeisImmuneAdapter()
        theta = OperadOperation(name="theta_op", source_colours=("Code",), target_colour="Audit")
        phi = OperadOperation(name="phi_op", source_colours=("Proof",), target_colour="Code")

        # Sum 1/2 < 2 at the defaults -> refused
        with self.assertRaises(SubstitutionError) as cm:
            allosteric_consensus_substitute(
                theta,
                0,
                phi,
                [SensorReading("a", Fraction(1, 5)), SensorReading("b", Fraction(3, 10))],
                immune=immune,
            )
        self.assertEqual(cm.exception.code, "ALLOSTERIC_QUORUM_NOT_MET")

        # Sum 5/2 >= 2 from three distinct capped sensors -> passes
        composed = allosteric_consensus_substitute(
            theta,
            0,
            phi,
            [SensorReading("a", 1), SensorReading("b", 1), SensorReading("c", Fraction(1, 2))],
            immune=immune,
        )
        self.assertEqual(composed.target_colour, "Audit")
        self.assertEqual(composed.source_colours, ("Proof",))

    def test_admit_skill_with_thymus_gate(self) -> None:
        """Assert candidate skills are screened against self-panel fixtures."""
        from operads.application.immune_guards import (
            admit_skill_with_thymus,
        )
        from operads.domain.capability_catalog_v1 import (
            CapabilityCatalogRefusal,
            SkillCapabilityV1,
        )
        from operads.infrastructure.immune import OeeisImmuneAdapter

        thymus = OeeisImmuneAdapter(self_panel=["theorem coboundary_nilpotent : d1 * d0 = 0"])

        # Clean skill: no match to self-panel
        clean_skill = SkillCapabilityV1(
            skill_id="clean-auditor",
            name="clean-auditor",
            description="Audits clean architecture boundaries",
            source_path=".agents/skills/clean-auditor/SKILL.md",
            source_digest="a" * 64,
            source_colours=("Code",),
            target_colour="Audit",
            arity=1,
            residual_effect="audited",
            invocation="/clean-auditor",
            invocation_explicit=True,
            families=("audit",),
            declared_dependencies=(),
            declared_triggers=("audit boundary",),
            package_resources=(),
        )
        admitted = admit_skill_with_thymus(clean_skill, immune=thymus)
        self.assertEqual(admitted.skill_id, "clean-auditor")

        # Auto-reactive skill matching clean theorem
        toxic_skill = SkillCapabilityV1(
            skill_id="toxic-hunter",
            name="toxic-hunter",
            description="Matches valid math proofs by mistake",
            source_path=".agents/skills/toxic-hunter/SKILL.md",
            source_digest="b" * 64,
            source_colours=("Proof",),
            target_colour="Audit",
            arity=1,
            residual_effect="audited",
            invocation="/toxic-hunter",
            invocation_explicit=True,
            families=("audit",),
            declared_dependencies=(),
            declared_triggers=("coboundary_nilpotent",),
            package_resources=(),
        )
        with self.assertRaises(CapabilityCatalogRefusal) as cm:
            admit_skill_with_thymus(toxic_skill, immune=thymus)
        self.assertEqual(cm.exception.code, "AUTOIMMUNE_REACTION_ERROR")

    def test_operad_treg_supervisor_downgrades_toxic_operation(self) -> None:
        """Only independently checked benign suppressions count as false positives."""
        from fractions import Fraction
        from hashlib import sha256

        from operads.domain.operad import OperadTregSupervisor
        from operads.domain.operad.treg import CheckedFalsePositive

        def checked(subject):
            return CheckedFalsePositive('anti-op', sha256(subject.encode()).hexdigest(),
                'independent-control', sha256(('observed:' + subject).encode()).hexdigest())

        supervisor = OperadTregSupervisor(tau_threshold=Fraction(2, 5))

        # Two observed harmful controls remain legitimate defenses.
        receipt1 = supervisor.record_operation_step("anti-op", suppressed=True, danger_confirmed=True)
        self.assertIsNone(receipt1)
        self.assertFalse(supervisor.is_downgraded("anti-op"))

        receipt2 = supervisor.record_operation_step("anti-op", suppressed=True, danger_confirmed=True)
        self.assertIsNone(receipt2)

        # One checked false positive / three evaluated suppressions <= 2/5.
        receipt3 = supervisor.record_operation_step("anti-op", suppressed=True, danger_confirmed=False,
            false_positive=checked('benign-1'), learned_detector=True)
        self.assertIsNone(receipt3)
        self.assertFalse(supervisor.is_downgraded("anti-op"))

        # Two checked false positives / four evaluated suppressions > 2/5.
        receipt4 = supervisor.record_operation_step("anti-op", suppressed=True, danger_confirmed=False,
            false_positive=checked('benign-2'), learned_detector=True)
        self.assertIsNotNone(receipt4)
        self.assertEqual(receipt4.downgraded_authority, "DIAGNOSTIC_ONLY")
        self.assertEqual(receipt4.toxicity_index, Fraction(1, 2))
        self.assertTrue(supervisor.is_downgraded("anti-op"))

        # Step 5: already downgraded -> no duplicate receipt, remains downgraded
        receipt5 = supervisor.record_operation_step("anti-op", suppressed=True, danger_confirmed=False,
            false_positive=checked('benign-3'), learned_detector=True)
        self.assertIsNone(receipt5)
        self.assertTrue(supervisor.is_downgraded("anti-op"))

    def test_antimorphism_immune_bench_and_phagocytic_regenerator(self) -> None:
        """Assert AntimorphismImmuneBench and PhagocyticFormularyRegenerator filter and mature antibodies."""
        from eis.infrastructure import (
            CLEAN_PHYSICS_SELF_PANEL,
            AntimorphismImmuneBench,
            ImmuneBenchReport,
            PhagocyticFormularyRegenerator,
        )

        bench = AntimorphismImmuneBench()
        self.assertEqual(len(CLEAN_PHYSICS_SELF_PANEL), 6)

        # 1. Valid anti-morphism detector (doesn't match clean physics)
        valid_rule = DetectorRule(
            rule_id="RULE-CLEAN-01",
            target_epitope="FAKE_SOLVER",
            match_pattern=r"universal\s{1,4}fermion\s{1,4}solver",
        )
        # 2. Autoimmune anti-morphism detector (matches Troyer & Wiese excerpt in CLEAN_PHYSICS_SELF_PANEL)
        autoimmune_rule = DetectorRule(
            rule_id="RULE-TOXIC-01",
            target_epitope="SIGN_COMPLEXITY",
            match_pattern=r"NP-hard;\s{1,4}no\s{1,4}polynomial-time",
        )

        report = bench.screen_candidate_rules([valid_rule, autoimmune_rule])
        self.assertEqual(report.total_rules_evaluated, 2)
        self.assertEqual(report.admitted_rules, 1)
        self.assertEqual(report.purged_rules, 1)

        # Exact-type equality test on ImmuneBenchReport
        report_clone = ImmuneBenchReport(
            total_rules_evaluated=2,
            admitted_rules=1,
            purged_rules=1,
            results=report.results,
        )
        self.assertEqual(report, report_clone)
        self.assertEqual(hash(report), hash(report_clone))

        # Clonal mutation and aging
        mutated = bench.mutate_and_mature(valid_rule, mutation_variant=r"universal\s{1,4}quantum\s{1,4}solver", new_rule_id="RULE-CLEAN-02")
        self.assertEqual(mutated.rule_id, "RULE-CLEAN-02")
        self.assertEqual(mutated.generation, 2)

        aged_repertoire = bench.age_repertoire([mutated])
        self.assertEqual(len(aged_repertoire), 1)

        # Phagocytic formulary regeneration from CemeterySink motifs
        regenerator = PhagocyticFormularyRegenerator(bench=bench)
        motifs = [
            ("universal quantum solver", "EXPLOIT_EPITOPE"),
            ("Hubbard model on any bipartite lattice", "CLEAN_PHYSICS_EXCERPT"),
        ]
        admitted_antibodies = regenerator.phagocytose_and_admit(motifs)
        self.assertEqual(len(admitted_antibodies), 1)
        self.assertEqual(admitted_antibodies[0].target_epitope, "EXPLOIT_EPITOPE")

    def test_admit_skill_with_thymus_treats_triggers_as_literal_phrases(self) -> None:
        """Triggers are escaped: metacharacters neither crash nor over-match.

        Mutation: dropping re.escape admits the '*' trigger (as a regex it does not
        match the fixture) and refuses 'c++' as a regex syntax error.
        """
        from operads.application.immune_guards import (
            admit_skill_with_thymus,
        )
        from operads.domain.capability_catalog_v1 import (
            CapabilityCatalogRefusal,
            SkillCapabilityV1,
        )
        from operads.infrastructure.immune import OeeisImmuneAdapter

        thymus = OeeisImmuneAdapter(self_panel=["theorem coboundary_nilpotent : d1 * d0 = 0"])

        def skill(triggers: tuple[str, ...]) -> SkillCapabilityV1:
            return SkillCapabilityV1(
                skill_id="phrase-skill",
                name="phrase-skill",
                description="phrase trigger fixture",
                source_path=".agents/skills/phrase-skill/SKILL.md",
                source_digest="c" * 64,
                source_colours=("Code",),
                target_colour="Audit",
                arity=1,
                residual_effect="audited",
                invocation="/phrase-skill",
                invocation_explicit=True,
                families=("audit",),
                declared_dependencies=(),
                declared_triggers=triggers,
                package_resources=(),
            )

        self.assertEqual(admit_skill_with_thymus(skill(("  ", "c++ review")), immune=thymus).skill_id, "phrase-skill")
        self.assertEqual(admit_skill_with_thymus(skill((".",)), immune=thymus).skill_id, "phrase-skill")
        with self.assertRaises(CapabilityCatalogRefusal) as cm:
            admit_skill_with_thymus(skill(("d1 * d0",)), immune=thymus)
        self.assertEqual(cm.exception.code, "AUTOIMMUNE_REACTION_ERROR")

    def test_operad_treg_supervisor_waits_for_minimum_sample(self) -> None:
        """Unconfirmed suppression never contributes a false positive."""
        from fractions import Fraction

        from operads.domain.operad import OperadTregSupervisor

        supervisor = OperadTregSupervisor(tau_threshold=Fraction(2, 5))
        self.assertIsNone(supervisor.record_operation_step("op", suppressed=True, danger_confirmed=False))
        self.assertFalse(supervisor.is_downgraded("op"))
        self.assertIsNone(supervisor.record_operation_step("op", suppressed=True, danger_confirmed=True))
        receipt = supervisor.record_operation_step("op", suppressed=True, danger_confirmed=True)
        self.assertIsNone(receipt)
        self.assertFalse(supervisor.is_downgraded("op"))

        for bad in (0, -1, True, 2.0):
            with self.assertRaises(ValueError):
                OperadTregSupervisor(min_suppressions=bad)

    def test_immune_bench_report_rejects_inconsistent_counts(self) -> None:
        """A report whose counts disagree with its results must not construct."""
        from eis.infrastructure import ImmuneBenchReport

        with self.assertRaises(ValueError):
            ImmuneBenchReport(total_rules_evaluated=5, admitted_rules=1, purged_rules=1, results=())
        with self.assertRaises(ValueError):
            ImmuneBenchReport(total_rules_evaluated=2, admitted_rules=1, purged_rules=1, results=())
        with self.assertRaises(ValueError):
            ImmuneBenchReport(total_rules_evaluated=True, admitted_rules=0, purged_rules=0, results=())


if __name__ == "__main__":
    unittest.main()
