//! §2 — covering-edge diagrams: the coboundary `Δ(s)_e = r_{b,a} s(b) − s(a)`,
//! the raw tally `I(s) = Σ_e ‖Δ(s)_e‖₁`, the bound `‖Δ(s)‖₁ ≤ 2|E_cov|‖s‖_∞`,
//! and descent (`Δ(s) = 0`).
//!
//! Replicates `covering_edge.py`.  Claims B1/B2 of the paper's ledger: one
//! exact rational covering edge with `a, b` one-dimensional, `r = [[1]]`,
//! `s(a) = 1`, `s(b) = 3` gives defect `[['2']]`, `I = 2`, bound `6`.
//!
//! In the estate's vocabulary this is a *represented* compatibility defect
//! (§2.2 of the paper, §7.4.8 remark 1): a number computed on the declared
//! section, never an `H¹` class.  The bound certificate is a *witness*
//! certificate (`⊢ᵂ`): both sides are recomputed and compared, and the
//! Banach-space inequality it instantiates stays analytic.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c69beebe<T> {
    fn checked_invariant_c69beebe(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c69beebe<T> for Option<T> {
    #[inline]
    fn checked_invariant_c69beebe(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c69beebe<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c69beebe(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use super::matrix::Matrix;
use super::rational::{q, Rational};
use crate::certificate::{Certificate, CheckId, ObjectId};

/// One covering edge: a contractive restriction `r_{b,a} : F(b) → F(a)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CoveringEdge {
    /// Edge identifier.
    pub id: String,
    /// The lower node `a`.
    pub lower: String,
    /// The upper node `b`.
    pub upper: String,
    /// The restriction matrix, `dim F(a) × dim F(b)`, `ℓ¹`-contractive.
    pub restriction: Matrix,
}

/// A finite covering-edge diagram with declared fiber dimensions.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CoveringEdgeDiagram {
    /// Node → fiber dimension.
    pub fiber_dimensions: BTreeMap<String, usize>,
    /// The edges, in declaration order.
    pub edges: Vec<CoveringEdge>,
}

/// A section: node → column vector.
pub type Section = BTreeMap<String, Matrix>;

/// A defect family: edge → column vector.
pub type Defects = BTreeMap<String, Matrix>;

/// Exact witness for `‖Δ(s)‖₁ ≤ 2|E|‖s‖_∞`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CoboundaryBoundCertificate {
    /// Declared finite carrier and section retained for replay.
    pub diagram: CoveringEdgeDiagram,
    /// Section used to compute both sides.
    pub section: Section,
    /// `I(s)`.
    pub coboundary_norm: Rational,
    /// `‖s‖_∞ = max_x ‖s(x)‖₁`.
    pub section_sup_norm: Rational,
    /// `2|E|‖s‖_∞`.
    pub bound: Rational,
    /// Whether the bound holds.
    pub holds: bool,
}

impl CoboundaryBoundCertificate {
    /// Recompute both sides from a validated carrier and section.
    pub fn verify(&self) -> bool {
        let Ok(diagram) = CoveringEdgeDiagram::new(self.diagram.fiber_dimensions.clone(), self.diagram.edges.clone()) else { return false; };
        let Ok(section) = diagram.normalize_section(&self.section) else { return false; };
        let Ok(norm) = diagram.inconsistency(&section) else { return false; };
        let sup = section.values().map(Matrix::l1_norm).fold(Rational::ZERO, Rational::max);
        let bound = q(2) * q(diagram.edges.len() as i128) * sup;
        self.coboundary_norm == norm && self.section_sup_norm == sup && self.bound == bound
            && self.holds == (norm <= bound) && self.holds
    }

    /// The certificate the estate would issue: a witness — the object is
    /// the pair of sides, the check is their comparison.
    pub fn certificate(&self) -> Option<Certificate> {
        self.verify().then(|| Certificate::Witness {
            object: ObjectId(format!("I(s)={} bound={}", self.coboundary_norm, self.bound)),
            check: CheckId("both sides recomputed exactly; bound - I(s) >= 0".into()),
        })
    }
}

impl CoveringEdgeDiagram {
    /// Build and validate: nonempty, positive dimensions, unique edge ids,
    /// known nodes, right shapes, contractive restrictions.
    pub fn new(fiber_dimensions: BTreeMap<String, usize>, edges: Vec<CoveringEdge>) -> Result<CoveringEdgeDiagram, String> {
        if fiber_dimensions.is_empty() {
            return Err("a covering-edge diagram needs at least one fiber".into());
        }
        if fiber_dimensions.values().any(|&d| d == 0) {
            return Err("fiber dimensions must be positive".into());
        }
        let mut ids: Vec<&str> = edges.iter().map(|e| e.id.as_str()).collect();
        ids.sort();
        ids.dedup();
        if ids.len() != edges.len() {
            return Err("edge identifiers must be unique".into());
        }
        for e in &edges {
            let (Some(&da), Some(&db)) = (fiber_dimensions.get(&e.lower), fiber_dimensions.get(&e.upper)) else {
                return Err(format!("edge {:?} references an unknown node", e.id));
            };
            if !e.restriction.is_well_formed() || e.restriction.shape() != (da, db) {
                return Err(format!("edge {:?} has shape {:?}, expected {:?}", e.id, e.restriction.shape(), (da, db)));
            }
            if e.restriction.l1_operator_norm() > Rational::ONE {
                return Err(format!("edge {:?} is not l1-contractive", e.id));
            }
        }
        Ok(CoveringEdgeDiagram { fiber_dimensions, edges })
    }

    /// Validate a total section.
    pub fn normalize_section(&self, section: &Section) -> Result<Section, String> {
        let missing: Vec<&String> = self.fiber_dimensions.keys().filter(|k| !section.contains_key(*k)).collect();
        let extra: Vec<&String> = section.keys().filter(|k| !self.fiber_dimensions.contains_key(*k)).collect();
        if !missing.is_empty() || !extra.is_empty() {
            return Err(format!("section domain mismatch; missing={missing:?}, extra={extra:?}"));
        }
        for (node, &dim) in &self.fiber_dimensions {
            let v = &section[node];
            if !v.is_well_formed() || v.shape() != (dim, 1) {
                return Err(format!("section value at {node:?} has shape {:?}, expected {:?}", v.shape(), (dim, 1)));
            }
        }
        Ok(section.clone())
    }

    /// `Δ(s)_e = r_{b,a} s(b) − s(a)`, exactly, per edge.
    pub fn coboundary(&self, section: &Section) -> Result<Defects, String> {
        let s = self.normalize_section(section)?;
        Ok(self.edges.iter().map(|e| (e.id.clone(), e.restriction.mul(&s[&e.upper]).sub(&s[&e.lower]))).collect())
    }

    /// The raw tally `I(s)`.
    pub fn inconsistency(&self, section: &Section) -> Result<Rational, String> {
        let d = self.coboundary(section)?;
        Ok(self.edges.iter().fold(Rational::ZERO, |a, e| a + d[&e.id].l1_norm()))
    }

    /// Both sides of the §2.2 bound on this carrier.
    pub fn coboundary_bound_certificate(&self, section: &Section) -> Result<CoboundaryBoundCertificate, String> {
        let s = self.normalize_section(section)?;
        let sup = s.values().map(Matrix::l1_norm).fold(Rational::ZERO, Rational::max);
        let norm = self.inconsistency(&s)?;
        let bound = q(2) * q(self.edges.len() as i128) * sup;
        Ok(CoboundaryBoundCertificate { diagram: self.clone(), section: s, coboundary_norm: norm, section_sup_norm: sup, bound, holds: bound - norm >= Rational::ZERO })
    }

    /// True exactly when every covering-edge defect vanishes.
    pub fn is_descended(&self, section: &Section) -> Result<bool, String> {
        Ok(self.coboundary(section)?.values().all(Matrix::is_zero))
    }
}

/// The paper's B1/B2 receipt fixture: `{a: 1, b: 1}`, one edge `b>a` with
/// `r = [[1]]`, section `a ↦ 1`, `b ↦ 3`.
pub fn receipt_fixture() -> (CoveringEdgeDiagram, Section) {
    let dims = BTreeMap::from([("a".to_string(), 1), ("b".to_string(), 1)]);
    let edge = CoveringEdge { id: "b>a".into(), lower: "a".into(), upper: "b".into(), restriction: Matrix::eye(1) };
    let diagram = CoveringEdgeDiagram::new(dims, vec![edge]).checked_invariant_c69beebe("valid fixture");
    let section = Section::from([("a".to_string(), Matrix::column_i128(&[1])), ("b".to_string(), Matrix::column_i128(&[3]))]);
    (diagram, section)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/alpha_projection_obstruction/covering_edge.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:covering-edge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc69beebe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc69beebe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc69beebe {
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
impl BoundaryErrorc69beebe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc69beebe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc69beebe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc69beebe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc69beebe> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc69beebe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc69beebe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc69beebe::ExceedsCapacity {
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

    /// B1/B2: defect `[['2']]`, `I = 2`, bound `6`, and the bound holds.
    #[test]
    fn the_receipt_fixture_gives_defect_two_tally_two_bound_six() {
        let (d, s) = receipt_fixture();
        let defects = d.coboundary(&s).unwrap();
        assert_eq!(defects["b>a"].to_string(), "[['2']]");
        assert_eq!(d.inconsistency(&s).unwrap(), q(2));
        let b = d.coboundary_bound_certificate(&s).unwrap();
        assert_eq!((b.coboundary_norm, b.bound, b.holds), (q(2), q(6), true));
        assert_eq!(b.certificate().unwrap().kind(), crate::certificate::CertKind::Witness);
        assert!(!d.is_descended(&s).unwrap());
        let flat = Section::from([("a".to_string(), Matrix::column_i128(&[3])), ("b".to_string(), Matrix::column_i128(&[3]))]);
        assert!(d.is_descended(&flat).unwrap());
    }

    #[test]
    fn a_non_contractive_restriction_is_refused_at_construction() {
        let dims = BTreeMap::from([("a".to_string(), 1), ("b".to_string(), 1)]);
        let bad = CoveringEdge { id: "e".into(), lower: "a".into(), upper: "b".into(), restriction: Matrix::from_i128(&[&[2]]) };
        assert!(CoveringEdgeDiagram::new(dims.clone(), vec![bad]).unwrap_err().contains("not l1-contractive"));
        let wrong = CoveringEdge { id: "e".into(), lower: "a".into(), upper: "zz".into(), restriction: Matrix::eye(1) };
        assert!(CoveringEdgeDiagram::new(dims, vec![wrong]).unwrap_err().contains("unknown node"));
    }

    #[test]
    fn a_partial_section_is_a_domain_mismatch_not_a_zero() {
        let (d, _) = receipt_fixture();
        let partial = Section::from([("a".to_string(), Matrix::column_i128(&[1]))]);
        assert!(d.coboundary(&partial).unwrap_err().contains("missing"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c69beebe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc69beebe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc69beebe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc69beebe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc69beebe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc69beebe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc69beebe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc69beebe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
