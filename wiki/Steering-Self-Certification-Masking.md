# Steering: self-certification masking

A proposer that is allowed to write any token will sometimes write
`"status": "VERIFIED"` about its own work. The source project stopped this at
decode time: while the model was generating the status field, a logits processor
allowed only the proposer's legal states and set every self-certifying token to
minus infinity.

## What the source did

A grammar processor tracked the decoding prefix. When the output reached
`"proposal_status": "`, only `SUBMITTED` and `CANNOT_COMPLETE` could be
generated; `VERIFIED`, `APPROVED` and `AUTHORIZED` were hard-masked. The test
ran a small local model and checked that `VERIFIED` never appeared after that
prefix.

A related experiment compared three decoding controls on a cycle-repair task
with a 0.5B model: free decoding, a token mask and a slot grammar. Free decoding
produced prose that the host could not parse. The token mask parsed for three
integers and failed for four and five. The slot grammar parsed every time. None
of the three found a correct repair. A token mask also let the model write
`555555` for `3+4`: being in the allowed alphabet is not being correct.

So masking controls the **shape** of a reply and can forbid self-promotion. It
does not make the content right, and the host check is still needed.

## Replicate it here

Needs PyTorch, `transformers` and a small locally cached model; not run for this
page. `HfLocalRunner.generate` in
`pfp/infrastructure/adapters/decode_controls/local_hf_mechanism.py` takes
`allowed_replies`, builds a token trie from them and masks every other token at
each step:

```python
runner = HfLocalRunner(model, tokenizer, model_id="Qwen/Qwen2.5-0.5B-Instruct",
                       revision="<40-hex commit>")
reply = runner.generate(turn, seed=0, max_tokens=8,
                        allowed_replies=["SUBMITTED", "CANNOT_COMPLETE"])
```

The model (eager attention) and fast tokenizer are loaded by the caller; the
runner does not download anything. The trie restricts the whole reply to the
allowed strings, which is stricter than the source's prefix grammar, and it
enforces a declared language, not correctness. For a softer push,
`generate(..., logit_bias={token_id: delta})` adds a bounded bias between -16
and 16 to chosen token ids instead of forbidding them. The returned record
includes the prompt digest, token ids, the enforcement used and
`provider_calls=0`. `LocalHfMechanismAdapter` in the same file applies a carrier mask
without a model, for offline checks of the receipt shape.

The host half runs here now (checked) with [PFP Lab](PFP-Lab.md). Save this as
`claimed-fix.json`:

```json
{
  "schema": "pfp-lab.scenario.v1",
  "title": "A reply that claims a fix, checked by recomputation",
  "vertices": ["a", "b", "c"],
  "edges": [
    {"source": "a", "target": "b", "weight": 1},
    {"source": "b", "target": "c", "weight": 1},
    {"source": "c", "target": "a", "weight": 1}
  ],
  "moves": [
    {"move": "ASSERT", "source": "a", "target": "b", "value": "1"},
    {"move": "ASSERT", "source": "b", "target": "c", "value": "1"},
    {"move": "ASSERT", "source": "c", "target": "a", "value": "1"},
    {"move": "VERIFY", "obligation": "ZERO_OBSTRUCTION"},
    {"move": "CUT", "claims": [
      {"source": "a", "target": "b", "value": "1"},
      {"source": "b", "target": "c", "value": "1"},
      {"source": "c", "target": "a", "value": "5"}]},
    {"move": "CUT", "claims": [
      {"source": "a", "target": "b", "value": "1"},
      {"source": "b", "target": "c", "value": "1"},
      {"source": "c", "target": "a", "value": "-2"}]},
    {"move": "VERIFY", "obligation": "ZERO_OBSTRUCTION"}
  ]
}
```

```powershell
python -m pfp_lab.cli.main run claimed-fix.json
```

```text
step_004     VERIFY   no  VerificationFailed     3 -> 3
step_005     CUT      no  DefectIncrease         3 -> 7
step_006     CUT      yes ExactRepair            3 -> 0
step_007     VERIFY   yes Verified               0 -> 0
```

A `VERIFY` move is a request, not a status: the Lab recomputes the obstruction
and refuses it while the loop is still inconsistent, whatever the proposer
believes.

## How it relates to PFP, EIS and PCIV

- **PFP.** A proposer submits; only the host verifies. Masking enforces that
  division in the token stream, and the host check enforces it in the result.
- **EIS.** A self-certifying phrase is a detector match (Signal 1) that the
  [self-certification screen](Steering-Self-Certification-Screen.md) looks for
  when masking was not available.
- **PCIV.** A decoding control is part of a prompt variant's configuration and
  is recorded with the reader in a [prompt family](Steering-Prompt-Families.md).

## Where the code lives

`pfp/infrastructure/adapters/decode_controls/` (local runner and a vLLM adapter)
and the planned challenge write-ups in `pilots/llm_mechanism/planned/`,
especially `c004_grammar_masked_decode_ladder.md` and
`c005_hosted_decode_controls_bakeoff.md`.
