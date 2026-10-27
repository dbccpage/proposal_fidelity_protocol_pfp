import SLevel
/-!
Tower and zeta-data kernels for the S(n) / Symbol Game / packetization paper.

The tower coordinate is separate from the `LicensedLift` index.  A lift still
uses `S(n) -> S(n+1)`; a tower profile records the independent outcome measure
whose step may be 2 for this tower and different for other towers.

The zeta/RH bridge is intentionally weak.  It records finite tower-local zeta
data and says that a continuum-source claim is not authority unless a finite
bridge packet and certified terminal theorem are present.
-/

namespace SnSymbolGameAndPackets

universe u v w

structure TowerProfile where
  base : Nat
  delta : Nat
  deriving Repr

def TowerProfile.coord (T : TowerProfile) (k : Nat) : Nat :=
  T.base + T.delta * k

def deltaTwoTower : TowerProfile :=
  { base := 0, delta := 2 }

def deltaTower (delta : Nat) : TowerProfile :=
  { base := 0, delta := delta }

def positiveDeltaTower (index : Nat) : TowerProfile :=
  deltaTower (index + 1)

theorem delta_tower_first_coordinate (delta : Nat) :
    (deltaTower delta).coord 1 = delta := by
  unfold deltaTower TowerProfile.coord
  rw [Nat.mul_one, Nat.zero_add]

theorem positive_delta_tower_first_coordinate (index : Nat) :
    (positiveDeltaTower index).coord 1 = index + 1 := by
  unfold positiveDeltaTower
  exact delta_tower_first_coordinate (index + 1)

theorem positive_delta_tower_has_positive_step (index : Nat) :
    0 < (positiveDeltaTower index).delta := by
  unfold positiveDeltaTower deltaTower
  exact Nat.succ_pos index

theorem positive_delta_tower_family_injective_first_coordinate :
    Function.Injective (fun index : Nat =>
      (positiveDeltaTower index).coord 1) := by
  intro indexA indexB hEq
  change (positiveDeltaTower indexA).coord 1 =
    (positiveDeltaTower indexB).coord 1 at hEq
  rw [positive_delta_tower_first_coordinate indexA,
    positive_delta_tower_first_coordinate indexB] at hEq
  change Nat.succ indexA = Nat.succ indexB at hEq
  exact Nat.succ.inj hEq

theorem distinct_positive_delta_towers_have_distinct_first_coordinates
    {indexA indexB : Nat} (hIndex : indexA ≠ indexB) :
    (positiveDeltaTower indexA).coord 1 ≠
      (positiveDeltaTower indexB).coord 1 := by
  intro hEq
  exact hIndex (positive_delta_tower_family_injective_first_coordinate hEq)

theorem positive_delta_tower_index_one_is_delta_two :
    positiveDeltaTower 1 = deltaTwoTower := by
  rfl

theorem positive_delta_tower_symbol_game_index_iff_first_coordinate_two
    (index : Nat) :
    (positiveDeltaTower index).coord 1 = 2 ↔ index = 1 := by
  constructor
  · intro hEq
    rw [positive_delta_tower_first_coordinate] at hEq
    change Nat.succ index = Nat.succ 1 at hEq
    exact Nat.succ.inj hEq
  · intro hIndex
    rw [positive_delta_tower_first_coordinate, hIndex]

theorem delta_tower_first_coordinate_injective :
    Function.Injective (fun delta : Nat => (deltaTower delta).coord 1) := by
  intro deltaA deltaB hEq
  change (deltaTower deltaA).coord 1 = (deltaTower deltaB).coord 1 at hEq
  rw [delta_tower_first_coordinate deltaA] at hEq
  rw [delta_tower_first_coordinate deltaB] at hEq
  exact hEq

theorem distinct_delta_towers_have_distinct_first_coordinates
    {deltaA deltaB : Nat} (hDelta : deltaA ≠ deltaB) :
    (deltaTower deltaA).coord 1 ≠ (deltaTower deltaB).coord 1 := by
  intro hEq
  exact hDelta (delta_tower_first_coordinate_injective hEq)

theorem delta_tower_is_delta_two_iff_first_coordinate_two (delta : Nat) :
    (deltaTower delta).coord 1 = 2 ↔ delta = 2 := by
  constructor
  · intro hEq
    rw [delta_tower_first_coordinate] at hEq
    exact hEq
  · intro hDelta
    rw [delta_tower_first_coordinate, hDelta]

theorem tower_step_law (T : TowerProfile) (k : Nat) :
    T.coord (k + 1) = T.coord k + T.delta := by
  unfold TowerProfile.coord
  rw [Nat.mul_succ, Nat.add_assoc]

theorem positive_delta_tower_step_law (index k : Nat) :
    (positiveDeltaTower index).coord (k + 1) =
      (positiveDeltaTower index).coord k + (index + 1) := by
  unfold positiveDeltaTower
  exact tower_step_law (deltaTower (index + 1)) k

theorem delta_two_tower_step (k : Nat) :
    deltaTwoTower.coord (k + 1) = deltaTwoTower.coord k + 2 := by
  simpa [deltaTwoTower] using tower_step_law deltaTwoTower k

theorem positive_delta_step_strict
    (T : TowerProfile) (hDelta : 0 < T.delta) (k : Nat) :
    T.coord k < T.coord (k + 1) := by
  rw [tower_step_law]
  exact Nat.lt_add_of_pos_right hDelta

theorem positive_delta_no_terminal_coordinate
    (T : TowerProfile) (hDelta : 0 < T.delta) :
    ∀ k : Nat, ∃ j : Nat, T.coord k < T.coord j := by
  intro k
  exact ⟨k + 1, positive_delta_step_strict T hDelta k⟩

theorem same_base_first_coordinate_equal_forces_delta_equal
    (base deltaA deltaB : Nat) :
    ({ base := base, delta := deltaA : TowerProfile }).coord 1 =
        ({ base := base, delta := deltaB : TowerProfile }).coord 1 →
      deltaA = deltaB := by
  intro hEq
  change base + deltaA * 1 = base + deltaB * 1 at hEq
  rw [Nat.mul_one, Nat.mul_one] at hEq
  induction base with
  | zero =>
      simpa using hEq
  | succ base ih =>
      have hSucc : (base + deltaA).succ = (base + deltaB).succ := by
        simpa [Nat.succ_eq_add_one, Nat.add_assoc, Nat.add_comm,
          Nat.add_left_comm] using hEq
      apply ih
      exact Nat.succ.inj hSucc

structure TowerZetaFamily (T : TowerProfile) where
  zetaAt : Nat → Nat → Int
  authorityEffect : AuthorityEffect

def evidenceOnlyZetaFamily
    (T : TowerProfile) (zetaAt : Nat → Nat → Int) : TowerZetaFamily T :=
  { zetaAt, authorityEffect := AuthorityEffect.none }

theorem evidence_only_zeta_family_no_authority
    (T : TowerProfile) (zetaAt : Nat → Nat → Int) :
    (evidenceOnlyZetaFamily T zetaAt).authorityEffect = AuthorityEffect.none := by
  rfl

def deltaTowerZetaFamily
    (delta : Nat) (zetaAt : Nat → Nat → Int) :
    TowerZetaFamily (deltaTower delta) :=
  evidenceOnlyZetaFamily (deltaTower delta) zetaAt

theorem delta_tower_zeta_family_no_authority
    (delta : Nat) (zetaAt : Nat → Nat → Int) :
    (deltaTowerZetaFamily delta zetaAt).authorityEffect = AuthorityEffect.none := by
  rfl

theorem every_delta_has_evidence_only_zeta_family
    (delta : Nat) :
    ∃ Z : TowerZetaFamily (deltaTower delta),
      Z.authorityEffect = AuthorityEffect.none := by
  exact ⟨deltaTowerZetaFamily delta (fun _ _ => 0), rfl⟩

theorem every_positive_delta_tower_has_evidence_only_zeta_family
    (index : Nat) :
    ∃ Z : TowerZetaFamily (positiveDeltaTower index),
      Z.authorityEffect = AuthorityEffect.none := by
  unfold positiveDeltaTower
  exact every_delta_has_evidence_only_zeta_family (index + 1)

theorem delta_tower_zeta_family_carrier_first_coordinate
    (delta : Nat) (zetaAt : Nat → Nat → Int) :
    (deltaTower delta).coord 1 = delta ∧
      (deltaTowerZetaFamily delta zetaAt).authorityEffect =
        AuthorityEffect.none := by
  exact ⟨delta_tower_first_coordinate delta,
    delta_tower_zeta_family_no_authority delta zetaAt⟩

theorem distinct_delta_zeta_family_carriers_have_distinct_first_coordinates
    {deltaA deltaB : Nat}
    (_ZA : TowerZetaFamily (deltaTower deltaA))
    (_ZB : TowerZetaFamily (deltaTower deltaB))
    (hDelta : deltaA ≠ deltaB) :
    (deltaTower deltaA).coord 1 ≠ (deltaTower deltaB).coord 1 := by
  exact distinct_delta_towers_have_distinct_first_coordinates hDelta

theorem delta_tower_zeta_family_delta_two_iff_first_coordinate_two
    (delta : Nat) (_Z : TowerZetaFamily (deltaTower delta)) :
    (deltaTower delta).coord 1 = 2 ↔ delta = 2 :=
  delta_tower_is_delta_two_iff_first_coordinate_two delta

structure PositiveTowerFamilyBridge (Source : Type u) where
  indexOf : Source → Nat
  zetaAt : Source → Nat → Nat → Int

def PositiveTowerFamilyBridge.tower
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    (source : Source) : TowerProfile :=
  positiveDeltaTower (B.indexOf source)

def PositiveTowerFamilyBridge.zetaFamily
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    (source : Source) : TowerZetaFamily (B.tower source) :=
  deltaTowerZetaFamily (B.indexOf source + 1) (B.zetaAt source)

theorem positive_tower_family_bridge_first_coordinate
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    (source : Source) :
    (B.tower source).coord 1 = B.indexOf source + 1 := by
  unfold PositiveTowerFamilyBridge.tower
  exact positive_delta_tower_first_coordinate (B.indexOf source)

theorem positive_tower_family_bridge_zeta_no_authority
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    (source : Source) :
    (B.zetaFamily source).authorityEffect = AuthorityEffect.none := by
  unfold PositiveTowerFamilyBridge.zetaFamily
  exact delta_tower_zeta_family_no_authority
    (B.indexOf source + 1) (B.zetaAt source)

theorem positive_tower_family_bridge_distinct_indices_have_distinct_first_coordinates
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA ≠ B.indexOf sourceB) :
    (B.tower sourceA).coord 1 ≠ (B.tower sourceB).coord 1 := by
  unfold PositiveTowerFamilyBridge.tower
  exact distinct_positive_delta_towers_have_distinct_first_coordinates hIndex

theorem positive_tower_family_bridge_same_first_coordinate_forces_same_index
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    {sourceA sourceB : Source}
    (hCoord : (B.tower sourceA).coord 1 = (B.tower sourceB).coord 1) :
    B.indexOf sourceA = B.indexOf sourceB := by
  change (positiveDeltaTower (B.indexOf sourceA)).coord 1 =
    (positiveDeltaTower (B.indexOf sourceB)).coord 1 at hCoord
  exact positive_delta_tower_family_injective_first_coordinate hCoord

theorem positive_tower_family_bridge_delta_two_iff_index_one
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    (source : Source) :
    (B.tower source).coord 1 = 2 ↔ B.indexOf source = 1 := by
  unfold PositiveTowerFamilyBridge.tower
  exact positive_delta_tower_symbol_game_index_iff_first_coordinate_two
    (B.indexOf source)

theorem positive_tower_family_bridge_same_index_has_same_first_coordinate
    {Source : Type u} (B : PositiveTowerFamilyBridge Source)
    {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA = B.indexOf sourceB) :
    (B.tower sourceA).coord 1 = (B.tower sourceB).coord 1 := by
  rw [positive_tower_family_bridge_first_coordinate B sourceA,
    positive_tower_family_bridge_first_coordinate B sourceB, hIndex]

theorem positive_tower_family_bridge_index_collision_blocks_target_decode
    {Source : Type u} {Value : Type v}
    (B : PositiveTowerFamilyBridge Source) (target : Source → Value)
    {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA = B.indexOf sourceB)
    (hTarget : target sourceA ≠ target sourceB) :
    ¬ ∃ decode : Nat → Value,
        ∀ source : Source, decode (B.indexOf source) = target source := by
  intro h
  rcases h with ⟨decode, hDecode⟩
  have hA := hDecode sourceA
  have hB := hDecode sourceB
  have hDecodeSame :
      decode (B.indexOf sourceA) = decode (B.indexOf sourceB) := by
    rw [hIndex]
  have hTargetEq : target sourceA = target sourceB := by
    rw [← hA, ← hB]
    exact hDecodeSame
  exact hTarget hTargetEq

structure PositiveTowerFiniteZetaBridge
    (Source : Type u) (Sample : Type v) where
  indexOf : Source → Nat
  zetaAt : Source → Nat → Nat → Int
  sampleOf : Source → Sample

def PositiveTowerFiniteZetaBridge.tower
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    (source : Source) : TowerProfile :=
  positiveDeltaTower (B.indexOf source)

def PositiveTowerFiniteZetaBridge.zetaFamily
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    (source : Source) : TowerZetaFamily (B.tower source) :=
  deltaTowerZetaFamily (B.indexOf source + 1) (B.zetaAt source)

def PositiveTowerFiniteZetaBridge.packet
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    (source : Source) : Nat × Sample :=
  (B.indexOf source, B.sampleOf source)

theorem positive_tower_finite_zeta_bridge_first_coordinate
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample) (source : Source) :
    (B.tower source).coord 1 = B.indexOf source + 1 := by
  unfold PositiveTowerFiniteZetaBridge.tower
  exact positive_delta_tower_first_coordinate (B.indexOf source)

theorem positive_tower_finite_zeta_bridge_zeta_no_authority
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample) (source : Source) :
    (B.zetaFamily source).authorityEffect = AuthorityEffect.none := by
  unfold PositiveTowerFiniteZetaBridge.zetaFamily
  exact delta_tower_zeta_family_no_authority
    (B.indexOf source + 1) (B.zetaAt source)

theorem positive_tower_finite_zeta_bridge_packet_eq
    {Source : Type u} {Sample : Type v}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA = B.indexOf sourceB)
    (hSample : B.sampleOf sourceA = B.sampleOf sourceB) :
    B.packet sourceA = B.packet sourceB := by
  unfold PositiveTowerFiniteZetaBridge.packet
  exact Prod.ext hIndex hSample

theorem positive_tower_finite_zeta_bridge_decode_implies_packet_invariant
    {Source : Type u} {Sample : Type v} {Value : Type w}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    (target : Source → Value) (decode : Nat × Sample → Value)
    (hDecode : ∀ source : Source, decode (B.packet source) = target source)
    {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA = B.indexOf sourceB)
    (hSample : B.sampleOf sourceA = B.sampleOf sourceB) :
    target sourceA = target sourceB := by
  have hPacket :
      B.packet sourceA = B.packet sourceB :=
    positive_tower_finite_zeta_bridge_packet_eq B hIndex hSample
  rw [← hDecode sourceA, ← hDecode sourceB, hPacket]

theorem positive_tower_finite_zeta_bridge_collision_blocks_target_decode
    {Source : Type u} {Sample : Type v} {Value : Type w}
    (B : PositiveTowerFiniteZetaBridge Source Sample)
    (target : Source → Value) {sourceA sourceB : Source}
    (hIndex : B.indexOf sourceA = B.indexOf sourceB)
    (hSample : B.sampleOf sourceA = B.sampleOf sourceB)
    (hTarget : target sourceA ≠ target sourceB) :
    ¬ ∃ decode : Nat × Sample → Value,
        ∀ source : Source, decode (B.packet source) = target source := by
  intro h
  rcases h with ⟨decode, hDecode⟩
  exact hTarget
    (positive_tower_finite_zeta_bridge_decode_implies_packet_invariant
      B target decode hDecode hIndex hSample)

structure TowerFamilyBridge (Source : Type u) where
  deltaOf : Source → Nat
  zetaAt : Source → Nat → Nat → Int

def TowerFamilyBridge.tower
    {Source : Type u} (B : TowerFamilyBridge Source) (source : Source) :
    TowerProfile :=
  deltaTower (B.deltaOf source)

def TowerFamilyBridge.zetaFamily
    {Source : Type u} (B : TowerFamilyBridge Source) (source : Source) :
    TowerZetaFamily (B.tower source) :=
  deltaTowerZetaFamily (B.deltaOf source) (B.zetaAt source)

theorem tower_family_bridge_first_coordinate
    {Source : Type u} (B : TowerFamilyBridge Source) (source : Source) :
    (B.tower source).coord 1 = B.deltaOf source := by
  unfold TowerFamilyBridge.tower
  exact delta_tower_first_coordinate (B.deltaOf source)

theorem tower_family_bridge_zeta_no_authority
    {Source : Type u} (B : TowerFamilyBridge Source) (source : Source) :
    (B.zetaFamily source).authorityEffect = AuthorityEffect.none := by
  unfold TowerFamilyBridge.zetaFamily
  exact delta_tower_zeta_family_no_authority
    (B.deltaOf source) (B.zetaAt source)

theorem tower_family_bridge_distinct_deltas_have_distinct_first_coordinates
    {Source : Type u} (B : TowerFamilyBridge Source) {sourceA sourceB : Source}
    (hDelta : B.deltaOf sourceA ≠ B.deltaOf sourceB) :
    (B.tower sourceA).coord 1 ≠ (B.tower sourceB).coord 1 := by
  unfold TowerFamilyBridge.tower
  exact distinct_delta_towers_have_distinct_first_coordinates hDelta

theorem tower_family_bridge_same_first_coordinate_forces_same_delta
    {Source : Type u} (B : TowerFamilyBridge Source) {sourceA sourceB : Source}
    (hCoord : (B.tower sourceA).coord 1 = (B.tower sourceB).coord 1) :
    B.deltaOf sourceA = B.deltaOf sourceB := by
  change (deltaTower (B.deltaOf sourceA)).coord 1 =
    (deltaTower (B.deltaOf sourceB)).coord 1 at hCoord
  exact delta_tower_first_coordinate_injective hCoord

theorem tower_family_bridge_delta_two_iff_first_coordinate_two
    {Source : Type u} (B : TowerFamilyBridge Source) (source : Source) :
    (B.tower source).coord 1 = 2 ↔ B.deltaOf source = 2 := by
  unfold TowerFamilyBridge.tower
  exact delta_tower_is_delta_two_iff_first_coordinate_two (B.deltaOf source)

theorem tower_family_bridge_same_delta_has_same_first_coordinate
    {Source : Type u} (B : TowerFamilyBridge Source) {sourceA sourceB : Source}
    (hDelta : B.deltaOf sourceA = B.deltaOf sourceB) :
    (B.tower sourceA).coord 1 = (B.tower sourceB).coord 1 := by
  rw [tower_family_bridge_first_coordinate B sourceA,
    tower_family_bridge_first_coordinate B sourceB, hDelta]

theorem tower_family_bridge_delta_shadow_collision_blocks_target_decode
    {Source : Type u} {Value : Type v} (B : TowerFamilyBridge Source)
    (target : Source → Value) {sourceA sourceB : Source}
    (hDelta : B.deltaOf sourceA = B.deltaOf sourceB)
    (hTarget : target sourceA ≠ target sourceB) :
    ¬ ∃ decode : Nat → Value,
        ∀ source : Source, decode (B.deltaOf source) = target source := by
  intro h
  rcases h with ⟨decode, hDecode⟩
  have hA := hDecode sourceA
  have hB := hDecode sourceB
  have hDecodeSame :
      decode (B.deltaOf sourceA) = decode (B.deltaOf sourceB) := by
    rw [hDelta]
  have hTargetEq : target sourceA = target sourceB := by
    rw [← hA, ← hB]
    exact hDecodeSame
  exact hTarget hTargetEq

theorem tower_family_bridge_augmented_decode_implies_pair_invariant
    {Source : Type u} {Extra : Type v} {Value : Type w}
    (B : TowerFamilyBridge Source) (extra : Source → Extra)
    (target : Source → Value) (decode : Nat × Extra → Value)
    (hDecode : ∀ source : Source,
      decode (B.deltaOf source, extra source) = target source)
    {sourceA sourceB : Source}
    (hDelta : B.deltaOf sourceA = B.deltaOf sourceB)
    (hExtra : extra sourceA = extra sourceB) :
    target sourceA = target sourceB := by
  have hPair :
      (B.deltaOf sourceA, extra sourceA) =
        (B.deltaOf sourceB, extra sourceB) := by
    exact Prod.ext hDelta hExtra
  rw [← hDecode sourceA, ← hDecode sourceB, hPair]

theorem tower_family_bridge_augmented_collision_blocks_target_decode
    {Source : Type u} {Extra : Type v} {Value : Type w}
    (B : TowerFamilyBridge Source) (extra : Source → Extra)
    (target : Source → Value) {sourceA sourceB : Source}
    (hDelta : B.deltaOf sourceA = B.deltaOf sourceB)
    (hExtra : extra sourceA = extra sourceB)
    (hTarget : target sourceA ≠ target sourceB) :
    ¬ ∃ decode : Nat × Extra → Value,
        ∀ source : Source,
          decode (B.deltaOf source, extra source) = target source := by
  intro h
  rcases h with ⟨decode, hDecode⟩
  exact hTarget
    (tower_family_bridge_augmented_decode_implies_pair_invariant
      B extra target decode hDecode hDelta hExtra)

structure ContinuumSourceClaim where
  namesRiemannHypothesis : Bool
  finiteBridgePacket : Bool
  terminalizedCertifiedTheorem : Bool
  deriving Repr

def ContinuumSourceAdmissible (claim : ContinuumSourceClaim) : Prop :=
  claim.finiteBridgePacket = true ∧ claim.terminalizedCertifiedTheorem = true

def rhSourceClaimWithoutBridge : ContinuumSourceClaim :=
  { namesRiemannHypothesis := true,
    finiteBridgePacket := false,
    terminalizedCertifiedTheorem := false }

theorem rh_source_claim_alone_not_admissible :
    ¬ ContinuumSourceAdmissible rhSourceClaimWithoutBridge := by
  intro hAdmissible
  have hBridge := hAdmissible.1
  change false = true at hBridge
  cases hBridge

theorem continuum_source_admissible_requires_bridge_packet
    (claim : ContinuumSourceClaim) :
    ContinuumSourceAdmissible claim → claim.finiteBridgePacket = true := by
  intro hAdmissible
  exact hAdmissible.1

theorem continuum_source_admissible_requires_certified_terminal
    (claim : ContinuumSourceClaim) :
    ContinuumSourceAdmissible claim →
      claim.terminalizedCertifiedTheorem = true := by
  intro hAdmissible
  exact hAdmissible.2

inductive ContinuumZetaWorld where
  | riemannSource
  | alternateSource
  deriving DecidableEq, Repr

def finiteZetaShadow (_world : ContinuumZetaWorld) : Unit :=
  ()

def namesRhContinuumSource : ContinuumZetaWorld → Bool
  | ContinuumZetaWorld.riemannSource => true
  | ContinuumZetaWorld.alternateSource => false

theorem finite_zeta_shadow_forgets_continuum_source :
    ¬ ∃ F : Unit → Bool,
        ∀ world : ContinuumZetaWorld,
          F (finiteZetaShadow world) = namesRhContinuumSource world := by
  intro h
  rcases h with ⟨F, hF⟩
  have hRh := hF ContinuumZetaWorld.riemannSource
  have hAlt := hF ContinuumZetaWorld.alternateSource
  change F () = true at hRh
  change F () = false at hAlt
  rw [hRh] at hAlt
  cases hAlt

inductive TowerDeltaWorld where
  | deltaTwo
  | deltaThree
  deriving DecidableEq, Repr

def finiteTowerZetaShape (_world : TowerDeltaWorld) : Unit :=
  ()

def isDeltaTwoOutcome : TowerDeltaWorld → Bool
  | TowerDeltaWorld.deltaTwo => true
  | TowerDeltaWorld.deltaThree => false

theorem finite_zeta_shadow_forgets_delta_two_status :
    ¬ ∃ F : Unit → Bool,
        ∀ world : TowerDeltaWorld,
          F (finiteTowerZetaShape world) = isDeltaTwoOutcome world := by
  intro h
  rcases h with ⟨F, hF⟩
  have hTwo := hF TowerDeltaWorld.deltaTwo
  have hThree := hF TowerDeltaWorld.deltaThree
  change F () = true at hTwo
  change F () = false at hThree
  rw [hTwo] at hThree
  cases hThree

inductive RhNamedTowerWorld where
  | rhDeltaTwo
  | rhDeltaThree
  deriving DecidableEq, Repr

def namesRhSourceForTower (_world : RhNamedTowerWorld) : Bool := true

def rhNamedTowerIsDeltaTwo : RhNamedTowerWorld → Bool
  | RhNamedTowerWorld.rhDeltaTwo => true
  | RhNamedTowerWorld.rhDeltaThree => false

theorem rh_source_name_forgets_delta_two_status :
    ¬ ∃ F : Bool → Bool,
        ∀ world : RhNamedTowerWorld,
          F (namesRhSourceForTower world) = rhNamedTowerIsDeltaTwo world := by
  intro h
  rcases h with ⟨F, hF⟩
  have hTwo := hF RhNamedTowerWorld.rhDeltaTwo
  have hThree := hF RhNamedTowerWorld.rhDeltaThree
  change F true = true at hTwo
  change F true = false at hThree
  rw [hTwo] at hThree
  cases hThree

#print axioms SnSymbolGameAndPackets.tower_step_law
#print axioms SnSymbolGameAndPackets.positive_delta_tower_first_coordinate
#print axioms SnSymbolGameAndPackets.positive_delta_tower_has_positive_step
#print axioms SnSymbolGameAndPackets.positive_delta_tower_step_law
#print axioms SnSymbolGameAndPackets.positive_delta_tower_family_injective_first_coordinate
#print axioms SnSymbolGameAndPackets.distinct_positive_delta_towers_have_distinct_first_coordinates
#print axioms SnSymbolGameAndPackets.positive_delta_tower_index_one_is_delta_two
#print axioms SnSymbolGameAndPackets.positive_delta_tower_symbol_game_index_iff_first_coordinate_two
#print axioms SnSymbolGameAndPackets.delta_two_tower_step
#print axioms SnSymbolGameAndPackets.delta_tower_first_coordinate
#print axioms SnSymbolGameAndPackets.delta_tower_first_coordinate_injective
#print axioms SnSymbolGameAndPackets.distinct_delta_towers_have_distinct_first_coordinates
#print axioms SnSymbolGameAndPackets.delta_tower_is_delta_two_iff_first_coordinate_two
#print axioms SnSymbolGameAndPackets.positive_delta_step_strict
#print axioms SnSymbolGameAndPackets.positive_delta_no_terminal_coordinate
#print axioms SnSymbolGameAndPackets.same_base_first_coordinate_equal_forces_delta_equal
#print axioms SnSymbolGameAndPackets.evidence_only_zeta_family_no_authority
#print axioms SnSymbolGameAndPackets.delta_tower_zeta_family_no_authority
#print axioms SnSymbolGameAndPackets.every_delta_has_evidence_only_zeta_family
#print axioms SnSymbolGameAndPackets.every_positive_delta_tower_has_evidence_only_zeta_family
#print axioms SnSymbolGameAndPackets.delta_tower_zeta_family_carrier_first_coordinate
#print axioms SnSymbolGameAndPackets.distinct_delta_zeta_family_carriers_have_distinct_first_coordinates
#print axioms SnSymbolGameAndPackets.delta_tower_zeta_family_delta_two_iff_first_coordinate_two
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_first_coordinate
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_zeta_no_authority
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_distinct_indices_have_distinct_first_coordinates
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_same_first_coordinate_forces_same_index
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_delta_two_iff_index_one
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_same_index_has_same_first_coordinate
#print axioms SnSymbolGameAndPackets.positive_tower_family_bridge_index_collision_blocks_target_decode
#print axioms SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_first_coordinate
#print axioms SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_zeta_no_authority
#print axioms SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_packet_eq
#print axioms SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_decode_implies_packet_invariant
#print axioms SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_collision_blocks_target_decode
#print axioms SnSymbolGameAndPackets.tower_family_bridge_first_coordinate
#print axioms SnSymbolGameAndPackets.tower_family_bridge_zeta_no_authority
#print axioms SnSymbolGameAndPackets.tower_family_bridge_distinct_deltas_have_distinct_first_coordinates
#print axioms SnSymbolGameAndPackets.tower_family_bridge_same_first_coordinate_forces_same_delta
#print axioms SnSymbolGameAndPackets.tower_family_bridge_delta_two_iff_first_coordinate_two
#print axioms SnSymbolGameAndPackets.tower_family_bridge_same_delta_has_same_first_coordinate
#print axioms SnSymbolGameAndPackets.tower_family_bridge_delta_shadow_collision_blocks_target_decode
#print axioms SnSymbolGameAndPackets.tower_family_bridge_augmented_decode_implies_pair_invariant
#print axioms SnSymbolGameAndPackets.tower_family_bridge_augmented_collision_blocks_target_decode
#print axioms SnSymbolGameAndPackets.rh_source_claim_alone_not_admissible
#print axioms SnSymbolGameAndPackets.continuum_source_admissible_requires_bridge_packet
#print axioms SnSymbolGameAndPackets.continuum_source_admissible_requires_certified_terminal
#print axioms SnSymbolGameAndPackets.finite_zeta_shadow_forgets_continuum_source
#print axioms SnSymbolGameAndPackets.finite_zeta_shadow_forgets_delta_two_status
#print axioms SnSymbolGameAndPackets.rh_source_name_forgets_delta_two_status

end SnSymbolGameAndPackets
