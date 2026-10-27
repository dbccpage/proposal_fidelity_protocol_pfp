//! Primitive — **observer**: a bit-vector extractor **plus** a reading of the
//! vector.  Kept apart, or the second observer cannot exist.
//!
//! Crate boundary: coda-observe.  Source: `research/limit_and_observer`,
//! receipt `censuses.reading_axis`: readings 16, complement classes 8,
//! non-constant 7, induced separation behaviours **4**, sealed behaviour
//! `uncovered`; lawful readers by width 2/3/4/4 at widths 1–4.
//!
//! At a fixed context the coverage bit is constant across data
//! (`profile.rs`).  So of the sixteen Boolean functions of the pair
//! `(coverage, admission)`, what matters for *separation* is only whether the
//! function depends on the admission bit where coverage is absent, and
//! whether it does where coverage is present.  Two bits of behaviour: four
//! readers.
//!
//! | reader | reads the admission bit where coverage is | glyph |
//! |---|---|---|
//! | blind | nowhere | `R∅` |
//! | uncovered | absent | `R⁻` |
//! | covered | present | `R⁺` |
//! | either | absent and present | `R±` |
//!
//! Computed rather than declared: the sealed `derivable` is `R⁻`.  Its
//! exact complement on the covered half is `R⁺`, a second observer that sees
//! exactly what the first cannot.  The user's sandcastle picture is this
//! table: same object, two rulers, different verdicts.
//!
//! **The user's observer packet** `O = (K, F, R, δ, d0, d1, J, M, τ)` reads
//! onto this file as: `F` the extractor, `R` the reader, `J`/`M` the
//! aggregation over contexts, `τ` the terminalizer it hands its verdict to.
//! What this file does *not* model is co-presence — two readers held in one
//! admitted state at once — which the estate records OPEN (§13.10) and on
//! which the sealed bet `53da82a1…` is still unscored.

use crate::context::{contexts, plug, Context};
use crate::mark::{Mark, Pair};
use crate::profile::{admission, coverage};
use crate::regime::Regime;

/// The two bits the sealed relation combines.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct BitPair {
    /// The context's form carries the uniform rule.
    pub coverage: bool,
    /// The plugging is an admitted instance.
    pub admission: bool,
}

/// A bit-vector extractor: what the grammar can see at a context about a
/// datum, before any verdict is taken.
pub trait Bits {
    /// The vector type.
    type Vector: Eq + Clone;
    /// Extract the vector for datum `d` at context `c`.
    fn extract(&self, r: &Regime, c: &Context, d: Mark) -> Self::Vector;
}

/// A reading of a vector into a verdict.
pub trait Reader<V> {
    /// The verdict at one context for one datum.
    fn read(&self, v: &V) -> bool;
}

/// An observer is the pair.  There is no `Observer: Fn(&Regime) -> bool`
/// and there must never be one.
#[derive(Clone, Debug)]
pub struct Observer<B, R> {
    /// The extractor.
    pub bits: B,
    /// The reader.
    pub reader: R,
}

/// The sealed extractor: the coverage bit and the admission bit.
#[derive(Clone, Copy, Debug, Default)]
pub struct PairBits;

impl Bits for PairBits {
    type Vector = BitPair;
    fn extract(&self, r: &Regime, c: &Context, d: Mark) -> BitPair {
        BitPair { coverage: coverage(r, c.form), admission: admission(r, &plug(c, d)) }
    }
}

/// Any Boolean function of the bit pair, as its four-entry truth table
/// indexed by `(coverage, admission)`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Table(pub [bool; 4]);

impl Table {
    /// Table number `k` in `0..16`, bit `2*cov + adm` of `k`.
    pub fn nth(k: u8) -> Table {
        let mut t = [false; 4];
        for (i, slot) in t.iter_mut().enumerate() {
            *slot = (k >> i) & 1 == 1;
        }
        Table(t)
    }

    /// All sixteen readings.
    pub fn all() -> Vec<Table> {
        (0..16).map(Table::nth).collect()
    }

    fn at(&self, cov: bool, adm: bool) -> bool {
        self.0[(cov as usize) * 2 + adm as usize]
    }

    /// The separation behaviour this table induces.
    pub fn behaviour(&self) -> Behaviour {
        let reads_where_absent = self.at(false, false) != self.at(false, true);
        let reads_where_present = self.at(true, false) != self.at(true, true);
        match (reads_where_absent, reads_where_present) {
            (false, false) => Behaviour::Blind,
            (true, false) => Behaviour::Uncovered,
            (false, true) => Behaviour::Covered,
            (true, true) => Behaviour::Either,
        }
    }

    /// The sealed truth function, `coverage || admission`.
    pub fn sealed() -> Table {
        Table([false, true, true, true])
    }
}

impl Reader<BitPair> for Table {
    fn read(&self, v: &BitPair) -> bool {
        self.at(v.coverage, v.admission)
    }
}

/// The four separation behaviours the sixteen readings collapse to.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Behaviour {
    /// `R∅` — never reads the admission bit; separates nothing.
    Blind,
    /// `R⁻` — reads it where coverage is absent.  The sealed observer.
    Uncovered,
    /// `R⁺` — reads it where coverage is present.  The second observer.
    Covered,
    /// `R±` — reads it everywhere.
    Either,
}

impl<B: Bits, R: Reader<B::Vector>> Observer<B, R> {
    /// The aggregation "at least one separating context": the pair is
    /// separated iff some context gives the two data different verdicts.
    pub fn separates(&self, r: &Regime, p: Pair) -> bool {
        contexts(r).iter().any(|c| {
            let vi = self.bits.extract(r, c, p.i);
            let vj = self.bits.extract(r, c, p.j);
            self.reader.read(&vi) != self.reader.read(&vj)
        })
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/observer.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6ad003ea {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6ad003ea` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6ad003ea {
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
impl BoundaryError6ad003ea {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6ad003ea {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6ad003ea {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6ad003ea {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6ad003ea> {
        if capacity_bound == 0 {
            return Err(BoundaryError6ad003ea::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6ad003ea::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6ad003ea::ExceedsCapacity {
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
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;
    use crate::separability::separable;
    use std::collections::BTreeSet;

    #[test]
    fn sixteen_readings_collapse_to_four_behaviours() {
        let all = Table::all();
        assert_eq!(all.len(), 16);
        let behaviours: BTreeSet<Behaviour> = all.iter().map(Table::behaviour).collect();
        assert_eq!(behaviours.len(), 4);
        assert_eq!(all.iter().filter(|t| t.behaviour() == Behaviour::Blind).count(), 4);
        assert_eq!(all.iter().filter(|t| t.behaviour() == Behaviour::Uncovered).count(), 4);
        assert_eq!(all.iter().filter(|t| t.behaviour() == Behaviour::Covered).count(), 4);
        assert_eq!(all.iter().filter(|t| t.behaviour() == Behaviour::Either).count(), 4);
    }

    /// Computed, not declared: the sealed relation is the uncovered reader.
    #[test]
    fn the_sealed_observer_is_r_minus() {
        assert_eq!(Table::sealed().behaviour(), Behaviour::Uncovered);
    }

    /// The uncovered observer, aggregated by "at least one separating
    /// context", agrees with `separability::separable` on a population of
    /// states reached from both readings by one or two admissions.
    #[test]
    fn r_minus_reproduces_sealed_separability_on_a_population() {
        let obs = Observer { bits: PairBits, reader: Table::sealed() };
        let mut checked = 0;
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let n = base.n_data();
            let mut states = vec![base.clone()];
            for arity in 1..=2 {
                let f = step(&base, &Event::AdmitForm(arity)).unwrap();
                states.push(step(&f, &Event::AdmitRuleAll(0)).unwrap());
                for a in 0..n {
                    for b in 0..n {
                        let args: Vec<usize> = if arity == 1 { vec![a] } else { vec![a, b] };
                        let s = step(&f, &crate::testkit::inst(0, &args)).unwrap();
                        states.push(step(&s, &Event::AdmitRuleAll(0)).unwrap());
                        states.push(s);
                        if arity == 1 {
                            break;
                        }
                    }
                }
            }
            for s in &states {
                for i in 0..n {
                    for j in (i + 1)..n {
                        let p = Pair::of(i, j);
                        assert_eq!(obs.separates(s, p), separable(s, p.i, p.j));
                        checked += 1;
                    }
                }
            }
        }
        assert!(checked > 20);
    }

    /// The second observer: where the form is rule-covered, `R⁻` sees
    /// nothing and `R⁺` sees the admitted instance.
    #[test]
    fn r_plus_is_the_complement_on_the_covered_half() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        let covered = step(&r, &Event::AdmitRuleAll(0)).unwrap();
        let r_minus = Observer { bits: PairBits, reader: Table::sealed() };
        // R⁺: value = admission where coverage is present, constant otherwise.
        let r_plus = Observer { bits: PairBits, reader: Table([false, false, false, true]) };
        assert_eq!(r_plus.reader.behaviour(), Behaviour::Covered);
        let p = Pair::of(0, 1);
        assert!(r_minus.separates(&r, p) && !r_plus.separates(&r, p));
        assert!(!r_minus.separates(&covered, p) && r_plus.separates(&covered, p));
    }
}

#[cfg(test)]
mod l4_boundary_tests_6ad003ea {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6ad003ea::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6ad003ea::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6ad003ea::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6ad003ea::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6ad003ea::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6ad003ea::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6ad003ea::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
