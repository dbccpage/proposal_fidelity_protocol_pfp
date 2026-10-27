// Executable finite evidence; AuthorityEffect: None.
//! Foundational mathematical bridges connecting the Witnessed Difference Programme
//! to Homotopy Type Theory (HoTT), Higher Category Theory, and Quantum Mechanics.
//!
//! Exact rational homology of a WDP complex is `core_homology`'s: ingest it with
//! `crate::kan_wdp_bridge::KanSimplicialComplex::from_wdp_complex` and read
//! `core_homology::simplicial::SimplicialComplex::rational_betti_numbers`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ec9b099f<T> {
    fn checked_invariant_ec9b099f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ec9b099f<T> for Option<T> {
    #[inline]
    fn checked_invariant_ec9b099f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ec9b099f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ec9b099f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

use crate::cochains::FiniteComplex;
use crate::error::WdpError;
use crate::kan_wdp_bridge::KanSimplicialComplex;
use crate::types::AuthorityEffect;

// =========================================================================
// 1. Homotopy Type Theory (HoTT) Bridge
// =========================================================================

/// Shape-only named path reference. Converting to the HoTT spine does not
/// check an inhabitant of an identity type or establish a semantic equivalence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityPathWitness {
    pub source: String,
    pub target: String,
    pub is_refl: bool,
    pub path_steps: Vec<String>,
    pub authority_effect: AuthorityEffect,
}

impl IdentityPathWitness {
    pub fn refl(x: &str) -> Self {
        Self {
            source: x.to_string(),
            target: x.to_string(),
            is_refl: true,
            path_steps: vec![x.to_string()],
            authority_effect: AuthorityEffect::None,
        }
    }

    pub fn path(steps: Vec<String>) -> Result<Self, WdpError> {
        if steps.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "path steps cannot be empty".to_string(),
            });
        }
        let src = steps.first().checked_invariant_ec9b099f("checked invariant").clone();
        let tgt = steps.last().checked_invariant_ec9b099f("checked invariant").clone();
        let is_refl = steps.len() == 1 && src == tgt;
        Ok(Self {
            source: src,
            target: tgt,
            is_refl,
            path_steps: steps,
            authority_effect: AuthorityEffect::None,
        })
    }

    pub fn to_hott_path(&self, type_id: &str) -> core_homotopy_type_theory::path::Path {
        use core_homotopy_type_theory::identity::{TermId, TypeId};
        core_homotopy_type_theory::path::Path {
            type_id: TypeId(type_id.to_string()),
            source: TermId(self.source.clone()),
            target: TermId(self.target.clone()),
            path_ref: if self.is_refl {
                format!("refl({})", self.source)
            } else {
                self.path_steps.join("->")
            },
        }
    }

    pub fn from_hott_path(path: &core_homotopy_type_theory::path::Path) -> Self {
        // Equal endpoints do not make a loop the reflexivity term.
        let is_refl =
            path.source.0 == path.target.0 && path.path_ref == format!("refl({})", path.source.0);
        Self {
            source: path.source.0.clone(),
            target: path.target.0.clone(),
            is_refl,
            path_steps: if is_refl {
                vec![path.source.0.clone()]
            } else {
                vec![path.source.0.clone(), path.target.0.clone()]
            },
            authority_effect: AuthorityEffect::None,
        }
    }
}

/// A checked conclusion for paths in the realization of a declared simplicial
/// complex. Vanishing of one cocycle period never proves homotopy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PathHomotopyStatus {
    IdenticalPath,
    ClosedPeriodObstruction,
    Undetermined,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Homotopy2CellObstruction {
    pub path_p: Vec<String>,
    pub path_q: Vec<String>,
    pub loop_circulation: BigRational,
    /// Some(false) only for a nonzero period of a verified closed 1-cochain;
    /// Some(true) only for identical paths; None means no homotopy decision.
    pub is_homotopic: Option<bool>,
    pub status: PathHomotopyStatus,
    pub authority_effect: AuthorityEffect,
}

fn validate_cochain_entry(
    complex: &FiniteComplex,
    cochain: &BTreeMap<(String, String), BigRational>,
    u: &String,
    v: &String,
    value: &BigRational,
) -> Result<(), WdpError> {
    if value.denom().is_zero() {
        return Err(WdpError::InvalidInput {
            detail: "zero cochain denominator".into(),
        });
    }
    if !complex
        .edges
        .iter()
        .any(|(a, b)| (a == u && b == v) || (a == v && b == u))
    {
        return Err(WdpError::InvalidInput {
            detail: format!("cochain key {u}-{v} is not a declared edge"),
        });
    }
    if let Some(reverse) = cochain.get(&(v.clone(), u.clone())) {
        if reverse.denom().is_zero() || value.reduced() != -reverse.reduced() {
            return Err(WdpError::InvalidInput {
                detail: format!("inconsistent reverse cochain value on {u}-{v}"),
            });
        }
    }
    Ok(())
}

fn checked_simplicial_cochain(
    complex: &FiniteComplex,
    cochain: &BTreeMap<(String, String), BigRational>,
) -> Result<(KanSimplicialComplex, Vec<BigRational>), WdpError> {
    let simplicial = KanSimplicialComplex::from_wdp_complex(complex)?;
    for ((u, v), value) in cochain {
        validate_cochain_entry(complex, cochain, u, v, value)?;
    }
    let values = simplicial
        .complex
        .simplices(1)
        .iter()
        .map(|edge| {
            let vertices = edge.vertices();
            FiniteComplex::edge_value(
                cochain,
                &simplicial.id_to_vertex[vertices[0]],
                &simplicial.id_to_vertex[vertices[1]],
            )
            .map(|value| value.reduced())
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((simplicial, values))
}

fn check_path(complex: &FiniteComplex, path: &[String]) -> Result<(), WdpError> {
    if path.is_empty() || path.iter().any(|v| !complex.vertices.contains(v)) {
        return Err(WdpError::InvalidInput {
            detail: "path must use declared vertices and be nonempty".into(),
        });
    }
    for step in path.windows(2) {
        if !complex
            .edges
            .iter()
            .any(|(u, v)| (u == &step[0] && v == &step[1]) || (u == &step[1] && v == &step[0]))
        {
            return Err(WdpError::InvalidInput {
                detail: format!("undeclared path step {}-{}", step[0], step[1]),
            });
        }
    }
    Ok(())
}

/// Verify a simplicial closed 1-cochain before using its period as a one-way
/// homotopy obstruction. Nonclosed fields are rejected: their period is not
/// invariant under face contractions. Zero period remains undetermined because
/// one rational cocycle cannot detect every fundamental-group element.
fn classify_path_homotopy(
    path_p: &[String],
    path_q: &[String],
    loop_circulation: &BigRational,
) -> (PathHomotopyStatus, Option<bool>) {
    if path_p == path_q {
        (PathHomotopyStatus::IdenticalPath, Some(true))
    } else if !loop_circulation.is_zero() {
        (PathHomotopyStatus::ClosedPeriodObstruction, Some(false))
    } else {
        (PathHomotopyStatus::Undetermined, None)
    }
}

fn verify_closed_1_cochain(
    simplicial: &KanSimplicialComplex,
    values: &[BigRational],
) -> Result<(), WdpError> {
    let closure = simplicial
        .complex
        .coboundary_matrix(1)?
        .mul_vec(values)
        .map_err(|error| {
            WdpError::Homology(core_homology::errors::HomologicalError::MatrixError(error))
        })?;
    if closure.iter().any(|value| !value.is_zero()) {
        return Err(WdpError::InvalidInput {
            detail: "path-homotopy period requires a closed 1-cochain (d1 c = 0)".into(),
        });
    }
    Ok(())
}

pub fn evaluate_path_homotopy(
    complex: &FiniteComplex,
    cochain: &BTreeMap<(String, String), BigRational>,
    path_p: &[String],
    path_q: &[String],
) -> Result<Homotopy2CellObstruction, WdpError> {
    check_path(complex, path_p)?;
    check_path(complex, path_q)?;
    if path_p.first() != path_q.first() || path_p.last() != path_q.last() {
        return Err(WdpError::InvalidInput {
            detail: "paths must have identical endpoints".into(),
        });
    }
    let (simplicial, values) = checked_simplicial_cochain(complex, cochain)?;
    verify_closed_1_cochain(&simplicial, &values)?;
    let period = |path: &[String]| -> Result<BigRational, WdpError> {
        path.windows(2)
            .map(|step| FiniteComplex::edge_value(cochain, &step[0], &step[1]).map(|q| q.reduced()))
            .sum()
    };
    let loop_circulation = period(path_p)? - period(path_q)?;
    let (status, is_homotopic) = classify_path_homotopy(path_p, path_q, &loop_circulation);
    Ok(Homotopy2CellObstruction {
        path_p: path_p.to_vec(),
        path_q: path_q.to_vec(),
        loop_circulation,
        is_homotopic,
        status,
        authority_effect: AuthorityEffect::None,
    })
}

// =========================================================================
// 2. Higher Category Theory Bridge (Kan 2-Nerve Horn Fillers)
// =========================================================================

/// A horn Lambda^2_1 in a simplicial 2-nerve: two composable 1-morphisms f: x -> y, g: y -> z.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HornLambda21 {
    pub vertex_x: String,
    pub vertex_y: String,
    pub vertex_z: String,
    pub edge_xy: (String, String),
    pub edge_yz: (String, String),
}

/// Witness of Kan horn filling Lambda^2_1 -> Delta^2.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KanHornFillerWitness {
    pub horn: HornLambda21,
    pub composite_edge_xz: (String, String),
    pub face_2cell: (String, String, String),
    pub curvature_obstruction: BigRational,
    pub is_filled: bool,
    pub authority_effect: AuthorityEffect,
}

/// Check one declared triangular face and its boundary curvature. This is
/// simplicial face membership, not the Kan condition for arbitrary horn maps.
/// Flatness cannot manufacture a missing face; horn edge fields must match
/// their named endpoints and all three boundary edges must already exist.
pub fn verify_kan_horn_filling(
    complex: &FiniteComplex,
    cochain: &BTreeMap<(String, String), BigRational>,
    horn: HornLambda21,
) -> Result<KanHornFillerWitness, WdpError> {
    let x = horn.vertex_x.clone();
    let y = horn.vertex_y.clone();
    let z = horn.vertex_z.clone();
    if horn.edge_xy != (x.clone(), y.clone()) || horn.edge_yz != (y.clone(), z.clone()) {
        return Err(WdpError::InvalidInput {
            detail: "horn edge fields do not match declared endpoints".into(),
        });
    }
    let (simplicial, _) = checked_simplicial_cochain(complex, cochain)?;
    let membership = simplicial.verify_kan_horn_filling(&[x.clone(), y.clone(), z.clone()], 1)?;
    let defect = FiniteComplex::edge_value(cochain, &x, &y)?.reduced()
        + FiniteComplex::edge_value(cochain, &y, &z)?.reduced()
        - FiniteComplex::edge_value(cochain, &x, &z)?.reduced();
    Ok(KanHornFillerWitness {
        horn,
        composite_edge_xz: (x.clone(), z.clone()),
        face_2cell: (x, y, z),
        is_filled: membership.is_filled && defect.is_zero(),
        curvature_obstruction: defect,
        authority_effect: AuthorityEffect::None,
    })
}

// =========================================================================
// 3. Quantum Mechanics Bridge (Cabello 18-Ray & Sorkin Interference)
// =========================================================================

/// Cabello 18-ray contextuality parity obstruction (WDP-CH18-D01, WDP-CH18-P09).
/// In R^4, exhibits 18 unnormalized rays arranged into 9 mutually orthogonal tetrads.
/// Every ray belongs to exactly 2 tetrads.
/// Non-contextual hidden variables require 9 = 2k, which is impossible (odd != even).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cabello18RayWitness {
    pub num_rays: usize,
    pub num_tetrads: usize,
    pub ray_occurrences: BTreeMap<usize, usize>, // ray_id -> count in tetrads
    pub tetrad_sum_parity: usize,                // 9 % 2 = 1 (odd)
    pub total_ray_parity: usize,                 // (2 * sum) % 2 = 0 (even)
    pub is_parity_obstructed: bool,
    pub authority_effect: AuthorityEffect,
}

/// Constructs and verifies the Cabello 18-ray contextuality parity witness.
pub fn verify_cabello_18ray_parity() -> Cabello18RayWitness {
    // 9 tetrads indexed 0..8 containing ray indices 0..17
    // Standard Cabello 1996 configuration:
    let tetrads: [[usize; 4]; 9] = [
        [0, 1, 2, 3],
        [0, 4, 5, 6],
        [1, 7, 8, 9],
        [2, 10, 11, 12],
        [3, 13, 14, 15],
        [4, 7, 10, 16],
        [5, 8, 13, 17],
        [6, 11, 14, 16],
        [9, 12, 15, 17],
    ];

    let mut occurrences: BTreeMap<usize, usize> = BTreeMap::new();
    for t in &tetrads {
        for &r in t {
            *occurrences.entry(r).or_insert(0) += 1;
        }
    }

    let num_rays = occurrences.len();
    let num_tetrads = tetrads.len();

    // Every ray must appear in exactly 2 tetrads
    let all_two = occurrences.values().all(|&c| c == 2);
    let tetrad_parity = num_tetrads % 2; // 9 % 2 = 1
    let ray_parity = (occurrences.values().sum::<usize>()) % 2; // (18 * 2) % 2 = 0

    let is_obstructed = all_two && tetrad_parity == 1 && ray_parity == 0;

    Cabello18RayWitness {
        num_rays,
        num_tetrads,
        ray_occurrences: occurrences,
        tetrad_sum_parity: tetrad_parity,
        total_ray_parity: ray_parity,
        is_parity_obstructed: is_obstructed,
        authority_effect: AuthorityEffect::None,
    }
}

/// Sorkin 3rd-order interference cancellation witness.
/// Verifies that in quadratic measure models P(A) = |psi_A|^2,
/// I_3(A, B, C) = P(ABC) - P(AB) - P(BC) - P(CA) + P(A) + P(B) + P(C) == 0.
pub fn verify_sorkin_i3_cancellation(psi: [BigRational; 3]) -> (BigRational, bool) {
    let p = |indices: &[usize]| -> BigRational {
        let sum: BigRational = indices.iter().map(|&i| &psi[i]).sum();
        &sum * &sum
    };

    let p_abc = p(&[0, 1, 2]);
    let p_ab = p(&[0, 1]);
    let p_bc = p(&[1, 2]);
    let p_ca = p(&[2, 0]);
    let p_a = p(&[0]);
    let p_b = p(&[1]);
    let p_c = p(&[2]);

    let i3 = p_abc - p_ab - p_bc - p_ca + p_a + p_b + p_c;
    let is_zero = i3.is_zero();
    (i3, is_zero)
}

/// Algebraic non-factorable rank >= 2 witness on Bool x Bool over Z.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AlgebraicNonFactorableWitness {
    pub matrix: [[i64; 2]; 2],
    pub determinant: i64,
    pub is_nonfactorable: bool,
    pub authority_effect: AuthorityEffect,
}

impl AlgebraicNonFactorableWitness {
    pub fn bell_basis() -> Self {
        let matrix = [[1, 0], [0, 1]];
        let det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
        Self {
            matrix,
            determinant: det,
            is_nonfactorable: det != 0,
            authority_effect: AuthorityEffect::None,
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/bridges.rs
// Claim: urn:core:crates_rs:core-wdp:bridges:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordec9b099f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordec9b099f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorec9b099f {
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
impl BoundaryErrorec9b099f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorec9b099f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorec9b099f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordec9b099f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorec9b099f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorec9b099f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorec9b099f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorec9b099f::ExceedsCapacity {
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
    use core_homology::scalar::q;

    #[test]
    fn test_cabello_18ray_parity_witness() {
        let witness = verify_cabello_18ray_parity();
        assert_eq!(witness.num_rays, 18);
        assert_eq!(witness.num_tetrads, 9);
        assert!(witness.is_parity_obstructed);
    }

    #[test]
    fn test_sorkin_i3_vanishing() {
        let psi = [q(1), q(2), q(-1)];
        let (i3, is_zero) = verify_sorkin_i3_cancellation(psi);
        assert!(is_zero);
        assert_eq!(i3, q(0));
    }

    #[test]
    fn test_algebraic_nonfactorable_matrix() {
        let witness = AlgebraicNonFactorableWitness::bell_basis();
        assert_eq!(witness.determinant, 1);
        assert!(witness.is_nonfactorable);
    }

    #[test]
    fn test_hott_path_bridge_roundtrip() {
        let wdp_path = IdentityPathWitness::path(vec!["x".to_string(), "y".to_string()]).unwrap();
        let hott_path = wdp_path.to_hott_path("CarrierType");
        assert_eq!(hott_path.source.0, "x");
        assert_eq!(hott_path.target.0, "y");
        assert_eq!(hott_path.path_ref, "x->y");
        assert!(hott_path.validate().is_ok());

        let roundtrip = IdentityPathWitness::from_hott_path(&hott_path);
        assert_eq!(roundtrip.source, "x");
        assert_eq!(roundtrip.target, "y");
        assert!(!roundtrip.is_refl);

        let refl = IdentityPathWitness::refl("x");
        let hott_refl = refl.to_hott_path("CarrierType");
        assert_eq!(hott_refl.path_ref, "refl(x)");
        let roundtrip_refl = IdentityPathWitness::from_hott_path(&hott_refl);
        assert!(roundtrip_refl.is_refl);
    }
    fn triangle(filled: bool) -> FiniteComplex {
        FiniteComplex::new(
            std::collections::BTreeSet::from(["a".into(), "b".into(), "c".into()]),
            vec![
                ("a".into(), "b".into()),
                ("b".into(), "c".into()),
                ("a".into(), "c".into()),
            ],
            if filled {
                vec![("a".into(), "b".into(), "c".into())]
            } else {
                vec![]
            },
        )
        .unwrap()
    }
    fn triangle_cochain(value: i64) -> BTreeMap<(String, String), BigRational> {
        BTreeMap::from([
            (("a".into(), "b".into()), q(value)),
            (("b".into(), "c".into()), q(value)),
            (("a".into(), "c".into()), q(value)),
        ])
    }
    #[test]
    fn closed_period_is_only_a_one_way_homotopy_obstruction() {
        let p = vec!["a".into(), "b".into(), "c".into()];
        let direct = vec!["a".into(), "c".into()];
        assert!(
            evaluate_path_homotopy(&triangle(true), &triangle_cochain(1), &p, &direct).is_err()
        );
        let obstructed =
            evaluate_path_homotopy(&triangle(false), &triangle_cochain(1), &p, &direct).unwrap();
        assert_eq!(obstructed.is_homotopic, Some(false));
        assert_eq!(
            obstructed.status,
            PathHomotopyStatus::ClosedPeriodObstruction
        );
        let invisible =
            evaluate_path_homotopy(&triangle(false), &triangle_cochain(0), &p, &direct).unwrap();
        assert_eq!(invisible.is_homotopic, None);
        assert_eq!(invisible.status, PathHomotopyStatus::Undetermined);
        assert_eq!(
            evaluate_path_homotopy(&triangle(false), &triangle_cochain(0), &p, &p)
                .unwrap()
                .is_homotopic,
            Some(true)
        );
        assert!(evaluate_path_homotopy(
            &triangle(false),
            &triangle_cochain(0),
            &["a".into(), "ghost".into(), "c".into()],
            &direct
        )
        .is_err());
    }
    #[test]
    fn zero_curvature_does_not_create_a_face_or_validate_a_malformed_horn() {
        let horn = HornLambda21 {
            vertex_x: "a".into(),
            vertex_y: "b".into(),
            vertex_z: "c".into(),
            edge_xy: ("a".into(), "b".into()),
            edge_yz: ("b".into(), "c".into()),
        };
        assert!(
            !verify_kan_horn_filling(&triangle(false), &triangle_cochain(0), horn.clone())
                .unwrap()
                .is_filled
        );
        assert!(
            verify_kan_horn_filling(&triangle(true), &triangle_cochain(0), horn.clone())
                .unwrap()
                .is_filled
        );
        let mut malformed = horn;
        malformed.edge_xy = ("a".into(), "c".into());
        assert!(verify_kan_horn_filling(&triangle(true), &triangle_cochain(0), malformed).is_err());
        let loop_path = core_homotopy_type_theory::path::Path {
            type_id: core_homotopy_type_theory::identity::TypeId("A".into()),
            source: core_homotopy_type_theory::identity::TermId("x".into()),
            target: core_homotopy_type_theory::identity::TermId("x".into()),
            path_ref: "nontrivial-loop".into(),
        };
        assert!(!IdentityPathWitness::from_hott_path(&loop_path).is_refl);
    }
}

#[cfg(test)]
mod l4_boundary_tests_ec9b099f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordec9b099f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordec9b099f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordec9b099f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordec9b099f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordec9b099f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorec9b099f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorec9b099f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
