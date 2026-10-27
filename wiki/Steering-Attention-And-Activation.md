# Steering: attention and activation interventions

Besides masking output tokens, the source project edited the model's internal
computation on open-weight models: it hid distractor positions from attention,
patched individual heads between a clean and a corrupted prompt, and added
fixed directions to the residual stream.

## What the source did

- **Distractor-key masking.** On one prompt with `Qwen2.5-0.5B-Instruct`,
  masking the distractor key positions in every head and layer moved last-layer
  attention on the distractors from 0.043819 to 0, and the preferred digit stayed
  `7`. Masking the carrier positions instead changed the answer to `1`. That
  showed a real causal effect on one prompt; whether it raises accuracy on held
  out tasks was left as a planned measurement.
- **Head activation patching.** Activations of selected heads were copied from
  a clean prompt into a run on a corrupted one, to find which heads carry the
  mathematical content. The test ran live with TransformerLens hooks when that
  library was available and skipped otherwise.
- **Activation steering for sign discipline.** A planned challenge builds a
  contrastive steering vector on public Pauli-product cases and asks whether it
  beats an equal-norm random vector on hidden cases. The random-vector control is
  the point: a steering effect has to beat a direction chosen without the data.

Each intervention is reversible and logged, and every output still goes to the
host checker. An intervention that changes the answer is not thereby a better
answer.

## Replicate it here

Needs PyTorch, `transformers` and a locally cached Llama-family model loaded
with eager attention and a fast tokenizer; not run for this page. The runner
refuses a model without a pinned 40-character revision. `HfLocalRunner`
exposes the three interventions; each `forward` call returns the last-position
logits and a readout of what was changed:

```python
runner = HfLocalRunner(model, tokenizer, model_id="Qwen/Qwen2.5-0.5B-Instruct",
                       revision="<40-hex commit>")
text = runner.render(turn)
carrier = runner.carrier_positions(text, [(start, end)])   # character span -> token positions

# Bias attention toward the carrier keys in two layers (delta 0 to 16).
logits, readout = runner.forward(text, attention={"layers": [10, 11], "positions": carrier, "delta": 2.0})

# Patch one head's output from a clean prompt into a corrupted one.
clean = runner.capture(clean_text, layer=12, kind="head", head=3)
logits, readout = runner.forward(corrupted_text, patch={"layer": 12, "head": 3, "value": clean})

# Add a contrastive direction to the residual stream (alpha -4 to 4).
direction = (runner.capture(positive_text, layer=8, kind="residual")
             - runner.capture(negative_text, layer=8, kind="residual"))[0]
logits, readout = runner.forward(text, residual={"layer": 8, "alpha": 1.5, "vector": direction})
```

The runner adds `delta` to the eager attention mask at the chosen key
positions, so it raises attention on them; the source's distractor-masking
probe is not ported. `interventions()` in
`pfp/infrastructure/adapters/decode_controls/local_hf_mechanism.py` refuses
out-of-range layers, heads and scalars, and removes every hook afterwards.
`cache_parity()` checks that key-value-cache decoding matches a full forward
pass before any result is trusted. For the random-vector control, draw a vector
of the same norm as `direction` and run the same call.

Pair any intervention with a host check. For graph-repair tasks the simplest is
to write the model's proposed claims into a [PFP Lab](PFP-Lab.md) scenario and
run it: the Lab reports the obstruction regardless of how the claims were
produced.

## How it relates to PFP, EIS and PCIV

- **PFP.** These are proposer-side interventions. PFP's authority rule is
  unchanged: the edited model still only proposes.
- **EIS.** Not directly. An intervention is a configuration, not guidance text,
  so it does not pass through immune admission.
- **PCIV.** An intervention plus its controls (random vector, masked carrier)
  is a variant whose fitness has to be measured by an external checker on
  hidden tasks, never by the training cases.

## Where the code lives

`pfp/infrastructure/adapters/decode_controls/local_hf_mechanism.py` and the
planned challenges in `pfp/tests/demo_004/a_mechanism/`:
`c001_attention_distractor_mask_task_level.md`,
`c002_attention_steering_sweep_correctness.md`,
`c003_head_attribution_activation_patching.md`,
`c007_context_compaction_kv_surgery.md` and
`c008_activation_steering_sign_discipline.md`.
