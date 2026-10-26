# Bounded observations, 14 October 2026

The [documented commands](empirical_gate_play.md) executed 74 Anthropic calls:
32 matched token observations across four models and 42 raw/SQLite injection
and benign-control observations on Haiku 5.5. No paid rerun or prompt tuning was
used to improve scores. AuthorityEffect: None.

The exact standard-rate estimate is **$0.1147284**. Per-call upward rounding in
the existing ledger accounts for **$0.114748**, below the authorized combined
$0.50. Anthropic supplied token usage, not an invoice; vendor cost remains
unavailable. All 74 attempts are settled under the explicitly rated policy.
The two original allocations remain $0.25 each.

## Token comparison

Each model returned eight measurements: raw/symbolic arms at 1, 2, 9 and 10.
The metric is reported input plus output tokens. The following unit differences
include malformed replies and are **diagnostic usage**, not admitted task
comparisons. Negative increments can result from varying completion lengths.

| Model | PFP-valid replies / 8 | Raw increments, 2−1 / 10−9 | Symbolic increments, 2−1 / 10−9 | Total at 10, raw / symbolic |
| --- | --- | --- | --- | --- |
| `claude-haiku-5-5` | 8 | 81 / 99 | 72 / 66 | 1,285 / 1,607 |
| `claude-haiku-4-5-20251001` | 0 | 74 / 40 | 73 / 46 | 1,098 / 1,360 |
| `claude-sonnet-5` | 2 | 58 / 57 | 85 / 20 | 1,369 / 1,659 |
| `claude-sonnet-4-5-20250929` | 0 | 90 / −8 | 152 / −55 | 1,146 / 1,290 |

Twenty-two replies failed `PFP_TASK_ENVELOPE`: models returned Markdown fences
or accompanying prose despite the JSON-only prompt; two token replies also
reached the fixed 384-output-token ceiling. Their original bytes remain
failures; stripping them after the fact would change the experiment. Complete
four-model PFP coverage is unavailable, so EMP001 emits no native witness.
Haiku 5.5's complete subset has a smaller late symbolic increment but a larger
total at ten tasks; it does not satisfy the token-saving fences.

Practical next PFP work is native structured-output support through the existing
typed provider request, followed by a new explicitly scoped experiment. The
current Anthropic builder refuses `response_format`; this run used prompting
only. Improving that transport capability is separate from editing old scores.
The result also shows why total overhead, valid answers and unit differences
must be reported separately.

## Injection and rewrites

Haiku 5.5 returned the legitimate answer for **20/20 attacks in both raw and
SQLite arms**. Both benign-control replies passed. Native EMP002 accepted that
finite witness. There is no observed advantage for SQLite here and no claim of
general injection immunity.

The separately executed 50-case Egglog collection preserves the declared ordered
bytes, roles, boundaries and repeated constraints. Native EMP003 accepted its
actual finite payload. Retained-report replays for tokens, injection and rewrites
make zero provider sends; rewrite replay also makes zero Egglog executions.

## Applied repairs and retained observations

The first paid reply exposed an accounting parser regression: Anthropic includes
`usage.output_tokens_details.thinking_tokens`. Its
[API contract](https://platform.claude.com/docs/en/api/typescript/messages)
defines this as a decomposition of the inclusive billed output count. The
adapter now validates that detail without charging it twice. It still refuses
unknown billable fields. The held original reply was recovered and rated from
its retained bytes before the remaining 31 token calls; it was never resent and
the original allowance was not reset.

The review also found that a failed benign control could previously admit an
attack-only passing witness. A genuine failing regression now passes with the
existing admission guard: measurements remain available, while failed controls
withhold the native witness.

Raw bodies and continuing SQLite accounting remain in the operator's original
workspace output directory. The raw token report SHA-256 is
`f15ef933e87b345501b0983e4bd9e3e0b429b9d68a4affcbd51c40dd70804267`; the injection report
SHA-256 is `98016ff437525f2234d13a6e14bf1dcf75ff6bc606f6145ddbfd0e78f7c4597c`.
The initial stopped token report is retained alongside its completed descendant.
These are observed execution records, not authenticated publication evidence.
