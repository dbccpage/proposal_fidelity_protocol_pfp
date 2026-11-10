"""Create immutable planned capsules and preserve the remaining dossier sources."""
from __future__ import annotations

import json
import subprocess

import yaml

from .cases import FAMILIES, FORMS, IDS, PILOTS, SOURCES, sha, wrapped

CAMPAIGN = "dossier_replay_20261011"
ROOT = PILOTS.parents[1]


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"IMMUTABLE_ARTIFACT_CONFLICT: {path}")
        return
    with path.open("xb") as stream:
        stream.write(data)


def preserve_sources():
    old = PILOTS / "demo_003"
    manifest_path = PILOTS / "migration" / f"{CAMPAIGN}_sources.json"
    if not old.exists():
        return json.loads(manifest_path.read_text())
    rows = []
    for source in sorted(old.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(old).as_posix()
        owner = next((p for p, prefix in SOURCES.items() if relative.startswith(prefix + "/")), None)
        owner = owner or (189 if relative.startswith("demo_4/") else 191)
        prefix = SOURCES[owner] + "/"
        tail = relative[len(prefix):] if relative.startswith(prefix) else "notes/" + relative
        if source.name.startswith("test_") and source.suffix == ".py":
            tail += ".txt"  # preserved historical bytes, not an importable new test suite
        target = PILOTS / f"pilot_{owner:07d}" / "misc" / "source" / tail
        write_once(target, source.read_bytes())
        rows.append(dict(source=source.relative_to(ROOT).as_posix(), target=target.relative_to(ROOT).as_posix(), sha256=sha(source.read_bytes())))
    manifest = dict(schema="pfp.dossier-source-custody.v1", authority_effect="None",
                    source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), files=rows)
    write_once(manifest_path, json.dumps(manifest, indent=2).encode() + b"\n")
    return manifest


def prepare():
    preserve_sources()
    template_path = PILOTS / "pilot_0000000" / "prompt_template.yaml"
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    plan_path = PILOTS / "matrix" / f"{CAMPAIGN}.yaml"
    if plan_path.exists():
        return yaml.safe_load(plan_path.read_text())
    rows = []
    for pilot in IDS:
        folder = PILOTS / f"pilot_{pilot:07d}"
        existing = [int(p.name[5:]) for p in (folder / "tests").glob("test_[0-9][0-9]")]
        first = max(existing, default=-1) + 1
        if first + 25 > 100:
            raise ValueError("PILOT_TEST_LIMIT")
        if pilot >= 188:
            write_once(folder / "prompt_template.yaml", template_path.read_bytes())
            write_once(folder / "seed.yaml", dict(schema="pfp.dossier-seed-family.v1", pilot_id=folder.name,
                task_family=FAMILIES[pilot], seed_prompt="Generate an exact finite certificate from the declared carrier; never promote undeclared structure.",
                variants="tests/test_00 through tests/test_24 contain the authoritative per-trial carrier and wrapped seed.",
                source="misc/source", authority_effect="None"))
            write_once(folder / "spec.yaml", dict(schema="pfp.pilot-spec.v1", pilot_id=folder.name, authority_effect="None",
                phase="planned_provider_trials", coordinates=dict(task_family=FAMILIES[pilot], difficulty_rung=3,
                    model_id="awaiting-user-model-selection", temperature=0.0, stage_count=1),
                host_gate=dict(checker_id="PFP-DOSSIER-EXACT-v1", implementation="../dossier_trials/checking.py"),
                test_plan=dict(path="testplan.yaml", tests=25), responses=dict(directory="tests")))
            write_once(folder / "testplan.yaml", dict(schema="pfp.testplan.v1", campaign=CAMPAIGN,
                tests=25, independent_carriers=5, representations=list(FORMS), live_status="PLANNED",
                claim="Five matched carrier blocks, not 25 independent problems. Each provider call is independent; no cached calls counted."))
            write_once(folder / "README.md", (f"# {folder.name}: {FAMILIES[pilot]}\n\nAuthorityEffect: None.\n\n"
                "The 25 planned tests cross five finite carriers with five wrapped representations. "
                "Emoji and Egyptian glyphs encode the carrier only; the SPK-001 template and decoding legend remain explicit. "
                "Host checks accept alternative valid witnesses. Historical source bytes are under `misc/source`; they are not new run results.\n\n"
                f"Run and replay with `python -m omega_engine_education.pilots.dossier_trials.run`; see `../matrix/{CAMPAIGN}.yaml`. "
                "A planned capsule is not a provider result. Deterministic replay checks saved response bytes; it does not regenerate stochastic model output.\n").encode())
        for rung in range(1, 6):
            for form in FORMS:
                index = first + (rung-1)*5 + FORMS.index(form)
                case = wrapped(pilot, rung, form, template)
                case.update(campaign=CAMPAIGN, pilot_id=folder.name, test_index=index,
                            template_sha256=sha(template_path.read_bytes()))
                capsule = folder / "tests" / f"test_{index:02d}"
                write_once(capsule / "input.yaml", case)
                write_once(capsule / "test_spec.yaml", dict(schema="pfp.test-spec.v1", campaign=CAMPAIGN,
                    pilot_id=folder.name, test_index=index, task_family=FAMILIES[pilot], difficulty_rung=rung,
                    representation_rewrite=form, wrapper="SPK-001", observation_mode="INDEPENDENT_MODEL_TRIAL",
                    matched_carrier_id=case["carrier_sha256"], expected_outcome="HOST_CHECKED_WITNESS",
                    actual_outcome="PLANNED", model_id="awaiting-user-model-selection", authority_effect="None"))
                rows.append(dict(pilot_id=folder.name, capsule=capsule.relative_to(PILOTS).as_posix(),
                                 input_sha256=sha((capsule / "input.yaml").read_bytes())))
        if pilot < 188:
            # This pointer adds a new block without rewriting any earlier test plan or capsule.
            write_once(folder / "misc" / f"{CAMPAIGN}_plan.yaml", dict(campaign=CAMPAIGN, first_test=first,
                last_test=first+24, new_tests=25, earlier_tests_preserved=len(existing), independent_carriers=5))
    plan = dict(schema="pfp.dossier-campaign.v1", campaign=CAMPAIGN, authority_effect="None",
                new_pilots=[f"pilot_{p:07d}" for p in SOURCES], tests=250,
                carrier_blocks=50, distinct_carriers=45, matched_representations=5,
                shared_carrier_note="Pilots 1 and 5 deliberately repeat the graph carriers; do not treat those blocks as new problems.",
                status="PLANNED", cases=rows)
    write_once(plan_path, plan)
    from .metadata import standardize
    standardize()
    return plan


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
