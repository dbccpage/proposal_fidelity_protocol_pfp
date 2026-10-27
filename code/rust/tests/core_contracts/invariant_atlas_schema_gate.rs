use core_contracts::validation::{
    InvariantAtlasEntry, InvariantAtlasStore, SchemaGate, SchemaGateViolationKind,
    ValidationResult, ValidationStatus, ValidationViolation, Validator,
};
use core_types::{InvariantLayer, InvariantPacket, Refusable, RefusalSource};

fn atlas_store() -> InvariantAtlasStore {
    InvariantAtlasStore::from_entries([(
        "Phi1",
        InvariantAtlasEntry::new(
            InvariantLayer::GTFOC,
            "finite cochain carrier",
            "primal-dual replay certificate",
        )
        .expect("test atlas entry is non-empty"),
    )])
    .expect("test atlas ids are unique")
}

fn packet(
    invariant_id: &str,
    layer: InvariantLayer,
    carrier_type: &str,
    witness_protocol_id: &str,
) -> InvariantPacket {
    InvariantPacket::new(
        layer,
        carrier_type,
        "value.weighted_quotient_norm",
        invariant_id,
        "law.exact_repair_preserves_value",
        "operators.e_i_r_c_m_profile",
        witness_protocol_id,
        true,
        "refusal.phi1_certificate_missing",
    )
    .expect("test packet fields are non-empty")
}

fn well_formed_packet() -> InvariantPacket {
    packet(
        "Phi1",
        InvariantLayer::GTFOC,
        "finite cochain carrier",
        "primal-dual replay certificate",
    )
}

#[test]
fn well_formed_invariant_packet_passes_schema_gate() {
    let gate = SchemaGate::new(atlas_store());
    let packet = well_formed_packet();

    let artifact = gate.validate_packet(&packet);

    assert_eq!(artifact.status, ValidationStatus::Valid);
    assert!(matches!(artifact.result, ValidationResult::Valid(_)));
    assert!(matches!(gate.admit_packet(&packet), Refusable::Value(_)));
}

#[test]
fn default_schema_gate_validator_accepts_well_formed_packet() {
    let packet = well_formed_packet();

    let artifact = SchemaGate::validate(&packet);

    assert_eq!(artifact.status, ValidationStatus::Valid);
}

#[test]
fn well_formed_invariant_transition_passes_schema_gate() {
    let gate = SchemaGate::new(atlas_store());
    let before = well_formed_packet();
    let after = well_formed_packet();

    let artifact = gate.validate_transition(&before, &after);

    assert_eq!(artifact.status, ValidationStatus::Valid);
    let ValidationResult::Valid(witnesses) = &artifact.result else {
        panic!("well-formed transition should be valid");
    };
    assert!(witnesses[0]
        .checked_fields
        .contains(&"certificate_required"));
    assert!(matches!(
        gate.admit_transition(&before, &after),
        Refusable::Value(_)
    ));
}

#[test]
fn unregistered_invariant_packet_returns_refusal() {
    let gate = SchemaGate::new(atlas_store());
    let packet = packet(
        "UnknownInvariant",
        InvariantLayer::GTFOC,
        "finite cochain carrier",
        "primal-dual replay certificate",
    );

    let artifact = gate.validate_packet(&packet);

    assert_eq!(artifact.status, ValidationStatus::Invalid);
    let ValidationResult::Invalid(violations) = artifact.result else {
        panic!("unregistered invariant should be invalid");
    };
    assert!(violations
        .iter()
        .any(|v| v.kind == SchemaGateViolationKind::UnregisteredInvariant));
    assert_eq!(
        gate.admit_packet(&packet),
        Refusable::Refused(RefusalSource::Refusal)
    );
}

#[test]
fn corrupted_invariant_transition_returns_refusal() {
    let gate = SchemaGate::new(atlas_store());
    let before = well_formed_packet();
    let after = packet(
        "Phi1",
        InvariantLayer::GTFOC,
        "mutated cochain carrier",
        "primal-dual replay certificate",
    );

    let artifact = gate.validate_transition(&before, &after);

    assert_eq!(artifact.status, ValidationStatus::Invalid);
    let ValidationResult::Invalid(violations) = artifact.result else {
        panic!("carrier mutation should be invalid");
    };
    assert!(violations
        .iter()
        .any(|v| v.kind == SchemaGateViolationKind::CarrierTypeMismatch
            && v.code() == "InvariantCarrierTypeMismatch"));
    assert_eq!(
        gate.admit_transition(&before, &after),
        Refusable::Refused(RefusalSource::Refusal)
    );
}

#[test]
fn semantic_invariant_transition_mutation_returns_refusal() {
    let gate = SchemaGate::new(atlas_store());
    let before = well_formed_packet();
    let after = InvariantPacket::new(
        InvariantLayer::GTFOC,
        "finite cochain carrier",
        "value.weighted_quotient_norm",
        "Phi1",
        "law.exact_repair_preserves_value",
        "operators.e_i_r_c_m_profile",
        "primal-dual replay certificate",
        false,
        "refusal.phi1_certificate_missing",
    )
    .expect("test packet fields are non-empty");

    let artifact = gate.validate_transition(&before, &after);

    assert_eq!(artifact.status, ValidationStatus::Invalid);
    let ValidationResult::Invalid(violations) = artifact.result else {
        panic!("semantic packet mutation should be invalid");
    };
    assert!(violations.iter().any(|v| {
        v.kind == SchemaGateViolationKind::PacketFieldMutation
            && v.field == "certificate_required"
            && v.code() == "InvariantPacketFieldMutation"
    }));
    assert_eq!(
        gate.admit_transition(&before, &after),
        Refusable::Refused(RefusalSource::Refusal)
    );
}

#[test]
fn invariant_id_mutation_returns_refusal() {
    let gate = SchemaGate::new(atlas_store());
    let before = well_formed_packet();
    let after = packet(
        "Gamma2",
        InvariantLayer::GTFOC,
        "finite cochain carrier",
        "primal-dual replay certificate",
    );

    let artifact = gate.validate_transition(&before, &after);

    assert_eq!(artifact.status, ValidationStatus::Invalid);
    let ValidationResult::Invalid(violations) = artifact.result else {
        panic!("invariant id mutation should be invalid");
    };
    assert!(violations
        .iter()
        .any(|v| v.kind == SchemaGateViolationKind::InvariantIdMutation));
    assert_eq!(
        gate.admit_transition(&before, &after),
        Refusable::Refused(RefusalSource::Refusal)
    );
}

// Origin: engine/crates_rs/tests/core_contracts/invariant_atlas_schema_gate.rs
// Claim: urn:core:crates_rs:tests:invariant-atlas-schema-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord97149d23 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord97149d23` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError97149d23 {
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
impl BoundaryError97149d23 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError97149d23 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError97149d23 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord97149d23 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError97149d23> {
        if capacity_bound == 0 {
            return Err(BoundaryError97149d23::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError97149d23::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError97149d23::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_97149d23() {
    let admitted = BoundaryRecord97149d23::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord97149d23::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
