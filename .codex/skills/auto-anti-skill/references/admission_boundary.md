# Candidate and admission boundary

An anti-skill candidate records a possible recurring failure. It is not an admitted detector or repair.

Admission requires all of the following:

- At least two distinct episode IDs from at least two independent context keys.
- Evidence references and a clean counterexample.
- Held-out evaluation separated by conversation, task, and model where available.
- Measurable targeted-defect reduction with no protected-field loss.
- An evaluation receipt digest and explicit human review.
- A declared composition order or tested mutual commutation for overlapping repairs.

The v0 runtime does not implement the validator that would bind those facts to
an explicit human decision. `compile_registry_syntax_only` checks shape and
composition only, and both the loader and reviewer refuse every nonempty
registry. The shipped empty registry is therefore the only runtime-admissible
state in this packet.

The v0 syntax grammar contains structural detector kinds only. It accepts no arbitrary callable, executable regular expression, model verdict, or candidate-authored `PASS` field.

The original epistemic-immunity archive is provenance. Its recurrence thresholds, phrase classifiers, and hash-derived density scores are candidate-generating history, not evidence of correctness.
