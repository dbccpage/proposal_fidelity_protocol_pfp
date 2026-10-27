# Regulation and custody

Part of [Epistemic Immune System](EIS.md). Previous: [Antibody lifecycle](EIS-Antibody-Lifecycle.md)

An immune system that only ever adds detectors eventually blocks everything. The
EIS has two counterweights: **regulation**, which downgrades detectors that
suppress valid answers, and **custody**, which makes every admission decision
traceable to a configured key under an explicit policy.

## False suppression

Blocking a valid answer is called **false suppression**. In two-signal terms, a
firing with Signal 1 alone (a match with no observed damage) is the warning
sign: the detector recognised something that turned out to be harmless.

## Regulatory supervision (Treg)

`domain/treg.py` computes an exact rational toxicity index for each detector:

```text
toxicity = firings with Signal 1 alone / total triggers
```

When toxicity **meets or exceeds** `tau = 1/5`, the supervisor writes an
immutable regulatory record and downgrades the detector from `BLOCKING_GATE` to
`DIAGNOSTIC_ONLY`. The threshold is inclusive: one Signal-1-alone firing in five
triggers is already intolerable. A downgrade keeps the detector reporting; it
does not delete it.

There are two evaluation modes:

| Mode | Input | Meaning of toxicity |
| --- | --- | --- |
| `triggers` | Explicit `(signal 1, signal 2)` pairs | A true rate between 0 and 1 |
| `prompt_corpus` | A pinned benign corpus | Benign by definition, so every firing is Signal 1 alone: toxicity is 0 if it never fires and 1 if it fires once. Any firing downgrades. |

All arithmetic uses exact fractions; floats are not allowed.

The operad package has its own supervisor for anti-skills used during
composition, with a different rule: downgrade at an independently checked
false-suppression rate of 2/5, and only after at least three suppressions have
been observed. See [Skills, op inventory and the resolver](Operads-Skills-and-Catalog.md).

## Anergy: proposing, not acting

`domain/anergy.py` counts benign hits per detector. When a detector reaches the
threshold (default 5), it emits a proposal to the supervisor's queue with
`is_suspended = False`. The monitor never suspends anything itself.

## Scoped suspension

`use_cases/regulate_guard.py` suspends a learned detector **for one stated
scope and session** when an independent benign check shows it fired on
something harmless. The underlying admission is unchanged; only the guard's
effective authority in that scope narrows.

## Authenticated custody

Admission decisions, host-health reports and observations can be signed and
verified. The design is in
[`authenticated_custody.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/eis/documentation/authenticated_custody.md);
the verifier is native code, and records go to an existing SQLite receipt
ledger.

**Trust is explicit.** An operator supplies a policy (`core.eis.trust-policy.v1`)
with a trust domain and a list of keys. Each key states its issuer, key id,
public key, permitted purposes (`admission`, `health` or `observation`), exact
scopes, validity window, maximum lifetime and revocation flag. There is no
built-in production key, no trust discovery and no automatic admission. The
fixed keys in the tests are public test data.

**Every binding field is checked**, not only the candidate's identity:

| Field | Binds |
| --- | --- |
| `spec_id`, `scope` | The exact guard and its operational scope |
| `rule_digest` | The actual rule bytes |
| `source_digest` | The operator-selected source manifest |
| `subject_digest` | The rule (for admission), the payload (for health) or the full admission request (for observations) |
| `context_digest` | The exact policy, profile and assumptions |

A changed fixture needs a new bound request; a previously verified view cannot
be moved onto it.

**What is signed.** Ed25519 strict verification covers a fixed, ordered array of
the schema version, trust domain, purpose, issuer, key id, event id, the binding
fields, issue and expiry times, outcome, the previous event's hash and the
evidence digest. Each statement links to the one before it. Evidence is capped
at 1 MiB, policies at 64 keys and histories at 4,096 events.

**What a signature means.** A verified signature identifies a configured key.
It does not identify a person, and it does not show that a measurement is
correct. Mapping keys to people and processes is a deployment obligation.

## Retained failure evidence

[Paper 006](Paper-006.md) covers how refused proposals are kept: a JSONL failure
ledger that chains entry digests, verifies restart state and emits a
count-and-head receipt. It also explains exactly which edits those checks catch
and why an independent anchor is needed if an attacker can rewrite the whole
file. Reuse of retained failures follows a controlled procedure with benign
checks, downgrade thresholds and decay, so that a past rejection never turns
into authority by itself.

## Research memory

`use_cases/research_memory.py` gives scoped, diagnostic failure guidance to
experiments. Candidates offered this way never become admitted antibodies
through this path.
