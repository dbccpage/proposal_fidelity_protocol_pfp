"""OEWAS reaches the Epistemic Immune System only through `ImmuneScreenPort`.

Counterexamples:

- the OEWAS domain imported the OEEIS domain (`domain/workflow_graph.py`,
  `domain/planar_substitution.py`, `domain/capability_catalog_v1.py`);
- (review, 2026-09-29) the port accepted `detector_id=None` and then ran the
  unchecked gate, so a Signal 2 derived from Signal 1 suppressed a substitution;
- (review) the port took `Sequence[object]` instead of records it owns;
- (review) `quorum_verdict([1, 1])` from one caller activated the quorum.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

import pytest

from operads.application.immune_guards import (
    admit_skill_with_thymus,
    allosteric_consensus_substitute,
    immune_guarded_substitute,
    validate_workflow_immune_guard,
)
from operads.application.ports.immune_screen_port import (
    DetectorIdentity,
    DetectorMatch,
    HostDangerObservation,
    ImmuneEvidenceRefusal,
    ImmuneVerdict,
    SensorReading,
)
from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogRefusal,
    SkillCapabilityV1,
)
from operads.domain.planar_substitution import (
    OperadOperation,
    SubstitutionError,
)
from operads.domain.workflow_graph import (
    DangerSignalPolicy,
    WorkflowReport,
)

PACKAGE = Path(__file__).resolve().parents[2]
THETA = OperadOperation(name="theta", source_colours=("Audit", "State"), target_colour="Receipt")
PHI = OperadOperation(name="phi", source_colours=("Ledger",), target_colour="Audit")
DETECTOR = DetectorIdentity("prompt-scanner", frozenset(), False)
MATCH = DetectorMatch(epitope="E", matched_text="m", offset=0)
DANGER = HostDangerObservation(
    kind="PROTECTED_FIELD_VIOLATION",
    severity="HIGH",
    defect_count=1,
    evidence_digest="sha256:" + "a" * 64,
    observer_id="host-protected-field-check",
)


class StubImmune:
    """A port whose verdicts are fixed; records what it was asked."""

    def __init__(self, blocks: bool, decision: str = "STUB") -> None:
        self.verdict = ImmuneVerdict(blocks=blocks, decision=decision, rationale="stub rationale")
        self.calls: list[tuple] = []

    def danger_verdict(self, matches, danger, *, detector):
        self.calls.append(("danger", tuple(matches), danger, detector))
        return self.verdict

    def quorum_verdict(self, readings):
        self.calls.append(("quorum", tuple(readings)))
        return self.verdict

    def trigger_tolerance_verdict(self, rule_id, phrases):
        self.calls.append(("thymus", rule_id, tuple(phrases)))
        return self.verdict


def _skill(triggers: tuple[str, ...]) -> SkillCapabilityV1:
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


def test_the_domain_does_not_import_the_immune_system() -> None:
    for relative in ("workflow_graph.py", "planar_substitution.py", "capability_catalog_v1.py"):
        tree = ast.parse((PACKAGE / "domain" / relative).read_text(encoding="utf-8"))
        names = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ] + [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        assert not any(name.startswith("eis") for name in names), relative


def test_guards_follow_the_port_verdict() -> None:
    assert immune_guarded_substitute(
        THETA, 0, PHI, immune=StubImmune(False), detector=DETECTOR
    ).source_colours == ("Ledger", "State")
    with pytest.raises(SubstitutionError) as caught:
        immune_guarded_substitute(THETA, 0, PHI, immune=StubImmune(True), detector=DETECTOR)
    assert caught.value.code == "DANGER_GATE_SUPPRESSION"
    with pytest.raises(SubstitutionError) as caught:
        allosteric_consensus_substitute(THETA, 0, PHI, [SensorReading("a", 1)], immune=StubImmune(True))
    assert caught.value.code == "ALLOSTERIC_QUORUM_NOT_MET"


def test_the_detector_identity_is_required() -> None:
    """Counterexample: `detector_id=None` used to select the unchecked gate."""
    with pytest.raises(TypeError):
        immune_guarded_substitute(THETA, 0, PHI, immune=StubImmune(False))  # type: ignore[call-arg]


def test_the_workflow_guard_respects_the_policy_and_the_port() -> None:
    report = WorkflowReport(workflow_id="wf", declared=THETA, composed=THETA, findings=())
    blocked = validate_workflow_immune_guard(
        report, DangerSignalPolicy(), immune=StubImmune(True), detector=DETECTOR
    )
    assert blocked.composed is None and blocked.findings[0].code == "DANGER_GATE_SUPPRESSION"
    off = StubImmune(True)
    assert (
        validate_workflow_immune_guard(
            report, DangerSignalPolicy(enforce_danger_gate=False), immune=off, detector=DETECTOR
        )
        is report
    )
    assert off.calls == []


def test_the_thymus_guard_distinguishes_autoimmunity_from_unscreenable() -> None:
    with pytest.raises(CapabilityCatalogRefusal) as caught:
        admit_skill_with_thymus(_skill(("x",)), immune=StubImmune(True, "REFUSED"))
    assert caught.value.code == "AUTOIMMUNE_REACTION_ERROR"
    with pytest.raises(CapabilityCatalogRefusal) as caught:
        admit_skill_with_thymus(_skill(("x",)), immune=StubImmune(True, "UNSCREENABLE"))
    assert caught.value.code == "TRIGGER_NOT_SCREENABLE"
    stub = StubImmune(False)
    admit_skill_with_thymus(_skill(("  ",)), immune=stub)
    assert stub.calls == [("thymus", "SKILL-GATE-phrase-skill", ("phrase-skill",))]


@pytest.mark.parametrize("bad", [0.5, True, "1/2"])
def test_the_policy_threshold_is_exact(bad: object) -> None:
    """Counterexample: the policy threshold was a float compared with a 1e-9 tolerance."""
    with pytest.raises(TypeError):
        DangerSignalPolicy(allosteric_quorum_threshold=bad)  # type: ignore[arg-type]
    assert DangerSignalPolicy().allosteric_quorum_threshold == Fraction(1, 2)
    with pytest.raises(ValueError):
        DangerSignalPolicy(allosteric_quorum_threshold=1)


def test_the_port_records_refuse_untyped_values() -> None:
    with pytest.raises(ValueError):
        DetectorMatch(epitope="E", matched_text="m", offset=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        HostDangerObservation("K", "SEVERE", 1, "d", "o")
    with pytest.raises(ValueError):
        DetectorIdentity("d", frozenset(), 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        SensorReading("s", 0.5)  # type: ignore[arg-type]


def test_the_oeeis_adapter_checks_independence_on_every_danger_verdict() -> None:
    from operads.infrastructure.immune import OeeisImmuneAdapter

    adapter = OeeisImmuneAdapter(self_panel=["theorem coboundary_nilpotent : d1 * d0 = 0"])
    assert adapter.danger_verdict([MATCH], DANGER, detector=DETECTOR).blocks is True
    assert adapter.danger_verdict([], DANGER, detector=DETECTOR).blocks is False  # one signal
    # A Signal 2 observed by the detector itself, in any letter case, is refused.
    for observer in ("prompt-scanner", "Prompt-Scanner"):
        derived = HostDangerObservation("PROTECTED_FIELD_VIOLATION", "HIGH", 1, "sha256:" + "a" * 64, observer)
        with pytest.raises(ImmuneEvidenceRefusal) as caught:
            adapter.danger_verdict([MATCH], derived, detector=DETECTOR)
        assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
    # The detector's own predicates are refused as Signal 2.
    with pytest.raises(ImmuneEvidenceRefusal) as caught:
        adapter.danger_verdict(
            [MATCH],
            DANGER,
            detector=DetectorIdentity("pharmacy", frozenset({"PROTECTED_FIELD_VIOLATION"}), False),
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
    # The guard reports the refusal code instead of a suppression.
    with pytest.raises(SubstitutionError) as caught_sub:
        immune_guarded_substitute(
            THETA,
            0,
            PHI,
            immune=adapter,
            detector=DetectorIdentity("prompt-scanner", frozenset(), False),
            matches=(MATCH,),
            danger=HostDangerObservation(
                "PROTECTED_FIELD_VIOLATION", "HIGH", 1, "sha256:" + "a" * 64, "PROMPT-SCANNER"
            ),
        )
    assert caught_sub.value.code == "TWO_SIGNAL_COLLAPSE"
    with pytest.raises(TypeError):
        adapter.danger_verdict([MATCH], DANGER)  # type: ignore[call-arg]


def test_the_oeeis_adapter_counts_each_sensor_once() -> None:
    from operads.infrastructure.immune import OeeisImmuneAdapter

    adapter = OeeisImmuneAdapter(self_panel=["clean"])
    assert adapter.quorum_verdict([SensorReading("a", 1), SensorReading("b", 1)]).blocks is False
    assert adapter.quorum_verdict([SensorReading("a", 1)]).blocks is True
    for readings in (
        [SensorReading("a", 1), SensorReading("a", 1)],
        [SensorReading("a", 1), SensorReading("A", 1)],
    ):
        with pytest.raises(ImmuneEvidenceRefusal) as caught:
            adapter.quorum_verdict(readings)
        assert caught.value.code == "DUPLICATE_SENSOR"
    with pytest.raises(ImmuneEvidenceRefusal):
        adapter.quorum_verdict([1, 1])  # type: ignore[list-item]


def test_the_oeeis_adapter_thymus_verdicts() -> None:
    from operads.infrastructure.immune import OeeisImmuneAdapter

    adapter = OeeisImmuneAdapter(self_panel=["theorem coboundary_nilpotent : d1 * d0 = 0"])
    assert adapter.trigger_tolerance_verdict("r", ["d1 * d0"]).decision == "REFUSED"
    assert adapter.trigger_tolerance_verdict("r", ["x" * 300]).decision == "UNSCREENABLE"
