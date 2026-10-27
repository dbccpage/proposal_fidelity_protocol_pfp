import Lake
open Lake DSL

package «l1_native_cohomology» where
  version := v!"0.1.0"

@[default_target]
lean_lib «L1NativeCohomology» where
  srcDir := "."
  roots := #[
    `l1c_core,
    `l1c_t01_attainment,
    `l1c_t02_quotient_norm,
    `l1c_t03_weak_duality,
    `l1c_t04_complementary_slackness,
    `l1c_t05_cycle_invariant,
    `l1c_t07_bianchi_nilpotency,
    `l1c_general_certificate,
    `l1c_lp_cochains,
    `l1c_lp_duality,
    `l1c_lp_strict_uniqueness,
    `l1c_lp_hodge_decomposition
  ]
