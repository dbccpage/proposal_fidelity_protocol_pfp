import Wrappers

open Derivation

namespace G12.Instances

def identity (n : Nat) : DRen n where
  f := id
  g := id
  fg := fun _ => rfl
  gf := fun _ => rfl
  fbound := fun _ h => h
  gbound := fun _ h => h

theorem ordered : ∀ q ∈ R2L.reqs, q.1 ≤ q.2 := by decide

theorem of_components : Nonempty (Iso R2L R2L) :=
  G12.Wrappers.Derivation_Iso_of_components R2L R2L rfl rfl
    (fun _ => Iff.rfl) (fun _ => Iff.rfl) (fun _ => Iff.rfl) (by decide) (by decide)

theorem symm : Nonempty (Iso R2L R2L) :=
  G12.Wrappers.Derivation_Iso_symm (isoRefl R2L (by decide))

theorem trans : Nonempty (Iso R2L R2L) :=
  G12.Wrappers.Derivation_Iso_trans (isoRefl R2L (by decide)) (isoRefl R2L (by decide))

theorem iso_of_relabel_eq : Nonempty (Iso R2L R2L) :=
  G12.Wrappers.Derivation_iso_of_relabel_eq
    (identity 2) (identity 0) (identity 2) (identity 0) (by decide) (by decide) rfl

theorem relabel_iso : Nonempty (Iso R2L (relabel R2L (identity 2) (identity 0))) :=
  G12.Wrappers.Derivation_relabel_iso R2L (identity 2) (identity 0) (by decide)

end G12.Instances
