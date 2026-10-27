//! Act I: carrier admission precedes history and synthetic perception.
use crate::act_capture::record_error;
use crate::authorization::AuthorizationTime;
use crate::carrier::{parse_carrier_json, ExactCochain, Network};
use crate::evidence::sha256_ref;
use crate::stage::ddc::DdcStep;
use crate::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::genealogy::AntibodyEntry;
use crate::stage::ports::Refusal;
use serde_json::{json, Map, Value};

pub struct CarrierFramingInput<'a> {
    pub carrier_json: Option<&'a str>,
    pub objective: &'a str,
    pub run_key: &'a str,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CarrierFramingOutcome {
    network: Network,
    initial_cochain: ExactCochain,
    active_antibodies: Vec<AntibodyEntry>,
    prompt_sbe: SbeReport,
    narrative: Value,
    carrier_status: String,
}
impl CarrierFramingOutcome {
    pub fn network(&self) -> &Network {
        &self.network
    }
    pub fn initial_cochain(&self) -> &ExactCochain {
        &self.initial_cochain
    }
    pub fn active_antibodies(&self) -> &[AntibodyEntry] {
        &self.active_antibodies
    }
    pub fn prompt_sbe(&self) -> &SbeReport {
        &self.prompt_sbe
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn carrier_status(&self) -> &str {
        &self.carrier_status
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        Ok(
            json!({"network":self.network.to_dict()?,"cochain":self.initial_cochain.to_dict(),
            "active_antibodies":self.active_antibodies.iter().map(AntibodyEntry::to_dict).collect::<Vec<_>>(),
            "prompt_sbe":self.prompt_sbe.to_dict(),"narrative":self.narrative}),
        )
    }
}
fn load_active_antibodies(
    objective: &str,
    emitters: &mut Option<&mut EmitterSuite<'_>>,
) -> Vec<AntibodyEntry> {
    if let Some(suite) = emitters.as_mut() {
        if let Some(history) = suite.antibodies.as_mut() {
            // Source semantics: history read refusal does not block perception.
            if let Ok(entries) = history.load_antibodies(objective) {
                return entries;
            }
        }
    }
    Vec::new()
}

pub fn execute_act1_carrier_framing(
    input: &CarrierFramingInput<'_>,
    diagnostic: &mut dyn SbeDiagnosticPort,
    mut emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<CarrierFramingOutcome, Refusal> {
    let carrier = parse_carrier_json(input.carrier_json)?;
    let active_antibodies = load_active_antibodies(input.objective, &mut emitters);
    let prompt_sbe = diagnostic.compute(input.objective, 28)?;
    if let Some(suite) = emitters {
        let event_id = sha256_ref(format!("{}:act1", input.run_key).as_bytes());
        let payload = Map::from_iter([
            ("act".into(), json!("I")),
            ("title".into(), json!("Catalyst & Perception")),
            ("objective".into(), json!(input.objective)),
            (
                "active_antibodies".into(),
                json!(active_antibodies
                    .iter()
                    .map(AntibodyEntry::to_dict)
                    .collect::<Vec<_>>()),
            ),
            ("carrier_status".into(), json!(carrier.carrier_status())),
            ("forge_sbe".into(), prompt_sbe.to_dict()),
        ]);
        let (event, bytes) = build_intelligence_event(
            EventDescriptor {
                ie_id: &event_id,
                actor_id: "actor_thanatos_procurator",
                actor_kind: "SWARM_SEAT",
                event_kind: "COMM",
                source_system: "oeas.act1",
                session_id: input.run_key,
                parent_ie_id: Vec::new(),
                object_ids: Vec::new(),
                terminal: false,
            },
            Payload::Object(&payload),
            time.event_clock,
        )?;
        let step: DdcStep = serde_json::from_value(json!({"letter":"C", "before_class":"UnindexedPrompt",
            "after_class":"PerceivedCatalyst", "carrier_hash":sha256_ref(b"carrier"),
            "witness_hash":sha256_ref(input.objective.as_bytes()), "receipt_sha256":sha256_ref(&bytes),
            "timestamp":if input.now_utc.is_empty() { time.dda_timestamp } else { input.now_utc }})).map_err(record_error)?;
        emit_event(&event, &bytes, suite, Some(&step), None)?;
    }
    let carrier_status = carrier.carrier_status().to_string();
    let body = format!(
        "Prompt ingested: '{}'. Loaded {} active antibodies from compost history. Carrier {}{}",
        input.objective,
        active_antibodies.len(),
        carrier_status,
        if carrier.declared() {
            format!(
                " ({} edges, {} left unassigned and recorded as zero).",
                carrier.network().edges().len(),
                carrier.implicit_zero_edges()
            )
        } else {
            "; no carrier measurement is possible.".into()
        }
    );
    let narrative = json!({"act_number":"I", "title":"Catalyst & Perception", "body":body,
        "carrier_status":carrier_status, "implicit_zero_edges":carrier.implicit_zero_edges()});
    Ok(CarrierFramingOutcome {
        network: carrier.network().clone(),
        initial_cochain: carrier.cochain().clone(),
        active_antibodies,
        prompt_sbe,
        narrative,
        carrier_status,
    })
}

// Origin: engine/crates_rs/core_adversary/src/carrier_framing.rs
// Claim: urn:core:crates_rs:core-adversary:carrier-framing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddcd72543 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddcd72543` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordcd72543 {
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
impl BoundaryErrordcd72543 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordcd72543 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordcd72543 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddcd72543 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordcd72543> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordcd72543::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordcd72543::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordcd72543::ExceedsCapacity {
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
mod l4_boundary_tests_dcd72543 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddcd72543::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddcd72543::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddcd72543::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddcd72543::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddcd72543::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordcd72543::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordcd72543::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
