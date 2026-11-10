# pilot_0000199: Corrected causal refinement theorem

AuthorityEffect: None.

Distinct derivation target: OBL-R01-01, OBL-R01-02, OBL-R01-03 from PO035. The full
seed remains authoritative; the exact finite witness is a control, not the theorem.
Mode: `PFP-12-SIMPLICIAL-CARRIER`; refusal mode: `PFP-14-TYPED-REFUSAL`.

Five completed loops each traverse proposal, lift grant, witness check, negative
control and learning refinement. These are five provider trials and twenty host
stages. The test wrapper separately exposes 25 finite host controls (overlapping the
central matrix). Limits per pilot: USD0.05, 120000 provider tokens, 180seconds.

| Loop | Provider proposal capsule | Four host stage capsules |
|:--|:--|:--|
| 1 | test_00 | test_01-test_04 |
| 2 | test_05 | test_06-test_09 |
| 3 | test_10 | test_11-test_14 |
| 4 | test_15 | test_16-test_19 |
| 5 | test_20 | test_21-test_24 |

The actual versioned input/response files are in each capsule's `v2/` directory.
Original `test_spec.yaml` planning records are retained; [testplan.yaml](testplan.yaml)
indexes completed execution. Raw provider replies and source pins are in
[the evidence directory](../evidence/po035_derivations_20261012/pilot_0000199/).

Pilot199 grant and learning v2 capsules are posthoc extraction; live requests did not see these grants. Original live stage capsules are retained alongside v2.

Replay all five source-bound pilots and final prompts offline from the repository
root:

```powershell
.venv/Scripts/python.exe -m omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay --bundle omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012 --profile five-final-prompts
```

Read [findings and potential solution routes](../evidence/po035_derivations_20261012_v2/README.md)
and the [reviewed final prompt](../evidence/po035_derivations_20261012_v2/reviewed_final_prompts/pilot_0000199.yaml). All five loops are finished; do not
restart this run or add a sixth trial. The next round requires a separate budget.

This supports exact replay of finite checks and retained candidate learning.
It does not establish the analytical derivation, physical consequences or improved
single-shot success. The narrow result is five refused model attempts with reusable
experimental process advice. The next test is a paired original/final-prompt trial.
