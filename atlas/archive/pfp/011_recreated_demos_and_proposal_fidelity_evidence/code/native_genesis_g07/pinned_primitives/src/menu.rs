//! Primitive — the **response menu**: the declared finite proposal set.
//!
//! Crate boundary: represented.  Source: Lean `Represented.responseMenu`
//! (*"the declared finite response menu … menu is constitution"*), and the
//! sealed candidate space it instantiates here.
//!
//! The menu is **declared, not searched for**.  It is every well-formed
//! delta within the declared bounds — the *unpruned* space, because the menu
//! is the constitution an obstruction is measured against, and an
//! obstruction is *exhaustive* failure over it.  The pruned enumeration in
//! `enumeration.rs` is a strategy for finding minima faster; it is not the
//! menu.
//!
//! In the author's vocabulary this is the **proposal** primitive.  Note what
//! it is not: it is not a proposer.  The estate's finding (crosstab §3) is
//! that "evaluation" splits into three — does it repair (`repair.rs`), is it
//! admissible (`world.rs`), does it certify and up to what (`panel.rs`) —
//! and that no single evaluation primitive exists.

use crate::bounds::Bounds;
use crate::candidate::Delta;
use crate::certificate::{Bound, SpaceId};
use crate::enumeration::iter_full_deltas;
use crate::regime::Regime;

/// The declared finite proposal set for one base regime.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Menu {
    /// Which space this is, for certificates.
    pub space: SpaceId,
    /// The bound it was enumerated under.
    pub bound: Bound,
    /// Every well-formed delta of at most `max_items` items.
    pub items: Vec<Delta>,
}

/// Enumerate the menu.  Unpruned; complete within the bounds.
pub fn menu(base: &Regime, bounds: &Bounds) -> Menu {
    bounds.validate().expect("unsupported candidate bounds");
    let mut items = Vec::new();
    for cost in 0..=bounds.max_items {
        items.extend(iter_full_deltas(base, cost, bounds));
    }
    Menu {
        space: SpaceId(format!("every well-formed delta over a regime with {} data and {} forms", base.n_data(), base.n_forms())),
        bound: Bound(bounds.describe()),
        items,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    #[should_panic(expected = "unsupported candidate bounds")]
    fn larger_advertised_space_is_not_silently_truncated() {
        menu(&Regime::genesis(), &Bounds { max_items: 3, max_arity: 2 });
    }

    #[test]
    fn the_menu_is_the_unpruned_space_and_contains_the_empty_delta() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = menu(&base, &Bounds::default());
        assert!(m.items.contains(&Vec::new()));
        let full2 = iter_full_deltas(&base, 2, &Bounds::default()).len();
        let full1 = iter_full_deltas(&base, 1, &Bounds::default()).len();
        assert_eq!(m.items.len(), 1 + full1 + full2);
    }
}
