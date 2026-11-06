import Derivation
import Derivation.DiffAnchor

/-!
# Import-compatibility probe for the parked `DiffAnchor`

`DiffAnchor` imports `ContactBridge` and `ObsDescent` (both root-imported), not
the full `Derivation` root, so compiling it alone would not catch a name it
declares colliding with a root module outside those cones.  This module imports
both the root target and `DiffAnchor`, so the per-module census build fails on
any such collision at the source.

It carries no declarations.  Scope: this probe covers `DiffAnchor` only; its
two imports are already root-imported (not parked).

AuthorityEffect: None.  Parked; no declarations, hence no axiom footprint.
-/
