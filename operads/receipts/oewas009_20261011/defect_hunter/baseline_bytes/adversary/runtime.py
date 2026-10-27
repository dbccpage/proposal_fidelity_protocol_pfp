"""Composition root for the Adversary Swarm.

This is the only module that chooses concrete adapters. Use cases receive them
by injection:

* ``build_adversary_runtime`` composes the generic the city runtime (scheduler,
  sinks, seat port). Fixture mode uses deterministic canned replies whose
  critic reply follows the structured ``critique`` contract. Live mode needs an
  explicit ``turn_executor``; without one the runtime has no seat port and a
  bout refuses with ``EXECUTION_UNAVAILABLE`` before any work.
* ``build_adversary_service`` wires the service: the Rust-backed
  ``DefaultCochainScoringAdapter`` measures carriers, the injected checker (or
  the null checker, which is ``NOT_MEASURED``) judges candidates, and the
  intelligence root comes from ``try_resolve_intelligence_repo_root``.
* ``build_adversary_spine`` binds every estate port of the base swarm to its adapter,
  and ``build_adversary_swarm`` builds any ``AdversarySwarm`` specialisation
  on that spine. No other module constructs a Adversary swarm.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

from adversary.application.emission import EmitterSuiteV1
from adversary.application.ports import (
    HostPortV1,
    SeatTurnReplyV1,
    SeatTurnRequestV1,
)
from adversary.application.run_swarm import SwarmRuntimeV1
from adversary.application.scheduler import DeterministicSchedulerV1
from adversary.domain import SwarmProfileV1
from adversary.domain.topology import SwarmCompositionV1
from adversary.infrastructure.default_adapters import (
    AntigravityAgentTurnAdapter,
    DiscreteDeformationCalculusDdcSink,
    FileAntibodyAdapter,
    FileCemeteryAdapter,
    FileGenealogyAdapter,
    FixtureAgentTurnAdapter,
    SymbolGameSgtSink,
    UniversalNarrativeUnsSink,
    UniversalTraceUtsSink,
)
from operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
    try_resolve_intelligence_repo_root,
)
from operations.domain.rop.result import Err
from symbol_game.ffi import RustSymbolGameHost
from symbol_game.infrastructure.seat_transport.transport import (
    is_symbol_game_transport,
)

from .domain.circuit import (
    ADVERSARY_SWARM_COMPOSITION_V1,
    validate_adversary_swarm_composition,
)
from .domain.estate_ports import AntiSkillGatePort
from .domain.models import SymbolGameRequestV1
from .domain.ports import CandidateCheckerPort, CochainScoringPort, InstructionIngressPort
from .domain.residual_algebra.dialogue_ports import DialogueProvider
from .domain.residual_algebra.dialogue_synthesizer import DialogueSynthesizer
from .domain.specialization import (
    PortName,
    SpecializationError,
    SwarmSpecializationV1,
    SwarmTypeV1,
)
from .infrastructure.cochain_adapter import DefaultCochainScoringAdapter
from .infrastructure.estates.coda_lggr import CodaPortAdapter, LggrPortAdapter
from .infrastructure.estates.envelope_store import FileEnvelopeStore
from .infrastructure.estates.adversary_sgt import AdversarySgtAdapter
from .infrastructure.estates.native_bout_port import NativeBoutPortAdapter
from .infrastructure.estates.null_estate import NullEstateAdapter
from .infrastructure.estates.oeeis_immune import OeeisImmuneAdapter
from .infrastructure.estates.oewas_anti_skill import OewasAntiSkillAdapter
from .infrastructure.estates.probe_only import AdversaryRuntimeProbe, SeatTransportProbe
from .infrastructure.estates.prompt_civ_genealogy import PromptCivGenealogyAdapter
from .infrastructure.native_bout import NativeBoutExecutionAdapter
from .infrastructure.prime_continuation_adapter import PrimeContinuationAdapter
from .infrastructure.prime_descent_adapter import PrimeDescentAdapter
from .infrastructure.research_swarm.source_audit import SourceAuditSquads
from .infrastructure.scenes.receipt_writer import SceneReceiptWriter
from .infrastructure.scenes.repository import YamlSceneRepository
from .infrastructure.specialization_check import check_specialization
from .infrastructure.symbol_game_checker import SymbolGameCandidateChecker
from .profile.profile_loader import load_adversary_council_profile
from .use_cases.base_swarm.specializations import (
    WORKLOAD_PROFILES_V01,
    resolve_swarm_type_profile,
)
from .use_cases.base_swarm.adversary_swarm import AdversarySwarm, AdversarySpineV1
from .use_cases.bout_service import AdversarySwarmService
from .use_cases.governing_councils_bout_use_case import GoverningCouncilsBoutUseCase
from .use_cases.product_mgmt_bout_use_case import ProductMgmtBoutUseCase
from .use_cases.research_swarm.repo_wide_coda_lggr_auditor import RepoWideCodaLggrAuditor
from .use_cases.scenes.adversary_bout_use_case import AdversaryBoutUseCase
from .use_cases.software_dev_bout_use_case import SoftwareDevBoutUseCase
from .use_cases.thanatos_bout_use_case import ThanatosBoutUseCase

TurnExecutor = Callable[[SeatTurnRequestV1], "str | SeatTurnReplyV1"]

#: The fixture critic states, in the structured contract, that it searched for
#: nothing. It blocks nothing and proves nothing; a fixture bout therefore
#: selects a candidate as a proposal at most and is never authorized.
FIXTURE_CRITIQUE_REPLY = SeatTurnReplyV1(
    reply_text=(
        "```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Open\nDISPOSITION=PASS\n```\n"
        "Deterministic fixture critique: no counterexample search was run.\n"
        '```critique\n{"blocking": false, "counterexample": null}\n```'
    ),
    machine_fields={
        "AUTHORITY_EFFECT": "None",
        "RESIDUAL_COLOUR": "Open",
        "DISPOSITION": "PASS",
    },
    residual_colour="Open",
    authority_effect="None",
    raw_bytes=b"deterministic_fixture_critique",
)


def require_mediated_transport(turn_executor: object | None) -> None:
    """Refuse any model route that is not a Symbol Game seat transport.

    Adversary reaches models only through ``core.symbol_game.protocol.v2``; a raw callable,
    a provider client or a transport defined outside Symbol Game is refused before any
    runtime is built.
    """
    if turn_executor is not None and not is_symbol_game_transport(turn_executor):
        raise ValueError(
            "LLM_PROTOCOL_UNMEDIATED: seat transports must be Symbol Game transports "
            "declaring core.symbol_game.protocol.v2"
        )


def adversary_fixture_seat_port() -> FixtureAgentTurnAdapter:
    """Deterministic seat replies for CI; the critic uses the structured contract."""
    return FixtureAgentTurnAdapter(
        canned_replies={("act2_panel_debate", "seat_defect_hunter"): FIXTURE_CRITIQUE_REPLY}
    )


def build_adversary_runtime(
    *,
    composition: SwarmCompositionV1 = ADVERSARY_SWARM_COMPOSITION_V1,
    profile: SwarmProfileV1 | tuple[Any, ...] | None = None,
    council_assembly: tuple[Any, ...] | None = None,
    output_dir: str | Path | None = None,
    request_external_admission: bool = False,
    fixture_mode: bool = False,
    max_critique_rounds: int = 4,
    turn_executor: TurnExecutor | None = None,
    provider: str | None = None,
    model: str | None = None,
    host: HostPortV1 | None = None,
) -> SwarmRuntimeV1:
    """Compose the SwarmRuntimeV1 with all canonical stores and emitters.

    When ``council_assembly`` is supplied as a 5-tuple
    ``(definition, scene_graph, profile, plan, stop)`` the YAML loader is
    skipped entirely, avoiding redundant disk I/O and keeping the injected
    profile consistent with its companion definition/graph/plan/stop.

    ``output_dir`` defaults to ``<intelligence root>/_ic/darpa/adversary``; when the
    root cannot be resolved, ``IntelligenceRootUnresolvedError`` is raised
    rather than writing into the working directory.
    """
    validate_adversary_swarm_composition(composition)
    require_mediated_transport(turn_executor)
    if not fixture_mode and provider == "openrouter" and turn_executor is None:
        raise ValueError(
            "DIRECT_RUNTIME_PROVIDER_UNADMITTED: construct live providers only "
            "through a plan-consuming Adversary service boundary"
        )
    if type(max_critique_rounds) is not int or not 1 <= max_critique_rounds <= 10:
        raise ValueError("max_critique_rounds must be an integer from 1 through 10")

    out_path = (
        Path(output_dir)
        if output_dir is not None
        else intelligence_path(resolve_intelligence_repo_root(), "_intelligence/_adversary")
    )
    if out_path.name == "_intelligence":
        custody = intelligence_path(out_path.parent, "_intelligence/_adversary")
    elif out_path.parts[-3:] == ("_ic", "darpa", "adversary"):
        custody = intelligence_path(out_path.parents[2], "_intelligence/_adversary")
    else:
        custody = out_path / "_adversary"
    if council_assembly is not None:
        definition, scene_graph, prof, plan, stop = council_assembly
    else:
        definition, scene_graph, prof, plan, stop = load_adversary_council_profile()

    if isinstance(profile, SwarmProfileV1):
        prof = profile

    scheduler = DeterministicSchedulerV1(definition, prof, scene_graph, plan, stop)

    uts_sink = UniversalTraceUtsSink()
    uns_sink = UniversalNarrativeUnsSink()
    ddc_sink = DiscreteDeformationCalculusDdcSink(custody / "ddc_actions.jsonl")
    sgt_sink = SymbolGameSgtSink(custody / "sgt_packets.jsonl")
    cemetery_sink = FileCemeteryAdapter(custody / "cemetery")
    antibody_adapter = FileAntibodyAdapter(custody / "antibodies")
    genealogy_adapter = FileGenealogyAdapter(custody / "prompt_genealogy.jsonl")

    emitter_suite = EmitterSuiteV1(
        uts=uts_sink,
        uns=uns_sink,
        sgt=sgt_sink,
        ddc=ddc_sink,
        cemetery=cemetery_sink,
        antibodies=antibody_adapter,
        genealogy=genealogy_adapter,
    )

    if fixture_mode:
        seat_port = adversary_fixture_seat_port()
    elif turn_executor is not None:
        seat_port = AntigravityAgentTurnAdapter(turn_executor)
    else:
        # No executor is configured: leave the seat port empty so the bout
        # refuses with EXECUTION_UNAVAILABLE instead of failing mid-run.
        seat_port = None

    return SwarmRuntimeV1(
        profile=prof,
        seat_port=seat_port,
        scheduler=scheduler,
        # The bout never calls a valuator; none is attached rather than one
        # that would invent residuals.
        valuator=None,
        continuation=PrimeContinuationAdapter(),
        emitters=emitter_suite,
        request_external_admission=request_external_admission,
        max_critique_rounds=max_critique_rounds,
        operational_output_dir=str(custody),
        host=host,
    )


def build_adversary_service(
    repo_root: Path | str | None = None,
    *,
    cochain_adapter: CochainScoringPort | None = None,
    candidate_checker: CandidateCheckerPort | None = None,
    symbol_game_request: SymbolGameRequestV1 | None = None,
    turn_executor: TurnExecutor | None = None,
    provider: str | None = None,
    model: str | None = None,
    learning_completion: Any = None,
    intelligence_collection: Any = None,
    learning_context: Any = None,
    learning_config: Path | None = None,
    bout_journal: Any = None,
    instruction_ingress: InstructionIngressPort | None = None,
    require_instruction_ingress: bool = False,
    anti_skill_gate: AntiSkillGatePort | None = None,
) -> AdversarySwarmService:
    """Build a bout service; non-fixture requests require typed ingress.

    Fixture requests remain the pre-cutover compatibility path. No source
    document or candidate OEWAS plan is silently treated as admission.
    """
    learning_init_error = None
    collection_init_error = None
    resolved_root = Path(repo_root).resolve() if repo_root is not None else None
    if resolved_root is None:
        resolved = try_resolve_intelligence_repo_root()
        if resolved.is_ok:
            resolved_root = resolved.unwrap()
    use_native = all(
        value is None
        for value in (
            turn_executor,
            cochain_adapter,
            candidate_checker,
            bout_journal,
        )
    )
    if not use_native and provider == "openrouter" and turn_executor is None:
        raise ValueError(
            "PYTHON_FALLBACK_PROVIDER_UNADMITTED: an explicit provider cannot "
            "be constructed outside a plan-consuming service boundary"
        )
    # Do not construct a credential-bearing provider at service-build time.
    # The Python runtime factory is invoked only after the service's instruction
    # and anti-skill pre-dispatch gates; the native path follows the same gates.
    require_mediated_transport(turn_executor)

    if candidate_checker is not None and symbol_game_request is not None:
        raise ValueError("choose one checker binding")
    if symbol_game_request is not None and not use_native:
        candidate_checker = SymbolGameCandidateChecker(symbol_game_request)

    if intelligence_collection is None and resolved_root is not None:
        from operations.infrastructure.intelligence_digestion import (
            DurableIntelligenceCollector,
        )

        try:
            intelligence_collection = DurableIntelligenceCollector(resolved_root)
        except Exception as exc:
            collection_init_error = exc

    if learning_completion is None:
        from workflows_agents_skills.domain.autopoiesis.learning import CallerContext
        from workflows_agents_skills.infrastructure.autopoiesis.learning_runtime import (
            build_learning_completion,
        )

        if resolved_root is not None:
            parent_budget = getattr(turn_executor, "budget_controller", None)
            parent_model = model or getattr(turn_executor, "model", None)
            if learning_context is None and parent_budget is not None and provider and parent_model:
                learning_context = CallerContext(
                    provider, parent_model, "adversary-parent-budget", parent_budget
                )
            try:
                learning_completion = build_learning_completion(
                    resolved_root,
                    executor=turn_executor,
                    context=learning_context,
                    config_path=learning_config,
                )
            except Exception as exc:
                learning_init_error = exc

    service = AdversarySwarmService(
        repo_root=repo_root,
        runtime_factory=partial(
            build_adversary_runtime,
            turn_executor=turn_executor,
            provider=provider,
            model=model,
        ),
        profile_loader=load_adversary_council_profile,
        cochain_adapter=cochain_adapter or DefaultCochainScoringAdapter(),
        candidate_checker=candidate_checker,
        intelligence_root=try_resolve_intelligence_repo_root,
        intelligence_path=intelligence_path,
        learning_completion=learning_completion,
        intelligence_collection=intelligence_collection,
        bout_journal=bout_journal,
        native_execution=(
            NativeBoutExecutionAdapter(
                provider=provider, model=model, symbol_game_request=symbol_game_request,
            ) if use_native else None
        ),
        instruction_ingress=instruction_ingress,
        require_instruction_ingress=require_instruction_ingress,
        anti_skill_gate=anti_skill_gate,
    )
    if learning_init_error is not None:
        service.record_learning_init_failure(learning_init_error)
    if collection_init_error is not None:
        service.record_intelligence_collection_init_failure(collection_init_error)
    if bout_journal is not None:
        from .use_cases.bout_recovery import reconcile_crashed_bouts

        reconciled = reconcile_crashed_bouts(bout_journal)
        if reconciled.is_err:
            service.record_bout_recovery_failure(reconciled.unwrap_err())
    return service


def _probe_bout_service(root: Path) -> AdversarySwarmService:
    """A minimal native bout service rooted at a probe scratch directory."""
    return AdversarySwarmService(repo_root=root, native_execution=NativeBoutExecutionAdapter())


def build_adversary_spine(
    repo_root: Path | str | None = None,
    *,
    turn_executor: TurnExecutor | None = None,
    provider: str | None = None,
    model: str | None = None,
    anti_skill_runtime: Any = None,
    disconnected_ports: frozenset[PortName] = frozenset(),
    swarm_type: SwarmTypeV1 | str | None = None,
) -> AdversarySpineV1:
    """Bind every base-swarm port to its estate adapter under one intelligence root.

    ``repo_root`` defaults to the root the operating system resolves; an unresolved root
    raises rather than writing into the working directory. ``disconnected_ports`` swaps
    the named ports for ``NullEstateAdapter``; nothing is disconnected by default.
    When ``swarm_type`` is specified, the domain profile is resolved, checked natively,
    and any ports not licensed by that profile are automatically disconnected.
    """
    root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else resolve_intelligence_repo_root()
    )
    resolved_swarm_type = (
        SwarmTypeV1.from_str(swarm_type)
        if swarm_type is not None
        else SwarmTypeV1.OPEN_TOPIC
    )
    spec = resolve_swarm_type_profile(resolved_swarm_type)
    if spec not in _NATIVELY_CHECKED:
        checked = check_specialization(spec)
        if isinstance(checked, Err):
            raise SpecializationError(checked.error.code, checked.error.message)
        _NATIVELY_CHECKED.add(spec)

    unlicensed = frozenset(PortName) - spec.licensed_ports
    effective_disconnected = disconnected_ports | unlicensed

    custody = intelligence_path(root, "_intelligence/_adversary")
    anti_skill_adapter = OewasAntiSkillAdapter(anti_skill_runtime)
    service = build_adversary_service(
        root,
        turn_executor=turn_executor,
        provider=provider,
        model=model,
        anti_skill_gate=(
            None if PortName.OEWAS_ANTI_SKILL in effective_disconnected else anti_skill_adapter
        ),
    )
    ports: dict[PortName, Any] = {
        PortName.NATIVE_BOUT: NativeBoutPortAdapter(service, _probe_bout_service),
        PortName.CODA_EVALUATION: CodaPortAdapter(),
        PortName.LGGR_GLUING: LggrPortAdapter(),
        PortName.IMMUNE_ANTIBODIES: OeeisImmuneAdapter(root),
        PortName.PROMPT_GENEALOGY: PromptCivGenealogyAdapter(custody / "swarm_lineage.jsonl"),
        PortName.OEWAS_ANTI_SKILL: anti_skill_adapter,
        PortName.SGT_EMISSION: AdversarySgtAdapter(custody / "sgt_packets.jsonl"),
        PortName.ENVELOPE_STORE: FileEnvelopeStore(custody / "runs"),
        PortName.ADVERSARY_RUNTIME: AdversaryRuntimeProbe(build_adversary_runtime),
        PortName.SEAT_TRANSPORT: SeatTransportProbe(),
    }
    unknown = set(effective_disconnected) - set(ports)
    if unknown:
        raise ValueError(f"no adapter to disconnect for {sorted(p.value for p in unknown)}")
    for port in effective_disconnected:
        ports[port] = NullEstateAdapter(ports[port].estate, port)
    return AdversarySpineV1(
        bout=ports[PortName.NATIVE_BOUT],
        coda=ports[PortName.CODA_EVALUATION],
        lggr=ports[PortName.LGGR_GLUING],
        immune=ports[PortName.IMMUNE_ANTIBODIES],
        genealogy=ports[PortName.PROMPT_GENEALOGY],
        anti_skill=ports[PortName.OEWAS_ANTI_SKILL],
        sgt=ports[PortName.SGT_EMISSION],
        envelopes=ports[PortName.ENVELOPE_STORE],
        extra_probes=(ports[PortName.ADVERSARY_RUNTIME], ports[PortName.SEAT_TRANSPORT]),
        swarm_type=resolved_swarm_type,
        specialization=spec,
    )


SwarmT = TypeVar("SwarmT", bound=AdversarySwarm)
#: Specialisations the native check accepted in this process; they are immutable values.
_NATIVELY_CHECKED: set[SwarmSpecializationV1] = set()


def build_adversary_swarm(
    swarm_class: type[SwarmT],
    *,
    spine: AdversarySpineV1 | None = None,
    specialization: SwarmSpecializationV1 | None = None,
    swarm_type: SwarmTypeV1 | str | None = None,
    **spine_options: Any,
) -> SwarmT:
    """Build a Adversary swarm specialisation on a spine (built here unless given)."""
    if not (isinstance(swarm_class, type) and issubclass(swarm_class, AdversarySwarm)):
        raise TypeError("swarm_class must specialise AdversarySwarm")
    if specialization is not None and swarm_class is not AdversarySwarm:
        raise TypeError("instance workload profiles are only valid on the Adversary base")
    if swarm_type is not None and specialization is None:
        specialization = resolve_swarm_type_profile(swarm_type)
    spec = specialization if specialization is not None else swarm_class.SPECIALIZATION
    if type(spec) is not SwarmSpecializationV1:
        raise TypeError("specialization must be an exact SwarmSpecializationV1")
    validate_adversary_swarm_composition(spec.composition)
    if spec not in _NATIVELY_CHECKED:
        checked = check_specialization(spec)
        if isinstance(checked, Err):
            raise SpecializationError(checked.error.code, checked.error.message)
        _NATIVELY_CHECKED.add(spec)
    if specialization is not None and spec not in WORKLOAD_PROFILES_V01.values():
        raise SpecializationError("WORKLOAD_PROFILE_UNDECLARED", spec.specialization_id)
    if spine is not None and spine_options:
        raise ValueError("pass either a spine or spine options, not both")
    if swarm_type is not None and "swarm_type" not in spine_options:
        spine_options["swarm_type"] = swarm_type
    built_spine = spine if spine is not None else build_adversary_spine(**spine_options)
    if specialization is not None:
        return swarm_class(built_spine, specialization=spec)
    return swarm_class(built_spine)


def build_scene_use_case(
    repo_root: Path | str | None = None, *, dialogue_provider: DialogueProvider | None = None
) -> AdversaryBoutUseCase:
    """The residual-scene use case over the YAML scene repository."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return AdversaryBoutUseCase(
        YamlSceneRepository(root),
        SceneReceiptWriter(root),
        synthesizer=DialogueSynthesizer(dialogue_provider),
    )


def build_software_dev_use_case(
    repo_root: Path | str | None = None, *, dialogue_provider: DialogueProvider | None = None
) -> SoftwareDevBoutUseCase:
    """The Software-Dev Shop bout use case with the novelist Panel-to-Techne role mapping."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return SoftwareDevBoutUseCase(
        root,
        synthesizer=DialogueSynthesizer(dialogue_provider),
    )


def build_governing_councils_use_case(
    repo_root: Path | str | None = None, *, dialogue_provider: DialogueProvider | None = None
) -> GoverningCouncilsBoutUseCase:
    """The Governing Councils Deliberation and Non-Interference observation use case."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return GoverningCouncilsBoutUseCase(
        root,
        synthesizer=DialogueSynthesizer(dialogue_provider),
    )


def build_thanatos_use_case(
    repo_root: Path | str | None = None, *, dialogue_provider: DialogueProvider | None = None
) -> ThanatosBoutUseCase:
    """The Thanatos Council and Nemesis child swarm handoff use case."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return ThanatosBoutUseCase(
        root,
        synthesizer=DialogueSynthesizer(dialogue_provider),
    )


def build_product_mgmt_use_case(
    repo_root: Path | str | None = None, *, dialogue_provider: DialogueProvider | None = None
) -> ProductMgmtBoutUseCase:
    """The Product Management and Sprint Lifecycle bout use case."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return ProductMgmtBoutUseCase(
        root,
        synthesizer=DialogueSynthesizer(dialogue_provider),
    )




def build_repo_wide_auditor(repo_root: Path | str | None = None) -> RepoWideCodaLggrAuditor:
    """The repo-wide CODA/LGGR source auditor (rebuilt on the base swarm in its own epic)."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return RepoWideCodaLggrAuditor(SourceAuditSquads(root), repo_root=root)


def build_prime_descent_adapter(
    host: RustSymbolGameHost | None = None,
) -> PrimeDescentAdapter:
    """Build PrimeDescentAdapter wired to the native Rust symbol game host."""
    return PrimeDescentAdapter(host=host)


def build_graph_service(
    output_dir: Path | str,
    *,
    host: RustSymbolGameHost | None = None,
    fixture_mode: bool = False,
    gateway: Any = None,
    provider: str | None = None,
    model: str | None = None,
) -> AdversarySwarmService:
    """Wire the bounded graph use case into the existing Adversary service.

    Without model configuration, diagnosis and native catalog enumeration are
    deterministic. Fixture responses are explicit. A live gateway is refused
    until admitted OEWAS instructions and anti-skill evidence bind this lane.
    """
    if gateway is None and (provider is not None or model is not None):
        raise ValueError("explicit provider and model require a configured gateway")
    if gateway is not None:
        raise ValueError("GRAPH_INSTRUCTION_INGRESS_UNBOUND: live graph gateway is not admitted")
    from providers.adapters.graph_task_adapter import GraphProviderAdapter

    from .infrastructure.graph_adapter import GraphCandidateChecker, NativeGraphEvaluator
    from .infrastructure.graph_persistence import GraphRunPersistence
    from .infrastructure.graph_replay_adapter import GraphLearningAdapter
    from .use_cases.run_graph import RunGraphTask

    evaluator = NativeGraphEvaluator(host)
    generation = (
        GraphProviderAdapter(
            evaluator, gateway=gateway, provider=provider, model=model, fixture_mode=fixture_mode
        )
        if fixture_mode or gateway is not None
        else None
    )
    return AdversarySwarmService(
        graph_execution=RunGraphTask(
            checker=GraphCandidateChecker(),
            evaluator=evaluator,
            model=generation,
            learning=GraphLearningAdapter(evaluator),
            persistence=GraphRunPersistence(output_dir),
        )
    )


def replay_graph_run(
    directory: Path | str, receipt_ref: str, *, host: RustSymbolGameHost | None = None
):
    """Revalidate a pinned five-file run and independently replay every stored certificate."""
    from operations.domain.rop.result import Ok

    from .domain.evidence import sha256_ref
    from .domain.graph_task import read_json
    from .infrastructure.graph_adapter import GraphCandidateChecker, NativeGraphEvaluator, refusal
    from .infrastructure.graph_replay_adapter import (
        GraphIntelligenceReplayAdapter,
        PersistedGraphCustody,
    )
    from .use_cases.intelligence_miner import mine_intelligence

    try:
        custody = PersistedGraphCustody(directory, receipt_ref)
        evaluator = NativeGraphEvaluator(host, custody_check=custody.verify_snapshot)
        checker = GraphCandidateChecker()
        summary = read_json((Path(directory) / "summary.json").read_bytes(), 16_777_216)["result"]
        rows = {
            row["candidate_ref"]: row
            for row in (summary["original_diagnosis"], *summary["candidate_evaluations"])
        }
        fresh = {}
        for source in custody.sources.values():
            check = checker.check(custody.task, source.candidate_bytes)
            if source.checker_receipt_bytes != check.checker_receipt_bytes:
                return refusal(
                    "GRAPH_REPLAY_CHECK_CHANGED",
                    "stored permission or fidelity check was not reproduced",
                )
            if source.native_evidence_bytes:
                replay = evaluator.replay(
                    custody.task, source.candidate_bytes, source.native_evidence_bytes
                )
                if replay.is_err:
                    return replay
                value = replay.unwrap()
                if value.to_dict() != rows[value.candidate_ref]:
                    return refusal(
                        "GRAPH_REPLAY_RESULT_CHANGED",
                        "stored measurement flags contradict independently replayed evidence",
                    )
                fresh[value.candidate_ref] = value
            elif check.verdict.value == "ACCEPTED":
                return refusal(
                    "GRAPH_REPLAY_VERIFIER_MISSING",
                    "accepted patch has no native certificate to replay",
                )
        catalog = {sha256_ref(custody.task.candidate_bytes(p)) for p in custody.task.repair_catalog}
        sourced_receipts = {
            (source.candidate_bytes, source.checker_receipt_bytes)
            for source in custody.sources.values()
        }
        checked: set[str] = set()
        for patch in custody.task.repair_catalog:
            candidate_bytes = custody.task.candidate_bytes(patch)
            check = checker.check(custody.task, candidate_bytes)
            ref = sha256_ref(candidate_bytes)
            if (
                check.verdict.value == "REJECTED"
                and (candidate_bytes, check.checker_receipt_bytes) in sourced_receipts
            ):
                checked.add(ref)
            elif check.verdict.value == "ACCEPTED" and ref in fresh:
                checked.add(ref)
        if summary["search_complete"] and not catalog <= checked:
            return refusal(
                "GRAPH_REPLAY_SEARCH_INCOMPLETE", "catalog exhaustion was not reproduced"
            )
        candidates = [
            fresh[row["candidate_ref"]]
            for row in summary["candidate_evaluations"]
            if row["candidate_ref"] in fresh and fresh[row["candidate_ref"]].verified_repair
        ]
        selected = (
            min(candidates, key=lambda item: (item.edit_cost, item.candidate_ref))
            if candidates
            else None
        )
        if summary["selected_candidate_ref"] != (selected.candidate_ref if selected else None):
            return refusal(
                "GRAPH_REPLAY_SELECTION_CHANGED",
                "selected candidate is not the minimum verified declared cost",
            )
        if summary["optimality_certified"] and (not summary["search_complete"] or selected is None):
            return refusal(
                "GRAPH_REPLAY_OPTIMALITY_REFUSED",
                "optimality requires complete checked catalog search",
            )
        replay = GraphIntelligenceReplayAdapter(custody, evaluator, checker)
        return Ok(
            mine_intelligence(custody.observations(), replay_port=replay, recurrence_threshold=2)
        )
    except (ValueError, TypeError, KeyError, OSError, UnicodeDecodeError) as exc:
        return refusal("GRAPH_REPLAY_CUSTODY_REFUSED", str(exc))


def notify_persisted_learning(
    repo_root: Path,
    directory: Path,
    verdict: str,
    *,
    source: str,
    runtime_factory: str | None = None,
) -> dict | None:
    """Capture a persisted run before optional autopoietic learning work.

    The collection receipt is committed independently of the learning worker.
    A learning failure therefore cannot make the persisted source disappear
    from the digestion queue or change the parent verdict.
    """
    import importlib
    import warnings

    from operations.infrastructure.intelligence_digestion import (
        DurableIntelligenceCollector,
    )
    from workflows_agents_skills.infrastructure.autopoiesis.learning_runtime import (
        build_learning_completion,
    )

    try:
        DurableIntelligenceCollector(repo_root).collect(
            directory,
            outcome=verdict,
            origin="adversary_skill",
            producer_id="core_adversary",
        )
    except Exception as exc:
        warnings.warn(
            f"Intelligence collection failed independently of persisted verdict: {exc}",
            RuntimeWarning,
        )
    try:
        if runtime_factory:
            module, name = runtime_factory.split(":", 1)
            completion = getattr(importlib.import_module(module), name)(repo_root)
        else:
            completion = build_learning_completion(repo_root)
        completion.completed(
            str(directory),
            outcome=verdict,
            origin="autop" if source == "autop" else "session",
        )
        return completion.last_receipt
    except Exception as exc:
        warnings.warn(
            f"AutoP completion failed independently of persisted verdict: {exc}", RuntimeWarning
        )


__all__ = [
    "FIXTURE_CRITIQUE_REPLY",
    "PrimeDescentAdapter",
    "build_governing_councils_use_case",
    "build_prime_descent_adapter",
    "build_product_mgmt_use_case",
    "build_repo_wide_auditor",
    "build_scene_use_case",
    "build_software_dev_use_case",
    "build_thanatos_use_case",
    "build_adversary_runtime",
    "build_adversary_service",
    "build_adversary_spine",
    "build_adversary_swarm",
    "wire_research_protocols",
    "adversary_fixture_seat_port",
]


from .domain.research.protocols import (  # noqa: E402
    register_claim_queue_port,
    register_cloud_kill_dispatcher_port,
    register_increment_pad_port,
    register_stage_route_port,
)
from .entrypoints.research.cloud_kill_dispatch import CloudKillDispatcher  # noqa: E402
from .infrastructure.research.claim_queue import select_one_open_from_paper  # noqa: E402
from .infrastructure.research.increment_pad import load_pad, refuse_merge_unless_ready  # noqa: E402
from .infrastructure.research.stage_routes import (  # noqa: E402
    code_rust_propose_default_route,
    code_strict_inspect_route,
    resolve_stage_route,
    run_propose_for_route,
)


class DefaultStageRouteAdapter:
    def resolve_stage_route(self, stage_id: str) -> Any:
        return resolve_stage_route(stage_id=stage_id)

    def code_rust_propose_default_route(self) -> Any:
        return code_rust_propose_default_route()

    def code_strict_inspect_route(self) -> Any:
        return code_strict_inspect_route()

    def run_propose_for_route(
        self,
        gateway: Any,
        route: Any,
        request: Any,
        *,
        require_local_live: bool = False,
    ) -> tuple[Any, dict[str, Any]]:
        return run_propose_for_route(gateway, route, request, require_local_live=require_local_live)


class DefaultIncrementPadAdapter:
    def load_pad(self, pad_root: Any) -> Any:
        return load_pad(pad_root)

    def refuse_merge_unless_ready(self, pad: Any, *, authorizer_accept: bool = False) -> None:
        refuse_merge_unless_ready(pad, authorizer_accept=authorizer_accept)


class DefaultClaimQueueAdapter:
    def select_one_open_from_paper(
        self,
        paper_path: Any,
        *,
        priority_asc: bool = True,
        prefer_scale: bool = False,
    ) -> tuple[Any, Any]:
        return select_one_open_from_paper(
            paper_path, priority_asc=priority_asc, prefer_scale=prefer_scale
        )


def wire_research_protocols() -> None:
    register_stage_route_port(DefaultStageRouteAdapter())
    register_increment_pad_port(DefaultIncrementPadAdapter())
    register_cloud_kill_dispatcher_port(CloudKillDispatcher())
    register_claim_queue_port(DefaultClaimQueueAdapter())


wire_research_protocols()
