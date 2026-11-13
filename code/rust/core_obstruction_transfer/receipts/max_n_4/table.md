## Census

| n | beta1 | graphs |
|---|---|---|
| 3 | 1 | 1 |
| 4 | 1 | 2 |
| 4 | 2 | 1 |

| n | beta1 | edges with w=2 | (G,w) classes | instances |
|---|---|---|---|---|
| 3 | 1 | 0 | 1 | 5 |
| 3 | 1 | 1 | 1 | 5 |
| 3 | 1 | 2 | 1 | 5 |
| 3 | 1 | 3 | 1 | 5 |
| 4 | 1 | 0 | 2 | 10 |
| 4 | 1 | 1 | 4 | 20 |
| 4 | 1 | 2 | 6 | 30 |
| 4 | 1 | 3 | 4 | 20 |
| 4 | 1 | 4 | 2 | 10 |
| 4 | 2 | 0 | 1 | 25 |
| 4 | 2 | 1 | 2 | 50 |
| 4 | 2 | 2 | 4 | 100 |
| 4 | 2 | 3 | 4 | 100 |
| 4 | 2 | 4 | 2 | 50 |
| 4 | 2 | 5 | 1 | 25 |

## Table

| cohort | level | method | pairs | SCORED | NO_HEADROOM | REFUSED | S=1 | S<0 | sum S | NH worse | NH sum(D_tau-D0) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| main | L1 | gauge_transport | 618 | 300 | 318 | 0 | 300 | 0 | 300 | 0 | 0 |
| main | L1 | structural_trace | 618 | 72 | 139 | 407 | 64 | 0 | 64 | 8 | 12 |
| main | L2 | gauge_transport | 11770 | 11182 | 588 | 0 | 11182 | 0 | 11182 | 0 | 0 |
| main | L2 | structural_trace | 11770 | 1922 | 86 | 9762 | 1518 | 26 | 5984282/3465 | 12 | 16 |
| main | L3 | gauge_transport | 3632 | 2608 | 1024 | 0 | 119 | 1989 | -5178 | 738 | 2660 |
| main | L3 | structural_trace | 3632 | 2608 | 1024 | 0 | 1442 | 294 | 3737/3 | 332 | 848 |
| main | L4 | gauge_transport | 6860 | 0 | 0 | 6860 | 0 | 0 | 0 | 0 | 0 |
| main | L4 | structural_trace | 6860 | 3412 | 3320 | 128 | 2292 | 116 | 14119/6 | 340 | 553 |
| main | L5 | gauge_transport | 9128 | 0 | 0 | 9128 | 0 | 0 | 0 | 0 | 0 |
| main | L5 | structural_trace_max | 9128 | 5024 | 3976 | 128 | 3663 | 68 | 11785/3 | 270 | 417 |
| main | L5 | structural_trace_min | 9128 | 5024 | 3976 | 128 | 1460 | 498 | 3683/3 | 562 | 1047 |
| control_shuffled_claims | L1 | gauge_transport | 108 | 24 | 84 | 0 | 24 | 0 | 24 | 0 | 0 |
| control_shuffled_claims | L1 | structural_trace | 108 | 8 | 52 | 48 | 8 | 0 | 8 | 0 | 0 |
| control_shuffled_claims | L2 | gauge_transport | 16 | 8 | 8 | 0 | 8 | 0 | 8 | 0 | 0 |
| control_shuffled_claims | L2 | structural_trace | 16 | 8 | 8 | 0 | 8 | 0 | 8 | 0 | 0 |
| control_shuffled_claims | L3 | gauge_transport | 240 | 152 | 88 | 0 | 0 | 123 | -1691/6 | 83 | 322 |
| control_shuffled_claims | L3 | structural_trace | 240 | 144 | 88 | 8 | 31 | 27 | 59/6 | 53 | 166 |
| control_shuffled_claims | L5 | gauge_transport | 96 | 0 | 0 | 96 | 0 | 0 | 0 | 0 | 0 |
| control_shuffled_claims | L5 | structural_trace_max | 96 | 56 | 40 | 0 | 54 | 0 | 54 | 4 | 6 |
| control_shuffled_claims | L5 | structural_trace_min | 96 | 56 | 40 | 0 | 48 | 2 | 46 | 10 | 18 |
| control_cross_betti | none | gauge_transport | 440 | 0 | 0 | 440 | 0 | 0 | 0 | 0 | 0 |
| control_cross_betti | none | structural_trace | 440 | 0 | 0 | 440 | 0 | 0 | 0 | 0 | 0 |

| cohort | level | method | refusal code | count |
|---|---|---|---|---|
| main | L1 | structural_trace | CHORD_NO_IMAGE | 407 |
| main | L2 | structural_trace | CHORD_NO_IMAGE | 9762 |
| main | L4 | gauge_transport | NO_VERTEX_MAP | 6860 |
| main | L4 | structural_trace | CUT_POSITION_OUT_OF_RANGE | 128 |
| main | L5 | gauge_transport | NO_VERTEX_MAP | 9128 |
| main | L5 | structural_trace_max | CUT_POSITION_OUT_OF_RANGE | 128 |
| main | L5 | structural_trace_min | CUT_POSITION_OUT_OF_RANGE | 128 |
| control_shuffled_claims | L1 | structural_trace | CHORD_NO_IMAGE | 48 |
| control_shuffled_claims | L3 | structural_trace | CHORD_NO_IMAGE | 8 |
| control_shuffled_claims | L5 | gauge_transport | NO_VERTEX_MAP | 96 |
| control_cross_betti | none | gauge_transport | BETTI_MISMATCH | 440 |
| control_cross_betti | none | structural_trace | BETTI_MISMATCH | 440 |
