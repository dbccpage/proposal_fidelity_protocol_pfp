"""Summarize replayed observations without promoting failures or candidate guidance."""
from collections import Counter
import csv
import io
import json
import sqlite3

import yaml

from .cases import FAMILIES, IDS, PILOTS
from .learn import report
from .metadata import standardize
from .prepare import CAMPAIGN, write_once


def publish():
    result = report()
    if result["provider_completed"] != 300 or result["statuses"].get("PLANNED"):
        raise ValueError("CAMPAIGN_INCOMPLETE")
    rows = result["rows"]
    if len({r["generation_id"] for r in rows}) != 300:
        raise ValueError("DUPLICATE_PROVIDER_GENERATION")
    root = PILOTS / "matrix" / CAMPAIGN
    summary = []
    for p in IDS:
        pilot = f"pilot_{p:07d}"
        subset = [r for r in rows if r["pilot_id"] == pilot]
        summary.append(dict(pilot=pilot, family=FAMILIES[p], baseline_calls=25,
            baseline_accepted=sum(r["arm"] == "baseline" and r["status"] == "HOST_ACCEPTED" for r in subset),
            guidance_calls=5, guidance_accepted=sum(r["arm"] == "guidance" and r["status"] == "HOST_ACCEPTED" for r in subset),
            answer_only_valid=sum(r["diagnostics"]["answer_valid"] is True for r in subset),
            cost_microusd=sum(r["cost_microusd"] for r in subset)))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)
    write_once(root / "pilot_results.csv", stream.getvalue().encode())
    signatures = {arm: dict(Counter(r["diagnostics"]["signature"] for r in rows if r["arm"] == arm)) for arm in ("baseline", "guidance")}
    baseline_by_path = {r["capsule"]: r for r in rows if r["arm"] == "baseline"}
    plan = yaml.safe_load((PILOTS / "matrix" / f"{CAMPAIGN}_guidance.yaml").read_text())
    followup_by_path = {r["capsule"]: r for r in rows if r["arm"] == "guidance"}
    pairs = Counter((baseline_by_path[p["parent_capsule"]]["status"], followup_by_path[p["capsule"]]["status"]) for p in plan["cases"])
    outcome = dict(admitted=False, authority_effect="None", matched_pairs=50,
        pair_outcomes={" -> ".join(k): v for k, v in pairs.items()}, schema_signatures=signatures,
        conclusion="Exploratory matched observations only; no automatic skill or antibody admission.")
    write_once(root / "guidance_outcome.yaml", outcome)
    candidate = yaml.safe_load((root / "candidate_guidance.yaml").read_text())
    for kind, artifact in candidate["artifacts"].items():
        write_once(root / "learning" / f"{kind}.yaml", dict(schema="pfp.learning-candidate.v1", kind=kind,
            admitted=False, authority_effect="None", evidence="../candidate_guidance.yaml", outcome="../guidance_outcome.yaml", **artifact))
    skill = ("---\nname: typed-summary-witness\ndescription: Experimental guidance for preserving typed summary objects and checking finite witnesses.\n---\n\n"
             "Status: candidate, not admitted. AuthorityEffect: None.\n\n"
             "Use only with the declared SPK-001 response schema. Name the required summary object fields, preserve exact rational strings, and check the proposed witness against the supplied carrier before emission. Never replace host checks with self-certification.\n\n"
             "Evidence: `../../candidate_guidance.yaml`; observed follow-up: `../../guidance_outcome.yaml`. "
             "These matched trials do not authorize a general efficacy claim or automatic activation.\n")
    write_once(root / "learning" / "typed-summary-witness" / "SKILL.md", skill.encode())
    ledger_path = root / "free_followup" / "budget.sqlite3"
    if ledger_path.exists():
        with sqlite3.connect(ledger_path) as db:
            ledger = {k: json.loads(v) for k, v in db.execute("select id,state from provider_budget")}
    else:
        ledger = json.loads((root / "free_followup" / "budget_snapshot.json").read_text())
    if any(a["state"] != "settled" for state in ledger.values() for a in state["attempts"].values()):
        raise ValueError("UNSETTLED_FREE_OBSERVATION")
    write_once(root / "free_followup" / "budget_snapshot.json", (json.dumps(ledger, indent=2)+"\n").encode())
    table = "\n".join(f"| {r['pilot']} | {r['family']} | {r['baseline_accepted']}/25 | {r['guidance_accepted']}/5 |" for r in summary)
    tokens = sum(r["usage"]["total_tokens"] for r in rows)
    accepted = sum(r["status"] == "HOST_ACCEPTED" for r in rows)
    text = f"""# Dossier pilot campaign: observed results

AuthorityEffect: None. These are finite development experiments, not a general model ranking.

## Completed work and source custody

The remaining four dossiers in `demo_003` became pilots 0000188–0000191. All 31 historical source files were copied byte-for-byte before the directory was removed. The source commit and SHA-256 mapping are in [the custody manifest](../../migration/dossier_replay_20261011_sources.json). Archived checker outputs retain their historical status; they are not fresh LLM evidence. Historical paths inside copied prompts remain provenance labels. The canonical matrix records the replacement paths.

Pilots 0000000–0000005 received fresh, harder carrier variants without overwriting earlier histories. The fixed baseline has 250 separate provider generations: five carriers by five representations in each of ten pilots. Pilots 1 and 5 repeat the same graph carriers, so there are **45 distinct mathematical carriers in 50 blocks**, not 250 independent problems. A separately recorded follow-up adds five matched guidance trials per pilot at rung 3: 50 additional calls and no new mathematical problems.

Every dispatched seed used the existing SPK-001 prompt template. Emoji and Egyptian glyphs replace the carrier's JSON tokens through an explicit reversible legend; the wrapper and instructions remain readable. This does not test an entirely glyph-only conversation. Every representation round-trips to the same carrier. Alternative minimum graph repairs, complementary spin witnesses and shifted LP potentials are accepted when they satisfy the exact predicate.

## Model observations

The completed deployment was `nvidia/nemotron-3.5-lightning:free`, temperature 0, reasoning disabled, 900 output tokens maximum, provider fallback disabled. Model metadata and prices were fetched before dispatch. **{accepted}/300** complete envelopes passed the host checks. The raw provider replies, exact request bodies, token usage, latency, finish reason, generation ID, schema and gate verdict are retained in each capsule. Offline replay reproduced all 300 verdicts and required unique generation IDs. Total reported tokens: **{tokens:,}**.

| Pilot | Task family | Baseline accepted | Guidance accepted |
|---|---|---:|---:|
{table}

Detailed outcomes are in `final_results.json` and `pilot_results.csv`. The answer-only diagnostic never changes a failed envelope into an accepted response. A typed host refusal also does not mean the model voluntarily abstained.

## Cost and the first failed attempt

All 300 completed free-model receipts reported cost **${result['cost_microusd']/1_000_000:.6f}**. The user authorized at most $0.05 per run; the free session used a stricter $0 campaign budget with catalog-confirmed zero input/output prices. No automatic retries or hidden fallback calls were used.

The initial DeepSeek V4.1 Flash request returned HTTP 429. The shared transport retained no provider body or generation ID. Its billed cost is **unknown**, not asserted to be zero; the **$0.003221 reservation remains unresolved** and paid retries remain blocked. `paid_attempt_budget_snapshot.json` and pilot 0000000 test_31 preserve that failure. The free replacement for that case is test_56. The free model is a new recorded experiment, not a mislabeled DeepSeek result.

## What the failures taught us

The dominant early failure was flattening the required summary object into a string. Some replies also violated JSON syntax, returned the wrong answer shape, or supplied invalid mathematical witnesses. The candidate guidance explicitly names nested summary fields and requests witness substitution. Its matched outcomes and schema signatures are recorded in `guidance_outcome.yaml`; fixed ordering and a single free deployment prevent a causal or cross-model claim.

`learning/` contains an evidence-linked candidate skill, antiskill, pattern, rule, prompt family and antibody. They remain **admitted: false**. A schema written in a prompt plus a strict host gate rejects invalid output; it does not itself constrain the model's token decoder. Provider-constrained decoding is registered as a future axis, not claimed as implemented by these trials. This campaign stops here rather than adding an optimization loop or sweeping models.

The old F2 checker could certify an unobstructed/nonminimal candidate. The new finite spin gate checks the actual optimum. Exact LP checks accept any feasible zero-gap certificate. The topology pilot separates adjacent-chain failures and declared-Betti mismatches from the absence of a cup-product carrier. Original dossier certificates and the original topology mismatch were rechecked with the new host predicates. No fresh Rust/Lean qualification, continuum result or manifold identification is claimed.

## Replay and targeted verification

From the repository root, with Python 3.12.10 and the package versions recorded in `python_environment.json`:

```sh
py -3.12 -m omega_engine_education.pilots.dossier_trials.run --replay --session free_followup
py -3.12 -m omega_engine_education.pilots.dossier_trials.learn
py -3.12 -m pytest omega_engine_education/pilots/dossier_trials/test_campaign.py omega_engine_education/pfp/tests/types/test_taxonomy_task_families_yaml.py omega_engine_education/pfp/tests/types/test_taxonomy_trial_statuses_yaml.py omega_engine_education/pfp/tests/types/test_taxonomy_enums_yaml.py -q
```

Replay verifies saved raw bytes and re-executes the host checker; it does not regenerate stochastic model completions. Changed inputs, requests, replies, model identity, checker source or recorded verdicts refuse replay. Independent SymPy/NetworkX finite oracles, alternate valid witnesses, wrong-witness controls and type mutations distinguish checker correctness from model performance. Only targeted local checks were run; no full canonical CI.
"""
    write_once(root / "REPORT.md", text.encode("utf-8"))
    standardize()
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    publish()
