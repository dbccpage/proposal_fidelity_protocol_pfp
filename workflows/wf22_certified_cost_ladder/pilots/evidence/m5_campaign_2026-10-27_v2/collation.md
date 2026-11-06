# M5 matched campaign collation

Charged $0.147539 of the $25.000000 cap (unknown costs charged at the per-run cap). AuthorityEffect: None.

| model and arm | runs | accepted | accepted at stage 1 | calls | prompt tokens | completion tokens | known cost | unknown-cost runs | elapsed ms | replay failures |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash | baseline | 21/21 | 0 | 0 | 42 | 248327 | 10512 | $0.017169 | 0 | 171590 | 0 |
| deepseek/deepseek-v4-flash | typed_witness | 21/21 | 0 | 0 | 42 | 250770 | 10155 | $0.017129 | 0 | 162747 | 0 |
| google/gemini-2.5-flash | baseline | 21/21 | 0 | 0 | 21 | 127951 | 8790 | $0.055959 | 0 | 85386 | 0 |
| google/gemini-2.5-flash | typed_witness | 21/21 | 0 | 0 | 21 | 129203 | 8839 | $0.057282 | 0 | 86525 | 0 |

Matched pairs (baseline vs typed_witness):

- deepseek/deepseek-v4-flash: 21 pairs; both accepted 0, neither 21, only typed_witness [], only baseline [].
- google/gemini-2.5-flash: 21 pairs; both accepted 0, neither 21, only typed_witness [], only baseline [].

Final status and failure-class counts:

- deepseek/deepseek-v4-flash | baseline: {'PROVIDER_COMPLETED': 21}; failure classes {'CERTIFICATE': 1, 'ENVELOPE': 19, 'WIRE_DISCRIMINATOR': 1}
- deepseek/deepseek-v4-flash | typed_witness: {'PROVIDER_COMPLETED': 21}; failure classes {'CERTIFICATE': 1, 'ENVELOPE': 19, 'WIRE_DISCRIMINATOR': 1}
- google/gemini-2.5-flash | baseline: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
- google/gemini-2.5-flash | typed_witness: {'INFRASTRUCTURE_ERROR': 21}; failure classes {'PFP_OR_ACCOUNTING': 21}
