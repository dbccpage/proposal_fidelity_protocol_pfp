//! §7.2 — the three certification levels on one exact linear presentation:
//! an induced cochain (observation maps applied to residuals), membership
//! `ω ∈ im(d₀)` with a repair witness or a separating left-kernel vector,
//! and the quotient `ℓ¹` distance `Φ([ω]) = min_α ‖ω − d₀α‖₁` by primal and
//! dual vertex enumeration.  Higher-cell data (`C²`, `d₁`) is refused,
//! never synthesised.
//!
//! Replicates `cochain_presentation.py`.  Ledger claims A2/A3/D8/G1 (the
//! pipeline on `d₀ = [[1],[1]]`, residuals `2, 3`: induced `[2, 3]`,
//! repair witness `[2]` for `[2, 2]`, separator `[-1, 1]` with pairing `1`
//! for `[2, 3]`, quotient distance `1` with dual witness `[-1, 1]`), and
//! B4/G2 (the refusal).
//!
//! The estate's reading: membership is a *witness* certificate, non-membership
//! is an *obstruction* certificate (the separator is the proof), and the
//! quotient distance is a witness certificate whose check is the primal–dual
//! agreement.  The missing `d₁` is a *capability refusal*: no certificate of
//! any kind is issued for what was not supplied, and in particular the
//! absence of `d₁` is not an obstruction certificate that `d₁` cannot exist.

use std::collections::BTreeMap;

use super::matrix::{combinations, Matrix};
use super::rational::{q, Rational};
use crate::certificate::{Certificate, CheckId, ObjectId, ProofId};

/// One exact linear map `q_e : R_e → V_e`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ObservationMap {
    /// Edge identifier.
    pub edge_id: String,
    /// The map.
    pub matrix: Matrix,
}

impl ObservationMap {
    /// Apply to a residual column.
    pub fn observe(&self, residual: &Matrix) -> Result<Matrix, String> {
        if residual.shape() != (self.matrix.cols, 1) {
            return Err(format!("residual for {:?} has shape {:?}, expected {:?}", self.edge_id, residual.shape(), (self.matrix.cols, 1)));
        }
        Ok(self.matrix.mul(residual))
    }
}

/// Ordered exact edge blocks produced by a total observation presentation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct InducedCochain {
    /// The declared edge order.
    pub edge_order: Vec<String>,
    /// One block per edge, in that order.
    pub blocks: Vec<Matrix>,
}

impl InducedCochain {
    /// The stacked column.
    pub fn as_vector(&self) -> Matrix {
        Matrix::vstack(&self.blocks)
    }
}

/// A total, ordered family of exact observation maps.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ObservationPresentation {
    /// The declared edge order.
    pub edge_order: Vec<String>,
    /// Edge → map.
    pub maps: BTreeMap<String, ObservationMap>,
}

impl ObservationPresentation {
    /// Build and validate.
    pub fn new(edge_order: Vec<String>, maps: BTreeMap<String, ObservationMap>) -> Result<ObservationPresentation, String> {
        if edge_order.is_empty() {
            return Err("an observation presentation needs at least one edge".into());
        }
        let mut sorted = edge_order.clone();
        sorted.sort();
        sorted.dedup();
        if sorted.len() != edge_order.len() {
            return Err("edge_order contains duplicates".into());
        }
        let missing: Vec<&String> = edge_order.iter().filter(|e| !maps.contains_key(*e)).collect();
        let extra: Vec<&String> = maps.keys().filter(|e| !edge_order.contains(e)).collect();
        if !missing.is_empty() || !extra.is_empty() {
            return Err(format!("observation-map domain mismatch; missing={missing:?}, extra={extra:?}"));
        }
        if edge_order.iter().any(|e| maps[e].edge_id != *e) {
            return Err("observation-map keys must match their edge_id fields".into());
        }
        Ok(ObservationPresentation { edge_order, maps })
    }

    /// Apply every map to its residual, in order.
    pub fn induce_field(&self, residuals: &BTreeMap<String, Matrix>) -> Result<InducedCochain, String> {
        let missing: Vec<&String> = self.edge_order.iter().filter(|e| !residuals.contains_key(*e)).collect();
        if !missing.is_empty() {
            return Err(format!("normal residuals missing declared edges: {missing:?}"));
        }
        let extra: Vec<&String> = residuals.keys().filter(|e| !self.edge_order.contains(e)).collect();
        if !extra.is_empty() {
            return Err(format!("normal residuals contain edges without declared maps: {extra:?}"));
        }
        let mut blocks = Vec::new();
        for e in &self.edge_order {
            blocks.push(self.maps[e].observe(&residuals[e])?);
        }
        Ok(InducedCochain { edge_order: self.edge_order.clone(), blocks })
    }
}

/// Exact membership or non-membership witness for `ω ∈ im(d₀)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExactnessCertificate {
    /// Whether `ω` is a coboundary.
    pub is_exact_coboundary: bool,
    /// `ω`.
    pub cochain: Matrix,
    /// `d₀`.
    pub repair_map: Matrix,
    /// The repair witness `α` with `d₀α = ω`, when exact.
    pub witness: Option<Matrix>,
    /// A left-kernel vector `v` with `vᵀd₀ = 0` and `vᵀω ≠ 0`, when not.
    pub separating_left_kernel_vector: Option<Matrix>,
    /// `vᵀω`.
    pub separating_pairing: Option<Rational>,
}

impl ExactnessCertificate {
    /// Recheck from the data alone.
    pub fn verify(&self) -> bool {
        if !self.repair_map.is_well_formed() || !self.cochain.is_well_formed()
            || self.cochain.shape() != (self.repair_map.rows, 1) { return false; }
        if self.is_exact_coboundary {
            return self.separating_left_kernel_vector.is_none() && self.separating_pairing.is_none()
                && self.witness.as_ref().is_some_and(|w| w.is_well_formed()
                    && w.shape() == (self.repair_map.cols, 1)
                    && self.repair_map.mul(w) == self.cochain);
        }
        let (Some(v), Some(p)) = (&self.separating_left_kernel_vector, self.separating_pairing) else { return false };
        self.witness.is_none() && v.is_well_formed() && v.shape() == (self.repair_map.rows, 1)
            && v.transpose().mul(&self.repair_map).is_zero()
            && v.transpose().mul(&self.cochain).get(0, 0) == p && !p.is_zero()
    }

    /// The estate's certificate: a witness when exact, an obstruction
    /// (the separator is the proof) when not.
    pub fn certificate(&self) -> Option<Certificate> {
        if !self.verify() { return None; }
        Some(if self.is_exact_coboundary {
            Certificate::Witness {
                object: ObjectId(format!("repair alpha={}", self.witness.as_ref().map_or("?".to_string(), |w| w.to_string()))),
                check: CheckId("d0 * alpha == omega, exactly".into()),
            }
        } else {
            Certificate::Obstruction {
                proof: ProofId(format!(
                    "left-kernel separator v={} with v^T d0 = 0 and v^T omega = {}",
                    self.separating_left_kernel_vector.as_ref().map_or("?".to_string(), |v| v.to_string()),
                    self.separating_pairing.map_or("?".to_string(), |p| p.to_string())
                )),
            }
        })
    }
}

/// Exact rational `ℓ¹` distance from `ω` to `im(d₀)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QuotientDistanceCertificate {
    /// `Φ([ω])`.
    pub distance: Rational,
    /// A minimiser `α`.
    pub repair_witness: Matrix,
    /// `ω − d₀α`.
    pub residual: Matrix,
    /// `ω`.
    pub cochain: Matrix,
    /// A dual vertex `y` with `d₀ᵀy = 0`, `‖y‖_∞ ≤ 1`.
    pub dual_witness: Matrix,
    /// `yᵀω`, which equals the distance.
    pub dual_pairing: Rational,
    /// `d₀`.
    pub repair_map: Matrix,
}

impl QuotientDistanceCertificate {
    /// Recheck from the data alone.
    pub fn verify(&self) -> bool {
        let m = self.repair_map.rows;
        self.repair_map.is_well_formed() && self.cochain.is_well_formed()
            && self.repair_witness.is_well_formed() && self.residual.is_well_formed()
            && self.dual_witness.is_well_formed()
            && self.cochain.shape() == (m, 1) && self.residual.shape() == (m, 1)
            && self.repair_witness.shape() == (self.repair_map.cols, 1)
            && self.dual_witness.shape() == (m, 1)
            && self.residual == self.cochain.sub(&self.repair_map.mul(&self.repair_witness))
            && self.residual.l1_norm() == self.distance
            && self.repair_map.transpose().mul(&self.dual_witness).is_zero()
            && self.dual_witness.data.iter().all(|v| v.abs() <= Rational::ONE)
            && self.dual_witness.transpose().mul(&self.cochain).get(0, 0) == self.dual_pairing
            && self.dual_pairing == self.distance && self.distance >= Rational::ZERO
    }

    /// A witness certificate: the object is the primal–dual pair, the check
    /// is their agreement.
    pub fn certificate(&self) -> Option<Certificate> {
        if !self.verify() { return None; }
        Some(Certificate::Witness {
            object: ObjectId(format!("primal alpha={} dual y={}", self.repair_witness, self.dual_witness)),
            check: CheckId(format!("||omega - d0 alpha||_1 = y^T omega = {}", self.distance)),
        })
    }
}

/// The refusal for higher-cell data that was not supplied.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CochainRefusal {
    /// The native covering-edge carrier supplies no `C²` or `d₁`.
    HigherDifferentialUnavailable(String),
    /// `d₁·d₀ ≠ 0`, or the shapes do not compose.
    ComplexConditionFailed(String),
}

/// Capability witness for a verified complex `C⁰ → C¹ → C²`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdmittedComplexV1 {
    /// `d₀`.
    pub d0: Matrix,
    /// `d₁`, with `d₁·d₀ = 0` checked.
    pub d1: Matrix,
}

/// Check `d₁·d₀ = 0` exactly, or refuse absent higher-cell data.
pub fn verify_cochain_complex(d0: &Matrix, d1: Option<&Matrix>) -> Result<AdmittedComplexV1, CochainRefusal> {
    let Some(d1) = d1 else {
        return Err(CochainRefusal::HigherDifferentialUnavailable("PO-000 native covering-edge data supplies no C2 or d1".into()));
    };
    if !d0.is_well_formed() || !d1.is_well_formed() || d1.cols != d0.rows {
        return Err(CochainRefusal::ComplexConditionFailed("d1 and d0 dimensions do not compose".into()));
    }
    if !d1.mul(d0).is_zero() {
        return Err(CochainRefusal::ComplexConditionFailed("d1*d0=0 complex condition failed".into()));
    }
    Ok(AdmittedComplexV1 { d0: d0.clone(), d1: d1.clone() })
}

impl AdmittedComplexV1 {
    /// Construct a verified complex `C⁰ → C¹ → C²`, or return a `CochainRefusal`.
    pub fn new(d0: Matrix, d1: Matrix) -> Result<Self, CochainRefusal> {
        verify_cochain_complex(&d0, Some(&d1))
    }

    /// True if the 1-cochain `ω` satisfies `d₁ ω = 0` (closed 1-cocycle).
    pub fn is_closed(&self, omega: &Matrix) -> bool {
        if verify_cochain_complex(&self.d0, Some(&self.d1)).is_err() { return false; }
        if !omega.is_well_formed() || omega.shape() != (self.d1.cols, 1) {
            return false;
        }
        self.d1.mul(omega).is_zero()
    }

    /// Evaluate the 2-coboundary `d₁ ω`.
    pub fn coboundary_2(&self, omega: &Matrix) -> Result<Matrix, String> {
        verify_cochain_complex(&self.d0, Some(&self.d1)).map_err(|e| format!("invalid complex: {e:?}"))?;
        if !omega.is_well_formed() || omega.shape() != (self.d1.cols, 1) {
            return Err(format!("cochain shape {:?} incompatible with d1 cols {}", omega.shape(), self.d1.cols));
        }
        Ok(self.d1.mul(omega))
    }

    /// Create the linear repair problem for the 0-coboundary `d₀`.
    pub fn repair_problem(&self) -> LinearRepairProblem {
        LinearRepairProblem::new(self.d0.clone())
    }

    /// Classify a 1-cochain across the 2-complex: closed status (`d₁ ω = 0`),
    /// exactness status (`ω ∈ im(d₀)`), and quotient distance `Φ([ω])`.
    pub fn cohomology_classification(&self, omega: &Matrix) -> Result<CohomologyClassification, String> {
        verify_cochain_complex(&self.d0, Some(&self.d1)).map_err(|e| format!("invalid complex: {e:?}"))?;
        if !omega.is_well_formed() || omega.shape() != (self.d0.rows, 1) {
            return Err(format!("cochain shape {:?} incompatible with complex dimension {}", omega.shape(), self.d0.rows));
        }
        let d1_omega = self.d1.mul(omega);
        let is_closed = d1_omega.is_zero();
        let repair_prob = self.repair_problem();
        let exactness = repair_prob.exactness_certificate(omega)?;
        let quotient = repair_prob.quotient_l1_distance(omega)?;

        Ok(CohomologyClassification {
            source_complex: self.clone(),
            source_cochain: omega.clone(),
            is_closed,
            d1_omega,
            exactness,
            quotient,
        })
    }
}

/// Classification of a 1-cochain across a verified complex `C⁰ → C¹ → C²`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CohomologyClassification {
    source_complex: AdmittedComplexV1,
    source_cochain: Matrix,
    /// True if `d₁ ω = 0` (closed cocycle).
    pub is_closed: bool,
    /// The higher coboundary evaluation `d₁ ω`.
    pub d1_omega: Matrix,
    /// Exactness certificate against `im(d₀)`.
    pub exactness: ExactnessCertificate,
    /// Quotient distance certificate `Φ([ω]) = min_α ‖ω − d₀ α‖₁`.
    pub quotient: QuotientDistanceCertificate,
}

impl CohomologyClassification {
    /// Recompute all fields from the bound maps and cochain before issuing a certificate.
    pub fn verify(&self) -> bool {
        self.source_complex.cohomology_classification(&self.source_cochain).ok().as_ref() == Some(self)
    }
    /// True if `ω` represents a non-trivial cohomology class in `H¹ = ker(d₁) / im(d₀)`:
    /// closed (`d₁ ω = 0`), non-bounding (`ω ∉ im(d₀)`), and strictly positive quotient distance.
    pub fn is_nontrivial_cohomology_class(&self) -> bool {
        self.verify() && self.is_closed && !self.exactness.is_exact_coboundary && self.quotient.distance > Rational::ZERO
    }

    /// Certificate for the recomputed cohomology classification.
    pub fn certificate(&self) -> Option<Certificate> {
        if !self.verify() { return None; }
        if self.is_nontrivial_cohomology_class() {
            Some(Certificate::Obstruction {
                proof: ProofId(format!(
                    "cohomology class [omega] with Phi = {} certified by d1 omega = 0 and separator v^T d0 = 0",
                    self.quotient.distance
                )),
            })
        } else if self.exactness.is_exact_coboundary {
            self.exactness.certificate()
        } else {
            None
        }
    }
}

/// Construct the 2-edge bigon 2-complex: `d₀ = [[1], [1]]`, `d₁ = [[1, -1]]`.
///
/// `d₁ · d₀ = 0` holds for every 0-cochain `s`.
/// Here `d₁ ω = ω₁ - ω₂` and `Φ([ω]) = |ω₁ - ω₂|`; for `ω = (1, -1)ᵀ` both equal `2`,
/// demonstrating that filling the 2-cell directly detects the circulation obstruction.
pub fn bigon_2complex() -> Result<AdmittedComplexV1, CochainRefusal> {
    let d0 = Matrix::from_i128(&[&[1], &[1]]);
    let d1 = Matrix::from_i128(&[&[1, -1]]);
    AdmittedComplexV1::new(d0, d1)
}

/// Construct a finite algebraic 2-complex where `H¹ = ker(d₁) / im(d₀)` is non-trivial.
///
/// The legacy function name carries no minimality or topological-realization theorem.
/// This is a declared complex of ranks `(1, 3, 1)`, not the three-patch section defect.
/// `d₀ = [[1], [1], [0]]`, `d₁ = [[0, 0, 1]]`.
/// Here:
/// - `d₁ · d₀ = 0` holds for all 0-cochains.
/// - The test cochain `ω = (1, -1, 0)ᵀ` is closed: `d₁ ω = 0`.
/// - `ω` is non-bounding: `ω ∉ im(d₀)`, with quotient distance `Φ([ω]) = 2`.
pub fn minimal_nontrivial_3patch_2complex() -> Result<AdmittedComplexV1, CochainRefusal> {
    let d0 = Matrix::from_i128(&[&[1], &[1], &[0]]);
    let d1 = Matrix::from_i128(&[&[0, 0, 1]]);
    AdmittedComplexV1::new(d0, d1)
}

/// Construct the 6-edge 3-patch covering cycle of Proposition 7.4.5 filled by a single 2-cell `σ`.
///
/// `d₀ : ℝ⁶ → ℝ⁶`, `d₁ = [[1, -1, 1, -1, 1, -1]]`.
/// Satisfies `d₁ · d₀ = 0` for all 0-cochains (alternating cancellation around the 6-cycle).
pub fn three_patch_cycle_2complex() -> Result<AdmittedComplexV1, CochainRefusal> {
    let d0 = Matrix::from_i128(&[
        &[-1, 0, 0, 1, 0, 0], // e1: u1 - x12
        &[-1, 0, 0, 0, 1, 0], // e2: u2 - x12
        &[0, -1, 0, 0, 1, 0], // e3: u2 - x23
        &[0, -1, 0, 0, 0, 1], // e4: u3 - x23
        &[0, 0, -1, 0, 0, 1], // e5: u3 - x31
        &[0, 0, -1, 1, 0, 0], // e6: u1 - x31
    ]);
    let d1 = Matrix::from_i128(&[&[1, -1, 1, -1, 1, -1]]);
    AdmittedComplexV1::new(d0, d1)
}

/// Exact finite linear repair problem `d₀ : V⁰ → V¹`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LinearRepairProblem {
    /// `d₀`.
    pub d0: Matrix,
}

fn independent_column_indices(m: &Matrix, rank: usize) -> Result<Vec<usize>, String> {
    combinations(m.cols, rank)
        .into_iter()
        .find(|idx| m.columns(idx).rank() == rank)
        .ok_or_else(|| "matrix rank has no matching independent-column witness".to_string())
}

/// Enumerate vertices of the residual hyperplane arrangement: the minimum
/// of `‖ω − d₀α‖₁` is attained where `rank(d₀)` residual coordinates vanish.
fn primal_vertex(d0: &Matrix, omega: &Matrix) -> Result<(Matrix, Matrix, Rational), String> {
    let rank = d0.rank();
    if rank == 0 {
        return Ok((Matrix::zeros(d0.cols, 1), omega.clone(), omega.l1_norm()));
    }
    let basis = independent_column_indices(d0, rank)?;
    let reduced = d0.columns(&basis);
    let all_cols: Vec<usize> = (0..rank).collect();
    let mut best: Option<(Rational, Matrix, Matrix)> = None;
    for rows in combinations(d0.rows, rank) {
        let square = reduced.extract(&rows, &all_cols);
        if square.rank() != rank {
            continue;
        }
        let target = omega.extract(&rows, &[0]);
        let inv = square.inverse().ok_or("square vertex block is singular despite full rank")?;
        let w = inv.mul(&target);
        let mut candidate = Matrix::zeros(d0.cols, 1);
        for (local, &col) in basis.iter().enumerate() {
            candidate.set(col, 0, w.get(local, 0));
        }
        let residual = omega.sub(&d0.mul(&candidate));
        let distance = residual.l1_norm();
        if best.as_ref().is_none_or(|b| distance < b.0) {
            best = Some((distance, candidate, residual));
        }
    }
    best.map(|(d, c, r)| (c, r, d)).ok_or_else(|| "no primal l1 vertex found despite positive matrix rank".to_string())
}

/// Enumerate vertices of `ker(d₀ᵀ) ∩ [−1, 1]^m`: the dual optimum
/// `max { yᵀω : d₀ᵀy = 0, ‖y‖_∞ ≤ 1 }`.
fn dual_vertex(d0: &Matrix, omega: &Matrix) -> Result<(Matrix, Rational), String> {
    let m = d0.rows;
    let rank = d0.rank();
    let t = d0.transpose();
    if rank == 0 {
        let w = Matrix::column(&omega.data.iter().map(|v| q(v.signum())).collect::<Vec<_>>());
        let p = w.transpose().mul(omega).get(0, 0);
        return Ok((w, p));
    }
    if rank == m {
        return Ok((Matrix::zeros(m, 1), Rational::ZERO));
    }
    let mut best: Option<(Rational, Matrix)> = None;
    for free in combinations(m, rank) {
        let free_matrix = t.columns(&free);
        if free_matrix.rank() != rank {
            continue;
        }
        let fixed: Vec<usize> = (0..m).filter(|i| !free.contains(i)).collect();
        let fixed_matrix = t.columns(&fixed);
        let n_fixed = fixed.len();
        let vertex_count = 1u64.checked_shl(u32::try_from(n_fixed).map_err(|_| "dual vertex count exceeds u64")?)
            .ok_or("dual vertex count exceeds u64")?;
        for mask in 0..vertex_count {
            let signs: Vec<Rational> = (0..n_fixed).map(|k| if (mask >> k) & 1 == 0 { q(-1) } else { q(1) }).collect();
            let rhs = fixed_matrix.mul(&Matrix::column(&signs)).scale(q(-1));
            let Some((free_vector, parameters)) = free_matrix.solve(&rhs) else { continue };
            if parameters != 0 || free_vector.data.iter().any(|v| v.abs() > Rational::ONE) {
                continue;
            }
            let mut candidate = Matrix::zeros(m, 1);
            for (k, &i) in free.iter().enumerate() {
                candidate.set(i, 0, free_vector.get(k, 0));
            }
            for (k, &i) in fixed.iter().enumerate() {
                candidate.set(i, 0, signs[k]);
            }
            let pairing = candidate.transpose().mul(omega).get(0, 0);
            if best.as_ref().is_none_or(|b| pairing > b.0) {
                best = Some((pairing, candidate));
            }
        }
    }
    best.map(|(p, c)| (c, p)).ok_or_else(|| "no dual l1 vertex found".to_string())
}

impl LinearRepairProblem {
    /// A repair problem with the given `d₀`.
    pub fn new(d0: Matrix) -> LinearRepairProblem {
        LinearRepairProblem { d0 }
    }

    /// Either a repair witness or a separating witness, rechecked.
    pub fn exactness_certificate(&self, omega: &Matrix) -> Result<ExactnessCertificate, String> {
        if !self.d0.is_well_formed() || !omega.is_well_formed() || omega.shape() != (self.d0.rows, 1) {
            return Err(format!("cochain has shape {:?}, expected {:?}", omega.shape(), (self.d0.rows, 1)));
        }
        let cert = if self.d0.rank() == self.d0.row_join(omega).rank() {
            let (witness, _free) = self.d0.solve(omega).ok_or("rank test passed but the solve failed")?;
            ExactnessCertificate {
                is_exact_coboundary: true,
                cochain: omega.clone(),
                repair_map: self.d0.clone(),
                witness: Some(witness),
                separating_left_kernel_vector: None,
                separating_pairing: None,
            }
        } else {
            let separator = self
                .d0
                .transpose()
                .nullspace()
                .into_iter()
                .find(|v| !v.transpose().mul(omega).get(0, 0).is_zero())
                .ok_or("no separating left-kernel vector despite a rank gap")?;
            let pairing = separator.transpose().mul(omega).get(0, 0);
            ExactnessCertificate {
                is_exact_coboundary: false,
                cochain: omega.clone(),
                repair_map: self.d0.clone(),
                witness: None,
                separating_left_kernel_vector: Some(separator),
                separating_pairing: Some(pairing),
            }
        };
        if !cert.verify() {
            return Err("internal exactness certificate failed self-recheck".into());
        }
        Ok(cert)
    }

    /// The rational `ℓ¹` distance by primal and dual vertex enumeration.
    pub fn quotient_l1_distance(&self, omega: &Matrix) -> Result<QuotientDistanceCertificate, String> {
        if !self.d0.is_well_formed() || !omega.is_well_formed() || omega.shape() != (self.d0.rows, 1) {
            return Err(format!("cochain has shape {:?}, expected {:?}", omega.shape(), (self.d0.rows, 1)));
        }
        let (repair_witness, residual, optimum) = primal_vertex(&self.d0, omega)?;
        let (dual_witness, dual_pairing) = dual_vertex(&self.d0, omega)?;
        if dual_pairing != optimum {
            return Err(format!("primal and dual quotient optima disagree: {optimum} vs {dual_pairing}"));
        }
        let cert = QuotientDistanceCertificate {
            distance: optimum,
            repair_witness,
            residual,
            cochain: omega.clone(),
            dual_witness,
            dual_pairing,
            repair_map: self.d0.clone(),
        };
        if !cert.verify() {
            return Err("internal quotient certificate failed self-recheck".into());
        }
        Ok(cert)
    }
}

/// The paper's receipt presentation: edges `e1, e2`, both maps `[[1]]`.
pub fn receipt_presentation() -> ObservationPresentation {
    let maps = BTreeMap::from([
        ("e1".to_string(), ObservationMap { edge_id: "e1".into(), matrix: Matrix::eye(1) }),
        ("e2".to_string(), ObservationMap { edge_id: "e2".into(), matrix: Matrix::eye(1) }),
    ]);
    ObservationPresentation::new(vec!["e1".into(), "e2".into()], maps).expect("valid fixture")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::certificate::CertKind;

    /// A2/A3/D8/G1: induced `[2,3]`; `[2,2]` exact with witness `[2]`;
    /// `[2,3]` obstructed with separator `[-1,1]`, pairing 1; quotient
    /// distance 1 with dual witness `[-1,1]`, pairing 1.
    #[test]
    fn the_receipt_pipeline_reproduces_every_witness() {
        let p = receipt_presentation();
        let residuals = BTreeMap::from([("e1".to_string(), Matrix::column_i128(&[2])), ("e2".to_string(), Matrix::column_i128(&[3]))]);
        let field = p.induce_field(&residuals).unwrap();
        assert_eq!(field.as_vector().to_string(), "[['2'], ['3']]");
        let problem = LinearRepairProblem::new(Matrix::from_i128(&[&[1], &[1]]));
        let exact = problem.exactness_certificate(&Matrix::column_i128(&[2, 2])).unwrap();
        assert!(exact.is_exact_coboundary && exact.verify());
        assert_eq!(exact.witness.as_ref().unwrap().to_string(), "[['2']]");
        assert_eq!(exact.certificate().expect("verified fixture").kind(), CertKind::Witness);
        let obstructed = problem.exactness_certificate(&field.as_vector()).unwrap();
        assert!(!obstructed.is_exact_coboundary && obstructed.verify());
        assert_eq!(obstructed.separating_left_kernel_vector.as_ref().unwrap().to_string(), "[['-1'], ['1']]");
        assert_eq!(obstructed.separating_pairing, Some(q(1)));
        assert_eq!(obstructed.certificate().expect("verified fixture").kind(), CertKind::Obstruction);
        let quotient = problem.quotient_l1_distance(&field.as_vector()).unwrap();
        assert!(quotient.verify());
        assert_eq!(quotient.distance, q(1));
        assert_eq!(quotient.dual_witness.to_string(), "[['-1'], ['1']]");
        assert_eq!(quotient.dual_pairing, q(1));
        assert_eq!(quotient.repair_witness.to_string(), "[['2']]");
        assert_eq!(quotient.certificate().expect("verified fixture").kind(), CertKind::Witness);
        // Φ ≤ I: the quotient mass never exceeds the raw tally.
        assert!(quotient.distance <= field.as_vector().l1_norm());
        // An exact cochain has Φ = 0.
        assert_eq!(problem.quotient_l1_distance(&Matrix::column_i128(&[2, 2])).unwrap().distance, Rational::ZERO);
    }

    /// B4/G2: no `d₁` was supplied, so nothing is certified about it.
    #[test]
    fn a_missing_higher_differential_is_refused_not_invented() {
        let d0 = Matrix::from_i128(&[&[1], &[1]]);
        assert!(matches!(verify_cochain_complex(&d0, None), Err(CochainRefusal::HigherDifferentialUnavailable(_))));
        let d1 = Matrix::from_i128(&[&[1, -1]]);
        assert!(verify_cochain_complex(&d0, Some(&d1)).is_ok());
        let bad = Matrix::from_i128(&[&[1, 1]]);
        assert!(matches!(verify_cochain_complex(&d0, Some(&bad)), Err(CochainRefusal::ComplexConditionFailed(_))));
    }

    #[test]
    fn the_rank_zero_and_full_rank_dual_branches() {
        let zero = LinearRepairProblem::new(Matrix::zeros(2, 1));
        let c = zero.quotient_l1_distance(&Matrix::column_i128(&[3, -4])).unwrap();
        assert_eq!(c.distance, q(7));
        assert_eq!(c.dual_witness, Matrix::column_i128(&[1, -1]));
        let full = LinearRepairProblem::new(Matrix::eye(2));
        let c = full.quotient_l1_distance(&Matrix::column_i128(&[3, -4])).unwrap();
        assert_eq!(c.distance, Rational::ZERO);
    }

    #[test]
    fn bigon_2complex_verifies_d1_d0_zero_and_circulation_defect() {
        let complex = bigon_2complex().expect("valid 2-complex");
        // d1 * d0 = 0
        assert!(complex.d1.mul(&complex.d0).is_zero());
        for alpha in [-5, 0, 7] {
            let s = Matrix::column_i128(&[alpha]);
            let d0_s = complex.d0.mul(&s);
            assert!(complex.d1.mul(&d0_s).is_zero());
        }
        // Test cochain omega = (1, -1)
        let omega = Matrix::column_i128(&[1, -1]);
        let classification = complex.cohomology_classification(&omega).unwrap();
        // Not closed on this filled bigon: d1 omega = 2 = Phi([omega])
        assert!(!classification.is_closed);
        assert_eq!(classification.d1_omega, Matrix::column_i128(&[2]));
        assert!(!classification.exactness.is_exact_coboundary);
        assert_eq!(classification.quotient.distance, q(2));
        assert_eq!(classification.quotient.dual_witness, Matrix::column_i128(&[1, -1]));
    }

    #[test]
    fn minimal_3patch_2complex_verifies_closed_and_nonbounding() {
        let complex = minimal_nontrivial_3patch_2complex().expect("valid 2-complex");
        // d1 * d0 = 0
        assert!(complex.d1.mul(&complex.d0).is_zero());
        for alpha in [-10, 0, 3, 42] {
            let s = Matrix::column_i128(&[alpha]);
            let d0_s = complex.d0.mul(&s);
            assert!(complex.d1.mul(&d0_s).is_zero());
        }
        // Test cochain omega = (1, -1, 0)
        let omega = Matrix::column_i128(&[1, -1, 0]);
        let classification = complex.cohomology_classification(&omega).unwrap();
        // 1. Closed: d1 omega = 0
        assert!(classification.is_closed);
        assert!(classification.d1_omega.is_zero());
        assert!(complex.is_closed(&omega));
        // 2. Non-bounding: omega not in im(d0)
        assert!(!classification.exactness.is_exact_coboundary);
        assert_eq!(classification.exactness.separating_left_kernel_vector.as_ref().unwrap(), &Matrix::column_i128(&[-1, 1, 0]));
        assert_eq!(classification.exactness.separating_pairing, Some(q(-2)));
        // 3. Quotient distance Phi([omega]) = 2
        assert_eq!(classification.quotient.distance, q(2));
        assert_eq!(omega.sub(&complex.d0.mul(&classification.quotient.repair_witness)).l1_norm(), q(2));
        // 4. Non-trivial cohomology class certified
        assert!(classification.is_nontrivial_cohomology_class());
        assert_eq!(classification.certificate().expect("obstruction certificate").kind(), CertKind::Obstruction);
    }

    #[test]
    fn three_patch_cycle_2complex_satisfies_complex_condition() {
        let complex = three_patch_cycle_2complex().expect("valid 2-complex");
        // d1 * d0 = 0 (shape 1x6)
        assert_eq!(complex.d1.shape(), (1, 6));
        assert_eq!(complex.d0.shape(), (6, 6));
        assert!(complex.d1.mul(&complex.d0).is_zero());

        // For multiple distinct sections across C0 = R^6, d1(d0 s) = 0
        let test_sections = [
            Matrix::column_i128(&[1, 2, 3, 4, 5, 6]),
            Matrix::column_i128(&[-3, 0, 5, -1, 2, 8]),
            Matrix::column_i128(&[10, -20, 30, -40, 50, -60]),
        ];
        for s in &test_sections {
            let d0_s = complex.d0.mul(s);
            assert!(complex.d1.mul(&d0_s).is_zero());
        }
    }
}
