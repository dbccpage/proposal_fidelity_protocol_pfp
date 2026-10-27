import Lake
open Lake DSL

package «authority_gap» where
  version := v!"0.1.0"

@[default_target]
lean_lib «AuthorityGap» where
  srcDir := "."
  roots := #[`AuthorityGap]
