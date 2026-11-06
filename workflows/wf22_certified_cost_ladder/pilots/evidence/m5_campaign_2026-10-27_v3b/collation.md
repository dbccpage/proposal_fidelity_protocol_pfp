# M5 matched campaign collation

Charged $0.176508 of the $25.000000 cap (unknown costs charged at the per-run cap). AuthorityEffect: None.

| model and arm | runs | accepted | accepted at stage 1 | calls | prompt tokens | completion tokens | known cost | unknown-cost runs | elapsed ms | replay failures |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash | baseline | 21/21 | 2 | 2 | 38 | 233127 | 19130 | $0.020282 | 0 | 558212 | 0 |
| deepseek/deepseek-v4-flash | typed_witness | 21/21 | 4 | 1 | 39 | 239769 | 23304 | $0.022494 | 0 | 787187 | 0 |
| google/run_g-2.5-flash | baseline | 21/21 | 0 | 0 | 21 | 132642 | 12353 | $0.063514 | 0 | 173774 | 0 |
| google/run_g-2.5-flash | typed_witness | 21/21 | 0 | 0 | 21 | 133898 | 14884 | $0.070218 | 0 | 167055 | 0 |

Matched pairs (baseline vs typed_witness):

- deepseek/deepseek-v4-flash: 21 pairs; both accepted 2, neither 17, only typed_witness ['C014', 'C021'], only baseline [].
- google/run_g-2.5-flash: 21 pairs; both accepted 0, neither 21, only typed_witness [], only baseline [].

Final status and failure-class counts:

- deepseek/deepseek-v4-flash | baseline: {'CHECKER_DEFECT': 2, 'HOST_ACCEPTED': 2, 'PROVIDER_COMPLETED': 17}; failure classes {'CERTIFICATE': 13, 'CHECKER': 1, 'DISAGREEMENT': 1, 'SCOPE': 3, 'WIRE_DISCRIMINATOR': 1}
- deepseek/deepseek-v4-flash | typed_witness: {'CHECKER_DEFECT': 3, 'HOST_ACCEPTED': 4, 'INFRASTRUCTURE_ERROR': 1, 'PROVIDER_COMPLETED': 13}; failure classes {'CERTIFICATE': 11, 'CHECKER': 1, 'DISAGREEMENT': 2, 'PFP_OR_ACCOUNTING': 1, 'SCOPE': 1, 'WIRE_DISCRIMINATOR': 1}
- google/run_g-2.5-flash | baseline: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
- google/run_g-2.5-flash | typed_witness: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
