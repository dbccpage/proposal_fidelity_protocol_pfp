"""Eight bounded original-family proposals on a pinned local HF checkpoint.

This is an explicit small-model feasibility pilot, not the frozen 7B/8B
replicated scientific protocols or their full public/hidden selection panels.
"""
import argparse
import base64
import json
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from adversary.tests.pilots.challenge_suite.catalog import SOURCE as CHALLENGE_SOURCE
from pfp.domain.quantum.pauli import PauliString
from pfp.infrastructure.adapters.decode_controls.local_hf_mechanism import (
    HfLocalRunner,
)
from pfp.infrastructure.task_turn import prepare_task_turn

SOURCE = CHALLENGE_SOURCE / "a_mechanism"
PROTOCOL_FILES = (
    "c002_attention_steering_sweep_correctness.md",
    "c003_head_attribution_activation_patching.md",
    "c004_grammar_masked_decode_ladder.md",
    "c008_activation_steering_sign_discipline.md",
)
PROMPT_RECIPES = {
    "local-mechanism-v1.0.0": dict(role="BASELINE_TYPED_INPUT_ORIGINAL_CERTIFICATE",
        instructions="Compute the task from input. Certificate fields must agree with the calculation."),
    "local-mechanism-v1.0.1": dict(role="CANDIDATE_CALCULATION_HINT_AND_MINIMAL_PRIVATE_SCRATCH",
        instructions="Do not copy the input or response schema. Calculate briefly on private scratch, then emit only the response envelope. "
        "Products: mark each negative factor, count the marks for negative_count, and return '-' exactly when that count is odd. "
        "Cycles: walk the requested cycle; add the listed claim when traversing forward and its negative when traversing backward. "
        "Pauli commutation: list exactly the zero-based positions where both letters are non-I and differ; return '-1' exactly when the list length is odd. "
        "Check that your answer follows from your certificate. Return canonical integer strings. The host does not supply the answer."),
}


def cases():
    rows = []
    for index, n in enumerate((6, 9)):
        nodes = [f"v{i}" for i in range(n)]
        directed = [(nodes[i], nodes[(i + 1) % n]) for i in range(n)]
        oriented = [(v, u) if i % 3 == 1 else (u, v) for i, (u, v) in enumerate(directed)]
        claims = {f"{u}->{v}": str((-1 if i % 2 else 1) * (11 + 3 * i)) for i, (u, v) in enumerate(oriented)}
        rows.append(dict(id=f"cycle-{n}", protocol="C002", kind="cycle_sum", nodes=nodes,
            edges=list(map(list, oriented)), claims=claims, cycle=nodes + [nodes[0]]))
    for index, n in enumerate((6, 8, 10, 12)):
        values = [(-1 if (i + index) % 3 else 1) * (3 + i * 2) for i in range(n)]
        rows.append(dict(id=f"product-{n}", protocol="C003", kind="product_sign", factors=values))
    for index, (p, q) in enumerate((("XYIZ", "ZYXI"), ("YYYY", "XXZZ"))):
        rows.append(dict(id=f"pauli-{index}", protocol="C008", kind="commutation", P=p, Q=q))
    return rows


def expected(case):
    if case["kind"] == "product_sign":
        count = sum(value < 0 for value in case["factors"])
        return dict(status="SOLVED", kind="product_sign", answer="-" if count % 2 else "+", negative_count=str(count))
    if case["kind"] == "cycle_sum":
        total = Fraction(0)
        for u, v in zip(case["cycle"], case["cycle"][1:]):
            total += Fraction(case["claims"][f"{u}->{v}"]) if f"{u}->{v}" in case["claims"] else -Fraction(case["claims"][f"{v}->{u}"])
        return dict(status="SOLVED", kind="cycle_sum", cycle=case["cycle"], sum=str(total))
    sites = [str(i) for i, (p, q) in enumerate(zip(case["P"], case["Q"])) if p != "I" and q != "I" and p != q]
    return dict(status="SOLVED", kind="commutation", sign="-1" if len(sites) % 2 else "+1", anticommuting_sites=sites)


def judge(case, answer):
    return answer == expected(case), "original finite certificate fields recomputed"


def second_judge(case, answer):
    if case["kind"] == "product_sign":
        product = 1
        for value in case["factors"]:
            product *= value
        valid = answer.get("answer") == ("-" if product < 0 else "+")
        valid = valid and answer.get("negative_count") == str(len([v for v in case["factors"] if v < 0]))
    elif case["kind"] == "commutation":
        valid = answer.get("sign") == ("+1" if PauliString(case["P"]).commutes_with(PauliString(case["Q"])) else "-1")
        independent_sites = [str(i) for i, (p, q) in enumerate(zip(case["P"], case["Q"]))
            if not PauliString(p).commutes_with(PauliString(q))]
        valid = valid and answer.get("anticommuting_sites") == independent_sites
    else:
        arrows = {(u, v): int(case["claims"][f"{u}->{v}"]) for u, v in case["edges"]}
        arrows.update({(v, u): -value for (u, v), value in list(arrows.items())})
        valid = answer.get("sum") == str(sum(arrows[edge] for edge in zip(case["cycle"], case["cycle"][1:])))
        valid = valid and answer.get("cycle") == case["cycle"]
    return valid and answer.get("status") == "SOLVED" and answer.get("kind") == case["kind"], "secondary Python/domain check; not native parity"


def turn_for(case, *, attempt_id, recipe="local-mechanism-v1.0.0"):
    # The schema declares certificate types/shape, never their expected values.
    scalar = dict(type="string", pattern=r"^(0|[1-9][0-9]*|-[1-9][0-9]*)$")
    props = dict(status={"const": "SOLVED"}, kind={"const": case["kind"]})
    if case["kind"] == "product_sign":
        props.update(answer={"enum": ["-", "+"]}, negative_count=scalar)
    elif case["kind"] == "cycle_sum":
        props.update(cycle=dict(type="array", items={"type": "string"}), sum=scalar)
    else:
        props.update(sign={"enum": ["-1", "+1"]}, anticommuting_sites=dict(type="array", items=scalar))
    if recipe not in PROMPT_RECIPES:
        raise ValueError("UNKNOWN_LOCAL_PROMPT_RECIPE")
    return prepare_task_turn(system="Solve the exact supplied task. Return only the typed response envelope.",
        user=PROMPT_RECIPES[recipe]["instructions"],
        task_id="local-original:" + case["id"], attempt_id=attempt_id,
        answer_schema=dict(type="object", properties=props, required=list(props), additionalProperties=False),
        checker_id="original-family-python-certificate-v1", context=case)


def finite_language(turn, case):
    # Includes wrong answers and wrong certificate counts: no host answer injected.
    answers = []
    if case["kind"] == "product_sign":
        answers = [dict(status="SOLVED", kind="product_sign", answer=sign, negative_count=str(count))
            for sign in ("-", "+") for count in range(len(case["factors"]) + 1)]
    elif case["kind"] == "commutation":
        sites = [str(i) for i in range(len(case["P"]))]
        answers = [dict(status="SOLVED", kind="commutation", sign=sign, anticommuting_sites=list(subset))
            for sign in ("-1", "+1") for n in range(len(sites) + 1) for subset in combinations(sites, n)]
    else:
        return None  # Do not sneak a host-computed cycle sum into a finite grammar.
    binding = {key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    return [json.dumps(binding | {"answer": answer}, separators=(",", ":")) for answer in answers]


def checkpoint_binding(model_dir, *, model_id, revision, custody_manifest=None):
    files = {path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(model_dir).iterdir()) if path.is_file()}
    result = dict(local_files=files, identity_status="DECLARED_REVISION_LOCAL_BYTES_ONLY")
    if custody_manifest is not None:
        raw = Path(custody_manifest).read_bytes()
        manifest = json.loads(raw)
        if (manifest.get("model_id") != model_id or manifest.get("revision") != revision
                or manifest.get("files") != files or manifest.get("remote_code") is not False
                or manifest.get("serialization") != "safetensors only"):
            raise ValueError("LOCAL_CHECKPOINT_CUSTODY_MISMATCH")
        result.update(identity_status="EXACT_BYTES_MATCH_EXISTING_COMPOSITION_MANIFEST",
            custody_manifest_sha256=sha256(raw).hexdigest())
    return result


def load_runner(model_dir, *, model_id, revision, custody_manifest=None):
    binding = checkpoint_binding(model_dir, model_id=model_id, revision=revision,
        custody_manifest=custody_manifest)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True,
        trust_remote_code=False, use_safetensors=True, torch_dtype=torch.float32, attn_implementation="eager")
    runner = HfLocalRunner(model, tokenizer, model_id=model_id, revision=revision)
    runner.pipeline.update(binding)
    return runner


def protocol_sources():
    """Require every real protocol source before any local inference."""
    sources = {}
    for name in PROTOCOL_FILES:
        path = SOURCE / name
        if not path.is_file():
            raise ValueError("LOCAL_MECHANISM_PROTOCOL_SOURCE_UNAVAILABLE:" + name)
        sources[name] = sha256(path.read_bytes()).hexdigest()
    return sources


def run(runner, *, recipe="local-mechanism-v1.0.0", selected_case_ids=None):
    sources = protocol_sources()
    rows = []
    for index, case in enumerate(cases()):
        if selected_case_ids is not None and case["id"] not in selected_case_ids:
            continue
        turn = turn_for(case, attempt_id=f"local-draw-{index}", recipe=recipe)
        options = dict(seed=41000 + index, max_tokens=160, temperature=0 if index % 2 == 0 else 0.7,
            allowed_replies=finite_language(turn, case))
        rendered = runner.render(turn)
        if index < 2:
            marker = '"claims"'
            start = rendered.index(marker)
            positions = runner.carrier_positions(rendered, [(start, start + len(marker))])
            options["attention"] = dict(layers=[0], positions=positions, delta=0 if index == 0 else 2)
        elif index < 4:
            options["heads"] = dict(layer=0, heads=[0], alpha=1 if index == 2 else 1.5)
        elif index < 6:
            # A clean/counterfactual one-sign pair, not a claimed causal ranking.
            clean = runner.capture(rendered, layer=0, kind="head", head=0)
            options["patch"] = dict(layer=0, head=0, value=clean)
        else:
            # Calibration is independent of every scored task and certificate.
            # The previous target-conditioned directions are quarantined in the
            # preserved initial receipts; they are not blind model observations.
            calibration = prepare_task_turn(system="Task-independent sign-token calibration.",
                user="The two sign symbols are +1 and -1. This is not a scored task.",
                task_id="fixed-sign-calibration-v1", attempt_id="calibration",
                answer_schema={"enum": ["+1", "-1"]}, checker_id="calibration-only-no-acceptance")
            calibration_text = runner.render(calibration)
            vector = (runner.capture(calibration_text + "+1", layer=0, kind="residual")
                - runner.capture(calibration_text + "-1", layer=0, kind="residual"))[0]
            options["residual"] = dict(layer=0, vector=vector, alpha=1 if index == 6 else -1)
        actual = runner.generate(turn, **options)
        raw = actual.pop("raw_reply")
        checked = turn.check(raw, judges=(("finite-original-certificate", lambda _c, a, case=case: judge(case, a)),
            ("secondary-domain-python", lambda _c, a, case=case: second_judge(case, a))), require_checker=True)
        rows.append(dict(case=case, prepared_prompt=turn.prompt.to_dict(), prompt_recipe=recipe,
            calibration="TASK_INDEPENDENT_FIXED_SIGN_CONTRAST" if index >= 6 else None,
            binding=turn.binding, generation=actual, pfp=checked,
            raw_reply_base64=base64.b64encode(raw).decode(), raw_reply_sha256=sha256(raw).hexdigest()))
    return dict(schema="pfp.local-mechanism-feasibility.v1", pipeline=runner.pipeline, sources=sources,
        prompt_recipe=dict(id=recipe, **PROMPT_RECIPES[recipe]),
        scope="EIGHT_ORIGINAL_FAMILY_PROPOSALS_NOT_FULL_PROTOCOL_OR_7B_REPLICATION", trials=rows,
        provider_calls=0, billed_usd="0", verified=sum(row["pfp"]["status"] == "HOST_ACCEPTED" for row in rows),
        limits=["No native parity for C002/C003/C008", "No public selection or hidden statistical gate",
            "Finite grammar covers bounded sign/commutation replies only; arbitrary C004 grammar remains open",
            "Local CPU compute unpriced; raw failures are retained"])


def main(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--custody-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recipe", choices=tuple(PROMPT_RECIPES), default="local-mechanism-v1.0.0")
    parser.add_argument("--case-id", action="append", choices=[case["id"] for case in cases()])
    parsed = parser.parse_args(args)
    runner = load_runner(parsed.model_dir, model_id=parsed.model_id, revision=parsed.revision,
        custody_manifest=parsed.custody_manifest)
    result = run(runner, recipe=parsed.recipe, selected_case_ids=parsed.case_id)
    parsed.output.parent.mkdir(parents=True, exist_ok=True)
    with parsed.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps(dict(trials=len(result["trials"]), verified=result["verified"],
        provider_calls=0, billed_usd="0")))


if __name__ == "__main__":
    main()
