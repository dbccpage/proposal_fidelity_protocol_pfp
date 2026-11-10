# pilot_0000195: d_physics_mtheory

AuthorityEffect: None.

This pilot tests PFP proposal fidelity and transfer of bounded repair rules across the original challenge family. The complete source problems remain under `../../../../omega_engine_pfp/tests/demo_004/`. Cases and source digests live in the canonical matrix.

Run `python -m omega_engine_woland.tests.pilots.challenge_suite --help` from the repository root. Use `--host` for trusted NO_LLM controls and `--replay` for independent reruns. A reference solver's output is a control, never a model response.

Compare a baseline prompt, a typed witness prompt, and a failure-derived rule on disjoint held-out cases. Allow at most two stages. Checker disagreement stops the run. Rules remain candidates until transfer and self-tolerance are measured. Live dispatch reserves a conservative stage cost against the USD 0.05 total run cap; no live dispatch is implied by this spec.

Rust support is initially limited to the existing Q40 certificate checker through the canonical Symbol Game host. Other challenges retain their original domain judges. No claim of general mathematical or physical truth is made.

Observed trials and harness defects are indexed in [the campaign evidence](../evidence/demo004_pfp_learning/README.md). This pilot protocol remains partially executed.
