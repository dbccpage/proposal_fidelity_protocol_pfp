"""Filesystem/YAML implementation of the scene catalog port."""

from pathlib import Path
from typing import List

import yaml

from omega_engine_woland.domain.residual_algebra.residual_sorts import R_PRODUCT_EDGE
from omega_engine_woland.domain.residual_algebra.scene_models import WolandScene


class YamlSceneRepository:
    def __init__(self, repo_root: Path) -> None:
        council_dir = repo_root / "omega_engine_woland" / "the_master_and_margarita"
        if not council_dir.exists():
            council_dir = (
                repo_root
                / "omega_engine_governance"
                / "anomalon_councils"
                / "the_master_and_margarita"
            )
        self.scenes_yaml_path = council_dir / "scenes.yaml"

    def load_scenes(self) -> List[WolandScene]:
        """Loads and parses all scenes from canonical scenes.yaml."""
        if not self.scenes_yaml_path.exists():
            raise FileNotFoundError(f"Missing scenes file at {self.scenes_yaml_path}")

        with open(self.scenes_yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        scenes: List[WolandScene] = []
        for s in raw.get("scenes", []):
            scene = WolandScene(
                id=s["id"],
                title=s["title"],
                location=s.get("location", ""),
                source=s.get("source", ""),
                targets=tuple(s.get("targets", [])),
                fits=s.get("fits", "unresolved"),
                multicategory_term_str=s.get("multicategory_term", "E_generic"),
                residual_sort=s.get("residual_sort", R_PRODUCT_EDGE),
                beats=tuple(s.get("beats", [])),
            )
            scenes.append(scene)
        return scenes
