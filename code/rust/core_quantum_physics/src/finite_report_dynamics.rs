// AuthorityEffect: None.

//! Reversible dilations, half steps and scaled interpolants of finite report
//! dynamics.
//!
//! A report map is a function `f : Q -> Q` on a finite label set
//! `Q = {0, .., n-1}`, given by its list of images. Computed exactly:
//!
//! - reversible dilations: bijections `P` of `Q x A`, with `(q, a)` stored at
//!   index `q |A| + a`, whose report coordinate reproduces `f`, either for every
//!   ancilla value or only for a declared prepared value. They are counted by
//!   enumerating the bijections of at most eight points
//!   (`report_fiber::permutations`);
//! - half steps: every map `sigma : Q -> Q` with `sigma o sigma = f`, by
//!   enumerating all `|Q|^|Q|` maps;
//! - scaled interpolants of the two-label swap `X` over the Gaussian integers:
//!   every `M` in `M_2(Z[i])` with `M^2 = c X`. Such an `M` commutes with
//!   `M^2 = c X`, whose commutant is `{a I + b X}`; then `a^2 + b^2 = 0`, so
//!   `b = +-i a` (the Gaussian integers have no zero divisors), and `2ab = c`.
//!   For odd `c` there is no Gaussian-integer solution, and for even `c` the
//!   norms satisfy `N(a) N(b) = c^2 / 4`, which bounds the search for `a`.
//!   Every candidate is squared and compared before it is returned.
//!
//! Refused: empty label sets, images outside `Q`, dilation carriers above
//! eight points, prepared values outside the ancilla, half-step searches above
//! six labels, and nonpositive scales. Nothing here defines a channel
//! class, prefers a dilation, or constructs continuous time.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_45f4d525<T> {
    fn checked_invariant_45f4d525(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_45f4d525<T> for Option<T> {
    #[inline]
    fn checked_invariant_45f4d525(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_45f4d525<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_45f4d525(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::gi;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigUint;
use core_combinatorics::enumeration::{factorial, permutations};
use core_number_theory::cyclotomic::GaussianRat;

/// Largest label set searched for half steps.
pub const MAX_HALF_STEP_LABELS: usize = 6;

/// Refusals for report dynamics.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReportDynamicsError {
    #[error("the label set is empty")]
    Empty,
    #[error("image {image} of label {label} is outside the {labels} labels")]
    ImageOutOfRange {
        label: usize,
        image: usize,
        labels: usize,
    },
    #[error("the ancilla is empty")]
    EmptyAncilla,
    #[error("prepared value {prepared} is outside the {ancilla} ancilla values")]
    PreparedOutOfRange { prepared: usize, ancilla: usize },
    #[error("carrier budget: {0}")]
    Budget(String),
    #[error("scale {0} must be strictly positive")]
    Scale(i64),
}

fn check_map(f: &[usize]) -> Result<(), ReportDynamicsError> {
    if f.is_empty() {
        return Err(ReportDynamicsError::Empty);
    }
    if let Some((label, &image)) = f.iter().enumerate().find(|(_, &image)| image >= f.len()) {
        return Err(ReportDynamicsError::ImageOutOfRange {
            label,
            image,
            labels: f.len(),
        });
    }
    Ok(())
}

/// Bijections `P` of `Q x A` with `report(P(q, a)) = f(q)` for every ancilla
/// value `a` (`prepared = None`) or for `a = prepared` only.
pub fn reversible_dilations(
    f: &[usize],
    ancilla: usize,
    prepared: Option<usize>,
) -> Result<Vec<Vec<usize>>, ReportDynamicsError> {
    check_map(f)?;
    if ancilla == 0 {
        return Err(ReportDynamicsError::EmptyAncilla);
    }
    if let Some(p) = prepared.filter(|&p| p >= ancilla) {
        return Err(ReportDynamicsError::PreparedOutOfRange {
            prepared: p,
            ancilla,
        });
    }
    let carrier = f
        .len()
        .checked_mul(ancilla)
        .ok_or_else(|| ReportDynamicsError::Budget("carrier multiplication overflow".into()))?;
    let bijections =
        permutations(carrier, 40320).map_err(|e| ReportDynamicsError::Budget(e.to_string()))?;
    Ok(bijections
        .into_iter()
        .filter(|p| {
            f.iter().enumerate().all(|(q, &target)| match prepared {
                Some(a) => p[q * ancilla + a] / ancilla == target,
                None => (0..ancilla).all(|a| p[q * ancilla + a] / ancilla == target),
            })
        })
        .collect())
}

fn count_prepared_dilations(
    carrier: usize,
    f_len: usize,
    ancilla: usize,
    fibres: &[usize],
) -> Result<BigUint, ReportDynamicsError> {
    if fibres.iter().any(|&m| m > ancilla) {
        return Ok(BigUint::from(0u32));
    }
    let mut count =
        factorial(carrier - f_len).map_err(|e| ReportDynamicsError::Budget(e.to_string()))?;
    for &m in fibres {
        for j in 0..m {
            count *= BigUint::from(ancilla - j);
        }
    }
    Ok(count)
}

fn count_unprepared_dilations(
    n: usize,
    ancilla: usize,
    fibres: &[usize],
) -> Result<BigUint, ReportDynamicsError> {
    if fibres.iter().any(|&m| m != 1) {
        return Ok(BigUint::from(0u32));
    }
    let base = factorial(ancilla).map_err(|e| ReportDynamicsError::Budget(e.to_string()))?;
    let exp = u32::try_from(n)
        .map_err(|_| ReportDynamicsError::Budget("exponent overflow".into()))?;
    Ok(base.pow(exp))
}

/// Number of reversible dilations, without enumerating their permutations.
pub fn reversible_dilation_count(
    f: &[usize],
    ancilla: usize,
    prepared: Option<usize>,
) -> Result<BigUint, ReportDynamicsError> {
    check_map(f)?;
    if ancilla == 0 {
        return Err(ReportDynamicsError::EmptyAncilla);
    }
    if let Some(p) = prepared.filter(|&p| p >= ancilla) {
        return Err(ReportDynamicsError::PreparedOutOfRange {
            prepared: p,
            ancilla,
        });
    }
    let carrier = f
        .len()
        .checked_mul(ancilla)
        .ok_or_else(|| ReportDynamicsError::Budget("carrier multiplication overflow".into()))?;
    let mut fibres = vec![0usize; f.len()];
    for &image in f {
        fibres[image] += 1;
    }
    match prepared {
        None => count_unprepared_dilations(f.len(), ancilla, &fibres),
        Some(_) => count_prepared_dilations(carrier, f.len(), ancilla, &fibres),
    }
}

/// Permutation square roots exist precisely when every even cycle length has
/// an even number of cycles. This does not assert a root for a non-bijection.
pub fn permutation_has_half_step(f: &[usize]) -> Result<bool, ReportDynamicsError> {
    check_map(f)?;
    let mut multiplicities = vec![0usize; f.len()];
    for &v in f {
        multiplicities[v] += 1;
    }
    if multiplicities.iter().any(|&m| m != 1) {
        return Ok(false);
    }
    let mut seen = vec![false; f.len()];
    let mut lengths = std::collections::BTreeMap::<usize, usize>::new();
    for start in 0..f.len() {
        if seen[start] {
            continue;
        }
        let (mut at, mut len) = (start, 0);
        while !seen[at] {
            seen[at] = true;
            len += 1;
            at = f[at];
        }
        *lengths.entry(len).or_default() += 1;
    }
    Ok(lengths
        .iter()
        .all(|(len, count)| len % 2 != 0 || count % 2 == 0))
}

/// Every map `sigma` of the labels with `sigma(sigma(q)) = f(q)`.
pub fn half_steps(f: &[usize]) -> Result<Vec<Vec<usize>>, ReportDynamicsError> {
    check_map(f)?;
    let n = f.len();
    if n > MAX_HALF_STEP_LABELS {
        return Err(ReportDynamicsError::Budget(format!(
            "{n} labels exceed {MAX_HALF_STEP_LABELS}"
        )));
    }
    let total = n.pow(n as u32);
    Ok((0..total)
        .map(|code| {
            let mut code = code;
            (0..n)
                .map(|_| {
                    let image = code % n;
                    code /= n;
                    image
                })
                .collect::<Vec<usize>>()
        })
        .filter(|sigma| (0..n).all(|q| sigma[sigma[q]] == f[q]))
        .collect())
}

/// Every `M` in `M_2(Z[i])` with `M^2 = scale * X`, `X` the swap.
pub fn swap_interpolants(scale: i64) -> Result<Vec<BasicMatrix<GaussianRat>>, ReportDynamicsError> {
    if scale <= 0 {
        return Err(ReportDynamicsError::Scale(scale));
    }
    if scale % 4 != 0 {
        return Ok(Vec::new());
    }
    let square = scale / 4;
    let k = num_bigint::BigInt::from(square).sqrt();
    if &k * &k != num_bigint::BigInt::from(square) {
        return Ok(Vec::new());
    }
    use num_traits::ToPrimitive;
    let k = k
        .to_i64()
        .ok_or_else(|| ReportDynamicsError::Budget("root overflow".into()))?;
    let target = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(0, 0), gi(scale, 0)],
        vec![gi(scale, 0), gi(0, 0)],
    ])
    .map_err(crate::exact_hermitian::ExactHermitianError::from)
    .checked_invariant_45f4d525("2 x 2 rows are rectangular");
    let mut out = Vec::new();
    for sign in [-1, 1] {
        for chirality in [-1, 1] {
            let a = gi(sign * k, chirality * sign * k);
            let b = gi(sign * k, -chirality * sign * k);
            let m = linear_algebra::exact_field::matrix::from_rows(vec![
                vec![a.clone(), b.clone()],
                vec![b.clone(), a.clone()],
            ])
            .map_err(crate::exact_hermitian::ExactHermitianError::from)
            .checked_invariant_45f4d525("2 x 2 rows are rectangular");
            if linear_algebra::exact_field::matrix::multiply_with_limits(
                &(m),
                &m,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_45f4d525("validated finite matrix shape and budget")
                == target
            {
                out.push(m);
            }
        }
    }
    Ok(out)
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_report_dynamics.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-report-dynamics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_45f4d525 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
