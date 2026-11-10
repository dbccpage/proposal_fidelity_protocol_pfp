/-
  PFP X (Paper 010): a plaquette whose four links are the identity.

  This file records one elementary lemma used as a remark in the paper: if the
  four links around a plaquette are all the identity, the oriented product
  U(e0) U(e1) U(e2)^-1 U(e3)^-1 is the identity. The proof uses only the
  identity law and inv one = one. It justifies skipping such plaquettes as an
  optimization; it says nothing about plaquettes with non-identity links, and
  it is not a flatness test.
-/

namespace SymbolGame010

/-- A group given by its operations and laws, with no library dependency. -/
structure DiscreteGroup (G : Type) where
  mul : G → G → G
  inv : G → G
  one : G
  mul_assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c)
  mul_one : ∀ g, mul g one = g
  one_mul : ∀ g, mul one g = g
  mul_inv : ∀ g, mul g (inv g) = one
  inv_mul : ∀ g, mul (inv g) g = one
  inv_one : inv one = one

/-- Oriented plaquette product: two links traversed forward, two backward. -/
def plaquette_holonomy {G : Type} (grp : DiscreteGroup G) (e0 e1 e2 e3 : G) : G :=
  grp.mul (grp.mul (grp.mul e0 e1) (grp.inv e2)) (grp.inv e3)

/-- Lemma: four identity links give the identity plaquette product. -/
theorem identity_links_give_identity_product {G : Type} (grp : DiscreteGroup G)
    (e0 e1 e2 e3 : G)
    (h0 : e0 = grp.one) (h1 : e1 = grp.one) (h2 : e2 = grp.one) (h3 : e3 = grp.one) :
    plaquette_holonomy grp e0 e1 e2 e3 = grp.one := by
  dsimp [plaquette_holonomy]
  rw [h0, h1, h2, h3]
  rw [grp.inv_one]
  rw [grp.one_mul]
  rw [grp.one_mul]
  rw [grp.one_mul]

end SymbolGame010
