//! Sort 6 — **Judgment**: a positive observation form that holds or does not.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::derivable`; the
//! boundary kernel's `OnSide` / `SideNamed` and its docstring *"There is no
//! `Empty` or counting judgment"*.
//!
//! ```text
//! L7   the absence of a judgment is never a judgment
//! ```
//!
//! The grammar is **positive by type**.  There is no `Not`, no `Empty`, no
//! `Count`.  That is not a limitation waiting to be lifted; it is what makes
//! `FW-ABSENCE` enforceable — absence of a test is never converted into
//! equality, because absence is not something the grammar can say.
//!
//! To extend the grammar, add a positive variant.  Never add a negative one.

use crate::profile::derivable;
use crate::regime::{Inst, Regime};

/// A positive judgment.  Extend, never negate.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Judgment {
    /// The instance is derivable in the regime.
    Derivable(Inst),
}

/// The names of the grammar's forms.  One entry per variant; a test checks
/// the count against an exhaustive `match`, which is the only reflection a
/// type system gives.
pub const GRAMMAR: &[&str] = &["Derivable"];

/// `⊙` — does the judgment hold in the regime?
pub fn holds(r: &Regime, j: &Judgment) -> bool {
    match j {
        Judgment::Derivable(inst) => derivable(r, inst),
    }
}

/// Every judgment that holds in the regime, enumerated over the admitted
/// instances and rule-covered instances.  Metatheoretic: the returned
/// collection is not an object-language value.
pub fn holding(r: &Regime) -> Vec<Judgment> {
    let mut out: Vec<Judgment> = r.insts.iter().map(|i| Judgment::Derivable(i.clone())).collect();
    out.sort();
    out.dedup();
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::replay::replay;

    /// If a variant is added, this `match` stops being exhaustive and the
    /// file stops compiling until GRAMMAR is updated too.
    #[test]
    fn the_grammar_is_positive_and_censused() {
        let j = Judgment::Derivable(Inst::new(0, vec![Mark(0)]));
        let name = match &j {
            Judgment::Derivable(_) => "Derivable",
        };
        assert_eq!(GRAMMAR, &[name]);
    }

    #[test]
    fn l7_nothing_holds_before_a_form_is_admitted() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(holding(&base).is_empty());
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        assert!(!holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(0)]))));
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        assert!(holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(0)]))));
        assert!(!holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(1)]))));
    }
}
