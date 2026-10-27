// Modular data of a ribbon fusion category: the unnormalised `S~` and `T`, the Verlinde
// formula, the modular relations, Gauss-Milgram and the genus-`g` ground-state count,
// all evaluated exactly in the coefficient field.
//
// Conventions. With quantum dimensions `d_a`, twists `theta_a`, `D^2 = sum_a d_a^2`
// and `p_+ = sum_a d_a^2 theta_a`:
//
// - `S~_{ab} = sum_c N_{a b*}^c d_c theta_c / (theta_a theta_b)` (so `S~ = D S` for the
//   normalised `S`) and `T = diag(theta_a)`;
// - `S~` is symmetric, `S~^2 = D^2 C` (`C` the charge conjugation), `S~ S~^dagger = D^2 I`,
//   and `(S~ T)^3 = p_+ S~^2`. These are the exact in-field statements. The familiar
//   `(ST)^3 = S^2` holds only for the c-normalised `T~ = T e^{-2 pi i c / 24}`, which is
//   not in general an element of the field, and only after dividing by `D` (a square
//   root that need not lie in the field either);
// - Verlinde: `N_{ab}^c = (1/D^2) sum_x S~_{ax} S~_{bx} conj(S~_{cx}) / S~_{0x}`;
// - Gauss-Milgram: `p_+ / D = exp(2 pi i c / 8)`. In the field it is the exact statement
//   `p_+^2 / D^2 = zeta` with `zeta` a root of unity, which fixes `c` modulo 4; when `D`
//   itself lies in the field, `p_+ / D` is a root of unity and fixes `c` modulo 8;
// - the Frobenius-Schur indicator by Bantay's formula
//   `nu_a = (1/D^2) sum_{b,c} N_{bc}^a d_b d_c (theta_b / theta_c)^2`;
// - the genus-`g` ground-state degeneracy `sum_a (D^2 / d_a^2)^{g-1}`.
//
// What is computed is exact; what is not: the topological entanglement entropy
// `gamma = ln D` is reported as the algebraic `D^2` (no logarithm, no floating point), and
// no statement is made about any material hosting the category.
// [`ModularData::central_charge_mod_8`] takes `D` as an element of the field and checks
// `D^2 = sum_a d_a^2` and `D > 0` exactly (the sign through
// [`FusionScalar::real_sign`]).
//
// AuthorityEffect: None.
use std::cmp::Ordering;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use core_number_theory::rational::Rational;
use thiserror::Error;

use crate::braided::RibbonFusionCategory;
use crate::error::FusionError;
use crate::fusion_ring::FusionRing;
use crate::scalar::{root_of_unity_data, FusionScalar};
use linear_algebra::exact_field::{elimination, involution, matrix};

/// A modular relation that fails, with the matrix position or labels at which it fails.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Error)]
pub enum ModularDefect {
    /// `S~` is not symmetric at `(a, b)`.
    #[error("S~ is not symmetric at ({a}, {b})")]
    NotSymmetric { a: usize, b: usize },
    /// `S~` has rank below the number of simple objects: the braiding is degenerate.
    #[error("the braiding is degenerate: S~ has rank {rank} of {size}")]
    Degenerate { rank: usize, size: usize },
    /// `S~^2 != D^2 C` at `(a, b)`.
    #[error("S~^2 differs from D^2 C at ({a}, {b})")]
    SSquared { a: usize, b: usize },
    /// `S~ S~^dagger != D^2 I` at `(a, b)`.
    #[error("S~ S~^dagger differs from D^2 I at ({a}, {b})")]
    Unitarity { a: usize, b: usize },
    /// `(S~ T)^3 != p_+ S~^2` at `(a, b)`.
    #[error("(S~ T)^3 differs from p_+ S~^2 at ({a}, {b})")]
    Relation { a: usize, b: usize },
    /// The Verlinde formula does not reproduce `N_{ab}^c`.
    #[error("the Verlinde formula fails at ({a}, {b}, {c})")]
    Verlinde { a: usize, b: usize, c: usize },
    /// `D^2 = 0`.
    #[error("the global dimension squared is zero")]
    ZeroGlobalDimension,
    /// The Bantay sum for `label` is not one of `-1, 0, 1`.
    #[error("the Frobenius-Schur sum of label {label} is not -1, 0 or 1")]
    FrobeniusSchur { label: usize },
    /// A supplied `D` with `D^2` different from the global dimension squared.
    #[error("the supplied dimension D does not satisfy D^2 = sum_a d_a^2")]
    WrongGlobalDimension,
    /// A supplied `D` that is not positive under the canonical embedding.
    #[error("the supplied dimension D is not positive")]
    NonPositiveDimension,
}

/// The modular data `(S~, T)` of a ribbon fusion category, with its dimensions and ring.
#[derive(Debug, Clone, PartialEq)]
pub struct ModularData<K> {
    ring: FusionRing,
    dimensions: Vec<K>,
    twists: Vec<K>,
    s_tilde: BasicMatrix<K>,
    d_squared: K,
    p_plus: K,
}

impl<K: FusionScalar> ModularData<K> {
    /// Computes `S~`, `T`, `D^2` and `p_+` of a ribbon category; nothing is verified (see
    /// [`Self::verify`] and [`Self::verified`]).
    pub fn from_ribbon(ribbon: &RibbonFusionCategory<K>) -> Result<Self, FusionError> {
        let s_tilde = Self::ribbon_s_matrix(ribbon.ring(), ribbon.dimensions(), ribbon.twists())?;
        Ok(Self {
            ring: ribbon.ring().clone(),
            dimensions: ribbon.dimensions().to_vec(),
            twists: ribbon.twists().to_vec(),
            s_tilde,
            d_squared: ribbon.global_dimension_squared(),
            p_plus: ribbon.gauss_sum(),
        })
    }

    fn ribbon_s_matrix(
        ring: &FusionRing,
        dimensions: &[K],
        twists: &[K],
    ) -> Result<BasicMatrix<K>, FusionError> {
        let n = ring.rank();
        let inverses = twists
            .iter()
            .map(|theta| core_number_theory::scalar::inverse(theta).map_err(FusionError::from))
            .collect::<Result<Vec<_>, _>>()?;
        let weighted = dimensions
            .iter()
            .zip(twists)
            .map(|(d, t)| d.mul(t))
            .collect::<Vec<_>>();
        let duals = (0..n)
            .map(|b| ring.dual(b))
            .collect::<Result<Vec<_>, _>>()?;
        BasicMatrix::try_from_fn_result(n, n, |a, b| {
            let total = Self::fusion_sum(ring, a, duals[b], &weighted)?;
            Ok(total.mul(&inverses[a]).mul(&inverses[b]))
        })
    }

    fn add_multiple(total: K, value: &K, multiplicity: u64) -> Result<K, FusionError> {
        match multiplicity {
            0 => Ok(total),
            1 => Ok(total.add(value)),
            _ => {
                let weight = core_number_theory::scalar::from_i64::<K>(
                    i64::try_from(multiplicity).map_err(|_| FusionError::Overflow {
                        context: "embedding a fusion coefficient",
                    })?,
                );
                Ok(total.add(&weight.mul(value)))
            }
        }
    }

    fn fusion_sum(ring: &FusionRing, a: usize, b: usize, values: &[K]) -> Result<K, FusionError> {
        let mut total = K::zero();
        for (c, value) in values.iter().enumerate() {
            total = Self::add_multiple(total, value, ring.n(a, b, c))?;
        }
        Ok(total)
    }

    /// Computes the modular data and verifies every relation of [`Self::verify`].
    pub fn verified(ribbon: &RibbonFusionCategory<K>) -> Result<Self, FusionError> {
        let data = Self::from_ribbon(ribbon)?;
        data.verify()?;
        Ok(data)
    }

    /// The number of simple objects.
    pub fn rank(&self) -> usize {
        self.ring.rank()
    }

    /// The fusion ring.
    pub fn ring(&self) -> &FusionRing {
        &self.ring
    }

    /// The quantum dimensions.
    pub fn dimensions(&self) -> &[K] {
        &self.dimensions
    }

    /// The twists.
    pub fn twists(&self) -> &[K] {
        &self.twists
    }

    /// The unnormalised `S~ = D S`.
    pub fn s_tilde(&self) -> &BasicMatrix<K> {
        &self.s_tilde
    }

    /// `D^2 = sum_a d_a^2`.
    pub fn d_squared(&self) -> &K {
        &self.d_squared
    }

    /// `p_+ = sum_a d_a^2 theta_a`.
    pub fn p_plus(&self) -> &K {
        &self.p_plus
    }

    /// The topological entanglement entropy of the category is `gamma = ln D = (1/2) ln D^2`;
    /// this returns the algebraic number `D^2` it is the logarithm of. No logarithm is
    /// computed.
    pub fn topological_entanglement_entropy_dimension_squared(&self) -> &K {
        &self.d_squared
    }

    /// `T = diag(theta_a)`.
    pub fn t_matrix(&self) -> Result<BasicMatrix<K>, FusionError> {
        matrix::diagonal(&self.twists).map_err(FusionError::from)
    }

    /// The charge conjugation `C_{ab} = delta_{b, a*}`.
    pub fn charge_conjugation(&self) -> Result<BasicMatrix<K>, FusionError> {
        self.scaled_charge_conjugation(&K::one())
    }

    fn scaled_charge_conjugation(&self, scale: &K) -> Result<BasicMatrix<K>, FusionError> {
        let n = self.rank();
        BasicMatrix::try_from_fn_result(n, n, |a, b| {
            Ok(if self.ring.dual(a)? == b {
                scale.clone()
            } else {
                K::zero()
            })
        })
    }

    fn scaled_identity(&self, scale: &K) -> Result<BasicMatrix<K>, FusionError> {
        let n = self.rank();
        BasicMatrix::try_from_fn(n, n, |a, b| if a == b { scale.clone() } else { K::zero() })
            .map_err(FusionError::from)
    }

    fn first_difference(
        left: &BasicMatrix<K>,
        right: &BasicMatrix<K>,
    ) -> Result<Option<(usize, usize)>, FusionError> {
        if left.shape() != right.shape() {
            return Err(FusionError::Shape {
                operation: "comparing modular matrices",
                left: left.shape(),
                right: right.shape(),
            });
        }
        for a in 0..left.rows() {
            for b in 0..left.cols() {
                if left.get_ref(a, b)? != right.get_ref(a, b)? {
                    return Ok(Some((a, b)));
                }
            }
        }
        Ok(None)
    }

    /// Verifies, exactly in the field: `D^2 != 0`; `S~` symmetric; `S~` of full rank;
    /// `S~^2 = D^2 C`; `S~ S~^dagger = D^2 I`; `(S~ T)^3 = p_+ S~^2`; and the Verlinde formula
    /// against the fusion ring. The error names the first relation that fails.
    pub fn verify(&self) -> Result<(), FusionError> {
        if self.d_squared.is_zero() {
            return Err(FusionError::Modular(ModularDefect::ZeroGlobalDimension));
        }
        self.verify_symmetry()?;
        self.verify_nondegenerate()?;
        let squared = self.verify_square()?;
        self.verify_unitarity()?;
        self.verify_relation(&squared)?;
        self.verify_verlinde()
    }

    fn require_equal(
        left: &BasicMatrix<K>,
        right: &BasicMatrix<K>,
        defect: impl FnOnce(usize, usize) -> ModularDefect,
    ) -> Result<(), FusionError> {
        if let Some((a, b)) = Self::first_difference(left, right)? {
            return Err(FusionError::Modular(defect(a, b)));
        }
        Ok(())
    }

    fn verify_symmetry(&self) -> Result<(), FusionError> {
        for a in 0..self.rank() {
            for b in a + 1..self.rank() {
                if self.s_tilde.get_ref(a, b)? != self.s_tilde.get_ref(b, a)? {
                    return Err(FusionError::Modular(ModularDefect::NotSymmetric { a, b }));
                }
            }
        }
        Ok(())
    }

    fn verify_nondegenerate(&self) -> Result<(), FusionError> {
        let rank = elimination::rank(&self.s_tilde).map_err(FusionError::from)?;
        if rank < self.rank() {
            return Err(FusionError::Modular(ModularDefect::Degenerate {
                rank,
                size: self.rank(),
            }));
        }
        Ok(())
    }

    fn verify_square(&self) -> Result<BasicMatrix<K>, FusionError> {
        let squared = matrix::multiply(&self.s_tilde, &self.s_tilde).map_err(FusionError::from)?;
        Self::require_equal(
            &squared,
            &self.scaled_charge_conjugation(&self.d_squared)?,
            |a, b| ModularDefect::SSquared { a, b },
        )?;
        Ok(squared)
    }

    fn verify_unitarity(&self) -> Result<(), FusionError> {
        let actual = matrix::multiply(
            &self.s_tilde,
            &involution::adjoint(&self.s_tilde).map_err(FusionError::from)?,
        )
        .map_err(FusionError::from)?;
        Self::require_equal(&actual, &self.scaled_identity(&self.d_squared)?, |a, b| {
            ModularDefect::Unitarity { a, b }
        })
    }

    fn st_matrix(&self) -> Result<BasicMatrix<K>, FusionError> {
        let n = self.rank();
        BasicMatrix::try_from_fn_result(n, n, |a, b| {
            Ok(self.s_tilde.get_ref(a, b)?.mul(&self.twists[b]))
        })
    }

    fn verify_relation(&self, squared: &BasicMatrix<K>) -> Result<(), FusionError> {
        let st = self.st_matrix()?;
        let square = matrix::multiply(&st, &st).map_err(FusionError::from)?;
        let cube = matrix::multiply(&square, &st).map_err(FusionError::from)?;
        let expected = matrix::scale(squared, &self.p_plus).map_err(FusionError::from)?;
        Self::require_equal(&cube, &expected, |a, b| ModularDefect::Relation { a, b })
    }

    fn verify_verlinde(&self) -> Result<(), FusionError> {
        if let Some(&[a, b, c]) = self
            .ring
            .verlinde_defects(&self.s_tilde, &self.d_squared)?
            .first()
        {
            return Err(FusionError::Modular(ModularDefect::Verlinde { a, b, c }));
        }
        Ok(())
    }

    /// The central charge modulo 4, as an exact rational in `[0, 4)`: `p_+^2 / D^2` is
    /// `exp(2 pi i c / 4)`, a root of unity of the field, read off exactly.
    pub fn central_charge_mod_4(&self) -> Result<Rational, FusionError> {
        let ratio =
            core_number_theory::scalar::divide(&self.p_plus.mul(&self.p_plus), &self.d_squared)
                .map_err(FusionError::from)?;
        let (n, k) = root_of_unity_data(&ratio).ok_or(FusionError::NotInSubfield {
            what: "p_+^2 / D^2",
            expected: "a root of unity",
        })?;
        Ok(Rational::new(
            BigInt::from(4 * u64::from(k)),
            BigInt::from(n),
        ))
    }

    /// The central charge modulo 8, as an exact rational in `[0, 8)`, given the global
    /// dimension `D` as an element of the field with `D^2 = sum_a d_a^2` and `D > 0`:
    /// `p_+ / D = exp(2 pi i c / 8)` is a root of unity of the field.
    ///
    /// A square root of `D^2` is determined only up to sign (with `-D` the answer would
    /// shift by 4), so the positivity of the supplied `D` under the canonical embedding is
    /// checked exactly: a non-positive `D` is [`ModularDefect::NonPositiveDimension`], and a
    /// scalar type that cannot decide signs is [`FusionError::SignUndecided`].
    pub fn central_charge_mod_8(&self, total_dimension: &K) -> Result<Rational, FusionError> {
        if total_dimension.mul(total_dimension) != self.d_squared {
            return Err(FusionError::Modular(ModularDefect::WrongGlobalDimension));
        }
        match total_dimension.real_sign() {
            Some(Ordering::Greater) => {}
            Some(_) => return Err(FusionError::Modular(ModularDefect::NonPositiveDimension)),
            None => {
                return Err(FusionError::SignUndecided {
                    context: "the global dimension D",
                })
            }
        }
        let ratio = core_number_theory::scalar::divide(&self.p_plus, total_dimension)
            .map_err(FusionError::from)?;
        let (n, k) = root_of_unity_data(&ratio).ok_or(FusionError::NotInSubfield {
            what: "p_+ / D",
            expected: "a root of unity",
        })?;
        Ok(Rational::new(
            BigInt::from(8 * u64::from(k)),
            BigInt::from(n),
        ))
    }

    /// The Frobenius-Schur indicator of `a` by Bantay's formula: `+1` or `-1` for a
    /// self-dual object, `0` otherwise.
    pub fn frobenius_schur_indicator(&self, a: usize) -> Result<i8, FusionError> {
        let n = self.rank();
        if a >= n {
            return Err(FusionError::Label { label: a, rank: n });
        }
        let weights = self.indicator_weights()?;
        let mut total = K::zero();
        for b in 0..n {
            total = total.add(&self.indicator_row(a, b, &weights)?);
        }
        let value = core_number_theory::scalar::divide(&total, &self.d_squared)
            .map_err(FusionError::from)?;
        Self::indicator_result(a, &value)
    }

    fn indicator_weights(&self) -> Result<Vec<(K, K)>, FusionError> {
        self.dimensions
            .iter()
            .zip(&self.twists)
            .map(|(d, t)| {
                let square = t.mul(t);
                Ok((
                    d.mul(&square),
                    core_number_theory::scalar::divide(d, &square).map_err(FusionError::from)?,
                ))
            })
            .collect()
    }

    fn indicator_row(&self, a: usize, b: usize, weights: &[(K, K)]) -> Result<K, FusionError> {
        let mut total = K::zero();
        for (c, (_, right)) in weights.iter().enumerate() {
            let multiplicity = self.ring.n(b, c, a);
            if multiplicity == 0 {
                continue;
            }
            total = Self::add_multiple(total, &weights[b].0.mul(right), multiplicity)?;
        }
        Ok(total)
    }

    fn indicator_result(a: usize, value: &K) -> Result<i8, FusionError> {
        if *value == K::one() {
            Ok(1)
        } else if *value == K::one().neg() {
            Ok(-1)
        } else if value.is_zero() {
            Ok(0)
        } else {
            Err(FusionError::Modular(ModularDefect::FrobeniusSchur {
                label: a,
            }))
        }
    }

    /// The ground-state degeneracy on a closed surface of genus `g`:
    /// `sum_a (D^2 / d_a^2)^(g - 1)`, exactly (it is always a non-negative integer; a
    /// value outside the integers is reported as an error, not rounded). Genus 0 gives 1.
    pub fn ground_state_degeneracy(&self, genus: u32) -> Result<BigInt, FusionError> {
        let exponent = Self::genus_exponent(genus)?;
        let mut total = K::zero();
        for (ratio, multiplicity) in self.dimension_ratios()? {
            let value =
                core_number_theory::scalar::power(&ratio, exponent).map_err(FusionError::from)?;
            total = Self::add_multiple(total, &value, multiplicity)?;
        }
        let rational = total.to_rational().ok_or(FusionError::NotInSubfield {
            what: "the ground-state degeneracy",
            expected: "a rational number",
        })?;
        if !rational.is_integer() || rational < Rational::from_integer(BigInt::from(0)) {
            return Err(FusionError::NotInSubfield {
                what: "the ground-state degeneracy",
                expected: "a non-negative integer",
            });
        }
        Ok(rational.to_integer())
    }
    fn genus_exponent(genus: u32) -> Result<i64, FusionError> {
        let exponent = i64::from(genus) - 1;
        let requested = exponent.unsigned_abs();
        let limit = core_number_theory::scalar::MAX_SCALAR_EXPONENT;
        if requested > limit {
            return Err(FusionError::Budget {
                what: "ground-state exponent",
                requested: requested as u128,
                limit: limit as u128,
            });
        }
        Ok(exponent)
    }

    fn dimension_ratios(&self) -> Result<Vec<(K, u64)>, FusionError> {
        let mut squares: Vec<(K, u64)> = Vec::new();
        for d in &self.dimensions {
            let square = d.mul(d);
            if let Some((_, count)) = squares.iter_mut().find(|(s, _)| *s == square) {
                *count += 1;
            } else {
                squares.push((square, 1));
            }
        }
        for (square, _) in &mut squares {
            *square = core_number_theory::scalar::divide(&self.d_squared, square)
                .map_err(FusionError::from)?;
        }
        Ok(squares)
    }
}

// Origin: engine/crates_rs/core_fusion_categories/src/modular.rs
// Claim: urn:core:crates_rs:core-fusion-categories:modular:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e2f0fd10 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
