"""Target checker of record for MSS-023, row 23 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 23): check compatible overlap restrictions and unique gluing
for declared cover. Negative instance: locally agreeing names with conflicting
overlaps are rejected.

Input (closed): ``{"points": [name], "patches": [[name]], "sections":
[[[point, value]]], "glued": [[point, value]]}``. Section i lives on patch i;
``glued`` is the producer's gluing witness, a global assignment.

Declared input class: the function reading. Sections are value assignments on
finite patches of a finite point set, and restriction is restriction of
functions, so a compatible family glues to at most one global assignment, and
to exactly one when the patches cover the points. The transport reading
(fibres twisted by per-overlap transports around a cycle of the nerve) is not
decided here.

Clauses, recomputed from the sections, never read from a declared flag:

- C1 ``R023_NOT_COVERING``: some point lies in no patch, so no glue is unique;
- C2 ``R023_SECTION_DOMAIN``: a section is not defined on exactly its patch;
- C3 ``R023_OVERLAP_CONFLICT``: two sections disagree at a shared point (the
  level's negative);
- C4 ``R023_GLUE_MISMATCH``: the declared glue is not a global assignment
  that restricts to every section.
"""

STAGE = 23
ROW_SHA256 = "sha256:c800e910c45a89708526710f6d6b02fe353ddf8e7100141e4520c5432bbfd641"
FIELDS = ("glued", "patches", "points", "sections")
CLAUSES = (
    ("C1", "R023_NOT_COVERING"),
    ("C2", "R023_SECTION_DOMAIN"),
    ("C3", "R023_OVERLAP_CONFLICT"),
    ("C4", "R023_GLUE_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("restriction",)
OWN_NEGATIVE = {
    "glued": [["1", "0"], ["2", "1"], ["3", "0"]],
    "patches": [["1", "2"], ["2", "3"]],
    "points": ["1", "2", "3"],
    "sections": [[["1", "0"], ["2", "1"]], [["2", "0"], ["3", "0"]]],
}
OWN_NEGATIVE_CODE = "R023_OVERLAP_CONFLICT"


def _assignment(rows):
    out = {}
    for row in _seq(rows):
        _seq(row, 2)
        point, value = _text(row[0]), _text(row[1])
        _require(point not in out, "R_SCHEMA")
        out[point] = value
    return out


def _decide(payload):
    points = [_text(p) for p in _seq(payload["points"])]
    _require(len(set(points)) == len(points), "R_SCHEMA")
    known = set(points)
    patches = []
    for patch in _seq(payload["patches"]):
        members = [_text(p) for p in _seq(patch)]
        _require(members and len(set(members)) == len(members) and set(members) <= known, "R_SCHEMA")
        patches.append(set(members))
    sections = [_assignment(rows) for rows in _seq(payload["sections"], len(patches))]
    for patch, section in zip(patches, sections):
        _require(set(section) == patch, "R023_SECTION_DOMAIN")
    covered = set().union(*patches) if patches else set()
    _require(covered == known, "R023_NOT_COVERING")
    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            for point in patches[i] & patches[j]:
                _require(sections[i][point] == sections[j][point], "R023_OVERLAP_CONFLICT")
    glued = _assignment(payload["glued"])
    _require(set(glued) == known, "R023_GLUE_MISMATCH")
    for section in sections:
        _require(all(glued[point] == value for point, value in section.items()), "R023_GLUE_MISMATCH")
