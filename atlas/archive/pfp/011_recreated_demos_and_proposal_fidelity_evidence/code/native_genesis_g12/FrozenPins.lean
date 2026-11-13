import Wrappers

example : ∀ (A B : Derivation.Regime),
  A.data = B.data →
    A.forms = B.forms →
      (∀ (i : Derivation.Inst), i ∈ A.insts ↔ i ∈ B.insts) →
        (∀ (f : Nat), f ∈ A.rules ↔ f ∈ B.rules) →
          (∀ (q : Nat × Nat), q ∈ A.reqs ↔ q ∈ B.reqs) →
            (∀ (q : Nat × Nat), q ∈ A.reqs → q.fst ≤ q.snd) →
              (∀ (q : Nat × Nat), q ∈ B.reqs → q.fst ≤ q.snd) → Nonempty (Derivation.Iso A B) := @G12.Wrappers.Derivation_Iso_of_components

example : ∀ {r s : Derivation.Regime} (h : Derivation.Iso r s), Nonempty (Derivation.Iso s r) := @G12.Wrappers.Derivation_Iso_symm

example : ∀ {r s t : Derivation.Regime} (h : Derivation.Iso r s) (k : Derivation.Iso s t), Nonempty (Derivation.Iso r t) := @G12.Wrappers.Derivation_Iso_trans

example : ∀ {r s : Derivation.Regime} (πr : Derivation.DRen r.data) (φr : Derivation.DRen r.forms.length)
  (πs : Derivation.DRen s.data) (φs : Derivation.DRen s.forms.length),
  (∀ (q : Nat × Nat), q ∈ r.reqs → q.fst ≤ q.snd) →
    (∀ (q : Nat × Nat), q ∈ s.reqs → q.fst ≤ q.snd) →
      Derivation.relabel r πr φr = Derivation.relabel s πs φs → Nonempty (Derivation.Iso r s) := @G12.Wrappers.Derivation_iso_of_relabel_eq

example : ∀ (r : Derivation.Regime) (π : Derivation.DRen r.data) (φ : Derivation.DRen r.forms.length),
  (∀ (q : Nat × Nat), q ∈ r.reqs → q.fst ≤ q.snd) → Nonempty (Derivation.Iso r (Derivation.relabel r π φ)) := @G12.Wrappers.Derivation_relabel_iso

