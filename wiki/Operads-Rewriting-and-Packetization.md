# Rewriting and packetization

Part of [Operads](Operads.md). Previous: [Prompts as operad trees](Operads-Prompt-Trees.md) · Next: [Typed workflows](Operads-Typed-Workflows.md)

Operads, rewriting and packetization are the core of PFP. This page shows how
they hand off to one another. The rules of rewriting itself, layer by layer,
are in the [Rewriting](Rewriting.md) section; this page focuses on where the
operad meets it.

## The three stages

```text
Raw packet P
   │  1. Prompts: build an operad tree
   ▼
P* = template(P)  ──▶  { P*_sub }        tree with typed slots, URIs, bound guards
   │  2. Rewriting: apply declared rules, check every step
   ▼
candidate move ──▶ two-signal gate ──▶ PASS or REFUSED (typed)
   │  3. Packetization: seal what happened
   ▼
PacketEnvelope (payload hash, envelope hash, AuthorityEffect: None)
```

| Stage | Question it answers | Main code |
| --- | --- | --- |
| Prompts | What exactly is being asked, from which source bytes? | `pfp/domain/operad/prompt.py`, `operads/domain/prompt_hierarchy/` |
| Rewriting | Which declared rule changed the term, and is the result still the same problem? | `pfp/domain/rewriting/`, see [Rewriting](Rewriting.md) |
| Packetization | Can someone else replay and check exactly what was proposed and decided? | `pfp/domain/packet_codec.py`, `pfp/domain/bridge/symbol_game_packets.py` |

## Stage 1: prompts with addresses and guards

Every prompt node has a canonical address:

```text
prompt://<domain>/<subdomain>/<task>/<stage>/<prompt_id>[/<subprompt_id>]
```

`PromptUri` parses it and lists its ancestors from root to leaf, so a guard
bound high in the hierarchy can be found from any sub-prompt. A
`PromptTreeNode` (in `operads/domain/prompt_hierarchy/models.py`) carries:

- `anti_ops`: procedural checks, each inspecting one named slot and owning a
  refusal code;
- `antibodies`: empirical failure detectors from the [EIS](EIS.md), each with a
  minimum status (default `admitted`; candidates stay inert);
- an optional `immune_fence` limiting how many antibodies and bytes a template
  may pull in (defaults 3 and 2,048);
- an optional `operad_binding` tying the prompt to one coloured operad
  operation.

### Degree-of-freedom locks

An `OperadPromptBinding` names the operation's source and target colours, maps
each named slot to a colour, and can require independent pins for sub-channels,
cross-slot equality groups and boundary witness slots. Each requirement is one
**lock**. When a payload arrives, `evaluate_prompt_gates` checks the locks one
by one and subtracts each satisfied lock from the count:

```text
residual degrees of freedom = locks declared − locks satisfied
```

A fully constrained prompt reaches 0. A missing slot refuses with
`OPERAD_MISSING_SOURCE_SLOT`; a slot map whose colours disagree with the
signature refuses with `OPERAD_ARITY_OR_COLOUR_MISMATCH`; missing sub-channel
pins refuse with `DOF_UNPINNED_SUBCHANNEL_COMPENSATION`. The last one blocks a
specific trick: fitting a target by moving a constant from one sub-channel to
another so that the total still looks right.

A whole derivation map can be collected into one coloured operad. The
`DerivationMapOperadReport` records the composite signature, the total locks,
the residual freedom and every antibody and anti-op collected along the way.

## Stage 2: rewriting under declared rules

A rewrite replaces one term with another under a rule that was declared and
admitted beforehand. In the operad picture:

- **Grafting** (`∘_i`) builds terms. It is checked by colour and slot, and a
  defective subterm absorbs to `NullTree`.
- **Rewrite rules** transform terms. Each step must name its kind
  (representation change, witness replacement, cochain repair, problem change
  or prompt heuristic), because each kind carries a different obligation. The
  [Rewriting](Rewriting.md) page has the table.
- **Retractions** move back down the tower. `r_k(u_k(P*))` returns `P*`; a term
  off the image is refused as `NON_DESCENT`.
- **The gate** sees every candidate move. A move is refused when a guard fires
  on both signals, or when the host measures a nonzero defect.

Rewriting is also how the operad catalogue is simplified.
`skill_operad/symmetric_quotient.py` and `execute_operadic_compression.py`
propose declared normalisations and quotient candidates: operations that might
be merged. They are read-only by default and never merge or delete anything,
because matching signatures and a few scalar observations do not prove two
operations behave the same. [Paper 026](Paper-026.md) shows the general danger:
two states with the same current output can still allow different future
operations or costs, so compressing them on output alone loses information.

The full rewriting story, from four glyphs with no rules up to PFP, is in
[Rewriting](Rewriting.md). The PFP layer is summarised on
[PFP rewriting](Rewriting-PFP.md), and a complete worked repair that keeps the
question fixed is on [Residual repair](Rewriting-PFP-Residual-Repair.md).

## Stage 3: packetization

A **packet** is the unit that crosses a boundary: from host to model, from model
back to host, from one stage to the next. Packetization turns a payload into a
sealed, content-addressed record.

`PacketCodec.seal(payload, packet_family, ...)` in
[`packet_codec.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/packet_codec.py)
produces:

| Field | Meaning |
| --- | --- |
| `schema_version` | Envelope schema, currently `2.0.0` |
| `packet_family`, `payload_schema` | What kind of packet this is |
| `payload` | A deep copy of the payload |
| `payload_sha256` | SHA-256 of the canonical bytes of the payload |
| `parent_id`, `carrier_id` | Optional link to the packet this one answers, and the carrier it uses |
| `authority_effect` | Always `"None"` |
| `envelope_sha256` | SHA-256 of the canonical bytes of everything above |

Before hashing, text is normalised to Unicode NFC, and two keys that collapse
to the same normalised form are refused rather than merged. `verify` recomputes
both hashes and refuses on any mismatch, and also refuses any authority effect
other than `"None"`. A packet cannot grant itself permission.

The packet compiler in `bridge/symbol_game_packets.py` builds the envelopes a
session uses:

- a **problem packet** carries the task id, the payload, an initial state hash,
  the constraints (for example "finite exact carrier", "strict verified
  descent", `d1*d0=0`), the protected boundaries and a step budget;
- a **step packet** carries the step index, the candidate, the host's score
  (`phi_1`, `gamma_2`, whether the step is exact) and the prior score, linked to
  its parent event.

Because a returned packet keeps the original problem beside the answer, anyone
can replay the check. [Prompt Civilization](PCIV.md) uses the same idea to tell
a prompt genome apart from its many execution occurrences.

## Why the channel does not matter

Theorem 1 of [Paper 027](Paper-027.md) is the reason the three stages can vary
freely while the guarantee holds. Fix a task, a decoder that binds every
admitted reply to that task, and a sound host checker. Then **no** proposal
channel, whether a natural-language prompt, a glyph game, an operad
decomposition or a logit mask, can get an invalid candidate accepted. The
channel changes what is proposed and how often it succeeds; it cannot change
what the host accepts. Soundness says nothing about how often a channel finds a
valid answer: that is a separate, empirical question.

## Summary

| Stage | Carries | Refuses with |
| --- | --- | --- |
| Prompt tree | Exact spans, typed slots, URIs, bound guards, locks | `NullTree`, colour and slot errors, missing-slot and unpinned codes |
| Rewrite | A declared rule and its kind | `NON_DESCENT`, typed rewrite refusals, gate `REFUSED` |
| Packet | Payload hash, envelope hash, parent link, `AuthorityEffect: None` | Hash mismatch, prohibited authority effect, colliding keys |
