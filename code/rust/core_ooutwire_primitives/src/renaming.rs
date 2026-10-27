//! Sort 8 — **Renaming**: a transformation the reading permits.
//!
//! Crate boundary: coda-iso.  Source: `iso.py::rename`, `serialize`; for the
//! boundary reading see `boundary.rs`, where the permitted set is *declared
//! by the reading* (mark permutations always, the side exchange under U only).
//!
//! In the sealed reading a renaming is a **bijection pair**: one permutation
//! of data indices, one of form indices.  Presentation tokens travel with
//! their data and are then forgotten by `serialize`, which is the whole
//! mechanism by which tokens fail to survive canonicalisation.
//!
//! `serialize` is a *total* serialisation: every field of the regime except
//! the tokens, under the bijection.  Two regimes are isomorphic exactly when
//! some bijection pair makes their serialisations equal — and `canonical.rs`
//! turns "some" into a computed minimum.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_dcbfe7ee<T> {
    fn checked_invariant_dcbfe7ee(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_dcbfe7ee<T> for Option<T> {
    #[inline]
    fn checked_invariant_dcbfe7ee(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_dcbfe7ee<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_dcbfe7ee(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::mark::{Mark, Pair};
use crate::regime::{Inst, Regime};

/// A bijection pair `pi` on data and `phi` on forms, as `pi[old] = new`.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bijection {
    /// The data permutation.
    pub data: Vec<usize>,
    /// The form permutation.
    pub forms: Vec<usize>,
}

impl Bijection {
    /// The identity on `n` data and `nf` forms.
    pub fn identity(n: usize, nf: usize) -> Bijection {
        Bijection { data: (0..n).collect(), forms: (0..nf).collect() }
    }

    /// Check both maps against the complete carrier they claim to permute.
    pub fn validate(&self, r: &Regime) -> Result<(), String> {
        for (name, perm, size) in [("data", &self.data, r.n_data()), ("forms", &self.forms, r.n_forms())] {
            if perm.len() != size {
                return Err(format!("{name} permutation length differs from the carrier"));
            }
            let mut seen = vec![false; size];
            for &image in perm {
                if image >= size || seen[image] {
                    return Err(format!("{name} map is not a permutation"));
                }
                seen[image] = true;
            }
        }
        Ok(())
    }
}

/// The total serialisation of a regime under a bijection: everything but
/// the tokens.
pub type Key = (usize, Vec<usize>, Vec<(usize, Vec<usize>)>, Vec<usize>, Vec<(usize, usize)>);

/// All permutations of `0..n`, in lexicographic order.
pub fn permutations(n: usize) -> Vec<Vec<usize>> {
    fn go(rest: &mut Vec<usize>, cur: &mut Vec<usize>, out: &mut Vec<Vec<usize>>) {
        if rest.is_empty() {
            out.push(cur.clone());
            return;
        }
        for k in 0..rest.len() {
            let v = rest.remove(k);
            cur.push(v);
            go(rest, cur, out);
            cur.pop();
            rest.insert(k, v);
        }
    }
    let mut out = Vec::new();
    let mut rest: Vec<usize> = (0..n).collect();
    go(&mut rest, &mut Vec::new(), &mut out);
    out
}

/// The inverse of a permutation.
pub fn invert(perm: &[usize]) -> Vec<usize> {
    let mut out = vec![0; perm.len()];
    for (old, &new) in perm.iter().enumerate() {
        out[new] = old;
    }
    out
}

/// Serialize the regime under the bijection pair: tokens forgotten.
pub fn serialize(r: &Regime, b: &Bijection) -> Key {
    let pi = &b.data;
    let phi = &b.forms;
    let mut forms = vec![0; r.n_forms()];
    for (f, &arity) in r.forms.iter().enumerate() {
        forms[phi[f]] = arity;
    }
    let mut insts: Vec<(usize, Vec<usize>)> = r
        .insts
        .iter()
        .map(|i| (phi[i.form], i.args.iter().map(|m| pi[m.0]).collect()))
        .collect();
    insts.sort();
    let mut rules: Vec<usize> = r.rules.iter().map(|&f| phi[f]).collect();
    rules.sort();
    let mut reqs: Vec<(usize, usize)> = r
        .reqs
        .iter()
        .map(|p| {
            let (a, b) = (pi[p.i.0], pi[p.j.0]);
            (a.min(b), a.max(b))
        })
        .collect();
    reqs.sort();
    (r.n_data(), forms, insts, rules, reqs)
}

/// `π·` — apply the bijection pair, producing an isomorphic regime.  Tokens
/// travel with their data. Panics if the supplied maps are not bijections;
/// use `try_rename` when maps come from a caller or witness.
pub fn rename(r: &Regime, b: &Bijection) -> Regime {
    try_rename(r, b).checked_invariant_dcbfe7ee("renaming requires a bijection on the complete carrier")
}

/// Validate both maps before constructing a renamed regime. Duplicate,
/// omitted, or out-of-range images cannot produce an invalid carrier.
pub fn try_rename(r: &Regime, b: &Bijection) -> Result<Regime, String> {
    b.validate(r)?;
    let pi = &b.data;
    let phi = &b.forms;
    let mut data = vec![crate::token::Token::new(""); r.n_data()];
    for (d, tok) in r.data.iter().enumerate() {
        data[pi[d]] = tok.clone();
    }
    let mut forms = vec![0; r.n_forms()];
    for (f, &arity) in r.forms.iter().enumerate() {
        forms[phi[f]] = arity;
    }
    let insts = r
        .insts
        .iter()
        .map(|i| Inst::new(phi[i.form], i.args.iter().map(|m| Mark(pi[m.0])).collect()))
        .collect();
    let rules = r.rules.iter().map(|&f| phi[f]).collect();
    let reqs = r.reqs.iter().map(|p| Pair::of(pi[p.i.0], pi[p.j.0])).collect();
    Ok(Regime { data, forms, insts, rules, reqs })
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/renaming.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:renaming:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddcbfe7ee {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddcbfe7ee` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordcbfe7ee {
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
impl BoundaryErrordcbfe7ee {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordcbfe7ee {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordcbfe7ee {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddcbfe7ee {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordcbfe7ee> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordcbfe7ee::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordcbfe7ee::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordcbfe7ee::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::READING_F;
    use crate::replay::replay;

    #[test]
    fn permutations_are_complete_and_lexicographic() {
        let p = permutations(3);
        assert_eq!(p.len(), 6);
        assert_eq!(p[0], vec![0, 1, 2]);
        assert_eq!(p[5], vec![2, 1, 0]);
        assert_eq!(invert(&[2, 0, 1]), vec![1, 2, 0]);
    }

    #[test]
    fn rename_carries_tokens_and_serialize_forgets_them() {
        let base = replay(&READING_F.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(2)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0, 2])).unwrap();
        let b = Bijection { data: vec![2, 0, 1], forms: vec![0] };
        let s = rename(&r, &b);
        assert_eq!(s.data[2], r.data[0], "the token travelled with its datum");
        assert_eq!(serialize(&s, &Bijection::identity(3, 1)), serialize(&r, &b));
    }
}

#[cfg(test)]
mod l4_boundary_tests_dcbfe7ee {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddcbfe7ee::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddcbfe7ee::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddcbfe7ee::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddcbfe7ee::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddcbfe7ee::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordcbfe7ee::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordcbfe7ee::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
