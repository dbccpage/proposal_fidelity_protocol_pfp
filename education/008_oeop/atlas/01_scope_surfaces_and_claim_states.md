# Scope, Surfaces, and Claim States

## Review boundary

The audit froze two Git path sets at
`c86134f8c05c2b530607e3ec0c882c63d230d3f6`:

```text
omega_engine_workflows_agents_skills/**  166 paths
.agents/operad/**                          65 paths
                                         ---------
                                         231 paths
```

Every tracked path is assigned an owning chapter in the
[file ledger](11_file_by_file_audit_ledger.md). Untracked caches, generated Python
bytecode, and adjacent packages are outside this evidence set.

## Four bounded contexts

| Context | What exists | What must not be inferred |
| --- | --- | --- |
| OEWAS V3 | Documents, operations, catalogs, lifecycle facets, handlers, ports, adapters | Production cutover, complete execution, or global authority |
| OEWAS local operad | Ten colours, planar profiles, partial substitution, units, witnesses | Symmetric action, equivariance, or behavioral equivalence |
| OEWAS legacy/migration | V1/V2 snapshots, Woland projection, successor-byte manifest | Semantic preservation or successor admission |
| `.agents/operad` | Reference registry, compatibility API, dispatch, residual diagnostics, compiler | Execution, promotion authority, or contractivity certification |

The contexts share vocabulary but not one canonical aggregate or persistence
schema. A central improvement is to choose an owner for each concept and make all
other surfaces explicit adapters.

## Authority model

The V3 enum has four effects:

```text
None < EvidenceOnly < FactOnly < StateTransition
```

The reviewed package declares `AuthorityEffect: None`. The ordering is a type-level
ceiling mechanism, not evidence that higher effects are licensed. The reference
operad and skill compiler likewise produce resolutions, proposals, diagnostics,
and receipts without granting authority.

## Architecture as implemented

```text
frontends/controllers
        |
application commands, queries, ports, DTOs
        |
domain entities, values, and planar operad scaffold
        ^
infrastructure adapters, SQLite, filesystem, parser, projection
```

This dependency direction is partly enforced by architecture tests. It is not
strict throughout: the application operad compiler directly reads files and YAML.
The composition root also leaves signing, outbox dispatch, migration, local-operad
services, and anti-skill admission as separate subsystems.

## Evidence hierarchy

From strongest to weakest in this snapshot:

1. exact source bytes and Git object identity;
2. replayable tests bound to a named checkout;
3. canonical digests over explicitly enumerated fields;
4. schema validation and typed construction;
5. declared prose contracts;
6. conceptual diagrams and research analogies.

A stronger-looking name does not move an artifact upward. For example, a
`VerificationReceipt` that records only operation identifiers does not commit to
the operation schemas, source, lifecycle, or composition graph.

## Canonical terminology

- **Skill document**: parsed source plus spans, operands, operations, and
  compositions.
- **Operation**: a typed input profile, output colour, lifecycle, and authority
  ceiling.
- **Composition**: substitution of child operations into ordered parent slots.
- **Catalog**: an aggregate over documents and operations for one estate/epoch.
- **Capability slice**: a bounded selection or projection; not execution authority.
- **Residual**: a diagnostic difference or obstruction; not automatically a metric
  or proof.
- **Dispatch**: resolution of a registered operation; the current reference API
  returns `RESOLVED_NOT_EXECUTED`.
- **Admission**: an explicitly governed state transition requiring evidence and,
  where specified, a human decision.
