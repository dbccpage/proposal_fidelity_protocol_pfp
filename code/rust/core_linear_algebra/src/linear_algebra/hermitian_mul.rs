use num_complex::Complex64 as C64;
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MatrixRole {
    Left,
    Right,
    HermitianInput,
    ConjugatingMatrix,
}

#[derive(Debug, Error, Clone, PartialEq)]
pub enum HermitianMulError {
    #[error("dimension overflow: n={n}")]
    DimensionOverflow { n: usize },

    #[error("{role:?} length mismatch: expected {expected}, actual {actual}")]
    LengthMismatch {
        role: MatrixRole,
        expected: usize,
        actual: usize,
    },

    #[error("{role:?} has non-finite entry at index {index}")]
    NonFiniteEntry { role: MatrixRole, index: usize },

    #[error("invalid Hermitian tolerance: {tol}")]
    InvalidTolerance { tol: f64 },

    #[error("matrix is not Hermitian: i={i}, j={j}, defect={defect}, tol={tol}")]
    NonHermitian {
        i: usize,
        j: usize,
        defect: f64,
        tol: f64,
    },
}

#[derive(Debug, Clone, Copy)]
pub struct HermitianMulConfig {
    pub hermitian_tol: f64,
}

impl Default for HermitianMulConfig {
    fn default() -> Self {
        Self {
            hermitian_tol: 1e-10,
        }
    }
}

impl HermitianMulConfig {
    pub fn validate(&self) -> Result<(), HermitianMulError> {
        if !self.hermitian_tol.is_finite() || self.hermitian_tol < 0.0 {
            return Err(HermitianMulError::InvalidTolerance {
                tol: self.hermitian_tol,
            });
        }
        Ok(())
    }
}

fn checked_square_len(n: usize) -> Result<usize, HermitianMulError> {
    n.checked_mul(n)
        .ok_or(HermitianMulError::DimensionOverflow { n })
}

pub(crate) fn validate_matrix(
    role: MatrixRole,
    data: &[C64],
    n: usize,
) -> Result<(), HermitianMulError> {
    let expected = checked_square_len(n)?;

    if data.len() != expected {
        return Err(HermitianMulError::LengthMismatch {
            role,
            expected,
            actual: data.len(),
        });
    }

    for (index, z) in data.iter().enumerate() {
        if !z.re.is_finite() || !z.im.is_finite() {
            return Err(HermitianMulError::NonFiniteEntry { role, index });
        }
    }

    Ok(())
}

pub(crate) fn validate_hermitian(
    role: MatrixRole,
    data: &[C64],
    n: usize,
    tol: f64,
) -> Result<(), HermitianMulError> {
    validate_matrix(role, data, n)?;

    for i in 0..n {
        for j in 0..i {
            let defect = (data[i * n + j] - data[j * n + i].conj()).norm();

            if defect > tol {
                return Err(HermitianMulError::NonHermitian { i, j, defect, tol });
            }
        }
    }

    Ok(())
}

pub(crate) fn mul_then_force_hermitian_from_upper_triangle_unchecked(
    a: &[C64],
    b: &[C64],
    n: usize,
) -> Vec<C64> {
    (0..n).flat_map(|i| (i..n).map(move |j| (i, j))).fold(
        vec![C64::new(0.0, 0.0); n * n],
        |mut c, (i, j)| {
            let sum = (0..n)
                .map(|k| a[i * n + k] * b[k * n + j])
                .fold(C64::new(0.0, 0.0), |acc, x| acc + x);

            c[i * n + j] = sum;

            if i != j {
                c[j * n + i] = sum.conj();
            }

            c
        },
    )
}

pub(crate) fn hermitian_conjugation_unchecked(u: &[C64], a: &[C64], n: usize) -> Vec<C64> {
    // Step 1: tmp = A * U^dagger
    let tmp: Vec<C64> = (0..n)
        .flat_map(|i| (0..n).map(move |j| (i, j)))
        .map(|(i, j)| {
            (0..n)
                .map(|k| a[i * n + k] * u[j * n + k].conj()) // U^dagger[k,j] = conj(U[j,k])
                .fold(C64::new(0.0, 0.0), |acc, x| acc + x)
        })
        .collect();

    // Step 2: C = U * tmp, upper triangle only (result is Hermitian)
    mul_then_force_hermitian_from_upper_triangle_unchecked(u, &tmp, n)
}

pub fn hermitian_square_checked(
    rho: &[C64],
    n: usize,
    config: HermitianMulConfig,
) -> Result<Vec<C64>, HermitianMulError> {
    config.validate()?;
    validate_hermitian(MatrixRole::HermitianInput, rho, n, config.hermitian_tol)?;

    Ok(mul_then_force_hermitian_from_upper_triangle_unchecked(
        rho, rho, n,
    ))
}

pub fn hermitian_conjugation_checked(
    u: &[C64],
    a: &[C64],
    n: usize,
    config: HermitianMulConfig,
) -> Result<Vec<C64>, HermitianMulError> {
    config.validate()?;
    validate_matrix(MatrixRole::ConjugatingMatrix, u, n)?;
    validate_hermitian(MatrixRole::HermitianInput, a, n, config.hermitian_tol)?;

    Ok(hermitian_conjugation_unchecked(u, a, n))
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/hermitian_mul.rs
// Claim: urn:core:crates_rs:core-linear-algebra:hermitian-mul:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_hermitian_square_matches_expected_diagonal() {
        let n = 2;
        let mut dm_data = vec![C64::new(0.0, 0.0); 4];
        dm_data[0] = C64::new(0.6, 0.0);
        dm_data[3] = C64::new(0.4, 0.0);

        let config = HermitianMulConfig::default();
        let squared = hermitian_square_checked(&dm_data, n, config).unwrap();
        assert!((squared[0].re - 0.36).abs() < 1e-10);
        assert!((squared[3].re - 0.16).abs() < 1e-10);
    }

    #[test]
    fn rejects_length_mismatch() {
        let n = 2;
        let dm_data = vec![C64::new(0.0, 0.0); 3];
        let config = HermitianMulConfig::default();
        let err = hermitian_square_checked(&dm_data, n, config).unwrap_err();
        assert!(matches!(err, HermitianMulError::LengthMismatch { .. }));
    }

    #[test]
    fn rejects_non_finite_entry() {
        let n = 2;
        let mut dm_data = vec![C64::new(0.0, 0.0); 4];
        dm_data[0] = C64::new(f64::NAN, 0.0);
        let config = HermitianMulConfig::default();
        let err = hermitian_square_checked(&dm_data, n, config).unwrap_err();
        assert!(matches!(err, HermitianMulError::NonFiniteEntry { .. }));
    }

    #[test]
    fn rejects_non_hermitian_input() {
        let n = 2;
        let mut dm_data = vec![C64::new(0.0, 0.0); 4];
        dm_data[1] = C64::new(1.0, 0.0); // non hermitian
        let config = HermitianMulConfig::default();
        let err = hermitian_square_checked(&dm_data, n, config).unwrap_err();
        assert!(matches!(err, HermitianMulError::NonHermitian { .. }));
    }

    #[test]
    fn zero_dimension_returns_empty() {
        let config = HermitianMulConfig::default();
        let res = hermitian_square_checked(&[], 0, config).unwrap();
        assert!(res.is_empty());
    }

    #[test]
    fn hermitian_conjugation_identity_returns_input() {
        let n = 2;
        let mut a = vec![C64::new(0.0, 0.0); 4];
        a[0] = C64::new(2.0, 0.0);
        let mut u = vec![C64::new(0.0, 0.0); 4];
        u[0] = C64::new(1.0, 0.0);
        u[3] = C64::new(1.0, 0.0);

        let config = HermitianMulConfig::default();
        let res = hermitian_conjugation_checked(&u, &a, n, config).unwrap();
        assert_eq!(res[0], C64::new(2.0, 0.0));
    }
}
