# OEOP capability sources and host discovery

AuthorityEffect: None.

Editable Markdown skills and workflow specifications live in
`operads/skills/` and `operads/workflows/`.
The `.agents`, `.claude`, `.codex`, and `.grok` copies are generated discovery
views, not alternative instruction authorities. Edit the OEOP source and use
the existing packaging tools to update selected host packages. Host-specific
configuration and unrelated assets are preserved.

The common editable instruction guide is `documentation/host_instructions.md`.
Its generated views are `GEMINI.md` and each host's `AGENTS.md`.
`manifests/host_discovery_version.txt` supplies the unchanged `0.0.0-a00`
compatibility marker in each host's `VERSION`; no release or admission is implied.

Typed declarations and composition live under `operads/contracts/`
and `operads/skill_operad/`. Existing serialized identifiers and
historical receipts keep their original identities. Source ownership does not
admit every discovered skill for runtime execution or issue any capability.

OEOP supplies capability definitions and composition. OEEIS owns immune
evaluation and antibody data, Prompt Civilization owns evolution and lineage,
and Adversary owns execution, scheduling, budgets, and run evidence. These remain
separate subsystems with injected interfaces.

The source cutover covers skills, workflows, rules, registries, hook templates,
and anti/helpful pattern descriptions in OEOP. Antibody definitions, pharmacy
data and anti-skill data live in `eis/antibodies/`
and `eis/antiskills/`. Runtime candidate stores
and the existing activation rules stay with their runtime owners. Quarantine
history, host settings and the existing content-lock address are preserved.
Existing Grok-only Rhai entrypoints remain host-specific configuration; they
are not silently added to the portable workflow catalog.
Old claims that host discovery roots are empty or that OEOP is wholly
shadow-only do not describe this source layout.

Use the existing mirror CLI for a selected Markdown skill package:

```text
python -m operations.controllers.skill_mirror_cli --skills <name>
```

Selected shared configuration trees use the existing packaging `mirror_skill`
function with their OEOP source and existing host destination; it refuses
destination-only files rather than deleting them. Typed packages use the
existing typed-contract projector. Its conflict checks
still refuse manual edits to generated files; source relocation does not weaken
that protection. The mirror receipt compares authored source bytes as well as
all host destinations. Recovery restores destinations, never the authored source.

Do not store secrets, live costs, transcripts, leases, runtime journals,
worktrees or scheduler state in host discovery roots. Runtime evidence belongs
to its existing runtime owner. Local checks, general mathematical proof,
publication and authority remain distinct.
