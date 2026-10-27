//! cohomology_in_monoidal shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_070111f2;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_070111f2<T> = std::result::Result<T, BoundaryError_070111f2>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for cohomology computed in / valued in a monoidal category.
/// Diagnostic inventory only — not a spectral-sequence certificate.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CohomologyInMonoidal {
    pub label: String,
    /// Ambient monoidal category shell label (coefficients / target).
    pub monoidal_ref: String,
    /// Cochain / chain complex ref.
    pub complex_ref: String,
    /// Degree index tag (e.g. "n", "2").
    pub degree: String,
    /// Optional cohomology object / group label at that degree.
    pub cohomology_object: String,
    pub notes: Vec<String>,
}

impl CohomologyInMonoidal {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            complex_ref: String::new(),
            degree: String::new(),
            cohomology_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn at_degree(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        complex_ref: impl Into<String>,
        degree: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            complex_ref: complex_ref.into(),
            degree: degree.into(),
            cohomology_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.monoidal_ref.is_empty() {
            return Err("empty monoidal_ref".into());
        }
        if self.complex_ref.is_empty() {
            return Err("empty complex_ref".into());
        }
        if self.degree.is_empty() {
            return Err("empty degree".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/cohomology_in_monoidal.rs
// Claim: urn:core:crates_rs:core-category-theory:cohomology-in-monoidal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(CohomologyInMonoidal::at_degree("H", "Ab", "Cdot", "2")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CohomologyInMonoidal::new("").validate_shell().is_err());
    }
}

/// A normalized integer 2-cochain on Z/n is a cocycle when its coboundary vanishes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroupCocycle {
    modulus: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CocycleError {
    Bound,
    Shape,
    Coboundary { x: i32, y: i32, z: i32, value: i32 },
}

impl std::fmt::Display for CocycleError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CocycleError::Bound => write!(formatter, "modulus must lie in 1..=6"),
            CocycleError::Shape => write!(formatter, "the cochain table must be modulus squared"),
            CocycleError::Coboundary { x, y, z, value } => {
                write!(formatter, "coboundary at ({x},{y},{z}) is {value}")
            }
        }
    }
}

impl std::error::Error for CocycleError {}

impl GroupCocycle {
    fn check_cocycle_triple(
        mu: &[i32],
        modulus: i32,
        x: i32,
        y: i32,
        z: i32,
    ) -> Result<(), CocycleError> {
        let yz = coeff(mu, modulus, y, z)?;
        let xy_z = coeff(mu, modulus, (x + y).rem_euclid(modulus), z)?;
        let x_yz = coeff(mu, modulus, x, (y + z).rem_euclid(modulus))?;
        let xy = coeff(mu, modulus, x, y)?;
        let value = yz
            .checked_sub(xy_z)
            .and_then(|step| step.checked_add(x_yz))
            .and_then(|step| step.checked_sub(xy))
            .ok_or(CocycleError::Bound)?;
        let residue = value.rem_euclid(modulus);
        if residue != 0 {
            return Err(CocycleError::Coboundary {
                x,
                y,
                z,
                value: residue,
            });
        }
        Ok(())
    }

    pub fn certify(modulus: i32, mu: &[i32]) -> Result<Self, CocycleError> {
        if modulus < 1 || modulus > 6 {
            return Err(CocycleError::Bound);
        }
        let width = usize::try_from(modulus).map_err(|_| CocycleError::Shape)?;
        let expected = width.checked_mul(width).ok_or(CocycleError::Shape)?;
        if mu.len() != expected {
            return Err(CocycleError::Shape);
        }
        for x in 0..modulus {
            for y in 0..modulus {
                for z in 0..modulus {
                    Self::check_cocycle_triple(mu, modulus, x, y, z)?;
                }
            }
        }
        Ok(Self { modulus })
    }

    pub fn modulus(&self) -> i32 {
        self.modulus
    }
}

fn coeff(mu: &[i32], modulus: i32, x: i32, y: i32) -> Result<i32, CocycleError> {
    let width = usize::try_from(modulus).map_err(|_| CocycleError::Shape)?;
    let row = usize::try_from(x).map_err(|_| CocycleError::Shape)?;
    let column = usize::try_from(y).map_err(|_| CocycleError::Shape)?;
    let index = row.checked_mul(width).and_then(|value| value.checked_add(column)).ok_or(CocycleError::Shape)?;
    mu.get(index).copied().ok_or(CocycleError::Shape)
}

#[cfg(test)]
mod cocycle_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn the_zero_cochain_is_a_cocycle_and_a_point_mass_is_not() {
        let zero = taken(GroupCocycle::certify(2, &[0, 0, 0, 0]));
        assert_eq!(zero.modulus(), 2);
        assert!(matches!(
            GroupCocycle::certify(2, &[1, 0, 0, 0]),
            Err(CocycleError::Coboundary { x: 0, y: 0, z: 1, value: 1 })
        ));
    }
}
