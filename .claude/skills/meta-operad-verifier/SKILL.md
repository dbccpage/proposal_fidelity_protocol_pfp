---
name: meta-operad-verifier
description: "Shared engine and catalog for the meta operad operations. Colour matching, placement law and residual evidence bar."
status: canonical
invocation: discipline
operad_source_colours: []
operad_target_colour: "Audit"
operad_arity: 0
operad_residual: "unknown"
families: [meta, operad]
---

# meta-operad-verifier

`AuthorityEffect: None.`

## Operadic Metaskill Execution Engine

The 24 `meta-*` packages operate as functional morphisms in the repository's colored operad:

$$\mathcal{O}(C_1, \ldots, C_k) \longrightarrow C_\text{target}$$

The 24 packages declare signatures and expose CLI entrypoints. Entrypoint presence is not execution coverage: no evaluator is admitted by default. An unimplemented operation returns `NOT_EXECUTABLE`; a successful bounded evaluator must be named in the actual execution record. Declared scope, finite execution and OEEIS admission remain separate.

## Placement Law

An operation with target colour $T$ may be placed anywhere the next operation's open slot has input colour $T$. Any other placement is an error, not a warning. Colour matching is necessary and **not** sufficient: it licenses the wiring, not the claim.

## The Residual-Evidence Bar

An operation without residual evidence may not be cited as evidence and may not be relied on in a pipeline that promises a residual decrease. Finite residual observations remain diagnostics, regardless of their count. A general contractivity claim requires an independently checked statement with premises and scope. Without that evidence the declared residual stays `unknown`; preserve the original observations without promoting them.

## Signature Register (24 Metaskills)

| Package | Consumes | Produces | Responsibility |
| --- | --- | --- | --- |
| `meta-atlas-state-to-state-verifier` | State | State | Enforces atlas package directories, lakefiles, notebooks |
| `meta-auto-paper-to-paper-verifier` | Paper, Audit | Paper | Applies audit remediations to research paper manuscripts |
| `meta-auto-state-to-receipt-verifier` | State, Audit | Receipt | Validates worktree state against audit findings; emits receipt |
| `meta-blackrod-contract-to-audit-verifier` | Contract | Audit | Audits Nomos contracts against Blackrod enforcer standards |
| `meta-code-audit--code--contractive` | Code, Audit | Code | Applies code audit remediations contractively |
| `meta-contract-audit--contract--contractive` | Contract, Audit | Contract | Refines Nomos contracts to resolve audit findings |
| `meta-contract-code--audit--contractive` | Contract, Code | Audit | Verifies code implementations against contract boundaries |
| `meta-dda-dag-emitter` | Receipt | Diagram | Parses DDA trace receipts and emits Mermaid DAG diagrams |
| `meta-glossa-proof-to-proof-verifier` | Proof | Proof | Audits Lean 4 proofs for dialect/lexicon compliance |
| `meta-goo-ledger-to-ledger-verifier` | Ledger, Paper | Ledger | Reconciles claim ledgers against paper text (1:1 bijection) |
| `meta-goo-paper-to-paper-verifier` | Paper | Paper | Verifies research paper deposit envelopes and canonical structures |
| `meta-goo-proof-to-audit-verifier` | Proof, Code | Audit | Compares Lean 4 proofs with test suites for semantic parity |
| `meta-kybernesis-paper-to-post-verifier` | Paper, Proof | Post | Synthesizes public math posts from papers and formal proofs |
| `meta-law-contract-enforcer` | Contract, Code | Audit | Continuous legal audit: code adherence to Nomos contracts |
| `meta-no-comments` | Code, Audit | Code | Erases comments while preserving docstrings and test files |
| `meta-paper--audit--contractive` | Paper | Audit | Audits paper packages against structure and claim hygiene |
| `meta-paper--receipt--contractive` | Paper | Receipt | Validates paper deposit envelopes; emits deposit receipts |
| `meta-proof-code--proof--contractive` | Proof, Code | Proof | Refines Lean 4 formalization using solver witness data |
| `meta-proof-to-paper-verifier` | Proof, Code | Paper | Generates paper claim tables from Lean proofs and test suites |
| `meta-residual-harmonic-optimizer` | Ledger, Audit | Receipt | Derives persistent residual invariants in optimization loops |
| `meta-state--receipt--contractive` | State | Receipt | Evaluates worktree state and mirror parity; emits receipt |
| `meta-state--state--contractive` | State | State | Enforces clean worktree, UTF-8 normalization, mirror parity |
| `meta-techne-code-to-audit-verifier` | Code | Audit | Audits Clean Architecture inward dependencies and layer purity |
| `meta-techne-code-to-code-verifier` | Code | Code | Deterministically formats code and standardizes interfaces |

## Disambiguation of Signature Collisions

Three signature pairs share identical input/output colours but differ fundamentally in domain operational semantics:

1. **`{State} -> State`**:
   - `meta-atlas-state-to-state-verifier`: Specifically inspects and verifies directory layouts, lakefiles, and notebooks under `coda_atlas/`.
   - `meta-state--state--contractive`: Operates across the root repository, enforcing UTF-8 line endings, git hygiene, and host root mirror parity.
2. **`{Contract, Code} -> Audit`**:
   - `meta-contract-code--audit--contractive`: Performs AST-level symbol and boundary compliance between code modules and contract interface schemas.
   - `meta-law-contract-enforcer`: Evaluates Nomos legal compliance, enforcing authority ceilings (`AuthorityEffect: None`) and licensing boundaries.
3. **`{Code, Audit} -> Code`**:
   - `meta-code-audit--code--contractive`: Applies structured refactorings to remediate architectural findings from audit reports.
   - `meta-no-comments`: Deterministically strips inline commentary from production code while strictly preserving docstrings, license notices, and test suites.

## Verification & Execution

Execute any metaskill via its local runner:

```bash
python operads/skills/<skill_name>/scripts/execute.py
```

Or invoke via the unified execution engine:

```bash
python -m operads.frontend.cli.meta_operad_cli <skill_name>
```
