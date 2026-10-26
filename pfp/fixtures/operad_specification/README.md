# Operad architecture reference metadata

AuthorityEffect: None.

`reference.json` and `reference.yaml` describe the same finite example.
`architecture_spec.schema.json` is generated from
`omega_engine_pfp.domain.operad.specification.ArchitectureSpec`.

Use `parse_architecture_json(raw_utf8_json)` for JSON input. It rejects duplicate
keys before Pydantic validation. A YAML consumer must reject duplicate mapping
keys itself before serializing the decoded value to JSON; this package does not
supply a YAML loader. Strict frozen models preserve tuples and reject unknown
fields, boolean/float integer aliases, and noncanonical rational strings.

The metadata validators check the supplied UTF-8 source bytes, half-open byte
spans and hashes, nominal colour references, finite topological graft trees,
slot permutations, declared work limits/effect classes, artifact references,
DPO obligation bindings, finite bundle ranks/cocycle declarations, tensor-factor
shapes, and the declared two-factor partial-trace input/output relationship.

The model performs no rewrite, graph search, density arithmetic, PSD check,
signature verification, theorem checking, or external artifact loading. The
reference evidence text is deliberately an unverified declaration rather than a
proof. Passing metadata validation therefore does not establish operadic
associativity/equivariance, bundle gluing, channel laws, Wilsonian interpretation,
normal-form convergence, DPO confluence, trusted signing, or native acceptance.
A `NullTreeNode` is a typed failed term and is distinct from any density matrix.

The existing bounded DPO owner is
`omega_engine_pfp.domain.rewriting.finite_dpo.apply_registered_rule`. It supports
one finite attributed directed-graph schema with identity-key monic interfaces.
Exact density/partial-trace execution belongs to
`omega_quantum_physics::density_matrix::ExactDensityMatrix`. Signature metadata
names the existing EIS authenticated verification source; an explicit trust
policy artifact is required, and cryptographic verification remains unperformed.

The unsigned benchmark example supplies no signature. A `signed_metadata` record
requires signature/key bytes and a trust-policy artifact, while retaining
`signature_status: supplied_not_cryptographically_verified`.

The focused source-level validation suite is
`omega_engine_pfp/tests/test_operad_specification.py`. It includes forged source
bindings, UTF-8 boundary cuts, nominal/permutation/type errors, node reuse,
missing DPO/cocycle obligations, unrelated owner references, matrix-claim
laundering, and signed/unsigned receipt confusion controls.
