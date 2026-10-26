# Catalog Lifecycle and Architecture

## Catalog flow

```text
estate bytes
  -> parse skill documents
  -> compile operations and compositions
  -> persist catalog and journal events
  -> verify bounded invariants
  -> project a capability view
```

The handlers expose compile, get, verify, projection, workflow validation, and
licensed-term surfaces. The implemented flow is a shadow catalog pipeline, not an
execution scheduler.

## Compilation

Compilation reads an estate, parses skill files, builds a catalog, and records
events through a unit of work. Idempotency mechanisms exist for selected requests.
Important limits are:

- parse/read failures can be omitted instead of becoming explicit refusals;
- the catalog digest hashes sorted operation identifiers rather than complete
  operation/document semantics;
- wall-clock values make some receipts time-dependent;
- the application operad compiler performs filesystem and YAML I/O directly.

The digest must be described as an operation-ID set commitment, not catalog
integrity.

## Verification

Verification exercises only the aggregate fields available after loading. Because
SQLite persistence drops documents, leaves, operands, compositions, residuals,
proven roots, and capability slices, a post-roundtrip verification cannot verify
the original in-memory aggregate. This is the most consequential boundary between
the declared architecture and current behavior.

## Projection

Projection returns a bounded view, but the requested output format is not fully
honored. A projection does not confer lifecycle admission, executor binding, or
authority.

## Licensed-term compilation

The endpoint exists but always refuses without a license witness. Until a witness
type, verifier, provenance binding, and replay tests exist, this refusal is the
correct behavior.

## Clean Architecture assessment

The package separates domain, application, controllers/frontends, and
infrastructure. Dependency tests protect part of that boundary. Two issues keep the
strong “strict Clean Architecture” claim from being current:

1. application compiler code performs direct filesystem and YAML operations;
2. the composition root does not integrate all documented subsystems into one
   runtime.

The architecture is a useful direction with enforceable islands, not a completed
production boundary.

## Catalog invariants to make explicit

- document and operation identifiers are unique;
- every composition reference resolves;
- every slice reference resolves;
- lifecycle evidence digests are non-sentinel and domain-separated;
- catalog integrity commits to canonical documents, operations, compositions, and
  relevant provenance;
- save/load roundtrips preserve the complete semantic aggregate;
- verification failures survive persistence as structured evidence.

Each invariant needs both a constructor or handler check and a falsification test.
