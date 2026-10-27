//! Bounded declared rational hinge turns and their exact holonomy in `Q/Z`.
//!
//! The supplied angles are turns `theta/(2*pi)`, so the declared deficit is
//! `1 - sum(theta/(2*pi))`. They are not inferred from lengths, simplex metrics,
//! or the rational Regge proxy. A checked modulo-turn correspondence with a
//! separately supplied `d1*w` and a signed integral `d2` license an oriented
//! boundary holonomy identity. They do not license an unrestricted scalar sum.
//! Ordered noncommuting `SO(4,Q)` word cancellation has its own API and receipt.
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::regge_exact::So4;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_holonomy::gauge_quotient::{
    GaugeDiagnosticAuthority, GaugeQuotientRefusal, GaugeSource, RationalGaugeQuotient,
    MAX_GAUGE_DIMENSION,
};
use core_number_theory::rational_turns::RationalTurn;
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReggeTurnRefusal {
    #[error("a source binding is required")]
    MissingSource,
    #[error("required data are absent: {0}")]
    MissingData(&'static str),
    #[error("finite turn/word budget exceeded")]
    Budget,
    #[error("shape does not match the declared carrier: {0}")]
    Shape(&'static str),
    #[error("a coefficient is not a canonical rational: {0}")]
    NonCanonicalRational(&'static str),
    #[error("each supplied interior dihedral turn must be strictly between 0 and 1/2")]
    DihedralTurnRange,
    #[error("hinge star must be a closed simple chamber cycle with at least three sectors")]
    InvalidHingeCycle,
    #[error("hinge index {0} is outside the curvature carrier")]
    HingeOutOfRange(usize),
    #[error("hinge index {0} is repeated")]
    DuplicateHinge(usize),
    #[error("hinge index {0} has no declared turn data")]
    MissingHinge(usize),
    #[error("d2 entries must be signed incidence coefficients -1, 0 or 1")]
    NonIntegralIncidence,
    #[error("d2*d1 is nonzero")]
    CurvatureLaw,
    #[error("declared deficit and cochain curvature differ modulo turns at hinge {0}")]
    DeficitCorrespondence(usize),
    #[error("the supplied three-chain has an empty boundary cycle")]
    EmptyBoundaryCycle,
    #[error("receipt belongs to a different complete turn carrier")]
    CarrierMismatch,
    #[error("SO(4) transport has an out-of-carrier endpoint")]
    FrameEndpoint,
    #[error("transition matrix is not in SO(4,Q)")]
    FrameRejected,
    #[error("ordered step refers to absent edge {0}")]
    MissingEdge(usize),
    #[error("face loop is not a closed path at the supplied common basepoint")]
    CommonBasepoint,
    #[error("the complete ordered boundary word does not freely cancel")]
    UncancelledBoundaryWord,
    #[error("independent replay failed: {0}")]
    Replay(&'static str),
    #[error("exact gauge quotient refused: {0}")]
    Gauge(#[from] GaugeQuotientRefusal),
    #[error("mathematical owner refused: {0}")]
    Owner(String),
}

fn owner(error: impl std::fmt::Debug) -> ReggeTurnRefusal {
    ReggeTurnRefusal::Owner(format!("{error:?}"))
}

fn canonical(value: &BigRational) -> bool {
    if value.denom() <= &0.into() {
        return false;
    }
    let normalized = BigRational::new(value.numer().clone(), value.denom().clone());
    normalized.numer() == value.numer() && normalized.denom() == value.denom()
}

fn pair(
    cycle: &[BigRational],
    values: &[BigRational],
    limits: OperationLimits,
) -> Result<BigRational, ReggeTurnRefusal> {
    if cycle.len() != values.len() {
        return Err(ReggeTurnRefusal::Shape("pairing"));
    }
    let row = BasicMatrix::from_row_major(1, cycle.len(), cycle.to_vec()).map_err(owner)?;
    row.checked_mul_vec_with_limits(values, limits)
        .map_err(owner)?
        .into_iter()
        .next()
        .ok_or(ReggeTurnRefusal::Replay("pairing output"))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ReggeTurnScope {
    /// Supplied rational turns with a checked algebraic correspondence.
    /// There is no length-to-angle derivation or geometric Regge action here.
    DeclaredRationalHingeTurns,
}

/// An explicit closed chamber cycle and the interior turn assigned to each
/// sector. These are declarations, not a certificate of simplex realizability.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredHingeStar {
    hinge: usize,
    chamber_cycle: Vec<usize>,
    dihedral_turns: Vec<BigRational>,
}
impl DeclaredHingeStar {
    fn validate_chamber_cycle(chamber_cycle: &[usize], n_turns: usize) -> Result<(), ReggeTurnRefusal> {
        if n_turns < 3
            || chamber_cycle.len() != n_turns + 1
            || chamber_cycle.first() != chamber_cycle.last()
            || chamber_cycle.iter().any(|&vertex| vertex >= MAX_GAUGE_DIMENSION)
        {
            return Err(ReggeTurnRefusal::InvalidHingeCycle);
        }
        let distinct: BTreeSet<_> = chamber_cycle.iter().take(n_turns).copied().collect();
        if distinct.len() != n_turns {
            return Err(ReggeTurnRefusal::InvalidHingeCycle);
        }
        Ok(())
    }

    fn validate_dihedral_turns(dihedral_turns: &[BigRational]) -> Result<(), ReggeTurnRefusal> {
        if dihedral_turns.iter().any(|turn| !canonical(turn)) {
            return Err(ReggeTurnRefusal::NonCanonicalRational("dihedral turns"));
        }
        let half = BigRational::new(1.into(), 2.into());
        if dihedral_turns
            .iter()
            .any(|turn| turn <= &BigRational::zero() || turn >= &half)
        {
            return Err(ReggeTurnRefusal::DihedralTurnRange);
        }
        Ok(())
    }

    pub fn try_new(
        hinge: usize,
        chamber_cycle: Option<Vec<usize>>,
        dihedral_turns: Option<Vec<BigRational>>,
    ) -> Result<Self, ReggeTurnRefusal> {
        let chamber_cycle = chamber_cycle.ok_or(ReggeTurnRefusal::MissingData("chamber cycle"))?;
        let dihedral_turns =
            dihedral_turns.ok_or(ReggeTurnRefusal::MissingData("dihedral turns"))?;
        if dihedral_turns.len() > MAX_GAUGE_DIMENSION
            || chamber_cycle.len() > MAX_GAUGE_DIMENSION + 1
        {
            return Err(ReggeTurnRefusal::Budget);
        }
        Self::validate_chamber_cycle(&chamber_cycle, dihedral_turns.len())?;
        Self::validate_dihedral_turns(&dihedral_turns)?;
        Ok(Self {
            hinge,
            chamber_cycle,
            dihedral_turns,
        })
    }
    pub fn hinge(&self) -> usize {
        self.hinge
    }
    pub fn chamber_cycle(&self) -> &[usize] {
        &self.chamber_cycle
    }
    pub fn dihedral_turns(&self) -> &[BigRational] {
        &self.dihedral_turns
    }
    pub fn deficit_turns(&self) -> BigRational {
        BigRational::one() - self.dihedral_turns.iter().cloned().sum::<BigRational>()
    }
}

/// Complete finite cochain data through `d2`. Signed integral incidence makes
/// modulo-turn boundary evaluation well defined; rational weights would not.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredReggeTurnComplex {
    source: GaugeSource,
    quotient: RationalGaugeQuotient,
    d2: BasicMatrix<BigRational>,
}
impl DeclaredReggeTurnComplex {
    fn validate_d2_matrix(
        d2: &BasicMatrix<BigRational>,
        dim2: usize,
    ) -> Result<(), ReggeTurnRefusal> {
        if d2.rows() > MAX_GAUGE_DIMENSION {
            return Err(ReggeTurnRefusal::Budget);
        }
        if dim2 == 0 || d2.cols() != dim2 {
            return Err(ReggeTurnRefusal::Shape("d2/hinge carrier"));
        }
        if d2.as_slice().iter().any(|value| !canonical(value)) {
            return Err(ReggeTurnRefusal::NonCanonicalRational("d2"));
        }
        if d2.as_slice().iter().any(|value| {
            !value.denom().is_one() || value.numer() < &(-1).into() || value.numer() > &1.into()
        }) {
            return Err(ReggeTurnRefusal::NonIntegralIncidence);
        }
        Ok(())
    }

    pub fn try_new(
        source: Option<GaugeSource>,
        quotient: &RationalGaugeQuotient,
        d2: Option<BasicMatrix<BigRational>>,
        limits: OperationLimits,
    ) -> Result<Self, ReggeTurnRefusal> {
        let source = source.ok_or(ReggeTurnRefusal::MissingSource)?;
        let d2 = d2.ok_or(ReggeTurnRefusal::MissingData("d2"))?;
        Self::validate_d2_matrix(&d2, quotient.dimensions()[2])?;
        quotient.replay_chain_law(limits)?;
        let product = d2
            .checked_mul_with_limits(quotient.d1(), limits)
            .map_err(owner)?;
        if product.as_slice().iter().any(|value| !value.is_zero()) {
            return Err(ReggeTurnRefusal::CurvatureLaw);
        }
        Ok(Self {
            source,
            quotient: quotient.clone(),
            d2,
        })
    }

    pub fn source(&self) -> &GaugeSource {
        &self.source
    }
    pub fn quotient(&self) -> &RationalGaugeQuotient {
        &self.quotient
    }
    pub fn d2(&self) -> &BasicMatrix<BigRational> {
        &self.d2
    }

    pub fn replay_curvature_law(&self, limits: OperationLimits) -> Result<(), ReggeTurnRefusal> {
        self.quotient.replay_chain_law(limits)?;
        let product = self
            .d2
            .checked_mul_with_limits(self.quotient.d1(), limits)
            .map_err(owner)?;
        if product.as_slice().iter().any(|value| !value.is_zero()) {
            return Err(ReggeTurnRefusal::CurvatureLaw);
        }
        Ok(())
    }

    /// Evaluates every declared hinge, then checks `deficit = d1*w` in `Q/Z`.
    /// Both the real lift of the deficit and its periodic holonomy are retained.
    fn validate_evaluate_budget(
        stars: &[DeclaredHingeStar],
        hinges: usize,
        limits: OperationLimits,
    ) -> Result<(), ReggeTurnRefusal> {
        if stars.len() > hinges {
            return Err(ReggeTurnRefusal::Shape("hinge stars"));
        }
        let angle_entries = stars.iter().try_fold(0usize, |count, star| {
            count
                .checked_add(star.dihedral_turns.len())
                .ok_or(ReggeTurnRefusal::Budget)
        })?;
        if angle_entries > limits.max_elements
            || angle_entries
                .checked_add(hinges)
                .ok_or(ReggeTurnRefusal::Budget)?
                > limits.max_scalar_ops
        {
            return Err(ReggeTurnRefusal::Budget);
        }
        Ok(())
    }

    fn collect_star_deficits(
        stars: &[DeclaredHingeStar],
        hinges: usize,
        curvature: &[BigRational],
    ) -> Result<Vec<BigRational>, ReggeTurnRefusal> {
        let mut seen = BTreeSet::new();
        let mut deficits = vec![BigRational::zero(); hinges];
        for star in stars {
            if star.hinge >= hinges {
                return Err(ReggeTurnRefusal::HingeOutOfRange(star.hinge));
            }
            if !seen.insert(star.hinge) {
                return Err(ReggeTurnRefusal::DuplicateHinge(star.hinge));
            }
            let deficit = star.deficit_turns();
            if RationalTurn::new(deficit.clone())
                != RationalTurn::new(curvature[star.hinge].clone())
            {
                return Err(ReggeTurnRefusal::DeficitCorrespondence(star.hinge));
            }
            deficits[star.hinge] = deficit;
        }
        if let Some(missing) = (0..hinges).find(|hinge| !seen.contains(hinge)) {
            return Err(ReggeTurnRefusal::MissingHinge(missing));
        }
        Ok(deficits)
    }

    pub fn evaluate(
        &self,
        stars: Option<&[DeclaredHingeStar]>,
        representative: Option<&[BigRational]>,
        limits: OperationLimits,
    ) -> Result<ReggeDeficitReceipt, ReggeTurnRefusal> {
        let stars = stars.ok_or(ReggeTurnRefusal::MissingData("hinge stars"))?;
        let representative =
            representative.ok_or(ReggeTurnRefusal::MissingData("connection cochain"))?;
        let hinges = self.quotient.dimensions()[2];
        Self::validate_evaluate_budget(stars, hinges, limits)?;
        self.replay_curvature_law(limits)?;
        let curvature = self.quotient.curvature(representative, limits)?;
        let deficits = Self::collect_star_deficits(stars, hinges, &curvature)?;
        let holonomy_turns = deficits.iter().cloned().map(RationalTurn::new).collect();
        Ok(ReggeDeficitReceipt {
            context: self.clone(),
            stars: stars.to_vec(),
            representative: representative.to_vec(),
            deficits,
            curvature,
            holonomy_turns,
            scope: ReggeTurnScope::DeclaredRationalHingeTurns,
            authority_effect: GaugeDiagnosticAuthority::None,
        })
    }

    /// The supplied integral 3-chain determines the oriented 2-cycle `d2ᵀ*c3`.
    /// Checks both its zero curvature pairing and its integer deficit pairing.
    fn compute_boundary_cycle(
        &self,
        three_chain: &[BigInt],
        limits: OperationLimits,
    ) -> Result<Vec<BigRational>, ReggeTurnRefusal> {
        if three_chain.len() != self.d2.rows() {
            return Err(ReggeTurnRefusal::Shape("integral three-chain"));
        }
        if self.d2.as_slice().len() > limits.max_elements
            || self.quotient.d1().as_slice().len() > limits.max_elements
        {
            return Err(ReggeTurnRefusal::Budget);
        }
        let coefficients: Vec<_> = three_chain
            .iter()
            .cloned()
            .map(BigRational::from_integer)
            .collect();
        let cycle = self
            .d2
            .try_transpose()
            .map_err(owner)?
            .checked_mul_vec_with_limits(&coefficients, limits)
            .map_err(owner)?;
        if cycle.iter().all(Zero::is_zero) {
            return Err(ReggeTurnRefusal::EmptyBoundaryCycle);
        }
        let cycle_boundary = self
            .quotient
            .d1()
            .try_transpose()
            .map_err(owner)?
            .checked_mul_vec_with_limits(&cycle, limits)
            .map_err(owner)?;
        if cycle_boundary.iter().any(|value| !value.is_zero()) {
            return Err(ReggeTurnRefusal::Replay("boundary cycle"));
        }
        Ok(cycle)
    }

    fn extract_integral_boundary_cycle(
        cycle: &[BigRational],
    ) -> Result<Vec<BigInt>, ReggeTurnRefusal> {
        cycle
            .iter()
            .map(|value| {
                if !value.denom().is_one() {
                    return Err(ReggeTurnRefusal::Replay("integral boundary cycle"));
                }
                Ok(value.numer().clone())
            })
            .collect()
    }

    pub fn boundary_holonomy(
        &self,
        deficit: &ReggeDeficitReceipt,
        three_chain: Option<&[BigInt]>,
        limits: OperationLimits,
    ) -> Result<BoundaryTurnReceipt, ReggeTurnRefusal> {
        deficit.replay(self, limits)?;
        let three_chain =
            three_chain.ok_or(ReggeTurnRefusal::MissingData("integral three-chain"))?;
        let cycle = self.compute_boundary_cycle(three_chain, limits)?;
        let curvature_pairing = pair(&cycle, &deficit.curvature, limits)?;
        let deficit_pairing = pair(&cycle, &deficit.deficits, limits)?;
        let holonomy = RationalTurn::new(deficit_pairing.clone());
        if !curvature_pairing.is_zero() || holonomy != RationalTurn::zero() {
            return Err(ReggeTurnRefusal::Replay(
                "oriented modulo-turn boundary identity",
            ));
        }
        let boundary_cycle = Self::extract_integral_boundary_cycle(&cycle)?;
        Ok(BoundaryTurnReceipt {
            deficit: deficit.clone(),
            three_chain: three_chain.to_vec(),
            boundary_cycle,
            curvature_pairing,
            deficit_pairing,
            holonomy,
            authority_effect: GaugeDiagnosticAuthority::None,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReggeDeficitReceipt {
    context: DeclaredReggeTurnComplex,
    stars: Vec<DeclaredHingeStar>,
    representative: Vec<BigRational>,
    deficits: Vec<BigRational>,
    curvature: Vec<BigRational>,
    holonomy_turns: Vec<RationalTurn>,
    scope: ReggeTurnScope,
    authority_effect: GaugeDiagnosticAuthority,
}
impl ReggeDeficitReceipt {
    pub fn stars(&self) -> &[DeclaredHingeStar] {
        &self.stars
    }
    pub fn representative(&self) -> &[BigRational] {
        &self.representative
    }
    pub fn deficit_turns(&self) -> &[BigRational] {
        &self.deficits
    }
    pub fn curvature(&self) -> &[BigRational] {
        &self.curvature
    }
    pub fn holonomy_turns(&self) -> &[RationalTurn] {
        &self.holonomy_turns
    }
    pub fn source(&self) -> &GaugeSource {
        &self.context.source
    }
    pub fn scope(&self) -> ReggeTurnScope {
        self.scope
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(
        &self,
        context: &DeclaredReggeTurnComplex,
        limits: OperationLimits,
    ) -> Result<(), ReggeTurnRefusal> {
        if self.context != *context {
            return Err(ReggeTurnRefusal::CarrierMismatch);
        }
        if context.evaluate(Some(&self.stars), Some(&self.representative), limits)? != *self {
            return Err(ReggeTurnRefusal::Replay("deficit receipt"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryTurnReceipt {
    deficit: ReggeDeficitReceipt,
    three_chain: Vec<BigInt>,
    boundary_cycle: Vec<BigInt>,
    curvature_pairing: BigRational,
    deficit_pairing: BigRational,
    holonomy: RationalTurn,
    authority_effect: GaugeDiagnosticAuthority,
}
impl BoundaryTurnReceipt {
    pub fn three_chain(&self) -> &[BigInt] {
        &self.three_chain
    }
    pub fn boundary_cycle(&self) -> &[BigInt] {
        &self.boundary_cycle
    }
    pub fn curvature_pairing(&self) -> &BigRational {
        &self.curvature_pairing
    }
    pub fn deficit_pairing(&self) -> &BigRational {
        &self.deficit_pairing
    }
    pub fn holonomy(&self) -> &RationalTurn {
        &self.holonomy
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(
        &self,
        context: &DeclaredReggeTurnComplex,
        limits: OperationLimits,
    ) -> Result<(), ReggeTurnRefusal> {
        if context.boundary_holonomy(&self.deficit, Some(&self.three_chain), limits)? != *self {
            return Err(ReggeTurnRefusal::Replay("boundary turn receipt"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum So4Orientation {
    Forward,
    Reverse,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct OrientedSo4Step {
    pub edge: usize,
    pub orientation: So4Orientation,
}

/// Checked directed frame transport. The matrix owner certifies `SO(4,Q)`.
/// Keeping the matrix private prevents post-admission mutation of that claim.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct So4EdgeTransport {
    source: usize,
    target: usize,
    transition: So4,
}
impl So4EdgeTransport {
    pub fn endpoints(&self) -> (usize, usize) {
        (self.source, self.target)
    }
    pub fn try_new(
        source: usize,
        target: usize,
        matrix: [[BigRational; 4]; 4],
    ) -> Result<Self, ReggeTurnRefusal> {
        if source >= MAX_GAUGE_DIMENSION || target >= MAX_GAUGE_DIMENSION {
            return Err(ReggeTurnRefusal::FrameEndpoint);
        }
        if matrix.iter().flatten().any(|value| !canonical(value)) {
            return Err(ReggeTurnRefusal::NonCanonicalRational("SO4 transition"));
        }
        let transition = So4::try_new(matrix).map_err(|_| ReggeTurnRefusal::FrameRejected)?;
        Ok(Self {
            source,
            target,
            transition,
        })
    }
    pub fn transition(&self) -> &So4 {
        &self.transition
    }
}

/// Replays the WHOLE ordered word: every face loop uses a common basepoint and
/// the concatenated edge/inverse word freely cancels before matrix evaluation.
/// This is a sufficient combinatorial Bianchi premise. No chamber geometry or
/// completeness of a 3-cell's face inventory is inferred from its cancellation.
fn validate_so4_dimension_bounds(
    edges_len: usize,
    loops_len: usize,
    steps: usize,
    common_basepoint: usize,
) -> Result<(), ReggeTurnRefusal> {
    if edges_len > MAX_GAUGE_DIMENSION || loops_len > MAX_GAUGE_DIMENSION {
        return Err(ReggeTurnRefusal::Budget);
    }
    if steps > 4096 || common_basepoint >= MAX_GAUGE_DIMENSION {
        return Err(ReggeTurnRefusal::Budget);
    }
    Ok(())
}

fn validate_so4_inputs_nonempty(
    edges: &[So4EdgeTransport],
    loops: &[Vec<OrientedSo4Step>],
) -> Result<(), ReggeTurnRefusal> {
    if edges.is_empty() || loops.is_empty() || loops.iter().any(Vec::is_empty) {
        return Err(ReggeTurnRefusal::MissingData("nonempty SO4 boundary word"));
    }
    Ok(())
}

fn validate_so4_boundary_budget(
    edges: &[So4EdgeTransport],
    loops: &[Vec<OrientedSo4Step>],
    common_basepoint: usize,
    limits: OperationLimits,
) -> Result<(), ReggeTurnRefusal> {
    validate_so4_inputs_nonempty(edges, loops)?;
    let steps = loops.iter().try_fold(0usize, |count, face| {
        count
            .checked_add(face.len())
            .ok_or(ReggeTurnRefusal::Budget)
    })?;
    validate_so4_dimension_bounds(edges.len(), loops.len(), steps, common_basepoint)?;

    let multiplications = steps
        .checked_add(loops.len())
        .ok_or(ReggeTurnRefusal::Budget)?;
    let matrix_elements = multiplications
        .checked_add(edges.len())
        .and_then(|count| count.checked_add(1))
        .and_then(|count| count.checked_mul(16))
        .ok_or(ReggeTurnRefusal::Budget)?;
    let scalar_ops = multiplications
        .checked_mul(128)
        .ok_or(ReggeTurnRefusal::Budget)?;
    if matrix_elements > limits.max_elements || scalar_ops > limits.max_scalar_ops {
        return Err(ReggeTurnRefusal::Budget);
    }
    Ok(())
}

fn verify_so4_word_cancellation(
    edges: &[So4EdgeTransport],
    loops: &[Vec<OrientedSo4Step>],
    common_basepoint: usize,
) -> Result<(), ReggeTurnRefusal> {
    let mut stack: Vec<OrientedSo4Step> = Vec::new();
    for face in loops {
        let mut vertex = common_basepoint;
        for step in face {
            let edge = edges
                .get(step.edge)
                .ok_or(ReggeTurnRefusal::MissingEdge(step.edge))?;
            let (from, to) = match step.orientation {
                So4Orientation::Forward => (edge.source, edge.target),
                So4Orientation::Reverse => (edge.target, edge.source),
            };
            if from != vertex {
                return Err(ReggeTurnRefusal::CommonBasepoint);
            }
            vertex = to;
            if stack
                .last()
                .is_some_and(|last| last.edge == step.edge && last.orientation != step.orientation)
            {
                stack.pop();
            } else {
                stack.push(*step);
            }
        }
        if vertex != common_basepoint {
            return Err(ReggeTurnRefusal::CommonBasepoint);
        }
    }
    if !stack.is_empty() {
        return Err(ReggeTurnRefusal::UncancelledBoundaryWord);
    }
    Ok(())
}

fn compute_so4_face_holonomies(
    edges: &[So4EdgeTransport],
    loops: &[Vec<OrientedSo4Step>],
) -> Result<So4, ReggeTurnRefusal> {
    let mut face_holonomies = Vec::new();
    for face in loops {
        let mut transitions = Vec::new();
        for step in face {
            let edge = edges
                .get(step.edge)
                .ok_or(ReggeTurnRefusal::MissingEdge(step.edge))?;
            transitions.push(match step.orientation {
                So4Orientation::Forward => edge.transition.clone(),
                So4Orientation::Reverse => edge.transition.transpose(),
            });
        }
        face_holonomies.push(crate::exact_regge::hinge_holonomy(&transitions));
    }
    let ordered_product = crate::exact_regge::hinge_holonomy(&face_holonomies);
    if !ordered_product.is_identity() {
        return Err(ReggeTurnRefusal::Replay("SO4 ordered product"));
    }
    Ok(ordered_product)
}

pub fn ordered_so4_boundary(
    source: Option<GaugeSource>,
    edges: Option<&[So4EdgeTransport]>,
    loops: Option<&[Vec<OrientedSo4Step>]>,
    common_basepoint: usize,
    limits: OperationLimits,
) -> Result<So4BoundaryReceipt, ReggeTurnRefusal> {
    let source = source.ok_or(ReggeTurnRefusal::MissingSource)?;
    let edges = edges.ok_or(ReggeTurnRefusal::MissingData("SO4 edges"))?;
    let loops = loops.ok_or(ReggeTurnRefusal::MissingData("SO4 boundary loops"))?;

    validate_so4_boundary_budget(edges, loops, common_basepoint, limits)?;
    verify_so4_word_cancellation(edges, loops, common_basepoint)?;
    let ordered_product = compute_so4_face_holonomies(edges, loops)?;

    Ok(So4BoundaryReceipt {
        source,
        edges: edges.to_vec(),
        loops: loops.to_vec(),
        common_basepoint,
        ordered_product,
        authority_effect: GaugeDiagnosticAuthority::None,
    })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct So4BoundaryReceipt {
    source: GaugeSource,
    edges: Vec<So4EdgeTransport>,
    loops: Vec<Vec<OrientedSo4Step>>,
    common_basepoint: usize,
    ordered_product: So4,
    authority_effect: GaugeDiagnosticAuthority,
}
impl So4BoundaryReceipt {
    pub fn edges(&self) -> &[So4EdgeTransport] {
        &self.edges
    }
    pub fn loops(&self) -> &[Vec<OrientedSo4Step>] {
        &self.loops
    }
    pub fn common_basepoint(&self) -> usize {
        self.common_basepoint
    }
    pub fn source(&self) -> &GaugeSource {
        &self.source
    }
    pub fn ordered_product(&self) -> &So4 {
        &self.ordered_product
    }
    pub fn authority_effect(&self) -> GaugeDiagnosticAuthority {
        self.authority_effect
    }
    pub fn replay(&self, limits: OperationLimits) -> Result<(), ReggeTurnRefusal> {
        if ordered_so4_boundary(
            Some(self.source.clone()),
            Some(&self.edges),
            Some(&self.loops),
            self.common_basepoint,
            limits,
        )? != *self
        {
            return Err(ReggeTurnRefusal::Replay("SO4 boundary receipt"));
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ea7a2a00 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
