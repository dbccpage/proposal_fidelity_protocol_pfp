# Native functional conformance fixtures

AuthorityEffect: None.

These six finite cases were authored for the Windows campaign. They are not
recovered historical fixtures: neither referenced JSON file exists in the
current tracked tree or the inspected reachable Git history. The old test path
pointed into an absent archive. Keeping that path produced setup failures.

## Independent expected calculations

Use integer coordinates and unit weights. For each valid complex, d0 is the
column (1, 0), so its image contains exactly vectors whose second coordinate is
zero. The first coordinate can be repaired; the second cannot.

| Case | Independent calculation | Expected result |
| --- | --- | --- |
| closed | (0, 1) dot (4, 0) = 0 | Gamma2 = 0 |
| open_negative_coordinate | abs((0, 1) dot (4, -3)) = 3 | Gamma2 = 3 |
| non_cochain | (1, 0) dot (1, 0) = 1 | CochainIdentityViolation at (0, 0) |
| exact | (2, 0) - d0 times 2 = (0, 0) | ExactRepair diagnostic |
| closed_residual | distance of (0, 3) to im(d0) is 3; d1 is zero | ClosedResidual diagnostic |
| active_closure | same distance 3; (0, 1) dot (0, 3) = 3 | ActiveClosureFailure diagnostic |

The last two Phi1 certificates use dual witness (0, 1). It annihilates d0,
has weighted dual norm one, and pairs with (0, 3) to give 3. The matching primal
and dual bounds establish that finite distance independently of the native
solver. The exact-repair case uses a zero dual witness and matching zero bounds.

The JSON retains the historical vector vocabulary StabilizedSurvivor and
OpenObstruction as input labels, mapped explicitly to the current diagnostic
enum. These labels confer no terminal, mathematical publication, licensing or
workload-completion authority. No external service or generated code executes.

The test asserts the complete case identities, schema and authority label;
missing, empty or unexpected populations cannot silently pass. Negative cases
name the exact refusal variant, not just a generic error.
