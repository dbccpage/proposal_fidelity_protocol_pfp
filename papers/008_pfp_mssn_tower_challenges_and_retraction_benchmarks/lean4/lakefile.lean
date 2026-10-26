import Lake
open Lake DSL

package «pfp_008» where
  version := v!"0.1.0"

@[default_target]
lean_lib «Pfp008» where
  srcDir := "."
  roots := #[`ExactRat, `FlowCertificate, `Level16IndObject, `Level21DiscreteRegge,
    `Level22FibredDependentContexts, `Level23SheafDescent]
