"""Test-only draft checker for the arc challenge, in two strengths.

``--endpoints-only`` checks endpoints and ignores the protected pair, so it
disagrees with the native verdicts on the separation fixtures.
"""
import json
import sys

VERDICT = ("is_", "has_", "passes", "verdict")


def refuse(code):
    print(json.dumps({"verdict": "REFUSE", "code": code}))
    sys.exit(0)


obj = json.load(sys.stdin)
if not obj:
    refuse("R_EMPTY_INPUT")
if any(k.startswith(VERDICT) for k in obj):
    refuse("R_VERDICT_FIELD")
nodes, off = set(), 0
for name, count in obj["sorts"]:
    if name == "node":
        nodes = set(range(off, off + count))
    off += count
for name, args in obj["relations"]:
    if len(args) != 2 or args[0] >= off or args[1] >= off:
        refuse("R002_ABSENT")
    if args[0] not in nodes:
        refuse("R002_SOURCE")
    if args[1] not in nodes:
        refuse("R002_TARGET")
if "--endpoints-only" not in sys.argv:
    def profile(d):
        out = {("node",)} if d in nodes else set()
        for name, args in obj["relations"]:
            if d in args:
                out.add((name, tuple(None if a == d else a for a in args)))
        return out
    for p, q in obj["protected"]:
        if profile(p) == profile(q):
            refuse("R002_COLLAPSED")
print(json.dumps({"verdict": "ACCEPT"}))
