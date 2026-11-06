# Finite ACSet/DPO cochain rewriting v001

This optional offline pilot asks whether one reusable restricted graph rewrite
executor can repair cochain data while an independent exact judge protects its
meaning. It uses attributed directed graphs, explicit injective matches and
identity-key interface inclusions. Julia is not required.

The seed asks for one registered edge rewrite on a three-vertex rational cycle.
The PFP task-turn template wraps the seed and source/rule inventory; the answer
contains only copied source/rule digests, rule ID, explicit matches and fuel.
The full rule digest binds L, K and R. The model never supplies an acceptance
verdict. The host computes the result digest and remaining fuel in its operation
receipt; replay checks retained bytes and reexecutes the operation before
comparing that receipt. `--prepare` exposes the existing typed PFP boundary.

The judge freezes all vertices and potential values, and preserves oriented edge
multiplicity. An edge may acquire a fresh ID when the DPO operation deletes and
recreates it. For every resulting edge u -> v, the judge separately checks
`cochain(edge) == potential(v) - potential(u)` using `Fraction`. A zero sum of
weights or residuals is insufficient: parallel +1/-1 edges remain nonexact.
This checks a supplied fixed potential; it does not minimize a quotient norm.

From the repository root:

```powershell
python -m omega_engine_adversary.tests.pilots.acset_cochain_rewriting.run --prepare
python -m omega_engine_adversary.tests.pilots.acset_cochain_rewriting.run --fixture
python -m omega_engine_adversary.tests.pilots.acset_cochain_rewriting.run --reply reply.json
python -m pytest omega_engine_adversary/tests/pilots/acset_cochain_rewriting/tests/test_acset_cochain_rewriting.py -q
```

The 25 distinct tests cover orientation, disconnected components, exact rationals,
loops, parallel edges, cancellation, fixed potentials, topology, typed rational
ingress, structural versus mathematical acceptance, source/rule/match/fuel/result
tampering and zero-send PFP replay. The default command requires an explicit mode;
`--fixture` constructs a labelled host fixture, never an actual model response.

These are `NO_LLM` checks with zero provider sends. They establish neither better
single-shot model results nor token savings, universal confluence, a Meron physical
bridge or an observed provider bill. Any later paid trial stays under the existing
continuing $0.05 gate. `AuthorityEffect: None`.
