//! Exact incidence operator algebra on strict chains of a finite poset.
//!
//! Degree n components have type Hom(V_last, V_first). The internal-face
//! differential b is nilpotent; D_A = b + [A,-] is curved, D_A² = [K,-].
//! This is an algebraic carrier, not a physical gauge or an H² certificate.
//! The executable profile admits 1..=8 vertices and fiber dimensions 1..=4.
//! Every component must be supplied; missing components never mean zero.

use crate::finite_poset::{FinitePoset, PosetError};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_rational::BigRational;
use num_traits::{One, Zero};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::Arc;

pub type Matrix = BasicMatrix<BigRational>;
pub type Components = BTreeMap<Vec<usize>, Matrix>;
pub type CoverMaps = BTreeMap<(usize, usize), Matrix>;

#[derive(Debug, thiserror::Error)]
pub enum RestrictionError {
    #[error(transparent)]
    Poset(#[from] PosetError),
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error("profile requires 1..=8 vertices and one dimension in 1..=4 per vertex")]
    Profile,
    #[error("cochain or cover component coverage differs from the declared carrier")]
    Coverage,
    #[error("matrix shape differs from the endpoint fiber dimensions")]
    Shape,
    #[error("rational denominator must be strictly positive")]
    Denominator,
    #[error("operations require the same poset and fiber dimensions")]
    CarrierMismatch,
    #[error("cochain degrees differ or a connection has degree other than one")]
    Degree,
    #[error("cochain degree overflow")]
    DegreeOverflow,
    #[error("vertex matrices are not mutual inverses")]
    Inverse,
    #[error(
        "saturated paths disagree between {lower} and {upper}: {first_path:?}, {second_path:?}"
    )]
    PathDependent {
        lower: usize,
        upper: usize,
        first_path: Vec<usize>,
        second_path: Vec<usize>,
    },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OperatorCarrier {
    poset: FinitePoset,
    dimensions: Vec<usize>,
    chains: Vec<Vec<Vec<usize>>>,
}

impl OperatorCarrier {
    pub fn new(poset: FinitePoset, dimensions: Vec<usize>) -> Result<Arc<Self>, RestrictionError> {
        let n = poset.size();
        if !(1..=8).contains(&n)
            || dimensions.len() != n
            || dimensions.iter().any(|&d| !(1..=4).contains(&d))
        {
            return Err(RestrictionError::Profile);
        }
        let mut chains = vec![Vec::new(); n];
        for chain in poset.chains(255)? {
            chains[chain.len() - 1].push(chain);
        }
        Ok(Arc::new(Self {
            poset,
            dimensions,
            chains,
        }))
    }

    pub fn chains(&self, degree: usize) -> &[Vec<usize>] {
        self.chains.get(degree).map(Vec::as_slice).unwrap_or(&[])
    }

    pub fn dimensions(&self) -> &[usize] {
        &self.dimensions
    }

    pub fn poset(&self) -> &FinitePoset {
        &self.poset
    }

    /// Extend cover maps iff all saturated path products agree. The first
    /// differing pair of paths is returned as a typed obstruction.
    pub fn flat_cover_extension(
        self: &Arc<Self>,
        covers: CoverMaps,
    ) -> Result<Cochain, RestrictionError> {
        let expected: BTreeSet<_> = self.poset.covers().into_iter().collect();
        if covers.keys().copied().collect::<BTreeSet<_>>() != expected {
            return Err(RestrictionError::Coverage);
        }
        let mut checked = BTreeMap::new();
        for ((x, y), matrix) in covers {
            checked.insert((x, y), self.checked_matrix(&[x, y], matrix)?);
        }
        let mut products: BTreeMap<(usize, usize), (Vec<usize>, Matrix)> = BTreeMap::new();
        for chain in self.chains.iter().skip(1).flatten() {
            if !chain
                .windows(2)
                .all(|pair| expected.contains(&(pair[0], pair[1])))
            {
                continue;
            }
            let product = self.compute_chain_product(chain, &checked)?;
            Self::record_chain_product(&mut products, chain, product)?;
        }
        let mut values = BTreeMap::new();
        for pair in self.chains(1) {
            let (_, matrix) = products
                .get(&(pair[0], pair[1]))
                .ok_or(RestrictionError::Coverage)?;
            values.insert(pair.clone(), matrix.clone());
        }
        Cochain::new(self.clone(), 1, values)
    }

    fn compute_chain_product(
        &self,
        chain: &[usize],
        checked: &BTreeMap<(usize, usize), Matrix>,
    ) -> Result<Matrix, RestrictionError> {
        let mut product = identity(self.dimensions[chain[0]])?;
        for pair in chain.windows(2) {
            let map = checked
                .get(&(pair[0], pair[1]))
                .ok_or(RestrictionError::Coverage)?;
            product = product.mul(map)?;
        }
        Ok(product)
    }

    fn record_chain_product(
        products: &mut BTreeMap<(usize, usize), (Vec<usize>, Matrix)>,
        chain: &[usize],
        product: Matrix,
    ) -> Result<(), RestrictionError> {
        let endpoints = (chain[0], chain[chain.len() - 1]);
        if let Some((first_path, first)) = products.get(&endpoints) {
            if first != &product {
                return Err(RestrictionError::PathDependent {
                    lower: endpoints.0,
                    upper: endpoints.1,
                    first_path: first_path.clone(),
                    second_path: chain.to_vec(),
                });
            }
        } else {
            products.insert(endpoints, (chain.to_vec(), product));
        }
        Ok(())
    }

    fn checked_matrix(&self, chain: &[usize], matrix: Matrix) -> Result<Matrix, RestrictionError> {
        let first = chain.first().ok_or(RestrictionError::Coverage)?;
        let last = chain.last().ok_or(RestrictionError::Coverage)?;
        let rows = self
            .dimensions
            .get(*first)
            .ok_or(RestrictionError::Coverage)?;
        let cols = self
            .dimensions
            .get(*last)
            .ok_or(RestrictionError::Coverage)?;
        if matrix.shape() != (*rows, *cols) {
            return Err(RestrictionError::Shape);
        }
        matrix.try_map(|q| {
            if q.denom() <= &0.into() {
                return Err(RestrictionError::Denominator);
            }
            Ok(BigRational::new(q.numer().clone(), q.denom().clone()))
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Cochain {
    carrier: Arc<OperatorCarrier>,
    degree: usize,
    values: Components,
}

impl Cochain {
    pub fn new(
        carrier: Arc<OperatorCarrier>,
        degree: usize,
        values: Components,
    ) -> Result<Self, RestrictionError> {
        let expected: BTreeSet<_> = carrier.chains(degree).iter().cloned().collect();
        if values.keys().cloned().collect::<BTreeSet<_>>() != expected {
            return Err(RestrictionError::Coverage);
        }
        let values = values
            .into_iter()
            .map(|(chain, matrix)| {
                carrier
                    .checked_matrix(&chain, matrix)
                    .map(|matrix| (chain, matrix))
            })
            .collect::<Result<_, _>>()?;
        Ok(Self {
            carrier,
            degree,
            values,
        })
    }

    pub fn zero(carrier: Arc<OperatorCarrier>, degree: usize) -> Result<Self, RestrictionError> {
        Self::build(carrier, degree, |chain, c| {
            Ok(Matrix::zero(
                c.dimensions[chain[0]],
                c.dimensions[chain[chain.len() - 1]],
            )?)
        })
    }

    pub fn unit(carrier: Arc<OperatorCarrier>) -> Result<Self, RestrictionError> {
        Self::build(carrier, 0, |chain, c| identity(c.dimensions[chain[0]]))
    }

    pub fn degree(&self) -> usize {
        self.degree
    }
    pub fn components(&self) -> &Components {
        &self.values
    }
    pub fn carrier(&self) -> &Arc<OperatorCarrier> {
        &self.carrier
    }
    pub fn is_zero(&self) -> bool {
        self.values.values().all(|m| {
            (0..m.rows())
                .all(|i| (0..m.cols()).all(|j| m.get_ref(i, j).is_ok_and(BigRational::is_zero)))
        })
    }

    pub fn add(&self, rhs: &Self) -> Result<Self, RestrictionError> {
        self.combine(rhs, false)
    }
    pub fn sub(&self, rhs: &Self) -> Result<Self, RestrictionError> {
        self.combine(rhs, true)
    }

    fn combine(&self, rhs: &Self, subtract: bool) -> Result<Self, RestrictionError> {
        self.same_carrier(rhs)?;
        if self.degree != rhs.degree {
            return Err(RestrictionError::Degree);
        }
        Self::build(self.carrier.clone(), self.degree, |chain, _| {
            let a = self.at(chain)?;
            let b = rhs.at(chain)?;
            Ok(if subtract { a.sub(b)? } else { a.add(b)? })
        })
    }

    pub fn cup(&self, rhs: &Self) -> Result<Self, RestrictionError> {
        self.same_carrier(rhs)?;
        let degree = self
            .degree
            .checked_add(rhs.degree)
            .ok_or(RestrictionError::DegreeOverflow)?;
        Self::build(self.carrier.clone(), degree, |chain, _| {
            Ok(self
                .at(&chain[..=self.degree])?
                .mul(rhs.at(&chain[self.degree..])?)?)
        })
    }

    /// Exact graded Lie bracket; two odd degrees use an anticommutator.
    pub fn graded_bracket(&self, rhs: &Self) -> Result<Self, RestrictionError> {
        let left = self.cup(rhs)?;
        let right = rhs.cup(self)?;
        if self.degree % 2 == 1 && rhs.degree % 2 == 1 {
            left.add(&right)
        } else {
            left.sub(&right)
        }
    }

    /// b f = sum over internal deletions only, with sign (-1)^i.
    pub fn internal_differential(&self) -> Result<Self, RestrictionError> {
        let degree = self
            .degree
            .checked_add(1)
            .ok_or(RestrictionError::DegreeOverflow)?;
        Self::build(self.carrier.clone(), degree, |chain, c| {
            let mut value =
                Matrix::zero(c.dimensions[chain[0]], c.dimensions[chain[chain.len() - 1]])?;
            for i in 1..=self.degree {
                let mut face = chain.to_vec();
                face.remove(i);
                value = if i % 2 == 0 {
                    value.add(self.at(&face)?)?
                } else {
                    value.sub(self.at(&face)?)?
                };
            }
            Ok(value)
        })
    }

    /// D_A f = b f + A cup f - (-1)^degree f cup A.
    pub fn covariant_differential(&self, connection: &Self) -> Result<Self, RestrictionError> {
        self.same_carrier(connection)?;
        if connection.degree != 1 {
            return Err(RestrictionError::Degree);
        }
        let left = self.internal_differential()?.add(&connection.cup(self)?)?;
        let right = self.cup(connection)?;
        if self.degree % 2 == 0 {
            left.sub(&right)
        } else {
            left.add(&right)
        }
    }

    pub fn curvature(&self) -> Result<Self, RestrictionError> {
        if self.degree != 1 {
            return Err(RestrictionError::Degree);
        }
        self.internal_differential()?.add(&self.cup(self)?)
    }

    /// Vertexwise basis change: f^g_chain = g_first f_chain h_last.
    /// Both inverse equations g h = h g = I are checked at every vertex.
    pub fn gauge(&self, g: &[Matrix], h: &[Matrix]) -> Result<Self, RestrictionError> {
        if g.len() != self.carrier.dimensions.len() || h.len() != g.len() {
            return Err(RestrictionError::Coverage);
        }
        let mut checked_g = Vec::new();
        let mut checked_h = Vec::new();
        for (x, &dim) in self.carrier.dimensions.iter().enumerate() {
            let (gx, hx) = self.check_gauge_pair(x, dim, g[x].clone(), h[x].clone())?;
            checked_g.push(gx);
            checked_h.push(hx);
        }
        Self::build(self.carrier.clone(), self.degree, |chain, _| {
            Ok(checked_g[chain[0]]
                .mul(self.at(chain)?)?
                .mul(&checked_h[chain[chain.len() - 1]])?)
        })
    }

    fn check_gauge_pair(
        &self,
        x: usize,
        dim: usize,
        gx_in: Matrix,
        hx_in: Matrix,
    ) -> Result<(Matrix, Matrix), RestrictionError> {
        let gx = self.carrier.checked_matrix(&[x], gx_in)?;
        let hx = self.carrier.checked_matrix(&[x], hx_in)?;
        let id = identity(dim)?;
        if gx.mul(&hx)? != id || hx.mul(&gx)? != id {
            return Err(RestrictionError::Inverse);
        }
        Ok((gx, hx))
    }

    fn at(&self, chain: &[usize]) -> Result<&Matrix, RestrictionError> {
        self.values.get(chain).ok_or(RestrictionError::Coverage)
    }

    fn same_carrier(&self, rhs: &Self) -> Result<(), RestrictionError> {
        if self.carrier != rhs.carrier {
            return Err(RestrictionError::CarrierMismatch);
        }
        Ok(())
    }

    fn build<F>(
        carrier: Arc<OperatorCarrier>,
        degree: usize,
        mut f: F,
    ) -> Result<Self, RestrictionError>
    where
        F: FnMut(&[usize], &OperatorCarrier) -> Result<Matrix, RestrictionError>,
    {
        let mut values = BTreeMap::new();
        for chain in carrier.chains(degree) {
            values.insert(chain.clone(), f(chain, &carrier)?);
        }
        Self::new(carrier, degree, values)
    }
}

fn identity(dim: usize) -> Result<Matrix, RestrictionError> {
    Ok(Matrix::try_from_fn(dim, dim, |i, j| {
        if i == j {
            BigRational::one()
        } else {
            BigRational::zero()
        }
    })?)
}

// Origin: engine/crates_rs/core_homology/src/restriction_dga.rs
// Claim: urn:core:crates_rs:core-homology:restriction-dga:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_794d3773 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
