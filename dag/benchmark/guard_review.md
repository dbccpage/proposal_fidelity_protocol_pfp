# Paid-run guard adversarial review

Three actionable findings reproduced before fixes; all are P1 for this paid-run admission guard.

1. **Mutable prepared wire bypasses its reservation.** `request_evidence()` exposes the same `wire` object used for dispatch. After a quote of 4,800 microusd, a synthetic caller changed `max_tokens` from 4,000 to 100,000 and re-enabled fallback. `complete()` sent the changed wire while its recorded digest still described the original. Return independent evidence and bind the actual dispatched wire.
2. **An unfinished campaign run does not block the next admission.** After closing and reopening a ledger with run 0 still `reserved`, run 1 was admitted and `blocked` remained false. This violates the declared stop-on-uncertain-charge policy following a crash. The existing full-run hold still limits planned reservations under honest-provider bounds; this is not an arithmetic-cap counterexample.
3. **Known charges are lost on later validation or artifact failure.** With a reported 110,000-microusd cost, either malformed token usage or a simulated response-artifact write failure left run spend at zero and only a 4,800-microusd quoted hold. The campaign recorded zero known spend and held 100,000. In the artifact case, the final receipt retained `actual_microusd: 110000` while its budget said zero spent. Retain known billing durably before fallible response processing and artifact persistence.

Four adversarial reproductions and three positive controls ran. Ordinary success, an intact known overrun, and a caught timeout behaved as intended. No obvious credential logging path was found in the reviewed fixed-destination, no-proxy, no-redirect transport; this is a bounded source observation, not production attestation.

All six requested files were fully read and unchanged. The actual benchmark seed and credentials were never read. Synthetic runs used a harmless fixture under a temporary directory in `dag/benchmark`, with the real HTTP method disabled. No existing tests, network calls or paid requests ran. Temporary fixtures were removed. Exact source hashes, source lines, probe outputs and qualifications are in `guard_review.json`.
