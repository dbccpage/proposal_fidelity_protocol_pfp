import Lake
open Lake DSL

package «pfp_symbol_game_kernel» where
  version := v!"0.1.0"

@[default_target]
lean_lib «SymbolGameKernel» where
  srcDir := "."
  roots := #[
    `PrimitiveDifference,
    `SLevel,
    `Sweeper,
    `TowerZeta,
    `ShadowBoundary,
    `TypedPacketShadow,
    `FidelityAdequacy,
    `LiftPatchSemantics,
    `OperationTreeFold
  ]
