import Lake
open Lake DSL

package «symbol_game_010» where
  version := v!"0.1.0"

@[default_target]
lean_lib «SymbolGame010» where
  srcDir := "."
  roots := #[`LatticeDecimation]
