# Review and incorporation of the concurrent curriculum

AuthorityEffect: None.

The 125-lesson syllabus gives a useful ordering of topics. A passing notebook
count or syntax check cannot establish that each topic is implemented. The
read-only [per-notebook review](curriculum_125_review.json) is a historical
snapshot of the pre-relocation notebook and generator bytes. It records
structural findings, shared-computation groups, and replacement routes; it is
not a refreshable current-state receipt.

The pre-relocation generator and its 200/300/400 source table were retired.
They targeted the removed `education/the_symbol_game/lessons`
tree, while the canonical notebooks now live in this directory and have
continued to evolve. Replaying those stale sources would overwrite newer
integrated laboratory cells. Current review therefore reads these checked-in
artifacts directly and must not regenerate them from the historical snapshot.

## Confirmed patterns and concrete replacements

| Existing pattern | Why the evidence is insufficient | Runnable replacement |
| --- | --- | --- |
| Generic arithmetic reused under different lesson titles | A difference of two constants or a normalized singleton does not test the titled mechanism | Follow the per-notebook replacement route; each new notebook imports the implementation it exercises |
| Hidden exercise solution contains a constant assertion | It cannot detect a wrong learner implementation or changed input | Every new lesson supplies a changed-input probe or independent reference computation |
| Diagnostic answer assigned immediately before asserting that same answer | It tests the supplied answer key rather than the learner's model | Predict a refusal or changed exact value before executing each new adversarial cell |
| Determinant assigned as an expected Fraction and then compared with itself | No matrix determinant has been computed | [Four-simplex lesson](300_advanced/01_four_simplex_volume.ipynb) computes Gaussian elimination and an independent Leibniz determinant |
| A zero duality gap stated without primal and dual feasibility | Equal objectives can accompany invalid witnesses | [LP lesson](200_intermediates/02_exact_lp_certificates.ipynb) rejects infeasible primal, non-closed dual, and positive-gap candidates |
| Deterministic execution labeled as proof without a finite-domain qualifier | Runtime assertions support the checked fixtures and paths | Each new lesson has an explicit evidence boundary and source list |
| Hash length checked without changing a payload | A 64-character digest alone does not test tamper detection | [Codec lesson](100_novices/01_codecs_and_tamper_evidence.ipynb) mutates a DAG node while retaining the old digest key |
| Static receipt covers a subset of the titled curriculum | The selected subset cannot be counted as execution of all 125 notebooks | New receipt records every one of the 20 integration notebooks separately |

Shared-computation groups are a review signal, not an automatic judgment that
the underlying calculation is wrong. A self-contained arithmetic lesson can be
appropriate when its title and evidence are scoped to that calculation. The
JSON review only labels patterns it detects in the current bytes and does not
claim to semantically review or execute every existing lesson.

## Source defects exposed by integration

The DDC carrier constructor previously permitted a face whose full boundary was
absent. Integration exposed this defect, and the constructor now rejects a
boundary edge absent in both orientations. The
[nilpotence lesson](200_intermediates/01_nilpotence_and_missing_boundaries.ipynb)
checks this refusal, retains the reversed-orientation positive control, and
independently audits every vertex basis potential. Boundary completeness and
nilpotence remain separate checks.

The legacy Python anti-skill verifier and loader previously passed `code`,
`message`, and `locus` to a result wrapper that accepts one payload. They raised
a constructor error before returning their intended runtime-retirement status.
This integration adds a frozen diagnostic payload and returns `Refusal(payload)`
at all three retired entry points. A focused regression test checks their exact
status and failure behavior. The retirement policy remains explicit; no skill is
admitted.

The degree-four lesson uses a declared rational pairing and quotient certificate.
It does not count an assigned zero cochain as an evaluated cup product, or infer
manifold topology from a fixture name. The original Demo 9 cellular ranks require
independent topology review before its named geometric interpretation can be
accepted.

## Remaining completion work

The preserved 125 notebooks still need topic-specific replacement where their
evidence is generic. The new routes provide concrete executable reference
lessons for that work. Native Rust detector replay, full RFC 8785 conformance,
Lean theorem replay, real neural interventions, and model-quality benchmarking
remain separate tasks unless a linked receipt explicitly records them.
