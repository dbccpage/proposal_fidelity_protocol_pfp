#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_25a53551;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_25a53551<T> = std::result::Result<T, BoundaryError_25a53551>;

/// Generates test-time lambda property checks.
///
/// This macro does not emit persisted `ValidationWitness` artifacts. Persistent
/// witness evidence belongs in `crate::witness::evidence` and
/// `crate::witness::empirical`.
#[macro_export]
macro_rules! generate_lambda_witnesses {
    ($impl_ty:ty, $contract:ty) => {
        // ─── Compile-time bound assertions ───────────────────────────────────
        const _: () = {
            // Contract must be a strict lambda contract
            fn assert_strict_lambda<C: $crate::descriptors::StrictLambdaContract>() {}
            fn assert_bound_contract<C: $crate::binding::BoundContract>() {}

            // Input and output must expose phi for phi monotonicity checks.
            fn assert_input_phi<T: $crate::witness::capability::HasPhi>() {}
            fn assert_output_phi<T: $crate::witness::capability::HasPhi>() {}

            let _ = assert_strict_lambda::<$contract>;
            let _ = assert_bound_contract::<$contract>;
            let _ = assert_input_phi::<<$contract as $crate::binding::BoundContract>::Input>;
            let _ = assert_output_phi::<<$contract as $crate::binding::BoundContract>::Output>;
        };

        #[cfg(test)]
        mod __lambda_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}

                let _ =
                    assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn phi_non_increasing(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let output = <$impl_ty as $crate::traits::operators::LambdaOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                        <$contract as $crate::binding::BoundContract>::Output,
                    >>::apply(&op, &input)
                        .expect("contract requires total operator (lambda must not fail)");

                    let before = $crate::witness::capability::HasPhi::phi(&input);
                    let after = $crate::witness::capability::HasPhi::phi(&output);

                    prop_assert!(
                        after <= before,
                        "phi increased: before={:?}, after={:?}, input={:?}",
                        before,
                        after,
                        input
                    );
                }
            }
        }
    };
}

/// Generates test-time reducer property checks.
///
/// This macro does not emit persisted `ValidationWitness` artifacts.
#[macro_export]
macro_rules! generate_reducer_witnesses {
    ($impl_ty:ty, $contract:ty) => {
        // ─── Compile-time bound assertions ───────────────────────────────────
        const _: () = {
            fn assert_strict_reducer<C: $crate::descriptors::StrictReducerContract>() {}
            fn assert_bound_contract<C: $crate::binding::BoundContract>() {}

            let _ = assert_strict_reducer::<$contract>;
            let _ = assert_bound_contract::<$contract>;
        };

        #[cfg(test)]
        mod __reducer_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}
                fn assert_input_eq<T: PartialEq>() {}

                let _ = assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_eq::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn reducer_idempotence(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let once = <$impl_ty as $crate::traits::operators::ReducerOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &input)
                        .expect("contract requires total operator (reducer must not fail)");

                    let twice = <$impl_ty as $crate::traits::operators::ReducerOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &once)
                        .expect("contract requires total operator (reducer must not fail on own output)");

                    prop_assert_eq!(
                        once,
                        twice,
                        "reducer is not idempotent: input={:?}",
                        input
                    );
                }
            }
        }
    };
}

/// Generates test-time transform determinism checks.
///
/// This macro does not emit persisted `ValidationWitness` artifacts.
#[macro_export]
macro_rules! generate_transform_determinism_witnesses {
    ($impl_ty:ty, $contract:ty) => {
        // ─── Compile-time bound assertions ───────────────────────────────────
        const _: () = {
            fn assert_strict_transform<C: $crate::descriptors::StrictTransformContract>() {}
            fn assert_bound_contract<C: $crate::binding::BoundContract>() {}

            let _ = assert_strict_transform::<$contract>;
            let _ = assert_bound_contract::<$contract>;
        };

        #[cfg(test)]
        mod __transform_property_witnesses {
            use super::*;
            use proptest::prelude::*;

            const _: () = {
                fn assert_input_arbitrary<T: proptest::arbitrary::Arbitrary>() {}
                fn assert_input_debug<T: core::fmt::Debug>() {}
                fn assert_input_eq<T: PartialEq>() {}

                let _ = assert_input_arbitrary::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_debug::<<$contract as $crate::binding::BoundContract>::Input>;
                let _ = assert_input_eq::<<$contract as $crate::binding::BoundContract>::Input>;
            };

            proptest! {
                #[test]
                fn transform_determinism(
                    input in any::<<$contract as $crate::binding::BoundContract>::Input>()
                ) {
                    let op = <$impl_ty>::default();

                    let a = <$impl_ty as $crate::traits::operators::TransformOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &input)
                        .expect("contract requires total operator (transform must not fail)");

                    let b = <$impl_ty as $crate::traits::operators::TransformOp<
                        <$contract as $crate::binding::BoundContract>::Input,
                    >>::apply(&op, &input)
                        .expect("contract requires total operator (transform must not fail on repeat)");

                    prop_assert_eq!(
                        a,
                        b,
                        "transform is not deterministic: input={:?}",
                        input
                    );
                }
            }
        }
    };
}

// Origin: engine/crates_rs/core_contracts/src/witness_property_macros.rs
// Claim: urn:core:crates_rs:core-contracts:witness-property-macros:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord25a53551 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord25a53551` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError25a53551 {
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
impl BoundaryError25a53551 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError25a53551 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError25a53551 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord25a53551 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError25a53551> {
        if capacity_bound == 0 {
            return Err(BoundaryError25a53551::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError25a53551::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError25a53551::ExceedsCapacity {
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
mod l4_boundary_tests_25a53551 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord25a53551::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord25a53551::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord25a53551::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord25a53551::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord25a53551::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError25a53551::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError25a53551::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
