import Derivation.Basic
import Derivation.CountTransport

/-!
# Form renaming (P1 of the CL-ISO-SOUND scope)

Data renaming (`renameRegime`, `Derivation/CountTransport.lean`) relabels
datum indices inside instance argument tuples and leaves form indices
alone: `mapInst f (i.1, i.2) = (i.1, i.2.map f)`.  A full regime
isomorphism also permutes the **form** indices, arity-preserving.  That
half was never exercised.  This module builds its record level: the form
action on a regime, its inverse within the fixed-form-length fibre, and
arity preservation -- mirroring the data-side idioms.  Transporting `wf`,
contexts, derivability, collapse, and transitions under form renaming is
the remaining P1 step.  An earlier version of this line added that "full
regime isomorphism" stays future work until those land; `IsoCanon.lean` has
since proved the combined action a `Minimality.Iso` (`relabel_iso`) -- on
regimes with ordered requirement pairs (as `Regime.wf` gives), and without
those transports -- so what remains future work is the transports, not the
isomorphism connection itself.

A form renaming is a bounded index bijection `DRen m` with
`m = r.forms.length` -- a pair of maps `f, g` each inverting the other
(not necessarily a self-inverse), the same structure the data side uses,
reused so form and datum renamings share one bijection type.

AuthorityEffect: None.  This is new object-level structure, not a claim.
Nothing here is wired into the sealed theorem set; it is a parked module,
elaborated by the per-module CI census (and `lake build
Derivation.FormRenaming`) but not by the default `lake build` target, and
outside the paper's cited axiom inventory.  Its axioms are verified here by
hand, not preserved by the root axiom gate.
-/

namespace Derivation

/-- Permute a form-arity list by an index map.  Position `j` of the
result holds the arity of the form that maps *to* `j` under the
renaming, i.e. old position `g j`.  With `g` the inverse of the acting
map `f`, this gives arity preservation at `f i` below. -/
def permForms (g : Nat → Nat) (forms : List Nat) : List Nat :=
  (List.range forms.length).map (fun j => forms.getD (g j) 0)

@[simp] theorem permForms_length (g : Nat → Nat) (forms : List Nat) :
    (permForms g forms).length = forms.length := by
  simp [permForms]

/-- The defining property: reading position `j` of the permuted list is
reading position `g j` of the original.  Stated only for `j` in range:
out of range the left side is the default, but the right,
`forms.getD (g j) 0`, need not be -- `g` may send an out-of-range `j`
back into range -- which is why `hj` is required. -/
theorem permForms_getD (g : Nat → Nat) (forms : List Nat) {j : Nat}
    (hj : j < forms.length) :
    (permForms g forms).getD j 0 = forms.getD (g j) 0 := by
  unfold permForms
  rw [List.getD_eq_getElem?_getD, List.getElem?_map]
  have hrange : (List.range forms.length)[j]? = some j := by
    simp [hj]
  rw [hrange]
  rfl

/-- Relabel the form index of an instance, leaving its argument tuple. -/
def mapInstForm (φ : Nat → Nat) (i : Inst) : Inst := (φ i.1, i.2)

/-- The form action on a whole regime: forms permuted, instance form
indices and rule form indices relabelled, data and requirements
untouched (they carry no form index). -/
def renameForms (φ g : Nat → Nat) (r : Regime) : Regime :=
  { r with
    forms := permForms g r.forms
    insts := r.insts.map (mapInstForm φ)
    rules := r.rules.map φ }

@[simp] theorem renameForms_data (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).data = r.data := rfl

@[simp] theorem renameForms_reqs (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).reqs = r.reqs := rfl

@[simp] theorem renameForms_forms_length (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).forms.length = r.forms.length := by
  simp [renameForms]

/-- **Arity preservation.**  A form at index `i` keeps its arity at its
new index `φ i`, provided `φ i` lands in range and `g` inverts `φ` on
`i`.  This is the property a form renaming must have to be an
isomorphism: it may shuffle form indices but never changes any form's
arity. -/
theorem renameForms_arity (φ g : Nat → Nat) (r : Regime) {i : Nat}
    (hbound : φ i < r.forms.length) (hgf : g (φ i) = i) :
    (renameForms φ g r).forms.getD (φ i) 0 = r.forms.getD i 0 := by
  show (permForms g r.forms).getD (φ i) 0 = r.forms.getD i 0
  rw [permForms_getD g r.forms hbound, hgf]

/-- Field-wise extensionality for `Regime` (it derives `DecidableEq` but
carries no `@[ext]`; this supplies the one used below without touching
the sealed `Basic`). -/
theorem Regime.ext' {r s : Regime} (hd : r.data = s.data)
    (hf : r.forms = s.forms) (hi : r.insts = s.insts)
    (hru : r.rules = s.rules) (hq : r.reqs = s.reqs) : r = s := by
  cases r; cases s; simp_all

/-- Mapping `mapInstForm` by `φ` then by `g` is the identity on an
instance whenever `g` inverts `φ` on that instance's form index. -/
theorem mapInstForm_gf (φ g : Nat → Nat) (i : Inst) (h : g (φ i.1) = i.1) :
    mapInstForm g (mapInstForm φ i) = i := by
  show (g (φ i.1), i.2) = i
  rw [h]

/-- The form action, undone.  A form renaming `σ : DRen r.forms.length`
acting by `σ.f` is inverted by acting by `σ.g`: `renameForms σ.g σ.f`
composed after `renameForms σ.f σ.g` is the identity on `r`.  So on the
fibre of regimes sharing this form-arity length the record transform has a
two-sided inverse -- a bijection at the record level, within that fibre.
It is *not* yet an automorphism of unqualified `Regime`, nor a transport
of `wf`, contexts, derivability, collapse, or transitions; those are the
remaining P1 steps.  The data-side counterpart is `renameRegime`'s
inverse-pair lemma. -/
theorem renameForms_gf (r : Regime) (σ : DRen r.forms.length) :
    renameForms σ.g σ.f (renameForms σ.f σ.g r) = r := by
  have hforms : permForms σ.f (permForms σ.g r.forms) = r.forms := by
    apply List.ext_getElem
    · simp
    · intro j h1 _
      have hj : j < r.forms.length := by simpa using h1
      have e1 : (permForms σ.f (permForms σ.g r.forms))[j]
          = (permForms σ.f (permForms σ.g r.forms)).getD j 0 := by
        rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem h1]; rfl
      have e2 : r.forms[j] = r.forms.getD j 0 := by
        rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hj]; rfl
      rw [e1, e2]
      have hlen : (permForms σ.g r.forms).length = r.forms.length := by simp
      rw [permForms_getD σ.f (permForms σ.g r.forms) (by rw [hlen]; exact hj)]
      rw [permForms_getD σ.g r.forms (σ.fbound j hj), σ.fg]
  have hinsts : (r.insts.map (mapInstForm σ.f)).map (mapInstForm σ.g) = r.insts := by
    rw [List.map_map]
    have hid : (mapInstForm σ.g ∘ mapInstForm σ.f) = id :=
      funext fun i => mapInstForm_gf σ.f σ.g i (σ.fg i.1)
    rw [hid, List.map_id]
  have hrules : (r.rules.map σ.f).map σ.g = r.rules := by
    rw [List.map_map]
    have hid : (σ.g ∘ σ.f) = id := funext σ.fg
    rw [hid, List.map_id]
  refine Regime.ext' rfl hforms hinsts hrules rfl

end Derivation
