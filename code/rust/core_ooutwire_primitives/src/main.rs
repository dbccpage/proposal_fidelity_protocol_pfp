//! `omega` — run the engine and print what it did, what it asked for, and
//! what it refused to claim.
//!
//! ```text
//! cargo run --release            # the sealed situations, pushed and unpushed
//! cargo run --release -- --full  # also rebuild the depth-15 trees (963 / 1847 nodes)
//! ```
//!
//! `AuthorityEffect: None.`


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_89ee294e<T> {
    fn checked_invariant_89ee294e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_89ee294e<T> for Option<T> {
    #[inline]
    fn checked_invariant_89ee294e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_89ee294e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_89ee294e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_ooutwire_primitives::boundary::reflection_census;
use core_ooutwire_primitives::bounds::Bounds;
use core_ooutwire_primitives::hash::hex;
use core_ooutwire_primitives::measure::{Measure, MeasureKind};
use core_ooutwire_primitives::minima::challenge3;
use core_ooutwire_primitives::engine::{Config, Gate, Core, Report};
use core_ooutwire_primitives::outside::{Scripted, Silent};
use core_ooutwire_primitives::reading::{readings, Reading};
use core_ooutwire_primitives::replay::replay;
use core_ooutwire_primitives::tree::build_tree;

fn print_move(m: &core_ooutwire_primitives::engine::Move) {
    let prices: Vec<String> = m.prices.iter().map(|(mk, c, n)| format!("{}={:?} in {} class(es)", mk.name(), c, n)).collect();
    println!(
        "  round {:>2}  target {}  origin {:?}  menu {}  repairs {}  augmentations {}  gate {:?}  role {}",
        m.round,
        m.target,
        m.origin,
        m.menu_size,
        m.repairs,
        m.augmentations,
        m.gate,
        m.role.as_ref().map_or("-".to_string(), |r| r.to_string())
    );
    if !prices.is_empty() {
        println!("            prices: {}", prices.join("; "));
    }
    for (k, c) in m.classes.iter().enumerate() {
        let mark = if m.chosen == Some(k) { "*" } else { " " };
        println!("            {mark} class {k}: {} (size {})", c.label, c.size);
    }
    if let Some(c) = &m.certificate {
        println!("            {c}");
    }
    if m.gate == Gate::Passed {
        println!("            {} -> {}", hex(m.fp_before), hex(m.fp_after));
    }
}

fn print_checklist_and_claims(report: &Report) {
    println!("checklist     {}/{} construction-summary items (not an independent proof audit)", report.checklist.iter().filter(|(_, ok)| *ok).count(), report.checklist.len());
    for (item, ok) in &report.checklist {
        println!("  [{}] {item}", if *ok { "x" } else { " " });
    }
    println!("not claimed:");
    for n in &report.not_claimed {
        println!("  - {n}");
    }
    println!();
}

fn print_report(title: &str, report: &Report, bounds: &Bounds) {
    println!("=== {title} ===");
    println!("terminal      {}  — {}", report.terminated.terminal, report.terminated.reason);
    println!("scope         {}", report.terminated.scope);
    if let Some(c) = &report.terminated.certificate {
        println!("certificate   {c}");
    }
    println!("fingerprint   {}", hex(report.fingerprint));
    println!("history       {} event(s); {} move(s)", report.history.len(), report.moves.len());
    for m in &report.moves {
        print_move(m);
    }
    if !report.witnesses.is_empty() {
        println!("witnesses     {}", report.witnesses.iter().map(|(p, w)| format!("{p}: {w}")).collect::<Vec<_>>().join("; "));
    }
    println!("blind spot    {}", if report.blind_spot.is_empty() { "none".to_string() } else { report.blind_spot.iter().map(|p| p.to_string()).collect::<Vec<_>>().join(", ") });
    match report.verify(bounds) {
        Ok(()) => println!("replay        every recorded fingerprint and support reproduced"),
        Err(e) => println!("replay        FAILED: {e}"),
    }
    print_checklist_and_claims(report);
}

fn run_reading(reading: &Reading) {
    let bounds = Bounds::default();
    // Unpushed: a silent outside.
    let mut cfg = Config::sealed(reading.name);
    cfg.closure_policy = false;
    let report = Core::new(Silent, cfg).run(&reading.genesis);
    print_report(&format!("reading {}, silent outside, closure policy off", reading.name), &report, &bounds);
    // Pushed: one demand, first class, licence, fuel.
    let script = Scripted::one_demand(reading.target, 6);
    let mut omega = Core::new(script, Config::sealed(reading.name));
    let report = omega.run(&reading.genesis);
    print_report(&format!("reading {}, scripted outside", reading.name), &report, &bounds);
    println!("what the outside was asked, in order:");
    for l in &omega.outside.log {
        println!("  {l}");
    }
    println!();
}

fn main() {
    let full = std::env::args().any(|a| a == "--full");
    println!("ooutwire_primitives — the Core engine over the sealed primitives.  AuthorityEffect: None.\n");

    println!("--- sealed Challenge 3, recomputed (pins: L mu1 6 raw / 3 classes; L mu2 2 / 1; F mu1 10 / 5; F mu2 2 / 1) ---");
    for reading in readings() {
        let base = replay(&reading.genesis).checked_invariant_89ee294e("genesis");
        for mk in MeasureKind::ALL {
            let c = challenge3(&base, reading.target, mk, &Bounds::default());
            let labels: Vec<String> = c.classes.iter().map(|k| format!("{}×{}", k.label, k.size)).collect();
            println!("  {} {}  cost {:?}  raw {}  classes {}  [{}]", reading.name, mk.name(), c.cost, c.valid_at_minimum, c.classes.len(), labels.join(", "));
        }
    }
    println!();

    println!("--- boundary reflection census, recomputed (pins from challenge0.json) ---");
    println!("  marks placements U-classes O-classes fixed");
    for row in reflection_census(4) {
        println!("  {:>5} {:>10} {:>9} {:>9} {:>5}", row.marks, row.placements, row.classes_under_u, row.classes_under_o, row.fixed_by_reflection_up_to_mark_renaming);
    }
    println!();

    for reading in readings() {
        run_reading(reading);
    }

    println!("--- closed-system baselines (pins: L 4 nodes / 3 terminal / 1 round; F 20 / 16 / 3) ---");
    for reading in readings() {
        let t = build_tree(reading, MeasureKind::Mu1, &Bounds::default(), 15, 250, false);
        let s = t.stats();
        println!("  {}  nodes {}  terminal {}  max depth {}  all certified {}", reading.name, s.nodes, t.terminal_branches(), s.max_depth, s.all_certified);
    }
    println!();

    if full {
        println!("--- depth-15 trees under mu2 with the external continuation policy (pins: L 963 nodes / 1022 edges; F 1847 / 1960) ---");
        for reading in readings() {
            let t = build_tree(reading, MeasureKind::Mu2, &Bounds::default(), 15, 3000, true);
            let s = t.stats();
            let roles: Vec<String> = s.roles.iter().map(|(k, v)| format!("{k} {v}")).collect();
            println!("  {}  nodes {}  edges {}  max depth {}  ties {}  roles [{}]  all certified {}", reading.name, s.nodes, s.edges, s.max_depth, s.expansions_with_ties, roles.join(", "), s.all_certified);
        }
        println!("--- guard-bounded trees under mu1, guard 1200 (sealed: L 1205 nodes / 1250 edges; F 1201 / 1244) ---");
        println!("    a guard cut depends on expansion order, and this crate's class order is not byte-identical");
        println!("    to the sealed one, so these agree closely and not exactly; the unguarded mu2 trees agree exactly");
        for reading in readings() {
            let t = build_tree(reading, MeasureKind::Mu1, &Bounds::default(), 15, 1200, true);
            let s = t.stats();
            println!("  {}  nodes {}  edges {}  max depth {}  by status {:?}", reading.name, s.nodes, s.edges, s.max_depth, s.by_status);
        }
    } else {
        println!("(pass --full to rebuild the depth-15 trees and compare against 963 / 1847 nodes)");
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/main.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89ee294e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89ee294e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89ee294e {
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
impl BoundaryError89ee294e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89ee294e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89ee294e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89ee294e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89ee294e> {
        if capacity_bound == 0 {
            return Err(BoundaryError89ee294e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89ee294e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89ee294e::ExceedsCapacity {
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
mod l4_boundary_tests_89ee294e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord89ee294e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord89ee294e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord89ee294e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord89ee294e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord89ee294e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError89ee294e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError89ee294e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
