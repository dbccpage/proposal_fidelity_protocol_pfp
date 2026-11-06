# Blinded score table (verifier verdicts only)

Columns X and Y are two anonymised arms; the assignment is a per-prompt coin fixed by the protocol hash and is not shown here.
Counts are accepted/rejected/unverified units per class: O operad entry, L Lean file, W Rust or Python witness. Cost is withheld until `--unblind`.

| stratum | prompt | X outcome | X units | Y outcome | Y units |
|---|---|---|---|---|---|
| D | FQ-GAP-BORN-UNIQUENESS-GLEASON | ACCEPTED | O 20/0/0 L 0/0/3 W 0/0/0 | NONE | O 0/1/0 L 0/0/0 W 0/0/0 |
| D | FQ-GAP-CONTINUUM-HILBERT-LIFT | ACCEPTED | O 2/0/0 L 0/0/0 W 0/0/0 | ACCEPTED | O 12/0/0 L 0/0/2 W 0/0/0 |
| D | FQ-GAP-STONE-CONTINUOUS-TIME | ACCEPTED | O 12/0/0 L 0/0/1 W 0/0/0 | ABSTAINED | O 0/1/0 L 0/0/0 W 0/0/0 |
| D | L1-IMP-HILBERT-INNER-PRODUCT | ACCEPTED | O 14/0/0 L 0/0/0 W 0/0/0 | ACCEPTED | O 3/0/0 L 0/0/0 W 0/0/0 |
| D | L1-IMP-LINEAR-ISOMETRIC-DYNAMICS | ACCEPTED | O 19/0/0 L 0/0/2 W 0/0/0 | ACCEPTED | O 3/0/0 L 0/0/0 W 0/0/0 |
| D | TFQ-0084 | ACCEPTED | O 2/0/0 L 0/0/0 W 0/0/0 | ACCEPTED | O 6/0/0 L 0/0/2 W 0/0/0 |
| P | TFQ-0022 | ACCEPTED | O 2/0/0 L 0/0/0 W 0/0/0 | FAILED | O 0/1/0 L 0/0/0 W 0/0/0 |
| P | TFQ-0028 | ACCEPTED | O 2/0/0 L 0/0/0 W 0/0/0 | ACCEPTED | O 12/0/0 L 0/0/0 W 0/0/0 |
| P | TFQ-0031 | FAILED | O 0/1/0 L 0/0/0 W 0/0/0 | ACCEPTED | O 4/0/0 L 0/0/0 W 0/0/0 |
| C | FQ-CONTINUUM-HILBERT-LIFT-CONSTRUCTION | NONE | - | NONE | - |
| C | MUB6-ROUTE-C-CONDITIONAL | NONE | - | ACCEPTED | O 6/0/0 L 0/0/1 W 0/0/0 |
| C | TFQ-0237 | ACCEPTED | O 4/0/0 L 0/0/0 W 0/0/0 | NONE | - |
| C | TFQ-0279 | NONE | - | NONE | O 0/0/0 L 0/0/0 W 0/0/0 |
| C | TFQ-0280 | NONE | O 0/0/0 L 0/0/0 W 0/0/0 | NONE | - |
| C | TFQ-0088 | NONE | O 0/0/0 L 0/0/0 W 0/0/0 | NONE | - |
