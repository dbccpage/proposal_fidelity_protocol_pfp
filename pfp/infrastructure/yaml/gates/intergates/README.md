# PFP intergate contracts

AuthorityEffect: None. The ten adjacent YAML files retain their original bytes as
design references. They contain proposed cognitive interpretations, not evidence
that a gate prevents sycophancy, guarantees progress or establishes a theorem.

The explicit finite resolution is `pfp-intergates-source-v1`. Its numeric and
signature predicates have one native owner, `omega_woland.intergates.v2`; Python
validates the declared input shape and uses an injected native evaluator. Missing
native composition refuses. Absence of `contract_profile`, or explicit
`legacy-diagnostic-v1`, keeps the original weaker diagnostic predicates. Unknown
and null profiles refuse; source-profile failure never falls back to legacy.

All observations remain scoped to the supplied bytes, metrics, history and trust
policy. The host must independently bind/read them. A diagnostic PASS grants no
execution authority, mathematical truth or arbitrary prompt-semantic equivalence.
The original YAML SHA remains the design-source identity; native output also
binds `source_profile_sha256` and the selected contract profile.

## Resolved finite contracts

All numeric inputs reject booleans and nonfinite values. Scores for critique,
vagueness, antagonism and exploit severity are in [0,1]. Round/turn indices are
positive integers and the previous record, when required, must be adjacent.
All source-profile requests include `contract_profile: pfp-intergates-source-v1`.
The exact top-level field types are declared in the existing
`omega_engine_woland/domain/intergates/payload_contract.py`.

| ID / design reference | Input and finite decision |
| --- | --- |
| IG01 [flow](01_flow_state_hysteresis.yaml) | `round_number`, `prompt_complexity_score`, `agent_capacity_score`, `feedback_loop_ms`, `feedback_loop_limit_ms`, `prior_round`. The score is explicitly the incremental delta, not an absolute prompt score. Delta is nonnegative; capacity and the host-selected latency limit are positive. Feedback latency must be at or below its host-selected limit. Ratio >1.2 blocks immediately. A first low ratio <0.8 requests adjustment; consecutive two low rounds produce stagnation. The prior record has round number, delta score and capacity; [0.8,1.2] is inclusive. |
| IG02 [surprise](02_epistemic_surprise_break.yaml) | `round_number`, `previous_prompt_kl_divergence`, `carrier_isomorphism_valid`, `carrier_mapping`. KL is in [0.15,3.5], inclusive. Mapping contains nonempty unique `source`/`target` string arrays and `forward`/`inverse` index permutations composing to identity between the supplied sets; different labels are allowed. A claimed boolean alone is insufficient. This finite bijection is not a general semantic-isomorphism proof. |
| IG03 [yielding](03_cowardice_evasion_filter.yaml) | Original critique/vagueness/yield/admission fields plus `typed_defect`, `sponsor_challenge_present`, `response_evidence_hex`, `explicit_refusal`. Yield without counter-evidence blocks unless a typed defect with nonempty `code`, exact `evidence_hex` and matching `evidence_sha256` is supplied. This resolves the YAML's unconditional-yield wording in favor of its explicit typed-defect exception. Severity >0.7 with vagueness >0.4 still blocks; a sponsor challenge requires evidence or explicit refusal. Typed evidence binding alone does not prove the defect correct. |
| IG04 [sandbox](04_playful_reversibility_sandbox.yaml) | `sandbox_boundary_active`, `declared_authority_effect`, `has_production_side_effects`, `canonical_before_hex`, `canonical_after_hex`, `sandbox_before_hex`, `sandbox_restored_hex`. Require active boundary, authority None, no production side effects, unchanged canonical bytes and exact sandbox rollback readback. This checks supplied readbacks; the evaluator does not create an OS sandbox. |
| IG05 [urgency](05_false_urgency_desensitization.yaml) | `prompt_text`, `urgency_indicators`, `sanitized_prompt_text`, `verification_started_ms`, `verification_completed_ms`, `minimum_buffer_ms`, `declared_time_constraint`. Recompute exact case-insensitive stripping of known/declared urgency markers; the downstream text must equal that result. The positive host-selected audit buffer must have elapsed, using supplied timestamps, with no sleeps. A declared deadline additionally requires the authenticated timestamp witness below. The pure predicate does not itself advance a clock or forward a prompt. |
| IG06 [rejoin](06_affective_deescalation_rejoin.yaml) | `turn_number`, `antagonism_score`, `prior_turn`, `has_acknowledged_error`, `repair_action_proposed`, `scar_before`, `scar_after`, `deescalation_envelope`. Adjacent history records whether antagonism is high (>0.6) for two turns. Each high current score requires the envelope, acknowledgement and a nonempty repair action before rejoin. Retain every prior scar. Supplied scores are operational observations, not diagnoses. |
| IG07 [consensus](07_manufactured_consensus_audit.yaml) | Distinct `agent_evaluator_ids`, matching distinct `sampling_seeds`, `producer_id`, `producer_context_hex`, `evaluator_contexts`, `dissenting_evaluator_ids`, `dissent_records`. At least two reviewers, none the producer; reviewer contexts differ from producer context. Each dissent record binds the declared reviewer to nonempty content bytes. Identity/seed/context diversity is a finite independence control, not proof of truth or statistical independence. |
| IG08 [quarantine](08_quarantine_recovery_containment.yaml) | `quarantine_cause`, `harm_class`, `repair_before_hex`, `repair_after_hex`, `candidate_content`, `checker_receipt_hex`, `checker_receipt_verdict`, plus shared trust and dual witnesses. Repair bytes must be nonempty, changed, and the exact accepted candidate. The checker receipt must accept that candidate; two distinct configured Stravinsky/Master issuers and public keys authenticate the same receipt. No trust or two arbitrary strings cannot admit. This profile covers changed prompt-byte repair; environment-only recovery needs its own explicit contract. |
| IG09 [defense](09_deception_countermeasure_tie.yaml) | `detected_exploit_uids`, `exploit_severities`, `bound_countermeasure_uids`, `applied_countermeasure_uids`. Unique aligned lists establish exact positional 1-to-1 UID associations. Every detected exploit needs its defense; severity >0.7 requires that corresponding defense actually be recorded as applied. The finite association does not establish real-world effectiveness. |
| IG10 [terminal](10_terminal_reality_tether.yaml) | `candidate_summary_text`, `checker_receipt_verdict`, `candidate_content`, `checker_receipt_hex`, plus shared trust/checker attestation. Recompute hype/four-part summary checks and parse exact receipt bytes; require ACCEPTED, exact candidate digest and matching configured `checker_id`. Authenticate the receipt under the declared checker trust policy. This is separate from native gate authorization and does not upgrade a finite checker to a universal proof. |

## Authenticated witness scope

IG08/IG10 use the existing EIS `TrustPolicy`, `Binding`, `SignedEvidence` verifier.
IG05 uses it only for a nonempty declared time constraint. Common fields are
`task_id`, `source_digest`, `candidate_content`, `trust_policy`, `expected_binding`
and `now`. The composing host pins the policy and bindings outside model output.
Verification is relative to that supplied policy; it does not establish an
independently authenticated operator or grant authority. Missing trust is an
explicit refusal, never a trusted boolean or fallback PASS.

The binding scope is `woland.intergate.source.v1`; `spec_id` is the exact gate ID,
`rule_digest` is the original YAML SHA reference, `subject_digest` hashes exact
candidate UTF-8 bytes, and `source_digest` matches the declared source.
`context_digest` hashes `task_id` UTF-8 except IG08, where it hashes the compact
UTF-8 JSON array `[task_id, quarantine_cause, harm_class, repair_before_hex,
repair_after_hex]`. Use the native owner to construct/check exact bindings.

- IG08: `witness_issuers` has configured `stravinsky`/`master` issuers;
  `dual_witnesses` contains exactly two signed ADMIT/REINSTATE statements over the
  exact checker receipt. Distinct issuer names alone are insufficient.
- IG10: `checker_issuer`, `checker_id`, `checker_attestation` bind a signed ADMIT
  statement to the exact checker receipt and configured checker identity.
- IG05: `timestamp_issuer`, `timestamp_witness` authenticate exact JSON payload
  bytes with `constraint_text`, `observed_at_ms`, `deadline_ms`. Constraint text
  must match; observed time equals verification completion; deadline is not
  before observation. `now` follows the existing EIS trust-clock contract.

## Python composition and readback

Construct `IntergateEvaluator(native_evaluator=callable)` at the outer host seam.
The callable takes `(gate_id, payload, history_edges)` and returns the actual
native `gate_evaluate` outcome. Python checks profile, gate, original YAML digest,
native implementation digest and authority ceiling before translating the result.
`last_native_result` retains the complete source-profile observation, including
IG05 `downstream_text`; it resets on each call. The existing persistence helper
accepts an optional evaluator and captures that result only when present. It
keeps the original unprofiled output shape and does not create a transport.

The original YAML files and captured receipts stay intact. Current host/native
source pins and actual replay remain separate from these design declarations.
