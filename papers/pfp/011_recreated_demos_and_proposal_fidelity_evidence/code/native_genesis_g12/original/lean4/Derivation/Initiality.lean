import Derivation.Constitution
import Derivation.NoOutside

/-!
# Ultra closure, Stage VII: minimality in a declared comparison class

The comparison class is exact and finite: the 64-member constitution
family of `Constitution.ConstitutionDesc`, each member executed by the
fixed family interpreter.  Morphisms are simulation maps commuting
with the step on shared events (the panel extension's projection is
the worked example).  Compliance is a declared, decidable probe
battery: one probe per guard, each probing the property the sealed
kernel proves as a theorem —

1. dedup-inertia (repeat admission is silent);
2. requirement well-formedness at admission;
3. acceptance preservation (no accepted mark breaks a satisfied
   requirement);
4. the budget gate;
5. the license gate;
6. certificate-bearing refusal.

Results:

* each guard is load-bearing — switching any one off violates its
  probe (six separation theorems, each a concrete countermodel);
* the sealed kernel's description is the *unique* member of the class
  passing the battery (`unique_compliant`), and its execution is
  exactly the sealed step (`Constitution.interp_describe`), whose full
  properties are the sealed theorems;
* under both declared cost orders (enabled-guard count; lexicographic
  guards-then-gates), the unique compliant member is trivially the
  minimum — the orders cannot disagree on a singleton;
* the panel-extended kernel of `NoOutside` retracts onto the sealed
  kernel: the projection is a simulation for every base event and
  every base history (`extension_retract`, `extension_retract_replay`)
  — a conservative-retract instance of the initiality property, in
  class.

Scope, stated exactly: minimality and initiality are proved **relative
to this declared class and probe battery**.  No claim is made that the
kernel is minimal in any wider, undeclared class; the paper records
this as the boundary of the "most primitive engine" question.
-/

namespace Initiality

open Represented Constitution

/-! ## Probe worlds -/

def dupWorld : World :=
  { data := [5], views := [], reqs := [], refusals := [],
    budget := 9, augLicensed := true, notes := [] }

def satWorld : World :=
  { data := [10, 20], views := [[0]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

def brokeWorld : World :=
  { data := [10, 20], views := [[]], reqs := [(0, 1)],
    refusals := [], budget := 0, augLicensed := true, notes := [] }

def unlicensedWorld : World :=
  { data := [10, 20], views := [[]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := false, notes := [] }

/-! ## The probe battery (declared, decidable) -/

def probeDedup (d : ConstitutionDesc) : Bool :=
  interpStep d dupWorld (.admitTok 5) == dupWorld

def probeRequire (d : ConstitutionDesc) : Bool :=
  interpStep d dupWorld (.require 0 0) == dupWorld

def probeAccept (d : ConstitutionDesc) : Bool :=
  interpStep d satWorld (.mark [0] 1) == satWorld

def probeBudget (d : ConstitutionDesc) : Bool :=
  interpStep d brokeWorld (.mark [] 0) == brokeWorld

def probeLicense (d : ConstitutionDesc) : Bool :=
  interpStep d unlicensedWorld (.addView [0]) == unlicensedWorld

def probeRefusal (d : ConstitutionDesc) : Bool :=
  interpStep d satWorld (.refuse 0 1) == satWorld

def compliantB (d : ConstitutionDesc) : Bool :=
  probeDedup d && probeRequire d && probeAccept d && probeBudget d
    && probeLicense d && probeRefusal d

/-! ## The six load-bearing separations

Each guard, switched off alone, violates its probe: a concrete
countermodel per guard.  (The probes are calibrated on the sealed
kernel: `interp_describe` + the sealed theorems say the all-on member
passes each one; the checks below are decidable instances.) -/

theorem dedup_load_bearing :
    probeDedup { kernelDesc with dedupAdmit := false } = false ∧
      probeDedup kernelDesc = true := by decide

theorem require_guard_load_bearing :
    probeRequire { kernelDesc with guardRequire := false } = false ∧
      probeRequire kernelDesc = true := by decide

theorem accept_guard_load_bearing :
    probeAccept { kernelDesc with guardAccept := false } = false ∧
      probeAccept kernelDesc = true := by decide

theorem budget_gate_load_bearing :
    probeBudget { kernelDesc with gateBudget := false } = false ∧
      probeBudget kernelDesc = true := by decide

theorem license_gate_load_bearing :
    probeLicense { kernelDesc with gateLicense := false } = false ∧
      probeLicense kernelDesc = true := by decide

theorem refusal_certificate_load_bearing :
    probeRefusal { kernelDesc with certRefusal := false } = false ∧
      probeRefusal kernelDesc = true := by decide

/-! ## Uniqueness in class -/

/-- **The sealed kernel is the unique compliant member of the declared
64-member constitution class.**  Exhaustive: the filter of the
complete enumeration is exactly the kernel's description. -/
theorem unique_compliant :
    allDescs.filter compliantB = [kernelDesc] := by decide

/-- Minimality under both declared cost orders is immediate: the
compliant set is a singleton, so the enabled-guard count order and the
lexicographic order select the same, unique member.  (Stated as the
filter identity above; the two orders are computed and compared in the
Python mirror, where the class is also re-checked exhaustively.) -/
theorem minimum_unique_in_class :
    ∀ d ∈ allDescs.filter compliantB, d = kernelDesc := by
  intro d hd
  rw [unique_compliant] at hd
  cases hd with
  | head => rfl
  | tail _ h => cases h

/-! ## The retract half of initiality, in class

The panel-extended kernel (`NoOutside.CWorld`) is a compliant
extension; its projection onto the sealed kernel commutes with every
base event and every base history: the sealed kernel is a
conservative retract of the extension.  Together with uniqueness in
the constitution class this is the exact initiality content proved:
unique minimum in the declared class, retract of the declared
extension — nothing wider. -/

theorem extension_retract (cw : NoOutside.CWorld) (e : Event) :
    (NoOutside.stepC cw (.base e)).base = step cw.base e := rfl

theorem extension_retract_replay (h : List Event) :
    ∀ cw : NoOutside.CWorld,
      (NoOutside.replayC (h.map .base) cw).base = replay h cw.base := by
  induction h with
  | nil => intro cw; rfl
  | cons e rest ih =>
      intro cw
      exact ih (NoOutside.stepC cw (.base e))

/-- The section: injecting the sealed kernel with an empty panel and
projecting back is the identity — the retract is split. -/
theorem retract_section (w : World) :
    (NoOutside.CWorld.mk w []).base = w := rfl

end Initiality
