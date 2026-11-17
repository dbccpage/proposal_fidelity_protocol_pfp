# Standard Output Formats

Reusable output format templates for skills.

## Analysis Format

```markdown

# Analysis: {Topic}

## Problem Statement
{Clear problem definition}

## Approach
{Methodology used}

## Findings
{Key findings}

## Recommendations
{Actionable recommendations}

## Confidence Level
{Calibrated confidence with reasoning}

``` ext

## Technical Report Format

```markdown

# Technical Report: {Topic}

## Summary
{Executive summary}

## Background
{Context and prior work}

## Methodology
{Technical approach}

## Results
{Detailed findings}

## Discussion
{Interpretation}

## Limitations
{Known limitations}

## Next Steps
{Recommendations}

``` ext

## Complexity Analysis Format

```markdown

# Complexity Analysis: {Algorithm/System}

## Time Complexity
- Best case: O(...)
- Average case: O(...)
- Worst case: O(...)

## Space Complexity
- Auxiliary: O(...)
- Total: O(...)

## Communication Complexity [if distributed]
- Messages: O(...)
- Rounds: O(...)

## Tradeoffs
| Approach | Time | Space | Pros | Cons |
|----------|------|-------|------|------|
| ... | O(..) | O(..) | ... | ... |

``` ext

## Error/Issue Format

```markdown

# Issue Analysis: {Issue}

## Symptoms
{What was observed}

## Root Cause
{Underlying cause}

## Impact
{Severity and scope}

## Resolution
{Fix or mitigation}

## Prevention
{How to prevent recurrence}

``` ext

## Governance Audit Format

```markdown

# Governance Audit: {Artifact}

## Status
PASS / PARTIAL / FAIL / QUARANTINE / NOT PROVIDED / STALE

## Evidence Reviewed
{Files, commands, tests, citations}

## Credit Allowed
{What can be claimed}

## Credit Denied
{What cannot be claimed}

## Violations
{Constraint IDs and explanations}

## Required Remediation
{Specific next patches/tests}

## Blackrod Decision
{Credit decision}

``` ext

## Evidence Path Format

```markdown

# Evidence: {Ticket/Story ID}

## Artifact
Path: {file path}
SHA256: {hash}

## Verification
Method: {command or manual check}
Output: {capture or summary}

## Witness
Agent: {agent name}
Timestamp: {ISO8601}

``` ext
