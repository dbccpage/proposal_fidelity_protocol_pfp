// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Exact odd-prime discrete Wigner phase spaces and real cyclotomic values.
//!
//! Implements the discrete Gross phase space on F_5 x F_5:
//! - 25 exact Gross phase-point operators A(q, p) = D(q, p) P D(q, p)^\dagger
//! - Phase-point Hermiticity, unit trace, and orthogonality Tr(A(u) A(v)) = 5 delta_{u, v}
//! - Phase space resolution sum_u A(u) = 5 I_5
//! - Gross stabilizer covariance under discrete Weyl displacements
//! - Exact Wigner function evaluation W_rho(q, p) = 1/5 Tr(rho A(q, p))
//! - Magic state point negativity: W_M(0, 0) = -1/5 < 0
//! - Stabilizer state non-negativity for |0>.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3a01849a<T> {
    fn checked_invariant_3a01849a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3a01849a<T> for Option<T> {
    #[inline]
    fn checked_invariant_3a01849a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3a01849a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3a01849a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_traits::Zero;
use serde::{Deserialize, Serialize};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as iv, matrix as mx};
use core_lie_theory::heisenberg::WeylHeisenberg;
use core_number_theory::cyclotomic::Cyc5;
use core_number_theory::rational::{ri, rq, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum WignerError {
    #[error("the operator has the wrong dimension")]
    Shape,
    #[error("the operator must be Hermitian")]
    NotHermitian,
    #[error("a Wigner value is not fixed by complex conjugation")]
    NotReal,
    #[error("a real cyclotomic Wigner value is not rational; use evaluate_exact")]
    NonRational,
    #[error("phase-space coordinates are outside the declared field")]
    Coordinate,
    #[error(transparent)]
    Heisenberg(#[from] core_lie_theory::heisenberg::HeisenbergError),
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Embedding(#[from] core_number_theory::real_embedding::EmbeddingError),
}

/// Gross phase space on F_p², over Q(zeta_p). The prime is a type parameter;
/// admissibility is checked at construction rather than assumed from the type.
#[derive(Debug, Clone)]
pub struct DiscreteWigner<const P: usize> {
    weyl: core_lie_theory::heisenberg::WeylHeisenberg<
        core_number_theory::cyclotomic_field::Cyclotomic<P>,
    >,
}

impl<const P: usize> DiscreteWigner<P> {
    pub fn new() -> Result<Self, WignerError> {
        core_lie_theory::heisenberg::stone_von_neumann_census(P)?;
        Ok(Self {
            weyl: core_lie_theory::heisenberg::WeylHeisenberg::new(
                P,
                core_number_theory::cyclotomic_field::Cyclotomic::<P>::zeta(1),
            )?,
        })
    }

    pub fn operator(
        &self,
        q: i64,
        p: i64,
    ) -> Result<
        linear_algebra::backend::basic_matrix::BasicMatrix<
            core_number_theory::cyclotomic_field::Cyclotomic<P>,
        >,
        WignerError,
    > {
        Ok(self.weyl.displaced_parity(q, p)?)
    }

    pub fn evaluate(
        &self,
        rho: &linear_algebra::backend::basic_matrix::BasicMatrix<
            core_number_theory::cyclotomic_field::Cyclotomic<P>,
        >,
    ) -> Result<Vec<Vec<core_number_theory::cyclotomic_field::Cyclotomic<P>>>, WignerError> {
        if rho.shape() != (P, P) {
            return Err(WignerError::Shape);
        }
        if !core_lie_theory::scalar::is_hermitian(rho)? {
            return Err(WignerError::NotHermitian);
        }
        let mut grid = Vec::with_capacity(P);
        for q in 0..P {
            let mut row = Vec::with_capacity(P);
            for p in 0..P {
                let value = self
                    .weyl
                    .parity_pairing(rho, q as i64, p as i64)?
                    .scale(&rq(1, P as i64));
                if !value.is_real() {
                    return Err(WignerError::NotReal);
                }
                row.push(value);
            }
            grid.push(row);
        }
        Ok(grid)
    }

    /// The rank-one spectral projector of D(a,b) at eigenvalue omega^k.
    pub fn stabilizer_projector(
        &self,
        a: i64,
        b: i64,
        k: i64,
    ) -> Result<
        linear_algebra::backend::basic_matrix::BasicMatrix<
            core_number_theory::cyclotomic_field::Cyclotomic<P>,
        >,
        WignerError,
    > {
        use linear_algebra::exact_field::matrix as mx;
        use core_number_theory::cyclotomic_field::Cyclotomic;
        let a = a.rem_euclid(P as i64);
        let b = b.rem_euclid(P as i64);
        let k = k.rem_euclid(P as i64);
        if a == 0 && b == 0 {
            return Err(WignerError::Coordinate);
        }
        let mut projector = mx::zeros(P, P)?;
        for t in 0..P as i64 {
            projector = mx::add(
                &projector,
                &mx::scale(
                    &self.weyl.displacement(t * a, t * b)?,
                    &Cyclotomic::<P>::zeta(-k * t),
                )?,
            )?;
        }
        Ok(mx::scale(
            &projector,
            &Cyclotomic::<P>::rational(rq(1, P as i64)),
        )?)
    }

    /// Probability on the affine line `q*b-p*a=k`, the marginal associated with D(a,b).
    pub fn line_marginal(
        &self,
        rho: &linear_algebra::backend::basic_matrix::BasicMatrix<
            core_number_theory::cyclotomic_field::Cyclotomic<P>,
        >,
        a: i64,
        b: i64,
        k: i64,
    ) -> Result<core_number_theory::cyclotomic_field::Cyclotomic<P>, WignerError> {
        use core_number_theory::cyclotomic_field::Cyclotomic;
        let (a, b, k) = (
            a.rem_euclid(P as i64),
            b.rem_euclid(P as i64),
            k.rem_euclid(P as i64),
        );
        if a == 0 && b == 0 {
            return Err(WignerError::Coordinate);
        }
        let grid = self.evaluate(rho)?;
        let mut result = Cyclotomic::<P>::zero();
        for q in 0..P {
            for p in 0..P {
                if (q as i64 * b - p as i64 * a).rem_euclid(P as i64) == k {
                    result = result.add(&grid[q][p]);
                }
            }
        }
        Ok(result)
    }

    /// Sum of absolute Wigner values in the declared embedding (`k=1` canonically).
    /// Its logarithm is mana; this method returns the exact argument of that logarithm.
    pub fn l1_norm(
        &self,
        rho: &linear_algebra::backend::basic_matrix::BasicMatrix<
            core_number_theory::cyclotomic_field::Cyclotomic<P>,
        >,
        embedding: i64,
    ) -> Result<core_number_theory::cyclotomic_field::Cyclotomic<P>, WignerError> {
        let values: Vec<_> = self.evaluate(rho)?.into_iter().flatten().collect();
        Ok(core_functional::norms::cyclotomic_l1(&values, embedding)?)
    }
}

/// Discrete Gross phase-space system on F_5 x F_5 with 25 phase point operators.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DiscreteWignerSystemD5 {
    /// 5x5 grid of 25 phase-point operators A(q, p).
    operators: Vec<Vec<BasicMatrix<Cyc5>>>,
}

impl Default for DiscreteWignerSystemD5 {
    fn default() -> Self {
        Self::new()
    }
}

impl DiscreteWignerSystemD5 {
    pub fn new() -> Self {
        let system = WeylHeisenberg::new(5, Cyc5::zeta5(1)).checked_invariant_3a01849a("declared primitive fifth root");
        Self {
            operators: (0..5)
                .map(|q| {
                    (0..5)
                        .map(|p| system.displaced_parity(q, p).checked_invariant_3a01849a("bounded phase point"))
                        .collect()
                })
                .collect(),
        }
    }
    pub fn operator(&self, q: usize, p: usize) -> Result<&BasicMatrix<Cyc5>, WignerError> {
        if q >= 5 || p >= 5 {
            return Err(WignerError::Coordinate);
        }
        if !self.valid_geometry() {
            return Err(WignerError::Shape);
        }
        let op = self
            .operators
            .get(q)
            .and_then(|r| r.get(p))
            .ok_or(WignerError::Coordinate)?;
        if op.shape() != (5, 5) {
            return Err(WignerError::Shape);
        }
        Ok(op)
    }
    pub fn try_operator(&self, q: usize, p: usize) -> Result<&BasicMatrix<Cyc5>, WignerError> {
        self.operator(q, p)
    }
    fn valid_geometry(&self) -> bool {
        self.operators.len() == 5
            && self
                .operators
                .iter()
                .all(|row| row.len() == 5 && row.iter().all(|m| m.shape() == (5, 5)))
    }
    pub fn verify_hermiticity(&self) -> bool {
        self.valid_geometry()
            && self
                .operators
                .iter()
                .flatten()
                .all(|a| iv::is_hermitian(a).unwrap_or(false))
    }
    pub fn verify_unit_trace(&self) -> bool {
        self.valid_geometry()
            && self
                .operators
                .iter()
                .flatten()
                .all(|a| mx::trace(a).map(|t| t == Cyc5::one()).unwrap_or(false))
    }
    pub fn verify_orthogonality(&self) -> bool {
        if !self.valid_geometry() {
            return false;
        }
        let ops = self.operators.iter().flatten().collect::<Vec<_>>();
        for (u, a) in ops.iter().enumerate() {
            for (v, b) in ops.iter().enumerate() {
                let Ok(pair) = iv::hs_inner(a, b) else {
                    return false;
                };
                if pair != Cyc5::rat(ri(if u == v { 5 } else { 0 })) {
                    return false;
                }
            }
        }
        true
    }
    pub fn verify_resolution(&self) -> bool {
        if !self.valid_geometry() {
            return false;
        }
        let Ok(mut total) = mx::zeros(5, 5) else {
            return false;
        };
        for a in self.operators.iter().flatten() {
            let Ok(sum) = mx::add(&total, a) else {
                return false;
            };
            total = sum;
        }
        mx::identity(5)
            .and_then(|i| mx::scale(&i, &Cyc5::rat(ri(5))))
            .map(|i| i == total)
            .unwrap_or(false)
    }
    pub fn verify_gross_covariance(&self) -> bool {
        if !self.valid_geometry() {
            return false;
        }
        let Ok(w) = WeylHeisenberg::new(5, Cyc5::zeta5(1)) else {
            return false;
        };
        for q0 in 0..5 {
            for p0 in 0..5 {
                let Ok(d) = w.displacement(q0, p0) else {
                    return false;
                };
                let Ok(dd) = iv::adjoint(&d) else {
                    return false;
                };
                for q in 0..5 {
                    for p in 0..5 {
                        let transformed = self
                            .operator(q, p)
                            .and_then(|a| Ok(mx::multiply(&mx::multiply(&d, a)?, &dd)?));
                        let target = self.operator((q + q0 as usize) % 5, (p + p0 as usize) % 5);
                        if !matches!((transformed,target),(Ok(a),Ok(b)) if a==*b) {
                            return false;
                        }
                    }
                }
            }
        }
        true
    }
    /// Full real cyclotomic values; no projection onto a rational coefficient.
    pub fn evaluate_exact(&self, rho: &BasicMatrix<Cyc5>) -> Result<Vec<Vec<Cyc5>>, WignerError> {
        if rho.shape() != (5, 5) || !self.valid_geometry() {
            return Err(WignerError::Shape);
        }
        if !iv::is_hermitian(rho)? {
            return Err(WignerError::NotHermitian);
        }
        let mut grid = vec![vec![Cyc5::zero(); 5]; 5];
        for q in 0..5 {
            for p in 0..5 {
                let value = iv::hs_inner(rho, self.operator(q, p)?)?.mul(&Cyc5::rat(rq(1, 5)));
                if value.conj() != value {
                    return Err(WignerError::NotReal);
                }
                grid[q][p] = value;
            }
        }
        Ok(grid)
    }
    pub fn evaluate_wigner(
        &self,
        rho: &BasicMatrix<Cyc5>,
    ) -> Result<Vec<Vec<Rational>>, WignerError> {
        self.evaluate_exact(rho)?
            .into_iter()
            .map(|row| {
                row.into_iter()
                    .map(|x| {
                        if x.a[1..].iter().any(|c| !c.is_zero()) {
                            return Err(WignerError::NonRational);
                        }
                        Ok(x.a[0].clone())
                    })
                    .collect()
            })
            .collect()
    }
}

/// Ground stabilizer state |0><0| in d=5.
pub fn state_ground_d5() -> BasicMatrix<Cyc5> {
    let mut rho = mx::zeros(5, 5).checked_invariant_3a01849a("declared 5x5 state");
    rho.set(0, 0, Cyc5::one()).checked_invariant_3a01849a("state index");
    rho
}

/// Magic state |M> = 1/sqrt(2)(|1> - |4>) in d=5.
///
/// Notice P |M> = -|M>, an odd-parity eigenstate.
/// rho_M = 1/2 (|1><1| - |1><4| - |4><1| + |4><4|).
pub fn state_magic_d5() -> BasicMatrix<Cyc5> {
    let mut rho = mx::zeros(5, 5).checked_invariant_3a01849a("declared 5x5 state");
    let half = Cyc5::rat(rq(1, 2));
    let neg_half = Cyc5::rat(rq(-1, 2));

    rho.set(1, 1, half.clone()).checked_invariant_3a01849a("state index");
    rho.set(1, 4, neg_half.clone()).checked_invariant_3a01849a("state index");
    rho.set(4, 1, neg_half.clone()).checked_invariant_3a01849a("state index");
    rho.set(4, 4, half.clone()).checked_invariant_3a01849a("state index");
    rho
}

// Origin: engine/crates_rs/core_quantum_physics/src/wigner.rs
// Claim: urn:core:crates_rs:core-quantum-physics:wigner:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_d5_phase_point_algebra() {
        let wsys = DiscreteWignerSystemD5::new();
        assert!(wsys.verify_hermiticity());
        assert!(wsys.verify_unit_trace());
        assert!(wsys.verify_orthogonality());
        assert!(wsys.verify_resolution());
        assert!(wsys.verify_gross_covariance());
    }

    #[test]
    fn test_d5_magic_state_point_negativity() {
        use core_number_theory::cyclotomic_field::CyclotomicNumber;
        use core_number_theory::cyclotomic_ordered::standard_real_sign;

        let wsys = DiscreteWignerSystemD5::new();
        let rho_m = state_magic_d5();
        let w_grid = wsys.evaluate_exact(&rho_m).unwrap();
        let values: Vec<CyclotomicNumber> = w_grid
            .iter()
            .flatten()
            .map(CyclotomicNumber::from)
            .collect();
        let signs: Vec<i8> = values
            .iter()
            .map(|value| standard_real_sign(value).unwrap())
            .collect();

        // The origin is rational; the full grid contains nonrational real values.
        assert_eq!(values[0].as_rational(), Some(rq(-1, 5)));
        assert_eq!(signs.len(), 25);
        assert_eq!(signs[0], -1);
        assert!(signs.iter().any(|sign| *sign == -1));
        assert!(values.iter().any(|value| value.as_rational().is_none()));

        // Preserve all cyclotomic coefficients while checking exact unit total mass.
        let total_sum = w_grid
            .iter()
            .flatten()
            .fold(Cyc5::zero(), |sum, value| sum.add(value));
        assert_eq!(total_sum, Cyc5::one());
        assert!(matches!(
            wsys.evaluate_wigner(&rho_m),
            Err(WignerError::NonRational)
        ));
    }

    #[test]
    fn test_d5_stabilizer_ground_state_non_negativity() {
        let wsys = DiscreteWignerSystemD5::new();
        let rho_0 = state_ground_d5();

        let w_grid = wsys.evaluate_wigner(&rho_0).unwrap();

        // All points must be non-negative
        for q in 0..5 {
            for p in 0..5 {
                assert!(w_grid[q][p] >= Rational::zero());
            }
        }

        // Total sum = 1
        let total_sum: Rational = w_grid.iter().flat_map(|row| row.iter()).cloned().sum();
        assert_eq!(total_sum, ri(1));
    }
}
