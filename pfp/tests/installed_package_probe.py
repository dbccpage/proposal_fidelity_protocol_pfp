"""Run with python -I, the installed target, and an explicit native binary path.

This is an offline distribution probe, not a source-checkout pytest substitute.
Third-party dependencies come from the invoking environment. Every imported
Omega production module must come from the installed target.
"""

import base64
import contextlib
import io
import json
import os
import sys
from hashlib import sha256
from importlib import import_module, resources
from pathlib import Path
from tempfile import TemporaryDirectory


def public_pfp_api_probe():
    """Resolve public names and exercise the runner's existing refusal contract."""
    from omega_engine_pfp import DemoCatalog, DemoRunReceipt, DemoSpec
    from omega_engine_pfp.infrastructure import UnifiedPfpDemoRunner
    from omega_engine_pfp.infrastructure.pilot_runners.pilot_dispatch import (
        UnifiedPfpDemoRunner as CanonicalRunner,
    )

    assert UnifiedPfpDemoRunner is CanonicalRunner
    task = DemoSpec(id="unregistered-installed-probe", title="Unknown demo control", seed="public input")
    receipts = UnifiedPfpDemoRunner().run_all(DemoCatalog(demos=[task]))
    assert len(receipts) == 1 and isinstance(receipts[0], DemoRunReceipt)
    refusal = receipts[0]
    assert refusal.demo_id == task.id and refusal.runner_id == "unregistered"
    assert not refusal.all_passed and refusal.terminal_status == "Refused"
    assert refusal.authority_effect == "None"
    assert len(refusal.checks) == 1 and not refusal.checks[0].passed
    assert refusal.checks[0].name == "runner_registered"
    return ["public PFP runner identity and unknown-demo refusal; no model or original-protocol evidence"]


def current_profile_probe(installed):
    """Render current packaged roles and read historical identities without Git."""
    assert not any((parent / ".git").exists() for parent in (installed, *installed.parents)), (
        "Mutation controls require a disposable installed copy outside a checkout")
    import yaml

    from omega_engine_pfp.infrastructure import numbered_prompts as prompts
    from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import read_frozen_prompt_source
    from omega_engine_woland.tests.pilots.relational_spacetime import tasks, trial_prompts

    assert prompts.VERSION == "1.0.4"
    assert Path(prompts.__file__).resolve().is_relative_to(installed / "omega_engine_pfp")
    registry = prompts._registry()
    for relative, expected in registry["file_sha256"].items():
        assert sha256((installed / relative).read_bytes()).hexdigest() == expected
    rendered = 0
    for pilot in tasks.BY_ID:
        for stage in (1, 2, 3):
            prompt = prompts.build_prompt(pilot, stage)
            wire = yaml.safe_load(prompt["user_prompt"])
            assert prompt["recipe"] == "PFP-R0001-v1.0.4"
            assert prompt["provider_dispatches"] == 0 and prompt["analytical_status"] == "UNVERIFIED"
            assert prompt["construction_path"] == "omega_engine_pfp/infrastructure/numbered_prompts.py"
            assert prompt["construction_sha256"] == sha256(Path(prompts.__file__).read_bytes()).hexdigest()
            assert wire["original_seed"] == tasks.BY_ID[pilot]["text"]
            if pilot == "pilot_0000201":
                assert sha256(wire["source_context"]["section_5"].encode()).hexdigest() == trial_prompts.SECTION_5_SHA256
            rendered += 1
    assert rendered == 15
    prefix = "omega_engine_education/pfp/infrastructure/yaml/prompts/versioned/"
    frozen = ("PFP-prompt-role-registry-v1.0.0.yaml", "PFP-R0001-v1.0.0.yaml",
        "PFP-T0001-v1.0.0.yaml", "PFP-T0002-v1.0.0.yaml", "PFP-T0003-v1.0.0.yaml", "README.md")
    # Main retired these files to pinned Git history. A wheel without those
    # Git objects must refuse, never substitute current prompt-role bytes.
    available = []
    unavailable = []
    for name in frozen:
        try:
            assert read_frozen_prompt_source(prefix + name)
            available.append(name)
        except ValueError as exc:
            assert str(exc) == "FROZEN_SOURCE_UNAVAILABLE:" + prefix + name
            unavailable.append(name)
    assert len(available) + len(unavailable) == len(frozen)
    assert unavailable == list(frozen), "Update custody expectations if historical data is deliberately repackaged"
    try:
        read_frozen_prompt_source(prefix + "PFP-T0001-v1.0.4.yaml")
    except ValueError as exc:
        assert str(exc) == "UNKNOWN_FROZEN_PROMPT_SOURCE"
    else:
        raise AssertionError("current prompt was accepted under a historical identity")
    from omega_engine_woland.tests.pilots.relational_spacetime import (
        baseline,
        compact_trials,
        parameter_trials,
        typed_signals,
    )

    for operation in (
        baseline.sources, baseline.prepare, baseline.replay,
        lambda: parameter_trials.run("scratchpad", ["pilot_0000199"]),
        lambda: parameter_trials.replay("scratchpad", ["pilot_0000199"]),
        compact_trials.prepare,
        lambda: compact_trials.run(["pilot_0000199"]),
        lambda: compact_trials.replay(["pilot_0000199"]),
        lambda: typed_signals.run("pilot_0000199"), typed_signals.replay,
    ):
        try:
            operation()
        except ValueError as exc:
            assert "REPOSITORY_CONTEXT_REQUIRED" in str(exc)
        else:
            raise AssertionError("historical campaign did not refuse without Git context")
    return ["15 installed current v1.0.4 roles, source pins and canonical construction",
        "six Git-retired original identities refuse outside Git; no current-byte fallback",
        "ten installed historical campaign entrypoints refuse without Git context"]


def _probe_invoke(command, arguments, expected=0):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = command(arguments)
    assert status == expected, (status, output.getvalue())
    return json.loads(output.getvalue())

def _probe_envelope(prepared, answer):
    properties = prepared["response_schema"]["properties"]
    return {
        **{key: properties[key]["const"] for key in ("task_id", "attempt_id", "input_sha256")},
        "answer": answer,
    }

def public_task_cli_probe():
    """Exercise host-free task parsers and exact raw binding/refusal controls."""
    from omega_engine_pfp.entrypoints.cli.pfp import main as pfp_main

    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        folder = Path(temporary)
        specification, reply = folder / "task.json", folder / "reply.json"
        specification.write_text(
            json.dumps(
                dict(
                    task_id="synthetic-installed-task-cli",
                    objective="Synthetic integer-product plumbing; a separate judge must decide correctness.",
                    input={"expression": "17 * -9"},
                    answer_schema={"type": "integer"},
                )
            ),
            encoding="utf-8",
        )
        prepared = _probe_invoke(pfp_main, ["prepare-task", str(specification), "--attempt", "one"])
        for answer in (-153, -152):
            raw = json.dumps(_probe_envelope(prepared, answer)).encode("utf-8")
            reply.write_bytes(raw)
            checked = _probe_invoke(
                pfp_main, ["check-task", str(specification), str(reply), "--attempt", "one"]
            )
            assert checked["schema_valid"] and checked["status"] == "PROVIDER_COMPLETED"
            assert checked["evidence_grade"] == "UNVERIFIED" and checked["provider_calls"] == 0
            assert base64.b64decode(checked["raw_reply_base64"], validate=True) == raw
        wrong = {**_probe_envelope(prepared, -153), "task_id": "wrong-task"}
        for raw in (b"malformed synthetic reply", json.dumps(wrong).encode("utf-8")):
            reply.write_bytes(raw)
            checked = _probe_invoke(
                pfp_main, ["check-task", str(specification), str(reply), "--attempt", "one"], 2
            )
            assert not checked["schema_valid"] and checked["failure_class"] != "NONE"
            assert checked["provider_calls"] == 0
            assert base64.b64decode(checked["raw_reply_base64"], validate=True) == raw

    return [
        "public PFP task CLI: synthetic binding controls, semantic acceptance not claimed",
        "public command malformed/wrong-binding refusals retain actual raw bytes",
    ]


def current_ide_cli_probe(native=None):
    """Exercise the full partial IDE handoff only with an explicit native host."""
    if native is None or not isinstance(native, (str, Path)):
        raise ValueError("INSTALLED_NATIVE_HOST_REQUIRED")
    native = Path(native).absolute()
    if not native.is_file() or native.is_symlink():
        raise ValueError("INSTALLED_NATIVE_HOST_REQUIRED")
    from omega_engine_woland.entrypoints.teamwork_cli import main as teamwork_main

    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        folder = Path(temporary)
        reply = folder / "reply.json"
        # Current public IDE handoff: Hella and applicable host gates precede
        # a prepared Retinue turn. This is plumbing, not an actual model run.
        state = folder / "ide.json"
        scope = folder / "intake-scope.json"
        scope.write_text(json.dumps({
            "native_intake": ["PFP-IG-05-FALSE-URGENCY-DESENSITIZATION"],
            **{name: ["PFP-IG-05-FALSE-URGENCY-DESENSITIZATION"] for name in ("native_pre", "native_post", "native_learn_pre",
                "native_learn_post", "native_finish")},
        }), encoding="utf-8")
        def start(path, identity):
            report = _probe_invoke(teamwork_main, ["start", "--objective", "Synthetic installed role plumbing only.",
                "--state", str(path), "--run-id", identity,
                "--native-gate-scope", str(scope), "--native-host", str(native),
                "--checker-id", "installed.fixture.v1",
                "--check-command", sys.executable, "-c", "raise SystemExit(0)"])
            while report["next_action"]["communication"] != "pfp":
                action = report["next_action"]
                operation = "check" if action["communication"] == "deterministic" else action["kind"].replace("_", "-")
                report = _probe_invoke(teamwork_main, [operation, "--state", str(path)])
            return report
        report = start(state, "synthetic-installed-ide")
        assert report["executor"] == "ide"
        assert report["pfp_turn"]["transport"] == "current_ide_session"
        assert report["pfp_turn"]["cost_usd"] is None
        raw = json.dumps(_probe_envelope(report["pfp_turn"],
            {"summary": "Synthetic role plumbing only", "findings": []})).encode()
        reply.write_bytes(raw)
        report = _probe_invoke(teamwork_main, ["submit", "--state", str(state),
            "--raw-reply", str(reply), "--worker", "synthetic installed current-IDE probe"])
        saved = json.loads(state.read_bytes())
        metadata = saved["observations"][-1]["metadata"]
        assert metadata["pfp"]["evidence_grade"] == "UNVERIFIED"
        assert metadata["cost_usd"] is None
        assert base64.b64decode(metadata["pfp"]["raw_reply_base64"], validate=True) == raw
        assert report["next_action"] is not None  # A partial handoff is not completion.
        for index in (0, 1):
            state = folder / f"ide-negative-{index}.json"
            report = start(state, f"synthetic-negative-{index}")
            wrong = {**_probe_envelope(report["pfp_turn"],
                {"summary": "Synthetic refusal control", "findings": []}), "task_id": "wrong-task"}
            reply.write_bytes(b"malformed synthetic reply" if index == 0 else json.dumps(wrong).encode())
            report = _probe_invoke(teamwork_main, ["submit", "--state", str(state),
                "--raw-reply", str(reply), "--worker", "synthetic negative control"], 2)
            assert report["work_status"] == "blocked"

    return ["current-IDE Woland CLI: applicable intake gate, prepared/raw handoff, explicitly partial"]


def public_cli_probe(native=None):
    """Retain the full composite and legacy ambient binding; main passes native."""
    task_controls = public_task_cli_probe()
    ide_controls = current_ide_cli_probe(native if native is not None else os.environ.get("OMEGA_SYMBOL_GAME_HOST"))
    return [task_controls[0], ide_controls[0], task_controls[1]]


def installed_challenge_probe(installed):
    """Require installed tasks/cases/checkers to prepare real source-bound briefs."""
    from omega_engine_pfp.infrastructure.challenge_live import choose_case
    from omega_engine_woland.infrastructure import challenge_play
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import (
        ROOT,
        canonical,
        digest,
        relocated,
    )

    installed = installed.resolve()
    assert ROOT.resolve() == installed
    challenges = ("C001", "C005", "C011", "C041", "C051", "C052", "C053", "C054", "C055", "C059")
    for challenge in challenges:
        row = choose_case(challenge, "development", 0)
        source = (ROOT / relocated(row["source"])).resolve()
        assert source.is_relative_to(installed), challenge
        assert digest(source.read_bytes()) == row["sha256"], challenge
        state = challenge_play.start(row, executor="ide", historical_v3=True)
        sources = state["sources"]
        assert sources, challenge
        for relative, expected in sources.items():
            path = (installed / relative).resolve()
            assert path.is_relative_to(installed), relative
            assert digest(path.read_bytes()) == expected, (challenge, relative)
        if challenge in {"C051", "C052", "C053", "C054", "C055", "C059"}:
            assert any("/judge_packet/" in name and name.endswith(".py") for name in sources), (
                challenge,
                "installed checker sources are missing from the binding",
            )
        report = challenge_play.report(state)
        assert report["work_status"] == "pending_host" and report["executor"] == "ide"
        assert report["next_action"]["role_id"] == "azazello" and report["task_check"] is None
        assert report["provider_replies"] == report["ide_submissions"] == 0
        prompt = report["pfp_turn"]
        public = json.loads(prompt["user"])
        assert state["run"]["acceptance_check"]["checker_id"] == "demo004:" + digest(canonical(sources))
        properties = prompt["response_schema"]["properties"]
        assert all(
            public[key] == properties[key]["const"]
            for key in ("task_id", "attempt_id", "input_sha256")
        )
    return ["ten installed historical-v3 challenge starts: full-Retinue intake/source bindings, zero model calls"]


def installed_host_fixture_probe(installed):
    """One original C054 host fixture and falsifier; no model experiment."""
    from omega_engine_pfp.infrastructure.challenge_execution import isolated
    from omega_engine_pfp.infrastructure.challenge_live import choose_case
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import ROOT

    assert ROOT.resolve() == installed.resolve()
    row = choose_case("C054", "development", 0)
    verified = isolated(dict(kind="NO_LLM", row=row), timeout=20)
    assert verified["status"] == "FIXTURE_VERIFIED", verified
    assert len(verified["judges"]) == 2 and all(judge["accepted"] for judge in verified["judges"])
    rejected = isolated(dict(kind="CHECK_ANSWER", row=row, answer={}), timeout=20)
    assert rejected["status"] == "PROVIDER_COMPLETED" and rejected["failure_class"] != "NONE", rejected
    assert len(rejected["judges"]) == 2 and all(not judge["accepted"] for judge in rejected["judges"])
    return ["installed C054 host fixture: isolated original dual-judge verification and empty-witness refusal; no model evidence"]


def installed_matrix_cli_probe(installed):
    """Current matrix commands must reach their bounded parser without a checkout."""
    import runpy

    previous = sys.argv
    try:
        for number in (*range(43, 51), 56, 57, 58, 60):
            family = "e_formal_math" if number < 51 else "f_program_synthesis"
            base = installed / "omega_engine_pfp/tests/demo_004" / family
            paths = list(base.glob(f"c{number:03d}_*/run_c{number:03d}_matrix.py"))
            assert len(paths) == 1, (number, paths)
            for direct in (False, True):
                sys.argv = [str(paths[0]), "--help"]
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    try:
                        if direct:
                            runpy.run_path(str(paths[0]), run_name="__main__")
                        else:
                            module = paths[0].relative_to(installed).with_suffix("").as_posix().replace("/", ".")
                            runpy.run_module(module, run_name="__main__")
                    except SystemExit as exc:
                        assert exc.code == 0, (number, exc)
                    else:
                        raise AssertionError(f"C{number:03d} did not reach its help parser")
                assert "--max-provider-calls" in output.getvalue(), number
                assert "--max-estimated-cost-microusd" in output.getvalue(), number
    finally:
        sys.argv = previous
    return ["twelve installed matrix commands: module/direct bounded CLI help without checkout or dispatch"]


def civilization_custody_probe(native):
    """Exercise the canonical installed adapters and actual authenticated public route."""
    import hmac
    from dataclasses import replace

    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
    from omega_engine_prompt_civilization.controllers.prompt_civ_controller import (
        PromptCivilizationController,
    )
    from omega_engine_prompt_civilization.domain.models import (
        CustodyTier,
        PromptGenomeV1,
        UnauthorizedAdmissionError,
    )
    from omega_engine_prompt_civilization.use_cases.custody import (
        PromptCustodyLedgerV1,
        PromptReviewReceiptV1,
    )
    from omega_engine_prompt_civilization.use_cases.fitness import PromptFitnessCalculatorV1
    from omega_engine_woland.domain.evidence import CheckerVerdict
    from omega_engine_woland.domain.models import SymbolGameRequestV1
    from omega_engine_woland.infrastructure.symbol_game_checker import SymbolGameCandidateChecker

    for leaf in ("custody", "fitness", "operator_custody", "record"):
        alias = import_module("omega_engine_operating_system.adapters.prompt_civ." + leaf)
        owner = import_module(
            "omega_engine_prompt_civilization.domain.models" if leaf == "record"
            else "omega_engine_prompt_civilization.use_cases." + leaf
        )
        for name in alias.__all__:
            assert getattr(alias, name) is getattr(owner, name), (leaf, name)

    state = {"installed": dict(prompt_id="installed", content="Exact arithmetic", tier="REVIEWED",
        pagerank_score="0", operator_signature=None, authority_effect="None")}
    outcome = RustSymbolGameHost(binary=native).invoke_runtime("prompt_civilization", dict(
        operation="authorize_admission", prompt_id="installed", state=state,
        operator_signature="sig:ed25519:" + "ab" * 64)).unwrap()
    assert outcome["success"] and outcome["result"]["refusal"]["code"] == "UNAUTHORIZED_ADMISSION"
    assert outcome["result"]["refusal"]["state"] == state

    class TestReviewVerifier:
        key = b"installed-probe-only-operator-key"

        def sign(self, receipt):
            return replace(receipt, external_receipt=hmac.new(self.key, receipt.signed_bytes(), sha256).hexdigest())

        def verify(self, receipt):
            return hmac.compare_digest(receipt.external_receipt, self.sign(receipt).external_receipt)

    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        content = "Compute exact rational eigenvalues."
        genome = PromptGenomeV1([{"sha256": "sha256:" + sha256(content.encode()).hexdigest()}], {"domain": "math"})
        verifier = TestReviewVerifier()
        ledger = PromptCustodyLedgerV1(Path(temporary) / "custody.sqlite", verifier)
        try:
            ledger.submit_candidate(genome, "producer")
            reviewed = verifier.sign(PromptReviewReceiptV1("review", genome.prompt_id, "operator", CustodyTier.REVIEWED, ("math",), ""))
            ledger.apply(genome, reviewed)
            admitted = verifier.sign(replace(reviewed, decision_id="admit", outcome=CustodyTier.ADMITTED))
            controller = PromptCivilizationController(custody_ledger=ledger)
            controller.ingest_prompt(genome.prompt_id, content)
            try:
                controller.authorize_admission(genome.prompt_id, operator_signature="sig:ed25519:" + "ab" * 64)
            except UnauthorizedAdmissionError:
                pass
            else:
                raise AssertionError("installed public controller admitted a shape token")
            try:
                controller.authorize_admission(genome.prompt_id, review_receipt=replace(admitted, external_receipt="forged"), scope="math")
            except PermissionError:
                pass
            else:
                raise AssertionError("installed public controller admitted a forged review")
            assert controller.authorize_admission(genome.prompt_id, review_receipt=admitted, scope="math")["is_admitted"]
            assert controller.state.prompts[genome.prompt_id].authority_effect == "None"
        finally:
            ledger.close()

    case = {"challenge": "c011", "nodes": ["a", "b"], "edges": [["a", "b"]], "claims": {"a->b": "1/10"}}
    answer = {"status": "SOLVED", "phi1": "0", "potential": {"a": "0", "b": "1/10"}, "repair": {}, "dual": {}}
    fitness = PromptFitnessCalculatorV1(candidate_checker=SymbolGameCandidateChecker(SymbolGameRequestV1(json.dumps(case))))
    for payload, verdict, credit in ((answer, CheckerVerdict.ACCEPTED, 1), ({**answer, "phi1": "1"}, CheckerVerdict.REJECTED, 0)):
        check = fitness.check_candidate(run_key="installed", objective="C011 exact check", candidate_id="candidate",
            candidate_bytes=json.dumps(payload).encode(), carrier_context=None).unwrap()
        assert check.verdict is verdict and fitness.checked_success_credit(check) == credit
    assert fitness.extract_obligation_success_credit("claim", dict(verifier_status="VERIFIED_EXACT", sealed_receipt_digest="sha256:" + "ab" * 32)) == 0
    return ["canonical installed OEOS/OEPCIV reexport identities", "native/public shape-token refusal and actual authenticated controller admission",
        "installed independent C011 checker credit, changed certificate rejection and zero metadata credit"]


def receipt_delivery_probe():
    """Use the installed public composition root, real SQLite and a signed retained tip."""
    import sqlite3

    from omega_engine_operads.infrastructure.bootstrap import OeopContainer
    from omega_engine_operads.infrastructure.storage.receipt_ledger import (
        LedgerError,
    )

    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        workspace = Path(temporary)
        database, tip = workspace / "events.db", workspace / "retained/tip.json"
        key = b"installed-probe-only-key-32-bytes"
        container = OeopContainer(workspace_root=workspace, db_path=str(database))
        with contextlib.closing(sqlite3.connect(database)) as connection, connection:
            for identifier in ("one", "two"):
                connection.execute("INSERT INTO events_v3 VALUES (?,?,?,?,?,?,?)", (identifier, "stream", "event", "c", "c", "now", "{}"))
                connection.execute("INSERT INTO outbox_v3(outbox_id,event_id,destination,created_at) VALUES (?,?,?,?)", (identifier, identifier, "events.oewas.v3", "now"))
        try:
            dispatcher = container.configure_receipt_delivery(tip_path=tip, key=key, ledger_id="installed", worker_id="worker-one")
            assert dispatcher.dispatch_pending().unwrap().delivered_count == 2
            assert len(container.receipt_subscriber.ledger) == 2
            retained = tip.read_bytes()
        finally:
            container.close()
        reopened = OeopContainer(workspace_root=workspace, db_path=str(database))
        try:
            dispatcher = reopened.configure_receipt_delivery(tip_path=tip, key=key, ledger_id="installed", worker_id="worker-two")
            assert dispatcher.dispatch_pending().unwrap().delivered_count == 0
            with contextlib.closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("INSERT INTO outbox_v3(outbox_id,event_id,destination,created_at) VALUES ('retry','one','events.oewas.v3','now')")
            assert dispatcher.dispatch_pending().unwrap().delivered_count == 1
            assert len(reopened.receipt_subscriber.ledger) == 2 and tip.read_bytes() == retained
        finally:
            reopened.close()
        forged = json.loads(retained)
        forged["body"]["tip"] = "0" * 64
        tip.write_text(json.dumps(forged), encoding="utf8")
        tampered = tip.read_bytes()
        reopened = OeopContainer(workspace_root=workspace, db_path=str(database))
        try:
            try:
                reopened.configure_receipt_delivery(tip_path=tip, key=key, ledger_id="installed")
            except LedgerError as error:
                assert error.code == "TIP_AUTHENTICATION_FAILED"
            else:
                raise AssertionError("installed receipt delivery repinned a forged tip")
            assert tip.read_bytes() == tampered
        finally:
            reopened.close()
    return ["installed public OEWAS leased delivery, reopen and exact-event deduplication",
        "installed signed-tip tamper refusal without repinning"]


def main():
    installed = Path(sys.argv[1]).resolve()
    native = Path(sys.argv[2]).resolve()
    assert not (Path.cwd() / ".git").exists(), "Run outside the checkout"
    # An editable .pth must not contribute production namespace portions.
    sys.path[:] = [entry for entry in sys.path if not (Path(entry) / "pyproject.toml").is_file()]
    sys.path.insert(0, str(installed))
    os.environ["OMEGA_SYMBOL_GAME_HOST"] = str(native)
    probes = []
    for name in (
        "omega_engine_pfp.entrypoints.cli.pfp",
        "omega_engine_pfp.entrypoints.cli.symbol_game",
        "omega_engine_pfp.infrastructure.task_turn",
        "omega_engine_pfp.infrastructure.estimated_gateway",
        "omega_engine_pfp.infrastructure.formal_matrix",
        "omega_engine_pfp.infrastructure.synthesis_matrix",
        "omega_engine_woland.entrypoints.teamwork_cli",
        "omega_engine_woland.infrastructure.teamwork_openrouter",
        "omega_engine_operads.domain.prompt_hierarchy.evaluator",
        "omega_engine_pfp.infrastructure.challenge_execution",
        "omega_engine_pfp.infrastructure.challenge_live",
        "omega_engine_woland.infrastructure.challenge_play",
        "omega_engine_woland.infrastructure.mechanism_play",
        "omega_engine_pfp.infrastructure.numbered_prompts",
    ):
        import_module(name)
        probes.append(name)

    for name in ("omega_engine_woland", "omega_engine_woland.controllers"):
        surface = import_module(name)
        for exported in surface.__all__:
            module_name, attribute = surface._EXPORTS[exported]
            implementation = getattr(import_module(module_name, name), attribute)
            assert getattr(surface, exported) is implementation
        probes.append(f"{name}: {len(surface.__all__)} public exports")

    from omega_engine_pfp.entrypoints.cli.pfp import main as pfp_main
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            pfp_main(["--help"])
        except SystemExit as exc:
            assert exc.code == 0
    probes.append("pfp CLI help")

    root = resources.files("omega_engine_pfp")
    import yaml
    assert isinstance(yaml.safe_load(root.joinpath(
        "infrastructure/yaml/prompts/templates/template_role_registry.yaml").read_bytes()), dict)
    # The retired generic prompt_template.yaml is absent on main. The current
    # versioned role registry is the executable resource used below.
    probes.append("packaged current prompt-role registry")
    probes.extend(public_pfp_api_probe())
    probes.extend(current_profile_probe(installed))
    probes.extend(public_cli_probe(native))
    probes.extend(installed_challenge_probe(installed))
    probes.extend(installed_host_fixture_probe(installed))
    probes.extend(installed_matrix_cli_probe(installed))
    from importlib.util import find_spec
    for old in ("omega_engine_education.pfp", "omega_engine_education.pilots",
        "omega_engine_education.pilots.relational_spacetime.compact_prompts",
        "omega_engine_education.pilots.challenge_suite.execution",
        "omega_engine_education.pilots.challenge_suite.live",
        "omega_engine_education.pilots.challenge_suite.woland",
        "omega_engine_education.pilots.challenge_suite.mechanism"):
        try:
            spec = find_spec(old)
        except ModuleNotFoundError:
            spec = None
        assert spec is None, old
    assert not (installed / "omega_engine_education/pilots").exists()
    assert not (installed / "omega_engine_education/pfp").exists()
    assert not (installed / "omega_engine_woland/tests/pilots/evidence").exists()
    assert not (installed / "omega_engine_woland/tests/pilots/results").exists()
    probes.append("retired active runtime paths absent; no forwarding modules")

    from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
    turn = prepare_task_turn(system="Return the integer product.", user="17 * -9",
        task_id="installed-product", attempt_id="one", answer_schema={"type": "integer"})
    reply = {key: value for key, value in turn.binding.items() if key != "checker_id"}
    raw = json.dumps({**reply, "answer": -153}).encode()
    checked = turn.check(raw, judges=[("integer-product", lambda case, answer: (answer == 17 * -9, "Recomputed"))])
    assert checked["status"] == "HOST_ACCEPTED"
    assert turn.replay(checked)["schema_valid"]
    assert not turn.check(json.dumps({**reply, "input_sha256": "wrong", "answer": -153}).encode())["schema_valid"]
    probes.extend(("finite typed answer", "offline replay", "changed binding refusal"))

    from omega_engine_pfp.use_cases.pfp_mode_checks import execute_mode_check
    guard = dict(prompt_uri="prompt://pfp/installed/task/stage1/candidate",
        anti_op="pfp.refuse_unlicensed_multiplication", payload="add marks",
        harmful_control="multiply marks", benign_control="add marks")
    assert execute_mode_check(4, guard)["gate"]["status"] == "PASS"
    try:
        execute_mode_check(4, {**guard, "payload": "multiply marks"})
    except ValueError as exc:
        assert "KNOWN_PATHOLOGY" in str(exc)
    else:
        raise AssertionError("OEWAS negative control passed")
    probes.extend(("PFP to OEWAS procedural gate", "OEWAS harmful control"))

    from omega_engine_woland.domain.providers.types import Provider
    from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway
    from omega_engine_woland.infrastructure.teamwork_openrouter import OpenRouterTeamworkExecutor
    calls = []
    def wire(provider, model, request):
        calls.append(request)
        public = json.loads(request.user)
        answer = {"summary": "Synthetic review", "findings": []} if public["input"]["context"]["kind"] == "review" else "proposed text"
        completion = {key: public[key] for key in ("task_id", "attempt_id", "input_sha256")}
        return json.dumps({"id": "synthetic-" + str(len(calls)), "model": model,
            "choices": [{"message": {"content": json.dumps({**completion, "answer": answer})}}]}).encode()
    wire.provenance = "synthetic-installed-probe"
    model = "fixture/installed"
    gateway = unbudgeted_gateway(provider=Provider.OPENROUTER, model=model,
        transport=wire, max_output_tokens=256)
    # A direct raw gateway is deliberately insufficient for Woland dispatch.
    # Use a real prepared action and assert refusal before synthetic transport.
    from omega_engine_woland.infrastructure.teamwork_intelligence_host import (
        bind_acceptance,
        bind_episode_admission,
    )
    from omega_engine_woland.infrastructure.teamwork_retinue import (
        create_teamwork_run,
        run_hella_check,
    )
    from omega_engine_woland.use_cases.teamwork import next_action, observe
    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        run = create_teamwork_run("Installed budget refusal control", historical_v3=True,
            acceptance_check=bind_acceptance("installed.fixture.v1", (sys.executable, "-c", "raise SystemExit(0)")))
        run = run.model_copy(update={"episode_binding": bind_episode_admission(run, Path(temporary)/"episodes.sqlite3")})
        run = observe(run, run_hella_check(next_action(run)))
        try:
            OpenRouterTeamworkExecutor(gateway, model)(next_action(run))
        except ValueError as exc:
            assert "WOLAND_RUN_BUDGET_REQUIRED" in str(exc)
        else:
            raise AssertionError("unaccounted installed Woland dispatch was accepted")
        assert not calls
    probes.append("installed Woland rejects unaccounted dispatch before transport")

    # Native arithmetic is supplied explicitly, never inferred from wheel imports.
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
    from omega_engine_pfp.infrastructure.estimated_gateway import DurableRunGateway
    from omega_engine_woland.domain.providers.allowlist import ModelAllowlist
    from omega_engine_woland.domain.providers.budget import (
        BudgetController,
        GatewayPolicy,
        PriceTable,
    )
    from omega_engine_woland.domain.providers.ports import configure_budget_runtime
    from omega_engine_woland.domain.providers.types import CandidateRequest
    from omega_engine_woland.infrastructure.providers.gateway import OearsLlmGateway
    from omega_engine_woland.infrastructure.providers.rust_budget import RustBudgetRuntime
    native = Path(sys.argv[2]).resolve()
    configure_budget_runtime(RustBudgetRuntime(RustSymbolGameHost(binary=native)))
    billed_calls = []

    class BoundedFixture:
        provenance = "synthetic-installed-budget"

        def maximum_liability(self, *args):
            return 10_000

        def dispatch(self, admitted):
            billed_calls.append(admitted)
            return json.dumps(dict(id="fixture-" + admitted.attempt_id, model=admitted.model,
                choices=[dict(message=dict(content="Synthetic accounting control"))],
                usage=dict(prompt_tokens=8, completion_tokens=4, cost="0.001"))).encode()

    with TemporaryDirectory(dir=Path.cwd()) as temporary:
        def reopen():
            gateway = OearsLlmGateway(ModelAllowlist.builtin(),
                GatewayPolicy(PriceTable.builtin(), BudgetController(50_000), 20,
                    pricing_clock=lambda: "2026-10-12T12:00:00.000000Z"),
                BoundedFixture(), Provider.OPENROUTER, "openai/gpt-4o-mini")
            return DurableRunGateway(gateway, accounting_path=Path(temporary) / "run.sqlite3",
                run_id="installed-budget", objective_sha256=sha256(b"shared objective").hexdigest(),
                max_calls=8)
        budget = reopen()
        request = CandidateRequest("System", "Accounting control")
        for action in ("worker:0", "review:0", "repair:0", "review:1", "learn:0"):
            result = budget.for_action(action).complete_result(request)
            assert result.is_ok
        assert budget.budget.spent_microusd == 50_000
        restored = reopen()
        assert restored.for_action("worker:0").complete_result(request).error.code == "PFP_ACTION_ALREADY_CLAIMED"
        assert restored.for_action("extra:0").complete_result(request).error.code == "BUDGET_EXCEEDED"
        assert restored.budget.spent_microusd == 50_000 and len(billed_calls) == 5
        assert restored.raw_reply("worker:0")
        assert DurableRunGateway.read_binding(restored.path) == restored.binding
        assert DurableRunGateway.read_action(restored.path, "worker:0") == restored.action("worker:0")
        assert DurableRunGateway.read_raw_reply(restored.path, "worker:0") == restored.raw_reply("worker:0")
        settlement = restored.settle_generation("worker:0", dict(data=dict(
            id=restored.action("worker:0")["generation_id"], total_cost="0.001")))
        assert settlement.status == "RECONCILED" and restored.budget.spent_microusd == 41_000
    probes.append("installed durable run cap, role holds, restart, duplicate refusal and trusted settlement")

    probes.extend(civilization_custody_probe(native))
    probes.extend(receipt_delivery_probe())

    origins = {}
    namespace_paths = {}
    for name, module in tuple(sys.modules.items()):
        assert name != "omega_engine_education" and not name.startswith(
            "omega_engine_education."
        ), name
        if name == "omega_engine" or name.startswith(("omega_engine.", "omega_engine_")):
            if getattr(module, "__file__", None):
                origin = Path(module.__file__).resolve()
                assert origin.is_relative_to(installed), (name, str(origin))
                origins[name] = str(origin.relative_to(installed))
            if hasattr(module, "__path__"):
                paths = [Path(path).resolve() for path in module.__path__]
                assert all(path.is_relative_to(installed) for path in paths), (name, paths)
                namespace_paths[name] = [str(path.relative_to(installed)) for path in paths]
    print(json.dumps(dict(status="PASS", probes=probes, imported_production_modules=len(origins),
        installed_root=str(installed), external_provider_calls=0, fixture_calls=len(calls),
        billing_fixture_calls=len(billed_calls), native_binary_sha256=sha256(native.read_bytes()).hexdigest(),
        origins=origins, namespace_paths=namespace_paths, authority_effect="None"), indent=2))


if __name__ == "__main__":
    main()
