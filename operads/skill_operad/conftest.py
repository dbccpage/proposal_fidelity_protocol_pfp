"""Make the canon operad suites importable when pytest runs from the repo root.

`skill_compiler/tests/test_skill_compiler.py` does `from skill_compiler import
budget_gate, resolve`, which resolves only when `.agents/operad/` is on
`sys.path`. Nothing put it there, so from the repository root the suite did not
fail -- it failed to COLLECT, which is louder in isolation and silent in a
sweep, and no runner referenced it either. Twenty-six tests and four subtests
guarding the OEWAS-006 budget gate were unreachable by any invocation the
repository documents.

Canon only, deliberately
------------------------

`operad/` is duplicated across four hosts. Giving each mirror a conftest would
put four directories named `.../operad` on `sys.path` in the same session,
`import skill_compiler` would bind to whichever host was collected first, and
every later host's tests would silently exercise the first host's modules. A
green run would then say nothing about three of the four trees.

So only `.agents/` -- the canonical host -- gets this file, and
`test_operad_suite_is_collectable.py` pins both halves: canon collects, and the
mirrors stay without a conftest so the ambiguity cannot reappear unnoticed.

`sys.path.append`, not `insert(0,)`: this directory contains `domain/`,
`application/`, and `infrastructure/`, names generic enough to shadow something
else's top-level import if given priority. The repository has been bitten by
exactly this before -- `library/code/` shadowing the stdlib `code`
module -- and the house rule that came out of it is to never let a convenience
path win a name race.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

_OPERAD_ROOT = str(Path(__file__).resolve().parent)

if _OPERAD_ROOT not in sys.path:
    sys.path.append(_OPERAD_ROOT)
