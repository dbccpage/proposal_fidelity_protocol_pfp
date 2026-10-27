import os
import subprocess

"""
Generates Rust macro implementations for base contracts.

Running this must reproduce the committed `macros.rs` byte for byte. It did not:
the output was CRLF in an LF-only repository, it was never passed through
rustfmt though GOV-002 invariant 2 requires that, and it did not know about the
`License` associated type that `traits::execution::Engine` requires -- so
regenerating emitted an `Engine` impl that failed to satisfy its own trait.

`test_generated_macros_are_reproducible.py` holds that reproducibility now.
"""

output = []

output.append(
    """#[macro_export]
macro_rules! assert_contract_binding {
    ($ty:ty, $contract:ty) => {{
        let _ = $crate::binding::audit_implementation::<$ty, $contract>().unwrap();
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
"""
)

macros = [
    (
        "impl_lambda",
        "LambdaKind",
        "LambdaOp<<$contract as $crate::binding::BoundContract>::Input, <$contract as $crate::binding::BoundContract>::Output>",
        "apply",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Input) -> Result<<$contract as $crate::binding::BoundContract>::Output, $crate::types::failure_lambda::LambdaFailure>",
        "require_lambda_shape",
        "$crate::descriptors::assert_lambda_laws",
    ),
    (
        "impl_reducer",
        "ReducerKind",
        "ReducerOp<<$contract as $crate::binding::BoundContract>::Input>",
        "apply",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Input) -> Result<<$contract as $crate::binding::BoundContract>::Input, $crate::types::failure_reducer::ReducerFailure>",
        "require_reducer_shape",
        "$crate::descriptors::assert_reducer_laws",
    ),
    (
        "impl_transform",
        "TransformKind",
        "TransformOp<<$contract as $crate::binding::BoundContract>::Input>",
        "apply",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Input) -> Result<<$contract as $crate::binding::BoundContract>::Input, $crate::types::failure_transform::TransformFailure>",
        "require_transform_shape",
        "$crate::descriptors::assert_transform_laws",
    ),
    (
        "impl_meta",
        "MetaKind",
        "MetaRule<<$contract as $crate::binding::BoundContract>::Subject>",
        "evaluate",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Subject) -> Result<Self::Output, Self::Error>",
        "require_meta_shape",
        "$crate::descriptors::assert_meta_laws",
    ),
    (
        "impl_engine",
        "EngineKind",
        "Engine<<$contract as $crate::binding::BoundContract>::Input>",
        "step",
        # `_license` is required: `traits::execution::Engine` declares
        # `type License` and takes it on `step`. It was hand-patched into the
        # generated macros.rs and never taught to this generator, so running
        # the generator emitted an `Engine` impl that did not satisfy its own
        # trait -- the crate stopped compiling and nothing detected it.
        "(&mut self, input: <$contract as $crate::binding::BoundContract>::Input, _license: &Self::License) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error>",
        None,
        "$crate::traits::assert_engine_laws",
    ),
    (
        "impl_pipeline",
        "PipelineKind",
        "Pipeline<<$contract as $crate::binding::BoundContract>::Input>",
        "run",
        "(&mut self, input: <$contract as $crate::binding::BoundContract>::Input) -> Result<(Self::PipelineState, Self::Output, Self::Trace), Self::Error>",
        None,
        None,
    ),
    (
        "impl_runtime",
        "RuntimeKind",
        "Runtime",
        "start",
        "(&mut self, arg: Self::Input) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error>",
        None,
        None,
    ),
    (
        "impl_analysis_unit",
        "AnalysisUnitKind",
        "AnalysisUnit<<$contract as $crate::binding::BoundContract>::Subject>",
        "analyze",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Subject) -> Result<Self::Output, Self::Error>",
        None,
        "$crate::descriptors::assert_validation_laws",
    ),
    (
        "impl_policy_unit",
        "PolicyUnitKind",
        "PolicyUnit<<$contract as $crate::binding::BoundContract>::Subject>",
        "decide",
        "(&self, input: &<$contract as $crate::binding::BoundContract>::Subject) -> Result<Self::Output, Self::Error>",
        None,
        "$crate::traits::assert_policy_laws",
    ),
    (
        "impl_action_executor",
        "ActionExecutorKind",
        "ActionExecutor<<$contract as $crate::binding::BoundContract>::Subject>",
        "execute",
        "(&mut self, decision: &<$contract as $crate::binding::BoundContract>::Subject) -> Result<Self::Output, Self::Error>",
        None,
        "$crate::traits::assert_engine_laws",
    ),
]

for name, kind, op_trait, fn_name, fn_sig, shape_check, strict_law in macros:
    if name == "impl_engine":
        op_trait_full = f"$crate::traits::execution::{op_trait}"
        assoc_types = (
            "type Operator = $ty;\n"
            "            type License = String;\n"
            "            type RuntimeState = <$contract as $crate::binding::BoundContract>::RuntimeState;\n"
            "            type Output = <$contract as $crate::binding::BoundContract>::Output;\n"
            "            type Trace = core_types::trace_artifact::VoidTrace;\n"
            "            type Error = $crate::types::failure_operator::OperatorFailure;"
        )
        closure_args = "|$self:ident, $input:ident|"
    elif name == "impl_pipeline":
        op_trait_full = f"$crate::traits::execution::{op_trait}"
        assoc_types = (
            "type Engine = $ty;\n"
            "            type PipelineState = <$contract as $crate::binding::BoundContract>::RuntimeState;\n"
            "            type Output = <$contract as $crate::binding::BoundContract>::Output;\n"
            "            type Trace = core_types::trace_artifact::VoidTrace;\n"
            "            type Error = $crate::types::failure_operator::OperatorFailure;"
        )
        closure_args = "|$self:ident, $input:ident|"
    elif name == "impl_runtime":
        op_trait_full = "$crate::traits::execution::Runtime<<$contract as $crate::binding::BoundContract>::Input>"
        assoc_types = (
            "type Pipeline = $ty;\n"
            "            type Input = <$contract as $crate::binding::BoundContract>::Input;\n"
            "            type RuntimeState = <$contract as $crate::binding::BoundContract>::RuntimeState;\n"
            "            type Output = <$contract as $crate::binding::BoundContract>::Output;\n"
            "            type Trace = core_types::trace_artifact::VoidTrace;\n"
            "            type Error = $crate::types::failure_operator::OperatorFailure;"
        )
        closure_args = "|$self:ident, $arg:ident|"
    elif name in (
        "impl_meta",
        "impl_analysis_unit",
        "impl_policy_unit",
        "impl_action_executor",
    ):
        op_trait_full = f"$crate::traits::analysis::{op_trait}"
        assoc_types = (
            "type Output = <$contract as $crate::binding::BoundContract>::Output;\n"
            "            type Error = $crate::types::failure_operator::OperatorFailure;"
        )
        if name == "impl_action_executor":
            closure_args = "|$self:ident, $decision:ident|"
        else:
            closure_args = "|$self:ident, $input:ident|"
    else:
        op_trait_full = f"$crate::traits::operators::{op_trait}"
        assoc_types = ""
        closure_args = "|$input:ident|"

    if "self" in closure_args:
        closure_decl = closure_args
        let_self = "let $self = self;"
    else:
        closure_decl = closure_args
        let_self = ""

    sig = fn_sig

    id_impl = f"""
        impl $crate::traits::operators::OperatorIdentity for $ty {{
            fn name(&self) -> &'static str {{
                <$contract as $crate::binding::GeneratedContractImage>::DESCRIPTOR.id()
            }}
        }}"""

    assert_kind = f"""
        const _: () = {{
            fn assert_kind<C: $crate::binding::BoundContract + $crate::kinds::{kind}>() {{}}
            assert_kind::<$contract>();
        }};"""

    shape_call = f", $crate::binding::{shape_check}" if shape_check else ""
    law_call = f", {strict_law}" if strict_law else ""
    witness_call = "$crate::attach_witness_profile!($ty, $contract);" if name in ("impl_lambda", "impl_reducer", "impl_transform", "impl_meta") else ""

    macro_str = f"""#[macro_export]
macro_rules! {name} {{
    (
        type = $ty:ident,
        contract = $contract:ty,
        {fn_name} = {closure_decl} $body:expr
    ) => {{
        $crate::__impl_contract_base!($ty, $contract, $crate::kinds::{kind});
{assert_kind}{id_impl}
        impl {op_trait_full} for $ty where $contract: $crate::binding::BoundContract {{
            {assoc_types}
            fn {fn_name}{sig} {{
                {let_self}
                $body
            }}
        }}

        $crate::attach_contract_laws!($ty, $contract{law_call});
        {witness_call}
        $crate::attach_test_harness!($ty, $contract{shape_call});
    }};
}}
"""
    # Replace any empty lines where witness_call was empty
    macro_str = macro_str.replace("        \n", "")
    output.append(macro_str)

target = os.path.join(os.path.dirname(__file__), "macros.rs")

# newline is forced: on Windows the default translates "\n" to CRLF, and this
# repository is LF-only ("* text eol=lf"). Without it, running the generator
# rewrote every line of its own output and dirtied the tree.
with open(target, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(output))

# GOV-002 invariant 2 requires generated Rust to be "formatted according to
# rustfmt". The generator never did, so its output could not match the
# committed file even when the content agreed -- 13 hunks of pure formatting.
# Formatting here is what makes the output reproducible, and reproducibility is
# what lets a test detect a real divergence.
_fmt = subprocess.run(
    ["rustfmt", "--edition", "2021", target],
    capture_output=True,
    text=True,
)
if _fmt.returncode != 0:
    raise SystemExit(
        "rustfmt failed on the generated macros; refusing to leave unformatted "
        f"output in the tree:\n{_fmt.stderr}"
    )

# rustfmt writes with the platform's line ending, so normalise again after it.
with open(target, "rb") as f:
    _formatted = f.read()
with open(target, "wb") as f:
    f.write(_formatted.replace(b"\r\n", b"\n"))
