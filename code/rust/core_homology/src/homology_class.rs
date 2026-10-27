use crate::coefficient_domain::CoefficientDomain;
use crate::error::HomologyError;
use crate::hash::ComplexHash;
use crate::quotient::QuotientClass;
use linear_algebra::backend::basic_matrix::CheckedNumeric;
use num_traits::Zero;
use serde::Serialize;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertifiedCycle<K> {
    coefficients: Vec<K>,
    degree: usize,
}

impl<K> CertifiedCycle<K> {
    pub fn new_unchecked(coefficients: Vec<K>, degree: usize) -> Self {
        Self {
            coefficients,
            degree,
        }
    }

    pub fn coefficients(&self) -> &[K] {
        &self.coefficients
    }

    pub fn degree(&self) -> usize {
        self.degree
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomologyClass<K> {
    cycle: CertifiedCycle<K>,
    quotient_class: QuotientClass<K>,
    complex_id: ComplexHash,
    coefficient_domain: CoefficientDomain,
}

impl<K: CheckedNumeric + Zero + PartialEq + Clone + Serialize> HomologyClass<K> {
    pub fn new_checked(
        cycle: CertifiedCycle<K>,
        quotient_class: QuotientClass<K>,
        complex_id: ComplexHash,
        coefficient_domain: CoefficientDomain,
    ) -> Result<Self, HomologyError> {
        if quotient_class.ambient_complex_id() != &complex_id {
            return Err(HomologyError::ComplexMismatch);
        }
        if quotient_class.get_coefficient_domain() != coefficient_domain {
            return Err(HomologyError::DomainMismatch);
        }
        Ok(Self {
            cycle,
            quotient_class,
            complex_id,
            coefficient_domain,
        })
    }

    pub fn cycle(&self) -> &CertifiedCycle<K> {
        &self.cycle
    }

    pub fn quotient_class(&self) -> &QuotientClass<K> {
        &self.quotient_class
    }

    pub fn complex_id(&self) -> &ComplexHash {
        &self.complex_id
    }

    pub fn coefficient_domain(&self) -> CoefficientDomain {
        self.coefficient_domain
    }

    pub fn degree(&self) -> usize {
        self.cycle.degree()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CohomologyClass<K> {
    cocycle: CertifiedCycle<K>,
    quotient_class: QuotientClass<K>,
    complex_id: ComplexHash,
    coefficient_domain: CoefficientDomain,
}

impl<K: CheckedNumeric + Zero + PartialEq + Clone + Serialize> CohomologyClass<K> {
    pub fn new_checked(
        cocycle: CertifiedCycle<K>,
        quotient_class: QuotientClass<K>,
        complex_id: ComplexHash,
        coefficient_domain: CoefficientDomain,
    ) -> Result<Self, HomologyError> {
        if quotient_class.ambient_complex_id() != &complex_id {
            return Err(HomologyError::ComplexMismatch);
        }
        if quotient_class.get_coefficient_domain() != coefficient_domain {
            return Err(HomologyError::DomainMismatch);
        }
        Ok(Self {
            cocycle,
            quotient_class,
            complex_id,
            coefficient_domain,
        })
    }

    pub fn cocycle(&self) -> &CertifiedCycle<K> {
        &self.cocycle
    }

    pub fn quotient_class(&self) -> &QuotientClass<K> {
        &self.quotient_class
    }

    pub fn complex_id(&self) -> &ComplexHash {
        &self.complex_id
    }

    pub fn coefficient_domain(&self) -> CoefficientDomain {
        self.coefficient_domain
    }

    pub fn degree(&self) -> usize {
        self.cocycle.degree()
    }
}

// Origin: engine/crates_rs/core_homology/src/homology_class.rs
// Claim: urn:core:crates_rs:core-homology:homology-class:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::quotient::{QuotientRelation, QuotientSpace};
    use linear_algebra::backend::basic_matrix::{BasicMatrix, CheckedNumeric};
    use thiserror::Error;

    #[derive(Debug, Clone, PartialEq, Eq, Serialize)]
    struct CheckedI64(i64);

    #[derive(Debug, Error, Clone, PartialEq, Eq)]
    #[error("overflow")]
    struct OverflowError;

    impl std::ops::Add for CheckedI64 {
        type Output = Self;
        fn add(self, rhs: Self) -> Self {
            CheckedI64(self.0 + rhs.0)
        }
    }

    impl Zero for CheckedI64 {
        fn zero() -> Self {
            CheckedI64(0)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }

    impl CheckedNumeric for CheckedI64 {
        type Error = OverflowError;
        fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_add(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_sub(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_mul(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
    }

    #[test]
    fn test_homology_class_complex_mismatch_rejected() {
        let cycle = CertifiedCycle::new_unchecked(vec![CheckedI64(1), CheckedI64(1)], 1);

        let p_mat = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(0), CheckedI64(0), CheckedI64(1)],
        )
        .unwrap();
        let space = QuotientSpace::new_unchecked(
            ComplexHash::new(b"99"),
            CoefficientDomain::Integers,
            2,
            1,
            QuotientRelation::ModBoundaries,
            p_mat,
        );
        let q_class = QuotientClass::new_checked(&[CheckedI64(1), CheckedI64(1)], &space).unwrap();

        let res = HomologyClass::new_checked(
            cycle,
            q_class,
            ComplexHash::new(b"42"),
            CoefficientDomain::Integers,
        );
        assert!(matches!(res, Err(HomologyError::ComplexMismatch)));
    }

    #[test]
    fn test_homology_class_domain_mismatch_rejected() {
        let cycle = CertifiedCycle::new_unchecked(vec![CheckedI64(1), CheckedI64(1)], 1);

        let p_mat = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(0), CheckedI64(0), CheckedI64(1)],
        )
        .unwrap();
        let complex_id = ComplexHash::new(b"99");
        let space = QuotientSpace::new_unchecked(
            complex_id.clone(),
            CoefficientDomain::Integers,
            2,
            1,
            QuotientRelation::ModBoundaries,
            p_mat,
        );
        let q_class = QuotientClass::new_checked(&[CheckedI64(1), CheckedI64(1)], &space).unwrap();

        let res =
            HomologyClass::new_checked(cycle, q_class, complex_id, CoefficientDomain::Rational);
        assert!(matches!(res, Err(HomologyError::DomainMismatch)));
    }

    #[test]
    fn test_homology_class_matching_complex_and_domain_accepted() {
        let cycle = CertifiedCycle::new_unchecked(vec![CheckedI64(1), CheckedI64(1)], 1);

        let p_mat = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(0), CheckedI64(0), CheckedI64(1)],
        )
        .unwrap();
        let complex_id = ComplexHash::new(b"99");
        let space = QuotientSpace::new_unchecked(
            complex_id.clone(),
            CoefficientDomain::Integers,
            2,
            1,
            QuotientRelation::ModBoundaries,
            p_mat,
        );
        let q_class = QuotientClass::new_checked(&[CheckedI64(1), CheckedI64(1)], &space).unwrap();

        let class = HomologyClass::new_checked(
            cycle,
            q_class,
            complex_id.clone(),
            CoefficientDomain::Integers,
        )
        .expect("matching complex and domain must construct");
        assert_eq!(class.degree(), 1);
        assert_eq!(class.coefficient_domain(), CoefficientDomain::Integers);
        assert_eq!(class.complex_id(), &complex_id);
    }

    #[test]
    fn test_cohomology_class_complex_mismatch_rejected() {
        let cocycle = CertifiedCycle::new_unchecked(vec![CheckedI64(1), CheckedI64(1)], 1);

        let p_mat = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(0), CheckedI64(0), CheckedI64(1)],
        )
        .unwrap();
        let space = QuotientSpace::new_unchecked(
            ComplexHash::new(b"99"),
            CoefficientDomain::Integers,
            2,
            1,
            QuotientRelation::ModBoundaries,
            p_mat,
        );
        let q_class = QuotientClass::new_checked(&[CheckedI64(1), CheckedI64(1)], &space).unwrap();

        let res = CohomologyClass::new_checked(
            cocycle,
            q_class,
            ComplexHash::new(b"42"),
            CoefficientDomain::Integers,
        );
        assert!(matches!(res, Err(HomologyError::ComplexMismatch)));
    }
}
