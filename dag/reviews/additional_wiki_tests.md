# Wiki test-page review

All **47 frozen pages (197,686 bytes)** were read in full and assessed. Their strongest contribution is explaining finite certificates, carrier boundaries, exact encodings and the difference between a matched refusal and a solved problem. Existing source-review findings are explicitly attributed; historical test counts were not rerun.

The main corrections needed are:

- **Equational and recurrence certification:** current C050 checkers admit false proofs/nonmodels; finite sequence agreement does not prove an infinite law, and C047 start-range binding is defective.
- **Replay coverage:** C054/C055 custody tests skip their retained mutation envelope field, so passing those tests does not establish the advertised mutation checks.
- **Oracle evidence:** the JSON freezer says it was frozen after native implementation. Its seeded stream contains 129 NaNs and 130 subnormals, but no infinities or signed zero; explicit special cases are separate evidence.
- **Boundary claims:** the purity scanner misses four I/O spellings; co-stored hashes need a retained external expectation to establish historical drift; role labels are not signatures; algorithmic diversity supplies no statistical independence guarantee.
- **Documentation accuracy:** the universal 14/64/48 package template is false, the quadratic-form solver/check cost is overstated, and the template page's converse exercise needs reversed replacement order.

Six bounded controls passed, reproducing the stated counterexamples and selected exact worksheet arithmetic. The JSON records **11 actionable documentation findings**, each page's mathematical contribution/usefulness/limits, three narrowly inspected source owners, and exact prior-source pins. No original sources changed; no provider, private benchmark, answer key or native build was used.
