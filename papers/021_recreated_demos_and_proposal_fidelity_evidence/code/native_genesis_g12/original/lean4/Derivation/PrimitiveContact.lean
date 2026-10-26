import Derivation.PrimitiveCore
import Derivation.PrimitiveCats
import Derivation.ContactBridge

/-!
# Primitive contact: the collision protocol and its input status

Stages III–V of the contact-and-passage run.

The run protocol declares a contact package

    contact/omega_primdiff/
      CONTACT_MANIFEST.json
      lean4/
      prose/

to be read in two stages (Lean before prose), each only after the
corresponding native commitment.

**SEALED PRE-CONTACT TEXT — true at the blind-native-base `ccd3a53`,
SUPERSEDED on 2026-08-13 by the addendum below.  Do not read the
following sentences as a description of the current repository; the
package arrived at `e4aed9e` and the collision was executed.**  "The
package is absent from the repository: no `contact/` directory exists
at the pre-contact commit (`blind-native-base`) or at completion.  Per
the protocol, the native stages complete and the contact stages
terminate with `CONTACT_INPUT_ABSENT`; no contents are invented, no
comparison is fabricated, and no agreement pressure exists."

What this module does record, so that any FUTURE contact meets a fixed
interface rather than a movable one:

1. the native kernel, bound under its contact-facing name — the class
   of settings carrying a pointed witnessed irreflexive relation
   (candidate A of `PrimitiveCore`), inhabited by the two-element
   oriented realization;
2. the proved status the kernel brings to any collision: the complete
   72-cell implication/countermodel matrix over the nine candidate
   readings (`PrimitiveCore.matrixCells`), initiality of the
   two-element carrier in the pointed witnessed category
   (`PrimitiveCats.d2_initial`), the retained orientation fork
   (`PrimitiveCats.s2_initial_sym`, `PrimitiveCats.s2_not_weakly_initial`),
   and the observer-branching theorem
   (`PrimitiveCats.no_terminal_pres`);
3. the collision discipline that would apply: statements only, never
   comments; assumption graphs and axiom reports per supplied theorem;
   for every notion pair exactly one of equivalence-under-hypotheses,
   one-direction-with-countermodel, incomparability, or common-third
   realization.

**Sealed history addendum (2026-08-13, base a5caee2).**  The text
above is the pre-contact record, written at the blind-native-base
(ccd3a53) when no `contact/` directory existed; it stands unchanged,
and its declarations (`contactStatus`, `NativeKernel`,
`nativeKernelWitness`, `native_kernel_initial`) are sealed.  This run
executed the collision: the supplied single-file development arrived
under `contact/omega_primdiff/` (manifest binding:
`contact/omega_primdiff/CONTACT_MANIFEST.json`; supplied Lean file
sha256
`d9cdb350a53c513e3e211e72f17262be6ba85d7da6159f910388c7137e814a89`;
prose stage: PROSE_INPUT_ABSENT) and was processed Lean-only under
the collision discipline declared above.  The collision content lives
in `ObsDescent` (reconstruction), `ContactBridge` (bridges,
countermodels, pricing), and `ContactKernel` (the common replacement
kernel, which meets the fixed interface below via
`ContactKernel.toNativeKernel`).  This run's status and verdict
constants are declared at the end of this module; the historical
terminal is preserved as the first entry of `contactStatusHistory`.
-/

namespace PrimitiveContact

/-- **SUPERSEDED — the sealed pre-contact terminal**, recorded at the
blind-native base and preserved unchanged for the record.  It is NOT
the status of this repository at any commit from `e4aed9e` onward.
The current terminal is `contactStatusCurrent`
(`CONTACT_PROCESSED_LEAN_ONLY`) and the full history is
`contactStatusHistory`; a consumer reading this constant alone gets
the value superseded on 2026-08-13. -/
def contactStatus : String := "CONTACT_INPUT_ABSENT"

/-- The native kernel, under its contact-facing name: settings
carrying a pointed witnessed irreflexive relation. -/
def NativeKernel : Type 1 :=
  { S : PrimitiveCore.Setting // PrimitiveCore.A S }

/-- The kernel is inhabited by the oriented two-element realization
(bare: empty retention, protection, and operation stores). -/
def nativeKernelWitness : NativeKernel :=
  ⟨{ X := Bool, r := PrimDiff.D2, a := false, b := true,
     ret := fun _ _ => False, prot := fun _ _ => False,
     Ops := fun _ => False },
   ⟨PrimDiff.D2_witness, PrimDiff.D2_irrefl⟩⟩

/-- The kernel's carrier of record is initial in the pointed
witnessed category — the strongest universal status the native side
brings to any future collision (proved, not postured:
`PrimitiveCats.d2_initial`). -/
theorem native_kernel_initial : PrimitiveCats.Initial
    PrimitiveCats.d2Obj := PrimitiveCats.d2_initial

/-! ## This run's contact section (2026-08-13)

The declarations above are the sealed pre-contact record.  The
declarations below record the executed collision.  Recorded facts of
the run: manifest at `contact/omega_primdiff/CONTACT_MANIFEST.json`;
supplied Lean file sha256
`d9cdb350a53c513e3e211e72f17262be6ba85d7da6159f910388c7137e814a89`;
prose stage PROSE_INPUT_ABSENT.  The evidence for the verdict is the
theorem corpus of `ObsDescent`, `ContactBridge`, and
`ContactKernel`; the artifact `primitive_contact.json` carries the
matching status and verdict blocks. -/

/-- The status history: the sealed pre-contact terminal, then this
run's terminal.  DECLARED_POLICY. -/
def contactStatusHistory : List String :=
  ["CONTACT_INPUT_ABSENT (pre-contact, blind-native-base ccd3a53)",
   "CONTACT_PROCESSED_LEAN_ONLY (2026-08-13, base a5caee2)"]

/-- The current contact status.  DECLARED_POLICY; must equal the
Python generator's status constant. -/
def contactStatusCurrent : String := "CONTACT_PROCESSED_LEAN_ONLY"

/-- The primary verdict of the executed collision.
DECLARED_POLICY. -/
def contactVerdictPrimary : String :=
  "CONTACT_INCOMPARABLE_WITH_COUNTERMODELS"

/-- The history carries exactly the two terminals.
FINITE_COMPUTATION. -/
theorem contact_status_count : contactStatusHistory.length = 2 := rfl

/-- The sealed interface object is exactly what an arriving
zero-complement observer cannot represent: the oriented two-element
witness.  Re-export of the collision's signature-level refutation at
the fixed interface. -/
theorem native_interface_not_representable :
    ¬ ∃ (R : Type) (O : DiffInterface.DiffObs Bool R),
        ∀ x y, ContactBridge.obsApart O x y ↔ PrimDiff.D2 x y :=
  ContactBridge.d2_not_obs_complement

end PrimitiveContact
