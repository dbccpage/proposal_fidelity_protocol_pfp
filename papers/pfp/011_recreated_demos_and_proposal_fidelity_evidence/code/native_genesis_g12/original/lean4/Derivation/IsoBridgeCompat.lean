import Derivation
import Derivation.IsoBridge

/-!
# Import-compatibility probe for the parked `IsoBridge`

`IsoBridge` imports `IsoCanon` (itself parked), not the full `Derivation`
root, so compiling it alone would not catch a name it declares colliding with
a root module.  This module imports both the root target and `IsoBridge`, so
the per-module census build fails on any such collision at the source.

It carries no declarations.  Scope: this probe covers `IsoBridge` (and,
transitively, its parked imports `IsoCanon`, `IsoCollapse`, `FormRenaming`)
only.

AuthorityEffect: None.  Parked; no declarations, hence no axiom footprint.
-/
