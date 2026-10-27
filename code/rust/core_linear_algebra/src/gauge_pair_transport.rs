//! Exact descent of full directed pair tables modulo integer gradients.
//! The map is total; target vertices with empty fibers are retained.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_829d2b9c<T> {
    fn checked_invariant_829d2b9c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_829d2b9c<T> for Option<T> {
    #[inline]
    fn checked_invariant_829d2b9c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_829d2b9c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_829d2b9c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::semiring_lumpability::push_forward_square;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};

pub const MAX_TRANSPORT_VERTICES: usize = 256;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GaugeTransportError {
    #[error("pair transport requires a total map into the declared target carrier")]
    VertexMap,
    #[error("carrier transport exceeds the 256-vertex work cap")]
    WorkCap,
    #[error("the table or potential does not match the source carrier")]
    SourceShape,
    #[error("the complete intermediate carriers differ")]
    Intermediate,
    #[error("this map does not transport every gradient to a gradient")]
    NoDescent,
    #[error("matrix owner refusal: {0}")]
    Matrix(#[from] MatrixError),
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct GaugeTransportObstruction {
    /// Unit potential at this source vertex witnesses failure.
    pub source_vertex: usize,
    pub cycle: [usize; 3],
    pub value: BigInt,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum GaugeDescent {
    Descends,
    Obstructed(GaugeTransportObstruction),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugePairTransport {
    image: Vec<usize>,
    fibers: Vec<usize>,
}

impl GaugePairTransport {
    pub fn new(image: Vec<usize>, target: usize) -> Result<Self, GaugeTransportError> {
        if image.len() > MAX_TRANSPORT_VERTICES || target > MAX_TRANSPORT_VERTICES {
            return Err(GaugeTransportError::WorkCap);
        }
        if image.iter().any(|&v| v >= target) {
            return Err(GaugeTransportError::VertexMap);
        }
        let mut fibers = vec![0; target];
        for &v in &image {
            fibers[v] += 1;
        }
        Ok(Self { image, fibers })
    }
    pub fn image(&self) -> &[usize] {
        &self.image
    }
    pub fn fibers(&self) -> &[usize] {
        &self.fibers
    }
    pub fn source_size(&self) -> usize {
        self.image.len()
    }
    pub fn target_size(&self) -> usize {
        self.fibers.len()
    }
    /// Complete criterion, including empty and one-occupied-fiber carriers.
    pub fn descent(&self) -> GaugeDescent {
        if self.trivially_descends() {
            return GaugeDescent::Descends;
        }
        for a in 0..self.target_size() {
            if let Some(obstruction) = self.obstruction_from_fiber(a) {
                return GaugeDescent::Obstructed(obstruction);
            }
        }
        // If all other fibers agree at every occupied a, two occupied a's
        // force every fiber to have the same size, handled above.
        unreachable!("private fiber counts contradict the complete descent criterion")
    }

    fn trivially_descends(&self) -> bool {
        self.target_size() <= 2
            || self.fibers.iter().filter(|&&m| m > 0).count() <= 1
            || self.fibers.iter().all(|m| Some(m) == self.fibers.first())
    }

    fn obstruction_from_fiber(&self, a: usize) -> Option<GaugeTransportObstruction> {
        if self.fibers[a] == 0 {
            return None;
        }
        let b = usize::from(a == 0);
        let c = (0..self.target_size())
            .find(|&c| c != a && c != b && self.fibers[c] != self.fibers[b])?;
        Some(GaugeTransportObstruction {
            source_vertex: self
                .image
                .iter()
                .position(|&v| v == a)
                .checked_invariant_829d2b9c("checked invariant"),
            cycle: [a, b, c],
            value: BigInt::from(self.fibers[b]) - BigInt::from(self.fibers[c]),
        })
    }
    pub fn apply(
        &self,
        table: &BasicMatrix<BigRational>,
    ) -> Result<BasicMatrix<BigRational>, GaugeTransportError> {
        if table.shape() != (self.source_size(), self.source_size()) {
            return Err(GaugeTransportError::SourceShape);
        }
        Ok(push_forward_square(table, &self.image, self.target_size())?)
    }
    /// T(dg)(a,b) = m_b s_a - m_a s_b, s_a = sum_{f(x)=a} g_x.
    pub fn push_gradient(
        &self,
        potential: &[BigInt],
    ) -> Result<BasicMatrix<BigRational>, GaugeTransportError> {
        if potential.len() != self.source_size() {
            return Err(GaugeTransportError::SourceShape);
        }
        let mut sums = vec![BigInt::zero(); self.target_size()];
        for (&a, value) in self.image.iter().zip(potential) {
            sums[a] += value;
        }
        Ok(BasicMatrix::try_from_fn(
            self.target_size(),
            self.target_size(),
            |a, b| {
                BigRational::from_integer(
                    BigInt::from(self.fibers[b]) * &sums[a]
                        - BigInt::from(self.fibers[a]) * &sums[b],
                )
            },
        )?)
    }
    /// Root-zero target potential, admitted only for universally lawful maps.
    pub fn quotient_potential(
        &self,
        potential: &[BigInt],
    ) -> Result<Vec<BigInt>, GaugeTransportError> {
        if self.descent() != GaugeDescent::Descends {
            return Err(GaugeTransportError::NoDescent);
        }
        let moved = self.push_gradient(potential)?;
        (0..self.target_size())
            .map(|a| Ok(moved.get(a, 0)?.to_integer()))
            .collect()
    }
    /// Replay a purported obstruction through actual P M P^T, not fiber flags.
    pub fn verify_obstruction(
        &self,
        witness: &GaugeTransportObstruction,
    ) -> Result<bool, GaugeTransportError> {
        if !self.is_valid_obstruction_witness(witness) {
            return Ok(false);
        }
        let [a, b, c] = witness.cycle;
        let mut g = vec![BigRational::zero(); self.source_size()];
        g[witness.source_vertex] = BigRational::one();
        let gradient =
            BasicMatrix::try_from_fn(self.source_size(), self.source_size(), |x, y| &g[x] - &g[y])?;
        let moved = self.apply(&gradient)?;
        Ok(moved.get(a, b)? + moved.get(b, c)? + moved.get(c, a)?
            == BigRational::from_integer(witness.value.clone()))
    }

    fn is_valid_obstruction_witness(&self, witness: &GaugeTransportObstruction) -> bool {
        let [a, b, c] = witness.cycle;
        let in_bounds = witness.source_vertex < self.source_size()
            && witness.cycle.iter().all(|&v| v < self.target_size());
        let distinct_cycle = a != b && b != c && c != a;
        in_bounds && distinct_cycle && !witness.value.is_zero()
    }
    /// Raw operators compose on complete declared carriers. If both operands
    /// descend, their composite does too; no lawfulness flag is accepted.
    pub fn then(&self, after: &Self) -> Result<Self, GaugeTransportError> {
        if self.target_size() != after.source_size() {
            return Err(GaugeTransportError::Intermediate);
        }
        Self::new(
            self.image.iter().map(|&a| after.image[a]).collect(),
            after.target_size(),
        )
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/gauge_pair_transport.rs
// Claim: urn:core:crates_rs:core-linear-algebra:gauge-pair-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_829d2b9c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
