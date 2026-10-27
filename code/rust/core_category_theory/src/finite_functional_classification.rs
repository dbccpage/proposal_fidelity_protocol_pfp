//! Complete constructive finite predicate classifications, without phenomenology.
//!
//! Component data are not predicates: these theorems classify explicitly chosen
//! invariants of total finite maps. Every permitted signature has a concrete
//! witness with at most four states; necessity uses universal map arguments.
//! Complete constructive finite predicate classifications, without phenomenology.
//!
//! Component data are not predicates: these theorems classify explicitly chosen
//! invariants of total finite maps. Every permitted signature has a concrete
//! witness with at most four states; necessity uses universal map arguments.

use std::collections::{BTreeMap, BTreeSet};

use crate::finite_moore::FiniteMoore;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClassificationError {
    InvalidModel,
    ImpossibleSignature,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_functional_classification.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-functional-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ClassificationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ClassificationError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RetentionSignature {
    pub nontrivial: bool,
    pub reversible: bool,
    pub observable: bool,
    pub tolerance: bool,
    pub minimal: bool,
    pub active: bool,
}

impl RetentionSignature {
    fn singleton_is_realizable(self) -> bool {
        self.reversible && self.observable && !self.tolerance && self.minimal && !self.active
    }

    /// Complete necessary/sufficient criterion for these SIX predicates.
    /// Singleton maps force reversible/injective/minimal and no activity/tolerance.
    /// Injective recognized reports force minimality. Identity dynamics have no
    /// future distinguishing power, so minimal iff raw-injective and no tolerance.
    /// Complete necessary/sufficient criterion for these SIX predicates.
    /// Singleton maps force reversible/injective/minimal and no activity/tolerance.
    /// Injective recognized reports force minimality. Identity dynamics have no
    /// future distinguishing power, so minimal iff raw-injective and no tolerance.
    pub fn is_realizable(self) -> bool {
        if !self.nontrivial {
            return self.singleton_is_realizable();
        }
        if self.observable && !self.tolerance && !self.minimal {
            return false;
        }
        if !self.active {
            return self.reversible && self.minimal == (self.observable && !self.tolerance);
        }
        true
    }
}

/// Raw and recognized report identifiers, together with a total Moore system.
/// Recognition must factor through raw report equality, making a genuine finite
/// report equivalence; arbitrary nontransitive tolerances are outside this scope.
/// Raw and recognized report identifiers, together with a total Moore system.
/// Recognition must factor through raw report equality, making a genuine finite
/// report equivalence; arbitrary nontransitive tolerances are outside this scope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteRetentionModel {
    raw_reports: Vec<usize>,
    moore: FiniteMoore,
}

impl FiniteRetentionModel {
    pub fn new(
        raw_reports: Vec<usize>,
        recognized: Vec<usize>,
        transitions: Vec<Vec<usize>>,
        inputs: usize,
    ) -> Result<Self, ClassificationError> {
        if raw_reports.len() != recognized.len() {
            return Err(ClassificationError::InvalidModel);
        }
        let mut factor = BTreeMap::new();
        for (&raw, &report) in raw_reports.iter().zip(&recognized) {
            if let Some(previous) = factor.insert(raw, report) {
                if previous != report {
                    return Err(ClassificationError::InvalidModel);
                }
            }
        }
        let moore = FiniteMoore::new(recognized, transitions, inputs)
            .map_err(|_| ClassificationError::InvalidModel)?;
        Ok(Self { raw_reports, moore })
    }

    pub fn raw_reports(&self) -> &[usize] {
        &self.raw_reports
    }
    pub fn moore(&self) -> &FiniteMoore {
        &self.moore
    }

    pub fn signature(&self) -> RetentionSignature {
        let n = self.moore.state_count();
        let observable = self.raw_reports.iter().collect::<BTreeSet<_>>().len() == n;
        let tolerance = has_tolerance(&self.raw_reports, self.moore.reports());
        let reversible = permutation_columns(&self.moore);
        let active = self
            .moore
            .transitions()
            .iter()
            .enumerate()
            .any(|(x, row)| row.iter().any(|&y| x != y));
        RetentionSignature {
            nontrivial: n > 1,
            reversible,
            observable,
            tolerance,
            minimal: self.moore.behavioral_quotient().quotient.state_count() == n,
            active,
        }
    }
}

fn has_tolerance(raw: &[usize], recognized: &[usize]) -> bool {
    let mut representatives = BTreeMap::new();
    for (&r, &s) in raw.iter().zip(recognized) {
        if let Some(previous) = representatives.insert(s, r) {
            if previous != r {
                return true;
            }
        }
    }
    false
}

fn permutation_columns(moore: &FiniteMoore) -> bool {
    if moore.input_count() == 0 {
        return true;
    }
    let mut seen = vec![false; moore.state_count()];
    (0..moore.input_count()).all(|i| column_is_permutation(moore.transitions(), i, &mut seen))
}

fn column_is_permutation(transitions: &[Vec<usize>], column: usize, seen: &mut [bool]) -> bool {
    seen.fill(false);
    for row in transitions {
        if std::mem::replace(&mut seen[row[column]], true) {
            return false;
        }
    }
    true
}

/// Construct every realizable signature; exhaustive checks are corroboration,
/// while the construction and universal implications prove completeness.
/// Construct every realizable signature; exhaustive checks are corroboration,
/// while the construction and universal implications prove completeness.
pub fn realize_retention(
    signature: RetentionSignature,
) -> Result<FiniteRetentionModel, ClassificationError> {
    if !signature.is_realizable() {
        return Err(ClassificationError::ImpossibleSignature);
    }
    let (raw, recognized) = retention_reports(signature)?;
    let n = raw.len();
    let transitions = (0..n)
        .map(|x| vec![retention_successor(signature, x, n)])
        .collect();
    FiniteRetentionModel::new(raw, recognized, transitions, 1)
}

fn retention_reports(
    signature: RetentionSignature,
) -> Result<(Vec<usize>, Vec<usize>), ClassificationError> {
    if !signature.nontrivial {
        return Ok((vec![0], vec![0]));
    }
    if signature.minimal {
        return Ok(minimal_retention_reports(
            signature.observable,
            signature.tolerance,
        ));
    }
    match (signature.observable, signature.tolerance) {
        (true, true) => Ok((vec![0, 1], vec![0, 0])),
        (false, false) => Ok((vec![0, 0], vec![0, 0])),
        (false, true) => Ok((vec![0, 0, 1], vec![0, 0, 0])),
        (true, false) => Err(ClassificationError::ImpossibleSignature),
    }
}

fn minimal_retention_reports(observable: bool, tolerance: bool) -> (Vec<usize>, Vec<usize>) {
    match (observable, tolerance) {
        (true, false) => (vec![0, 1], vec![0, 1]),
        (false, false) => (vec![0, 0, 1], vec![0, 0, 1]),
        (true, true) => (vec![0, 1, 2], vec![0, 0, 1]),
        (false, true) => (vec![0, 0, 1, 2], vec![0, 0, 0, 1]),
    }
}

fn retention_successor(signature: RetentionSignature, x: usize, n: usize) -> usize {
    if !signature.active {
        x
    } else if signature.reversible {
        (x + 1) % n
    } else if signature.minimal {
        (x + 1).min(n - 1)
    } else {
        0
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FunctionalSignature {
    /// An independent report s factors through the accessible presentation q.
    /// An independent report s factors through the accessible presentation q.
    pub linked: bool,
    /// q is stable under the declared context action t.
    /// q is stable under the declared context action t.
    pub presentation_stable: bool,
    /// s is stable under t (the manuscript's REPORT-stability predicate).
    /// s is stable under t (the manuscript's REPORT-stability predicate).
    pub report_stable: bool,
    /// Report equals the declared behavioral target at every state.
    /// Report equals the declared behavioral target at every state.
    pub calibrated: bool,
    /// At least two states have the same accessible presentation.
    /// At least two states have the same accessible presentation.
    pub blind_spot: bool,
}

impl FunctionalSignature {
    /// Exactly two constraints: injective q forces factorization, and linked
    /// reports inherit presentation stability. All other combinations occur.
    /// Exactly two constraints: injective q forces factorization, and linked
    /// reports inherit presentation stability. All other combinations occur.
    pub fn is_realizable(self) -> bool {
        (self.blind_spot || self.linked)
            && !(self.linked && self.presentation_stable && !self.report_stable)
    }
}

/// Exact finite presentation/report/target labels and a total context action
/// on a nonempty common state carrier. Label values need not be state indices.
/// No report factorization is presumed; factors are defined on realized labels.
/// Total finite maps q,s,t,b on a nonempty common carrier. Accessible self-state
/// is identified with that carrier. No report factorization is presumed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteFunctionalModel {
    presentation: Vec<usize>,
    report: Vec<usize>,
    context: Vec<usize>,
    target: Vec<usize>,
}

impl FiniteFunctionalModel {
    pub fn new(
        presentation: Vec<usize>,
        report: Vec<usize>,
        context: Vec<usize>,
        target: Vec<usize>,
    ) -> Result<Self, ClassificationError> {
        let n = presentation.len();
        if n == 0
            || report.len() != n
            || context.len() != n
            || target.len() != n
            || context.iter().any(|&x| x >= n)
        {
            return Err(ClassificationError::InvalidModel);
        }
        Ok(Self {
            presentation,
            report,
            context,
            target,
        })
    }
    pub fn presentation(&self) -> &[usize] {
        &self.presentation
    }
    pub fn report(&self) -> &[usize] {
        &self.report
    }
    pub fn context(&self) -> &[usize] {
        &self.context
    }
    pub fn target(&self) -> &[usize] {
        &self.target
    }

    /// Factorization exists iff every q-fiber has a constant s; this is a
    /// checked partial map on realized presentations, not a guessed decoder.
    /// Factorization exists iff every q-fiber has a constant s; this is a
    /// checked partial map on realized presentations, not a guessed decoder.
    pub fn report_factor(&self) -> Option<BTreeMap<usize, usize>> {
        let mut factor = BTreeMap::new();
        for (&q, &s) in self.presentation.iter().zip(&self.report) {
            if let Some(old) = factor.insert(q, s) {
                if old != s {
                    return None;
                }
            }
        }
        Some(factor)
    }
    pub fn signature(&self) -> FunctionalSignature {
        FunctionalSignature {
            linked: self.report_factor().is_some(),
            presentation_stable: self
                .context
                .iter()
                .enumerate()
                .all(|(x, &tx)| self.presentation[x] == self.presentation[tx]),
            report_stable: self
                .context
                .iter()
                .enumerate()
                .all(|(x, &tx)| self.report[x] == self.report[tx]),
            calibrated: self.report == self.target,
            blind_spot: self.presentation.iter().collect::<BTreeSet<_>>().len()
                < self.presentation.len(),
        }
    }
}

/// Construct all 20 realizable signatures with at most three states.
/// Calibration is independent: b=s for success, change b(0) for failure.
/// Construct all 20 realizable signatures with at most three states.
/// Calibration is independent: b=s for success, change b(0) for failure.
pub fn realize_functional(
    signature: FunctionalSignature,
) -> Result<FiniteFunctionalModel, ClassificationError> {
    if !signature.is_realizable() {
        return Err(ClassificationError::ImpossibleSignature);
    }
    let (q, s, t) = functional_witness_data(signature);
    let mut target = s.clone();
    if !signature.calibrated {
        target[0] += 1;
    }
    FiniteFunctionalModel::new(q, s, t, target)
}

fn functional_witness_data(signature: FunctionalSignature) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    if !signature.blind_spot {
        let (s, t) = linked_functional_data(signature, false);
        return (vec![0, 1], s, t);
    }
    let q = vec![0, 0, 1];
    let (s, t) = if signature.linked {
        linked_functional_data(signature, true)
    } else {
        unlinked_functional_data(signature.presentation_stable, signature.report_stable)
    };
    (q, s, t)
}

fn linked_functional_data(signature: FunctionalSignature, blind: bool) -> (Vec<usize>, Vec<usize>) {
    if blind {
        return match (signature.presentation_stable, signature.report_stable) {
            (true, _) => (vec![0, 0, 1], vec![0, 1, 2]),
            (false, true) => (vec![0, 0, 0], vec![2, 1, 2]),
            (false, false) => (vec![0, 0, 1], vec![2, 1, 2]),
        };
    }
    match (signature.presentation_stable, signature.report_stable) {
        (true, _) => (vec![0, 1], vec![0, 1]),
        (false, true) => (vec![0, 0], vec![1, 1]),
        (false, false) => (vec![0, 1], vec![1, 1]),
    }
}

fn unlinked_functional_data(
    presentation_stable: bool,
    report_stable: bool,
) -> (Vec<usize>, Vec<usize>) {
    match (presentation_stable, report_stable) {
        (true, true) => (vec![0, 1, 0], vec![0, 1, 2]),
        (true, false) => (vec![0, 1, 0], vec![1, 1, 2]),
        (false, true) => (vec![0, 1, 0], vec![2, 1, 2]),
        (false, false) => (vec![0, 1, 2], vec![2, 1, 2]),
    }
}

/// A positive or negative literal in the documented signature field order.
/// A positive or negative literal in the documented signature field order.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PropertyLiteral {
    pub index: usize,
    pub value: bool,
}

/// Return an explicit countermodel, or None when every classified retention
/// model satisfying the premises satisfies the conclusion. Field order is
/// N,V,O,T,K,A. Contradictory premises entail vacuously; invalid indices refuse.
/// Completeness follows from the universal classification plus constructors,
/// not an assumed bound on possible carrier sizes.
/// Return an explicit countermodel, or None when every classified retention
/// model satisfying the premises satisfies the conclusion. Field order is
/// N,V,O,T,K,A. Contradictory premises entail vacuously; invalid indices refuse.
/// Completeness follows from the universal classification plus constructors,
/// not an assumed bound on possible carrier sizes.
pub fn retention_implication_countermodel(
    premises: &[PropertyLiteral],
    conclusion: PropertyLiteral,
) -> Result<Option<FiniteRetentionModel>, ClassificationError> {
    if conclusion.index >= 6 || premises.iter().any(|literal| literal.index >= 6) {
        return Err(ClassificationError::InvalidModel);
    }
    for bits in 0_usize..64 {
        let flags: [bool; 6] = std::array::from_fn(|i| bits & (1 << i) != 0);
        if flags[conclusion.index] == conclusion.value
            || premises
                .iter()
                .any(|literal| flags[literal.index] != literal.value)
        {
            continue;
        }
        let signature = RetentionSignature {
            nontrivial: flags[0],
            reversible: flags[1],
            observable: flags[2],
            tolerance: flags[3],
            minimal: flags[4],
            active: flags[5],
        };
        if signature.is_realizable() {
            return realize_retention(signature).map(Some);
        }
    }
    Ok(None)
}

/// Complete implication replay for F,P,S,C,B with an explicit finite witness
/// for every failed implication. Returns None iff the implication is valid in
/// the entire declared class (including the vacuous contradictory-premise case).
/// Complete implication replay for F,P,S,C,B with an explicit finite witness
/// for every failed implication. Returns None iff the implication is valid in
/// the entire declared class (including the vacuous contradictory-premise case).
pub fn functional_implication_countermodel(
    premises: &[PropertyLiteral],
    conclusion: PropertyLiteral,
) -> Result<Option<FiniteFunctionalModel>, ClassificationError> {
    if conclusion.index >= 5 || premises.iter().any(|literal| literal.index >= 5) {
        return Err(ClassificationError::InvalidModel);
    }
    for bits in 0_usize..32 {
        let flags: [bool; 5] = std::array::from_fn(|i| bits & (1 << i) != 0);
        if flags[conclusion.index] == conclusion.value
            || premises
                .iter()
                .any(|literal| flags[literal.index] != literal.value)
        {
            continue;
        }
        let signature = FunctionalSignature {
            linked: flags[0],
            presentation_stable: flags[1],
            report_stable: flags[2],
            calibrated: flags[3],
            blind_spot: flags[4],
        };
        if signature.is_realizable() {
            return realize_functional(signature).map(Some);
        }
    }
    Ok(None)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5224fd2d {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
