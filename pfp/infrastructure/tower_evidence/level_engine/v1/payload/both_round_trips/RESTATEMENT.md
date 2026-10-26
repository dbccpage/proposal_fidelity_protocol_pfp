# Restatement: `both_round_trips`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two sides, a source and a target, each place finitely many units in a
numbered list of degrees shared by both, and each carries a step table from
every unit to the units one degree lower, with exact rational entries. On
each side a step followed by a step is zero. A map there, from source to
target, and a map back, from target to source, keep degrees and commute with
the steps. Each side also carries a declared lift table, from every unit to
the units one degree higher. Both round trips must return to the identity
through their lifts: on the source, back after there, less the identity, is
step after lift plus lift after step in every degree; on the target, the
same holds for there after back.

## Refused case

A round trip that returns on one side only, offered as a return on both:
back after there returns on the source, but there after back does not return
on the target through the declared target lift.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| degree, next | supplied object-language datum | the numbered degrees and which follows which |
| source, target, source_in, target_in | supplied object-language datum | the units of each side and their degrees |
| number | supplied object-language datum | exact rational values for entries |
| source_step, target_step | supplied object-language datum | each side's step table |
| there, back | supplied object-language datum | the two maps |
| source_lift, target_lift | supplied object-language datum | the declared lifts |
| source_placed, target_placed, one_source_place, one_target_place | derived definition | relational requirements: each unit lies in one degree |
| source_steps_given, target_steps_given, there_given, back_given, source_lifts_given, target_lifts_given | derived definition | relational requirements: an entry for every related pair of units |
| one_source_step, one_target_step, one_there, one_back, one_source_lift, one_target_lift | derived definition | relational requirements: one entry per pair |
| source_steps_graded, target_steps_graded, there_graded, back_graded, source_lifts_graded, target_lifts_graded | derived definition | relational requirements: no entry between units of the wrong degrees |
| degrees_in_line, steps_square_zero, maps_commute, source_return, target_return | derived definition | value clauses, decided over exact values |
| products and sums of tables of exact rationals | metatheory apparatus | the harness's exact arithmetic |
| what each side keeps in each degree (rank count) | metatheory apparatus | a description of each fixture, not a clause |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The lifts are declared and replayed exactly; they are
never searched for. The positive is a target whose step sends one unit to
a0 + 2 a1, next to a source whose step sends one unit to another: both keep
one unit's worth in degrees 0 and 2 and nothing in degree 1, and the maps
with their lifts return on both sides (17 elements). In the own negative the
target's step is zero, so the target keeps more than the source and no
target lift can return.
