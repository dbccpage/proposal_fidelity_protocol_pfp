import Lake
open Lake DSL

package «was_operads» where
  version := v!"0.1.0"

@[default_target]
lean_lib «WasOperads» where
  srcDir := "."
  roots := #[`WasOperads]
