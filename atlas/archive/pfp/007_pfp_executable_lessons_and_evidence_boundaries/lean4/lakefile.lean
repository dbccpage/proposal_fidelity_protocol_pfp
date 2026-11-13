import Lake
open Lake DSL

package «companion_007_formal_statements» where
  version := v!"0.1.0"

@[default_target]
lean_lib «Companion007» where
  srcDir := "."
  roots := #[`Expressivity, `GrammarCeiling, `GrammarDepthCeiling]
