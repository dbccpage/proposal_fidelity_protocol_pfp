# Reference Operad, Residuals, Dispatch, and Skill Compiler

## Ownership boundary

`.agents/operad/OWNERSHIP.md` (a historical path: `.agents/operad/` does not exist at `201dc8d`;
the surviving ownership note is
`omega_engine_operads/skill_operad/_docs/OWNERSHIP.md`) describes the intended structure as a coloured
non-symmetric multicategory. The root `coloured_operad.py` is a historical JSON
compatibility API; `domain/` is the newer domain surface. Symmetric scaffolding is
experimental, and scalar quotient observations must not be promoted into
equivalence or contractivity.

The audit found 65 tracked files: six governance/data files, ten domain files,
eight application/infrastructure files, eighteen root runtimes/scripts, fifteen
skill-compiler files, and eight tests.

During this review, `SEMANTICS_MAP.md` was repaired to close its YAML fence and to
replace stale typing-coverage and equivariance statements with the live bounded
counts below. This documentation repair does not alter runtime semantics.

## Live signature

At the frozen base, `operad_signature.json` records ten colours, ten identities,
and 145 operations. That count is historical: at `201dc8d` (2026-10-15)
`.agents/skill_operads/operad_signature.json` records ten colours, ten identities
and 232 operations, one per skill, and `agent_capability_slices.json` is
`{"agents": {}}`, so the 13-agent slice figure below is historical too. The operational model is ordered and planar. Only 37 operations
carry invocation grading metadata: 34 discipline and three entry operations.
Capability slices cover 13 agents and pass narrow reference/colour checks, but no
gate checks unit inclusion, closure under composition, grading closure, workflow
typing, or runtime-carrier compatibility.

## Validator disagreement

The canonical root validator exits nonzero because the symmetric-closure operation
`techne-code-lossless-parser_p10` is introduced after unit compositions are built.
It lacks registered left/right unit laws. Some composition failures are printed but
not added to the error list, which is a fail-open path.

The application validator reports valid with 155 operations, ten units, three
admitted entry skills, and one unverified law. It reconstructs a weaker model and
does not treat the unverified law as failure. These validators prove different
predicates and must not share a single “valid” label.

## Residuals and quotients

Residual claims and obligations are separate; composition concatenates them and
takes maximum risk. Exact identity residuals may be meaningful, while ordinary
operation residuals default to unknown.

Confirmed drifts include:

- the registry preserves one custom residual and one equivariant operation that
  current skill frontmatter does not declare;
- the honesty gate rejects only the literal `contractive`, allowing arbitrary
  alternative vocabulary;
- `domain/quotient.py` can classify contractiveness from average scalar deltas,
  contrary to the safer diagnostic-only root quotient;
- planar execution adds the outer residual twice;
- an identity shortcut relies on name/shape conventions rather than verified body
  semantics.

No scalar observation in this tree establishes contractivity, quotient admissibility,
equivalence, or promotion.

## Repository and mutation safety

`JsonOperadRepository` is not roundtrip-safe: it ignores serialized identities,
changes identity casing, emits a different document shape, and drops registry
metadata. Several mutation scripts write canonical files directly without a lock,
atomic replacement, rollback, dry-run, or post-validation transaction. Signature
compilation defaults missing or unknown typing to `Code -> Code`, accepts arbitrary
residual strings, and preserves stale fields from prior state.

The strongest trace recorder is locked, content-addressed, and atomically replaced.
The application recorder can replace corrupt history with an empty list and lacks
hash/schema enforcement. These are separate custody ceilings.

## Dispatch

Root dispatch resolves registered operations and returns
`RESOLVED_NOT_EXECUTED`. Agent slices are permission sets. The agent-constrained
workflow path incorrectly requires the workflow identifier itself to be licensed
before checking its steps, which can deny an otherwise step-licensed workflow.

Resolution is not execution. Permission is not closure. A slice is not a proven
sub-operad.

## Skill Compiler pipeline

```text
inert episode
  -> representation resolution
  -> evaluation bank
  -> proposal/promotion receipt
  -> budget and parity gates
```

The intended preference is mechanized code gate, shared contract, references,
existing prose, then new skill as a last resort. `NEW_SKILL` writes only a pending
ooutwire proposal and never grants admission. Outputs remain
`AuthorityEffect: None`.

### Confirmed compiler defects

1. Budget exception maxima are applied before approval/expiry checks, so an
   unapproved exception can expand a budget; an approved maximum is not enforced as
   a ceiling.
2. Missing governed roots are skipped while the gate stays green.
3. Promotion targets an obsolete register syntax, computes stale entry numbers,
   injects candidate text into Markdown without structural escaping, and rewrites
   without locking or atomicity before receipt creation.
4. A generic `AuthorityEffect: None` route misclassifies unrelated findings into a
   math/physics contract.
5. Actual precedence puts `NEW_SKILL` ahead of existing operation/prose, contrary
   to the documented last-resort law.
6. Mixed relative and top-level imports create duplicate Python class identities.
7. Unknown confidence values can become `MEDIUM` in the episode while remaining
   arbitrary in the disposition.
8. Empty or malformed evaluation expectations can pass vacuously; receipts omit
   the bank digest and tested Git SHA.
9. Episode JSONL is useful memory but has no lock, hash chain, duplicate protection,
   or truncation detection.
10. Metrics query moving Git history without recording HEAD, so replay can change.

## HoTT and antibody vocabulary

The HoTT modules provide software metaphors for paths, transport, and 2-cells.
They are not formal homotopy type theory. Antibody modules provide finite AST and
pullback checks, not exhaustive adversarial survival. Success prose must name the
exact finite battery.

## Repair order

1. Restore unit closure after symmetric expansion and make every validator error
   fatal.
2. Remove scalar-to-contractive promotion and enforce one residual enum.
3. Select canonical operad, quotient, receipt, and persistence representations.
4. Repair budget authorization and promotion against the live register.
5. Make registry/profile/trace mutations locked, atomic, post-validated, and
   receipted.
