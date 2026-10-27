//! The original quantum scalar constants regression, at the canonical carrier home.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use linear_algebra::linear_algebra::complex_matrix::C64;

    #[test]
    fn test_c64_constants() {
        let z0 = C64::ZERO;
        let z1 = C64::ONE;
        assert_eq!(z0.re, 0.0);
        assert_eq!(z0.im, 0.0);
        assert_eq!(z1.re, 1.0);
        assert_eq!(z1.im, 0.0);
        assert_eq!(z1.norm_sqr(), 1.0);
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_linear_algebra/qm_complex_regression.rs
// Claim: urn:core:linear-algebra:gaussian-integer:norm-multiplicativity:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
struct GaussNorm {
    product_norm: i64,
    factor_product: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum GaussNormError {
    Overflow,
    NotMultiplicative { product_norm: i64, factor_product: i64 },
}

// Origin: engine/crates_rs/tests/core_linear_algebra/qm_complex_regression.rs
// Claim: urn:core:crates_rs:tests:qm-complex-regression:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GaussNormError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GaussNormError {}

fn square_sum(real: i64, imag: i64) -> Result<i64, GaussNormError> {
    let real_sq = real.checked_mul(real).ok_or(GaussNormError::Overflow)?;
    let imag_sq = imag.checked_mul(imag).ok_or(GaussNormError::Overflow)?;
    real_sq.checked_add(imag_sq).ok_or(GaussNormError::Overflow)
}

fn gauss_mul(z_re: i64, z_im: i64, w_re: i64, w_im: i64) -> Result<(i64, i64), GaussNormError> {
    let ac = z_re.checked_mul(w_re).ok_or(GaussNormError::Overflow)?;
    let bd = z_im.checked_mul(w_im).ok_or(GaussNormError::Overflow)?;
    let ad = z_re.checked_mul(w_im).ok_or(GaussNormError::Overflow)?;
    let bc = z_im.checked_mul(w_re).ok_or(GaussNormError::Overflow)?;
    let real = ac.checked_sub(bd).ok_or(GaussNormError::Overflow)?;
    let imag = ad.checked_add(bc).ok_or(GaussNormError::Overflow)?;
    Ok((real, imag))
}

fn try_gauss_norm(z_re: i64, z_im: i64, w_re: i64, w_im: i64) -> Result<GaussNorm, GaussNormError> {
    let (real, imag) = gauss_mul(z_re, z_im, w_re, w_im)?;
    let product_norm = square_sum(real, imag)?;
    let factor_product = square_sum(z_re, z_im)?
        .checked_mul(square_sum(w_re, w_im)?)
        .ok_or(GaussNormError::Overflow)?;
    if product_norm != factor_product {
        return Err(GaussNormError::NotMultiplicative {
            product_norm,
            factor_product,
        });
    }
    Ok(GaussNorm {
        product_norm,
        factor_product,
    })
}

#[cfg(test)]
mod gaussian_integer_norm_tests {
    use super::{try_gauss_norm, GaussNormError};

    #[test]
    fn the_norm_of_one_plus_i_times_one_minus_i_is_four() {
        let witness = try_gauss_norm(1, 1, 1, -1);
        assert!(matches!(
            witness,
            Ok(ref row) if row.product_norm == 4 && row.factor_product == 4
        ));
    }

    #[test]
    fn refuses_a_square_that_overflows() {
        assert!(matches!(try_gauss_norm(i64::MAX, 1, 1, 0), Err(GaussNormError::Overflow)));
    }
}
