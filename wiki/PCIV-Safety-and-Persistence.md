# Safety and persistence

Part of [Prompt Civilization](PCIV.md). Previous: [Selection and retrieval](PCIV-Selection-and-Retrieval.md)

This page covers Levels 08 to 10 and the experimental selection code: what
happens when something in the population turns out to be bad, how events are
recorded so they survive a crash, and how an experimental improvement is
accepted without becoming a deployment.

## Two negative operations

When a defective rule or a compromised artifact is found, PCIV keeps two
operations apart (Level 08):

| | Global invalidation | Forward causal taint |
| --- | --- | --- |
| Acts on | An antibody rule, by exact version and scope | An artifact and everything built from it |
| Triggered by | The antibody being suspended or revoked | An authenticated taint decision |
| How it spreads | Not at all: the rule is disarmed everywhere at once, no graph walk | Forward along inheritance and realisation edges, to a fixpoint |
| Reaches | Ancestors, descendants and unrelated prompts alike | Children, grandchildren and occurrences that consumed the artifact |

Mixing them up is a real failure: walking the graph to disarm a bad rule misses
unrelated prompts that also use it, while disarming globally to contain a
compromised artifact over-reaches.

**A clean parent does not cleanse a child (`F-RES-11`).** The default taint
policy is OR: a child with one tainted parent and one clean parent is tainted.

## Durable events

`infrastructure/event_log.py` and `cas.py` implement Level 09.

**The producer mints the id (`F-EVT-01`).** An event id is derived
deterministically from the producer, event kind, run, occurrence, subject and an
ordinal, so two genuinely distinct acquisitions both survive, and a resend of
the same event does not duplicate it.

**Same id, different payload is a conflict (`F-EVT-02`).**

| Request | Result |
| --- | --- |
| New id | Appended |
| Known id, same payload hash | Success, no-op (idempotent resend) |
| Known id, different payload hash | Refused with `EVENT_IDENTITY_CONFLICT`, and an audit record is written |

**Bytes are content-addressed (`F-EVT-03`).** Raw prompt and response packets
are stored by SHA-256, and the log refers to them by id and hash. A missing or
corrupted object raises `CAS_OBJECT_MISSING` or `CAS_DIGEST_MISMATCH`. Missing
bytes are never regenerated.

**Provider calls have explicit states (`F-EVT-04`, `F-EVT-05`).**

```text
INTENT_RECORDED ──▶ SENT ──▶ RESPONSE_CAPTURED
                       └───▶ OUTCOME_UNKNOWN     (crash after sending)
```

Retrying an `OUTCOME_UNKNOWN` call needs an explicit retry authorisation or a
provider idempotency key. Once a response is captured, rebuilding projections
makes **zero** provider calls.

## Custody

`use_cases/custody.py` keeps append-only prompt custody. A change of custody
needs an authenticating verifier injected by the host; a generated status, a
rank, a fitness score or a string shaped like a receipt cannot change it.
`operator_custody.py` adds independent operator admission and witnessed
offspring.

## The elenchus

`domain/elenchus.py` interrogates candidate text for attempts to talk a check
away. It refuses, with fitness 0:

- **flattery used to waive a check**, such as praise combined with "skip the
  tests" (`REFUSED_FLATTERY_CONTEXT_SMUGGLE`);
- **urgency used to waive a check**, such as "urgent" combined with "bypass
  review", or any "emergency release" (`REFUSED_URGENCY_PANIC`).

Praise or urgency alone does not trigger a refusal; the combination with a
waiver does. It is a lexical screen, not a model of intent.

## Choosing an experimental incumbent

`use_cases/research_selection.py` decides whether a candidate harness replaces
the current experimental incumbent. It is strict about what may be compared:

- every evaluation row must share the experiment's source, checker, split,
  configuration and budget (`FOREIGN_EVALUATION_BINDING`);
- each row must belong to the candidate or the incumbent, with the right parent
  and model (`FOREIGN_CANDIDATE`, `STALE_PARENT_OR_MODEL`);
- the candidate's parent must be the current incumbent (`STALE_CANDIDATE_PARENT`);
- confirmation rows must be fresh occurrences (`CONFIRMATION_NOT_FRESH`);
- candidate and incumbent must be evaluated on the same tasks, families and
  repetitions (`UNPAIRED_EVALUATIONS`).

The candidate wins only if controls pass and it improves on **both** the
selection set and a separate confirmation set: on the Pareto front over
correctness and cost, ahead of the incumbent, and no worse on any task family.
An incomplete or infrastructure-error row means no improvement. Winning makes
it the experimental incumbent, with no deployment authority.
`use_cases/ablation.py` complements this with report-only ablations that remove
one or two barriers at a time to see what each contributes.

This is the selection step of [Paper 029](Paper-029.md)'s harness-evolution
loop. That campaign was deferred, so no improvement is claimed.

## Open horizons

Level 10 records planned work, with no operational authority yet:

- **Crossover** limited to homologous blocks, with a conflict check when the
  parents carry conflicting immunities.
- **Islands**: separate populations with different priors or objectives, and
  bounded migration that records projection loss.
- **A frozen state** for lineages that stay dominant and pass held-out checks
  for a set number of epochs, as fixed reference anchors.
- **Metabolic bounds**: refusing closed loops where agents cite their own
  unverified output as evidence, and allocating resources only against verified
  progress.

The intelligence metabolism in `pciv/use_cases/intelligence_metabolism/` is
already partly built: it segments obstruction episodes, mines recurring motifs
read-only, and writes a claim-disciplined daily digest.
