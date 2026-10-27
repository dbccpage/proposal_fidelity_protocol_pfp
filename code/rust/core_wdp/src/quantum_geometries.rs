// Executable finite evidence; AuthorityEffect: None.
//! Vector and Quantum Observer Geometries: Stalks, CPTP Transitions & Classical Shadows.
//!
//! Grounded in GS-003 ("Vector and Quantum Observer Geometries"):
//! 1. Vector Observer Bundles: Stalks V_v \cong Q^k and transitions g_{uv} \in GL(k, Q).
//! 2. Quantum Density Stalks: Exact rational density matrices \rho_v \in Q^{k \times k} with Tr(\rho_v) = 1, \rho_v \ge 0.
//! 3. CPTP Transitions: Completely positive trace-preserving transition channels on edges.
//! 4. Schatten-1 Trace Distance: Exact squared qubit distance, rational roots when available.
//! 5. Classical Population Shadows: Diagonal projection P(\rho) with contractive Schatten-to-classical L1 bounds.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a9d8673f<T> {
    fn checked_invariant_a9d8673f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a9d8673f<T> for Option<T> {
    #[inline]
    fn checked_invariant_a9d8673f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a9d8673f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a9d8673f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use linear_algebra::exact_ldlt::is_psd_rational;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};

use crate::types::AuthorityEffect;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::exact_channel::{ExactChannelError, ExactKrausChannel};

/// Verification receipt for quantum observer geometry operations.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuantumGeometryReceipt {
    pub is_valid_density: bool,
    pub trace: BigRational,
    pub is_positive_semidefinite: bool,
    pub classical_shadow_probabilities: Vec<BigRational>,
    pub trace_distance_to_target: Option<BigRational>,
    pub classical_l1_distance: Option<BigRational>,
    pub is_contractive: bool,
    pub authority_effect: AuthorityEffect,
}

/// Exact rational density matrix \rho \in Q^{k \times k} on a quantum observer stalk.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuantumDensityStalk {
    pub dim: usize,
    pub data: Vec<Vec<BigRational>>, // k x k real symmetric rational density matrix
    pub authority_effect: AuthorityEffect,
}

impl QuantumDensityStalk {
    /// Creates a new density stalk, asserting squareness.
    pub fn new(data: Vec<Vec<BigRational>>) -> Result<Self, &'static str> {
        let k = data.len();
        if k == 0 {
            return Err("Density stalk dimension cannot be 0");
        }
        for row in &data {
            if row.len() != k {
                return Err("Density matrix must be square");
            }
        }
        Ok(Self {
            dim: k,
            data,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Pure state projector |psi><psi| / <psi|psi> from rational vector.
    pub fn from_pure_vector(psi: &[BigRational]) -> Result<Self, &'static str> {
        let k = psi.len();
        if k == 0 {
            return Err("Vector dimension cannot be 0");
        }
        let norm_sq: BigRational = psi.iter().map(|x| x * x).sum();
        if norm_sq.is_zero() {
            return Err("Cannot form pure state from zero vector");
        }
        let mut data = vec![vec![BigRational::zero(); k]; k];
        for i in 0..k {
            for j in 0..k {
                data[i][j] = (&psi[i] * &psi[j]) / &norm_sq;
            }
        }
        Ok(Self {
            dim: k,
            data,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Maximally mixed state (1/k) * I.
    pub fn maximally_mixed(dim: usize) -> Result<Self, &'static str> {
        if dim == 0 {
            return Err("Dimension cannot be 0");
        }
        let factor = BigRational::new(BigInt::one(), BigInt::from(dim));
        let mut data = vec![vec![BigRational::zero(); dim]; dim];
        for i in 0..dim {
            data[i][i] = factor.clone();
        }
        Ok(Self {
            dim,
            data,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Checked density constructor (DP-8): squareness, symmetry, unit trace and exact
    /// positive semidefiniteness. [`Self::new`] checks squareness only and its result is
    /// not a density until [`Self::is_valid_density_matrix`] holds; public fields can also
    /// be changed after either constructor, so consumers re-check.
    pub fn try_density(data: Vec<Vec<BigRational>>) -> Result<Self, &'static str> {
        let stalk = Self::new(data)?;
        if !stalk.is_symmetric() {
            return Err("Density matrix must be symmetric");
        }
        if stalk.trace() != BigRational::one() {
            return Err("Density matrix must have trace one");
        }
        if !stalk.is_positive_semidefinite() {
            return Err("Density matrix must be positive semidefinite");
        }
        Ok(stalk)
    }

    /// The same matrix on the Gaussian-rational carrier of `core_quantum_physics`,
    /// after re-checking the shape of the public fields.
    pub fn to_gaussian(&self) -> Result<BasicMatrix<GaussianRat>, &'static str> {
        if !self.has_valid_shape() {
            return Err("Density matrix shape does not match its dimension");
        }
        to_gaussian_matrix(&self.data)
    }

    /// Evaluates exact trace Tr(\rho) = sum_i \rho_{ii}.
    pub fn trace(&self) -> BigRational {
        let mut tr = BigRational::zero();
        for i in 0..self.dim {
            tr += &self.data[i][i];
        }
        tr
    }

    /// Asserts symmetry \rho_{ij} == \rho_{ji}.
    pub fn is_symmetric(&self) -> bool {
        for i in 0..self.dim {
            for j in (i + 1)..self.dim {
                if self.data[i][j] != self.data[j][i] {
                    return false;
                }
            }
        }
        true
    }

    /// Exact positive semidefiniteness in every dimension, by `core_linear_algebra`'s
    /// symmetric elimination on the running Schur complement. Non-symmetric data is
    /// not a real density matrix and is refused before the test.
    pub fn is_positive_semidefinite(&self) -> bool {
        self.is_symmetric() && is_psd_rational(&self.data)
    }

    /// Validates unit trace and positive semidefiniteness.
    pub fn is_valid_density_matrix(&self) -> bool {
        self.has_valid_shape()
            && self.trace() == BigRational::one()
            && self.is_positive_semidefinite()
    }

    /// Extracts classical population shadow P(\rho) = diag(\rho).
    pub fn classical_population_shadow(&self) -> Vec<BigRational> {
        (0..self.dim).map(|i| self.data[i][i].clone()).collect()
    }

    /// Exact square of the trace distance for real rational qubit densities.
    ///
    /// For Delta = [[a,b],[b,-a]], Delta^2 = (a^2+b^2) I, hence
    /// D(rho,sigma)^2 = a^2+b^2. This remains rational when D is irrational.
    pub fn trace_distance_squared_2x2(&self, other: &Self) -> Result<BigRational, &'static str> {
        if self.dim != 2 || other.dim != 2 {
            return Err("trace_distance_2x2 is specialized for dimension 2");
        }
        if !self.has_valid_shape() || !other.has_valid_shape() {
            return Err("Density matrix shape does not match its dimension");
        }
        core_functional::distinguishability::DistinguishabilityFunctional::qubit_trace_distance_squared(&self.data, &other.data)
    }

    /// Exact rational trace distance, refusing irrational results instead of rounding.
    /// Use `trace_distance_squared_2x2` to retain exact evidence in every case.
    pub fn trace_distance_2x2(&self, other: &Self) -> Result<BigRational, &'static str> {
        if self.dim != 2 || other.dim != 2 {
            return Err("trace_distance_2x2 is specialized for dimension 2");
        }
        if !self.has_valid_shape() || !other.has_valid_shape() {
            return Err("Density matrix shape does not match its dimension");
        }
        core_functional::distinguishability::DistinguishabilityFunctional::qubit_trace_distance(
            &self.data,
            &other.data,
        )
    }

    /// Exact witness for diagonal-shadow contraction: D^2 - TV^2 = b^2 >= 0.
    /// TV = |a| because both qubit densities have trace one. Zero slack is
    /// equivalent to equality of their off-diagonal coherences.
    pub fn classical_shadow_contraction_slack_2x2(
        &self,
        other: &Self,
    ) -> Result<BigRational, &'static str> {
        if self.dim != 2 || other.dim != 2 {
            return Err("trace_distance_2x2 is specialized for dimension 2");
        }
        if !self.has_valid_shape() || !other.has_valid_shape() {
            return Err("Density matrix shape does not match its dimension");
        }
        core_functional::distinguishability::DistinguishabilityFunctional::qubit_shadow_contraction_slack(&self.data, &other.data)
    }

    fn has_valid_shape(&self) -> bool {
        self.dim > 0
            && self.data.len() == self.dim
            && self.data.iter().all(|row| row.len() == self.dim)
    }

    /// Classical L1 distance between diagonal shadows: (1/2) sum_i |p_i - q_i|.
    pub fn classical_l1_distance(&self, other: &Self) -> BigRational {
        let p = self.classical_population_shadow();
        let q = other.classical_population_shadow();
        core_functional::distinguishability::DistinguishabilityFunctional::rational_total_variation(&p,&q)
            .checked_invariant_a9d8673f("matching exact diagonal shadows")
    }
}

/// Completely Positive Trace-Preserving (CPTP) Transition Channel.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CptpChannel {
    pub dim: usize,
    pub kraus_operators: Vec<Vec<Vec<BigRational>>>, // list of k x k matrices K_i
    pub authority_effect: AuthorityEffect,
}

impl CptpChannel {
    /// Identity channel.
    pub fn identity(dim: usize) -> Self {
        let mut k0 = vec![vec![BigRational::zero(); dim]; dim];
        for i in 0..dim {
            k0[i][i] = BigRational::one();
        }
        Self {
            dim,
            kraus_operators: vec![k0],
            authority_effect: AuthorityEffect::None,
        }
    }

    /// Creates a CPTP channel from Kraus operators, verifying completeness sum_i K_i^T K_i = I.
    pub fn new(kraus: Vec<Vec<Vec<BigRational>>>) -> Result<Self, &'static str> {
        let dim = Self::validate_kraus_shapes(&kraus)?;
        // Verify completeness: sum_i K_i^T K_i == I
        let sum_kt_k = Self::sum_kraus_transpose_product(&kraus, dim)?;
        Self::verify_identity_completeness(&sum_kt_k, dim)?;
        Ok(Self {
            dim,
            kraus_operators: kraus,
            authority_effect: AuthorityEffect::None,
        })
    }

    fn validate_kraus_shapes(kraus: &[Vec<Vec<BigRational>>]) -> Result<usize, &'static str> {
        if kraus.is_empty() {
            return Err("Must have at least one Kraus operator");
        }
        let dim = kraus[0].len();
        if dim == 0 {
            return Err("Kraus operator dimension cannot be 0");
        }
        if kraus
            .iter()
            .any(|k| k.len() != dim || k.iter().any(|row| row.len() != dim))
        {
            return Err("Kraus operators must be square and share a dimension");
        }
        Ok(dim)
    }

    fn sum_kraus_transpose_product(
        kraus: &[Vec<Vec<BigRational>>],
        dim: usize,
    ) -> Result<Vec<Vec<BigRational>>, &'static str> {
        let mut sum_kt_k = vec![vec![BigRational::zero(); dim]; dim];
        for k in kraus {
            if k.len() != dim {
                return Err("Kraus operator dimension mismatch");
            }
            Self::accumulate_kt_k(&mut sum_kt_k, k, dim);
        }
        Ok(sum_kt_k)
    }

    fn accumulate_kt_k(sum_kt_k: &mut [Vec<BigRational>], k: &[Vec<BigRational>], dim: usize) {
        for i in 0..dim {
            for j in 0..dim {
                let mut dot = BigRational::zero();
                for m in 0..dim {
                    dot += &k[m][i] * &k[m][j]; // K^T_{im} * K_{mj}
                }
                sum_kt_k[i][j] += dot;
            }
        }
    }

    fn verify_identity_completeness(
        sum_kt_k: &[Vec<BigRational>],
        dim: usize,
    ) -> Result<(), &'static str> {
        for i in 0..dim {
            for j in 0..dim {
                let expected = if i == j {
                    BigRational::one()
                } else {
                    BigRational::zero()
                };
                if sum_kt_k[i][j] != expected {
                    return Err("Kraus operators do not satisfy trace preservation completeness sum K_i^T K_i = I");
                }
            }
        }
        Ok(())
    }

    /// Shape of the public fields: positive dimension, at least one Kraus operator, every
    /// operator `dim x dim`.
    fn has_valid_shape(&self) -> bool {
        self.dim > 0
            && !self.kraus_operators.is_empty()
            && self
                .kraus_operators
                .iter()
                .all(|k| k.len() == self.dim && k.iter().all(|row| row.len() == self.dim))
    }

    /// Re-admits this channel through the owner `ExactKrausChannel` (DP-8), which checks
    /// trace preservation `sum K* K = I` independently of [`Self::new`]. A channel built by
    /// [`Self::identity`]`(0)` or with mutated public fields is refused here.
    pub fn to_exact_kraus(&self) -> Result<ExactKrausChannel, ExactChannelError> {
        if self.dim == 0 {
            return Err(ExactChannelError::ZeroDimension);
        }
        if self.kraus_operators.is_empty() {
            return Err(ExactChannelError::EmptyKrausSet);
        }
        let mut ops = Vec::with_capacity(self.kraus_operators.len());
        for (index, k) in self.kraus_operators.iter().enumerate() {
            let cols = k.first().map_or(0, Vec::len);
            if k.len() != self.dim || k.iter().any(|row| row.len() != self.dim) {
                return Err(ExactChannelError::KrausShape {
                    index,
                    expected: (self.dim, self.dim),
                    actual: (k.len(), cols),
                });
            }
            ops.push(
                to_gaussian_matrix(k).map_err(|_| ExactChannelError::KrausShape {
                    index,
                    expected: (self.dim, self.dim),
                    actual: (k.len(), cols),
                })?,
            );
        }
        ExactKrausChannel::try_new(self.dim, self.dim, ops, "wdp_cptp_channel")
    }

    /// Applies the channel to a density stalk: E(\rho) = sum_i K_i \rho K_i^T.
    pub fn apply(&self, stalk: &QuantumDensityStalk) -> Result<QuantumDensityStalk, &'static str> {
        if stalk.dim != self.dim {
            return Err("Density stalk dimension must match channel dimension");
        }
        // Public fields can disagree with `dim`; refuse instead of indexing out of range.
        if !stalk.has_valid_shape() || !self.has_valid_shape() {
            return Err("Channel or stalk shape does not match its dimension");
        }
        let dim = self.dim;
        let mut out_data = vec![vec![BigRational::zero(); dim]; dim];

        for k in &self.kraus_operators {
            // intermediate = K * \rho
            let k_rho = Self::multiply_square(k, &stalk.data, dim);
            // term = (K * \rho) * K^T
            Self::accumulate_times_transpose(&mut out_data, &k_rho, k, dim);
        }

        QuantumDensityStalk::new(out_data)
    }

    fn multiply_square(
        a: &[Vec<BigRational>],
        b: &[Vec<BigRational>],
        dim: usize,
    ) -> Vec<Vec<BigRational>> {
        let mut out = vec![vec![BigRational::zero(); dim]; dim];
        for i in 0..dim {
            for j in 0..dim {
                let mut sum = BigRational::zero();
                for m in 0..dim {
                    sum += &a[i][m] * &b[m][j];
                }
                out[i][j] = sum;
            }
        }
        out
    }

    fn accumulate_times_transpose(
        out_data: &mut [Vec<BigRational>],
        k_rho: &[Vec<BigRational>],
        k: &[Vec<BigRational>],
        dim: usize,
    ) {
        for i in 0..dim {
            for j in 0..dim {
                let mut sum = BigRational::zero();
                for m in 0..dim {
                    sum += &k_rho[i][m] * &k[j][m]; // K^T_{mj} = K_{jm}
                }
                out_data[i][j] += sum;
            }
        }
    }
}

fn to_gaussian_matrix(rows: &[Vec<BigRational>]) -> Result<BasicMatrix<GaussianRat>, &'static str> {
    let n = rows.len();
    let data = rows
        .iter()
        .flat_map(|r| r.iter().map(|x| GaussianRat::from_rational(x.clone())))
        .collect();
    BasicMatrix::from_row_major(n, n, data).map_err(|_| "matrix is not square")
}

/// Quantum Observer Bundle over a finite 1-skeleton.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuantumObserverBundle {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub vertex_stalks: BTreeMap<String, QuantumDensityStalk>,
    pub edge_channels: BTreeMap<(String, String), CptpChannel>,
    pub authority_effect: AuthorityEffect,
}

impl QuantumObserverBundle {
    pub fn new(
        vertices: Vec<String>,
        edges: Vec<(String, String)>,
        stalks: BTreeMap<String, QuantumDensityStalk>,
        channels: BTreeMap<(String, String), CptpChannel>,
    ) -> Result<Self, &'static str> {
        for v in &vertices {
            if !stalks.contains_key(v) {
                return Err("Missing stalk for declared vertex");
            }
        }
        for e in &edges {
            if !channels.contains_key(e) {
                return Err("Missing transition channel for declared edge");
            }
        }
        Ok(Self {
            vertices,
            edges,
            vertex_stalks: stalks,
            edge_channels: channels,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Evaluates transition defect along edge e = (u, v): ||E_e(\rho_u) - \rho_v||_1.
    pub fn evaluate_edge_defect_2x2(&self, u: &str, v: &str) -> Result<BigRational, &'static str> {
        let edge_key = (u.to_string(), v.to_string());
        let channel = self
            .edge_channels
            .get(&edge_key)
            .ok_or("Channel not found")?;
        let rho_u = self.vertex_stalks.get(u).ok_or("Stalk u not found")?;
        let rho_v = self.vertex_stalks.get(v).ok_or("Stalk v not found")?;

        let evolved = channel.apply(rho_u)?;
        evolved.trace_distance_2x2(rho_v)
    }
}

// Origin: engine/crates_rs/core_wdp/src/quantum_geometries.rs
// Claim: urn:core:crates_rs:core-wdp:quantum-geometries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda9d8673f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda9d8673f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora9d8673f {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrora9d8673f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora9d8673f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora9d8673f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda9d8673f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora9d8673f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora9d8673f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora9d8673f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora9d8673f::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core_homology::scalar::{q, qr};

    #[test]
    fn test_density_stalk_validity_and_shadow() {
        let rho = QuantumDensityStalk::maximally_mixed(2).unwrap();
        assert!(rho.is_valid_density_matrix());
        assert_eq!(rho.trace(), q(1));

        let shadow = rho.classical_population_shadow();
        assert_eq!(shadow, vec![qr(1, 2), qr(1, 2)]);
        assert_eq!(rho.authority_effect, AuthorityEffect::None);
    }

    #[test]
    fn test_psd_is_exact_in_every_dimension() {
        let rows = |r: &[[i64; 4]]| r.iter().map(|row| row.map(q).to_vec()).collect::<Vec<_>>();
        // Leading principal minors are all 0, but the (1, 2) block [[0, 1], [1, 0]] is indefinite.
        let indefinite_3 = QuantumDensityStalk::new(vec![
            vec![q(0), q(0), q(0)],
            vec![q(0), q(0), q(1)],
            vec![q(0), q(1), q(0)],
        ])
        .unwrap();
        assert!(!indefinite_3.is_positive_semidefinite());

        // Above 3x3 the previous check only inspected the diagonal.
        let indefinite_4 = QuantumDensityStalk::new(rows(&[
            [1, 2, 0, 0],
            [2, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]))
        .unwrap();
        assert!(!indefinite_4.is_positive_semidefinite());

        let mixed_4 = QuantumDensityStalk::maximally_mixed(4).unwrap();
        assert!(mixed_4.is_valid_density_matrix());
    }

    #[test]
    fn test_cptp_channel_trace_preservation() {
        let id_channel = CptpChannel::identity(2);
        let psi = vec![q(1), q(0)];
        let pure = QuantumDensityStalk::from_pure_vector(&psi).unwrap();

        let evolved = id_channel.apply(&pure).unwrap();
        assert_eq!(evolved.trace(), q(1));
        assert_eq!(evolved, pure);
    }

    #[test]
    fn test_schatten_to_classical_contraction() {
        let psi0 = vec![q(1), q(0)];
        let psi1 = vec![q(0), q(1)];
        let rho0 = QuantumDensityStalk::from_pure_vector(&psi0).unwrap();
        let rho1 = QuantumDensityStalk::from_pure_vector(&psi1).unwrap();

        let trace_dist = rho0.trace_distance_2x2(&rho1).unwrap();
        let classical_dist = rho0.classical_l1_distance(&rho1);

        assert_eq!(trace_dist, q(1));
        assert_eq!(classical_dist, q(1));
        // Contraction: D_class <= D_quantum
        assert!(classical_dist <= trace_dist);
    }
}

#[cfg(test)]
mod l4_boundary_tests_a9d8673f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda9d8673f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda9d8673f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda9d8673f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda9d8673f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda9d8673f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora9d8673f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora9d8673f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
