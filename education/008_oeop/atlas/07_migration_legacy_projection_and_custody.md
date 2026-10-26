# Migration, Legacy Projection, and Custody

## Three distinct claims

Migration evidence must keep these claims separate:

1. **Byte custody**: a manifest names the exact bytes currently present at a
   successor path.
2. **Structural translation**: a legacy declaration can be represented in the V3
   schema.
3. **Semantic preservation**: the successor behaves equivalently for an explicit
   set of observations.

The reviewed migration manifest supports the first claim for four hosts after
refresh. It offers partial structural translation. It does not establish the third
claim.

## Four-host successor manifest

The manifest covers 41 legacy entries and checks successor `SKILL.md` bytes across:

```text
.agents  .claude  .codex  .grok
```

Entries remain `DECLARED_UNADMITTED`. Multiple legacy operations can map to the
same successor skill, so exact successor-byte equality is not one-to-one behavioral
equivalence. The refresh script can faithfully bind whatever bytes are present; an
independent review is still needed before those bytes become an approved baseline.

## Repair made during this review

The frozen manifest referenced the retired `paper-package-techne` successor. The
working tree now uses `panepistimion-paper-package-techne` in all five affected
prefixes and refreshes the 41 exact four-host hash/size records with the repository’s
deterministic refresh script.

The Woland projection manifest also referenced retired or renamed skills. It now
uses:

| Retired reference | Current successor |
| --- | --- |
| `techne-code-python-principal-developer` | `techne-code-python-developer` |
| `adversarial-receipt-audit` | `thanatos-adversarial-receipt-audit` |
| `oeops-evidence-receipt-harness` | `techne-oeops-evidence-receipt-harness` |
| `omega-old-man-chatgpt-red-team` | `thanatos-old-man-chatgpt-red-team` |
| two retired architecture/scanner entries | one `techne-code-principal-architect` |

The repaired selection has 21 unique skills and no missing references. Its
projection expectation was updated to the corresponding exact digest. Focused
migration/projection regression tests pass; see
[Testing and falsification](09_testing_and_falsification.md).

## Legacy V1/V2 models

Legacy models retain useful discipline around immutable snapshots, strict source
spans, canonical JSON, declared substitutions, and lifecycle fields. They also
contain incomplete reference checks and statuses whose names can outpace their
evidence. V2 section extraction can omit the preamble, frontmatter, and first
heading once second-level sections exist.

The dual-read adapter synthesizes permissive placeholder operations and lifecycle
facets that do not arise from real schema/executor validation. It is a compatibility
reader, not admission evidence.

## Woland projection

The projection is explicitly shadow-only, `AuthorityEffect: None`, and cutover
false. It is a selected byte-bound view over current skills. It is not a scheduler,
execution plan, or proof that the selected skills compose.

## Custody procedure

For every manifest refresh:

1. freeze the Git base and enumerate exact manifest entries;
2. verify every successor path is contained in an allowed host root;
3. hash raw bytes with one declared algorithm;
4. compare all required hosts and report every missing/divergent path;
5. review semantic mappings independently of byte parity;
6. run mutation tests that prove a changed byte makes the gate fail;
7. record command, runtime, Git state, and result in a receipt;
8. leave lifecycle state unadmitted until the designated authority decides.

## Nonclaims

- Four-host equality is not evidence of correctness.
- A refreshed manifest is not independent review.
- A successor-byte digest is not a digest of legacy behavior.
- A capability slice is not useful if its operations are absent from the owning
  catalog.
