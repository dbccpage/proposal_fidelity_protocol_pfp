//! Finite floating-point Lp diagnostics, not exact quotient/proof evidence.
//!
//! Positive p<1 gives a quasi-norm and does not carry triangle-inequality status.
//! Positive infinity gives the maximum magnitude. Scaling avoids unnecessary
//! intermediate overflow/underflow; the result remains a floating approximation.
use serde::{Deserialize, Serialize};

/// Legacy floating L2 diagnostic. It preserves IEEE nonfinite/overflow behavior;
/// callers needing a checked finite magnitude use `lp_norm` instead.
pub fn l2_diagnostic(values: &[f64]) -> f64 {
    values.iter().map(|value| value * value).sum::<f64>().sqrt()
}

/// Exact L1 magnitude of cyclotomic coordinates in a declared real embedding.
pub fn cyclotomic_l1<const P: usize>(
    values: &[core_number_theory::cyclotomic_field::Cyclotomic<P>],
    embedding: i64,
) -> Result<
    core_number_theory::cyclotomic_field::Cyclotomic<P>,
    core_number_theory::real_embedding::EmbeddingError,
> {
    use core_number_theory::cyclotomic_field::Cyclotomic;
    let mut signs = core_number_theory::real_embedding::RealEmbeddings::new(P)?;
    let mut result = Cyclotomic::<P>::zero();
    for value in values {
        let sign = signs.sign_under_embedding(value.as_number(), embedding)?;
        result = result.add(&if sign == std::cmp::Ordering::Less {
            value.neg()
        } else {
            value.clone()
        });
    }
    Ok(result)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum LpKind {
    Norm,
    QuasiNorm,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum LpNormError {
    #[error("LP_INVALID_ORDER: positive finite p or positive infinity required")]
    InvalidOrder,
    #[error("LP_NONFINITE_INPUT: index {index}")]
    NonFiniteInput { index: usize },
    #[error("LP_UNREPRESENTABLE_MAGNITUDE")]
    UnrepresentableMagnitude,
}

/// Checked finite approximate magnitude. Not a theorem, quotient distance,
/// normalized quantum state, error-bound certificate or actor authorization.
///
/// No unchecked constructor or wire deserializer is supplied.
///
/// ~~~compile_fail
/// use core_functional::norms::{LpKind, LpMagnitude};
/// let forged = LpMagnitude { value: 1.0, order: 0.0, kind: LpKind::Norm };
/// ~~~
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct LpMagnitude {
    value: f64,
    order: f64,
    kind: LpKind,
}

impl LpMagnitude {
    pub fn value(&self) -> f64 {
        self.value
    }

    pub fn order(&self) -> f64 {
        self.order
    }

    pub fn kind(&self) -> LpKind {
        self.kind
    }
}

/// Compute a finite approximate (sum |x_i|^p)^(1/p), with p=+infinity
/// interpreted as max |x_i| and the empty vector assigned zero.
///
/// No global rounding-error bound or mathematical exactness is claimed. All
/// submitted coordinates are checked even for the infinity norm. A nonfinite
/// result is a typed refusal, never infinity, NaN or a substituted zero.
pub fn lp_norm(values: &[f64], p: f64) -> Result<LpMagnitude, LpNormError> {
    if p.is_nan() || p <= 0.0 {
        return Err(LpNormError::InvalidOrder);
    }
    let mut scale = 0.0_f64;
    let mut nonzero = 0;
    for (index, value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(LpNormError::NonFiniteInput { index });
        }
        scale = scale.max(value.abs());
        nonzero += usize::from(*value != 0.0);
    }
    let kind = if p < 1.0 {
        LpKind::QuasiNorm
    } else {
        LpKind::Norm
    };
    // These cases have an exact finite f64 representation and need no powers.
    // Infinity is a defined norm order, not permission for nonfinite coordinates.
    if nonzero <= 1 || p == f64::INFINITY {
        return Ok(LpMagnitude {
            value: scale,
            order: p,
            kind,
        });
    }

    let magnitude = if p >= 1.0 {
        let sum = values
            .iter()
            .map(|value| (value.abs() / scale).powf(p))
            .sum::<f64>();
        scale * sum.powf(1.0 / p)
    } else {
        // For small p, the unscaled power root can overflow while its product
        // with a tiny scale is representable. Use the log domain for that root.
        // log(abs(x))-log(scale) also avoids an underflowed abs(x)/scale ratio.
        let log_scale = scale.ln();
        let sum = values
            .iter()
            .filter(|value| **value != 0.0)
            .map(|value| (p * (value.abs().ln() - log_scale)).exp())
            .sum::<f64>();
        (log_scale + sum.ln() / p).exp()
    };
    if !magnitude.is_finite() {
        return Err(LpNormError::UnrepresentableMagnitude);
    }
    // Every positive-order magnitude is at least max |x_i|. Log/exp rounding
    // must not turn the diagnostic into a smaller value or an underflowed zero.
    Ok(LpMagnitude {
        value: magnitude.max(scale),
        order: p,
        kind,
    })
}

// Origin: engine/crates_rs/core_functional/src/norms.rs
// Claim: urn:core:crates_rs:core-functional:norms:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn close(actual: f64, expected: f64, relative: f64) {
        assert!(actual.is_finite() && expected.is_finite());
        assert!(
            (actual / expected - 1.0).abs() <= relative,
            "{actual:?} != {expected:?}"
        );
    }

    #[test]
    fn known_lp_values_preserve_sign_symmetry_order_and_empty_convention() {
        let values = [-3.0, 4.0];
        for (p, expected) in [(1.0, 7.0), (2.0, 5.0), (f64::INFINITY, 4.0)] {
            let result = lp_norm(&values, p).unwrap();
            close(result.value(), expected, 1e-14);
            assert_eq!(result.kind(), LpKind::Norm);
            assert_eq!(result.order(), p);
            assert_eq!(lp_norm(&[], p).unwrap().value(), 0.0);
        }
        close(
            lp_norm(&[1.0, 2.0, 2.0], 3.0).unwrap().value(),
            2.5712815906582354,
            1e-14,
        );
        close(lp_norm(&[-4.0, 9.0], 0.5).unwrap().value(), 25.0, 1e-14);
    }

    #[test]
    fn quasi_norms_do_not_acquire_triangle_inequality_status() {
        let joined = lp_norm(&[1.0, 1.0], 0.5).unwrap();
        let separate = lp_norm(&[1.0], 0.5).unwrap().value() * 2.0;
        assert_eq!(joined.kind(), LpKind::QuasiNorm);
        close(joined.value(), 4.0, 1e-14);
        assert!(joined.value() > separate);
        assert_eq!(lp_norm(&[1.0, 1.0], 1.0).unwrap().kind(), LpKind::Norm);
    }

    #[test]
    fn scaling_avoids_spurious_overflow_and_underflow_at_order_two() {
        let high = lp_norm(&[1e308, -1e308], 2.0).unwrap().value();
        let low = lp_norm(&[1e-300, -1e-300], 2.0).unwrap().value();
        close(high / 1e308, 2.0_f64.sqrt(), 1e-14);
        close(low / 1e-300, 2.0_f64.sqrt(), 1e-14);
        assert!(low > 0.0);
    }

    #[test]
    fn log_domain_preserves_representable_roots_small_terms_and_scale_floor() {
        // Independent 100-digit Decimal oracle:
        // Decimal.from_float(1e-300) * 2**2000.
        let magnitude = lp_norm(&[1e-300, 1e-300], 0.0005).unwrap().value();
        close(magnitude, 1.1481306952742546e302, 5e-12);
        // Widely separated coordinates still contribute for small p.
        close(
            lp_norm(&[1e200, 1e-200], 0.01).unwrap().value(),
            1.0100496620928765e200,
            5e-12,
        );
        // The tiny coordinate cannot change the nearest f64 magnitude here,
        // and exp(log(scale)) must not round the answer below max |x_i|.
        assert_eq!(lp_norm(&[1e300, 1e-300], 0.5).unwrap().value(), 1e300);
    }

    #[test]
    fn invalid_orders_are_refused_even_when_the_vector_is_empty() {
        for p in [0.0, -0.0, -1.0, f64::NEG_INFINITY, f64::NAN] {
            assert_eq!(lp_norm(&[], p), Err(LpNormError::InvalidOrder));
            assert_eq!(lp_norm(&[1.0], p), Err(LpNormError::InvalidOrder));
        }
        assert!(lp_norm(&[1.0, 2.0], f64::INFINITY).is_ok());
    }

    #[test]
    fn nonfinite_coordinates_are_refused_including_the_infinity_order() {
        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            for p in [0.5, 1.0, 2.0, f64::INFINITY] {
                assert_eq!(
                    lp_norm(&[1.0, value], p),
                    Err(LpNormError::NonFiniteInput { index: 1 })
                );
            }
        }
    }

    #[test]
    fn unrepresentable_results_are_refusals_not_infinities_or_zero() {
        assert_eq!(
            lp_norm(&[f64::MAX, f64::MAX], 1.0),
            Err(LpNormError::UnrepresentableMagnitude)
        );
        assert_eq!(
            lp_norm(&[1.0, 1.0], 1e-6),
            Err(LpNormError::UnrepresentableMagnitude)
        );
        assert_eq!(
            lp_norm(&[f64::MAX, f64::MAX], f64::INFINITY)
                .unwrap()
                .value(),
            f64::MAX
        );
    }

    #[test]
    fn single_nonzero_and_zero_vectors_do_not_roundtrip_through_logs() {
        for value in [f64::from_bits(1), f64::MAX, -f64::MAX, 0.0, -0.0] {
            for p in [0.0001, 0.5, 1.0, 2.0, f64::INFINITY] {
                assert_eq!(
                    lp_norm(&[0.0, value, -0.0], p).unwrap().value(),
                    value.abs()
                );
            }
        }
    }

    #[test]
    fn positive_rescaling_and_coordinate_permutation_preserve_the_diagnostic() {
        let base = lp_norm(&[-1.0, 2.0, -3.0], 3.5).unwrap();
        let scaled = lp_norm(&[-21.0, -7.0, 14.0], 3.5).unwrap();
        close(scaled.value(), base.value() * 7.0, 1e-14);
        assert_eq!(base.kind(), LpKind::Norm);
    }
}
