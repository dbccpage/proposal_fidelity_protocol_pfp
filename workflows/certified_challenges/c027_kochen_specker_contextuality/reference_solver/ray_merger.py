# AuthorityEffect: None.
"""
Ray parsing and canonical merging for C027.

Handles:
1. Parsing vector coordinates from wire format into QuadRat.
2. Checking for zero vectors (triggers OUT_OF_SCOPE).
3. Merging parallel vectors into canonical rays (projective equivalence u ~ c*v).
4. Mapping from input vector indices to canonical ray indices.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from .quad_field import QuadRat
except (ImportError, ValueError):
    try:
        from c027_kochen_specker_contextuality.reference_solver.quad_field import QuadRat
    except (ImportError, ValueError):
        from quad_field import QuadRat


def normalize_ray(vec: List[QuadRat]) -> List[QuadRat]:
    """
    Normalizes a non-zero vector by dividing by its first non-zero coordinate.
    The resulting vector has first non-zero entry equal to 1, providing
    a canonical representative for the projective ray.
    """
    first_nonzero: Optional[QuadRat] = None
    for coord in vec:
        if not coord.is_zero():
            first_nonzero = coord
            break

    if first_nonzero is None:
        raise ValueError("Cannot normalize zero vector")

    return [c / first_nonzero for c in vec]


def parse_and_merge_rays(
    dimension: int,
    raw_vectors: List[Any],
) -> Tuple[bool, Optional[Dict[str, Any]], List[List[QuadRat]], List[int]]:
    """
    Parses raw vector coordinates, validates dimensions and non-zeroness,
    and merges parallel vectors into canonical rays.

    Returns:
        (is_valid, error_witness, canonical_rays, input_to_ray_map)
    """
    if dimension not in (3, 4):
        return False, {"kind": "invalid_dimension", "dimension": dimension}, [], []

    canonical_rays: List[List[QuadRat]] = []
    ray_lookup: Dict[Tuple[QuadRat, ...], int] = {}
    input_to_ray: List[int] = []

    for v_idx, raw_v in enumerate(raw_vectors):
        if not isinstance(raw_v, list) or len(raw_v) != dimension:
            return (
                False,
                {"kind": "dimension_mismatch", "index": v_idx, "expected": dimension},
                [],
                [],
            )

        # Parse coordinates
        parsed_coords: List[QuadRat] = []
        is_all_zero = True
        for elem in raw_v:
            try:
                qr = QuadRat.from_wire(elem)
            except Exception as ex:
                return (
                    False,
                    {"kind": "unparseable_coordinate", "index": v_idx, "error": str(ex)},
                    [],
                    [],
                )
            if not qr.is_zero():
                is_all_zero = False
            parsed_coords.append(qr)

        if is_all_zero:
            return False, {"kind": "zero_vector", "index": v_idx}, [], []

        # Canonical normalization
        canon_vec = normalize_ray(parsed_coords)
        key = tuple(canon_vec)

        if key in ray_lookup:
            ray_id = ray_lookup[key]
        else:
            ray_id = len(canonical_rays)
            ray_lookup[key] = ray_id
            canonical_rays.append(canon_vec)

        input_to_ray.append(ray_id)

    return True, None, canonical_rays, input_to_ray
