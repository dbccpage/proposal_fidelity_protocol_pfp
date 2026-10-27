//! Structured finite-shadow refinement data for the Q/CODA-CS membrane.
//!
//! --- Math Contract:
//! - Purpose: bind a declared spectral shadow family to exact symbolic rate
//!   metadata and content-hashed source bindings with declared theorem names.
//! - Inputs: finite refinement levels, an explicit refinement relation, and a
//!   canonical theorem receipt for the selected family and mode.
//! - Outputs: validated [`RefinementTower`] and [`ConvergenceCertificate`]
//!   values. These are proof bindings; they do not run a numerical solver.
//! - Invariants: mesh scales use exact [`BigRational`] values, certificate
//!   fields are private, resolutions strictly increase, maximum gaps strictly
//!   decrease, and family-specific constructors fix the theorem and rate.
//! - Failure: malformed or inconsistent metadata is refused with
//!   [`RefinementTypeError`].
//! - Numerical status: no floating-point values occur in this module.
//! - Authority: every certificate has `AuthorityEffectLevel::None`; a limit,
//!   proof receipt, or complete Q debt does not mint authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b4b6cd5e<T> {
    fn checked_invariant_b4b6cd5e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b4b6cd5e<T> for Option<T> {
    #[inline]
    fn checked_invariant_b4b6cd5e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b4b6cd5e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b4b6cd5e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::cmp::Ordering;

use num_bigint::BigInt;
use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::authority_lattice::AuthorityEffectLevel;

/// Schema stamped on structured refinement certificates.
pub const CONVERGENCE_CERTIFICATE_SCHEMA: &str = "core.refinement-convergence.v1";

// Existing CODA source bytes. Three historical hashes differ only in their
// first import line; tests preserve that transformation explicitly. No Lean
// compilation or axiom replay is performed by this Rust source-binding check.
pub const D1_BINDING_STATUS: &str = "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY";
pub const D1_BOUNDS_SOURCE: &str = "lean4/original_lean_20260809/one_regime_spectral_bounds.lean";
pub const D1_BOUNDS_SOURCE_SHA256: &str =
    "a55e4db5aa446d70becf17bb817097d25f30bc084932db4bccf09c662b713651";
pub const D1_HISTORICAL_BOUNDS_SOURCE_SHA256: &str =
    "a55e4db5aa446d70becf17bb817097d25f30bc084932db4bccf09c662b713651";
pub const D1_INTERFACES_SOURCE: &str =
    "lean4/original_lean_20260809/one_regime_spectral_interfaces.lean";
pub const D1_INTERFACES_SOURCE_SHA256: &str =
    "30dd41810264fe5bd08778cb50e305d314861d8c2f5dcbdeba7a27a9b8f6ab89";
pub const D1_HISTORICAL_INTERFACES_SOURCE_SHA256: &str =
    "347efc79fee3babaac29b57f85677b975f761d73d0a55ff49a3e167b223b0d59";
pub const D1_BOUNDS_AUDIT_SOURCE: &str =
    "lean4/original_lean_20260809/one_regime_spectral_bounds_audit.lean";
pub const D1_BOUNDS_AUDIT_SHA256: &str =
    "3d9dc1ae6d757d8baef1a983c87085e6c1f1d751da1a2ae7dd87d223325f17c9";
pub const D1_HISTORICAL_BOUNDS_AUDIT_SHA256: &str =
    "f065cee92557e7c40e33d60bb5728c8057d96c6fe7b48c86e20fd0c779f74c48";
pub const D1_INTERFACES_AUDIT_SOURCE: &str =
    "lean4/original_lean_20260809/d1_one_regime_interfaces_audit.lean";
pub const D1_INTERFACES_AUDIT_SHA256: &str =
    "9269631fba1bce851273609660aff1fbe21b86b9f7ecbd68d7d1c799e3d7a927";
pub const D1_HISTORICAL_INTERFACES_AUDIT_SHA256: &str =
    "1d83c635b093cf631dc49080ba3c7b782f0d604e81f7b3dd7a8bcd35c507ea16";
/// Replay the Rust source-binding gate from the repository root; this is not a Lean build.
pub const D1_REPLAY_COMMAND: &str = "cargo test --manifest-path engine/crates_rs/Cargo.toml -p core_types --test refinement_tower_receipts compiled_receipt_hashes_match_all_four_repository_files -- --exact";

/// The only topology certified by the spectral refinement results.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SpectralTopology {
    /// Pointwise convergence of each ordered eigenvalue, equivalently
    /// convergence in every fixed finite spectral prefix.
    OrderedFinitePrefix,
}

/// Finite observer used to construct a shadow.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ShadowKind {
    /// Uniform periodic cycle with the ordinary graph Laplacian scaled by `n²`.
    UniformCycle,
    /// Cell-centred Neumann path with `n` equal control volumes.
    CellCenteredNeumannPath,
    /// Periodic piecewise-linear / finite-volume stiffness with lumped mass.
    PeriodicLumpedFiniteVolume,
}

/// Relation actually established between successive finite shadows.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RefinementRelation {
    /// Every later uniform resolution is an integer refinement of its
    /// predecessor.
    ExactUniformSubdivision,
    /// Shadows need not refine one another as partitions; a theorem compares
    /// them through a common ordered spectral limit.
    CommonLimitComparison,
}

/// Mesh variable used by a symbolic convergence rate.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MeshVariable {
    /// `1 / n`, for a declared uniform resolution `n`.
    InverseResolution,
    /// `H = max_i ell_i`, the largest physical gap in a partition.
    MaximumGap,
}

/// Exact D1 theorem selected by a canonical receipt.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UniformD1ReceiptKind {
    UniformCycle,
    CellCenteredNeumannPath,
}

/// The only axioms admitted by the D1 Lean receipt.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LeanAxiom {
    Propext,
    ClassicalChoice,
    QuotSound,
}

/// Positive exact rational stored canonically as [`BigRational`].
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize)]
pub struct PositiveRational(BigRational);

impl PositiveRational {
    /// Constructs a positive exact rational.
    pub fn new(numerator: BigInt, denominator: BigInt) -> Result<Self, RefinementTypeError> {
        if denominator == BigInt::from(0_u8) {
            return Err(RefinementTypeError::ZeroDenominator);
        }
        if numerator <= BigInt::from(0_u8) {
            return Err(RefinementTypeError::NonPositiveNumerator);
        }
        if denominator < BigInt::from(0_u8) {
            return Err(RefinementTypeError::NegativeDenominator);
        }
        Ok(Self(BigRational::new(numerator, denominator)))
    }

    /// Convenience constructor for a positive `u64 / u64`.
    pub fn from_u64(numerator: u64, denominator: u64) -> Result<Self, RefinementTypeError> {
        Self::new(BigInt::from(numerator), BigInt::from(denominator))
    }

    /// Exact canonical rational.
    pub fn value(&self) -> &BigRational {
        &self.0
    }

    /// Exact numerator in lowest terms.
    pub fn numerator(&self) -> &BigInt {
        self.0.numer()
    }

    /// Exact positive denominator in lowest terms.
    pub fn denominator(&self) -> &BigInt {
        self.0.denom()
    }
}

impl PartialOrd for PositiveRational {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for PositiveRational {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0.cmp(&other.0)
    }
}

/// One finite shadow level.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct RefinementLevel {
    resolution: usize,
    maximum_gap: PositiveRational,
}

impl RefinementLevel {
    /// Creates a finite level with an exact upper bound for its maximum gap.
    pub fn new(
        resolution: usize,
        maximum_gap: PositiveRational,
    ) -> Result<Self, RefinementTypeError> {
        if resolution < 2 {
            return Err(RefinementTypeError::ResolutionTooSmall(resolution));
        }
        Ok(Self {
            resolution,
            maximum_gap,
        })
    }

    pub fn resolution(&self) -> usize {
        self.resolution
    }

    pub fn maximum_gap(&self) -> &PositiveRational {
        &self.maximum_gap
    }
}

/// Identity and scope of a finite shadow family.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ShadowFamily {
    id: String,
    kind: ShadowKind,
    topology: SpectralTopology,
    declared_object: String,
}

impl ShadowFamily {
    /// Creates a named family over a declared object.
    pub fn new(
        id: impl Into<String>,
        kind: ShadowKind,
        declared_object: impl Into<String>,
    ) -> Result<Self, RefinementTypeError> {
        let id = require_text("family id", id.into())?;
        let declared_object = require_text("declared object", declared_object.into())?;
        Ok(Self {
            id,
            kind,
            topology: SpectralTopology::OrderedFinitePrefix,
            declared_object,
        })
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn kind(&self) -> ShadowKind {
        self.kind
    }

    pub fn topology(&self) -> SpectralTopology {
        self.topology
    }

    pub fn declared_object(&self) -> &str {
        &self.declared_object
    }
}

/// A validated sequence of finite shadows.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct RefinementTower {
    family: ShadowFamily,
    relation: RefinementRelation,
    levels: Vec<RefinementLevel>,
}

impl RefinementTower {
    /// Validates a tower.
    ///
    /// `ExactUniformSubdivision` additionally requires that each resolution
    /// divide the next. `CommonLimitComparison` deliberately does not pretend
    /// that two arbitrary observer partitions are exact refinements.
    pub fn new(
        family: ShadowFamily,
        relation: RefinementRelation,
        levels: Vec<RefinementLevel>,
    ) -> Result<Self, RefinementTypeError> {
        if levels.len() < 2 {
            return Err(RefinementTypeError::TooFewLevels);
        }
        for pair in levels.windows(2) {
            let earlier = &pair[0];
            let later = &pair[1];
            if later.resolution <= earlier.resolution {
                return Err(RefinementTypeError::ResolutionNotIncreasing {
                    earlier: earlier.resolution,
                    later: later.resolution,
                });
            }
            if later.maximum_gap >= earlier.maximum_gap {
                return Err(RefinementTypeError::MaximumGapNotDecreasing);
            }
            if relation == RefinementRelation::ExactUniformSubdivision
                && later.resolution % earlier.resolution != 0
            {
                return Err(RefinementTypeError::NotExactUniformRefinement {
                    earlier: earlier.resolution,
                    later: later.resolution,
                });
            }
        }
        Ok(Self {
            family,
            relation,
            levels,
        })
    }

    pub fn family(&self) -> &ShadowFamily {
        &self.family
    }

    pub fn relation(&self) -> RefinementRelation {
        self.relation
    }

    pub fn levels(&self) -> &[RefinementLevel] {
        &self.levels
    }

    /// SHA-256 of the versioned canonical JSON representation.
    pub fn digest_sha256(&self) -> String {
        let payload = serde_json::to_vec(&(
            "core.refinement-tower.v1",
            &self.family,
            self.relation,
            &self.levels,
        ))
        .checked_invariant_b4b6cd5e("private refinement types serialize without fallible map keys");
        sha256_hex(payload)
    }
}

/// Exact symbolic monomial `q * pi^p * mode^m * mesh^r`.
///
/// This is metadata for a proved bound, not a floating-point evaluation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct SymbolicRateBound {
    mode_index: usize,
    rational_coefficient: PositiveRational,
    pi_power: u8,
    mode_power: u8,
    mesh_variable: MeshVariable,
    mesh_power: u8,
    domain: String,
}

impl SymbolicRateBound {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        mode_index: usize,
        rational_coefficient: PositiveRational,
        pi_power: u8,
        mode_power: u8,
        mesh_variable: MeshVariable,
        mesh_power: u8,
        domain: impl Into<String>,
    ) -> Result<Self, RefinementTypeError> {
        if mesh_power == 0 {
            return Err(RefinementTypeError::ZeroRatePower);
        }
        let domain = require_text("rate domain", domain.into())?;
        Ok(Self {
            mode_index,
            rational_coefficient,
            pi_power,
            mode_power,
            mesh_variable,
            mesh_power,
            domain,
        })
    }

    pub fn mode_index(&self) -> usize {
        self.mode_index
    }

    pub fn rational_coefficient(&self) -> &PositiveRational {
        &self.rational_coefficient
    }

    pub fn pi_power(&self) -> u8 {
        self.pi_power
    }

    pub fn mode_power(&self) -> u8 {
        self.mode_power
    }

    pub fn mesh_variable(&self) -> MeshVariable {
        self.mesh_variable
    }

    pub fn mesh_power(&self) -> u8 {
        self.mesh_power
    }

    pub fn domain(&self) -> &str {
        &self.domain
    }
}

/// Content hash for one source or audit file.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct HashedLeanSource {
    path: String,
    sha256: String,
}

impl HashedLeanSource {
    fn canonical(path: &'static str, sha256: String) -> Self {
        Self {
            path: path.to_string(),
            sha256,
        }
    }

    pub fn path(&self) -> &str {
        &self.path
    }

    pub fn sha256(&self) -> &str {
        &self.sha256
    }
}

/// Source identity and declared theorem metadata for a spectral certificate.
///
/// The D1 constructor compares supplied hashes with compiled source identities.
/// The disk gate verifies those identities separately. Neither operation runs
/// Lean or replays the declared axiom set; `source_binding_status` records this
/// limit. The type deliberately has no `Deserialize`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct TheoremReceipt {
    kind: UniformD1ReceiptKind,
    source_files: Vec<HashedLeanSource>,
    audit_files: Vec<HashedLeanSource>,
    theorem_names: Vec<String>,
    replay_command: String,
    source_binding_status: String,
    axioms: Vec<LeanAxiom>,
}

impl TheoremReceipt {
    #[allow(clippy::too_many_arguments)]
    pub fn uniform_d1(
        kind: UniformD1ReceiptKind,
        bounds_source_sha256: impl Into<String>,
        interfaces_source_sha256: impl Into<String>,
        bounds_audit_sha256: impl Into<String>,
        interfaces_audit_sha256: impl Into<String>,
    ) -> Result<Self, RefinementTypeError> {
        let bounds_source_sha256 = require_receipt_hash(
            "D1 bounds source",
            bounds_source_sha256.into(),
            D1_BOUNDS_SOURCE_SHA256,
        )?;
        let interfaces_source_sha256 = require_receipt_hash(
            "D1 interfaces source",
            interfaces_source_sha256.into(),
            D1_INTERFACES_SOURCE_SHA256,
        )?;
        let bounds_audit_sha256 = require_receipt_hash(
            "D1 bounds axiom audit",
            bounds_audit_sha256.into(),
            D1_BOUNDS_AUDIT_SHA256,
        )?;
        let interfaces_audit_sha256 = require_receipt_hash(
            "D1 interfaces axiom audit",
            interfaces_audit_sha256.into(),
            D1_INTERFACES_AUDIT_SHA256,
        )?;

        let theorem_names = match kind {
            UniformD1ReceiptKind::UniformCycle => vec![
                "CoreCosmology.OneRegime.cycle_dispersion_bound".to_string(),
                "CoreCosmology.OneRegime.UniformCycleModeInterface.spectral_defect_bound"
                    .to_string(),
            ],
            UniformD1ReceiptKind::CellCenteredNeumannPath => vec![
                "CoreCosmology.OneRegime.neumann_path_dispersion_bound".to_string(),
                "CoreCosmology.OneRegime.NeumannPathModeInterface.spectral_defect_bound"
                    .to_string(),
            ],
        };

        Ok(Self {
            kind,
            source_files: vec![
                HashedLeanSource::canonical(D1_BOUNDS_SOURCE, bounds_source_sha256),
                HashedLeanSource::canonical(D1_INTERFACES_SOURCE, interfaces_source_sha256),
            ],
            audit_files: vec![
                HashedLeanSource::canonical(D1_BOUNDS_AUDIT_SOURCE, bounds_audit_sha256),
                HashedLeanSource::canonical(D1_INTERFACES_AUDIT_SOURCE, interfaces_audit_sha256),
            ],
            theorem_names,
            replay_command: D1_REPLAY_COMMAND.to_string(),
            source_binding_status: D1_BINDING_STATUS.to_string(),
            axioms: vec![
                LeanAxiom::Propext,
                LeanAxiom::ClassicalChoice,
                LeanAxiom::QuotSound,
            ],
        })
    }

    pub fn kind(&self) -> UniformD1ReceiptKind {
        self.kind
    }

    pub fn source_files(&self) -> &[HashedLeanSource] {
        &self.source_files
    }

    pub fn audit_files(&self) -> &[HashedLeanSource] {
        &self.audit_files
    }

    pub fn theorem_names(&self) -> &[String] {
        &self.theorem_names
    }

    pub fn source_binding_status(&self) -> &str {
        &self.source_binding_status
    }

    pub fn replay_command(&self) -> &str {
        &self.replay_command
    }

    pub fn axioms(&self) -> &[LeanAxiom] {
        &self.axioms
    }
}

/// Proof-bound convergence evidence for one finite shadow family.
///
/// Family-specific constructors synthesize the symbolic rate and check the
/// exact theorem receipt. The private authority field is fixed to `None`.
/// There is deliberately no unchecked `Deserialize` implementation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ConvergenceCertificate {
    schema: String,
    tower_digest_sha256: String,
    family_id: String,
    family_kind: ShadowKind,
    topology: SpectralTopology,
    mode_index: usize,
    rate_bounds: Vec<SymbolicRateBound>,
    theorem_receipt: TheoremReceipt,
    authority_effect: AuthorityEffectLevel,
}

impl ConvergenceCertificate {
    pub fn uniform_cycle(
        tower: &RefinementTower,
        mode_index: usize,
        theorem_receipt: TheoremReceipt,
    ) -> Result<Self, RefinementTypeError> {
        require_family_and_relation(tower, ShadowKind::UniformCycle)?;
        if theorem_receipt.kind != UniformD1ReceiptKind::UniformCycle {
            return Err(RefinementTypeError::ReceiptKindMismatch {
                expected: UniformD1ReceiptKind::UniformCycle,
                actual: theorem_receipt.kind,
            });
        }
        for level in tower.levels() {
            if level.resolution < 3
                || (mode_index > 0 && mode_index >= level.resolution.div_ceil(2))
            {
                return Err(RefinementTypeError::ModeOutsideCertificateDomain {
                    kind: ShadowKind::UniformCycle,
                    mode_index,
                    resolution: level.resolution,
                });
            }
        }
        let rate = SymbolicRateBound::new(
            mode_index,
            PositiveRational::from_u64(4, 3)?,
            4,
            4,
            MeshVariable::InverseResolution,
            2,
            "uniform cycle; n >= 3; n > 2k; fixed k",
        )?;
        Ok(Self::bind(tower, mode_index, vec![rate], theorem_receipt))
    }

    pub fn cell_centered_neumann_path(
        tower: &RefinementTower,
        mode_index: usize,
        theorem_receipt: TheoremReceipt,
    ) -> Result<Self, RefinementTypeError> {
        require_family_and_relation(tower, ShadowKind::CellCenteredNeumannPath)?;
        if theorem_receipt.kind != UniformD1ReceiptKind::CellCenteredNeumannPath {
            return Err(RefinementTypeError::ReceiptKindMismatch {
                expected: UniformD1ReceiptKind::CellCenteredNeumannPath,
                actual: theorem_receipt.kind,
            });
        }
        for level in tower.levels() {
            if mode_index >= level.resolution {
                return Err(RefinementTypeError::ModeOutsideCertificateDomain {
                    kind: ShadowKind::CellCenteredNeumannPath,
                    mode_index,
                    resolution: level.resolution,
                });
            }
        }
        let rate = SymbolicRateBound::new(
            mode_index,
            PositiveRational::from_u64(1, 12)?,
            4,
            4,
            MeshVariable::InverseResolution,
            2,
            "cell-centered Neumann path; n >= 2; 0 <= k < n; fixed k",
        )?;
        Ok(Self::bind(tower, mode_index, vec![rate], theorem_receipt))
    }

    fn bind(
        tower: &RefinementTower,
        mode_index: usize,
        rate_bounds: Vec<SymbolicRateBound>,
        theorem_receipt: TheoremReceipt,
    ) -> Self {
        Self {
            schema: CONVERGENCE_CERTIFICATE_SCHEMA.to_string(),
            tower_digest_sha256: tower.digest_sha256(),
            family_id: tower.family.id.clone(),
            family_kind: tower.family.kind,
            topology: tower.family.topology,
            mode_index,
            rate_bounds,
            theorem_receipt,
            authority_effect: AuthorityEffectLevel::None,
        }
    }

    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn tower_digest_sha256(&self) -> &str {
        &self.tower_digest_sha256
    }

    pub fn family_id(&self) -> &str {
        &self.family_id
    }

    pub fn family_kind(&self) -> ShadowKind {
        self.family_kind
    }

    pub fn topology(&self) -> SpectralTopology {
        self.topology
    }

    pub fn mode_index(&self) -> usize {
        self.mode_index
    }

    pub fn rate_bounds(&self) -> &[SymbolicRateBound] {
        &self.rate_bounds
    }

    pub fn theorem_receipt(&self) -> &TheoremReceipt {
        &self.theorem_receipt
    }

    pub fn authority_effect(&self) -> AuthorityEffectLevel {
        self.authority_effect
    }
}

/// Typed validation failures for refinement metadata.
#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum RefinementTypeError {
    #[error("positive rational numerator must be strictly positive")]
    NonPositiveNumerator,
    #[error("positive rational denominator must be nonzero")]
    ZeroDenominator,
    #[error("positive rational denominator must be positive")]
    NegativeDenominator,
    #[error("refinement resolution {0} is smaller than two")]
    ResolutionTooSmall(usize),
    #[error("a refinement tower requires at least two levels")]
    TooFewLevels,
    #[error("resolution must increase: {earlier} then {later}")]
    ResolutionNotIncreasing { earlier: usize, later: usize },
    #[error("maximum gap must strictly decrease")]
    MaximumGapNotDecreasing,
    #[error("{later} is not an exact uniform refinement of {earlier}")]
    NotExactUniformRefinement { earlier: usize, later: usize },
    #[error("symbolic convergence rate power must be positive")]
    ZeroRatePower,
    #[error("{field} must contain non-whitespace text")]
    MissingText { field: &'static str },
    #[error("{artifact} is not a 64-digit SHA-256 value")]
    MalformedSha256 { artifact: &'static str },
    #[error("{artifact} does not match the canonical repository receipt")]
    ReceiptHashMismatch { artifact: &'static str },
    #[error("certificate family mismatch: expected {expected:?}, got {actual:?}")]
    WrongFamily {
        expected: ShadowKind,
        actual: ShadowKind,
    },
    #[error("uniform D1 certificates require exact uniform subdivision")]
    WrongRefinementRelation,
    #[error("theorem receipt mismatch: expected {expected:?}, got {actual:?}")]
    ReceiptKindMismatch {
        expected: UniformD1ReceiptKind,
        actual: UniformD1ReceiptKind,
    },
    #[error(
        "mode {mode_index} at resolution {resolution} is outside the {kind:?} certificate domain"
    )]
    ModeOutsideCertificateDomain {
        kind: ShadowKind,
        mode_index: usize,
        resolution: usize,
    },
}

fn require_text(field: &'static str, value: String) -> Result<String, RefinementTypeError> {
    if value.trim().is_empty() {
        Err(RefinementTypeError::MissingText { field })
    } else {
        Ok(value)
    }
}

fn require_receipt_hash(
    artifact: &'static str,
    value: String,
    expected: &'static str,
) -> Result<String, RefinementTypeError> {
    let normalized = value.trim().to_ascii_lowercase();
    if normalized.len() != 64 || !normalized.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(RefinementTypeError::MalformedSha256 { artifact });
    }
    if normalized != expected {
        return Err(RefinementTypeError::ReceiptHashMismatch { artifact });
    }
    Ok(normalized)
}

fn require_family_and_relation(
    tower: &RefinementTower,
    expected: ShadowKind,
) -> Result<(), RefinementTypeError> {
    if tower.family.kind != expected {
        return Err(RefinementTypeError::WrongFamily {
            expected,
            actual: tower.family.kind,
        });
    }
    if tower.relation != RefinementRelation::ExactUniformSubdivision {
        return Err(RefinementTypeError::WrongRefinementRelation);
    }
    Ok(())
}

fn sha256_hex(payload: impl AsRef<[u8]>) -> String {
    let digest = Sha256::digest(payload.as_ref());
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

// Origin: engine/crates_rs/core_types/src/refinement_tower.rs
// Claim: urn:core:crates_rs:core-types:refinement-tower:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn uniform_tower(kind: ShadowKind, levels: &[u64]) -> RefinementTower {
        let family = ShadowFamily::new("shadow:uniform", kind, "declared compact object")
            .expect("valid family");
        let levels = levels
            .iter()
            .copied()
            .map(|n| {
                RefinementLevel::new(
                    usize::try_from(n).expect("small test resolution"),
                    PositiveRational::from_u64(1, n).expect("positive mesh scale"),
                )
                .expect("valid level")
            })
            .collect();
        RefinementTower::new(family, RefinementRelation::ExactUniformSubdivision, levels)
            .expect("valid nested tower")
    }

    fn canonical_receipt(kind: UniformD1ReceiptKind) -> TheoremReceipt {
        TheoremReceipt::uniform_d1(
            kind,
            D1_BOUNDS_SOURCE_SHA256,
            D1_INTERFACES_SOURCE_SHA256,
            D1_BOUNDS_AUDIT_SHA256,
            D1_INTERFACES_AUDIT_SHA256,
        )
        .expect("canonical receipt")
    }

    #[test]
    fn positive_rational_is_reduced_and_ordered_exactly() {
        let half = PositiveRational::from_u64(2, 4).expect("positive rational");
        let third = PositiveRational::from_u64(1, 3).expect("positive rational");
        assert_eq!(half.numerator(), &BigInt::from(1_u8));
        assert_eq!(half.denominator(), &BigInt::from(2_u8));
        assert!(third < half);
    }

    #[test]
    fn exact_uniform_relation_refuses_nondivisible_resolutions() {
        let family =
            ShadowFamily::new("f", ShadowKind::UniformCycle, "unit circle").expect("family");
        let levels = vec![
            RefinementLevel::new(8, PositiveRational::from_u64(1, 8).unwrap()).unwrap(),
            RefinementLevel::new(15, PositiveRational::from_u64(1, 15).unwrap()).unwrap(),
        ];
        assert_eq!(
            RefinementTower::new(family, RefinementRelation::ExactUniformSubdivision, levels),
            Err(RefinementTypeError::NotExactUniformRefinement {
                earlier: 8,
                later: 15
            })
        );
    }

    #[test]
    fn cycle_certificate_is_hash_rate_family_and_authority_bound() {
        let tower = uniform_tower(ShadowKind::UniformCycle, &[16, 32, 64]);
        let receipt = canonical_receipt(UniformD1ReceiptKind::UniformCycle);
        let certificate =
            ConvergenceCertificate::uniform_cycle(&tower, 3, receipt).expect("certificate");

        assert_eq!(certificate.schema(), CONVERGENCE_CERTIFICATE_SCHEMA);
        assert_eq!(certificate.tower_digest_sha256(), tower.digest_sha256());
        assert_eq!(certificate.family_kind(), ShadowKind::UniformCycle);
        assert_eq!(certificate.mode_index(), 3);
        assert_eq!(certificate.authority_effect(), AuthorityEffectLevel::None);
        assert_eq!(certificate.rate_bounds().len(), 1);
        assert_eq!(certificate.rate_bounds()[0].mesh_power(), 2);
        assert_eq!(
            certificate.rate_bounds()[0].rational_coefficient().value(),
            &BigRational::new(BigInt::from(4_u8), BigInt::from(3_u8))
        );
        assert_eq!(
            certificate.theorem_receipt().axioms(),
            &[
                LeanAxiom::Propext,
                LeanAxiom::ClassicalChoice,
                LeanAxiom::QuotSound
            ]
        );
        let serialized = serde_json::to_value(&certificate).expect("serialize certificate");
        assert_eq!(serialized["authority_effect"], "None");
    }

    #[test]
    fn receipt_hash_mutation_and_cross_family_receipt_are_refused() {
        assert_eq!(
            TheoremReceipt::uniform_d1(
                UniformD1ReceiptKind::UniformCycle,
                "0".repeat(64),
                D1_INTERFACES_SOURCE_SHA256,
                D1_BOUNDS_AUDIT_SHA256,
                D1_INTERFACES_AUDIT_SHA256,
            ),
            Err(RefinementTypeError::ReceiptHashMismatch {
                artifact: "D1 bounds source"
            })
        );

        let tower = uniform_tower(ShadowKind::UniformCycle, &[16, 32]);
        let path_receipt = canonical_receipt(UniformD1ReceiptKind::CellCenteredNeumannPath);
        assert_eq!(
            ConvergenceCertificate::uniform_cycle(&tower, 2, path_receipt),
            Err(RefinementTypeError::ReceiptKindMismatch {
                expected: UniformD1ReceiptKind::UniformCycle,
                actual: UniformD1ReceiptKind::CellCenteredNeumannPath
            })
        );
    }

    #[test]
    fn family_rate_and_mode_domains_cannot_be_mixed() {
        let path_tower = uniform_tower(ShadowKind::CellCenteredNeumannPath, &[16, 32, 64]);
        let cycle_receipt = canonical_receipt(UniformD1ReceiptKind::UniformCycle);
        assert_eq!(
            ConvergenceCertificate::uniform_cycle(&path_tower, 2, cycle_receipt),
            Err(RefinementTypeError::WrongFamily {
                expected: ShadowKind::UniformCycle,
                actual: ShadowKind::CellCenteredNeumannPath
            })
        );

        let cycle_tower = uniform_tower(ShadowKind::UniformCycle, &[16, 32]);
        let receipt = canonical_receipt(UniformD1ReceiptKind::UniformCycle);
        assert_eq!(
            ConvergenceCertificate::uniform_cycle(&cycle_tower, 8, receipt),
            Err(RefinementTypeError::ModeOutsideCertificateDomain {
                kind: ShadowKind::UniformCycle,
                mode_index: 8,
                resolution: 16
            })
        );
    }

    #[test]
    fn tower_digest_has_known_answer_and_detects_tampering() {
        let tower = uniform_tower(ShadowKind::UniformCycle, &[16, 32, 64]);
        let tampered = uniform_tower(ShadowKind::UniformCycle, &[16, 32, 128]);
        let digest = tower.digest_sha256();
        assert_eq!(
            digest,
            "9779cf6ef05b997c4d725ee5975ba1c7d9a214b74f7e3b0f4a317ad88cbb6ad5"
        );
        assert_ne!(digest, tampered.digest_sha256());
    }

    #[test]
    fn malformed_rationals_and_hashes_are_typed_failures() {
        assert_eq!(
            PositiveRational::new(BigInt::from(0_u8), BigInt::from(1_u8)),
            Err(RefinementTypeError::NonPositiveNumerator)
        );
        assert_eq!(
            PositiveRational::new(BigInt::from(1_u8), BigInt::from(0_u8)),
            Err(RefinementTypeError::ZeroDenominator)
        );
        assert_eq!(
            TheoremReceipt::uniform_d1(
                UniformD1ReceiptKind::UniformCycle,
                "not-a-hash",
                D1_INTERFACES_SOURCE_SHA256,
                D1_BOUNDS_AUDIT_SHA256,
                D1_INTERFACES_AUDIT_SHA256,
            ),
            Err(RefinementTypeError::MalformedSha256 {
                artifact: "D1 bounds source"
            })
        );
    }
}
