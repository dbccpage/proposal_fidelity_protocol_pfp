import Wrappers
open Derivation
theorem G12.Misplaced : Nonempty (Iso R2L R2L) :=
  ⟨isoRefl R2L (by decide)⟩
