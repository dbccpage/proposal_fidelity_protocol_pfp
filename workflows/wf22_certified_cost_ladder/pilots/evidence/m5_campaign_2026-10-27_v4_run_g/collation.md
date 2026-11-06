# M5 matched campaign collation

Charged $0.233172 of the $25.000000 cap (unknown costs charged at the per-run cap). AuthorityEffect: None.

| model and arm | runs | accepted | accepted at stage 1 | calls | prompt tokens | completion tokens | known cost | unknown-cost runs | elapsed ms | replay failures |
|---|---|---|---|---|---|---|---|---|---|---|
| google/run_g-2.5-flash | baseline | 21/21 | 2 | 2 | 40 | 253108 | 22107 | $0.115909 | 0 | 160389 | 0 |
| google/run_g-2.5-flash | typed_witness | 21/21 | 2 | 2 | 39 | 248419 | 22999 | $0.117263 | 0 | 165994 | 0 |

Matched pairs (baseline vs typed_witness):

- google/run_g-2.5-flash: 21 pairs; both accepted 1, neither 18, only typed_witness ['C024'], only baseline ['C005'].

Final status and failure-class counts:

- google/run_g-2.5-flash | baseline: {'HOST_ACCEPTED': 2, 'PROVIDER_COMPLETED': 19}; failure classes {'CERTIFICATE': 10, 'COBOUNDARY_RESIDUAL': 1, 'ENVELOPE': 4, 'SCOPE': 3, 'WIRE_DISCRIMINATOR': 1}
- google/run_g-2.5-flash | typed_witness: {'CHECKER_DEFECT': 1, 'HOST_ACCEPTED': 2, 'INFRASTRUCTURE_ERROR': 1, 'PROVIDER_COMPLETED': 17}; failure classes {'CERTIFICATE': 11, 'COBOUNDARY_RESIDUAL': 1, 'DISAGREEMENT': 1, 'ENVELOPE': 2, 'PFP_OR_ACCOUNTING': 1, 'SCOPE': 2, 'WIRE_DISCRIMINATOR': 1}
