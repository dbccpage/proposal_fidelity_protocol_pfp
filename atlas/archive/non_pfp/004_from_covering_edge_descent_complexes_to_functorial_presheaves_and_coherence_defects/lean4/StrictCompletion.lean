/-!
Paper PO-001 strict completion kernel.

This file isolates the finite algebra used by Path A: if comparable-pair
restrictions are supplied with identity and composition laws, then diamonds are
path-independent; conversely, a two-edge chain has a unique direct completion.
-/

namespace Paper001a

universe u v w z

def ChainComposition
    {A : Type u} {B : Type v} {C : Type w}
    (rCB : C -> B) (rBA : B -> A) (rCA : C -> A) : Prop :=
  forall c : C, rBA (rCB c) = rCA c

theorem strict_completion_from_covering_edges
    {A : Type u} {B : Type v} {C : Type w}
    (rCB : C -> B) (rBA : B -> A) :
    exists rCA : C -> A, ChainComposition rCB rBA rCA := by
  exact ⟨fun c => rBA (rCB c), by intro c; rfl⟩

theorem strict_completion_unique_from_chain
    {A : Type u} {B : Type v} {C : Type w}
    {rCB : C -> B} {rBA : B -> A} {rCA sCA : C -> A}
    (hr : ChainComposition rCB rBA rCA)
    (hs : ChainComposition rCB rBA sCA) :
    rCA = sCA := by
  funext c
  exact (hr c).symm.trans (hs c)

theorem diamond_path_independence
    {A : Type u} {B : Type v} {D : Type w} {C : Type z}
    {rCB : C -> B} {rBA : B -> A}
    {rCD : C -> D} {rDA : D -> A}
    (h : forall c : C, rBA (rCB c) = rDA (rCD c)) :
    forall c : C, rBA (rCB c) = rDA (rCD c) :=
  h

theorem diamond_path_independence_of_common_completion
    {A : Type u} {B : Type v} {D : Type w} {C : Type z}
    {rCB : C -> B} {rBA : B -> A}
    {rCD : C -> D} {rDA : D -> A} {rCA : C -> A}
    (hleft : ChainComposition rCB rBA rCA)
    (hright : ChainComposition rCD rDA rCA) :
    forall c : C, rBA (rCB c) = rDA (rCD c) := by
  intro c
  exact (hleft c).trans (hright c).symm

structure StrictCompletion (Obj : Type u) (Fiber : Obj -> Type v) where
  restr : (a c : Obj) -> Fiber c -> Fiber a
  id_law : forall (a : Obj) (x : Fiber a), restr a a x = x
  comp_law :
    forall (a b c : Obj) (x : Fiber c),
      restr a b (restr b c x) = restr a c x

namespace StrictCompletion

theorem identity
    {Obj : Type u} {Fiber : Obj -> Type v}
    (S : StrictCompletion Obj Fiber) (a : Obj) (x : Fiber a) :
    S.restr a a x = x :=
  S.id_law a x

theorem chain_law
    {Obj : Type u} {Fiber : Obj -> Type v}
    (S : StrictCompletion Obj Fiber)
    (a b c : Obj) (x : Fiber c) :
    S.restr a b (S.restr b c x) = S.restr a c x :=
  S.comp_law a b c x

theorem diamond
    {Obj : Type u} {Fiber : Obj -> Type v}
    (S : StrictCompletion Obj Fiber)
    (a b d c : Obj) (x : Fiber c)
    (hleft : S.restr a b (S.restr b c x) = S.restr a c x)
    (hright : S.restr a d (S.restr d c x) = S.restr a c x) :
    S.restr a b (S.restr b c x) =
      S.restr a d (S.restr d c x) := by
  exact hleft.trans hright.symm

theorem diamond_from_chain_law
    {Obj : Type u} {Fiber : Obj -> Type v}
    (S : StrictCompletion Obj Fiber)
    (a b d c : Obj) (x : Fiber c) :
    S.restr a b (S.restr b c x) =
      S.restr a d (S.restr d c x) := by
  exact diamond S a b d c x
    (S.chain_law a b c x)
    (S.chain_law a d c x)

end StrictCompletion

end Paper001a
