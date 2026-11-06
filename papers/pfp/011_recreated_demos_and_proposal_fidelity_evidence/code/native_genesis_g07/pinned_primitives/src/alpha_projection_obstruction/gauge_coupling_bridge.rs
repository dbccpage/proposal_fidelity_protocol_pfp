//! Exact finite matrix diagnostics for a declared corner-based curvature polynomial.
//! This discretization supplies no gauge-covariance or topological-class theorem.
//! In a nonabelian model, d0 chi is only a linear gauge ansatz, not a group pure gauge.
//!
//! `AuthorityEffect: None.`
//!
//! Connects an admitted 2-complex `C⁰ → C¹ → C²` to discrete gauge-coupling solvers:
//! - Lie-algebra-valued cochains and connections `A ∈ C¹ ⊗ 𝔤`
//! - Discrete 2-form curvature `F = d₁ A + [A, A]`
//! - Verification of pure gauge configurations `A = d₀ χ`
//! - Verification of group-valued parallel transports `U_{uv} = g_u⁻¹ g_v` and Wilson loop holonomies
//! - Verification of multi-patch covering cycles and transition cocycles

use super::cochain_presentation::AdmittedComplexV1;
use super::matrix::Matrix;
use super::rational::Rational;
use crate::certificate::{Certificate, CheckId, ObjectId, ProofId};

fn validate_matrices(values: &[Matrix], orthogonal: bool) -> Result<(), String> {
    let Some(first) = values.first() else {
        return Err("empty matrix family".into());
    };
    let shape = first.shape();
    if shape.0 == 0 || shape.0 != shape.1 {
        return Err("nonempty square matrices required".into());
    }
    for matrix in values {
        if !matrix.is_well_formed() || matrix.shape() != shape {
            return Err("malformed or inconsistent matrix shape".into());
        }
        if orthogonal && matrix.transpose().mul(matrix) != Matrix::eye(shape.0) {
            return Err("orthogonality premise failed".into());
        }
    }
    Ok(())
}

/// Oriented corner of a 2-cell `σ`, defining the incident boundary edge pair `(e_i, e_j)`
/// used to evaluate the discrete non-abelian commutator term `[A_{e_i}, A_{e_j}]`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CellCorner {
    /// The index of the 2-cell `σ ∈ {0, ..., n₂ - 1}`.
    pub cell_index: usize,
    /// First incident boundary edge index `e_i ∈ {0, ..., n₁ - 1}`.
    pub edge_i: usize,
    /// Second incident boundary edge index `e_j ∈ {0, ..., n₁ - 1}`.
    pub edge_j: usize,
}

/// Exact rational representation of standard 𝖘𝔬(3) Lie algebra generators:
/// `J₁`, `J₂`, `J₃` satisfying `[J₁, J₂] = J₃`, `[J₂, J₃] = J₁`, `[J₃, J₁] = J₂`.
pub fn so3_generators() -> [Matrix; 3] {
    let j1 = Matrix::from_i128(&[&[0, 0, 0], &[0, 0, -1], &[0, 1, 0]]);
    let j2 = Matrix::from_i128(&[&[0, 0, 1], &[0, 0, 0], &[-1, 0, 0]]);
    let j3 = Matrix::from_i128(&[&[0, -1, 0], &[1, 0, 0], &[0, 0, 0]]);
    [j1, j2, j3]
}

/// Real-coordinate basis of a one-dimensional abelian Lie algebra.
/// This is not its complex anti-Hermitian matrix representation.
pub fn u1_generator() -> Matrix {
    Matrix::from_i128(&[&[1]])
}

/// Exact matrix commutator `[X, Y] = X Y − Y X`.
pub fn commutator(x: &Matrix, y: &Matrix) -> Matrix {
    assert_eq!(x.shape(), y.shape(), "matrix shape mismatch in commutator");
    assert_eq!(x.rows, x.cols, "non-square matrix in commutator");
    x.mul(y).sub(&y.mul(x))
}

/// Bridge connecting an admitted 2-complex `C⁰ → C¹ → C²` to discrete gauge-coupling solvers.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GaugeCouplingBridge {
    /// Underlying verified cochain complex.
    complex: AdmittedComplexV1,
    /// Assigned corner edge pairs per 2-cell for non-abelian commutator evaluation.
    cell_corners: Vec<CellCorner>,
}

impl GaugeCouplingBridge {
    /// Construct a verified gauge-coupling bridge.
    pub fn new(
        complex: AdmittedComplexV1,
        cell_corners: Vec<CellCorner>,
    ) -> Result<GaugeCouplingBridge, String> {
        let complex = AdmittedComplexV1::new(complex.d0, complex.d1)
            .map_err(|e| format!("invalid complex: {e:?}"))?;
        if complex.d0.cols == 0 || complex.d0.rows == 0 || complex.d1.rows == 0 {
            return Err(
                "gauge diagnostics require nonempty vertex, edge, and cell carriers".into(),
            );
        }
        let n2 = complex.d1.rows;
        let n1 = complex.d1.cols;
        for corner in &cell_corners {
            if corner.cell_index >= n2 {
                return Err(format!(
                    "corner references cell index {} >= n2 ({})",
                    corner.cell_index, n2
                ));
            }
            if corner.edge_i >= n1 || corner.edge_j >= n1 {
                return Err(format!(
                    "corner references edge indices ({}, {}) >= n1 ({})",
                    corner.edge_i, corner.edge_j, n1
                ));
            }
        }
        Ok(GaugeCouplingBridge {
            complex,
            cell_corners,
        })
    }

    /// Construct pure gauge connection 1-cochains `A = d₀ χ` from vertex parameters `χ`.
    pub fn pure_gauge_connection(&self, chi: &[Matrix]) -> Result<Vec<Matrix>, String> {
        let n0 = self.complex.d0.cols;
        let n1 = self.complex.d0.rows;
        if chi.len() != n0 {
            return Err(format!(
                "expected {} vertex parameters, got {}",
                n0,
                chi.len()
            ));
        }
        validate_matrices(chi, false)?;
        let shape = chi[0].shape();
        if shape.0 != shape.1 {
            return Err("gauge parameters must be square matrices".into());
        }
        for (idx, c) in chi.iter().enumerate() {
            if c.shape() != shape {
                return Err(format!(
                    "inconsistent shape {:?} at vertex {}",
                    c.shape(),
                    idx
                ));
            }
        }
        let mut a = Vec::with_capacity(n1);
        for e in 0..n1 {
            let mut a_e = Matrix::zeros(shape.0, shape.1);
            for (v, chi_v) in chi.iter().enumerate() {
                let coeff = self.complex.d0.get(e, v);
                if !coeff.is_zero() {
                    a_e = a_e.add(&chi_v.scale(coeff));
                }
            }
            a.push(a_e);
        }
        Ok(a)
    }

    /// Evaluate the linear coboundary `d₁ A` across all 2-cells.
    pub fn linear_coboundary_d1(&self, a: &[Matrix]) -> Result<Vec<Matrix>, String> {
        let n1 = self.complex.d1.cols;
        let n2 = self.complex.d1.rows;
        if a.len() != n1 {
            return Err(format!("expected {} edge connections, got {}", n1, a.len()));
        }
        validate_matrices(a, false)?;
        let shape = a[0].shape();
        let mut d1_a = Vec::with_capacity(n2);
        for s in 0..n2 {
            let mut d1_s = Matrix::zeros(shape.0, shape.1);
            for (e, edge_a) in a.iter().enumerate() {
                let coeff = self.complex.d1.get(s, e);
                if !coeff.is_zero() {
                    d1_s = d1_s.add(&edge_a.scale(coeff));
                }
            }
            d1_a.push(d1_s);
        }
        Ok(d1_a)
    }

    /// Evaluate the discrete non-abelian commutator term `[A, A]` across all 2-cells.
    pub fn commutator_curvature(&self, a: &[Matrix]) -> Result<Vec<Matrix>, String> {
        let n1 = self.complex.d1.cols;
        let n2 = self.complex.d1.rows;
        if a.len() != n1 {
            return Err(format!("expected {} edge connections, got {}", n1, a.len()));
        }
        validate_matrices(a, false)?;
        let shape = a[0].shape();
        let mut comm = vec![Matrix::zeros(shape.0, shape.1); n2];
        for corner in &self.cell_corners {
            let term = commutator(&a[corner.edge_i], &a[corner.edge_j]);
            comm[corner.cell_index] = comm[corner.cell_index].add(&term);
        }
        Ok(comm)
    }

    /// Evaluate total discrete 2-form curvature `F = d₁ A + [A, A]`.
    pub fn total_curvature(&self, a: &[Matrix]) -> Result<Vec<Matrix>, String> {
        let d1_a = self.linear_coboundary_d1(a)?;
        let comm = self.commutator_curvature(a)?;
        let mut f = Vec::with_capacity(d1_a.len());
        for (d, c) in d1_a.into_iter().zip(comm) {
            f.push(d.add(&c));
        }
        Ok(f)
    }

    /// Verify whether discrete 2-form curvature `F = d₁ A + [A, A]` vanishes on pure gauge `A = d₀ χ`.
    pub fn verify_pure_gauge(
        &self,
        chi: &[Matrix],
    ) -> Result<PureGaugeCurvatureVerification, String> {
        let a = self.pure_gauge_connection(chi)?;
        let d1_a = self.linear_coboundary_d1(&a)?;
        let d1_a_vanishes = d1_a.iter().all(|m| m.is_zero());
        let comm = self.commutator_curvature(&a)?;
        let commutator_vanishes = comm.iter().all(|m| m.is_zero());
        let f = self.total_curvature(&a)?;
        let total_curvature_vanishes = f.iter().all(|m| m.is_zero());
        let max_norm = f.iter().fold(Rational::ZERO, |acc, m| acc.max(m.l1_norm()));

        // Check whether vertex parameters mutually commute
        let mut is_abelian = true;
        for i in 0..chi.len() {
            for j in (i + 1)..chi.len() {
                if !commutator(&chi[i], &chi[j]).is_zero() {
                    is_abelian = false;
                    break;
                }
            }
            if !is_abelian {
                break;
            }
        }

        Ok(PureGaugeCurvatureVerification {
            source: self.clone(),
            parameters: chi.to_vec(),
            is_abelian,
            d1_a_vanishes,
            commutator_vanishes,
            total_curvature_vanishes,
            curvature_matrices: f,
            max_curvature_norm: max_norm,
        })
    }

    /// Verify group-valued plaquette holonomy `W = ∏ U_e` on pure gauge link variables `U_{uv} = g_u⁻¹ g_v`.
    ///
    /// Orthogonal matrices (`O(n)`) are checked explicitly, so `g⁻¹ = gᵀ`.
    /// The supplied vertex loops need not be a cellular realization of d1.
    pub fn verify_group_holonomy(
        &self,
        g_vertices: &[Matrix],
        plaquette_loops: &[Vec<(usize, usize)>],
    ) -> Result<GroupHolonomyVerification, String> {
        let n0 = self.complex.d0.cols;
        if g_vertices.len() != n0 {
            return Err(format!(
                "expected {} vertex group elements, got {}",
                n0,
                g_vertices.len()
            ));
        }
        validate_matrices(g_vertices, true)?;
        if plaquette_loops.is_empty() {
            return Err("at least one closed loop is required".into());
        }
        let dim = g_vertices[0].rows;
        let mut holonomies = Vec::with_capacity(plaquette_loops.len());
        let mut max_defect = Rational::ZERO;

        for pl in plaquette_loops {
            if pl.is_empty()
                || pl.last().unwrap().1 != pl[0].0
                || pl.windows(2).any(|edges| edges[0].1 != edges[1].0)
            {
                return Err("plaquette must be a nonempty closed contiguous vertex loop".into());
            }
            let mut w = Matrix::eye(dim);
            for &(u, v) in pl {
                if u >= n0 || v >= n0 {
                    return Err(format!("edge ({} -> {}) leaves vertex set {}", u, v, n0));
                }
                // U_{uv} = g_u^T * g_v
                let u_edge = g_vertices[u].transpose().mul(&g_vertices[v]);
                w = w.mul(&u_edge);
            }
            let defect = w.sub(&Matrix::eye(dim)).l1_norm();
            max_defect = max_defect.max(defect);
            holonomies.push(w);
        }

        let is_trivial = max_defect.is_zero();
        Ok(GroupHolonomyVerification {
            source: self.clone(),
            vertices: g_vertices.to_vec(),
            loops: plaquette_loops.to_vec(),
            is_trivial,
            holonomies,
            max_defect_norm: max_defect,
        })
    }

    /// Verify multi-patch transition cycle holonomy `W = g₁₂ g₂₃ g₃₁` across a 3-patch covering.
    pub fn verify_multipatch_transition(
        &self,
        transitions: &[Matrix],
        associated_quotient: Option<Rational>,
    ) -> Result<MultiPatchTransitionVerification, String> {
        if transitions.len() != 3 {
            return Err(format!(
                "expected 3 transition matrices for 3-patch cycle, got {}",
                transitions.len()
            ));
        }
        validate_matrices(transitions, true)?;
        if associated_quotient.is_some_and(|value| value < Rational::ZERO) {
            return Err("reported quotient annotation must be nonnegative".into());
        }
        let dim = transitions[0].rows;
        let product = transitions[0].mul(&transitions[1]).mul(&transitions[2]);
        let defect = product.sub(&Matrix::eye(dim)).l1_norm();
        let is_cocycle_trivial = defect.is_zero();

        Ok(MultiPatchTransitionVerification {
            source: self.clone(),
            transitions: transitions.to_vec(),
            reported_quotient: associated_quotient,
            is_cocycle_trivial,
            transition_product: product,
            transition_defect_norm: defect,
            associated_quotient_distance: associated_quotient,
        })
    }
}

/// Verification result for discrete 2-form curvature `F = d₁ A + [A, A]` on pure gauge `A = d₀ χ`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PureGaugeCurvatureVerification {
    source: GaugeCouplingBridge,
    parameters: Vec<Matrix>,
    /// True if all vertex gauge parameters commute.
    pub is_abelian: bool,
    /// True if the linear coboundary term `d₁ A` vanishes identically.
    pub d1_a_vanishes: bool,
    /// True if the discrete non-abelian commutator term `[A, A]` vanishes.
    pub commutator_vanishes: bool,
    /// True if total discrete 2-form curvature `F = d₁ A + [A, A]` vanishes.
    pub total_curvature_vanishes: bool,
    /// Curvature matrices per 2-cell.
    pub curvature_matrices: Vec<Matrix>,
    /// Maximum `ℓ¹` norm across all curvature matrices.
    pub max_curvature_norm: Rational,
}

impl PureGaugeCurvatureVerification {
    /// Produce a certificate of the verification result.
    pub fn certificate(&self) -> Option<Certificate> {
        if self
            .source
            .verify_pure_gauge(&self.parameters)
            .ok()
            .as_ref()
            != Some(self)
        {
            return None;
        }
        if self.total_curvature_vanishes {
            Some(Certificate::Witness {
                object: ObjectId("discrete 2-form curvature F = d1 A + [A, A]".into()),
                check: CheckId("F vanishes on pure gauge A = d0 chi".into()),
            })
        } else {
            Some(Certificate::Obstruction {
                proof: ProofId(format!(
                    "non-abelian curvature defect with max l1 norm {} (d1 A = 0 but [A, A] != 0)",
                    self.max_curvature_norm
                )),
            })
        }
    }
}

/// Verification result for group-valued plaquette holonomies.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GroupHolonomyVerification {
    source: GaugeCouplingBridge,
    vertices: Vec<Matrix>,
    loops: Vec<Vec<(usize, usize)>>,
    /// True if all plaquette holonomies equal the identity matrix.
    pub is_trivial: bool,
    /// Plaquette holonomy matrices.
    pub holonomies: Vec<Matrix>,
    /// Maximum `ℓ¹` defect norm `‖W − I‖₁`.
    pub max_defect_norm: Rational,
}

impl GroupHolonomyVerification {
    /// Produce a certificate of the verification result.
    pub fn certificate(&self) -> Option<Certificate> {
        if self
            .source
            .verify_group_holonomy(&self.vertices, &self.loops)
            .ok()
            .as_ref()
            != Some(self)
        {
            return None;
        }
        if self.is_trivial {
            Some(Certificate::Witness {
                object: ObjectId("group-valued pure gauge holonomy W = I".into()),
                check: CheckId("verified across all plaquettes".into()),
            })
        } else {
            Some(Certificate::Obstruction {
                proof: ProofId(format!(
                    "non-trivial group holonomy with max defect norm {}",
                    self.max_defect_norm
                )),
            })
        }
    }
}

/// Verification result for multi-patch transition cycle holonomy.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MultiPatchTransitionVerification {
    source: GaugeCouplingBridge,
    transitions: Vec<Matrix>,
    reported_quotient: Option<Rational>,
    /// True if transition product equals identity (`g₁₂ g₂₃ g₃₁ = I`).
    pub is_cocycle_trivial: bool,
    /// Transition product matrix `g₁₂ g₂₃ g₃₁`.
    pub transition_product: Matrix,
    /// Transition defect `ℓ¹` norm `‖g₁₂ g₂₃ g₃₁ − I‖₁`.
    pub transition_defect_norm: Rational,
    /// Caller-supplied, unverified annotation; never included in the certificate.
    pub associated_quotient_distance: Option<Rational>,
}

impl MultiPatchTransitionVerification {
    /// Produce a certificate of the verification result.
    pub fn certificate(&self) -> Option<Certificate> {
        if self
            .source
            .verify_multipatch_transition(&self.transitions, self.reported_quotient)
            .ok()
            .as_ref()
            != Some(self)
        {
            return None;
        }
        if self.is_cocycle_trivial {
            Some(Certificate::Witness {
                object: ObjectId("3-patch transition cycle".into()),
                check: CheckId("cocycle-trivial: g12 g23 g31 = I".into()),
            })
        } else {
            Some(Certificate::Obstruction {
                proof: ProofId(format!(
                    "supplied transition product differs from identity by l1 norm {}; no cohomology identification claimed",
                    self.transition_defect_norm
                )),
            })
        }
    }
}

/// Construct a single filled triangle 2-complex: vertices `{0, 1, 2}`, edges `e₀ = (0→1), e₁ = (1→2), e₂ = (0→2)`.
///
/// `d₀ = [[-1, 1, 0], [0, -1, 1], [-1, 0, 1]]`.
/// `d₁ = [[1, 1, -1]]`.
/// Oriented corner on the 2-cell: `(e₀, e₁)`.
pub fn single_triangle_bridge() -> Result<GaugeCouplingBridge, String> {
    let d0 = Matrix::from_i128(&[&[-1, 1, 0], &[0, -1, 1], &[-1, 0, 1]]);
    let d1 = Matrix::from_i128(&[&[1, 1, -1]]);
    let complex = AdmittedComplexV1::new(d0, d1).map_err(|e| format!("{:?}", e))?;
    let corners = vec![CellCorner {
        cell_index: 0,
        edge_i: 0,
        edge_j: 1,
    }];
    GaugeCouplingBridge::new(complex, corners)
}

#[cfg(test)]
mod tests {
    use super::super::rational::q;
    use super::*;
    use crate::certificate::CertKind;

    #[test]
    fn so3_generators_satisfy_exact_commutation_relations() {
        let [j1, j2, j3] = so3_generators();
        assert_eq!(commutator(&j1, &j2), j3);
        assert_eq!(commutator(&j2, &j3), j1);
        assert_eq!(commutator(&j3, &j1), j2);
    }

    #[test]
    fn abelian_pure_gauge_curvature_vanishes_identically() {
        let bridge = single_triangle_bridge().expect("valid single triangle bridge");
        // 1D abelian gauge parameters at vertices 0, 1, 2
        let chi = [
            Matrix::from_i128(&[&[2]]),
            Matrix::from_i128(&[&[-5]]),
            Matrix::from_i128(&[&[7]]),
        ];
        let verif = bridge.verify_pure_gauge(&chi).expect("verification passes");
        assert!(verif.is_abelian);
        assert!(verif.d1_a_vanishes);
        assert!(verif.commutator_vanishes);
        assert!(verif.total_curvature_vanishes);
        assert_eq!(verif.max_curvature_norm, Rational::ZERO);
        assert_eq!(
            verif.certificate().expect("witness cert").kind(),
            CertKind::Witness
        );
    }

    #[test]
    fn nonabelian_linear_pure_gauge_curvature_does_not_vanish_when_noncommuting() {
        let bridge = single_triangle_bridge().expect("valid single triangle bridge");
        let [j1, j2, _j3] = so3_generators();
        // Non-commuting vertex gauge parameters: chi_0 = 0, chi_1 = J1, chi_2 = J2
        let chi = [Matrix::zeros(3, 3), j1.clone(), j2.clone()];
        let verif = bridge.verify_pure_gauge(&chi).expect("verification passes");
        // 1. Non-abelian parameters do not commute
        assert!(!verif.is_abelian);
        // 2. Linear coboundary d1 A ALWAYS vanishes on pure gauge because d1 * d0 = 0
        assert!(verif.d1_a_vanishes);
        // 3. But discrete commutator [A, A] does NOT vanish
        assert!(!verif.commutator_vanishes);
        // 4. Total curvature F = d1 A + [A, A] = 0 + [A, A] != 0
        assert!(!verif.total_curvature_vanishes);
        assert!(verif.max_curvature_norm > Rational::ZERO);
        // The corner evaluates [A(e0), A(e1)] = [J1, J2 - J1] = [J1, J2] = J3
        let [_j1, _j2, j3] = so3_generators();
        assert_eq!(verif.curvature_matrices[0], j3);
        assert_eq!(
            verif.certificate().expect("obstruction cert").kind(),
            CertKind::Obstruction
        );
    }

    #[test]
    fn nonabelian_linear_pure_gauge_curvature_vanishes_in_commuting_cartan_subalgebra() {
        let bridge = single_triangle_bridge().expect("valid single triangle bridge");
        let [_j1, _j2, j3] = so3_generators();
        // Commuting vertex parameters in the span of J3
        let chi = [j3.scale(q(1)), j3.scale(q(-3)), j3.scale(q(5))];
        let verif = bridge.verify_pure_gauge(&chi).expect("verification passes");
        assert!(verif.is_abelian);
        assert!(verif.d1_a_vanishes);
        assert!(verif.commutator_vanishes);
        assert!(verif.total_curvature_vanishes);
        assert_eq!(verif.max_curvature_norm, Rational::ZERO);
    }

    #[test]
    fn group_valued_pure_gauge_plaquette_holonomy_vanishes_strictly() {
        let bridge = single_triangle_bridge().expect("valid single triangle bridge");
        // Orthogonal matrices in SO(3) at vertices: 180-degree rotations about axes
        let r1 = Matrix::from_i128(&[&[1, 0, 0], &[0, -1, 0], &[0, 0, -1]]);
        let r2 = Matrix::from_i128(&[&[-1, 0, 0], &[0, 1, 0], &[0, 0, -1]]);
        let r3 = Matrix::from_i128(&[&[-1, 0, 0], &[0, -1, 0], &[0, 0, 1]]);
        let g_verts = [r1, r2, r3];
        // Triangle loop: 0 -> 1 -> 2 -> 0
        let loops = vec![vec![(0, 1), (1, 2), (2, 0)]];
        let hol_verif = bridge
            .verify_group_holonomy(&g_verts, &loops)
            .expect("holonomy check passes");
        assert!(hol_verif.is_trivial);
        assert_eq!(hol_verif.max_defect_norm, Rational::ZERO);
        assert_eq!(hol_verif.holonomies[0], Matrix::eye(3));
        assert_eq!(
            hol_verif.certificate().expect("witness cert").kind(),
            CertKind::Witness
        );
    }

    #[test]
    fn multipatch_transition_cycle_detects_quotient_obstruction() {
        let bridge = single_triangle_bridge().expect("valid single triangle bridge");
        let eye = Matrix::eye(3);
        // Trivial transition cocycle: g12 = I, g23 = I, g31 = I -> W = I
        let trivial_transitions = [eye.clone(), eye.clone(), eye.clone()];
        let triv_res = bridge
            .verify_multipatch_transition(&trivial_transitions, Some(Rational::ZERO))
            .unwrap();
        assert!(triv_res.is_cocycle_trivial);
        assert_eq!(triv_res.transition_defect_norm, Rational::ZERO);

        // Obstructed transition cycle: g31 carries a twist R != I
        let r_twist = Matrix::from_i128(&[&[-1, 0, 0], &[0, -1, 0], &[0, 0, 1]]);
        let obstructed_transitions = [eye.clone(), eye, r_twist];
        let obs_res = bridge
            .verify_multipatch_transition(&obstructed_transitions, Some(q(2)))
            .unwrap();
        assert!(!obs_res.is_cocycle_trivial);
        assert_eq!(obs_res.transition_defect_norm, q(4)); // ||diag(-1,-1,1) - diag(1,1,1)||_1 = 2 + 2 + 0 = 4
        assert_eq!(
            obs_res.certificate().expect("obstruction cert").kind(),
            CertKind::Obstruction
        );
    }
}
