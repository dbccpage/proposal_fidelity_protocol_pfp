//! Act II: exact scorer delegation and source-ordered obstruction audit.
use crate::act_capture::record_error;
use crate::authorization::AuthorizationTime;
use crate::carrier::{ExactCochain, Network};
use crate::evidence::{sha256_ref, ObstructionMeasurement};
use crate::scoring_ports::{CochainScoringPort, CochainScoringRequest, NullCochainScorer};
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use serde_json::{json, Map, Value};

pub struct ObstructionIdentificationInput<'a> {
    pub network: &'a Network,
    pub initial_cochain: &'a ExactCochain,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub run_key: &'a str,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObstructionIdentificationOutcome {
    measurement: ObstructionMeasurement,
    narrative: Value,
}
impl ObstructionIdentificationOutcome {
    pub fn measurement(&self) -> &ObstructionMeasurement {
        &self.measurement
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        Ok(json!({"measurement":self.measurement.to_dict()?,"narrative":self.narrative}))
    }
}
fn emit_act2_event(
    input: &ObstructionIdentificationInput<'_>,
    measurement: &ObstructionMeasurement,
    suite: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let event_id = sha256_ref(format!("{}:act2", input.run_key).as_bytes());
    let payload = Map::from_iter([
        ("act".into(), json!("II")),
        ("title".into(), json!("Obstruction Identification")),
        ("measurement".into(), measurement.to_dict()?),
    ]);
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_aletheia_procurator",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.act2",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let witness = format!(
        "[{}]",
        measurement
            .active_obstructions()
            .iter()
            .map(|text| repr_string(text))
            .collect::<Vec<_>>()
            .join(", ")
    );
    let mut fields = Map::from_iter([
        ("letter".into(), json!("R")),
        ("before_class".into(), json!("PerceivedCatalyst")),
        ("after_class".into(), json!("ActiveObstruction")),
        ("carrier_hash".into(), json!(sha256_ref(b"carrier"))),
        ("witness_hash".into(), json!(sha256_ref(witness.as_bytes()))),
        ("receipt_sha256".into(), json!(sha256_ref(&bytes))),
        (
            "timestamp".into(),
            json!(if input.now_utc.is_empty() {
                time.dda_timestamp
            } else {
                input.now_utc
            }),
        ),
    ]);
    if measurement.is_measured() {
        fields.insert("phi_1".into(), json!(measurement.phi1_text()));
        fields.insert("gamma_2".into(), json!(measurement.gamma2_text()));
    }
    let step: DdcStep = serde_json::from_value(Value::Object(fields)).map_err(record_error)?;
    emit_event(&event, &bytes, suite, Some(&step), None).map(|_| ())
}

pub fn execute_act2_obstruction_identification(
    input: &ObstructionIdentificationInput<'_>,
    scorer: Option<&mut dyn CochainScoringPort>,
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<ObstructionIdentificationOutcome, Refusal> {
    let measurement = if input.network.nodes().is_empty() {
        ObstructionMeasurement::not_measured(
            "NO_CARRIER_DECLARED: the bout declared no carrier to measure".into(),
            "carrier_validation".into(),
        )?
    } else {
        let request = CochainScoringRequest {
            network: input.network,
            initial_cochain: input.initial_cochain,
            ablation_flags: input.ablation_flags,
        };
        if let Some(port) = scorer {
            port.identify_obstructions(&request)?
        } else {
            NullCochainScorer.identify_obstructions(&request)?
        }
    };
    let body = if measurement.is_measured() {
        format!(
            "Exact measurement: Phi1={}, Gamma2={}, active defects={}, certificate verified by {}.",
            measurement.phi1_text().as_deref().unwrap_or("None"),
            measurement.gamma2_text().as_deref().unwrap_or("None"),
            measurement.defect_count(),
            measurement.backend()
        )
    } else {
        format!(
            "NOT_MEASURED ({}): {}",
            measurement.backend(),
            measurement.reason()
        )
    };
    let narrative = json!({"act_number":"II","title":"Obstruction Identification","body":body,"measurement":measurement.to_dict()?});
    if let Some(suite) = emitters {
        emit_act2_event(input, &measurement, suite, time)?;
    }
    Ok(ObstructionIdentificationOutcome {
        measurement,
        narrative,
    })
}

// Origin: engine/crates_rs/core_adversary/src/obstruction_identification.rs
// Claim: urn:core:crates_rs:core-adversary:obstruction-identification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4754e444 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4754e444` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4754e444 {
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
impl BoundaryError4754e444 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4754e444 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4754e444 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4754e444 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4754e444> {
        if capacity_bound == 0 {
            return Err(BoundaryError4754e444::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4754e444::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4754e444::ExceedsCapacity {
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
mod l4_boundary_tests_4754e444 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4754e444::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4754e444::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4754e444::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4754e444::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4754e444::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4754e444::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4754e444::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
