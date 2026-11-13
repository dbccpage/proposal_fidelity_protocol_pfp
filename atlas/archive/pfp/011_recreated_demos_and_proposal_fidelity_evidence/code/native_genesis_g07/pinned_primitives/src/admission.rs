//! Primitive — **admission**: the only thing that changes state.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::step`.
//!
//! ```text
//! L2   ∀e. step(Γ,e) ≠ Γ  ⟹  e is an admission or an imposition
//! L6   re-admission of an admitted token is a designation, not a duplication
//! ```
//!
//! `step` is deterministic and total on well-formed events; an ill-formed
//! admission is *refused by name* with an `AdmissionError`, never absorbed
//! silently.  The boundary derivation withdrew an earlier version of its own
//! kernel for exactly that sin — a moving admission absorbed as a no-op — and
//! the withdrawal is recorded in its module docstring.  Refuse loudly.
//!
//! **L6 is a convention.**  Presentation identity is metatheoretic, so whether
//! the second handing-in of the same token duplicates or designates is a
//! *choice*.  The sealed derivation chose designation, and `challenge1_report`
//! computes that the two sub-readings converge at Challenge 2 because of it.

use crate::event::{AdmissionError, Event};
use crate::imposition::impose;
use crate::regime::{Inst, Regime};

/// Apply one event.  `Supply` returns the regime unchanged (L1).  Admissions
/// change state; ill-formed ones are refused.
pub fn step(r: &Regime, e: &Event) -> Result<Regime, AdmissionError> {
    match e {
        Event::Supply(_) => Ok(r.clone()),
        Event::AdmitDatum(tok) => {
            if r.data.contains(tok) {
                // L6: designation of the existing datum, not a duplication.
                return Ok(r.clone());
            }
            let mut out = r.clone();
            out.data.push(tok.clone());
            Ok(out)
        }
        Event::AdmitForm(arity) => {
            if *arity < 1 {
                return Err(AdmissionError(format!("form arity must be >= 1, got {arity}")));
            }
            let mut out = r.clone();
            out.forms.push(*arity);
            Ok(out)
        }
        Event::AdmitInst(form, args) => {
            let Some(&arity) = r.forms.get(*form) else {
                return Err(AdmissionError(format!("unknown form {form}")));
            };
            if args.len() != arity {
                return Err(AdmissionError(format!(
                    "form {form} has arity {arity}, got {} arguments",
                    args.len()
                )));
            }
            if !args.iter().all(|m| r.has_mark(*m)) {
                return Err(AdmissionError(format!("instance arguments out of range: {args:?}")));
            }
            let mut out = r.clone();
            out.insts.insert(Inst::new(*form, args.clone()));
            Ok(out)
        }
        Event::AdmitRuleAll(form) => {
            if *form >= r.n_forms() {
                return Err(AdmissionError(format!("unknown form {form}")));
            }
            let mut out = r.clone();
            out.rules.insert(*form);
            Ok(out)
        }
        Event::Impose(pair) => impose(r, *pair),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mark::Pair;
    use crate::token::Token;

    fn two_data() -> Regime {
        let g = Regime::genesis();
        let a = step(&g, &Event::AdmitDatum(Token::new("<a>"))).unwrap();
        step(&a, &Event::AdmitDatum(Token::new("<ab>"))).unwrap()
    }

    #[test]
    fn l2_only_admissions_and_impositions_change_state() {
        let base = two_data();
        let f = step(&base, &Event::AdmitForm(1)).unwrap();
        assert_ne!(f, base);
        let i = step(&f, &crate::testkit::inst(0, &[0])).unwrap();
        assert_ne!(i, f);
        let ru = step(&f, &Event::AdmitRuleAll(0)).unwrap();
        assert_ne!(ru, f);
        let im = step(&base, &Event::Impose(Pair::of(0, 1))).unwrap();
        assert_ne!(im, base);
        assert_eq!(step(&base, &Event::Supply(Token::new("<a>"))).unwrap(), base);
    }

    #[test]
    fn l6_readmission_designates_and_does_not_duplicate() {
        let base = two_data();
        let again = step(&base, &Event::AdmitDatum(Token::new("<a>"))).unwrap();
        assert_eq!(again, base);
        assert_eq!(again.n_data(), 2);
    }

    #[test]
    fn ill_formed_admissions_are_refused_by_name() {
        let base = two_data();
        assert!(step(&base, &Event::AdmitForm(0)).is_err());
        assert!(step(&base, &crate::testkit::inst(0, &[0])).is_err(), "no form 0 yet");
        let f = step(&base, &Event::AdmitForm(2)).unwrap();
        assert!(step(&f, &crate::testkit::inst(0, &[0])).is_err(), "arity mismatch");
        assert!(step(&f, &crate::testkit::inst(0, &[0, 7])).is_err(), "mark 7 not admitted");
        assert!(step(&f, &Event::AdmitRuleAll(3)).is_err());
        assert!(step(&base, &Event::Impose(Pair::of(0, 5))).is_err());
    }
}
