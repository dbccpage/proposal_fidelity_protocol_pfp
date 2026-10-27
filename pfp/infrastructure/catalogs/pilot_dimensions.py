"""Load the pilot dimensions catalog. AuthorityEffect: None."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from pfp.infrastructure.yaml_loading import strict_yaml_load
from pfp.domain.stages.cartesian_matrix_types import (
    DimensionDefinition,
    CartesianCoordinate,
    SamplingSlice,
)


class CartesianMatrixSpace:
    """Manager and calculator for the PFP Cartesian Product matrix space."""

    _instance: CartesianMatrixSpace | None = None

    def __init__(self, register_path: Path | None = None) -> None:
        self._dimensions: dict[str, DimensionDefinition] = {}
        self._slices: dict[str, SamplingSlice] = {}
        self._register_path = register_path
        self._load_register()

    @classmethod
    def get_instance(cls, register_path: Path | None = None) -> CartesianMatrixSpace:
        if cls._instance is None:
            cls._instance = CartesianMatrixSpace(register_path=register_path)
        return cls._instance

    def _load_register(self) -> None:
        reg_file = self._register_path
        if reg_file is None:
            reg_file = (
                Path(__file__).resolve().parents[1]
                / "yaml"
                / "cartesian_matrix/cartesian_matrix_register.yaml"
            )
        if reg_file and reg_file.is_file():
            data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for d in data.get("dimensions", []):
                    try:
                        defn = DimensionDefinition.model_validate(d)
                        self._dimensions[defn.dimension_id] = defn
                    except Exception:
                        pass
                for s in data.get("sampling_slices", []):
                    try:
                        sl = SamplingSlice.model_validate(s)
                        self._slices[sl.slice_id] = sl
                    except Exception:
                        pass

    def compute_total_volume(self, custom_family_count: int | None = None) -> int:
        volume = 1
        for dim_id, dim in self._dimensions.items():
            if dim_id == "task_family" and custom_family_count is not None:
                volume *= custom_family_count
            else:
                volume *= max(1, len(dim.levels))
        return volume

    def dimension_names(self) -> list[str]:
        return list(self._dimensions.keys())

    def get_dimension(self, dim_id: str) -> DimensionDefinition | None:
        return self._dimensions.get(dim_id)

    def get_slice(self, slice_id: str) -> SamplingSlice | None:
        return self._slices.get(slice_id)

    def validate_coordinate(self, coord: CartesianCoordinate) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for dim_id, value in coord.model_dump().items():
            dim = self._dimensions.get(dim_id)
            if dim is None:
                continue
            if dim_id == "task_family":
                if not isinstance(value, str) or not value:
                    errors.append(f"task_family must be non-empty string, got {value!r}")
            elif dim_id == "difficulty_rung":
                if not isinstance(value, int) or value < 1:
                    errors.append(f"difficulty_rung must be positive int, got {value!r}")
            else:
                if value not in dim.levels:
                    errors.append(f"Invalid {dim_id}: {value!r}. Must be one of {dim.levels}")
        return len(errors) == 0, errors
