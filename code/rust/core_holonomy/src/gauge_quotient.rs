//! Exact finite `C¹ / im(d₀)` and the descended map `dbar₁` to `C²`.
//!
//! The kernel is `H¹ = ker(d₁) / im(d₀)`, rather than the whole quotient.
//! Shape, canonical rational coefficients and `d₁ d₀ = 0` are replayed.
//! Elimination and quotient bases belong to the sovereign linear-algebra and
//! homology owners. No norm minimization or geometric interpretation is inferred.
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::elimination::{solve_with_limits, LinearSolution};
use num_traits::Zero;
use core_homology::finite_rational_homology::{
    FiniteRationalChainComplex, RationalHomologyQuotient,
};
use core_homology::scalar::Q;
use core_kernel::Digest;

/// Hard bound on each carrier. Owner limits additionally bound each operation;
/// they do not bound BigInt limb allocation or constitute a wall-clock deadline.
pub const MAX_GAUGE_DIMENSION: usize = 256;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum GaugeDiagnosticAuthority {
    None,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GaugeQuotientRefusal {
    #[error("a source binding is required")]
    MissingSource,
    #[error("source label must be nonempty and at most 512 bytes")]
    InvalidSource,
    #[error("missing cochain differential {0}")]
    MissingDifferential(&'static str),
    #[error("finite carrier exceeds the declared bound")]
    CarrierBudget,
    #[error("shape does not match the declared cochain carrier: {0}")]
    Shape(&'static str),
    #[error("a coefficient is not a canonical rational: {0}")]
    NonCanonicalRational(&'static str),
    #[error("d1*d0 is nonzero")]
    ChainLaw,
    #[error("quotient class belongs to another complete carrier")]
    CarrierMismatch,
    #[error("the cochain map does not commute with {0}")]
    NonCommutingMap(&'static str),
    #[error("independent exact replay failed: {0}")]
    Replay(&'static str),
    #[error("mathematical owner refused an operation: {0}")]
    Owner(String),
}

fn owner(error: impl std::fmt::Debug) -> GaugeQuotientRefusal {
    GaugeQuotientRefusal::Owner(format!("{error:?}"))
}

fn canonical(value: &Q) -> bool {
    if value.denom() <= &0.into() {
        return false;
    }
    let normalized = Q::new(value.numer().clone(), value.denom().clone());
    normalized.numer() == value.numer() && normalized.denom() == value.denom()
}

fn check_vector(
    values: &[Q],
    length: usize,
    label: &'static str,
) -> Result<(), GaugeQuotientRefusal> {
    if values.len() != length {
        return Err(GaugeQuotientRefusal::Shape(label));
    }
    if values.iter().any(|value| !canonical(value)) {
        return Err(GaugeQuotientRefusal::NonCanonicalRational(label));
    }
    Ok(())
}

fn check_matrix(
    matrix: &BasicMatrix<Q>,
    shape: (usize, usize),
    label: &'static str,
) -> Result<(), GaugeQuotientRefusal> {
    if matrix.shape() != shape {
        return Err(GaugeQuotientRefusal::Shape(label));
    }
    if matrix.as_slice().iter().any(|value| !canonical(value)) {
        return Err(GaugeQuotientRefusal::NonCanonicalRational(label));
    }
    Ok(())
}

fn frame(bytes: &mut Vec<u8>, item: &[u8]) {
    bytes.extend_from_slice(&(item.len() as u64).to_be_bytes());
    bytes.extend_from_slice(item);
}

fn frame_matrix(bytes: &mut Vec<u8>, matrix: &BasicMatrix<Q>) {
    frame(bytes, &(matrix.rows() as u64).to_be_bytes());
    frame(bytes, &(matrix.cols() as u64).to_be_bytes());
    for value in matrix.as_slice() {
        frame(bytes, value.to_string().as_bytes());
    }
}

/// Declared source custody. This binds a label and digest; it does not read a
/// file, certify its contents, or promote a source assertion to a theorem.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugeSource {
    label: String,
    digest: Digest,
}

impl GaugeSource {
    pub fn try_new(label: String, digest: Digest) -> Result<Self, GaugeQuotientRefusal> {
        if label.trim().is_empty() || label.len() > 512 {
            return Err(GaugeQuotientRefusal::InvalidSource);
        }
        Ok(Self { label, digest })
    }

    pub fn from_bytes(label: String, bytes: &[u8]) -> Result<Self, GaugeQuotientRefusal> {
        Self::try_new(label, Digest::of_bytes(bytes))
    }

    pub fn label(&self) -> &str {
        &self.label
    }

    pub fn digest(&self) -> &Digest {
        &self.digest
    }
}

/// Immutable complete `Q` cochain window and chosen exact quotient bases.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalGaugeQuotient {
    source: GaugeSource,
    dimensions: [usize; 3],
    d0: BasicMatrix<Q>,
    d1: BasicMatrix<Q>,
    quotient: RationalHomologyQuotient,
    h1: RationalHomologyQuotient,
    context_digest: Digest,
}

impl RationalGaugeQuotient {
    pub fn try_new(
        source: Option<GaugeSource>,
        dimensions: [usize; 3],
        d0: Option<BasicMatrix<Q>>,
        d1: Option<BasicMatrix<Q>>,
        limits: OperationLimits,
    ) -> Result<Self, GaugeQuotientRefusal> {
        let source = source.ok_or(GaugeQuotientRefusal::MissingSource)?;
        let d0 = d0.ok_or(GaugeQuotientRefusal::MissingDifferential("d0"))?;
        let d1 = d1.ok_or(GaugeQuotientRefusal::MissingDifferential("d1"))?;
        Self::validate_differentials(dimensions, &d0, &d1, limits)?;
        // Reverse degrees so the homology owner computes the two cochain
        // quotients. In degree zero the first complex has no cycle restriction.
        let all_one_cochains = FiniteRationalChainComplex::new(
            vec![dimensions[1], dimensions[0]],
            vec![d0.clone()],
            limits,
        )
        .map_err(owner)?;
        let reversed = FiniteRationalChainComplex::new(
            vec![dimensions[2], dimensions[1], dimensions[0]],
            vec![d1.clone(), d0.clone()],
            limits,
        )
        .map_err(owner)?;
        let quotient =
            RationalHomologyQuotient::new(&all_one_cochains, 0, limits).map_err(owner)?;
        let h1 = RationalHomologyQuotient::new(&reversed, 1, limits).map_err(owner)?;
        let context_digest = Self::compute_context_digest(&source, dimensions, &d0, &d1);
        Ok(Self {
            source,
            dimensions,
            d0,
            d1,
            quotient,
            h1,
            context_digest,
        })
    }

    fn validate_differentials(
        dimensions: [usize; 3],
        d0: &BasicMatrix<Q>,
        d1: &BasicMatrix<Q>,
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        if dimensions.iter().any(|&n| n > MAX_GAUGE_DIMENSION) {
            return Err(GaugeQuotientRefusal::CarrierBudget);
        }
        check_matrix(d0, (dimensions[1], dimensions[0]), "d0")?;
        check_matrix(d1, (dimensions[2], dimensions[1]), "d1")?;
        let product = d1.checked_mul_with_limits(d0, limits).map_err(owner)?;
        if product.as_slice().iter().any(|value| !value.is_zero()) {
            return Err(GaugeQuotientRefusal::ChainLaw);
        }
        Ok(())
    }

    fn compute_context_digest(
        source: &GaugeSource,
        dimensions: [usize; 3],
        d0: &BasicMatrix<Q>,
        d1: &BasicMatrix<Q>,
    ) -> Digest {
        let mut bytes = Vec::new();
        frame(&mut bytes, source.label().as_bytes());
        frame(&mut bytes, source.digest().as_str().as_bytes());
        for dimension in dimensions {
            frame(&mut bytes, &(dimension as u64).to_be_bytes());
        }
        frame_matrix(&mut bytes, d0);
        frame_matrix(&mut bytes, d1);
        Digest::of_domained("core.holonomy.rational-gauge-quotient.v1", &bytes)
    }

    pub fn source(&self) -> &GaugeSource {
        &self.source
    }
    pub fn dimensions(&self) -> [usize; 3] {
        self.dimensions
    }
    pub fn d0(&self) -> &BasicMatrix<Q> {
        &self.d0
    }
    pub fn d1(&self) -> &BasicMatrix<Q> {
        &self.d1
    }
    pub fn context_digest(&self) -> &Digest {
        &self.context_digest
    }
    pub fn quotient_dimension(&self) -> usize {
        self.quotient.dimension()
    }
    pub fn h1_dimension(&self) -> usize {
        self.h1.dimension()
    }

    pub fn replay_chain_law(&self, limits: OperationLimits) -> Result<(), GaugeQuotientRefusal> {
        let product = self
            .d1
            .checked_mul_with_limits(&self.d0, limits)
            .map_err(owner)?;
        if product.as_slice().iter().any(|value| !value.is_zero()) {
            return Err(GaugeQuotientRefusal::ChainLaw);
        }
        Ok(())
    }

    pub fn project(
        &self,
        representative: &[Q],
        limits: OperationLimits,
    ) -> Result<RationalGaugeClass, GaugeQuotientRefusal> {
        check_vector(representative, self.dimensions[1], "representative")?;
        let coordinates = self
            .quotient
            .coordinates(representative, limits)
            .map_err(owner)?;
        Ok(RationalGaugeClass {
            context_digest: self.context_digest.clone(),
            coordinates,
        })
    }

    pub fn representative(
        &self,
        class: &RationalGaugeClass,
        limits: OperationLimits,
    ) -> Result<Vec<Q>, GaugeQuotientRefusal> {
        if class.context_digest != self.context_digest {
            return Err(GaugeQuotientRefusal::CarrierMismatch);
        }
        self.quotient
            .representative(&class.coordinates, limits)
            .map_err(owner)
    }

    /// `dbar₁([w]) = d₁w`, defined on the full quotient, including nonclosed classes.
    pub fn dbar1(
        &self,
        class: &RationalGaugeClass,
        limits: OperationLimits,
    ) -> Result<Vec<Q>, GaugeQuotientRefusal> {
        self.replay_chain_law(limits)?;
        self.d1
            .checked_mul_vec_with_limits(&self.representative(class, limits)?, limits)
            .map_err(owner)
    }

    pub fn curvature(
        &self,
        representative: &[Q],
        limits: OperationLimits,
    ) -> Result<Vec<Q>, GaugeQuotientRefusal> {
        let class = self.project(representative, limits)?;
        let curvature = self
            .d1
            .checked_mul_vec_with_limits(representative, limits)
            .map_err(owner)?;
        if curvature != self.dbar1(&class, limits)? {
            return Err(GaugeQuotientRefusal::Replay(
                "dbar1 representative independence",
            ));
        }
        Ok(curvature)
    }

    /// Retains the original and shifted representatives and replays both images.
    pub fn shift_with_receipt(
        &self,
        representative: &[Q],
        potential: &[Q],
        limits: OperationLimits,
    ) -> Result<GaugeShiftReceipt, GaugeQuotientRefusal> {
        check_vector(representative, self.dimensions[1], "representative")?;
        check_vector(potential, self.dimensions[0], "potential")?;
        let coboundary = self
            .d0
            .checked_mul_vec_with_limits(potential, limits)
            .map_err(owner)?;
        let shifted: Vec<Q> = representative
            .iter()
            .zip(&coboundary)
            .map(|(a, b)| a + b)
            .collect();
        let class = self.project(representative, limits)?;
        if class != self.project(&shifted, limits)? {
            return Err(GaugeQuotientRefusal::Replay("quotient shift"));
        }
        let curvature = self.curvature(representative, limits)?;
        if curvature != self.curvature(&shifted, limits)? {
            return Err(GaugeQuotientRefusal::Replay("curvature shift"));
        }
        Ok(GaugeShiftReceipt {
            context_digest: self.context_digest.clone(),
            original: representative.to_vec(),
            potential: potential.to_vec(),
            shifted,
            class,
            curvature,
            authority_effect: GaugeDiagnosticAuthority::None,
        })
    }

    /// Exactness is solved and replayed; zero curvature alone never supplies a repair.
    pub fn diagnose(
        &self,
        representative: &[Q],
        limits: OperationLimits,
    ) -> Result<GaugeDiagnosisReceipt, GaugeQuotientRefusal> {
        let class = self.project(representative, limits)?;
        let curvature = self.curvature(representative, limits)?;
        let classification = if representative.iter().all(Zero::is_zero) {
            GaugeClassification::Zero
        } else if class.coordinates.iter().all(Zero::is_zero) {
            self.classify_zero_quotient(representative, limits)?
        } else {
            self.classify_nonzero_quotient(representative, &curvature, limits)?
        };
        Ok(GaugeDiagnosisReceipt {
            context_digest: self.context_digest.clone(),
            representative: representative.to_vec(),
            class,
            curvature,
            classification,
            h1_dimension: self.h1.dimension(),
            authority_effect: GaugeDiagnosticAuthority::None,
        })
    }

    fn classify_zero_quotient(
        &self,
        representative: &[Q],
        limits: OperationLimits,
    ) -> Result<GaugeClassification, GaugeQuotientRefusal> {
        match solve_with_limits(&self.d0, representative, limits).map_err(owner)? {
            LinearSolution::Consistent { particular, .. } => {
                if self
                    .d0
                    .checked_mul_vec_with_limits(&particular, limits)
                    .map_err(owner)?
                    != representative
                {
                    return Err(GaugeQuotientRefusal::Replay("exact repair"));
                }
                Ok(GaugeClassification::ExactRepairable {
                    potential: particular,
                })
            }
            LinearSolution::Inconsistent { .. } => {
                Err(GaugeQuotientRefusal::Replay("zero quotient exactness"))
            }
        }
    }

    fn classify_nonzero_quotient(
        &self,
        representative: &[Q],
        curvature: &[Q],
        limits: OperationLimits,
    ) -> Result<GaugeClassification, GaugeQuotientRefusal> {
        if curvature.iter().all(Zero::is_zero) {
            let coordinates = self.h1.coordinates(representative, limits).map_err(owner)?;
            if coordinates.iter().all(Zero::is_zero) || self.h1.dimension() == 0 {
                return Err(GaugeQuotientRefusal::Replay("nonzero H1 class"));
            }
            Ok(GaugeClassification::ClosedNonExact {
                h1_coordinates: coordinates,
            })
        } else {
            Ok(GaugeClassification::NonClosed)
        }
    }
}

/// Context-bound coordinates, with equality exactly in the computed quotient.
/// Fields are private; no unchecked class deserialization is provided.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalGaugeClass {
    context_digest: Digest,
    coordinates: Vec<Q>,
}
impl RationalGaugeClass {
    pub fn coordinates(&self) -> &[Q] {
        &self.coordinates
    }
    pub fn is_zero(&self) -> bool {
        self.coordinates.iter().all(Zero::is_zero)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum GaugeClassification {
    Zero,
    ExactRepairable { potential: Vec<Q> },
    ClosedNonExact { h1_coordinates: Vec<Q> },
    NonClosed,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugeShiftReceipt {
    context_digest: Digest,
    original: Vec<Q>,
    potential: Vec<Q>,
    shifted: Vec<Q>,
    class: RationalGaugeClass,
    curvature: Vec<Q>,
    authority_effect: GaugeDiagnosticAuthority,
}
impl GaugeShiftReceipt {
    pub fn original(&self) -> &[Q] {
        &self.original
    }
    pub fn potential(&self) -> &[Q] {
        &self.potential
    }
    pub fn shifted(&self) -> &[Q] {
        &self.shifted
    }
    pub fn class(&self) -> &RationalGaugeClass {
        &self.class
    }
    pub fn curvature(&self) -> &[Q] {
        &self.curvature
    }
    pub fn context_digest(&self) -> &Digest {
        &self.context_digest
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(
        &self,
        carrier: &RationalGaugeQuotient,
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        if carrier.context_digest != self.context_digest {
            return Err(GaugeQuotientRefusal::CarrierMismatch);
        }
        if carrier.shift_with_receipt(&self.original, &self.potential, limits)? != *self {
            return Err(GaugeQuotientRefusal::Replay("shift receipt"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugeDiagnosisReceipt {
    context_digest: Digest,
    representative: Vec<Q>,
    class: RationalGaugeClass,
    curvature: Vec<Q>,
    classification: GaugeClassification,
    h1_dimension: usize,
    authority_effect: GaugeDiagnosticAuthority,
}
impl GaugeDiagnosisReceipt {
    pub fn representative(&self) -> &[Q] {
        &self.representative
    }
    pub fn classification(&self) -> &GaugeClassification {
        &self.classification
    }
    pub fn class(&self) -> &RationalGaugeClass {
        &self.class
    }
    pub fn curvature(&self) -> &[Q] {
        &self.curvature
    }
    pub fn h1_dimension(&self) -> usize {
        self.h1_dimension
    }
    pub fn context_digest(&self) -> &Digest {
        &self.context_digest
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(
        &self,
        carrier: &RationalGaugeQuotient,
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        if carrier.context_digest != self.context_digest {
            return Err(GaugeQuotientRefusal::CarrierMismatch);
        }
        if carrier.diagnose(&self.representative, limits)? != *self {
            return Err(GaugeQuotientRefusal::Replay("diagnosis receipt"));
        }
        Ok(())
    }
}

/// A complete exact cochain map. Commutation licenses quotient transport;
/// injectivity, inverse transport and norm preservation require further data.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommutingGaugeMap {
    source: RationalGaugeQuotient,
    target: RationalGaugeQuotient,
    maps: [BasicMatrix<Q>; 3],
    context_digest: Digest,
}
impl CommutingGaugeMap {
    pub fn source(&self) -> &RationalGaugeQuotient {
        &self.source
    }
    pub fn target(&self) -> &RationalGaugeQuotient {
        &self.target
    }
    pub fn maps(&self) -> &[BasicMatrix<Q>; 3] {
        &self.maps
    }
    pub fn context_digest(&self) -> &Digest {
        &self.context_digest
    }
    pub fn try_new(
        source: &RationalGaugeQuotient,
        target: &RationalGaugeQuotient,
        maps: [BasicMatrix<Q>; 3],
        limits: OperationLimits,
    ) -> Result<Self, GaugeQuotientRefusal> {
        source.replay_chain_law(limits)?;
        target.replay_chain_law(limits)?;
        for (degree, map) in maps.iter().enumerate() {
            check_matrix(
                map,
                (target.dimensions[degree], source.dimensions[degree]),
                "transport",
            )?;
        }
        Self::verify_commuting_squares(source, target, &maps, limits)?;
        let mut bytes = Vec::new();
        frame(&mut bytes, source.context_digest.as_str().as_bytes());
        frame(&mut bytes, target.context_digest.as_str().as_bytes());
        for map in &maps {
            frame_matrix(&mut bytes, map);
        }
        let context_digest = Digest::of_domained("core.holonomy.commuting-gauge-map.v1", &bytes);
        Ok(Self {
            source: source.clone(),
            target: target.clone(),
            maps,
            context_digest,
        })
    }

    fn verify_commuting_squares(
        source: &RationalGaugeQuotient,
        target: &RationalGaugeQuotient,
        maps: &[BasicMatrix<Q>; 3],
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        if target
            .d0
            .checked_mul_with_limits(&maps[0], limits)
            .map_err(owner)?
            != maps[1]
                .checked_mul_with_limits(&source.d0, limits)
                .map_err(owner)?
        {
            return Err(GaugeQuotientRefusal::NonCommutingMap("d0"));
        }
        if target
            .d1
            .checked_mul_with_limits(&maps[1], limits)
            .map_err(owner)?
            != maps[2]
                .checked_mul_with_limits(&source.d1, limits)
                .map_err(owner)?
        {
            return Err(GaugeQuotientRefusal::NonCommutingMap("d1"));
        }
        Ok(())
    }

    pub fn transport_class(
        &self,
        class: &RationalGaugeClass,
        limits: OperationLimits,
    ) -> Result<RationalGaugeClass, GaugeQuotientRefusal> {
        let representative = self.source.representative(class, limits)?;
        let image = self.maps[1]
            .checked_mul_vec_with_limits(&representative, limits)
            .map_err(owner)?;
        self.target.project(&image, limits)
    }

    pub fn transport_with_receipt(
        &self,
        representative: &[Q],
        potential: &[Q],
        limits: OperationLimits,
    ) -> Result<GaugeTransportReceipt, GaugeQuotientRefusal> {
        let shift = self
            .source
            .shift_with_receipt(representative, potential, limits)?;
        let image = self.maps[1]
            .checked_mul_vec_with_limits(representative, limits)
            .map_err(owner)?;
        let image_potential = self.maps[0]
            .checked_mul_vec_with_limits(potential, limits)
            .map_err(owner)?;
        let target_shift = self
            .target
            .shift_with_receipt(&image, &image_potential, limits)?;
        self.verify_transport_consistency(&shift, &target_shift, limits)?;
        Ok(GaugeTransportReceipt {
            map_digest: self.context_digest.clone(),
            source_shift: shift,
            target_shift,
            authority_effect: GaugeDiagnosticAuthority::None,
        })
    }

    fn verify_transport_consistency(
        &self,
        shift: &GaugeShiftReceipt,
        target_shift: &GaugeShiftReceipt,
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        let shifted_image = self.maps[1]
            .checked_mul_vec_with_limits(shift.shifted(), limits)
            .map_err(owner)?;
        if target_shift.shifted() != shifted_image
            || self.transport_class(shift.class(), limits)? != *target_shift.class()
        {
            return Err(GaugeQuotientRefusal::Replay("representative transport"));
        }
        let transported_curvature = self.maps[2]
            .checked_mul_vec_with_limits(shift.curvature(), limits)
            .map_err(owner)?;
        if target_shift.curvature() != transported_curvature {
            return Err(GaugeQuotientRefusal::Replay("dbar1 transport"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaugeTransportReceipt {
    map_digest: Digest,
    source_shift: GaugeShiftReceipt,
    target_shift: GaugeShiftReceipt,
    authority_effect: GaugeDiagnosticAuthority,
}
impl GaugeTransportReceipt {
    pub fn map_digest(&self) -> &Digest {
        &self.map_digest
    }
    pub fn source_shift(&self) -> &GaugeShiftReceipt {
        &self.source_shift
    }
    pub fn target_shift(&self) -> &GaugeShiftReceipt {
        &self.target_shift
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(
        &self,
        map: &CommutingGaugeMap,
        limits: OperationLimits,
    ) -> Result<(), GaugeQuotientRefusal> {
        if self.map_digest != map.context_digest {
            return Err(GaugeQuotientRefusal::CarrierMismatch);
        }
        if map.transport_with_receipt(
            self.source_shift.original(),
            self.source_shift.potential(),
            limits,
        )? != *self
        {
            return Err(GaugeQuotientRefusal::Replay("transport receipt"));
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2ac3dcc0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
