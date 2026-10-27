# Steering: closed artifact schema

Asking a model for "JSON in a code fence" invites half-structured prose that a
host then has to scrape. The source project instead gave the builder and repair
roles a closed object schema supplied by the host. The model proposes the
object inside the PFP reply envelope; the host encodes it.

## What the source did

- The host supplies a closed schema: an object type with every property
  required and no extra properties.
- The builder's bound object is JSON-encoded **by the host**, deterministically.
- The host does not repair unbound prose, extract an object from code fences, or
  label host-derived text as if the model had written it.
- The model's exact raw bytes and the provider's raw bytes are kept alongside the
  encoded object.
- JSON and schema validity are not task acceptance. A valid object still goes
  to the task's own checker.

The same idea appears in the critique contract: a critic must end its reply
with exactly one fenced block tagged `critique` holding
`{"blocking": ..., "counterexample": ..., "kind": ...}`. Two blocks, or none,
make the critique malformed, and a malformed critique blocks (see
[Critique loop](Steering-Critique-Loop.md)).

## Replicate it here

The strict decoding half is already a runnable demo:
[Strict provider reply JSON](Test-Strict-Provider-Reply-JSON.md) refuses
duplicate keys, non-finite numbers, bad bytes and non-object roots without
echoing the reply.

```powershell
python -m pytest demos/provider_reply_guard/test_reply_guard_strict_json.py -q
```

[PFP Lab](PFP-Lab.md) uses the same discipline for its own input: a scenario
with an unknown field, a float, or a boolean where a number belongs is refused
before anything runs (`python -m pfp_lab.cli.main schema` writes the closed
schemas). Feed a model's proposed moves to the Lab as a scenario and the Lab's
refusal is the schema check, while its recomputation is the task check.

The local swarm accepts `teamwork start --artifact-schema <file>` (see
[running the local swarm](Steering.md#running-the-local-swarm)); that option was not exercised for this page.

## How it relates to PFP, EIS and PCIV

- **PFP.** The envelope binds task, attempt and input; the closed object is the
  proposal inside it. Encoding by the host removes one place where a model's
  formatting could change meaning.
- **EIS.** A reply that fails the schema is a typed refusal with its bytes kept,
  which gives the immune system evidence instead of a silently repaired object.
- **PCIV.** A closed schema is part of a prompt variant; replies that fail it are
  recorded as failed calls in the [prompt family](Steering-Prompt-Families.md).

## Where the code lives

`pfp/domain/aggregates/prompt_artifact.py` and
`pfp/infrastructure/trace/provider_dispatch.py` for artifacts and dispatch; the
critique contract is `CRITIQUE_REPLY_CONTRACT` in `ops/adversary/domain/evidence.py`.
