import Lake
open Lake DSL

package «paper_009_review_protocol» where
  version := v!"0.1.0"

@[default_target]
lean_lib «Paper009» where
  srcDir := "."
  roots := #[`SLevel, `RuntimeLimits, `TriggerNotLicense, `Level15AuthorityCalculus]
