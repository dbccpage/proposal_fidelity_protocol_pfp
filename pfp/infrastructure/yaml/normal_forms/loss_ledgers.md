# Loss Ledgers

Status: Operational semantics.
AuthorityEffect: None

A loss ledger records distinctions erased by representation transport, compression, redaction, summarization, projection, approximation, or forgetting.

Use `Loss(F)` for a transport `F`.

### Required Schema & Canonical Example:

```yaml
loss_ledger_id: ledger.transport.cpnf.001
transport: F_lowering_ast
source_representation: ast.decorated_symbol_tree.v1
target_representation: bytecode.linear_opcode_stream.v1
erased_distinctions:
  - field: inline_type_annotations
    reason: projection
    authority_impact: bounded
  - field: local_variable_names
    reason: compression
    authority_impact: none
residual_budget:
  Phi: "0/1"
  Gamma: "0/1"
  Xi: "0/1"
terminal_route: CompileOk
non_claims:
  - does not prove semantic preservation of erased source distinctions
  - forward replay establishes target reproducibility rather than source inversion
```

Rule: if `F` erases attributes, precision, lineage, predicates, joins, or provenance and no loss ledger is present, `TransportOK(F)` must fail.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
