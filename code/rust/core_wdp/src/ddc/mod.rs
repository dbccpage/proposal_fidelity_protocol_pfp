
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_0e26b98f<T> {
    fn checked_invariant_0e26b98f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_0e26b98f<T> for Option<T> {
    #[inline]
    fn checked_invariant_0e26b98f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_0e26b98f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_0e26b98f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
pub mod agent_contract;
pub use agent_contract::swarm_kernel;
pub mod ddc_alphabet;
pub mod ddc_trace;
pub use ddc_alphabet as dda_alphabet;
pub use ddc_trace as dda_trace;
pub mod degree_tower;
pub mod non_authority;
pub use non_authority as coda5_non_authority;
pub mod episode;
pub mod motif;
pub mod move_network;
pub mod mub_cochain;
pub mod op_verification;
pub mod parser;
pub mod sprint_trajectory_gate;
pub mod transition_effects;

pub use parser::{DdcParsedStep, DdcParserRefusal, DdcTapeParser, DdcTapeReceipt};

pub use ddc_trace::{assign_letter, compute_ddc_row_hash, DdcStepRowV1, StateMetrics};
pub use episode::{EpisodeSegmenter, EpisodeStatus, ObstructionEpisodeV1};
pub use motif::{mine_ddc_ngrams, DdcMotifLedgerV1};
pub use transition_effects::{
    canonical_id as transition_canonical_id, effect_receipt, events_commute,
    semantic_effect_classes, solver_trace_allowed, trace_rewrite_equivalent, EffectKind,
    EffectOwner, EffectReceiptV1, EventV1, FiniteTransitionSystemV1, Refusal as TransitionRefusal,
    TransitionEffectsError,
};

use core_functional::gamma2::Gamma2Functional;
use serde::Serialize;
use std::collections::BTreeMap;
use std::ops::{Add, Mul, Neg};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LambdaAlgebraError {
    DifferentFace,
    CapacityOverflow,
    NoObstruction,
    LambdaDidNotResolve,
    DestructiveLambdaExtension,
    ZeroL1WeightTotal,
    GaugeArtifactOnly,
    QuotientCertificateMismatch,
    MissingDegreeTwoSupport,
    PrimaryDiagnosticMismatch,
    XiTieBreakerNotImproving,
    NeedsRealizationFunctor,
    MissingProofCarryingCertificate,
    RepresentationLayerOnlyClaim,
    NonAuthoritativeTerminalStatus,
    ObserverPassivityViolation,
    MissingInvolutionWitness,
    CrossTermNotRepairInvariant,
    CrossTermCoboundary,
}

// Origin: engine/crates_rs/core_wdp/src/ddc/mod.rs
// Claim: urn:core:crates_rs:core-wdp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LambdaAlgebraError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LambdaAlgebraError {}

/// Represents a discrete topological deformation (Lambda surface)
/// anchored to a generic Face identifier `F`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FaceLambda<F> {
    pub face: F,
    pub capacity: i64,
}

/// A declared oriented edge in C1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct OrientedEdge<V> {
    pub source: V,
    pub target: V,
}

impl<V> OrientedEdge<V> {
    pub fn new(source: V, target: V) -> Self {
        Self { source, target }
    }
}

/// A declared oriented 2-simplex with boundary +BC -AC +AB.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct OrientedTriangle<V> {
    pub a: V,
    pub b: V,
    pub c: V,
}

impl<V> OrientedTriangle<V> {
    pub fn new(a: V, b: V, c: V) -> Self {
        Self { a, b, c }
    }
}

/// A finite local execution window: declared vertices, C1 edges, and C2 faces.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteWindow<V> {
    pub vertices: Vec<V>,
    pub edges: Vec<(V, V)>,
    pub faces: Vec<OrientedTriangle<V>>,
}

/// The local C0 -> C1 -> C2 scan result for a finite window.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteWindowScan<V: Ord> {
    pub c1: Cochain1<V>,
    pub l1_tension: u64,
    pub face_gamma2: Vec<u64>,
    pub gamma2_total: u64,
}

impl<V: Ord> FiniteWindowScan<V> {
    pub fn checked_diagnostic_from_quotient(
        &self,
        certificate: QuotientIrreducibilityCertificate,
    ) -> Result<FiniteDiagnostic, LambdaAlgebraError> {
        FiniteDiagnostic::checked_from_quotient_certificate(certificate, self.gamma2_total)
    }
}

impl<V> FiniteWindow<V> {
    pub fn new(vertices: Vec<V>, edges: Vec<(V, V)>, faces: Vec<OrientedTriangle<V>>) -> Self {
        Self {
            vertices,
            edges,
            faces,
        }
    }

    pub fn edges(&self) -> &[(V, V)] {
        &self.edges
    }

    pub fn faces(&self) -> &[OrientedTriangle<V>] {
        &self.faces
    }
}

/// A finite C1 boundary with canonical edge orientation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Boundary1<V: Ord> {
    coefficients: BTreeMap<OrientedEdge<V>, i64>,
}

/// A finite C1 cochain uses the same declared oriented-edge storage as a C1 boundary shadow.
pub type Cochain1<V> = Boundary1<V>;

impl<V: Ord> Default for Boundary1<V> {
    fn default() -> Self {
        Self {
            coefficients: BTreeMap::new(),
        }
    }
}

impl<V: Clone + Ord> Boundary1<V> {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn coefficients(&self) -> &BTreeMap<OrientedEdge<V>, i64> {
        &self.coefficients
    }

    pub fn checked_coefficient(&self, source: V, target: V) -> Result<i64, LambdaAlgebraError> {
        let (edge, sign) = canonical_edge(source, target);
        self.coefficients
            .get(&edge)
            .copied()
            .unwrap_or(0)
            .checked_mul(sign)
            .ok_or(LambdaAlgebraError::CapacityOverflow)
    }

    /// Ergonomic signed read of the canonical-edge coefficient.
    ///
    /// This is **total**: it can never panic. The only stored value that could
    /// overflow the reverse-orientation sign multiply (`i64::MIN * -1`) is
    /// `i64::MIN`, and the write paths
    /// ([`Self::checked_set_term`] / [`Self::checked_add_term`]) reject storing
    /// `i64::MIN` (returning [`LambdaAlgebraError::CapacityOverflow`]), so a
    /// stored coefficient of `i64::MIN` is unrepresentable. The internal
    /// `.expect()` therefore guards an invariant that cannot be violated
    /// through the public API.
    #[must_use]
    pub fn coefficient(&self, source: V, target: V) -> i64 {
        self.checked_coefficient(source, target)
            .checked_invariant_0e26b98f("Boundary1 coefficient: i64::MIN is rejected by the write paths (unreachable)")
    }

    pub fn checked_add_term(
        &mut self,
        source: V,
        target: V,
        coefficient: i64,
    ) -> Result<(), LambdaAlgebraError> {
        let (edge, sign) = canonical_edge(source, target);
        let signed = coefficient
            .checked_mul(sign)
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;
        let next = self
            .coefficients
            .get(&edge)
            .copied()
            .unwrap_or(0)
            .checked_add(signed)
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;

        if next == 0 {
            self.coefficients.remove(&edge);
        } else {
            // Refuse to store i64::MIN: its reverse-orientation sign multiply
            // (i64::MIN * -1) is unrepresentable, which would make the signed
            // read non-total. Keeping i64::MIN out of storage makes
            // `coefficient` / `checked_coefficient` total.
            if next == i64::MIN {
                return Err(LambdaAlgebraError::CapacityOverflow);
            }
            self.coefficients.insert(edge, next);
        }
        Ok(())
    }

    pub fn checked_set_term(
        &mut self,
        source: V,
        target: V,
        coefficient: i64,
    ) -> Result<(), LambdaAlgebraError> {
        let (edge, sign) = canonical_edge(source, target);
        let signed = coefficient
            .checked_mul(sign)
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;
        if signed == 0 {
            self.coefficients.remove(&edge);
        } else {
            // Refuse to store i64::MIN (see `checked_add_term`): keeps the
            // signed read total so `coefficient` cannot panic.
            if signed == i64::MIN {
                return Err(LambdaAlgebraError::CapacityOverflow);
            }
            self.coefficients.insert(edge, signed);
        }
        Ok(())
    }

    pub fn checked_merge(&self, rhs: &Self) -> Result<Self, LambdaAlgebraError> {
        let mut merged = self.clone();
        for (edge, coefficient) in &rhs.coefficients {
            merged.checked_add_term(edge.source.clone(), edge.target.clone(), *coefficient)?;
        }
        Ok(merged)
    }

    pub fn checked_reverse(&self) -> Result<Self, LambdaAlgebraError> {
        let mut reversed = Self::new();
        for (edge, coefficient) in &self.coefficients {
            let negated = coefficient
                .checked_neg()
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            reversed.checked_add_term(edge.source.clone(), edge.target.clone(), negated)?;
        }
        Ok(reversed)
    }

    pub fn checked_scale(&self, scalar: i64) -> Result<Self, LambdaAlgebraError> {
        let mut scaled = Self::new();
        for (edge, coefficient) in &self.coefficients {
            let product = coefficient
                .checked_mul(scalar)
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            scaled.checked_add_term(edge.source.clone(), edge.target.clone(), product)?;
        }
        Ok(scaled)
    }

    pub fn checked_closure_defect(
        &self,
        face: &OrientedTriangle<V>,
    ) -> Result<i64, LambdaAlgebraError> {
        Gamma2Functional::checked_closure(self.checked_face_values(face)?)
            .map_err(|_| LambdaAlgebraError::CapacityOverflow)
    }

    pub fn checked_gamma2(&self, face: &OrientedTriangle<V>) -> Result<u64, LambdaAlgebraError> {
        Gamma2Functional::checked_face(self.checked_face_values(face)?)
            .map_err(|_| LambdaAlgebraError::CapacityOverflow)
    }

    fn checked_face_values(
        &self,
        face: &OrientedTriangle<V>,
    ) -> Result<[i64; 3], LambdaAlgebraError> {
        Ok([
            self.checked_coefficient(face.a.clone(), face.b.clone())?,
            self.checked_coefficient(face.b.clone(), face.c.clone())?,
            self.checked_coefficient(face.c.clone(), face.a.clone())?,
        ])
    }

    pub fn checked_l1_tension(&self) -> Result<u64, LambdaAlgebraError> {
        self.coefficients
            .values()
            .try_fold(0_u64, |acc, coefficient| {
                acc.checked_add(coefficient.unsigned_abs())
                    .ok_or(LambdaAlgebraError::CapacityOverflow)
            })
    }
}

fn canonical_edge<V: Ord>(source: V, target: V) -> (OrientedEdge<V>, i64) {
    if source <= target {
        (OrientedEdge::new(source, target), 1)
    } else {
        (OrientedEdge::new(target, source), -1)
    }
}

impl<V: Clone + Ord> FiniteWindow<V> {
    pub fn checked_l1_tension(&self, cochain: &Cochain1<V>) -> Result<u64, LambdaAlgebraError> {
        self.edges.iter().try_fold(0_u64, |acc, (source, target)| {
            let value = cochain.checked_coefficient(source.clone(), target.clone())?;
            acc.checked_add(value.unsigned_abs())
                .ok_or(LambdaAlgebraError::CapacityOverflow)
        })
    }

    pub fn checked_primitive_difference(
        &self,
        potential: &Cochain0<V>,
    ) -> Result<Cochain1<V>, LambdaAlgebraError> {
        potential.checked_primitive_difference(self.edges.iter().cloned())
    }

    pub fn checked_scan_c1(
        &self,
        c1: &Cochain1<V>,
    ) -> Result<FiniteWindowScan<V>, LambdaAlgebraError> {
        let l1_tension = self.checked_l1_tension(c1)?;
        let mut face_gamma2 = Vec::with_capacity(self.faces.len());
        for face in &self.faces {
            face_gamma2.push(c1.checked_gamma2(face)?);
        }
        let gamma2_total = Gamma2Functional::checked_total(&face_gamma2)
            .map_err(|_| LambdaAlgebraError::CapacityOverflow)?;
        Ok(FiniteWindowScan {
            c1: c1.clone(),
            l1_tension,
            face_gamma2,
            gamma2_total,
        })
    }

    pub fn checked_scan(
        &self,
        potential: &Cochain0<V>,
    ) -> Result<FiniteWindowScan<V>, LambdaAlgebraError> {
        let c1 = self.checked_primitive_difference(potential)?;
        self.checked_scan_c1(&c1)
    }
}

/// A finite C0 assignment; omitted vertices have zero local potential.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Cochain0<V: Ord> {
    values: BTreeMap<V, i64>,
}

impl<V: Ord> Default for Cochain0<V> {
    fn default() -> Self {
        Self {
            values: BTreeMap::new(),
        }
    }
}

impl<V: Clone + Ord> Cochain0<V> {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn from_values<I>(values: I) -> Self
    where
        I: IntoIterator<Item = (V, i64)>,
    {
        Self {
            values: values.into_iter().collect(),
        }
    }

    pub fn value(&self, vertex: &V) -> i64 {
        self.values.get(vertex).copied().unwrap_or(0)
    }

    pub fn set(&mut self, vertex: V, value: i64) {
        if value == 0 {
            self.values.remove(&vertex);
        } else {
            self.values.insert(vertex, value);
        }
    }

    pub fn checked_primitive_difference<I>(
        &self,
        edges: I,
    ) -> Result<Cochain1<V>, LambdaAlgebraError>
    where
        I: IntoIterator<Item = (V, V)>,
    {
        let mut difference = Cochain1::new();
        for (source, target) in edges {
            let coefficient = self
                .value(&target)
                .checked_sub(self.value(&source))
                .ok_or(LambdaAlgebraError::CapacityOverflow)?;
            difference.checked_set_term(source, target, coefficient)?;
        }
        Ok(difference)
    }
}

/// Provenance of a finite diagnostic vector.
///
/// This DDA type currently stores only caller-declared scalars. A structural
/// descent check over these values is not a computation or verification of the
/// canonical Phi1 and Gamma2 functionals.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FiniteDiagnosticProvenance {
    UnverifiedScalarClaim,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FiniteDiagnostic {
    pub phi1: u64,
    pub gamma2: u64,
    provenance: FiniteDiagnosticProvenance,
}

impl FiniteDiagnostic {
    /// Construct an unverified scalar claim for structural DDA bookkeeping.
    /// This does not calculate or certify the canonical functionals.
    pub fn new(phi1: u64, gamma2: u64) -> Self {
        Self {
            phi1,
            gamma2,
            provenance: FiniteDiagnosticProvenance::UnverifiedScalarClaim,
        }
    }

    pub fn provenance(self) -> FiniteDiagnosticProvenance {
        self.provenance
    }

    /// Legacy scalar receipt ingress. Equality of two claimed L1 values does
    /// not replay a primal-dual witness or bind a carrier, so it cannot create
    /// a functional diagnostic. A future typed path must use core_functional.
    pub fn checked_from_quotient_certificate(
        certificate: QuotientIrreducibilityCertificate,
        _gamma2: u64,
    ) -> Result<Self, LambdaAlgebraError> {
        certificate.require_irreducible()?;
        Err(LambdaAlgebraError::MissingProofCarryingCertificate)
    }

    pub fn checked_tension(self) -> Option<u64> {
        self.phi1.checked_add(self.gamma2)
    }

    pub fn is_resolved(self) -> bool {
        self.phi1 == 0 && self.gamma2 == 0
    }

    pub fn is_obstructed(self) -> bool {
        self.phi1 > 0 || self.gamma2 > 0
    }

    /// A structural check of declared scalar values. With
    /// `UnverifiedScalarClaim` provenance, this is not a canonical functional
    /// certificate or authority to make a terminal mathematical claim.
    #[must_use = "ignoring the lambda-license result skips the declared-scalar obstruction check"]
    pub fn require_lambda_license(self) -> Result<Self, LambdaAlgebraError> {
        if self.is_obstructed() {
            Ok(self)
        } else {
            Err(LambdaAlgebraError::NoObstruction)
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NonDestructiveExtensionCertificate {
    pub preserves_old_vertices: bool,
    pub preserves_old_edges: bool,
    pub records_tradeoff: bool,
}

impl NonDestructiveExtensionCertificate {
    pub fn new(
        preserves_old_vertices: bool,
        preserves_old_edges: bool,
        records_tradeoff: bool,
    ) -> Self {
        Self {
            preserves_old_vertices,
            preserves_old_edges,
            records_tradeoff,
        }
    }

    #[must_use = "ignoring the non-destructive result skips the extension gate"]
    pub fn require_non_destructive(self) -> Result<Self, LambdaAlgebraError> {
        if self.preserves_old_vertices && self.preserves_old_edges && self.records_tradeoff {
            Ok(self)
        } else {
            Err(LambdaAlgebraError::DestructiveLambdaExtension)
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FiniteLambdaStepCertificate {
    pub before: FiniteDiagnostic,
    pub after: FiniteDiagnostic,
    pub extension: NonDestructiveExtensionCertificate,
}

impl FiniteLambdaStepCertificate {
    pub fn new(
        before: FiniteDiagnostic,
        after: FiniteDiagnostic,
        extension: NonDestructiveExtensionCertificate,
    ) -> Self {
        Self {
            before,
            after,
            extension,
        }
    }

    /// Single-step PaperFOC005 gate: the `before` state must be obstructed
    /// (Lambda is licensed), the `after` state must be fully resolved
    /// (`Phi1 = Gamma2 = 0`), and the extension must be non-destructive.
    ///
    /// This is the terminal-step contract. Intermediate steps of a multi-step
    /// chain do NOT resolve to zero on their own — see [`Self::require_descent_step`].
    #[must_use = "ignoring the validity result skips the PaperFOC005 gate"]
    pub fn require_valid(self) -> Result<Self, LambdaAlgebraError> {
        self.before.require_lambda_license()?;
        if !self.after.is_resolved() {
            return Err(LambdaAlgebraError::LambdaDidNotResolve);
        }
        self.extension.require_non_destructive()?;
        Ok(self)
    }

    /// Intermediate-step PaperFOC005 gate for a multi-step descent: the `before`
    /// state must be obstructed (Lambda is licensed) and the extension must be
    /// non-destructive, but the `after` state may STILL be obstructed — it only
    /// has to be a monotone non-increase of the obstruction mass
    /// `Phi1 + Gamma2` (componentwise: `after.phi1 <= before.phi1` and
    /// `after.gamma2 <= before.gamma2`).
    ///
    /// This is the contract that makes a `>= 2`-step chain reachable: only the
    /// FINAL step must resolve to zero (via [`Self::require_valid`]); every
    /// earlier step only has to make non-destructive monotone progress.
    #[must_use = "ignoring the descent-step result skips the monotone-progress gate"]
    pub fn require_descent_step(self) -> Result<Self, LambdaAlgebraError> {
        self.before.require_lambda_license()?;
        if self.after.phi1 > self.before.phi1 || self.after.gamma2 > self.before.gamma2 {
            // An intermediate step that increases either obstruction coordinate
            // is not a descent: it manufactures obstruction the chain cannot
            // discharge. Reuse the observer-passivity error class.
            return Err(LambdaAlgebraError::ObserverPassivityViolation);
        }
        self.extension.require_non_destructive()?;
        Ok(self)
    }

    pub fn after_tension(self) -> Option<u64> {
        self.after.checked_tension()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteLambdaLedger {
    pub initial: FiniteDiagnostic,
    pub steps: Vec<FiniteLambdaStepCertificate>,
    pub terminal: FiniteDiagnostic,
}

impl FiniteLambdaLedger {
    pub fn new(
        initial: FiniteDiagnostic,
        steps: Vec<FiniteLambdaStepCertificate>,
        terminal: FiniteDiagnostic,
    ) -> Self {
        Self {
            initial,
            steps,
            terminal,
        }
    }

    /// Sequence-level PaperFOC005 preservation: a chained finite-Lambda descent.
    ///
    /// The chain is admissible iff
    /// - the head matches `initial` (`steps[0].before == initial`),
    /// - consecutive steps compose (`steps[i].after == steps[i+1].before`),
    /// - every NON-FINAL step is a non-destructive monotone descent
    ///   ([`FiniteLambdaStepCertificate::require_descent_step`]) — its `after`
    ///   may still be obstructed, it only has to make componentwise
    ///   non-increasing progress on `(Phi1, Gamma2)`,
    /// - the FINAL step is a fully-resolving single-step certificate
    ///   ([`FiniteLambdaStepCertificate::require_valid`]) — its `after` is
    ///   `Phi1 = Gamma2 = 0`, and
    /// - the tail matches `terminal` (`steps[last].after == terminal`).
    ///
    /// Because intermediate `after` states are allowed to stay obstructed, a
    /// genuine `>= 2`-step descent (e.g. `Phi1: 3 -> 2 -> 0`) is reachable: the
    /// success path is NOT contradictory. An empty ledger is admissible only
    /// when `initial == terminal` and `initial` is already resolved.
    fn verify_step_endpoints_and_chain(&self, last: usize) -> Result<(), LambdaAlgebraError> {
        // head: ledger.initial must equal the first step's before
        if self.steps[0].before != self.initial {
            return Err(LambdaAlgebraError::LambdaDidNotResolve);
        }
        // chain: consecutive steps must compose
        for window in self.steps.windows(2) {
            if window[0].after != window[1].before {
                return Err(LambdaAlgebraError::LambdaDidNotResolve);
            }
        }
        // tail: last step's after must equal ledger.terminal, and (because the
        // final require_valid enforces is_resolved on after) terminal is the
        // resolved endpoint.
        if self.steps[last].after != self.terminal {
            return Err(LambdaAlgebraError::LambdaDidNotResolve);
        }
        Ok(())
    }

    #[must_use = "ignoring the chaining result skips the sequence-level PaperFOC005 gate"]
    pub fn require_chained(&self) -> Result<&Self, LambdaAlgebraError> {
        if self.steps.is_empty() {
            // empty ledger is admissible only when initial == terminal
            // and initial is resolved (Phi1 = Gamma2 = 0)
            if self.initial != self.terminal || !self.initial.is_resolved() {
                return Err(LambdaAlgebraError::LambdaDidNotResolve);
            }
            return Ok(self);
        }
        let last = self.steps.len() - 1;
        // every NON-FINAL step is a monotone non-destructive descent; its
        // after may stay obstructed (only the final after must resolve).
        for step in &self.steps[..last] {
            step.require_descent_step()?;
        }
        // the FINAL step must drive the obstruction to zero.
        self.steps[last].require_valid()?;
        self.verify_step_endpoints_and_chain(last)?;
        Ok(self)
    }
}

/// Observer/trace shadows may report diagnostics but may not create a stronger obstruction.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ObserverPassivityCertificate {
    pub source: FiniteDiagnostic,
    pub observed: FiniteDiagnostic,
}

impl ObserverPassivityCertificate {
    pub fn new(source: FiniteDiagnostic, observed: FiniteDiagnostic) -> Self {
        Self { source, observed }
    }

    #[must_use = "ignoring the passivity result skips the observer gate"]
    pub fn require_passive(self) -> Result<Self, LambdaAlgebraError> {
        if self.observed.phi1 <= self.source.phi1 && self.observed.gamma2 <= self.source.gamma2 {
            Ok(self)
        } else {
            Err(LambdaAlgebraError::ObserverPassivityViolation)
        }
    }

    pub fn observed_diagnostic(self) -> FiniteDiagnostic {
        self.observed
    }
}

/// Pub010 inversion gate: a cross-term obstruction is typed only with an involution witness.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CrossTermObstructionCertificate {
    pub cross_term_l1: u64,
    pub has_involution: bool,
    pub repair_invariant: bool,
    pub non_coboundary: bool,
}

impl CrossTermObstructionCertificate {
    pub fn new(
        cross_term_l1: u64,
        has_involution: bool,
        repair_invariant: bool,
        non_coboundary: bool,
    ) -> Self {
        Self {
            cross_term_l1,
            has_involution,
            repair_invariant,
            non_coboundary,
        }
    }

    #[must_use = "ignoring the typed-obstruction result skips the cross-term gate"]
    pub fn require_typed_obstruction(self) -> Result<Self, LambdaAlgebraError> {
        if !self.has_involution {
            return Err(LambdaAlgebraError::MissingInvolutionWitness);
        }
        if !self.repair_invariant {
            return Err(LambdaAlgebraError::CrossTermNotRepairInvariant);
        }
        if !self.non_coboundary || self.cross_term_l1 == 0 {
            return Err(LambdaAlgebraError::CrossTermCoboundary);
        }
        Ok(self)
    }

    /// The typed cross-term observation remains distinct from Phi1/Gamma2.
    pub fn cross_term_diagnostic(self) -> Result<CrossTermDiagnostic, LambdaAlgebraError> {
        let certificate = self.require_typed_obstruction()?;
        Ok(CrossTermDiagnostic {
            declared_cross_term_l1: certificate.cross_term_l1,
        })
    }

    /// Compatibility ingress that refuses to relabel a cross-term scalar as
    /// canonical Phi1 or to assert Gamma2 = 0 without a declared C2 carrier.
    pub fn diagnostic(self) -> Result<FiniteDiagnostic, LambdaAlgebraError> {
        self.require_typed_obstruction()?;
        Err(LambdaAlgebraError::MissingProofCarryingCertificate)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CrossTermDiagnostic {
    pub declared_cross_term_l1: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct QuotientIrreducibilityCertificate {
    pub residual_l1: u64,
    pub dual_witness_l1: u64,
}

impl QuotientIrreducibilityCertificate {
    pub fn new(residual_l1: u64, dual_witness_l1: u64) -> Self {
        Self {
            residual_l1,
            dual_witness_l1,
        }
    }

    /// Check only the submitted scalar consistency conditions. Equality of
    /// two caller-supplied masses does not prove quotient irreducibility.
    #[must_use = "ignoring the result skips the declared-scalar consistency check"]
    pub fn require_irreducible(self) -> Result<Self, LambdaAlgebraError> {
        if self.residual_l1 == 0 {
            return Err(LambdaAlgebraError::GaugeArtifactOnly);
        }
        if self.residual_l1 != self.dual_witness_l1 {
            return Err(LambdaAlgebraError::QuotientCertificateMismatch);
        }
        Ok(self)
    }

    /// Report the submitted value only; it is not a verified quotient Phi1.
    pub fn declared_residual_l1(self) -> u64 {
        self.residual_l1
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NormalizedL1Weight {
    pub numerator: u64,
    pub denominator: u64,
}

/// PaperQF002 firewall: Born normalization only re-encodes declared positive L1 weights.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BornNormalizationCertificate {
    weights: Vec<u64>,
    total_l1: u64,
}

impl BornNormalizationCertificate {
    pub fn checked_from_l1_weights<I>(weights: I) -> Result<Self, LambdaAlgebraError>
    where
        I: IntoIterator<Item = u64>,
    {
        let weights: Vec<u64> = weights.into_iter().collect();
        let total_l1 = weights.iter().try_fold(0_u64, |acc, weight| {
            acc.checked_add(*weight)
                .ok_or(LambdaAlgebraError::CapacityOverflow)
        })?;
        if total_l1 == 0 {
            return Err(LambdaAlgebraError::ZeroL1WeightTotal);
        }
        Ok(Self { weights, total_l1 })
    }

    pub fn total_l1(&self) -> u64 {
        self.total_l1
    }

    pub fn weights(&self) -> &[u64] {
        &self.weights
    }

    pub fn normalized_weight(&self, index: usize) -> Option<NormalizedL1Weight> {
        self.weights
            .get(index)
            .copied()
            .map(|numerator| NormalizedL1Weight {
                numerator,
                denominator: self.total_l1,
            })
    }

    pub fn born_probability_from_squared_norm(&self, index: usize) -> Option<NormalizedL1Weight> {
        self.normalized_weight(index)
    }

    pub fn preserves_diagnostic(&self, diagnostic: FiniteDiagnostic) -> FiniteDiagnostic {
        diagnostic
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProposalAuthority {
    ExternalEvaluatorOnly,
}

/// PaperAF000 firewall: operators may propose algebraic shadows, not accept them.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperatorProposal<T> {
    pub proposal: T,
}

impl<T> OperatorProposal<T> {
    pub fn new(proposal: T) -> Self {
        Self { proposal }
    }

    pub fn authority(&self) -> ProposalAuthority {
        ProposalAuthority::ExternalEvaluatorOnly
    }
}

/// Paper015 firewall: AI lift proposals are admissible only as proof-carrying finite Lambda certificates.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProofCarryingAiProposal<T> {
    pub proposal: T,
    pub certificate: FiniteLambdaStepCertificate,
    pub proof_carrying: bool,
}

impl<T> ProofCarryingAiProposal<T> {
    pub fn new(
        proposal: T,
        certificate: FiniteLambdaStepCertificate,
        proof_carrying: bool,
    ) -> Self {
        Self {
            proposal,
            certificate,
            proof_carrying,
        }
    }

    #[must_use = "ignoring the proof-carrying result skips the AI-proposal gate"]
    pub fn require_proof_carrying(&self) -> Result<(), LambdaAlgebraError> {
        if !self.proof_carrying {
            return Err(LambdaAlgebraError::MissingProofCarryingCertificate);
        }
        self.certificate.require_valid()?;
        Ok(())
    }

    pub fn accepted_diagnostic(&self) -> Result<FiniteDiagnostic, LambdaAlgebraError> {
        self.require_proof_carrying()?;
        Ok(self.certificate.after)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DegreeTwoSupport {
    GraphOnly,
    DeclaredTwoCells,
}

impl DegreeTwoSupport {
    #[must_use = "ignoring the gamma2-visibility result skips the degree-two-support gate"]
    pub fn require_gamma2_visible(self) -> Result<Self, LambdaAlgebraError> {
        match self {
            Self::DeclaredTwoCells => Ok(self),
            Self::GraphOnly => Err(LambdaAlgebraError::MissingDegreeTwoSupport),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct XiTiePrecondition {
    pub left_primary: FiniteDiagnostic,
    pub right_primary: FiniteDiagnostic,
}

impl XiTiePrecondition {
    pub fn new(left_primary: FiniteDiagnostic, right_primary: FiniteDiagnostic) -> Self {
        Self {
            left_primary,
            right_primary,
        }
    }

    #[must_use = "ignoring the primary-tie result skips the xi-precondition gate"]
    pub fn require_primary_tie(self) -> Result<Self, LambdaAlgebraError> {
        if self.left_primary == self.right_primary {
            Ok(self)
        } else {
            Err(LambdaAlgebraError::PrimaryDiagnosticMismatch)
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct XiTieBreakCertificate {
    pub before_primary: FiniteDiagnostic,
    pub after_primary: FiniteDiagnostic,
    pub xi_before: u64,
    pub xi_after: u64,
}

impl XiTieBreakCertificate {
    pub fn new(
        before_primary: FiniteDiagnostic,
        after_primary: FiniteDiagnostic,
        xi_before: u64,
        xi_after: u64,
    ) -> Self {
        Self {
            before_primary,
            after_primary,
            xi_before,
            xi_after,
        }
    }

    #[must_use = "ignoring the tie-breaker result skips the xi-hierarchy gate"]
    pub fn require_tie_breaker(self) -> Result<Self, LambdaAlgebraError> {
        if self.before_primary != self.after_primary {
            return Err(LambdaAlgebraError::PrimaryDiagnosticMismatch);
        }
        if self.xi_after >= self.xi_before {
            return Err(LambdaAlgebraError::XiTieBreakerNotImproving);
        }
        Ok(self)
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RealizationBoundary {
    NeedsRealizationFunctor,
    RealizedFiniteCarrier,
}

impl RealizationBoundary {
    #[must_use = "ignoring the realization result skips the realized-carrier gate"]
    pub fn require_realized(self) -> Result<Self, LambdaAlgebraError> {
        match self {
            Self::RealizedFiniteCarrier => Ok(self),
            Self::NeedsRealizationFunctor => Err(LambdaAlgebraError::NeedsRealizationFunctor),
        }
    }
}

/// Stable cross-domain evidence id for the PaperFOC000c claim-packet boundary.
pub const PAPER000C_CLAIM_PACKET_EVIDENCE_ID: &str = "PAPER000C-CLAIM-PACKET-AUTHORITY-BOUNDARY";

/// Root authority status for representation-layer claim packets.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TerminalStatus {
    Certified,
    Repaired,
    Lifted,
    Stabilized,
    Refused,
    NoRule,
    BudgetUnknown,
}

impl TerminalStatus {
    pub fn is_authoritative(self) -> bool {
        matches!(
            self,
            Self::Certified | Self::Repaired | Self::Lifted | Self::Stabilized
        )
    }

    pub fn is_typed_refusal(self) -> bool {
        matches!(self, Self::Refused | Self::NoRule | Self::BudgetUnknown)
    }
}

/// PaperFOC000c boundary: representation-layer material earns authority only by descent.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClaimPacket<T> {
    pub representation: T,
    pub descends_to_primitive_difference: bool,
    pub descends_to_structure: bool,
    pub typed_refusal: bool,
    pub terminal_status: TerminalStatus,
}

impl<T> ClaimPacket<T> {
    pub fn new(
        representation: T,
        descends_to_primitive_difference: bool,
        descends_to_structure: bool,
        typed_refusal: bool,
        terminal_status: TerminalStatus,
    ) -> Self {
        Self {
            representation,
            descends_to_primitive_difference,
            descends_to_structure,
            typed_refusal,
            terminal_status,
        }
    }

    pub fn descends_to_real0(&self) -> bool {
        self.descends_to_primitive_difference || self.descends_to_structure
    }

    pub fn is_terminalized(&self) -> bool {
        self.descends_to_real0() || self.typed_refusal
    }

    pub fn has_authority(&self) -> bool {
        self.descends_to_real0() && self.terminal_status.is_authoritative()
    }

    #[must_use = "ignoring the terminalization result skips the claim-packet gate"]
    pub fn require_terminalized(&self) -> Result<&Self, LambdaAlgebraError> {
        if self.is_terminalized() {
            Ok(self)
        } else {
            Err(LambdaAlgebraError::RepresentationLayerOnlyClaim)
        }
    }

    #[must_use = "ignoring the authority result skips the descent + status gate"]
    pub fn require_authority(&self) -> Result<&Self, LambdaAlgebraError> {
        if !self.descends_to_real0() {
            return Err(LambdaAlgebraError::RepresentationLayerOnlyClaim);
        }
        if !self.terminal_status.is_authoritative() {
            return Err(LambdaAlgebraError::NonAuthoritativeTerminalStatus);
        }
        Ok(self)
    }
}

impl<F: PartialEq> FaceLambda<F> {
    pub fn new(face: F, capacity: i64) -> Self {
        Self { face, capacity }
    }

    pub fn checked_merge(self, rhs: Self) -> Result<Self, LambdaAlgebraError> {
        if self.face != rhs.face {
            return Err(LambdaAlgebraError::DifferentFace);
        }

        let capacity = self
            .capacity
            .checked_add(rhs.capacity)
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;

        Ok(Self {
            face: self.face,
            capacity,
        })
    }
}

impl<F> FaceLambda<F> {
    pub fn checked_reverse(self) -> Result<Self, LambdaAlgebraError> {
        let capacity = self
            .capacity
            .checked_neg()
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;

        Ok(Self {
            face: self.face,
            capacity,
        })
    }

    pub fn checked_scale(self, scalar: i64) -> Result<Self, LambdaAlgebraError> {
        let capacity = self
            .capacity
            .checked_mul(scalar)
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;

        Ok(Self {
            face: self.face,
            capacity,
        })
    }
}

impl<V: Clone + Ord> FaceLambda<OrientedTriangle<V>> {
    pub fn checked_boundary(&self) -> Result<Boundary1<V>, LambdaAlgebraError> {
        let mut boundary = Boundary1::new();
        let negative_capacity = self
            .capacity
            .checked_neg()
            .ok_or(LambdaAlgebraError::CapacityOverflow)?;
        boundary.checked_add_term(self.face.b.clone(), self.face.c.clone(), self.capacity)?;
        boundary.checked_add_term(self.face.a.clone(), self.face.c.clone(), negative_capacity)?;
        boundary.checked_add_term(self.face.a.clone(), self.face.b.clone(), self.capacity)?;
        Ok(boundary)
    }
}

/// 1. Merge (Addition)
impl<F: PartialEq> Add for FaceLambda<F> {
    type Output = Self;

    /// # Panics
    ///
    /// Panics on a different-face merge or a capacity overflow. Use the
    /// non-panicking [`FaceLambda::checked_merge`] when either is possible.
    fn add(self, rhs: Self) -> Self::Output {
        self.checked_merge(rhs)
            .checked_invariant_0e26b98f("FaceLambda Add failed: invariant violation (different face or overflow)")
    }
}

/// 2. Reverse (Negation)
impl<F> Neg for FaceLambda<F> {
    type Output = Self;

    /// # Panics
    ///
    /// Panics on a capacity overflow (`i64::MIN` negation). Use the
    /// non-panicking [`FaceLambda::checked_reverse`] when that is possible.
    fn neg(self) -> Self::Output {
        self.checked_reverse()
            .checked_invariant_0e26b98f("FaceLambda Neg failed: invariant violation (capacity overflow)")
    }
}

/// 3. Scale (Scalar Multiplication)
impl<F> Mul<i64> for FaceLambda<F> {
    type Output = Self;

    /// # Panics
    ///
    /// Panics on a capacity overflow. Use the non-panicking
    /// [`FaceLambda::checked_scale`] when that is possible.
    fn mul(self, scalar: i64) -> Self::Output {
        self.checked_scale(scalar)
            .checked_invariant_0e26b98f("FaceLambda Mul failed: invariant violation (capacity overflow)")
    }
}

// Commutative scalar multiplication
impl<F> Mul<FaceLambda<F>> for i64 {
    type Output = FaceLambda<F>;

    /// # Panics
    ///
    /// Panics on a capacity overflow (delegates to `FaceLambda * i64`). Use
    /// [`FaceLambda::checked_scale`] when that is possible.
    fn mul(self, lambda: FaceLambda<F>) -> Self::Output {
        lambda * self
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_capacity_merge_linearity() {
        let l1 = FaceLambda::new("A_B_C", 5);
        let l2 = FaceLambda::new("A_B_C", 3);

        let merged = l1 + l2;

        assert_eq!(merged.capacity, l1.capacity + l2.capacity);
    }

    #[test]
    fn test_capacity_reverse_linearity() {
        let l = FaceLambda::new("A_B_C", 5);
        let reversed = -l;

        assert_eq!(reversed.capacity, -l.capacity);
    }

    #[test]
    fn test_capacity_scale_linearity() {
        let l = FaceLambda::new("A_B_C", 5);
        let scale = 4;
        let scaled = l * scale;

        assert_eq!(scaled.capacity, scale * l.capacity);
    }

    #[test]
    #[should_panic(expected = "invariant violation")]
    fn test_merge_rejects_different_faces() {
        let l1 = FaceLambda::new("A_B_C", 5);
        let l2 = FaceLambda::new("A_B_D", 3);
        let _ = l1 + l2;
    }

    #[test]
    #[should_panic(expected = "invariant violation")]
    fn test_add_overflow_panics_consistently() {
        let l1 = FaceLambda::new("A_B_C", i64::MAX);
        let l2 = FaceLambda::new("A_B_C", 1);
        let _ = l1 + l2;
    }

    #[test]
    #[should_panic(expected = "invariant violation")]
    fn test_neg_i64_min_panics_consistently() {
        let l = FaceLambda::new("A_B_C", i64::MIN);
        let _ = -l;
    }

    #[test]
    #[should_panic(expected = "invariant violation")]
    fn test_mul_overflow_panics_consistently() {
        let l = FaceLambda::new("A_B_C", i64::MAX);
        let _ = l * 2;
    }

    #[test]
    fn test_boundary_of_lambda_is_c1_shadow() {
        let lambda = FaceLambda::new(OrientedTriangle::new("A", "B", "C"), 5);
        let boundary = lambda.checked_boundary().unwrap();

        assert_eq!(boundary.coefficient("B", "C"), 5);
        assert_eq!(boundary.coefficient("A", "C"), -5);
        assert_eq!(boundary.coefficient("A", "B"), 5);
    }

    #[test]
    fn test_adjacent_lambda_boundaries_merge_shared_edge() {
        let lambda_1 = FaceLambda::new(OrientedTriangle::new("A", "B", "C"), 5);
        let lambda_2 = FaceLambda::new(OrientedTriangle::new("C", "B", "D"), 3);

        let merged = lambda_1
            .checked_boundary()
            .unwrap()
            .checked_merge(&lambda_2.checked_boundary().unwrap())
            .unwrap();

        assert_eq!(merged.coefficient("B", "C"), 2);
    }

    #[test]
    fn test_boundary_reverse_and_scale_are_checked() {
        let lambda = FaceLambda::new(OrientedTriangle::new("A", "B", "C"), 5);
        let boundary = lambda.checked_boundary().unwrap();

        assert_eq!(
            boundary.checked_reverse().unwrap().coefficient("B", "C"),
            -5
        );
        assert_eq!(boundary.checked_scale(4).unwrap().coefficient("B", "C"), 20);
    }

    #[test]
    fn test_boundary_i64_min_refuses_typed_overflow() {
        let lambda = FaceLambda::new(OrientedTriangle::new("A", "B", "C"), i64::MIN);

        assert_eq!(
            lambda.checked_boundary(),
            Err(LambdaAlgebraError::CapacityOverflow)
        );
    }

    #[test]
    fn test_set_term_rejects_storing_i64_min_keeping_coefficient_total() {
        // The reverse-orientation read of a stored i64::MIN would overflow the
        // sign multiply, which is the only way `coefficient` could panic. The
        // write paths refuse to store i64::MIN, so the signed read stays total.
        let mut boundary = Cochain1::new();
        // Canonical edge with target < source so canonical_edge negates: storing
        // +i64::MIN on ("B","A") would persist i64::MIN under the canonical key.
        assert_eq!(
            boundary.checked_set_term("A", "B", i64::MIN),
            Err(LambdaAlgebraError::CapacityOverflow)
        );
        assert_eq!(boundary.coefficients().len(), 0);

        // checked_add_term reaching i64::MIN is also refused.
        let mut acc = Cochain1::new();
        acc.checked_set_term("A", "B", i64::MIN + 1).unwrap();
        assert_eq!(
            acc.checked_add_term("A", "B", -1),
            Err(LambdaAlgebraError::CapacityOverflow)
        );

        // A maximal-magnitude legal store still reads back totally (no panic).
        let mut legal = Cochain1::new();
        legal.checked_set_term("A", "B", i64::MIN + 1).unwrap();
        // coefficient is total: this call must not panic.
        assert_eq!(legal.coefficient("A", "B"), i64::MIN + 1);
        assert_eq!(legal.coefficient("B", "A"), -(i64::MIN + 1));
    }

    #[test]
    fn test_primitive_difference_builds_c1_from_c0() {
        let potential = Cochain0::from_values([("A", 2), ("B", 7)]);
        let difference = potential
            .checked_primitive_difference([("A", "B"), ("B", "A")])
            .unwrap();

        assert_eq!(difference.coefficient("A", "B"), 5);
        assert_eq!(difference.coefficient("B", "A"), -5);
    }

    #[test]
    fn test_exact_primitive_difference_has_zero_triangle_closure() {
        let face = OrientedTriangle::new("A", "B", "C");
        let potential = Cochain0::from_values([("A", 1), ("B", 4), ("C", 8)]);
        let difference = potential
            .checked_primitive_difference([("A", "B"), ("B", "C"), ("C", "A")])
            .unwrap();

        assert_eq!(difference.checked_closure_defect(&face), Ok(0));
        assert_eq!(difference.checked_gamma2(&face), Ok(0));
    }

    #[test]
    fn test_l1_tension_sums_absolute_edge_magnitudes() {
        let potential = Cochain0::from_values([("A", 1), ("B", 4), ("C", 8)]);
        let difference = potential
            .checked_primitive_difference([("A", "B"), ("B", "C"), ("C", "A")])
            .unwrap();

        assert_eq!(difference.checked_l1_tension(), Ok(14));
    }

    #[test]
    fn test_finite_window_scan_builds_local_c0_c1_c2_diagnostic() {
        let window = FiniteWindow::new(
            vec!["A", "B", "C"],
            vec![("A", "B"), ("B", "C"), ("C", "A")],
            vec![OrientedTriangle::new("A", "B", "C")],
        );
        let potential = Cochain0::from_values([("A", 1), ("B", 4), ("C", 8)]);

        let scan = window.checked_scan(&potential).unwrap();

        assert_eq!(scan.c1.coefficient("A", "B"), 3);
        assert_eq!(scan.l1_tension, 14);
        assert_eq!(scan.face_gamma2, vec![0]);
        assert_eq!(scan.gamma2_total, 0);
    }

    #[test]
    fn test_finite_window_scan_c1_detects_local_closure_defect() {
        let window = FiniteWindow::new(
            vec!["A", "B", "C"],
            vec![("A", "B"), ("B", "C"), ("C", "A")],
            vec![OrientedTriangle::new("A", "B", "C")],
        );
        let mut residual = Cochain1::new();
        residual.checked_set_term("A", "B", 2).unwrap();
        residual.checked_set_term("B", "C", 3).unwrap();
        residual.checked_set_term("C", "A", 4).unwrap();

        let scan = window.checked_scan_c1(&residual).unwrap();

        assert_eq!(scan.l1_tension, 9);
        assert_eq!(scan.face_gamma2, vec![9]);
        assert_eq!(scan.gamma2_total, 9);
    }

    #[test]
    fn test_finite_window_scan_refuses_gauge_only_quotient_diagnostic() {
        let window = FiniteWindow::new(
            vec!["A", "B", "C"],
            vec![("A", "B"), ("B", "C"), ("C", "A")],
            vec![OrientedTriangle::new("A", "B", "C")],
        );
        let potential = Cochain0::from_values([("A", 1), ("B", 4), ("C", 8)]);
        let scan = window.checked_scan(&potential).unwrap();

        assert_eq!(
            scan.checked_diagnostic_from_quotient(QuotientIrreducibilityCertificate::new(0, 0)),
            Err(LambdaAlgebraError::GaugeArtifactOnly)
        );
    }

    #[test]
    fn test_finite_window_scan_refuses_unverified_quotient_phi1() {
        let window = FiniteWindow::new(
            vec!["A", "B", "C"],
            vec![("A", "B"), ("B", "C"), ("C", "A")],
            vec![OrientedTriangle::new("A", "B", "C")],
        );
        let mut residual = Cochain1::new();
        residual.checked_set_term("A", "B", 2).unwrap();
        residual.checked_set_term("B", "C", 3).unwrap();
        residual.checked_set_term("C", "A", 4).unwrap();
        let scan = window.checked_scan_c1(&residual).unwrap();
        assert_eq!(scan.gamma2_total, 9);

        assert_eq!(
            scan.checked_diagnostic_from_quotient(QuotientIrreducibilityCertificate::new(7, 7)),
            Err(LambdaAlgebraError::MissingProofCarryingCertificate)
        );
    }

    #[test]
    fn test_closure_defect_is_invariant_under_exact_gauge_shift() {
        let face = OrientedTriangle::new("A", "B", "C");
        let mut residual = Cochain1::new();
        residual.checked_set_term("A", "B", 2).unwrap();
        residual.checked_set_term("B", "C", 3).unwrap();
        residual.checked_set_term("C", "A", 4).unwrap();

        let gauge = Cochain0::from_values([("A", 10), ("B", 15), ("C", 11)]);
        let exact_shift = gauge
            .checked_primitive_difference([("A", "B"), ("B", "C"), ("C", "A")])
            .unwrap();
        let shifted = residual.checked_merge(&exact_shift).unwrap();

        assert_eq!(residual.checked_closure_defect(&face), Ok(9));
        assert_eq!(shifted.checked_closure_defect(&face), Ok(9));
        assert_eq!(shifted.checked_gamma2(&face), Ok(9));
    }

    #[test]
    fn test_primitive_difference_overflow_refuses_typed() {
        let potential = Cochain0::from_values([("A", i64::MAX), ("B", i64::MIN)]);

        assert_eq!(
            potential.checked_primitive_difference([("A", "B")]),
            Err(LambdaAlgebraError::CapacityOverflow)
        );
    }
    #[test]
    fn test_zero_quotient_certificate_is_gauge_artifact_only() {
        let certificate = QuotientIrreducibilityCertificate::new(0, 0);

        assert_eq!(
            certificate.require_irreducible(),
            Err(LambdaAlgebraError::GaugeArtifactOnly)
        );
    }

    #[test]
    fn test_quotient_certificate_requires_dual_saturation() {
        let certificate = QuotientIrreducibilityCertificate::new(7, 6);

        assert_eq!(
            certificate.require_irreducible(),
            Err(LambdaAlgebraError::QuotientCertificateMismatch)
        );
    }

    #[test]
    fn test_scalar_quotient_receipt_cannot_mint_phi1_diagnostic() {
        let certificate = QuotientIrreducibilityCertificate::new(7, 7);
        assert_eq!(certificate.declared_residual_l1(), 7);
        assert_eq!(
            FiniteDiagnostic::checked_from_quotient_certificate(certificate, 2),
            Err(LambdaAlgebraError::MissingProofCarryingCertificate)
        );
        assert_eq!(
            FiniteDiagnostic::new(7, 2).provenance(),
            FiniteDiagnosticProvenance::UnverifiedScalarClaim
        );
    }
    #[test]
    fn test_resolved_diagnostic_refuses_lambda_license() {
        let diagnostic = FiniteDiagnostic::new(0, 0);

        assert!(diagnostic.is_resolved());
        assert_eq!(
            diagnostic.require_lambda_license(),
            Err(LambdaAlgebraError::NoObstruction)
        );
    }

    #[test]
    fn test_positive_diagnostic_licenses_lambda_without_authority() {
        let diagnostic = FiniteDiagnostic::new(1, 0);

        assert_eq!(diagnostic.checked_tension(), Some(1));
        assert_eq!(diagnostic.require_lambda_license(), Ok(diagnostic));
    }
    #[test]
    fn test_lambda_step_certificate_requires_positive_before_obstruction() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(0, 0),
            FiniteDiagnostic::new(0, 0),
            NonDestructiveExtensionCertificate::new(true, true, true),
        );

        assert_eq!(
            certificate.require_valid(),
            Err(LambdaAlgebraError::NoObstruction)
        );
    }

    #[test]
    fn test_lambda_step_certificate_requires_resolved_after_diagnostic() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 0),
            FiniteDiagnostic::new(1, 0),
            NonDestructiveExtensionCertificate::new(true, true, true),
        );

        assert_eq!(
            certificate.require_valid(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_lambda_step_certificate_requires_non_destructive_extension() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 0),
            FiniteDiagnostic::new(0, 0),
            NonDestructiveExtensionCertificate::new(true, false, true),
        );

        assert_eq!(
            certificate.require_valid(),
            Err(LambdaAlgebraError::DestructiveLambdaExtension)
        );
    }

    #[test]
    fn test_lambda_step_certificate_zeroes_tension_without_destruction() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 2),
            FiniteDiagnostic::new(0, 0),
            NonDestructiveExtensionCertificate::new(true, true, true),
        );
        let valid = certificate.require_valid().unwrap();

        assert_eq!(valid.after_tension(), Some(0));
    }

    #[test]
    fn test_observer_passivity_refuses_created_phi1() {
        let certificate = ObserverPassivityCertificate::new(
            FiniteDiagnostic::new(1, 3),
            FiniteDiagnostic::new(2, 3),
        );

        assert_eq!(
            certificate.require_passive(),
            Err(LambdaAlgebraError::ObserverPassivityViolation)
        );
    }

    #[test]
    fn test_observer_passivity_refuses_created_gamma2() {
        let certificate = ObserverPassivityCertificate::new(
            FiniteDiagnostic::new(2, 3),
            FiniteDiagnostic::new(2, 4),
        );

        assert_eq!(
            certificate.require_passive(),
            Err(LambdaAlgebraError::ObserverPassivityViolation)
        );
    }

    #[test]
    fn test_observer_passivity_accepts_componentwise_nonincrease() {
        let observed = FiniteDiagnostic::new(2, 3);
        let certificate = ObserverPassivityCertificate::new(FiniteDiagnostic::new(5, 3), observed);
        let passive = certificate.require_passive().unwrap();

        assert_eq!(passive.observed_diagnostic(), observed);
    }

    #[test]
    fn test_cross_term_requires_involution_witness() {
        let certificate = CrossTermObstructionCertificate::new(5, false, true, true);

        assert_eq!(
            certificate.require_typed_obstruction(),
            Err(LambdaAlgebraError::MissingInvolutionWitness)
        );
    }

    #[test]
    fn test_cross_term_requires_repair_invariance() {
        let certificate = CrossTermObstructionCertificate::new(5, true, false, true);

        assert_eq!(
            certificate.require_typed_obstruction(),
            Err(LambdaAlgebraError::CrossTermNotRepairInvariant)
        );
    }

    #[test]
    fn test_cross_term_requires_nonzero_non_coboundary() {
        let coboundary = CrossTermObstructionCertificate::new(5, true, true, false);
        let zero = CrossTermObstructionCertificate::new(0, true, true, true);

        assert_eq!(
            coboundary.require_typed_obstruction(),
            Err(LambdaAlgebraError::CrossTermCoboundary)
        );
        assert_eq!(
            zero.require_typed_obstruction(),
            Err(LambdaAlgebraError::CrossTermCoboundary)
        );
    }

    #[test]
    fn test_cross_term_observation_cannot_mint_primary_functionals() {
        let certificate = CrossTermObstructionCertificate::new(8, true, true, true);

        assert_eq!(
            certificate.cross_term_diagnostic(),
            Ok(CrossTermDiagnostic {
                declared_cross_term_l1: 8
            })
        );
        assert_eq!(
            certificate.diagnostic(),
            Err(LambdaAlgebraError::MissingProofCarryingCertificate)
        );
    }

    #[test]
    fn test_born_normalization_refuses_zero_l1_total() {
        assert_eq!(
            BornNormalizationCertificate::checked_from_l1_weights([0, 0, 0]),
            Err(LambdaAlgebraError::ZeroL1WeightTotal)
        );
    }

    #[test]
    fn test_born_probability_redundant_with_l1_normalization() {
        let certificate = BornNormalizationCertificate::checked_from_l1_weights([2, 3, 5]).unwrap();

        assert_eq!(certificate.total_l1(), 10);
        assert_eq!(
            certificate.normalized_weight(1),
            Some(NormalizedL1Weight {
                numerator: 3,
                denominator: 10,
            })
        );
        assert_eq!(
            certificate.born_probability_from_squared_norm(1),
            certificate.normalized_weight(1)
        );
    }

    #[test]
    fn test_born_normalization_preserves_obstruction_diagnostic() {
        let certificate = BornNormalizationCertificate::checked_from_l1_weights([2, 3, 5]).unwrap();
        let diagnostic = FiniteDiagnostic::new(7, 2);

        assert_eq!(certificate.preserves_diagnostic(diagnostic), diagnostic);
    }
    #[test]
    fn test_operator_proposal_has_external_evaluator_only_authority() {
        let proposal = OperatorProposal::new("candidate-boundary-shadow");

        assert_eq!(
            proposal.authority(),
            ProposalAuthority::ExternalEvaluatorOnly
        );
    }

    #[test]
    fn test_ai_proposal_requires_proof_carrying_certificate() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 0),
            FiniteDiagnostic::new(0, 0),
            NonDestructiveExtensionCertificate::new(true, true, true),
        );
        let proposal = ProofCarryingAiProposal::new("candidate-lift", certificate, false);

        assert_eq!(
            proposal.require_proof_carrying(),
            Err(LambdaAlgebraError::MissingProofCarryingCertificate)
        );
    }

    #[test]
    fn test_ai_proposal_delegates_to_finite_lambda_certificate() {
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 0),
            FiniteDiagnostic::new(1, 0),
            NonDestructiveExtensionCertificate::new(true, true, true),
        );
        let proposal = ProofCarryingAiProposal::new("candidate-lift", certificate, true);

        assert_eq!(
            proposal.require_proof_carrying(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_ai_proposal_accepts_only_verified_finite_diagnostic() {
        let after = FiniteDiagnostic::new(0, 0);
        let certificate = FiniteLambdaStepCertificate::new(
            FiniteDiagnostic::new(1, 2),
            after,
            NonDestructiveExtensionCertificate::new(true, true, true),
        );
        let proposal = ProofCarryingAiProposal::new("candidate-lift", certificate, true);

        assert_eq!(proposal.accepted_diagnostic(), Ok(after));
    }

    #[test]
    fn test_gamma2_visibility_requires_declared_c2_support() {
        assert_eq!(
            DegreeTwoSupport::GraphOnly.require_gamma2_visible(),
            Err(LambdaAlgebraError::MissingDegreeTwoSupport)
        );
        assert_eq!(
            DegreeTwoSupport::DeclaredTwoCells.require_gamma2_visible(),
            Ok(DegreeTwoSupport::DeclaredTwoCells)
        );
    }

    #[test]
    fn test_xi_tie_precondition_requires_primary_diagnostic_tie() {
        let left = FiniteDiagnostic::new(1, 0);
        let right = FiniteDiagnostic::new(1, 1);
        let tied = XiTiePrecondition::new(left, left);
        let mismatched = XiTiePrecondition::new(left, right);

        assert_eq!(tied.require_primary_tie(), Ok(tied));
        assert_eq!(
            mismatched.require_primary_tie(),
            Err(LambdaAlgebraError::PrimaryDiagnosticMismatch)
        );
    }

    #[test]
    fn test_xi_hierarchy_refuses_primary_worsening_even_if_xi_improves() {
        let before = FiniteDiagnostic::new(1, 0);
        let after = FiniteDiagnostic::new(2, 0);
        let certificate = XiTieBreakCertificate::new(before, after, 10, 1);

        assert_eq!(
            certificate.require_tie_breaker(),
            Err(LambdaAlgebraError::PrimaryDiagnosticMismatch)
        );
    }

    #[test]
    fn test_xi_hierarchy_requires_strict_xi_improvement_under_primary_tie() {
        let primary = FiniteDiagnostic::new(1, 0);
        let certificate = XiTieBreakCertificate::new(primary, primary, 5, 5);

        assert_eq!(
            certificate.require_tie_breaker(),
            Err(LambdaAlgebraError::XiTieBreakerNotImproving)
        );
    }

    #[test]
    fn test_xi_hierarchy_accepts_strict_tie_break_only_after_primary_tie() {
        let primary = FiniteDiagnostic::new(1, 0);
        let certificate = XiTieBreakCertificate::new(primary, primary, 5, 4);

        assert_eq!(certificate.require_tie_breaker(), Ok(certificate));
    }
    #[test]
    fn test_trace_validation_requires_realized_finite_carrier() {
        assert_eq!(
            RealizationBoundary::NeedsRealizationFunctor.require_realized(),
            Err(LambdaAlgebraError::NeedsRealizationFunctor)
        );
        assert_eq!(
            RealizationBoundary::RealizedFiniteCarrier.require_realized(),
            Ok(RealizationBoundary::RealizedFiniteCarrier)
        );
    }

    #[test]
    fn test_claim_packet_evidence_id_is_stable() {
        assert_eq!(
            PAPER000C_CLAIM_PACKET_EVIDENCE_ID,
            "PAPER000C-CLAIM-PACKET-AUTHORITY-BOUNDARY"
        );
    }
    #[test]
    fn test_representation_only_claim_has_no_authority() {
        let packet = ClaimPacket::new(
            "unlicensed-mark",
            false,
            false,
            false,
            TerminalStatus::Certified,
        );

        assert!(!packet.descends_to_real0());
        assert!(!packet.is_terminalized());
        assert_eq!(
            packet.require_authority(),
            Err(LambdaAlgebraError::RepresentationLayerOnlyClaim)
        );
    }

    #[test]
    fn test_typed_refusal_terminalizes_without_authority() {
        let packet = ClaimPacket::new("refused-mark", false, false, true, TerminalStatus::Refused);

        assert_eq!(packet.require_terminalized(), Ok(&packet));
        assert!(!packet.has_authority());
        assert_eq!(
            packet.require_authority(),
            Err(LambdaAlgebraError::RepresentationLayerOnlyClaim)
        );
    }

    #[test]
    fn test_authority_requires_descent_and_authoritative_status() {
        let packet = ClaimPacket::new(
            "descended-mark",
            true,
            false,
            false,
            TerminalStatus::Certified,
        );
        let refused = ClaimPacket::new(
            "descended-but-refused",
            true,
            false,
            true,
            TerminalStatus::Refused,
        );

        assert_eq!(packet.require_authority(), Ok(&packet));
        assert_eq!(
            refused.require_authority(),
            Err(LambdaAlgebraError::NonAuthoritativeTerminalStatus)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_new_stores_fields() {
        let initial = FiniteDiagnostic::new(2, 1);
        let terminal = FiniteDiagnostic::new(0, 0);
        let step = FiniteLambdaStepCertificate::new(
            initial,
            terminal,
            NonDestructiveExtensionCertificate::new(true, true, true),
        );

        let ledger = FiniteLambdaLedger::new(initial, vec![step], terminal);

        assert_eq!(ledger.initial, initial);
        assert_eq!(ledger.steps, vec![step]);
        assert_eq!(ledger.terminal, terminal);
    }

    #[test]
    fn test_finite_lambda_ledger_chains_consecutive_steps() {
        let initial = FiniteDiagnostic::new(5, 5);
        let terminal = FiniteDiagnostic::new(0, 0);

        let ext1 = NonDestructiveExtensionCertificate::new(true, true, true);

        let step1 = FiniteLambdaStepCertificate::new(initial, terminal, ext1);

        let ledger = FiniteLambdaLedger::new(initial, vec![step1], terminal);
        assert_eq!(ledger.require_chained(), Ok(&ledger));
    }

    #[test]
    fn test_finite_lambda_ledger_two_step_descent_phi1_3_2_0_is_ok() {
        // L5 closure: a genuine, REACHABLE >= 2-step chain returning Ok.
        // Phi1 descends 3 -> 2 -> 0 across two steps. The FIRST step's `after`
        // (2, 0) is STILL OBSTRUCTED (this is exactly the case the old
        // every-step-resolves contract made unreachable); only the SECOND
        // (final) step resolves to (0, 0).
        let initial = FiniteDiagnostic::new(3, 0);
        let mid = FiniteDiagnostic::new(2, 0);
        let terminal = FiniteDiagnostic::new(0, 0);

        let ext = NonDestructiveExtensionCertificate::new(true, true, true);

        // intermediate step: 3 -> 2 (after still obstructed, monotone descent)
        let step1 = FiniteLambdaStepCertificate::new(initial, mid, ext);
        // final step: 2 -> 0 (resolves)
        let step2 = FiniteLambdaStepCertificate::new(mid, terminal, ext);

        // Precondition: the intermediate after is obstructed (the unreachable
        // case under the old semantics).
        assert!(mid.is_obstructed());

        let ledger = FiniteLambdaLedger::new(initial, vec![step1, step2], terminal);
        assert_eq!(ledger.require_chained(), Ok(&ledger));
    }

    #[test]
    fn test_finite_lambda_ledger_three_step_descent_phi1_gamma2_is_ok() {
        // Three-step descent driving both coordinates down monotonically:
        // (2,2) -> (2,1) -> (1,0) -> (0,0). Two obstructed intermediate
        // `after`s, only the final step resolves.
        let s0 = FiniteDiagnostic::new(2, 2);
        let s1 = FiniteDiagnostic::new(2, 1);
        let s2 = FiniteDiagnostic::new(1, 0);
        let s3 = FiniteDiagnostic::new(0, 0);
        let ext = NonDestructiveExtensionCertificate::new(true, true, true);

        let ledger = FiniteLambdaLedger::new(
            s0,
            vec![
                FiniteLambdaStepCertificate::new(s0, s1, ext),
                FiniteLambdaStepCertificate::new(s1, s2, ext),
                FiniteLambdaStepCertificate::new(s2, s3, ext),
            ],
            s3,
        );
        assert_eq!(ledger.require_chained(), Ok(&ledger));
    }

    #[test]
    fn test_finite_lambda_ledger_refuses_intermediate_obstruction_increase() {
        // Negative control for the descent gate: an intermediate step whose
        // `after` INCREASES an obstruction coordinate (1 -> 2 on Phi1) is not a
        // monotone descent and must be refused, even though the final step
        // would resolve. This is what keeps `require_descent_step` honest.
        let initial = FiniteDiagnostic::new(1, 0);
        let mid = FiniteDiagnostic::new(2, 0); // increases Phi1 — illegal
        let terminal = FiniteDiagnostic::new(0, 0);
        let ext = NonDestructiveExtensionCertificate::new(true, true, true);

        let step1 = FiniteLambdaStepCertificate::new(initial, mid, ext);
        let step2 = FiniteLambdaStepCertificate::new(mid, terminal, ext);

        let ledger = FiniteLambdaLedger::new(initial, vec![step1, step2], terminal);
        assert_eq!(
            ledger.require_chained(),
            Err(LambdaAlgebraError::ObserverPassivityViolation)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_refuses_final_step_not_resolved() {
        // The FINAL step must still resolve to (0, 0): a chain whose last step
        // ends obstructed is refused.
        let initial = FiniteDiagnostic::new(3, 0);
        let mid = FiniteDiagnostic::new(2, 0);
        let unresolved = FiniteDiagnostic::new(1, 0);
        let ext = NonDestructiveExtensionCertificate::new(true, true, true);

        let step1 = FiniteLambdaStepCertificate::new(initial, mid, ext);
        let step2 = FiniteLambdaStepCertificate::new(mid, unresolved, ext);

        let ledger = FiniteLambdaLedger::new(initial, vec![step1, step2], unresolved);
        assert_eq!(
            ledger.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_refuses_broken_chain() {
        let initial = FiniteDiagnostic::new(5, 5);
        let mid1 = FiniteDiagnostic::new(0, 0);
        let mid2 = FiniteDiagnostic::new(1, 0);
        let terminal = FiniteDiagnostic::new(0, 0);

        let ext1 = NonDestructiveExtensionCertificate::new(true, true, true);
        let ext2 = NonDestructiveExtensionCertificate::new(true, true, true);

        let step1 = FiniteLambdaStepCertificate::new(initial, mid1, ext1);
        // Step 2 before doesn't match step 1 after
        let step2 = FiniteLambdaStepCertificate::new(mid2, terminal, ext2);

        let ledger = FiniteLambdaLedger::new(initial, vec![step1, step2], terminal);
        assert_eq!(
            ledger.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_refuses_head_mismatch() {
        let initial = FiniteDiagnostic::new(5, 5);
        let wrong_head = FiniteDiagnostic::new(4, 5);
        let terminal = FiniteDiagnostic::new(0, 0);

        let ext1 = NonDestructiveExtensionCertificate::new(true, true, true);

        let step1 = FiniteLambdaStepCertificate::new(wrong_head, terminal, ext1);

        let ledger = FiniteLambdaLedger::new(initial, vec![step1], terminal);
        assert_eq!(
            ledger.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_empty_requires_resolved_endpoints_equal() {
        let resolved = FiniteDiagnostic::new(0, 0);
        let ledger1 = FiniteLambdaLedger::new(resolved, vec![], resolved);
        assert_eq!(ledger1.require_chained(), Ok(&ledger1));

        let obstructed = FiniteDiagnostic::new(1, 0);
        let ledger2 = FiniteLambdaLedger::new(obstructed, vec![], obstructed);
        assert_eq!(
            ledger2.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );

        let resolved2 = FiniteDiagnostic::new(0, 0);
        let obstructed2 = FiniteDiagnostic::new(1, 0);
        let ledger3 = FiniteLambdaLedger::new(resolved2, vec![], obstructed2);
        assert_eq!(
            ledger3.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }

    #[test]
    fn test_finite_lambda_ledger_empty_refuses_unresolved_endpoint() {
        let unresolved = FiniteDiagnostic::new(1, 0);
        let ledger = FiniteLambdaLedger::new(unresolved, vec![], unresolved);

        assert_eq!(
            ledger.require_chained(),
            Err(LambdaAlgebraError::LambdaDidNotResolve)
        );
    }
}
