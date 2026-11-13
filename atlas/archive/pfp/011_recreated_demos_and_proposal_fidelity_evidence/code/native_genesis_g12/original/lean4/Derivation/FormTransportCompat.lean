import Derivation
import Derivation.FormTransport

/-!
# Import-compatibility probe for the parked `FormTransport`

A parked module is compiled alone by the per-module census, so a name it
declares can silently collide with a declaration in the public `Derivation`
root target and no gate would notice -- until a downstream file imports both.
That happened once: an earlier `FormTransport` declared `Iso`, which already
exists in `Minimality.lean` (root-imported), and the collision surfaced only
under `import Derivation; import Derivation.FormTransport`.

This module IS those two imports.  It carries no declarations; its only job
is to force the root and the parked module into one environment, so the
census build fails on any such collision at the source, not downstream.

Scope: this probe covers `FormTransport` (and, transitively, `FormRenaming`)
only.  The older parked modules `Breaking` and `Composing` are not probed
here; a full guard would add one probe per parked module.

AuthorityEffect: None.  Parked; no declarations, hence no axiom footprint.
-/
