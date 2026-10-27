//! # lggr_engine — Evaluated Path Kernel (exact rational math)
//!
//! **Placement in OE:**
//! - **Pipelines** orchestrate engines, trace, solvers, search, replay, eval,
//!   functionals (when needed), terminalizers.
//! - **Engines** orchestrate 1-/2-morphisms (reducer / transformer / λ / generator / constructor / …)
//!   that act without increasing Φ.
//! - This file is the **evaluator** face of LGGR I-III path composition: map declared
//!   finite trajectories → diagnostic mass / defects with **Auth = 0**.
//! - It is **not** a functional crate (Φ₁/Γ₂ live in `core_functional`), not a host ledger,
//!   not an auth terminalizer, and not a new package.
//!
//! **Math (paper 019 / LGGR I):** Feynman-style path bookkeeping with finite
//! exact rational weights — no continuum integrals, no phase, no Born rule, zero floats, zero `exp`:
//!
//! \[
//! Z(S_b\mid S_a)=\sum_{\gamma:a\to b} E(\gamma)\,w[\gamma]
//! \]
//!
//! \[
//! \Delta_E = E_g - E_1 E_2 \in \{-1,0,1\}
//! \]
//!
//! Host overlays (Auth=0 residual ledger, detector adequacy) live in sister modules of `core_epk`.
//! **AuthorityEffect: None.** Mints nothing.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

// ── errors ──────────────────────────────────────────────────────────────────

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum LggrError {
    #[error("at least one composition record is required")]
    EmptyPathSet,
    #[error("{0} must be a non-empty string")]
    EmptyId(&'static str),
    #[error("{field} must be non-negative, got {value}")]
    NegativeCost { field: &'static str, value: String },
    #[error(
        "composition `{composed}` is not glued at the boundary: \
         left output `{left_output}` != right input `{right_input}`"
    )]
    Unglued {
        composed: String,
        left_output: String,
        right_input: String,
    },
    #[error("unknown trace id `{0}` referenced by a composition record")]
    UnknownTrace(String),
    #[error("invalid evaluator gluing defect: {0} (expected -1, 0, or 1)")]
    InvalidDefect(i64),
    #[error("metric identity failed: {0}")]
    IdentityViolation(String),
    #[error("length mismatch: {expected} expected, found {found}")]
    LengthMismatch { expected: usize, found: usize },
}

pub type EpkError = LggrError;

fn require_nonnegative(value: &BigRational, field: &'static str) -> Result<(), LggrError> {
    if value < &BigRational::zero() {
        return Err(LggrError::NegativeCost {
            field,
            value: value.to_string(),
        });
    }
    Ok(())
}

fn require_nonempty(value: &str, field: &'static str) -> Result<(), LggrError> {
    if value.is_empty() {
        return Err(LggrError::EmptyId(field));
    }
    Ok(())
}

// ── formal exponent kernels ─────────────────────────────────────────────────

/// A formal exponent monomial term `c · e^{-β A}` represented without evaluating `exp`.
///
/// In the group ring / polynomial representation over ℚ, multiplication of two terms
/// multiplies their rational coefficients and adds their rational exponents:
/// `(c₁ e^{-A₁}) · (c₂ e^{-A₂}) = (c₁ c₂) e^{-(A₁ + A₂)}`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FormalExponent {
    pub coefficient: BigRational,
    pub exponent: BigRational,
}

impl FormalExponent {
    pub fn zero() -> Self {
        Self {
            coefficient: BigRational::zero(),
            exponent: BigRational::zero(),
        }
    }

    pub fn one() -> Self {
        Self {
            coefficient: BigRational::one(),
            exponent: BigRational::zero(),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.coefficient.is_zero()
    }

    pub fn mul(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            Self::zero()
        } else {
            Self {
                coefficient: &self.coefficient * &other.coefficient,
                exponent: &self.exponent + &other.exponent,
            }
        }
    }
}

/// Exact sum of formal monomials `c · e^{-exponent}`.
///
/// Terms that share an exponent combine by adding coefficients. A coefficient
/// that cancels is dropped, so opposite defects cancel only when their actions
/// agree. The exponent is the positive quantity inside `e^{-·}`; it is not evaluated.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct FormalSeries {
    terms: Vec<FormalExponent>,
}

impl FormalSeries {
    pub fn is_zero(&self) -> bool {
        self.terms.is_empty()
    }

    pub fn terms(&self) -> &[FormalExponent] {
        &self.terms
    }

    /// Coefficient of `e^{-exponent}`, or zero if that exponent is absent.
    pub fn coefficient(&self, exponent: &BigRational) -> BigRational {
        self.terms
            .iter()
            .find(|term| &term.exponent == exponent)
            .map(|term| term.coefficient.clone())
            .unwrap_or_else(BigRational::zero)
    }

    pub fn add_term(&mut self, coefficient: BigRational, exponent: BigRational) {
        if coefficient.is_zero() {
            return;
        }
        if let Some(index) = self.terms.iter().position(|term| term.exponent == exponent) {
            self.terms[index].coefficient += &coefficient;
            if self.terms[index].coefficient.is_zero() {
                self.terms.remove(index);
            }
            return;
        }
        self.terms.push(FormalExponent {
            coefficient,
            exponent,
        });
        self.terms
            .sort_by(|left, right| left.exponent.cmp(&right.exponent));
    }
}

// ── carriers ────────────────────────────────────────────────────────────────

/// One evaluated step γ: content-hash states, path action A[γ], gate E(γ).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceRecord {
    pub trace_id: String,
    pub task_id: String,
    pub stage: String,
    pub parent_trace_id: Option<String>,
    pub input_hash: String,
    pub output_hash: String,
    pub cost: BigRational,
    pub residual_risk: BigRational,
    pub evaluator_pass: bool,
}

impl TraceRecord {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        trace_id: impl Into<String>,
        task_id: impl Into<String>,
        stage: impl Into<String>,
        parent_trace_id: Option<String>,
        input_hash: impl Into<String>,
        output_hash: impl Into<String>,
        cost: BigRational,
        residual_risk: BigRational,
        evaluator_pass: bool,
    ) -> Result<Self, EpkError> {
        let record = TraceRecord {
            trace_id: trace_id.into(),
            task_id: task_id.into(),
            stage: stage.into(),
            parent_trace_id,
            input_hash: input_hash.into(),
            output_hash: output_hash.into(),
            cost,
            residual_risk,
            evaluator_pass,
        };
        require_nonempty(&record.trace_id, "TraceRecord trace_id")?;
        require_nonempty(&record.task_id, "TraceRecord task_id")?;
        require_nonempty(&record.input_hash, "TraceRecord input_hash")?;
        require_nonempty(&record.output_hash, "TraceRecord output_hash")?;
        require_nonnegative(&record.cost, "TraceRecord cost")?;
        require_nonnegative(&record.residual_risk, "TraceRecord residual_risk")?;
        Ok(record)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluatorEvent {
    pub trace_id: String,
    pub evaluator: String,
    pub eval_pass: bool,
    pub stage: Option<String>,
}

/// Fold E(γ) as AND of events; `None` if no event for `trace_id`.
pub fn fold_evaluator_events(trace_id: &str, events: &[EvaluatorEvent]) -> Option<bool> {
    let mut seen = false;
    let mut all_pass = true;
    for event in events {
        if event.trace_id == trace_id {
            seen = true;
            all_pass &= event.eval_pass;
        }
    }
    seen.then_some(all_pass)
}

/// Declared boundary slice B ⊆ S for kernel composition.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BoundarySlice {
    pub name: String,
    pub states: BTreeSet<String>,
}

impl BoundarySlice {
    pub fn new(name: impl Into<String>, states: impl IntoIterator<Item = String>) -> Self {
        BoundarySlice {
            name: name.into(),
            states: states.into_iter().collect(),
        }
    }

    pub fn contains(&self, state: &str) -> bool {
        self.states.contains(state)
    }
}

/// Two-segment composition: (E₁, E₂, E_g) + optional composed cost.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompositionRecord {
    pub composed_trace_id: String,
    pub left_trace_id: String,
    pub right_trace_id: String,
    pub local_left_pass: bool,
    pub local_right_pass: bool,
    pub global_pass: bool,
    pub composed_cost: Option<BigRational>,
}

impl CompositionRecord {
    pub fn new(
        composed_trace_id: impl Into<String>,
        left_trace_id: impl Into<String>,
        right_trace_id: impl Into<String>,
        local_left_pass: bool,
        local_right_pass: bool,
        global_pass: bool,
        composed_cost: Option<BigRational>,
    ) -> Result<Self, EpkError> {
        let record = CompositionRecord {
            composed_trace_id: composed_trace_id.into(),
            left_trace_id: left_trace_id.into(),
            right_trace_id: right_trace_id.into(),
            local_left_pass,
            local_right_pass,
            global_pass,
            composed_cost,
        };
        require_nonempty(
            &record.composed_trace_id,
            "CompositionRecord composed_trace_id",
        )?;
        require_nonempty(&record.left_trace_id, "CompositionRecord left_trace_id")?;
        require_nonempty(&record.right_trace_id, "CompositionRecord right_trace_id")?;
        if let Some(ref cost) = record.composed_cost {
            require_nonnegative(cost, "CompositionRecord composed_cost")?;
        }
        Ok(record)
    }

    pub fn local_product(&self) -> bool {
        self.local_left_pass && self.local_right_pass
    }
}

/// Index of segments by trace_id.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TraceLedger {
    records: BTreeMap<String, TraceRecord>,
}

impl TraceLedger {
    pub fn new() -> Self {
        TraceLedger::default()
    }

    pub fn from_records(records: impl IntoIterator<Item = TraceRecord>) -> Self {
        let mut ledger = TraceLedger::new();
        for record in records {
            ledger.insert(record);
        }
        ledger
    }

    pub fn insert(&mut self, record: TraceRecord) -> Option<TraceRecord> {
        self.records.insert(record.trace_id.clone(), record)
    }

    pub fn get(&self, trace_id: &str) -> Option<&TraceRecord> {
        self.records.get(trace_id)
    }

    pub fn len(&self) -> usize {
        self.records.len()
    }

    pub fn is_empty(&self) -> bool {
        self.records.is_empty()
    }

    pub fn resolve_boundary(&self, comp: &CompositionRecord) -> Result<String, EpkError> {
        let left = self
            .get(&comp.left_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.left_trace_id.clone()))?;
        let right = self
            .get(&comp.right_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.right_trace_id.clone()))?;
        if left.output_hash != right.input_hash {
            return Err(EpkError::Unglued {
                composed: comp.composed_trace_id.clone(),
                left_output: left.output_hash.clone(),
                right_input: right.input_hash.clone(),
            });
        }
        Ok(left.output_hash.clone())
    }
}

// ── defects ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct GluingDefect {
    pub delta_eval: i8,
    pub local_product: bool,
    pub global_pass: bool,
}

/// Δ_E = E_g − E₁·E₂ ∈ {-1, 0, 1}. −1 is local-green / global-red.
pub fn evaluator_gluing_defect(comp: &CompositionRecord) -> GluingDefect {
    let local_product = comp.local_product();
    let global_pass = comp.global_pass;
    let delta_eval = global_pass as i8 - local_product as i8;
    GluingDefect {
        delta_eval,
        local_product,
        global_pass,
    }
}

/// Δ_A = composed_cost − (left.cost + right.cost); None if uncheckable.
pub fn action_gluing_defect(comp: &CompositionRecord, ledger: &TraceLedger) -> Option<BigRational> {
    let composed = comp.composed_cost.as_ref()?;
    let left = ledger.get(&comp.left_trace_id)?;
    let right = ledger.get(&comp.right_trace_id)?;
    Some(composed - (&left.cost + &right.cost))
}

// ── kernels (finite Riemann path mass) ──────────────────────────────────────

pub type KernelKey = (String, String);
pub type Kernel = BTreeMap<KernelKey, BigRational>;

/// Exact formal exponent path weight: returns formal monomial `1 · e^{-β·A[γ]}` when gate passes,
/// or formal zero when the gate fails.
pub fn path_weight(eval_pass: bool, cost: &BigRational, beta: &BigRational) -> FormalExponent {
    if eval_pass {
        FormalExponent {
            coefficient: BigRational::one(),
            exponent: beta * cost,
        }
    } else {
        FormalExponent::zero()
    }
}

/// Exact path weight directly on ℚ: returns `weight` if gate passes, or 0 if gate fails.
pub fn exact_path_weight(eval_pass: bool, weight: &BigRational) -> BigRational {
    if eval_pass {
        weight.clone()
    } else {
        BigRational::zero()
    }
}

/// Z(b|a) = Σ_{γ:a→b} E(γ) with exact rational weights. When unweighted, each passing path has weight 1.
pub fn segment_kernel(segments: &[TraceRecord]) -> Kernel {
    let mut kernel = Kernel::new();
    for seg in segments {
        if seg.evaluator_pass {
            *kernel
                .entry((seg.input_hash.clone(), seg.output_hash.clone()))
                .or_insert_with(BigRational::zero) += BigRational::one();
        }
    }
    kernel
}

/// Segment kernel with explicit exact rational path weights.
pub fn weighted_segment_kernel(
    segments: &[TraceRecord],
    weights: &[BigRational],
) -> Result<Kernel, EpkError> {
    if segments.len() != weights.len() {
        return Err(EpkError::LengthMismatch {
            expected: segments.len(),
            found: weights.len(),
        });
    }
    let mut kernel = Kernel::new();
    for (seg, weight) in segments.iter().zip(weights.iter()) {
        require_nonnegative(weight, "segment weight")?;
        if seg.evaluator_pass {
            *kernel
                .entry((seg.input_hash.clone(), seg.output_hash.clone()))
                .or_insert_with(BigRational::zero) += weight;
        }
    }
    Ok(kernel)
}

/// Composed kernel keyed (source, target) using E_g and glued segments.
pub fn composed_kernel(
    comps: &[CompositionRecord],
    ledger: &TraceLedger,
) -> Result<Kernel, EpkError> {
    let mut kernel = Kernel::new();
    for comp in comps {
        ledger.resolve_boundary(comp)?;
        let left = ledger
            .get(&comp.left_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.left_trace_id.clone()))?;
        let right = ledger
            .get(&comp.right_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.right_trace_id.clone()))?;
        if comp.global_pass {
            *kernel
                .entry((left.input_hash.clone(), right.output_hash.clone()))
                .or_insert_with(BigRational::zero) += BigRational::one();
        }
    }
    Ok(kernel)
}

/// Ẑ(c|a) = Σ_{b∈B} Z(c|b)·Z(b|a) in exact rational arithmetic.
pub fn compose_kernels(left: &Kernel, right: &Kernel, boundary: &BoundarySlice) -> Kernel {
    let mut result = Kernel::new();
    for ((b1, c), z_cb) in left {
        if !boundary.contains(b1) {
            continue;
        }
        for ((a, b2), z_ba) in right {
            if b1 != b2 {
                continue;
            }
            *result
                .entry((a.clone(), c.clone()))
                .or_insert_with(BigRational::zero) += z_cb * z_ba;
        }
    }
    result
}

// ── composition conditions G1–G3 (G4 is proposal-side, not decidable here) ─

pub fn g2_action_additive(
    comp: &CompositionRecord,
    ledger: &TraceLedger,
    tol: Option<&BigRational>,
) -> Option<bool> {
    let composed = comp.composed_cost.as_ref()?;
    let left = ledger.get(&comp.left_trace_id)?;
    let right = ledger.get(&comp.right_trace_id)?;
    let diff = (composed - (&left.cost + &right.cost)).abs();
    match tol {
        Some(t) => Some(diff <= *t),
        None => Some(diff.is_zero()),
    }
}

pub fn g3_evaluator_factorizes(comp: &CompositionRecord) -> bool {
    evaluator_gluing_defect(comp).delta_eval == 0
}

pub fn boundary_in_slice(
    comp: &CompositionRecord,
    ledger: &TraceLedger,
    slice: &BoundarySlice,
) -> Result<bool, EpkError> {
    let boundary = ledger.resolve_boundary(comp)?;
    Ok(slice.contains(&boundary))
}

/// R_Eval = Σ Δ_E · e^{-β(A[γ₁]+A[γ₂])}, kept as an exact formal series.
///
/// The Boltzmann factor is not evaluated. A positive defect and a negative
/// defect therefore cancel only when `β(A₁+A₂)` agrees; summing the bare
/// defects would report that cancellation for every action.
pub fn evaluator_residual(
    comps: &[CompositionRecord],
    ledger: &TraceLedger,
    beta: &BigRational,
) -> Result<FormalSeries, EpkError> {
    if beta.is_negative() {
        return Err(EpkError::NegativeCost {
            field: "beta",
            value: beta.to_string(),
        });
    }
    let mut series = FormalSeries::default();
    for comp in comps {
        ledger.resolve_boundary(comp)?;
        let left = ledger
            .get(&comp.left_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.left_trace_id.clone()))?;
        let right = ledger
            .get(&comp.right_trace_id)
            .ok_or_else(|| EpkError::UnknownTrace(comp.right_trace_id.clone()))?;
        let delta =
            BigRational::from_integer(BigInt::from(evaluator_gluing_defect(comp).delta_eval));
        let action = &left.cost + &right.cost;
        series.add_term(delta, beta * &action);
    }
    Ok(series)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompositionReport {
    pub n: usize,
    pub g3_factorization_rate: BigRational,
    pub g2_action_additive_rate: Option<BigRational>,
    pub boundary_in_slice_rate: BigRational,
    pub evaluator_residual: FormalSeries,
}

pub fn analyze_composition(
    comps: &[CompositionRecord],
    ledger: &TraceLedger,
    slice: &BoundarySlice,
    beta: &BigRational,
    tol: Option<&BigRational>,
) -> Result<CompositionReport, EpkError> {
    if comps.is_empty() {
        return Err(EpkError::EmptyPathSet);
    }
    let n = comps.len();
    let n_rat = BigRational::from_integer(BigInt::from(n));
    let g3_pass = comps.iter().filter(|c| g3_evaluator_factorizes(c)).count();
    let mut g2_checked = 0usize;
    let mut g2_pass = 0usize;
    let mut in_slice = 0usize;
    for comp in comps {
        if let Some(ok) = g2_action_additive(comp, ledger, tol) {
            g2_checked += 1;
            if ok {
                g2_pass += 1;
            }
        }
        if boundary_in_slice(comp, ledger, slice)? {
            in_slice += 1;
        }
    }
    Ok(CompositionReport {
        n,
        g3_factorization_rate: BigRational::from_integer(BigInt::from(g3_pass)) / &n_rat,
        g2_action_additive_rate: if g2_checked > 0 {
            Some(
                BigRational::from_integer(BigInt::from(g2_pass))
                    / BigRational::from_integer(BigInt::from(g2_checked)),
            )
        } else {
            None
        },
        boundary_in_slice_rate: BigRational::from_integer(BigInt::from(in_slice)) / &n_rat,
        evaluator_residual: evaluator_residual(comps, ledger, beta)?,
    })
}

// ── metrics ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LggrMetrics {
    pub n: usize,
    pub lpr: BigRational,
    pub gpr: BigRational,
    pub avg_delta_eval: BigRational,
    pub ngd: BigRational,
    pub positive_defect_rate: BigRational,
    pub zero_defect_rate: BigRational,
    pub egd: BigRational,
    pub rke: Option<BigRational>,
    pub nrke: Option<BigRational>,
    pub avg_action_defect: Option<BigRational>,
    #[serde(default)]
    pub notes: BTreeMap<String, Value>,
}

pub type EpkMetrics = LggrMetrics;

#[derive(Default)]
struct MetricTallies {
    lpr_count: usize,
    gpr_count: usize,
    delta_sum: BigInt,
    ngd_count: usize,
    pgd_count: usize,
    zdr_count: usize,
    egd_count: usize,
    action_sum: BigRational,
    action_count: usize,
}

impl MetricTallies {
    fn record(
        &mut self,
        comp: &CompositionRecord,
        ledger: Option<&TraceLedger>,
    ) -> Result<(), LggrError> {
        self.lpr_count += usize::from(comp.local_product());
        self.gpr_count += usize::from(comp.global_pass);
        let defect = evaluator_gluing_defect(comp);
        self.delta_sum += BigInt::from(defect.delta_eval);
        match defect.delta_eval {
            -1 => self.ngd_count += 1,
            1 => self.pgd_count += 1,
            0 => self.zdr_count += 1,
            other => return Err(EpkError::InvalidDefect(i64::from(other))),
        }
        self.egd_count += usize::from(defect.delta_eval != 0);
        if let Some(action_defect) = ledger.and_then(|l| action_gluing_defect(comp, l)) {
            self.action_sum += action_defect;
            self.action_count += 1;
        }
        Ok(())
    }
}

pub fn calculate_metrics(
    comps: &[CompositionRecord],
    ledger: Option<&TraceLedger>,
    rke: Option<BigRational>,
    nrke: Option<BigRational>,
    notes: Option<BTreeMap<String, Value>>,
) -> Result<LggrMetrics, LggrError> {
    if comps.is_empty() {
        return Err(LggrError::EmptyPathSet);
    }
    if let Some(ref r) = rke {
        require_nonnegative(r, "rke")?;
    }
    if let Some(ref nr) = nrke {
        require_nonnegative(nr, "nrke")?;
    }

    let n = comps.len();
    let n_rat = BigRational::from_integer(BigInt::from(n));
    let mut t = MetricTallies::default();
    for comp in comps {
        t.record(comp, ledger)?;
    }

    let rate = |count: usize| BigRational::from_integer(BigInt::from(count)) / &n_rat;
    let avg_action_defect = (t.action_count > 0)
        .then(|| t.action_sum / BigRational::from_integer(BigInt::from(t.action_count)));

    let metrics = LggrMetrics {
        n,
        lpr: rate(t.lpr_count),
        gpr: rate(t.gpr_count),
        avg_delta_eval: BigRational::new(t.delta_sum, BigInt::from(n)),
        ngd: rate(t.ngd_count),
        positive_defect_rate: rate(t.pgd_count),
        zero_defect_rate: rate(t.zdr_count),
        egd: rate(t.egd_count),
        rke,
        nrke,
        avg_action_defect,
        notes: notes.unwrap_or_default(),
    };
    validate_metric_identity(&metrics)?;
    Ok(metrics)
}

/// Exact algebraic verification of the three metric identities:
/// 1. GPR - LPR == avg_delta_eval
/// 2. NGD + PGD + ZDR == 1
/// 3. EGD == NGD + PGD
pub fn validate_metric_identity(metrics: &LggrMetrics) -> Result<(), LggrError> {
    let id1 = &metrics.gpr - &metrics.lpr;
    if id1 != metrics.avg_delta_eval {
        return Err(LggrError::IdentityViolation(format!(
            "GPR-LPR={} != avg_delta_eval={}",
            id1, metrics.avg_delta_eval
        )));
    }
    let partition = &metrics.ngd + &metrics.positive_defect_rate + &metrics.zero_defect_rate;
    if partition != BigRational::one() {
        return Err(LggrError::IdentityViolation(format!(
            "NGD+PGD+ZDR={partition} != 1"
        )));
    }
    let egd_check = &metrics.ngd + &metrics.positive_defect_rate;
    if metrics.egd != egd_check {
        return Err(LggrError::IdentityViolation(format!(
            "EGD={} != NGD+PGD={}",
            metrics.egd, egd_check
        )));
    }
    Ok(())
}

// ── residual kernel error (path-mass mismatch — not FOC Φ₁) ─────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResidualKernelReport {
    pub source_id: String,
    pub target_id: String,
    pub actual_value: BigRational,
    pub estimated_value: BigRational,
    pub rke: BigRational,
    pub nrke: Option<BigRational>,
    pub actual_zero: bool,
    pub estimated_positive: bool,
}

pub fn residual_kernel_error(
    actual: &Kernel,
    estimated: &Kernel,
    source_id: impl Into<String>,
    target_id: impl Into<String>,
    epsilon: Option<&BigRational>,
) -> Result<ResidualKernelReport, EpkError> {
    let source_id = source_id.into();
    let target_id = target_id.into();
    require_nonempty(&source_id, "residual source_id")?;
    require_nonempty(&target_id, "residual target_id")?;

    let key = (source_id.clone(), target_id.clone());
    let actual_value = actual.get(&key).cloned().unwrap_or_else(BigRational::zero);
    let estimated_value = estimated
        .get(&key)
        .cloned()
        .unwrap_or_else(BigRational::zero);
    require_nonnegative(&actual_value, "actual kernel value")?;
    require_nonnegative(&estimated_value, "estimated kernel value")?;

    let rke = (&actual_value - &estimated_value).abs();
    let nrke = match epsilon {
        Some(eps) => {
            if eps <= &BigRational::zero() {
                return Err(EpkError::NegativeCost {
                    field: "epsilon (must be positive)",
                    value: eps.to_string(),
                });
            }
            Some(&rke / (&actual_value + eps))
        }
        None => {
            if actual_value.is_zero() {
                None
            } else {
                Some(&rke / &actual_value)
            }
        }
    };
    let actual_zero = actual_value.is_zero();
    let estimated_positive = estimated_value > BigRational::zero();
    Ok(ResidualKernelReport {
        source_id,
        target_id,
        actual_value,
        estimated_value,
        rke,
        nrke,
        actual_zero,
        estimated_positive,
    })
}

// ── tests ───────────────────────────────────────────────────────────────────

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/lggr_engine.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:lggr-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn comps(triples: &[(bool, bool, bool)]) -> Vec<CompositionRecord> {
        triples
            .iter()
            .enumerate()
            .map(|(i, &(l, r, g))| {
                CompositionRecord::new(format!("c{i}"), "l", "r", l, r, g, None).unwrap()
            })
            .collect()
    }

    #[test]
    fn delta_e_lggr_and_metrics_phone_test() {
        // LGGR I phone fixture: LPR=3/5, GPR=1/5, E[Δ_E]=−2/5, NGD=2/5
        let m = calculate_metrics(
            &comps(&[
                (true, true, true),
                (true, true, false),
                (true, true, false),
                (true, false, false),
                (false, true, false),
            ]),
            None,
            None,
            None,
            None,
        )
        .unwrap();
        assert_eq!(m.lpr, BigRational::new(3.into(), 5.into()));
        assert_eq!(m.gpr, BigRational::new(1.into(), 5.into()));
        assert_eq!(m.avg_delta_eval, BigRational::new((-2).into(), 5.into()));
        assert_eq!(m.ngd, BigRational::new(2.into(), 5.into()));
        assert_eq!(m.positive_defect_rate, BigRational::zero());
        assert_eq!(m.zero_defect_rate, BigRational::new(3.into(), 5.into()));
        assert_eq!(m.egd, BigRational::new(2.into(), 5.into()));
        assert_eq!(&m.gpr - &m.lpr, m.avg_delta_eval);

        assert_eq!(
            evaluator_gluing_defect(
                &CompositionRecord::new("c", "l", "r", true, true, false, None).unwrap()
            )
            .delta_eval,
            -1
        );
    }

    #[test]
    fn kernel_compose_and_residual() {
        let mut right = Kernel::new();
        right.insert(
            ("a".into(), "b".into()),
            BigRational::from_integer(2.into()),
        );
        let mut left = Kernel::new();
        left.insert(
            ("b".into(), "c".into()),
            BigRational::from_integer(3.into()),
        );
        let boundary = BoundarySlice::new("B", ["b".to_string()]);
        let composed = compose_kernels(&left, &right, &boundary);
        assert_eq!(
            composed.get(&("a".into(), "c".into())),
            Some(&BigRational::from_integer(6.into()))
        );

        let mut actual = Kernel::new();
        actual.insert(("a".into(), "c".into()), BigRational::one());
        let report = residual_kernel_error(&actual, &composed, "a", "c", None).unwrap();
        assert_eq!(report.rke, BigRational::from_integer(5.into()));
    }

    #[test]
    fn formal_exponent_multiplication() {
        let t1 = FormalExponent {
            coefficient: BigRational::from_integer(2.into()),
            exponent: BigRational::from_integer(3.into()),
        };
        let t2 = FormalExponent {
            coefficient: BigRational::from_integer(5.into()),
            exponent: BigRational::from_integer(4.into()),
        };
        let prod = t1.mul(&t2);
        assert_eq!(prod.coefficient, BigRational::from_integer(10.into()));
        assert_eq!(prod.exponent, BigRational::from_integer(7.into()));
    }

    #[test]
    fn path_weight_gate() {
        let beta = BigRational::one();
        let cost = BigRational::one();
        let w_false = path_weight(false, &cost, &beta);
        assert!(w_false.is_zero());
        let w_true = path_weight(true, &BigRational::zero(), &beta);
        assert_eq!(w_true.coefficient, BigRational::one());
        assert_eq!(w_true.exponent, BigRational::zero());
    }

    fn segment(id: &str, input: &str, output: &str, cost: i64) -> TraceRecord {
        TraceRecord::new(
            id,
            "task",
            "stage",
            None,
            input,
            output,
            BigRational::from_integer(cost.into()),
            BigRational::zero(),
            true,
        )
        .unwrap()
    }

    #[test]
    fn evaluator_residual_keeps_distinct_actions_from_cancelling() {
        // Δ = +1 on action 0 and Δ = −1 on action 5. The bare sum is 0.
        // The weighted residual is e^{0} − e^{-5}, which is not zero.
        let mut ledger = TraceLedger::new();
        ledger.insert(segment("l0", "s", "m0", 0));
        ledger.insert(segment("r0", "m0", "t", 0));
        ledger.insert(segment("l1", "s", "m1", 3));
        ledger.insert(segment("r1", "m1", "t", 2));
        let comps = vec![
            CompositionRecord::new("c0", "l0", "r0", false, true, true, None).unwrap(),
            CompositionRecord::new("c1", "l1", "r1", true, true, false, None).unwrap(),
        ];
        let beta = BigRational::one();
        let series = evaluator_residual(&comps, &ledger, &beta).unwrap();
        assert!(!series.is_zero());
        assert_eq!(series.coefficient(&BigRational::zero()), BigRational::one());
        assert_eq!(
            series.coefficient(&BigRational::from_integer(5.into())),
            BigRational::from_integer((-1).into())
        );

        // Equal actions do cancel.
        let mut same = TraceLedger::new();
        same.insert(segment("l0", "s", "m0", 2));
        same.insert(segment("r0", "m0", "t", 3));
        same.insert(segment("l1", "s", "m1", 4));
        same.insert(segment("r1", "m1", "t", 1));
        let cancelled = evaluator_residual(&comps, &same, &beta).unwrap();
        assert!(cancelled.is_zero());
    }

    #[test]
    fn negative_beta_is_refused() {
        let mut ledger = TraceLedger::new();
        ledger.insert(segment("l0", "s", "m", 1));
        ledger.insert(segment("r0", "m", "t", 1));
        let comps =
            vec![CompositionRecord::new("c0", "l0", "r0", true, true, false, None).unwrap()];
        let err = evaluator_residual(&comps, &ledger, &BigRational::from_integer((-1).into()))
            .unwrap_err();
        assert!(matches!(err, EpkError::NegativeCost { field: "beta", .. }));
    }
}
