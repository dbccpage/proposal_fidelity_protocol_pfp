# AuthorityEffect: None.
"""
Lexicographic Path Order (LPO) for Term Rewriting in C046.
Guarantees strict well-founded reduction order for termination of rewrite rules.
"""

from typing import Dict, Optional

from .term import Fun, Term, Var


class TermOrder:
    """Lexicographic Path Order (LPO) with custom symbol precedence."""

    def __init__(self, precedence: Optional[Dict[str, int]] = None):
        # Higher integer = higher precedence
        self.precedence = precedence or {
            "inv": 100,
            "mul": 50,
            "add": 40,
            "neg": 80,
            "f": 30,
            "g": 20,
            "h": 10,
            "e": 5,
            "0": 5,
            "1": 5,
        }

    def prec(self, symbol: str) -> int:
        return self.precedence.get(symbol, 0)

    def greater(self, s: Term, t: Term) -> bool:
        """Returns True if s >_lpo t."""
        # 1. If t is a variable: s > t iff t in vars(s) and s != t
        if t.is_var():
            assert isinstance(t, Var)
            return t.name in s.vars() and s != t

        # 2. If s is a variable: x cannot be > any non-variable term
        if s.is_var():
            return False

        assert isinstance(s, Fun) and isinstance(t, Fun)

        # 3. Case 1: Any subterm of s is >= t
        for si in s.args:
            if si == t or self.greater(si, t):
                return True

        # 4. For Cases 2 and 3, s must be greater than ALL arguments of t
        if not all(self.greater(s, tj) for tj in t.args):
            return False

        # 5. Case 2: Function symbol precedence f > g
        if self.prec(s.symbol) > self.prec(t.symbol):
            return True

        # 6. Case 3: Same function symbol f == g and lexicographic comparison
        if s.symbol == t.symbol:
            # Lexicographic comparison of arguments
            for si, tj in zip(s.args, t.args):
                if si == tj:
                    continue
                return self.greater(si, tj)
            return len(s.args) > len(t.args)

        return False
