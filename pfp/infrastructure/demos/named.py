"""Bounded named experiments and explicitly labelled illustrations."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from fractions import Fraction
from importlib.resources import files

from pfp.domain.demos import (
    DemoRefusal,
    strict_descent,
)
from pfp.infrastructure.adapters.mssn_research import loader
from pfp.use_cases.mssn_demo import evaluate_cases

from .canonical import digest


def need(condition, detail):
    if not condition:
        raise DemoRefusal("SCENARIO_CHECK_FAILED", detail)


_RETIRED_KINDS = frozenset(
    {
        "quantum",
        "meron-2d",
        "meron-3d",
        "meron-4d",
        "meron-4d-su2",
        "meron-benchmark",
        "cohomology",
    }
)
_RETIRED_IDS = frozenset(
    {
        "demo_q40_quantum_solver",
        "demo_meron_2d_gross_neveu",
        "demo_meron_3d_string_linking",
        "demo_meron_4d_half_instanton",
        "demo_meron_4d_su2_gauge",
        "demo_meron_2d_benchmark",
    }
)


def run_named(scenario_id, fixture, proposals, quarantine, *, live: bool = False):
    if scenario_id in _RETIRED_IDS or fixture.get("kind") in _RETIRED_KINDS:
        raise DemoRefusal("SCENARIO_RETIRED", scenario_id)
    kind = fixture["kind"]
    if kind == "illustration":
        return {
            "status": "ILLUSTRATION_ONLY",
            "scope": fixture["scope"],
            "declared_data": fixture["data"],
        }
    if kind == "native":
        return native(fixture, proposals)
    if kind == "levels":
        levels = {
            f"mss-{i:03d}": evaluate_cases(loader.checker(i), loader.fixture(i)["cases"])
            for i in range(101)
        }
        need(
            all(c["matches_expectation"] for cases in levels.values() for c in cases),
            "level case expectations",
        )
        from pfp.infrastructure.adapters.mssn_scenarios.product_cell_ring import (
            run_product_cell_ring,
        )

        return {"status": "CHECKED", "levels": levels, "product_cell_ring": run_product_cell_ring()}
    if kind == "protocol":
        from pfp.infrastructure.adapters.mssn_scenarios.protocol import (
            run_all_protocol_matrix,
            run_live_protocol_matrix,
        )

        if live:
            value = run_live_protocol_matrix(lambda prompt: proposals.propose(prompt, ""))
            need(value["provider_calls"] > 0, "live protocol made no provider call")
            return {
                "status": "CHECKED",
                "scope": (
                    "Live OpenRouter proposer over the demo 3 host. "
                    "Arm dispositions are host records from this pass, not a treatment-effect claim."
                ),
                "matrix": value,
            }
        value = run_all_protocol_matrix()
        need(
            len(value["runs"]) == 5 and all(len(arms) == 6 for arms in value["runs"].values()),
            "protocol matrix cardinality",
        )
        return {
            "status": "CHECKED",
            "scope": "30 scripted finite host protocol arms; no live-model efficacy claim",
            "matrix": value,
        }
    if kind == "sign-gauge":
        from pfp.infrastructure.adapters.mssn_research.sign_switching import (
            classify_sign_gauge,
            verify_cycle,
            verify_gauge,
        )

        outcomes = []
        for case in fixture["cases"]:
            result = classify_sign_gauge(case["matrix"])
            actual = "GAUGE" if result.gaugeable else "CYCLE"
            need(actual == case["expected"], case["id"] + " disposition")
            need(
                verify_gauge(case["matrix"], result.gauge)
                if result.gaugeable
                else verify_cycle(case["matrix"], result.cycle),
                case["id"] + " independent witness replay",
            )
            outcomes.append(
                {"case_id": case["id"], "result": asdict(result), "witness_replayed": True}
            )
        return {
            "status": "CHECKED",
            "scope": fixture["scope"],
            "cases": json.loads(json.dumps(outcomes, default=str)),
        }
    if kind == "finite-library":
        from pfp.infrastructure.adapters.mssn_scenarios import (
            antimorphic_reversal,
            polygraph_confluence,
            product_cell_ring,
            token_frontier,
        )

        functions = {
            "demo_token_frontier": token_frontier.run_frontier_scenarios,
            "demo_antimorphic_reversal": antimorphic_reversal.run_antimorphism_scenarios,
            "demo_polygraph_confluence": lambda: polygraph_confluence.run_polygraph_confluence_demo(
                verbose=False
            ),
            "product_cell_ring": product_cell_ring.run_product_cell_ring,
        }
        return {"status": "CHECKED", "scope": fixture["scope"], "result": functions[scenario_id]()}
    if kind == "tower-lift":
        from pfp.domain.mssn_research.grammar.spectral_geometry import LiftGoal
        from pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel
        from pfp.domain.mssn_research.grammar.lift_policies import (
    check_lift_necessity_certificate,
    execute_bounded_lift_necessity_search,
)

        rows = []
        for level, goal in (
            (0, LiftGoal.IRREFLEXIVE_WITNESSED_RELATION),
            (1, LiftGoal.DIRECTED_PATH_COMPOSITION),
            (1, LiftGoal.DIRECTED_CYCLE_THREE),
        ):
            cert = execute_bounded_lift_necessity_search(StageLevel(level), goal).unwrap()
            need(check_lift_necessity_certificate(cert).is_ok(), "lift certificate replay")
            rows.append(
                {
                    "from_stage": level,
                    "to_stage": cert.target_stage.level,
                    "goal": goal.value,
                    "exhaustion_digest": cert.exhaustion_proof_digest.value,
                    "target_witness": cert.target_resolution_witness,
                }
            )
        return {"status": "CHECKED", "certificates": rows}
    if kind == "genesis":
        data = files(loader.PACKAGE).joinpath("genesis_crosswalk.md").read_bytes()
        need(digest(data) == fixture["source_sha256"], "compendium pin")
        need(not data.startswith(b"\xef\xbb\xbf") and b"\x1b" not in data, "encoding")
        text = data.decode("utf-8")
        parts = re.split(r'<a id="gen-(\d{3})"></a>', text)
        sections = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
        need(set(sections) == set(range(101)), "101 unique Genesis sections")
        need(
            all(fixture["stage_pin"] in value for value in sections.values()), "section stage pins"
        )
        for pattern in fixture["forbidden_patterns"]:
            need(re.search(pattern, text, re.I) is None, "claim hygiene")
        return {
            "status": "CHECKED",
            "total_papers_verified": 101,
            "stage_pin": fixture["stage_pin"],
            "source_sha256": digest(data),
        }
    if kind == "immune":
        return immune(fixture, proposals, quarantine)
    raise DemoRefusal("SCENARIO_ADAPTER_UNAVAILABLE", kind)


def native(fixture, proposals):
    from adversary.infrastructure.providers.adapters.native_functional import (
        NativeFunctionalInputRefused,
        NativeFunctionalRefusal,
        NativeFunctionalUnavailable,
        compute_graph_phi1,
    )

    adapter = fixture["adapter"]
    if adapter != "graph_phi1":
        raise DemoRefusal(
            "FUNCTIONAL_ADAPTER_UNAVAILABLE",
            adapter + "; retained historical values are not newly evaluated",
        )
    outputs = []
    for case in fixture["cases"]:
        try:
            before, _ = compute_graph_phi1(
                case["vertices"],
                [(u, v, Fraction(w)) for u, v, w in case["edges"]],
                {(u, v): Fraction(w) for u, v, w in case["before"]},
            )
            after, _ = compute_graph_phi1(
                case["vertices"],
                [(u, v, Fraction(w)) for u, v, w in case["edges"]],
                {(u, v): Fraction(w) for u, v, w in case["after"]},
            )
        except NativeFunctionalUnavailable as exc:
            raise DemoRefusal(exc.code, "explicit pinned Rust graph executable required") from exc
        except NativeFunctionalRefusal as exc:
            # The evaluator ran and refused: keep its own reason in the receipt.
            raise DemoRefusal(
                exc.code, f"{exc.reason} (native exit status {exc.returncode})"
            ) from exc
        except NativeFunctionalInputRefused as exc:
            raise DemoRefusal(exc.code, exc.reason) from exc
        outputs.append(
            {
                "case_id": case["id"],
                "phi1_before": str(before),
                "phi1_after": str(after),
                "strict_descent": strict_descent(before, after),
            }
        )
    return {
        "status": "CHECKED",
        "cases": outputs,
        "scope": "native exact graph functional on declared finite carriers",
    }


def immune(fixture, proposals, quarantine):
    """The OEEIS two-signal screen on the pharmacy controls, farm probes and replies.

    All screening is the single OEEIS implementation in
    `eis.infrastructure.immune_demo_screens`.
    Signal 2 comes from host payload checks, never from the number of detector
    matches. The pharmacy's native classes need the built Symbol Game host; without
    it this scenario is a typed refusal (NATIVE_PHARMACY_UNAVAILABLE).
    """
    from eis.infrastructure.immune_demo_screens import (
        screen_farm_probe,
        screen_pharmacy_control,
        screen_reply,
    )
    from eis.infrastructure.native_pharmacy import (
        NativePharmacy,
        NativePharmacyUnavailable,
    )
    from pfp.infrastructure.adapters.mssn_scenarios.immune_fixtures import (
        NEGATIVE_FIXTURES,
        POSITIVE_FIXTURES,
    )

    native = NativePharmacy()
    outcomes = []
    for case in POSITIVE_FIXTURES + NEGATIVE_FIXTURES:
        try:
            classes, subject_digest, screened = screen_pharmacy_control(
                case, quarantine=quarantine, native=native
            )
        except NativePharmacyUnavailable as exc:
            raise DemoRefusal("NATIVE_PHARMACY_UNAVAILABLE", f"{exc.code}: {exc.detail}") from exc
        if case in POSITIVE_FIXTURES:
            need(case["target_class"].value in classes, case["id"])
        else:
            need(not classes, case["id"])
        outcomes.append(
            {
                "case_id": case["id"],
                "clean": not classes,
                "subject_digest": subject_digest,
                "immune": screened,
            }
        )
    farm = []
    if fixture.get("farm_probes"):
        from eis.infrastructure.mssn_domains import DOMAINS

        for domain in DOMAINS.values():
            for probe in domain.probes:
                for expected, text in (
                    (True, probe.scripted_hallucination),
                    (False, probe.scripted_grounded),
                ):
                    raw = proposals.propose(probe.prompt, text)
                    screened = screen_farm_probe(probe, raw, quarantine=quarantine)
                    need(bool(screened["matches"]) == expected, probe.probe_id)
                    farm.append({"expected_trigger": expected, **screened})
    screens = []
    for index, reply in enumerate(fixture.get("immune_replies", fixture["replies"])):
        raw = proposals.propose(
            "Return candidate data for a bounded MSS-N host check; do not certify it.", reply
        )
        screens.append({"case_id": f"proposal-{index}", **screen_reply(raw, quarantine=quarantine)})
    return {
        "status": "CHECKED",
        "scope": (
            "24 pharmacology controls and OEEIS two-signal/thymus/idle-counter/quarantine "
            "fixture probes; Signal 2 from host payload checks only"
        ),
        "cases": outcomes,
        "screens": screens,
        "farm": farm,
    }
