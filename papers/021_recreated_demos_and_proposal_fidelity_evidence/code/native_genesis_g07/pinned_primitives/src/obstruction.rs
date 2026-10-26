//! Primitive — **obstruction**: a recorded requirement plus the EXHAUSTIVE
//! failure of the declared menu.  Never mere lookalikeness.
//!
//! Crate boundary: represented.  Source: Lean `Represented.obstructedB` and
//! its countermodel `incomplete_search_false_alarm`; crosstab §11.1 block D
//! (*"An obstruction is not 'the check failed'"*).
//!
//! `obstructed` returns an **exhaustion certificate** or nothing.  It does
//! not return a `bool`, because a `bool` cannot carry which space was
//! searched and under which bound, and a refusal recorded without those is a
//! refusal recorded without evidence (`refusal.rs`).
//!
//! `obstructed_truncated` is the countermodel kept as code: it examines only
//! the first `k` menu items.  On the world in the test a working repair sits
//! past the truncation point, so the truncated check declares an obstruction
//! the exhaustive check refutes.  Obstruction requires exhaustive failure
//! *by definition*, and this is what happens when the definition is skipped.

use crate::certificate::Certificate;
use crate::mark::Pair;
use crate::menu::Menu;
use crate::regime::Regime;
use crate::repair::repair_family;
use crate::response::response_valid_naive;
use crate::separability::separable;

/// Is `target` a recorded, currently violated requirement?
pub fn violated(base: &Regime, target: Pair) -> bool {
    base.reqs.contains(&target) && !separable(base, target.i, target.j)
}

/// The exhaustion certificate, if `target` is violated and no menu member
/// repairs it.
pub fn obstructed(base: &Regime, target: Pair, menu: &Menu) -> Option<Certificate> {
    if !violated(base, target) {
        return None;
    }
    let fam = repair_family(base, target, menu);
    if !fam.members.is_empty() {
        return None;
    }
    Some(Certificate::Exhaustion { space: menu.space.clone(), bound: menu.bound.clone(), searched: fam.examined })
}

/// The countermodel: examine only the first `k` menu items.
pub fn obstructed_truncated(base: &Regime, target: Pair, menu: &Menu, k: usize) -> bool {
    violated(base, target)
        && menu.items.iter().take(k).all(|d| !response_valid_naive(base, target, d).unwrap_or(false))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::bounds::Bounds;
    use crate::event::Event;
    use crate::menu::menu;
    use crate::reading::READING_L;
    use crate::replay::replay;

    /// `incomplete_search_false_alarm`: the truncated check declares an
    /// obstruction that the exhaustive check refutes.
    #[test]
    fn a_truncated_search_falsely_certifies() {
        let base = replay(&READING_L.genesis).unwrap();
        let base = step(&base, &Event::Impose(READING_L.target)).unwrap();
        let m = menu(&base, &Bounds::default());
        assert!(violated(&base, READING_L.target));
        assert!(obstructed(&base, READING_L.target, &m).is_none(), "the exhaustive check finds a repair");
        // The empty delta and every single item fail; repairs start at two
        // items, past a small truncation point.
        let k = 1 + crate::enumeration::iter_cost1_items(&base, &Bounds::default()).len();
        assert!(obstructed_truncated(&base, READING_L.target, &m, k), "the truncated check cries obstruction");
    }

    /// A genuine obstruction: within one item, nothing separates the pair
    /// (CL-3-MIN-TWO), so the one-item menu is exhausted and certifies.
    #[test]
    fn a_real_obstruction_carries_its_space_and_bound() {
        let base = replay(&READING_L.genesis).unwrap();
        let base = step(&base, &Event::Impose(READING_L.target)).unwrap();
        let one = Bounds { max_items: 1, max_arity: 2 };
        let m = menu(&base, &one);
        let cert = obstructed(&base, READING_L.target, &m).expect("obstructed within one item");
        match cert {
            Certificate::Exhaustion { searched, bound, .. } => {
                assert_eq!(searched, m.items.len());
                assert!(bound.0.contains("max_items=1"));
            }
            _ => panic!("an obstruction is an exhaustion certificate"),
        }
    }

    #[test]
    fn an_unrecorded_or_satisfied_pair_is_not_obstructed() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = menu(&base, &Bounds { max_items: 1, max_arity: 2 });
        assert!(obstructed(&base, READING_L.target, &m).is_none(), "not recorded");
    }
}
