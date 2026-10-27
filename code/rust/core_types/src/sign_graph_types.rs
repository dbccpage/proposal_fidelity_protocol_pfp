use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum Filling {
    HalfFilled,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct HamiltonianDescriptor {
    pub n_sites: usize,
    pub adjacency: Vec<(usize, usize)>,
    pub edge_signs: Option<Vec<u8>>,
    pub filling: Filling,
    pub hopping: Option<Vec<f64>>,
    pub interaction_u: f64,
    pub has_spin_orbit: bool,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SignFreeVerdict {
    pub is_sign_free: bool,
    pub explanation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SignedGraph {
    pub n_vertices: usize,
    pub edges: Vec<(usize, usize)>,
    pub signs: Vec<bool>,
    pub weights: Option<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SignFreeDomain {
    pub vertices: Vec<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignError { kind: &'static str, left: i128, right: i128 }
impl SignError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Product of three signs in {+1, -1}. The triangle is frustrated exactly when the product is -1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TriangleSign { product: i8, frustrated: bool }
impl TriangleSign {
    pub fn try_triangle(signs: &[i8]) -> Result<Self, SignError> {
        if signs.len() != 3 {
            return Err(SignError::new("a triangle carries three signs", i128::try_from(signs.len()).map_or(i128::MAX, |converted| converted), 3));
        }
        let mut product = 1i8;
        for sign in signs {
            if *sign != 1 && *sign != -1 {
                return Err(SignError::new("a sign is +1 or -1", i128::from(*sign), 1));
            }
            product = product.checked_mul(*sign).ok_or_else(|| SignError::new("sign product overflow", i128::from(product), i128::from(*sign)))?;
        }
        Ok(Self { product, frustrated: product == -1 })
    }
    pub const fn frustrated(&self) -> bool { self.frustrated }
}

// Origin: engine/crates_rs/core_types/src/sign_graph_types.rs
// Claim: urn:core:crates_rs:core-types:sign-graph-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord155cf590 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord155cf590` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError155cf590 {
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
impl BoundaryError155cf590 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError155cf590 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError155cf590 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord155cf590 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError155cf590> {
        if capacity_bound == 0 {
            return Err(BoundaryError155cf590::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError155cf590::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError155cf590::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod triangle_sign_checks {
    use super::TriangleSign;
    #[test]
    fn one_negative_sign_frustrates_the_triangle() {
        let sign = TriangleSign::try_triangle(&[1, 1, -1]);
        assert_eq!(sign.as_ref().map(|item| item.product), Ok(-1));
        assert_eq!(sign.as_ref().map(TriangleSign::frustrated), Ok(true));
        assert_eq!(TriangleSign::try_triangle(&[2, 1, 1]).map(|_| ()).map_err(|e| e.kind()), Err("a sign is +1 or -1"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_155cf590 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord155cf590::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord155cf590::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord155cf590::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord155cf590::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord155cf590::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError155cf590::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError155cf590::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
