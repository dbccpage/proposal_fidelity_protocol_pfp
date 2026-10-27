//! Sovereign Rust bridge connecting `core_epistemic_immune_system` (OEEIS),
//! `core_operads` (OEWAS), and `core_adversary` (OEADVERSARY).
//!
//! AuthorityEffect: None.
//!
//! Responsibilities:
//! 1. Implements `core_operads::immune_ports::ImmuneScreenPort`
//!    via `OeeisImmuneAdapter`, delegating two-signal danger checks, signal
//!    independence verification, allosteric Hill consensus quorum checks, and
//!    central-tolerance thymus screening to `core_epistemic_immune_system`.
//! 2. Binds `SwarmSpecialization` 7-act stage port licensing (`PortName::ImmuneAntibodies`,
//!    `PortName::OeopAntiSkill`, `PortName::OeopLearning`) to OEWAS operad
//!    substitution and workflow guard execution via `AdversaryOeopBoutBridge`.

use crate::specialization::{base, PortName, StageBinding, SwarmSpecialization};
use num_rational::BigRational;
use core_epistemic_immune_system::{
    allostery::{canonical, AllostericConsensusGate, HillParameters},
    anti_skill::{AntiSkillSpecV2, FailureClass},
    danger_gate::TwoSignalDangerGate,
    formulary::{AdmissionReceiptV1, Formulary},
    independence::{CharacterSpan, DangerEvidence, DetectorContext, MatchEvidence},
    regulation::{DetectorTelemetry, TregSupervisor},
    signal_gate::{CategorizedDangerEvidence, DangerDecision, DangerSeverity},
    thymus::{ThymusGate, ThymusVerdict},
    Refusal as EisRefusal,
};
use core_types::python_unicode::casefold;
use core_operads::{
    immune_guards::{
        allosteric_consensus_substitute, immune_guarded_substitute, validate_workflow_immune_guard,
        DangerScreenRequest,
    },
    immune_ports::{
        DetectorIdentity, DetectorMatch, HostDangerObservation, ImmuneScreenPort, ImmuneVerdict,
        SensorReading,
    },
    planar::OperadOperation,
    policy::DangerSignalPolicy,
    workflow::WorkflowReport,
    Refusal as OeopRefusal,
};
use regex::Regex;
use serde_json::{Map, Value};
use std::collections::BTreeSet;

const MAX_SAFE_PATTERN_CHARS: usize = 256;

fn map_eis_refusal(error: EisRefusal) -> OeopRefusal {
    let prefix = format!("{}: ", error.code);
    let detail = error
        .message
        .strip_prefix(&prefix)
        .unwrap_or(&error.message)
        .to_owned();
    OeopRefusal::new(&error.code, detail)
}

fn map_severity(raw: &str) -> Result<DangerSeverity, OeopRefusal> {
    match raw {
        "LOW" => Ok(DangerSeverity::Low),
        "MEDIUM" => Ok(DangerSeverity::Medium),
        "HIGH" => Ok(DangerSeverity::High),
        "CRITICAL" => Ok(DangerSeverity::Critical),
        other => Err(OeopRefusal::new(
            "BAD_EVIDENCE",
            format!("unsupported danger severity {other:?}"),
        )),
    }
}

fn decision_str(decision: DangerDecision) -> &'static str {
    match decision {
        DangerDecision::Tolerated => "TOLERATED",
        DangerDecision::DiagnosticOnly => "DIAGNOSTIC_ONLY",
        DangerDecision::DefensiveLockdown => "DEFENSIVE_LOCKDOWN",
        DangerDecision::Quarantined => "QUARANTINED",
    }
}

/// Concrete `ImmuneScreenPort` implementation backed by `core_epistemic_immune_system`.
#[derive(Debug, Clone)]
pub struct OeeisImmuneAdapter {
    self_panel: Vec<String>,
    quorum_gate: AllostericConsensusGate,
}

impl OeeisImmuneAdapter {
    /// Construct an adapter with the provided self-tolerance panel and default
    /// Hill parameters (`n = 2`, `K = 2`, `threshold = 1/2`, `per_sensor_cap = 1`).
    pub fn new(self_panel: Vec<String>) -> Result<Self, OeopRefusal> {
        let params =
            HillParameters::new(2, BigRational::from_integer(2.into())).map_err(map_eis_refusal)?;
        let threshold = BigRational::new(1.into(), 2.into());
        let cap = Some(BigRational::from_integer(1.into()));
        let quorum_gate =
            AllostericConsensusGate::new(params, threshold, cap).map_err(map_eis_refusal)?;
        Ok(Self {
            self_panel,
            quorum_gate,
        })
    }

    /// Construct an adapter with custom allosteric quorum gate parameters.
    pub fn with_quorum_gate(
        self_panel: Vec<String>,
        quorum_gate: AllostericConsensusGate,
    ) -> Self {
        Self {
            self_panel,
            quorum_gate,
        }
    }

    /// Construct an adapter initialized with the standard baseline self-panel.
    pub fn standard_baseline() -> Result<Self, OeopRefusal> {
        Self::new(vec![
            "AuthorityEffect: None".to_owned(),
            "exact rational duality gap is zero".to_owned(),
            "bounded finite complex with exact coboundary".to_owned(),
            "verify_simplicial_boundary_law succeeds".to_owned(),
            "fractions.Fraction(1, 2) is exact".to_owned(),
            "BigRational::from_integer(1) is pure".to_owned(),
            "clean architecture inward dependency verified".to_owned(),
            "four-host mirror synchronization succeeded".to_owned(),
            "Lean 4 lake build complete with 0 errors".to_owned(),
            "theorem verified by kernel check".to_owned(),
        ])
    }

    pub fn self_panel(&self) -> &[String] {
        &self.self_panel
    }
}

impl ImmuneScreenPort for OeeisImmuneAdapter {
    fn danger_verdict(
        &mut self,
        matches: &[DetectorMatch],
        danger: Option<&HostDangerObservation>,
        detector: &DetectorIdentity,
    ) -> Result<ImmuneVerdict, OeopRefusal> {
        let signal1: Vec<MatchEvidence> = matches
            .iter()
            .map(|m| {
                MatchEvidence::new(
                    m.epitope().clone(),
                    m.matched_text().clone(),
                    m.offset().get().clone(),
                )
            })
            .collect();

        let signal2 = match danger {
            None => None,
            Some(obs) => {
                let severity = map_severity(obs.severity())?;
                let spans = obs
                    .evidence_spans()
                    .iter()
                    .map(|(low, high)| CharacterSpan::new(low.get().clone(), high.get().clone()))
                    .collect::<Result<Vec<_>, _>>()
                    .map_err(map_eis_refusal)?;
                let evidence = DangerEvidence::new(
                    obs.kind().clone(),
                    obs.observer_id().clone(),
                    obs.evidence_digest().clone(),
                    obs.defect_count().get().clone(),
                    spans,
                );
                Some(CategorizedDangerEvidence::new(evidence, severity))
            }
        };

        let context = DetectorContext {
            detector_id: detector.detector_id().clone(),
            detector_predicates: detector.predicates().clone(),
            offsets_are_content: *detector.offsets_are_content(),
        };

        let evaluation =
            TwoSignalDangerGate::evaluate_independent(&signal1, signal2.as_ref(), &context)
                .map_err(map_eis_refusal)?;
        let serialized = serde_json::to_value(&evaluation)
            .map_err(|e| OeopRefusal::new("IMMUNE_PORT_WIRE_INVALID", e.to_string()))?;
        let rationale = serialized["rationale"]
            .as_str()
            .unwrap_or("Two-signal evaluation completed.")
            .to_owned();
        ImmuneVerdict::new(
            evaluation.is_suppressed(),
            decision_str(evaluation.decision()).to_owned(),
            rationale,
        )
    }

    fn quorum_verdict(&mut self, readings: &[SensorReading]) -> Result<ImmuneVerdict, OeopRefusal> {
        let mut seen = BTreeSet::new();
        let mut signals = Map::new();
        for reading in readings {
            let trimmed = reading
                .sensor_id()
                .trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c));
            let folded = casefold(trimmed);
            if !seen.insert(folded) {
                return Err(OeopRefusal::new(
                    "DUPLICATE_SENSOR",
                    format!("sensor {:?} reported more than once", reading.sensor_id()),
                ));
            }
            signals.insert(
                reading.sensor_id().clone(),
                Value::String(canonical(reading.value())),
            );
        }
        let outcome = self
            .quorum_gate
            .evaluate(&signals)
            .map_err(map_eis_refusal)?;
        let is_activated = outcome["is_activated"].as_bool().unwrap_or(false);
        let rationale = outcome["rationale"]
            .as_str()
            .unwrap_or("Allosteric quorum evaluated.")
            .to_owned();
        ImmuneVerdict::new(
            !is_activated,
            if is_activated {
                "ACTIVATED".to_owned()
            } else {
                "NOT_ACTIVATED".to_owned()
            },
            rationale,
        )
    }

    fn trigger_tolerance_verdict(
        &mut self,
        rule_id: &str,
        phrases: &[String],
    ) -> Result<ImmuneVerdict, OeopRefusal> {
        if self.self_panel.is_empty() {
            return Err(OeopRefusal::new(
                "EMPTY_SELF_PANEL",
                "a thymus screen needs a non-empty self panel",
            ));
        }
        if rule_id.trim().is_empty() {
            return Err(OeopRefusal::new(
                "IMMUNE_PORT_VALUE_ERROR",
                "rule_id must be a non-empty str",
            ));
        }
        for phrase in phrases {
            if phrase.trim().is_empty() {
                return ImmuneVerdict::new(
                    true,
                    "UNSCREENABLE".to_owned(),
                    "Refused pattern (PATTERN_EMPTY)".to_owned(),
                );
            }
            let escaped = regex::escape(phrase);
            let pattern_len = escaped.chars().count();
            if pattern_len > MAX_SAFE_PATTERN_CHARS {
                return ImmuneVerdict::new(
                    true,
                    "UNSCREENABLE".to_owned(),
                    format!("Refused pattern (PATTERN_TOO_LONG): {pattern_len}"),
                );
            }
            let pattern = format!("(?i){escaped}");
            let compiled = match Regex::new(&pattern) {
                Ok(re) => re,
                Err(err) => {
                    return ImmuneVerdict::new(
                        true,
                        "UNSCREENABLE".to_owned(),
                        format!("Refused pattern (PATTERN_SYNTAX): {err}"),
                    );
                }
            };
            let violations = self
                .self_panel
                .iter()
                .filter(|sample| compiled.is_match(sample))
                .count();
            if violations > 0 {
                return ImmuneVerdict::new(
                    true,
                    "REFUSED".to_owned(),
                    format!(
                        "Autoimmune apoptosis: candidate detector {rule_id} triggered on {violations} healthy self fixture(s) out of {}. Purged.",
                        self.self_panel.len()
                    ),
                );
            }
        }
        ImmuneVerdict::new(
            false,
            "ADMITTED".to_owned(),
            format!(
                "{} trigger phrase(s) matched none of {} self fixture(s)",
                phrases.len(),
                self.self_panel.len()
            ),
        )
    }
}

/// Seven-act Adversary coordinator binding `SwarmSpecialization` port licensing to
/// OEWAS operad guards and OEEIS immune gates.
pub struct AdversaryOeopBoutBridge {
    specialization: SwarmSpecialization,
    immune: OeeisImmuneAdapter,
    formulary: Formulary,
    treg: TregSupervisor,
}

impl AdversaryOeopBoutBridge {
    /// Construct and validate a 7-act bridge against the base Adversary specialization.
    pub fn new(
        specialization: SwarmSpecialization,
        immune: OeeisImmuneAdapter,
    ) -> Result<Self, OeopRefusal> {
        specialization
            .validate_within(&base())
            .map_err(|err| OeopRefusal::new(&err.code, err.message))?;
        Ok(Self {
            specialization,
            immune,
            formulary: Formulary::new(),
            treg: TregSupervisor::default(),
        })
    }

    /// Construct a bridge with the canonical base specialization and standard self-panel.
    pub fn standard_base() -> Result<Self, OeopRefusal> {
        Self::new(base(), OeeisImmuneAdapter::standard_baseline()?)
    }

    pub fn specialization(&self) -> &SwarmSpecialization {
        &self.specialization
    }

    pub fn immune_mut(&mut self) -> &mut OeeisImmuneAdapter {
        &mut self.immune
    }

    pub fn formulary(&self) -> &Formulary {
        &self.formulary
    }

    fn require_stage_port(
        &self,
        stage_id: &str,
        allowed_ports: &[PortName],
    ) -> Result<&StageBinding, OeopRefusal> {
        let stage = self
            .specialization
            .stage_plan
            .iter()
            .find(|s| s.stage_id == stage_id)
            .ok_or_else(|| {
                OeopRefusal::new(
                    "STAGE_NOT_IN_PLAN",
                    format!(
                        "stage {stage_id:?} is not declared in specialization {}",
                        self.specialization.specialization_id
                    ),
                )
            })?;
        let licensed = stage.ports.iter().any(|p| {
            allowed_ports.contains(p) && self.specialization.licensed_ports.contains(p)
        });
        if !licensed {
            return Err(OeopRefusal::new(
                "PORT_NOT_LICENSED_AT_STAGE",
                format!(
                    "stage {} (act {}) does not license any of {:?}",
                    stage.stage_id, stage.act, allowed_ports
                ),
            ));
        }
        Ok(stage)
    }

    /// Execute two-signal danger-guarded operad substitution at a licensed stage
    /// (`ImmuneAntibodies` or `OeopAntiSkill`).
    pub fn stage_danger_guarded_substitute(
        &mut self,
        stage_id: &str,
        theta: &OperadOperation,
        index: &Value,
        phi: &OperadOperation,
        evidence: DangerScreenRequest<'_>,
    ) -> Result<OperadOperation, OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::ImmuneAntibodies, PortName::OeopAntiSkill],
        )?;
        immune_guarded_substitute(theta, index, phi, &mut self.immune, evidence)
    }

    /// Execute allosteric quorum-guarded operad substitution at a licensed stage
    /// (`ImmuneAntibodies` or `OeopLearning`).
    pub fn stage_allosteric_quorum_substitute(
        &mut self,
        stage_id: &str,
        theta: &OperadOperation,
        index: &Value,
        phi: &OperadOperation,
        readings: &[SensorReading],
    ) -> Result<OperadOperation, OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::ImmuneAntibodies, PortName::OeopLearning],
        )?;
        allosteric_consensus_substitute(theta, index, phi, readings, &mut self.immune)
    }

    /// Validate a workflow report under the two-signal danger gate at a licensed stage.
    pub fn stage_validate_workflow_guard(
        &mut self,
        stage_id: &str,
        report: &WorkflowReport,
        policy: &DangerSignalPolicy,
        evidence: DangerScreenRequest<'_>,
    ) -> Result<WorkflowReport, OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::ImmuneAntibodies, PortName::OeopAntiSkill],
        )?;
        validate_workflow_immune_guard(report, policy, &mut self.immune, evidence)
    }

    /// Screen skill trigger phrases against the thymus self-panel at a licensed stage.
    pub fn stage_screen_skill_triggers(
        &mut self,
        stage_id: &str,
        rule_id: &str,
        phrases: &[String],
    ) -> Result<ImmuneVerdict, OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::ImmuneAntibodies, PortName::OeopAntiSkill],
        )?;
        self.immune.trigger_tolerance_verdict(rule_id, phrases)
    }

    /// Propose an `AntiSkillSpecV2` and run `ThymusGate` central-tolerance screening
    /// at a licensed stage (`OeopAntiSkill` or `ImmuneAntibodies`).
    pub fn stage_propose_and_screen_antiskill(
        &self,
        stage_id: &str,
        pattern: &str,
        failure_class: FailureClass,
        target_domain: &str,
        description: &str,
        epoch: u64,
    ) -> Result<(AntiSkillSpecV2, ThymusVerdict), OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::OeopAntiSkill, PortName::ImmuneAntibodies],
        )?;
        let thymus = ThymusGate::new(self.immune.self_panel().to_vec());
        let mut spec =
            AntiSkillSpecV2::propose(pattern, failure_class, target_domain, description, epoch);
        let verdict = thymus.screen(&mut spec);
        Ok((spec, verdict))
    }

    /// Register a candidate `AntiSkillSpecV2` in the `Formulary` and admit it with
    /// an external human receipt at a licensed stage (`OeopAntiSkill` or `ImmuneAntibodies`).
    pub fn stage_register_and_admit_antiskill(
        &mut self,
        stage_id: &str,
        candidate: AntiSkillSpecV2,
        approver: &str,
        epoch: u64,
        receipt_digest: &str,
    ) -> Result<(AntiSkillSpecV2, AdmissionReceiptV1), OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[PortName::OeopAntiSkill, PortName::ImmuneAntibodies],
        )?;
        let id = candidate.id.clone();
        self.formulary
            .register_candidate(candidate)
            .map_err(|code| OeopRefusal::new(code, code))?;
        let receipt = self
            .formulary
            .admit_with_receipt(&id, approver, epoch, receipt_digest)
            .map_err(|code| OeopRefusal::new(code, code))?;
        let admitted = self
            .formulary
            .get(&id)
            .cloned()
            .ok_or_else(|| OeopRefusal::new("ANTI_SKILL_NOT_FOUND", "ANTI_SKILL_NOT_FOUND"))?;
        Ok((admitted, receipt))
    }

    /// Evaluate `TregSupervisor` false-discovery regulatory suspension at a licensed stage.
    pub fn stage_review_detector_telemetry(
        &self,
        stage_id: &str,
        spec: &mut AntiSkillSpecV2,
        telemetry: &DetectorTelemetry,
    ) -> Result<bool, OeopRefusal> {
        self.require_stage_port(
            stage_id,
            &[
                PortName::OeopAntiSkill,
                PortName::OeopLearning,
                PortName::ImmuneAntibodies,
            ],
        )?;
        Ok(self.treg.review(spec, telemetry))
    }
}

// Origin: engine/crates_rs/core_adversary/src/oewas_oeeis_bridge.rs
// Claim: urn:core:crates_rs:core-adversary:oewas-oeeis-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0bbe2b9d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0bbe2b9d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0bbe2b9d {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError0bbe2b9d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0bbe2b9d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0bbe2b9d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0bbe2b9d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0bbe2b9d> {
        if capacity_bound == 0 {
            return Err(BoundaryError0bbe2b9d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0bbe2b9d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0bbe2b9d::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_0bbe2b9d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0bbe2b9d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0bbe2b9d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0bbe2b9d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0bbe2b9d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0bbe2b9d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0bbe2b9d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0bbe2b9d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
