# Dossier 2: Declared degree-4 cochain and finite LP certificate

AuthorityEffect: None.

The supplied matrix complex supports exact checks of adjacent compositions, a pairing of a declared 4-cochain with a cycle, and the degree-4 rational LP certificate. The input's manifold and cup-product claims exceed that evidence.

## What the checker computes

The cochain dimensions are (4, 4, 2, 2, 1). Exact row reduction gives ranks (3, 1, 0, 0) for d0 through d3. Therefore

    b_k = dim(C^k) - rank(d_k) - rank(d_(k-1))

gives Betti numbers (1, 0, 1, 2, 1). The input declares (1, 0, 2, 0, 1), so the checker emits REFUSED_DECLARED_TOPOLOGY_MISMATCH. It does not identify this carrier with a manifold.

The exact flux d1*A = (4,-4) is computed. No cellular diagonal or cup-product map is supplied. Its claimed degree-4 cup square remains UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER; the pairing value is absent.

For the separately declared degree-4 cochain P=(2) and cycle (1), the pairing is 2. Since d3=0, the primal value is 2, the feasible dual witness (1) gives value 2, and the exact duality gap is 0. This certifies the finite LP on its declared inputs.

## Scope and next obligation

The arithmetic does not derive P from a curvature cup square, establish gauge invariance, or identify a Pontryagin or Chern class. Rust replay checks the same finite LP only.

A separate [product-cell ring demo](../../../../../omega_engine_symbol_game/infrastructure/adapters/mssn_scenarios/product_cell_ring.py) declares basis 1,a,b,w, relations a*a=b*b=0, a*b=b*a=w, and derives (p*a+q*b)^2=2*p*q*w by exact bilinear multiplication. Its product-cell interpretation is an input assumption. It does not repair this dossier's inconsistent carrier.

To extend this dossier, supply compatible cellular incidence data and an explicit cup-product map, then check the Leibniz identity, cohomology compatibility and the intended cycle pairing.
