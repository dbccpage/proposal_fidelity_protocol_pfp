# Routing Monopoly Breaker & Open Obligation Frontier

This reference document specifies the protocols for detecting cognitive routing monopolies across proposal pipelines and systematically harvesting estate-wide open obligations into a resumable, actionable frontier.

---

## Part 1: Curious Routing Monopoly Breaker

When an automated routing pipeline or committee repeatedly routes tasks or proposals to the same destination, the router ceases to route: it exhibits **cognitive capture**.

```text
                  Incoming Proposals
                          │
                          ▼
            [Routing Distribution Tabulator]
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    [Share ≤ 50%: DIVERSE]      [Share > 50%: CAPTURE RISK]
                                        │
                                        ▼
                            [Generate Counter-Route]
                            Identify alternative council;
                            declare deciding evidence witness
```

### 1. Protocol:
1. **Distribution Tabulation:** Tabulate destination councils across the active proposal or task register.
2. **Monopoly Metric:** Compute the queue share held by the single most frequent destination:
   $$\operatorname{Share}(C^*) = \frac{\operatorname{Count}(C^*)}{\sum_{c} \operatorname{Count}(c)}$$
3. **Capture Threshold:** If $\operatorname{Share}(C^*) > 0.50$, the queue is declared in a **Monopoly State**.
4. **Counter-Route Generation:** For every proposal routed to the dominant council under a monopoly state:
   - Construct the strongest alternative council assignment (e.g. Nous, Dianoia, Thanatos).
   - Formulate a concrete **Decision Witness**: state precisely what empirical data or formal proof would decide between the primary route and the counter-route.
5. **Report & Fence:** Report the distribution and counter-routes. Woland never forces re-routing; the decision remains with the governing routing authority.

### 2. Terminals:
- `DIVERSE`: No single destination holds $> 50\%$ of the active queue.
- `CONCENTRATED`: Single destination holds between $35\%$ and $50\%$; monitor trend.
- `MONOPOLY`: Single destination holds $> 50\%$; trigger mandatory counter-routing.
- `COUNTER_ROUTE_PROPOSED`: Alternative council path and decision witness documented.

---

## Part 2: Curious Open Obligation Frontier

Software and mathematical repositories are frequently honest about their own gaps in local comments, but fail to collect them into an actionable backlog. Uncollected gaps become forgotten debt.

### 1. Protocol:
1. **Obligation Harvester:** Scan technical specifications (`plans/specs/**`), epics (`plans/epics/**`), `SKILL.md` bodies, and runbook ledgers for self-declared uncompleted work:
   - Target strings: `"open obligation"`, `"not this change"`, `"residual"`, `"UNBUDGETED"`, `"left open"`, `"human decision"`.
2. **Tuple Capture:** For each match, record:
   - **Claim:** The exact statement of what remains incomplete.
   - **Provenance:** Source file, line number, and commit/date written.
   - **Status:** Current resolution state (`OPEN`, `RESOLVED_ELSEWHERE`, `SUPERSEDED`, `NO_NEXT_STEP`).
3. **The Next-Step Mandate:**
   > **An obligation without a concrete next step is a wish.**
   Every harvested row MUST specify:
   - A designated owner or responsible council.
   - The immediate next action required to unblock or resolve it.
4. **Append-Only Ledger:** Append harvested entries to `_ooutwire/ledgers/open_obligations.jsonl`. Existing lines are immutable; resolutions append update records.

### 2. Terminals:
- `OPEN`: Valid unaddressed obligation with declared owner and next step.
- `RESOLVED_ELSEWHERE`: Obligation addressed in a subsequent commit or document.
- `SUPERSEDED`: Obligation rendered moot by architectural change.
- `NO_NEXT_STEP`: Defective obligation missing actionable path; flagged for immediate triage.

### 3. Nonclaims
Collecting an obligation frontier creates visibility into technical debt; it does not commit resources, schedule sprints, or prioritize implementation.
