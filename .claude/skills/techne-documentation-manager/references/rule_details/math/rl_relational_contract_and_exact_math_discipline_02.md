# Detailed definition: Relational Contracts & Exact Math (2)

**AuthorityEffect:** None.

Parent: [Relational Contracts & Exact Math](../../../../../rules/math/rl_relational_contract_and_exact_math_discipline.md). Load for the matching predicate, not every task.

## 7. Filesystem Re-indexing, Prefix Shifts & Path Hygiene

- **Descending Order Renaming**: When re-indexing prefixed documentation or curriculum directory shelves (e.g. shifting directories by $+k$), renames must be executed strictly in descending numerical order (from highest prefix down to lowest) to prevent collisions with unshifted target paths.
- **Git Empty Directory Safety**: Because `git mv` fails on empty directories with `fatal: source directory is empty`, empty shelf directories must be moved/renamed using host filesystem tools (e.g. PowerShell `Rename-Item`), and immediate follow-up cross-reference verification tests must be executed locally.
- **Documentation Link Portability**: Markdown documents and SVGs must strictly use repository-relative links (e.g., `../_images/diagram.svg`), never host-local machine paths (`file:///c:/...`).
