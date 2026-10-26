# 09. LP forcing trace: a worked example

**AuthorityEffect:** None.

## Core idea

The game compresses vague intent into declared symbols, rules, obstructions, operators, and terminal conditions before prose or code is allowed.

Vague request:

```text
build me a primal-dual solver in rust.
```

Symbol game request:

```text
use symbols a-z, 0-9, <, >, =.
declare the carrier.
declare allowed terms.
declare allowed rewrites.
declare the obstruction.
declare the terminal condition.
then derive the operator structure needed for a solver.
```

Code comes after symbolic compression, obstruction detection, operator selection, and validation.

## Trace

```text
lp<
max<3x+2y>
var<x,y>
ub1<x+y<=4>
ub2<x<=2>
ub3<y<=3>
nn<x>=0,y>=0>
try<x=2,y=2>
hit<10>
proof<
use<2*ub1+ub2>
derive<3x+2y<=10>
>
qed<try=opt>
>
```

The model emits a trace in a constrained algebra, so a failure is measurable.

## Two checks

| Check | Question |
|---|---|
| Local | Does `2*ub1+ub2` yield `3x+2y<=10`? |
| Global | Does the derived bound bound the declared objective? Does `try` satisfy every original constraint? Does `qed` match the declared problem? |

Only when both pass is `optimalitycertified` reached. Local validity alone can produce a fragment that does not solve the declared problem. A trace must stay green at the packet boundary: same problem, same protected skeleton, same terminal target, same evidence ceiling.

## Statuses

Passing: `syntaxvalid`, `candidatefeasible`, `objectivehitvalid`, `upperboundcertified`, `optimalitycertified`, `localstepvalid`, `globalboundaryvalid`, `admissiblestep`.

Failing: `malformedpacket`, `invalidconstraintreference`, `invalidlinearcombination`, `candidateinfeasible`, `objectivemismatch`, `upperboundgap`, `qedrejected`, `boundaryviolation`, `problemmutation`, `constraintscopeleak`, `protectedskeletonmutation`, `evidencepromotionattempt`.

## Supports / does not support

- Supports: the local/global split as a teaching device.
- Does not support: that the listed statuses are the native host's complete set.
