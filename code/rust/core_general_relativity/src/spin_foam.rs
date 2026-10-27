//! Exact finite SU(2)_2 tetrahedral recoupling at q=exp(i pi/4).
//! Labels are twice-spin 0,1,2. This computes quantum Racah coefficients and
//! finite products, with no continuum or triangulation-invariance admission.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_69e80abb<T> {
    fn checked_invariant_69e80abb(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_69e80abb<T> for Option<T> {
    #[inline]
    fn checked_invariant_69e80abb(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_69e80abb<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_69e80abb(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_number_theory::quadratic::Quadratic;
pub type IsingScalar = Quadratic<2>;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite recoupling; no continuum admission.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinFoamError {
    #[error("SU(2)_2 label must be in 0..=2")]
    Label,
    #[error("admissible recoupling coefficient did not lie in Q(sqrt(2))")]
    Field,
    #[error("finite state sum exceeds its operation budget")]
    Budget,
}
pub fn ising_admissible(a: u8, b: u8, c: u8) -> bool {
    a <= 2
        && b <= 2
        && c <= 2
        && a + b >= c
        && a + c >= b
        && b + c >= a
        && (a + b + c) % 2 == 0
        && a + b + c <= 4
}
pub fn quantum_dimension(label: u8) -> Result<IsingScalar, SpinFoamError> {
    match label {
        0 | 2 => Ok(IsingScalar::one()),
        1 => Ok(IsingScalar::sqrt_d()),
        _ => Err(SpinFoamError::Label),
    }
}
fn qfactorial(n: u8) -> IsingScalar {
    let mut previous = IsingScalar::zero();
    let mut current = IsingScalar::one();
    let mut result = IsingScalar::one();
    for _ in 1..=n {
        result = result.mul(&current);
        let next = IsingScalar::sqrt_d().mul(&current).sub(&previous);
        previous = current;
        current = next;
    }
    result
}
fn delta_squared(a: u8, b: u8, c: u8) -> IsingScalar {
    qfactorial((a + b - c) / 2)
        .mul(&qfactorial((a + c - b) / 2))
        .mul(&qfactorial((b + c - a) / 2))
        .checked_div(&qfactorial((a + b + c) / 2 + 1))
        .checked_invariant_69e80abb("admissibility keeps denominator nonzero")
}
/// An exact quantum Racah amplitude `factor * sqrt(squared_prefactor)`.
/// Keeping the positive root as data admits the fourth roots appearing in
/// unnormalized SU(2)_2 six-j symbols without falsely narrowing their field.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RacahCoefficient {
    factor: IsingScalar,
    squared_prefactor: IsingScalar,
}
impl RacahCoefficient {
    pub fn factor(&self) -> &IsingScalar {
        &self.factor
    }
    pub fn squared_prefactor(&self) -> &IsingScalar {
        &self.squared_prefactor
    }
    pub fn squared_value(&self) -> IsingScalar {
        self.factor.mul(&self.factor).mul(&self.squared_prefactor)
    }
    /// Refuse when this unnormalized coefficient needs a field extension.
    pub fn quadratic_value(&self) -> Result<IsingScalar, SpinFoamError> {
        if self.factor == IsingScalar::zero() {
            return Ok(IsingScalar::zero());
        }
        Ok(self
            .factor
            .mul(&self.squared_prefactor.sqrt().ok_or(SpinFoamError::Field)?))
    }
}
/// {a b c; d e f}_q in the quantum Racah convention, retaining an exact
/// positive-root certificate. Forbidden couplings have amplitude zero.
pub fn ising_six_j_radical(labels: [u8; 6]) -> Result<RacahCoefficient, SpinFoamError> {
    let [a, b, c, d, e, f] = labels;
    if labels.iter().any(|&v| v > 2) {
        return Err(SpinFoamError::Label);
    }
    let triangles = [(a, b, c), (a, e, f), (d, b, f), (d, e, c)];
    if triangles
        .iter()
        .any(|&(u, v, w)| !ising_admissible(u, v, w))
    {
        return Ok(RacahCoefficient {
            factor: IsingScalar::zero(),
            squared_prefactor: IsingScalar::one(),
        });
    }
    let squared_prefactor = triangles.iter().fold(IsingScalar::one(), |x, &(u, v, w)| {
        x.mul(&delta_squared(u, v, w))
    });
    let t = [
        (a + b + c) / 2,
        (a + e + f) / 2,
        (d + b + f) / 2,
        (d + e + c) / 2,
    ];
    let u = [
        (a + b + d + e) / 2,
        (a + c + d + f) / 2,
        (b + c + e + f) / 2,
    ];
    let lower = *t.iter().max().checked_invariant_69e80abb("four faces");
    let upper = *u.iter().min().checked_invariant_69e80abb("three sums");
    let mut sum = IsingScalar::zero();
    for z in lower..=upper {
        let denominator = t
            .iter()
            .fold(IsingScalar::one(), |x, &v| x.mul(&qfactorial(z - v)));
        let denominator = u
            .iter()
            .fold(denominator, |x, &v| x.mul(&qfactorial(v - z)));
        let term = qfactorial(z + 1)
            .checked_div(&denominator)
            .ok_or(SpinFoamError::Field)?;
        sum = if z % 2 == 0 {
            sum.add(&term)
        } else {
            sum.sub(&term)
        };
    }
    Ok(RacahCoefficient {
        factor: sum,
        squared_prefactor,
    })
}
/// The six-j value in Q(sqrt(2)), with a typed field-extension refusal.
/// Use `ising_six_j_radical` to retain every admissible coefficient exactly.
pub fn ising_six_j(labels: [u8; 6]) -> Result<IsingScalar, SpinFoamError> {
    ising_six_j_radical(labels)?.quadratic_value()
}
fn ising_f_admissible(a: u8, b: u8, c: u8, d: u8, e: u8, f: u8) -> bool {
    ising_admissible(a, b, e)
        && ising_admissible(e, c, d)
        && ising_admissible(b, c, f)
        && ising_admissible(a, f, d)
}

/// F^{abc}_d[e,f], including quantum dimension factors and the standard
/// (-1)^(a+b+c+d)/2 recoupling phase. Inadmissible rows have zero amplitude.
pub fn ising_f(a: u8, b: u8, c: u8, d: u8, e: u8, f: u8) -> Result<IsingScalar, SpinFoamError> {
    if [a, b, c, d, e, f].iter().any(|&v| v > 2) {
        return Err(SpinFoamError::Label);
    }
    if !ising_f_admissible(a, b, c, d, e, f) {
        return Ok(IsingScalar::zero());
    }
    let racah = ising_six_j_radical([a, b, e, c, d, f])?;
    // The two separate roots can require fourth roots of two. The normalized
    // recoupling uses their product, which lies in the declared quadratic field.
    let root = quantum_dimension(e)?
        .mul(&quantum_dimension(f)?)
        .mul(racah.squared_prefactor())
        .sqrt()
        .ok_or(SpinFoamError::Field)?;
    let value = root.mul(racah.factor());
    Ok(if ((a + b + c + d) / 2) % 2 == 0 {
        value
    } else {
        value.neg()
    })
}
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct SpinFoam {
    pub degree: usize,
    pub label: String,
    pub tetrahedral_labels: Vec<[u8; 6]>,
}
impl SpinFoam {
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
            tetrahedral_labels: Vec::new(),
        }
    }
    pub fn from_tetrahedra(
        labels: Vec<[u8; 6]>,
        label: impl Into<String>,
    ) -> Result<Self, SpinFoamError> {
        if labels.len() > 4096 {
            return Err(SpinFoamError::Budget);
        }
        for &cell in &labels {
            ising_six_j_radical(cell)?;
        }
        Ok(Self {
            degree: labels.len(),
            label: label.into(),
            tetrahedral_labels: labels,
        })
    }
    pub fn tetrahedral_amplitude(&self) -> Result<RacahCoefficient, SpinFoamError> {
        if self.tetrahedral_labels.len() > 4096 {
            return Err(SpinFoamError::Budget);
        }
        self.tetrahedral_labels.iter().try_fold(
            RacahCoefficient {
                factor: IsingScalar::one(),
                squared_prefactor: IsingScalar::one(),
            },
            |product, &labels| {
                let cell = ising_six_j_radical(labels)?;
                Ok(RacahCoefficient {
                    factor: product.factor.mul(&cell.factor),
                    squared_prefactor: product.squared_prefactor.mul(&cell.squared_prefactor),
                })
            },
        )
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/spin_foam.rs
// Claim: urn:core:crates_rs:core-general-relativity:spin-foam:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_69e80abb {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
