import Lake
open Lake DSL

package «degree_wise_dsl» where
  version := v!"0.1.0"

@[default_target]
lean_lib «DegreeSeparation» where
  srcDir := "."
  roots := #[
    `DegreeSeparation
  ]
