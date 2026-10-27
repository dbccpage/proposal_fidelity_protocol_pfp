
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_2cb9ef18;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_2cb9ef18<T> = std::result::Result<T, BoundaryError_2cb9ef18>;
#[macro_export]
macro_rules! assert_contract_binding {
    ($ty:ty, $contract:ty) => {{
        if let Err(err) = $crate::binding::audit_implementation::<$ty, $contract>() { unreachable!("checked invariant: {:?}", err); }
    }};
}

#[macro_export]
macro_rules! __impl_contract_base {
    ($ty:ident, $contract:ty, $kind:ty) => {
        #[derive(Debug, Clone, Copy, Default)]
        pub struct $ty;

        impl $crate::sealed::Sealed for $ty {}
        impl $kind for $ty {}

        impl $crate::binding::ImplementsContract<$contract> for $ty {}

        $crate::require_contract!($contract);

        const _: () = {
            fn assert_impl<I: $crate::binding::ImplementsContract<$contract>>() {}
            assert_impl::<$ty>();
        };
    };
}

#[macro_export]
macro_rules! attach_contract_laws {
    ($ty:ident, $contract:ty, $assert_fn:path) => {
        const _: () = {
            fn _run() {
                $assert_fn::<$contract>();
            }
        };
    };
    ($ty:ident, $contract:ty) => {};
}

#[macro_export]
macro_rules! attach_witness_profile {
    ($ty:ident, $contract:ty) => {
        $crate::enforcement::generated::emit_contract_witnesses!($ty, $contract);
    };
}

#[macro_export]
macro_rules! attach_test_harness {
    ($ty:ident, $contract:ty, $shape_check:path) => {
        #[cfg(test)]
        mod __witness_obligations {
            use super::*;

            #[test]
            fn contract_binding_is_valid() {
                $crate::assert_contract_binding!($ty, $contract);
            }

            #[test]
            fn shape_is_valid() {
                $shape_check::<$ty, $contract>();
            }
        }
    };
    ($ty:ident, $contract:ty) => {
        #[cfg(test)]
        mod __witness_obligations {
            use super::*;

            #[test]
            fn contract_binding_is_valid() {
                $crate::assert_contract_binding!($ty, $contract);
            }
        }
    };
}

#[macro_export]
macro_rules! impl_lambda {
    (
        type = $ty:ident,
        contract = $contract:ty,
        apply = |$input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::LambdaKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::LambdaKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::operators::LambdaOp<
                <$contract as $crate::binding::BoundContract>::Input,
                <$contract as $crate::binding::BoundContract>::Output,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            fn apply(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Input,
            ) -> Result<
                <$contract as $crate::binding::BoundContract>::Output,
                $crate::types::failure_lambda::LambdaFailure,
            > {
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::descriptors::assert_lambda_laws);
        $crate::attach_witness_profile!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract, $crate::binding::require_lambda_shape);
    };
}

#[macro_export]
macro_rules! impl_reducer {
    (
        type = $ty:ident,
        contract = $contract:ty,
        apply = |$input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::ReducerKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::ReducerKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::operators::ReducerOp<
                <$contract as $crate::binding::BoundContract>::Input,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            fn apply(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Input,
            ) -> Result<
                <$contract as $crate::binding::BoundContract>::Input,
                $crate::types::failure_reducer::ReducerFailure,
            > {
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::descriptors::assert_reducer_laws);
        $crate::attach_witness_profile!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract, $crate::binding::require_reducer_shape);
    };
}

#[macro_export]
macro_rules! impl_transform {
    (
        type = $ty:ident,
        contract = $contract:ty,
        apply = |$input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::TransformKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::TransformKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::operators::TransformOp<
                <$contract as $crate::binding::BoundContract>::Input,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            fn apply(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Input,
            ) -> Result<
                <$contract as $crate::binding::BoundContract>::Input,
                $crate::types::failure_transform::TransformFailure,
            > {
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::descriptors::assert_transform_laws);
        $crate::attach_witness_profile!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract, $crate::binding::require_transform_shape);
    };
}

#[macro_export]
macro_rules! impl_meta {
    (
        type = $ty:ident,
        contract = $contract:ty,
        evaluate = |$self:ident, $input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::MetaKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::MetaKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::analysis::MetaRule<
                <$contract as $crate::binding::BoundContract>::Subject,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn evaluate(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Subject,
            ) -> Result<Self::Output, Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::descriptors::assert_meta_laws);
        $crate::attach_witness_profile!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract, $crate::binding::require_meta_shape);
    };
}

#[macro_export]
macro_rules! impl_engine {
    (
        type = $ty:ident,
        contract = $contract:ty,
        step = |$self:ident, $input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::EngineKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::EngineKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl $crate::traits::execution::Engine<<$contract as $crate::binding::BoundContract>::Input>
            for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Operator = $ty;
            type License = String;
            type RuntimeState = <$contract as $crate::binding::BoundContract>::RuntimeState;
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Trace = core_types::trace_artifact::VoidTrace;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn step(
                &mut self,
                input: <$contract as $crate::binding::BoundContract>::Input,
                _license: &Self::License,
            ) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::traits::assert_engine_laws);
        $crate::attach_test_harness!($ty, $contract);
    };
}

#[macro_export]
macro_rules! impl_pipeline {
    (
        type = $ty:ident,
        contract = $contract:ty,
        run = |$self:ident, $input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::PipelineKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::PipelineKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::execution::Pipeline<
                <$contract as $crate::binding::BoundContract>::Input,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Engine = $ty;
            type PipelineState = <$contract as $crate::binding::BoundContract>::RuntimeState;
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Trace = core_types::trace_artifact::VoidTrace;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn run(
                &mut self,
                input: <$contract as $crate::binding::BoundContract>::Input,
            ) -> Result<(Self::PipelineState, Self::Output, Self::Trace), Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract);
    };
}

#[macro_export]
macro_rules! impl_runtime {
    (
        type = $ty:ident,
        contract = $contract:ty,
        start = |$self:ident, $arg:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::RuntimeKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::RuntimeKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::execution::Runtime<<$contract as $crate::binding::BoundContract>::Input>
            for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Pipeline = $ty;
            type Input = <$contract as $crate::binding::BoundContract>::Input;
            type RuntimeState = <$contract as $crate::binding::BoundContract>::RuntimeState;
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Trace = core_types::trace_artifact::VoidTrace;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn start(
                &mut self,
                arg: Self::Input,
            ) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract);
        $crate::attach_test_harness!($ty, $contract);
    };
}

#[macro_export]
macro_rules! impl_analysis_unit {
    (
        type = $ty:ident,
        contract = $contract:ty,
        analyze = |$self:ident, $input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::AnalysisUnitKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::AnalysisUnitKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::analysis::AnalysisUnit<
                <$contract as $crate::binding::BoundContract>::Subject,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn analyze(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Subject,
            ) -> Result<Self::Output, Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::descriptors::assert_validation_laws);
        $crate::attach_test_harness!($ty, $contract);
    };
}

#[macro_export]
macro_rules! impl_policy_unit {
    (
        type = $ty:ident,
        contract = $contract:ty,
        decide = |$self:ident, $input:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::PolicyUnitKind);

        const _: () = {
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::PolicyUnitKind>() {}
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::analysis::PolicyUnit<
                <$contract as $crate::binding::BoundContract>::Subject,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn decide(
                &self,
                input: &<$contract as $crate::binding::BoundContract>::Subject,
            ) -> Result<Self::Output, Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::traits::assert_policy_laws);
        $crate::attach_test_harness!($ty, $contract);
    };
}

#[macro_export]
macro_rules! impl_action_executor {
    (
        type = $ty:ident,
        contract = $contract:ty,
        execute = |$self:ident, $decision:ident| $body:expr
    ) => {
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::ActionExecutorKind);

        const _: () = {
            fn assert_kind<
                C: $crate::binding::BoundContract + $crate::kinds::ActionExecutorKind,
            >() {
            }
            assert_kind::<$contract>();
        };
        impl $crate::traits::operators::OperatorIdentity for $ty {
            fn name(&self) -> &'static str {
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }
        }
        impl
            $crate::traits::analysis::ActionExecutor<
                <$contract as $crate::binding::BoundContract>::Subject,
            > for $ty
        where
            $contract: $crate::binding::BoundContract,
        {
            type Output = <$contract as $crate::binding::BoundContract>::Output;
            type Error = $crate::types::failure_operator::OperatorFailure;
            fn execute(
                &mut self,
                decision: &<$contract as $crate::binding::BoundContract>::Subject,
            ) -> Result<Self::Output, Self::Error> {
                let $self = self;
                $body
            }
        }

        $crate::attach_contract_laws!($ty, $contract, $crate::traits::assert_engine_laws);
        $crate::attach_test_harness!($ty, $contract);
    };
}

// Origin: engine/crates_rs/core_contracts/src/enforcement_macros.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement-macros:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2cb9ef18 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2cb9ef18` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2cb9ef18 {
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
impl BoundaryError2cb9ef18 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2cb9ef18 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2cb9ef18 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2cb9ef18 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2cb9ef18> {
        if capacity_bound == 0 {
            return Err(BoundaryError2cb9ef18::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2cb9ef18::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2cb9ef18::ExceedsCapacity {
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
mod l4_boundary_tests_2cb9ef18 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2cb9ef18::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2cb9ef18::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2cb9ef18::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2cb9ef18::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2cb9ef18::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2cb9ef18::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2cb9ef18::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
