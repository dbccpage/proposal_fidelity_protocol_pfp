# Task C051: Exact LP Solver with Dual and Farkas Certificates
Max c^T x s.t. A x <= b, x >= 0.
Emit exact certificates: OPTIMAL (x, y, value), INFEASIBLE (farkas_y), UNBOUNDED (x, ray), OUT_OF_SCOPE (witness).
All values formatted as canonical rational strings: "n" or "n/d" (d > 1, gcd(|n|, d) == 1).
