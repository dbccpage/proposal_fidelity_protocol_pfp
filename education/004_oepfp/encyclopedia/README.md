# PFP Encyclopedia (`encyclopedia`)

**AuthorityEffect:** `None`

## 1. Role

A single subfolder, `entries/`, holding 95 markdown entries named `enc-NNNN-<slug>.md` (first `enc-0080`, last `enc-1209`; the numbering has gaps). Each entry has YAML frontmatter, a `# ENC-NNNN` heading, and a `## Statement` section.

## 2. Directory Inventory

| Item | Type | Purpose |
|---|---|---|
| [`entries/`](entries/) | Directory, 95 `.md` files | One entry per definition, lemma, theorem, proposition, or corollary of the Symbol Game layer |

## 3. Entry Frontmatter (as observed)

`id`, `kind`, `name`, `status`, `conditional_on`, `layer`, `tower_level`, `primitive`, `aliases`, `sources`, `uses`, `lean_status`, `lean_refs`, `extracted`, `migration`.

Counts across the 95 entries:

| Field | Values |
|---|---|
| `layer` | `symbol-game` (95) |
| `kind` | theorem 74, lemma 7, corollary 7, definition 6, proposition 1 |
| `status` | MECHANIZED 45, PROVED-PROSE 34, CONDITIONAL 7, DEFINED 7, SKETCH 2 |

## 4. Scope

- `status` and `lean_status` are values written in each entry. They were not re-checked against Lean or code here.
- The sample entry read (`ENC-0080`) cites `canonical_omega_math_spine.md` as its source; whether that file is present was not checked.
- Entries are extracted statements, not new claims.
