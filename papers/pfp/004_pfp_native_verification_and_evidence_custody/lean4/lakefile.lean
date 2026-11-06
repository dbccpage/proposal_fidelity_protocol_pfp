import Lake
open Lake DSL

package «symbol_game_three_layer_sovereignty» where
  version := v!"0.1.0"

@[default_target]
lean_lib «SymbolGame» where
  srcDir := "."
  roots := #[`TotalUnimodularity, `IdentityTypes, `Topology50, `SparseLanding, `SnTower, `SparseLandingGeneral]
