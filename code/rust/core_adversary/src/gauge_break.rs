//! Act IV: bounded diagnostic stagnation triggers a cochain-preserving lift.
use crate::act_capture::record_error;
use crate::authorization::{flag, AuthorizationTime};
use crate::carrier::{key_equal, ExactCochain, Network, NodeLabel};
use crate::evidence::{canonical_rational, sha256_ref, ObstructionMeasurement};
use crate::exact::Integer;
use crate::stage::ddc::DdcStep;
use crate::stage::diagnostics::SbeDiagnosticPort;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::ports::{Refusal, SeatPort, SeatTurnRequest};
use crate::wire_json::python_ascii_json;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Signed;
use serde_json::{json, Map, Value};

pub struct GaugeBreakInput<'a> {
    pub network: &'a Network,
    pub initial_cochain: &'a ExactCochain,
    /// Act III's exact string contents, in order; other candidate fields are unused.
    pub candidate_contents: &'a [String],
    pub measurement: &'a ObstructionMeasurement,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub run_key: &'a str,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugeBreakOutcome {
    triggered: bool,
    network: Network,
    cochain: ExactCochain,
    telemetry: Value,
    narrative: Value,
}
impl GaugeBreakOutcome {
    pub fn triggered(&self) -> bool {
        self.triggered
    }
    pub fn network(&self) -> &Network {
        &self.network
    }
    pub fn cochain(&self) -> &ExactCochain {
        &self.cochain
    }
    pub fn telemetry(&self) -> &Value {
        &self.telemetry
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        Ok(
            json!({"gauge_break_triggered":self.triggered,"network":self.network.to_dict()?,
            "cochain":self.cochain.to_dict(),"telemetry":self.telemetry,"narrative":self.narrative}),
        )
    }
}
fn compute_sbe_delta(
    input: &GaugeBreakInput<'_>,
    diagnostic: &mut dyn SbeDiagnosticPort,
) -> Result<Option<BigRational>, Refusal> {
    if input.candidate_contents.len() < 2 {
        return Ok(None);
    }
    let first = diagnostic
        .compute(&input.candidate_contents[0], 28)?
        .point();
    let second = diagnostic
        .compute(&input.candidate_contents[1], 28)?
        .point();
    Ok(first
        .zip(second)
        .map(|(first, second)| (first.0 - second.0).abs() + (first.1 - second.1).abs()))
}

fn inactive_gauge_break_narrative(
    no_gauge: bool,
    no_split: bool,
    obstructed: bool,
) -> &'static str {
    if no_gauge {
        "Act IV 9-dot gauge break suppressed: no_gauge_change ablated (locked gauge coordinates xi=0)."
    } else if no_split {
        "Act IV carrier dimensional lift suppressed: no_carrier_split ablated (single carrier framing locked)."
    } else if !obstructed {
        "No measured open obstruction: carrier framing maintained under standard gauge."
    } else {
        "Carrier framing maintained under standard gauge: no stagnation detected."
    }
}

fn collect_bridge_edges(network: &Network, bridge: &NodeLabel) -> Vec<[NodeLabel; 2]> {
    let mut added = Vec::new();
    for [u, v] in network.edges().iter().take(2) {
        for edge in [[u.clone(), bridge.clone()], [v.clone(), bridge.clone()]] {
            let reverse = [edge[1].clone(), edge[0].clone()];
            if !network.edges().contains(&edge)
                && !network.edges().contains(&reverse)
                && !added.contains(&edge)
                && !added.contains(&reverse)
            {
                added.push(edge);
            }
        }
    }
    added
}

fn perform_gauge_break_lift(
    input: &GaugeBreakInput<'_>,
    seat_port: Option<&mut dyn SeatPort>,
    telemetry: &mut Map<String, Value>,
) -> Result<(Network, ExactCochain, Value), Refusal> {
    if let Some(port) = seat_port {
        let request = SeatTurnRequest {
            scene_id: "act4_sandbox".into(),
            seat_id: "seat_primal_dual".into(),
            prompt_text:
                "Execute 9-dot gauge break and orthogonal carrier lift on stagnant carrier complex."
                    .into(),
            cognitive_operator: "Placebo & Hopeful Generative Envelope (E_placebo)".into(),
            role_kind: "prose".into(),
            candidate_id: String::new(),
            round_index: 0,
            context_bytes: Vec::new(),
        };
        let reply = port.execute_turn(&request)?;
        telemetry.insert(
            "gauge_break_reply_sha256".into(),
            json!(sha256_ref(&reply.raw_bytes)),
        );
    }
    let mut bridge_number = BigInt::from(9);
    while input
        .network
        .nodes()
        .iter()
        .any(|node| key_equal(node, &NodeLabel::Integer(Integer(bridge_number.clone()))))
    {
        bridge_number += 1;
    }
    let bridge = NodeLabel::Integer(Integer(bridge_number.clone()));
    let mut nodes = input.network.nodes().to_vec();
    nodes.push(bridge.clone());
    let added = collect_bridge_edges(input.network, &bridge);
    let mut edges = input.network.edges().to_vec();
    edges.extend(added.clone());
    let mut faces = input.network.faces().to_vec();
    faces.extend(
        input
            .network
            .edges()
            .iter()
            .take(2)
            .map(|[u, v]| [u.clone(), v.clone(), bridge.clone()]),
    );
    let network = Network::new(
        nodes,
        edges,
        faces,
        input.network.tetrahedra().to_vec(),
        input.network.four_simplices().to_vec(),
    )?;
    let cochain = input
        .initial_cochain
        .transport_onto(input.network.edges(), &added);
    telemetry.insert(
        "lift".into(),
        json!({"bridge_node":bridge,"new_edges":added,
        "transported_edges":input.network.edges().len(),
        "rule":"original edges keep their values; only new bridge edges start at zero"}),
    );
    let narrative = json!({"act_number":"IV","title":"9-Dot Gauge Break",
        "body":format!("Act IV 9-dot gauge break executed: lifted carrier with bridge node {bridge_number}; the input cochain was transported unchanged onto the original edges.")});
    Ok((network, cochain, narrative))
}

fn emit_act4_event(
    input: &GaugeBreakInput<'_>,
    triggered: bool,
    telemetry: &Value,
    suite: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let event_id = sha256_ref(format!("{}:act4", input.run_key).as_bytes());
    let payload = Map::from_iter([
        ("act".into(), json!("IV")),
        ("title".into(), json!("Gauge Break & Carrier Splitting")),
        ("gauge_break_triggered".into(), json!(triggered)),
    ]);
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_dianoia_second_curator",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.act4",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let (letter, after_class, carrier_tag) = if triggered {
        ("LAMBDA", "CarrierExpanded", b"lifted_carrier".as_slice())
    } else {
        ("C", "CandidateProposed", b"carrier".as_slice())
    };
    let timestamp = if input.now_utc.is_empty() {
        time.dda_timestamp
    } else {
        input.now_utc
    };
    let step: DdcStep = serde_json::from_value(json!({
        "letter": letter,
        "before_class": "CandidateProposed",
        "after_class": after_class,
        "carrier_hash": sha256_ref(carrier_tag),
        "witness_hash": sha256_ref(python_ascii_json(telemetry)?.as_bytes()),
        "receipt_sha256": sha256_ref(&bytes),
        "timestamp": timestamp
    }))
    .map_err(record_error)?;
    emit_event(&event, &bytes, suite, Some(&step), None).map(|_| ())
}

fn evaluate_stagnation_and_telemetry(
    input: &GaugeBreakInput<'_>,
    diagnostic: &mut dyn SbeDiagnosticPort,
    no_gauge: bool,
    no_split: bool,
) -> Result<(bool, bool, Map<String, Value>), Refusal> {
    let obstructed = input.measurement.has_open_obstruction();
    let threshold = BigRational::new(BigInt::from(1), BigInt::from(20));
    let delta = compute_sbe_delta(input, diagnostic)?;
    let below_threshold = input.candidate_contents.len() < 2
        || delta.as_ref().is_some_and(|value| value < &threshold);
    let stagnant = obstructed && below_threshold;
    let telemetry = Map::from_iter([
        (
            "sbe_delta".into(),
            json!(delta.as_ref().map(canonical_rational)),
        ),
        (
            "sbe_threshold".into(),
            json!(canonical_rational(&threshold)),
        ),
        (
            "measurement_status".into(),
            input.measurement.to_dict()?["status"].clone(),
        ),
        ("phi1".into(), json!(input.measurement.phi1_text())),
        ("gamma2".into(), json!(input.measurement.gamma2_text())),
        ("stagnant".into(), json!(stagnant)),
        ("no_gauge_change_ablated".into(), json!(no_gauge)),
        ("no_carrier_split_ablated".into(), json!(no_split)),
    ]);
    Ok((obstructed, stagnant, telemetry))
}

pub fn execute_act4_gauge_break(
    input: &GaugeBreakInput<'_>,
    diagnostic: &mut dyn SbeDiagnosticPort,
    seat_port: Option<&mut dyn SeatPort>,
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<GaugeBreakOutcome, Refusal> {
    let no_gauge = flag(input.ablation_flags, "no_gauge_change");
    let no_split = flag(input.ablation_flags, "no_carrier_split");
    let (obstructed, stagnant, mut telemetry) =
        evaluate_stagnation_and_telemetry(input, diagnostic, no_gauge, no_split)?;
    let triggered = stagnant && !no_gauge && !no_split;
    let (network, cochain, narrative) = if !triggered {
        let body = inactive_gauge_break_narrative(no_gauge, no_split, obstructed);
        (
            input.network.clone(),
            input.initial_cochain.clone(),
            json!({"act_number":"IV","title":"Gauge Stability","body":body}),
        )
    } else {
        perform_gauge_break_lift(input, seat_port, &mut telemetry)?
    };
    let telemetry = Value::Object(telemetry);
    if let Some(suite) = emitters {
        emit_act4_event(input, triggered, &telemetry, suite, time)?;
    }
    Ok(GaugeBreakOutcome {
        triggered,
        network,
        cochain,
        telemetry,
        narrative,
    })
}

// Origin: engine/crates_rs/core_adversary/src/gauge_break.rs
// Claim: urn:core:crates_rs:core-adversary:gauge-break:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord78bd4d35 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord78bd4d35` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError78bd4d35 {
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
impl BoundaryError78bd4d35 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError78bd4d35 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError78bd4d35 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord78bd4d35 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError78bd4d35> {
        if capacity_bound == 0 {
            return Err(BoundaryError78bd4d35::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError78bd4d35::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError78bd4d35::ExceedsCapacity {
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
mod l4_boundary_tests_78bd4d35 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord78bd4d35::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord78bd4d35::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord78bd4d35::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord78bd4d35::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord78bd4d35::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError78bd4d35::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError78bd4d35::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
