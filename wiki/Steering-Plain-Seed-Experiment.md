# Steering: plain seed experiment

A common way to steer a multi-agent run is a long, carefully designed seed that
tells every role what to check. The source project tested the opposite: it gave
the run only the user's one-line task and watched what the host did and did not
actually check. Three versions followed, each repairing what the previous one
exposed.

## What the source did

The input was exactly:

```text
solve the meron sign problem inside our finite system
```

A long seed design existed, listing every check the run should cover, but it
was deliberately **not** appended. The run used the full role panel.

What the first run showed:

- The roles produced bound contributions, a builder produced a candidate, and
  reviewers agreed with fresh derivative checks at the finite scope. But the run
  had no acceptance check bound: an empty checker id and no check command.
  **Numeric results and unanimous review cannot fill those fields.**
- A prompt that lists the checks it wants does not make the host execute them.
  Role attendance is not evidence that a check ran.
- Worker identity is not role identity. Seven model workers produced 36
  contributions; one worker applied fifteen review perspectives in turn. Full
  attendance would not have meant independent agents. One role never got a turn
  before the repair allowance ran out, and its attendance was not recorded after
  the fact.
- Two replies began with a literal `\S`, which looks like the schema's
  non-blank pattern leaking into output. The source kept the bytes and recorded
  it as an observation, not a diagnosis.
- The 36 prompts totalled 995,495 bytes. Bytes are not tokens or cost, and the
  run supports no claim about speed, cheap models or a best template.

The second version kept the seed unchanged and bound a fixed host acceptance
operation that compares every field of the candidate with exact calculations.
The third added per-check receipts so that the run's record shows which checks
actually executed. A later closure fixed the evaluation limit, partial learning
and storage of the reusable procedure.

## Replicate it here

The local swarm now runs (see [running the local swarm](Steering.md#running-the-local-swarm)), and its
`teamwork start` refuses to begin without a bound acceptance check, which is
the repair this experiment led to. The lesson also replicates with
[PFP Lab](PFP-Lab.md): a scenario's moves are what the "roles" propose, and the
Lab's recomputation is the bound acceptance. Run any pack twice, once reading
only the proposals and once reading the receipt:

```powershell
python -m pfp_lab.cli.main packs paper-005-worked-session
python -m pfp_lab.cli.main run --pack paper-005-worked-session --receipt receipt.json
python -m pfp_lab.cli.main verify receipt.json
```

The first command shows what was proposed; only the second and third tell you
what was accepted, and `verify` replays the receipt independently.

## How it relates to PFP, EIS and PCIV

- **PFP.** The experiment is the PFP thesis in a field test: without a bound
  acceptance check there is no result, however good the reviews look.
- **PCIV.** The three versions are a prompt-and-harness lineage whose seed stayed
  fixed while the host contract changed; the fitness gains came from the host,
  not from rewording.
- **EIS.** The `\S` leakage is the kind of observation that can become guidance
  later, but only after a benign control shows it is a real pattern.

## Where the code lives

The prompt concepts the source relied on are in this repository:
`pfp/domain/prompts/pfp_prompt.py` (text leaf with a content digest),
`pfp/domain/rewriting/prompt_containment.py` (ordered containment),
`pfp/domain/prompts/prompts.py` (templates with declared slots) and
`pfp/domain/contracts/pfp_runtime.py` (the dispatch packet).
