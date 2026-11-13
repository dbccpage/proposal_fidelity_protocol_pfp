# Exact public-input representation before synthesis

The first live pilot repeatedly changed the Hamiltonian while expanding tensor
products. This implementation checks that particular boundary before asking for
a full solution. It is a bounded adaptation of R01-I03, witnessed representation
transport, rather than a complete native PFP/EIS/PCIV/OPERADS implementation.

`hamiltonian_artifact.py` derives three coefficient matrices from exact complex
rational Pauli tensor products in basis 00,01,10,11. It checks all 48 entries of
a candidate's canonical rational matrices. Equality of the three coefficients
implies equality of their affine linear combination for every real J, Delta
and K. Conversely, equality of those affine combinations for every parameter
triple implies coefficient equality by evaluating each coordinate basis vector.
This is a polynomial identity check, not sampling finitely many parameter
values. It assumes the public Hamiltonian and basis convention; it proves no
spectrum, time evolution, entanglement, thermodynamics, or final-answer result.

The checker is restricted to the exact committed seed hash. JSON has a closed
schema, 32KiB byte ceiling, depth limit, canonical reduced n/d strings and
128-bit rational components. It rejects malformed inputs rather than repairing
them silently. Expected entries in failure feedback are public-input
calculations, never private evaluator material.

The three plans share an identical final-synthesis instruction and, for an
identical valid matrix, byte-identical final requests:

| Plan | Procedure | Model calls | Maximum output tokens |
| --- | --- | ---: | ---: |
| `hamiltonian_checked_v1` | Propose matrices; check; allow one correction on failure; synthesize only after acceptance | 2, or 3 with correction | 6,400 |
| `hamiltonian_ungated_v1` | Propose matrices; synthesize regardless; withhold host checker feedback | 2 | 5,200 |
| `hamiltonian_host_matrix_v1` | Host computes matrices from public input; synthesize | 1 | 4,000 |

The host control matters because checking these coefficients already computes
the correct representation. Paid proposal/correction calls should demonstrate
an advantage over that simpler computation rather than receive automatic credit
for adding stages. The ungated arm isolates enforcement from decomposition.
Host observations remain in every receipt; a failed ungated representation is
not relabeled as accepted. A matrix without synthesis is never a final answer.

Each call includes the complete unchanged seed. The final answer uses plain
text, so the small typed artifact and long mathematical explanation do not
compete inside a single JSON envelope. All branches share the existing durable
USD0.10 run ledger. Unknown billing stops further calls. A failed second matrix
attempt refuses synthesis. No hidden retries, tools, repository retrieval,
reference answer or grade feedback are available to the model.

The second live pilot is preregistered by `hamiltonian_campaign_run.py prepare`:
four arms (including the unchanged direct baseline), two samples per arm,
one OpenRouter endpoint, a fixed shuffle and USD0.80 aggregate ceiling. The
direct baseline retains its old instruction, while the other three share a
compact synthesis instruction; a direct-versus-matrix difference therefore does
not isolate matrix context alone. Total token allowances also differ. This is
a small descriptive experiment, not a general workflow ranking. Frozen outputs
are graded afterward with the existing rubric.
