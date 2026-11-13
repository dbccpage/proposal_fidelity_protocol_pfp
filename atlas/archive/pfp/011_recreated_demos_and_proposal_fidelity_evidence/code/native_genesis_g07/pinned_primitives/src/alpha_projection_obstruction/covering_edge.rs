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
    let diagram = CoveringEdgeDiagram::new(dims, vec![edge]).expect("valid fixture");
    let section = Section::from([("a".to_string(), Matrix::column_i128(&[1])), ("b".to_string(), Matrix::column_i128(&[3]))]);
    (diagram, section)
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
