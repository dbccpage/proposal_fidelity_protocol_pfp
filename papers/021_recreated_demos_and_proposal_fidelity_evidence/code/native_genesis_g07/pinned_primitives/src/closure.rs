//! Primitive — the **declared pair-separation closure policy**, and the
//! external continuation policy it is kept apart from.
//!
//! Crate boundary: engine.  Source: `engine.py::closure_challenge_orbits`
//! and the module docstring's two-component decomposition of the challenge
//! source; sealed terminal clause (f); standing obstruction **OB-1**.
//!
//! No object-language endogenous demand generator was derived.  The sealed
//! challenge source is two *declared* pieces of metatheory:
//!
//! 1. **the closure policy** — reissue the admitted requirement pattern
//!    (separation) on the collapsed pairs, one challenge per automorphism
//!    orbit.  It reads only profile equality and the automorphism
//!    structure; it never reads token glyphs, never supplies data, never
//!    imports a new goal kind.  It reaches a fixpoint once every pair is
//!    separated, in at most `n(n-1)/2` rounds;
//! 2. **the external continuation policy** — supply and admit one fresh
//!    opaque token.  Explicitly external; `supply = false` runs are the
//!    closed-system baseline.
//!
//! A collapsed pair is not an obstruction by itself.  *This policy is what
//! makes it one.*  The Core engine (`core.rs`) accepts a demand from the
//! outside or from this policy, and records which — because the difference
//! between "the world asked" and "the policy reissued" is the difference OB-1
//! is about.

use crate::automorphism::pair_orbits;
use crate::canonical::IsoBudgetError;
use crate::mark::Pair;
use crate::regime::Regime;
use crate::separability::collapsed_pairs;

/// One representative (least member) per automorphism orbit of the
/// collapsed pairs; empty at the fixpoint.
pub fn closure_challenge_orbits(r: &Regime) -> Result<Vec<Pair>, IsoBudgetError> {
    Ok(pair_orbits(r, &collapsed_pairs(r))?.into_iter().map(|o| o[0]).collect())
}

/// The upper bound on rounds the sealed paper states for the closure.
pub fn closure_round_bound(n_data: usize) -> usize {
    n_data * n_data.saturating_sub(1) / 2
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::regime::Regime;
    use crate::renaming::{rename, Bijection};
    use crate::replay::replay;
    use crate::token::Token;

    #[test]
    fn one_challenge_per_orbit() {
        let f = replay(&READING_F.genesis).unwrap();
        assert_eq!(closure_challenge_orbits(&f).unwrap(), vec![Pair::of(0, 1)]);
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(closure_challenge_orbits(&l).unwrap(), vec![Pair::of(0, 1)]);
    }

    /// Token-blind: renaming the tokens only (not the indices) changes
    /// nothing the policy reads.
    #[test]
    fn the_policy_never_reads_token_glyphs() {
        let f = replay(&READING_F.genesis).unwrap();
        let mut g = f.clone();
        g.data = vec![Token::new("x"), Token::new("y"), Token::new("z")];
        assert_eq!(closure_challenge_orbits(&f).unwrap(), closure_challenge_orbits(&g).unwrap());
    }

    /// Equivariance: renaming by a bijection maps the challenge set onto the
    /// corresponding challenge set.
    #[test]
    fn the_policy_is_equivariant() {
        let f = replay(&READING_F.genesis).unwrap();
        let r = step(&f, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[2])).unwrap();
        let b = Bijection { data: vec![2, 0, 1], forms: vec![0] };
        let s = rename(&r, &b);
        let mapped: Vec<Pair> = closure_challenge_orbits(&r)
            .unwrap()
            .iter()
            .map(|p| Pair::of(b.data[p.i.0], b.data[p.j.0]))
            .collect();
        let mut expected = closure_challenge_orbits(&s).unwrap();
        let mut mapped_sorted = mapped;
        mapped_sorted.sort();
        expected.sort();
        assert_eq!(mapped_sorted, expected);
    }

    #[test]
    fn the_fixpoint_is_empty_and_genesis_has_no_demand() {
        assert!(closure_challenge_orbits(&Regime::genesis()).unwrap().is_empty());
        assert_eq!(closure_round_bound(3), 3);
        assert_eq!(closure_round_bound(2), 1);
    }
}
