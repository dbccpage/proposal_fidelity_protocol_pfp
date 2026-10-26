# Source-to-contract experiment v1

This example exercises the existing typed compiler, task selector and signed
instruction-admission port. Its retained source is
`catalog/contracts/v1/woland_claim_audit.json`, SHA-256
`b81f25486057701057f0d5bac9628324768e98824f8f11b6252d8ee6214dcb28`.
The independent contextual requirement is the literal ordered signature
`(findings: Audit, subject: Contract) -> receipt: Receipt`, with explicit schema
and validator revision pins. It is not an arity copied from a compiled operation.

Run from the repository root with OpenSSH's `ssh-keygen` available:

```text
python -B -m omega_engine_operads.documentation.examples.prior_art_contract_binding --repo-root . --output .scratch/source-contract/result.json
```

The example compiles actual retained resources, selects the bounded one-operation
route and verifies a real signature made with a temporary fixture key. It then
requires the production admission port to refuse a swapped input order, omitted
input, foreign source pin and different candidate body. Keys and signatures are
deleted when the example finishes. This installs no trusted key, production
admission or learned detector, and makes no provider call. Its output retains
the source, task and candidate digests and each actual refusal code.

The contextual controls revealed that admission compared a signed task-shape
digest with a stale selection without recomputing it from the supplied task.
Admission now uses the selector's existing digest profile to check the current
ordered inputs, output, required operations, capabilities and bounds. The wire
profile and valid historical task digests are unchanged.

The fixed source, schema and validator pins deliberately make this a versioned
experiment. An intentional revision requires a reviewed successor context; do
not weaken the context to accept new output. Tests additionally cover an
incompatible schema, changed output and narrower effect ceiling. Current
instruction admission and OEEIS activation remain separate decisions.

This finite experiment demonstrates source/context custody and a repaired
admission check. It does not establish that PICARD, homotopy invariance or any
paper's meaning has been extracted into an operation. General interpretation
and automatic factorization remain research questions. The full prior-art
inventory audit and its retained source custody have separate owners.

AuthorityEffect: None.
