//! Primitive — the **repair family**: the menu members that actually repair.
//! Sound, complete, and ties retained.
//!
//! Crate boundary: represented.  Source: Lean `Represented.repairFamily`,
//! `repairFamily_sound`, `repairFamily_complete`,
//! `repairFamily_retains_ties`.
//!
//! The family is a *filter* of the declared menu by the validity predicate.
//! Sound: every member is a valid response.  Complete: every valid menu
//! member is in the family.  Ties retained: the family is a list, never a
//! choice; "no member is dropped because another member also repairs" is
//! the Lean theorem, and here it is what a filter is.
//!
//! The Omega engine prices this family under every declared measure and
//! quotients it into classes.  It never picks.

use crate::candidate::{is_structure_creating, Delta};
use crate::mark::Pair;
use crate::menu::Menu;
use crate::regime::Regime;
use crate::response::response_valid_naive;

/// The members of the menu that discharge `target` while preserving every
/// recorded requirement.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RepairFamily {
    /// The target.
    pub target: Pair,
    /// The members, in menu order.
    pub members: Vec<Delta>,
    /// How many menu items were examined — all of them.
    pub examined: usize,
}

impl RepairFamily {
    /// Rule-1 members: instances only.
    pub fn repairs(&self) -> Vec<&Delta> {
        self.members.iter().filter(|d| !is_structure_creating(d)).collect()
    }
    /// Rule-2 members: anything that creates structure.
    pub fn augmentations(&self) -> Vec<&Delta> {
        self.members.iter().filter(|d| is_structure_creating(d)).collect()
    }
}

/// Filter the menu.  Uses the naive (replay) check, so it needs no rule-free
/// invariant and is the reference the fast path is checked against.
pub fn repair_family(base: &Regime, target: Pair, menu: &Menu) -> RepairFamily {
    let members = menu
        .items
        .iter()
        .filter(|d| response_valid_naive(base, target, d).unwrap_or(false))
        .cloned()
        .collect();
    RepairFamily { target, members, examined: menu.items.len() }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bounds::Bounds;
    use crate::menu::menu;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    #[test]
    fn sound_and_complete_against_the_menu() {
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let m = menu(&base, &Bounds::default());
            let fam = repair_family(&base, reading.target, &m);
            assert_eq!(fam.examined, m.items.len());
            for d in &fam.members {
                assert!(response_valid_naive(&base, reading.target, d).unwrap(), "sound");
            }
            for d in &m.items {
                if response_valid_naive(&base, reading.target, d).unwrap_or(false) {
                    assert!(fam.members.contains(d), "complete");
                }
            }
            assert!(!fam.members.is_empty());
        }
    }

    /// At the Challenge 3 base every repair needs a new form, so the family
    /// is all rule 2 and no rule 1: there is nothing to discriminate *with*.
    #[test]
    fn at_challenge3_every_repair_creates_structure() {
        let base = replay(&READING_L.genesis).unwrap();
        let fam = repair_family(&base, READING_L.target, &menu(&base, &Bounds::default()));
        assert!(fam.repairs().is_empty());
        assert_eq!(fam.augmentations().len(), fam.members.len());
    }
}
