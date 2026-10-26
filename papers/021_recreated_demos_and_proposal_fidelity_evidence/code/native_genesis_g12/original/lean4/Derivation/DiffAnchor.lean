import Derivation.ContactBridge
import Derivation.ObsDescent

/-!
# BR-0: quotient descent for the declared-observation observer

The typed native-difference anchor over the declared observation columns is
**already root-audited** in `ContactBridge`: `ContactBridge.colView` is the
per-column membership signature of an occurrence, and
`ContactBridge.declared_zero_as_view` proves the interface's `ZeroRel` on its
kernel observer is exactly `PrimitivePassage.zeroP`.  `ContactBridge` is the
**canonical owner** of that view and its fidelity; this module does not
re-derive them (an earlier version of this module did, and duplicated them).

What this module adds, parked, is the descent side `ContactBridge` does not
state:

* `colObs cols` -- a *named* handle for the observer
  `ContactBridge.observation_stage_realizes_observer` exhibits existentially,
  so the results below have an object to talk about;
* `colObs_quotient_eq_iff_zeroP` -- **exact** quotient identification, the
  `↔` (composing the generic `ObsDescent.obsQuotient_mk_eq_iff` with the
  ContactBridge fidelity), not just one direction;
* `colObs_deltaConstant` -- the genuinely new content: `ObsDescent.DeltaConstant`
  holds, so the difference map itself descends to the quotient
  (`ObsDescent.deltaDescend`).

`cols` is DECLARED (`zeroP` exists only on the declared observation side).  So
this is conditional on a declared observation, not a claim it is forced.  By
the typed-anchor discipline, nothing here names `applyDelta`, `repairFamily`,
boundary cancellation, or renaming isomorphism.

AuthorityEffect: None.  Parked module (not imported by `Derivation.lean`);
axioms within `{propext, Quot.sound}`, verified by hand, not by the root gate.
-/

open DiffInterface ObsDescent

namespace DiffAnchor

/-- The declared-observation observer: the kernel observer of `ContactBridge`'s
root-audited column view.  A named handle for the witness of
`ContactBridge.observation_stage_realizes_observer`, not a new view. -/
def colObs (cols : List (List Nat)) : DiffObs Nat (List Bool × List Bool) :=
  kernelObs (ContactBridge.colView cols)

/-- Fidelity, re-exported from `ContactBridge`'s root-audited theorem. -/
theorem colObs_zeroRel_iff_zeroP (cols : List (List Nat)) (i j : Nat) :
    ZeroRel (colObs cols) i j ↔ PrimitivePassage.zeroP cols i j = true := by
  unfold colObs
  exact (ContactBridge.declared_zero_as_view cols i j).symm

/-- **Exact quotient identification.**  Quotient points coincide *exactly* on
the declared zero-pairs -- the `↔`, composing the generic quotient exactness
`ObsDescent.obsQuotient_mk_eq_iff` with the fidelity above. -/
theorem colObs_quotient_eq_iff_zeroP (cols : List (List Nat)) (i j : Nat) :
    ObsQuotient.mk (colObs cols) i = ObsQuotient.mk (colObs cols) j
      ↔ PrimitivePassage.zeroP cols i j = true := by
  rw [obsQuotient_mk_eq_iff, colObs_zeroRel_iff_zeroP]

/-- **The `DeltaConstant` test passes** (the new content).  The difference map
is a function of the two column views only, so it is constant on zero-classes
in both arguments and descends to the quotient (`ObsDescent.deltaDescend`). -/
theorem colObs_deltaConstant (cols : List (List Nat)) :
    DeltaConstant (colObs cols) := by
  intro x x' y y' hx hy
  have hx' : ContactBridge.colView cols x = ContactBridge.colView cols x' := hx
  have hy' : ContactBridge.colView cols y = ContactBridge.colView cols y' := hy
  show (ContactBridge.colView cols x, ContactBridge.colView cols y)
     = (ContactBridge.colView cols x', ContactBridge.colView cols y')
  rw [hx', hy']

end DiffAnchor
