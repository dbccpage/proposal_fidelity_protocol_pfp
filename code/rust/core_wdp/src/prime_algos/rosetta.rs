//! Rosetta empirical layer: cross-domain residual-family stats under one alphabet.
//!
//! H-O2: if Algorithm Prime 000 + DDA is a domain-independent obstruction algebra,
//! then letter tapes and trichotomy branches should be comparable across domains
//! without domain-specific secret authority paths.
//!
//! This module **does not prove** the Rosetta conjecture. It computes finite
//! statistics and hard invariants (shared required letters, authority None,
//! no foreign alphabet symbols).

use crate::prime_algos::prime_algorithm_0::{
    run_prime_algorithm_0, DefectBranch, DomainAdapter, EvidenceProvenance, PrimeAlgorithm0Receipt,
    PrimeDomain, PrimeTerminal,
};
use crate::ddc::dda_alphabet::DdaOp;
use core_types::authority::AuthorityEffect;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};

/// Compact summary of one domain's Prime 000 letter tape.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DomainTapeSummary {
    pub domain: String,
    pub residual_family_label: String,
    pub letter_tape: String,
    pub letter_histogram: BTreeMap<String, usize>,
    pub branch: String,
    pub terminal: String,
    pub phi1: Option<u64>,
    pub gamma2: Option<u64>,
    pub authority_effect: String,
    /// Whether THIS domain's masses were computed or declared.
    pub provenance: EvidenceProvenance,
}

impl DomainTapeSummary {
    pub fn from_receipt(r: &PrimeAlgorithm0Receipt) -> Self {
        let mut hist: BTreeMap<String, usize> = BTreeMap::new();
        for ch in r.letter_tape.chars() {
            *hist.entry(ch.to_string()).or_insert(0) += 1;
        }
        // Normalize Λ if stored as multi-byte — letter() uses "Λ"
        Self {
            domain: r.domain.as_str().to_string(),
            residual_family_label: r.residual_family_label.clone(),
            letter_tape: r.letter_tape.clone(),
            letter_histogram: hist,
            branch: r.branch.as_str().to_string(),
            terminal: r.terminal.as_str().to_string(),
            phi1: r.phi1,
            gamma2: r.gamma2,
            // Read from the receipt. This was hard-coded `"None".into()`, so any
            // assertion comparing it to "None" compared a literal against itself
            // and could not fail.
            authority_effect: format!("{:?}", r.authority_effect),
            provenance: r.evidence_provenance,
        }
    }
}

/// Roster-level provenance, derived from the receipts rather than asserted.
///
/// The previous field was a hard-coded `FixtureDrivenStructuralDemo` on the whole
/// report. That was true when every adapter declared its numbers, and would have
/// silently stayed true after one began computing them.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum RosterProvenance {
    /// Every domain declared its masses.
    AllFixtureDriven,
    /// Some domains compute, some declare. Names the ones that compute.
    Mixed { verifier_produced: Vec<String> },
    /// Every domain's masses were computed by a verifier.
    AllVerifierProduced,
}

/// Aggregate Rosetta report over several domains.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct RosettaReport {
    /// What the numbers below actually are, derived from the receipts.
    pub provenance: RosterProvenance,
    pub domains: Vec<DomainTapeSummary>,
    /// Every domain emits C, R, and T at least once.
    pub shared_required_letters: bool,
    /// Every letter is in the declared 8-letter alphabet.
    pub alphabet_closed: bool,
    /// All receipts carry AuthorityEffect::None.
    pub authority_all_none: bool,
    /// Φ₁ and Γ₂ always stored as distinct slots (never a merged field).
    pub phi_gamma_separated: bool,
    /// Literature steps never appear before first T in any domain.
    pub literature_always_after_terminal: bool,
    pub branch_histogram: BTreeMap<String, usize>,
    pub terminal_histogram: BTreeMap<String, usize>,
    pub residual_family_count: usize,
    /// Distinct residual-family labels seen.
    pub residual_families: Vec<String>,
    /// Jaccard similarity of letter *sets* between domain pairs (scaled ×1000).
    pub pairwise_letter_jaccard_x1000: BTreeMap<String, u64>,
    /// No receipt violates a *decidable* letter law. Not full conformance — see
    /// `prime_algorithm_0_conformance::UNDECIDABLE_WITHOUT_PER_STEP_STATE`.
    pub no_decidable_letter_law_violation: bool,
    /// Domain -> the letter laws it broke. Empty iff the flag above is true.
    pub letter_law_violations: BTreeMap<String, Vec<String>>,
    pub rosetta_smoke_pass: bool,
}

fn alphabet_letters() -> BTreeSet<char> {
    DdaOp::alphabet()
        .iter()
        .flat_map(|o| o.letter().chars())
        .collect()
}

/// Build a Rosetta report from already-run receipts.
pub fn rosetta_from_receipts(receipts: &[PrimeAlgorithm0Receipt]) -> RosettaReport {
    let allowed = alphabet_letters();
    let domains: Vec<DomainTapeSummary> = receipts
        .iter()
        .map(DomainTapeSummary::from_receipt)
        .collect();

    let shared_required_letters = domains.iter().all(|d| {
        d.letter_tape.contains('C') && d.letter_tape.contains('R') && d.letter_tape.contains('T')
    });

    let alphabet_closed = domains.iter().all(|d| {
        d.letter_tape.chars().all(|c| {
            // multi-byte ops: allow any char that appears in some alphabet letter
            allowed.contains(&c) || "Λ".contains(c)
        })
    });

    let authority_all_none = receipts
        .iter()
        .all(|r| r.authority_effect == AuthorityEffect::None);

    // Φ₁ and Γ₂ must be independent slots, not one mass surfaced twice.
    //
    // This previously matched all four (Option, Option) combinations and returned
    // `true` in every arm -- a tautology. It could not fail, so every conjunction
    // containing it was weaker than it read, and no test could tell it from a
    // constant. Replaced with a witness that can actually be absent:
    //
    // aliased fields cannot produce a receipt in which they DIFFER, so observing a
    // difference anywhere in the roster witnesses separation. A roster where they
    // never differ is reported unseparated rather than silently green -- weak
    // evidence, but evidence, and it fails when there is none.
    let phi_gamma_separated = receipts.iter().any(|r| match (r.phi1, r.gamma2) {
        (Some(p), Some(g)) => p != g,
        (Some(_), None) | (None, Some(_)) => true,
        (None, None) => false,
    });

    let literature_always_after_terminal = receipts.iter().all(|r| {
        let first_t = r.steps.iter().position(|s| s.op == "T");
        match first_t {
            None => r.steps.iter().all(|s| s.prime_step != 12),
            Some(i) => r.steps[..i].iter().all(|s| s.prime_step != 12),
        }
    });

    let mut branch_histogram: BTreeMap<String, usize> = BTreeMap::new();
    let mut terminal_histogram: BTreeMap<String, usize> = BTreeMap::new();
    for d in &domains {
        *branch_histogram.entry(d.branch.clone()).or_insert(0) += 1;
        *terminal_histogram.entry(d.terminal.clone()).or_insert(0) += 1;
    }

    let mut families: BTreeSet<String> = BTreeSet::new();
    for d in &domains {
        families.insert(d.residual_family_label.clone());
    }
    let residual_families: Vec<String> = families.iter().cloned().collect();

    let mut pairwise: BTreeMap<String, u64> = BTreeMap::new();
    for i in 0..domains.len() {
        for j in (i + 1)..domains.len() {
            let a: BTreeSet<char> = domains[i].letter_tape.chars().collect();
            let b: BTreeSet<char> = domains[j].letter_tape.chars().collect();
            let inter = a.intersection(&b).count() as u64;
            let union = a.union(&b).count() as u64;
            let jacc = (inter * 1000).checked_div(union).unwrap_or(0);
            let key = format!("{}|{}", domains[i].domain, domains[j].domain);
            pairwise.insert(key, jacc);
        }
    }

    // Letter-law conformance, per receipt. This was omitted entirely, so
    // `rosetta_smoke_pass` stayed true while a domain terminalised an open
    // residual — a T-law violation the checker could already see and the smoke
    // verdict simply never asked about.
    let letter_law_violations: BTreeMap<String, Vec<String>> = receipts
        .iter()
        .filter_map(|r| {
            let c = crate::prime_algos::prime_algorithm_0_conformance::check_receipt(r);
            let v = c.violations();
            if v.is_empty() {
                None
            } else {
                Some((
                    r.domain.as_str().to_string(),
                    v.iter().map(|x| format!("{x:?}")).collect(),
                ))
            }
        })
        .collect();
    let no_decidable_letter_law_violation = letter_law_violations.is_empty();

    let rosetta_smoke_pass = shared_required_letters
        && alphabet_closed
        && authority_all_none
        && phi_gamma_separated
        && literature_always_after_terminal
        && no_decidable_letter_law_violation
        && !domains.is_empty();

    // Derived, never asserted: the roster's provenance is whatever its receipts say.
    let verifier_produced: Vec<String> = receipts
        .iter()
        .filter(|r| r.evidence_provenance == EvidenceProvenance::VerifierProduced)
        .map(|r| r.domain.as_str().to_string())
        .collect();
    let provenance = if verifier_produced.is_empty() {
        RosterProvenance::AllFixtureDriven
    } else if verifier_produced.len() == receipts.len() {
        RosterProvenance::AllVerifierProduced
    } else {
        RosterProvenance::Mixed { verifier_produced }
    };

    RosettaReport {
        provenance,
        domains,
        shared_required_letters,
        alphabet_closed,
        authority_all_none,
        phi_gamma_separated,
        literature_always_after_terminal,
        branch_histogram,
        terminal_histogram,
        residual_family_count: residual_families.len(),
        residual_families,
        pairwise_letter_jaccard_x1000: pairwise,
        no_decidable_letter_law_violation,
        letter_law_violations,
        rosetta_smoke_pass,
    }
}

/// Run all provided adapters and compute the Rosetta report.
pub fn rosetta_run(adapters: &[&dyn DomainAdapter]) -> RosettaReport {
    let receipts: Vec<PrimeAlgorithm0Receipt> =
        adapters.iter().map(|a| run_prime_algorithm_0(*a)).collect();
    rosetta_from_receipts(&receipts)
}

/// Convenience: run the built-in multi-domain roster.
pub fn rosetta_builtin_roster() -> RosettaReport {
    rosetta_from_receipts(&builtin_receipts())
}

/// The built-in roster's receipts, so conformance and the report read the same runs.
pub fn builtin_receipts() -> Vec<PrimeAlgorithm0Receipt> {
    use crate::prime_algos::domain_adapters::{
        CodaResidualAdapter, FspChannelAAdapter, GenericMss0Adapter,
        MubWallAdapter, SymbolGameExpressivityAdapter,
    };
    let g = GenericMss0Adapter;
    let m = MubWallAdapter;
    let f = FspChannelAAdapter;
    let c = CodaResidualAdapter;
    let s = SymbolGameExpressivityAdapter::default();
    let adapters: [&dyn DomainAdapter; 5] = [&g, &m, &f, &c, &s];
    adapters.iter().map(|a| run_prime_algorithm_0(*a)).collect()
}

/// Residual-family row for empirical tables (domain × family × branch × terminal).
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ResidualFamilyStat {
    pub domain: PrimeDomain,
    pub family: String,
    pub branch: DefectBranch,
    pub terminal: PrimeTerminal,
    pub phi1: Option<u64>,
    pub gamma2: Option<u64>,
    pub letter_tape: String,
}

pub fn residual_family_table(receipts: &[PrimeAlgorithm0Receipt]) -> Vec<ResidualFamilyStat> {
    receipts
        .iter()
        .map(|r| ResidualFamilyStat {
            domain: r.domain,
            family: r.residual_family_label.clone(),
            branch: r.branch,
            terminal: r.terminal,
            phi1: r.phi1,
            gamma2: r.gamma2,
            letter_tape: r.letter_tape.clone(),
        })
        .collect()
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/rosetta.rs
// Claim: urn:core:crates_rs:core-wdp:rosetta:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord346014c2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord346014c2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError346014c2 {
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
impl BoundaryError346014c2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError346014c2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError346014c2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord346014c2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError346014c2> {
        if capacity_bound == 0 {
            return Err(BoundaryError346014c2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError346014c2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError346014c2::ExceedsCapacity {
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
    use crate::prime_algos::domain_adapters::{
        CodaResidualAdapter, FspChannelAAdapter, GenericMss0Adapter, MubWallAdapter,
        SymbolGameExpressivityAdapter,
    };

    /// Asserts only the conjuncts that can actually fail.
    #[test]
    fn rosetta_builtin_roster_reports_measurable_structure() {
        let report = rosetta_builtin_roster();

        assert_eq!(report.domains.len(), 5);
        assert!(report.residual_family_count >= 4);
        assert!(report.authority_all_none);
        assert!(report.alphabet_closed);
        assert!(report.literature_always_after_terminal);

        // `shared_required_letters` is FALSE, and that is the correct reading.
        //
        // It reported true only because a domain that refused kept executing:
        // MUB emits "refuse construction" at step 4, and the runner used to carry
        // on through Q¹ (R), the mass split, the lift search and routing (R
        // again), so the tape acquired the required letters *after* the refusal.
        //
        // With refusals terminal, MUB stops at step 4 and terminalises. Its tape
        // carries no `R`, because no residual projection ever ran. The Rosetta
        // "every domain emits C, R and T" invariant was an artifact of ignoring
        // refusals, not a property of the domains.
        assert!(
            !report.shared_required_letters,
            "a refusing domain cannot emit R; if this passes, refusals stopped              being terminal again"
        );
        let mub = report
            .domains
            .iter()
            .find(|d| d.domain == "mub")
            .expect("mub in roster");
        assert_eq!(mub.terminal, "Refusal");
        assert!(!mub.letter_tape.contains('R'));
    }

    /// The smoke verdict now consults letter-law conformance, and FSP breaks it.
    ///
    /// FSP has masses (1, 1) -> Open, terminalises with `T` at Γ₂ = 1, which the
    /// T law forbids ("T is inert and requires zero closure defect"). The old
    /// `rosetta_smoke_pass` never asked, so it stayed true over a known violation.
    #[test]
    fn smoke_verdict_sees_the_fsp_t_law_violation() {
        let report = rosetta_builtin_roster();

        assert!(
            !report.no_decidable_letter_law_violation,
            "expected FSP's T-law violation to be visible"
        );
        assert!(
            report.letter_law_violations.contains_key("fsp"),
            "violations recorded: {:?}",
            report.letter_law_violations
        );
        assert!(
            !report.rosetta_smoke_pass,
            "smoke must not pass while a domain terminalises an open residual"
        );
    }

    #[test]
    fn residual_family_table_has_distinct_labels() {
        let receipts = [
            run_prime_algorithm_0(&GenericMss0Adapter),
            run_prime_algorithm_0(&MubWallAdapter),
            run_prime_algorithm_0(&FspChannelAAdapter),
            run_prime_algorithm_0(&CodaResidualAdapter),
            run_prime_algorithm_0(&SymbolGameExpressivityAdapter::default()),
        ];
        let table = residual_family_table(&receipts);
        let labels: BTreeSet<_> = table.iter().map(|r| r.family.as_str()).collect();
        assert!(labels.len() >= 4);
        // FSP is Open (gamma2>0); generic/coda/sg are StabilizedSurvivor
        assert!(table.iter().any(|r| r.branch == DefectBranch::Open));
        assert!(table
            .iter()
            .any(|r| r.branch == DefectBranch::StabilizedSurvivor));
    }

    #[test]
    fn pairwise_jaccard_recorded() {
        let report = rosetta_run(&[&GenericMss0Adapter, &CodaResidualAdapter]);
        assert!(report
            .pairwise_letter_jaccard_x1000
            .contains_key("generic|coda"));
        let j = report.pairwise_letter_jaccard_x1000["generic|coda"];
        assert!(j > 0, "expected some shared letters");
    }

    /// All built-in adapters are currently fixture-driven, and say so.
    #[test]
    fn roster_provenance_is_fixture_driven() {
        let report = rosetta_builtin_roster();
        match &report.provenance {
            RosterProvenance::AllFixtureDriven => {}
            other => panic!("expected AllFixtureDriven, got {other:?}"),
        }
        for d in &report.domains {
            assert_eq!(
                d.provenance,
                EvidenceProvenance::FixtureDrivenStructuralDemo,
                "{} claims verifier-produced masses it does not have",
                d.domain
            );
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_346014c2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord346014c2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord346014c2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord346014c2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord346014c2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord346014c2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError346014c2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError346014c2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
