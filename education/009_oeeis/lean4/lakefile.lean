import Lake
open Lake DSL

package «epistemic_immune_system» where
  version := v!"0.1.0"

@[default_target]
lean_lib «EpistemicImmuneSystem» where
  srcDir := "."
  roots := #[`EpistemicImmuneSystem]
