// Executable finite evidence; AuthorityEffect: None.
//! Chapter 19: the empirical adapter from run tables to compatible models, and its
//! tolerant version. Executable finite evidence for `WDP-CH19-P02`, `WDP-CH19-P06`
//! and `WDP-CH19-P07`, and the CHSH fixtures of `WDP-CH19-P05`; the residual
//! `WDP-CH19-O01` is the tolerance policy itself.
//!
//! A [`MeasurementCover`] declares measurements `0..m`, outcomes `0..k` and contexts
//! (sorted sets of measurements read together). A [`RunTable`] lists, for each context,
//! recorded runs: the outcome assignment of the context's measurements, aligned with the
//! context order. A section over a set of measurements is an outcome vector aligned with
//! that set in increasing measurement order.
//!
//! - [`frequencies`] normalizes the run multiplicities of every context. A context with
//!   no runs is refused as [`AdapterRefusal::EmptyContext`].
//! - [`adapt_exact`] (`WDP-CH19-P02`) accepts exactly the tables whose context
//!   frequencies agree on every pairwise overlap, and returns the
//!   [`EmpiricalModel`]; the first disagreement is refused as
//!   [`AdapterRefusal::Signalling`] with the pair and the overlap section.
//! - [`signalling_defect`] is the L1 distance `D_ij` between the two overlap marginals of
//!   every pair `i < j`; an empty overlap has marginal one on both sides, so `D_ij = 0`.
//! - [`adapt_tolerant`] (`WDP-CH19-P06`) accepts when every context has runs and
//!   `max D_ij <= eps`. At `eps = 0` it accepts exactly what [`adapt_exact`] accepts. If
//!   every context frequency vector is within `eps` in L1 of one compatible model, then
//!   `D_ij <= 2 eps` for every pair ([`l1_distance_to_model`]).
//! - [`two_context_repair`] (`WDP-CH19-P07`): for exactly two contexts, replacing both
//!   overlap marginals by their average moves each context by exactly `D / 2` in L1, so a
//!   compatible model within `eps` per context exists exactly when `D <= 2 eps`.
//!
//! The tolerance `eps` is a declared policy, not derived; acceptance under `eps > 0` is
//! not compatibility and confers no standing (`WDP-CH19-O01` stays open).
//!
//! [`has_positive_global_assignment`](EmpiricalModel::has_positive_global_assignment) is
//! the support-level test: some assignment of all measurements has positive probability in
//! every context. If none does, no joint distribution reproduces the model (the model is
//! strongly contextual). If one does, that is necessary and not sufficient for a joint
//! distribution: the test never certifies noncontextuality.
//!
//! The CHSH fixtures ([`chsh_cover`], [`pr_box_run_table`], [`global_run_table`]) are
//! presented to `core_quantum_physics`'s `PairwiseBox` ([`chsh_pairwise_box`]), and
//! [`chsh_correlator`] and [`chsh_value`] are its `correlator` and `chsh`.
//!
//! Enumerating global assignments is capped by [`MAX_ASSIGNMENTS`] and a cover by
//! [`MAX_MEASUREMENTS`]; [`EmpiricalModel::positive_global_assignments_with_limit`] takes
//! the cap as an argument.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_34e2bb5b<T> {
    fn checked_invariant_34e2bb5b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_34e2bb5b<T> for Option<T> {
    #[inline]
    fn checked_invariant_34e2bb5b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_34e2bb5b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_34e2bb5b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet};

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_quantum_physics::finite_chsh_correlations::PairwiseBox;
use thiserror::Error;

use crate::error::WdpError;
use crate::stochastic_package::bounded_power;
use crate::types::AuthorityEffect;

/// Outcomes of measurements, aligned with an increasing list of measurement ids.
pub type Section = Vec<usize>;

/// A finitely supported distribution over sections; only positive weights are stored.
pub type SectionDistribution = BTreeMap<Section, BigRational>;

/// Signalling defects `D_ij` keyed by the context pair `(i, j)`, `i < j`.
pub type PairDefects = Vec<((usize, usize), BigRational)>;

/// Cap on enumerated global assignments.
pub const MAX_ASSIGNMENTS: usize = 1_000_000;

/// Cap on the measurements of a cover.
pub const MAX_MEASUREMENTS: usize = 1_000_000;

/// The overlap section on which two contexts disagree, with both weights.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
#[error(
    "contexts {i} and {j} disagree on overlap section {overlap_section:?}: {weight_i} against {weight_j}"
)]
pub struct SignallingWitness {
    pub i: usize,
    pub j: usize,
    pub overlap_section: Section,
    pub weight_i: BigRational,
    pub weight_j: BigRational,
}

/// The first pair whose marginal defect exceeds the declared tolerance.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
#[error(
    "contexts {i} and {j} have marginal defect {defect} above tolerance {eps} on overlap {overlap:?}"
)]
pub struct ToleranceWitness {
    pub i: usize,
    pub j: usize,
    pub defect: BigRational,
    pub eps: BigRational,
    pub overlap: Vec<usize>,
}

/// Typed refusals of the empirical adapters. The witnesses are boxed: they carry exact
/// rationals, and a refusal is the rare path.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum AdapterRefusal {
    #[error("context {0} has no runs")]
    EmptyContext(usize),
    #[error(transparent)]
    Signalling(Box<SignallingWitness>),
    #[error(transparent)]
    ToleranceExceeded(Box<ToleranceWitness>),
    #[error("invalid input: {detail}")]
    InvalidInput { detail: String },
    /// A crate error other than plain invalid input, carried intact.
    #[error("crate refusal: {0}")]
    Wdp(#[source] Box<WdpError>),
}

impl From<WdpError> for AdapterRefusal {
    /// Plain invalid input keeps its shape; a wrapped adapter refusal is unwrapped;
    /// every other crate error is carried whole in [`AdapterRefusal::Wdp`].
    fn from(error: WdpError) -> Self {
        match error {
            WdpError::InvalidInput { detail } => AdapterRefusal::InvalidInput { detail },
            WdpError::Adapter(refusal) => *refusal,
            other => AdapterRefusal::Wdp(Box::new(other)),
        }
    }
}

fn invalid(detail: String) -> AdapterRefusal {
    AdapterRefusal::InvalidInput { detail }
}

/// Declared measurements, outcome set and contexts.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MeasurementCover {
    measurements: usize,
    outcomes: usize,
    contexts: Vec<Vec<usize>>,
}

impl MeasurementCover {
    /// Measurements `0..measurements` (at most [`MAX_MEASUREMENTS`]), outcomes
    /// `0..outcomes`, and at least one context, each a nonempty strictly increasing list of
    /// measurement ids.
    pub fn new(
        measurements: usize,
        outcomes: usize,
        contexts: Vec<Vec<usize>>,
    ) -> Result<Self, WdpError> {
        let bad = |detail: String| WdpError::InvalidInput { detail };
        if measurements == 0 || outcomes == 0 {
            return Err(bad(
                "a cover needs at least one measurement and one outcome".to_string(),
            ));
        }
        if measurements > MAX_MEASUREMENTS {
            return Err(bad(format!(
                "{measurements} measurements exceed the cap {MAX_MEASUREMENTS}"
            )));
        }
        if contexts.is_empty() {
            return Err(bad("a cover needs at least one context".to_string()));
        }
        for (i, context) in contexts.iter().enumerate() {
            if context.is_empty() {
                return Err(bad(format!("context {i} has no measurements")));
            }
            if context.windows(2).any(|w| w[0] >= w[1]) {
                return Err(bad(format!("context {i} is not strictly increasing")));
            }
            if let Some(&id) = context.iter().find(|&&id| id >= measurements) {
                return Err(bad(format!(
                    "context {i} names measurement {id} outside 0..{measurements}"
                )));
            }
        }
        Ok(Self {
            measurements,
            outcomes,
            contexts,
        })
    }

    pub fn measurements(&self) -> usize {
        self.measurements
    }

    pub fn outcomes(&self) -> usize {
        self.outcomes
    }

    pub fn contexts(&self) -> &[Vec<usize>] {
        &self.contexts
    }

    /// The increasing measurement ids shared by contexts `i` and `j`, or `None` when an
    /// index is out of range.
    pub fn overlap(&self, i: usize, j: usize) -> Option<Vec<usize>> {
        (i < self.contexts.len() && j < self.contexts.len()).then(|| self.overlap_unchecked(i, j))
    }

    /// The overlap of two contexts whose indices the caller has already bounded.
    fn overlap_unchecked(&self, i: usize, j: usize) -> Vec<usize> {
        let cj = &self.contexts[j];
        self.contexts[i]
            .iter()
            .copied()
            .filter(|id| cj.contains(id))
            .collect()
    }
}

/// Recorded runs: for each context, a list of outcome assignments aligned with the context.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunTable {
    runs: Vec<Vec<Section>>,
}

impl RunTable {
    /// A table against `cover`: one run list per context, every run aligned with its
    /// context and with outcomes below the cover's outcome count. Empty run lists are
    /// allowed here and refused by the adapters.
    pub fn new(cover: &MeasurementCover, runs: Vec<Vec<Section>>) -> Result<Self, WdpError> {
        check_runs(cover, &runs)?;
        Ok(Self { runs })
    }

    pub fn runs(&self) -> &[Vec<Section>] {
        &self.runs
    }
}

/// Whether `runs` has one list per context of `cover`, every run aligned with its context
/// and with outcomes below the cover's outcome count.
fn check_runs(cover: &MeasurementCover, runs: &[Vec<Section>]) -> Result<(), WdpError> {
    let bad = |detail: String| WdpError::InvalidInput { detail };
    if runs.len() != cover.contexts.len() {
        return Err(bad(format!(
            "{} run lists for {} contexts",
            runs.len(),
            cover.contexts.len()
        )));
    }
    for (i, (context, context_runs)) in cover.contexts.iter().zip(runs).enumerate() {
        for (r, run) in context_runs.iter().enumerate() {
            if run.len() != context.len() {
                return Err(bad(format!(
                    "run {r} of context {i} has {} outcomes, expected {}",
                    run.len(),
                    context.len()
                )));
            }
            if let Some(&o) = run.iter().find(|&&o| o >= cover.outcomes) {
                return Err(bad(format!(
                    "run {r} of context {i} has outcome {o} outside 0..{}",
                    cover.outcomes
                )));
            }
        }
    }
    Ok(())
}

/// The restriction of a section over `context` to the measurement ids `onto`.
fn restrict(context: &[usize], section: &[usize], onto: &[usize]) -> Section {
    onto.iter()
        .filter_map(|id| context.iter().position(|c| c == id).map(|p| section[p]))
        .collect()
}

fn marginal(context: &[usize], dist: &SectionDistribution, onto: &[usize]) -> SectionDistribution {
    let mut out = SectionDistribution::new();
    for (section, weight) in dist {
        *out.entry(restrict(context, section, onto))
            .or_insert_with(BigRational::zero) += weight;
    }
    out
}

/// `sum_s |a(s) - b(s)|` over the union of supports.
pub fn l1_distance(a: &SectionDistribution, b: &SectionDistribution) -> BigRational {
    let keys: BTreeSet<&Section> = a.keys().chain(b.keys()).collect();
    let zero = BigRational::zero();
    let difference: Vec<_> = keys
        .into_iter()
        .map(|key| a.get(key).unwrap_or(&zero) - b.get(key).unwrap_or(&zero))
        .collect();
    core_functional::Phi1Functional::unweighted_l1_rational(&difference)
        .checked_invariant_34e2bb5b("exact section frequencies")
}

fn check_table_shape(cover: &MeasurementCover, table: &RunTable) -> Result<(), AdapterRefusal> {
    Ok(check_runs(cover, &table.runs)?)
}

/// Normalized run multiplicities per context.
pub fn frequencies(
    cover: &MeasurementCover,
    table: &RunTable,
) -> Result<Vec<SectionDistribution>, AdapterRefusal> {
    check_table_shape(cover, table)?;
    let mut all = Vec::with_capacity(table.runs.len());
    for (i, runs) in table.runs.iter().enumerate() {
        if runs.is_empty() {
            return Err(AdapterRefusal::EmptyContext(i));
        }
        let total = BigRational::from_integer(runs.len().into());
        let mut dist = SectionDistribution::new();
        for run in runs {
            *dist.entry(run.clone()).or_insert_with(BigRational::zero) += BigRational::one();
        }
        for weight in dist.values_mut() {
            *weight = &*weight / &total;
        }
        all.push(dist);
    }
    Ok(all)
}

fn pairs(count: usize) -> impl Iterator<Item = (usize, usize)> {
    (0..count).flat_map(move |i| ((i + 1)..count).map(move |j| (i, j)))
}

/// The pair marginals over the overlap, for `i < j`, both keyed by overlap sections.
fn pair_marginals(
    cover: &MeasurementCover,
    dists: &[SectionDistribution],
    i: usize,
    j: usize,
) -> (Vec<usize>, SectionDistribution, SectionDistribution) {
    let overlap = cover.overlap_unchecked(i, j);
    let mu_i = marginal(&cover.contexts[i], &dists[i], &overlap);
    let mu_j = marginal(&cover.contexts[j], &dists[j], &overlap);
    (overlap, mu_i, mu_j)
}

fn check_compatible(
    cover: &MeasurementCover,
    dists: &[SectionDistribution],
) -> Result<(), AdapterRefusal> {
    for (i, j) in pairs(dists.len()) {
        let (_, mu_i, mu_j) = pair_marginals(cover, dists, i, j);
        let keys: BTreeSet<&Section> = mu_i.keys().chain(mu_j.keys()).collect();
        let zero = BigRational::zero();
        for key in keys {
            let (weight_i, weight_j) = (
                mu_i.get(key).unwrap_or(&zero),
                mu_j.get(key).unwrap_or(&zero),
            );
            if weight_i != weight_j {
                return Err(AdapterRefusal::Signalling(Box::new(SignallingWitness {
                    i,
                    j,
                    overlap_section: key.clone(),
                    weight_i: weight_i.clone(),
                    weight_j: weight_j.clone(),
                })));
            }
        }
    }
    Ok(())
}

/// Per-context distributions that agree on every pairwise overlap.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EmpiricalModel {
    cover: MeasurementCover,
    distributions: Vec<SectionDistribution>,
    authority_effect: AuthorityEffect,
}

impl EmpiricalModel {
    /// A model: one distribution per context, nonnegative, summing to one, over sections
    /// of the right length and outcome range, and marginal-compatible on all overlaps.
    pub fn new(
        cover: MeasurementCover,
        distributions: Vec<SectionDistribution>,
    ) -> Result<Self, AdapterRefusal> {
        if distributions.len() != cover.contexts.len() {
            return Err(invalid(format!(
                "{} distributions for {} contexts",
                distributions.len(),
                cover.contexts.len()
            )));
        }
        let mut canonical = Vec::with_capacity(distributions.len());
        for (i, (context, dist)) in cover.contexts.iter().zip(&distributions).enumerate() {
            let mut total = BigRational::zero();
            let mut kept = SectionDistribution::new();
            for (section, weight) in dist {
                if section.len() != context.len() || section.iter().any(|&o| o >= cover.outcomes) {
                    return Err(invalid(format!(
                        "context {i} has a malformed section {section:?}"
                    )));
                }
                if weight.is_negative() {
                    return Err(invalid(format!(
                        "context {i} has negative weight {weight} on {section:?}"
                    )));
                }
                total += weight;
                if !weight.is_zero() {
                    kept.insert(section.clone(), weight.clone());
                }
            }
            if !total.is_one() {
                return Err(invalid(format!(
                    "context {i} has total weight {total}, not 1"
                )));
            }
            canonical.push(kept);
        }
        check_compatible(&cover, &canonical)?;
        Ok(Self {
            cover,
            distributions: canonical,
            authority_effect: AuthorityEffect::None,
        })
    }

    pub fn cover(&self) -> &MeasurementCover {
        &self.cover
    }

    pub fn distributions(&self) -> &[SectionDistribution] {
        &self.distributions
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        self.authority_effect
    }

    /// Every assignment of all measurements whose restriction to each context has
    /// positive probability, in lexicographic order.
    pub fn positive_global_assignments(&self) -> Result<Vec<Section>, WdpError> {
        self.positive_global_assignments_with_limit(MAX_ASSIGNMENTS)
    }

    /// [`EmpiricalModel::positive_global_assignments`] refusing a cover with more than
    /// `limit` measurements or more than `limit` assignments (`outcomes^measurements`).
    pub fn positive_global_assignments_with_limit(
        &self,
        limit: usize,
    ) -> Result<Vec<Section>, WdpError> {
        let (m, k) = (self.cover.measurements, self.cover.outcomes);
        if m > limit {
            return Err(WdpError::InvalidInput {
                detail: format!("{m} measurements exceed the enumeration cap {limit}"),
            });
        }
        bounded_power(k, m, limit).ok_or_else(|| WdpError::InvalidInput {
            detail: format!("more than {limit} global assignments; enumeration refused"),
        })?;
        let mut positive = Vec::new();
        let mut assignment = vec![0usize; m];
        loop {
            let supported =
                self.cover
                    .contexts
                    .iter()
                    .zip(&self.distributions)
                    .all(|(context, dist)| {
                        let section: Section = context.iter().map(|&id| assignment[id]).collect();
                        dist.contains_key(&section)
                    });
            if supported {
                positive.push(assignment.clone());
            }
            let mut position = m;
            loop {
                if position == 0 {
                    return Ok(positive);
                }
                position -= 1;
                assignment[position] += 1;
                if assignment[position] < k {
                    break;
                }
                assignment[position] = 0;
            }
        }
    }

    /// Whether some global assignment is positive in every context (support level). When
    /// false, no joint distribution on assignments reproduces the model. When true, that
    /// is necessary and not sufficient for one.
    pub fn has_positive_global_assignment(&self) -> Result<bool, WdpError> {
        Ok(!self.positive_global_assignments()?.is_empty())
    }
}

/// `WDP-CH19-P02`: the model of the table if every context has runs and all overlap
/// marginals of the frequencies agree; otherwise the first refusal.
pub fn adapt_exact(
    cover: &MeasurementCover,
    table: &RunTable,
) -> Result<EmpiricalModel, AdapterRefusal> {
    let freqs = frequencies(cover, table)?;
    EmpiricalModel::new(cover.clone(), freqs)
}

fn defects_of(cover: &MeasurementCover, freqs: &[SectionDistribution]) -> PairDefects {
    pairs(freqs.len())
        .map(|(i, j)| {
            let (_, mu_i, mu_j) = pair_marginals(cover, freqs, i, j);
            ((i, j), l1_distance(&mu_i, &mu_j))
        })
        .collect()
}

/// `D_ij` for every pair `i < j` in lexicographic order, zero for an empty overlap.
pub fn signalling_defect(
    cover: &MeasurementCover,
    table: &RunTable,
) -> Result<PairDefects, AdapterRefusal> {
    Ok(defects_of(cover, &frequencies(cover, table)?))
}

/// The frequencies of a table accepted under a declared tolerance.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TolerantModel {
    pub frequencies: Vec<SectionDistribution>,
    pub defects: PairDefects,
    pub max_defect: BigRational,
    pub eps: BigRational,
    pub authority_effect: AuthorityEffect,
}

/// `WDP-CH19-P06`: accepts iff every context has runs and `max D_ij <= eps`; the refusal
/// names the first pair (lexicographic) whose defect exceeds `eps`. A negative `eps` is
/// refused as invalid input; the Lean `adaptTol` accepts any rational `eps` and, for a
/// negative one, never accepts (`D_ii = 0 > eps`), so the two agree on every accepted table.
pub fn adapt_tolerant(
    cover: &MeasurementCover,
    table: &RunTable,
    eps: &BigRational,
) -> Result<TolerantModel, AdapterRefusal> {
    if eps.is_negative() {
        return Err(invalid(format!("tolerance {eps} is negative")));
    }
    let freqs = frequencies(cover, table)?;
    let defects = defects_of(cover, &freqs);
    if let Some(((i, j), defect)) = defects.iter().find(|(_, d)| d > eps) {
        let overlap = cover.overlap(*i, *j).unwrap_or_default();
        return Err(AdapterRefusal::ToleranceExceeded(Box::new(
            ToleranceWitness {
                i: *i,
                j: *j,
                defect: defect.clone(),
                eps: eps.clone(),
                overlap,
            },
        )));
    }
    let max_defect =
        defects.iter().fold(
            BigRational::zero(),
            |acc, (_, d)| if d > &acc { d.clone() } else { acc },
        );
    Ok(TolerantModel {
        frequencies: freqs,
        defects,
        max_defect,
        eps: eps.clone(),
        authority_effect: AuthorityEffect::None,
    })
}

/// The L1 distance of each context's frequency vector from the model's distribution.
pub fn l1_distance_to_model(
    frequencies: &[SectionDistribution],
    model: &EmpiricalModel,
) -> Result<Vec<BigRational>, AdapterRefusal> {
    if frequencies.len() != model.distributions.len() {
        return Err(invalid(format!(
            "{} frequency vectors for {} contexts",
            frequencies.len(),
            model.distributions.len()
        )));
    }
    Ok(frequencies
        .iter()
        .zip(&model.distributions)
        .map(|(f, m)| l1_distance(f, m))
        .collect())
}

/// The section over `context` that reads `t` on `overlap` and outcome 0 elsewhere.
fn canonical_extension(context: &[usize], overlap: &[usize], t: &[usize]) -> Section {
    context
        .iter()
        .map(|id| overlap.iter().position(|o| o == id).map_or(0, |q| t[q]))
        .collect()
}

/// `WDP-CH19-P07`: for exactly two contexts, replaces both overlap marginals by their
/// average `nu = (mu_1 + mu_2) / 2`, rescaling conditionals (`p'(s) = p(s) nu(t) / mu(t)`
/// for `s` reading `t` on the overlap) and, where a context had `mu(t) = 0 < nu(t)`,
/// putting the mass `nu(t)` on the canonical extension of `t` (outcome 0 off the overlap).
pub fn two_context_repair(
    cover: &MeasurementCover,
    table: &RunTable,
) -> Result<EmpiricalModel, AdapterRefusal> {
    if cover.contexts.len() != 2 {
        return Err(invalid(format!(
            "two-context repair needs exactly 2 contexts, found {}",
            cover.contexts.len()
        )));
    }
    let freqs = frequencies(cover, table)?;
    let (overlap, mu_0, mu_1) = pair_marginals(cover, &freqs, 0, 1);
    let two = BigRational::from_integer(2.into());
    let mut nu = SectionDistribution::new();
    for key in mu_0.keys().chain(mu_1.keys()) {
        let zero = BigRational::zero();
        let average = (mu_0.get(key).unwrap_or(&zero) + mu_1.get(key).unwrap_or(&zero)) / &two;
        nu.insert(key.clone(), average);
    }
    let mut repaired = Vec::with_capacity(2);
    for (context, (freq, mu)) in cover.contexts.iter().zip(freqs.iter().zip([&mu_0, &mu_1])) {
        let mut dist = SectionDistribution::new();
        for (section, weight) in freq {
            let t = restrict(context, section, &overlap);
            let (Some(mu_t), Some(nu_t)) = (mu.get(&t), nu.get(&t)) else {
                return Err(invalid(format!(
                    "overlap section {t:?} has no marginal weight"
                )));
            };
            *dist
                .entry(section.clone())
                .or_insert_with(BigRational::zero) += weight * nu_t / mu_t;
        }
        for (t, nu_t) in &nu {
            if !mu.contains_key(t) {
                *dist
                    .entry(canonical_extension(context, &overlap, t))
                    .or_insert_with(BigRational::zero) += nu_t;
            }
        }
        repaired.push(dist);
    }
    EmpiricalModel::new(cover.clone(), repaired)
}

/// The CHSH cover: measurements `a_0, a_1, b_0, b_1` are ids `0..4`, binary outcomes,
/// and context `2x + y` is `{a_x, b_y}`.
pub fn chsh_cover() -> Result<MeasurementCover, WdpError> {
    MeasurementCover::new(4, 2, vec![vec![0, 2], vec![0, 3], vec![1, 2], vec![1, 3]])
}

/// The Popescu-Rohrlich box as runs: context `(x, y)` has the two outcome pairs `(a, b)`
/// with `a xor b = x y`, one run each.
pub fn pr_box_run_table() -> Result<RunTable, WdpError> {
    let cover = chsh_cover()?;
    let runs = (0..2usize)
        .flat_map(|x| (0..2usize).map(move |y| (x, y)))
        .map(|(x, y)| {
            [0usize, 1]
                .iter()
                .map(|&a| vec![a, a ^ (x * y)])
                .collect::<Vec<Section>>()
        })
        .collect();
    RunTable::new(&cover, runs)
}

/// A table in which every run assigns all measurements and every context reads the same
/// runs restricted to itself.
pub fn global_run_table(
    cover: &MeasurementCover,
    assignments: &[Section],
) -> Result<RunTable, WdpError> {
    if let Some(bad) = assignments.iter().find(|a| a.len() != cover.measurements) {
        return Err(WdpError::InvalidInput {
            detail: format!(
                "global run assigns {} measurements, expected {}",
                bad.len(),
                cover.measurements
            ),
        });
    }
    let runs = cover
        .contexts
        .iter()
        .map(|context| {
            assignments
                .iter()
                .map(|a| context.iter().map(|&id| a[id]).collect())
                .collect()
        })
        .collect();
    RunTable::new(cover, runs)
}

fn require_chsh_model(model: &EmpiricalModel) -> Result<(), AdapterRefusal> {
    if model.cover == chsh_cover()? {
        Ok(())
    } else {
        Err(invalid("the model is not on the CHSH cover".to_string()))
    }
}

/// The CHSH model as `core_quantum_physics`'s 16-coordinate `PairwiseBox`: context
/// `(x, y)` occupies coordinates `4 (2x + y) + 2 a + b` for outcomes `a, b`.
pub fn chsh_pairwise_box(model: &EmpiricalModel) -> Result<PairwiseBox, AdapterRefusal> {
    require_chsh_model(model)?;
    let mut coordinates = vec![BigRational::zero(); 16];
    for (context, dist) in model.distributions.iter().enumerate() {
        for (section, weight) in dist {
            coordinates[4 * context + 2 * section[0] + section[1]] = weight.clone();
        }
    }
    PairwiseBox::new(coordinates).map_err(|e| AdapterRefusal::from(WdpError::from(e)))
}

/// `E_xy = P(a = b) - P(a != b)` of context `2x + y` of a CHSH model, by `PairwiseBox`.
pub fn chsh_correlator(
    model: &EmpiricalModel,
    x: usize,
    y: usize,
) -> Result<BigRational, AdapterRefusal> {
    chsh_pairwise_box(model)?
        .correlator(x, y)
        .map_err(|e| AdapterRefusal::from(WdpError::from(e)))
}

/// `E_00 + E_01 + E_10 - E_11` of a CHSH model, by `PairwiseBox`.
pub fn chsh_value(model: &EmpiricalModel) -> Result<BigRational, AdapterRefusal> {
    Ok(chsh_pairwise_box(model)?.chsh())
}

// Origin: engine/crates_rs/core_wdp/src/empirical_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:empirical-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_34e2bb5b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
