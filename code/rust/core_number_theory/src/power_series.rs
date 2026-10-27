//! Formal exact power series modulo x^(N+1). Coefficients use the estate's
//! exact scalar tower; calculus refuses fields where a required integer vanishes.
//! AuthorityEffect: None.
use linear_algebra::scalars::{ExactRing, Field};
pub const MAX_SERIES_ORDER: usize = 1024;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SeriesError {
    #[error("series order exceeds {MAX_SERIES_ORDER}")]
    Order,
    #[error("series orders differ")]
    OrderMismatch,
    #[error("series constant is not invertible")]
    NoninvertibleConstant,
    #[error("formal log needs constant 1; exp and inner composition need constant 0")]
    Constant,
    #[error("integer {0} is not invertible in the coefficient field")]
    Characteristic(usize),
    #[error("power exponent exceeds the formal series budget")]
    Exponent,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TruncatedSeries<K> {
    coefficients: Vec<K>,
}
fn integer<K: Field>(mut n: usize) -> K {
    let mut value = K::zero();
    let mut bit = K::one();
    while n > 0 {
        if n & 1 != 0 {
            value = value.add(&bit);
        }
        n >>= 1;
        if n > 0 {
            bit = bit.add(&bit);
        }
    }
    value
}
impl<K: Field + ExactRing> TruncatedSeries<K> {
    pub fn from_coefficients(mut coefficients: Vec<K>, order: usize) -> Result<Self, SeriesError> {
        if order > MAX_SERIES_ORDER || coefficients.len() > order + 1 {
            return Err(SeriesError::Order);
        }
        coefficients.resize_with(order + 1, K::zero);
        Ok(Self { coefficients })
    }
    pub fn constant(value: K, order: usize) -> Result<Self, SeriesError> {
        Self::from_coefficients(vec![value], order)
    }
    pub fn order(&self) -> usize {
        self.coefficients.len() - 1
    }
    pub fn coefficients(&self) -> &[K] {
        &self.coefficients
    }
    pub fn coefficient(&self, index: usize) -> Option<&K> {
        self.coefficients.get(index)
    }
    fn compatible(&self, other: &Self) -> Result<(), SeriesError> {
        if self.order() != other.order() {
            Err(SeriesError::OrderMismatch)
        } else {
            Ok(())
        }
    }
    pub fn add(&self, other: &Self) -> Result<Self, SeriesError> {
        self.compatible(other)?;
        Ok(Self {
            coefficients: self
                .coefficients
                .iter()
                .zip(&other.coefficients)
                .map(|(a, b)| a.add(b))
                .collect(),
        })
    }
    pub fn sub(&self, other: &Self) -> Result<Self, SeriesError> {
        self.compatible(other)?;
        Ok(Self {
            coefficients: self
                .coefficients
                .iter()
                .zip(&other.coefficients)
                .map(|(a, b)| a.sub(b))
                .collect(),
        })
    }
    pub fn scale(&self, c: &K) -> Self {
        Self {
            coefficients: self.coefficients.iter().map(|a| a.mul(c)).collect(),
        }
    }
    pub fn mul(&self, other: &Self) -> Result<Self, SeriesError> {
        self.compatible(other)?;
        let n = self.order();
        let mut result = vec![K::zero(); n + 1];
        for (k, coefficient) in result.iter_mut().enumerate() {
            for i in 0..=k {
                *coefficient =
                    coefficient.add(&self.coefficients[i].mul(&other.coefficients[k - i]));
            }
        }
        Ok(Self {
            coefficients: result,
        })
    }
    pub fn inverse(&self) -> Result<Self, SeriesError> {
        let inverse = self.coefficients[0]
            .try_inv()
            .ok_or(SeriesError::NoninvertibleConstant)?;
        let mut coefficients = vec![K::zero(); self.order() + 1];
        coefficients[0] = inverse.clone();
        for k in 1..=self.order() {
            let mut value = K::zero();
            for i in 1..=k {
                value = value.add(&self.coefficients[i].mul(&coefficients[k - i]));
            }
            coefficients[k] = value.neg().mul(&inverse);
        }
        Ok(Self { coefficients })
    }
    /// Formal derivative, padded to the same order. Its highest coefficient is unknown
    /// from an N-jet and recorded as zero; use only through degree N-1.
    pub fn derivative(&self) -> Self {
        let mut coefficients = vec![K::zero(); self.order() + 1];
        for k in 1..=self.order() {
            coefficients[k - 1] = self.coefficients[k].mul(&integer::<K>(k));
        }
        Self { coefficients }
    }
    pub fn integral(&self, constant: K) -> Result<Self, SeriesError> {
        let mut coefficients = vec![constant];
        for k in 1..=self.order() {
            coefficients.push(
                self.coefficients[k - 1].mul(
                    &integer::<K>(k)
                        .try_inv()
                        .ok_or(SeriesError::Characteristic(k))?,
                ),
            );
        }
        Ok(Self { coefficients })
    }
    pub fn log(&self) -> Result<Self, SeriesError> {
        if self.coefficients[0] != K::one() {
            return Err(SeriesError::Constant);
        }
        self.derivative().mul(&self.inverse()?)?.integral(K::zero())
    }
    pub fn exp(&self) -> Result<Self, SeriesError> {
        if !self.coefficients[0].is_zero() {
            return Err(SeriesError::Constant);
        }
        let mut coefficients = vec![K::zero(); self.order() + 1];
        coefficients[0] = K::one();
        for k in 1..=self.order() {
            let mut value = K::zero();
            for i in 1..=k {
                value = value.add(
                    &self.coefficients[i]
                        .mul(&integer::<K>(i))
                        .mul(&coefficients[k - i]),
                );
            }
            coefficients[k] = value.mul(
                &integer::<K>(k)
                    .try_inv()
                    .ok_or(SeriesError::Characteristic(k))?,
            );
        }
        Ok(Self { coefficients })
    }
    pub fn compose(&self, inner: &Self) -> Result<Self, SeriesError> {
        self.compatible(inner)?;
        if !inner.coefficients[0].is_zero() {
            return Err(SeriesError::Constant);
        }
        let mut result = Self::constant(K::zero(), self.order())?;
        for a in self.coefficients.iter().rev() {
            result = result.mul(inner)?;
            result.coefficients[0] = result.coefficients[0].add(a);
        }
        Ok(result)
    }
    pub fn pow(&self, mut exponent: usize) -> Result<Self, SeriesError> {
        if exponent > 1 << 20 {
            return Err(SeriesError::Exponent);
        }
        let mut result = Self::constant(K::one(), self.order())?;
        let mut base = self.clone();
        while exponent > 0 {
            if exponent & 1 != 0 {
                result = result.mul(&base)?;
            }
            exponent >>= 1;
            if exponent > 0 {
                base = base.mul(&base)?;
            }
        }
        Ok(result)
    }
}
// Origin: engine/crates_rs/core_number_theory/src/power_series.rs
// Claim: urn:core:crates_rs:core-number-theory:power-series:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::rq;
    use num_rational::BigRational;
    #[test]
    fn formal_series_inverse_log_exp_and_composition_are_exact() {
        let f = TruncatedSeries::from_coefficients(vec![rq(1, 1), rq(2, 1), rq(3, 1)], 8).unwrap();
        assert_eq!(
            f.mul(&f.inverse().unwrap()).unwrap(),
            TruncatedSeries::constant(rq(1, 1), 8).unwrap()
        );
        assert_eq!(f.log().unwrap().exp().unwrap(), f);
        let x = TruncatedSeries::from_coefficients(vec![rq(0, 1), rq(1, 1)], 8).unwrap();
        assert_eq!(f.compose(&x).unwrap(), f);
        assert_eq!(x.exp().unwrap().coefficients()[4], rq(1, 24));
        assert!(TruncatedSeries::<BigRational>::from_coefficients(vec![], usize::MAX).is_err());
        assert!(x.inverse().is_err());
        assert!(f.exp().is_err());
        assert!(f.compose(&f).is_err());
    }
}
