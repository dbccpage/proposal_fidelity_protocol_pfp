# M5 matched campaign collation

Charged $0.128167 of the $25.000000 cap (unknown costs charged at the per-run cap). AuthorityEffect: None.

| model and arm | runs | accepted | accepted at stage 1 | calls | prompt tokens | completion tokens | known cost | unknown-cost runs | elapsed ms | replay failures |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash | baseline | 21/21 | 1 | 0 | 33 | 193650 | 9379 | $0.013918 | 0 | 232538 | 0 |
| deepseek/deepseek-v4-flash | typed_witness | 21/21 | 0 | 0 | 34 | 203037 | 12665 | $0.015866 | 0 | 256021 | 0 |
| google/gemini-2.5-flash | baseline | 21/21 | 0 | 0 | 21 | 127071 | 5286 | $0.046659 | 0 | 65676 | 0 |
| google/gemini-2.5-flash | typed_witness | 21/21 | 0 | 0 | 21 | 128303 | 7385 | $0.051724 | 0 | 73500 | 0 |

Matched pairs (baseline vs typed_witness):

- deepseek/deepseek-v4-flash: 21 pairs; both accepted 0, neither 20, only typed_witness [], only baseline ['C005'].
- google/gemini-2.5-flash: 21 pairs; both accepted 0, neither 21, only typed_witness [], only baseline [].

Final status and failure-class counts:

- deepseek/deepseek-v4-flash | baseline: {'HOST_ACCEPTED': 1, 'INFRASTRUCTURE_ERROR': 11, 'PROVIDER_COMPLETED': 9}; failure classes {'CERTIFICATE': 2, 'ENVELOPE': 7, 'PFP_OR_ACCOUNTING': 11}
- deepseek/deepseek-v4-flash | typed_witness: {'INFRASTRUCTURE_ERROR': 17, 'PROVIDER_COMPLETED': 4}; failure classes {'CERTIFICATE': 1, 'ENVELOPE': 3, 'PFP_OR_ACCOUNTING': 17}
- google/gemini-2.5-flash | baseline: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
- google/gemini-2.5-flash | typed_witness: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
