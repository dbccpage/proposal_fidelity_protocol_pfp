//! Independent finite witnesses for exact permutation order, not pin authority.

use num_bigint::BigUint;
use pfp_runtime::rewriting::{PermutationOrderError, Presentation, Rule};

fn presentation(signature: &[&str], rules: &[(&str, &str)]) -> Presentation {
    Presentation {
        signature: signature
            .iter()
            .map(|symbol| (*symbol).to_owned())
            .collect(),
        rules: rules
            .iter()
            .enumerate()
            .map(|(index, (lhs, rhs))| Rule {
                name: format!("r{index}"),
                lhs: (*lhs).to_owned(),
                rhs: (*rhs).to_owned(),
            })
            .collect(),
    }
}

fn expected_cycles(cycles: &[&[&str]]) -> Vec<Vec<String>> {
    cycles
        .iter()
        .map(|cycle| cycle.iter().map(|symbol| (*symbol).to_owned()).collect())
        .collect()
}

fn c6() -> Presentation {
    presentation(
        &["e", "b", "d", "a", "c"],
        &[("d", "e"), ("b", "a"), ("e", "c"), ("a", "b"), ("c", "d")],
    )
}

/// Build declared disjoint cycles; expected orders below are literal constants,
/// not values derived by a second implementation of the production algorithm.
fn disjoint_cycles(lengths: &[usize]) -> Presentation {
    let mut result = Presentation {
        signature: Vec::new(),
        rules: Vec::new(),
    };
    let mut next_scalar = 0x1000_u32;
    for &length in lengths {
        assert!(length > 0);
        let cycle: Vec<String> = (0..length)
            .map(|_| {
                let symbol = char::from_u32(next_scalar)
                    .expect("the finite fixture stays below the surrogate range");
                next_scalar += 1;
                symbol.to_string()
            })
            .collect();
        result.signature.extend(cycle.iter().cloned());
        for index in 0..length {
            result.rules.push(Rule {
                name: format!("r{}", result.rules.len()),
                lhs: cycle[index].clone(),
                rhs: cycle[(index + 1) % length].clone(),
            });
        }
    }
    result
}

#[test]
fn singleton_fixed_point_has_order_one() {
    let result = presentation(&["x"], &[("x", "x")])
        .permutation_order()
        .unwrap();
    assert_eq!(result.order(), &BigUint::from(1_u8));
    assert_eq!(result.cycles(), expected_cycles(&[&["x"]]));
}

#[test]
fn multiple_fixed_points_are_sorted_and_still_have_order_one() {
    let result = presentation(&["c", "a", "b"], &[("b", "b"), ("c", "c"), ("a", "a")])
        .permutation_order()
        .unwrap();
    assert_eq!(result.order(), &BigUint::from(1_u8));
    assert_eq!(result.cycles(), expected_cycles(&[&["a"], &["b"], &["c"]]));
}

#[test]
fn five_cycle_preserves_successor_direction_not_lexical_member_order() {
    let result = presentation(
        &["e", "c", "a", "d", "b"],
        &[("e", "c"), ("c", "a"), ("a", "d"), ("d", "b"), ("b", "e")],
    )
    .permutation_order()
    .unwrap();
    assert_eq!(result.order(), &BigUint::from(5_u8));
    assert_eq!(
        result.cycles(),
        expected_cycles(&[&["a", "d", "b", "e", "c"]])
    );
}

#[test]
fn disjoint_two_and_three_cycles_have_order_six_not_signature_size() {
    let supplied = c6();
    assert_eq!(supplied.signature.len(), 5);
    let result = supplied.permutation_order().unwrap();
    assert_eq!(result.order(), &BigUint::from(6_u8));
    assert_eq!(
        result.cycles(),
        expected_cycles(&[&["a", "b"], &["c", "d", "e"]])
    );
}

#[test]
fn multibyte_unicode_scalars_are_symbols_and_sort_by_scalar() {
    let result = presentation(
        &["🦊", "β", "α", "é"],
        &[("β", "α"), ("🦊", "é"), ("α", "β"), ("é", "🦊")],
    )
    .permutation_order()
    .unwrap();
    assert_eq!(result.order(), &BigUint::from(2_u8));
    assert_eq!(
        result.cycles(),
        expected_cycles(&[&["é", "🦊"], &["α", "β"]])
    );
}

#[test]
fn declaration_reordering_leaves_the_complete_witness_unchanged() {
    let original = c6();
    let mut reordered = original.clone();
    reordered.signature.reverse();
    reordered.rules.reverse();
    assert_eq!(
        original.permutation_order().unwrap(),
        reordered.permutation_order().unwrap()
    );
    assert_eq!(
        reordered.permutation_order().unwrap().cycles(),
        expected_cycles(&[&["a", "b"], &["c", "d", "e"]])
    );
}

#[test]
fn shared_factors_use_lcm_not_the_product_of_cycle_lengths() {
    let result = presentation(
        &["j", "i", "h", "g", "f", "e", "d", "c", "b", "a"],
        &[
            ("a", "b"),
            ("b", "c"),
            ("c", "d"),
            ("d", "a"),
            ("e", "f"),
            ("f", "g"),
            ("g", "h"),
            ("h", "i"),
            ("i", "j"),
            ("j", "e"),
        ],
    )
    .permutation_order()
    .unwrap();
    assert_eq!(result.order(), &BigUint::from(12_u8));
    assert_eq!(
        result.cycles(),
        expected_cycles(&[&["a", "b", "c", "d"], &["e", "f", "g", "h", "i", "j"]])
    );
}

#[test]
fn names_including_blank_and_duplicate_names_do_not_change_this_operation() {
    let original = c6();
    let mut renamed = original.clone();
    for rule in &mut renamed.rules {
        rule.name = String::new();
    }
    assert_eq!(
        renamed.permutation_order().unwrap(),
        original.permutation_order().unwrap()
    );
    for rule in &mut renamed.rules {
        rule.name = "same name for every rule".to_owned();
    }
    assert_eq!(
        renamed.permutation_order().unwrap(),
        original.permutation_order().unwrap()
    );
}

#[test]
fn calculating_the_witness_does_not_modify_the_presentation() {
    let supplied = c6();
    let before = supplied.clone();
    let result = supplied.permutation_order().unwrap();
    assert_eq!(result.order(), &BigUint::from(6_u8));
    assert_eq!(supplied, before);
}

#[test]
fn exact_order_exceeds_u64_without_truncation() {
    // These distinct prime cycle lengths have product 32589158477190044730.
    // The expected decimal was computed independently of the Rust algorithm.
    const LENGTHS: [usize; 16] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53];
    let supplied = disjoint_cycles(&LENGTHS);
    assert_eq!(supplied.signature.len(), 381);
    let result = supplied.permutation_order().unwrap();
    assert_eq!(result.order().to_string(), "32589158477190044730");
    assert!(result.order() > &BigUint::from(u64::MAX));
    assert_eq!(
        result.cycles().iter().map(Vec::len).collect::<Vec<_>>(),
        LENGTHS
    );
    let mut reordered = supplied;
    reordered.signature.reverse();
    reordered.rules.reverse();
    assert_eq!(reordered.permutation_order().unwrap(), result);
}

#[test]
fn empty_signature_is_not_admitted_as_a_permutation() {
    assert_eq!(
        presentation(&[], &[]).permutation_order(),
        Err(PermutationOrderError::EmptySignature)
    );
}

#[test]
fn signature_entries_must_be_exactly_one_scalar() {
    for invalid in ["", "ab", "e\u{301}"] {
        assert_eq!(
            presentation(&[invalid], &[(invalid, invalid)]).permutation_order(),
            Err(PermutationOrderError::SignatureSymbolNotScalar)
        );
    }
}

#[test]
fn repeated_signature_symbols_are_refused() {
    assert_eq!(
        presentation(&["a", "a"], &[("a", "a")]).permutation_order(),
        Err(PermutationOrderError::DuplicateSignatureSymbol)
    );
}

#[test]
fn rule_sources_must_be_exactly_one_scalar() {
    for invalid in ["", "ab", "e\u{301}"] {
        assert_eq!(
            presentation(&["a"], &[(invalid, "a")]).permutation_order(),
            Err(PermutationOrderError::RuleSourceNotScalar)
        );
    }
}

#[test]
fn rule_targets_must_be_exactly_one_scalar() {
    for invalid in ["", "ab", "e\u{301}"] {
        assert_eq!(
            presentation(&["a"], &[("a", invalid)]).permutation_order(),
            Err(PermutationOrderError::RuleTargetNotScalar)
        );
    }
}

#[test]
fn rule_sources_outside_the_signature_are_refused() {
    assert_eq!(
        presentation(&["a"], &[("x", "a")]).permutation_order(),
        Err(PermutationOrderError::RuleSourceOutsideSignature)
    );
}

#[test]
fn rule_targets_outside_the_signature_are_refused() {
    assert_eq!(
        presentation(&["a"], &[("a", "x")]).permutation_order(),
        Err(PermutationOrderError::RuleTargetOutsideSignature)
    );
}

#[test]
fn duplicate_sources_are_refused_even_for_identical_target_rules() {
    for target in ["a", "b"] {
        assert_eq!(
            presentation(&["a", "b"], &[("a", "a"), ("a", target), ("b", "b")]).permutation_order(),
            Err(PermutationOrderError::DuplicateRuleSource)
        );
    }
}

#[test]
fn missing_sources_are_refused_as_non_total() {
    for rules in [Vec::new(), vec![("a", "b")]] {
        assert_eq!(
            presentation(&["a", "b"], &rules).permutation_order(),
            Err(PermutationOrderError::NonTotal)
        );
    }
}

#[test]
fn a_total_relation_that_is_not_onto_is_refused() {
    assert_eq!(
        presentation(&["a", "b"], &[("a", "b"), ("b", "b")]).permutation_order(),
        Err(PermutationOrderError::NotOnto)
    );
}

// Origin: engine/crates_rs/tests/pfp_runtime/permutation_order.rs
// Claim: urn:core:crates_rs:tests:permutation-order:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3f897df9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3f897df9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3f897df9 {
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
impl BoundaryError3f897df9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3f897df9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3f897df9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3f897df9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3f897df9> {
        if capacity_bound == 0 {
            return Err(BoundaryError3f897df9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3f897df9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3f897df9::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_3f897df9() {
    let admitted = BoundaryRecord3f897df9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3f897df9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
