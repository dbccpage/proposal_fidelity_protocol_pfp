# Steering: prompt geometry

Before trying to improve a prompt, the source project measured it. Each run
observed the user's original seed, the final system and user prompts sent to the
model, and the model's replies, as small density matrices. It also organized the
seed once by appending the task's declared fields. The measurement was never
allowed to choose a rewrite.

## What the source did

**Observation.** The `ordered-sha256-density-v1` profile splits UTF-8 text into
tokens, builds features from token order, adjacent pairs, position and field
identity, and projects them with SHA-256 into a fixed dimension (28 to 1024,
default 128). At most 16 normalized component vectors form a density matrix. The
report keeps the von Neumann entropy in bits, the purity, the effective rank
(two to the entropy) and, for two compatible observations, the quantum
Jensen-Shannon divergence. Inputs are bounded at 1 MiB and 32,768 tokens; empty
input, invalid UTF-8 and resource limits get explicit statuses and null metrics.
Observations with different dimensions, roles, fields or trust origins are not
compared.

The limits were stated plainly: coordinates are hashed features, not concepts;
hash collisions can happen; word-order and negation controls show the profile is
sensitive, not that it understands.

**Organization.** A single preparation step kept the seed verbatim as an exact
prefix and appended only the task, constraints, acceptance and response-contract
fields that the caller had supplied. Missing requirements were not inferred.
Repeated preparation only validated the stored result; a changed seed refused
before dispatch. Organization ran before the PFP prompt was rendered and its
digest computed; observation ran after, so measuring could not change what was
sent.

**What the numbers showed.** On one captured first action the seed (871 bytes)
grew to 1,761 bytes after organization, and the user prompt from 11,733 to
12,745 bytes. Entropy went down slightly at dimensions 28 and 128 and up
slightly at 1024. Because the sign of the change depended on the dimension, the
source concluded that entropy is not an optimization target and not a measure
of prompt quality, and that byte counts say nothing about tokens saved or
accuracy.

## Replicate it here

Needs the native host. The measurement is implemented in Rust in
`code/rust/engines/src/quantum/prompt_density.rs` and served by
`code/rust/pfp/src/prompt_geometry_host.rs`; the Python side is
`observe_text(text, dimension=..., role_id=..., field=..., trust_level=...)` in
`ops/adversary/infrastructure/prompt_geometry.py`. Without a built host it
returns a report with `status: "UNAVAILABLE"` and null metrics rather than an
invented number. The multi-role run that calls it on every turn is not runnable
here yet.

What you can do without the host is the organization rule, which is plain
string discipline: keep the seed as an exact byte prefix, append only declared
fields, and refuse if the stored organized text no longer starts with the seed.
`organize_initial_seed(objective, brief)` in the same file implements it.

## How it relates to PFP, EIS and PCIV

- **PFP.** Organization happens before the prompt digest and observation after,
  so the PFP binding between the prompt sent and the reply received is unchanged.
- **EIS.** Admitted immune guidance is part of the rendered prompt and is
  measured like any other text; geometry never admits or removes guidance (see
  [Admitted guidance](Steering-Admitted-Guidance.md)).
- **PCIV.** A density profile is a candidate descriptor for comparing prompt
  variants in a [family](Steering-Prompt-Families.md). The source's own results
  argue against using it as a fitness score.

## Where the code lives

`ops/adversary/infrastructure/prompt_geometry.py`, the Rust files above, and
`pfp/domain/bridge/sbe.py` for the older character-projection control.
