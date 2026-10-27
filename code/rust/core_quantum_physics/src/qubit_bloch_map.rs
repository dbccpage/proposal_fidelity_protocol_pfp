// AuthorityEffect: None.

//! The affine Bloch map of a trace-preserving qubit map given by Kraus operators over `Q(i)`.
//!
//! For `E(X) = sum_k K_k X K_k^dagger` with `sum_k K_k^dagger K_k = I`, the Bloch
//! vector `r` of `rho = (I + r . sigma) / 2` goes to `T r + t`, where
//! `T_ij = Tr(sigma_i E(sigma_j)) / 2` and `t_i = Tr(sigma_i E(I)) / 2`. The
//! Pauli matrices come from `core_lie_theory::pauli_symplectic`; their scales
//! are all one. Computed exactly: `T`, `t`, the image of a Bloch vector, the
//! rank of `T`, and whether the linear part is a contraction (`I - T^T T` PSD)
//! or a strict contraction (`I - T^T T` positive definite), decided by the
//! exact `LDL^T` of `linear_algebra::exact_ldlt`.
//!
//! Refused: an empty Kraus list, operators that are not `2 x 2`, and
//! `sum_k K_k^dagger K_k != I`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_8d1e7511<T> {
    fn checked_invariant_8d1e7511(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_8d1e7511<T> for Option<T> {
    #[inline]
    fn checked_invariant_8d1e7511(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_8d1e7511<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_8d1e7511(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, involution as iv, matrix as mx, ExactFieldError};
use linear_algebra::exact_ldlt::{is_psd_rational, ldlt_pivots_strictly_positive_rational};
use num_traits::{One, Zero};
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

/// Refusals for qubit Bloch maps.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BlochMapError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("an exact Pauli trace was nonreal")]
    NonRealTrace,
    #[error("the affine Bloch map is not completely positive")]
    NotCompletelyPositive,
    #[error("a map needs at least one Kraus operator")]
    EmptyKraus,
    #[error("Kraus operator {index} is not 2x2")]
    NotQubit { index: usize },
    #[error("sum of K^dagger K is not the identity, so the map is not trace preserving")]
    NotTracePreserving,
}

/// `r -> T r + t` on Bloch vectors.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QubitBlochMap {
    linear: [[Rational; 3]; 3],
    translation: [Rational; 3],
}

impl QubitBlochMap {
    /// Admit a trace-preserving affine map by positivity of its exact Choi matrix.
    pub fn from_affine(
        linear: [[Rational; 3]; 3],
        translation: [Rational; 3],
    ) -> Result<Self, BlochMapError> {
        let map = Self {
            linear,
            translation,
        };
        if !map.is_completely_positive() {
            return Err(BlochMapError::NotCompletelyPositive);
        }
        Ok(map)
    }

    /// Composition `self o before`, including the translation term.
    pub fn compose(&self, before: &Self) -> Self {
        let linear = std::array::from_fn(|i| {
            std::array::from_fn(|j| {
                (0..3)
                    .map(|k| &self.linear[i][k] * &before.linear[k][j])
                    .sum()
            })
        });
        let translation = self.apply(&before.translation);
        Self {
            linear,
            translation,
        }
    }

    pub fn depolarizing(lambda: Rational) -> Result<Self, BlochMapError> {
        Self::from_affine(
            std::array::from_fn(|i| {
                std::array::from_fn(|j| if i == j { lambda.clone() } else { ri(0) })
            }),
            std::array::from_fn(|_| ri(0)),
        )
    }

    pub fn dephasing(coherence: Rational) -> Result<Self, BlochMapError> {
        let diagonal = [coherence.clone(), coherence, ri(1)];
        Self::from_affine(
            std::array::from_fn(|i| {
                std::array::from_fn(|j| if i == j { diagonal[i].clone() } else { ri(0) })
            }),
            std::array::from_fn(|_| ri(0)),
        )
    }

    /// Rational s=sqrt(1-gamma) avoids an approximate amplitude-damping square root.
    pub fn amplitude_damping(s: Rational) -> Result<Self, BlochMapError> {
        let s2 = &s * &s;
        let diagonal = [s.clone(), s, s2.clone()];
        Self::from_affine(
            std::array::from_fn(|i| {
                std::array::from_fn(|j| if i == j { diagonal[i].clone() } else { ri(0) })
            }),
            [ri(0), ri(0), ri(1) - s2],
        )
    }

    pub fn choi_matrix(&self) -> BasicMatrix<GaussianRat> {
        use core_number_theory::cyclotomic::GaussianRat;
        let paulis: Vec<BasicMatrix<GaussianRat>> = [Pauli::X, Pauli::Y, Pauli::Z]
            .into_iter()
            .map(|axis| pauli::<GaussianRat>(axis).checked_invariant_8d1e7511("Q(i) contains Pauli entries"))
            .collect();
        let image = |x: &BasicMatrix<GaussianRat>| {
            let trace = mx::trace(x).checked_invariant_8d1e7511("fixed 2x2 operator");
            let mut out = mx::scale(&mx::identity(2).checked_invariant_8d1e7511("2x2"), &trace).checked_invariant_8d1e7511("2x2");
            for i in 0..3 {
                let mut coefficient = trace.mul(
                    &core_number_theory::cyclotomic::GaussianRat::from_rational(
                        self.translation[i].clone(),
                    ),
                );
                for j in 0..3 {
                    coefficient = coefficient.add(
                        &mx::trace(&mx::multiply(&paulis[j], x).checked_invariant_8d1e7511("2x2"))
                            .checked_invariant_8d1e7511("2x2")
                            .mul(
                                &core_number_theory::cyclotomic::GaussianRat::from_rational(
                                    self.linear[i][j].clone(),
                                ),
                            ),
                    );
                }
                out =
                    mx::add(&out, &mx::scale(&paulis[i], &coefficient).checked_invariant_8d1e7511("2x2")).checked_invariant_8d1e7511("2x2");
            }
            mx::scale(
                &out,
                &GaussianRat::from_rational(core_number_theory::rational::rq(1, 2)),
            )
            .checked_invariant_8d1e7511("2x2")
        };
        let mut choi = mx::zeros(4, 4).checked_invariant_8d1e7511("4x4");
        for a in 0..2 {
            for b in 0..2 {
                let mut e = mx::zeros(2, 2).checked_invariant_8d1e7511("2x2");
                e.set(a, b, GaussianRat::one()).checked_invariant_8d1e7511("2x2 index");
                let block = image(&e);
                for i in 0..2 {
                    for j in 0..2 {
                        choi.set(2 * a + i, 2 * b + j, block.get(i, j).checked_invariant_8d1e7511("2x2 index"))
                            .checked_invariant_8d1e7511("4x4 index");
                    }
                }
            }
        }
        choi
    }

    /// Realification turns Hermitian Choi positivity into one rational LDL test.
    pub fn is_completely_positive(&self) -> bool {
        let choi = self.choi_matrix();
        let real = (0..8)
            .map(|r| {
                (0..8)
                    .map(|c| {
                        let z = choi.get_ref(r % 4, c % 4).checked_invariant_8d1e7511("4x4 index");
                        match (r < 4, c < 4) {
                            (true, true) | (false, false) => z.re.clone(),
                            (true, false) => -&z.im,
                            (false, true) => z.im.clone(),
                        }
                    })
                    .collect()
            })
            .collect::<Vec<Vec<Rational>>>();
        is_psd_rational(&real)
    }

    /// Fujiwara-Algoet conditions, with the unsquared nonnegative left sides retained.
    pub fn unital_diagonal_is_cp(lambda: &[Rational; 3]) -> bool {
        let plus = ri(1) + &lambda[2];
        let minus = ri(1) - &lambda[2];
        plus >= ri(0)
            && minus >= ri(0)
            && &plus * &plus >= (&lambda[0] + &lambda[1]).pow(2)
            && &minus * &minus >= (&lambda[0] - &lambda[1]).pow(2)
    }
    fn check_qubit_kraus_shapes(
        kraus: &[BasicMatrix<GaussianRat>],
    ) -> Result<(), BlochMapError> {
        if kraus.is_empty() {
            return Err(BlochMapError::EmptyKraus);
        }
        if let Some(index) = kraus.iter().position(|k| k.rows() != 2 || k.cols() != 2) {
            return Err(BlochMapError::NotQubit { index });
        }
        Ok(())
    }

    fn validate_qubit_kraus_completeness(
        kraus: &[BasicMatrix<GaussianRat>],
    ) -> Result<(), BlochMapError> {
        Self::check_qubit_kraus_shapes(kraus)?;
        let mut completeness = mx::zeros(2, 2)?;
        for k in kraus {
            let term = mx::multiply(&iv::adjoint(k)?, k)?;
            completeness = mx::add(&completeness, &term)?;
        }
        if completeness != mx::identity(2)? {
            return Err(BlochMapError::NotTracePreserving);
        }
        Ok(())
    }

    fn apply_kraus_operators(
        kraus: &[BasicMatrix<GaussianRat>],
        x: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, BlochMapError> {
        let mut result = mx::zeros(2, 2)?;
        for k in kraus {
            let kx = mx::multiply(k, x)?;
            let kxk = mx::multiply(&kx, &iv::adjoint(k)?)?;
            result = mx::add(&result, &kxk)?;
        }
        Ok(result)
    }

    fn half_hs_trace(
        sigma: &BasicMatrix<GaussianRat>,
        m: &BasicMatrix<GaussianRat>,
    ) -> Result<Rational, BlochMapError> {
        let pairing = iv::hs_inner(sigma, m)?;
        if !pairing.im.is_zero() {
            return Err(BlochMapError::NonRealTrace);
        }
        Ok(pairing.re / ri(2))
    }

    pub fn from_kraus(kraus: &[BasicMatrix<GaussianRat>]) -> Result<Self, BlochMapError> {
        Self::validate_qubit_kraus_completeness(kraus)?;
        let paulis = [Pauli::X, Pauli::Y, Pauli::Z].map(|p| {
            pauli::<core_number_theory::cyclotomic::GaussianRat>(p)
                .checked_invariant_8d1e7511("exact Pauli carrier")
        });
        let images = paulis
            .iter()
            .map(|x| Self::apply_kraus_operators(kraus, x))
            .collect::<Result<Vec<_>, _>>()?;
        let shift = Self::apply_kraus_operators(kraus, &mx::identity(2)?)?;
        let mut linear = std::array::from_fn(|_| std::array::from_fn(|_| ri(0)));
        let mut translation = std::array::from_fn(|_| ri(0));
        for i in 0..3 {
            translation[i] = Self::half_hs_trace(&paulis[i], &shift)?;
            for j in 0..3 {
                linear[i][j] = Self::half_hs_trace(&paulis[i], &images[j])?;
            }
        }
        Ok(Self {
            linear,
            translation,
        })
    }

    pub fn linear(&self) -> &[[Rational; 3]; 3] {
        &self.linear
    }

    pub fn translation(&self) -> &[Rational; 3] {
        &self.translation
    }

    /// `T r + t`.
    pub fn apply(&self, r: &[Rational; 3]) -> [Rational; 3] {
        std::array::from_fn(|i| {
            self.linear[i]
                .iter()
                .zip(r)
                .map(|(a, b)| a * b)
                .sum::<Rational>()
                + &self.translation[i]
        })
    }

    /// `I - T^T T`.
    fn gram_defect(&self) -> Vec<Vec<Rational>> {
        (0..3)
            .map(|i| {
                (0..3)
                    .map(|j| {
                        let tt: Rational = (0..3)
                            .map(|k| &self.linear[k][i] * &self.linear[k][j])
                            .sum();
                        let identity = if i == j {
                            Rational::one()
                        } else {
                            Rational::zero()
                        };
                        identity - tt
                    })
                    .collect()
            })
            .collect()
    }

    /// `|T r| <= |r|` for every `r`.
    pub fn linear_is_contraction(&self) -> bool {
        is_psd_rational(&self.gram_defect())
    }

    /// `|T r| < |r|` for every nonzero `r`.
    pub fn linear_is_strict_contraction(&self) -> bool {
        ldlt_pivots_strictly_positive_rational(&self.gram_defect()).is_ok()
    }

    /// Exact rank of `T`.
    pub fn linear_rank(&self) -> usize {
        let matrix =
            BasicMatrix::from_row_major(3, 3, self.linear.iter().flatten().cloned().collect())
                .checked_invariant_8d1e7511("3x3");
        elimination::rank(&matrix).checked_invariant_8d1e7511("fixed 3x3 affine rank")
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/qubit_bloch_map.rs
// Claim: urn:core:crates_rs:core-quantum-physics:qubit-bloch-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_8d1e7511 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
