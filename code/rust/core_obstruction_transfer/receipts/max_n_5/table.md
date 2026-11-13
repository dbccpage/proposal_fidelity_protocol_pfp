## Census

| n | beta1 | graphs |
|---|---|---|
| 3 | 1 | 1 |
| 4 | 1 | 2 |
| 4 | 2 | 1 |
| 5 | 1 | 5 |
| 5 | 2 | 5 |

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
| 5 | 1 | 0 | 5 | 25 |
| 5 | 1 | 1 | 14 | 70 |
| 5 | 1 | 2 | 26 | 130 |
| 5 | 1 | 3 | 26 | 130 |
| 5 | 1 | 4 | 14 | 70 |
| 5 | 1 | 5 | 5 | 25 |
| 5 | 2 | 0 | 5 | 125 |
| 5 | 2 | 1 | 15 | 375 |
| 5 | 2 | 2 | 35 | 875 |
| 5 | 2 | 3 | 44 | 1100 |
| 5 | 2 | 4 | 35 | 875 |
| 5 | 2 | 5 | 15 | 375 |
| 5 | 2 | 6 | 5 | 125 |

## Table

| cohort | level | method | pairs | SCORED | NO_HEADROOM | REFUSED | S=1 | S<0 | sum S | NH worse | NH sum(D_tau-D0) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| main | L1 | gauge_transport | 6274 | 3102 | 3172 | 0 | 3102 | 0 | 3102 | 0 | 0 |
| main | L1 | structural_trace | 6274 | 1028 | 1589 | 3657 | 614 | 152 | 1420/3 | 240 | 526 |
| main | L2 | gauge_transport | 356736 | 349596 | 7140 | 0 | 349596 | 0 | 349596 | 0 | 0 |
| main | L2 | structural_trace | 356736 | 92234 | 1438 | 263064 | 41580 | 2978 | 30497159087693/446185740 | 802 | 1652 |
| main | L3 | gauge_transport | 43046 | 29180 | 13866 | 0 | 1310 | 22492 | -369049/6 | 9664 | 38056 |
| main | L3 | structural_trace | 43046 | 29180 | 13866 | 0 | 16939 | 2717 | 15542 | 3693 | 9122 |
| main | L4 | gauge_transport | 763560 | 0 | 0 | 763560 | 0 | 0 | 0 | 0 | 0 |
| main | L4 | structural_trace | 763560 | 346837 | 312923 | 103800 | 161400 | 50411 | 1390667/12 | 93541 | 195617 |
| main | L5 | gauge_transport | 1171968 | 0 | 0 | 1171968 | 0 | 0 | 0 | 0 | 0 |
| main | L5 | structural_trace_max | 1171968 | 542070 | 465182 | 164716 | 270603 | 46362 | 1559513/6 | 78103 | 142376 |
| main | L5 | structural_trace_min | 1171968 | 522372 | 450320 | 199276 | 93386 | 116725 | -698143/12 | 171712 | 410387 |
| control_shuffled_claims | L1 | gauge_transport | 588 | 116 | 472 | 0 | 116 | 0 | 116 | 0 | 0 |
| control_shuffled_claims | L1 | structural_trace | 588 | 40 | 376 | 172 | 40 | 0 | 40 | 0 | 0 |
| control_shuffled_claims | L2 | gauge_transport | 264 | 126 | 138 | 0 | 126 | 0 | 126 | 0 | 0 |
| control_shuffled_claims | L2 | structural_trace | 264 | 104 | 84 | 76 | 104 | 0 | 104 | 0 | 0 |
| control_shuffled_claims | L3 | gauge_transport | 1344 | 898 | 446 | 0 | 18 | 752 | -3799/2 | 411 | 1810 |
| control_shuffled_claims | L3 | structural_trace | 1344 | 882 | 446 | 16 | 389 | 113 | 609/2 | 223 | 710 |
| control_shuffled_claims | L5 | gauge_transport | 2564 | 0 | 0 | 2564 | 0 | 0 | 0 | 0 | 0 |
| control_shuffled_claims | L5 | structural_trace_max | 2564 | 1864 | 700 | 0 | 1677 | 49 | 9845/6 | 83 | 183 |
| control_shuffled_claims | L5 | structural_trace_min | 2564 | 1658 | 660 | 246 | 892 | 250 | 2368/5 | 272 | 873 |
| control_cross_betti | none | gauge_transport | 4740 | 0 | 0 | 4740 | 0 | 0 | 0 | 0 | 0 |
| control_cross_betti | none | structural_trace | 4740 | 0 | 0 | 4740 | 0 | 0 | 0 | 0 | 0 |

| cohort | level | method | refusal code | count |
|---|---|---|---|---|
| main | L1 | structural_trace | CHORD_NO_IMAGE | 3569 |
| main | L1 | structural_trace | CUT_REPEATED | 88 |
| main | L2 | structural_trace | CHORD_NO_IMAGE | 256024 |
| main | L2 | structural_trace | CUT_REPEATED | 7040 |
| main | L4 | gauge_transport | NO_VERTEX_MAP | 763560 |
| main | L4 | structural_trace | CUT_POSITION_OUT_OF_RANGE | 75331 |
| main | L4 | structural_trace | CUT_REPEATED | 22476 |
| main | L4 | structural_trace | CUT_SET_NOT_COTREE | 5993 |
| main | L5 | gauge_transport | NO_VERTEX_MAP | 1171968 |
| main | L5 | structural_trace_max | CUT_POSITION_OUT_OF_RANGE | 120056 |
| main | L5 | structural_trace_max | CUT_REPEATED | 33714 |
| main | L5 | structural_trace_max | CUT_SET_NOT_COTREE | 10946 |
| main | L5 | structural_trace_min | CUT_POSITION_OUT_OF_RANGE | 154616 |
| main | L5 | structural_trace_min | CUT_REPEATED | 33714 |
| main | L5 | structural_trace_min | CUT_SET_NOT_COTREE | 10946 |
| control_shuffled_claims | L1 | structural_trace | CHORD_NO_IMAGE | 172 |
| control_shuffled_claims | L2 | structural_trace | CHORD_NO_IMAGE | 76 |
| control_shuffled_claims | L3 | structural_trace | CHORD_NO_IMAGE | 16 |
| control_shuffled_claims | L5 | gauge_transport | NO_VERTEX_MAP | 2564 |
| control_shuffled_claims | L5 | structural_trace_min | CUT_POSITION_OUT_OF_RANGE | 246 |
| control_cross_betti | none | gauge_transport | BETTI_MISMATCH | 4740 |
| control_cross_betti | none | structural_trace | BETTI_MISMATCH | 4740 |
