# G02: original cut-census definitions and general theorem

**AuthorityEffect:** None.

The original task asks for four finite counts and the two general theorems

\[
\operatorname{cutCensus}(n,0,1)=2^{n-2}\quad(n\ge2),
\]

and the same formula for every distinct pair `a,b<n`. The literal `subsetsOf`
and `cutCensus` definitions are extracted unchanged from the sealed
`3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a` Git object. The original Python
twin and original obligation receipt are also retained as raw objects in
[the source manifest](source_manifest.json). These are three bounded execution
dependencies, separate from the pending full source archive.

[The clean final run](final_v3/receipt.json) has raw SHA-256
`15c1365812f8b369ddf072e2109c0092a1f513778ab3f6421bff95475f7eeec8`.
Installed Lean 4.33.0 compiles the general proof by induction on duplicate-free
lists. The final environment census reports 52 theorem and auxiliary constants,
each within the original `{propext, Quot.sound}` whitelist. Thirteen literal
statement pins include C1, C2, C3, all edge cases, the two poison refutations,
carriers nine and ten obtained from C3, and the relabelled pair `(3,1)`.

The finite values at carriers five through eight are `8,16,32,64`. The complete
finite check additionally enumerates all 1,014 triples with `n=0..12` and
`a,b=0..n+1`. The unchanged source Python sublist enumeration and the separately
declared Rust bitmask enumeration agree in every case. Both enumerate all
`2^n` subsets. A too-large carrier and a floating carrier receive the specified
typed refusals. The Rust checker uses the existing exact-integer owner and a
scoped build with retained compiler, source and archive hashes; those prebuilt
archives are not claimed to have been independently rebuilt.

The all-pairs formula has explicit edge cases: a repeated pair gives zero;
`a>=n` gives zero; `a<n<=b` gives `2^(n-1)`. The poisoned unguarded C2 fails at
`n=0`: the census is zero while natural subtraction yields `2^0=1`.

The five original mutation controls are actually compiled. The source-byte
gate rejects `sorry` in a doc-string and `open Classical`, even though their
kernel axiom reports pass. `native_decide` also produces a disallowed generated
axiom, literally `G02Mutation_native_decide.candidate._native.native_decide.ax_1_1`
in this compiler version, rather than the old specification's expected name
`Lean.ofReduceBool`. A replacement for `Nat.pow` with an unproved agreement axiom
is rejected. A valid theorem with the narrower `4<=n` domain fails the original
`2<=n` statement pin. A known valid candidate passes both gates.

Earlier diagnostics are retained: the first package configuration failed;
the next clean build correctly refused `Classical.choice`. The latter came from
stdlib lemmas selected by simplification. Local constructive filter-empty and
range-distinctness proofs remove that dependency without changing a target or
relaxing the whitelist. The successful final run binds 10,227 source/runtime
inputs before and after execution, raw process input/output bytes and ten
compiled output records. Its generated mutation files initially had only final
output hashes. The independent review requires a separate mutation-only replay
with each actual compiler input bound before and after its invocation; that
supplement is retained separately from the mathematical census run. The closed
[mutation custody replay](mutation_custody_v1/receipt.json), raw SHA-256
`76a851353e6fa4a08f854b0c20dca361849e3914e4389ada520276c2179adb9a`,
reproduces the same six candidate outcomes through eight compiler calls. Each
generated compiler input is hashed before and after use. The baseline runtime
and compiled-import closure also remain unchanged. Independent review confirms
that this closes the reported gap within the declared scope.

Twelve focused tests pass, including a fresh native replay of the complete
request, independent closed-form checks for every pair, byte corruption,
report corruption, mutation outcomes, the generated-input custody supplement,
and preservation of the valid candidate.
Ruff passes. The companion tests are
[test_paper011_genesis_g02.py](../../../code/tests/test_paper011_genesis_g02.py).

This is an operator-authored, provider-free reconstruction. It does not execute
the original model arms, dollar-budget comparison, McNemar/seed trial, external
estate workflow or owner PR. The current recorded Windows build configuration
is bound to its explicit short build directory; an isolated extracted-package
rebuild remains part of the unfinished release audit. OS and Python standard
library inputs are outside this run's declared runtime manifest. No census has
meaning beyond the retained definition, and no admission authority is granted.
