# Steering: admitted guidance

Most prompt steering adds advice: "check the sign convention", "do not trust the
cached value". The source project treated every such line as something that had
to be admitted by the immune system before it could be rendered into a prompt,
and bound the admitted text into the prompt's digest.

## What the source did

A pilot task checked finite claims about all 225 cross-ratios of one explicit
6x6 complex Hadamard phase table. Before the model saw the task, the immune
system searched its store of reviewed guidance for entries that applied, and a
renderer placed only **reviewed** entries into a fenced block of the PFP prompt.

The binder enforced:

- only guidance whose review had completed could be projected into the prompt;
  a missing admission refused rather than rendering without it;
- an unbound older template never queried the guidance store at all;
- the guidance's scope had to agree with the prompt it was attached to;
- the rendered prompt was deterministic, and the PFP digest covered the rule
  revision, so a change of guidance changed the prompt's identity.

The model's reply then went through the ordinary host checks. The pilot allowed
one repair and kept the earlier candidate, its check and what was learned. The
source was careful about scope: the pilot checks finite claims about that one
table, not a theorem about all complex Hadamard matrices.

The source also recorded one honest limit of its runs: one model worker applied
many role perspectives in sequence, which is not the same as many independent
reviewers.

## Replicate it here

Needs the native host for rendering. `NativeImmuneFenceRenderer` in
`pfp/infrastructure/immune_fence.py` sends the payload to the Rust host's
`immune_fence_render` operation and refuses unless the host's reply carries the
SHA-256 of exactly the payload that was sent. The binder that decides which
guidance may be projected is `ops/adversary/infrastructure/prompt_family_binder.py`.
The multi-role pilot run is not runnable here yet.

The admission rule can be exercised without the host through the two-signal
gate in `eis/`; see [Self-certification screen](Steering-Self-Certification-Screen.md)
for a checked snippet, and [EIS: antibody lifecycle](EIS-Antibody-Lifecycle.md)
for how guidance becomes reviewed.

## How it relates to PFP, EIS and PCIV

- **EIS.** This is the immune system's output side: reviewed antibodies become
  prompt guidance. Unreviewed guidance is never rendered.
- **PFP.** The guidance is part of the prompt the digest binds, so a reply can
  be traced to exactly the guidance it was given.
- **PCIV.** The Lamarckian loop in `pciv/use_cases/lamarckian_loop.py` passes
  admitted guidance to later prompt generations; inheritance only carries
  admitted text ([PCIV: mutation and inheritance](PCIV-Mutation-and-Inheritance.md)).

## Where the code lives

`pfp/infrastructure/immune_fence.py`,
`ops/adversary/infrastructure/prompt_family_binder.py`,
`ops/adversary/infrastructure/pilot035_play.py` and
`operads/application/prompt_gates.py`.
