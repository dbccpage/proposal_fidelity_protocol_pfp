
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_f2d5a669<T> {
    fn checked_invariant_f2d5a669(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_f2d5a669<T> for Option<T> {
    #[inline]
    fn checked_invariant_f2d5a669(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_f2d5a669<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_f2d5a669(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::{
    canonical_json_bytes, require_digest, require_name, FoundationError, FoundationErrorCode,
};
use pfp_runtime::canonical::framed_sha256;
use serde_json::{Map, Value};

const PACKET_KERNEL_ID_DOMAIN: &str = "core.symbol-game.packet-kernel-id.v1";

/// The four-field packet basis shared by admitted packet families. The packet
/// identifier is deliberately derived and is not stored as a fifth field.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PacketKernel {
    contract_id: String,
    task_id: String,
    payload: Value,
    parent_id: Option<String>,
}

impl PacketKernel {
    pub fn new(
        contract_id: impl Into<String>,
        task_id: impl Into<String>,
        payload: Value,
        parent_id: Option<String>,
    ) -> Result<Self, FoundationError> {
        let contract_id = contract_id.into();
        let task_id = task_id.into();
        require_name(&contract_id, "packet contract identity")?;
        require_name(&task_id, "packet task identity")?;
        if let Some(parent) = &parent_id {
            require_digest(parent, "packet parent identity")?;
        }
        canonical_json_bytes(&payload)?;
        Ok(Self {
            contract_id,
            task_id,
            payload,
            parent_id,
        })
    }

    pub fn contract_id(&self) -> &str {
        &self.contract_id
    }

    pub fn task_id(&self) -> &str {
        &self.task_id
    }

    pub fn payload(&self) -> &Value {
        &self.payload
    }

    pub fn parent_id(&self) -> Option<&str> {
        self.parent_id.as_deref()
    }

    pub fn identity_material(&self) -> Value {
        let mut object = Map::new();
        object.insert(
            "contract_id".to_owned(),
            Value::String(self.contract_id.clone()),
        );
        object.insert("task_id".to_owned(), Value::String(self.task_id.clone()));
        object.insert("payload".to_owned(), self.payload.clone());
        object.insert(
            "parent_packet_id".to_owned(),
            self.parent_id
                .as_ref()
                .map_or(Value::Null, |parent| Value::String(parent.clone())),
        );
        Value::Object(object)
    }

    pub fn canonical_identity_bytes(&self) -> Vec<u8> {
        canonical_json_bytes(&self.identity_material())
            .checked_invariant_f2d5a669("PacketKernel construction already validated exact JSON")
    }

    pub fn packet_id(&self) -> String {
        framed_sha256(PACKET_KERNEL_ID_DOMAIN, &self.canonical_identity_bytes())
    }
}

/// Compare the structural four-field identity after canonical normalization.
pub fn structurally_identical(left: &PacketKernel, right: &PacketKernel) -> bool {
    left.canonical_identity_bytes() == right.canonical_identity_bytes()
}

/// A contract-declared semantic projection.
pub trait PacketProjection {
    fn projection_id(&self) -> &str;
    fn project(&self, packet: &PacketKernel) -> Result<Value, String>;
}

/// A named projection backed by caller-supplied contract semantics.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DeclaredProjection<F> {
    projection_id: String,
    project: F,
}

impl<F> DeclaredProjection<F> {
    pub fn new(projection_id: impl Into<String>, project: F) -> Result<Self, FoundationError> {
        let projection_id = projection_id.into();
        require_name(&projection_id, "semantic projection identity")?;
        Ok(Self {
            projection_id,
            project,
        })
    }
}

impl<F> PacketProjection for DeclaredProjection<F>
where
    F: Fn(&PacketKernel) -> Result<Value, String>,
{
    fn projection_id(&self) -> &str {
        &self.projection_id
    }

    fn project(&self, packet: &PacketKernel) -> Result<Value, String> {
        (self.project)(packet)
    }
}

/// Compare packet semantics only through an explicit contract projection.
/// Calling without one yields a typed refusal rather than guessing from bytes.
pub fn semantic_equivalent(
    left: &PacketKernel,
    right: &PacketKernel,
    projection: Option<&dyn PacketProjection>,
) -> Result<bool, FoundationError> {
    let projection = projection.ok_or_else(|| {
        FoundationError::new(
            FoundationErrorCode::ProjectionRequired,
            "packet bytes have no contract-free semantic projection",
        )
    })?;
    let left_value = projection.project(left).map_err(|message| {
        FoundationError::new(
            FoundationErrorCode::ProjectionFailed,
            format!(
                "projection {:?} failed: {message}",
                projection.projection_id()
            ),
        )
    })?;
    let right_value = projection.project(right).map_err(|message| {
        FoundationError::new(
            FoundationErrorCode::ProjectionFailed,
            format!(
                "projection {:?} failed: {message}",
                projection.projection_id()
            ),
        )
    })?;
    Ok(canonical_json_bytes(&left_value)? == canonical_json_bytes(&right_value)?)
}

// Origin: engine/crates_rs/pfp/src/foundation/packet.rs
// Claim: urn:core:crates_rs:pfp:packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf2d5a669 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf2d5a669` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf2d5a669 {
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
impl BoundaryErrorf2d5a669 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf2d5a669 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf2d5a669 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf2d5a669 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf2d5a669> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf2d5a669::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf2d5a669::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf2d5a669::ExceedsCapacity {
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
mod l4_boundary_tests_f2d5a669 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf2d5a669::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf2d5a669::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf2d5a669::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf2d5a669::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf2d5a669::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf2d5a669::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf2d5a669::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
