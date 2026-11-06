# Demo 9: Degree-4 finite certificates and a topology boundary

## Current packaged execution

AuthorityEffect: None. The installed catalog owns current runs.

```console
symbol-game demo run demo_9 --output-dir ./runs/demo_9
symbol-game demo verify ./runs/demo_9/receipt.json
```

Current scope: Named functionals require an explicitly pinned Rust adapter. Historical values are not newly computed.

See the [migration ledger](../../migration/README.md) for source custody,
intentional behavior changes, native refusals, and the offline release gate.

## Historical baseline notes

The following describes the pre-migration research demonstration. Its old
runner commands and recorded values are historical; use the packaged commands
above for current execution. This migration does not refresh its evidence.

AuthorityEffect: None.

The two dossiers check rational cochain matrices and degree-4 primal/dual certificates. Dossier 2 also rejects an unsupported topological interpretation.

| Dossier | Checked finite result | Scope |
|---|---|---|
| Hollow 5-simplex fixture | Nilpotent adjacent differentials; closed bounded dual cycle; Phi4 = 1 and zero gap | Declared finite boundary complex |
| Declared degree-4 cochain | Pairing = 2; Phi4 = 2 and zero gap | Matrix carrier has Betti (1,0,1,2,1), which conflicts with the declared (1,0,2,0,1) |

## Learn the arithmetic first

For a degree-4 cochain G, compute

```text
Phi4([G]) = min_C sum_i weights_i * abs(G_i - (d3*C)_i).
```

A candidate dual vector v must satisfy transpose(d3)*v = 0 and abs(v_i) <= weights_i. When its pairing with G matches the feasible primal value exactly, the finite LP certificate is accepted.

The first dossier's negative norm fixture now scales the entire closed cycle by 2, so it reaches the norm check without first breaking closure. The second dossier's positive-gap probe uses a feasible zero dual witness against G=(2).

## The cup-product boundary

A matrix differential does not specify multiplication of cochains. Dossier 2 previously assigned the exact-flux cup-square result to zero without evaluating a product. The checker now leaves that value absent and emits UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER.

Exact row reduction also contradicts the fixture's stated Betti numbers. Its runner returns REFUSED_DECLARED_TOPOLOGY_MISMATCH for the topological scope while retaining a separate PASS for the finite LP.

See the [dossier scope](dossier_2_pontryagin_chern_4manifold/claim.md) and the separate [declared product-cell ring demo](../../../../omega_engine_symbol_game/infrastructure/adapters/mssn_scenarios/product_cell_ring.py). That demo derives (p*a+q*b)^2=2*p*q*w using an explicit multiplication table.

## Run

run_demo9.py requests the existing Rust degree-4 verifier and prints both the LP outcome and the scope refusal. The [system coverage runner](../demo_system_coverage/README.md) performs fresh Python fixture replays with optional Rust checks marked NOT_REQUESTED.

Historic checker_output.json files describe earlier source behavior. Use the source- and output-bound fresh receipt under ../demo_system_coverage/selected_evidence.json for this revision.
