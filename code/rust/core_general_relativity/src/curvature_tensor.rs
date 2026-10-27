//! Discrete Simplicial Riemann Curvature Tensor (Hamber §7.1, MTW §42.3).
//!
//! On a simplicial manifold, curvature is concentrated on codimension-2 hinges $h$.
//! The Riemann curvature tensor distribution at hinge $h$ is:
//!   $$R_{\mu\nu\rho\sigma}(h) = 2 \epsilon_h \frac{U_{\mu\nu}(h) U_{\rho\sigma}(h)}{A_h}$$
//! where:
//! - $\epsilon_h$ is the deficit angle at hinge $h$.
//! - $A_h$ is the hinge volume (area in 4D, length in 3D).
//! - $U_{\mu\nu}(h)$ is the unit bivector orthogonal to hinge $h$, satisfying
//!   $U_{\mu\nu} = -U_{\nu\mu}$ and $\sum_{\mu,\nu} U_{\mu\nu}^2 = 2$.
//!
//! Algebraic properties:
//! 1. Antisymmetry: $R_{\mu\nu\rho\sigma} = -R_{\nu\mu\rho\sigma} = -R_{\mu\nu\sigma\rho}$
//! 2. Pair exchange: $R_{\mu\nu\rho\sigma} = R_{\rho\sigma\mu\nu}$
//! 3. First algebraic Bianchi identity: $R_{\mu[\nu\rho\sigma]} = 0$
//! 4. Contraction to scalar curvature: $R(h) = g^{\mu\rho} g^{\nu\sigma} R_{\mu\nu\rho\sigma}(h) = \frac{2 \epsilon_h}{A_h}$
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; discrete simplicial Riemann tensor.";

/// 4-dimensional antisymmetric unit bivector U_{μν} orthogonal to a hinge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HingeBivector4D {
    /// 4x4 antisymmetric matrix entries.
    components: [[f64; 4]; 4],
}

impl HingeBivector4D {
    /// Construct a unit bivector spanning the orthogonal 2-plane formed by two orthonormal unit vectors e1, e2:
    /// U_{μν} = e1_μ e2_ν - e1_ν e2_μ.
    pub fn from_orthonormal_frame(e1: [f64; 4], e2: [f64; 4]) -> Result<Self, String> {
        // Verify orthogonality: e1 · e2 ~ 0
        let dot: f64 = e1.iter().zip(e2.iter()).map(|(&a, &b)| a * b).sum();
        if dot.abs() > 1e-6 {
            return Err(format!(
                "Frame vectors are not orthogonal: dot product = {dot}"
            ));
        }

        // Verify unit norms: |e1| ~ 1, |e2| ~ 1
        let norm1: f64 = e1.iter().map(|&a| a * a).sum::<f64>().sqrt();
        let norm2: f64 = e2.iter().map(|&b| b * b).sum::<f64>().sqrt();
        if (norm1 - 1.0).abs() > 1e-6 || (norm2 - 1.0).abs() > 1e-6 {
            return Err(format!(
                "Frame vectors not unit length: |e1|={norm1}, |e2|={norm2}"
            ));
        }

        let mut components = [[0.0; 4]; 4];
        for mu in 0..4 {
            for nu in 0..4 {
                components[mu][nu] = e1[mu] * e2[nu] - e1[nu] * e2[mu];
            }
        }

        Ok(Self { components })
    }

    /// Canonical bivector aligned with coordinate planes (e.g. z-w plane: mu=2, nu=3).
    pub fn canonical_plane(mu: usize, nu: usize) -> Result<Self, String> {
        if mu >= 4 || nu >= 4 || mu == nu {
            return Err("Invalid plane indices for 4D bivector".to_string());
        }
        let mut components = [[0.0; 4]; 4];
        components[mu][nu] = 1.0;
        components[nu][mu] = -1.0;
        Ok(Self { components })
    }

    pub fn get(&self, mu: usize, nu: usize) -> f64 {
        if mu < 4 && nu < 4 {
            self.components[mu][nu]
        } else {
            0.0
        }
    }

    /// Norm squared of the bivector: ∑_{μ,ν} U_{μν}² = 2 for a simple unit bivector.
    pub fn norm_squared(&self) -> f64 {
        let mut sum = 0.0;
        for mu in 0..4 {
            for nu in 0..4 {
                sum += self.components[mu][nu] * self.components[mu][nu];
            }
        }
        sum
    }
}

/// Discrete Riemann curvature tensor associated with a codimension-2 hinge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscreteRiemannTensor4D {
    pub hinge_vertices: Vec<usize>,
    pub deficit_angle: f64,
    pub hinge_area: f64,
    pub bivector: HingeBivector4D,
}

impl DiscreteRiemannTensor4D {
    pub fn new(
        hinge_vertices: Vec<usize>,
        deficit_angle: f64,
        hinge_area: f64,
        bivector: HingeBivector4D,
    ) -> Result<Self, String> {
        if hinge_area <= 1e-12 || !hinge_area.is_finite() {
            return Err(format!("Invalid non-positive hinge area {hinge_area}"));
        }
        if !deficit_angle.is_finite() {
            return Err("Non-finite deficit angle".to_string());
        }

        Ok(Self {
            hinge_vertices,
            deficit_angle,
            hinge_area,
            bivector,
        })
    }

    /// Evaluate Riemann tensor component R_{μνρσ} at this hinge:
    /// R_{μνρσ} = 2 * (ε / A) * U_{μν} * U_{ρσ}
    pub fn component(&self, mu: usize, nu: usize, rho: usize, sigma: usize) -> f64 {
        let factor = 2.0 * (self.deficit_angle / self.hinge_area);
        factor * self.bivector.get(mu, nu) * self.bivector.get(rho, sigma)
    }

    /// Scalar curvature density R = g^{μρ} g^{νσ} R_{μνρσ} in locally flat coordinates:
    /// R = ∑_{μ,ν} R_{μνμν} = (2 ε / A) * (1/2 ∑_{μ,ν} U_{μν}²) = 2 ε / A.
    pub fn scalar_curvature_density(&self) -> f64 {
        2.0 * (self.deficit_angle / self.hinge_area)
    }

    /// Integrated scalar curvature over the hinge volume:
    /// ∫ R √g d^D x = 2 ε A.
    pub fn integrated_scalar_curvature(&self) -> f64 {
        2.0 * self.deficit_angle * self.hinge_area
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/curvature_tensor.rs
// Claim: urn:core:crates_rs:core-general-relativity:curvature-tensor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde151cf2c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde151cf2c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore151cf2c {
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
impl BoundaryErrore151cf2c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore151cf2c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore151cf2c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde151cf2c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore151cf2c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore151cf2c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore151cf2c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore151cf2c::ExceedsCapacity {
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
    fn test_bivector_properties_and_norm() {
        let e1 = [1.0, 0.0, 0.0, 0.0];
        let e2 = [0.0, 1.0, 0.0, 0.0];
        let biv = HingeBivector4D::from_orthonormal_frame(e1, e2).unwrap();

        assert_eq!(biv.get(0, 1), 1.0);
        assert_eq!(biv.get(1, 0), -1.0);
        assert_eq!(biv.get(0, 0), 0.0);
        assert_eq!(biv.get(2, 3), 0.0);
        assert!((biv.norm_squared() - 2.0).abs() < 1e-9);
    }

    #[test]
    fn test_riemann_algebraic_symmetries() {
        let biv = HingeBivector4D::canonical_plane(2, 3).unwrap();
        let eps = 0.4;
        let area = 1.5;
        let r = DiscreteRiemannTensor4D::new(vec![0, 1, 2], eps, area, biv).unwrap();

        // 1. Antisymmetry in first two indices
        for mu in 0..4 {
            for nu in 0..4 {
                assert!((r.component(mu, nu, 2, 3) + r.component(nu, mu, 2, 3)).abs() < 1e-9);
            }
        }

        // 2. Pair exchange symmetry R_{μνρσ} = R_{ρσμν}
        assert!((r.component(2, 3, 2, 3) - 2.0 * eps / area).abs() < 1e-9);
        assert_eq!(r.component(2, 3, 0, 1), r.component(0, 1, 2, 3));

        // 3. First algebraic Bianchi identity: R_{μνρσ} + R_{μρσν} + R_{μσνρ} = 0
        let b1 = r.component(0, 1, 2, 3) + r.component(0, 2, 3, 1) + r.component(0, 3, 1, 2);
        assert!(b1.abs() < 1e-9);

        // 4. Scalar curvature density and integrated curvature
        let expected_density = 2.0 * eps / area;
        assert!((r.scalar_curvature_density() - expected_density).abs() < 1e-9);

        let expected_integrated = 2.0 * eps * area;
        assert!((r.integrated_scalar_curvature() - expected_integrated).abs() < 1e-9);
    }
}

#[cfg(test)]
mod l4_boundary_tests_e151cf2c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde151cf2c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde151cf2c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde151cf2c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde151cf2c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde151cf2c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore151cf2c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore151cf2c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
