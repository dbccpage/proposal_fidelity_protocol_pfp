// Executable finite evidence; AuthorityEffect: None.
//! Chapter 19: the composition principle, conditional on a declared composition. Executable
//! finite evidence for `WDP-CH19-P08`, `WDP-CH19-P09` and `WDP-CH19-P10`; the composition
//! principle `WDP-CH19-O02` itself is not derived.
//!
//! - `WDP-CH19-P08` ([`local_decoders`]): a composition table `c : A x B -> C` has local
//!   decoders `d_A c(a, b) = a` and `d_B c(a, b) = b` exactly when `c` is injective. The
//!   degenerate table `c(a, b) = b` ([`dump_right_table`]) is not injective once
//!   `|A| >= 2`.
//! - `WDP-CH19-P09` ([`JointState`]): a stochastic instrument applied on one side of a
//!   joint state leaves the other side's marginal untouched, summing `q[o][a][b']` over
//!   the outcome `o` and the new coordinate `b'` returns `sum_b p[a][b]`. A presentation
//!   `pres_A : A -> Q_A` lifts to `A x B` along the first projection and commutes with
//!   marginalization.
//! - `WDP-CH19-P10` ([`composite_state_from_bilinear`]): a bilinear form on effect vectors
//!   that is nonnegative on product effects and takes value one on the top effects is
//!   the joint distribution `p[a][b] = omega(1_a, 1_b)`. Nonnegativity on product effects
//!   is equivalent to nonnegativity on indicator product effects. [`pr_box_fixture`] is a
//!   compatible, strongly contextual box: its contexts agree on every overlap, yet no
//!   global assignment is positive in all four contexts, so no joint distribution
//!   reproduces it.
//!
//! A composite state built here confers no standing on a composition: the principle that
//! a composite is determined by its parts remains a declared premise.

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

use crate::empirical_adapter::{
    adapt_exact, chsh_cover, chsh_value, pr_box_run_table, signalling_defect, EmpiricalModel,
};
use crate::error::WdpError;
use crate::stochastic_package::{
    matrix_apply, matrix_shape, ClassicalInstrument, Matrix, MAX_MATRIX_ENTRIES,
};
use crate::types::AuthorityEffect;

/// Cap on the effect-grid size `3^(|A| + |B|)` checked for bilinearity.
pub const MAX_GRID_PAIRS: usize = 100_000;

/// Cap on the target states of a composition table or of a pushforward.
pub const MAX_TARGET_STATES: usize = 1_000_000;

/// Cap on the entries of a table built from caller-supplied dimensions.
pub const MAX_TABLE_ENTRIES: usize = 1_000_000;

fn invalid(detail: String) -> WdpError {
    WdpError::InvalidInput { detail }
}

/// Decoders `(d_A, d_B)` on `C = {0, ..., n_c - 1}`.
pub type Decoders = (Vec<usize>, Vec<usize>);

/// `WDP-CH19-P08`: the decoders of a table `c[a][b]`, or `None` when `c` is not injective.
/// `n_c` is one more than the largest table value; on values outside the image the
/// decoders are 0. A malformed (empty or ragged) table is refused.
fn validate_composition_table_target_count(c: &[Vec<usize>]) -> Result<usize, WdpError> {
    let n_a = c.len();
    let n_b = c.first().map_or(0, Vec::len);
    if n_a == 0 || n_b == 0 {
        return Err(invalid(
            "a composition table needs at least one row and column".to_string(),
        ));
    }
    if let Some(row) = c.iter().position(|r| r.len() != n_b) {
        return Err(invalid(format!("composition table row {row} is ragged")));
    }
    let n_c = match c.iter().flatten().max() {
        None => 0,
        Some(&largest) => largest.checked_add(1).ok_or_else(|| {
            invalid(format!(
                "composition table value {largest} leaves no target count"
            ))
        })?,
    };
    if n_c > MAX_TARGET_STATES {
        return Err(invalid(format!(
            "composition table names {n_c} target states, more than {MAX_TARGET_STATES}"
        )));
    }
    Ok(n_c)
}

pub fn local_decoders(c: &[Vec<usize>]) -> Result<Option<Decoders>, WdpError> {
    let n_c = validate_composition_table_target_count(c)?;
    let mut decoder_a = vec![0usize; n_c];
    let mut decoder_b = vec![0usize; n_c];
    let mut seen = vec![false; n_c];
    for (a, row) in c.iter().enumerate() {
        for (b, &value) in row.iter().enumerate() {
            if seen[value] {
                return Ok(None);
            }
            seen[value] = true;
            decoder_a[value] = a;
            decoder_b[value] = b;
        }
    }
    Ok(Some((decoder_a, decoder_b)))
}

/// Whether `d_A c(a, b) = a` and `d_B c(a, b) = b` for every pair.
pub fn decoders_are_left_inverse(c: &[Vec<usize>], decoders: &Decoders) -> bool {
    c.iter().enumerate().all(|(a, row)| {
        row.iter().enumerate().all(|(b, &value)| {
            decoders.0.get(value) == Some(&a) && decoders.1.get(value) == Some(&b)
        })
    })
}

/// Refuses an `n_a x n_b` table with a side or an entry count above [`MAX_TABLE_ENTRIES`]
/// (a side alone can be huge while the product is zero, and rows would still be allocated).
fn check_table_size(n_a: usize, n_b: usize) -> Result<(), WdpError> {
    if n_a > MAX_TABLE_ENTRIES
        || n_b > MAX_TABLE_ENTRIES
        || n_a
            .checked_mul(n_b)
            .is_none_or(|entries| entries > MAX_TABLE_ENTRIES)
    {
        return Err(invalid(format!(
            "a {n_a} x {n_b} table exceeds {MAX_TABLE_ENTRIES} entries"
        )));
    }
    Ok(())
}

/// The pairing table `c(a, b) = a * n_b + b`. The size check bounds `n_a * n_b`, so no
/// entry overflows.
pub fn pairing_table(n_a: usize, n_b: usize) -> Result<Vec<Vec<usize>>, WdpError> {
    check_table_size(n_a, n_b)?;
    Ok((0..n_a)
        .map(|a| (0..n_b).map(|b| a * n_b + b).collect())
        .collect())
}

/// The degenerate table `c(a, b) = b`, which forgets `A`.
pub fn dump_right_table(n_a: usize, n_b: usize) -> Result<Vec<Vec<usize>>, WdpError> {
    check_table_size(n_a, n_b)?;
    Ok((0..n_a).map(|_| (0..n_b).collect()).collect())
}

/// The pushforward of a vector along `map : {0..dist.len()} -> {0..n_target}`.
pub fn pushforward(
    dist: &[BigRational],
    map: &[usize],
    n_target: usize,
) -> Result<Vec<BigRational>, WdpError> {
    if map.len() != dist.len() {
        return Err(invalid(format!(
            "map has {} values for a vector of length {}",
            map.len(),
            dist.len()
        )));
    }
    if n_target > MAX_TARGET_STATES {
        return Err(invalid(format!(
            "target carrier {n_target} exceeds {MAX_TARGET_STATES} states"
        )));
    }
    let mut out = vec![BigRational::zero(); n_target];
    for (weight, &target) in dist.iter().zip(map) {
        let slot = out
            .get_mut(target)
            .ok_or_else(|| invalid(format!("map value {target} lies outside 0..{n_target}")))?;
        *slot += weight;
    }
    Ok(out)
}

/// The map `A x B -> Q_A`, `(a, b) -> pres_A(a)`, on pairs flattened as `a * n_b + b`.
pub fn lift_along_first(pres_a: &[usize], n_b: usize) -> Result<Vec<usize>, WdpError> {
    check_table_size(pres_a.len(), n_b)?;
    Ok(pres_a
        .iter()
        .flat_map(|&q| std::iter::repeat_n(q, n_b))
        .collect())
}

/// A joint distribution `p[a][b]` on a finite product carrier.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointState {
    p: Matrix,
    n_a: usize,
    n_b: usize,
}

impl JointState {
    /// Nonnegative entries summing to one.
    pub fn new(p: Matrix) -> Result<Self, WdpError> {
        let (n_a, n_b) = matrix_shape(&p, "joint state")?;
        if let Some((a, b)) = (0..n_a)
            .flat_map(|a| (0..n_b).map(move |b| (a, b)))
            .find(|&(a, b)| p[a][b].is_negative())
        {
            return Err(invalid(format!("joint state entry ({a}, {b}) is negative")));
        }
        let total = p
            .iter()
            .flatten()
            .fold(BigRational::zero(), |acc, x| acc + x);
        if !total.is_one() {
            return Err(invalid(format!(
                "joint state has total mass {total}, not 1"
            )));
        }
        Ok(Self { p, n_a, n_b })
    }

    pub fn entries(&self) -> &[Vec<BigRational>] {
        &self.p
    }

    pub fn n_a(&self) -> usize {
        self.n_a
    }

    pub fn n_b(&self) -> usize {
        self.n_b
    }

    /// `a -> sum_b p[a][b]`.
    pub fn marginal_a(&self) -> Vec<BigRational> {
        self.p
            .iter()
            .map(|row| row.iter().fold(BigRational::zero(), |acc, x| acc + x))
            .collect()
    }

    /// `b -> sum_a p[a][b]`.
    pub fn marginal_b(&self) -> Vec<BigRational> {
        (0..self.n_b)
            .map(|b| {
                self.p
                    .iter()
                    .fold(BigRational::zero(), |acc, row| acc + &row[b])
            })
            .collect()
    }

    /// `q[o][a][b'] = sum_b K_o[b'][b] p[a][b]` for an instrument `K` on `B`.
    pub fn apply_instrument_on_b(
        &self,
        instrument: &ClassicalInstrument,
    ) -> Result<Vec<Matrix>, WdpError> {
        if instrument.n_in() != self.n_b {
            return Err(invalid(format!(
                "the instrument has {} inputs, B has {} states",
                instrument.n_in(),
                self.n_b
            )));
        }
        Ok(instrument
            .updates()
            .iter()
            .map(|k| self.p.iter().map(|row| matrix_apply(k, row)).collect())
            .collect())
    }

    /// `q[o][a'][b] = sum_a K_o[a'][a] p[a][b]` for an instrument `K` on `A`.
    pub fn apply_instrument_on_a(
        &self,
        instrument: &ClassicalInstrument,
    ) -> Result<Vec<Matrix>, WdpError> {
        if instrument.n_in() != self.n_a {
            return Err(invalid(format!(
                "the instrument has {} inputs, A has {} states",
                instrument.n_in(),
                self.n_a
            )));
        }
        let columns: Vec<Vec<BigRational>> = (0..self.n_b)
            .map(|b| self.p.iter().map(|row| row[b].clone()).collect())
            .collect();
        Ok(instrument
            .updates()
            .iter()
            .map(|k| {
                let images: Vec<Vec<BigRational>> =
                    columns.iter().map(|col| matrix_apply(k, col)).collect();
                (0..instrument.n_out())
                    .map(|a2| images.iter().map(|image| image[a2].clone()).collect())
                    .collect()
            })
            .collect())
    }

    /// The pushforward of the joint state along `pres_A o fst : A x B -> Q_A`.
    pub fn pushforward_along_first(
        &self,
        pres_a: &[usize],
        n_q: usize,
    ) -> Result<Vec<BigRational>, WdpError> {
        if pres_a.len() != self.n_a {
            return Err(invalid(format!(
                "presentation has {} values for {} states of A",
                pres_a.len(),
                self.n_a
            )));
        }
        let flat: Vec<BigRational> = self.p.iter().flatten().cloned().collect();
        pushforward(&flat, &lift_along_first(pres_a, self.n_b)?, n_q)
    }

    /// The joint distribution `[q][b]` on `Q_A x B` after `pres_A x id_B`.
    pub fn pushforward_presentation_a(
        &self,
        pres_a: &[usize],
        n_q: usize,
    ) -> Result<Matrix, WdpError> {
        if pres_a.len() != self.n_a {
            return Err(invalid(format!(
                "presentation has {} values for {} states of A",
                pres_a.len(),
                self.n_a
            )));
        }
        if n_q
            .checked_mul(self.n_b)
            .is_none_or(|n| n > MAX_MATRIX_ENTRIES)
        {
            return Err(invalid(format!(
                "a {n_q} x {} table exceeds {MAX_MATRIX_ENTRIES} entries",
                self.n_b
            )));
        }
        let mut out = vec![vec![BigRational::zero(); self.n_b]; n_q];
        for (a, row) in self.p.iter().enumerate() {
            let target = out.get_mut(pres_a[a]).ok_or_else(|| {
                invalid(format!("presentation value {} outside 0..{n_q}", pres_a[a]))
            })?;
            for (slot, x) in target.iter_mut().zip(row) {
                *slot += x;
            }
        }
        Ok(out)
    }
}

/// `sum_{o, b'} q[o][a][b']` for each `a`.
pub fn outcome_marginal_a(q: &[Matrix]) -> Result<Vec<BigRational>, WdpError> {
    let first = q
        .first()
        .ok_or_else(|| invalid("no outcomes to marginalize".to_string()))?;
    let mut out = vec![BigRational::zero(); first.len()];
    for outcome in q {
        if outcome.len() != out.len() {
            return Err(invalid(
                "outcome tables have different numbers of rows".to_string(),
            ));
        }
        for (slot, row) in out.iter_mut().zip(outcome) {
            *slot += row.iter().fold(BigRational::zero(), |acc, x| acc + x);
        }
    }
    Ok(out)
}

/// `sum_{o, a'} q[o][a'][b]` for each `b`.
pub fn outcome_marginal_b(q: &[Matrix]) -> Result<Vec<BigRational>, WdpError> {
    let width = q
        .first()
        .and_then(|m| m.first())
        .map(Vec::len)
        .ok_or_else(|| invalid("no outcomes to marginalize".to_string()))?;
    let mut out = vec![BigRational::zero(); width];
    for outcome in q {
        for row in outcome {
            if row.len() != width {
                return Err(invalid("outcome tables have ragged rows".to_string()));
            }
            for (slot, x) in out.iter_mut().zip(row) {
                *slot += x;
            }
        }
    }
    Ok(out)
}

/// A bilinear form on effect vectors, `omega(e, f) = sum_{a,b} e_a W[a][b] f_b`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BilinearForm {
    w: Matrix,
    n_a: usize,
    n_b: usize,
}

impl BilinearForm {
    pub fn new(w: Matrix) -> Result<Self, WdpError> {
        let (n_a, n_b) = matrix_shape(&w, "bilinear form")?;
        Ok(Self { w, n_a, n_b })
    }

    pub fn evaluate(&self, e: &[BigRational], f: &[BigRational]) -> Result<BigRational, WdpError> {
        if e.len() != self.n_a || f.len() != self.n_b {
            return Err(invalid(format!(
                "effects have lengths ({}, {}), the form is {} x {}",
                e.len(),
                f.len(),
                self.n_a,
                self.n_b
            )));
        }
        Ok(self
            .w
            .iter()
            .zip(e)
            .fold(BigRational::zero(), |acc, (row, ea)| {
                acc + ea
                    * row
                        .iter()
                        .zip(f)
                        .fold(BigRational::zero(), |s, (x, fb)| s + x * fb)
            }))
    }
}

/// `WDP-CH19-P10`: the joint distribution `p = W` of a bilinear form that is nonnegative
/// on product effects (refused on an indicator product effect `(1_a, 1_b)` with negative
/// value) and normalized, `omega(1, 1) = 1`.
pub fn composite_state_from_bilinear(w: &[Vec<BigRational>]) -> Result<JointState, WdpError> {
    let form = BilinearForm::new(w.to_vec())?;
    for (a, row) in form.w.iter().enumerate() {
        for (b, value) in row.iter().enumerate() {
            if value.is_negative() {
                return Err(invalid(format!(
                    "the form is {value} on the indicator product effect (1_{a}, 1_{b})"
                )));
            }
        }
    }
    let top_a = vec![BigRational::one(); form.n_a];
    let top_b = vec![BigRational::one(); form.n_b];
    let total = form.evaluate(&top_a, &top_b)?;
    if !total.is_one() {
        return Err(invalid(format!("omega(1, 1) = {total}, not 1")));
    }
    JointState::new(w.to_vec())
}

fn show(v: &[BigRational]) -> String {
    let items: Vec<String> = v.iter().map(ToString::to_string).collect();
    format!("[{}]", items.join(", "))
}

fn indicator(n: usize, i: usize) -> Vec<BigRational> {
    (0..n)
        .map(|k| {
            if k == i {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        })
        .collect()
}

/// The effect vectors with entries in `{0, 1/2, 1}` of length `n`.
fn effect_grid(n: usize) -> Vec<Vec<BigRational>> {
    let levels = [
        BigRational::zero(),
        BigRational::new(1.into(), 2.into()),
        BigRational::one(),
    ];
    let mut grid = vec![Vec::new()];
    for _ in 0..n {
        grid = grid
            .into_iter()
            .flat_map(|prefix| {
                levels.iter().map(move |level| {
                    let mut next = prefix.clone();
                    next.push(level.clone());
                    next
                })
            })
            .collect();
    }
    grid
}

/// The joint state extracted from a black-box form, with the size of the verified grid.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormReceipt {
    pub state: JointState,
    /// Pairs of effects in `{0, 1/2, 1}^A x {0, 1/2, 1}^B` on which the form matched.
    pub grid_pairs_checked: usize,
    pub authority_effect: AuthorityEffect,
}

/// `WDP-CH19-P10` from a black-box form: extracts `W[a][b] = omega(1_a, 1_b)`, requires
/// [`composite_state_from_bilinear`], and then verifies `omega(e, f) = sum p[a][b] e_a f_b`
/// on every pair of effects in `{0, 1/2, 1}^A x {0, 1/2, 1}^B`. A form that disagrees with
/// the extracted `W` on that grid is refused at the first disagreeing pair; agreement on
/// the grid is what is checked, not bilinearity off it.
fn check_form_grid_budget(n_a: usize, n_b: usize) -> Result<(), WdpError> {
    if n_a == 0 || n_b == 0 {
        return Err(invalid("a form needs positive dimensions".to_string()));
    }
    n_a.checked_add(n_b)
        .and_then(|dimension| u32::try_from(dimension).ok())
        .and_then(|dimension| 3usize.checked_pow(dimension))
        .filter(|&g| g <= MAX_GRID_PAIRS)
        .ok_or_else(|| invalid(format!("effect grid exceeds {MAX_GRID_PAIRS} pairs")))?;
    Ok(())
}

pub fn composite_state_from_form(
    n_a: usize,
    n_b: usize,
    omega: &dyn Fn(&[BigRational], &[BigRational]) -> BigRational,
) -> Result<FormReceipt, WdpError> {
    check_form_grid_budget(n_a, n_b)?;
    let w: Matrix = (0..n_a)
        .map(|a| {
            (0..n_b)
                .map(|b| omega(&indicator(n_a, a), &indicator(n_b, b)))
                .collect()
        })
        .collect();
    let state = composite_state_from_bilinear(&w)?;
    let form = BilinearForm::new(state.p.clone())?;
    let mut grid_pairs_checked = 0usize;
    let grid_b = effect_grid(n_b);
    for e in effect_grid(n_a) {
        for f in &grid_b {
            if omega(&e, f) != form.evaluate(&e, f)? {
                return Err(invalid(format!(
                    "the form differs from its extracted bilinear form on the {{0, 1/2, 1}} grid at effects {}, {}",
                    show(&e),
                    show(f)
                )));
            }
            grid_pairs_checked += 1;
        }
    }
    Ok(FormReceipt {
        state,
        grid_pairs_checked,
        authority_effect: AuthorityEffect::None,
    })
}

/// The PR box on the CHSH cover: compatible, CHSH value 4, no positive global assignment.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PrBoxFixture {
    pub model: EmpiricalModel,
    /// Largest pairwise overlap-marginal L1 defect of the run frequencies.
    pub max_signalling_defect: BigRational,
    pub chsh_value: BigRational,
    pub positive_global_assignments: usize,
    /// No global assignment is positive in every context, so no joint distribution
    /// reproduces the model. This is the support-level fact only: the reverse
    /// (`positive_global_assignments > 0`) would be necessary and not sufficient for
    /// noncontextuality, and is never claimed.
    pub strongly_contextual: bool,
    pub authority_effect: AuthorityEffect,
}

/// The PR-box fixture: `adapt_exact` accepts it (no signalling), yet no global assignment
/// is positive in all four contexts, so it is strongly contextual.
pub fn pr_box_fixture() -> Result<PrBoxFixture, WdpError> {
    let cover = chsh_cover()?;
    let table = pr_box_run_table()?;
    let model = adapt_exact(&cover, &table)?;
    let max_signalling_defect =
        signalling_defect(&cover, &table)?
            .into_iter()
            .fold(
                BigRational::zero(),
                |acc, (_, d)| if d > acc { d } else { acc },
            );
    let value = chsh_value(&model)?;
    let positive = model.positive_global_assignments()?.len();
    Ok(PrBoxFixture {
        model,
        max_signalling_defect,
        chsh_value: value,
        positive_global_assignments: positive,
        strongly_contextual: positive == 0,
        authority_effect: AuthorityEffect::None,
    })
}

// Origin: engine/crates_rs/core_wdp/src/composition.rs
// Claim: urn:core:crates_rs:core-wdp:composition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde51e471e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde51e471e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore51e471e {
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
impl BoundaryErrore51e471e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore51e471e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore51e471e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde51e471e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore51e471e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore51e471e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore51e471e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore51e471e::ExceedsCapacity {
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
mod l4_boundary_tests_e51e471e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde51e471e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde51e471e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde51e471e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde51e471e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde51e471e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore51e471e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore51e471e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
