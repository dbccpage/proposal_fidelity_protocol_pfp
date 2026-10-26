//! Primitive — **cost measures** `mu1` and `mu2`: declared, never inferred.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::mu1`, `mu2`.
//!
//! ```text
//! L12  cost measures are declared, never inferred
//! ```
//!
//! `mu1` counts items.  `mu2` is `(item count, sum of new-form arities)`,
//! ordered lexicographically.  Two measures are carried because ties under
//! one may split under the other, and the sealed Challenge 3 is exactly that
//! case: three tied classes under `mu1` in reading L, one under `mu2`.
//!
//! No measure is preferred.  `CL-NO-UNIVERSAL-PROPERTY` refuses a best; the
//! `reach_measure` tree shows a third measure breaks some ties and leaves
//! others; `path_dependent_cost` shows a cost can be additive and not exact.
//! Whether cost is additive along composition is **unproved** for these two
//! (crosstab §9 item 4), so a composite's price is measured, not summed.

use crate::candidate::{Delta, Item};

/// A cost value.  Compared lexicographically.  The second component is `-1`
/// under `mu1`, so that a single `Cost` type serves both measures without
/// pretending they are comparable to each other.
pub type Cost = (usize, i64);

/// A declared cost measure.
pub trait Measure {
    /// Its name in receipts.
    fn name(&self) -> &'static str;
    /// `μ` — the cost of a candidate.
    fn cost(&self, delta: &Delta) -> Cost;
}

/// The two declared measures.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MeasureKind {
    /// Item count.
    Mu1,
    /// `(item count, new-form arity sum)`, lexicographic.
    Mu2,
}

impl MeasureKind {
    /// Both, in the order the sealed receipts list them.
    pub const ALL: [MeasureKind; 2] = [MeasureKind::Mu1, MeasureKind::Mu2];
}

/// The new-form arity sum of a delta.
pub fn arity_sum(delta: &Delta) -> i64 {
    delta.iter().map(|it| if let Item::NewForm(a) = it { *a as i64 } else { 0 }).sum()
}

impl Measure for MeasureKind {
    fn name(&self) -> &'static str {
        match self {
            MeasureKind::Mu1 => "mu1",
            MeasureKind::Mu2 => "mu2",
        }
    }
    fn cost(&self, delta: &Delta) -> Cost {
        match self {
            MeasureKind::Mu1 => (delta.len(), -1),
            MeasureKind::Mu2 => (delta.len(), arity_sum(delta)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mark::Mark;

    #[test]
    fn mu1_counts_items_and_mu2_refines_by_arity() {
        let unary = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let binary = vec![Item::NewForm(2), Item::NewInst(0, vec![Mark(0), Mark(0)])];
        assert_eq!(MeasureKind::Mu1.cost(&unary), MeasureKind::Mu1.cost(&binary));
        assert!(MeasureKind::Mu2.cost(&unary) < MeasureKind::Mu2.cost(&binary));
        assert_eq!(MeasureKind::Mu2.cost(&unary), (2, 1));
    }
}
