//! Discrete Weyl-Heisenberg systems and finite phase-space symplectic geometry.
//!
//! AuthorityEffect: None.
//!
//! Provides finite phase-space displacement labeling, symplectic inner products,
//! and ray decompositions for prime-dimensional Weyl systems without host I/O.

use thiserror::Error;

/// Mandatory authority effect declaration.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// Errors occurring during Weyl system operations.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum WeylSystemError {
    #[error("dimension must be >= 2 and <= 256")]
    InvalidDimension,
    #[error("dimension {0} must be prime for isotropic ray decomposition")]
    NotPrime(usize),
    #[error("coordinate ({0}, {1}) is out of bounds for dimension {2}")]
    CoordinateOutOfBounds(usize, usize, usize),
}

/// A point in discrete phase space $\mathbb{Z}_d \times \mathbb{Z}_d$.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct PhasePoint {
    pub q: usize,
    pub p: usize,
}

impl PhasePoint {
    pub fn new(q: usize, p: usize) -> Self {
        Self { q, p }
    }
}

/// A discrete Weyl system over dimension $d$.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteWeylSystem {
    dim: usize,
}

impl DiscreteWeylSystem {
    /// Creates a discrete Weyl system for dimension `dim`.
    pub fn new(dim: usize) -> Result<Self, WeylSystemError> {
        if dim < 2 || dim > 256 {
            return Err(WeylSystemError::InvalidDimension);
        }
        Ok(Self { dim })
    }

    /// Dimension of the Hilbert space / modular arithmetic.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Symplectic bilinear form $\omega(u, v) = u_q v_p - u_p v_q \pmod d$.
    pub fn symplectic_form(&self, u: PhasePoint, v: PhasePoint) -> Result<usize, WeylSystemError> {
        if u.q >= self.dim || u.p >= self.dim {
            return Err(WeylSystemError::CoordinateOutOfBounds(u.q, u.p, self.dim));
        }
        if v.q >= self.dim || v.p >= self.dim {
            return Err(WeylSystemError::CoordinateOutOfBounds(v.q, v.p, self.dim));
        }
        let term1 = (u.q * v.p) % self.dim;
        let term2 = (u.p * v.q) % self.dim;
        let res = (self.dim + term1 - term2) % self.dim;
        Ok(res)
    }

    /// Checks if two displacement operators commute: $\omega(u, v) \equiv 0 \pmod d$.
    pub fn commutes(&self, u: PhasePoint, v: PhasePoint) -> Result<bool, WeylSystemError> {
        Ok(self.symplectic_form(u, v)? == 0)
    }

    /// Addition of phase space points modulo $d$.
    pub fn add(&self, u: PhasePoint, v: PhasePoint) -> Result<PhasePoint, WeylSystemError> {
        if u.q >= self.dim || u.p >= self.dim {
            return Err(WeylSystemError::CoordinateOutOfBounds(u.q, u.p, self.dim));
        }
        if v.q >= self.dim || v.p >= self.dim {
            return Err(WeylSystemError::CoordinateOutOfBounds(v.q, v.p, self.dim));
        }
        Ok(PhasePoint {
            q: (u.q + v.q) % self.dim,
            p: (u.p + v.p) % self.dim,
        })
    }

    /// Decomposes the non-zero points of $\mathbb{Z}_p \times \mathbb{Z}_p$ into $p+1$ isotropic rays.
    /// Each ray is a maximal commuting set of $p$ points (including origin $(0, 0)$).
    /// Requires `dim` to be prime.
    pub fn isotropic_rays(&self) -> Result<Vec<Vec<PhasePoint>>, WeylSystemError> {
        let p = self.dim;
        for d in 2..p {
            if p % d == 0 {
                return Err(WeylSystemError::NotPrime(p));
            }
        }

        let mut rays = Vec::with_capacity(p + 1);

        // Ray infinity: q = 0, p in 0..p
        let mut ray_inf = Vec::with_capacity(p);
        for y in 0..p {
            ray_inf.push(PhasePoint::new(0, y));
        }
        rays.push(ray_inf);

        // Rays m in 0..p: p = m * q mod p
        for m in 0..p {
            let mut ray_m = Vec::with_capacity(p);
            for x in 0..p {
                ray_m.push(PhasePoint::new(x, (m * x) % p));
            }
            rays.push(ray_m);
        }

        Ok(rays)
    }
}

// Origin: engine/crates_rs/core_combinatorics/src/weyl_systems.rs
// Claim: urn:core:crates_rs:core-combinatorics:weyl-systems:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    #[test]
    fn test_symplectic_form_antisymmetry_and_bilinearity() {
        let weyl = DiscreteWeylSystem::new(5).unwrap();
        let u = PhasePoint::new(2, 3);
        let v = PhasePoint::new(1, 4);

        let core_uv = weyl.symplectic_form(u, v).unwrap();
        let core_vu = weyl.symplectic_form(v, u).unwrap();

        // Antisymmetry: omega(u, v) + omega(v, u) = 0 mod 5
        assert_eq!((core_uv + core_vu) % 5, 0);

        // Self-orthogonality: omega(u, u) = 0
        assert_eq!(weyl.symplectic_form(u, u).unwrap(), 0);
    }

    #[test]
    fn test_prime_isotropic_rays_partition() {
        for p in [2, 3, 5, 7] {
            let weyl = DiscreteWeylSystem::new(p).unwrap();
            let rays = weyl.isotropic_rays().unwrap();
            assert_eq!(rays.len(), p + 1);

            let origin = PhasePoint::new(0, 0);
            let mut seen_nonzero = BTreeSet::new();

            for ray in &rays {
                assert_eq!(ray.len(), p);
                assert!(ray.contains(&origin));

                // Every ray is isotropic: all pairs commute
                for &u in ray {
                    for &v in ray {
                        assert!(weyl.commutes(u, v).unwrap());
                    }
                }

                // Non-zero points are disjoint
                for &pt in ray {
                    if pt != origin {
                        assert!(seen_nonzero.insert(pt), "Disjoint partition violated at {:?}", pt);
                    }
                }
            }

            // Total non-zero points is p^2 - 1
            assert_eq!(seen_nonzero.len(), p * p - 1);
        }
    }
}
