"""conform_legacy_entries.py — durable fix for the recurring non-conforming
encyclopedia entries (e.g. the Kaggle product workstream's domain facts).

PROBLEM. Some workstreams author ENC entries with a non-standard frontmatter
vocabulary that `regen_encyclopedia.py` rejects, hard-failing the global regen so
no other entry's status can update. Two recurring dialects:
  * Kaggle domain — `kind: doctrine`, `status: IMPLEMENTATION-CHECKED`,
    `lean_status: NOT-NEEDED`, `migration: MANUAL`.
  * Codex GOMC / PrimitiveDifference / RDB workstream — `kind: theorem-package`
    or `kind: concept`, `migration: NEW`, `primitive: PrimitiveDifference`.
Both also tend to carry bare non-namespaced aliases and miss `## Provenance`.

FIX (governance-safe). This tool maps that legacy vocabulary to the nearest
HONEST *canonical* schema value — it adds NO new enum values, so the governed
status/kind/primitive/migration vocabulary is unchanged (canonical enums:
omega_engine/research/encyclopedia/readme.md). The blanket maps preserve intent:
  kind:        doctrine             -> proposition   (a checkable claim/requirement)
  kind:        theorem-package      -> theorem       (a bundled theorem)
  kind:        concept              -> definition    (a named construct)
  status:      IMPLEMENTATION-CHECKED -> INTERPRETIVE  (domain/impl-checked, NOT a tower proof)
  lean_status: NOT-NEEDED           -> NOT-PLANNED
  migration:   MANUAL               -> VERIFIED       (entry is test/source-verified)
  migration:   NEW                  -> EXTRACTED      (just-authored, pre-verification)
  primitive:   PrimitiveDifference  -> difference     (canonical primitive)
It also drops aliases lacking a known namespace (gt:/paper:/pl:/po:/spine:) and
adds a `## Provenance` section if missing.

NOT REMAPPED ON PURPOSE — status. There is deliberately no blanket `status:`
map for the GOMC dialect's `MECHANIZED-PARTIAL` / bare `MECHANIZED`: these are
per-entry judgments, not mechanical renames. `MECHANIZED-PARTIAL` is a
`lean_status`, never a prose `status`; demoting it correctly is usually
`-> CONDITIONAL`, but V6 then requires a nonempty `conditional_on`, and a bare
`MECHANIZED` status with no `## Proof` is either a missing proof or a `-> DEFINED`
demotion. Picking the right one needs a human / `/math-prover` pass, so status
conformance is left out of this tool.

RESIDUAL MANUAL STEPS — this tool cannot fix these; `--fix` may still leave
`regen_encyclopedia.py` red until a human resolves them:
  * Duplicate `id:` (V1) — two entries colliding on one ENC-NNNN must be
    renumbered to the next free id; the conformer never touches ids.
  * `uses:` pointing at Lean module names (e.g. `OmegaCore.PrimitiveDifference`,
    `QM.GOMC_01_Architecture`) — these are not ENC ids (V4 fails). Deciding
    whether to drop them (record the dep under `sources:`/`lean_refs:`) or map
    them to a real ENC id is a per-entry call.
  * Missing `## Proof` for a PROVED/PROVED-PROSE/MECHANIZED status (V6) — write
    the proof or demote the status; both are judgments, not remaps.
  * `status:` conformance generally (see NOT REMAPPED above).

USAGE.
  python conform_legacy_entries.py --check   # report; exit 1 if any non-conforming (CI / pre-commit)
  python conform_legacy_entries.py --fix     # rewrite in place (idempotent)
  python conform_legacy_entries.py           # same as --check

Idempotent: already-canonical entries are skipped, and re-running --fix over a
conformed entry is a no-op (no target value is a key in its own field-map).
Intended as a pre-commit hook or a one-command fix instead of per-entry hand-editing.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

# legacy value -> canonical value. Every target on the RHS is already a canonical
# enum value (see the enum sets in regen_encyclopedia.py and the schema table in
# omega_engine/research/encyclopedia/readme.md) — this map adds NO new vocabulary,
# so the governed status/kind/primitive/migration enums are unchanged.
# Idempotent by construction: no target value is ever a key in its own field-map,
# so a second pass over an already-conformed entry is a no-op.
FIELD_MAP = {
    # Kaggle-domain legacy vocabulary + Codex GOMC/PrimitiveDifference dialect.
    "kind": {
        "doctrine": "proposition",  # Kaggle domain: a checkable claim/requirement
        "theorem-package": "theorem",  # GOMC: a bundled theorem -> theorem
        "concept": "definition",  # GOMC: a named construct -> definition
    },
    "status": {"IMPLEMENTATION-CHECKED": "INTERPRETIVE"},
    "lean_status": {"NOT-NEEDED": "NOT-PLANNED"},
    "migration": {
        "MANUAL": "VERIFIED",  # Kaggle domain: entry is test/source-verified
        "NEW": "EXTRACTED",  # GOMC: just-authored entry -> EXTRACTED (pre-verify)
    },
    "primitive": {"PrimitiveDifference": "difference"},  # GOMC -> canonical primitive
}
KNOWN_NAMESPACES = ("gt:", "paper:", "pl:", "po:", "spine:")
PROV_TEMPLATE = (
    "## Provenance\n\n"
    "- Schema conformed by 'conform_legacy_entries.py' (legacy vocabulary mapped\n"
    "  to canonical: see the tool's FIELD_MAP). Original authoring sources are\n"
    "  listed in the 'sources:' frontmatter.\n"
)

# default scope: encyclopedia entries tree, relative to repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ENTRIES_GLOB = os.path.join(
    REPO_ROOT, "omega_engine", "research", "encyclopedia", "entries", "**", "*.md"
)


def _conform_text(text: str) -> tuple[str, list[str]]:
    """Return (new_text, changes). changes empty => already conforming."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    changes: list[str] = []
    in_fm = False
    fm_seen = 0
    in_aliases = False
    for line in lines:
        raw = line.rstrip("\n")
        if raw.strip() == "---":
            fm_seen += 1
            in_fm = fm_seen == 1
            in_aliases = False
            out.append(line)
            continue
        if in_fm:
            m = re.match(r"^([a-z_]+):\s*(.*?)\s*$", raw)
            if m and m.group(1) in FIELD_MAP:
                field, val = m.group(1), m.group(2)
                # Mirror regen_encyclopedia.py's _unquote: strip a matched
                # surrounding quote pair so a quoted scalar (e.g. kind: "concept")
                # conforms exactly as the unquoted form does. The canonical value
                # is re-emitted unquoted, which is the schema form for these enums.
                if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                    val = val[1:-1]
                if val in FIELD_MAP[field]:
                    new = FIELD_MAP[field][val]
                    out.append(f"{field}: {new}\n")
                    changes.append(f"{field}: {val}->{new}")
                    in_aliases = False
                    continue
            if re.match(r"^aliases:\s*$", raw):
                in_aliases = True
                out.append(line)
                continue
            if in_aliases:
                am = re.match(r'^\s*-\s*"?([^"]+)"?\s*$', raw)
                if am:
                    if not am.group(1).startswith(KNOWN_NAMESPACES):
                        changes.append(f"drop alias {am.group(1)}")
                        continue
                    out.append(line)
                    continue
                in_aliases = False
        out.append(line)
    new_text = "".join(out)
    if "## Provenance" not in new_text:
        if "## Changelog" in new_text:
            new_text = new_text.replace("## Changelog", PROV_TEMPLATE + "\n## Changelog", 1)
        else:
            new_text = new_text.rstrip() + "\n\n" + PROV_TEMPLATE
        changes.append("add ## Provenance")
    return new_text, changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix", action="store_true", help="rewrite in place")
    ap.add_argument("--check", action="store_true", help="report only (default)")
    args = ap.parse_args()
    do_fix = args.fix and not args.check

    paths = sorted(glob.glob(ENTRIES_GLOB, recursive=True))
    if not paths:
        print(f"ERROR: No entry files found matching {ENTRIES_GLOB}", file=sys.stderr)
        return 1

    nonconforming = 0
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new_text, changes = _conform_text(text)
        if not changes:
            continue
        nonconforming += 1
        rel = os.path.relpath(path, REPO_ROOT)
        print(f"{'FIXED' if do_fix else 'NEEDS-FIX'} {rel}: {'; '.join(changes)}")
        if do_fix:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new_text)

    if do_fix:
        print(f"\nconformed {nonconforming} entr{'y' if nonconforming == 1 else 'ies'}")
        return 0
    if nonconforming:
        print(
            f"\n{nonconforming} non-conforming entr{'y' if nonconforming == 1 else 'ies'}; run with --fix"
        )
        return 1
    print("all entries conform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
