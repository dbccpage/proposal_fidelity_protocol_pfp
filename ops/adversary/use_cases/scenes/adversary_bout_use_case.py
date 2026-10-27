"""Scene orchestration over injected domain ports. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Dict, List, Optional

from operations.domain.rop.result import Err
from pfp.functional_boundary import RustFunctionalRequired
from adversary.domain.residual_algebra.character_operators import (
    CharacterOperatorRegistry,
)
from adversary.domain.residual_algebra.dialogue_synthesizer import DialogueSynthesizer
from adversary.domain.residual_algebra.errors import ResidualAlgebraDomainError
from adversary.domain.residual_algebra.licensing_boundary import (
    LicensingBoundary,
    ObstructionValuator,
    ValuationReceipt,
)
from adversary.domain.residual_algebra.protocols import ObstructionValuatorProtocol
from adversary.domain.residual_algebra.residual_sorts import (
    EMPTY_RESIDUAL,
    Residual,
    Residual1Cochain,
)
from adversary.domain.residual_algebra.scene_models import (
    SceneBeat,
    SceneExecutionReceipt,
    AdversaryScene,
)
from adversary.domain.residual_algebra.scene_ports import (
    SceneReceiptStore,
    SceneRepository,
)

REQUIRED_SCENE_ROLES = ("syntax_prefilter", "adversary")


def _role_key(value: str) -> str:
    return "_".join(value.casefold().replace("-", " ").replace("_", " ").split())


def _speaker_roles(speaker: str) -> tuple[str, ...]:
    # The legacy composite speaker is rendered through the two existing operators.
    if _role_key(speaker) == "bare_metal_anchor_and_overconfidence_probe":
        return ("bare_metal_anchor", "overconfidence_probe")
    if _role_key(speaker) == "gauge_breaker":
        return ("gauge_breaker",)
    for spec in CharacterOperatorRegistry.registered_specs():
        if spec.matches(speaker.casefold().strip()):
            return (spec.key,)
    return (_role_key(speaker),)


def _selection_aliases(
    available: tuple[str, ...], scenes: Sequence[AdversaryScene]
) -> dict[str, str]:
    aliases = {role: role for role in available}
    for spec in CharacterOperatorRegistry.registered_specs():
        if spec.key in available:
            aliases.update({_role_key(alias): spec.key for alias in spec.aliases})
    if "gauge_breaker" in available:
        aliases["gauge_breaker"] = "gauge_breaker"
    # Only full declared display names are aliases; user IDs never substring-match.
    for scene in scenes:
        for beat in scene.beats:
            speaker = beat.get("speaker", "Unknown")
            roles = _speaker_roles(speaker)
            if len(roles) == 1 and roles[0] in available:
                aliases[_role_key(speaker)] = roles[0]
    return aliases


def _canonical_selection(selected_roles: Sequence[str], aliases: dict[str, str]) -> tuple[str, ...]:
    if isinstance(selected_roles, (str, bytes)) or not isinstance(selected_roles, Sequence):
        raise ResidualAlgebraDomainError(
            "SCENE_ROLE_SELECTION_INVALID", "roles must be a sequence of role IDs"
        )
    if not selected_roles:
        raise ResidualAlgebraDomainError("SCENE_ROLE_SELECTION_EMPTY", "select at least one role")
    chosen: list[str] = []
    for value in selected_roles:
        if not isinstance(value, str) or not value.strip():
            raise ResidualAlgebraDomainError(
                "SCENE_ROLE_SELECTION_EMPTY", "role IDs must be nonempty strings"
            )
        role = aliases.get(_role_key(value))
        if role is None:
            raise ResidualAlgebraDomainError("SCENE_ROLE_UNKNOWN", f"unknown role: {value}")
        if role in chosen:
            raise ResidualAlgebraDomainError("SCENE_ROLE_DUPLICATE", f"duplicate role: {role}")
        chosen.append(role)
    return tuple(chosen)


class AdversaryBoutUseCase:
    def __init__(
        self,
        scenes: SceneRepository,
        receipts: SceneReceiptStore,
        *,
        synthesizer: DialogueSynthesizer | None = None,
        valuator: ObstructionValuatorProtocol | None = None,
    ) -> None:
        self.scenes = scenes
        self.receipts = receipts
        self.synthesizer = synthesizer or DialogueSynthesizer()
        self.valuator = valuator or ObstructionValuator()
        self.intelligence_dir = receipts.intelligence_dir

    def load_scenes(self) -> List[AdversaryScene]:
        return self.scenes.load_scenes()

    def get_scene(self, scene_id: str) -> Optional[AdversaryScene]:
        """Lookup a specific scene by id."""
        for s in self.load_scenes():
            if s.id == scene_id:
                return s
        return None

    def list_roles(self, scene: AdversaryScene | None = None) -> tuple[str, ...]:
        """Discover the scene cast plus the fixed checker and terminal stages."""
        scenes = (scene,) if scene is not None else self.load_scenes()
        roles = set(REQUIRED_SCENE_ROLES)
        for item in scenes:
            for beat in item.beats:
                roles.update(_speaker_roles(beat.get("speaker", "Unknown")))
        return tuple(sorted(roles))

    def _select_roles(
        self, selected_roles: Sequence[str] | None, available: tuple[str, ...]
    ) -> tuple[str, ...]:
        if selected_roles is None:
            return available
        chosen = _canonical_selection(
            selected_roles, _selection_aliases(available, self.load_scenes())
        )
        missing = set(REQUIRED_SCENE_ROLES) - set(chosen)
        if missing:
            raise ResidualAlgebraDomainError(
                "SCENE_REQUIRED_ROLE_MISSING", "required roles: " + ", ".join(sorted(missing))
            )
        return chosen

    def execute_scene(
        self,
        scene: AdversaryScene,
        initial_carrier: Optional[Dict[str, Any]] = None,
        *,
        exactness_witness: Optional[Residual1Cochain] = None,
        selected_roles: Sequence[str] | None = None,
    ) -> SceneExecutionReceipt:
        """
        Executes a single Adversary scene deterministically through the 8-stage waist:
        1. Ingest carrier
        2. Construct and evaluate multicategory term
        3. Extract residual cochains
        4. Render dramatic & technical dialogue beats
        5. Value obstruction and verify exactness
        6. Apply licensing boundary
        7. Compute SHA-256 evidence digest
        """
        roles = self._select_roles(selected_roles, self.list_roles(scene))
        # Selection narrows dramatic operators only. Valuation and licensing below
        # remain unconditional; retaining these names never grants live-seat authority.
        term = scene.multicategory_term_str
        if selected_roles is not None:
            term = f"select_roles[{','.join(roles)}]({term})"
        if initial_carrier is None:
            carrier_in: Dict[str, Any] = {
                "scene_id": scene.id,
                "title": scene.title,
                "location": scene.location,
                "source": scene.source,
                "targets": list(scene.targets),
                "residual_sort": scene.residual_sort,
                "initial_status": "unverified",
                "authority_effect": "None",
            }
        else:
            carrier_in = dict(initial_carrier)

        carrier_in["scene_role_selection"] = list(roles)
        carrier_in["source_multicategory_term"] = scene.multicategory_term_str
        carrier_in["required_scene_stages"] = ["syntax_prefilter:obstruction_valuation", "adversary:licensing_boundary"]

        # 1. Construct Multicategory Term from scene beats and character operators
        operators: List[Any] = []
        beats_executed: List[SceneBeat] = []

        for b in scene.beats:
            speaker = b.get("speaker", "Unknown")
            cue = b.get("cue", "")
            speaker_roles = _speaker_roles(speaker)
            for role in speaker_roles:
                if role not in roles:
                    continue
                # Split the historical composite; keep all other source display names.
                spk = role.title() if len(speaker_roles) > 1 else speaker
                pkg = CharacterOperatorRegistry.get_operator_package(
                    role if role == "gauge_breaker" else spk
                )
                operators.append(pkg)
                dialogue_result = self.synthesizer.render_dialogue(spk, cue)
                if isinstance(dialogue_result, Err):
                    failure = dialogue_result.error
                    raise ResidualAlgebraDomainError(failure.code, failure.message)
                cochain = Residual1Cochain(
                    residual_sort=pkg.residual_out,
                    mass=0.0,
                    defects=(),
                    witness_data=(f"{role}:{cue[:30]}",),
                )
                beats_executed.append(
                    SceneBeat(
                        speaker=spk,
                        cue=cue,
                        dialogue=dialogue_result.value,
                        operator_tag=pkg.residual_out,
                        cochain=cochain,
                    )
                )

        carrier_in["executed_scene_roles"] = [
            role
            for beat in scene.beats
            for role in _speaker_roles(beat.get("speaker", "Unknown"))
            if role in roles
        ]

        # Build term chain: op_n o_0 ... o_0 op_1
        if not operators:
            operators.append(CharacterOperatorRegistry.get_operator_package("adversary"))

        carrier_out = carrier_in
        absorbed_res = EMPTY_RESIDUAL
        extracted_cochains = []
        for operator in operators:
            previous = carrier_out
            carrier_out = operator.apply_transform(previous)
            cochain = operator.extract_residual(previous, carrier_out)
            extracted_cochains.append(cochain)
            absorbed_res = absorbed_res.absorb(Residual(cochain.defects, cochain.mass))

        # Combine beat cochains with extracted cochains
        all_cochains = tuple(extracted_cochains) + tuple(
            b.cochain for b in beats_executed if b.cochain is not None
        )

        # 3. Value obstruction under ObstructionValuator
        try:
            if all_cochains:
                valuation = self.valuator.value_cochains(all_cochains)
            else:
                zero_c = Residual1Cochain(residual_sort=scene.residual_sort, mass=0.0)
                valuation = self.valuator.value_cochain(zero_c)
        except RustFunctionalRequired as exc:
            # Catalog dialogue has no declared chain complex. Keep its useful
            # observations without inventing a carrier or a zero functional.
            valuation = ValuationReceipt.not_measured(
                scene.residual_sort, code=exc.code, reason=str(exc),
            )

        # 4. Generate SHA-256 evidence digest
        evidence_payload = {
            "scene_id": scene.id,
            "term": term,
            "carrier_in": carrier_in,
            "carrier_out": carrier_out,
            "cochains_count": len(all_cochains),
            "residual_risk": absorbed_res.risk,
        }
        evidence_sha256 = hashlib.sha256(
            json.dumps(evidence_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        # 5. Check licensing boundary verdict
        is_licensed, token, reasons = LicensingBoundary.propose_token(
            target_receipt=valuation,
            witness_cochain=exactness_witness,
            expected_sha256=evidence_sha256,
        )

        if is_licensed:
            verdict = "PASS_TO_MASTER"
        else:
            verdict = "REFUSE" if valuation.has_defects() else "OPEN_RESIDUAL"

        receipt = SceneExecutionReceipt(
            scene_id=scene.id,
            title=scene.title,
            timestamp=time.time(),
            carrier_in=carrier_in,
            carrier_out=carrier_out,
            multicategory_term=term,
            cochains=all_cochains,
            absorbed_residual=absorbed_res,
            valuation=valuation,
            licensing_verdict=verdict,
            licensing_token=token,
            beats_executed=tuple(beats_executed),
            evidence_sha256=evidence_sha256,
            authority_effect="None",
        )

        return receipt

    def execute_all_scenes(
        self, *, selected_roles: Sequence[str] | None = None
    ) -> List[SceneExecutionReceipt]:
        """Executes all scenes in canonical sequence."""
        scenes = self.load_scenes()
        roles = self._select_roles(selected_roles, self.list_roles())
        receipts: List[SceneExecutionReceipt] = []
        for scene in scenes:
            scene_roles = None if selected_roles is None else tuple(
                role for role in roles if role in self.list_roles(scene)
            )
            r = self.execute_scene(scene, selected_roles=scene_roles)
            receipts.append(r)
        return receipts

    def save_receipt(
        self, receipt: SceneExecutionReceipt, target_dir: Optional[Path] = None
    ) -> Path:
        return self.receipts.save_receipt(receipt, target_dir)
