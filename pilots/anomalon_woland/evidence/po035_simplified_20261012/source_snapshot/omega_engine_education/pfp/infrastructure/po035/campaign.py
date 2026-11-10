"""PO035 composition, candidate learning, immutable capsules and final prompts."""

import argparse
import json
import os
import platform
import zipfile

import jsonschema
import yaml

from omega_engine_providers.infrastructure.openrouter_catalog import fetch_openrouter_catalog
from omega_engine_symbol_game.infrastructure.adapters.pfp_derivation import (
    PfpDerivationAdapter,
    model_pricing,
    replay_run,
)
from omega_engine_symbol_game.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    write_once,
)
from omega_engine_symbol_game.use_cases.pfp_derivation_loops import (
    DerivationLimits,
    run_derivation_loops,
)

from .cases import (
    BY_ID,
    CAMPAIGN,
    LIFTS,
    MODE,
    MODEL,
    PILOTS,
    ROOT,
    SOURCE,
    STAGES,
    TEMPLATE,
    load,
    prompt_container,
    proposal_body,
)
from .checking import evaluate, negative_control

EVIDENCE = PILOTS / "evidence" / CAMPAIGN
SOURCE_FILES = [
    *[
        f"omega_engine_education/pfp/infrastructure/po035/{name}.py"
        for name in ("cases", "checking", "campaign")
    ],
    "omega_engine_symbol_game/use_cases/pfp_derivation_loops.py",
    "omega_engine_symbol_game/infrastructure/adapters/pfp_derivation.py",
    "omega_engine_symbol_game/infrastructure/adapters/pfp_evidence.py",
    *[
        f"omega_engine_providers/infrastructure/{name}.py"
        for name in (
            "wire",
            "openai_compat",
            "openrouter_catalog",
            "openrouter_transport",
            "budget_ledger",
            "http",
            "openrouter_deadline",
        )
    ],
    "omega_engine_providers/domain/types.py",
    "omega_engine_providers/domain/ledger.py",
    TEMPLATE,
    f"{SOURCE}/claim_ledger.yaml",
    f"{SOURCE}/zero_container_relational_spacetime_and_witness_holonomy.md",
]


def sources():
    return dict(
        files={path: digest((ROOT / path).read_bytes()) for path in SOURCE_FILES},
        python=platform.python_version(),
        jsonschema=jsonschema.__version__,
        pyyaml=yaml.__version__,
    )


def capsule(pilot, loop, stage):
    return PILOTS / pilot / "tests" / f"test_{(loop - 1) * 5 + STAGES.index(stage):02d}"


def stage_record(pilot, loop, stage, input_doc, output):
    path = capsule(pilot, loop, stage)
    write_once(path / "input.yaml", yaml.safe_dump(input_doc, sort_keys=False).encode())
    write_once(path / "response.yaml", yaml.safe_dump(output, sort_keys=False).encode())
    return digest(canonical(output))


def observe(pilot, loop, path, prompt, result, receipt, context):
    verdict, payload = evaluate(pilot, prompt["prompt_id"], result["content"])
    body = proposal_body(payload) if payload else None
    common = dict(
        pilot_id=pilot,
        prompt_id=prompt["prompt_id"],
        loop=loop,
        raw_reply_sha256=receipt["raw_sha256"],
        authority_effect="None",
    )
    stage_record(
        pilot,
        loop,
        "proposal",
        prompt,
        {**common, "provider_status": "PROVIDER_COMPLETED", "receipt": receipt},
    )
    requested = body["requested_lifts"] if body else []
    old = context.get("granted_lifts", [])
    granted = sorted(set(old) | {row["id"] for row in requested if row["id"] in LIFTS})
    lift_result = {
        **common,
        "requested": requested,
        "granted": {key: LIFTS[key] for key in granted},
        "denied": [row for row in requested if row["id"] not in LIFTS],
        "condition": "Added hypotheses license only a conditional changed theorem.",
    }
    stage_record(
        pilot, loop, "lift_grant", {**common, "previous": old, "requested": requested}, lift_result
    )
    stage_record(pilot, loop, "witness_check", common, {**common, **verdict})
    control = negative_control(pilot, prompt["prompt_id"], payload)
    control["baseline_certificate_accepted"] = verdict["certificate_status"] == "HOST_ACCEPTED"
    stage_record(pilot, loop, "negative_control", common, {**common, **control})
    learning = []
    for index, item in enumerate(body["learning"] if body else []):
        learning.append(
            {
                **common,
                **item,
                "artifact_id": f"{pilot}:loop{loop:02d}:{item['kind']}:{index:02d}",
                "prompt_text_sha256": digest(prompt["user_prompt"].encode()),
                "original_seed_sha256": prompt["original_seed_sha256"],
                "status": "CANDIDATE",
                "admitted": False,
                "observed_schema_status": verdict["schema_status"],
                "observed_certificate_status": verdict["certificate_status"],
                "analytical_status": "UNVERIFIED",
                "negative_control": control,
            }
        )
    write_once(path / "candidate_learning.json", learning)
    guidance = context.get("guidance", []) + [
        {key: row[key] for key in ("artifact_id", "kind", "text", "failure_or_gain")}
        for row in learning
    ]
    # Retain every candidate on disk; only ten recent distinct texts enter the next prompt.
    seen = set()
    selected = []
    for row in reversed(guidance):
        if row["text"] not in seen:
            selected.append(row)
            seen.add(row["text"])
        if len(selected) == 10:
            break
    next_context = dict(
        parent_prompt_id=prompt["prompt_id"],
        granted_lifts=granted,
        guidance=list(reversed(selected)),
        feedback=verdict,
        previous_proposal={
            "prompt_id": prompt["prompt_id"],
            "raw_reply_sha256": receipt["raw_sha256"],
            "derivation": body["derivation"],
            "certificate": body["certificate"],
        }
        if body
        else None,
    )
    stage_record(
        pilot,
        loop,
        "learning_refinement",
        common,
        {**common, "candidate_artifacts": learning, "next_context": next_context},
    )
    write_once(path / "host_verdict.json", verdict)
    return next_context


def preserve_prior_evidence():
    old = ROOT / ".worktrees/oegov-planning/omega_engine_education/pilots"
    if not old.exists():
        return
    target = EVIDENCE / "historical_v1.zip"
    if target.exists():
        receipt = load(EVIDENCE / "historical_v1.json")
        if receipt["archive_sha256"] != digest(target.read_bytes()):
            raise ValueError("HISTORICAL_ARCHIVE_DIGEST_MISMATCH")
        with zipfile.ZipFile(target) as archive:
            if (
                archive.testzip() is not None
                or {name: digest(archive.read(name)) for name in archive.namelist()}
                != receipt["files"]
            ):
                raise ValueError("HISTORICAL_ARCHIVE_CONTENT_MISMATCH")
        return
    paths = [old / "matrix/po035_derivation_loops_20261011", old / "po035_derivation_trials"]
    paths += [old / f"pilot_{number:07d}" for number in range(192, 197)]
    manifest = {}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".zip.pending")
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in paths:
            for path in sorted(source.rglob("*")):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                name = path.relative_to(old).as_posix()
                raw = path.read_bytes()
                manifest[name] = digest(raw)
                archive.writestr(name, raw)
    os.replace(temporary, target)
    write_once(
        EVIDENCE / "historical_v1.json",
        dict(
            status="CONTAMINATED_AND_SUPERSEDED",
            authority_effect="None",
            archive_sha256=digest(target.read_bytes()),
            files=manifest,
            old_pilot_ids=list(range(192, 197)),
            new_pilot_ids=list(BY_ID),
            mapping_kind="replacement_research_recipes_not_renamed_trials",
            limitation="Historical 25 replies retained, excluded from capability and policy promotion. Old accepted spine responses leaked answers.",
        ),
    )


def prepare():
    preserve_prior_evidence()
    for pilot, row in BY_ID.items():
        folder = PILOTS / pilot
        spec = dict(
            schema="pfp.derivation-pilot.v1",
            authority_effect="None",
            pilot_id=pilot,
            task_family=row["family"],
            title=row["title"],
            source_obligations=row["obligations"],
            mode=MODE,
            refusal_mode="PFP-14-TYPED-REFUSAL",
            model=MODEL,
            limits=vars(DerivationLimits()),
            loops=5,
            stages=list(STAGES),
            tests=25,
            provider_calls_planned=5,
            host_stages_per_loop=4,
            analytical_acceptance="UNVERIFIED_UNTIL_INDEPENDENT_PROOF_REVIEW",
        )
        write_once(folder / "spec.yaml", yaml.safe_dump(spec, sort_keys=False).encode())
        seed = dict(
            prompt_id=f"{pilot}:po035:seed",
            original_seed=row["text"],
            seed_sha256=digest(row["text"].encode()),
            source_obligations=row["obligations"],
        )
        write_once(folder / "seed.yaml", yaml.safe_dump(seed, sort_keys=False).encode())
        write_once(folder / "prompt_template.yaml", (ROOT / TEMPLATE).read_bytes())
        write_once(
            folder / "p_star.yaml",
            yaml.safe_dump(
                prompt_container(pilot, 1), sort_keys=False, allow_unicode=True
            ).encode(),
        )
        write_once(
            folder / "README.md",
            (
                f"# {pilot}: {row['title']}\n\nAuthorityEffect: None.\n\n"
                f"This pilot attempts {', '.join(row['obligations'])} from PO035. The full derivation stays in its seed; the finite certificate is an independent control.\n\n"
                "Five loops each traverse proposal, lift grant, witness check, negative control, and learning refinement. These are five provider trials and twenty host stages, not twenty-five independent model trials.\n\n"
                "Limits per pilot: USD 0.05, 120000 total provider tokens, 180 seconds, five loops. No hidden retries or fallback. Learned guidance remains candidate advice, never automatically admitted.\n\n"
                "Run or replay through `python -m omega_engine_education.pfp.infrastructure.po035.campaign --replay`. Results and final prompts are in `../evidence/po035_derivations_20261012/`. Analytical derivations remain unverified; finite acceptance does not repair the paper's claim ledger.\n"
            ).encode(),
        )
        write_once(
            folder / "run.py",
            (
                '"""Canonical PO035 campaign entrypoint."""\nfrom omega_engine_education.pfp.infrastructure.po035.campaign import main\n\nif __name__ == \'__main__\':\n    main()\n'
            ).encode(),
        )
        write_once(
            folder / "tests/test_pilot.py",
            (
                '"""Twenty-five host-only adversarial controls; no provider calls."""\n'
                "import pytest\n"
                "from omega_engine_education.pfp.infrastructure.po035.test_fixtures import VARIANTS, check_variant\n\n"
                '@pytest.mark.parametrize("variant", VARIANTS)\n'
                f'def test_certificate_control(variant):\n    check_variant("{pilot}", variant)\n'
            ).encode(),
        )
        for loop in range(1, 6):
            for stage in STAGES:
                write_once(
                    capsule(pilot, loop, stage) / "test_spec.yaml",
                    yaml.safe_dump(
                        dict(
                            pilot_id=pilot,
                            loop=loop,
                            stage=stage,
                            status="PLANNED",
                            independent_model_trial=stage == "proposal",
                            source_obligations=row["obligations"],
                        ),
                        sort_keys=False,
                    ).encode(),
                )
    write_once(
        EVIDENCE / "authorization.json",
        dict(
            authority_effect="None",
            limits_per_pilot=vars(DerivationLimits()),
            provider="OpenRouter",
            model=MODEL,
            retries=0,
            user_authorized_prompt_dispatch=True,
            original_goal_scope="Five substantive PO035 derivations, learned candidate artifacts, five final prompts, commit push PR merge.",
        ),
    )


def run(pilot):
    prepare()
    raw = fetch_openrouter_catalog(timeout=20)
    row = model_pricing(raw, MODEL)
    root = EVIDENCE / pilot
    write_once(root / "catalog.json", raw)
    write_once(root / "pricing.json", row)
    port = PfpDerivationAdapter(
        pilot=pilot,
        folder=root,
        campaign=CAMPAIGN,
        model=MODEL,
        pricing_sha256=digest(raw),
        sources=sources(),
        prompt_builder=prompt_container,
        observer=observe,
    )
    result = run_derivation_loops(port)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "pilot_id",
                    "terminal",
                    "settled_calls",
                    "tokens",
                    "cost_microusd",
                    "elapsed_seconds",
                )
            }
        ),
        flush=True,
    )


def replay():
    rows = []
    for pilot in BY_ID:
        root = EVIDENCE / pilot
        raw = (root / "catalog.json").read_bytes()
        row = model_pricing(raw, MODEL)
        if load(root / "pricing.json") != row or load(root / "run.json")[
            "pricing_sha256"
        ] != digest(raw):
            raise ValueError("PRICING_BINDING_MISMATCH")
        rows.append(replay_run(root, pilot, MODEL, prompt_container, observe, sources()))
    return rows


def consolidate():
    rows = replay()
    candidates = []
    findings = []
    for row in rows:
        pilot = row["pilot_id"]
        root = EVIDENCE / pilot
        all_learning = []
        accepted = []
        derivations = []
        for path in sorted(root.glob("loop_*")):
            if not (path / "provider_receipt.json").exists():
                continue
            all_learning += load(path / "candidate_learning.json")
            prompt = load(path / "prompt.json")
            raw = decode_provider_content(path / "raw_reply.json")
            verdict, payload = evaluate(pilot, prompt["prompt_id"], raw)
            if payload:
                body = proposal_body(payload)
                derivations.append(
                    dict(
                        prompt_id=prompt["prompt_id"],
                        derivation=body["derivation"],
                        certificate=body["certificate"],
                        raw_sha256=digest((path / "raw_reply.json").read_bytes()),
                    )
                )
            if verdict["certificate_status"] == "HOST_ACCEPTED":
                accepted.append(prompt["prompt_id"])
        candidates += all_learning
        context = row["context"] | {
            "guidance": [
                {key: item[key] for key in ("artifact_id", "kind", "text", "failure_or_gain")}
                for item in all_learning
            ]
        }
        final = prompt_container(pilot, 6, context, final=True)
        final.update(
            candidate_artifact_ids=[item["artifact_id"] for item in all_learning],
            candidate_artifacts_sha256=digest(canonical(all_learning)),
            lineage_receipts=[
                str(path.relative_to(ROOT)).replace("\\", "/")
                for path in sorted(root.glob("loop_*/provider_receipt.json"))
            ],
            tag_status="CANDIDATE_UNADMITTED",
            analytical_status="UNVERIFIED",
        )
        write_once(
            EVIDENCE / "final_prompts" / f"{pilot}.yaml",
            yaml.safe_dump(final, sort_keys=False, allow_unicode=True).encode(),
        )
        findings.append(
            dict(
                pilot_id=pilot,
                source_obligations=BY_ID[pilot]["obligations"],
                terminal=load(root / "terminal.json"),
                finite_certificate_accepted_prompt_ids=accepted,
                model_derivation_proposals=derivations,
                learned_candidate_count=len(all_learning),
                analytical_status="UNVERIFIED",
                candidate_policy_admissions=0,
            )
        )
    write_once(EVIDENCE / "candidate_artifacts.json", candidates)
    write_once(
        EVIDENCE / "consolidated_findings.json",
        dict(
            authority_effect="None",
            pilots=findings,
            limitation="Retained derivations are potential solutions/counterexamples, not general theorem or physical verification. No causal guidance benefit is established without paired final-prompt trials.",
        ),
    )
    write_once(
        EVIDENCE / "replay.json", dict(status="REPLAY_VERIFIED", pilots=rows, sources=sources())
    )
    print(
        json.dumps(
            dict(
                replayed_calls=sum(row["replayed_calls"] for row in rows),
                final_prompts=5,
                candidate_artifacts=len(candidates),
            )
        ),
        flush=True,
    )


def decode_provider_content(path):
    from omega_engine_providers.infrastructure.wire import decode_reply

    return decode_reply(path.read_bytes())["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", choices=list(BY_ID))
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--consolidate", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.run:
        run(args.run)
    elif args.consolidate:
        consolidate()
    elif args.replay:
        print(json.dumps(replay()))
    else:
        parser.error("Choose --prepare, --run PILOT, --replay or --consolidate")


if __name__ == "__main__":
    main()
