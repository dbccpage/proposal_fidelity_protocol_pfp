import Lake

open Lake DSL

package «po001» where
  version := v!"2.0.0"

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @
    "56a005855ea17e0b0958f73ec801ae140b0a1679"

@[default_target]
lean_lib «Po001» where
  srcDir := "."
  roots := #[
    `StrictCompletion,
    `PrimitiveDifference,
    `PrimitiveDifferenceLggr,
    `CurvatureCochain,
    `CohomologyClass,
    `CurvedDerivation,
    `AllDegreeCurvature,
    `ConcreteIncidence,
    `HeterogeneousIncidence,
    `TransportIdentities,
    `FlatLossAndCurvature,
    `CurvedDerivationStandalone,
    `CODAWitnessStandalone,
    `PrimeTriadRouterStandalone,
    `ReggeBianchiStandalone,
    `SheafContextualityStandalone,
    `Core,
    `AxiomAudit,
    `Census,
  ]
