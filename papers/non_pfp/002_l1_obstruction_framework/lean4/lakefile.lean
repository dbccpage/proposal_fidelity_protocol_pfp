import Lake
open Lake DSL

package «l1_obstruction_framework» where
  version := v!"0.1.0"

@[default_target]
lean_lib «L1ObstructionFramework» where
  srcDir := "."
  roots := #[
    `lp_core,
    `lp_cochains,
    `lp_weak_duality,
    `lp_strict_convexity,
    `lp_hodge_helmholtz,
    `lp_general_certificate
  ]
