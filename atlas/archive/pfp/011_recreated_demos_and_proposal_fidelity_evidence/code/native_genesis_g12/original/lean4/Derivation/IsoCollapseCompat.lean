import Derivation
import Derivation.IsoCollapse

/-!
# Import-compatibility probe for the parked `IsoCollapse`

Like `FormTransportCompat`, but for `IsoCollapse`.  `IsoCollapse` imports
`Derivation.Minimality`, not the full `Derivation` root, so compiling it alone
would not catch a name it declares colliding with a root module outside
`Minimality`'s cone.  This module imports both the root target and
`IsoCollapse`, so the per-module census build fails on any such collision at
the source.

It carries no declarations.  Scope: this probe covers `IsoCollapse` only.

AuthorityEffect: None.  Parked; no declarations, hence no axiom footprint.
-/
