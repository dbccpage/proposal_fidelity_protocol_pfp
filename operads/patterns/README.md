# Colored Operad Pattern Estate

**AuthorityEffect:** None.

This directory tracks code anti-patterns and healthy patterns as operations within a coloured planar multicategory (colored operad).

## 1. Operad Architecture & Pattern Duality

In the engine operad architecture, code analysis, defect detection, and refactoring are represented as morphisms between typed colors:

- **Colors:**
  - `Code`: Source code syntax, AST, and module trees.
  - `Audit`: Operational verification context, constraints, and test receipts.
  - `Witness`: A typed defect witness / anti-pattern observation ($\Omega^-$).
  - `Remediation`: A localized transformation policy.
  - `Receipt`: A verification record binding findings to deterministic checks.

- **Morphism Duality (Anti-Pattern $\dashv$ Healthy Pattern):**
  - **Anti-Pattern Morphism ($A \in \text{Operad}(\text{Code}; \text{Witness})$):**
    An anti-pattern is an antibody / anti-morphism that inspects `Code` and extracts a non-empty `Witness` if a structural flaw or hazard is present.
  - **Healthy Pattern Morphism ($H \in \text{Operad}(\text{Code}; \text{Code})$):**
    A healthy pattern is a contractive endomorphism that transforms or structures `Code` such that the paired anti-pattern morphism evaluates to empty residual:
    $$\|A(H(c))\| = 0$$
  - **Composition:**
    $$A \circ H = \text{EMPTY}$$

## 2. Directory Layout

```text
.agents/patterns/
├── README.md               # This architectural specification
├── anti/                   # Anti-patterns (AP_* morphisms into Witness)
│   ├── autop/              # OEAUTOP slot (CATALOG_EMPTY.txt)
│   ├── html/               # HTML slot (CATALOG_EMPTY.txt)
│   ├── javascript/         # JavaScript slot (CATALOG_EMPTY.txt)
│   ├── json/               # JSON slot (CATALOG_EMPTY.txt)
│   ├── lean4/              # Lean 4 anti-patterns (AP_LN_*.md)
│   ├── manim/              # Manim slot (CATALOG_EMPTY.txt)
│   ├── markdown/           # Markdown anti-patterns (AP_MD_*.md)
│   ├── python/             # Python anti-patterns (AP_PY_*.md)
│   ├── rust/               # Rust anti-patterns (AP_RS_*.md)
│   ├── sql/                # SQL anti-patterns (AP_SQL_*.md)
│   └── svg/                # SVG slot (CATALOG_EMPTY.txt)
└── helpful/                # Paired helpful / healthy patterns (HP_* contractive endomorphisms)
    ├── autop/              # OEAUTOP slot (CATALOG_EMPTY.txt)
    ├── html/               # HTML slot (CATALOG_EMPTY.txt)
    ├── javascript/         # JavaScript slot (CATALOG_EMPTY.txt)
    ├── json/               # JSON slot (CATALOG_EMPTY.txt)
    ├── lean4/              # Lean 4 healthy patterns (HP_LN_*.md)
    ├── manim/              # Manim slot (CATALOG_EMPTY.txt)
    ├── markdown/           # Markdown healthy patterns (HP_MD_*.md)
    ├── python/             # Python healthy patterns (HP_PY_*.md)
    ├── rust/               # Rust healthy patterns (HP_RS_*.md)
    ├── sql/                # SQL healthy patterns (HP_SQL_*.md)
    └── svg/                # SVG slot (CATALOG_EMPTY.txt)
```

`json`, `html`, `javascript`, `manim`, `svg`, and `autop` are tracked catalog homes. Each holds `CATALOG_EMPTY.txt` until a pattern is admitted. An empty slot is not a discovered anti-pattern. `markdown` holds admitted prose-contract patterns.

## 3. Pattern Header Specification

Every pattern manifest declares sovereign operad frontmatter:

```yaml
---
pattern_id: AP_PY_001
name: blanket_mypy_ignore
category: anti_pattern # or healthy_pattern
operad_type: AntiMorphism # or ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Witness" # "Code" for healthy patterns
operad_arity: 1
operad_residual: "contractive" # "zero" for healthy patterns
dual_pattern: HP_PY_001_scoped_mypy_overrides
language: python
authority_effect: None
---
```

## 4. Multi-Host Parity Discipline

The `patterns/` tree is a shared governance and verification surface. In accordance with multi-host synchronization invariants, identical contents must be mirrored across `.agents/`, `.claude/`, `.codex/`, and `.grok/`.

## 5. Filename & ID Allocation Discipline

1. **Canonical Filename Syntax**:
   Every pattern file name must strictly match the regex:
   - Anti-patterns: `^AP_[A-Z0-9]+_\d{3}_[a-z0-9_]+\.md$` (e.g. `AP_MD_058_markdown_asterisk_list_syntax.md`)
   - Healthy patterns: `^HP_[A-Z0-9]+_\d{3}_[a-z0-9_]+\.md$` (e.g. `HP_MD_057_claim_ledger_pytest_addressing.md`)
   - Lowercase prefixes (`ap_...`, `hp_...`) and filenames omitting the 3-digit ID are strictly forbidden.

2. **Sequential Non-Colliding ID Allocation**:
   - Pattern IDs must be strictly monotonic sequential numbers per language family (`001`, `002`, ...).
   - Review finding codes (e.g., finding `F7`) must NEVER be transposed directly into `pattern_id` without querying the catalog for the next available unallocated sequential integer.
   - Every `pattern_id` in the frontmatter must be unique across the repository.

3. **Four-Host Parity Execution**:
   - In accordance with repository multi-host mirroring laws, all pattern additions, modifications, or renames must be applied synchronously across `.agents/`, `.claude/`, `.codex/`, and `.grok/`.

