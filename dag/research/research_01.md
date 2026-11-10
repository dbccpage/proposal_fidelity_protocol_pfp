# Research 01: typed certificates and proof obligations

Three proposed workflows address different failure modes: **R01-I01** checks dependency closure and repairs a bounded failed frontier; **R01-I02** checks definedness and complete exceptional-case coverage; **R01-I03** checks mathematical transport across representation and convention changes. All remain **proposed, not evaluated**. No paid models were called and no seed solution is included.

The established foundations are [proof-carrying code](https://www.cs.tufts.edu/comp/150CMP/papers/necula97pcc.pdf) and [modular checking of external proof witnesses](https://www-sop.inria.fr/marelle/Laurent.Thery/pub1.pdf). [SMTCoq's documentation](https://smtcoq.github.io/) also describes compositional certifying transformations. The proposed contribution is their bounded adaptation to PFP receipts, OPERADS interfaces, EIS mutation controls, and PCIV's offline paired evaluation. This is not a claim of literature-wide novelty.

| Idea | Model calls | Distinct mechanism | Conditional reserved API spend |
| --- | ---: | --- | ---: |
| R01-I01 | 2 | Propagate missing premises through a certificate DAG; repair only a failed frontier | $0.046 |
| R01-I02 | 1 | Require exhaustive branch coverage and a definedness witness for every partial operator | $0.040 |
| R01-I03 | 2 | Require checked maps and preservation obligations at representation changes | $0.042 |

These costs assume an admitted endpoint charging at most $1 per million input tokens and $5 per million output tokens, no per-request fee, and a $0.01 additional reserve. They are conditional budget envelopes, not quotations. A later run must pin current endpoint metadata, count complete requests, cap all billable output/reasoning, and refuse unknown charges. [OpenRouter's model endpoint](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties) exposes relevant pricing and limit fields. No retries or automatic model fallback are allowed.

The most reusable primitive is **ScopedObligationReceiptV1**: bind each checked statement to candidate, seed, context, branch, checker version, and dependencies; preserve unresolved premises and theory limits through composition. Host statuses must distinguish a checked predicate, a failed witness, an unsupported obligation, and an infrastructure error. Exact arithmetic, numerical checks, admitted theorem applications, and prose require different scope labels.

Two repository details materially affect the design. `pfp/domain/exact/poly.py` supplies univariate rational polynomial operations, not arbitrary symbolic analysis. `pfp/domain/exact/wire.py` and `pfp/domain/exact/q.py` use different canonical rational strings, so certificates need explicit codec versions. Equality of objective values also needs feasibility premises before it supports an optimality claim.

Start with host-only synthetic receipt controls, then a single-call R01-I02 experiment. Public synthetic cases can test missing complements, erased denominator conditions, overlap inconsistencies, and invalid endpoint conventions without solving the seed or consulting its private key. A finite mutation panel measures those controls only; it cannot establish checker completeness.

Every proposed workflow preserves the seed's exact bytes in a separate message. Private evaluation occurs only after outputs are frozen and supplies no model feedback. The full JSON report supplies schemas, stages, assumptions, baselines, ablations, falsification criteria, risks, source paths, and an explicit research prompt prohibiting any seed solution.
