import Lake
open Lake DSL

package «symbol_game_001» where
  version := v!"0.1.0"

@[default_target]
lean_lib «SymbolGame001» where
  srcDir := "."
  roots := #[`InvolutionLaws, `OddCycleObstruction, `NonAuthority]
