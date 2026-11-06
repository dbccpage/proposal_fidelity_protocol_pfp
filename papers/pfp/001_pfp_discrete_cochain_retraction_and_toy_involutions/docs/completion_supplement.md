# Paper 001 supplement: current scope and retained Fock artifact

The current [manuscript](../paper.md) is self-contained and supersedes earlier
completion language. Its subject is finite graph repair and the verification
boundary of the Proposal Fidelity Protocol (PFP). The native Rust solver
returns a minimum and a minimizing potential without a dual certificate. The
paper-local Python reference in
[code/symbol_game_governor.py](../code/symbol_game_governor.py) builds and
checks the full primal and dual certificate on small graphs; Section 6 of the
manuscript states the scope of each.

The exact integrated-path checker is preserved at
[code/exact_fock_gap.py](../code/exact_fock_gap.py). Its hypotheses, rational
exponential enclosures, 192-path enumeration, and representation boundary are
developed in the companion paper PFP II (Carroll, 2026a; see
[references.md](references.md)). No file move or altered historical receipt is
needed to reuse that result.

From the package root, its focused reproduction is:

~~~powershell
py -3.12 code/exact_fock_gap.py
py -3.12 -m pytest code/tests/test_exact_fock_gap.py -q
~~~

A passing result establishes the declared path-gap check only. Current
execution evidence for this revision is the dated review receipt described in
the manuscript's section "Verification for this revision".
