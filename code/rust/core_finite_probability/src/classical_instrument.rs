//! Finite classical instruments, their composition and coarse-graining, and conditional
//! two-party boxes with the no-signalling and local hidden-variable questions kept apart.
//!
//! A [`ClassicalInstrument`] from `X` to `Y` with outcome set `A` is a family of nonnegative
//! rational matrices `K_a in Q^(Y x X)` (column convention: `K_a(y, x)` is the weight of
//! moving from `x` to `y` while reporting `a`) with `sum_(a, y) K_a(y, x) = 1` for every
//! input `x`. Its forgotten map `U(K) = sum_a K_a` is column-stochastic.
//!
//! - Nonadaptive composition `(L o K)_(a, b) = L_b K_a`. Forgetting commutes with it:
//!   `U(L o K) = U(L) U(K)`. The equality is a theorem of the nonadaptive premise and is
//!   re-checked on every call by [`ClassicalInstrument::compose`] through
//!   [`ClassicalInstrument::forget`].
//! - Adaptive composition picks the second instrument from the first outcome:
//!   `(a, b) -> L^a_b K_a`. Forgetting gives `sum_a U(L^a) K_a`, which in general is not
//!   `U(L-bar) U(K)` for any single continuation; [`ClassicalInstrument::compose_adaptive`]
//!   computes it and the tests keep the counterexample.
//! - Coarse-graining sums the outcome maps over the classes of a declared function
//!   `A -> A'`.
//!
//! A [`ConditionalBox`] is a table `p(a, b | x, y)`. Two questions about it are kept apart:
//!
//! - No-signalling ([`ConditionalBox::signalling_witness`]): whether each party's marginal
//!   is independent of the other party's input. A failure is returned as an exact witness
//!   (party, input, outcome, the two other-party inputs and both sums).
//! - A local hidden-variable table ([`ConditionalBox::verify_local_model`]): a weighted
//!   family of deterministic assignments reproducing every entry exactly. The refutation
//!   [`ConditionalBox::support_compatible_assignments`] returns the deterministic
//!   assignments that never use a zero-probability entry; when that set is empty no local
//!   hidden-variable table exists, because every deterministic component of such a table
//!   lies inside the support.
//!
//! The PR box is no-signalling and has no support-compatible assignment. A no-signalling
//! certificate is therefore not a hidden-variable certificate.
//!
//! AuthorityEffect: None.

use std::collections::BTreeMap;

use num_traits::{One, Zero};
use core_number_theory::rational::Rational;

/// Refusals of the instrument and box layer.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClassicalInstrumentError {
    #[error("the input or output carrier is empty")]
    EmptyCarrier,
    #[error("the outcome family is empty")]
    EmptyOutcomeFamily,
    #[error("outcome {outcome}: expected a {rows}x{cols} matrix")]
    ShapeMismatch {
        outcome: usize,
        rows: usize,
        cols: usize,
    },
    #[error("outcome {outcome} has a negative entry at ({row}, {col})")]
    NegativeEntry {
        outcome: usize,
        row: usize,
        col: usize,
    },
    #[error("input column {col} carries total mass {total}, not one")]
    NormalizationDefect { col: usize, total: Rational },
    #[error("outcome {0} is not in the outcome family")]
    UnknownOutcome(usize),
    #[error("the second instrument reads {actual} inputs, the first writes {expected}")]
    CompositionMismatch { expected: usize, actual: usize },
    #[error("the coarse-graining map is not a function from the outcomes onto a declared range")]
    InvalidCoarseGraining,
    #[error("the state is not a probability vector of the declared length")]
    InvalidState,
    #[error("conditioning on an outcome of probability zero")]
    ZeroProbabilityConditioning,
    #[error("the conditional table is missing entries or ragged at input pair ({x}, {y})")]
    PartialTable { x: usize, y: usize },
    #[error("{actual} continuations supplied for {expected} outcomes")]
    ContinuationCount { expected: usize, actual: usize },
    #[error("the forgotten composite differs from the product of the forgotten maps")]
    ForgetLawDefect,
    #[error("the enumeration exceeds its declared budget")]
    ResourceLimit,
}

type Matrix = Vec<Vec<Rational>>;

fn mat_mul(left: &Matrix, right: &Matrix) -> Matrix {
    let rows = left.len();
    let inner = right.len();
    let cols = right.first().map_or(0, Vec::len);
    let mut out = vec![vec![Rational::zero(); cols]; rows];
    for (i, row) in left.iter().enumerate() {
        for k in 0..inner {
            if row[k].is_zero() {
                continue;
            }
            for j in 0..cols {
                out[i][j] += &row[k] * &right[k][j];
            }
        }
    }
    out
}

fn mat_add(left: &Matrix, right: &Matrix) -> Matrix {
    left.iter()
        .zip(right)
        .map(|(a, b)| a.iter().zip(b).map(|(x, y)| x + y).collect())
        .collect()
}

/// A finite classical instrument; every value has passed [`ClassicalInstrument::try_new`].
#[derive(Debug, Clone)]
pub struct ClassicalInstrument {
    inputs: usize,
    outputs: usize,
    maps: Vec<Matrix>,
}

impl PartialEq for ClassicalInstrument {
    fn eq(&self, other: &Self) -> bool {
        self.inputs == other.inputs && self.outputs == other.outputs && self.maps == other.maps
    }
}
impl Eq for ClassicalInstrument {}

impl ClassicalInstrument {
    fn accumulate_outcome_map(
        outcome: usize,
        k: &Matrix,
        inputs: usize,
        outputs: usize,
        totals: &mut [Rational],
    ) -> Result<(), ClassicalInstrumentError> {
        if k.len() != outputs || k.iter().any(|row| row.len() != inputs) {
            return Err(ClassicalInstrumentError::ShapeMismatch {
                outcome,
                rows: outputs,
                cols: inputs,
            });
        }
        for (row, entries) in k.iter().enumerate() {
            for (col, value) in entries.iter().enumerate() {
                if *value < Rational::zero() {
                    return Err(ClassicalInstrumentError::NegativeEntry { outcome, row, col });
                }
                totals[col] += value;
            }
        }
        Ok(())
    }

    /// Admits `maps[a]` as `outputs x inputs` nonnegative matrices whose total column
    /// sums are one.
    pub fn try_new(
        inputs: usize,
        outputs: usize,
        maps: Vec<Matrix>,
    ) -> Result<Self, ClassicalInstrumentError> {
        if inputs == 0 || outputs == 0 {
            return Err(ClassicalInstrumentError::EmptyCarrier);
        }
        if maps.is_empty() {
            return Err(ClassicalInstrumentError::EmptyOutcomeFamily);
        }
        let mut totals = vec![Rational::zero(); inputs];
        for (outcome, k) in maps.iter().enumerate() {
            Self::accumulate_outcome_map(outcome, k, inputs, outputs, &mut totals)?;
        }
        for (col, total) in totals.into_iter().enumerate() {
            if !total.is_one() {
                return Err(ClassicalInstrumentError::NormalizationDefect { col, total });
            }
        }
        Ok(Self {
            inputs,
            outputs,
            maps,
        })
    }

    pub fn inputs(&self) -> usize {
        self.inputs
    }
    pub fn outputs(&self) -> usize {
        self.outputs
    }
    pub fn outcome_count(&self) -> usize {
        self.maps.len()
    }
    /// The outcome map `K_a`.
    pub fn map(&self, outcome: usize) -> Result<&Matrix, ClassicalInstrumentError> {
        self.maps
            .get(outcome)
            .ok_or(ClassicalInstrumentError::UnknownOutcome(outcome))
    }

    /// The forgotten column-stochastic map `U(K) = sum_a K_a`.
    pub fn forget(&self) -> Matrix {
        let mut out = vec![vec![Rational::zero(); self.inputs]; self.outputs];
        for k in &self.maps {
            out = mat_add(&out, k);
        }
        out
    }

    fn check_state(&self, p: &[Rational]) -> Result<(), ClassicalInstrumentError> {
        if p.len() != self.inputs
            || p.iter().any(|v| *v < Rational::zero())
            || !p.iter().sum::<Rational>().is_one()
        {
            return Err(ClassicalInstrumentError::InvalidState);
        }
        Ok(())
    }

    /// Unnormalised post-measurement vector `K_a p`.
    pub fn apply(
        &self,
        outcome: usize,
        p: &[Rational],
    ) -> Result<Vec<Rational>, ClassicalInstrumentError> {
        self.check_state(p)?;
        let k = self.map(outcome)?;
        Ok(k.iter()
            .map(|row| row.iter().zip(p).map(|(a, b)| a * b).sum())
            .collect())
    }

    /// Outcome probabilities `Pr(a) = 1^T K_a p`.
    pub fn outcome_masses(&self, p: &[Rational]) -> Result<Vec<Rational>, ClassicalInstrumentError> {
        (0..self.maps.len())
            .map(|a| Ok(self.apply(a, p)?.into_iter().sum()))
            .collect()
    }

    /// Conditional state `K_a p / Pr(a)`; refuses an outcome of probability zero.
    pub fn condition(
        &self,
        outcome: usize,
        p: &[Rational],
    ) -> Result<Vec<Rational>, ClassicalInstrumentError> {
        let v = self.apply(outcome, p)?;
        let mass: Rational = v.iter().sum();
        if mass.is_zero() {
            return Err(ClassicalInstrumentError::ZeroProbabilityConditioning);
        }
        Ok(v.into_iter().map(|x| x / &mass).collect())
    }

    /// Nonadaptive sequential composition `(next o self)_(a, b) = next_b self_a`, outcome
    /// index `a * |B| + b`. The forgetting law `U(next o self) = U(next) U(self)` is
    /// re-checked; a failure would be a defect of this code, reported as a refusal.
    pub fn compose(&self, next: &Self) -> Result<Self, ClassicalInstrumentError> {
        if next.inputs != self.outputs {
            return Err(ClassicalInstrumentError::CompositionMismatch {
                expected: self.outputs,
                actual: next.inputs,
            });
        }
        let mut maps = Vec::with_capacity(self.maps.len() * next.maps.len());
        for k in &self.maps {
            for l in &next.maps {
                maps.push(mat_mul(l, k));
            }
        }
        let composed = Self::try_new(self.inputs, next.outputs, maps)?;
        if composed.forget() != mat_mul(&next.forget(), &self.forget()) {
            return Err(ClassicalInstrumentError::ForgetLawDefect);
        }
        Ok(composed)
    }

    /// Adaptive composition: `continuations[a]` is applied after outcome `a`; the joint
    /// outcome `(a, b)` has map `L^a_b K_a` and index `a * |B| + b`. Every continuation
    /// must read this instrument's outputs and share one outcome count and output size.
    pub fn compose_adaptive(&self, continuations: &[Self]) -> Result<Self, ClassicalInstrumentError> {
        if continuations.len() != self.maps.len() {
            return Err(ClassicalInstrumentError::ContinuationCount {
                expected: self.maps.len(),
                actual: continuations.len(),
            });
        }
        let first = &continuations[0];
        let mut maps = Vec::new();
        for (k, l) in self.maps.iter().zip(continuations) {
            if l.inputs != self.outputs {
                return Err(ClassicalInstrumentError::CompositionMismatch {
                    expected: self.outputs,
                    actual: l.inputs,
                });
            }
            if l.outputs != first.outputs || l.maps.len() != first.maps.len() {
                return Err(ClassicalInstrumentError::CompositionMismatch {
                    expected: first.outputs,
                    actual: l.outputs,
                });
            }
            for lb in &l.maps {
                maps.push(mat_mul(lb, k));
            }
        }
        Self::try_new(self.inputs, first.outputs, maps)
    }

    /// Coarse-graining along `group: A -> {0..target_count-1}`: `K'_c = sum_(g(a) = c) K_a`.
    pub fn coarse_grain(
        &self,
        group: &[usize],
        target_count: usize,
    ) -> Result<Self, ClassicalInstrumentError> {
        if group.len() != self.maps.len()
            || target_count == 0
            || group.iter().any(|&c| c >= target_count)
        {
            return Err(ClassicalInstrumentError::InvalidCoarseGraining);
        }
        let zero = vec![vec![Rational::zero(); self.inputs]; self.outputs];
        let mut maps = vec![zero; target_count];
        for (a, &c) in group.iter().enumerate() {
            maps[c] = mat_add(&maps[c], &self.maps[a]);
        }
        Self::try_new(self.inputs, self.outputs, maps)
    }

    /// Applies the instrument to the first factor of a joint distribution `p(x, z)`; the
    /// result is `p_a(y, z) = sum_x K_a(y, x) p(x, z)`.
    pub fn apply_local(&self, joint: &[Vec<Rational>]) -> Result<Vec<Matrix>, ClassicalInstrumentError> {
        let cols = joint.first().map_or(0, Vec::len);
        if joint.len() != self.inputs
            || cols == 0
            || joint.iter().any(|r| r.len() != cols || r.iter().any(|v| *v < Rational::zero()))
            || !joint.iter().flatten().sum::<Rational>().is_one()
        {
            return Err(ClassicalInstrumentError::InvalidState);
        }
        let joint: Matrix = joint.to_vec();
        Ok(self.maps.iter().map(|k| mat_mul(k, &joint)).collect())
    }
}

/// Second-factor marginal `q(z) = sum_y p(y, z)` of a joint table.
pub fn second_marginal(joint: &[Vec<Rational>]) -> Vec<Rational> {
    let cols = joint.first().map_or(0, Vec::len);
    (0..cols)
        .map(|z| joint.iter().map(|row| row[z].clone()).sum())
        .collect()
}

/// Which party a signalling witness concerns.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Party {
    Alice,
    Bob,
}

/// An exact signalling witness: the marginal of `party` at `(input, outcome)` differs
/// between the other party's inputs `other_inputs.0` and `other_inputs.1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignallingWitness {
    pub party: Party,
    pub input: usize,
    pub outcome: usize,
    pub other_inputs: (usize, usize),
    pub sums: (Rational, Rational),
}

/// A weighted family of deterministic assignments `(f, g)`, `f: X -> A`, `g: Y -> B`.
/// Kept as its own type: it is a hidden-variable table, not a no-signalling certificate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalHiddenVariableTable {
    pub weights: BTreeMap<(Vec<usize>, Vec<usize>), Rational>,
}

/// A conditional two-party table `p(a, b | x, y)`, indexed `entries[x][y][a][b]`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConditionalBox {
    inputs: (usize, usize),
    outputs: (usize, usize),
    entries: Vec<Vec<Matrix>>,
}

impl ConditionalBox {
    fn validate_box_cell(
        entries: &[Vec<Matrix>],
        inputs: (usize, usize),
        outputs: (usize, usize),
        x: usize,
        y: usize,
    ) -> Result<(), ClassicalInstrumentError> {
        let table = entries
            .get(x)
            .and_then(|r| r.get(y))
            .ok_or(ClassicalInstrumentError::PartialTable { x, y })?;
        if table.len() != outputs.0 || table.iter().any(|r| r.len() != outputs.1) {
            return Err(ClassicalInstrumentError::PartialTable { x, y });
        }
        if table.iter().flatten().any(|v| *v < Rational::zero()) {
            return Err(ClassicalInstrumentError::NegativeEntry {
                outcome: x * inputs.1 + y,
                row: 0,
                col: 0,
            });
        }
        let total: Rational = table.iter().flatten().sum();
        if !total.is_one() {
            return Err(ClassicalInstrumentError::NormalizationDefect {
                col: x * inputs.1 + y,
                total,
            });
        }
        Ok(())
    }

    /// Admits a complete nonnegative table normalised at every input pair.
    pub fn try_new(
        inputs: (usize, usize),
        outputs: (usize, usize),
        entries: Vec<Vec<Matrix>>,
    ) -> Result<Self, ClassicalInstrumentError> {
        if inputs.0 == 0 || inputs.1 == 0 || outputs.0 == 0 || outputs.1 == 0 {
            return Err(ClassicalInstrumentError::EmptyCarrier);
        }
        for x in 0..inputs.0 {
            for y in 0..inputs.1 {
                Self::validate_box_cell(&entries, inputs, outputs, x, y)?;
            }
            if entries[x].len() != inputs.1 {
                return Err(ClassicalInstrumentError::PartialTable { x, y: inputs.1 });
            }
        }
        if entries.len() != inputs.0 {
            return Err(ClassicalInstrumentError::PartialTable { x: inputs.0, y: 0 });
        }
        Ok(Self {
            inputs,
            outputs,
            entries,
        })
    }

    /// The PR box: `p(a, b | x, y) = 1/2` when `a xor b = x y`, zero otherwise.
    pub fn pr_box() -> Self {
        let half = Rational::new(1.into(), 2.into());
        let entries = (0..2)
            .map(|x| {
                (0..2)
                    .map(|y| {
                        (0..2)
                            .map(|a| {
                                (0..2)
                                    .map(|b| {
                                        if (a ^ b) == (x & y) {
                                            half.clone()
                                        } else {
                                            Rational::zero()
                                        }
                                    })
                                    .collect()
                            })
                            .collect()
                    })
                    .collect()
            })
            .collect();
        Self {
            inputs: (2, 2),
            outputs: (2, 2),
            entries,
        }
    }

    pub fn entry(&self, a: usize, b: usize, x: usize, y: usize) -> Option<&Rational> {
        self.entries.get(x)?.get(y)?.get(a)?.get(b)
    }

    /// The first failure of no-signalling in a fixed scan order, or `None`.
    pub fn signalling_witness(&self) -> Option<SignallingWitness> {
        let (nx, ny) = self.inputs;
        let (na, nb) = self.outputs;
        for x in 0..nx {
            for a in 0..na {
                let s0: Rational = self.entries[x][0][a].iter().sum();
                for y in 1..ny {
                    let s1: Rational = self.entries[x][y][a].iter().sum();
                    if s1 != s0 {
                        return Some(SignallingWitness {
                            party: Party::Alice,
                            input: x,
                            outcome: a,
                            other_inputs: (0, y),
                            sums: (s0, s1),
                        });
                    }
                }
            }
        }
        for y in 0..ny {
            for b in 0..nb {
                let s0: Rational = (0..na).map(|a| self.entries[0][y][a][b].clone()).sum();
                for x in 1..nx {
                    let s1: Rational = (0..na).map(|a| self.entries[x][y][a][b].clone()).sum();
                    if s1 != s0 {
                        return Some(SignallingWitness {
                            party: Party::Bob,
                            input: y,
                            outcome: b,
                            other_inputs: (0, x),
                            sums: (s0, s1),
                        });
                    }
                }
            }
        }
        None
    }

    fn assignments(count: usize, values: usize, budget: usize) -> Result<Vec<Vec<usize>>, ClassicalInstrumentError> {
        let mut total = 1usize;
        for _ in 0..count {
            total = total
                .checked_mul(values)
                .filter(|t| *t <= budget)
                .ok_or(ClassicalInstrumentError::ResourceLimit)?;
        }
        Ok((0..total)
            .map(|mut code| {
                (0..count)
                    .map(|_| {
                        let v = code % values;
                        code /= values;
                        v
                    })
                    .collect()
            })
            .collect())
    }

    /// Every deterministic assignment `(f, g)` with `p(f(x), g(y) | x, y) > 0` for every
    /// input pair. An empty result refutes every local hidden-variable table.
    pub fn support_compatible_assignments(
        &self,
        budget: usize,
    ) -> Result<Vec<(Vec<usize>, Vec<usize>)>, ClassicalInstrumentError> {
        let fs = Self::assignments(self.inputs.0, self.outputs.0, budget)?;
        let gs = Self::assignments(self.inputs.1, self.outputs.1, budget)?;
        if fs.len().checked_mul(gs.len()).is_none_or(|n| n > budget) {
            return Err(ClassicalInstrumentError::ResourceLimit);
        }
        let mut out = Vec::new();
        for f in &fs {
            for g in &gs {
                let ok = (0..self.inputs.0).all(|x| {
                    (0..self.inputs.1).all(|y| !self.entries[x][y][f[x]][g[y]].is_zero())
                });
                if ok {
                    out.push((f.clone(), g.clone()));
                }
            }
        }
        Ok(out)
    }

    fn valid_model_assignments(&self, model: &LocalHiddenVariableTable) -> bool {
        let (nx, ny) = self.inputs;
        let (na, nb) = self.outputs;
        model.weights.keys().all(|(f, g)| {
            f.len() == nx && g.len() == ny && f.iter().all(|&a| a < na) && g.iter().all(|&b| b < nb)
        })
    }

    fn entry_matches_model(
        &self,
        model: &LocalHiddenVariableTable,
        x: usize,
        y: usize,
        a: usize,
        b: usize,
    ) -> bool {
        let replay: Rational = model
            .weights
            .iter()
            .filter(|((f, g), _)| f[x] == a && g[y] == b)
            .map(|(_, w)| w.clone())
            .sum();
        replay == self.entries[x][y][a][b]
    }

    /// Exact replay of a supplied hidden-variable table: nonnegative weights summing to one,
    /// assignments inside the carriers, and every entry reproduced.
    pub fn verify_local_model(&self, model: &LocalHiddenVariableTable) -> bool {
        let total: Rational = model.weights.values().sum();
        if !total.is_one()
            || model.weights.values().any(|w| *w < Rational::zero())
            || !self.valid_model_assignments(model)
        {
            return false;
        }
        let (nx, ny) = self.inputs;
        let (na, nb) = self.outputs;
        for x in 0..nx {
            for y in 0..ny {
                for a in 0..na {
                    for b in 0..nb {
                        if !self.entry_matches_model(model, x, y, a, b) {
                            return false;
                        }
                    }
                }
            }
        }
        true
    }

    /// The CHSH sum `E00 + E01 + E10 - E11` of a binary box, `E_xy = sum (-1)^(a+b) p`.
    pub fn chsh(&self) -> Option<Rational> {
        if self.inputs != (2, 2) || self.outputs != (2, 2) {
            return None;
        }
        let mut s = Rational::zero();
        for x in 0..2 {
            for y in 0..2 {
                let mut e = Rational::zero();
                for a in 0..2 {
                    for b in 0..2 {
                        let v = &self.entries[x][y][a][b];
                        if (a + b) % 2 == 0 {
                            e += v;
                        } else {
                            e -= v;
                        }
                    }
                }
                if x * y == 1 {
                    s -= e;
                } else {
                    s += e;
                }
            }
        }
        Some(s)
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/classical_instrument.rs
// Claim: urn:core:crates_rs:core-finite-probability:classical-instrument:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};

    fn m(rows: &[&[(i64, i64)]]) -> Matrix {
        rows.iter()
            .map(|r| r.iter().map(|&(n, d)| rq(n, d)).collect())
            .collect()
    }

    fn report_k() -> ClassicalInstrument {
        ClassicalInstrument::try_new(
            2,
            2,
            vec![
                m(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 3)]]),
                m(&[&[(1, 2), (0, 1)], &[(0, 1), (2, 3)]]),
            ],
        )
        .expect("fixture is an instrument")
    }

    fn report_l() -> ClassicalInstrument {
        ClassicalInstrument::try_new(
            2,
            2,
            vec![
                m(&[&[(1, 3), (1, 2)], &[(0, 1), (0, 1)]]),
                m(&[&[(0, 1), (0, 1)], &[(2, 3), (1, 2)]]),
            ],
        )
        .expect("fixture is an instrument")
    }

    #[test]
    fn report_composition_masses_and_forgotten_state() {
        let lk = report_k().compose(&report_l()).expect("compatible");
        assert_eq!(lk.map(0).unwrap(), &m(&[&[(1, 6), (1, 6)], &[(0, 1), (0, 1)]]));
        assert_eq!(lk.map(1).unwrap(), &m(&[&[(0, 1), (0, 1)], &[(1, 3), (1, 6)]]));
        assert_eq!(lk.map(2).unwrap(), &m(&[&[(1, 6), (1, 3)], &[(0, 1), (0, 1)]]));
        assert_eq!(lk.map(3).unwrap(), &m(&[&[(0, 1), (0, 1)], &[(1, 3), (1, 3)]]));
        let p = vec![rq(2, 5), rq(3, 5)];
        assert_eq!(
            lk.outcome_masses(&p).unwrap(),
            vec![rq(1, 6), rq(7, 30), rq(4, 15), rq(1, 3)]
        );
        let forgotten: Vec<Rational> = lk
            .forget()
            .iter()
            .map(|row| row.iter().zip(&p).map(|(a, b)| a * b).sum())
            .collect();
        assert_eq!(forgotten, vec![rq(13, 30), rq(17, 30)]);
        // U(L o K) = U(L) U(K).
        assert_eq!(lk.forget(), mat_mul(&report_l().forget(), &report_k().forget()));
    }

    #[test]
    fn coarse_graining_sums_classes_and_refuses_bad_maps() {
        let lk = report_k().compose(&report_l()).unwrap();
        // Keep only the second outcome b: classes {(0,0),(1,0)} and {(0,1),(1,1)}.
        let by_b = lk.coarse_grain(&[0, 1, 0, 1], 2).unwrap();
        assert_eq!(by_b.map(0).unwrap(), &m(&[&[(1, 3), (1, 2)], &[(0, 1), (0, 1)]]));
        assert_eq!(by_b.forget(), lk.forget());
        // Full coarse-graining is the forgotten map.
        assert_eq!(lk.coarse_grain(&[0, 0, 0, 0], 1).unwrap().map(0).unwrap(), &lk.forget());
        assert_eq!(lk.coarse_grain(&[0, 1, 2], 3), Err(ClassicalInstrumentError::InvalidCoarseGraining));
        assert_eq!(lk.coarse_grain(&[0, 1, 2, 3], 3), Err(ClassicalInstrumentError::InvalidCoarseGraining));
        assert_eq!(lk.coarse_grain(&[], 0), Err(ClassicalInstrumentError::InvalidCoarseGraining));
    }

    #[test]
    fn adaptive_control_breaks_the_nonadaptive_forget_formula() {
        let k = ClassicalInstrument::try_new(2, 2, vec![m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]), m(&[&[(0, 1), (0, 1)], &[(0, 1), (1, 1)]])]).unwrap();
        let identity = ClassicalInstrument::try_new(2, 2, vec![m(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)]])]).unwrap();
        let swap = ClassicalInstrument::try_new(2, 2, vec![m(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]])]).unwrap();
        let adaptive = k.compose_adaptive(&[identity, swap]).unwrap();
        assert_eq!(adaptive.forget(), m(&[&[(1, 1), (1, 1)], &[(0, 1), (0, 1)]]));
        // Replacing the continuation by its average gives a different forgotten map.
        let average = m(&[&[(1, 2), (1, 2)], &[(1, 2), (1, 2)]]);
        assert_eq!(mat_mul(&average, &k.forget()), average);
        assert_ne!(adaptive.forget(), mat_mul(&average, &k.forget()));
        assert_eq!(
            k.compose_adaptive(&[k.clone()]),
            Err(ClassicalInstrumentError::ContinuationCount { expected: 2, actual: 1 })
        );
    }

    #[test]
    fn admission_refusals() {
        assert_eq!(
            ClassicalInstrument::try_new(2, 2, vec![vec![vec![ri(2), ri(0)], vec![ri(-1), ri(1)]]]),
            Err(ClassicalInstrumentError::NegativeEntry { outcome: 0, row: 1, col: 0 })
        );
        assert_eq!(
            ClassicalInstrument::try_new(1, 1, vec![vec![vec![ri(2)]]]),
            Err(ClassicalInstrumentError::NormalizationDefect { col: 0, total: ri(2) })
        );
        assert_eq!(ClassicalInstrument::try_new(0, 1, vec![]), Err(ClassicalInstrumentError::EmptyCarrier));
        assert_eq!(ClassicalInstrument::try_new(1, 1, vec![]), Err(ClassicalInstrumentError::EmptyOutcomeFamily));
        assert!(matches!(
            ClassicalInstrument::try_new(2, 1, vec![vec![vec![ri(1)]]]),
            Err(ClassicalInstrumentError::ShapeMismatch { .. })
        ));
        let k = report_k();
        assert_eq!(k.map(2), Err(ClassicalInstrumentError::UnknownOutcome(2)));
        assert_eq!(k.apply(0, &[rq(1, 2), rq(1, 3)]), Err(ClassicalInstrumentError::InvalidState));
        let wide = ClassicalInstrument::try_new(3, 3, vec![vec![vec![ri(1), ri(0), ri(0)], vec![ri(0), ri(1), ri(0)], vec![ri(0), ri(0), ri(1)]]]).unwrap();
        assert_eq!(k.compose(&wide), Err(ClassicalInstrumentError::CompositionMismatch { expected: 2, actual: 3 }));
        // Boundary: conditioning on a zero-probability outcome is refused.
        let det = ClassicalInstrument::try_new(1, 1, vec![vec![vec![ri(1)]], vec![vec![ri(0)]]]).unwrap();
        assert_eq!(det.condition(1, &[ri(1)]), Err(ClassicalInstrumentError::ZeroProbabilityConditioning));
        assert_eq!(det.condition(0, &[ri(1)]), Ok(vec![ri(1)]));
    }

    #[test]
    fn local_instrument_keeps_the_other_marginal_and_postselection_does_not() {
        let joint = m(&[&[(1, 3), (1, 6)], &[(1, 6), (1, 3)]]);
        let read = ClassicalInstrument::try_new(
            2,
            2,
            vec![m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]), m(&[&[(0, 1), (0, 1)], &[(0, 1), (1, 1)]])],
        )
        .unwrap();
        let parts = read.apply_local(&joint).unwrap();
        let summed = mat_add(&parts[0], &parts[1]);
        assert_eq!(second_marginal(&summed), second_marginal(&joint));
        assert_eq!(second_marginal(&joint), vec![rq(1, 2), rq(1, 2)]);
        // Postselecting outcome 0 and renormalising changes the other party's marginal.
        let mass: Rational = parts[0].iter().flatten().sum();
        let post: Matrix = parts[0].iter().map(|r| r.iter().map(|v| v / &mass).collect()).collect();
        assert_eq!(second_marginal(&post), vec![rq(2, 3), rq(1, 3)]);
    }

    #[test]
    fn pr_box_is_no_signalling_has_chsh_four_and_no_local_table() {
        let pr = ConditionalBox::pr_box();
        assert_eq!(pr.signalling_witness(), None);
        assert_eq!(pr.chsh(), Some(ri(4)));
        assert!(pr.support_compatible_assignments(64).unwrap().is_empty());
        let mut weights = BTreeMap::new();
        weights.insert((vec![0, 0], vec![0, 0]), ri(1));
        assert!(!pr.verify_local_model(&LocalHiddenVariableTable { weights }));
    }

    #[test]
    fn local_box_has_a_verified_hidden_variable_table() {
        // Deterministic a = 0, b = 0 everywhere.
        let point = m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]);
        let local = ConditionalBox::try_new((2, 2), (2, 2), vec![vec![point.clone(), point.clone()], vec![point.clone(), point]]).unwrap();
        assert_eq!(local.signalling_witness(), None);
        assert_eq!(local.chsh(), Some(ri(2)));
        assert_eq!(local.support_compatible_assignments(64).unwrap(), vec![(vec![0, 0], vec![0, 0])]);
        let mut weights = BTreeMap::new();
        weights.insert((vec![0, 0], vec![0, 0]), ri(1));
        let table = LocalHiddenVariableTable { weights };
        assert!(local.verify_local_model(&table));
        // Mutation: a weight off by a half no longer replays.
        let mut bad = table.clone();
        bad.weights.insert((vec![1, 0], vec![0, 0]), rq(0, 1));
        assert!(local.verify_local_model(&bad));
        bad.weights.insert((vec![0, 0], vec![0, 0]), rq(1, 2));
        bad.weights.insert((vec![1, 0], vec![0, 0]), rq(1, 2));
        assert!(!local.verify_local_model(&bad));
    }

    #[test]
    fn signalling_box_returns_an_exact_witness_and_partial_tables_are_refused() {
        // Bob's outcome copies Alice's input: Bob's marginal depends on x.
        let b0 = m(&[&[(1, 2), (0, 1)], &[(1, 2), (0, 1)]]);
        let b1 = m(&[&[(0, 1), (1, 2)], &[(0, 1), (1, 2)]]);
        let signalling = ConditionalBox::try_new((2, 2), (2, 2), vec![vec![b0.clone(), b0], vec![b1.clone(), b1]]).unwrap();
        assert_eq!(
            signalling.signalling_witness(),
            Some(SignallingWitness {
                party: Party::Bob,
                input: 0,
                outcome: 0,
                other_inputs: (0, 1),
                sums: (ri(1), ri(0)),
            })
        );
        let point = m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]);
        assert_eq!(
            ConditionalBox::try_new((2, 2), (2, 2), vec![vec![point.clone(), point.clone()], vec![point.clone()]]),
            Err(ClassicalInstrumentError::PartialTable { x: 1, y: 1 })
        );
        assert_eq!(
            ConditionalBox::pr_box().support_compatible_assignments(3),
            Err(ClassicalInstrumentError::ResourceLimit)
        );
    }
}
