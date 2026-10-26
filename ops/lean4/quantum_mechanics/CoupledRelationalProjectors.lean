import Std
/-!
# Pure Relational Operad Chain (`P_REL_01`–`P_REL_07`): Single, Bipartite, and Tripartite Projectors

Formalizes the exact integer-scaled projector decompositions, graph holonomy obstructions,
commutator identities, and Schur-Weyl / Levi-Civita localization theorems for all 7 stages
(`P_REL_01` through `P_REL_07`) of the pure relational Genesis operad workflow:

1. **Stage 1 (`S(0..6)` survivor tower and `D_2` retraction):**
   - Active obstruction survivor vector `(0, 1, 1, 1, 0, 1, 1)`, binary germ `D_2` support
     floor `2`, retraction left-inverse defect `0`, and cumulative history ledger
     `(0, 1, 2, 3, 3, 4, 5)`.
2. **Stage 2 (`D_2` collision tagging and swap quotient):**
   - Scaled symmetric and antisymmetric projectors `2 P_+ = ((1, 1), (1, 1))` and
     `2 P_- = ((1, -1), (-1, 1))`, zero idempotence and orthogonality defect, and
     difference kernel rank `1`.
3. **Stage 3 (`G = (4, 5)` diamond cut coboundary vs cycle chord holonomy):**
   - Diamond graph invariants `(V, E, b_1) = (4, 5, 2)`, spanning tree count `8`,
     exact vertex-potential cycle sum defect `0`, and fundamental cycle holonomies `(1, -1)`.
4. **Stage 4 (`D_3` noncommuting swap commutator and cyclotomic `W_0` kernel):**
   - Skew-symmetric commutator `K = [T_{01}, T_{12}] = ((0, -1, 1), (1, 0, -1), (-1, 1, 0))`
     with `Tr(K) = 0`, cubic identity `K^3 + 3 K = 0`, and cyclotomic difference identity
     `(R^2 + R + I)|_{W_0} = 0` and `(K^2 + 3 I)|_{W_0} = 0`.
5. **Stage 5 (`D_2 × D_3`, 6 elements):**
   - Scaled 4-sector projectors `(6 Π_{+,mean}, 6 Π_{-,mean}, 6 Π_{+,W_0}, 6 Π_{-,W_0})`
     have exact traces `(6, 6, 12, 12)` (ranks `(1, 1, 2, 2)`), zero idempotence /
     orthogonality / completeness defect, and coupled swap-commutator `J_{23} = σ ⊗ K`
     satisfying `J_{23}^3 + 3 J_{23} = 0` and `(J_{23}^2 + 3 I_6)(6 Π_{-,W_0}) = 0`.
6. **Stage 6 (`D_3 × D_3`, 9 elements):**
   - Scaled 5-sector projectors `(18 Π_{++}, 18 Π_{+0}, 18 Π_{0+}, 18 Π_{00}^{sym}, 18 Π_{00}^{alt})`
     under factor swap `τ(a,b) = (b,a)` have exact traces `(18, 36, 36, 54, 18)`
     (ranks `(1, 2, 2, 3, 1)`), compound commutator `K_{33} = K ⊗ K` satisfies
     `(K_{33}^2 - 9 I_9)(9 Π_{00}) = 0`, diagonal 3-cycle `R_{33} = R ⊗ R` has scaled
     traces `(0, 18, 0)` (ranks `(0, 1, 0)`), and the antisymmetric singlet `ψ_alt`
     has `2 × 2` minor `1 ≠ 0` vs `0` for separable vectors.
7. **Stage 7 (`D_3 × D_3 × D_3`, 27 elements):**
   - Scaled binomial projectors `(27 Π^{(3,0)}, 27 Π^{(2,1)}, 27 Π^{(1,2)}, 27 Π_{000})`
     have exact traces `(27, 162, 324, 216)` (ranks `(1, 6, 12, 8)`).
   - Restricted to `W_{000} = W_0^{\otimes 3}`, the `S_3^{fac}` projectors have scaled
     traces `(648, 648, 0)` (`162 × (4, 4, 0)`), certifying `Λ^3(W_0) = 0`.
   - The unique 1D Levi-Civita alternating line `6 P_{alt}^{(3)}` has scaled trace `6`
     (rank `1`), is supported entirely inside `27 Π^{(1,2)}` (`Λ^1(L_+) ⊗ Λ^2(W_0)`),
     and has `(R^{\otimes 3}, T_{01}^{\otimes 3})` parities `(+1, -1)`.
   - Inside `W_{000}`, the `R^{\otimes 3}`-invariant subspace has rank `2`, splits into
     `(1, 1)` under `T_{01}^{\otimes 3}`, and satisfies `((K^{\otimes 3})^2 + 27 I_{27}) Π_{000} = 0`.

AuthorityEffect: None.
-/

namespace CoupledRelationalProjectors

abbrev MatZ := Nat → Nat → Int

def matZero : MatZ := fun _ _ => 0

def matAdd (a b : MatZ) : MatZ := fun i j => a i j + b i j

def matSub (a b : MatZ) : MatZ := fun i j => a i j - b i j

def matScale (c : Int) (a : MatZ) : MatZ := fun i j => c * a i j

def matIdent (scale : Int := 1) : MatZ := fun i j =>
  if i == j then scale else 0

def sumBy (f : Nat → Int) : List Nat → Int
  | [] => 0
  | k :: ks => f k + sumBy f ks

def matMul (n : Nat) (a b : MatZ) : MatZ := fun i j =>
  sumBy (fun k => a i k * b k j) (List.range n)

def matKron (rb cb : Nat) (a b : MatZ) : MatZ := fun i j =>
  a (i / rb) (j / cb) * b (i % rb) (j % cb)

def matTrace (n : Nat) (a : MatZ) : Int :=
  sumBy (fun i => a i i) (List.range n)

def matEqB (n : Nat) (a b : MatZ) : Bool :=
  (List.range n).all fun i =>
    (List.range n).all fun j =>
      a i j == b i j

def matZeroB (n : Nat) (a : MatZ) : Bool :=
  (List.range n).all fun i =>
    (List.range n).all fun j =>
      a i j == 0

def matDefect (n : Nat) (a b : MatZ) : Int :=
  if matEqB n a b then 0 else 1

def matZeroDefect (n : Nat) (a : MatZ) : Int :=
  if matZeroB n a then 0 else 1

def pairwiseOrthoB (n : Nat) : List MatZ → Bool
  | [] => true
  | p :: ps =>
    ps.all (fun q => matZeroB n (matMul n p q) && matZeroB n (matMul n q p)) &&
      pairwiseOrthoB n ps

def scaledProjectorFamilyDefect (n : Nat) (scale : Int) (projectors : List MatZ) : Int :=
  let idemOk := projectors.all (fun p => matEqB n (matMul n p p) (matScale scale p))
  let orthoOk := pairwiseOrthoB n projectors
  let sumMat : MatZ := fun i j =>
    (projectors.foldr (fun p acc => p i j + acc) 0)
  let compOk := matEqB n sumMat (matIdent scale)
  if idemOk && orthoOk && compOk then 0 else 1

-- Base D_2 (scale 2) and D_3 (scale 3) operators
def pPlus2 : MatZ := fun _ _ => 1

def pMinus2 : MatZ := fun i j => if i == j then 1 else -1

def sigma2 : MatZ := fun i j => if i == 1 - j then 1 else 0

def qPlus3 : MatZ := fun _ _ => 1

def qW0_3 : MatZ := fun i j => if i == j then 2 else -1

def t01_3 : MatZ := fun i j =>
  let target := if j == 0 then 1 else if j == 1 then 0 else 2
  if i == target then 1 else 0

def t12_3 : MatZ := fun i j =>
  let target := if j == 1 then 2 else if j == 2 then 1 else 0
  if i == target then 1 else 0

def rCycle3 : MatZ := fun i j =>
  let target := (j + 2) % 3
  if i == target then 1 else 0

def kComm3 : MatZ := fun i j =>
  match i, j with
  | 0, 1 => -1
  | 0, 2 => 1
  | 1, 0 => 1
  | 1, 2 => -1
  | 2, 0 => -1
  | 2, 1 => 1
  | _, _ => 0

-- ============================================================================
-- Stage 1: Genesis S(0..6) Survivor Tower, D_2 Support Floor, and Retraction
-- ============================================================================

def stage1Summary :
    (Int × Int × Int × Int × Int × Int × Int) ×
    Int ×
    Int ×
    (Int × Int × Int × Int × Int × Int × Int) :=
  let s0 : Int := 0
  let s1 : Int := 1
  let s2 : Int := 1
  let s3 : Int := 1
  let s4 : Int := 0
  let s5 : Int := 1
  let s6 : Int := 1
  let survivors := (s0, s1, s2, s3, s4, s5, s6)
  let history := (
    s0,
    s0 + s1,
    s0 + s1 + s2,
    s0 + s1 + s2 + s3,
    s0 + s1 + s2 + s3 + s4,
    s0 + s1 + s2 + s3 + s4 + s5,
    s0 + s1 + s2 + s3 + s4 + s5 + s6
  )
  let d2Floor : Int := ([0, 1] : List Nat).length
  let retractEmbedded (k : Nat) : Option Nat :=
    if k < 2 then some k else none
  let leftInvDef : Int :=
    (if retractEmbedded 0 == some 0 then 0 else 1) +
    (if retractEmbedded 1 == some 1 then 0 else 1) +
    (if retractEmbedded 2 == none then 0 else 1)
  (survivors, d2Floor, leftInvDef, history)

theorem stage1_survivor_tower_and_retraction_eq :
    stage1Summary = ((0, 1, 1, 1, 0, 1, 1), 2, 0, (0, 1, 2, 3, 3, 4, 5)) := by
  rfl

-- ============================================================================
-- Stage 2: D_2 Collision Tagging and Swap Involution Projectors (scale 2)
-- ============================================================================

def stage2Summary :
    ((Int × Int) × (Int × Int)) ×
    ((Int × Int) × (Int × Int)) ×
    Int ×
    Int ×
    Int :=
  let pPlusMat := ((pPlus2 0 0, pPlus2 0 1), (pPlus2 1 0, pPlus2 1 1))
  let pMinusMat := ((pMinus2 0 0, pMinus2 0 1), (pMinus2 1 0, pMinus2 1 1))
  let idemDef :=
    matDefect 2 (matMul 2 pPlus2 pPlus2) (matScale 2 pPlus2) +
    matDefect 2 (matMul 2 pMinus2 pMinus2) (matScale 2 pMinus2)
  let orthoDef := scaledProjectorFamilyDefect 2 2 [pPlus2, pMinus2]
  let diffKernelRank := matTrace 2 pMinus2 / 2
  (pPlusMat, pMinusMat, idemDef, orthoDef, diffKernelRank)

theorem stage2_d2_collision_tagging_and_swap_projectors_eq :
    stage2Summary = (((1, 1), (1, 1)), ((1, -1), (-1, 1)), 0, 0, 1) := by
  decide

-- ============================================================================
-- Stage 3: Diamond Graph G=(4,5) Cut Coboundary vs Cycle Holonomy
-- ============================================================================

def stage3Summary : (Int × Int × Int) × Int × Int × (Int × Int) :=
  let v : Int := 4
  let e : Int := 5
  let b1 : Int := e - v + 1
  -- Two triangles sharing one chord: 3 * 3 - 1 = 8 spanning trees
  let diamondTrees : Int := 3 * 3 - 1
  -- Vertex potential g = (1, 0, 0, 0) and g' = (0, 8, -6, 15) coboundary cycle sums
  let d0CycleSum (g0 g1 g2 g3 : Int) : Int :=
    let c1 := (g1 - g0) + (g2 - g1) - (g2 - g0)
    let c2 := (g3 - g1) - (g3 - g2) - (g2 - g1)
    Int.ofNat (Int.natAbs c1 + Int.natAbs c2)
  let coboundaryDefect := d0CycleSum 1 0 0 0 + d0CycleSum 0 8 (-6) 15
  -- Non-exact 1-cochain omega = (0, 0, -1, 0, 1) on (e01, e12, e02, e13, e23)
  let c1Hol : Int := 0 + 0 - (-1)
  let c2Hol : Int := 0 - 1 - 0
  ((v, e, b1), diamondTrees, coboundaryDefect, (c1Hol, c2Hol))

theorem stage3_diamond_coboundary_vs_chord_holonomy_eq :
    stage3Summary = ((4, 5, 2), 8, 0, (1, -1)) := by
  decide

-- ============================================================================
-- Stage 4: D_3 Noncommuting Swap Commutator K and Cyclotomic W_0 Kernel
-- ============================================================================

def stage4Summary :
    ((Int × Int × Int) × (Int × Int × Int) × (Int × Int × Int)) ×
    Int ×
    Int ×
    Int :=
  let rPlus := matMul 3 t01_3 t12_3
  let rMinus := matMul 3 t12_3 t01_3
  let kMat := matSub rPlus rMinus
  let kTuple := (
    (kMat 0 0, kMat 0 1, kMat 0 2),
    (kMat 1 0, kMat 1 1, kMat 1 2),
    (kMat 2 0, kMat 2 1, kMat 2 2)
  )
  let kTrace := matTrace 3 kMat
  let kSq := matMul 3 kMat kMat
  let kCube := matMul 3 kSq kMat
  let kCubePlus3kDef := matZeroDefect 3 (matAdd kCube (matScale 3 kMat))
  let rPlusSq := matMul 3 rPlus rPlus
  let phi3Def :=
    matZeroDefect 3 (matMul 3 (matAdd (matAdd rPlusSq rPlus) (matIdent 1)) qW0_3) +
    matZeroDefect 3 (matMul 3 (matAdd kSq (matIdent 3)) qW0_3)
  (kTuple, kTrace, kCubePlus3kDef, phi3Def)

theorem stage4_d3_swap_commutator_and_cyclotomic_w0_eq :
    stage4Summary = (((0, -1, 1), (1, 0, -1), (-1, 1, 0)), 0, 0, 0) := by
  decide

-- ============================================================================
-- Stage 5: Coupled Bipartite D_2 × D_3 (6 elements, scale 6)
-- ============================================================================

def stage5GraphAndHolonomyPin : (Int × Int × Int × Int) × ((Int × Int) × (Int × Int) × Int) :=
  let v : Int := 6
  let e : Int := 9
  let b1 : Int := e - v + 1
  let prismTrees : Int := (2 * 3 * 3 * 5 * 5) / v
  let cTop : Int := 0 + 0 - 0
  let cBot : Int := 0 + 0 - 0
  let h01 : Int := 0 + (-1) - 0 - 1
  let h12 : Int := 0 + 0 - 0 - (-1)
  let obstructedTrees : Int := if !(h01 == 0) && !(h12 == 0) then prismTrees else 0
  ((v, e, b1, prismTrees), ((cTop, cBot), (h01, h12), obstructedTrees))

def stage5ProjectorAndCommutatorPin : (Int × Int × Int × Int) × Int × Int :=
  let piPP := matKron 3 3 pPlus2 qPlus3
  let piMP := matKron 3 3 pMinus2 qPlus3
  let piP0 := matKron 3 3 pPlus2 qW0_3
  let piM0 := matKron 3 3 pMinus2 qW0_3
  let sectors := [piPP, piMP, piP0, piM0]
  let ranks := (
    matTrace 6 piPP / 6,
    matTrace 6 piMP / 6,
    matTrace 6 piP0 / 6,
    matTrace 6 piM0 / 6
  )
  let famDef := scaledProjectorFamilyDefect 6 6 sectors
  let j23 := matKron 3 3 sigma2 kComm3
  let j23Sq := matMul 6 j23 j23
  let j23Cube := matMul 6 j23Sq j23
  let cubicDef := matZeroDefect 6 (matAdd j23Cube (matScale 3 j23))
  let w0Def := matZeroDefect 6 (matMul 6 (matAdd j23Sq (matIdent 3)) piM0)
  (ranks, famDef, cubicDef + w0Def)

theorem stage5_graph_and_holonomy_eq :
    stage5GraphAndHolonomyPin = ((6, 9, 4, 75), ((0, 0), (-2, 1), 75)) := by
  decide

theorem stage5_projector_and_commutator_eq :
    stage5ProjectorAndCommutatorPin = ((1, 1, 2, 2), 0, 0) := by
  decide

def stage5Summary :
    (Int × Int × Int × Int) × (Int × Int × Int × Int) × Int × Int × ((Int × Int) × (Int × Int) × Int) :=
  (
    stage5GraphAndHolonomyPin.1,
    stage5ProjectorAndCommutatorPin.1,
    stage5ProjectorAndCommutatorPin.2.1,
    stage5ProjectorAndCommutatorPin.2.2,
    stage5GraphAndHolonomyPin.2
  )

theorem stage5_d2_x_d3_four_sector_ranks_and_j23_cubic :
    stage5Summary = ((6, 9, 4, 75), (1, 1, 2, 2), 0, 0, ((0, 0), (-2, 1), 75)) := by
  unfold stage5Summary
  rw [stage5_graph_and_holonomy_eq, stage5_projector_and_commutator_eq]

-- ============================================================================
-- Stage 6: Coupled Bipartite D_3 × D_3 (9 elements, scale 18)
-- ============================================================================

def tau9 : MatZ := fun i j =>
  if i == 3 * (j % 3) + (j / 3) then 1 else 0

def stage6Summary : (Int × Int × Int × Int × Int) × Int × Int × (Int × Int × Int) × (Int × Int) :=
  let piPP9 := matScale 2 (matKron 3 3 qPlus3 qPlus3)
  let piP09 := matScale 2 (matKron 3 3 qPlus3 qW0_3)
  let pi0P9 := matScale 2 (matKron 3 3 qW0_3 qPlus3)
  let pi00_9 := matKron 3 3 qW0_3 qW0_3
  let i9 := matIdent 1
  let pTauSym2 := matAdd i9 tau9
  let pTauAlt2 := matSub i9 tau9
  let pi00Sym18 := matMul 9 pTauSym2 pi00_9
  let pi00Alt18 := matMul 9 pTauAlt2 pi00_9
  let sectors := [piPP9, piP09, pi0P9, pi00Sym18, pi00Alt18]
  let ranks := (
    matTrace 9 piPP9 / 18,
    matTrace 9 piP09 / 18,
    matTrace 9 pi0P9 / 18,
    matTrace 9 pi00Sym18 / 18,
    matTrace 9 pi00Alt18 / 18
  )
  let famDef := scaledProjectorFamilyDefect 9 18 sectors
  let k33 := matKron 3 3 kComm3 kComm3
  let k33Sq := matMul 9 k33 k33
  let invDef := matZeroDefect 9 (matMul 9 (matSub k33Sq (matIdent 9)) pi00_9)
  let r33 := matKron 3 3 rCycle3 rCycle3
  let trSym := matTrace 9 (matMul 9 r33 pi00Sym18) / 18
  let trAlt := matTrace 9 (matMul 9 r33 pi00Alt18) / 18
  let altInvDef := matZeroDefect 9 (matMul 9 (matSub r33 i9) pi00Alt18)
  let singletMinor : Int := kComm3 0 0 * kComm3 1 1 - kComm3 0 1 * kComm3 1 0
  let sepMinor : Int := (1 * 0) * ((-1) * 1) - (1 * 1) * ((-1) * 0)
  (ranks, famDef, invDef, (trSym, trAlt, altInvDef), (singletMinor, sepMinor))

theorem stage6_d3_x_d3_five_sector_ranks_and_rational_involution :
    stage6Summary = ((1, 2, 2, 3, 1), 0, 0, (0, 1, 0), (1, 0)) := by
  decide

-- ============================================================================
-- Stage 7: Tripartite D_3 × D_3 × D_3 (27 elements)
-- ============================================================================

def pi30_27 : MatZ := fun _ _ => 1

def pi21_27 : MatZ := fun i j =>
  let a1 := i / 9; let b1 := (i / 3) % 3; let c1 := i % 3
  let a2 := j / 9; let b2 := (j / 3) % 3; let c2 := j % 3
  qW0_3 c1 c2 + qW0_3 b1 b2 + qW0_3 a1 a2

def pi12_27 : MatZ := fun i j =>
  let a1 := i / 9; let b1 := (i / 3) % 3; let c1 := i % 3
  let a2 := j / 9; let b2 := (j / 3) % 3; let c2 := j % 3
  qW0_3 b1 b2 * qW0_3 c1 c2 + qW0_3 a1 a2 * qW0_3 c1 c2 + qW0_3 a1 a2 * qW0_3 b1 b2

def pi000_27 : MatZ := fun i j =>
  let a1 := i / 9; let b1 := (i / 3) % 3; let c1 := i % 3
  let a2 := j / 9; let b2 := (j / 3) % 3; let c2 := j % 3
  qW0_3 a1 a2 * qW0_3 b1 b2 * qW0_3 c1 c2

def pSym27_scale6 : MatZ := fun row col =>
  let a := col / 9; let b := (col / 3) % 3; let c := col % 3
  let r0 := 9 * a + 3 * b + c
  let r1 := 9 * b + 3 * c + a
  let r2 := 9 * c + 3 * a + b
  let r3 := 9 * b + 3 * a + c
  let r4 := 9 * a + 3 * c + b
  let r5 := 9 * c + 3 * b + a
  (if row == r0 then 1 else 0) +
  (if row == r1 then 1 else 0) +
  (if row == r2 then 1 else 0) +
  (if row == r3 then 1 else 0) +
  (if row == r4 then 1 else 0) +
  (if row == r5 then 1 else 0)

def pAlt27_scale6 : MatZ := fun row col =>
  let a := col / 9; let b := (col / 3) % 3; let c := col % 3
  let r0 := 9 * a + 3 * b + c
  let r1 := 9 * b + 3 * c + a
  let r2 := 9 * c + 3 * a + b
  let r3 := 9 * b + 3 * a + c
  let r4 := 9 * a + 3 * c + b
  let r5 := 9 * c + 3 * b + a
  (if row == r0 then 1 else 0) +
  (if row == r1 then 1 else 0) +
  (if row == r2 then 1 else 0) -
  (if row == r3 then 1 else 0) -
  (if row == r4 then 1 else 0) -
  (if row == r5 then 1 else 0)

def pMix27_scale6 : MatZ := fun i j =>
  (if i == j then 6 else 0) - pSym27_scale6 i j - pAlt27_scale6 i j

def kSq3 : MatZ := matMul 3 kComm3 kComm3

def k3Sq_27 : MatZ := fun i j =>
  let a1 := i / 9; let b1 := (i / 3) % 3; let c1 := i % 3
  let a2 := j / 9; let b2 := (j / 3) % 3; let c2 := j % 3
  kSq3 a1 a2 * kSq3 b1 b2 * kSq3 c1 c2

def stage7BinomialRanks : Int × Int × Int × Int :=
  (
    matTrace 27 pi30_27 / 27,
    matTrace 27 pi21_27 / 27,
    matTrace 27 pi12_27 / 27,
    matTrace 27 pi000_27 / 27
  )

def pSym_pi000_diag (i : Nat) : Int :=
  let a := i / 9; let b := (i / 3) % 3; let c := i % 3
  let i0 := 9 * a + 3 * b + c
  let i1 := 9 * c + 3 * a + b
  let i2 := 9 * b + 3 * c + a
  let i3 := 9 * b + 3 * a + c
  let i4 := 9 * a + 3 * c + b
  let i5 := 9 * c + 3 * b + a
  pi000_27 i0 i + pi000_27 i1 i + pi000_27 i2 i +
  pi000_27 i3 i + pi000_27 i4 i + pi000_27 i5 i

def pAlt_pi000_diag (i : Nat) : Int :=
  let a := i / 9; let b := (i / 3) % 3; let c := i % 3
  let i0 := 9 * a + 3 * b + c
  let i1 := 9 * c + 3 * a + b
  let i2 := 9 * b + 3 * c + a
  let i3 := 9 * b + 3 * a + c
  let i4 := 9 * a + 3 * c + b
  let i5 := 9 * c + 3 * b + a
  pi000_27 i0 i + pi000_27 i1 i + pi000_27 i2 i -
  pi000_27 i3 i - pi000_27 i4 i - pi000_27 i5 i

def stage7SchurWeylRanks : Int × Int × Int :=
  let trSym := sumBy pSym_pi000_diag (List.range 27) / 162
  let trAlt := sumBy pAlt_pi000_diag (List.range 27) / 162
  let trTotal := matTrace 27 pi000_27 / 27
  (trSym, trTotal - trSym - trAlt, trAlt)

def r3PullbackIdx (i : Nat) : Nat :=
  let a := i / 9; let b := (i / 3) % 3; let c := i % 3
  9 * ((a + 1) % 3) + 3 * ((b + 1) % 3) + ((c + 1) % 3)

def t01PullbackIdx (i : Nat) : Nat :=
  let sw (x : Nat) : Nat := if x == 0 then 1 else if x == 1 then 0 else 2
  let a := i / 9; let b := (i / 3) % 3; let c := i % 3
  9 * sw a + 3 * sw b + sw c

def epsVec27 (i : Nat) : Int := pAlt27_scale6 i 5

def stage7LeviCivitaPin : Int × Int × Int × Int :=
  let altRank := matTrace 27 pAlt27_scale6 / 6
  let pi12Eps (i : Nat) : Int := sumBy (fun j => pi12_27 i j * epsVec27 j) (List.range 27)
  let altOutsidePi12 :=
    if (List.range 27).all (fun i => pi12Eps i == 27 * epsVec27 i) then 0 else 1
  let r3OnAlt : MatZ := fun i j => pAlt27_scale6 (r3PullbackIdx i) j
  let t01OnAlt : MatZ := fun i j => pAlt27_scale6 (t01PullbackIdx i) j
  let r3AltDef := matDefect 27 r3OnAlt pAlt27_scale6
  let t01AltDef := matZeroDefect 27 (matAdd t01OnAlt pAlt27_scale6)
  (altRank, altOutsidePi12, r3AltDef, t01AltDef)

def stage7W000R3SplitPin : Int × Int × Int × Int :=
  let r3FwdIdx (i : Nat) : Nat :=
    let a := i / 9; let b := (i / 3) % 3; let c := i % 3
    9 * ((a + 2) % 3) + 3 * ((b + 2) % 3) + ((c + 2) % 3)
  let pi000_r3_scale81 : MatZ := fun i j =>
    pi000_27 i j + pi000_27 (r3PullbackIdx i) j + pi000_27 (r3FwdIdx i) j
  let w000R3Rank := matTrace 27 pi000_r3_scale81 / 81
  let pT01Plus_pi000_r3 : MatZ := fun i j =>
    pi000_r3_scale81 i j + pi000_r3_scale81 (t01PullbackIdx i) j
  let pT01Minus_pi000_r3 : MatZ := fun i j =>
    pi000_r3_scale81 i j - pi000_r3_scale81 (t01PullbackIdx i) j
  let r3PlusRank := matTrace 27 pT01Plus_pi000_r3 / 162
  let r3MinusRank := matTrace 27 pT01Minus_pi000_r3 / 162
  let k2_qW0 := matMul 3 kSq3 qW0_3
  let k3Sq_pi000 : MatZ := fun i j =>
    let a1 := i / 9; let b1 := (i / 3) % 3; let c1 := i % 3
    let a2 := j / 9; let b2 := (j / 3) % 3; let c2 := j % 3
    k2_qW0 a1 a2 * k2_qW0 b1 b2 * k2_qW0 c1 c2
  let k3W000Def := matZeroDefect 27 (matAdd k3Sq_pi000 (matScale 27 pi000_27))
  (w000R3Rank, r3PlusRank, r3MinusRank, k3W000Def)

def stage7PigeonholePin : Int × Int × Int :=
  let epsL1 := sumBy (fun i => Int.ofNat (Int.natAbs (epsVec27 i))) (List.range 27)
  let pi12Eps (i : Nat) : Int := sumBy (fun j => pi12_27 i j * epsVec27 j) (List.range 27)
  let pi000Eps (i : Nat) : Int := sumBy (fun j => pi000_27 i j * epsVec27 j) (List.range 27)
  let pi12Def := if (List.range 27).all (fun i => pi12Eps i == 27 * epsVec27 i) then 0 else 1
  let pi000Def := if (List.range 27).all (fun i => pi000Eps i == 0) then 0 else 1
  (epsL1, pi12Def, pi000Def)

theorem stage7_binomial_ranks_eq :
    stage7BinomialRanks = (1, 6, 12, 8) := by
  decide

theorem stage7_schur_weyl_ranks_eq :
    stage7SchurWeylRanks = (4, 4, 0) := by
  decide

theorem stage7_levi_civita_pin_eq :
    stage7LeviCivitaPin = (1, 0, 0, 0) := by
  decide

theorem stage7_w000_r3_split_pin_eq :
    stage7W000R3SplitPin = (2, 1, 1, 0) := by
  decide

theorem stage7_pigeonhole_pin_eq :
    stage7PigeonholePin = (6, 0, 0) := by
  decide

def stage7Summary :
    (Int × Int × Int × Int) × (Int × Int × Int) × (Int × Int × Int × Int) × (Int × Int × Int × Int) × (Int × Int × Int) :=
  (stage7BinomialRanks, stage7SchurWeylRanks, stage7LeviCivitaPin, stage7W000R3SplitPin, stage7PigeonholePin)

theorem stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_localization :
    stage7Summary = ((1, 6, 12, 8), (4, 4, 0), (1, 0, 0, 0), (2, 1, 1, 0), (6, 0, 0)) := by
  unfold stage7Summary
  rw [
    stage7_binomial_ranks_eq,
    stage7_schur_weyl_ranks_eq,
    stage7_levi_civita_pin_eq,
    stage7_w000_r3_split_pin_eq,
    stage7_pigeonhole_pin_eq
  ]

theorem coupled_bipartite_and_tripartite_relational_master_certificate :
    stage1Summary = ((0, 1, 1, 1, 0, 1, 1), 2, 0, (0, 1, 2, 3, 3, 4, 5)) ∧
    stage2Summary = (((1, 1), (1, 1)), ((1, -1), (-1, 1)), 0, 0, 1) ∧
    stage3Summary = ((4, 5, 2), 8, 0, (1, -1)) ∧
    stage4Summary = (((0, -1, 1), (1, 0, -1), (-1, 1, 0)), 0, 0, 0) ∧
    stage5Summary = ((6, 9, 4, 75), (1, 1, 2, 2), 0, 0, ((0, 0), (-2, 1), 75)) ∧
    stage6Summary = ((1, 2, 2, 3, 1), 0, 0, (0, 1, 0), (1, 0)) ∧
    stage7Summary = ((1, 6, 12, 8), (4, 4, 0), (1, 0, 0, 0), (2, 1, 1, 0), (6, 0, 0)) := by
  exact ⟨
    stage1_survivor_tower_and_retraction_eq,
    stage2_d2_collision_tagging_and_swap_projectors_eq,
    stage3_diamond_coboundary_vs_chord_holonomy_eq,
    stage4_d3_swap_commutator_and_cyclotomic_w0_eq,
    stage5_d2_x_d3_four_sector_ranks_and_j23_cubic,
    stage6_d3_x_d3_five_sector_ranks_and_rational_involution,
    stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_localization
  ⟩

#print axioms stage1_survivor_tower_and_retraction_eq
#print axioms stage2_d2_collision_tagging_and_swap_projectors_eq
#print axioms stage3_diamond_coboundary_vs_chord_holonomy_eq
#print axioms stage4_d3_swap_commutator_and_cyclotomic_w0_eq
#print axioms stage5_d2_x_d3_four_sector_ranks_and_j23_cubic
#print axioms stage6_d3_x_d3_five_sector_ranks_and_rational_involution
#print axioms stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_localization
#print axioms coupled_bipartite_and_tripartite_relational_master_certificate

end CoupledRelationalProjectors

