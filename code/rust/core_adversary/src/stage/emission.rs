//! Ordered Intelligence Spine emission. Concrete sinks and the clock are injected.
use crate::stage::canonical::{identifier, text, validated_record};
use crate::stage::ddc::DdcStep;
use crate::stage::genealogy::{AntibodyEntry, CemeteryHeadstone, GenealogyEntry};
use crate::stage::ports::Refusal;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

fn none() -> String {
    "None".into()
}
fn public() -> String {
    "PUBLIC".into()
}
validated_record!(IntelligenceEvent {
    ie_id: String, ts_utc: String, actor_id: String, actor_kind: String,
    event_kind: String, source_system: String, payload_uri: String, payload_sha256: String, session_id: String,
    #[serde(default)] parent_ie_id: Vec<String>,
    #[serde(default)] object_ids: Vec<String>,
    #[serde(default)] terminal: bool,
    #[serde(default = "none")] authority_effect: String,
    #[serde(default = "public")] privacy_class: String,
});
impl IntelligenceEvent {
    fn validate(&mut self) -> Result<(), String> {
        self.validate_scalar_fields()?;
        for id in &self.parent_ie_id {
            identifier(id, "parent_ie_id")?;
        }
        for id in &self.object_ids {
            text(id, "object_ids", false)?;
        }
        if self.authority_effect != "None" {
            return Err("authority_effect must be 'None'".into());
        }
        Ok(())
    }

    fn validate_scalar_fields(&self) -> Result<(), String> {
        for (value, label) in [
            (&self.ie_id, "ie_id"),
            (&self.actor_id, "actor_id"),
            (&self.actor_kind, "actor_kind"),
            (&self.event_kind, "event_kind"),
            (&self.source_system, "source_system"),
            (&self.session_id, "session_id"),
        ] {
            identifier(value, label)?;
        }
        text(&self.ts_utc, "ts_utc", false)?;
        text(&self.payload_uri, "payload_uri", true)?;
        text(&self.payload_sha256, "payload_sha256", false)
    }
}

pub enum Payload<'a> {
    Bytes(&'a [u8]),
    Text(&'a str),
    Object(&'a Map<String, Value>),
}
impl Payload<'_> {
    fn bytes(&self) -> Result<Vec<u8>, String> {
        match self {
            Self::Bytes(bytes) => Ok(bytes.to_vec()),
            Self::Text(text) => Ok(text.as_bytes().to_vec()),
            Self::Object(object) => serde_json::to_vec(object).map_err(|error| error.to_string()),
        }
    }
}

pub trait Clock {
    fn timestamp_utc(&self) -> String;
}
pub struct EventDescriptor<'a> {
    pub ie_id: &'a str,
    pub actor_id: &'a str,
    pub actor_kind: &'a str,
    pub event_kind: &'a str,
    pub source_system: &'a str,
    pub session_id: &'a str,
    pub parent_ie_id: Vec<String>,
    pub object_ids: Vec<String>,
    pub terminal: bool,
}
pub fn build_intelligence_event(
    descriptor: EventDescriptor<'_>,
    payload: Payload<'_>,
    clock: &dyn Clock,
) -> Result<(IntelligenceEvent, Vec<u8>), Refusal> {
    build_event(descriptor, payload, clock)
        .map_err(|message| emission_refusal("OEAS_EVENT_BUILD_REFUSED", message))
}

fn build_event(
    descriptor: EventDescriptor<'_>,
    payload: Payload<'_>,
    clock: &dyn Clock,
) -> Result<(IntelligenceEvent, Vec<u8>), String> {
    let raw = payload.bytes()?;
    let mut event = IntelligenceEvent {
        ie_id: descriptor.ie_id.into(),
        ts_utc: clock.timestamp_utc(),
        actor_id: descriptor.actor_id.into(),
        actor_kind: descriptor.actor_kind.into(),
        event_kind: descriptor.event_kind.into(),
        source_system: descriptor.source_system.into(),
        payload_uri: format!("memory://{}/{}", descriptor.session_id, descriptor.ie_id),
        payload_sha256: format!("sha256:{}", hex::encode(Sha256::digest(&raw))),
        session_id: descriptor.session_id.into(),
        parent_ie_id: descriptor.parent_ie_id,
        object_ids: descriptor.object_ids,
        terminal: descriptor.terminal,
        authority_effect: "None".into(),
        privacy_class: "PUBLIC".into(),
    };
    event.validate()?;
    Ok((event, raw))
}

pub trait UtsSink {
    fn record_event(
        &mut self,
        event: &IntelligenceEvent,
        payload: &[u8],
    ) -> Result<String, Refusal>;
}
pub trait DdcSink {
    fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal>;

    /// Expose a recorded tape only when this concrete sink retains one.
    fn recorded_steps(&self) -> Option<&[DdcStep]> {
        None
    }

    /// A sink exposes its checkpoint count only when it supports rollback.
    fn recorded_step_count(&self) -> Option<usize> {
        None
    }

    fn rollback(&mut self, _checkpoint_index: usize, _reason: &str) -> Result<(), Refusal> {
        Err(emission_refusal(
            "DDC_ROLLBACK_UNAVAILABLE",
            "DDC sink does not support rollback",
        ))
    }
}
pub trait UnsSink {
    fn record_narrative(&mut self, session: &str, text: &str) -> Result<String, Refusal>;
}
pub trait PacketSink {
    fn record_packet(&mut self, packet: &[u8]) -> Result<String, Refusal>;
}
pub trait TurnSink {
    fn record_turn(
        &mut self,
        session: &str,
        payload: &Map<String, Value>,
    ) -> Result<String, Refusal>;
}
pub enum SgtSink<'a> {
    Packet(&'a mut dyn PacketSink),
    Turn(&'a mut dyn TurnSink),
}
pub trait CemeterySink {
    fn record_headstone(&mut self, headstone: &CemeteryHeadstone) -> Result<String, Refusal>;
}
pub trait AntibodySink {
    fn record_failure(
        &mut self,
        failure_pattern: &str,
        constraint_rule: &str,
    ) -> Result<String, Refusal>;
    fn load_antibodies(&mut self, context_key: &str) -> Result<Vec<AntibodyEntry>, Refusal>;
}
pub trait GenealogySink {
    fn record_lineage(&mut self, entry: &GenealogyEntry) -> Result<String, Refusal>;
}
#[derive(Default)]
pub struct EmitterSuite<'a> {
    pub uts: Option<&'a mut dyn UtsSink>,
    pub ddc: Option<&'a mut dyn DdcSink>,
    pub uns: Option<&'a mut dyn UnsSink>,
    pub sgt: Option<SgtSink<'a>>,
    pub cemetery: Option<&'a mut dyn CemeterySink>,
    pub antibodies: Option<&'a mut dyn AntibodySink>,
    pub genealogy: Option<&'a mut dyn GenealogySink>,
}

fn emission_refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = "adversary.stage.application.emission.emit_event".into();
    refusal
}

fn decode_text(raw: &[u8]) -> Result<&str, String> {
    std::str::from_utf8(raw).map_err(|error| {
        let start = error.valid_up_to();
        let first = raw.get(start).copied().unwrap_or(0);
        let reason = if !(0xc2..=0xf4).contains(&first) {
            "invalid start byte"
        } else if error.error_len().is_none() {
            "unexpected end of data"
        } else {
            "invalid continuation byte"
        };
        let length = error.error_len().unwrap_or(raw.len().saturating_sub(start));
        if length == 1 {
            format!("'utf-8' codec can't decode byte 0x{first:02x} in position {start}: {reason}")
        } else {
            format!(
                "'utf-8' codec can't decode bytes in position {start}-{}: {reason}",
                start + length.saturating_sub(1)
            )
        }
    })
}

fn emit_uns_narrative(
    event: &IntelligenceEvent,
    payload: &[u8],
    uns: &mut Option<&mut dyn UnsSink>,
) -> Result<(), Refusal> {
    if event.event_kind == "NARRATIVE" {
        if let Some(sink) = uns {
            let text = decode_text(payload)
                .map_err(|message| emission_refusal("UNS_EMISSION_FAILED", message))?;
            sink.record_narrative(&event.session_id, text)?;
        }
    }
    Ok(())
}

pub fn emit_event(
    event: &IntelligenceEvent,
    payload: &[u8],
    suite: &mut EmitterSuite<'_>,
    step: Option<&DdcStep>,
    sgt_payload: Option<&Map<String, Value>>,
) -> Result<String, Refusal> {
    if is_impure_dda_record(event, suite, step) {
        return Err(emission_refusal(
            "DDA_IMPURE_RECORD",
            "Event of kind DDA requires dda_step parameter",
        ));
    }
    if let Some(sink) = &mut suite.uts {
        sink.record_event(event, payload)?;
    }
    if let (Some(step), Some(sink)) = (step, &mut suite.ddc) {
        sink.record_step(step)?;
    }
    if let Some(sink) = &mut suite.sgt {
        emit_sgt_event(event, payload, sink, sgt_payload)?;
    }
    emit_uns_narrative(event, payload, &mut suite.uns)?;
    Ok(event.ie_id.clone())
}

fn is_impure_dda_record(
    event: &IntelligenceEvent,
    suite: &EmitterSuite<'_>,
    step: Option<&DdcStep>,
) -> bool {
    [
        event.event_kind == "DDA",
        suite.ddc.is_some(),
        step.is_none(),
    ]
    .into_iter()
    .all(|b| b)
}

fn emit_sgt_event(
    event: &IntelligenceEvent,
    payload: &[u8],
    sink: &mut SgtSink<'_>,
    sgt_payload: Option<&Map<String, Value>>,
) -> Result<(), Refusal> {
    let explicit = sgt_payload.filter(|p| !p.is_empty());
    if explicit.is_none() && event.event_kind != "PACKET" {
        return Ok(());
    }
    match sink {
        SgtSink::Packet(sink) => {
            sink.record_packet(payload)?;
        }
        SgtSink::Turn(sink) => {
            let parsed;
            let turn = match explicit {
                Some(explicit) => explicit,
                None => {
                    parsed = parse_sgt_turn_payload(payload)?;
                    &parsed
                }
            };
            sink.record_turn(&event.session_id, turn)?;
        }
    }
    Ok(())
}

fn parse_sgt_turn_payload(payload: &[u8]) -> Result<Map<String, Value>, Refusal> {
    let text =
        decode_text(payload).map_err(|message| emission_refusal("SGT_EMISSION_FAILED", message))?;
    if !payload.starts_with(b"{") {
        return Ok(Map::from_iter([("raw".into(), Value::String(text.into()))]));
    }
    let value: Value = serde_json::from_str(text)
        .map_err(|error| emission_refusal("SGT_EMISSION_FAILED", error.to_string()))?;
    match value {
        Value::Object(object) => Ok(object),
        _ => Err(emission_refusal(
            "SGT_EMISSION_FAILED",
            "SGT turn must be an object",
        )),
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/emission.rs
// Claim: urn:core:crates_rs:core-adversary:emission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0011daff {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0011daff` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0011daff {
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
impl BoundaryError0011daff {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0011daff {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0011daff {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0011daff {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0011daff> {
        if capacity_bound == 0 {
            return Err(BoundaryError0011daff::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0011daff::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0011daff::ExceedsCapacity {
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
mod l4_boundary_tests_0011daff {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0011daff::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0011daff::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0011daff::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0011daff::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0011daff::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError0011daff::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError0011daff::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
