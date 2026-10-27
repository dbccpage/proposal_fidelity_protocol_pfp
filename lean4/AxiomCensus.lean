/-
Axiom census for the Symbol Game kernel in this folder.

Run from this folder after `lake build`:

    lake env lean AxiomCensus.lean

For each module root of `lean_lib SymbolGameKernel` it checks every constant
that the compiled environment assigns to that module: theorems, definitions,
instances, generated lemmas and internal auxiliary proofs. It fails if:

- the module declares an `axiom`, used or not; or
- any constant depends on an axiom outside {propext, Classical.choice,
  Quot.sound}, `sorryAx` included.

It prints each non-internal theorem with its axioms. `axiom_report.txt` is
this command's output.

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

open Lean Elab Command in
run_cmd do
  let modules : List Lean.Name := [`PrimitiveDifference, `SLevel, `Sweeper, `TowerZeta,
    `ShadowBoundary, `TypedPacketShadow, `FidelityAdequacy, `LiftPatchSemantics,
    `OperationTreeFold]
  let allowed : List Lean.Name := [`propext, `Classical.choice, `Quot.sound]
  let env ← getEnv
  let mut constants := 0
  let mut theorems := 0
  let mut axiomFree := 0
  let mut seen : List Lean.Name := []
  let mut bad : Array String := #[]
  let mut lines : Array String := #[]
  for m in modules do
    let some idx := env.getModuleIdx? m | throwError "module {m} is not in the environment"
    let mut all : Array Lean.Name := #[]
    for (n, _) in env.constants.map₁.toList do
      if env.getModuleIdxFor? n == some idx then all := all.push n
    all := all.qsort (fun a b => a.toString < b.toString)
    let mut shownHere : Array String := #[]
    for n in all do
      let some ci := env.find? n | throwError "constant {n} vanished"
      constants := constants + 1
      if ci matches .axiomInfo _ then bad := bad.push s!"{m} declares the axiom {n}"
      let axs ← liftCoreM (Lean.collectAxioms n)
      for a in axs do
        if !seen.contains a then seen := seen ++ [a]
        if !allowed.contains a then bad := bad.push s!"{n} depends on {a}"
      if (ci matches .thmInfo _) && !n.isInternal then
        theorems := theorems + 1
        if axs.isEmpty then axiomFree := axiomFree + 1
        let shown := ", ".intercalate (axs.toList.map toString)
        shownHere := shownHere.push s!"  {n}: [{shown}]"
    lines := lines.push s!"{m}: {all.size} constants checked, {shownHere.size} non-internal theorems"
    lines := lines ++ shownHere
  let distinct := ", ".intercalate ((seen.map toString).mergeSort (· ≤ ·))
  lines := lines.push s!"Constants checked: {constants}; non-internal theorems: {theorems}; of those with no axioms: {axiomFree}; distinct axioms over all constants: [{distinct}]"
  logInfo (String.intercalate "\n" lines.toList)
  unless bad.isEmpty do
    throwError "axioms outside the allowed set:\n{String.intercalate "\n" bad.toList}"
