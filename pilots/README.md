# pilots

`pilots/education/` holds teaching material: notes, runbooks, simulations and
scenes. Three readers still use it: `pfp/tests/finite_qm_workflow`,
`pfp/tests/test_consistency_teaching.py` and the wf19 challenge suite
(`workflows/wf19_failure_derived_rule_transfer/pilots/challenge_suite`).

The imported pilot estate that used to sit beside it was removed on 2026-11-12.
Its four reusable pilots moved first, into
`workflows/wf06_dialect_sweep/pilots/`, `workflows/wf08_staged_sealed_packets/pilots/`,
`workflows/wf11_dual_certificate_synthesis/pilots/` and
`workflows/wf16_substrate_crosswalk/pilots/`. The custody manifests are in
`dag/migrations/`, and the old bytes are in git history (commit `90228464`).

`.gitattributes` keeps every file here byte for byte (`* -text`).
