-- Vendored for Paper 008 from `lean4/Level23SheafDescent.lean` at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf
-- (git blob 37699f2bce800e009735288e47ad138a6f707a0e). Every line after this two-line header is byte-identical to that blob.
/-!
# Level 23: Sheaf and Descent

Formalizes restriction compatibility and a necessary condition for descent:
* Finite cover of a domain U by subdomains {U₁, U₂}.
* Restriction maps of sections res(U, V) : F(U) → F(V) for V ⊆ U.
* Compatibility condition: local sections s₁ ∈ F(U₁), s₂ ∈ F(U₂) agree on overlap U₁ ∩ U₂.
* Sheaf Gluing Soundness: any restriction of a global section is compatible.
* Falsifier Theorem: conflicting overlap restrictions strictly preclude global gluing.
-/

namespace MSSN.Level23

/-- A subdomain identifier in a finite topological space or site. -/
structure Subdomain where
  id : Nat
  deriving DecidableEq, Repr

/-- Inclusions V ⊆ U between subdomains. -/
def Inclusion (V U : Subdomain) : Prop :=
  V.id ≤ U.id

/-- A local section of a presheaf F over subdomain U assigning values in α to indices. -/
structure Section (U : Subdomain) (α : Type) where
  eval : Nat → α

/-- Two sections are extensionally equal if they produce the same evaluation on all points. -/
def SectionEq {U : Subdomain} {α : Type} (s₁ s₂ : Section U α) : Prop :=
  ∀ x, s₁.eval x = s₂.eval x

/-- Restriction map res : F(U) → F(V) along inclusion V ⊆ U. -/
def restrict {U V : Subdomain} (_inc : Inclusion V U) (s : Section U α) : Section V α :=
  ⟨s.eval⟩

/-- Binary cover of U by U₁ and U₂ with formal overlap U₁₂ = U₁ ∩ U₂. -/
structure BinaryCover (U U₁ U₂ U₁₂ : Subdomain) where
  inc1 : Inclusion U₁ U
  inc2 : Inclusion U₂ U
  inc12_1 : Inclusion U₁₂ U₁
  inc12_2 : Inclusion U₁₂ U₂

/-- Compatibility condition: local sections agree on the overlap U₁₂. -/
def IsCompatible {U U₁ U₂ U₁₂ : Subdomain} {α : Type}
    (cov : BinaryCover U U₁ U₂ U₁₂)
    (s₁ : Section U₁ α) (s₂ : Section U₂ α) : Prop :=
  SectionEq (restrict cov.inc12_1 s₁) (restrict cov.inc12_2 s₂)

/-- Amalgamation property: a global section restricts to given local sections. -/
def IsAmalgamation {U U₁ U₂ U₁₂ : Subdomain} {α : Type}
    (cov : BinaryCover U U₁ U₂ U₁₂)
    (s : Section U α) (s₁ : Section U₁ α) (s₂ : Section U₂ α) : Prop :=
  SectionEq (restrict cov.inc1 s) s₁ ∧ SectionEq (restrict cov.inc2 s) s₂

/-- Sheaf Gluing Soundness:
    Any global section s induces mutually compatible local restrictions s₁ and s₂. -/
theorem restriction_is_compatible {U U₁ U₂ U₁₂ : Subdomain} {α : Type}
    (cov : BinaryCover U U₁ U₂ U₁₂)
    (s : Section U α) :
    IsCompatible cov (restrict cov.inc1 s) (restrict cov.inc2 s) := by
  intro x
  rfl

/-- Falsifier Theorem (No-Descent on Disagreement):
    If local sections s₁ and s₂ disagree on the overlap U₁₂, then NO global section
    can exist that simultaneously restricts to both s₁ and s₂. -/
theorem descent_refusal_on_overlap_conflict {U U₁ U₂ U₁₂ : Subdomain} {α : Type}
    (cov : BinaryCover U U₁ U₂ U₁₂)
    (s₁ : Section U₁ α) (s₂ : Section U₂ α)
    (hConflict : ¬ IsCompatible cov s₁ s₂) :
    ¬ ∃ (s : Section U α), IsAmalgamation cov s s₁ s₂ := by
  intro ⟨s, ⟨h1, h2⟩⟩
  apply hConflict
  intro x
  have hS1 := h1 x
  have hS2 := h2 x
  unfold restrict SectionEq at *
  rw [← hS1, ← hS2]

#print axioms restriction_is_compatible
#print axioms descent_refusal_on_overlap_conflict

end MSSN.Level23
