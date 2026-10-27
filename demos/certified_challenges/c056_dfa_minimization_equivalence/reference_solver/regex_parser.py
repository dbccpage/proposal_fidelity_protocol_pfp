"""Regex AST definitions and recursive descent parser for Challenge C056."""

from typing import List


class Epsilon:
    def __repr__(self):
        return "%"


class EmptySet:
    def __repr__(self):
        return "#"


class Literal:
    def __init__(self, c: str):
        self.c = c

    def __repr__(self):
        return self.c


class Concat:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left}.{self.right})"


class Union:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left}|{self.right})"


class Star:
    def __init__(self, child):
        self.child = child

    def __repr__(self):
        return f"{self.child}*"


class ParseError(Exception):
    pass


def parse_regex(s: str, alphabet: List[str]):
    if not isinstance(s, str):
        raise ParseError("Regex must be a string")
    if not isinstance(alphabet, list) or len(alphabet) == 0:
        raise ParseError("Alphabet must be a non-empty list")

    alpha_set = set(alphabet)
    if len(alpha_set) != len(alphabet):
        raise ParseError("Alphabet contains duplicate letters")
    for a in alphabet:
        if not isinstance(a, str) or len(a) != 1 or a in ("%", "#", "(", ")", "*", "|"):
            raise ParseError(f"Invalid alphabet character: {a}")

    s = s.strip()
    if not s:
        return Epsilon()

    tokens = []
    for c in s:
        if c in (" ", "\t", "\n"):
            continue
        if c in alpha_set or c in ("%", "#", "(", ")", "*", "|"):
            tokens.append(c)
        else:
            raise ParseError(f"Character '{c}' not in alphabet or syntax symbols")

    # Insert explicit concatenation operators '.'
    atom_end = alpha_set | {"%", "#", ")", "*"}
    atom_start = alpha_set | {"%", "#", "("}
    inserted = []
    for i, t in enumerate(tokens):
        inserted.append(t)
        if i + 1 < len(tokens):
            if t in atom_end and tokens[i + 1] in atom_start:
                inserted.append(".")

    # Shunting Yard to postfix
    prec = {"*": 3, ".": 2, "|": 1}
    output = []
    ops = []

    for t in inserted:
        if t in alpha_set or t in ("%", "#"):
            output.append(t)
        elif t == "(":
            ops.append(t)
        elif t == ")":
            while ops and ops[-1] != "(":
                output.append(ops.pop())
            if not ops:
                raise ParseError("Mismatched parentheses: unclosed ')'")
            ops.pop()  # pop '('
        elif t in prec:
            while ops and ops[-1] != "(" and prec.get(ops[-1], 0) >= prec[t]:
                output.append(ops.pop())
            ops.append(t)

    while ops:
        top = ops.pop()
        if top in ("(", ")"):
            raise ParseError("Mismatched parentheses")
        output.append(top)

    # Build AST
    stack = []
    for t in output:
        if t in alpha_set:
            stack.append(Literal(t))
        elif t == "%":
            stack.append(Epsilon())
        elif t == "#":
            stack.append(EmptySet())
        elif t == "*":
            if not stack:
                raise ParseError("Invalid '*' with no operand")
            stack.append(Star(stack.pop()))
        elif t == ".":
            if len(stack) < 2:
                raise ParseError("Invalid concatenation operator placement")
            r = stack.pop()
            l = stack.pop()
            stack.append(Concat(l, r))
        elif t == "|":
            if len(stack) < 2:
                raise ParseError("Invalid union operator placement")
            r = stack.pop()
            l = stack.pop()
            stack.append(Union(l, r))

    if len(stack) != 1:
        raise ParseError("Invalid expression structure")

    return stack[0]
