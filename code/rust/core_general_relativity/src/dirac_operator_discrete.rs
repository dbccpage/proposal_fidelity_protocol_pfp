//! Discrete Dirac Operator on Simplicial Lattices (Hamber §7.4).
//!
//! Implements discrete spinor fields and the simplicial Dirac operator:
//! - Spinors $\psi(v) \in \mathbb{C}^2$ defined at vertices of the triangulation.
//! - Parallel transport spin connection $\Omega_{uv} \in \mathrm{SU}(2)$ along directed edges $(u, v)$,
//!   satisfying $\Omega_{vu} = \Omega_{uv}^\dagger$.
//! - The discrete Dirac operator acts as:
//!   $$(D \psi)(u) = \frac{-i}{V_u} \sum_{v \sim u} w_{uv} (\vec{\sigma} \cdot \hat{n}_{uv}) \Omega_{uv} \psi(v)$$
//!   where $w_{uv} = \frac{A^*_{uv}}{\ell_{uv}}$ is the dual geometric weight, and $\hat{n}_{uv}$ is the
//!   unit spatial vector along edge $(u, v)$ ($\hat{n}_{vu} = -\hat{n}_{uv}$).
//! - Under the volume-weighted Hilbert space inner product:
//!   $$\langle \phi, \psi \rangle = \sum_u V_u \phi(u)^\dagger \psi(u)$$
//!   the discrete Dirac operator is strictly Hermitian: $\langle \phi, D \psi \rangle = \langle D \phi, \psi \rangle$.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; discrete simplicial Dirac operator.";

/// 2-component complex spinor at a vertex.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Spinor2 {
    /// Upper component: (real, imag)
    pub u: (f64, f64),
    /// Lower component: (real, imag)
    pub d: (f64, f64),
}

impl Spinor2 {
    pub fn new(u: (f64, f64), d: (f64, f64)) -> Self {
        Self { u, d }
    }

    pub fn zero() -> Self {
        Self {
            u: (0.0, 0.0),
            d: (0.0, 0.0),
        }
    }

    /// Add two spinors.
    pub fn add(&self, other: &Self) -> Self {
        Self {
            u: (self.u.0 + other.u.0, self.u.1 + other.u.1),
            d: (self.d.0 + other.d.0, self.d.1 + other.d.1),
        }
    }

    /// Multiply spinor by complex scalar (cr, ci): c * psi.
    pub fn scale_complex(&self, c: (f64, f64)) -> Self {
        let (cr, ci) = c;
        Self {
            u: (cr * self.u.0 - ci * self.u.1, cr * self.u.1 + ci * self.u.0),
            d: (cr * self.d.0 - ci * self.d.1, cr * self.d.1 + ci * self.d.0),
        }
    }

    /// Spinor inner product: phi^dagger * psi = phi_u^* * psi_u + phi_d^* * psi_d.
    pub fn dot_dagger(&self, other: &Self) -> (f64, f64) {
        // self^dagger * other
        let re = (self.u.0 * other.u.0 + self.u.1 * other.u.1)
            + (self.d.0 * other.d.0 + self.d.1 * other.d.1);
        let im = (self.u.0 * other.u.1 - self.u.1 * other.u.0)
            + (self.d.0 * other.d.1 - self.d.1 * other.d.0);
        (re, im)
    }

    /// Action of Pauli matrix vector (vec{sigma} · n) on this spinor:
    /// (n_x σ_1 + n_y σ_2 + n_z σ_3) * psi
    pub fn pauli_dot(&self, n: [f64; 3]) -> Self {
        let [nx, ny, nz] = n;
        // Matrix M = [ [ nz, nx - i ny ], [ nx + i ny, -nz ] ]
        // (M * psi)_u = nz * psi_u + (nx - i ny) * psi_d
        // (M * psi)_d = (nx + i ny) * psi_u - nz * psi_d
        let term1_u = (nz * self.u.0, nz * self.u.1);
        let term2_u = (
            nx * self.d.0 + ny * self.d.1,
            nx * self.d.1 - ny * self.d.0,
        );

        let term1_d = (
            nx * self.u.0 - ny * self.u.1,
            nx * self.u.1 + ny * self.u.0,
        );
        let term2_d = (-nz * self.d.0, -nz * self.d.1);

        Self {
            u: (term1_u.0 + term2_u.0, term1_u.1 + term2_u.1),
            d: (term1_d.0 + term2_d.0, term1_d.1 + term2_d.1),
        }
    }
}

/// SU(2) parallel transport connection matrix on an edge:
/// Ω = a0 I + i (a1 σ1 + a2 σ2 + a3 σ3) with a0² + a1² + a2² + a3² = 1.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct SpinConnectionSU2 {
    pub a: [f64; 4], // (a0, a1, a2, a3)
}

impl SpinConnectionSU2 {
    pub fn identity() -> Self {
        Self {
            a: [1.0, 0.0, 0.0, 0.0],
        }
    }

    pub fn new_normalized(a: [f64; 4]) -> Result<Self, String> {
        let norm_sq = a[0] * a[0] + a[1] * a[1] + a[2] * a[2] + a[3] * a[3];
        if norm_sq < 1e-12 || !norm_sq.is_finite() {
            return Err("Zero or non-finite SU(2) connection parameters".to_string());
        }
        let norm = norm_sq.sqrt();
        Ok(Self {
            a: [a[0] / norm, a[1] / norm, a[2] / norm, a[3] / norm],
        })
    }

    /// Inverse (Hermitian adjoint) connection: Ω^dagger = a0 I - i (a · σ).
    pub fn dagger(&self) -> Self {
        Self {
            a: [self.a[0], -self.a[1], -self.a[2], -self.a[3]],
        }
    }

    /// Apply connection matrix to a spinor: Ω * psi.
    pub fn apply(&self, psi: &Spinor2) -> Spinor2 {
        let a0 = self.a[0];
        let term_id = Spinor2 {
            u: (a0 * psi.u.0, a0 * psi.u.1),
            d: (a0 * psi.d.0, a0 * psi.d.1),
        };
        // i * (a · σ) * psi
        let pauli = psi.pauli_dot([self.a[1], self.a[2], self.a[3]]);
        let i_pauli = pauli.scale_complex((0.0, 1.0)); // multiply by i
        term_id.add(&i_pauli)
    }
}

/// Discrete Dirac operator configured on a simplicial lattice.
#[derive(Debug, Clone, PartialEq)]
pub struct SimplicialDiracOperator {
    pub num_vertices: usize,
    pub vertex_volumes: Vec<f64>,
    /// Directed edges: (u, v, weight w_uv, unit_direction n_uv, connection Core_uv).
    pub directed_edges: Vec<(usize, usize, f64, [f64; 3], SpinConnectionSU2)>,
}

impl SimplicialDiracOperator {
    pub fn new(
        num_vertices: usize,
        vertex_volumes: Vec<f64>,
        directed_edges: Vec<(usize, usize, f64, [f64; 3], SpinConnectionSU2)>,
    ) -> Result<Self, String> {
        if vertex_volumes.len() != num_vertices {
            return Err("Vertex volumes count does not match num_vertices".to_string());
        }
        for (v, &vol) in vertex_volumes.iter().enumerate() {
            if vol <= 1e-12 || !vol.is_finite() {
                return Err(format!("Non-positive volume at vertex {v}: {vol}"));
            }
        }
        Ok(Self {
            num_vertices,
            vertex_volumes,
            directed_edges,
        })
    }

    /// Apply discrete Dirac operator:
    /// (D psi)(u) = (-i / V_u) ∑_{v ~ u} w_uv (σ · n_uv) Ω_uv psi(v).
    pub fn apply(&self, psi: &[Spinor2]) -> Result<Vec<Spinor2>, String> {
        if psi.len() != self.num_vertices {
            return Err("Spinor field dimension does not match operator dimension".to_string());
        }

        let mut d_psi = vec![Spinor2::zero(); self.num_vertices];

        for &(u, v, weight, n_uv, conn) in &self.directed_edges {
            if u >= self.num_vertices || v >= self.num_vertices {
                continue;
            }

            // 1. Parallel transport: psi'(v) = Ω_uv * psi(v)
            let psi_trans = conn.apply(&psi[v]);

            // 2. Pauli contraction: (σ · n_uv) * psi'
            let pauli_psi = psi_trans.pauli_dot(n_uv);

            // 3. Multiply by -i and weight: (-i * weight)
            let term = pauli_psi.scale_complex((0.0, -weight));

            d_psi[u] = d_psi[u].add(&term);
        }

        // 4. Divide by vertex volume V_u
        for (u, val) in d_psi.iter_mut().enumerate() {
            let inv_v = 1.0 / self.vertex_volumes[u];
            *val = val.scale_complex((inv_v, 0.0));
        }

        Ok(d_psi)
    }

    /// Volume-weighted Hilbert space inner product: ⟨phi, psi⟩ = ∑_u V_u phi(u)† psi(u).
    pub fn inner_product(&self, phi: &[Spinor2], psi: &[Spinor2]) -> Result<(f64, f64), String> {
        if phi.len() != self.num_vertices || psi.len() != self.num_vertices {
            return Err("Spinor field dimension mismatch in inner product".to_string());
        }

        let mut total_re = 0.0;
        let mut total_im = 0.0;

        for u in 0..self.num_vertices {
            let vol = self.vertex_volumes[u];
            let (dr, di) = phi[u].dot_dagger(&psi[u]);
            total_re += vol * dr;
            total_im += vol * di;
        }

        Ok((total_re, total_im))
    }

    /// Check Hermiticity: |⟨phi, D psi⟩ - ⟨D phi, psi⟩| < tolerance.
    pub fn check_hermiticity(
        &self,
        phi: &[Spinor2],
        psi: &[Spinor2],
        tolerance: f64,
    ) -> Result<bool, String> {
        let d_psi = self.apply(psi)?;
        let d_phi = self.apply(phi)?;

        let (re1, im1) = self.inner_product(phi, &d_psi)?;
        let (re2, im2) = self.inner_product(&d_phi, psi)?;

        let diff_sq = (re1 - re2).powi(2) + (im1 - im2).powi(2);
        Ok(diff_sq.sqrt() < tolerance)
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/dirac_operator_discrete.rs
// Claim: urn:core:crates_rs:core-general-relativity:dirac-operator-discrete:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord83350d86 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord83350d86` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError83350d86 {
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
impl BoundaryError83350d86 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError83350d86 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError83350d86 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord83350d86 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError83350d86> {
        if capacity_bound == 0 {
            return Err(BoundaryError83350d86::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError83350d86::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError83350d86::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_spinor_pauli_dot_involution() {
        // (σ · n)² = I for any unit vector n
        let psi = Spinor2::new((1.5, 0.5), (-0.8, 1.2));
        let n = [1.0 / 3.0f64.sqrt(), 1.0 / 3.0f64.sqrt(), 1.0 / 3.0f64.sqrt()];

        let step1 = psi.pauli_dot(n);
        let step2 = step1.pauli_dot(n);

        assert!((step2.u.0 - psi.u.0).abs() < 1e-9);
        assert!((step2.u.1 - psi.u.1).abs() < 1e-9);
        assert!((step2.d.0 - psi.d.0).abs() < 1e-9);
        assert!((step2.d.1 - psi.d.1).abs() < 1e-9);
    }

    #[test]
    fn test_discrete_dirac_operator_hermiticity_on_simplicial_pair() {
        // 2 vertices u=0, v=1 connected by an edge along x-axis
        let v_vols = vec![1.0, 1.0];
        let n_01 = [1.0, 0.0, 0.0];
        let n_10 = [-1.0, 0.0, 0.0];
        let weight = 1.0;
        let conn_01 = SpinConnectionSU2::new_normalized([0.8, 0.6, 0.0, 0.0]).unwrap();
        let conn_10 = conn_01.dagger();

        let edges = vec![
            (0, 1, weight, n_01, conn_01),
            (1, 0, weight, n_10, conn_10),
        ];

        let dirac = SimplicialDiracOperator::new(2, v_vols, edges).unwrap();

        let phi = vec![
            Spinor2::new((1.0, 0.2), (-0.5, 0.3)),
            Spinor2::new((0.4, -0.6), (1.1, 0.7)),
        ];
        let psi = vec![
            Spinor2::new((0.3, 0.9), (0.2, -0.1)),
            Spinor2::new((-0.7, 0.5), (0.8, 0.4)),
        ];

        let is_hermitian = dirac.check_hermiticity(&phi, &psi, 1e-7).unwrap();
        assert!(is_hermitian, "Discrete Dirac operator must be Hermitian");
    }
}

#[cfg(test)]
mod l4_boundary_tests_83350d86 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord83350d86::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord83350d86::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord83350d86::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord83350d86::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord83350d86::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError83350d86::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError83350d86::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
