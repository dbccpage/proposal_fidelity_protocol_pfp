"""Declared metaskill signatures; execution requires the canonical registry."""

METASKILL_SIGNATURES = {
    "meta-atlas-state-to-state-verifier": (
        ("State",),
        "State",
        "Enforces atlas package directories, lakefiles, notebooks",
    ),
    "meta-auto-paper-to-paper-verifier": (
        ("Paper", "Audit"),
        "Paper",
        "Applies audit remediations to research paper manuscripts",
    ),
    "meta-auto-state-to-receipt-verifier": (
        ("State", "Audit"),
        "Receipt",
        "Validates worktree state against audit findings; emits receipt",
    ),
    "meta-blackrod-contract-to-audit-verifier": (
        ("Contract",),
        "Audit",
        "Audits Nomos contracts against Blackrod enforcer standards",
    ),
    "meta-code-audit--code--contractive": (
        ("Code", "Audit"),
        "Code",
        "Applies code audit remediations contractively",
    ),
    "meta-contract-audit--contract--contractive": (
        ("Contract", "Audit"),
        "Contract",
        "Refines Nomos contracts to resolve audit findings",
    ),
    "meta-contract-code--audit--contractive": (
        ("Contract", "Code"),
        "Audit",
        "Verifies code implementations against contract boundaries",
    ),
    "meta-dda-dag-emitter": (
        ("Receipt",),
        "Diagram",
        "Parses DDA trace receipts and emits Mermaid DAG diagrams",
    ),
    "meta-glossa-proof-to-proof-verifier": (
        ("Proof",),
        "Proof",
        "Audits Lean 4 proofs for dialect/lexicon compliance",
    ),
    "meta-goo-ledger-to-ledger-verifier": (
        ("Ledger", "Paper"),
        "Ledger",
        "Reconciles claim ledgers against paper text (1:1 bijection)",
    ),
    "meta-goo-paper-to-paper-verifier": (
        ("Paper",),
        "Paper",
        "Verifies research paper deposit envelopes and canonical structures",
    ),
    "meta-goo-proof-to-audit-verifier": (
        ("Proof", "Code"),
        "Audit",
        "Compares Lean 4 proofs with test suites for semantic parity",
    ),
    "meta-kybernesis-paper-to-post-verifier": (
        ("Paper", "Proof"),
        "Post",
        "Synthesizes public math posts from papers and formal proofs",
    ),
    "meta-law-contract-enforcer": (
        ("Contract", "Code"),
        "Audit",
        "Continuous legal audit: code adherence to Nomos contracts",
    ),
    "meta-no-comments": (
        ("Code", "Audit"),
        "Code",
        "Erases comments while preserving docstrings and test files",
    ),
    "meta-paper--audit--contractive": (
        ("Paper",),
        "Audit",
        "Audits paper packages against structure and claim hygiene",
    ),
    "meta-paper--receipt--contractive": (
        ("Paper",),
        "Receipt",
        "Validates paper deposit envelopes; emits deposit receipts",
    ),
    "meta-proof-code--proof--contractive": (
        ("Proof", "Code"),
        "Proof",
        "Refines Lean 4 formalization using solver witness data",
    ),
    "meta-proof-to-paper-verifier": (
        ("Proof", "Code"),
        "Paper",
        "Generates paper claim tables from Lean proofs and test suites",
    ),
    "meta-residual-harmonic-optimizer": (
        ("Ledger", "Audit"),
        "Receipt",
        "Derives persistent residual invariants in optimization loops",
    ),
    "meta-state--receipt--contractive": (
        ("State",),
        "Receipt",
        "Evaluates worktree state and mirror parity; emits receipt",
    ),
    "meta-state--state--contractive": (
        ("State",),
        "State",
        "Enforces clean worktree, UTF-8 normalization, mirror parity",
    ),
    "meta-techne-code-to-audit-verifier": (
        ("Code",),
        "Audit",
        "Audits Clean Architecture inward dependencies and layer purity",
    ),
    "meta-techne-code-to-code-verifier": (
        ("Code",),
        "Code",
        "Deterministically formats code and standardizes interfaces",
    ),
}
