# Testing and Falsification

## Evidence rule

A passing test establishes only its named predicate for the tested checkout,
runtime, inputs, and dependency set. It does not promote a declared architecture or
mathematical analogy into an implementation fact.

## Current review gates

| Surface | Result | Bounded interpretation |
| --- | ---: | --- |
| Combined scoped pytest suite | 208 passed, 4 subtests passed | OEWAS and `.agents/operad`; one out-of-scope cross-package test excluded |
| OEWAS-only pytest suite | 106 passed | Current OEWAS tests excluding the same cross-package test |
| OEWAS migration/projection focused regression | 6 passed | Repaired mappings, byte custody, and projection expectation agree |
| `.agents/operad` unittest discovery | 73 passed | Existing unittest assertions pass |
| Skill Compiler focused unittests | 24 passed | Overlaps the 73-test discovery |
| Skill Compiler budget tests | 5 passed | Existing expiry/live cases only |
| Skill Compiler live eval bank | 16 passed | Current cases route as expected |
| Governed-root budget gate | 5 roots passed | Current roots fit budgets; bypass cases remain |
| Knowledge-parity gate | passed | Current finite doctrine scan is clean |
| Route/cull integration | 5 passed | Current references satisfy the checked rules |
| Residual honesty gate | passed | Seven rows remain diagnostic; vocabulary check is narrow |
| Canonical operad validator | **failed** | Three missing unit-law registrations |

Both pytest runs emitted one third-party FastAPI/Starlette deprecation warning.
One adjacent-package integration is deliberately outside this atlas scope.

## High-value missing falsifiers

### Documents and parser

- tilde fences, variable-length fences, indentation, CRLF, and unterminated fences;
- parsed composition slots through the higher-operad adapter;
- mutation coverage for every semantic-digest field;
- rejection of sentinel evidence digests in admitted lifecycle state;
- estate path traversal and root-containment cases.

### Composition and workflows

- negative, duplicate, missing, and out-of-range slots;
- child-operation identity and expected-boundary mismatch;
- forged/mismatched units and duplicate operation IDs;
- duplicate workflow nodes and edges;
- catalog resolution for every workflow operation;
- reachability, completion, dead-task, and effect-conflict cases.

### Persistence and security

- full aggregate save/load semantic equality;
- journal payload roundtrip;
- catalog digest mutation for source, profile, schema, lifecycle, and composition;
- HMAC tampering of manifest ID and algorithm;
- empty/weak key policy;
- outbox with no subscriber, partial fanout, retry, and concurrent dispatchers.

### Migration and compiler

- duplicate manifest IDs, malformed digests, escaped YAML, and path containment;
- budget exceptions that are unapproved, expired, or exceed declared maxima;
- live register format, structural-injection text, concurrent promotion, and receipt
  failure rollback;
- route precedence overlap and generic-doctrine false positives;
- empty, malformed, and duplicate evaluation-bank cases;
- receipt replay after Git history changes.

### Reference operad

- invoke the canonical validator from tests and require its exit status;
- build unit registrations after every closure operation;
- reject undeclared colours and residual vocabulary;
- prove JSON repository roundtrip equivalence;
- detect outer-residual duplication and unsafe identity shortcuts;
- prevent scalar diagnostics from producing contractivity labels;
- require full workflow-step licensing without licensing the workflow ID itself.

## Mutation-testing pattern

For every integrity claim, retain one known-good fixture and mutate exactly one
field at a time:

```text
good bytes -> accepted
mutate covered field -> rejected or digest changes
mutate uncovered field -> documented noncoverage, then repair
```

This is more informative than adding happy-path volume. It turns the digest and
validator boundary into a machine-checkable coverage map.

## Replay receipt template

```yaml
schema: oewas.test_receipt.v1
authority_effect: none
git_head: <sha256-like Git object id>
dirty_paths: []
command: <exact argv>
runtime: <implementation and version>
inputs: [{path: <path>, sha256: <digest>}]
result: {exit_code: 0, passed: 0, failed: 0, skipped: 0}
nonclaims: [<what this gate does not establish>]
```

The schema is proposed documentation, not an implemented receipt type.
