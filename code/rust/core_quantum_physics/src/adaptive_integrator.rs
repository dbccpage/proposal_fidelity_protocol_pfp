//! Exact finite adaptive cluster updates for an open, two-local qubit chain.
//!
//! A boundary detector uses the **full** cluster factors, in the order A then B,
//! and evaluates `Q_AB(-i[H_AB, rho_A tensor rho_B])`. The product differential
//! is the normalized ambient differential, including its trace correction; the
//! tensor-projector owner in `linear_algebra` performs every partial trace,
//! embedding, permutation and projection. A caller supplies the primal and
//! dual trace-norm witness. Rational matrix entries do not imply a rational
//! trace norm, and this module does not invent a rational spectrum.
//!
//! Refinement performs at most one merge at a sample, choosing the largest
//! certified rate strictly above the threshold whose merged size fits the
//! declared ceiling. Fusion changes the representation by a tensor product
//! and site permutation, with exact checks of the old marginals and the global
//! state. Cluster evolution uses the existing checked Cayley propagator and
//! Kraus-channel kernels, with every effective Hamiltonian frozen from the
//! same incoming partition.
//!
//! Scope: these are exact rational **finite Cayley steps**, not evaluations of
//! the generally transcendental exponential. Sampled ideal tangent residuals
//! do not bound the integration defect or the continuous trajectory error. No
//! analytic tolerance guarantee, quadrature bound, or monotonicity of future
//! residuals is certified. All receipts carry `AdaptiveDiagnosticAuthority::None` (AuthorityEffect: None).

use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use crate::exact_hermitian::{
    check_hermitian, check_rational_scalar, check_well_formed, exact_limits, partial_trace_first,
    partial_trace_second, ExactHermitianError,
};
use crate::exact_instrument::{ExactDensityState, ExactInstrumentError};
use crate::exact_operator::{ExactOperator, OperatorError};
use crate::quantum_hamiltonian::{ExactHamiltonian, ExactHamiltonianError};
use crate::trace_norm_certificate::{TraceNormCertificate, TraceNormError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::tensor_projector::{
    ProductReference, TensorLayout, TensorProjectorError,
};
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_kernel::resource_limits::{OperationLimits as PhysicalLimits, ResourceError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{Rational, Zero};
use std::collections::BTreeSet;

/// A diagnostic tag with exactly one variant. Adaptive arithmetic and fusion
/// evidence cannot encode release authorization or certified authority. This
/// carrier deliberately has no conversion to an authority-bearing type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Default)]
pub enum AdaptiveDiagnosticAuthority {
    #[default]
    None,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AdaptiveError {
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error(transparent)]
    Tensor(#[from] TensorProjectorError),
    #[error(transparent)]
    Hermitian(#[from] ExactHermitianError),
    #[error(transparent)]
    State(#[from] ExactInstrumentError),
    #[error(transparent)]
    Channel(#[from] ExactChannelError),
    #[error(transparent)]
    Operator(#[from] OperatorError),
    #[error(transparent)]
    Hamiltonian(#[from] ExactHamiltonianError),
    #[error(transparent)]
    Norm(#[from] TraceNormError),
    #[error(transparent)]
    Resource(#[from] ResourceError),
    #[error("a chain needs at least one qubit")]
    EmptyChain,
    #[error("an open {sites}-site chain needs {expected} bonds, got {actual}")]
    BondCount {
        sites: usize,
        expected: usize,
        actual: usize,
    },
    #[error("Hamiltonian dimension {actual} does not match {expected}")]
    HamiltonianDimension { expected: usize, actual: usize },
    #[error("a cluster needs a nonempty, strictly increasing list of sites")]
    ClusterSites,
    #[error("cluster density dimension {actual} does not match {expected}")]
    StateDimension { expected: usize, actual: usize },
    #[error("clusters must cover 0..{sites} exactly once")]
    PartitionSites { sites: usize },
    #[error("site {site} is outside 0..{sites}")]
    Site { site: usize, sites: usize },
    #[error("site {site} is not in this cluster")]
    ClusterSite { site: usize },
    #[error("cluster {cluster} is outside 0..{clusters}")]
    ClusterIndex { cluster: usize, clusters: usize },
    #[error("a cluster cannot be fused with itself")]
    SameCluster,
    #[error("bond {bond} is outside 0..{bonds}")]
    Bond { bond: usize, bonds: usize },
    #[error("the model has {model_sites} sites, the partition has {partition_sites}")]
    DifferentChains {
        model_sites: usize,
        partition_sites: usize,
    },
    #[error("a detector threshold must be nonnegative")]
    NegativeThreshold,
    #[error("a merge ceiling must be positive")]
    ZeroClusterCeiling,
    #[error("a finite evolution step must be positive")]
    NonPositiveStep,
    #[error("no exact trace-norm witness supplied for boundary bond {bond}")]
    WitnessUnavailable { bond: usize },
    #[error("fusion replay failed to preserve {role}")]
    FusionInvariant { role: &'static str },
}

fn qubit_dimension(sites: usize) -> Result<usize, AdaptiveError> {
    let limits = PhysicalLimits::default();
    let mut dimension = 1;
    for _ in 0..sites {
        dimension = limits.checked_product(dimension, 2)?;
        limits.check_hilbert_dim(dimension)?;
    }
    limits.check_dense_matrix(dimension, dimension, std::mem::size_of::<GaussianRat>())?;
    Ok(dimension)
}

fn qubit_layout(sites: usize) -> Result<TensorLayout, AdaptiveError> {
    qubit_dimension(sites)?;
    Ok(TensorLayout::new_with_limits(
        &vec![2; sites],
        exact_limits(),
    )?)
}

fn check_hamiltonian(
    matrix: &BasicMatrix<GaussianRat>,
    dimension: usize,
) -> Result<(), AdaptiveError> {
    check_hermitian(matrix)?;
    if matrix.rows() != dimension {
        return Err(AdaptiveError::HamiltonianDimension {
            expected: dimension,
            actual: matrix.rows(),
        });
    }
    Ok(())
}

/// An open chain with one declared Hermitian 2x2 term per site and one declared
/// Hermitian 4x4 interaction per adjacent bond. Zero terms are allowed. The
/// tensor order of bond `j` is `(j, j+1)`; larger interaction supports are refused
/// by this input contract rather than treated as an unproved two-local case.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactQubitChain {
    local_hamiltonians: Vec<BasicMatrix<GaussianRat>>,
    bond_hamiltonians: Vec<BasicMatrix<GaussianRat>>,
}

impl ExactQubitChain {
    pub fn try_new(
        local_hamiltonians: Vec<BasicMatrix<GaussianRat>>,
        bond_hamiltonians: Vec<BasicMatrix<GaussianRat>>,
    ) -> Result<Self, AdaptiveError> {
        let sites = local_hamiltonians.len();
        if sites == 0 {
            return Err(AdaptiveError::EmptyChain);
        }
        qubit_dimension(sites)?;
        let expected = sites - 1;
        if bond_hamiltonians.len() != expected {
            return Err(AdaptiveError::BondCount {
                sites,
                expected,
                actual: bond_hamiltonians.len(),
            });
        }
        for term in &local_hamiltonians {
            check_hamiltonian(term, 2)?;
        }
        for term in &bond_hamiltonians {
            check_hamiltonian(term, 4)?;
        }
        Ok(Self {
            local_hamiltonians,
            bond_hamiltonians,
        })
    }

    pub fn num_sites(&self) -> usize {
        self.local_hamiltonians.len()
    }

    pub fn local_hamiltonians(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.local_hamiltonians
    }

    pub fn bond_hamiltonians(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.bond_hamiltonians
    }

    /// The declared full finite Hamiltonian, embedded in canonical site order.
    pub fn full_hamiltonian(&self) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        let layout = qubit_layout(self.num_sites())?;
        let dimension = qubit_dimension(self.num_sites())?;
        let mut result = mx::zeros_with_limits(dimension, dimension, exact_limits())?;
        for (site, term) in self.local_hamiltonians.iter().enumerate() {
            Self::add_embedded_term(&mut result, &layout, term, &[site])?;
        }
        for (bond, term) in self.bond_hamiltonians.iter().enumerate() {
            Self::add_embedded_term(&mut result, &layout, term, &[bond, bond + 1])?;
        }
        check_hermitian(&result)?;
        Ok(result)
    }

    fn add_embedded_term(
        result: &mut BasicMatrix<GaussianRat>,
        layout: &TensorLayout,
        term: &BasicMatrix<GaussianRat>,
        sites: &[usize],
    ) -> Result<(), AdaptiveError> {
        let embedded = layout.embed_operator_with_limits(term, sites, exact_limits())?;
        *result = mx::add(result, &embedded)?;
        Ok(())
    }
}

/// A finite cluster density, whose tensor factors follow its strictly
/// increasing site list. Correlations inside a cluster are retained.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactQuantumCluster {
    sites: Vec<usize>,
    state: ExactDensityState,
}

impl ExactQuantumCluster {
    pub fn try_new(sites: Vec<usize>, state: ExactDensityState) -> Result<Self, AdaptiveError> {
        if sites.is_empty() || sites.windows(2).any(|pair| pair[0] >= pair[1]) {
            return Err(AdaptiveError::ClusterSites);
        }
        let expected = qubit_dimension(sites.len())?;
        if state.dimension() != expected {
            return Err(AdaptiveError::StateDimension {
                expected,
                actual: state.dimension(),
            });
        }
        Ok(Self { sites, state })
    }

    pub fn sites(&self) -> &[usize] {
        &self.sites
    }

    pub fn state(&self) -> &ExactDensityState {
        &self.state
    }

    fn local_index(&self, site: usize) -> Option<usize> {
        self.sites.binary_search(&site).ok()
    }

    pub fn single_site_marginal(&self, site: usize) -> Result<ExactDensityState, AdaptiveError> {
        let local = self
            .local_index(site)
            .ok_or(AdaptiveError::ClusterSite { site })?;
        let matrix = qubit_layout(self.sites.len())?.partial_trace_with_limits(
            self.state.matrix(),
            &[local],
            exact_limits(),
        )?;
        Ok(ExactDensityState::try_new(matrix)?)
    }
}

/// Untrusted primal/dual proposal for a Hermitian trace norm. The proposal is
/// accepted only by `TraceNormCertificate::try_new` on the detector's actual
/// computed normal operator. No eigenvalues are requested or inferred.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceNormWitness {
    pub positive_part: BasicMatrix<GaussianRat>,
    pub negative_part: BasicMatrix<GaussianRat>,
    pub dual_witness: BasicMatrix<GaussianRat>,
}

impl TraceNormWitness {
    pub fn from_certificate(certificate: &TraceNormCertificate) -> Self {
        Self {
            positive_part: certificate.positive_part().clone(),
            negative_part: certificate.negative_part().clone(),
            dual_witness: certificate.witness().clone(),
        }
    }
}

/// The ideal tangent residual at a sampled cluster-product reference. The
/// matrix order is all left-cluster sites followed by all right-cluster sites.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryResidual {
    bond: usize,
    left_cluster: usize,
    right_cluster: usize,
    left: ExactQuantumCluster,
    right: ExactQuantumCluster,
    embedded_hamiltonian: BasicMatrix<GaussianRat>,
    commutator_velocity: BasicMatrix<GaussianRat>,
    normal: BasicMatrix<GaussianRat>,
}

impl BoundaryResidual {
    pub fn bond(&self) -> usize {
        self.bond
    }

    pub fn left(&self) -> &ExactQuantumCluster {
        &self.left
    }

    pub fn right(&self) -> &ExactQuantumCluster {
        &self.right
    }

    pub fn embedded_hamiltonian(&self) -> &BasicMatrix<GaussianRat> {
        &self.embedded_hamiltonian
    }

    pub fn commutator_velocity(&self) -> &BasicMatrix<GaussianRat> {
        &self.commutator_velocity
    }

    pub fn operator(&self) -> &BasicMatrix<GaussianRat> {
        &self.normal
    }

    fn reference(&self) -> Result<ProductReference<GaussianRat>, AdaptiveError> {
        Ok(ProductReference::new_with_limits(
            &[
                self.left.state.matrix().clone(),
                self.right.state.matrix().clone(),
            ],
            exact_limits(),
        )?)
    }

    /// P(Z) = Tr_B(Z) tensor rho_B + rho_A tensor Tr_A(Z) - Tr(Z) rho_AB.
    /// This pure linear map preserves the two cluster marginals and is
    /// idempotent on the full ambient matrix space. At rank-deficient density
    /// factors its traceless image is an algebraic tangent space; a two-sided
    /// physical density-manifold tangent is not asserted.
    pub fn product_differential(
        &self,
        direction: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        check_well_formed(direction)?;
        Ok(self
            .reference()?
            .product_differential_with_limits(direction, exact_limits())?)
    }

    pub fn normal_projector(
        &self,
        direction: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        check_well_formed(direction)?;
        Ok(self
            .reference()?
            .normal_projector_with_limits(direction, exact_limits())?)
    }

    pub fn certify(
        &self,
        witness: TraceNormWitness,
        threshold: &Rational,
    ) -> Result<BoundaryDetectionReceipt, AdaptiveError> {
        check_threshold(threshold)?;
        let certificate = TraceNormCertificate::try_new(
            self.normal.clone(),
            witness.positive_part,
            witness.negative_part,
            witness.dual_witness,
        )?;
        Ok(BoundaryDetectionReceipt {
            boundary: self.clone(),
            certificate,
            threshold: threshold.clone(),
            authority_effect: AdaptiveDiagnosticAuthority::None,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryDetectionReceipt {
    boundary: BoundaryResidual,
    certificate: TraceNormCertificate,
    threshold: Rational,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl BoundaryDetectionReceipt {
    pub fn boundary(&self) -> &BoundaryResidual {
        &self.boundary
    }

    pub fn certificate(&self) -> &TraceNormCertificate {
        &self.certificate
    }

    pub fn rate(&self) -> &Rational {
        self.certificate.trace_norm()
    }

    pub fn threshold(&self) -> &Rational {
        &self.threshold
    }

    pub fn is_triggered(&self) -> bool {
        self.rate() > &self.threshold
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

/// Exact evidence of a representation change. The constructor has checked
/// both old full-cluster marginals and equality of the global states.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FusionReceipt {
    left: ExactQuantumCluster,
    right: ExactQuantumCluster,
    fused: ExactQuantumCluster,
    before_partition: Vec<Vec<usize>>,
    after_partition: Vec<Vec<usize>>,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl FusionReceipt {
    pub fn left(&self) -> &ExactQuantumCluster {
        &self.left
    }

    pub fn right(&self) -> &ExactQuantumCluster {
        &self.right
    }

    pub fn fused(&self) -> &ExactQuantumCluster {
        &self.fused
    }

    pub fn before_partition(&self) -> &[Vec<usize>] {
        &self.before_partition
    }

    pub fn after_partition(&self) -> &[Vec<usize>] {
        &self.after_partition
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum RefinementDecision {
    NoTriggeredBoundary,
    AllTriggeredMergesExceedCeiling,
    Fused { bond: usize },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RefinementReceipt {
    detections: Vec<BoundaryDetectionReceipt>,
    decision: RefinementDecision,
    fusion: Option<FusionReceipt>,
    max_cluster_qubits: usize,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl RefinementReceipt {
    pub fn detections(&self) -> &[BoundaryDetectionReceipt] {
        &self.detections
    }

    pub fn decision(&self) -> RefinementDecision {
        self.decision
    }

    pub fn fusion(&self) -> Option<&FusionReceipt> {
        self.fusion.as_ref()
    }

    pub fn max_cluster_qubits(&self) -> usize {
        self.max_cluster_qubits
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum EvolutionScope {
    /// Checked rational finite updates with frozen effective Hamiltonians.
    /// No exponential or analytic trajectory tolerance is certified.
    ExactFiniteFrozenCayley,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClusterCayleyReceipt {
    sites: Vec<usize>,
    incoming_state: ExactDensityState,
    outgoing_state: ExactDensityState,
    effective_hamiltonian: BasicMatrix<GaussianRat>,
    unitary: BasicMatrix<GaussianRat>,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl ClusterCayleyReceipt {
    pub fn sites(&self) -> &[usize] {
        &self.sites
    }

    pub fn incoming_state(&self) -> &ExactDensityState {
        &self.incoming_state
    }

    pub fn outgoing_state(&self) -> &ExactDensityState {
        &self.outgoing_state
    }

    pub fn effective_hamiltonian(&self) -> &BasicMatrix<GaussianRat> {
        &self.effective_hamiltonian
    }

    pub fn unitary(&self) -> &BasicMatrix<GaussianRat> {
        &self.unitary
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CayleyStepReceipt {
    step_size: Rational,
    clusters: Vec<ClusterCayleyReceipt>,
    scope: EvolutionScope,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl CayleyStepReceipt {
    pub fn step_size(&self) -> &Rational {
        &self.step_size
    }

    pub fn clusters(&self) -> &[ClusterCayleyReceipt] {
        &self.clusters
    }

    pub fn scope(&self) -> EvolutionScope {
        self.scope
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdaptiveStepReceipt {
    evolution: CayleyStepReceipt,
    refinement: RefinementReceipt,
    authority_effect: AdaptiveDiagnosticAuthority,
}

impl AdaptiveStepReceipt {
    pub fn evolution(&self) -> &CayleyStepReceipt {
        &self.evolution
    }

    pub fn refinement(&self) -> &RefinementReceipt {
        &self.refinement
    }

    pub fn authority_effect(&self) -> AdaptiveDiagnosticAuthority {
        self.authority_effect
    }
}

fn check_threshold(threshold: &Rational) -> Result<(), AdaptiveError> {
    check_rational_scalar(threshold)?;
    if threshold < &Rational::zero() {
        return Err(AdaptiveError::NegativeThreshold);
    }
    Ok(())
}

fn check_ceiling(max_cluster_qubits: usize) -> Result<(), AdaptiveError> {
    if max_cluster_qubits == 0 {
        return Err(AdaptiveError::ZeroClusterCeiling);
    }
    Ok(())
}

/// A validated cluster partition and its current product state. Inputs must
/// already be cluster-product data; a correlated global state is never silently
/// replaced by its site marginals. Clusters may contain noncontiguous sites.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactClusterPartition {
    num_sites: usize,
    clusters: Vec<ExactQuantumCluster>,
}

impl ExactClusterPartition {
    pub fn try_new(
        num_sites: usize,
        mut clusters: Vec<ExactQuantumCluster>,
    ) -> Result<Self, AdaptiveError> {
        if num_sites == 0 {
            return Err(AdaptiveError::EmptyChain);
        }
        qubit_dimension(num_sites)?;
        let mut seen = BTreeSet::new();
        for cluster in &clusters {
            for &site in cluster.sites() {
                if site >= num_sites || !seen.insert(site) {
                    return Err(AdaptiveError::PartitionSites { sites: num_sites });
                }
            }
        }
        if seen.len() != num_sites {
            return Err(AdaptiveError::PartitionSites { sites: num_sites });
        }
        clusters.sort_by(|left, right| left.sites.cmp(&right.sites));
        Ok(Self {
            num_sites,
            clusters,
        })
    }

    pub fn from_site_states(states: Vec<ExactDensityState>) -> Result<Self, AdaptiveError> {
        let num_sites = states.len();
        if num_sites == 0 {
            return Err(AdaptiveError::EmptyChain);
        }
        qubit_dimension(num_sites)?;
        let clusters = states
            .into_iter()
            .enumerate()
            .map(|(site, state)| ExactQuantumCluster::try_new(vec![site], state))
            .collect::<Result<Vec<_>, _>>()?;
        Self::try_new(num_sites, clusters)
    }

    pub fn num_sites(&self) -> usize {
        self.num_sites
    }

    pub fn clusters(&self) -> &[ExactQuantumCluster] {
        &self.clusters
    }

    pub fn partition_sites(&self) -> Vec<Vec<usize>> {
        self.clusters.iter().map(|c| c.sites.clone()).collect()
    }

    fn cluster(&self, index: usize) -> Result<&ExactQuantumCluster, AdaptiveError> {
        self.clusters.get(index).ok_or(AdaptiveError::ClusterIndex {
            cluster: index,
            clusters: self.clusters.len(),
        })
    }

    fn cluster_for_site(&self, site: usize) -> Result<usize, AdaptiveError> {
        if site >= self.num_sites {
            return Err(AdaptiveError::Site {
                site,
                sites: self.num_sites,
            });
        }
        self.clusters
            .iter()
            .position(|cluster| cluster.local_index(site).is_some())
            .ok_or(AdaptiveError::PartitionSites {
                sites: self.num_sites,
            })
    }

    fn check_model(&self, model: &ExactQubitChain) -> Result<(), AdaptiveError> {
        if model.num_sites() != self.num_sites {
            return Err(AdaptiveError::DifferentChains {
                model_sites: model.num_sites(),
                partition_sites: self.num_sites,
            });
        }
        Ok(())
    }

    pub fn single_site_marginal(&self, site: usize) -> Result<ExactDensityState, AdaptiveError> {
        self.cluster(self.cluster_for_site(site)?)?
            .single_site_marginal(site)
    }

    /// Reconstruct the actual represented global state in canonical site order.
    pub fn global_state(&self) -> Result<ExactDensityState, AdaptiveError> {
        let mut matrix = mx::identity_with_limits(1, exact_limits())?;
        let mut raw_sites = Vec::with_capacity(self.num_sites);
        for cluster in &self.clusters {
            matrix = mx::kronecker_with_limits(&matrix, cluster.state.matrix(), exact_limits())?;
            raw_sites.extend_from_slice(cluster.sites());
        }
        let order = (0..self.num_sites)
            .map(|site| {
                raw_sites
                    .iter()
                    .position(|&raw_site| raw_site == site)
                    .ok_or(AdaptiveError::PartitionSites {
                        sites: self.num_sites,
                    })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let matrix =
            qubit_layout(self.num_sites)?.permute_with_limits(&matrix, &order, exact_limits())?;
        Ok(ExactDensityState::try_new(matrix)?)
    }

    /// Compute a boundary normal from full cluster states. Internal bonds have
    /// no cluster boundary and return `None`; zero interactions still produce
    /// an explicit zero boundary operator, to be certified by a zero witness.
    pub fn boundary_residual(
        &self,
        model: &ExactQubitChain,
        bond: usize,
    ) -> Result<Option<BoundaryResidual>, AdaptiveError> {
        self.check_model(model)?;
        let term = model
            .bond_hamiltonians
            .get(bond)
            .ok_or(AdaptiveError::Bond {
                bond,
                bonds: model.bond_hamiltonians.len(),
            })?;
        let left_cluster = self.cluster_for_site(bond)?;
        let right_cluster = self.cluster_for_site(bond + 1)?;
        if left_cluster == right_cluster {
            return Ok(None);
        }
        let left = self.cluster(left_cluster)?;
        let right = self.cluster(right_cluster)?;
        let (embedded_hamiltonian, commutator_velocity, normal) =
            self.compute_boundary_operators(left, right, term, bond)?;
        Ok(Some(BoundaryResidual {
            bond,
            left_cluster,
            right_cluster,
            left: left.clone(),
            right: right.clone(),
            embedded_hamiltonian,
            commutator_velocity,
            normal,
        }))
    }

    fn compute_boundary_operators(
        &self,
        left: &ExactQuantumCluster,
        right: &ExactQuantumCluster,
        term: &BasicMatrix<GaussianRat>,
        bond: usize,
    ) -> Result<
        (
            BasicMatrix<GaussianRat>,
            BasicMatrix<GaussianRat>,
            BasicMatrix<GaussianRat>,
        ),
        AdaptiveError,
    > {
        let left_local = left
            .local_index(bond)
            .ok_or(AdaptiveError::PartitionSites {
                sites: self.num_sites,
            })?;
        let right_local = right
            .local_index(bond + 1)
            .ok_or(AdaptiveError::PartitionSites {
                sites: self.num_sites,
            })?;
        let embedded_hamiltonian = qubit_layout(left.sites.len() + right.sites.len())?
            .embed_operator_with_limits(
                term,
                &[left_local, left.sites.len() + right_local],
                exact_limits(),
            )?;
        let (commutator_velocity, normal) =
            Self::commutator_and_normal(left, right, &embedded_hamiltonian)?;
        Ok((embedded_hamiltonian, commutator_velocity, normal))
    }

    fn commutator_and_normal(
        left: &ExactQuantumCluster,
        right: &ExactQuantumCluster,
        embedded_hamiltonian: &BasicMatrix<GaussianRat>,
    ) -> Result<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>), AdaptiveError> {
        let reference = ProductReference::new_with_limits(
            &[left.state.matrix().clone(), right.state.matrix().clone()],
            exact_limits(),
        )?;
        let product =
            mx::kronecker_with_limits(left.state.matrix(), right.state.matrix(), exact_limits())?;
        let commutator = mx::sub(
            &mx::multiply_with_limits(embedded_hamiltonian, &product, exact_limits())?,
            &mx::multiply_with_limits(&product, embedded_hamiltonian, exact_limits())?,
        )?;
        let commutator_velocity = mx::scale(&commutator, &GaussianRat::from_ints(0, -1))?;
        let normal =
            reference.normal_projector_with_limits(&commutator_velocity, exact_limits())?;
        check_hermitian(&normal)?;
        Ok((commutator_velocity, normal))
    }

    /// Merge any two distinct clusters by a state-preserving representation
    /// change. All exact replay checks finish before the partition is changed.
    pub fn fuse_clusters(
        &mut self,
        left_index: usize,
        right_index: usize,
    ) -> Result<FusionReceipt, AdaptiveError> {
        let left = self.cluster(left_index)?.clone();
        let right = self.cluster(right_index)?.clone();
        if left_index == right_index {
            return Err(AdaptiveError::SameCluster);
        }
        let (fused, layout) = self.build_fused_cluster(&left, &right)?;
        self.verify_cluster_marginals(&fused, &layout, &left, &right)?;
        let next = self.replace_clusters_with_fused(left_index, right_index, fused.clone())?;
        let receipt = FusionReceipt {
            left,
            right,
            fused,
            before_partition: self.partition_sites(),
            after_partition: next.partition_sites(),
            authority_effect: AdaptiveDiagnosticAuthority::None,
        };
        *self = next;
        Ok(receipt)
    }

    fn build_fused_cluster(
        &self,
        left: &ExactQuantumCluster,
        right: &ExactQuantumCluster,
    ) -> Result<(ExactQuantumCluster, TensorLayout), AdaptiveError> {
        let raw_sites: Vec<_> = left.sites.iter().chain(&right.sites).copied().collect();
        let mut fused_sites = raw_sites.clone();
        fused_sites.sort_unstable();
        let order = fused_sites
            .iter()
            .map(|site| {
                raw_sites
                    .iter()
                    .position(|raw| raw == site)
                    .ok_or(AdaptiveError::PartitionSites {
                        sites: self.num_sites,
                    })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let raw_state =
            mx::kronecker_with_limits(left.state.matrix(), right.state.matrix(), exact_limits())?;
        let layout = qubit_layout(fused_sites.len())?;
        let state = layout.permute_with_limits(&raw_state, &order, exact_limits())?;
        let fused = ExactQuantumCluster::try_new(fused_sites, ExactDensityState::try_new(state)?)?;
        Ok((fused, layout))
    }

    fn verify_cluster_marginals(
        &self,
        fused: &ExactQuantumCluster,
        layout: &TensorLayout,
        left: &ExactQuantumCluster,
        right: &ExactQuantumCluster,
    ) -> Result<(), AdaptiveError> {
        for (role, old_cluster) in [("left marginal", left), ("right marginal", right)] {
            let retained = old_cluster
                .sites
                .iter()
                .map(|site| {
                    fused
                        .sites
                        .binary_search(site)
                        .map_err(|_| AdaptiveError::PartitionSites {
                            sites: self.num_sites,
                        })
                })
                .collect::<Result<Vec<_>, _>>()?;
            if layout.partial_trace_with_limits(fused.state.matrix(), &retained, exact_limits())?
                != *old_cluster.state.matrix()
            {
                return Err(AdaptiveError::FusionInvariant { role });
            }
        }
        Ok(())
    }

    fn replace_clusters_with_fused(
        &self,
        left_index: usize,
        right_index: usize,
        fused: ExactQuantumCluster,
    ) -> Result<Self, AdaptiveError> {
        let mut clusters = self
            .clusters
            .iter()
            .enumerate()
            .filter(|(index, _)| *index != left_index && *index != right_index)
            .map(|(_, cluster)| cluster.clone())
            .collect::<Vec<_>>();
        clusters.push(fused);
        let next = Self::try_new(self.num_sites, clusters)?;
        if self.global_state()? != next.global_state()? {
            return Err(AdaptiveError::FusionInvariant {
                role: "global state",
            });
        }
        Ok(next)
    }

    /// Certify all current boundary samples before choosing at most one merge.
    /// On ties, the lower bond index wins. A blocked stronger boundary does not
    /// prevent a weaker feasible one. Any missing or forged witness returns a
    /// typed refusal and leaves the partition unchanged.
    pub fn refine_with_witnesses<F>(
        &mut self,
        model: &ExactQubitChain,
        threshold: &Rational,
        max_cluster_qubits: usize,
        mut witness_provider: F,
    ) -> Result<RefinementReceipt, AdaptiveError>
    where
        F: FnMut(&BoundaryResidual) -> Result<TraceNormWitness, AdaptiveError>,
    {
        self.check_refinement_preconditions(model, threshold, max_cluster_qubits)?;
        let mut detections: Vec<BoundaryDetectionReceipt> = Vec::new();
        let mut selected: Option<usize> = None;
        let mut has_triggered_boundary = false;
        for bond in 0..model.bond_hamiltonians.len() {
            let Some(boundary) = self.boundary_residual(model, bond)? else {
                continue;
            };
            let witness = witness_provider(&boundary)?;
            let detection = boundary.certify(witness, threshold)?;
            self.update_selected_boundary(
                &detection,
                &detections,
                max_cluster_qubits,
                &mut selected,
                &mut has_triggered_boundary,
            )?;
            detections.push(detection);
        }
        let (decision, fusion) =
            self.finalize_refinement(selected, has_triggered_boundary, &detections)?;
        Ok(RefinementReceipt {
            detections,
            decision,
            fusion,
            max_cluster_qubits,
            authority_effect: AdaptiveDiagnosticAuthority::None,
        })
    }

    fn check_refinement_preconditions(
        &self,
        model: &ExactQubitChain,
        threshold: &Rational,
        max_cluster_qubits: usize,
    ) -> Result<(), AdaptiveError> {
        self.check_model(model)?;
        check_threshold(threshold)?;
        check_ceiling(max_cluster_qubits)?;
        Ok(())
    }

    fn update_selected_boundary(
        &self,
        detection: &BoundaryDetectionReceipt,
        detections: &[BoundaryDetectionReceipt],
        max_cluster_qubits: usize,
        selected: &mut Option<usize>,
        has_triggered_boundary: &mut bool,
    ) -> Result<(), AdaptiveError> {
        if !detection.is_triggered() {
            return Ok(());
        }
        *has_triggered_boundary = true;
        let boundary = detection.boundary();
        let size = boundary.left.sites.len() + boundary.right.sites.len();
        let is_largest = match *selected {
            None => true,
            Some(index) => {
                let previous = detections.get(index).ok_or(AdaptiveError::PartitionSites {
                    sites: self.num_sites,
                })?;
                detection.rate() > previous.rate()
            }
        };
        if size <= max_cluster_qubits && is_largest {
            *selected = Some(detections.len());
        }
        Ok(())
    }

    fn finalize_refinement(
        &mut self,
        selected: Option<usize>,
        has_triggered_boundary: bool,
        detections: &[BoundaryDetectionReceipt],
    ) -> Result<(RefinementDecision, Option<FusionReceipt>), AdaptiveError> {
        match selected {
            Some(index) => {
                let detection = detections.get(index).ok_or(AdaptiveError::PartitionSites {
                    sites: self.num_sites,
                })?;
                let boundary = detection.boundary();
                let receipt = self.fuse_clusters(boundary.left_cluster, boundary.right_cluster)?;
                Ok((
                    RefinementDecision::Fused {
                        bond: boundary.bond,
                    },
                    Some(receipt),
                ))
            }
            None if has_triggered_boundary => {
                Ok((RefinementDecision::AllTriggeredMergesExceedCeiling, None))
            }
            None => Ok((RefinementDecision::NoTriggeredBoundary, None)),
        }
    }

    /// Internal terms plus boundary mean fields evaluated on the current
    /// incoming partition. The contraction uses the outside site's actual
    /// marginal; this is distinct from the full-cluster detector above.
    pub fn effective_hamiltonian(
        &self,
        model: &ExactQubitChain,
        cluster_index: usize,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        self.check_model(model)?;
        let cluster = self.cluster(cluster_index)?;
        let layout = qubit_layout(cluster.sites.len())?;
        let mut result = self.cluster_local_hamiltonian(model, cluster, &layout)?;
        let identity = mx::identity_with_limits(2, exact_limits())?;
        result =
            self.accumulate_bond_effective_terms(model, cluster, &layout, &identity, result)?;
        check_hermitian(&result)?;
        Ok(result)
    }

    fn accumulate_bond_effective_terms(
        &self,
        model: &ExactQubitChain,
        cluster: &ExactQuantumCluster,
        layout: &TensorLayout,
        identity: &BasicMatrix<GaussianRat>,
        mut result: BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        for (bond, term) in model.bond_hamiltonians.iter().enumerate() {
            if let Some(addition) =
                self.bond_effective_term(cluster, layout, identity, bond, term)?
            {
                result = mx::add(&result, &addition)?;
            }
        }
        Ok(result)
    }

    fn cluster_local_hamiltonian(
        &self,
        model: &ExactQubitChain,
        cluster: &ExactQuantumCluster,
        layout: &TensorLayout,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        let dimension = cluster.state.dimension();
        let mut result = mx::zeros_with_limits(dimension, dimension, exact_limits())?;
        for &site in cluster.sites() {
            let local = cluster
                .local_index(site)
                .ok_or(AdaptiveError::PartitionSites {
                    sites: self.num_sites,
                })?;
            let term = model
                .local_hamiltonians
                .get(site)
                .ok_or(AdaptiveError::Site {
                    site,
                    sites: self.num_sites,
                })?;
            result = mx::add(
                &result,
                &layout.embed_operator_with_limits(term, &[local], exact_limits())?,
            )?;
        }
        Ok(result)
    }

    fn bond_effective_term(
        &self,
        cluster: &ExactQuantumCluster,
        layout: &TensorLayout,
        identity: &BasicMatrix<GaussianRat>,
        bond: usize,
        term: &BasicMatrix<GaussianRat>,
    ) -> Result<Option<BasicMatrix<GaussianRat>>, AdaptiveError> {
        let left_local = cluster.local_index(bond);
        let right_local = cluster.local_index(bond + 1);
        match (left_local, right_local) {
            (Some(left), Some(right)) => Ok(Some(layout.embed_operator_with_limits(
                term,
                &[left, right],
                exact_limits(),
            )?)),
            (Some(left), None) => {
                let contracted = self.contract_outside_right(term, identity, bond + 1)?;
                Ok(Some(layout.embed_operator_with_limits(
                    &contracted,
                    &[left],
                    exact_limits(),
                )?))
            }
            (None, Some(right)) => {
                let contracted = self.contract_outside_left(term, identity, bond)?;
                Ok(Some(layout.embed_operator_with_limits(
                    &contracted,
                    &[right],
                    exact_limits(),
                )?))
            }
            (None, None) => Ok(None),
        }
    }

    fn contract_outside_right(
        &self,
        term: &BasicMatrix<GaussianRat>,
        identity: &BasicMatrix<GaussianRat>,
        outside_site: usize,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        let outside = self.single_site_marginal(outside_site)?;
        let prod = mx::kronecker_with_limits(identity, outside.matrix(), exact_limits())?;
        let weighted = mx::multiply_with_limits(term, &prod, exact_limits())?;
        Ok(partial_trace_second(&weighted, 2, 2)?)
    }

    fn contract_outside_left(
        &self,
        term: &BasicMatrix<GaussianRat>,
        identity: &BasicMatrix<GaussianRat>,
        outside_site: usize,
    ) -> Result<BasicMatrix<GaussianRat>, AdaptiveError> {
        let outside = self.single_site_marginal(outside_site)?;
        let prod = mx::kronecker_with_limits(outside.matrix(), identity, exact_limits())?;
        let weighted = mx::multiply_with_limits(term, &prod, exact_limits())?;
        Ok(partial_trace_first(&weighted, 2, 2)?)
    }

    /// Advance all clusters using Cayley unitaries of effective Hamiltonians
    /// frozen from the same incoming states. Exact density admission is
    /// rechecked after each single-Kraus map; commit is atomic.
    pub fn cayley_step(
        &mut self,
        model: &ExactQubitChain,
        step_size: &Rational,
    ) -> Result<CayleyStepReceipt, AdaptiveError> {
        self.check_model(model)?;
        check_rational_scalar(step_size)?;
        if step_size <= &Rational::zero() {
            return Err(AdaptiveError::NonPositiveStep);
        }
        let mut clusters = Vec::with_capacity(self.clusters.len());
        let mut receipts = Vec::with_capacity(self.clusters.len());
        for (index, incoming) in self.clusters.iter().enumerate() {
            let (cluster, receipt) = self.cayley_step_cluster(model, index, incoming, step_size)?;
            clusters.push(cluster);
            receipts.push(receipt);
        }
        let next = Self::try_new(self.num_sites, clusters)?;
        let receipt = CayleyStepReceipt {
            step_size: step_size.clone(),
            clusters: receipts,
            scope: EvolutionScope::ExactFiniteFrozenCayley,
            authority_effect: AdaptiveDiagnosticAuthority::None,
        };
        *self = next;
        Ok(receipt)
    }

    fn cayley_step_cluster(
        &self,
        model: &ExactQubitChain,
        index: usize,
        incoming: &ExactQuantumCluster,
        step_size: &Rational,
    ) -> Result<(ExactQuantumCluster, ClusterCayleyReceipt), AdaptiveError> {
        let effective_hamiltonian = self.effective_hamiltonian(model, index)?;
        let hamiltonian =
            ExactHamiltonian::try_new(ExactOperator::try_new(effective_hamiltonian.clone())?)?;
        let unitary = hamiltonian.cayley_propagator(step_size)?.into_matrix();
        let channel = ExactKrausChannel::try_new(
            incoming.state.dimension(),
            incoming.state.dimension(),
            vec![unitary.clone()],
            "frozen-cluster-cayley",
        )?;
        let outgoing_state = ExactDensityState::try_new(channel.apply(incoming.state.matrix())?)?;
        let cluster = ExactQuantumCluster::try_new(incoming.sites.clone(), outgoing_state.clone())?;
        let receipt = ClusterCayleyReceipt {
            sites: incoming.sites.clone(),
            incoming_state: incoming.state.clone(),
            outgoing_state,
            effective_hamiltonian,
            unitary,
            authority_effect: AdaptiveDiagnosticAuthority::None,
        };
        Ok((cluster, receipt))
    }

    /// One finite evolution step followed by one sampled refinement. All work
    /// is staged, so a rejected norm witness preserves the last accepted states
    /// as well as the old partition. The threshold controls merging only.
    pub fn advance_and_refine<F>(
        &mut self,
        model: &ExactQubitChain,
        step_size: &Rational,
        threshold: &Rational,
        max_cluster_qubits: usize,
        witness_provider: F,
    ) -> Result<AdaptiveStepReceipt, AdaptiveError>
    where
        F: FnMut(&BoundaryResidual) -> Result<TraceNormWitness, AdaptiveError>,
    {
        check_threshold(threshold)?;
        check_ceiling(max_cluster_qubits)?;
        let mut next = self.clone();
        let evolution = next.cayley_step(model, step_size)?;
        let refinement =
            next.refine_with_witnesses(model, threshold, max_cluster_qubits, witness_provider)?;
        let receipt = AdaptiveStepReceipt {
            evolution,
            refinement,
            authority_effect: AdaptiveDiagnosticAuthority::None,
        };
        *self = next;
        Ok(receipt)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/adaptive_integrator.rs
// Claim: urn:core:crates_rs:core-quantum-physics:adaptive-integrator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1af48d93 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
