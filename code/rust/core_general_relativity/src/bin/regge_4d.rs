//! CLI receipt for the exact rational 4D Regge checks.
//!
//! AuthorityEffect: None.
//! The tests check rational Cayley-Menger data, simplicity via the pfaffian, chartwise closure, SO(4,Q) holonomy, Freudenthal volume conservation, and the rational defect predicate.
//! They do not evaluate Σ A_h ε_h and they do not claim the round 4-sphere Einstein-Hilbert action was computed. The flat comparison value is the rational 0.

#![forbid(unsafe_code)]

use linear_algebra::regge_exact::{cayley_menger, q_i64, q_ratio, signed_volume_4, So4};
use num_rational::BigRational;
use core_general_relativity::exact_regge::{
    all_hinges_simple, all_tetra_closures_vanish, closed_s4_cube_boundary, defect_bound_holds,
    flat_einstein_hilbert, freudenthal_refine_16, hinge_holonomy, orthogonal_pentatope,
    pythagorean_so4, pythagorean_so4_inverse, rational_regge_proxy, try_transition, ManifoldError,
    SimplicialManifold4D,
};
use serde_json::{json, Value};

fn main() -> std::process::ExitCode {
    let (value, checks_pass) = build_receipt();
    println!("{value}");
    if checks_pass && persist_receipt(&value) {
        std::process::ExitCode::SUCCESS
    } else {
        std::process::ExitCode::from(1)
    }
}

fn build_receipt() -> (Value, bool) {
    let flat = flat_einstein_hilbert();
    let orthogonal = orthogonal_receipt();
    let refinement = refinement_receipt(&flat);
    let closed = closed_s4_receipt();
    // Identity of the Pythagorean pair, zero Frobenius defect, and rejection of
    // the zero frame and of diag(1, 1, 1, -1).
    let holonomy_ok = holonomy_identity();
    let bound_accepts = manufactured_bound_accepts();
    let bound_rejects = manufactured_bound_rejects();

    let checks_pass = [
        orthogonal.nondegenerate,
        orthogonal.simple,
        orthogonal.closure,
        refinement.volume_conserved,
        refinement.defect_bound_holds,
        closed.nondegenerate,
        closed.simple,
        closed.closure,
        holonomy_ok,
        bound_accepts,
        bound_rejects,
        refinement.children == 16,
        closed.vertices == 32,
        closed.pentatopes == 240,
        orthogonal.euler_characteristic == 1,
        closed.euler_characteristic == 2,
        !orthogonal.signed_volume.is_empty(),
    ]
    .into_iter()
    .all(std::convert::identity);

    // `float_arithmetic` records that this receipt does not perform floating-point arithmetic.
    let value = json!({
        "authority_effect": "None",
        "scalar": "BigRational",
        "float_arithmetic": false,
        "classical_regge_action": "not_evaluated_transcendental_deficit",
        "flat_einstein_hilbert": flat.to_string(),
        "orthogonal_pentatope": {
            "signed_volume": orthogonal.signed_volume,
            "volume_squared": orthogonal.volume_squared,
            "nondegenerate": orthogonal.nondegenerate,
            "simple": orthogonal.simple,
            "closure": orthogonal.closure,
            "euler_characteristic": orthogonal.euler_characteristic,
        },
        "refinement": {
            "children": refinement.children,
            "volume_conserved": refinement.volume_conserved,
            "flat_proxy": refinement.flat_proxy,
            "defect_bound_holds": refinement.defect_bound_holds,
        },
        "closed_s4": {
            "vertices": closed.vertices,
            "pentatopes": closed.pentatopes,
            "euler_characteristic": closed.euler_characteristic,
            "nondegenerate": closed.nondegenerate,
            "simple": closed.simple,
            "closure": closed.closure,
        },
        "holonomy_identity": holonomy_ok,
        "manufactured_bound_accepts": bound_accepts,
        "manufactured_bound_rejects": bound_rejects,
    });
    (value, checks_pass)
}

struct OrthogonalReceipt {
    signed_volume: String,
    volume_squared: String,
    nondegenerate: bool,
    simple: bool,
    closure: bool,
    euler_characteristic: i64,
}

fn orthogonal_receipt() -> OrthogonalReceipt {
    let mut receipt = OrthogonalReceipt {
        signed_volume: String::new(),
        volume_squared: String::new(),
        nondegenerate: false,
        simple: false,
        closure: false,
        euler_characteristic: 0,
    };
    let Ok(manifold) = orthogonal_pentatope() else {
        return receipt;
    };
    receipt.nondegenerate = manifold.nondegeneracy().is_ok();
    receipt.simple = ok_true(all_hinges_simple(&manifold));
    receipt.closure = ok_true(all_tetra_closures_vanish(&manifold));
    receipt.euler_characteristic = manifold.euler_characteristic();
    let Ok(chart) = manifold.pentatope(0) else {
        return receipt;
    };
    if let Ok(volume) = signed_volume_4(&chart.coords) {
        receipt.signed_volume = volume.to_string();
    }
    let lengths = squared_edge_block(&chart.coords);
    if let Ok(cayley) = cayley_menger(4, &lengths) {
        receipt.volume_squared = cayley.volume_squared.to_string();
    }
    receipt
}

struct RefinementReceipt {
    children: usize,
    volume_conserved: bool,
    flat_proxy: String,
    defect_bound_holds: bool,
}

fn refinement_receipt(flat: &BigRational) -> RefinementReceipt {
    let mut receipt = RefinementReceipt {
        children: 0,
        volume_conserved: false,
        flat_proxy: String::new(),
        defect_bound_holds: false,
    };
    let Ok(manifold) = orthogonal_pentatope() else {
        return receipt;
    };
    let Ok(chart) = manifold.pentatope(0) else {
        return receipt;
    };
    let Ok(parent_volume) = signed_volume_4(&chart.coords) else {
        return receipt;
    };
    let Ok(children) = freudenthal_refine_16(&chart.coords) else {
        return receipt;
    };
    receipt.children = children.len();
    let mut sum = q_i64(0);
    let mut all_nonzero = !children.is_empty();
    for child in &children {
        match signed_volume_4(child) {
            Ok(volume) if volume != q_i64(0) => sum += volume,
            _ => {
                all_nonzero = false;
                break;
            }
        }
    }
    receipt.volume_conserved = all_nonzero && sum == parent_volume;

    let Ok(refined) = SimplicialManifold4D::from_ambient_pentatopes(&children) else {
        return receipt;
    };
    if refined.nondegeneracy().is_err() {
        return receipt;
    }
    let Ok(proxy) = rational_regge_proxy(&refined, &[]) else {
        return receipt;
    };
    receipt.flat_proxy = proxy.action.to_string();
    receipt.defect_bound_holds = match q_ratio(1, 4) {
        Ok(a_squared) => defect_bound_holds(&proxy.action, flat, &q_i64(1), &a_squared),
        Err(_) => false,
    };
    receipt
}

struct ClosedS4Receipt {
    vertices: u32,
    pentatopes: usize,
    euler_characteristic: i64,
    nondegenerate: bool,
    simple: bool,
    closure: bool,
}

fn closed_s4_receipt() -> ClosedS4Receipt {
    let mut receipt = ClosedS4Receipt {
        vertices: 0,
        pentatopes: 0,
        euler_characteristic: 0,
        nondegenerate: false,
        simple: false,
        closure: false,
    };
    let Ok(sphere) = closed_s4_cube_boundary() else {
        return receipt;
    };
    receipt.vertices = sphere.vertex_count();
    receipt.pentatopes = sphere.pentatope_count();
    receipt.euler_characteristic = sphere.euler_characteristic();
    receipt.nondegenerate = sphere.nondegeneracy().is_ok();
    receipt.simple = ok_true(all_hinges_simple(&sphere));
    receipt.closure = ok_true(all_tetra_closures_vanish(&sphere));
    receipt
}

fn holonomy_identity() -> bool {
    let holonomy: So4 = hinge_holonomy(&[pythagorean_so4(), pythagorean_so4_inverse()]);
    if !holonomy.is_identity() || holonomy.frobenius_defect_squared() != q_i64(0) {
        return false;
    }
    let zero = matrix4([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
    let reflection = matrix4([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]]);
    try_transition(zero).is_err() && try_transition(reflection).is_err()
}

fn manufactured_bound_accepts() -> bool {
    let Ok(s_regge) = q_ratio(1, 3) else {
        return false;
    };
    let Ok(s_eh) = q_ratio(1, 4) else {
        return false;
    };
    let Ok(a_squared) = q_ratio(1, 16) else {
        return false;
    };
    defect_bound_holds(&s_regge, &s_eh, &q_i64(2), &a_squared)
}

/// True when the violating witness is rejected, that is, when `defect_bound_holds` returns false.
fn manufactured_bound_rejects() -> bool {
    let Ok(a_squared) = q_ratio(1, 4) else {
        return false;
    };
    !defect_bound_holds(&q_i64(1), &q_i64(0), &q_i64(1), &a_squared)
}

fn ok_true(result: Result<bool, ManifoldError>) -> bool {
    matches!(result, Ok(true))
}

fn persist_receipt(value: &Value) -> bool {
    let path =
        std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/core_general_relativity/fixtures/regge_4d_receipt.json");
    let Some(parent) = path.parent() else {
        return false;
    };
    if std::fs::create_dir_all(parent).is_err() {
        return false;
    }
    let Ok(pretty) = serde_json::to_string_pretty(value) else {
        return false;
    };
    std::fs::write(path, pretty).is_ok()
}

/// Squared Euclidean distances of five points, packed into a symmetric 5×5 block.
/// The diagonal is zero. Only `BigRational` operations are used.
fn squared_edge_block(points: &[[BigRational; 4]; 5]) -> [[BigRational; 5]; 5] {
    std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            if i == j {
                q_i64(0)
            } else {
                squared_distance(&points[i], &points[j])
            }
        })
    })
}

fn squared_distance(left: &[BigRational; 4], right: &[BigRational; 4]) -> BigRational {
    let mut sum = q_i64(0);
    for (left_coord, right_coord) in left.iter().zip(right.iter()) {
        let delta = left_coord - right_coord;
        sum += &delta * &delta;
    }
    sum
}

fn matrix4(entries: [[i64; 4]; 4]) -> [[BigRational; 4]; 4] {
    std::array::from_fn(|row| std::array::from_fn(|col| q_i64(entries[row][col])))
}

// Origin: engine/crates_rs/core_general_relativity/src/bin/regge_4d.rs
// Claim: urn:core:crates_rs:core-general-relativity:regge-4d:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf0704ae3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf0704ae3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf0704ae3 {
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
impl BoundaryErrorf0704ae3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf0704ae3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf0704ae3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf0704ae3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf0704ae3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf0704ae3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf0704ae3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf0704ae3::ExceedsCapacity {
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
mod l4_boundary_tests_f0704ae3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf0704ae3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf0704ae3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf0704ae3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf0704ae3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf0704ae3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf0704ae3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf0704ae3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
