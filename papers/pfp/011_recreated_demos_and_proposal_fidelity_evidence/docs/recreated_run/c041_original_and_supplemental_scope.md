# C041 full original replay and separate supplemental proposals

The [full retained-algorithm replay](c041_pinned_v4/C041/recreation_receipt.json) executed all 64 original cases and all 48 retained mutations with the explicitly pinned Lean 4.34.1 kernel. Both retained checker functions share the original compiler wrapper; this is kernel-checked target evidence, not independent checker provenance or a recovered model experiment.

| Evidence set | Denominator | Actual result |
|---|---:|---|
| Original cases | 64 | 58 accepted: 36 proof candidates and 22 refutation candidates; four warranted malformed-input refusals and two heartbeat abstentions. |
| Original mutations | 48 | All 48 dual-rejected; no crashes, disagreements or unbound records. |
| Supplemental proposals | 2 selected original cases | Both accepted by the unchanged source checkers and pinned kernel. The original solver was not called or changed. |
| New supplemental controls | 4 | Two corrupted proofs and two wrong-kind/target submissions dual-rejected. This denominator is distinct from the original 48 mutants. |

The original warranted refusals are `c041_poison_01` (malformed prelude), `c041_poison_02` (nonexistent function), `c041_poison_04` (Bool/Nat type mismatch) and `c041_poison_06` (nonexistent import). Their literal checker outputs identify `WARRANTED_REFUSAL` while returning false for a verified proof. These are faithful negative cases, not missing mathematical proofs.

The original solver returns `UNKNOWN / DECIDE_HEARTBEAT_EXCEEDED` for two unchanged targets. The [separate proposal stream](phi2_and_c041_supplement_v5/C041/evaluations.jsonl) checks a refutation of `c041_base_16`, using the counterexample `(39,39)` to `a,b<40 ⇒ a+b<70`, and a proof of `c041_ctrl_08`, deriving `k≤49` from `¬(50≤k)` and hence `k²≤2401<2600`. The candidate fixture bytes are bound by SHA256 `cabc1fa6dc08d4438fb09aa820fb271c2a81320824423900f0f3d4d2c9f515d2`. Both proposals preserve the original raw case hashes and statements. They are agent-authored supplemental proposals; their checked results do not improve the historical solver's score or establish model accuracy.

The original full batch self-digest is `15dba079325a3f864372d73fd805a7ab43d252503f765248629fa66aca2e1e1a`. The separately closed supplement batch self-digest is `f5e5195b73af22aed9dc71ad36dc214c3fe0629a50b1646292a9a8bec534677f`. [Coverage matrix v5](coverage_matrix_v5.json), self-digest `e00930703eb37a83b54727e57fa8854d521ec431e8db8f0e2be2aaa9f0d923e3`, retains the original full C041 row and appends `supplemental_candidate_checks` rather than replacing the other 62 cases.

The original full replay's subprocess transcripts bind checker-observed decoded text; its proof/judge/module snapshots bind actual file bytes. The new supplement additionally captures physical native stdout/stderr bytes and records the original text decoding and newline normalization returned to the source checkers. Neither representation retroactively recovers absent historical model responses.
