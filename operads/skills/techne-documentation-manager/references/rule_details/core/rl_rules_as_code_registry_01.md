# Detailed definition: Rules-as-Code Registry & Rule Gate (1)

**AuthorityEffect:** None.

Parent: [Rules-as-Code Registry & Rule Gate](../../../../../rules/core/rl_rules_as_code_registry.md). Load for the matching predicate, not every task.

# Rule: Rules-as-Code Registry & Rule Gate (`RULE_RULES_AS_CODE_REGISTRY_001`)

**AuthorityEffect:** None.

Rule files are specifications. The machine-readable rule register is
`operads/skill_operad/yaml/rules_registry.yaml`, and the
executable gate is `operads/skill_operad/skill_compiler/rule_gate.py`.
A rule takes effect as a gate only where a named check enforces it.

---

## 1. Closed Folder Taxonomy

Every rule lives in exactly one folder under `rules/`. The folder set is closed and declared in
the registry: `core`, `authority`, `claims`, `git`, `paths`, `architecture`, `governance`,
`engineering`, `math`, `coda`, `genesis`, `papers`, `docs`, `education`, `swarms`. Adding a folder
means editing the registry taxonomy in the same change.

## 2. Registration and Ownership

1. Every `rules/**/*.md` file has exactly one registry entry, and every entry names an existing file.
2. Every invariant ID that appears anywhere in the rules (`RULE_..._NNN`, `AGT-...-NNNN`) is owned by
   exactly one registry entry, and the owning file contains that ID.
3. Each owned invariant carries a status:
   - `ENFORCED`: a named executable check fails when the invariant is violated.
   - `PARTIAL`: a named check covers a declared subset; `scope` states which part.
   - `CANDIDATE`: no executable check exists yet. This is the default.
4. `ENFORCED` and `PARTIAL` entries name `enforced_by` as `path` or `path::symbol`. The symbol must
   exist in that file.

## 3. File Hygiene

1. Each rule file is at most 12,000 bytes.
2. Filenames are lowercase snake case with the `rl_` prefix; content is UTF-8 without BOM.
3. Each file carries the header line `**AuthorityEffect:** None.`
4. Markdown links resolve relative to the file. Host-absolute `file:///` link targets are forbidden.
5. The rule tree is byte-identical across `.agents/`, `.claude/`, `.codex/` and `.grok/`; edits must sync across all four roots in the same commit to prevent `R7_HOST_DRIFT`.
6. The register table in `GEMINI.md` and the four host `AGENTS.md` files lists registered paths; these five files are byte-identical.



## 4. Growth Law

A new rule ships with its check, or it is registered as `CANDIDATE`. Promoting an invariant from
`CANDIDATE` to `ENFORCED` requires the named check to fail on a real violation first (a mutation
or fixture that turns it red), not only to pass on the current tree.

## 5. Operation

```
py -3.12 -m operads.skill_operad.skill_compiler.rule_gate --repo-root .
```

Exit status 0 means every check in sections 1–3 passed. The gate prints the per-status invariant
counts, so the share of rules that are still `CANDIDATE` stays visible.

## 6. Rule Splitting & Factorization Protocol

When a rule approaches 12,000 bytes (`size_ceiling_bytes: 12000`), agents must factor it:
1. **Domain Separation:** Split distinct conceptual domains into separate files in the taxonomy folder.
2. **1-to-1 Migration:** Move invariant IDs (`RULE_..._NNN`) to the new file without duplication.
3. **Cross-References:** Repoint relative markdown links to the new canonical rule path.
4. **Registry:** Update `rules_registry.yaml` with the new rule entry, invariant ownership, and summary.
5. **Four-Host Parity:** Sync all modified/new rule files across `.agents/`, `.claude/`, `.codex/`, and `.grok/`.
6. **Register Sync:** Run `py -3.12 -m operads.skill_operad.skill_compiler.rule_gate --write-register --write-scope` and confirm 0 findings.
7. **Invariant Ownership:** Declare new invariant IDs in `rules_registry.yaml` simultaneously to prevent `R6_UNOWNED`.
