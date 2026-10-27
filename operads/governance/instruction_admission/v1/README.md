# Adversary instruction-plan admission v0.1

This is the OEWAS governance home for human-approved instruction-plan decisions.
Keep small instruction bodies in `catalog/operands/v1/<domain>/<id>.md` and
leave `.agents` as a discovery/projection surface. OEEIS separately admits
anti-skills and activates guards; this directory cannot approve either.

An approval consists of a canonical UTF-8 JSON manifest and its detached
OpenSSH `.sig`. The JSON has exactly these fields:

`schema_version`, `decision`, `reviewer_identity`, `authority_effect`,
`request_digest`, `task_shape_digest`, `workload_profile_id`,
`workload_profile_digest`, `domain_id`, `selection_digest`, `route_id`,
`plan_digest`, `source_snapshot_digest`.

The only accepted schema is `oewas.adversary.instruction_admission.v0.1`, the only
accepted decision is `APPROVE`, and `authority_effect` must be `None`. The
manifest uses sorted keys, compact JSON separators, ASCII escaping, and one
terminal newline. All digests are lowercase `sha256:<64 hex>` references.
The approver signs those exact bytes with:

```text
ssh-keygen -Y sign -f <human-private-key> -n oewas-adversary-instruction-v0.1 <manifest.json>
```

The verifier requires an operator-maintained `allowed_signers` file supplied
outside the manifest and operand tree. Never check in a private key or let a
manifest designate its own trusted signer list. Source content, profile and
task binding, route selection, and signature are rechecked on each proposed
dispatch. A signature is not a semantic model-behavior proof.

Adversary has an opt-in signed-ingress adapter that re-reads configured source
files and produces a typed request-bound native transport receipt after this
verification. An operator must separately fix the domain and a declared Adversary
profile, provide one immutable exact-request task boundary and an external
signer trust root; none may come from the operand or objective prose. Ingress
compares the task and routes against the canonical profile digest and a fresh
native specialization verdict.
The default service does not configure the adapter.

No production approvals live here yet. The checked-in Adversary operand specimens
remain structurally unbound and unadmitted; do not make an approval file merely
to turn a test green. The verifier can now project its selected exact bodies
into a bounded native transport, and fixture bouts prove prompt consumption and
run-bundle custody. Native live execution still refuses: the host does not yet
verify a human signer or task/plan-bound OEEIS decision, so this directory
currently grants no live execution.
