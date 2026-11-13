//! Primitive — **transition roles**, derived from the accepted responses.
//!
//! Crate boundary: coda-price.  Source: `engine.py::_role`, `delta_label`;
//! sealed required question 9.
//!
//! The five roles the derivation itself produced — **supply,
//! discrimination, innovation, auxiliary witness, double discrimination** —
//! are not a taxonomy anyone declared.  They are the shapes of the deltas
//! the engine actually accepted, named after the fact.  The crosstab (§3)
//! makes the point that matters: these are the *object language's* roles;
//! the represented-process vocabulary (proposal, evaluation, authorization)
//! is a different layer built later to answer an outside question.  Running
//! the two together would be smuggling.
//!
//! In the represented process, `Discrimination` and `DoubleDiscrimination`
//! are rule-1 repairs; `Innovation` and `AuxiliaryWitness` are rule-2
//! augmentations (`candidate::is_structure_creating`).

use std::fmt;

use crate::candidate::{Delta, Item};
use crate::regime::Regime;

/// A recurring transition role.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Role {
    /// The external continuation policy admitted a fresh token.
    Supply,
    /// One instance on an existing form.
    Discrimination,
    /// A new form with one instance on it.
    Innovation,
    /// A fresh datum with an instance mentioning it.
    AuxiliaryWitness,
    /// Two instances on existing forms.
    DoubleDiscrimination,
    /// Any other accepted shape, named by its item kinds.
    Other(String),
}

/// The role of an accepted response.  `is_supply` marks the external
/// continuation move, which has an empty delta.
pub fn role(is_supply: bool, delta: &Delta) -> Role {
    if is_supply {
        return Role::Supply;
    }
    let mut kinds: Vec<&str> = delta
        .iter()
        .map(|it| match it {
            Item::NewDatum => "datum",
            Item::NewForm(_) => "form",
            Item::NewRuleAll(_) => "rule",
            Item::NewInst(_, _) => "inst",
        })
        .collect();
    kinds.sort();
    match kinds.as_slice() {
        ["inst"] => Role::Discrimination,
        ["form", "inst"] => Role::Innovation,
        ["datum", "inst"] => Role::AuxiliaryWitness,
        ["inst", "inst"] => Role::DoubleDiscrimination,
        other => Role::Other(other.join("+")),
    }
}

/// Deterministic neutral label for a response delta, as the sealed receipts
/// print it: `form1+inst1`, `form2+inst2diag`, `datum+inst2+fresh`, …
pub fn delta_label(base: &Regime, delta: &Delta) -> String {
    let n0 = base.n_data();
    let parts: Vec<String> = delta
        .iter()
        .map(|it| match it {
            Item::NewDatum => "datum".to_string(),
            Item::NewForm(a) => format!("form{a}"),
            Item::NewRuleAll(f) => format!("rule@{f}"),
            Item::NewInst(_, args) => {
                let distinct: std::collections::BTreeSet<usize> = args.iter().map(|m| m.0).collect();
                let shape = if distinct.len() == 1 && args.len() > 1 { "diag" } else { "" };
                let fresh = if args.iter().any(|m| m.0 >= n0) { "+fresh" } else { "" };
                format!("inst{}{shape}{fresh}", args.len())
            }
        })
        .collect();
    if parts.is_empty() {
        "empty".to_string()
    } else {
        parts.join("+")
    }
}

impl fmt::Display for Role {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Role::Supply => write!(f, "supply"),
            Role::Discrimination => write!(f, "discrimination"),
            Role::Innovation => write!(f, "innovation"),
            Role::AuxiliaryWitness => write!(f, "auxiliary_witness"),
            Role::DoubleDiscrimination => write!(f, "double_discrimination"),
            Role::Other(s) => write!(f, "{s}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn the_five_roles() {
        let m = |a: &[usize]| Item::NewInst(0, a.iter().map(|&x| Mark(x)).collect());
        assert_eq!(role(true, &vec![]), Role::Supply);
        assert_eq!(role(false, &vec![m(&[0])]), Role::Discrimination);
        assert_eq!(role(false, &vec![Item::NewForm(1), m(&[0])]), Role::Innovation);
        assert_eq!(role(false, &vec![Item::NewDatum, m(&[2])]), Role::AuxiliaryWitness);
        assert_eq!(role(false, &vec![m(&[0]), m(&[1])]), Role::DoubleDiscrimination);
    }

    #[test]
    fn labels_match_the_sealed_receipt_vocabulary() {
        let base = replay(&READING_L.genesis).unwrap();
        let m = |a: &[usize]| Item::NewInst(0, a.iter().map(|&x| Mark(x)).collect());
        assert_eq!(delta_label(&base, &vec![Item::NewForm(1), m(&[0])]), "form1+inst1");
        assert_eq!(delta_label(&base, &vec![Item::NewForm(2), m(&[0, 0])]), "form2+inst2diag");
        assert_eq!(delta_label(&base, &vec![Item::NewForm(2), m(&[0, 1])]), "form2+inst2");
        assert_eq!(delta_label(&base, &vec![Item::NewDatum, m(&[2])]), "datum+inst1+fresh");
        assert_eq!(delta_label(&base, &vec![]), "empty");
    }
}
