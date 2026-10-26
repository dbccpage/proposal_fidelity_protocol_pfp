import Derivation.IsoCanon

/-!
# The list-reorder bridge: equal components ⇒ isomorphic

`IsoCanon.lean`'s soundness kernel (`iso_of_relabel_eq`) proves that two
regimes whose relabellings coincide *as regimes* (exact lists) are isomorphic,
and notes the gap to key-level soundness: `serialize` sorts `insts`/`rules`/
`reqs` componentwise, so equal canonical keys leave the relabellings equal only
*up to those sorts* -- equal as multisets, hence equal as membership, but not
necessarily as lists.

This module closes exactly that step: two regimes agreeing on `data` and
`forms` and with equal `insts`/`rules`/`reqs` **membership** are isomorphic,
via the **identity** maps (`Iso.of_components`).  `serialize`'s sort makes the
components equal as sorted lists, which gives the membership equality this
consumes; so composed with the kernel it is the missing forward step (a
separate, purely list-combinatorial lemma -- sorted-list equality ⇒ membership
equality -- connects `serialize`'s literal output to the hypothesis here, and
is left to the key-definition unit).

Requirements must be ordered on both sides (as `Regime.wf` gives): the
identity map still sends a requirement `q` to `sortPair (q.1, q.2)`, which is
`q` only when `q` is ordered.

AuthorityEffect: None.  Parked module (not imported by `Derivation.lean`);
axioms within `{propext, Quot.sound}`, verified by hand, not by the root gate.
-/

namespace Derivation
namespace Iso

/-- **The list-reorder bridge.**  Regimes that agree on `data` and `forms` and
whose `insts`/`rules`/`reqs` have equal membership are `Minimality.Iso`, via
the identity maps.  Both sides' requirements must be ordered.  This is the step
the soundness kernel left open: from relabellings-equal-up-to-sort to `Iso`. -/
def of_components (A B : Regime)
    (hdata : A.data = B.data) (hforms : A.forms = B.forms)
    (hInst : ∀ i, i ∈ A.insts ↔ i ∈ B.insts)
    (hRule : ∀ f, f ∈ A.rules ↔ f ∈ B.rules)
    (hReq : ∀ q, q ∈ A.reqs ↔ q ∈ B.reqs)
    (hAord : ∀ q ∈ A.reqs, q.1 ≤ q.2)
    (hBord : ∀ q ∈ B.reqs, q.1 ≤ q.2) : Iso A B where
  dmap := id
  dinv := id
  fmap := id
  finv := id
  dmap_lt := fun d hd => hdata ▸ List.mem_range.mp hd
  dinv_lt := fun d hd => hdata.symm ▸ List.mem_range.mp hd
  dinv_dmap := fun _ _ => rfl
  dmap_dinv := fun _ _ => rfl
  fmap_lt := fun f hf => hforms ▸ List.mem_range.mp hf
  finv_lt := fun f hf => hforms.symm ▸ List.mem_range.mp hf
  finv_fmap := fun _ _ => rfl
  fmap_finv := fun _ _ => rfl
  arity := fun f _ => by
    show B.forms.getD (id f) 0 = A.forms.getD f 0
    rw [id_eq, hforms]
  insts_fwd := fun p hp => by simpa using (hInst p).mp hp
  insts_bwd := fun p hp => by simpa using (hInst p).mpr hp
  rules_fwd := fun f hf => by simpa using (hRule f).mp hf
  rules_bwd := fun f hf => by simpa using (hRule f).mpr hf
  reqs_fwd := fun q hq => by
    show sortPair (id q.1, id q.2) ∈ B.reqs
    simp only [id_eq]
    rw [sortPair_of_le (hAord q hq)]
    exact (hReq q).mp hq
  reqs_bwd := fun q hq => by
    show sortPair (id q.1, id q.2) ∈ A.reqs
    simp only [id_eq]
    rw [sortPair_of_le (hBord q hq)]
    exact (hReq q).mpr hq

end Iso
end Derivation
