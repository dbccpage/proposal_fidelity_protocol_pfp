/-
Axiom census for the Symbol Game kernel in this folder.

Run from this folder after `lake build`:

    lake env lean AxiomCensus.lean

For each module root of `lean_lib SymbolGameKernel`, it lists every theorem
that the compiled environment assigns to that module, with the axioms the
theorem depends on. It fails if any theorem depends on an axiom outside
{propext, Classical.choice, Quot.sound}, which includes `sorryAx` and any
user-declared axiom. `axiom_report.txt` is this command's output.

This file is an audit script. It declares no definition or theorem.
-/
import Lean
import PrimitiveDifference
import SLevel
import Sweeper
import TowerZeta
import ShadowBoundary
import TypedPacketShadow
import FidelityAdequacy
import LiftPatchSemantics
import OperationTreeFold
import Demo3ProtocolInvariants

open Lean Elab Command in
run_cmd do
  let modules : List Lean.Name := [`PrimitiveDifference, `SLevel, `Sweeper, `TowerZeta,
    `ShadowBoundary, `TypedPacketShadow, `FidelityAdequacy, `LiftPatchSemantics,
    `OperationTreeFold, `Demo3ProtocolInvariants]
  let allowed : List Lean.Name := [`propext, `Classical.choice, `Quot.sound]
  let env ← getEnv
  let mut total := 0
  let mut axiomFree := 0
  let mut seen : List Lean.Name := []
  let mut bad : Array String := #[]
  let mut lines : Array String := #[]
  for m in modules do
    let some idx := env.getModuleIdx? m | throwError "module {m} is not in the environment"
    let mut names : Array Lean.Name := #[]
    for (n, ci) in env.constants.map₁.toList do
      if env.getModuleIdxFor? n == some idx && !n.isInternal then
        if ci matches .thmInfo _ then names := names.push n
    names := names.qsort (fun a b => a.toString < b.toString)
    lines := lines.push s!"{m}: {names.size} theorems"
    for n in names do
      let axs ← liftCoreM (Lean.collectAxioms n)
      total := total + 1
      if axs.isEmpty then axiomFree := axiomFree + 1
      for a in axs do
        if !seen.contains a then seen := seen ++ [a]
        if !allowed.contains a then bad := bad.push s!"{n} depends on {a}"
      let shown := ", ".intercalate (axs.toList.map toString)
      lines := lines.push s!"  {n}: [{shown}]"
  let distinct := ", ".intercalate ((seen.map toString).mergeSort (· ≤ ·))
  lines := lines.push s!"Theorems: {total}; with no axioms: {axiomFree}; distinct axioms: [{distinct}]"
  logInfo (String.intercalate "\n" lines.toList)
  unless bad.isEmpty do
    throwError "axioms outside the allowed set:\n{String.intercalate "\n" bad.toList}"
