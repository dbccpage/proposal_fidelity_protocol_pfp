import Derivation
import Derivation.IsoCanon

/-!
# Import-compatibility probe for the parked `IsoCanon`

`IsoCanon` imports `IsoCollapse`, `TransitionTransport`, and `FormRenaming`,
not the full `Derivation` root, so compiling it alone would not catch a name
it declares colliding with a root module outside those cones.  This module imports both the
root target and `IsoCanon`, so the per-module census build fails on any such
collision at the source.

It carries no declarations.  Scope: this probe covers `IsoCanon` (and,
transitively, its parked imports `IsoCollapse` and `FormRenaming`) only.

AuthorityEffect: None.  Parked; no declarations, hence no axiom footprint.
-/
