# Mode 13: Relational Normal Form Chase & Equality Saturation

**Mode ID:** 13  
**Cluster:** Cluster III: Group & Cochain Structure  
**AuthorityEffect:** None  

## Overview

Mode 13 governs the confluent rewriting of prompt representations and structural schemas from raw un-normalized states (0NF) into canonical, irreducible normal forms (up to 6NF).

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_06_relational.sql` and `prompt_rewriting/adr_reuse_decision.md`:

### 1. Relational Normal Form (RNF) Profile

Prompt requests are normalized into explicit relational spans under `sqlite_strict_text_set_v1`:

```sql
CREATE TABLE IF NOT EXISTS prompt_spans (
    slot TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('task', 'constraint', 'context', 'unresolved')),
    text TEXT NOT NULL
);
```

- Each span carries an explicit, single functional role.
- Undeclared requirements or domain ambiguities are explicitly marked as `unresolved`.
- Natural join over ordered slots losslessly reconstructs the exact original text.

### 2. Bounded Native Equality Saturation (`egglog` Engine)

Mode 13 incorporates bounded relational equality saturation to discover optimal equivalent prompt expressions without semantic drift:

- **Rule 1 (`share-payload`):** Identical text spans $T_1 = T_2$ are unified into a single payload entity in `prompts_payloads`, while their occurrences in `prompts_occurrences` remain distinct.
- **Rule 2 (`role-canonical`):** Normalizes equivalent semantic labels into a closed finite vocabulary (`task`, `constraint`, `context`, `output`, `unresolved`).
- **Rule 3 (`identity-compact`):** Re-indexes slot references (`s0, s1, ...`) without altering persistent genome identifiers.

### 3. Confluence & Resource Budgets

- **Execution Bounds:** Strictly limited to `max_iterations = 10` and `max_nodes = 1024`.
- **Deterministic Extraction:** Cost function minimizes AST size and wire byte-length; ties are broken deterministically by lexicographical SHA-256 digest.
- **Verification:** Emits an `EgglogRewriteReceipt` asserting zero loss of source bytes or occurrence multiplicity.
