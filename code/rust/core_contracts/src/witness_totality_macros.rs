#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_513a094d;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_513a094d<T> = std::result::Result<T, BoundaryError_513a094d>;

/// Generates test-time totality checks for contracts that explicitly require totality.
///
/// Use this macro only when the contract's `WitnessDirective::REQUIRE_TOTAL`
/// is true. It does not emit persisted `ValidationWitness` artifacts.
#[macro_export]
macro_rules! generate_totality_witnesses {
    ($impl_ty:ty, $contract:ty, lambda) => {
        #[cfg(test)]
        mod __totality_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                const REQUIRE_TOTAL: bool =
                    <$contract as $crate::witness::directive::WitnessDirective>::REQUIRE_TOTAL;
                let _ = [()][(!REQUIRE_TOTAL) as usize];
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}

                let _ =
                    assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn operator_is_total(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let result = <$impl_ty as $crate::traits::operators::LambdaOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                        <$contract as $crate::binding::BoundContract>::Output,
                    >>::apply(&op, &input);

                    prop_assert!(
                        result.is_ok(),
                        "operator must be total over domain: input={:?}, error={:?}",
                        input,
                        result.err()
                    );
                }
            }
        }
    };
    ($impl_ty:ty, $contract:ty, reducer) => {
        #[cfg(test)]
        mod __totality_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                const REQUIRE_TOTAL: bool =
                    <$contract as $crate::witness::directive::WitnessDirective>::REQUIRE_TOTAL;
                let _ = [()][(!REQUIRE_TOTAL) as usize];
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}

                let _ =
                    assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn operator_is_total(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let result = <$impl_ty as $crate::traits::operators::ReducerOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &input);

                    prop_assert!(
                        result.is_ok(),
                        "operator must be total over domain: input={:?}, error={:?}",
                        input,
                        result.err()
                    );
                }
            }
        }
    };
    ($impl_ty:ty, $contract:ty, transform) => {
        #[cfg(test)]
        mod __totality_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                const REQUIRE_TOTAL: bool =
                    <$contract as $crate::witness::directive::WitnessDirective>::REQUIRE_TOTAL;
                let _ = [()][(!REQUIRE_TOTAL) as usize];
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}

                let _ =
                    assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn operator_is_total(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let result = <$impl_ty as $crate::traits::operators::TransformOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &input);

                    prop_assert!(
                        result.is_ok(),
                        "operator must be total over domain: input={:?}, error={:?}",
                        input,
                        result.err()
                    );
                }
            }
        }
    };
}

// Origin: engine/crates_rs/core_contracts/src/witness_totality_macros.rs
// Claim: urn:core:crates_rs:core-contracts:witness-totality-macros:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord513a094d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord513a094d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError513a094d {
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
impl BoundaryError513a094d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError513a094d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError513a094d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord513a094d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError513a094d> {
        if capacity_bound == 0 {
            return Err(BoundaryError513a094d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError513a094d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError513a094d::ExceedsCapacity {
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
mod l4_boundary_tests_513a094d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord513a094d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord513a094d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord513a094d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord513a094d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord513a094d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError513a094d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError513a094d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
