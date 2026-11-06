//! Primitive — the two **admission readings** L and F, and Challenges 0–2.
//!
//! Crate boundary: engine.  Source: `engine.py::GENESIS_L`, `GENESIS_F`,
//! `READING_L`, `READING_F`, `challenge0_report`, `challenge1_report`,
//! `challenge2_report`; sealed terminal clause (h).
//!
//! The challenge text is *underdetermined* on one point: whether the
//! initial inscription `<>` is admitted at genesis.  Reading **L** (strict)
//! admits only on explicit retention, so `<>` is presented and never
//! retained.  Reading **F** (possession) admits it at genesis.  No internal
//! fact separates the two, so **both towers are carried in full** — the
//! estate's standing habit of retaining a tie instead of resolving it by
//! taste.
//!
//! The reading also fixes the Challenge 3 target: in L the retained pair is
//! `(0, 1)` = `<a>, <ab>`; in F it is `(1, 2)`, because `<>` sits at index 0.

use std::sync::LazyLock;

use crate::event::Event;
use crate::mark::Pair;
use crate::regime::Regime;
use crate::replay::replay;
use crate::separability::collapsed_pairs;
use crate::profile::profiles;
use crate::supply::supply;
use crate::token::Token;

/// One admission reading of the challenge text.
#[derive(Clone, Debug)]
pub struct Reading {
    /// `"L"` or `"F"`.
    pub name: &'static str,
    /// What the reading admits and when.
    pub description: &'static str,
    /// The genesis history through Challenge 2.
    pub genesis: Vec<Event>,
    /// The Challenge 3 target pair.
    pub target: Pair,
}

/// Reading L: strict admission.
pub static READING_L: LazyLock<Reading> = LazyLock::new(|| Reading {
    name: "L",
    description: "strict admission: only explicit retention admits; the initial inscription is presented but never retained",
    genesis: vec![
        Event::Supply(Token::new("<>")),
        Event::Supply(Token::new("<a>")),
        Event::Supply(Token::new("<a>")),
        Event::Supply(Token::new("<ab>")),
        Event::AdmitDatum(Token::new("<a>")),
        Event::AdmitDatum(Token::new("<ab>")),
    ],
    target: Pair::of(0, 1),
});

/// Reading F: possession admission.
pub static READING_F: LazyLock<Reading> = LazyLock::new(|| Reading {
    name: "F",
    description: "possession admission: the initial inscription is admitted at genesis; supplied inscriptions are admitted on retention",
    genesis: vec![
        Event::Supply(Token::new("<>")),
        Event::AdmitDatum(Token::new("<>")),
        Event::Supply(Token::new("<a>")),
        Event::Supply(Token::new("<a>")),
        Event::Supply(Token::new("<ab>")),
        Event::AdmitDatum(Token::new("<a>")),
        Event::AdmitDatum(Token::new("<ab>")),
    ],
    target: Pair::of(1, 2),
});

/// Both readings, in the order the sealed receipts list them.
pub fn readings() -> [&'static Reading; 2] {
    [&READING_L, &READING_F]
}

/// Challenge 0: the initial inscription, no object-language operation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Challenge0 {
    /// Does supplying `<>` change the admitted state?
    pub supply_changes_state: bool,
    /// How many contexts exist after the supply.
    pub context_count: usize,
    /// Is any successor internally forced?  Always `None`: no rule, and every
    /// state change factors through an external event.
    pub internally_forced_successor: Option<Event>,
}

/// Compute Challenge 0.
pub fn challenge0() -> Challenge0 {
    let g = Regime::genesis();
    let after = supply(&g, &Token::new("<>"));
    Challenge0 {
        supply_changes_state: after != g,
        context_count: crate::context::contexts(&after).len(),
        internally_forced_successor: None,
    }
}

/// Challenge 1: supply of `<a>`; the sub-readings and their convergence.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Challenge1 {
    /// Data after bare supply.
    pub bare_supply_data: Vec<Token>,
    /// Data after supply plus admission.
    pub supply_plus_admission_data: Vec<Token>,
    /// Do the two sub-readings reach the same regime at Challenge 2 close?
    pub sub_readings_converge_at_challenge2: bool,
}

/// Compute Challenge 1.
pub fn challenge1() -> Challenge1 {
    let bare = vec![Event::Supply(Token::new("<>")), Event::Supply(Token::new("<a>"))];
    let mut admit = bare.clone();
    admit.push(Event::AdmitDatum(Token::new("<a>")));
    let tail = [
        Event::Supply(Token::new("<a>")),
        Event::Supply(Token::new("<ab>")),
        Event::AdmitDatum(Token::new("<a>")),
        Event::AdmitDatum(Token::new("<ab>")),
    ];
    let mut bare_full = bare.clone();
    bare_full.extend(tail.iter().cloned());
    let mut admit_full = admit.clone();
    admit_full.extend(tail.iter().cloned());
    Challenge1 {
        bare_supply_data: replay(&bare).unwrap().data,
        supply_plus_admission_data: replay(&admit).unwrap().data,
        sub_readings_converge_at_challenge2: replay(&bare_full).unwrap() == replay(&admit_full).unwrap(),
    }
}

/// Challenge 2, per reading: what changed by admission and what remains
/// internally unavailable.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Challenge2 {
    /// The reading.
    pub reading: &'static str,
    /// Admitted data.
    pub admitted_data: Vec<Token>,
    /// Are the tokens pairwise distinct in the metatheory?
    pub externally_distinct_tokens: bool,
    /// The collapsed pairs.
    pub collapsed_pairs: Vec<Pair>,
    /// How many observational classes.
    pub observational_classes: usize,
    /// Did admission increase expressive power over Challenge 0?  No.
    pub expressive_increase_over_challenge0: bool,
}

/// Compute Challenge 2 for one reading.
pub fn challenge2(reading: &Reading) -> Challenge2 {
    let r = replay(&reading.genesis).unwrap();
    let profs = profiles(&r);
    let classes: std::collections::BTreeSet<_> = profs.iter().collect();
    let distinct: std::collections::BTreeSet<_> = r.data.iter().collect();
    Challenge2 {
        reading: reading.name,
        externally_distinct_tokens: distinct.len() == r.data.len(),
        collapsed_pairs: collapsed_pairs(&r),
        observational_classes: if profs.is_empty() { 0 } else { classes.len() },
        expressive_increase_over_challenge0: classes.len() > 1,
        admitted_data: r.data,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn challenge0_generates_nothing() {
        let c = challenge0();
        assert!(!c.supply_changes_state);
        assert_eq!(c.context_count, 0);
        assert!(c.internally_forced_successor.is_none());
    }

    #[test]
    fn challenge1_sub_readings_converge_because_admission_dedups() {
        let c = challenge1();
        assert!(c.bare_supply_data.is_empty());
        assert_eq!(c.supply_plus_admission_data, vec![Token::new("<a>")]);
        assert!(c.sub_readings_converge_at_challenge2);
    }

    #[test]
    fn challenge2_admission_need_not_increase_expressive_power() {
        for reading in readings() {
            let c = challenge2(reading);
            assert!(c.externally_distinct_tokens);
            assert_eq!(c.observational_classes, 1);
            assert!(!c.expressive_increase_over_challenge0);
        }
        assert_eq!(challenge2(&READING_L).admitted_data.len(), 2);
        assert_eq!(challenge2(&READING_F).admitted_data.len(), 3);
    }
}
