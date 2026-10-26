"""Stage → tier route table (SCALE-001 S2).

Default propose = OpenRouter DeepSeek V4 Flash; judge = strong LLM or host scripts.
AuthorityEffect: None. Does not apply package diffs or mint GlobalGreen.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, fields, replace
from enum import Enum
from typing import Any
from uuid import uuid4

from omega_engine_pfp.infrastructure.task_turn import complete_task_turn

from omega_engine_woland.domain.providers.types import (
    CandidateRequest,
    CandidateResponse,
    ChatMessage,
    Provider,
    ProviderConfigError,
)
from omega_engine_woland.infrastructure.providers.ollama_local import local_model_name, use_local_propose_env
from omega_engine_woland.infrastructure.providers.gateway import enclosing_accounted_gateway
from omega_engine_woland.infrastructure.providers.openai_compat import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENROUTER_GEMINI_MODEL,
    DEFAULT_OPENROUTER_MODEL,
)
from omega_engine_woland.domain.research.protocols import ProposalGatewayPort
from omega_engine_woland.domain.research.stage_spec import (
    CODE_STAGE_PIPELINE,
    RIP_PAPERS_STAGE_PIPELINE,
)

AUTHORITY_EFFECT = "None"
SCHEMA_VERSION = "urn:omega:oears:stage_route:v1"

# Env overrides (optional)
ENV_PROPOSE_PROVIDER = "OEARS_DEFAULT_PROPOSE_PROVIDER"
ENV_PROPOSE_MODEL = "OEARS_DEFAULT_PROPOSE_MODEL"
ENV_JUDGE_PROVIDER = "OEARS_DEFAULT_JUDGE_PROVIDER"
ENV_JUDGE_MODEL = "OEARS_DEFAULT_JUDGE_MODEL"

DEFAULT_PROPOSE_PROVIDER = Provider.OPENROUTER
DEFAULT_PROPOSE_MODEL = DEFAULT_OPENROUTER_MODEL  # deepseek/deepseek-v4-flash
DEFAULT_JUDGE_PROVIDER = Provider.ANTHROPIC
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-20250514"


class RouteTier(str, Enum):
    """Coarse cost/quality tier for a stage."""

    PROPOSE_CHEAP = "propose_cheap"
    JUDGE_STRONG = "judge_strong"
    JUDGE_HOST = "judge_host"
    HOST_ONLY = "host_only"


class JudgeMode(str, Enum):
    """Who judges residual honesty for the stage."""

    HOST = "host"  # pytest / lake / scripts — no LLM
    STRONG = "strong"  # expensive model
    NONE = "none"  # no judge slot (build/export)


@dataclass(frozen=True)
class StageRoute:
    """Raw route configuration; the proposal call validates its finite binding.

    Construction alone does not validate these fields or authorize execution.
    """

    stage_id: str
    skill_id: str
    tier: RouteTier
    propose_provider: str | None
    propose_model: str | None
    judge_mode: JudgeMode
    judge_provider: str | None
    judge_model: str | None
    authority_effect: str = AUTHORITY_EFFECT
    schema_version: str = SCHEMA_VERSION

    def to_receipt(self) -> dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["judge_mode"] = self.judge_mode.value
        d["claims_global_green"] = False
        d['operation'] = declared_route_operation(self)
        return d


def declared_route_operation(route: StageRoute) -> dict:
    """Read the current package; only the proposal slot has an executable adapter."""
    from .skill_resolution import resolve_skill_source
    from omega_engine_woland.infrastructure.operad_binding import operation_binding
    source = resolve_skill_source(route.skill_id)
    executable = route.tier is RouteTier.PROPOSE_CHEAP and route.judge_mode is JudgeMode.HOST
    return dict(source={key: value for key, value in source.items() if key != 'instruction'},
        execution_status='DECLARED_NOT_EXECUTED' if executable else 'NOT_EXECUTABLE',
        operation_binding=operation_binding('research.' + route.stage_id, SCHEMA_VERSION,
            skill_source=source, adapter='research'))


def _env_provider(name: str, default: Provider) -> Provider:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    try:
        return Provider(raw)
    except ValueError as exc:
        raise ProviderConfigError(
            f"invalid {name}={raw!r}; expected Provider value"
        ) from exc


def _env_model(name: str, default: str) -> str:
    raw = os.environ.get(name, "").strip()
    return raw or default


def default_propose_provider() -> Provider:
    """OpenRouter by default; LOCAL when OEARS_USE_LOCAL_PROPOSE is set (S3)."""
    if use_local_propose_env() and not os.environ.get(ENV_PROPOSE_PROVIDER, "").strip():
        return Provider.LOCAL
    return _env_provider(ENV_PROPOSE_PROVIDER, DEFAULT_PROPOSE_PROVIDER)


def default_propose_model() -> str:
    """Flash by default; local model name when propose provider is LOCAL."""
    if default_propose_provider() == Provider.LOCAL:
        if os.environ.get(ENV_PROPOSE_MODEL, "").strip():
            return _env_model(ENV_PROPOSE_MODEL, local_model_name())
        return local_model_name()
    return _env_model(ENV_PROPOSE_MODEL, DEFAULT_PROPOSE_MODEL)


def default_judge_provider() -> Provider:
    return _env_provider(ENV_JUDGE_PROVIDER, DEFAULT_JUDGE_PROVIDER)


def default_judge_model() -> str:
    return _env_model(ENV_JUDGE_MODEL, DEFAULT_JUDGE_MODEL)


# skill_id → (tier, judge_mode) — propose/judge models filled at resolve time
_SKILL_ROUTE_SPEC: dict[str, tuple[RouteTier, JudgeMode]] = {
    "paper-redteam-dialogue": (RouteTier.PROPOSE_CHEAP, JudgeMode.HOST),
    "paper-improver": (RouteTier.PROPOSE_CHEAP, JudgeMode.HOST),
    "paper-adversary": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    "paper-proof-signoff": (RouteTier.JUDGE_HOST, JudgeMode.HOST),
    "paper-release": (RouteTier.JUDGE_HOST, JudgeMode.HOST),
    "paper-build": (RouteTier.HOST_ONLY, JudgeMode.NONE),
    "omega-old-man-chatgpt-red-team": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    "omega-old-man-red-team": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    # SCALE-006 CODE / ODASDS skill routes
    "techne-docs-lint-hunter-killer": (RouteTier.HOST_ONLY, JudgeMode.NONE),
    "techne-code-rust-principal-developer": (
        RouteTier.PROPOSE_CHEAP,
        JudgeMode.HOST,
    ),
    "techne-code-python-principal-developer": (
        RouteTier.PROPOSE_CHEAP,
        JudgeMode.HOST,
    ),
    "techne-code-soviet-inspector": (RouteTier.JUDGE_HOST, JudgeMode.HOST),
    "techne-software-dev-manager": (RouteTier.JUDGE_HOST, JudgeMode.HOST),
    "techne-code-contracts-adversary": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    "techne-code-rust-code-reviewer": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    "techne-code-python-code-reviewer": (RouteTier.JUDGE_STRONG, JudgeMode.STRONG),
    "techne-code-soviet-builder": (RouteTier.PROPOSE_CHEAP, JudgeMode.HOST),
    "techne-code-contracts-improver": (RouteTier.PROPOSE_CHEAP, JudgeMode.HOST),
}


_STAGE_SKILL_BINDINGS = {
    stage.stage_id: stage.skill_id
    for stage in (*RIP_PAPERS_STAGE_PIPELINE, *CODE_STAGE_PIPELINE)
}


def _skill_for_stage_id(stage_id: str) -> str:
    try:
        return _STAGE_SKILL_BINDINGS[stage_id]
    except KeyError as exc:
        raise ProviderConfigError(f"unknown stage_id={stage_id!r}") from exc


def resolve_stage_route(
    *,
    stage_id: str | None = None,
    skill_id: str | None = None,
) -> StageRoute:
    """Resolve a route, checking any explicit stage against its catalogue skill.

    Identity refusal precedes environment resolution. This resolver does not
    validate caller-constructed ``StageRoute`` instances or authorize execution.
    """
    sid = (stage_id or "").strip()
    sk = (skill_id or "").strip()
    if stage_id is not None:
        if not sid:
            raise ProviderConfigError("stage_id must be nonblank when supplied")
        bound_skill = _skill_for_stage_id(sid)
        if sk and sk != bound_skill:
            raise ProviderConfigError(
                f"stage/skill mismatch: stage_id={sid!r} binds "
                f"skill_id={bound_skill!r}, not {sk!r}"
            )
        sk = bound_skill
    elif sk:
        # map first matching catalog stage (papers then code)
        for s in list(RIP_PAPERS_STAGE_PIPELINE) + list(CODE_STAGE_PIPELINE):
            if s.skill_id == sk:
                sid = s.stage_id
                break
        if not sid:
            sid = f"skill:{sk}"
    else:
        raise ProviderConfigError("stage_id or skill_id required")

    if sk not in _SKILL_ROUTE_SPEC:
        raise ProviderConfigError(
            f"no stage route for skill_id={sk!r}; known: "
            + ", ".join(sorted(_SKILL_ROUTE_SPEC))
        )

    tier, judge_mode = _SKILL_ROUTE_SPEC[sk]
    propose_p: str | None = None
    propose_m: str | None = None
    judge_p: str | None = None
    judge_m: str | None = None

    if tier == RouteTier.PROPOSE_CHEAP:
        propose_p = default_propose_provider().value
        propose_m = default_propose_model()
    elif tier == RouteTier.JUDGE_STRONG:
        # strong stages use judge slot as the primary LLM (adversary/OMC)
        judge_p = default_judge_provider().value
        judge_m = default_judge_model()
    # HOST_ONLY / JUDGE_HOST: no propose model

    if judge_mode == JudgeMode.STRONG and not judge_p:
        judge_p = default_judge_provider().value
        judge_m = default_judge_model()

    return StageRoute(
        stage_id=sid,
        skill_id=sk,
        tier=tier,
        propose_provider=propose_p,
        propose_model=propose_m,
        judge_mode=judge_mode,
        judge_provider=judge_p,
        judge_model=judge_m,
    )


def improver_default_route() -> StageRoute:
    """Canonical cheap improver path (S2 exit criterion)."""
    return resolve_stage_route(stage_id="stage_1_improver")


def code_rust_propose_default_route() -> StageRoute:
    """SCALE-006 S2/S3: panel-default CODE rust propose (Flash)."""
    return resolve_stage_route(stage_id="code_stage_1_rust_propose")


def code_soviet_inspect_route() -> StageRoute:
    """SCALE-006: soviet inspector host judge after code propose."""
    return resolve_stage_route(stage_id="code_stage_3_soviet_inspect")


def catalog_routes() -> list[dict[str, Any]]:
    """All RIP_PAPERS stages with resolved routes (receipt-friendly)."""
    out: list[dict[str, Any]] = []
    for s in RIP_PAPERS_STAGE_PIPELINE:
        out.append(resolve_stage_route(stage_id=s.stage_id).to_receipt())
    return out


def code_catalog_routes() -> list[dict[str, Any]]:
    """All CODE_STAGE_PIPELINE stages with resolved routes."""
    out: list[dict[str, Any]] = []
    for s in CODE_STAGE_PIPELINE:
        out.append(resolve_stage_route(stage_id=s.stage_id).to_receipt())
    return out


def _validated_propose_route(
    route: StageRoute,
) -> tuple[Provider, str, dict[str, Any]]:
    """Snapshot a canonical proposal binding, without licensing an actor.

    Use no environment defaults or caller methods here. The snapshot contains
    only validated immutable field values before probes or gateway callbacks.
    """
    if type(route) is not StageRoute:
        raise ProviderConfigError("proposal route must be an exact StageRoute")
    snapshot = {
        field.name: getattr(route, field.name, None) for field in fields(StageRoute)
    }
    if (
        type(snapshot["schema_version"]) is not str
        or snapshot["schema_version"] != SCHEMA_VERSION
    ):
        raise ProviderConfigError("proposal route schema_version is invalid")
    if (
        type(snapshot["authority_effect"]) is not str
        or snapshot["authority_effect"] != AUTHORITY_EFFECT
    ):
        raise ProviderConfigError("proposal route authority_effect must be None")
    sid, sk = snapshot["stage_id"], snapshot["skill_id"]
    if type(sid) is not str or type(sk) is not str:
        raise ProviderConfigError("proposal route identities must be exact strings")
    tier, judge_mode = snapshot["tier"], snapshot["judge_mode"]
    if type(tier) is not RouteTier or type(judge_mode) is not JudgeMode:
        raise ProviderConfigError(
            "proposal route tier and judge_mode must be exact enums"
        )
    expected = _SKILL_ROUTE_SPEC.get(sk)
    if expected is None:
        raise ProviderConfigError("proposal route skill is unknown")
    bound_skill = _STAGE_SKILL_BINDINGS.get(sid)
    if bound_skill is not None:
        if bound_skill != sk:
            raise ProviderConfigError("proposal route stage/skill mismatch")
    elif not (sid == f"skill:{sk}" and sk not in _STAGE_SKILL_BINDINGS.values()):
        raise ProviderConfigError("proposal route stage identity is not canonical")
    expected_tier, expected_judge_mode = expected
    if tier is not expected_tier or judge_mode is not expected_judge_mode:
        raise ProviderConfigError("proposal route tier/judge binding mismatch")
    if tier is not RouteTier.PROPOSE_CHEAP or judge_mode is not JudgeMode.HOST:
        raise ProviderConfigError(
            f"stage {sid} has no propose LLM slot (tier={tier.value})"
        )
    if snapshot["judge_provider"] is not None or snapshot["judge_model"] is not None:
        raise ProviderConfigError("proposal route has incompatible judge LLM slots")
    provider_name, model = snapshot["propose_provider"], snapshot["propose_model"]
    if (
        type(provider_name) is not str
        or not provider_name.strip()
        or type(model) is not str
        or not model.strip()
    ):
        raise ProviderConfigError(
            "proposal route provider/model must be nonempty exact strings"
        )
    try:
        provider = Provider(provider_name)
    except ValueError as exc:
        raise ProviderConfigError("proposal route provider is invalid") from exc
    snapshot["tier"] = tier.value
    snapshot["judge_mode"] = judge_mode.value
    snapshot["claims_global_green"] = False
    return provider, model, snapshot


def run_propose_for_route(
    gateway: ProposalGatewayPort,
    route: StageRoute,
    request: CandidateRequest,
    *,
    require_local_live: bool = False,
    ollama_get_json: Any | None = None,
) -> tuple[CandidateResponse, dict[str, Any]]:
    """Validate the finite route binding, then use its proposal slot.

    Host-only and judge-only routes refuse, even with caller-supplied slots.
    These checks do not license an actor or authorize package mutation.
    Live proposals use OpenRouter; explicit fixtures remain available. Other
    provider records remain readable. Current-IDE work uses prepare/submit.
    The dedicated paper swarm remains a separate entrypoint; a paper-named
    stage in this generic Woland adapter does not create a bypass exception.
    """
    provider, model, route_receipt = _validated_propose_route(route)
    if provider not in (Provider.FIXTURE, Provider.OPENROUTER):
        raise ProviderConfigError(
            "WOLAND_EXECUTOR_RETIRED: this proposal provider is retired; "
            "use the current IDE session or OpenRouter. No fallback was attempted."
        )
    if not enclosing_accounted_gateway(gateway):
        raise ProviderConfigError(
            "RESEARCH_ACCOUNTED_GATEWAY_REQUIRED: bind the enclosing run's existing "
            "budgeted or accounted gateway."
        )
    from .skill_resolution import resolve_skill_source
    from omega_engine_woland.infrastructure.operad_binding import validate_operation_binding
    declared = declared_route_operation(route)
    route_receipt['operation'] = declared
    operation = validate_operation_binding(declared['operation_binding'],
        role_id='research.' + route.stage_id)
    source = resolve_skill_source(route.skill_id)
    if source['source_sha256'] != declared['source']['source_sha256']:
        raise ValueError('OPERATION_SOURCE_CHANGED')
    guidance = ('Selected current skill package: ' + source['canonical_skill_id'] + '\n'
        + source['instruction'])
    request = (replace(request, messages=(ChatMessage('system', guidance), *request.messages))
               if request.messages else replace(request, system=request.system + '\n' + guidance))
    cand, budget, checked = complete_task_turn(gateway, request,
        task_id="woland-stage:" + route_receipt["stage_id"], attempt_id=uuid4().hex,
        provider=provider, model=model)
    receipt: dict[str, Any] = {
        "stage_route": route_receipt,
        "budget": budget.to_dict() if budget is not None else None,
        "pfp": checked,
        'operation_execution': {**operation, 'binding': declared['operation_binding'],
            'executed_operation_ids': operation['operation_ids'],
            'executed_guard_ids': [guard['op_id'] for guard in operation['guards']],
            'outcome': checked['failure_class'],
            'source': {**declared['source'], 'executed': True},
            'execution_kind': 'checked_pfp_guidance', 'authority_effect': 'None'},
        "candidate": {
            "provider": cand.provider,
            "model": cand.model,
            "input_tokens": cand.input_tokens,
            "output_tokens": cand.output_tokens,
            "transport": cand.transport,
            "authority_effect": cand.authority_effect,
        },
        "authority_effect": AUTHORITY_EFFECT,
    }
    return cand, receipt


def local_improver_route() -> StageRoute:
    """Improver route forced to LOCAL + configured Ollama model (S3 helper)."""
    base = improver_default_route()
    return StageRoute(
        stage_id=base.stage_id,
        skill_id=base.skill_id,
        tier=base.tier,
        propose_provider=Provider.LOCAL.value,
        propose_model=local_model_name(),
        judge_mode=base.judge_mode,
        judge_provider=base.judge_provider,
        judge_model=base.judge_model,
    )


def fixture_residual_improver_propose(
    *,
    gateway: ProposalGatewayPort,
    residual_id: str = "R-SCALE-001",
    system: str = "OEARS residual-honest improver (fixture)",
    user: str | None = None,
) -> dict[str, Any]:
    """One residual propose via an explicitly injected fixture gateway (S4).

    Does not apply package diffs. AuthorityEffect None.
    """
    route = improver_default_route()
    text = user or (
        f"Propose residual-honest text for {residual_id}; "
        "do not claim GlobalGreen or theorem closure."
    )
    cand, receipt = run_propose_for_route(
        gateway,
        route,
        CandidateRequest(system=system, user=text),
        require_local_live=False,
    )
    out = {
        "residual_id": residual_id,
        "propose_receipt": receipt,
        "content_len": len(cand.content),
        "authority_effect": AUTHORITY_EFFECT,
        "claims_global_green": False,
        "applied": False,
        "human_accept_required": True,
    }
    return out


def gemini_strong_judge_route(*, stage_id: str = "stage_2_adversary") -> StageRoute:
    """SCALE-003 S3: strong-judge route using native Gemini Flash (allowlist+budget).

    Does not change default Anthropic judge; operator opts into Gemini explicitly.
    """
    base = resolve_stage_route(stage_id=stage_id)
    return StageRoute(
        stage_id=base.stage_id,
        skill_id=base.skill_id,
        tier=RouteTier.JUDGE_STRONG,
        propose_provider=None,
        propose_model=None,
        judge_mode=JudgeMode.STRONG,
        judge_provider=Provider.GEMINI.value,
        judge_model=DEFAULT_GEMINI_MODEL,
    )


def gemini_openrouter_propose_route() -> StageRoute:
    """SCALE-003 S3: cheap propose via OpenRouter Google Gemini Flash slug."""
    base = improver_default_route()
    return StageRoute(
        stage_id=base.stage_id,
        skill_id=base.skill_id,
        tier=base.tier,
        propose_provider=Provider.OPENROUTER.value,
        propose_model=DEFAULT_OPENROUTER_GEMINI_MODEL,
        judge_mode=base.judge_mode,
        judge_provider=base.judge_provider,
        judge_model=base.judge_model,
    )
