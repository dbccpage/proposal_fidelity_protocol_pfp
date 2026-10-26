# Skill Documents and Ingestion

## Value objects

The domain supplies strict identifiers, SHA-256 digests, source spans, authority
effects, lifecycle facets, and operand references. Construction rejects several
obvious shape errors, which is useful local evidence. It does not make the enclosing
aggregate deeply immutable or prove cross-reference completeness.

`SkillLifecycleV3` is best understood as five orthogonal facets:

1. declaration;
2. schema binding;
3. executor binding;
4. validation;
5. admission.

An operation is executable only when all five states are satisfied and both
required digests are present. This is a predicate over metadata; the reviewed tree
does not provide a general executor that follows from the predicate.

## Document aggregate

`SkillDocumentV3` can retain:

- raw and semantic digests;
- byte-addressed leaves and source spans;
- artifact operand references;
- operation declarations;
- composition declarations;
- a declared proven root.

Document equality is narrower than semantic equality: it uses the document ID and
raw digest. Mutable dictionaries inside otherwise frozen DTOs and hashable
aggregates deserve caution.

## Parser: actual accepted language

The infrastructure adapter is a regular-expression parser for selected fenced YAML
blocks. It recognizes declarations such as:

```text
oewas.operand.v3
oewas.operation.v3
oewas.composition.v3
```

It preserves the original bytes as prose and code-fence leaves with byte spans.
That is useful loss-aware behavior for its accepted syntax. It is not a complete
CommonMark parser and does not cover all fence forms, indentation rules, tilde
fences, variable fence lengths, or malformed/unterminated constructs.

## Parser-generated meaning

When declarations omit data, the parser currently supplies defaults, including
colours, schema references, all-zero digests, lifecycle state, and a first-operation
`proven_root`. These are implementation conveniences, not facts extracted from the
source. An admitted lifecycle should reject sentinel digests rather than let a
default resemble evidence.

The semantic digest also covers less than the full document semantics. Mutation
tests should establish exactly which changes it binds.

## Confirmed slot-type defect

Parsed composition slot keys are converted to strings, while the higher-operad
adapter compares slots as integers. A parsed composition can therefore reach a
string-versus-integer comparison and fail before returning a structured refusal.
The repair is small—normalize and validate slot indices once at the parser
boundary—but it needs an integration test that passes parser output into the
adapter.

## Estate source boundary

The filesystem adapter enumerates direct `.agents/skills/*/SKILL.md` files. Its
`read_skill_bytes` path join does not demonstrate root-containment enforcement, and
the supplied `estate_ref` is not a meaningful isolation boundary. Callers must not
be allowed to traverse outside the configured root.

## Ingestion contract to adopt

```text
bytes
  -> syntax parse with exact spans
  -> schema validation
  -> reference/type validation
  -> lifecycle/evidence validation
  -> explicit admission decision
```

Each arrow should return typed diagnostics. No stage should silently fabricate a
later stage, and failure at one stage should not be described as success at another.

## Nonclaims

- Byte-span preservation for recognized leaves is not full-source semantic
  losslessness.
- A semantic digest is not complete unless its covered fields are enumerated and
  mutation-tested.
- A schema-conforming operation is not executable, admitted, or authorized.
- A declared proven root is not a proof.
