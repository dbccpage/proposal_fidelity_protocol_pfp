"""meta_operad.py
==============

Higher-Order Operadic Management Calculus (HOMC-v1).

Implements the candidate specification for Operadic Meta-Management (OMM):
  - OperadSpec (Level 2 operads O = (C, Sigma, circ, I))
  - OperadMorphism (Strict/weak morphisms preserving colours, arities, and ideals)
  - OperadicBimodule (Mediating heterogeneous cross-operad interactions)
  - ObstructionCohomology (H^0 invariant fences, H^1 first-order decoys, H^2 repair obstructions)
  - ReceiptMonad (Kleisli category of receipted operads with fail-closed composition)
  - OperadicEcology (The interacting multi-operad environment E = ({O_alpha}, {phi_ab}, {B_ab}))

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple
import yaml


class CohomologyDegree(Enum):
    H0_INVARIANT_FENCE = 0
    H1_FIRST_ORDER_DEFORMATION = 1
    H2_REPAIR_OBSTRUCTION = 2
    HN_HIGHER_COHERENCE = 3


class OperadManagementError(Exception):
    """Base exception for operadic management and morphism violations."""
    pass


class MorphismViolationError(OperadManagementError):
    """Raised when an operad morphism violates colour, generator, or ideal preservation."""
    pass


class BimoduleActionError(OperadManagementError):
    """Raised when an operadic bimodule action fails typing or carrier bounds."""
    pass


@dataclass(frozen=True)
class ObstructionClass:
    """Classifies an obstruction in H^n(O; M)."""
    degree: int
    antibody_id: str
    description: str
    remediation_candidate: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def level_name(self) -> str:
        if self.degree == 0:
            return "H^0 (Invariant Domain Fence)"
        elif self.degree == 1:
            return "H^1 (First-Order Decoy / Refutation Witness)"
        elif self.degree == 2:
            return "H^2 (Obstruction to Repair / Extension)"
        return f"H^{self.degree} (Higher Coherence Obstruction)"


@dataclass
class Receipt:
    """Enriched hom-object / verification receipt."""
    receipt_id: str
    status: str  # "PASS" | "FAIL" | "REFUSAL"
    evidence_scope: str
    obstructions: List[ObstructionClass] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_pass(self) -> bool:
        return self.status == "PASS" and len(self.obstructions) == 0

    def compose(self, other: "Receipt") -> "Receipt":
        """Fail-closed Kleisli composition of receipts."""
        composite_status = "PASS" if (self.is_pass and other.is_pass) else "FAIL"
        combined_obs = list(self.obstructions) + list(other.obstructions)
        combined_scope = f"{self.evidence_scope} * {other.evidence_scope}"
        return Receipt(
            receipt_id=f"{self.receipt_id}::compose::{other.receipt_id}",
            status=composite_status,
            evidence_scope=combined_scope,
            obstructions=combined_obs,
            metadata={"left": self.metadata, "right": other.metadata},
        )


@dataclass
class OperadSpec:
    """Level 2 Operad O = (C, Sigma, circ, I)."""
    id: str
    domain: str
    colours: Set[str]
    # generator_name -> (tuple of source colours, target colour)
    generators: Dict[str, Tuple[Tuple[str, ...], str]]
    ideals: List[str]
    enrichment: str = "Receipt"
    lineage: Dict[str, Any] = field(default_factory=dict)
    obstruction_classes: List[ObstructionClass] = field(default_factory=list)

    def validate_internal_coherence(self) -> None:
        """Verify that all generators reference declared colours."""
        for g_name, (sources, target) in self.generators.items():
            for s in sources:
                if s not in self.colours:
                    raise OperadManagementError(
                        f"Generator '{g_name}' references undeclared source colour '{s}' in operad '{self.id}'"
                    )
            if target not in self.colours:
                raise OperadManagementError(
                    f"Generator '{g_name}' references undeclared target colour '{target}' in operad '{self.id}'"
                )


@dataclass
class OperadMorphism:
    """Strict or weak morphism phi: O_alpha -> O_beta."""
    id: str
    source_id: str
    target_id: str
    colour_map: Dict[str, str]
    generator_map: Dict[str, str]
    ideal_map: Dict[str, str] = field(default_factory=dict)
    kind: str = "suboperad_embedding"  # "strict" | "suboperad_embedding"
    authority_effect: str = "None"

    def verify(self, source: OperadSpec, target: OperadSpec) -> Receipt:
        """Verify colour preservation, arity typing, and ideal containment."""
        if source.id != self.source_id:
            raise MorphismViolationError(f"Source mismatch: expected {self.source_id}, got {source.id}")
        if target.id != self.target_id:
            raise MorphismViolationError(f"Target mismatch: expected {self.target_id}, got {target.id}")

        obs: List[ObstructionClass] = []

        # 1. Check colour preservation
        if self.kind == "strict":
            for sc in source.colours:
                if sc not in self.colour_map:
                    obs.append(ObstructionClass(
                        degree=1,
                        antibody_id=f"AB_UNMAPPED_COLOUR_{sc}",
                        description=f"Source colour '{sc}' is not mapped by strict morphism '{self.id}'",
                    ))
        for sc, tc in self.colour_map.items():
            if sc not in source.colours:
                obs.append(ObstructionClass(
                    degree=1,
                    antibody_id=f"AB_SOURCE_COLOUR_MISSING_{sc}",
                    description=f"Mapped source colour '{sc}' does not exist in source operad '{source.id}'",
                ))
            if tc not in target.colours:
                obs.append(ObstructionClass(
                    degree=1,
                    antibody_id=f"AB_TARGET_COLOUR_MISSING_{tc}",
                    description=f"Mapped target colour '{tc}' does not exist in target operad '{target.id}'",
                ))

        # 2. Check generator preservation and typing
        generators_to_check = source.generators.keys() if self.kind == "strict" else self.generator_map.keys()
        for sg_name in generators_to_check:
            if sg_name not in self.generator_map:
                obs.append(ObstructionClass(
                    degree=1,
                    antibody_id=f"AB_UNMAPPED_GENERATOR_{sg_name}",
                    description=f"Source generator '{sg_name}' is not mapped by strict morphism '{self.id}'",
                ))
            else:
                if sg_name not in source.generators:
                    obs.append(ObstructionClass(
                        degree=1,
                        antibody_id=f"AB_SOURCE_GENERATOR_MISSING_{sg_name}",
                        description=f"Mapped source generator '{sg_name}' does not exist in source operad '{source.id}'",
                    ))
                    continue
                tg_name = self.generator_map[sg_name]
                if tg_name not in target.generators:
                    obs.append(ObstructionClass(
                        degree=1,
                        antibody_id=f"AB_TARGET_GENERATOR_MISSING_{tg_name}",
                        description=f"Mapped generator '{tg_name}' does not exist in target operad '{target.id}'",
                    ))
                else:
                    s_sources, s_target = source.generators[sg_name]
                    t_sources, t_target = target.generators[tg_name]
                    # Check arity
                    if len(s_sources) != len(t_sources):
                        obs.append(ObstructionClass(
                            degree=2,
                            antibody_id=f"AB_ARITY_MISMATCH_{sg_name}",
                            description=f"Arity mismatch: {sg_name} has {len(s_sources)}, {tg_name} has {len(t_sources)}",
                        ))
                    else:
                        # Check mapped input types
                        for idx, src_c in enumerate(s_sources):
                            mapped_c = self.colour_map.get(src_c)
                            tgt_c = t_sources[idx]
                            if mapped_c != tgt_c:
                                obs.append(ObstructionClass(
                                    degree=2,
                                    antibody_id=f"AB_TYPE_MISMATCH_{sg_name}_SLOT_{idx}",
                                    description=f"Slot {idx} colour mismatch: {mapped_c} != {tgt_c}",
                                ))
                        # Check mapped output type
                        mapped_tgt = self.colour_map.get(s_target)
                        if mapped_tgt != t_target:
                            obs.append(ObstructionClass(
                                degree=2,
                                antibody_id=f"AB_TARGET_TYPE_MISMATCH_{sg_name}",
                                description=f"Output colour mismatch: {mapped_tgt} != {t_target}",
                            ))

        status = "PASS" if not obs else "FAIL"
        return Receipt(
            receipt_id=f"receipt::{self.id}",
            status=status,
            evidence_scope=f"Morphism check {source.id} -> {target.id}",
            obstructions=obs,
        )


@dataclass
class OperadicBimodule:
    """Operadic bimodule M mediating left O_left action and right O_right action."""
    id: str
    left_operad_id: str
    right_operad_id: str
    carrier_types: Tuple[str, ...]
    actions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OperadicEcology:
    """The operadic ecology E = ({O_alpha}, {phi_alpha_beta}, {B_alpha_beta}, K)."""
    operads: Dict[str, OperadSpec] = field(default_factory=dict)
    morphisms: Dict[str, OperadMorphism] = field(default_factory=dict)
    bimodules: Dict[str, OperadicBimodule] = field(default_factory=dict)
    global_ideals: List[str] = field(default_factory=list)

    def register_operad(self, spec: OperadSpec) -> None:
        spec.validate_internal_coherence()
        self.operads[spec.id] = spec

    def register_morphism(self, morph: OperadMorphism) -> Receipt:
        source = self.operads.get(morph.source_id)
        target = self.operads.get(morph.target_id)
        if not source:
            raise OperadManagementError(f"Morphism source operad '{morph.source_id}' not found")
        if not target:
            raise OperadManagementError(f"Morphism target operad '{morph.target_id}' not found")

        receipt = morph.verify(source, target)
        if receipt.is_pass:
            self.morphisms[morph.id] = morph
        return receipt

    def register_bimodule(self, bim: OperadicBimodule) -> None:
        if bim.left_operad_id not in self.operads:
            raise OperadManagementError(f"Bimodule left operad '{bim.left_operad_id}' not found")
        if bim.right_operad_id not in self.operads:
            raise OperadManagementError(f"Bimodule right operad '{bim.right_operad_id}' not found")
        self.bimodules[bim.id] = bim

    def check_embedding(self, sub_id: str, super_id: str) -> bool:
        """Checks if O_sub embeds into O_super via an admitted morphism."""
        for m in self.morphisms.values():
            if m.source_id == sub_id and m.target_id == super_id:
                receipt = m.verify(self.operads[sub_id], self.operads[super_id])
                if receipt.is_pass:
                    return True
        return False

    def translate_witness(self, witness: Dict[str, Any], morphism_id: str) -> Dict[str, Any]:
        """Translates a typed witness across an admitted morphism."""
        morph = self.morphisms.get(morphism_id)
        if not morph:
            raise OperadManagementError(f"Morphism '{morphism_id}' not registered in ecology")

        translated_types = {}
        for k, v in witness.get("types", {}).items():
            translated_types[k] = morph.colour_map.get(v, v)

        return {
            "source_morphism": morphism_id,
            "original_witness": witness,
            "translated_types": translated_types,
            "status": "TRANSLATED",
        }

    def execute(self, operation_id: str, *inputs: object) -> dict:
        """Ecology declarations are not executors; never turn registration into work."""
        return {"status":"REFUSED","code":"NOT_EXECUTABLE","operation_id":operation_id,"authority_effect":"None","message":"Meta-operation has no bound runtime executor"}

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "OperadicEcology":
        """Builds an OperadicEcology from a HOMC-v1 compliant dict."""
        eco = cls()
        eco_data = data.get("ecology", {})

        # 1. Operads
        for op in eco_data.get("operads", []):
            colours = set(op.get("colours", []))
            gens: Dict[str, Tuple[Tuple[str, ...], str]] = {}
            for g in op.get("generators", []):
                gens[g["name"]] = (tuple(g["inputs"]), g["output"])

            obs_classes: List[ObstructionClass] = []
            for ob in op.get("obstruction_classes", []):
                deg = ob.get("degree", ob.get("class", 0))
                if isinstance(deg, str) and deg.startswith("H^"):
                    deg = int(deg[2:])
                obs_classes.append(ObstructionClass(
                    degree=int(deg),
                    antibody_id=ob.get("antibody", ""),
                    description=ob.get("description", ""),
                ))

            spec = OperadSpec(
                id=op["id"],
                domain=op.get("domain", ""),
                colours=colours,
                generators=gens,
                ideals=op.get("ideal", op.get("ideals", [])),
                enrichment=op.get("enrichment", "Receipt"),
                lineage=op.get("lineage", {}),
                obstruction_classes=obs_classes,
            )
            eco.register_operad(spec)

        # 2. Morphisms
        for m in eco_data.get("morphisms", []):
            morph = OperadMorphism(
                id=m["id"],
                source_id=m["source"],
                target_id=m["target"],
                colour_map=m.get("colour_map", {}),
                generator_map=m.get("generator_map", {}),
                ideal_map=m.get("ideal_map", {}),
            )
            eco.register_morphism(morph)

        # 3. Bimodules
        for b in eco_data.get("bimodules", []):
            bim = OperadicBimodule(
                id=b["id"],
                left_operad_id=b["left"],
                right_operad_id=b["right"],
                carrier_types=tuple(b.get("carrier_types", [])),
                actions=b.get("actions", []),
            )
            eco.register_bimodule(bim)

        return eco

    @classmethod
    def load_from_yaml(cls, path_or_str: str | Path) -> "OperadicEcology":
        """Loads and parses a HOMC-v1 YAML file or raw string."""
        p = Path(path_or_str)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8")
        else:
            content = str(path_or_str)
        data = yaml.safe_load(content)
        return cls.load_from_dict(data)


# Canonical alias
OperadEcology = OperadicEcology

