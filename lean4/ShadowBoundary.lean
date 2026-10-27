import PrimitiveDifference
import TowerZeta
/-!
Generic finite-shadow boundary for the S(n) / Symbol Game / packetization paper.

This file extracts the common obstruction behind packet-shape forgetfulness,
LGGR dashboards, and tower-zeta shadows: if a finite shadow identifies two
worlds whose target value differs, no decoder from that shadow can recover the
target for all worlds.
-/

namespace SnSymbolGameAndPackets

def shadowPrimitiveDifference
    {World Shadow : Type}
    (shadow : World → Shadow) : OmegaCore.PrimitiveDifference World Prop where
  δ := fun x y => shadow x = shadow y
  Zero := fun p => p
  zero_refl := by
    intro x
    rfl
  zero_symm := by
    intro x y hxy
    exact hxy.symm
  zero_trans := by
    intro x y z hxy hyz
    exact Eq.trans hxy hyz

def ShadowFiberInvariant
    {World Shadow Value : Type}
    (shadow : World → Shadow) (value : World → Value) : Prop :=
  ∀ x y : World, shadow x = shadow y → value x = value y

theorem shadow_value_descends_iff_fiber_invariant
    {World Shadow Value : Type}
    (shadow : World → Shadow) (value : World → Value) :
    (∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) = value world)
      ↔ ShadowFiberInvariant shadow value := by
  exact OmegaCore.PrimitiveDifference.invariantFactor_exists_iff_invariantCongruent
    (shadowPrimitiveDifference shadow) value

theorem no_factor_through_shadow_of_collision
    {World Shadow Value : Type}
    (shadow : World → Shadow) (value : World → Value)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b) :
    ¬ ∃ F : Shadow → Value, ∀ world : World, F (shadow world) = value world := by
  intro h
  rcases h with ⟨F, hF⟩
  have hA := hF a
  have hB := hF b
  have hSameShadowValue : F (shadow a) = F (shadow b) :=
    congrArg F hShadow
  have hSameValue : value a = value b :=
    Eq.trans hA.symm (Eq.trans hSameShadowValue hB)
  exact hValue hSameValue

theorem bridge_factorization_implies_fiber_invariant
    {World Bridge Value : Type}
    (bridge : World → Bridge) (value : World → Value)
    (hFactor : ∃ F : Bridge → Value,
      ∀ world : World, F (bridge world) = value world) :
    ShadowFiberInvariant bridge value := by
  intro x y hBridge
  rcases hFactor with ⟨F, hF⟩
  have hSameBridgeValue : F (bridge x) = F (bridge y) :=
    congrArg F hBridge
  exact Eq.trans (hF x).symm (Eq.trans hSameBridgeValue (hF y))

theorem bridge_factorization_descends_to_bridge_quotient
    {World Bridge Value : Type}
    (bridge : World → Bridge) (value : World → Value)
    (hFactor : ∃ F : Bridge → Value,
      ∀ world : World, F (bridge world) = value world) :
    ∃ F : (shadowPrimitiveDifference bridge).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference bridge) world) = value world := by
  have hInvariant :
      ShadowFiberInvariant bridge value :=
    bridge_factorization_implies_fiber_invariant bridge value hFactor
  exact (shadow_value_descends_iff_fiber_invariant bridge value).2 hInvariant

theorem coarsened_shadow_invariant_lifts_to_refinement
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hInvariant :
      ShadowFiberInvariant
        (fun world => coarsen (fineShadow world)) value) :
    ShadowFiberInvariant fineShadow value := by
  intro x y hFine
  exact hInvariant x y (congrArg coarsen hFine)

theorem coarsened_factor_lifts_to_refinement
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hFactor : ∃ F : CoarseShadow → Value,
      ∀ world : World, F (coarsen (fineShadow world)) = value world) :
    ∃ G : FineShadow → Value,
      ∀ world : World, G (fineShadow world) = value world := by
  rcases hFactor with ⟨F, hF⟩
  exact ⟨fun fineValue => F (coarsen fineValue), by intro world; exact hF world⟩

theorem coarsened_quotient_descent_lifts_to_refinement
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hDescends :
      ∃ F :
          (shadowPrimitiveDifference
            (fun world => coarsen (fineShadow world))).ResidualQuotient → Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference
                (fun world => coarsen (fineShadow world))) world) =
            value world) :
    ∃ G : (shadowPrimitiveDifference fineShadow).ResidualQuotient → Value,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference fineShadow) world) = value world := by
  have hCoarseInvariant :
      ShadowFiberInvariant
        (fun world => coarsen (fineShadow world)) value :=
    (shadow_value_descends_iff_fiber_invariant
      (fun world => coarsen (fineShadow world)) value).1 hDescends
  have hFineInvariant :
      ShadowFiberInvariant fineShadow value :=
    coarsened_shadow_invariant_lifts_to_refinement
      fineShadow coarsen value hCoarseInvariant
  exact (shadow_value_descends_iff_fiber_invariant fineShadow value).2
    hFineInvariant

theorem no_coarsened_invariant_if_no_refinement_invariant
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hNoFine : ¬ ShadowFiberInvariant fineShadow value) :
    ¬ ShadowFiberInvariant
        (fun world => coarsen (fineShadow world)) value := by
  intro hCoarseInvariant
  exact hNoFine
    (coarsened_shadow_invariant_lifts_to_refinement
      fineShadow coarsen value hCoarseInvariant)

theorem no_coarsened_factor_if_no_refinement_factor
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hNoFine : ¬ ∃ G : FineShadow → Value,
      ∀ world : World, G (fineShadow world) = value world) :
    ¬ ∃ F : CoarseShadow → Value,
      ∀ world : World, F (coarsen (fineShadow world)) = value world := by
  intro hCoarseFactor
  exact hNoFine
    (coarsened_factor_lifts_to_refinement
      fineShadow coarsen value hCoarseFactor)

theorem no_coarsened_quotient_descent_if_no_refinement_quotient_descent
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (hNoFine :
      ¬ ∃ G : (shadowPrimitiveDifference fineShadow).ResidualQuotient → Value,
        ∀ world : World,
          G (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference fineShadow) world) = value world) :
    ¬ ∃ F :
        (shadowPrimitiveDifference
          (fun world => coarsen (fineShadow world))).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference
              (fun world => coarsen (fineShadow world))) world) = value world := by
  intro hCoarseDescent
  exact hNoFine
    (coarsened_quotient_descent_lifts_to_refinement
      fineShadow coarsen value hCoarseDescent)

theorem fiber_equivalent_shadow_invariant_iff
    {World ShadowA ShadowB Value : Type}
    (shadowA : World → ShadowA) (shadowB : World → ShadowB)
    (value : World → Value)
    (hFibers : ∀ x y : World,
      shadowA x = shadowA y ↔ shadowB x = shadowB y) :
    ShadowFiberInvariant shadowA value ↔
      ShadowFiberInvariant shadowB value := by
  constructor
  · intro hA x y hB
    exact hA x y ((hFibers x y).2 hB)
  · intro hB x y hA
    exact hB x y ((hFibers x y).1 hA)

theorem mutually_decodable_factorization_iff
    {World ShadowA ShadowB Value : Type}
    (shadowA : World → ShadowA) (shadowB : World → ShadowB)
    (value : World → Value)
    (toA : ShadowB → ShadowA) (toB : ShadowA → ShadowB)
    (hAfromB : ∀ world : World, shadowA world = toA (shadowB world))
    (hBfromA : ∀ world : World, shadowB world = toB (shadowA world)) :
    (∃ F : ShadowA → Value,
      ∀ world : World, F (shadowA world) = value world) ↔
    (∃ G : ShadowB → Value,
      ∀ world : World, G (shadowB world) = value world) := by
  constructor
  · intro hFactorA
    rcases hFactorA with ⟨F, hF⟩
    exact ⟨fun b => F (toA b), by
      intro world
      change F (toA (shadowB world)) = value world
      rw [← hAfromB world]
      exact hF world⟩
  · intro hFactorB
    rcases hFactorB with ⟨G, hG⟩
    exact ⟨fun a => G (toB a), by
      intro world
      change G (toB (shadowA world)) = value world
      rw [← hBfromA world]
      exact hG world⟩

theorem fiber_equivalent_quotient_descent_iff
    {World ShadowA ShadowB Value : Type}
    (shadowA : World → ShadowA) (shadowB : World → ShadowB)
    (value : World → Value)
    (hFibers : ∀ x y : World,
      shadowA x = shadowA y ↔ shadowB x = shadowB y) :
    (∃ F : (shadowPrimitiveDifference shadowA).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadowA) world) = value world) ↔
    (∃ G : (shadowPrimitiveDifference shadowB).ResidualQuotient → Value,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadowB) world) = value world) := by
  have hInvariantIff :=
    fiber_equivalent_shadow_invariant_iff shadowA shadowB value hFibers
  constructor
  · intro hDescendsA
    exact (shadow_value_descends_iff_fiber_invariant shadowB value).2
      (hInvariantIff.1
        ((shadow_value_descends_iff_fiber_invariant shadowA value).1 hDescendsA))
  · intro hDescendsB
    exact (shadow_value_descends_iff_fiber_invariant shadowA value).2
      (hInvariantIff.2
        ((shadow_value_descends_iff_fiber_invariant shadowB value).1 hDescendsB))

theorem mutually_decodable_no_factorization_iff
    {World ShadowA ShadowB Value : Type}
    (shadowA : World → ShadowA) (shadowB : World → ShadowB)
    (value : World → Value)
    (toA : ShadowB → ShadowA) (toB : ShadowA → ShadowB)
    (hAfromB : ∀ world : World, shadowA world = toA (shadowB world))
    (hBfromA : ∀ world : World, shadowB world = toB (shadowA world)) :
    (¬ ∃ F : ShadowA → Value,
      ∀ world : World, F (shadowA world) = value world) ↔
    (¬ ∃ G : ShadowB → Value,
      ∀ world : World, G (shadowB world) = value world) := by
  have hFactorIff :=
    mutually_decodable_factorization_iff
      shadowA shadowB value toA toB hAfromB hBfromA
  constructor
  · intro hNoA hFactorB
    exact hNoA (hFactorIff.2 hFactorB)
  · intro hNoB hFactorA
    exact hNoB (hFactorIff.1 hFactorA)

def encodedTarget
    {World Value Encoded : Type}
    (encode : Value → Encoded) (value : World → Value) :
    World → Encoded :=
  fun world => encode (value world)

def TargetImageInjective
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded) : Prop :=
  ∀ x y : World, encode (value x) = encode (value y) → value x = value y

theorem injective_encoding_implies_target_image_injective
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded)
    (hInjective : Function.Injective encode) :
    TargetImageInjective value encode := by
  intro x y hEncoded
  exact hInjective hEncoded

theorem target_image_injective_encoded_target_fibers
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode)
    (x y : World) :
    encodedTarget encode value x = encodedTarget encode value y ↔
      value x = value y := by
  constructor
  · intro hEncoded
    exact hTargetImageInjective x y hEncoded
  · intro hValue
    exact congrArg encode hValue

theorem encoded_target_fiber_equivalence_implies_target_image_injective
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded)
    (hFibers : ∀ x y : World,
      encodedTarget encode value x = encodedTarget encode value y ↔
        value x = value y) :
    TargetImageInjective value encode := by
  intro x y hEncoded
  exact (hFibers x y).1 hEncoded

theorem target_image_injective_iff_encoded_target_fiber_equivalence
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded) :
    TargetImageInjective value encode ↔
      ∀ x y : World,
        encodedTarget encode value x = encodedTarget encode value y ↔
          value x = value y := by
  constructor
  · intro hTargetImageInjective x y
    exact target_image_injective_encoded_target_fibers
      value encode hTargetImageInjective x y
  · intro hFibers
    exact encoded_target_fiber_equivalence_implies_target_image_injective
      value encode hFibers

theorem target_image_injective_preserves_target_distinction
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode)
    {x y : World}
    (hValueDistinct : value x ≠ value y) :
    encodedTarget encode value x ≠ encodedTarget encode value y := by
  intro hEncoded
  exact hValueDistinct (hTargetImageInjective x y hEncoded)

theorem encoded_collision_on_distinct_targets_blocks_target_image_injective
    {World Value Encoded : Type}
    (value : World → Value) (encode : Value → Encoded)
    {x y : World}
    (hEncoded : encodedTarget encode value x = encodedTarget encode value y)
    (hValueDistinct : value x ≠ value y) :
    ¬ TargetImageInjective value encode := by
  intro hTargetImageInjective
  exact hValueDistinct (hTargetImageInjective x y hEncoded)

theorem target_image_injective_preserves_downstream_shadow_invariant
    {World Value Encoded Downstream : Type}
    (value : World → Value) (encode : Value → Encoded)
    (downstream : World → Downstream)
    (hTargetImageInjective : TargetImageInjective value encode) :
    ShadowFiberInvariant (encodedTarget encode value) downstream ↔
      ShadowFiberInvariant value downstream := by
  exact fiber_equivalent_shadow_invariant_iff
    (encodedTarget encode value) value downstream
    (fun x y =>
      target_image_injective_encoded_target_fibers
        value encode hTargetImageInjective x y)

theorem target_image_injective_preserves_downstream_quotient_descent
    {World Value Encoded Downstream : Type}
    (value : World → Value) (encode : Value → Encoded)
    (downstream : World → Downstream)
    (hTargetImageInjective : TargetImageInjective value encode) :
    (∃ F : (shadowPrimitiveDifference
          (encodedTarget encode value)).ResidualQuotient → Downstream,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference
              (encodedTarget encode value)) world) = downstream world) ↔
    (∃ G : (shadowPrimitiveDifference value).ResidualQuotient → Downstream,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference value) world) = downstream world) := by
  exact fiber_equivalent_quotient_descent_iff
    (encodedTarget encode value) value downstream
    (fun x y =>
      target_image_injective_encoded_target_fibers
        value encode hTargetImageInjective x y)

theorem target_image_injective_composition
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂)
    (hFirst : TargetImageInjective value encode₁)
    (hSecond :
      TargetImageInjective (encodedTarget encode₁ value) encode₂) :
    TargetImageInjective value (fun v => encode₂ (encode₁ v)) := by
  intro x y hComposed
  have hEncoded₁ : encodedTarget encode₁ value x =
      encodedTarget encode₁ value y :=
    hSecond x y hComposed
  exact hFirst x y hEncoded₁

theorem composed_target_image_injective_implies_first
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂)
    (hComposed :
      TargetImageInjective value (fun v => encode₂ (encode₁ v))) :
    TargetImageInjective value encode₁ := by
  intro x y hEncoded₁
  exact hComposed x y (congrArg encode₂ hEncoded₁)

theorem composed_target_image_injective_implies_second_on_first_image
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂)
    (hComposed :
      TargetImageInjective value (fun v => encode₂ (encode₁ v))) :
    TargetImageInjective (encodedTarget encode₁ value) encode₂ := by
  intro x y hEncoded₂
  exact congrArg encode₁ (hComposed x y hEncoded₂)

theorem target_image_injective_composition_iff
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂) :
    TargetImageInjective value (fun v => encode₂ (encode₁ v)) ↔
      TargetImageInjective value encode₁ ∧
        TargetImageInjective (encodedTarget encode₁ value) encode₂ := by
  constructor
  · intro hComposed
    exact ⟨
      composed_target_image_injective_implies_first
        value encode₁ encode₂ hComposed,
      composed_target_image_injective_implies_second_on_first_image
        value encode₁ encode₂ hComposed⟩
  · intro hStages
    exact target_image_injective_composition
      value encode₁ encode₂ hStages.1 hStages.2

theorem unsafe_first_stage_blocks_composed_target_image_injective
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂)
    (hUnsafeFirst : ¬ TargetImageInjective value encode₁) :
    ¬ TargetImageInjective value (fun v => encode₂ (encode₁ v)) := by
  intro hComposed
  exact hUnsafeFirst
    (composed_target_image_injective_implies_first
      value encode₁ encode₂ hComposed)

theorem unsafe_second_stage_blocks_composed_target_image_injective
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Encoded₁ → Encoded₂)
    (hUnsafeSecond :
      ¬ TargetImageInjective (encodedTarget encode₁ value) encode₂) :
    ¬ TargetImageInjective value (fun v => encode₂ (encode₁ v)) := by
  intro hComposed
  exact hUnsafeSecond
    (composed_target_image_injective_implies_second_on_first_image
      value encode₁ encode₂ hComposed)

def JointTargetImageInjective
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂) : Prop :=
  ∀ x y : World,
    encode₁ (value x) = encode₁ (value y) →
      encode₂ (value x) = encode₂ (value y) →
        value x = value y

theorem pair_target_image_injective_iff_joint
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂) :
    TargetImageInjective value (fun v => (encode₁ v, encode₂ v)) ↔
      JointTargetImageInjective value encode₁ encode₂ := by
  constructor
  · intro hPair x y hEncoded₁ hEncoded₂
    exact hPair x y (Prod.ext hEncoded₁ hEncoded₂)
  · intro hJoint x y hPair
    have hEncoded₁ :
        encode₁ (value x) = encode₁ (value y) :=
      congrArg Prod.fst hPair
    have hEncoded₂ :
        encode₂ (value x) = encode₂ (value y) :=
      congrArg Prod.snd hPair
    exact hJoint x y hEncoded₁ hEncoded₂

theorem left_target_image_injective_implies_joint
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    (hLeft : TargetImageInjective value encode₁) :
    JointTargetImageInjective value encode₁ encode₂ := by
  intro x y hEncoded₁ _hEncoded₂
  exact hLeft x y hEncoded₁

theorem right_target_image_injective_implies_joint
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    (hRight : TargetImageInjective value encode₂) :
    JointTargetImageInjective value encode₁ encode₂ := by
  intro x y _hEncoded₁ hEncoded₂
  exact hRight x y hEncoded₂

theorem left_target_image_injective_implies_pair_safe
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    (hLeft : TargetImageInjective value encode₁) :
    TargetImageInjective value (fun v => (encode₁ v, encode₂ v)) :=
  (pair_target_image_injective_iff_joint value encode₁ encode₂).2
    (left_target_image_injective_implies_joint value encode₁ encode₂ hLeft)

theorem right_target_image_injective_implies_pair_safe
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    (hRight : TargetImageInjective value encode₂) :
    TargetImageInjective value (fun v => (encode₁ v, encode₂ v)) :=
  (pair_target_image_injective_iff_joint value encode₁ encode₂).2
    (right_target_image_injective_implies_joint value encode₁ encode₂ hRight)

theorem joint_encoded_collision_on_distinct_targets_blocks_pair_safe
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    {x y : World}
    (hEncoded₁ : encode₁ (value x) = encode₁ (value y))
    (hEncoded₂ : encode₂ (value x) = encode₂ (value y))
    (hValueDistinct : value x ≠ value y) :
    ¬ TargetImageInjective value (fun v => (encode₁ v, encode₂ v)) := by
  intro hPairSafe
  exact hValueDistinct (hPairSafe x y (Prod.ext hEncoded₁ hEncoded₂))

theorem pair_safe_blocks_joint_encoded_collision
    {World Value Encoded₁ Encoded₂ : Type}
    (value : World → Value)
    (encode₁ : Value → Encoded₁)
    (encode₂ : Value → Encoded₂)
    (hPairSafe : TargetImageInjective value (fun v => (encode₁ v, encode₂ v)))
    {x y : World}
    (hValueDistinct : value x ≠ value y) :
    ¬ (encode₁ (value x) = encode₁ (value y) ∧
        encode₂ (value x) = encode₂ (value y)) := by
  intro hBoth
  exact hValueDistinct (hPairSafe x y (Prod.ext hBoth.1 hBoth.2))

theorem target_encoding_preserves_shadow_invariant
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hInvariant : ShadowFiberInvariant shadow value) :
    ShadowFiberInvariant shadow (encodedTarget encode value) := by
  intro x y hShadow
  exact congrArg encode (hInvariant x y hShadow)

theorem injective_target_encoding_reflects_shadow_invariant
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hInjective : Function.Injective encode)
    (hInvariant : ShadowFiberInvariant shadow (encodedTarget encode value)) :
    ShadowFiberInvariant shadow value := by
  intro x y hShadow
  exact hInjective (hInvariant x y hShadow)

theorem target_image_injective_reflects_shadow_invariant
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode)
    (hInvariant : ShadowFiberInvariant shadow (encodedTarget encode value)) :
    ShadowFiberInvariant shadow value := by
  intro x y hShadow
  exact hTargetImageInjective x y (hInvariant x y hShadow)

theorem injective_target_encoding_shadow_invariant_iff
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hInjective : Function.Injective encode) :
    ShadowFiberInvariant shadow (encodedTarget encode value) ↔
      ShadowFiberInvariant shadow value := by
  constructor
  · exact injective_target_encoding_reflects_shadow_invariant
      shadow value encode hInjective
  · exact target_encoding_preserves_shadow_invariant shadow value encode

theorem target_image_injective_shadow_invariant_iff
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode) :
    ShadowFiberInvariant shadow (encodedTarget encode value) ↔
      ShadowFiberInvariant shadow value := by
  constructor
  · exact target_image_injective_reflects_shadow_invariant
      shadow value encode hTargetImageInjective
  · exact target_encoding_preserves_shadow_invariant shadow value encode

theorem target_encoding_preserves_quotient_descent
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hDescends :
      ∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) = value world) :
    ∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) =
          encodedTarget encode value world := by
  rcases hDescends with ⟨F, hF⟩
  exact ⟨fun q => encode (F q), by
    intro world
    change encode (F (OmegaCore.PrimitiveDifference.classOf
      (shadowPrimitiveDifference shadow) world)) = encode (value world)
    rw [hF world]⟩

theorem injective_target_encoding_reflects_quotient_descent
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hInjective : Function.Injective encode)
    (hDescends :
      ∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
        ∀ world : World,
          G (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) =
            encodedTarget encode value world) :
    ∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) = value world := by
  have hEncodedInvariant :
      ShadowFiberInvariant shadow (encodedTarget encode value) :=
    (shadow_value_descends_iff_fiber_invariant
      shadow (encodedTarget encode value)).1 hDescends
  have hValueInvariant :
      ShadowFiberInvariant shadow value :=
    injective_target_encoding_reflects_shadow_invariant
      shadow value encode hInjective hEncodedInvariant
  exact (shadow_value_descends_iff_fiber_invariant shadow value).2
    hValueInvariant

theorem target_image_injective_reflects_quotient_descent
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode)
    (hDescends :
      ∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
        ∀ world : World,
          G (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) =
            encodedTarget encode value world) :
    ∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) = value world := by
  have hEncodedInvariant :
      ShadowFiberInvariant shadow (encodedTarget encode value) :=
    (shadow_value_descends_iff_fiber_invariant
      shadow (encodedTarget encode value)).1 hDescends
  have hValueInvariant :
      ShadowFiberInvariant shadow value :=
    target_image_injective_reflects_shadow_invariant
      shadow value encode hTargetImageInjective hEncodedInvariant
  exact (shadow_value_descends_iff_fiber_invariant shadow value).2
    hValueInvariant

theorem injective_target_encoding_quotient_descent_iff
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hInjective : Function.Injective encode) :
    (∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) =
          encodedTarget encode value world) ↔
    (∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) = value world) := by
  constructor
  · exact injective_target_encoding_reflects_quotient_descent
      shadow value encode hInjective
  · exact target_encoding_preserves_quotient_descent shadow value encode

theorem target_image_injective_quotient_descent_iff
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (hTargetImageInjective : TargetImageInjective value encode) :
    (∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) =
          encodedTarget encode value world) ↔
    (∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
      ∀ world : World,
        F (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference shadow) world) = value world) := by
  constructor
  · exact target_image_injective_reflects_quotient_descent
      shadow value encode hTargetImageInjective
  · exact target_encoding_preserves_quotient_descent shadow value encode

theorem encoded_invariant_on_target_collision_forces_noninjective
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b)
    (hEncodedInvariant :
      ShadowFiberInvariant shadow (encodedTarget encode value)) :
    ¬ Function.Injective encode := by
  intro hInjective
  exact hValue (hInjective (hEncodedInvariant a b hShadow))

theorem encoded_quotient_descent_on_target_collision_forces_noninjective
    {World Shadow Value Encoded : Type}
    (shadow : World → Shadow) (value : World → Value)
    (encode : Value → Encoded)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b)
    (hEncodedDescends :
      ∃ G : (shadowPrimitiveDifference shadow).ResidualQuotient → Encoded,
        ∀ world : World,
          G (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) =
            encodedTarget encode value world) :
    ¬ Function.Injective encode := by
  have hEncodedInvariant :
      ShadowFiberInvariant shadow (encodedTarget encode value) :=
    (shadow_value_descends_iff_fiber_invariant
      shadow (encodedTarget encode value)).1 hEncodedDescends
  exact encoded_invariant_on_target_collision_forces_noninjective
    shadow value encode a b hShadow hValue hEncodedInvariant

theorem bridge_factorization_separates_target_distinct_worlds
    {World Bridge Value : Type}
    (bridge : World → Bridge) (value : World → Value)
    (hFactor : ∃ F : Bridge → Value,
      ∀ world : World, F (bridge world) = value world)
    {a b : World}
    (hValue : value a ≠ value b) :
    bridge a ≠ bridge b := by
  intro hBridge
  rcases hFactor with ⟨F, hF⟩
  have hSameBridgeValue : F (bridge a) = F (bridge b) :=
    congrArg F hBridge
  have hSameValue : value a = value b :=
    Eq.trans (hF a).symm (Eq.trans hSameBridgeValue (hF b))
  exact hValue hSameValue

theorem nonseparating_bridge_cannot_decode_target
    {World Bridge Value : Type}
    (bridge : World → Bridge) (value : World → Value)
    (a b : World)
    (hBridge : bridge a = bridge b)
    (hValue : value a ≠ value b) :
    ¬ ∃ F : Bridge → Value,
      ∀ world : World, F (bridge world) = value world := by
  intro hFactor
  exact bridge_factorization_separates_target_distinct_worlds
    bridge value hFactor hValue hBridge

theorem packet_shape_forgetfulness_is_shadow_collision :
    ¬ ∃ F : Unit → Bool,
        ∀ world : PromptWorld, F (packetShape world) = semanticTruth world := by
  exact no_factor_through_shadow_of_collision
    packetShape
    semanticTruth
    PromptWorld.faithful
    PromptWorld.silentMutation
    rfl
    (by
      intro h
      cases h)

inductive LocalShadowWorld where
  | allGreen
  | localGreenGlobalRed
  deriving DecidableEq, Repr

def localPassShadow (_world : LocalShadowWorld) : Unit :=
  ()

def globalGreenTarget : LocalShadowWorld → Bool
  | LocalShadowWorld.allGreen => true
  | LocalShadowWorld.localGreenGlobalRed => false

theorem local_pass_shadow_forgets_global_green :
    ¬ ∃ F : Unit → Bool,
        ∀ world : LocalShadowWorld,
          F (localPassShadow world) = globalGreenTarget world := by
  exact no_factor_through_shadow_of_collision
    localPassShadow
    globalGreenTarget
    LocalShadowWorld.allGreen
    LocalShadowWorld.localGreenGlobalRed
    rfl
    (by
      intro h
      cases h)

theorem finite_zeta_source_forgetfulness_is_shadow_collision :
    ¬ ∃ F : Unit → Bool,
        ∀ world : ContinuumZetaWorld,
          F (finiteZetaShadow world) = namesRhContinuumSource world := by
  exact no_factor_through_shadow_of_collision
    finiteZetaShadow
    namesRhContinuumSource
    ContinuumZetaWorld.riemannSource
    ContinuumZetaWorld.alternateSource
    rfl
    (by
      intro h
      cases h)

theorem finite_zeta_delta_forgetfulness_is_shadow_collision :
    ¬ ∃ F : Unit → Bool,
        ∀ world : TowerDeltaWorld,
          F (finiteTowerZetaShape world) = isDeltaTwoOutcome world := by
  exact no_factor_through_shadow_of_collision
    finiteTowerZetaShape
    isDeltaTwoOutcome
    TowerDeltaWorld.deltaTwo
    TowerDeltaWorld.deltaThree
    rfl
    (by
      intro h
      cases h)

theorem rh_source_name_forgetfulness_is_shadow_collision :
    ¬ ∃ F : Bool → Bool,
        ∀ world : RhNamedTowerWorld,
          F (namesRhSourceForTower world) = rhNamedTowerIsDeltaTwo world := by
  exact no_factor_through_shadow_of_collision
    namesRhSourceForTower
    rhNamedTowerIsDeltaTwo
    RhNamedTowerWorld.rhDeltaTwo
    RhNamedTowerWorld.rhDeltaThree
    rfl
    (by
      intro h
      cases h)

theorem rh_delta_bridge_must_separate_delta_worlds
    {Bridge : Type}
    (bridge : RhNamedTowerWorld → Bridge)
    (hFactor : ∃ F : Bridge → Bool,
      ∀ world : RhNamedTowerWorld,
        F (bridge world) = rhNamedTowerIsDeltaTwo world) :
    bridge RhNamedTowerWorld.rhDeltaTwo ≠
      bridge RhNamedTowerWorld.rhDeltaThree := by
  exact bridge_factorization_separates_target_distinct_worlds
    bridge
    rhNamedTowerIsDeltaTwo
    hFactor
    (by
      intro h
      cases h)

def targetAugmentedShadow
    {World Shadow Value : Type}
    (shadow : World → Shadow) (value : World → Value) (world : World) :
    Shadow × Value :=
  (shadow world, value world)

def augmentedShadow
    {World Shadow Extra : Type}
    (shadow : World → Shadow) (extra : World → Extra) (world : World) :
    Shadow × Extra :=
  (shadow world, extra world)

def AugmentedFiberInvariant
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value) : Prop :=
  ∀ x y : World,
    shadow x = shadow y → extra x = extra y → value x = value y

def AugmentationSeparatesTargetCollisions
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value) : Prop :=
  ∀ x y : World,
    shadow x = shadow y → value x ≠ value y → extra x ≠ extra y

theorem augmented_fiber_invariant_iff_separates_target_collisions
    {World Shadow Extra Value : Type} [DecidableEq Value]
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value) :
    AugmentedFiberInvariant shadow extra value ↔
      AugmentationSeparatesTargetCollisions shadow extra value := by
  constructor
  · intro hInvariant x y hShadow hValue hExtra
    exact hValue (hInvariant x y hShadow hExtra)
  · intro hSeparates x y hShadow hExtra
    by_cases hValue : value x = value y
    · exact hValue
    · exact False.elim ((hSeparates x y hShadow hValue) hExtra)

theorem augmented_value_descends_iff_pair_fiber_invariant
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value) :
    (∃ F : (shadowPrimitiveDifference (augmentedShadow shadow extra)).ResidualQuotient →
          Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference (augmentedShadow shadow extra))
              world) = value world)
      ↔ AugmentedFiberInvariant shadow extra value := by
  constructor
  · intro h
    have hInvariant :=
      (shadow_value_descends_iff_fiber_invariant
        (augmentedShadow shadow extra) value).1 h
    intro x y hShadow hExtra
    exact hInvariant x y (Prod.ext hShadow hExtra)
  · intro hInvariant
    apply (shadow_value_descends_iff_fiber_invariant
      (augmentedShadow shadow extra) value).2
    intro x y hPair
    exact hInvariant x y (congrArg Prod.fst hPair) (congrArg Prod.snd hPair)

theorem augmented_quotient_descent_iff_separates_target_collisions
    {World Shadow Extra Value : Type} [DecidableEq Value]
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value) :
    (∃ F : (shadowPrimitiveDifference (augmentedShadow shadow extra)).ResidualQuotient →
          Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference (augmentedShadow shadow extra))
              world) = value world)
      ↔ AugmentationSeparatesTargetCollisions shadow extra value := by
  exact Iff.trans
    (augmented_value_descends_iff_pair_fiber_invariant shadow extra value)
    (augmented_fiber_invariant_iff_separates_target_collisions
      shadow extra value)

theorem shadow_fiber_invariant_lifts_to_augmented
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value)
    (hInvariant : ShadowFiberInvariant shadow value) :
    AugmentedFiberInvariant shadow extra value := by
  intro x y hShadow _hExtra
  exact hInvariant x y hShadow

theorem shadow_factor_lifts_to_augmented_shadow
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value)
    (hFactor : ∃ F : Shadow → Value,
      ∀ world : World, F (shadow world) = value world) :
    ∃ G : Shadow × Extra → Value,
      ∀ world : World, G (shadow world, extra world) = value world := by
  rcases hFactor with ⟨F, hF⟩
  exact ⟨fun pair => F pair.1, by intro world; exact hF world⟩

theorem shadow_quotient_descent_lifts_to_augmented_quotient
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow) (extra : World → Extra)
    (value : World → Value)
    (hDescends :
      ∃ F : (shadowPrimitiveDifference shadow).ResidualQuotient → Value,
        ∀ world : World,
          F (OmegaCore.PrimitiveDifference.classOf
              (shadowPrimitiveDifference shadow) world) = value world) :
    ∃ G : (shadowPrimitiveDifference (augmentedShadow shadow extra)).ResidualQuotient →
          Value,
      ∀ world : World,
        G (OmegaCore.PrimitiveDifference.classOf
            (shadowPrimitiveDifference (augmentedShadow shadow extra)) world) =
          value world := by
  have hInvariant :
      ShadowFiberInvariant shadow value :=
    (shadow_value_descends_iff_fiber_invariant shadow value).1 hDescends
  have hAugmentedInvariant :
      AugmentedFiberInvariant shadow extra value :=
    shadow_fiber_invariant_lifts_to_augmented shadow extra value hInvariant
  exact (augmented_value_descends_iff_pair_fiber_invariant shadow extra value).2
    hAugmentedInvariant

theorem target_augmented_shadow_carries_value
    {World Shadow Value : Type}
    (shadow : World → Shadow) (value : World → Value) :
    ∃ F : Shadow × Value → Value,
      ∀ world : World,
        F (targetAugmentedShadow shadow value world) = value world := by
  exact ⟨Prod.snd, by intro world; rfl⟩

theorem coarsening_cannot_repair_shadow_collision
    {World FineShadow CoarseShadow Value : Type}
    (fineShadow : World → FineShadow)
    (coarsen : FineShadow → CoarseShadow)
    (value : World → Value)
    (a b : World)
    (hFineCollision : fineShadow a = fineShadow b)
    (hValue : value a ≠ value b) :
    ¬ ∃ F : CoarseShadow → Value,
        ∀ world : World,
          F (coarsen (fineShadow world)) = value world := by
  exact no_factor_through_shadow_of_collision
    (fun world => coarsen (fineShadow world))
    value
    a
    b
    (congrArg coarsen hFineCollision)
    hValue

theorem augmentation_must_separate_target_collision
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow)
    (extra : World → Extra)
    (value : World → Value)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b)
    (F : Shadow × Extra → Value)
    (hF : ∀ world : World, F (shadow world, extra world) = value world) :
    extra a ≠ extra b := by
  intro hExtra
  have hPair : (shadow a, extra a) = (shadow b, extra b) := by
    exact Prod.ext hShadow hExtra
  have hSameAugmentedValue :
      F (shadow a, extra a) = F (shadow b, extra b) :=
    congrArg F hPair
  have hSameValue : value a = value b :=
    Eq.trans (hF a).symm (Eq.trans hSameAugmentedValue (hF b))
  exact hValue hSameValue

theorem nonseparating_augmentation_cannot_repair_collision
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow)
    (extra : World → Extra)
    (value : World → Value)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hExtra : extra a = extra b)
    (hValue : value a ≠ value b) :
    ¬ ∃ F : Shadow × Extra → Value,
        ∀ world : World, F (shadow world, extra world) = value world := by
  intro h
  rcases h with ⟨F, hF⟩
  exact augmentation_must_separate_target_collision
    shadow extra value a b hShadow hValue F hF hExtra

theorem shadow_derived_augmentation_cannot_repair_collision
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow)
    (deriveExtra : Shadow → Extra)
    (value : World → Value)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b) :
    ¬ ∃ F : Shadow × Extra → Value,
        ∀ world : World,
          F (shadow world, deriveExtra (shadow world)) = value world := by
  exact nonseparating_augmentation_cannot_repair_collision
    shadow
    (fun world => deriveExtra (shadow world))
    value
    a
    b
    hShadow
    (congrArg deriveExtra hShadow)
    hValue

theorem successful_augmentation_not_shadow_derived_on_collision
    {World Shadow Extra Value : Type}
    (shadow : World → Shadow)
    (extra : World → Extra)
    (value : World → Value)
    (a b : World)
    (hShadow : shadow a = shadow b)
    (hValue : value a ≠ value b)
    (F : Shadow × Extra → Value)
    (hF : ∀ world : World, F (shadow world, extra world) = value world) :
    ¬ ∃ deriveExtra : Shadow → Extra,
        ∀ world : World, extra world = deriveExtra (shadow world) := by
  intro hDerived
  rcases hDerived with ⟨deriveExtra, hExtra⟩
  have hExtraAB : extra a = extra b := by
    calc
      extra a = deriveExtra (shadow a) := hExtra a
      _ = deriveExtra (shadow b) := congrArg deriveExtra hShadow
      _ = extra b := (hExtra b).symm
  exact augmentation_must_separate_target_collision
    shadow extra value a b hShadow hValue F hF hExtraAB

#print axioms SnSymbolGameAndPackets.no_factor_through_shadow_of_collision
#print axioms SnSymbolGameAndPackets.bridge_factorization_implies_fiber_invariant
#print axioms SnSymbolGameAndPackets.bridge_factorization_descends_to_bridge_quotient
#print axioms SnSymbolGameAndPackets.coarsened_shadow_invariant_lifts_to_refinement
#print axioms SnSymbolGameAndPackets.coarsened_factor_lifts_to_refinement
#print axioms SnSymbolGameAndPackets.coarsened_quotient_descent_lifts_to_refinement
#print axioms SnSymbolGameAndPackets.no_coarsened_invariant_if_no_refinement_invariant
#print axioms SnSymbolGameAndPackets.no_coarsened_factor_if_no_refinement_factor
#print axioms SnSymbolGameAndPackets.no_coarsened_quotient_descent_if_no_refinement_quotient_descent
#print axioms SnSymbolGameAndPackets.fiber_equivalent_shadow_invariant_iff
#print axioms SnSymbolGameAndPackets.mutually_decodable_factorization_iff
#print axioms SnSymbolGameAndPackets.fiber_equivalent_quotient_descent_iff
#print axioms SnSymbolGameAndPackets.mutually_decodable_no_factorization_iff
#print axioms SnSymbolGameAndPackets.injective_encoding_implies_target_image_injective
#print axioms SnSymbolGameAndPackets.target_image_injective_encoded_target_fibers
#print axioms SnSymbolGameAndPackets.encoded_target_fiber_equivalence_implies_target_image_injective
#print axioms SnSymbolGameAndPackets.target_image_injective_iff_encoded_target_fiber_equivalence
#print axioms SnSymbolGameAndPackets.target_image_injective_preserves_target_distinction
#print axioms SnSymbolGameAndPackets.encoded_collision_on_distinct_targets_blocks_target_image_injective
#print axioms SnSymbolGameAndPackets.target_image_injective_preserves_downstream_shadow_invariant
#print axioms SnSymbolGameAndPackets.target_image_injective_preserves_downstream_quotient_descent
#print axioms SnSymbolGameAndPackets.target_image_injective_composition
#print axioms SnSymbolGameAndPackets.composed_target_image_injective_implies_first
#print axioms SnSymbolGameAndPackets.composed_target_image_injective_implies_second_on_first_image
#print axioms SnSymbolGameAndPackets.target_image_injective_composition_iff
#print axioms SnSymbolGameAndPackets.unsafe_first_stage_blocks_composed_target_image_injective
#print axioms SnSymbolGameAndPackets.unsafe_second_stage_blocks_composed_target_image_injective
#print axioms SnSymbolGameAndPackets.pair_target_image_injective_iff_joint
#print axioms SnSymbolGameAndPackets.left_target_image_injective_implies_joint
#print axioms SnSymbolGameAndPackets.right_target_image_injective_implies_joint
#print axioms SnSymbolGameAndPackets.left_target_image_injective_implies_pair_safe
#print axioms SnSymbolGameAndPackets.right_target_image_injective_implies_pair_safe
#print axioms SnSymbolGameAndPackets.joint_encoded_collision_on_distinct_targets_blocks_pair_safe
#print axioms SnSymbolGameAndPackets.pair_safe_blocks_joint_encoded_collision
#print axioms SnSymbolGameAndPackets.target_encoding_preserves_shadow_invariant
#print axioms SnSymbolGameAndPackets.injective_target_encoding_reflects_shadow_invariant
#print axioms SnSymbolGameAndPackets.target_image_injective_reflects_shadow_invariant
#print axioms SnSymbolGameAndPackets.injective_target_encoding_shadow_invariant_iff
#print axioms SnSymbolGameAndPackets.target_image_injective_shadow_invariant_iff
#print axioms SnSymbolGameAndPackets.target_encoding_preserves_quotient_descent
#print axioms SnSymbolGameAndPackets.injective_target_encoding_reflects_quotient_descent
#print axioms SnSymbolGameAndPackets.target_image_injective_reflects_quotient_descent
#print axioms SnSymbolGameAndPackets.injective_target_encoding_quotient_descent_iff
#print axioms SnSymbolGameAndPackets.target_image_injective_quotient_descent_iff
#print axioms SnSymbolGameAndPackets.encoded_invariant_on_target_collision_forces_noninjective
#print axioms SnSymbolGameAndPackets.encoded_quotient_descent_on_target_collision_forces_noninjective
#print axioms SnSymbolGameAndPackets.bridge_factorization_separates_target_distinct_worlds
#print axioms SnSymbolGameAndPackets.nonseparating_bridge_cannot_decode_target
#print axioms SnSymbolGameAndPackets.shadow_value_descends_iff_fiber_invariant
#print axioms SnSymbolGameAndPackets.augmented_fiber_invariant_iff_separates_target_collisions
#print axioms SnSymbolGameAndPackets.augmented_value_descends_iff_pair_fiber_invariant
#print axioms SnSymbolGameAndPackets.augmented_quotient_descent_iff_separates_target_collisions
#print axioms SnSymbolGameAndPackets.shadow_fiber_invariant_lifts_to_augmented
#print axioms SnSymbolGameAndPackets.shadow_factor_lifts_to_augmented_shadow
#print axioms SnSymbolGameAndPackets.shadow_quotient_descent_lifts_to_augmented_quotient
#print axioms SnSymbolGameAndPackets.packet_shape_forgetfulness_is_shadow_collision
#print axioms SnSymbolGameAndPackets.local_pass_shadow_forgets_global_green
#print axioms SnSymbolGameAndPackets.finite_zeta_source_forgetfulness_is_shadow_collision
#print axioms SnSymbolGameAndPackets.finite_zeta_delta_forgetfulness_is_shadow_collision
#print axioms SnSymbolGameAndPackets.rh_source_name_forgetfulness_is_shadow_collision
#print axioms SnSymbolGameAndPackets.rh_delta_bridge_must_separate_delta_worlds
#print axioms SnSymbolGameAndPackets.target_augmented_shadow_carries_value
#print axioms SnSymbolGameAndPackets.coarsening_cannot_repair_shadow_collision
#print axioms SnSymbolGameAndPackets.augmentation_must_separate_target_collision
#print axioms SnSymbolGameAndPackets.nonseparating_augmentation_cannot_repair_collision
#print axioms SnSymbolGameAndPackets.shadow_derived_augmentation_cannot_repair_collision
#print axioms SnSymbolGameAndPackets.successful_augmentation_not_shadow_derived_on_collision

end SnSymbolGameAndPackets
