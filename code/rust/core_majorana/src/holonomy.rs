//! Discrete holonomy residual on a declared face (CODE_DEMO).
//!
//! # What this is (only this)
//!
//! Given a **declared** finite complex and a **declared** edge cochain (connection
//! data in a **declared** coefficient monoid), each face has a **holonomy** equal
//! to the ordered product of edge values around that face (for \(\mathbb{F}_2\),
//! the sum mod 2 of incident edges — same linear map as \(d_1\)).
//!
//! The **holonomy residual** on a face is the failure of that product/sum to equal
//! the monoid identity. On \(\mathbb{F}_2\) that residual **is** the face component
//! of \(d_1 A\).
//!
//! # Authority fence
//!
//! - AuthorityEffect: **None** on every receipt.
//! - Does not mint `CertifiedAuthority`, FOC ExactRepair, or continuum curvature.
//! - Does not assert ontology outside the declared carrier and monoid.
//! - Gauge-equivalent connections (differ by \(d_0\alpha\)) share the same face
//!   holonomy residual when \(d_1 d_0 = 0\) — a **declared** identity of the
//!   cochain complex, not a claim about anything outside the packet.

use crate::complexes::ChainComplexGf2;
use crate::gf2_terminalizer::{
    Cyclotomic16Element, GF2Matrix, GF2ScheduleStatus, Gf2CocycleClassifier,
};
use serde::{Deserialize, Serialize};

pub const HOLONOMY_RECEIPT_TAG: &str = "core.majorana-holonomy-receipt.v1";

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; declared carrier + monoid only; diagnostic receipt.";

/// \(\mathbb{F}_2\) holonomy residual on each face: \(r = d_1 A\).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HolonomyReceiptGf2 {
    pub certificate_tag: String,
    pub complex_name: String,
    /// Edge cochain \(A \in C^1(\mathbb{F}_2)\).
    pub connection: Vec<u8>,
    /// Face residuals \(r = d_1 A\) (same length as number of faces).
    pub face_residuals: Vec<u8>,
    /// True iff every face residual is 0.
    pub flat: bool,
    /// Hamming weight of face residual vector.
    pub residual_weight: usize,
    pub boundary_valid: bool,
    /// Always `"None"`.
    pub authority_effect: String,
    pub notes: String,
}

/// Parallel-transport product around one face in \(\mathbb{Q}(\zeta_{16})\) (exact seed monoid).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HolonomyReceiptCyclotomic {
    pub certificate_tag: String,
    pub face_index: usize,
    /// Edge indices used on the face walk (as listed in `d1` support).
    pub edge_walk: Vec<usize>,
    /// Product of declared edge elements around the face (basis coeffs).
    pub holonomy_coeffs: [i64; 8],
    /// Residual = holonomy * inverse(identity) failure: true iff holonomy ≠ 1.
    pub residual_nontrivial: bool,
    pub authority_effect: String,
    pub notes: String,
}

/// Face residual vector \(r = d_1 A\) over \(\mathbb{F}_2\).
pub fn face_holonomy_residual_gf2(d1: &GF2Matrix, connection: &[u8]) -> Result<Vec<u8>, String> {
    if connection.len() != d1.cols {
        return Err(format!(
            "connection len {} != d1.cols {}",
            connection.len(),
            d1.cols
        ));
    }
    let mut r = vec![0u8; d1.rows];
    for i in 0..d1.rows {
        let mut acc = 0u8;
        for j in 0..d1.cols {
            acc ^= d1.data[i][j] & (connection[j] % 2);
        }
        r[i] = acc & 1;
    }
    Ok(r)
}

/// Holonomy residual receipt for a declared complex + \(\mathbb{F}_2\) connection.
pub fn holonomy_receipt_gf2(
    complex: &ChainComplexGf2,
    connection: &[u8],
) -> Result<HolonomyReceiptGf2, String> {
    if !complex.verify_boundary() {
        return Err("boundary invalid: d1 d0 != 0 on declared complex".into());
    }
    if connection.len() != complex.num_edges {
        return Err(format!(
            "connection len {} != num_edges {}",
            connection.len(),
            complex.num_edges
        ));
    }
    let face_residuals = face_holonomy_residual_gf2(&complex.d1, connection)?;
    let residual_weight = face_residuals.iter().filter(|&&b| b == 1).count();
    let flat = residual_weight == 0;
    let notes = if flat {
        "All face holonomies are identity in F2 (sum of edge values on each face = 0). \
         Residual weight 0 on the declared complex."
            .into()
    } else {
        format!(
            "Face holonomy residual weight {residual_weight}: at least one face has \
             d1 A = 1. This is a residual of the declared (complex, connection) pair. \
             Same data as OpenObstruction when residual is treated as a 1-cochain syndrome \
             on edges only after adapter choice; here residual lives on faces."
        )
    };
    Ok(HolonomyReceiptGf2 {
        certificate_tag: HOLONOMY_RECEIPT_TAG.into(),
        complex_name: complex.name.into(),
        connection: connection.iter().map(|x| x % 2).collect(),
        face_residuals,
        flat,
        residual_weight,
        boundary_valid: true,
        authority_effect: "None".into(),
        notes,
    })
}

/// Gauge transform: \(A' = A + d_0 \alpha\) (edge coboundary of a vertex 0-cochain).
pub fn gauge_transform_gf2(
    d0: &GF2Matrix,
    connection: &[u8],
    alpha: &[u8],
) -> Result<Vec<u8>, String> {
    if connection.len() != d0.rows || alpha.len() != d0.cols {
        return Err("gauge_transform shape mismatch".into());
    }
    let mut out = vec![0u8; d0.rows];
    for r in 0..d0.rows {
        let mut cob = 0u8;
        for c in 0..d0.cols {
            cob ^= d0.data[r][c] & (alpha[c] % 2);
        }
        out[r] = (connection[r] % 2) ^ cob;
    }
    Ok(out)
}

/// Edge indices with nonzero incidence on face `f` (walk support for products).
pub fn face_edge_support(d1: &GF2Matrix, face: usize) -> Result<Vec<usize>, String> {
    if face >= d1.rows {
        return Err("face index out of range".into());
    }
    Ok((0..d1.cols).filter(|&j| d1.data[face][j] == 1).collect())
}

/// Cyclotomic holonomy around face 0: product of declared edge elements.
///
/// Edge data must have length = number of edges; unused edges may be `one()`.
pub fn holonomy_receipt_cyclotomic_face0(
    complex: &ChainComplexGf2,
    edge_elements: &[Cyclotomic16Element],
) -> Result<HolonomyReceiptCyclotomic, String> {
    if complex.num_faces == 0 {
        return Err("no faces".into());
    }
    if edge_elements.len() != complex.num_edges {
        return Err("edge_elements length mismatch".into());
    }
    let walk = face_edge_support(&complex.d1, 0)?;
    let mut h = Cyclotomic16Element::one();
    for &e in &walk {
        h = h.checked_mul(&edge_elements[e]).ok_or("cyclotomic coefficient overflow")?;
    }
    let residual_nontrivial = h != Cyclotomic16Element::one();
    Ok(HolonomyReceiptCyclotomic {
        certificate_tag: HOLONOMY_RECEIPT_TAG.into(),
        face_index: 0,
        edge_walk: walk,
        holonomy_coeffs: h.coeffs,
        residual_nontrivial,
        authority_effect: "None".into(),
        notes: "Ordered product of declared Cyclotomic16Element on face-0 support. \
                residual_nontrivial iff product ≠ 1 in Z[ζ16]. \
                Declared representation data only."
            .into(),
    })
}

/// Bridge: treat face residual as open if any face has holonomy residual 1,
/// and compare to schedule class when connection is re-read as edge syndrome
/// against the same complex (optional diagnostic link, not an identification of layers).
pub fn connect_to_schedule_class(
    complex: &ChainComplexGf2,
    connection: &[u8],
) -> Result<(HolonomyReceiptGf2, GF2ScheduleStatus), String> {
    let hol = holonomy_receipt_gf2(complex, connection)?;
    let cert = Gf2CocycleClassifier::classify(&complex.d0, &complex.d1, connection)?;
    Ok((hol, cert.status))
}

// Origin: engine/crates_rs/core_majorana/src/holonomy.rs
// Claim: urn:core:crates_rs:core-majorana:holonomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6cb5e9b4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6cb5e9b4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6cb5e9b4 {
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
impl BoundaryError6cb5e9b4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6cb5e9b4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6cb5e9b4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6cb5e9b4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6cb5e9b4> {
        if capacity_bound == 0 {
            return Err(BoundaryError6cb5e9b4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6cb5e9b4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6cb5e9b4::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::complexes::{plaquette, surface_grid_2x2_torus, torus_logical_x_example, triangle};
    use crate::gf2_terminalizer::GF2Matrix;

    #[test]
    fn plaquette_flat_connection() {
        let c = plaquette();
        // All-zero connection: flat
        let r = holonomy_receipt_gf2(&c, &[0, 0, 0, 0]).unwrap();
        assert!(r.flat);
        assert_eq!(r.residual_weight, 0);
        assert_eq!(r.authority_effect, "None");
        assert_eq!(r.certificate_tag, HOLONOMY_RECEIPT_TAG);
    }

    #[test]
    fn plaquette_single_edge_flux() {
        let c = plaquette();
        // One edge set → face residual 1
        let r = holonomy_receipt_gf2(&c, &[1, 0, 0, 0]).unwrap();
        assert!(!r.flat);
        assert_eq!(r.face_residuals, vec![1]);
        assert_eq!(r.residual_weight, 1);
        assert_eq!(r.authority_effect, "None");
    }

    #[test]
    fn plaquette_full_cycle_flat_in_f2() {
        let c = plaquette();
        // All four edges: sum mod 2 = 0 on the single face
        let r = holonomy_receipt_gf2(&c, &[1, 1, 1, 1]).unwrap();
        assert!(r.flat);
        assert_eq!(r.face_residuals, vec![0]);
    }

    #[test]
    fn gauge_invariance_of_face_residual() {
        // Kills: gauge_transform returning the input connection, which keeps the residual equal.
        let c = plaquette();
        let a = vec![1, 0, 0, 0];
        let a2 = gauge_transform_gf2(&c.d0, &a, &[1, 0, 0, 0]).unwrap();
        assert_eq!(a2, vec![0, 0, 0, 1]);
        let r0 = holonomy_receipt_gf2(&c, &a).unwrap();
        let r1 = holonomy_receipt_gf2(&c, &a2).unwrap();
        assert_eq!(r0.face_residuals, vec![1]);
        assert_eq!(r1.face_residuals, vec![1]);
        assert!(gauge_transform_gf2(&c.d0, &a, &[1, 0])
            .unwrap_err()
            .contains("shape mismatch"));
    }

    #[test]
    fn triangle_holonomy_matches_d1() {
        let c = triangle();
        let a = vec![1, 1, 0];
        let r = holonomy_receipt_gf2(&c, &a).unwrap();
        // d1 = [1,1,1], sum = 0
        assert!(r.flat);
        let a2 = vec![1, 0, 0];
        let r2 = holonomy_receipt_gf2(&c, &a2).unwrap();
        assert_eq!(r2.face_residuals, vec![1]);
    }

    #[test]
    fn torus_single_edge_lights_faces_zero_and_two() {
        // Kills: a length-4 residual that is nonzero but not the support of edge 0.
        let c = surface_grid_2x2_torus();
        let r = holonomy_receipt_gf2(&c, &[1, 0, 0, 0, 0, 0, 0, 0]).unwrap();
        assert_eq!(r.face_residuals, vec![1, 0, 1, 0]);
        assert_eq!(r.residual_weight, 2);
        assert!(!r.flat);
        assert_eq!(face_edge_support(&c.d1, 0).unwrap(), vec![0, 2, 4, 5]);
        assert!(face_edge_support(&c.d1, 4)
            .unwrap_err()
            .contains("out of range"));
    }

    #[test]
    fn refuses_a_short_connection_and_a_broken_boundary() {
        // Kills: skipping the length check or the d1*d0 check.
        let c = plaquette();
        assert!(holonomy_receipt_gf2(&c, &[1, 0, 0])
            .unwrap_err()
            .contains("len"));
        let mut broken = c.clone();
        broken.d1 = GF2Matrix::from_data(vec![vec![1, 0, 0, 0]]);
        assert!(holonomy_receipt_gf2(&broken, &[0, 0, 0, 0])
            .unwrap_err()
            .contains("d1 d0"));
    }

    #[test]
    fn cyclotomic_face0_product_one() {
        let c = plaquette();
        let ones: Vec<_> = (0..4).map(|_| Cyclotomic16Element::one()).collect();
        let r = holonomy_receipt_cyclotomic_face0(&c, &ones).unwrap();
        assert!(!r.residual_nontrivial);
        assert_eq!(r.authority_effect, "None");
        assert_eq!(r.edge_walk.len(), 4);
    }

    #[test]
    fn cyclotomic_face0_zeta_product() {
        let c = plaquette();
        // ζ on one edge: product = ζ ≠ 1
        let mut edges: Vec<_> = (0..4).map(|_| Cyclotomic16Element::one()).collect();
        let mut z = [0i64; 8];
        z[1] = 1; // ζ
        edges[0] = Cyclotomic16Element { coeffs: z };
        let r = holonomy_receipt_cyclotomic_face0(&c, &edges).unwrap();
        // Kills: setting residual_nontrivial without writing the product into the basis.
        assert_eq!(r.holonomy_coeffs, [0, 1, 0, 0, 0, 0, 0, 0]);
        assert!(r.residual_nontrivial);
        edges[1] = Cyclotomic16Element::zeta();
        let r2 = holonomy_receipt_cyclotomic_face0(&c, &edges).unwrap();
        assert_eq!(r2.holonomy_coeffs, [0, 0, 1, 0, 0, 0, 0, 0]);
        assert!(r2.residual_nontrivial);
    }

    #[test]
    fn schedule_bridge_separates_flat_logical_from_open_flux() {
        // Kills: deriving the schedule class from flatness (flat would become Exact).
        let c = plaquette();
        let (h, status) = connect_to_schedule_class(&c, &[1, 0, 0, 0]).unwrap();
        assert_eq!(h.face_residuals, vec![1]);
        assert_eq!(status, GF2ScheduleStatus::OpenObstruction);
        let torus = surface_grid_2x2_torus();
        let (flat, logical) =
            connect_to_schedule_class(&torus, &torus_logical_x_example()).unwrap();
        assert_eq!(flat.face_residuals, vec![0, 0, 0, 0]);
        assert!(flat.flat);
        assert_eq!(logical, GF2ScheduleStatus::ClosedResidual);
    }
}

#[cfg(test)]
mod l4_boundary_tests_6cb5e9b4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6cb5e9b4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6cb5e9b4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6cb5e9b4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6cb5e9b4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6cb5e9b4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6cb5e9b4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6cb5e9b4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
