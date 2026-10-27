"""Finite category validation and basic operations for C049.
Handles objects, morphisms, identities, and composition tables.
"""

from typing import Any, Dict, List, Optional, Tuple


class FiniteCategory:
    def __init__(
        self, objects: List[str], morphisms: List[List[str]], comp: Dict[str, Dict[str, str]]
    ):
        self.objects = list(objects)
        # morphisms are [name, src, dst]
        self.morphisms = {m[0]: (m[1], m[2]) for m in morphisms}
        self.raw_comp = comp  # comp[g][f] = g ∘ f
        self.id_map = {}  # obj -> id_morphism_name

        # Find or verify identity for each object
        for m_name, (src, dst) in self.morphisms.items():
            if src == dst:
                # Potential identity
                if m_name.startswith("id") or m_name == f"id_{src}" or m_name == f"id{src}":
                    self.id_map[src] = m_name

        # If not explicitly named, identify identity by behavior
        for obj in self.objects:
            if obj not in self.id_map:
                for m_name, (src, dst) in self.morphisms.items():
                    if src == obj and dst == obj:
                        self.id_map[obj] = m_name
                        break

    def compose(self, g: str, f: str) -> Optional[str]:
        """Compute g ∘ f where f: X -> Y and g: Y -> Z."""
        if f not in self.morphisms or g not in self.morphisms:
            return None
        src_f, dst_f = self.morphisms[f]
        src_g, dst_g = self.morphisms[g]
        if dst_f != src_g:
            return None  # Uncomposable

        # Identity laws
        if f == self.id_map.get(src_f):
            return g
        if g == self.id_map.get(src_g):
            return f

        # Table lookup
        if g in self.raw_comp and f in self.raw_comp[g]:
            return self.raw_comp[g][f]

        # Check if g ∘ f equals an identity morphism when dst_g == src_f
        # Default: if only one morphism exists between src_f and dst_g, return it
        hom = self.hom_set(src_f, dst_g)
        if len(hom) == 1:
            return hom[0]

        return None

    def hom_set(self, src: str, dst: str) -> List[str]:
        """Return list of all morphisms from src to dst."""
        return [m for m, (s, d) in self.morphisms.items() if s == src and d == dst]

    def validate(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate category laws: identities exist, composition is closed and associative."""
        # 1. Identities exist
        for obj in self.objects:
            if obj not in self.id_map:
                return False, {"reason": "MISSING_IDENTITY", "object": obj}

        # 2. Composition associativity: h ∘ (g ∘ f) == (h ∘ g) ∘ f
        for f, (s_f, d_f) in self.morphisms.items():
            for g in self.hom_set(d_f, d_f):  # check composable
                pass
        for f, (s_f, d_f) in self.morphisms.items():
            for g, (s_g, d_g) in self.morphisms.items():
                if d_f != s_g:
                    continue
                gf = self.compose(g, f)
                if gf is None:
                    return False, {"reason": "COMPOSITION_NOT_CLOSED", "g": g, "f": f}
                for h, (s_h, d_h) in self.morphisms.items():
                    if d_g != s_h:
                        continue
                    hg = self.compose(h, g)
                    if hg is None:
                        return False, {"reason": "COMPOSITION_NOT_CLOSED", "h": h, "g": g}

                    left = self.compose(h, gf)
                    right = self.compose(hg, f)
                    if left != right:
                        return False, {
                            "reason": "NOT_ASSOCIATIVE",
                            "f": f,
                            "g": g,
                            "h": h,
                            "left": left,
                            "right": right,
                        }

        return True, None

    def opposite(self) -> "FiniteCategory":
        """Construct the dual / opposite category C^op."""
        op_morphisms = [[name, dst, src] for name, (src, dst) in self.morphisms.items()]
        # In C^op, f^op: Y -> X, g^op: Z -> Y, and f^op ∘ g^op = (g ∘ f)^op
        op_comp = {}
        for g, row in self.raw_comp.items():
            for f, gf in row.items():
                # in op, f ∘_op g = g ∘ f = gf
                if f not in op_comp:
                    op_comp[f] = {}
                op_comp[f][g] = gf
        return FiniteCategory(self.objects, op_morphisms, op_comp)
